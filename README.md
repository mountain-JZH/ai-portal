# AI Portal

信息运维部智能助手平台。

技术栈：

- Vue 3
- Vite
- FastAPI
- SQLite
- Dify

---

## 一、项目结构

```text
ai-portal
├─ frontend
│  ├─ src/layouts/AdminLayout.vue
│  ├─ src/views/AdminDashboardView.vue
│  └─ Vue 3 + Vite
│
├─ backend
│  └─ FastAPI + SQLite
│
├─ README.md
└─ .gitignore
```

---

## 二、当前已完成

- `GET /api/news`：读取已发布新闻列表
- `POST /api/news`：新增新闻并写入 SQLite
- `GET /api/news/{id}`：按 id 读取单条新闻，不存在时返回 404
- 首页“最新动态”从 FastAPI 获取最新 3 条新闻
- 新增新闻页面 `/admin/news/new`
- 新闻详情页 `/news/:id` 已从本地 JSON 迁移到 FastAPI
- 新闻详情页支持 loading、404 和网络/后端错误状态
- 新闻列表页 `/news` 已从本地 JSON 迁移到 FastAPI
- 新闻列表页支持 loading、empty 和 error 状态
- `PUT /api/news/{id}`：更新新闻并返回数据库中的最新数据
- 新闻编辑页面 `/admin/news/:id/edit`
- 编辑页支持数据库数据回填、保存状态和 404 处理
- 更新成功后可通过详情接口读取数据库中的最新内容
- 本地 `news.json` 已删除
- `DELETE /api/news/{id}`：删除新闻，不存在时返回 404
- `GET /api/admin/news`：读取全部已发布和未发布新闻
- 基础新闻管理页面 `/admin/news`
- 管理页支持新增、编辑、二次确认删除和删除后列表更新
- 管理页展示已发布和未发布状态
- `PATCH /api/news/{id}/publish`：快捷发布或下架新闻
- 管理页支持发布 / 下架操作，并在当前列表直接更新状态
- 公开接口 `GET /api/news` 只返回已发布新闻
- 管理接口 `GET /api/admin/news` 返回全部新闻
- 顶部导航已增加“管理后台”入口
- 新增统一的 `AdminLayout`
- 新增 `/admin` 管理首页与新闻统计
- 新闻管理、新增和编辑页面已整合到后台嵌套路由

## 三、当前正在处理

- V2.3 工具数据层、管理后台与门户 API 化已完成
- 新闻、Banner、公告和工具均已采用 SQLite / FastAPI 统一内容链路
- 门户已移除独立“操作知识”页面及 `/knowledge` 路由；Dify 与未来知识问答能力保持不变

## 四、V1.1 收口记录

- Calendar / Todo 切换时保持右侧工作区高度稳定
- 当日待办只显示浏览器本地当天的任务
- 过期未完成任务自动移动到当天，任务 id 保持不变且不会生成副本
- 已完成的历史任务保留在原日期，不参与自动顺延
- 继续兼容现有 `ai-portal-todos-v1` localStorage 数据
- 完成首页视觉一致性与响应式静态检查
- 清理遗留调试代码、旧布局规则和无用资源
- 在“AI 与常用工具”中增加 Dify 助手占位卡片
- 完成前端 lint、生产构建与 Python 语法检查

Dify 助手卡片目前仅用于预留入口，不包含链接、API、iframe 或新增 Embed。后续计划由用户浏览器在公司内网环境下直接跳转至 Dify App 页面，Portal 服务器不代理 Dify 请求。

## 五、V2.1 管理后台框架

- AdminLayout 与后台独立视觉外壳
- `/admin` Dashboard
- Vue Router 后台嵌套路由
- 新闻管理、新增和编辑页面整合
- 后台统一导航与菜单高亮
- Dashboard 新闻总数、已发布和未发布统计
- 门户“管理后台”入口

## 六、V2.2A 门户内容数据层

- SQLite 新增 `banners` 表与 `announcements` 表
- 新增 Banner 公开接口、管理列表及完整 CRUD API
- 新增平台公告公开接口、管理列表及完整 CRUD API
- 公开列表只返回启用内容，管理列表返回全部内容
- 两类内容均支持 `sort_order` 稳定排序与启用 / 停用
- V2.2A 阶段已将原静态内容一次性导入现有数据库
- 当前后台管理 API 尚未加入认证，计划在 V2.4 统一处理

## 七、V2.2B 门户内容管理

