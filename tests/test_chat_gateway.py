from fastapi.testclient import TestClient
from mcp_agent_platform.agent.runner import AgentEvent, AgentRunResult
from mcp_agent_platform.gateway.app import create_app


def test_chat_endpoint_runs_configured_agent() -> None:
    agent = FakeAgent()
    client = TestClient(create_app(agent=agent))

    response = client.post("/chat", json={"message": "/echo hello"})

    assert response.status_code == 200
    assert agent.messages == ["/echo hello"]
    payload = response.json()
    assert payload["session_id"]
    assert payload == {
        "answer": '{"echo": "hello"}',
        "session_id": payload["session_id"],
        "tool_name": "echo",
        "tool_arguments": {"text": "hello"},
        "tool_result": {
            "content": [{"type": "json", "json": {"echo": "hello"}}],
            "isError": False,
        },
        "events": [
            {
                "type": "action",
                "message": "Calling tool: echo",
                "data": {
                    "tool_name": "echo",
                    "tool_arguments": {"text": "hello"},
                },
            },
            {
                "type": "answer",
                "message": "Final answer generated",
                "data": {"answer": '{"echo": "hello"}'},
            },
        ],
        "messages": [
            {"role": "user", "content": "/echo hello"},
            {"role": "assistant", "content": '{"echo": "hello"}'},
        ],
    }


def test_chat_endpoint_rejects_empty_message() -> None:
    client = TestClient(create_app(agent=FakeAgent()))

    response = client.post("/chat", json={"message": "   "})

    assert response.status_code == 422


def test_chat_endpoint_keeps_recent_messages_for_same_session() -> None:
    client = TestClient(create_app(agent=FakeAgent()))

    first_response = client.post("/chat", json={"message": "/echo first"})
    session_id = first_response.json()["session_id"]
    second_response = client.post(
        "/chat",
        json={"message": "/echo second", "session_id": session_id},
    )

    assert second_response.status_code == 200
    assert second_response.json()["session_id"] == session_id
    assert second_response.json()["messages"] == [
        {"role": "user", "content": "/echo first"},
        {"role": "assistant", "content": '{"echo": "hello"}'},
        {"role": "user", "content": "/echo second"},
        {"role": "assistant", "content": '{"echo": "hello"}'},
    ]


def test_chat_stream_endpoint_returns_agent_events_as_sse() -> None:
    agent = FakeAgent()
    client = TestClient(create_app(agent=agent))

    response = client.post("/chat/stream", json={"message": "/echo hello"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == (
        "event: action\n"
        'data: {"type":"action","message":"Calling tool: echo",'
        '"data":{"tool_name":"echo","tool_arguments":{"text":"hello"}}}\n\n'
        "event: answer\n"
        'data: {"type":"answer","message":"Final answer generated",'
        '"data":{"answer":"{\\"echo\\": \\"hello\\"}"}}\n\n'
    )


class FakeAgent:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def run(self, user_input: str) -> AgentRunResult:
        self.messages.append(user_input)
        return AgentRunResult(
            user_input=user_input,
            final_answer='{"echo": "hello"}',
            tool_name="echo",
            tool_arguments={"text": "hello"},
            tool_result={
                "content": [{"type": "json", "json": {"echo": "hello"}}],
                "isError": False,
            },
            events=[
                AgentEvent(
                    type="action",
                    message="Calling tool: echo",
                    data={
                        "tool_name": "echo",
                        "tool_arguments": {"text": "hello"},
                    },
                ),
                AgentEvent(
                    type="answer",
                    message="Final answer generated",
                    data={"answer": '{"echo": "hello"}'},
                ),
            ],
        )
