import asyncio
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from mcp_agent_platform.mcp.server import BaseMCPServer, Tool
from mcp_agent_platform.mcp.transport.stdio import run_stdio_server


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(Protocol):
    async def search(self, query: str, top_k: int, language: str) -> list[SearchResult]:
        """Search external information sources."""


class UnconfiguredSearchProvider:
    async def search(self, query: str, top_k: int, language: str) -> list[SearchResult]:
        raise RuntimeError("No search provider configured")


def create_server(provider: SearchProvider | None = None) -> BaseMCPServer:
    provider = provider or UnconfiguredSearchProvider()

    async def web_search(arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments["query"]
        top_k = int(arguments.get("top_k", 5))
        language = str(arguments.get("language", "zh-CN"))
        results = await provider.search(query=query, top_k=top_k, language=language)
        return {"results": [asdict(result) for result in results]}

    return BaseMCPServer(
        name="web-search-server",
        version="0.1.0",
        tools=[
            Tool(
                name="web_search",
                description="Search the web and return title, URL, and snippet results.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 5},
                        "language": {"type": "string", "default": "zh-CN"},
                    },
                    "required": ["query"],
                },
                handler=web_search,
            )
        ],
    )


def main() -> None:
    asyncio.run(run_stdio_server(create_server()))


if __name__ == "__main__":
    main()
