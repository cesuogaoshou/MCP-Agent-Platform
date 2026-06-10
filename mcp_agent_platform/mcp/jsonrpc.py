import json
from dataclasses import dataclass
from typing import Any

JSONRPC_VERSION = "2.0"


@dataclass(frozen=True)
class JsonRpcError(Exception):
    code: int
    message: str
    data: Any | None = None


def decode_message(raw_message: str) -> dict[str, Any]:
    try:
        message = json.loads(raw_message)
    except json.JSONDecodeError as exc:
        raise JsonRpcError(-32700, "Parse error") from exc

    if not isinstance(message, dict):
        raise JsonRpcError(-32600, "Invalid Request")

    if message.get("jsonrpc") != JSONRPC_VERSION:
        raise JsonRpcError(-32600, "Invalid Request")

    if "method" not in message and "result" not in message and "error" not in message:
        raise JsonRpcError(-32600, "Invalid Request")

    return message


def make_success_response(message_id: str | int | None, result: Any) -> dict[str, Any]:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": message_id,
        "result": result,
    }


def make_error_response(
    message_id: str | int | None,
    code: int,
    message: str,
    data: Any | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if data is not None:
        error["data"] = data

    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": message_id,
        "error": error,
    }
