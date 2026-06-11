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


class FakeDictSearchProvider:
    async def search(self, query: str, top_k: int, language: str) -> list[dict[str, str]]:
        return [
            {
                "title": "Dict Result",
                "url": "https://example.com/dict",
                "snippet": "Dict snippet",
            }
        ]


class FailingSearchProvider:
    async def search(self, query: str, top_k: int, language: str) -> list[dict[str, str]]:
        raise RuntimeError("search backend unavailable")


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
async def test_web_search_server_accepts_dict_results_from_provider() -> None:
    server = create_server(FakeDictSearchProvider())

    response = await server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "web_search",
                "arguments": {"query": "anything"},
            },
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "content": [
                {
                    "type": "json",
                    "json": {
                        "results": [
                            {
                                "title": "Dict Result",
                                "url": "https://example.com/dict",
                                "snippet": "Dict snippet",
                            }
                        ]
                    },
                }
            ],
            "isError": False,
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


@pytest.mark.anyio
async def test_web_search_server_returns_tool_error_for_missing_query() -> None:
    server = create_server(FakeDictSearchProvider())

    response = await server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "web_search",
                "arguments": {},
            },
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 4,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "Missing required argument: query",
                }
            ],
            "isError": True,
        },
    }


@pytest.mark.anyio
async def test_web_search_server_returns_tool_error_when_provider_fails() -> None:
    server = create_server(FailingSearchProvider())

    response = await server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "web_search",
                "arguments": {"query": "mcp protocol"},
            },
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 5,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "search backend unavailable",
                }
            ],
            "isError": True,
        },
    }
