# MCP Agent Platform 落地路线图

## 1. 总体原则

这个项目先做一个能跑通的最小闭环，不追求完整平台化。第一版只需要证明三件事：

1. MCP 工具可以被 Agent 调用。
2. Agent 可以基于工具结果生成回答。
3. 用户可以在页面上看到完整执行过程。

第一版完成后，再补充长期记忆、多工具、多 Agent、Docker 等增强能力。

## 2. 阶段总览

| 阶段 | 目标 | 完成标志 |
| --- | --- | --- |
| 阶段 0：项目骨架 | 把空目录变成可运行的 Python Web 工程 | 服务能启动，测试命令能跑 |
| 阶段 1：MCP 协议闭环 | 跑通本地 Tool Server 的工具发现和工具调用 | 能通过 stdio 调用 `tools/list` 和 `tools/call` |
| 阶段 2：单工具可用 | 实现一个真实可用的 `web_search` 工具 | 工具返回搜索结果，失败时有清晰错误 |
| 阶段 3：Agent 闭环 | Agent 能决定调用工具并基于结果回答 | 产生 Thought -> Action -> Observation -> Answer |
| 阶段 4：网关与页面 | 用户能通过浏览器使用系统 | 页面实时展示执行过程和最终回答 |
| 阶段 5：收尾展示 | 项目具备可交付、可演示、可写简历的形态 | README、截图、Demo 流程完整 |
| 阶段 6：可选增强 | 在 MVP 稳定后扩展平台能力 | 按需增加 RAG、记忆、多 Agent、Docker |

## 3. 阶段 0：项目骨架

### 目标

建立最小工程结构，让后续功能都能在清晰目录下开发、测试和运行。

### 小任务

| 编号 | 任务 | 产出 |
| --- | --- | --- |
| 0.1 | 初始化 Python 包目录 | `mcp_agent_platform/`、`tests/` 基础目录 |
| 0.2 | 建立依赖文件 | `requirements.txt` 或 `pyproject.toml` |
| 0.3 | 建立配置模板 | `.env.example`，包含 LLM、搜索、Agent 步数等配置项 |
| 0.4 | 建立 FastAPI 空应用 | `/health` 返回基础状态 |
| 0.5 | 建立测试入口 | `pytest` 可以执行，至少有一个健康检查测试 |
| 0.6 | 建立 README 骨架 | 说明项目目标、启动方式占位、当前阶段 |

### 验收成果

- 可以安装依赖。
- 可以启动一个空的 FastAPI 服务。
- `GET /health` 返回 `{"status": "ok"}`。
- `pytest` 能执行并通过最小测试。

## 4. 阶段 1：MCP 协议闭环

### 目标

实现项目最核心的协议层，先不接真实业务工具，只保证 MCP Client 和 MCP Server 能通过 stdio 正常通信。

### 小任务

| 编号 | 任务 | 产出 |
| --- | --- | --- |
| 1.1 | 定义 JSON-RPC 数据结构 | Request、Response、Error、Notification 类型 |
| 1.2 | 实现 JSON-RPC 编解码 | 能解析合法消息，能返回标准错误 |
| 1.3 | 实现 MCP Server 基类 | 支持 `initialize`、`notifications/initialized`、`tools/list`、`tools/call` |
| 1.4 | 实现 stdio transport | 每行一个 JSON 消息，日志只写 stderr |
| 1.5 | 实现 Echo Tool Server | 用于验证协议，不依赖外部服务 |
| 1.6 | 实现 MCP Client | 能启动子进程、握手、列工具、调用工具 |
| 1.7 | 补充协议测试 | 覆盖成功、错误、notification、未知 method |

### 验收成果

- 命令行或测试中可以启动 Echo MCP Server。
- Client 能完成 `initialize`。
- Client 能调用 `tools/list` 获取工具列表。
- Client 能调用 `tools/call` 并收到 Echo 结果。
- 协议错误能返回标准 JSON-RPC error。

## 5. 阶段 2：单工具可用

### 目标

把 Echo 工具替换或扩展为一个真实有用的 `web_search` 工具，让 Agent 后续有可调用的信息来源。

### 小任务

| 编号 | 任务 | 产出 |
| --- | --- | --- |
| 2.1 | 定义 Tool 抽象 | 工具名、描述、inputSchema、执行函数 |
| 2.2 | 定义 SearchProvider 接口 | 屏蔽 DuckDuckGo、SerpAPI、Bing 的差异 |
| 2.3 | 实现一个默认搜索 provider | 优先使用低配置成本方案 |
| 2.4 | 实现 `web_search` MCP Server | 暴露 `query`、`top_k`、`language` 参数 |
| 2.5 | 加入参数校验 | 缺少 query、top_k 非法时返回清晰错误 |
| 2.6 | 加入超时处理 | 搜索超时不会卡死 MCP 调用 |
| 2.7 | 补充工具测试 | 覆盖正常结果、空结果、参数错误、超时错误 |

### 验收成果

- `tools/list` 返回 `web_search` 及其 JSON Schema。
- `tools/call` 能返回 `title`、`url`、`snippet` 结构的搜索结果。
- 外部搜索失败时返回可解释错误，不导致服务崩溃。
- 搜索 provider 可以通过配置切换或替换。

## 6. 阶段 3：Agent 闭环

### 目标

实现最小 ReAct Agent，让模型能够看到工具列表，选择工具，读取 Observation，生成最终回答。

