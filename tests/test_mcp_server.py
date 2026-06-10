import pytest
from mcp_agent_platform.mcp.server import BaseMCPServer, Tool


async def echo(arguments: dict) -> dict:
    return {"echo": arguments["text"]}


def make_server() -> BaseMCPServer:
    return BaseMCPServer(
        name="test-server",
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


@pytest.mark.anyio
async def test_initialize_returns_server_capabilities() -> None:
    response = await make_server().handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "serverInfo": {
                "name": "test-server",
                "version": "0.1.0",
            },
            "capabilities": {
                "tools": {},
            },
        },
    }


@pytest.mark.anyio
async def test_initialized_notification_returns_no_response() -> None:
    response = await make_server().handle_message(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
    )

    assert response is None


@pytest.mark.anyio
async def test_tools_list_returns_registered_tool_schema() -> None:
    response = await make_server().handle_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "tools": [
                {
                    "name": "echo",
                    "description": "Echo input text.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"],
                    },
                }
            ]
        },
    }


@pytest.mark.anyio
async def test_tools_call_invokes_registered_tool() -> None:
    response = await make_server().handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "echo",
                "arguments": {"text": "hello"},
            },
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "content": [
                {
                    "type": "json",
                    "json": {"echo": "hello"},
                }
            ],
            "isError": False,
        },
    }


@pytest.mark.anyio
async def test_unknown_method_returns_json_rpc_error() -> None:
    response = await make_server().handle_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "unknown/method",
            "params": {},
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 4,
        "error": {
            "code": -32601,
            "message": "Method not found",
        },
    }
