# AI Portal 精简与 ECS 清理报告

日期：2026-11-02。阶段 A–C 完成；D–F 等待 ECS 连接信息、现场证据及相应人工批准。未提交、未推送 GitHub，未操作生产环境。

## 1. 源码备份

- 路径：`D:\workspace\ai-portal-backups\20261102-pre-project-removal-01`。
- HEAD：`efb1018b25a6f85e9662efba9a9201c925332290`。
- 本地标签：`backup-pre-project-removal-20261102-01`。
- `source.zip` 含 192 个文件、7,842,399 字节原始内容，包括原 README 修改、未跟踪设计文档/素材、AGENTS 和验收脚本；排除真实 `.env`、密钥、数据库、uploads、虚拟环境与缓存。
- ZIP SHA256：`354ec4a418944d582cc98619734486a1f4f7e7295267cab73e2ca654bd12b59c`。
- ZIP CRC 检查及隔离目录解包后全部 192 个文件 SHA256 比对通过；`manifest.json` 保存逐文件摘要、排除项与原工作区状态，`HEAD.txt`/`RESTORE.txt` 保存恢复信息。

## 2. 删除的前端文件

共 21 个业务源码文件、5 个专属测试文件；精确路径见 [删除清单](../../artifacts/project-removal/deleted-files.json)。

- views：`ProjectsView.vue`、`ProjectsAdminView.vue`、`ProjectEditView.vue`。
- components：`ProjectBoardCard.vue`、`ProjectBusinessContent.vue`、`ProjectDashboard.vue`、`ProjectDetail.vue`、`ProjectHistoryDialog.vue`、`ProjectNodeEditor.vue`、`ProjectReadOnlyDetail.vue`、`ProjectStageProgress.vue`、`ProjectUpdateBadge.vue`。
- services：`projects.js`；assets：`project-board.css`、`projects.css`。
- utils：`projectBoard.js`、`projectDisplay.js`、`projectEditor.js`、`projectNodes.js`、`projectUpdates.js`、已无使用方的 `modalPageLock.js`。
- tests：`project-board`、`project-maintenance`、`project-nodes`、`project-updates`、`projects` 对应 `.test.mjs`。

首页独立个人时间线 `ProjectNodeManager.vue` 改名为 `PersonalTimeline.vue`。与备份逐字节一致，浏览器存储键及功能保留；它从未依赖服务端看板 API。

## 3. 删除的后端文件

- `projects_api.py`、`project_write_api.py`、`project_data.py`、`project_changes.py`、`project_updates.py`。
- 专属测试/夹具：`test_projects.py`、`test_project_http.py`、`test_project_maintenance.py`、`test_project_updates.py`、`project_board_fixtures.py`。
- 另删除 3 份失效模块文档：`docs/project-dashboard.md`、`docs/project-maintenance.md`、`docs/project-board-v28.md`。实际删除合计 39 个文件，组件重命名单列。

## 4. 修改的公共文件

- 后端：`main.py` 移除路由/导入中间件；`database.py` 停止初始化项目表和专属员工权限；`employee_api.py`/`employee_security.py` 删除维护授权和响应字段。
- 前端：router、AppHeader、AdminLayout、EmployeesAdminView 移除项目入口/授权/局部主题；PlannerExpandPanel 使用重命名组件。
- ToolGrid/HeroBanner 不再渲染指向未注册站内路由的有效动作，兼容旧 DB 中可能存在的失效工具/Banner 链接；不改写生产记录。
- 更新认证/导航测试，新增真实路由及首页 SSR 检查、后端 API 移除/新旧 schema/Dify 契约检查。
- 保留并修订原未跟踪隔离验收脚本；同步 README、frontend README、部署/认证/发布及设计文档。历史发布审查明确标记为已被取代。
- 增加源码备份、逐套后端测试、只读 ECS 审计及候选封装脚本；package 增加 `npm test`；忽略本地候选压缩包。

## 5. 依赖清理

Python 删除仅服务于 Excel 导入的 `openpyxl==3.1.5`、`defusedxml==0.7.1`。npm 未发现项目看板专属依赖，无包需要删除。未卸载现有 Python/Node/Nginx 环境。

## 6. 本地验收

