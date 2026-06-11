from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

import httpx


class DuckDuckGoLiteSearchProvider:
    def __init__(self, http_client: Any | None = None) -> None:
        self.http_client = http_client or httpx.AsyncClient(timeout=10)

    async def search(self, query: str, top_k: int, language: str) -> list[dict[str, str]]:
        response = await self.http_client.get(
            "https://duckduckgo.com/html/",
            params={"q": query, "kl": _duckduckgo_region(language)},
            headers={"User-Agent": "MCP-Agent-Platform/0.1"},
        )
        response.raise_for_status()
        return _parse_duckduckgo_results(response.text)[:top_k]


class FakeSearchProvider:
    async def search(self, query: str, top_k: int, language: str) -> list[dict[str, str]]:
        return [
            {
                "title": f"Fake result for {query}",
                "url": f"https://example.com/search?q={quote(query)}",
                "snippet": "This is a deterministic fake search result.",
            }
        ][:top_k]


def _duckduckgo_region(language: str) -> str:
    if language.lower().startswith("zh"):
        return "cn-zh"
    return "us-en"


def _parse_duckduckgo_results(html: str) -> list[dict[str, str]]:
    parser = _DuckDuckGoHTMLParser()
    parser.feed(html)
    return parser.results


def _normalize_duckduckgo_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    return raw_url


class _DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._capture: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if tag == "div" and "result" in classes:
            self._current = {"title": "", "url": "", "snippet": ""}

        if self._current is None:
            return

        if tag == "a" and "result__a" in classes:
            self._capture = "title"
            self._buffer = []
            self._current["url"] = _normalize_duckduckgo_url(attributes.get("href") or "")
            return

        if tag in {"a", "div"} and "result__snippet" in classes:
            self._capture = "snippet"
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._current is None:
            return

        if self._capture == "title" and tag == "a":
            self._current["title"] = " ".join("".join(self._buffer).split())
            self._capture = None
            self._buffer = []
            return

        if self._capture == "snippet" and tag in {"a", "div"}:
            self._current["snippet"] = " ".join("".join(self._buffer).split())
            self._capture = None
            self._buffer = []
            return

        if tag == "div" and self._current["title"] and self._current["url"]:
            self.results.append(self._current)
            self._current = None
