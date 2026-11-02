# 当前源码审查与提交范围

2026-11-02：旧含看板的拟暂存清单作废。使用 `git diff --name-status` 和 `git status --short` 审查当前精简版；删除文件清单见 `artifacts/project-removal/deleted-files.json`。

必须纳入：精简后的 backend/frontend 源码、个人时间线重命名、保留功能测试、requirements/package、当前部署/设计文档、受控脚本。

未跟踪的 AGENTS.md、设计文档、设计素材和本地验收脚本为用户已有工作，已经备份。逐项审查，不用 `git add .`。

绝不暂存：真实 `.env`、数据库及 sidecar、uploads、虚拟环境、node_modules、dist、源码备份包、凭据、私有业务素材。保持现有忽略保护。

不自动暂存、Commit、Push，也不清理 Git 历史。候选制品基于当前工作树，须记录 SHA256，不能只用旧 HEAD 声称包含本轮修改。