- Banner 管理列表
- Banner 新增、编辑、删除及启用 / 停用
- 平台公告管理列表
- 平台公告新增、编辑、删除及启用 / 停用
- Banner 与公告均支持通过数字维护 `sort_order`
- V2.2B 阶段门户仍使用静态 JSON，V2.2C 已完成 API 迁移

## 八、V2.2C 门户内容 API 化

- `HeroBanner` 通过 `GET /api/banners` 读取启用 Banner
- `AppHeader` 通过 `GET /api/announcements` 读取启用公告
- 门户内容统一从 SQLite 经 FastAPI 公开接口读取
- Banner 与 Announcement 前端静态 JSON 已删除
- 后端数据库初始化已与前端源码和静态 JSON 解耦
- 新数据库会创建 `news`、`banners`、`announcements` 表，内容表初始允许为空

当前门户内容链路：

```text
管理后台
  ↓
FastAPI
  ↓
SQLite
  ↓
公开 API
  ↓
门户
```

## 九、V2.3A AI 与常用工具数据层

- SQLite 新增 `tools` 表，保留现有工具的图标、标题、描述、业务状态、按钮文案和 action 字段
- V2.3A 阶段曾从前端静态数据幂等导入初始工具；V2.3C 已解除该过渡依赖
- `GET /api/tools` 只返回 `is_active = 1` 的工具
- `GET /api/admin/tools` 返回全部工具
- 提供工具详情、新增、编辑、删除和启用 / 停用 API
- `is_active` 决定工具是否出现在公开门户，`status` 继续表达“可用 / 待接入 / 开发中”等用户可见业务状态
- API 使用与现有前端兼容的 `actionType` / `actionTarget` 字段，当前支持 `none`、`route`、`static`、`external`
- Dify 助手仍为 `integrating + none + 空 actionTarget` 的待接入占位，不包含虚假地址
- V2.3A 阶段门户仍使用静态工具数据，V2.3C 已完成 API 迁移

## 十、V2.3B AI 与常用工具管理后台

- 新增 `/admin/tools` 工具管理列表
- 支持工具新增、编辑和删除
- 支持启用 / 停用，并在列表中本地更新状态
- 支持维护 `status`、`actionType`、`actionTarget` 和 `sortOrder`
- 工具管理已纳入现有 `AdminLayout`，新增和编辑路由均保持工具管理菜单高亮
- Dify 助手仍保持待接入占位，未填写地址，未修改现有 DifyChatbot
- V2.3B 阶段门户仍使用静态工具数据，V2.3C 已完成 API 迁移

## 十一、V2.3C 工具门户 API 化

- 首页 `ToolGrid` 与 `/tools` 页面统一通过 `GET /api/tools` 读取启用工具
- 工具区域提供 loading、empty 和 error 状态，不再回退静态数据
- `available`、`integrating`、`developing` 业务状态展示保持不变
- `none`、`route`、`static`、`external` action 行为保持不变
- QsTArT 继续通过 `static + /tools/qstart/index.html` 在新标签页打开
- Dify 助手继续保持待接入占位，不包含地址且不可点击
- 前端工具静态 JSON 已删除
- 后端数据库初始化已与前端工具 JSON 解耦，新数据库的 `tools` 表初始允许为空
- SQLite 已成为工具内容唯一数据源

V2.3 已完成。当前新闻、Banner、公告和工具统一采用：

```text
管理后台
  ↓
FastAPI
  ↓
SQLite
  ↓
公开 API
  ↓
Portal
```

## 十二、V2 内容管理阶段总验收

- 新闻、Banner、公告和工具均已完成管理后台、FastAPI、SQLite、公开 API 与门户展示闭环
- 四类内容的 CRUD、发布 / 启停、公开过滤、排序、404 和 422 已通过临时数据验证
- 前端业务请求统一使用 `API_BASE_URL`，开发环境 CORS 仅允许 `localhost:5173` 与 `127.0.0.1:5173`
- Fresh DB 可创建 `news`、`banners`、`announcements`、`tools` 四张空表，不依赖前端 JSON
- 新闻、Banner、公告和工具的旧静态 JSON 均已清理，SQLite 是唯一内容数据源
- `/knowledge` 与“操作知识”入口已移除，QsTArT 静态工具继续保留
- Dify 助手工具卡仍为待接入占位，现有 DifyChatbot 保持不变
- Todo、Calendar、Planner 与四象限继续使用浏览器本地存储，不进入内容数据库
- 管理后台和全部管理写操作已在 V2.4 接入单管理员认证

V2 内容管理阶段总验收通过。

