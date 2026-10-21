# AI Portal V1.8 发布准备审查（历史记录）

> 本文主体保留 2026-10-19 的历史观察与计数，不是当前发布指令或放行结论。2026-10-21 当前流程以 [DEPLOYMENT.md](../../DEPLOYMENT.md)、[当前验收清单](release-acceptance-checklist.md)、[精确拟暂存清单](git-staging-plan.md) 为准：/login 单次登录，服务端角色授权；受保护 API 未登录 401；uploads/QsTArT 经认证代理。当前不强制首次改密。生产 Exchange 开关必须单独确认，不按历史分批建议自动改值。

审查日期：2026-10-19。对象：`D:\workspace\ai-portal` 当前工作区，而非已经发布的 ECS。

## 1. 结论与证据边界

**结论：可以进入发布准备，不批准立即部署（NO-GO）。** 本地工程检查通过，但当前默认构建含开发 API 地址，内部访问边界及正式发布门槛仍需在部署窗口复核。用户提供的 2026-10-19 SSH 实际检查结果已补录在下节；Codex 本轮没有自行连接 ECS，也没有修改生产配置、迁移真实数据库、推送或部署。除本目录发布文档外，没有为本次 Git 整理修改业务代码。

- 本地源码、差异、测试和配置模板：已核查。
- 用户提供的 SSH 实检结果可作为当前 ECS 快照记录；它不等同于 Codex 独立核验，也不构成本轮部署授权。
- 浏览器运行入口报 `sandboxPolicy` 缺失，未完成真实浏览器视觉、触摸和页面交互验收。SSR/ASGI/HTTP 测试不等同浏览器验收。
- 本地测试均隔离数据库和上传目录；真实本地数据库只以只读连接检查，未迁移、写入或清空。
- 不能仅根据 HEAD 对比界定线上增量：最终应以核实后的生产 SHA/文件快照重新比较。

历史曾建议 Exchange 分批开放；当前已增加全站认证，发布范围与开关值须由业务负责人重新批准，不自动关闭原功能。所有生产发布阻塞项仍须解除。

### 用户提供的 ECS SSH 实检快照

以下信息来自用户提供的 2026-10-19 实际 SSH 检查结果，**不是 Codex 本轮自行连接服务器核验的结果**：

- ECS 当前源码版本为 `f2e9abe`，与本地整理前基线一致。
- 服务器 Python 为 `3.12.3`。
- 实际 SQLite 数据库路径为 `/opt/ai-portal/data/ai_portal.db`；生产备份应继续使用 `deploy/scripts/backup_db.py` 的 SQLite Backup API，不直接复制活跃数据库文件。
- Nginx 已作为当前入口运行；正式部署前仍须按手册保留并复核其生效配置，不用仓库示例覆盖现场配置。
- 持久化上传目录为 `/opt/ai-portal/uploads/`，发布与回滚不得覆盖、删除或随源码切换迁移该目录。
- ECS 存在现场部署脚本 `/opt/ai-portal/update.sh`；本轮仅记录其存在，未执行、未修改，后续部署前仍须以现场脚本内容为准单独复核。

本轮只进行本地 Git 提交；没有 push、没有执行 `update.sh`、没有更新 ECS。

## 2. Git 与基线

| 项目 | 核查结果 |
| --- | --- |
| 分支 | `main` |
| HEAD | `f2e9abe06b4abee9192c7b4343b69606c59a345b` |
| HEAD 主题 | `feat: add banner v2 and image-only slides`，2026-10-17 |
| 缓存上游 | `origin/main` 与 HEAD 相同，左右差异 `0 0` |
| 在线远程 | 未 fetch；不能证明 GitHub 当前版本仍相同 |
| 暂存区 | 无改动 |
| 审查前工作区 | 13 个已跟踪修改文件 + 47 个未跟踪文件，共 60 个 |
| 本轮新增 | 三份发布文档；审查后共 63 个待处理文件（按独立文件计） |
| 原有文件保护 | Lint、Build、测试后对原有 122 个已跟踪/非忽略未跟踪文件 SHA-256 比较无变化 |
| ECS 源码版本 | 用户提供的 SSH 实检结果为 `f2e9abe`；Codex 未独立连接核验 |

