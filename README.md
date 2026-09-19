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

## 三、当前正在处理

- 新闻 CRUD 基本完成，准备优化上下架和管理入口

## 四、下一步计划

- 新闻上下架优化
- 统一前端 API 地址配置
- 管理页面入口优化
- 后续管理权限
- 其他模块后台化

---

## 五、前端环境变量

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
