import asyncio
import json
import os
from asyncio.subprocess import PIPE, Process
from pathlib import Path
from typing import Any

from mcp_agent_platform.mcp.jsonrpc import JsonRpcError, decode_message


class StdioMCPClient:
    def __init__(
        self,
        command: list[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.command = command
        self.cwd = cwd
        self.env = env
        self._process: Process | None = None
        self._next_id = 1

    async def start(self) -> None:
        env = None
        if self.env is not None:
            env = os.environ.copy()
            env.update(self.env)

        self._process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            cwd=self.cwd,
            env=env,
        )

    async def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        process = self._require_process()
        message_id = self._next_id
        self._next_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": message_id,
            "method": method,
            "params": params or {},
        }
        await self._write_line(process, request)

        if process.stdout is None:
            raise RuntimeError("MCP server stdout is not available")

        raw_response = await process.stdout.readline()
        if not raw_response:
            stderr = await self._read_stderr(process)
            raise RuntimeError(f"MCP server closed stdout: {stderr}")

        response = decode_message(raw_response.decode("utf-8"))
        if "error" in response:
            error = response["error"]
            raise JsonRpcError(error["code"], error["message"], error.get("data"))

        return response["result"]

    async def close(self) -> None:
        if self._process is None:
            return

        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=2)
        except TimeoutError:
            self._process.kill()
            await self._process.wait()
        finally:
            self._process = None

    def _require_process(self) -> Process:
        if self._process is None:
            raise RuntimeError("MCP client has not been started")
        return self._process

    async def _write_line(self, process: Process, payload: dict[str, Any]) -> None:
        if process.stdin is None:
            raise RuntimeError("MCP server stdin is not available")

        process.stdin.write(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")
        await process.stdin.drain()

    async def _read_stderr(self, process: Process) -> str:
        if process.stderr is None:
            return ""

        try:
            raw_stderr = await asyncio.wait_for(process.stderr.read(), timeout=1)
        except TimeoutError:
            return ""

        return raw_stderr.decode("utf-8", errors="replace").strip()
