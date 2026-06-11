from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from mcp_agent_platform.mcp.jsonrpc import make_error_response, make_success_response

ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler

    def as_mcp_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class BaseMCPServer:
    def __init__(self, name: str, version: str, tools: list[Tool] | None = None) -> None:
        self.name = name
        self.version = version
        self._tools = {tool.name: tool for tool in tools or []}

    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        message_id = message.get("id")
        params = message.get("params") or {}

        if method == "notifications/initialized" and "id" not in message:
            return None

        if method == "initialize":
            return make_success_response(message_id, self.initialize())

        if method == "tools/list":
            return make_success_response(message_id, self.list_tools())

        if method == "tools/call":
            result = await self.call_tool(params)
            return make_success_response(message_id, result)

        return make_error_response(message_id, -32601, "Method not found")

    def initialize(self) -> dict[str, Any]:
        return {
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
            "capabilities": {
                "tools": {},
            },
        }

    def list_tools(self) -> dict[str, Any]:
        return {"tools": [tool.as_mcp_schema() for tool in self._tools.values()]}

    async def call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}

        if tool_name not in self._tools:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}",
                    }
                ],
                "isError": True,
            }

        try:
            result = await self._tools[tool_name].handler(arguments)
        except Exception as exc:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(exc),
                    }
                ],
                "isError": True,
            }

        return {
            "content": [
                {
                    "type": "json",
                    "json": result,
                }
            ],
            "isError": False,
        }