## 十三、V2.4 单管理员后台认证

- 普通门户 `/`、`/news`、`/news/:id`、`/tools` 继续免登录访问
- 管理后台 `/admin` 及其子路由需要管理员登录
- SQLite 新增 `admins` 表，仅保存管理员用户名、Argon2 密码哈希、启用状态与创建时间
- 初始管理员只在 `admins` 表为空且 `ADMIN_USERNAME`、`ADMIN_PASSWORD` 均已配置时创建，重复启动不会重复写入
- 使用 HttpOnly、SameSite=Lax 的 Cookie Session，不使用 JWT，不在 localStorage 保存认证 token
- `POST /api/auth/login`、`GET /api/auth/me`、`POST /api/auth/logout` 提供登录状态管理
- 所有 `/api/admin/*` 查询及新闻、Banner、公告、工具写操作均要求有效管理员 Session
- 每次受保护请求都会重新查询 `admins` 并确认 `is_active = 1`，停用管理员后已有 Session 立即失效
- 前端 `/login` 提供用户名与密码登录，Router Guard 保护 `/admin/**`，登录后优先返回原目标路由
- `AdminLayout` 显示当前管理员用户名并提供退出登录；后台请求遇到 401 会返回登录页
- CORS 继续只允许明确的本地开发源，并启用 Cookie credentials
- 本阶段没有普通用户体系、注册、JWT、角色或 RBAC

后端本地环境变量示例见 `backend/.env.example`。必须自行设置真实值，不要将账号、密码或 Session Secret 提交到 Git：

```dotenv
ADMIN_USERNAME=change-me
ADMIN_PASSWORD=change-me
SESSION_SECRET=replace-with-a-long-random-secret
SESSION_COOKIE_SECURE=false
```

部署到 HTTPS 后，将 `SESSION_COOKIE_SECURE` 设置为 `true`。

## 十四、后续规划

- V2.5 Dify 助手正式跳转因公司内网条件暂缓，尚未完成
- V2.6B 云服务器正式部署

以上项目仅作为后续规划，本阶段未开始实现。

---

## 十五、V2.6A 部署前生产化准备

- 本地开发继续使用 `127.0.0.1:5173` 与 `127.0.0.1:8000`
- 前端生产配置使用同源相对路径 `VITE_API_BASE_URL=/api`
- 后端支持通过 `DATABASE_PATH` 将生产 SQLite 独立存放在 `/opt/ai-portal/data`
- `SESSION_COOKIE_SECURE` 可在生产 HTTPS 环境启用，Session Secret 仍只从环境变量读取
- 新增无需登录的 `GET /api/health`，通过轻量 `SELECT 1` 检查 SQLite 可访问性
- 新增 Nginx 静态托管与 `/api` 反向代理模板
- 新增非 root 用户运行的 systemd Uvicorn 服务模板
- 新增基于 Python sqlite3 backup API 的安全备份脚本
- 新增 `DEPLOYMENT.md`，记录普通 Linux ECS 的安装、构建、启动、日志、备份、更新与回滚步骤
- V2.7 已开始支持 ECS 本地 Banner / 新闻图片上传

V2.6A 只完成部署前准备，当前尚未连接或部署任何云服务器。下一阶段为 V2.6B 云服务器正式部署。

## 十六、本地开发启动

推荐直接双击项目根目录中的：

```text
start-dev.bat
```

脚本会分别打开两个 PowerShell 窗口，启动 FastAPI 与 Vite，等待约 4 秒后自动打开 `http://127.0.0.1:5173`。两个服务运行期间，请勿关闭对应的 PowerShell 窗口。

脚本直接使用 `backend/.venv/Scripts/python.exe`，不需要手动执行 `Activate.ps1`，也不会自动安装 Python、Node 或项目依赖。

需要手动启动时，可使用以下命令。

Backend：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

本地开发地址：

- Portal：`http://127.0.0.1:5173`
- API：`http://127.0.0.1:8000`

## 十七、前端环境变量

前端通过 `VITE_API_BASE_URL` 统一配置 ai-portal FastAPI 后端地址。

首次配置时，在 `frontend` 目录复制示例文件：

```powershell
Copy-Item .env.example .env
```

也可以使用 Windows `copy`：

```cmd
copy .env.example .env
```

默认配置内容：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

- `frontend/.env` 保存本机实际配置，不提交 Git。
- `frontend/.env.example` 可以提交，用于新环境初始化。
- 修改 `.env` 后需要重新启动 `npm run dev`，Vite 才会读取新的环境变量。
