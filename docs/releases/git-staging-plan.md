# 精确 Git 拟暂存清单

基线：main / 5a1acd2。此清单是审核白名单，不是已暂存结果，不授权 Commit、Push 或部署。必须保留当前工作区其他成果，禁止 git add . / git add -A。后续经用户批准才可按下列精确路径暂存，再检查 git diff --cached --name-status、--stat、--check 和敏感内容。

A/B/C 为本次正式候选集合；D 为可选开发辅助。不要只提交已跟踪修改：许多正式模块仍为未跟踪文件。backend/main.py、database.py 直接依赖新增认证/项目模块；前端 router/视图与组件也须配套。不得为了模块化提交拆出无法运行的中间状态。

## A. 后端认证、项目系统、历史及测试（26 个文件）

```text
backend/auth_api.py
backend/auth_security.py
backend/database.py
backend/employee_api.py
backend/employee_security.py
backend/main.py
backend/portal_access.py
backend/project_changes.py
backend/project_data.py
backend/project_updates.py
backend/project_write_api.py
backend/projects_api.py
backend/requirements.txt
backend/scripts/create_employee.py
backend/scripts/set_admin_password.py
backend/tests/auth_support.py
backend/tests/project_board_fixtures.py
backend/tests/test_employee_auth.py
backend/tests/test_exchange.py
backend/tests/test_project_http.py
backend/tests/test_project_maintenance.py
backend/tests/test_project_updates.py
backend/tests/test_projects.py
backend/tests/test_section_visuals.py
backend/tests/test_single_login.py
backend/tests/test_tool_images.py
```

## B. 前端登录、项目看板、维护页面及测试（56 个文件）

```text
frontend/src/App.vue
frontend/src/assets/employee-login.css
frontend/src/assets/project-board.css
frontend/src/assets/projects.css
frontend/src/components/AppHeader.vue
frontend/src/components/HeroBanner.vue
frontend/src/components/NewsList.vue
frontend/src/components/PriorityMatrix.vue
frontend/src/components/ProjectBoardCard.vue
frontend/src/components/ProjectBusinessContent.vue
frontend/src/components/ProjectDashboard.vue
frontend/src/components/ProjectDetail.vue
frontend/src/components/ProjectHistoryDialog.vue
frontend/src/components/ProjectNodeEditor.vue
frontend/src/components/ProjectNodeManager.vue
frontend/src/components/ProjectReadOnlyDetail.vue
frontend/src/components/ProjectStageProgress.vue
frontend/src/components/ProjectUpdateBadge.vue
frontend/src/components/ToolGrid.vue
frontend/src/components/WorkCalendar.vue
frontend/src/layouts/AdminLayout.vue
frontend/src/router/index.js
frontend/src/services/exchange.js
frontend/src/services/projects.js
frontend/src/utils/adminAuth.js
frontend/src/utils/authState.js
frontend/src/utils/employeeAuth.js
frontend/src/utils/modalPageLock.js
frontend/src/utils/personalStorage.js
frontend/src/utils/projectBoard.js
frontend/src/utils/projectDisplay.js
frontend/src/utils/projectEditor.js
frontend/src/utils/projectNodes.js
frontend/src/utils/projectUpdates.js
frontend/src/utils/quadrantStorage.js
frontend/src/utils/routeAccess.js
frontend/src/utils/todoStorage.js
frontend/src/views/ChangePasswordView.vue
frontend/src/views/EmployeesAdminView.vue
frontend/src/views/HomeView.vue
frontend/src/views/LoginView.vue
frontend/src/views/NewsDetailView.vue
frontend/src/views/NewsView.vue
frontend/src/views/ProjectEditView.vue
frontend/src/views/ProjectsAdminView.vue
frontend/src/views/ProjectsView.vue
frontend/tests/app-header.test.mjs
frontend/tests/employee-auth.test.mjs
frontend/tests/exchange.test.mjs
frontend/tests/project-board.test.mjs
frontend/tests/project-maintenance.test.mjs
frontend/tests/project-nodes.test.mjs
frontend/tests/project-updates.test.mjs
frontend/tests/projects.test.mjs
frontend/tests/section-masthead.test.mjs
frontend/vite.config.js
```

## C. 文档、Nginx 模板及安全忽略规则（12 个文件）