最近相关提交：`efb551f` Dify 独立页面、`4c7e4a1` Banner 压缩、`46c403d` Banner 上传、`2862777` 上传 API、`ef4166b` 历史 ECS 发布。最后一条只是历史记录，不是现运行版本证明。

正式 `HeroBanner.vue`、`components/banner/BannerSlide.vue`、`BannerFormView.vue` 已被 Git 跟踪且本轮工作区相对 HEAD 无差异；Banner V2 不是待收集的实验文件。

### 分类规则

- A：建议纳入发布候选，仍需共同发布门槛通过。
- B：功能实现已检查，但需人工页面/业务验收后转入发布。
- C：历史原型，保留在开发仓库，不进入生产 webroot/运行包。
- D：测试与 fixtures，保留仓库，不进入生产 webroot。
- E：本地/生产持久化和私有配置，绝不互相覆盖。
- F：用途或生产状态未确认，不自动纳入或执行。

### 已跟踪修改文件（13）

| 文件 | 类别 | 作用及依赖 |
| --- | --- | --- |
| `backend/database.py` | A | 新表及增量列迁移；所有新增后端功能先决条件 |
| `backend/main.py` | A | 注册图片/Exchange 路由、中间件；依赖新增 Python 文件、Pillow |
| `backend/requirements.txt` | A | 新增固定版本 Pillow；服务器需 Python ≥3.11 |
| `backend/tools_api.py` | A | JSON/Multipart 双兼容与封面写入；依赖新列与图片处理 |
| `frontend/src/components/AppHeader.vue` | B | Editorial Header、Exchange 导航；需桌面/手机验收 |
| `frontend/src/components/NewsList.vue` | B | 真实 API 前三条、整条链接、首页排版 |
| `frontend/src/components/ToolGrid.vue` | B | 首页正方形封面卡及启动入口；详细工具中心分支保留 |
| `frontend/src/components/WorkCalendar.vue` | B | 首页槽位尺寸和 Chevron；个人业务脚本未重构 |
| `frontend/src/layouts/AdminLayout.vue` | B | 新管理入口；沿用管理员认证 |
| `frontend/src/router/index.js` | A | Exchange、栏目管理路由与认证守卫；依赖新增 views |
| `frontend/src/views/BannerAdminView.vue` | B | 复用 Banner/栏目管理页签，不改变 Banner CRUD |
| `frontend/src/views/HomeView.vue` | B | 新首页组合、栏目公开 API、开发预览隔离 |
| `frontend/src/views/ToolFormView.vue` | B | 封面取景、单次 Multipart 保存，依赖新后端 |

### 未跟踪正式运行文件（23）

| 文件 | 类别 | 作用 |
| --- | --- | --- |
| `backend/exchange_api.py` | A | 公共投稿/读取、鉴权管理、开关、限流及图片清理 |
| `backend/image_processing.py` | A | Pillow 格式/完整性/像素校验与重编码 |
| `backend/section_visuals_api.py` | A | 两个固定栏目图片和深浅文字管理 |
| `frontend/src/assets/exchange.css` | B | 正式 Exchange 局部样式 |
| `frontend/src/assets/home/news-masthead.png` | A | 正式新闻报头素材，经 Vite 打包 |
| `frontend/src/assets/home/tools-masthead.png` | A | 正式工具报头素材，经 Vite 打包 |
| `frontend/src/assets/homepage.css` | B | 首页局部视觉体系 |
| `frontend/src/components/BannerManagementTabs.vue` | B | Banner/栏目管理入口 |
| `frontend/src/components/ChevronRight.vue` | A | 共享 SVG 图标 |
| `frontend/src/components/ImageCropFrame.vue` | B | 共享原生 Canvas 取景 |
| `frontend/src/components/MastheadPreview.vue` | B | 栏目取景预览 |
| `frontend/src/components/SectionImageCropper.vue` | B | 栏目取景交互 |
| `frontend/src/components/SectionMasthead.vue` | B | 首页统一整块链接、深浅文字与局部 Chevron |
| `frontend/src/components/ToolCardPreview.vue` | B | 后台真实工具卡预览 |
| `frontend/src/components/exchange/ExchangeCard.vue` | B | 单层完整资源展示 |
| `frontend/src/components/exchange/ExchangeSubmitForm.vue` | B | 真实投稿表单与取景；仅收到服务器成功才确认 |
| `frontend/src/config/sectionVisuals.js` | A | 栏目 key 与正式默认图来源 |
| `frontend/src/services/exchange.js` | A | API 适配、管理请求、持久化图片 URL |
| `frontend/src/utils/exchangeDiscovery.js` | A | 编号、搜索、随机队列、安全链接与字段校验 |
| `frontend/src/utils/sectionImageCrop.js` | A | 参数化裁剪几何及 Canvas 导出 |
| `frontend/src/views/ExchangeAdminView.vue` | B | 分页、完整详情、确认删除 |
| `frontend/src/views/ExchangeView.vue` | B | 随机发现、搜索、真实投稿 |
| `frontend/src/views/SectionVisualsAdminView.vue` | B | 栏目背景与文字深浅配置 |

