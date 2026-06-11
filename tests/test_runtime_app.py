from fastapi.testclient import TestClient
from mcp_agent_platform.gateway.app import create_app


def test_runtime_app_chat_calls_echo_tool(monkeypatch) -> None:
    monkeypatch.setenv("MCP_AGENT_SEARCH_PROVIDER", "fake")

    with TestClient(create_app(enable_runtime=True)) as client:
        response = client.post("/chat", json={"message": "/echo hello"})

    assert response.status_code == 200
    assert response.json()["answer"] == '{"echo": "hello"}'
    assert response.json()["tool_name"] == "echo"
