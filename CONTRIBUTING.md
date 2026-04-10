# Contributing to MatterSim-WebUI  
# 向 MatterSim-WebUI 贡献代码

Thank you for your interest in contributing to MatterSim-WebUI!  
欢迎你为 MatterSim-WebUI 做出贡献！

We welcome bug reports, feature requests, documentation improvements, and code contributions.  
我们欢迎 Bug 反馈、功能建议、文档改进和代码贡献。

---

## Reporting Issues  
## 报告问题

When reporting a bug, please include:  
报告 Bug 时请提供：

- Clear description of the issue  
  问题的清晰描述  
- Steps to reproduce  
  复现步骤  
- Expected vs actual behavior  
  预期行为与实际行为  
- Screenshots or logs (if applicable)  
  截图或日志（如有）  
- Environment info (OS, Python, MatterSim version)  
  环境信息（系统、Python、MatterSim 版本）

Submit issues here:  
在此提交 Issue：  
https://github.com/hfzxlzy/MatterSim-WebUI/issues

---

## Requesting Features  
## 功能请求

Please describe:  
请描述：

- The problem you want to solve  
  你想解决的问题  
- Why it is useful  
  为什么有用  
- Possible implementation ideas (optional)  
  实现思路（可选）

---

## Submitting Pull Requests  
## 提交 Pull Request

1. Fork the repository  
   Fork 本仓库  
2. Create a new branch  
   创建新分支  
   ```
   git checkout -b feature/my-feature
   ```
3. Make your changes  
   修改代码  
4. Ensure code is clean and readable  
   保持代码整洁可读  
5. Commit with a clear message  
   使用清晰的 commit 信息  
6. Open a Pull Request  
   提交 PR

PR 应包含：  
- 修改说明  
- 相关 Issue（如有）  
- UI 改动的截图（如有）

---

## Project Structure Overview  
## 项目结构概览

```
webui/
  core/          # 环境、系统监控、历史记录
  inference/     # 推理链路、插件、UI
  training/      # 训练 UI、预设、命令构建
  ase_tools/     # 基于 ASE 的结构工具
```

---

## Code Style  
## 代码风格

- Follow Python best practices  
  遵循 Python 最佳实践  
- Keep functions small and modular  
  函数保持简洁、模块化  
- Avoid hard-coded paths  
  避免硬编码路径  
- Use clear variable names  
  使用清晰的变量名

---

## Thank You  
## 感谢你的贡献

Your contributions help improve MatterSim-WebUI for everyone!  
你的贡献将让 MatterSim-WebUI 更加完善！