这些文件不可漏发：`main.py` 和 Router 已直接引用它们。只提交现有 tracked diff 会造成缺少模块。

### 未跟踪原型与测试（24）

以下路径全部保留，不删除；C/D 不部署到 Nginx webroot。`artifacts/` 不参与当前 Vite 入口构建。

| 文件（逐项列出） | 类别 |
| --- | --- |
| `artifacts/banner-studio-responsive/viewport-1200-slide-1.png` | C |
| `artifacts/banner-studio-responsive/viewport-1200-slide-2.png` | C |
| `artifacts/banner-studio-responsive/viewport-1200-slide-3.png` | C |
| `artifacts/banner-studio-responsive/viewport-390-slide-1.png` | C |
| `artifacts/banner-studio-responsive/viewport-390-slide-2.png` | C |
| `artifacts/banner-studio-responsive/viewport-390-slide-3.png` | C |
| `artifacts/banner-studio-responsive/viewport-768-slide-1.png` | C |
| `artifacts/banner-studio-responsive/viewport-768-slide-2.png` | C |
| `artifacts/banner-studio-responsive/viewport-768-slide-3.png` | C |
| `artifacts/design-system-v1-preview.html` | C |
| `artifacts/design-system-v1.2-assets/news-masthead.png` | C，正式副本已位于 src/assets/home |
| `artifacts/design-system-v1.2-assets/tools-masthead.png` | C，正式副本已位于 src/assets/home |
| `artifacts/design-system-v1.2-preview.html` | C |
| `artifacts/design-system-v1.3-site-preview.html` | C |
| `artifacts/discovery-lab-v1.html` | C |
| `artifacts/header-design-lab.html` | C |
| `backend/tests/test_exchange.py` | D |
| `backend/tests/test_section_visuals.py` | D |
| `backend/tests/test_tool_images.py` | D |
| `frontend/tests/app-header.test.mjs` | D |
| `frontend/tests/exchange.test.mjs` | D |
| `frontend/tests/section-image-crop.test.mjs` | D |
| `frontend/tests/section-masthead.test.mjs` | D |
| `frontend/src/data/exchangeDemo.js` | D，只有测试引用，不是正式接口 fallback |

E 类：`.env`、后端虚拟环境、本地 SQLite、`uploads/`、`node_modules`、缓存和当前本地 `dist/`；规则受 `.gitignore` 保护，不能因“被忽略”就认为已有生产备份。未发现 tracked 数据库或私有 `.env`。F 类：实际生产文件差异、服务器可能存在的 `update.sh`；仓库中没有此脚本，不能审查或批准它。

## 3. 模块核查与发布范围

