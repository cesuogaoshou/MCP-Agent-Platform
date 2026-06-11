from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp_agent_platform.mcp.client import StdioMCPClient


@dataclass(frozen=True)
class RegisteredServer:
    name: str
    command: list[str]
    cwd: Path | None = None
    env: dict[str, str] | None = None


class ToolRegistry:
    def __init__(self, servers: list[RegisteredServer]) -> None:
        self._servers = servers
        self._clients: list[StdioMCPClient] = []
        self._tools: list[dict[str, Any]] = []
        self._routes: dict[str, StdioMCPClient] = {}

    async def start(self) -> None:
        for server in self._servers:
            client = StdioMCPClient(
                command=server.command,
                cwd=server.cwd,
                env=server.env,
            )
            await client.start()
            await client.request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {
                        "name": "mcp-agent-platform",
                        "version": "0.1.0",
                    },
                },
            )

            tools_result = await client.request("tools/list")
            for tool in tools_result["tools"]:
                self._tools.append(tool)
                self._routes[tool["name"]] = client

            self._clients.append(client)

    async def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        client = self._routes.get(name)
        if client is None:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {name}",
                    }
                ],
                "isError": True,
            }

        return await client.request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

    async def close(self) -> None:
        for client in self._clients:
            await client.close()
        self._clients.clear()
        self._tools.clear()
        self._routes.clear()
