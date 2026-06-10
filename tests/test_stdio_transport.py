import sys
from pathlib import Path

import pytest
from mcp_agent_platform.mcp.client import StdioMCPClient


def write_echo_server(script_path: Path) -> None:
    script_path.write_text(
        """
import asyncio

from mcp_agent_platform.mcp.server import BaseMCPServer, Tool
from mcp_agent_platform.mcp.transport.stdio import run_stdio_server


async def echo(arguments):
    return {"echo": arguments["text"]}


server = BaseMCPServer(
    name="echo-server",
    version="0.1.0",
    tools=[
        Tool(
            name="echo",
            description="Echo input text.",
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
            handler=echo,
        )
    ],
)

asyncio.run(run_stdio_server(server))
""".lstrip(),
        encoding="utf-8",
    )


@pytest.mark.anyio
async def test_stdio_client_calls_echo_tool(tmp_path: Path) -> None:
    script_path = tmp_path / "echo_server.py"
    write_echo_server(script_path)

    project_root = Path.cwd()
    client = StdioMCPClient(
        [sys.executable, str(script_path)],
        cwd=project_root,
        env={"PYTHONPATH": str(project_root)},
    )
    await client.start()
    try:
        initialize = await client.request("initialize", {})
        tools = await client.request("tools/list", {})
        result = await client.request(
            "tools/call",
            {
                "name": "echo",
                "arguments": {"text": "hello"},
            },
        )
    finally:
        await client.close()

    assert initialize["serverInfo"] == {
        "name": "echo-server",
        "version": "0.1.0",
    }
    assert tools["tools"][0]["name"] == "echo"
    assert result == {
        "content": [
            {
                "type": "json",
                "json": {"echo": "hello"},
            }
        ],
        "isError": False,
    }