| 模块 | 实际实现及依赖 | 验证/建议 |
| --- | --- | --- |
| 首页 | 1200px 主轴、新闻 128+3×112=464px、日历槽位 464px、四张 1:1 工具卡；栏目图从 `/api/section-visuals`，失败用正式打包资源；Home 开发封面预览受 DEV 限制 | 相关组件测试通过；人工确认窄屏排版与日历内容滚动后发布 |
| Header | Editorial 品牌、首页/新闻/互通有无/工具/后台有效入口；项目看板未开放，不制造空路由；活动态按路径判断 | 8 项 Header 测试通过；需浏览器菜单、字体、焦点验收 |
| Banner | 正式 S2、渐隐、standard/image_only、API 读取、图片上传、轮播保留；旧 dify action 分支仍存在 | HEAD 已包含；未本轮改动；混合轮播/历史动作生产数据需人工核验 |
| 新闻 | 首页最多三条真实发布内容，整条到 `/news/:id`；新闻 CRUD 和发布字段保持 | 隔离测试含新闻鉴权及 CRUD；新闻中心和详情仍有旧视觉，未宣称完成全站重设计 |
| 工具 | 公开 SQLite/API、首页封面卡、不可用卡静态；后台新图片与字段一次 Multipart 保存；旧 JSON CRUD 继续支持，缺省 icon 保留 | 后端 8 项测试、前端工具回归通过；依赖新列、Pillow、新 API；详细 `/tools` 保留旧结构 |
| 日历/待办 | 本地个人数据、切换、保存、展开保留；改动为布局及 Chevron | 源码对比非业务重写；实际 464px 容器、长待办和切换需要人工验收 |
| 栏目管理 | `/admin/content/banners/sections`，背景上传取景、dark/light 保存及复用前台预览 | 后端 12 项及前端测试通过；依赖新表/列；有保存失败遗留文件问题见风险表 |
| Exchange | `/exchange`、`/admin/exchange`、真实投稿与读取、编号/日期/搜索/随机、管理详情及安全删除 | 后端 13 项、前端相关测试及隔离进程重启 HTTP 闭环通过；仅候选部署，内部边界未证实前不得开放 |
| 管理后台 | Router 守卫加服务端 `get_current_admin`；新增管理页面 | 鉴权测试通过；仍需 HTTPS Cookie 登录和页面操作验收，不能用 Router 守卫替代 API 鉴权 |

## 4. SQLite 与上传文件

### 4.1 路径与迁移

实际路径由 `backend/database.py` 的 `DATABASE_PATH` 决定；相对路径基于 backend，默认 `backend/ai_portal.db`。运行进程的环境优先于 dotenv，生产必须同时核对 systemd 环境文件、实际进程环境和工作目录，不可只看仓库示例。

本地只读观察：journal_mode=`delete`，integrity_check=`ok`；news 6、banners 6、announcements 2、tools 4、admins 1、section_visuals 2、exchange_resources 0。**不是生产数量，也不能用先前“已有 001”的聊天描述替代现状。**

`init_database()` 在 `main.py` import 时运行，也可显式执行 `database.py`：

- `banners.banner_type`：旧记录 default `standard`，已在 HEAD；生产缺列仍会按 PRAGMA 幂等补列。
- `tools.cover_image_url`：新增 NOT NULL、default 空串；保留旧 icon、动作等字段。
- `section_visuals`：两固定 section key、image_path、updated_at；旧表缺 `text_mode` 时补列，default `dark`。
- `exchange_resources`：AUTOINCREMENT 编号、完整内容、tags、图片/外链、UTC 日期；不导入演示数据。
- 不清表、不覆盖旧数据；管理员只在空 admins 且提供启动账号配置时初始化。不要在生产迁移时临时注入测试管理员。

DDL 是增量、可重复的，但不要把整个跨表迁移宣称为必然全有或全无；失败后检查实际 schema，再解决原因及重跑。应用回滚通常可保留新增列/表；不可自动反向 DROP 或恢复旧 DB 丢弃新投稿。

### 4.2 一致性与持久化

`deploy/scripts/backup_db.py` 使用 sqlite3 backup API；已用仍有活跃 WAL 的临时数据库验证备份可读、完整性 ok、已提交记录存在。首次验证脚本遗漏关闭检查连接而触发 Windows 临时目录清理错误，修正检查脚本后完整通过；不是业务备份代码错误。备份脚本本身不自动做完整性验收，且文件名秒级，发布应使用唯一备份目录并验证备份。

