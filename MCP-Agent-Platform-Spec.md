# MCP Agent Platform 文档入口

本目录当前处于项目设计阶段，尚未初始化代码工程。原始规格书已经拆分为两份更清晰的文档：

- [MCP-Agent-Platform-Dev-Spec.md](MCP-Agent-Platform-Dev-Spec.md)：面向开发落地，定义 MVP 范围、架构、模块边界、API、目录结构、实施计划和验收标准。
- [MCP-Agent-Platform-Roadmap.md](MCP-Agent-Platform-Roadmap.md)：面向项目执行，按大阶段拆分小任务，并定义每个阶段的验收成果。
- [MCP-Agent-Platform-Interview-Guide.md](MCP-Agent-Platform-Interview-Guide.md)：面向简历和面试展示，整理项目亮点、讲解话术、技术追问、README/Demo 重点。

维护原则：

1. 开发规格以可落地为准，先保证第一版能跑通端到端闭环。
2. 面试指南只能讲开发规格中已经实现或明确规划的能力，避免过度承诺。
3. MCP 协议实现优先覆盖 `stdio` transport；远程 MCP transport 可按当前规范扩展为 Streamable HTTP。前端实时展示使用应用层 SSE，不等同于 MCP transport。
