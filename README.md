# MCP Agent Platform

MCP-native Agent 工具调用平台。当前目标是先实现一个简单可运行的个人版本：本地 MCP 工具调用、简单 Agent 执行层、FastAPI 网关和后续最小 Web 演示。

## 文档

详细规划文档放在本地 `docs/` 目录中，用于个人开发和面试准备。该目录已加入 `.gitignore`，不会上传到 GitHub。

## 当前状态

当前已经跑通最小后端闭环：

- MCP JSON-RPC 基础封装
- MCP stdio client/server 通信
- `echo` 本地 MCP Tool Server
- `web_search` 本地 MCP Tool Server
- `ToolRegistry` 工具发现与路由
- `ToolCallingAgent` 简单命令式工具调用
- FastAPI `/health` 与 `/chat` 接口
- pytest + Ruff 基础质量检查

## MVP 目标

1. MCP Client 通过 `stdio` 调用本地 Tool Server。
2. Agent 能基于工具结果生成回答。
3. FastAPI + Web UI 能展示 Agent 执行过程。

## 最小架构

```text
Browser / curl
    |
FastAPI Gateway
    |-- /health
    |-- /tools
    |-- /chat
    |-- /chat/stream
    |
ToolCallingAgent
    |
ToolRegistry
    |
MCP stdio Tool Servers
    |-- echo
    |-- web_search
```

## 本地开发

创建虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

运行测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

运行 Ruff 检查：

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

启动开发服务：

```powershell
.\.venv\Scripts\python.exe -m mcp_agent_platform.gateway
```

打开 Web UI：

```text
http://127.0.0.1:8000/
```

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

查看已注册工具：

```powershell
curl http://127.0.0.1:8000/tools
```

调用 Agent：

```powershell
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"/echo hello\"}"
```

以 SSE 格式获取 Agent 执行事件：

```powershell
curl -N -X POST http://127.0.0.1:8000/chat/stream `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"/echo hello\"}"
```

离线测试搜索工具时，可以启用 fake provider：

```powershell
$env:MCP_AGENT_SEARCH_PROVIDER = "fake"
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"/search mcp protocol\"}"
Remove-Item Env:\MCP_AGENT_SEARCH_PROVIDER
```

当前 Agent 支持的最小命令：

- `/echo <text>`：调用 `echo` 工具。
- `/search <query>`：调用 `web_search` 工具。

`/chat` 响应会返回 `answer`、工具调用信息和 `events`。`events` 当前包含
`action`、`observation`、`answer`，后续 Web UI 和 SSE 会基于这些事件展示执行过程。

`/chat` 还会返回 `session_id` 和当前会话的 `messages`。后续请求带上同一个
`session_id`，后端会在进程内保留最近的用户和助手消息，便于做最小多轮会话演示。

MCP stdio 协议自检：

```powershell
@'
import asyncio
import sys

from mcp_agent_platform.mcp.client import StdioMCPClient


async def main():
    client = StdioMCPClient([sys.executable, "-m", "mcp_agent_platform.tools.echo_server"])
    await client.start()
    try:
        print(await client.request("tools/list", {}))
        print(await client.request("tools/call", {"name": "echo", "arguments": {"text": "hello"}}))
    finally:
        await client.close()


asyncio.run(main())
'@ | .\.venv\Scripts\python.exe -
```

Web search MCP Server 自检（使用 fake provider，不访问网络）：

```powershell
$env:MCP_AGENT_SEARCH_PROVIDER = "fake"
@'
import asyncio
import sys

from mcp_agent_platform.mcp.client import StdioMCPClient


async def main():
    client = StdioMCPClient([sys.executable, "-m", "mcp_agent_platform.tools.web_search_server"])
    await client.start()
    try:
        print(await client.request("tools/list", {}))
        print(await client.request("tools/call", {"name": "web_search", "arguments": {"query": "mcp protocol", "top_k": 1}}))
    finally:
        await client.close()


asyncio.run(main())
'@ | .\.venv\Scripts\python.exe -
Remove-Item Env:\MCP_AGENT_SEARCH_PROVIDER
```

## Demo 流程

推荐先用离线搜索模式演示，避免外部网络影响效果：

```powershell
$env:MCP_AGENT_SEARCH_PROVIDER = "fake"
.\.venv\Scripts\python.exe -m mcp_agent_platform.gateway
```

然后打开：

```text
http://127.0.0.1:8000/
```

稳定演示问题：

```text
/echo hello
/search mcp protocol
/search agent tool calling
```

可观察到的效果：

- 左侧展示 `echo`、`web_search` 工具。
- 中间展示用户输入和助手回答。
- 右侧展示 Agent events，包括 `action`、`observation`、`answer`。
- 同一页面连续提问会复用 `session_id`，消息会保留在当前会话中。

演示结束后关闭服务，并清理环境变量：

```powershell
Remove-Item Env:\MCP_AGENT_SEARCH_PROVIDER
```

## 当前限制

- Agent 目前是命令式最小实现，不是真正 LLM ReAct。
- `/chat/stream` 当前是把一次 Agent 运行后的事件按 SSE 输出，不是逐 token 流式生成。
- 会话记忆是进程内存储，服务重启后会丢失。
- `web_search` 默认 provider 依赖外部网络；离线演示建议使用 fake provider。