上传根目录来自 `backend/upload_api.py`：项目根目录 `/uploads`，不支持随意把 backend 搬到另一 release 根而不处理持久化映射。类别是 banners/news（已有）、tools、sections、exchange（新增）；FastAPI StaticFiles 必须指向稳定上传目录；Nginx /uploads/ 只可反向代理进入认证链，不得直接公开 alias。发布/回滚不覆盖或清理 uploads，不用本地上传文件替代生产图片。

本地聚合观察：banners 7 文件约 6.50MB、sections 3 文件约 0.88MB、tools 2 文件约 1.11MB、exchange 0；不能用于估算生产磁盘余量或 Linux 权限。需确认运行用户可写 DB 文件及父目录、上传目录；Nginx 用户可读且父目录可遍历，禁止 chmod 777。

Exchange 删除先提交 DB 删除，再校验固定目录/UUID/符号链接边界后清理本资源图片；跨目录拒绝，失败返回 `imageCleanupPending`。事务失败不删原图，编号不会因普通删除而复用；测试覆盖。工具/栏目替换保留旧图，不应顺手 GC。

## 5. 运行兼容性与配置

| 项目 | 本地已确认 | 生产核查门槛 |
| --- | --- | --- |
| Python | 本地 3.12.4；用户提供的 ECS 实检为 3.12.3 | 候选 venv 仍须按发布手册独立安装和验证 |
| Pillow | requirements 固定 `13.0.0`，安装 metadata 要求 Python ≥3.11 | Python <3.11 时当前依赖不能直接安装；另行批准升级或兼容版本验证，不现场盲改 |
| FastAPI/Uvicorn | `0.141.1` / `0.52.4`，metadata 均要求 Python ≥3.10 | 核对实际 Python、依赖及服务启动参数 |
| multipart | `python-multipart==0.0.20` | 新 venv 全量安装 requirements，不只临时补 Pillow |
| Node/npm | 22.23.2 / 10.9.8 | engines 要求 `^22.18.0 || >=24.12.0`；使用 lockfile，Vite 本地 8.2.2 |
| API Base | 本地 `.env` 配置 loopback；无 `.env.production` 覆盖 | **默认 build 产物 index-YRyiEgVN.js 含 127.0.0.1:8000，不可发布**；显式同源构建后重新审计 |
| Dify | 前端 iframe 读取 VITE_DIFY_EMBED_URL | VITE 变量是公开构建内容；使用批准的 Embed 地址，不放 API Key/Token，不在审查文档打印真实配置 |
| CORS | localhost:5173 与 127.0.0.1:5173、credentials，未 wildcard origin | 同源生产不依赖新增 CORS；独立域名另行审批 |
| Nginx | 仓库模板含 dist root、API 8000 代理、uploads/QsTArT 认证代理、SPA fallback、5m | 用户确认 ECS 当前由 Nginx 提供入口；正式发布前仍复核现场生效配置，不以模板覆盖 |
| systemd 模板 | aiportal 用户、backend/.venv、EnvironmentFile、127.0.0.1:8000 | 实际服务名、路径、用户、代理信任设置待确认 |
| update.sh | 仓库未找到；用户确认 ECS 存在 `/opt/ai-portal/update.sh` | 本轮未执行、未修改；部署前须单独读审 |

不能用当前 dist 直接上线。发布时可在审核过的独立工作副本显式 `VITE_API_BASE_URL=/api npm run build`，并按批准的 Dify 配置构建；`config/api.js` 会把 `/api` 规范成同源空 base，已有请求路径不会产生 `/api/api`。本轮没有改变环境配置。

## 6. Exchange 与安全