| 检查 | 结果 |
| --- | --- |
| 前端全部测试 | 62/62 通过，见 [结果](../../artifacts/project-removal/frontend-test-results.json) |
| 后端逐套隔离测试 | 56/56 通过，见 [结果](../../artifacts/project-removal/backend-test-results.json) |
| 同源生产构建 | `VITE_API_BASE_URL=/api`，122 modules，成功 |
| Python 语法、pip check | 通过；无 broken requirements |
| 修改/重命名前端源码 ESLint | 通过，未自动修复 |
| 相对 import 与 Git diff check | 无缺失 import，无 diff 格式问题 |
| 路由与 API | 四个项目页面无匹配路由；已登录 GET/POST/PUT/DELETE 项目路径为 404；OpenAPI 无项目操作 |
| 数据兼容 | 新库无项目表/权限字段；测试旧库的历史项目数据/字段、新闻/Banner/公告/工具/员工/管理员哈希，重复初始化保持不变 |
| 保留功能 | 登录、权限、会话、内容 CRUD、图片、资源交流 HTTP 闭环通过；首页/个人时间线实际组件 SSR 通过；Dify 代理使用模拟上游验证契约 |
| dist 检索 | 无项目 API/后台/编辑路由、专属权限、开发 API 地址或重复 `/api/api/` |

额外对照备份：新闻、内容、工具、资源交流、认证、访问保护等核心源码未变；个人时间线重命名前后字节一致。上述结果不替代 ECS 真实浏览器验收或外部 Dify 实际连通性检查。

整套后端测试必须使用 `backend/.venv/Scripts/python.exe deploy/scripts/run_backend_tests.py`；各套件持有模块级应用/临时库，不能用同一进程的 unittest discover 复用状态。

## 7. ECS 当前状态

未获得 SSH 目标/账号/密钥路径，未直接连接 ECS。生产仍运行上一稳定版是用户提供的已知事实；当前 HEAD、实际进程/venv、Nginx root、DB 状态及残留引用尚未现场确认。没有声称审计完成。

最少只读检查命令及证据要求见 [ECS 手册](ecs-deployment-runbook.md)。提供 SSH 连接方式或执行并回传该脚本脱敏结果后，才能形成有体积和依赖证据的精确清理清单。

## 8. ECS 待清理清单

[ECS 手册分类表](ecs-deployment-runbook.md) 已区分 A/B/C：

- A：生产 DB/sidecar、uploads、当前 backend/dist、有效 `.env`/venv/Nginx/systemd，以及 `release-backups/20261021-pre-upgrade` 恢复备份。
- C：`source`、`release-testing/20261021`、`release-candidates` 的实际子项、`update.sh`、可能废弃配置和临时文件。体积均待现场审计，不按名称推断无用。
- B：目前没有经证据确认的废弃项。证明无引用、可丢弃后提交绝对路径、体积、删除理由与 dry-run，再取得人工确认。

第一批可含已证实与生产无关的测试副本；第二批旧运行产物必须精简版上线验收后再次获批。重要恢复备份和未知文件不清理。

## 9. 已批准且实际完成的 ECS 清理

无。尚无 ECS 删除批准，也未执行任何 ECS 删除。此事项仍待完成，不以分类清单代替正式清理。

## 10. 尚需保留的生产文件

完整保留 `/opt/ai-portal/data/ai_portal.db`、`/opt/ai-portal/uploads`、当前实际运行代码/前端、私有环境配置、有效服务/代理配置、旧稳定 venv 和重要恢复备份。历史项目表/字段无需物理删除；不执行 DROP、不清空数据、不重置管理员密码。

## 11. 唯一新候选及待批准上线

- [精简候选](../../artifacts/project-removal/ai-portal-slim-20261102-02.tar.gz)：134 个文件，4,430,491 字节；含精简源码、测试、前端 dist 和部署脚本/模板，不含运行数据与真实 `.env`。
- SHA256：`468185ce05ee3b987fd1a9b60564fc9757396b67cd24cc835c4aa51d05d8d46b`。
- [制品清单](../../artifacts/project-removal/ai-portal-slim-20261102-02.tar.gz.manifest.json)：归档逐文件摘要读取验证通过；来自当前未提交工作树，不能将旧 HEAD 视为候选 SHA。
- 尚未上传、切换或重启。先现场审计并审阅实际 update.sh，再形成具体配置 diff/操作清单。未读取服务器脚本，不能声称已完成它的修订。
- 待批准项：最新生产备份及必要停写、独立候选环境准备、必要 schema 初始化写入、配置切换/服务重启及验收、两批精确清理。不会执行旧含看板候选。
- 保持公网 IP + HTTP 80。公网 HTTP 可能泄露登录凭据和会话；保留现有安全保护，本轮不以域名/HTTPS 阻断。

## 12. 回滚

本地：将删除前 `source.zip` 解压到空目录，按 manifest 逐文件验证，补入受控环境和运行数据后测试；备份标签定位原已提交历史，ZIP 恢复未提交修改。避免直接硬重置当前工作区。

生产：保留原稳定后端、原路径 venv、dist、unit/Nginx 和私有配置。获批后成套回退并验收，默认继续使用现有 DB/uploads；恢复旧数据库须另行批准并处理新增写入，不能盲目覆盖。回滚目标不使用已取消的看板候选。详细顺序见 [ECS 手册](ecs-deployment-runbook.md)。
