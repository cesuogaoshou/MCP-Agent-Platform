from fastapi import FastAPI

from mcp_agent_platform.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="MCP Agent Platform", version=settings.version)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.service_name,
            "version": settings.version,
        }

    return app


app = create_app()
