from dataclasses import dataclass

import pytest
from mcp_agent_platform.tools.search_providers import DuckDuckGoLiteSearchProvider


@dataclass
class FakeResponse:
    text: str

    def raise_for_status(self) -> None:
        return None


class FakeHttpClient:
    def __init__(self, html: str) -> None:
        self.html = html
        self.calls: list[dict] = []

    async def get(self, url: str, params: dict, headers: dict) -> FakeResponse:
        self.calls.append(
            {
                "url": url,
                "params": params,
                "headers": headers,
            }
        )
        return FakeResponse(self.html)


@pytest.mark.anyio
async def test_duckduckgo_provider_parses_results_and_limits_top_k() -> None:
    html = """
    <html>
      <body>
        <div class="result">
          <a class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com%2Fone">
            First Result
          </a>
          <a class="result__snippet">First snippet</a>
        </div>
        <div class="result">
          <a class="result__a" href="https://example.com/two">Second Result</a>
          <a class="result__snippet">Second snippet</a>
        </div>
      </body>
    </html>
    """
    http_client = FakeHttpClient(html)
    provider = DuckDuckGoLiteSearchProvider(http_client=http_client)

    results = await provider.search("mcp protocol", top_k=1, language="zh-CN")

    assert results == [
        {
            "title": "First Result",
            "url": "https://example.com/one",
            "snippet": "First snippet",
        }
    ]
    assert http_client.calls == [
        {
            "url": "https://duckduckgo.com/html/",
            "params": {"q": "mcp protocol", "kl": "cn-zh"},
            "headers": {"User-Agent": "MCP-Agent-Platform/0.1"},
        }
    ]
