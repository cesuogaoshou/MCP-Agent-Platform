from typing import Any, Protocol

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from mcp_agent_platform.config.settings import get_settings


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


def create_app(agent: AgentLike | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="MCP Agent Platform", version=settings.version)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.service_name,
            "version": settings.version,
        }

    @app.post("/chat")
    async def chat(request: ChatRequest) -> ChatResponse:
        if agent is None:
            raise HTTPException(status_code=503, detail="Agent is not configured")

        result = await agent.run(request.message)
        return ChatResponse(
            answer=result.final_answer,
            tool_name=result.tool_name,
            tool_arguments=result.tool_arguments,
            tool_result=result.tool_result,
        )

    return app


app = create_app()
