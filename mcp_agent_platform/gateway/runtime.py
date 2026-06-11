import sys
from pathlib import Path

from mcp_agent_platform.agent.runner import ToolCallingAgent
from mcp_agent_platform.agent.tool_registry import RegisteredServer, ToolRegistry


def create_default_agent() -> tuple[ToolCallingAgent, ToolRegistry]:
    registry = create_default_registry()
    return ToolCallingAgent(registry), registry


def create_default_registry() -> ToolRegistry:
    project_root = Path(__file__).resolve().parents[2]
    base_env = {"PYTHONPATH": str(project_root)}

    return ToolRegistry(
        servers=[
            RegisteredServer(
                name="echo",
                command=[sys.executable, "-m", "mcp_agent_platform.tools.echo_server"],
                cwd=project_root,
                env=base_env,
            ),
            RegisteredServer(
                name="web-search",
                command=[sys.executable, "-m", "mcp_agent_platform.tools.web_search_server"],
                cwd=project_root,
                env=base_env,
            ),
        ]
    )
