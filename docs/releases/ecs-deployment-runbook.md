# ECS 精简版审计、清理、发布与回滚

2026-11-02。当前尚无 SSH 连接证据。已知目录来自任务描述，不能视作已确认用途。此手册不授权生产动作；旧含看板的候选不再部署。

## 只读审计

最少执行一条命令（在本机 Bash 中，替换真实 SSH 目标；服务名有差异时替换）：

```bash
ssh <实际SSH目标> 'sudo -n python3 - --service ai-portal.service' < deploy/scripts/audit_ecs_readonly.py
```

脚本不落盘、不导入应用、不执行更新、不打印密钥或密码；读取运行 PID/cwd/exe、允许的非秘密环境项、服务配置路径、Nginx 结构、目录体积/链接、Git HEAD、数据库只读检查和记录数量、配置引用及更新脚本危险操作行号。若 sudo -n 不可用，由操作人在已有 SSH 会话内以可读所需文件的身份运行同一脚本，不把密码放进命令。

主进程无打开 DB fd 不证明未使用 SQLite。必须将 DATABASE_PATH、EnvironmentFile 中相应配置（只读所需键，勿贴密钥）、实际代码默认路径与进程核对。审计的固定 DB 检查仅证明已知路径的状态；路径不一致先停止。Nginx 涉及多个虚拟主机时核对公网 IP 命中的 server，不能只看第一条 root。

进一步只读检查限于证据缺口：

- 实际 unit/drop-in 的 ExecStart、WorkingDirectory、EnvironmentFile 与进程一致；私密文件仅本地审阅，回传脱敏差异。
- 所有 worker、其他服务、timer/cron、打开 fd、cwd、软链接和候选父目录外的引用。脚本的配置搜索不是无引用的完整证明。
- 私密审阅 `/opt/ai-portal/update.sh` 全文，记录 SHA256；针对覆盖 DB/.env、rm/rsync --delete、git reset/clean、原地 pip 升级提出具体 diff。
- `release-candidates` 每个直接子目录分别列体积、Git HEAD、dist/venv/DB 内容及引用，不用目录名判定废弃。

## 清理分类（当前为待取证清单）

| 类别 | 绝对路径 | 体积 | 当前处理与原因 |
| --- | --- | --- | --- |
| A 保留 | `/opt/ai-portal/data/ai_portal.db` 及有效 sidecar | 待审计 | 生产数据库，禁止删除/覆盖 |
| A 保留 | `/opt/ai-portal/uploads` | 待审计 | 生产附件，禁止删除/覆盖 |
| A 保留 | `/opt/ai-portal/backend`、`/opt/ai-portal/frontend/dist` | 待审计 | 已知运行目录，现场核实实际引用；切换验收前保留 |
| A 保留 | 实际 `.env`、venv、Nginx/systemd 配置 | 待审计 | 运行必需，路径待证据确认 |
| A 保留 | `/opt/ai-portal/release-backups/20261021-pre-upgrade` | 待审计 | 重要恢复备份；未经验证替代备份，不清理 |
| C 待确认 | `/opt/ai-portal/source` | 待审计 | 可能为运行源码/发布或恢复来源，不能推断废弃 |
| C 待确认 | `/opt/ai-portal/release-testing/20261021` | 待审计 | 仅在证明无引用且为可丢弃测试副本后转 B |
| C 待确认 | `/opt/ai-portal/release-candidates` 的逐个实际子目录 | 待审计 | 尚无精确子项与依赖证据，不批准整个父目录删除 |
| C 待确认 | `/opt/ai-portal/update.sh` | 待审计 | 可能仍被 cron/人工使用，先审阅替换方案 |
| C 待确认 | 可能废弃的 drop-in、Nginx 片段、重复 dist、临时脚本 | 待审计 | 没有精确路径、体积及真实引用证据，不清理 |
| B 可删除 | 暂无已证实项 | — | 当前无 SSH 证据，不能虚构已确认废弃文件 |

每个转 B 的对象提交：绝对路径、realpath/链接、KiB、文件摘要、当前引用检查、保留备份、删除理由、批次。dry-run 为逐个 `stat`、`du -skx -- /exact/path` 和只读内容/引用预览。人工确认必须覆盖该精确清单；此文不是删除授权。

第一批：已证实与生产无关的废弃测试副本，可在上线前获批清理。第二批：旧运行代码/部署产物，只能精简版上线并验收通过后再次获批。未知文件与重要恢复备份不进入任一批次。禁止宽泛通配符、禁止对 `/opt/ai-portal` 整体递归清理。

删除前再次核对路径没有变更为软链接/挂载或当前依赖；若证据变更，原清单失效。每批删除后重查 systemd active、Nginx 配置、health、首页和已登录业务。

## 待批准发布顺序

1. 现场审计通过，固定精简制品及摘要、旧运行路径/环境、精确配置 diff、回滚路径与维护窗口。
2. 批准备份写入、必要停写及服务操作后：制作最新 SQLite Backup API 备份和一致 uploads/代码/dist/配置恢复包，校验恢复可用。保留旧 venv 原路径，不原地升级。
3. 仅在独立候选路径安装已锁定依赖和构建制品；核对 Dify 公开配置、uploads 实路径、绝对 DATABASE_PATH 和 `.env`。不复制本地运行数据。
4. 审阅并修订现场 update.sh，或批准逐条替代流程。未经读取实际脚本，不声称已修订。禁止启动任何含看板候选。
5. 按批准的精确 unit/Nginx 差异切换，nginx -t；仅必要时 daemon-reload/restart/reload。应用首次导入可能初始化数据库，已纳入生产写入授权。
6. 验收原管理员/员工登录、首页、新闻/内容、工具、资源交流、Dify 和后台；项目 API 在已登录会话下为 404，OpenAPI 无注册。匿名业务仍 401、普通员工管理仍 403。
7. 记录新进程真实路径、版本/摘要和 Nginx root；验收成功后提出第二批清理清单。审批和执行结果写入精简报告。

## 回滚

- 触发：登录失败、持续 5xx、数据/附件不可用或核心业务回归。
- 经批准停止新写入，保存失败现场和当前数据库最新备份；回退成套旧后端/原路径旧 venv/旧 dist 和原 unit/Nginx 配置，验证配置后重启并验收。
- 默认继续使用原生产 DB/uploads，不恢复旧库，不撤销已经合法发生的新写入。历史项目表无需清除。
- 如确需恢复数据库，必须另行批准目标备份、停所有写入并制定新数据合并方案；不要用 cp 活跃 SQLite 或只换主文件忽略 WAL。
- 回滚版本是本轮保留的原生产稳定版；已取消的含看板候选不能成为回滚目标。回滚也必须保留有效访问控制。
