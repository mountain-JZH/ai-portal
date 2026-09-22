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
- `PATCH /api/news/{id}/publish`：快捷发布或下架新闻
- 管理页支持发布 / 下架操作，并在当前列表直接更新状态
- 公开接口 `GET /api/news` 只返回已发布新闻
- 管理接口 `GET /api/admin/news` 返回全部新闻
- 顶部导航已增加“新闻管理”入口

## 三、当前正在处理

- V1.1 收口已完成，进入下一阶段前的稳定版本

## 四、V1.1 收口记录

- Calendar / Todo 切换时保持右侧工作区高度稳定
- 完成首页视觉一致性与响应式静态检查
- 清理遗留调试代码、旧布局规则和无用资源
- 在“AI 与常用工具”中增加 Dify 助手占位卡片
- 完成前端 lint、生产构建与 Python 语法检查

Dify 助手卡片目前仅用于预留入口，不包含链接、API、iframe 或新增 Embed。后续计划由用户浏览器在公司内网环境下直接跳转至 Dify App 页面，Portal 服务器不代理 Dify 请求。

## 五、下一阶段：V2 平台管理化

1. AdminLayout
2. `/admin` Dashboard
3. 门户 Banner / 公告后台化
4. AI 工具后台化
5. 登录 / 管理员权限
6. 后续个人数据后台化

---

## 六、前端环境变量

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
