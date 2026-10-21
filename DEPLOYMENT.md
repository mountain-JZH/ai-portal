# AI Portal 上线与账号兼容指南

适用：单次登录、员工权限及项目维护正式候选。仅是人工执行流程，不是自动发布授权。真实路径、服务名、维护窗口及候选 SHA 必须在执行前确认；不得把下列示例路径直接当作现场事实。生产动作须另行批准，本轮不连接 ECS。

配套：[分阶段发布与回滚](docs/releases/ecs-deployment-runbook.md)、[发布验收清单](docs/releases/release-acceptance-checklist.md)、[精确拟暂存清单](docs/releases/git-staging-plan.md)、[认证实现](docs/employee-authentication.md)。

## 1. 发布前清单

- [ ] 固定批准的完整候选 SHA，包含所有新模块；不发布脏工作区或本地数据库。
- [ ] 核实实际进程、WorkingDirectory、EnvironmentFile、DATABASE_PATH、uploads、webroot、服务用户及服务名。
- [ ] 核实 Python ≥3.11、Node 满足 frontend/package.json engines；独立候选 venv 安装 requirements.txt，执行 pip check，保留旧 venv 原路径。
- [ ] 核实 HTTPS、网关、安全组及防火墙；FastAPI 仅监听 127.0.0.1，不使用 --reload。
- [ ] 运维单独阅读服务器 update.sh，不假定仓库已审查它，不自动运行。
- [ ] 按业务负责人决定保留或关闭 Exchange；EXCHANGE_ENABLED 未设置默认关闭。关闭会拒绝已登录员工的列表与投稿，不是“只读开放”。
- [ ] Dify Embed 地址与分享权限经服务负责人批准；不复制本地 .env。
- [ ] 备份、生产副本迁移、账号兼容和回滚演练通过后，才批准真实切换。

## 2. 一致性备份与迁移

示例持久目录为 /opt/ai-portal/data/ai_portal.db、/opt/ai-portal/uploads。以现场确认值为准。

1. 批准维护窗口，停全部数据库及上传写入方。数据库在线 backup 可以取得 SQLite 一致快照，但不能自动保证它与另一时点的 uploads 一致。
2. 在 webroot 外新建本次唯一私有备份目录，限制权限。使用现有 deploy/scripts/backup_db.py（SQLite Backup API）备份；活跃 WAL 库不能只复制 .db。
3. 同时备份 uploads、旧代码、旧 dist、原 venv、私有 .env、实际 Nginx/systemd 配置；秘密只保存在受控备份，禁止进入 Git 或公开日志。
4. 验证备份 integrity_check、表数量、文件清单、校验和并在隔离目录恢复演练。
5. 在生产备份的副本上设置明确 DATABASE_PATH，用候选 database.py 初始化两次。比较旧表旧列数据、管理员 ID/密码哈希、员工权限及编号序列，确认未改变、重复执行幂等。不要输出密码哈希。
6. 真实迁移须另行批准；不得上传本地库、导入示例或重新灌入新闻/Banner/工具/Exchange。初始化只有空 admins 且启动凭据齐全才创建管理员，不会自动重置已有管理员。
7. main.py 导入仍调用初始化；多步 DDL/executescript 不保证整个迁移失败时完全回滚。失败应停服、保留现场、核对部分结构，而不是盲目重复或删除字段。

## 3. adminMO 首次上线：优先保留原密码

### 正常兼容路径

1. 在生产备份副本先核对：admins 中仅一个大小写归一后名为 adminMO 的账号，状态有效；employees 是否已有同名账号或 admin_id 关联。只记录数量、关联及状态，不导出凭据。
2. 保留原 admins 行、不可变 ID、Argon2 哈希及原 SESSION_SECRET。已有 employees 的 ID、权限也不得由代码更新覆盖。
3. 使用 /login 输入原管理员账号与原密码。后端验证原 admins 密码后：
   - 尚无同名员工：自动创建对应员工身份并关联原管理员 ID；
   - 已正确关联：沿用该身份；
   - 同名但未关联、停用或存在冲突：拒绝自动合并，人工核实后另行批准处理。
4. 不预先在员工后台创建同名 adminMO，不同时运行多个账号初始化工具；不通过 SQL 把普通员工直接升级。
5. 管理员一次登录即可进入首页、/projects 和 /admin，无独立管理员二次登录。旧 /admin/login 重定向 /login，旧客户端认证接口执行同一登录。
6. 当前不强制首次/重置后改密；保留主动修改密码、管理员重置和会话撤销。临时密码安全交付，是否启用更严格的上线密码策略由负责人决定，本轮不改变策略。

### 仅在明确批准的恢复情况下设置密码

原密码可用时不要执行。以下命令属于真实账号写入，必须替换并复核绝对路径、解释器与服务用户；先备份并演练副本。

~~~bash
/path/to/approved/venv/bin/python /path/to/approved/source/backend/scripts/set_admin_password.py \
  --database /absolute/path/to/confirmed-production.db --username adminMO
~~~

脚本显示目标路径和账号，要求输入 SET ADMIN，再两次隐藏输入 12–128 位密码。不得把密码放进命令参数、.env、聊天、截图或 Git。脚本不导入 main.py；保留已有 ID，写入 Argon2 哈希并撤销旧会话，不自动启用停用账号或合并冲突身份。它可以创建不存在的管理员，所以执行前必须先确认原账号事实，不能当作日常升级步骤。

