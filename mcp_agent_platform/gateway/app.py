from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Protocol

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from mcp_agent_platform.config.settings import get_settings
from mcp_agent_platform.gateway.runtime import create_default_agent


class AgentLike(Protocol):
    async def run(self, user_input: str) -> Any:
        """Run an agent turn for a user input."""


class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be empty")
        return value


class ChatResponse(BaseModel):
    answer: str
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None


def create_app(agent: AgentLike | None = None, enable_runtime: bool = False) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        runtime_registry = None
        if enable_runtime and agent is None:
            runtime_agent, runtime_registry = create_default_agent()
            await runtime_registry.start()
            app.state.agent = runtime_agent
        else:
            app.state.agent = agent

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
        return ChatResponse(
            answer=result.final_answer,
            tool_name=result.tool_name,
            tool_arguments=result.tool_arguments,
            tool_result=result.tool_result,
        )

    return app


app = create_app(enable_runtime=True)
