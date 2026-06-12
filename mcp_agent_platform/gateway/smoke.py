from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SmokeCheckError(RuntimeError):
    """Raised when a demo smoke check fails."""


def run_smoke_check(
    base_url: str = "http://127.0.0.1:8000",
    *,
    include_search: bool = False,
    timeout_seconds: float = 5,
) -> dict[str, Any]:
    normalized_base_url = base_url.rstrip("/")
    checks: list[str] = []

    health = _request_json("GET", f"{normalized_base_url}/health", timeout_seconds=timeout_seconds)
    if health.get("status") != "ok":
        raise SmokeCheckError("health check failed: expected status=ok")
    checks.append("health")

    tools = _request_json("GET", f"{normalized_base_url}/tools", timeout_seconds=timeout_seconds)
    tool_names = {tool.get("name") for tool in tools.get("tools", [])}
    missing_tools = {"echo", "web_search"} - tool_names
    if missing_tools:
        missing = ", ".join(sorted(missing_tools))
        raise SmokeCheckError(f"tools check failed: missing required tools: {missing}")
    checks.append("tools")

    echo_response = _chat(
        normalized_base_url,
        "/echo hello",
        timeout_seconds=timeout_seconds,
    )
    _assert_chat_response(echo_response, expected_answer_fragment="hello")
    checks.append("chat_echo")

    if include_search:
        search_response = _chat(
            normalized_base_url,
            "/search mcp protocol",
            timeout_seconds=timeout_seconds,
        )
        _assert_chat_response(search_response, expected_answer_fragment="mcp")
        checks.append("chat_search")

    return {
        "base_url": normalized_base_url,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run demo smoke checks against a running gateway.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--include-search", action="store_true")
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args(argv)

    try:
        report = run_smoke_check(
            args.base_url,
            include_search=args.include_search,
            timeout_seconds=args.timeout,
        )
    except SmokeCheckError as exc:
        print(f"smoke check failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _chat(base_url: str, message: str, *, timeout_seconds: float) -> dict[str, Any]:
    return _request_json(
        "POST",
        f"{base_url}/chat",
        payload={"message": message},
        timeout_seconds=timeout_seconds,
    )


def _request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout_seconds: float,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_body = response.read()
    except HTTPError as exc:
        raise SmokeCheckError(f"{method} {url} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise SmokeCheckError(f"{method} {url} failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise SmokeCheckError(f"{method} {url} timed out") from exc

    try:
        return json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SmokeCheckError(f"{method} {url} did not return valid JSON") from exc


def _assert_chat_response(
    response: dict[str, Any],
    *,
    expected_answer_fragment: str,
) -> None:
    answer = str(response.get("answer", ""))
    if expected_answer_fragment.lower() not in answer.lower():
        raise SmokeCheckError(
            f"chat check failed: answer does not contain {expected_answer_fragment!r}"
        )

    event_types = [event.get("type") for event in response.get("events", [])]
    expected_events = ["action", "observation", "answer"]
    if event_types != expected_events:
        raise SmokeCheckError(
            f"chat check failed: expected events {expected_events}, got {event_types}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
