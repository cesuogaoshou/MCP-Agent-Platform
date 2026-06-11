import json
from typing import Any

import pytest
from mcp_agent_platform.agent.runner import ToolCallingAgent


@pytest.mark.anyio
async def test_agent_routes_echo_command_to_echo_tool() -> None:
    registry = FakeRegistry(
        {
            "echo": {
                "content": [{"type": "json", "json": {"echo": "hello"}}],
                "isError": False,
            }
        }
    )
    agent = ToolCallingAgent(registry)

    result = await agent.run("/echo hello")

    assert registry.calls == [("echo", {"text": "hello"})]
    assert result.tool_name == "echo"
    assert result.tool_arguments == {"text": "hello"}
    assert result.final_answer == json.dumps({"echo": "hello"}, ensure_ascii=False)


@pytest.mark.anyio
async def test_agent_routes_search_command_to_web_search_tool() -> None:
    registry = FakeRegistry(
        {
            "web_search": {
                "content": [
                    {
                        "type": "json",
                        "json": {
                            "results": [
                                {
                                    "title": "MCP",
                                    "url": "https://example.com",
                                    "snippet": "Model Context Protocol",
                                }
                            ]
                        },
                    }
                ],
                "isError": False,
            }
        }
    )
    agent = ToolCallingAgent(registry)

    result = await agent.run("/search mcp protocol")

    assert registry.calls == [("web_search", {"query": "mcp protocol"})]
    assert result.tool_name == "web_search"
    assert result.final_answer == json.dumps(
        {
            "results": [
                {
                    "title": "MCP",
                    "url": "https://example.com",
                    "snippet": "Model Context Protocol",
                }
            ]
        },
        ensure_ascii=False,
    )


@pytest.mark.anyio
async def test_agent_returns_direct_answer_when_no_tool_matches() -> None:
    registry = FakeRegistry({})
    agent = ToolCallingAgent(registry)

    result = await agent.run("hello")

    assert registry.calls == []
    assert result.tool_name is None
    assert result.final_answer == "No matching tool command found."


class FakeRegistry:
    def __init__(self, results: dict[str, dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, arguments))
        return self.results[name]
