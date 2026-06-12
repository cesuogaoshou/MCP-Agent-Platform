from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any

import pytest
from mcp_agent_platform.gateway.smoke import SmokeCheckError, run_smoke_check


class DemoSmokeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        if self.path == "/tools":
            self._send_json(
                {
                    "tools": [
                        {"name": "echo", "description": "Echo input text"},
                        {"name": "web_search", "description": "Search the web"},
                    ]
                }
            )
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/chat":
            self.send_error(404)
            return

        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        message = body["message"]
        if message.startswith("/search"):
            self._send_json(
                {
                    "answer": "Found fake search results for mcp protocol",
                    "events": [
                        {"type": "action"},
                        {"type": "observation"},
                        {"type": "answer"},
                    ],
                }
            )
            return

        self._send_json(
            {
                "answer": "hello",
                "events": [
                    {"type": "action"},
                    {"type": "observation"},
                    {"type": "answer"},
                ],
            }
        )

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def demo_server() -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoSmokeHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_run_smoke_check_verifies_demo_endpoints(demo_server: str) -> None:
    report = run_smoke_check(demo_server)

    assert report["base_url"] == demo_server
    assert report["checks"] == [
        "health",
        "tools",
        "chat_echo",
    ]


def test_run_smoke_check_can_include_search_path(demo_server: str) -> None:
    report = run_smoke_check(demo_server, include_search=True)

    assert report["checks"] == [
        "health",
        "tools",
        "chat_echo",
        "chat_search",
    ]


def test_run_smoke_check_fails_when_required_tool_is_missing(demo_server: str) -> None:
    class MissingToolHandler(DemoSmokeHandler):
        def do_GET(self) -> None:
            if self.path == "/tools":
                self._send_json({"tools": [{"name": "echo"}]})
                return
            super().do_GET()

    server = ThreadingHTTPServer(("127.0.0.1", 0), MissingToolHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with pytest.raises(SmokeCheckError, match="missing required tools"):
            run_smoke_check(f"http://{host}:{port}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
