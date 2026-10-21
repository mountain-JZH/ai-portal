# 统一登录与权限（单次登录版）

## 登录与三种角色

- 唯一页面入口 `/login`。旧 `/admin/login` 安全重定向到该入口，并保留站内返回目标。
- 管理员：门户、全部管理后台、员工管理、项目维护；市场部等维护人员：门户、项目新增/编辑/历史；普通员工：门户及项目/历史只读。
- 后端每次请求读取有效会话、员工状态和实际管理员关联。维护权限不授予系统管理权限，客户端传权限布尔值不能提权。
- 本地测试阶段不强制首次或重置后改密。保留 `/change-password` 主动改密、后台创建/重置账号、停用及撤销会话。
- 同一会话有效期 7 天，无单独的一小时后台期限；到期、退出、停用及密码重置仍会失效。密码变化撤销旧会话。Cookie 继续 HttpOnly、SameSite=Lax；生产 HTTPS 的 Secure 设置沿用现有配置，不在本轮改动环境文件。

## 身份兼容与数据安全

保留 `admins` 和 `employees`，不删除账号、不重建业务表。增量增加 `employees.admin_id` 及非空唯一索引，关联原管理员 ID；原 Argon2 哈希继续使用。

现有管理员第一次输入正确凭据后，若无账号冲突，会建立对应的员工身份，以支持项目历史不可变员工 ID。若与未关联员工重名，不自动合并、升级或覆盖；需人工核实。原管理员 ID 及历史导入操作者保持不变。

`employee_sessions.admin_id/admin_expires_at` 旧列保留但不再用于提权；旧二次认证 Cookie 或字段不能绕过新权限。当前业务只信任员工身份上的明确管理员关联。

`POST /api/employee/login` 是统一登录接口。`/api/auth/login` 作为旧客户端兼容入口执行同一登录，不执行第二道认证；`/api/auth/me` 读取管理员身份；两套退出接口都撤销同一个登录会话。

应用启动仍会执行现有幂等初始化。源码修改前必须检查并停止指向真实库的自动重载进程，不能把测试请求发到真实业务库。本轮原库指纹应在前后核验，真实管理员密码不自动设置。

## 安全设置管理员密码（用户显式执行）

在项目根目录运行：

```powershell
backend\.venv\Scripts\python.exe backend\scripts\set_admin_password.py --database D:\workspace\ai-portal\backend\ai_portal.db --username adminMO
```

这是明确的账号写入操作，不是只读检查；只在用户决定应用到该目标库后执行。工具先显示绝对数据库路径与账号，要求输入 `SET ADMIN`，随后两次隐藏输入 12–128 位密码。不要将密码放到参数、环境文件、聊天或 Git 中。

工具复用现有管理员身份并保存 Argon2 哈希，撤销该账号旧会话；保留业务数据及已有 ID。不创建不存在的数据库文件，不自动合并重名员工，不自动重新启用停用账号。无需导入 `main.py` 或初始化全站业务数据。本轮开发者不执行该命令修改原库。

普通员工由后台创建；已有本地引导脚本 `create_employee.py` 仍可在显式确认目标库后使用，无公开注册。

## CSRF、限流和附件

- 所有写请求（含登录/退出/上传）保留 Cookie + X-CSRF-Token；登录和改密旋转令牌，客户端必须使用新值。
- 登录两个兼容入口共享 SQLite 限流桶：5 分钟内每来源 20 次、每账号 8 次，最多 4096 活动桶。
- 未登录访问内部 API/附件为 401；有效普通员工访问管理 API 为 403。服务器校验错误不回显密码。
- FastAPI 的 uploads 与 QsTArT 继续由员工会话保护。生产 Nginx 静态 alias/CDN 旁路仍需按既有部署方案单独验收；本轮没有修改或连接生产环境。
- Dify iframe 地址由用户浏览器直接访问，仍需 Dify 或公司网关自行保护，不能把 VITE_ 配置当秘密存储。
- 个人 Calendar/Todo/Planner 保留按不可变员工 ID 的存储隔离；不迁移匿名旧键，不改变业务数据格式。
- 原项目版本、字段历史、节点日志、Excel 冲突保护不变；管理员现在明确拥有项目维护权限。

## 隔离浏览器验收

生产 adminMO 的首次兼容、优先保留原密码、同名冲突核查、显式交互式恢复及认证失败回退，统一见 [部署指南](../DEPLOYMENT.md)。不要将本节临时账号流程用于生产，也不要运行被排除的旧 run_project_demo.py / run_project_acceptance.py。

`backend/scripts/run_single_login_acceptance.py --port 8002` 仅创建全新的临时 SQLite/uploads，生成三种角色及虚构新闻、Banner、工具和八类项目；不会打开原开发数据库，不启用 reload。

Windows 临时密码使用 DPAPI CurrentUser 加密，不在终端/日志中显示。启动后输出临时目录及非敏感 session.json；使用：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File backend\scripts\copy_acceptance_password.ps1 -SessionDirectory "实际启动输出的临时目录" -Role admin
```

Role 可选 `admin`、`market`、`employee`；对应账号 `adminMO`、`market-demo`、`employee-demo`。命令只复制该临时账号密码到当前剪贴板，登录后执行 `Set-Clipboard -Value ''` 清空。它不是原开发库的真实密码。

验收前端使用独立端口（本轮 5175），同源代理 /api、/uploads、/tools/qstart 到 8002，VITE_API_BASE_URL 仅在该进程设置为 /api；使用独立 Cookie 名称 `ai_portal_single_login_acceptance`，避免与旧 5173/5174 会话冲突。前端及后端均只绑定 127.0.0.1。

人工检查：

1. adminMO 从 /login 一次进入后台，访问首页、项目、员工管理、编辑；访问旧 /admin/login 不再提示二次验证。
2. 退出后登录 market-demo，可新增/编辑项目和查看历史，不能管理系统。
3. 退出后登录 employee-demo，可读取但无编辑入口，直接编辑 URL 或管理 API 不能绕过。
4. 保存字段后核对历史身份、时间和版本；退出后旧会话失效。
5. 首页新闻/Banner/工具非空且均明确是虚构验收内容；原开发数据不应出现在此环境。

自动化通过不等于浏览器视觉、Safari、触控或生产代理验收。正式环境开关、部署和原库账号设置都留给用户确认，不自动实施。
