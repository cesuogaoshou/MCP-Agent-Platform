# MCP Agent Platform

MCP-native Agent 工具调用平台。项目目标是先实现一个简单可运行的个人版本：本地 MCP 工具调用、ReAct Agent、FastAPI 网关和最小 Web 演示。

## 文档

详细规划文档放在本地 `docs/` 目录中，用于个人开发和面试准备。该目录已加入 `.gitignore`，不会上传到 GitHub。

## 当前阶段

阶段 0：项目骨架初始化。

当前已具备最小 Python/FastAPI 工程骨架：

- `mcp_agent_platform/` Python 包
- FastAPI 应用工厂
- `/health` 健康检查接口
- `.env.example` 配置模板
- pytest 测试入口

下一步进入阶段 1：MCP JSON-RPC 与 stdio 协议闭环。

## MVP 目标

1. MCP Client 通过 `stdio` 调用本地 Tool Server。
2. ReAct Agent 能基于工具结果生成回答。
3. FastAPI + Web UI 能展示 Agent 执行过程。

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

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

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
