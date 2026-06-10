import uvicorn


def main() -> None:
    uvicorn.run(
        "mcp_agent_platform.gateway.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
