# MCP Agent Platform

MCP-native Agent 工具调用平台。当前项目处于设计和仓库初始化阶段，目标是先实现一个简单可运行的个人项目版本：本地 MCP 工具调用、ReAct Agent、FastAPI 网关和最小 Web 演示。

## 文档

- [开发规格](MCP-Agent-Platform-Dev-Spec.md)
- [落地路线图](MCP-Agent-Platform-Roadmap.md)
- [面试与简历指南](MCP-Agent-Platform-Interview-Guide.md)
- [文档入口](MCP-Agent-Platform-Spec.md)

## 当前阶段

阶段 0：项目骨架准备。

暂未进入代码实现。下一步会先完成最小 Python/FastAPI 工程初始化，再逐步实现 MCP 协议闭环。

## MVP 目标

1. MCP Client 通过 `stdio` 调用本地 Tool Server。
2. ReAct Agent 能基于工具结果生成回答。
3. FastAPI + Web UI 能展示 Agent 执行过程。

## GitHub 准备

本仓库建议使用 `main` 分支。首次上传前需要：

1. 在 GitHub 创建空仓库。
2. 配置本地 git 提交身份。
3. 添加远程地址并推送。

```powershell
git config user.name "Your Name"
git config user.email "you@example.com"
git add .
git commit -m "docs: initialize project documentation"
git remote add origin <your-github-repo-url>
git push -u origin main
```
