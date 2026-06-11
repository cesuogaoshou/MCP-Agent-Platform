import sys
from pathlib import Path

import pytest
from mcp_agent_platform.agent.tool_registry import RegisteredServer, ToolRegistry


@pytest.mark.anyio
async def test_registry_lists_tools_from_registered_servers() -> None:
    registry = make_registry()
    await registry.start()
    try:
        tools = await registry.list_tools()
    finally:
        await registry.close()

    assert [tool["name"] for tool in tools] == ["echo", "web_search"]


@pytest.mark.anyio
async def test_registry_routes_tool_call_by_name() -> None:
    registry = make_registry()
    await registry.start()
    try:
        echo_result = await registry.call_tool("echo", {"text": "hello"})
        search_result = await registry.call_tool(
            "web_search", {"query": "mcp protocol", "top_k": 1}
        )
    finally:
        await registry.close()

    assert echo_result == {
        "content": [
            {
                "type": "json",
                "json": {"echo": "hello"},
            }
        ],
        "isError": False,
    }
    assert search_result["content"][0]["json"]["results"][0]["title"] == (
        "Fake result for mcp protocol"
    )


def make_registry() -> ToolRegistry:
    project_root = Path.cwd()
    return ToolRegistry(
        servers=[
            RegisteredServer(
                name="echo",
                command=[sys.executable, "-m", "mcp_agent_platform.tools.echo_server"],
                cwd=project_root,
                env={"PYTHONPATH": str(project_root)},
            ),
            RegisteredServer(
                name="web-search",
                command=[sys.executable, "-m", "mcp_agent_platform.tools.web_search_server"],
                cwd=project_root,
                env={
                    "PYTHONPATH": str(project_root),
                    "MCP_AGENT_SEARCH_PROVIDER": "fake",
                },
            ),
        ]
    )
