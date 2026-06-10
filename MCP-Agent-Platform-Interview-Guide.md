# MCP Agent Platform 面试与简历指南

## 1. 项目定位

这是一个 MCP-native 的 Agent 工具调用平台。它不是简单套壳聊天应用，而是从 MCP 协议、工具进程、Agent 决策循环和事件流展示这几层串起一个完整工程闭环。

推荐业务包装：

> 自动化技术调研助手：用户输入一个技术选型问题，系统自动搜索资料、分析差异、生成结构化 Markdown 调研报告，并展示 Agent 的思考链和工具调用过程。

## 2. 简历写法

### MVP 已实现时

可写：

- 从零实现 MCP JSON-RPC 2.0 子集与 `stdio` transport，支持 `initialize`、`tools/list`、`tools/call`。
- 设计 Tool Registry 管理 MCP Tool Server，支持工具发现、调用路由、超时和错误处理。
- 实现 ReAct Agent 循环，将 LLM 推理、工具调用和 Observation 反馈串成可追踪执行链。
- 基于 FastAPI 和 SSE 构建实时任务接口，在前端展示 Thought、Action、Observation、Final Answer。
- 以技术调研助手为场景，完成“搜索资料 -> 分析 -> 生成报告”的端到端演示。

### 后续增强完成后再写

仅在实际实现后使用：

- 支持 Streamable HTTP 远程 MCP transport。
- 引入 Redis/ChromaDB 实现短期和长期记忆。
- 实现多 Agent Plan-Execute 编排。
- 实现 RAG、代码执行、文件操作等多个 MCP Tool Server。

## 3. 30 秒介绍

我做了一个基于 MCP 协议的 Agent 工具调用平台，业务场景是自动化技术调研助手。核心不是调一个聊天 API，而是自己实现 MCP 的 JSON-RPC 通信、stdio 工具进程、Tool Registry 和 ReAct Agent 循环。用户提问后，Agent 会决定调用搜索工具、读取 Observation，再生成结构化报告；前端通过 SSE 实时展示 Thought、Action、Observation 的完整链路。

## 4. 2 分钟介绍

这个项目的目标是把 Agent 调用外部工具的过程工程化、协议化和可观察化。

底层我实现了 MCP 的核心子集，包括 JSON-RPC 2.0 消息、`initialize` 握手、`tools/list` 工具发现和 `tools/call` 工具调用。第一版优先支持 `stdio` transport，每个工具是独立子进程，Agent 通过 MCP Client 调用工具，工具日志写 stderr，协议消息走 stdout。

中间层是 Tool Registry，负责管理所有 MCP Server 连接、聚合工具 schema、按工具名路由调用，并处理超时和错误。

上层是 ReAct Agent。Agent 每一步先生成 Thought，再选择 Action 和 Action Input，执行工具后把结果作为 Observation 放回上下文，直到生成 Final Answer。为了避免死循环，我加了最大步数、重复 Action 检测和工具失败处理。

应用层用 FastAPI 暴露 `/chat`，通过 SSE 把每一步 Agent 事件推送到前端，所以演示时能清楚看到 Agent 为什么调用某个工具、工具返回了什么、最后如何汇总成报告。

## 5. 技术亮点

### 5.1 协议层亮点

- MCP 工具调用不绑定某个 LLM 厂商。
- 工具通过 JSON Schema 描述输入参数，便于 LLM 选择和校验。
- `stdio` transport 让本地工具天然适合做进程隔离。
- Tool Server 可独立开发、测试、替换。

### 5.2 Agent 层亮点

- ReAct 循环可观察：Thought、Action、Observation 分开记录。
- 工具调用失败不会直接崩溃，而是作为 Observation 反馈给 Agent。
- 通过最大步数和重复 Action 检测降低无限循环风险。
- 最终回答要求基于工具结果，而不是直接凭模型生成。

### 5.3 工程层亮点

- Tool Registry 解耦 Agent 和具体工具进程。
- SSE 让长任务有实时反馈，用户不需要等待黑盒结果。
- 协议层、Agent 层、Web 层职责清晰，方便测试。

