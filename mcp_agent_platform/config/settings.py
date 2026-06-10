from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "mcp-agent-platform"
    version: str = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MCP_AGENT_",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
