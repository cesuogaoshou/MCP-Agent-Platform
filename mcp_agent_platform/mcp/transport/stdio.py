import asyncio
import json
import sys
from typing import TextIO

from mcp_agent_platform.mcp.jsonrpc import JsonRpcError, decode_message, make_error_response
from mcp_agent_platform.mcp.server import BaseMCPServer


async def run_stdio_server(
    server: BaseMCPServer,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    input_stream = input_stream or sys.stdin
    output_stream = output_stream or sys.stdout

    while True:
        line = await asyncio.to_thread(input_stream.readline)
        if line == "":
            break

        response = await _handle_line(server, line)
        if response is None:
            continue

        output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
        output_stream.flush()


async def _handle_line(server: BaseMCPServer, line: str) -> dict | None:
    try:
        message = decode_message(line)
        return await server.handle_message(message)
    except JsonRpcError as exc:
        return make_error_response(None, exc.code, exc.message, exc.data)
