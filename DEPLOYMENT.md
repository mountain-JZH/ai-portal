# AI Portal 精简版部署指南

2026-11-02。新候选仅允许不含服务端项目看板的版本。入口保持公网 IP + HTTP 80，域名和 HTTPS 不作为本轮阻断项。所有生产切换、数据库写入、服务重启与删除需人工批准。

配套：[ECS 审计、发布及回滚](docs/releases/ecs-deployment-runbook.md)、[验收清单](docs/releases/release-acceptance-checklist.md)、[精简报告](docs/releases/slim-release-report.md)。

## 本地验证

```powershell
backend/.venv/Scripts/python.exe deploy/scripts/run_backend_tests.py
cd frontend
npm.cmd test
$env:VITE_API_BASE_URL='/api'
npm.cmd run build
```

后端集成套件各自持有模块级 FastAPI、数据库和 uploads，必须逐套独立进程运行。直接 unittest discover 会复用已缓存应用和失效临时路径，不是有效的整套运行方式。测试只使用临时虚构数据。

## 发布约束

1. 先核实 ECS 实际 unit/drop-in、cwd、Python/venv、Nginx root/upstream、数据库和上传目录。不得根据目录名称判断用途；审计脚本不导入 main.py。
2. 不运行未审查的 `/opt/ai-portal/update.sh`。只读审计后，针对实际脚本形成具体替换 diff，再批准执行。
3. 固定精简候选制品 SHA256；工作树修改没有提交时，不将旧 HEAD 冒充本轮候选。未经授权不 push GitHub。
4. 保留当前稳定源码、dist、venv 原路径和私有配置，使用独立新 venv。Python 与 Node 版本以 requirements/package 及实际安装结果为准。
5. 批准维护窗口后，备份最新生产 SQLite（SQLite Backup API）、uploads、代码/构建/配置。验证备份可打开及校验和。不要直接复制活跃 WAL 数据库作为一致备份。
6. 不覆盖生产 SQLite、uploads、`.env` 或 SESSION_SECRET；不修改原管理员密码。不执行 DROP TABLE。旧项目表/历史权限字段保留，新库不再初始化它们。
7. 本轮不重复大规模生产副本迁移演练；核对必要 schema 差异、管理员关联冲突即可。`main.py` 启动会调用幂等初始化，生产启动属于可能写库的获批操作。
8. 只发布精简版后端和同源前端 dist；不发布本地数据库、用户素材、设计实验 HTML 或密钥。Dify 公开 Embed URL 应与批准的生产值一致，不能用本地值盲目替换。
9. 若使用版本化候选根：`upload_api.py` 从源码父目录计算 uploads。必须在候选根建立指向 `/opt/ai-portal/uploads` 的已批准链接并验证真实路径；DB 使用确认的绝对路径。不能只改 systemd cwd 后直接启动。
10. Nginx 的 `/api/`、`/uploads/`、`/tools/qstart` 都进入 FastAPI；附件和静态工具不能公开 alias 绕过员工认证。Uvicorn 仅 loopback，upstream 端口一致，不用 --reload。
11. 修改 Nginx 先 nginx -t，再按批准流程 reload；systemd drop-in 的 ExecStart 覆盖需先清空旧值，保留实际有效安全设置。具体差异在现场审计后形成。
12. 验收管理员及员工登录、首页、新闻/内容、工具、资源交流、Dify、后台及退出失效。Exchange 沿用现有开关，不擅自开启或关闭。
13. 切换验收后再提出第二批旧产物删除清单，保留必要稳定版和重要备份。

## 身份与 HTTP

原 `admins` ID 和 Argon2 哈希继续使用。管理员以原账号和密码统一登录；同名未关联员工冲突必须核实，不能自动合并或重置密码。`set_admin_password.py` 仅用于另行批准的账号恢复，不作为发布步骤。

当前公网 HTTP 无传输加密，账号密码及会话可能被监听/劫持。保留 HttpOnly、SameSite、CSRF、限流及现有网络保护；Secure Cookie 与实际协议匹配，若现场已有 TLS/网关保护，不擅自降低。未来可独立安排 HTTPS。