```text
.gitignore
DEPLOYMENT.md
README.md
deploy/nginx/ai-portal.conf.example
docs/employee-authentication.md
docs/project-board-v28.md
docs/project-dashboard.md
docs/project-maintenance.md
docs/releases/ecs-deployment-runbook.md
docs/releases/git-staging-plan.md
docs/releases/release-acceptance-checklist.md
docs/releases/release-readiness-review.md
```

## D. 可选安全本地验收工具（2 个文件）

```text
backend/scripts/copy_acceptance_password.ps1
backend/scripts/run_single_login_acceptance.py
```

## 明确禁止提交

- 原始或验收 SQLite、WAL/SHM、任意副本/备份、真实 .env、密钥、密码、credentials.dpapi、测试密码文件。
- 真实公司 Excel、业务 HTML、上传附件、运行日志和缓存；node_modules、dist、venv。
- artifacts/project-dashboard/项目推进看板_2026-10-20.html：存在于本地，必须保持忽略且不在 index。
- backend/scripts/run_project_demo.py、backend/scripts/run_project_acceptance.py：保留在磁盘，但本次忽略/排除；旧认证说明及临时密码输出流程未修复，不是生产依赖。
- 未审查的其他文件一律不自动纳入。不要用强制添加绕过忽略规则。

以下 15 个实验/截图资源本轮排除，不删除；未来如需归档，另行核对内容、保密与授权：

```text
artifacts/banner-studio-responsive/viewport-1200-slide-1.png
artifacts/banner-studio-responsive/viewport-1200-slide-2.png
artifacts/banner-studio-responsive/viewport-1200-slide-3.png
artifacts/banner-studio-responsive/viewport-390-slide-1.png
artifacts/banner-studio-responsive/viewport-390-slide-2.png
artifacts/banner-studio-responsive/viewport-390-slide-3.png
artifacts/banner-studio-responsive/viewport-768-slide-1.png
artifacts/banner-studio-responsive/viewport-768-slide-2.png
artifacts/banner-studio-responsive/viewport-768-slide-3.png
artifacts/design-system-v1-preview.html
artifacts/design-system-v1.2-assets/news-masthead.png
artifacts/design-system-v1.2-assets/tools-masthead.png
artifacts/design-system-v1.2-preview.html
artifacts/design-system-v1.3-site-preview.html
artifacts/header-design-lab.html
```

安全静态 HTML 和合成 .xlsx 测试夹具不被全局忽略；真实资料应放入 private-data/、local-private/ 等明确私有目录，或增加经审核的精确路径规则。无法根据后缀自动辨别业务保密性，新增文件仍须人工审查。

## Dify 历史配置：事实与待决定事项

- ea1ba78 的旧组件包含 URL 与前端 Embed 标识，不是已识别的服务端 API Key。当前正式源码无 DifyChatbot 引用。
- 本轮只读核对的本地 /assistant 配置没有复用旧 Embed 标识，也未复用旧配置主机；这不是生产配置或服务端撤销状态的证明。
- 当前 /assistant 使用 VITE_DIFY_EMBED_URL；所有 VITE_ 为浏览器公开值，不能存 Key/Token/Cookie。不要把公司真实地址写进源码、示例、清单或提交。
- 待 Dify 负责人确认：旧分享应用是否仍开放、是否具备匿名访问知识的权限、旧标识是否被其他调用方使用、旧地址暴露的内部拓扑影响。
- 如无依赖且有越权共享风险，批准后撤销/轮换旧应用的 Embed/分享标识或关闭其共享，收紧 Dify/网关权限，再更新必要调用方；不能直接断开现用业务服务。
- 如服务端 API Key 确有独立泄露证据，再单独轮换该 Key；不能把 Embed 标识误称为 API Key。
- Git 历史中的配置不会因删除当前文件而消失。历史清理须另行批准、协调所有克隆与公开托管缓存；本轮不改写历史、不强推。

## 建议提交顺序（未执行）

1. feat(backend): unify login and add audited project maintenance — A，保持后端认证/项目/迁移相互依赖完整。
2. feat(frontend): integrate authenticated project board and maintenance — B，包含认证适配与所有新页面/组件/样式/测试。
3. docs(release): align deployment and secure staging rules — C。
4. 可选 chore(dev): add isolated single-login acceptance helpers — D；仅代码，不含运行生成的实际凭据或数据库。

发布必须固定包含完整兼容集合的候选 SHA，不能将仅后端或仅前端的中间提交直接上线。执行暂存前复核本清单与实时 git status，新增未知文件应停止该项，不能自动扩张白名单。