- `EXCHANGE_ENABLED` 默认 false。本地被忽略的 backend/.env 为 true，属于已有本地测试配置，本轮未修改。生产不得拷贝这个文件。
- false 同时令公开 GET/POST 返回 503，**不是只关闭投稿**；管理接口仍需管理员。前台会显示未开放错误，分享按钮仍可进入表单，最终 503 不会冒充成功；阶段一需人工确认这一交互是否可接受。
- false **不会撤销已有 `/uploads/exchange/` URL 的访问**，Nginx/StaticFiles 静态文件不查该开关。内部保护必须同时覆盖页面、读写 API、图片及可能直连的后端端口。
- 当前未取得 VPN、公司网关、白名单或外部阻断证据。仅“公司内部使用”的定位不能充当边界证明。未验证前生产必须保持关闭；已有敏感图片还需要独立边界，不能只关开关。
- 管理员沿用 HttpOnly Cookie、服务端 get_current_admin；生产 HTTPS 下需验证 SESSION_COOKIE_SECURE、可信代理、Cookie 属性及登录/退出。不能泄露或改写 SESSION_SECRET、管理员口令。
- 新图片链路实际校验 JPEG/PNG/WebP 格式与 MIME 匹配、verify+load、静态帧、边长 ≤8192、像素 ≤1600 万、输入和重编码输出 ≤5MB；重编码清除原始尾随内容/元数据。已有 Banner 上传逻辑未被这一新链路替换。
- Exchange 有整体请求体上限、每 peer 10/min、全局 60/min 的进程内限流；重启清零、多 worker 不共享。需检查可信代理链，避免所有人共用一个代理 IP 或信任任意伪造来源。不能把限流称为身份或内部访问控制。
- 本轮对源码/文档作有限模式扫描，未发现匹配私钥头、常见 AWS/GitHub token 或直接赋值的长敏感字段；不代表完整历史凭据审计。未打印真实环境密钥、Cookie 或公司 Dify URL。公开仓库历史内容需要独立审查，不能承诺“无任何泄露”。
- 历史 `/api/chat` 仍存在无鉴权的后端 Dify 调用，非本轮新增。如生产仍配置有效 Dify Key，应单独评估匿名消耗/滥用风险；本轮未调用或修改。

## 7. 本轮实际检查

| 检查 | 结果/范围 |
| --- | --- |
| `npm.cmd run lint` | 通过；命令自身带 --fix，文件哈希证明没有修改原源码 |
| `npm.cmd run build` | 通过，115 modules；dist/index.html、dist/tools/qstart/index.html 存在；但产物 API 地址不适合生产 |
| `node --test --test-concurrency=1 tests/exchange.test.mjs tests/app-header.test.mjs tests/section-image-crop.test.mjs tests/section-masthead.test.mjs` | 51/51 通过；含随机队列、搜索、裁剪几何、整卡入口、Header、编辑表单及预览 |
| `backend/.venv/Scripts/python.exe backend/tests/test_exchange.py` | 13/13 通过；临时 DB/uploads、真实 ASGI/HTTP、鉴权、CRUD、编号、删除越界、请求约束、幂等迁移、新闻回归 |
| `... backend/tests/test_tool_images.py` | 8/8 通过；临时 DB/uploads、JSON/Multipart、图片安全、保存失败等 |
| `... backend/tests/test_section_visuals.py` | 12/12 通过；临时 DB/uploads、文字模式、图片安全、鉴权及兼容 |
| py_compile | backend 顶层 .py + backup_db.py，共 12 文件通过；没有直接 import 真实 main 触发真实 DB 初始化 |
| 隔离进程重启 HTTP 闭环 | 新图投稿 201 → 完全停止子进程 → 同一临时 DB/uploads 启动新进程 → 公开读图及列表 200 → 管理登录/详情/删除 → 列表空、图片 404，全部通过 |
| WAL 备份 | 活跃 WAL 的临时源经现有 backup API 备份，integrity_check=ok、记录存在；完整复验通过 |
| 栏目 SQL 失败注入 | 隔离复现 500 + 1 个未引用 WebP，作为问题记录，未改代码 |
| 原型与 fixtures 隔离 | dist 中无 Studio/Discovery Lab/Design HTML；正式 Exchange 没有导入 exchangeDemo.js |
| Git/新增文档格式 | 见最终检查；普通 git diff --check 不覆盖 untracked，另检查新增文档行末空白与源码语法 |
| 真实浏览器/ECS | Codex 未连接 ECS；仅补录用户提供的 SSH 实检快照，不把它写成 Codex 独立核验或部署通过 |

隔离进程重启验证首次尝试因 PowerShell 管道中文编码使测试 payload 变为非法枚举而返回 422；改用正确 Unicode 测试字段后通过，没有更改业务校验或绕过提交限制。