## 6. 高频追问

### Q1：MCP 和 Function Calling 有什么区别？

Function Calling 通常是模型厂商 API 的一部分，工具 schema 和调用格式会跟厂商绑定。MCP 是独立协议，它把工具、资源、提示词等能力抽象成统一接口，并且 transport 和模型本身解耦。同一个 MCP Tool Server 可以被不同 MCP Client 使用，不必为每个模型厂商重写工具适配。

### Q2：为什么第一版只做 stdio？

`stdio` 最适合本地 MVP：实现简单、调试直接、进程隔离清楚，也符合 MCP 本地工具的典型使用方式。远程场景可以后续扩展 Streamable HTTP。前端的 SSE 只是应用层展示 Agent 事件，不把它混同为 MCP transport。

### Q3：Agent 幻觉怎么控制？

第一，工具参数用 schema 校验，避免乱传参数。第二，最终回答要求引用工具 Observation 的结果。第三，工具返回内容保留来源 URL 或元数据。第四，Agent 循环设置最大步数和重复 Action 检测，避免模型陷入无效循环。

### Q4：工具进程挂了怎么办？

MCP Client 层设置调用超时和子进程状态检查。Tool Registry 可以把失败工具标记为不可用，并把错误作为 Observation 返回给 Agent。这样 Agent 可以解释失败，或者在有替代工具时换工具继续执行。

### Q5：为什么不直接用 LangChain/CrewAI？

这个项目的目的不是最快搭一个 Agent demo，而是展示协议层和 Agent 运行机制。LangChain/CrewAI 更像上层框架；这个项目从 MCP 通信、工具注册、Agent loop、事件流可观察性开始做，能更清楚解释每一层怎么工作。

### Q6：多 Agent 怎么扩展？

MVP 先实现单 Agent ReAct 闭环。多 Agent 可以在上层加 Orchestrator：先把任务拆成 plan，再把 step 分配给 SearchAgent、AnalystAgent、WriterAgent。Agent 之间不直接通信，而是通过 Workspace 共享中间结果，由 Orchestrator 控制依赖顺序。

## 7. Demo 脚本

演示问题：

> 对比 Kafka 和 RocketMQ 在金融交易场景下的适用性，给出结论和引用来源。

流程：

1. 启动后端和前端。
2. 打开 Web UI，输入问题。
3. 展示 `agent_thought`：Agent 判断需要搜索资料。
4. 展示 `agent_action`：调用 `web_search`。
5. 展示 `agent_observation`：返回搜索结果列表。
6. 展示 Agent 汇总信息并生成 Final Answer。
7. 展示最终 Markdown 报告，重点看对比表格、结论和来源。

## 8. README 展示重点

README 应包含：

- 一句话项目定位。
- 架构图，优先用 Mermaid。
- 快速开始命令。
- MCP 协议子集说明。
- Agent 执行链路截图或 GIF。
- API 示例：`/chat`、`/tools`、`/health`。
- 当前能力和 Roadmap 分开写。

避免写：

- 尚未实现的 5 个 Tool Server。
- 尚未实现的长期记忆。
- 尚未实现的多 Agent 编排。
- “完全兼容 MCP 全规范”这类不可验证表述。

## 9. 面试官可能认可的点

- 你知道 MCP 不只是“工具调用”，还涉及 client/server、capability、transport 和 schema。
- 你能解释为什么协议消息和日志要分开 stdout/stderr。
- 你能解释 ReAct 为什么需要循环上限和失败反馈。
- 你能说明 SSE 是用户界面实时反馈，不是所有场景都等同于 MCP transport。
- 你没有把第一版做成大而全，而是先保证端到端闭环。

## 10. 后续 Roadmap 讲法

第一阶段完成本地 MCP 工具调用和单 Agent 闭环。

第二阶段扩展工具生态，包括 RAG、本地文档检索、文件操作和 API 调用。

第三阶段加入 Redis/ChromaDB 记忆系统和 Plan-Execute Orchestrator，把单 Agent 工具调用升级为多 Agent 协作。

第四阶段补充 Docker Compose、观测指标、Demo 视频和技术博客。
