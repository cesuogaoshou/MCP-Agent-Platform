from fastapi.testclient import TestClient
from mcp_agent_platform.gateway.app import create_app


def test_root_serves_web_ui() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "MCP Agent Platform" in response.text
    assert 'id="chat-form"' in response.text
    assert 'id="event-list"' in response.text


def test_static_assets_are_served() -> None:
    client = TestClient(create_app())

    script_response = client.get("/static/app.js")
    style_response = client.get("/static/styles.css")

    assert script_response.status_code == 200
    assert "submitChat" in script_response.text
    assert style_response.status_code == 200
    assert ".app-shell" in style_response.text