### 创建员工

管理员登录 /admin/employees：市场部账号授予 canEditProjects，普通员工不授予；二者均不获得系统管理权限。使用不同账号名与强密码，按安全渠道交付。后端控制读取/写入/管理员权限，不能仅验收按钮隐藏。

## 4. 前端候选构建

只在独立候选目录操作，安装依赖使用 lockfile；不复制本地开发 .env。

~~~bash
cd /path/to/approved/candidate/frontend
npm ci
VITE_API_BASE_URL=/api npm run build
~~~

Dify 地址通过经批准的 VITE_DIFY_EMBED_URL 提供，可留空；示例只能是 https://your-dify-host/chatbot/your-app-id。所有 VITE_ 值会进入浏览器，不得存 API Key、Token、Cookie 或密码。/assistant 为浏览器直接加载 iframe，不需要新增后端代理。

- [ ] 必须在构建进程显式设置 VITE_API_BASE_URL=/api，避免本地 .env 覆盖默认同源值。
- [ ] 扫描 dist/assets：无 localhost/127.0.0.1:8000、无重复 /api/api；浏览器 Network 验证实际请求同源。
- [ ] 仅发布 dist，不发布 artifacts、src、tests、.env、真实 Excel 或数据库。
- [ ] dist/index.html 与工具资源存在，实验入口不在构建中；保留旧 hashed assets 支持已打开的页面。

## 5. Nginx、Cookie 与静态工具

仓库 deploy/nginx/ai-portal.conf.example 为 HTTP 结构示例，不能整份覆盖既有 HTTPS/网关配置。

- /api/、/uploads/、/tools/qstart 均反向代理至仅监听本机的 FastAPI，转发 Host、协议及 Cookie；受保护 uploads 禁止公开 alias、独立静态 location 或 CDN 缓存旁路。
- QsTArT 即使物理存在于 dist/public，也必须经上述代理及服务端员工认证；检查 /tools/qstart/index.html 和其他等效路径。
- 生产 HTTPS 必须 SESSION_COOKIE_SECURE=true，并验证 HttpOnly、SameSite=Lax、可信代理和退出失效。HTTP 示例配合 Secure Cookie 会无法正常登录，不能通过关闭生产 Secure 规避。
- 保留 SPA fallback 与原有业务路径。修改配置经批准后先 nginx -t，通过后再 reload。
- 保留模板 client_max_body_size 5m；后端文件限制 5MB，multipart 有额外开销，必须实测边界，不能承诺恰好 5MB 文件一定通过 Nginx。
- uploads 保持持久路径和权限，不随代码替换或回滚覆盖。服务账号需可读写，不能 chmod 777。
- 从可信网络核验外部无法直连后端端口绕过 Nginx；不能仅凭模板声称服务器已经安全。

## 6. 登录及业务验收

- [ ] /api/health 无登录可为 200；未登录的新闻、工具、项目、管理、uploads 和 QsTArT 请求应为 401，不应按旧公开 API 200 验收。
- [ ] 普通员工读取允许；管理 API 403；项目写入 403。市场部可维护项目但管理 API 403。管理员一次登录可管理。
- [ ] 登录、退出、密码修改/重置、停用、CSRF、限流及旧会话失效正常；正常使用不需要二次验证。
- [ ] 新闻、Banner、工具及原 Exchange 数据数量和图片引用保持，不导入虚构数据凑数。
- [ ] 项目四视角、B/D、编辑两模式、独立节点状态、历史和 409 通过；KPI/日期依据真实日志，不依据 AG。
- [ ] B 卡编号右侧仅一个持久日期标签；跨日/跨年格式正确，节点和 AD/AE/AF 不重复标日期，历史入口保留。
- [ ] 今日/近 7 天/近 30 天包含今日、按北京时间自然日去重并按最新修改时间排序。
- [ ] Exchange：未登录先 401；登录后 enabled=false 列表/投稿为 503，enabled=true 才按实际权限及业务验收；开关不清除原记录或图片。
- [ ] 原生产数据、真实浏览器、HTTPS 和真实 Nginx 路径须现场人工验收，本地测试通过不能替代。

## 7. 认证失败和回滚

1. 暂停放行，先只读检查实际 DB 路径、账号状态/关联、HTTP 状态、Cookie Secure/域名、代理协议、CSRF 和构建 API 地址，不先重置原密码。
2. 保存当前失败版本的代码/日志、数据库一致性快照及 uploads；不打印秘密。
3. 经批准回退成套后端+匹配前端、旧 venv、实际配置。旧版若没有全站认证，不得直接在公网恢复公开访问；维持网关限制或维护页。
4. 优先保留增量数据库结构及已产生的新记录，不删除 employees、history 或新字段，不把登录失败当作恢复旧库的理由。
5. 只有确认必要并获得单独批准，才恢复数据库；必须停全部写入、保全故障库和 WAL/SHM、核对精确备份路径及上线后新增数据。旧库恢复会丢失备份后写入，需要合并方案及业务确认。
6. 回滚后检查原账号、新闻/Banner/工具/Exchange、图片、项目历史及登录保护；备份与旧版本保留到负责人批准清理。
