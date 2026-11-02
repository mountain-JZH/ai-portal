# 统一登录与权限

2026-11-02：服务端项目看板及专属维护权限已经移除。

- 唯一页面入口 `/login`，旧 `/admin/login` 重定向到此入口。
- 管理员一次登录访问门户及全部管理后台；普通员工访问门户，不能管理内容或账号。
- 每次请求从数据库解析员工状态、会话与 `employees.admin_id`；客户端字段不能授予管理员身份。
- 保留主动改密、后台创建/重置账号、停用、会话撤销、CSRF、Argon2 和限流。当前不强制首次改密。
- 会话有效期 7 天；退出、到期、停用和密码重置使旧会话失效。
- 原 `admins` 行、ID、密码哈希保留。旧管理员正确登录后可建立关联员工身份；同名未关联员工冲突返回拒绝，不自动合并或升级。
- 历史数据库中的旧权限字段及项目表保持原样，新库不再创建。应用不再读写或返回专属权限。
- `/api/employee/login` 与兼容入口 `/api/auth/login` 使用同一登录；两套退出接口撤销同一会话。
- 业务 API、uploads、QsTArT 均要求登录。健康接口保留公开检查。

部署与恢复见 [部署指南](../DEPLOYMENT.md)。本次不修改生产密码、数据库或环境文件。

## 本地隔离验收

`backend/scripts/run_single_login_acceptance.py --port 8002` 在全新临时目录创建虚构账号、新闻、Banner、工具与 uploads。仅绑定 127.0.0.1，不读取原开发库；临时凭据使用 Windows DPAPI 加密。

`backend/scripts/copy_acceptance_password.ps1 -SessionDirectory <实际临时目录> -Role admin` 可复制该临时账号密码，登录后清空剪贴板。`market` 与 `employee` 均为普通员工，无独立维护权限。

人工检查管理员门户/后台、普通员工门户/拒绝后台、主动改密及退出旧 Cookie 失效。Dify 真实服务连通性需使用批准的现有公开 Embed 配置验收。
