from fastapi.testclient import TestClient
from mcp_agent_platform.gateway.app import create_app


def test_runtime_app_chat_calls_echo_tool(monkeypatch) -> None:
    monkeypatch.setenv("MCP_AGENT_SEARCH_PROVIDER", "fake")

    with TestClient(create_app(enable_runtime=True)) as client:
        response = client.post("/chat", json={"message": "/echo hello"})

    assert response.status_code == 200
    assert response.json()["answer"] == '{"echo": "hello"}'
    assert response.json()["tool_name"] == "echo"


def test_runtime_app_lists_registered_tools(monkeypatch) -> None:
    monkeypatch.setenv("MCP_AGENT_SEARCH_PROVIDER", "fake")

    with TestClient(create_app(enable_runtime=True)) as client:
        response = client.get("/tools")

    assert response.status_code == 200
    assert [tool["name"] for tool in response.json()["tools"]] == ["echo", "web_search"]


def test_runtime_app_streams_chat_events(monkeypatch) -> None:
    monkeypatch.setenv("MCP_AGENT_SEARCH_PROVIDER", "fake")

    with TestClient(create_app(enable_runtime=True)) as client:
        response = client.post("/chat/stream", json={"message": "/echo hello"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: action\n" in response.text
    assert "event: observation\n" in response.text
    assert "event: answer\n" in response.text


def test_runtime_app_keeps_session_messages(monkeypatch) -> None:
    monkeypatch.setenv("MCP_AGENT_SEARCH_PROVIDER", "fake")

    with TestClient(create_app(enable_runtime=True)) as client:
        first_response = client.post("/chat", json={"message": "/echo first"})
        session_id = first_response.json()["session_id"]
        second_response = client.post(
            "/chat",
            json={"message": "/echo second", "session_id": session_id},
        )

    assert second_response.status_code == 200
    assert second_response.json()["session_id"] == session_id
    assert [message["role"] for message in second_response.json()["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
