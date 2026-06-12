# MCP Agent Platform

一个 MCP-native 的 Agent 工具调用平台 MVP。当前目标不是做复杂平台，而是先跑通本地 MCP 工具调用、命令式 Agent 执行、FastAPI 网关和最小 Web UI 的完整闭环。

## 当前状态

当前已经实现：

- MCP JSON-RPC 2.0 最小子集。
- MCP `stdio` client/server 通信。
- `echo` 本地 MCP Tool Server。
- `web_search` 本地 MCP Tool Server。
- `ToolRegistry` 工具发现与路由。
- `ToolCallingAgent` 命令式工具调用。
- FastAPI `/health`、`/tools`、`/chat`、`/chat/stream`。
- 进程内 `session_id` 会话记忆。
- 最小 Web UI。
- Demo smoke check。
- pytest + Ruff 基础质量检查。

当前 Agent 不是完整 LLM ReAct。它是一个确定性的命令式最小 Agent，用来先验证 MCP 工具调用和事件展示链路。

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

创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

运行测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

运行 Ruff：

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

启动服务：

```powershell
.\.venv\Scripts\python.exe -m mcp_agent_platform.gateway
```

打开 Web UI：

```text
http://127.0.0.1:8000/
```

## API 示例

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

查看工具：

```powershell
curl http://127.0.0.1:8000/tools
```

调用 Agent：

```powershell
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"/echo hello\"}"
```

获取 Agent 事件流：

```powershell
curl -N -X POST http://127.0.0.1:8000/chat/stream `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"/echo hello\"}"
```

## Demo 流程

推荐用 fake search provider 演示，避免外部网络影响：

```powershell
$env:MCP_AGENT_SEARCH_PROVIDER = "fake"
.\.venv\Scripts\python.exe -m mcp_agent_platform.gateway
```

然后打开：

```text
http://127.0.0.1:8000/
```

稳定演示输入：

```text
/echo hello
/search mcp protocol
/search agent tool calling
```

可观察到：

- 左侧展示 `echo`、`web_search` 工具。
- 中间展示用户输入和助手回答。
- 右侧展示 Agent events：`action`、`observation`、`answer`。
- 同一页面连续提问会复用 `session_id`。

演示结束后清理环境变量：

```powershell
Remove-Item Env:\MCP_AGENT_SEARCH_PROVIDER
```

## Demo Smoke Check

服务启动后，可以在另一个 PowerShell 窗口运行验收脚本：

```powershell
.\.venv\Scripts\python.exe -m mcp_agent_platform.gateway.smoke
```

如果服务启动时启用了 fake search provider，也可以检查搜索链路：

```powershell
.\.venv\Scripts\python.exe -m mcp_agent_platform.gateway.smoke --include-search
```

脚本会检查：

- `GET /health`
- `GET /tools`
- `POST /chat` with `/echo hello`
- 可选：`POST /chat` with `/search mcp protocol`

## 当前限制

- Agent 当前是命令式最小实现，不是真正 LLM ReAct。
- `/chat/stream` 当前是把一次 Agent 运行后的事件按 SSE 输出，不是 token 级实时生成。
- 会话记忆是进程内存储，服务重启后会丢失。
- `web_search` 默认 provider 依赖外部网络；离线演示建议使用 fake provider。
- 暂未提供 Docker Compose。

## 文档

详细规划文档放在本地 `docs/` 目录中，用于个人开发和面试准备。该目录已加入 `.gitignore`，不会上传到 GitHub。