### 小任务

| 编号 | 任务 | 产出 |
| --- | --- | --- |
| 3.1 | 定义 Agent 事件模型 | Thought、Action、Observation、Answer、Error |
| 3.2 | 实现 Tool Registry | 聚合工具列表，按工具名路由调用 |
| 3.3 | 设计 ReAct Prompt | 约束输出格式和工具调用格式 |
| 3.4 | 实现 LLM Client 包装 | 统一模型调用、超时、错误处理 |
| 3.5 | 实现 ReAct 循环 | 支持最多 N 步工具调用 |
| 3.6 | 实现输出解析 | 解析 Action、Action Input、Final Answer |
| 3.7 | 实现循环保护 | 最大步数、重复 Action 检测 |
| 3.8 | 补充 Agent 测试 | 使用 fake LLM 验证工具调用链路 |

### 验收成果

- Agent 能看到 `web_search` 工具。
- 输入一个技术问题时，Agent 至少能完成一轮工具调用。
- 系统能记录并输出 Thought、Action、Observation、Final Answer。
- LLM 输出格式异常时，有一次修正或清晰失败。
- 不依赖真实 LLM 的单元测试可以验证主流程。

## 7. 阶段 4：网关与页面

### 目标

让项目从命令行验证升级为用户可交互的 Web Demo。

### 小任务

| 编号 | 任务 | 产出 |
| --- | --- | --- |
| 4.1 | 实现 `/tools` | 返回 Tool Registry 中的工具 |
| 4.2 | 实现 `/chat` | 接收用户消息并启动 Agent |
| 4.3 | 实现 SSE 事件流 | 持续推送 Agent 事件 |
| 4.4 | 实现最小会话记忆 | 同一 session 保存最近若干轮消息 |
| 4.5 | 创建 Web UI | 输入框、发送按钮、消息区域 |
| 4.6 | 展示 Agent 事件 | 前端展示 Thought、Action、Observation |
| 4.7 | 展示最终报告 | Markdown 或纯文本展示最终回答 |
| 4.8 | 补充接口测试 | 覆盖 `/health`、`/tools`、`/chat` 基础行为 |

### 验收成果

- 打开浏览器能看到页面。
- 用户输入问题后，页面能实时出现 Agent 执行过程。
- 最终回答能展示在页面中。
- `/tools` 和页面展示的工具信息一致。
- 后端错误能在页面中显示为可读错误。

## 8. 阶段 5：收尾展示

### 目标

把 MVP 打磨成可交付项目，便于复盘、录屏、写简历。

### 小任务

| 编号 | 任务 | 产出 |
| --- | --- | --- |
| 5.1 | 整理 README | 项目定位、架构图、启动步骤、API 示例 |
| 5.2 | 补充 Demo 问题 | 固定 2-3 个稳定演示问题 |
| 5.3 | 补充截图或 GIF | 页面、思考链、最终报告 |
| 5.4 | 整理异常说明 | 没有 API Key、搜索失败、LLM 失败时如何处理 |
| 5.5 | 清理配置 | `.env.example` 和 README 保持一致 |
| 5.6 | 最终回归测试 | 从安装依赖到完成一次 Demo 全流程验证 |

### 验收成果

- README 能指导别人启动项目。
- Demo 可以稳定复现。
- 面试指南中的 MVP 描述与实际能力一致。
- 项目没有明显的“文档写了但代码没有”的承诺。

## 9. 阶段 6：可选增强

这些功能不进入第一版 MVP，只有当前五个阶段稳定后再做。

| 优先级 | 增强项 | 价值 | 验收成果 |
| --- | --- | --- | --- |
| P1 | Dockerfile / Docker Compose | 降低启动成本 | 一条命令启动后端和前端 |
| P1 | RAGQuery Tool | 支持本地文档调研 | 能索引 Markdown 并检索相关片段 |
| P2 | Redis 短期记忆 | 支持更稳定的多轮会话 | 重启前保持会话上下文 |
| P2 | ChromaDB 长期记忆 | 支持跨会话检索 | 新会话能召回历史摘要 |
| P2 | Plan-Execute Orchestrator | 支持复杂任务拆解 | 任务能拆成多个 step 顺序执行 |
| P3 | 多 Agent 角色 | 展示协作能力 | Search/Analyst/Writer 分工明确 |
| P3 | Streamable HTTP transport | 支持远程 MCP Server | 远程工具可被 Registry 注册和调用 |

## 10. 推荐执行顺序

1. 先完成阶段 0 和阶段 1，不接 LLM，不接搜索，先证明协议层能跑。
2. 再完成阶段 2，让工具调用有真实业务价值。
3. 再完成阶段 3，接入 Agent。
4. 最后完成阶段 4 和阶段 5，把命令行能力包装成可演示产品。
5. 阶段 6 只按需要挑选，不要一次性全做。

## 11. 第一版最终验收清单

- [ ] 本地可以启动后端服务。
- [ ] `GET /health` 返回正常。
- [ ] `GET /tools` 能看到 `web_search`。
- [ ] MCP Client 能通过 stdio 调用 `web_search`。
- [ ] Agent 能完成 Thought -> Action -> Observation -> Final Answer。
- [ ] `/chat` 能以 SSE 返回 Agent 过程。
- [ ] Web 页面能输入问题并展示结果。
- [ ] README 能让别人按步骤跑起来。
- [ ] 面试指南中的 MVP 表述与实际能力一致。
