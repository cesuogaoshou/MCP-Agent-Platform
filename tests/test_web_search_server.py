import pytest
from mcp_agent_platform.tools.web_search_server import SearchResult, create_server


class FakeSearchProvider:
    async def search(self, query: str, top_k: int, language: str) -> list[SearchResult]:
        assert query == "mcp protocol"
        assert top_k == 2
        assert language == "zh-CN"
        return [
            SearchResult(
                title="MCP Specification",
                url="https://modelcontextprotocol.io",
                snippet="Model Context Protocol documentation.",
            )
        ]


@pytest.mark.anyio
async def test_web_search_server_lists_tool_schema() -> None:
    server = create_server(FakeSearchProvider())

    response = await server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
                {
                    "name": "web_search",
                    "description": "Search the web and return title, URL, and snippet results.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "top_k": {"type": "integer", "default": 5},
                            "language": {"type": "string", "default": "zh-CN"},
                        },
                        "required": ["query"],
                    },
                }
            ]
        },
    }


@pytest.mark.anyio
async def test_web_search_server_calls_provider() -> None:
    server = create_server(FakeSearchProvider())

    response = await server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "web_search",
                "arguments": {
                    "query": "mcp protocol",
                    "top_k": 2,
                    "language": "zh-CN",
                },
            },
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "content": [
                {
                    "type": "json",
                    "json": {
                        "results": [
                            {
                                "title": "MCP Specification",
                                "url": "https://modelcontextprotocol.io",
                                "snippet": "Model Context Protocol documentation.",
                            }
                        ]
                    },
                }
            ],
            "isError": False,
        },
    }
