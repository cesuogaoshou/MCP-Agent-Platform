import asyncio
from typing import Any

from mcp_agent_platform.mcp.server import BaseMCPServer, Tool
from mcp_agent_platform.mcp.transport.stdio import run_stdio_server


async def echo(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"echo": arguments["text"]}


def create_server() -> BaseMCPServer:
    return BaseMCPServer(
        name="echo-server",
        version="0.1.0",
        tools=[
            Tool(
                name="echo",
                description="Echo input text.",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                handler=echo,
            )
        ],
    )


def main() -> None:
    asyncio.run(run_stdio_server(create_server()))


if __name__ == "__main__":
    main()
