import sys
from pathlib import Path

import pytest
from mcp_agent_platform.mcp.client import StdioMCPClient


@pytest.mark.anyio
async def test_stdio_client_calls_project_echo_server() -> None:
    project_root = Path.cwd()
    client = StdioMCPClient(
        [sys.executable, "-m", "mcp_agent_platform.tools.echo_server"],
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


@pytest.mark.anyio
async def test_stdio_client_calls_project_web_search_server_with_fake_provider() -> None:
    project_root = Path.cwd()
    client = StdioMCPClient(
        [sys.executable, "-m", "mcp_agent_platform.tools.web_search_server"],
        cwd=project_root,
        env={
            "PYTHONPATH": str(project_root),
            "MCP_AGENT_SEARCH_PROVIDER": "fake",
        },
    )
    await client.start()
    try:
        tools = await client.request("tools/list", {})
        result = await client.request(
            "tools/call",
            {
                "name": "web_search",
                "arguments": {"query": "mcp protocol", "top_k": 1},
            },
        )
    finally:
        await client.close()

    assert tools["tools"][0]["name"] == "web_search"
    assert result == {
        "content": [
            {
                "type": "json",
                "json": {
                    "results": [
                        {
                            "title": "Fake result for mcp protocol",
                            "url": "https://example.com/search?q=mcp%20protocol",
                            "snippet": "This is a deterministic fake search result.",
                        }
                    ]
                },
            }
        ],
        "isError": False,
    }
