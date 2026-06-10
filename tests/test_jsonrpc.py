import pytest
from mcp_agent_platform.mcp.jsonrpc import (
    JsonRpcError,
    decode_message,
    make_error_response,
    make_success_response,
)


def test_decode_request_message() -> None:
    message = decode_message('{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}')

    assert message == {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }


def test_decode_notification_without_id() -> None:
    message = decode_message('{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}')

    assert "id" not in message
    assert message["method"] == "notifications/initialized"


def test_decode_invalid_json_raises_parse_error() -> None:
    with pytest.raises(JsonRpcError) as error:
        decode_message('{"jsonrpc":"2.0",')

    assert error.value.code == -32700
    assert error.value.message == "Parse error"


def test_make_success_response_preserves_id() -> None:
    response = make_success_response(1, {"tools": []})

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": []},
    }


def test_make_error_response_uses_standard_shape() -> None:
    response = make_error_response(1, -32601, "Method not found")

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32601,
            "message": "Method not found",
        },
    }
