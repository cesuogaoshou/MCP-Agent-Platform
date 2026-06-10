from fastapi.testclient import TestClient
from mcp_agent_platform.gateway.app import create_app


def test_health_endpoint_returns_project_status() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "mcp-agent-platform",
        "version": "0.1.0",
    }
