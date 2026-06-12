import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Protocol
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from mcp_agent_platform.config.settings import get_settings
from mcp_agent_platform.gateway.runtime import create_default_agent


class AgentLike(Protocol):
    async def run(self, user_input: str) -> Any:
        """Run an agent turn for a user input."""


class ToolRegistryLike(Protocol):
    async def list_tools(self) -> list[dict[str, Any]]:
        """List registered tools."""


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be empty")
        return value


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    messages: list[dict[str, str]] = Field(default_factory=list)


def create_app(
    agent: AgentLike | None = None,
    registry: ToolRegistryLike | None = None,
    enable_runtime: bool = False,
) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        runtime_registry = None
        if enable_runtime and agent is None:
            runtime_agent, runtime_registry = create_default_agent()
            await runtime_registry.start()
            app.state.agent = runtime_agent
            app.state.registry = runtime_registry
        else:
            app.state.agent = agent
            app.state.registry = registry

        try:
            yield
        finally:
            if runtime_registry is not None:
                await runtime_registry.close()

    app = FastAPI(
        title="MCP Agent Platform",
        version=settings.version,
        lifespan=lifespan,
    )
    app.state.agent = agent
    app.state.registry = registry
    app.state.sessions = {}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.service_name,
            "version": settings.version,
        }

    @app.post("/chat")
    async def chat(request: ChatRequest) -> ChatResponse:
        current_agent = app.state.agent
        if current_agent is None:
            raise HTTPException(status_code=503, detail="Agent is not configured")

        result = await current_agent.run(request.message)
        session_id, messages = _record_session_turn(
            sessions=app.state.sessions,
            requested_session_id=request.session_id,
            user_message=request.message,
            assistant_message=result.final_answer,
        )
        return ChatResponse(
            answer=result.final_answer,
            session_id=session_id,
            tool_name=result.tool_name,
            tool_arguments=result.tool_arguments,
            tool_result=result.tool_result,
            events=[event.as_dict() for event in result.events or []],
            messages=messages,
        )

    @app.post("/chat/stream")
    async def chat_stream(request: ChatRequest) -> StreamingResponse:
        current_agent = app.state.agent
        if current_agent is None:
            raise HTTPException(status_code=503, detail="Agent is not configured")

        result = await current_agent.run(request.message)
        return StreamingResponse(
            _iter_sse_events([event.as_dict() for event in result.events or []]),
            media_type="text/event-stream",
        )

    @app.get("/tools")
    async def tools() -> dict[str, list[dict[str, Any]]]:
        current_registry = app.state.registry
        if current_registry is None:
            raise HTTPException(status_code=503, detail="Tool registry is not configured")

        return {"tools": await current_registry.list_tools()}

    return app


async def _iter_sse_events(events: list[dict[str, Any]]) -> AsyncIterator[str]:
    for event in events:
        event_type = str(event["type"])
        data = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        yield f"event: {event_type}\ndata: {data}\n\n"


def _record_session_turn(
    sessions: dict[str, list[dict[str, str]]],
    requested_session_id: str | None,
    user_message: str,
    assistant_message: str,
) -> tuple[str, list[dict[str, str]]]:
    session_id = requested_session_id or uuid4().hex
    messages = sessions.setdefault(session_id, [])
    messages.extend(
        [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message},
        ]
    )
    return session_id, list(messages)


app = create_app(enable_runtime=True)
