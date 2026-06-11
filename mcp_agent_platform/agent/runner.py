import json
from dataclasses import dataclass
from typing import Any, Protocol


class ToolRegistryLike(Protocol):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a registered tool by name."""


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class AgentRunResult:
    user_input: str
    final_answer: str
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None


class CommandPlanner:
    def plan(self, user_input: str) -> ToolCall | None:
        text = user_input.strip()

        if text.startswith("/echo "):
            return ToolCall(name="echo", arguments={"text": text.removeprefix("/echo ").strip()})

        if text.startswith("/search "):
            return ToolCall(
                name="web_search",
                arguments={"query": text.removeprefix("/search ").strip()},
            )

        return None


class ToolCallingAgent:
    def __init__(
        self,
        registry: ToolRegistryLike,
        planner: CommandPlanner | None = None,
    ) -> None:
        self._registry = registry
        self._planner = planner or CommandPlanner()

    async def run(self, user_input: str) -> AgentRunResult:
        tool_call = self._planner.plan(user_input)
        if tool_call is None:
            return AgentRunResult(
                user_input=user_input,
                final_answer="No matching tool command found.",
            )

        tool_result = await self._registry.call_tool(tool_call.name, tool_call.arguments)
        return AgentRunResult(
            user_input=user_input,
            final_answer=_tool_result_to_text(tool_result),
            tool_name=tool_call.name,
            tool_arguments=tool_call.arguments,
            tool_result=tool_result,
        )


def _tool_result_to_text(tool_result: dict[str, Any]) -> str:
    content = tool_result.get("content") or []
    if not content:
        return ""

    first_item = content[0]
    if first_item.get("type") == "json":
        return json.dumps(first_item.get("json"), ensure_ascii=False)

    return str(first_item.get("text", ""))