## 8. 风险分级与处置

| 级别/编号 | 发现与依据 | 发布处置 |
| --- | --- | --- |
| BLOCKER B1 | 默认 build 受开发 .env 影响，JS 含 loopback API | 不上传当前 dist；生成并审计正确同源候选产物 |
| BLOCKER B2 | 生产 SHA/路径/DB/服务/备份未证实 | 只读取证并验证备份后才批准任何切换 |
| BLOCKER B3（待判定） | Pillow 13 要求 ≥3.11，服务器解释器未知 | 确认并在独立候选 venv 安装验证；不兼容就停止 |
| BLOCKER B4（开放 Exchange 时） | 内部边界无证据；开关不保护静态图 | 一期保持 false；读写和图片内外网实测通过后再审批开放 |
| HIGH H1 | 23 个正式依赖仍 untracked，单靠现有 commit 不含新功能 | 人工收集批准文件、固定候选版本与清单，禁止漏发和 git add . 混入本地数据 |
| HIGH H2 | 上传根依赖源码父路径，切换 release 根可指向新空目录 | 固定 app 根或确认持久化映射；前后端回退不删除 uploads |
| HIGH H3 | 生产回滚、旧依赖环境及新写入保护尚无实证 | 演练应用优先回滚；保留旧源码、venv、dist；DB 恢复需第二次审批 |
| HIGH H4（条件） | 旧 /api/chat 无鉴权，生产 Key/网关状态未知 | 核实是否仍有效及访问边界；另行处置，不在本轮偷偷修改 |
| MEDIUM M1 | 无真实浏览器验收：Header、取景、日历槽位及手机布局 | 人工清单逐项记录，不以 build 代替验收 |
| MEDIUM M2 | Nginx 5m 限整个请求，业务允许 5MB 单文件另带 multipart | 验证接近上限文件；必要调整需另行批准，不改本轮模板 |
| MEDIUM M3 | 栏目写文件后 SQL 失败会遗留新图（已复现） | 单独修复或接受并监测磁盘；不能自动删除旧有效图 |
| MEDIUM M4 | 限流为进程内、代理来源影响限流；信息日志可能未持久记录 | 核实 worker/可信 hop/日志 INFO 与清理失败追踪，不宣称具备全局限流审计 |
| MEDIUM M5 | 前台 Exchange 仅加载最新 200 条，搜索在已加载集合内 | 小规模可接受但需披露；大规模前另议服务端搜索/分页 |
| MEDIUM M6 | 新闻中心/详细工具中心仍旧视觉；关闭 Exchange 后分享入口的反馈需验收 | 作为明确的分阶段范围和人工决策，不视为全站视觉迁移完成 |
| MEDIUM M7 | 模板无缓存策略，旧页面可能请求旧 hash chunk | 候选 dist 保留上版 hashed assets，检查 HTML 缓存与发布顺序 |
| LOW L1 | 工具/栏目替换保留历史图片 | 容量监测与未来有引用证明的 GC，不本轮清理 |
| LOW L2 | 两张报头 PNG 约 1.25MB/1.46MB | 后续压缩与缓存优化，不本轮生成/替换素材 |
| LOW L3（数据相关） | HeroBanner 历史 dify action 仍寻找已移除气泡按钮 | 核实是否有该类生产记录，后台人工改为合法 route/external；不擅改历史数据 |

## 9. 发布门槛

1. 核实 ECS 运行版本、Python、DB 绝对路径、持久化上传根、服务和入口边界。
2. 通过候选源码及视觉人工验收；由用户选择性提交形成可复现 SHA，本轮不代提交。
3. 在隔离工作副本构建同源产物；不复制本地 .env/DB/uploads/venv；确认原型和测试 fixtures 不进入 webroot。
4. 完成并验证 DB、uploads、配置、源码、旧 venv、dist 的备份，演练回滚。
5. 按 runbook 先后端/迁移，后前端；一期 Exchange 保持关闭，二期单独批准。

操作细节见 [ECS 发布手册](ecs-deployment-runbook.md)，逐项签字见 [验收清单](release-acceptance-checklist.md)。完成本轮文档后停止，等待人工确认。
