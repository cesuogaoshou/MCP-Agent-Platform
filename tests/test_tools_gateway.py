from fastapi.testclient import TestClient
from mcp_agent_platform.gateway.app import create_app


def test_tools_endpoint_returns_registered_tools() -> None:
    client = TestClient(create_app(agent=FakeAgent(), registry=FakeRegistry()))

    response = client.get("/tools")

    assert response.status_code == 200
    assert response.json() == {
        "tools": [
            {
                "name": "echo",
                "description": "Echo input text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            },
            {
                "name": "web_search",
                "description": "Search the web.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        ]
    }


def test_tools_endpoint_returns_503_when_registry_is_not_configured() -> None:
    client = TestClient(create_app(agent=FakeAgent()))

    response = client.get("/tools")

    assert response.status_code == 503
    assert response.json() == {"detail": "Tool registry is not configured"}


class FakeAgent:
    pass


class FakeRegistry:
    async def list_tools(self) -> list[dict]:
        return [
            {
                "name": "echo",
                "description": "Echo input text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            },
            {
                "name": "web_search",
                "description": "Search the web.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        ]
