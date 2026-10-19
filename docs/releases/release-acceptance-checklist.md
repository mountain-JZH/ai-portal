# AI Portal V1.8 发布验收清单

日期：2026-10-19。`[x]` 仅代表本轮本地已执行；生产、真实浏览器、人工批准仍为 `[ ]`。本清单不是发布授权，所有生产动作需单独批准。关联文档：[审查报告](release-readiness-review.md) / [发布与回滚手册](ecs-deployment-runbook.md)。

ECS 信息来源说明：下列现场项来自用户提供的 2026-10-19 实际 SSH 检查结果，不是 Codex 自行连接服务器核验。用户确认 ECS 源码为 `f2e9abe`、Python 为 `3.12.3`、数据库为 `/opt/ai-portal/data/ai_portal.db`、uploads 为 `/opt/ai-portal/uploads/`、入口使用 Nginx，并存在 `/opt/ai-portal/update.sh`；生产数据库备份使用 `deploy/scripts/backup_db.py` 的 SQLite Backup API。本轮未执行该脚本、未更新 ECS、未部署。

## 1. 版本与范围

- [x] 当前 main / HEAD `f2e9abe06b4abee9192c7b4343b69606c59a345b` 已记录。
- [x] 缓存 origin/main 差异 0/0；未把缓存当在线远程或生产版本。
- [x] 审查前 13 modified + 47 untracked 逐文件分类；暂存区为空。
- [x] Banner V2 正式组件已跟踪且相对 HEAD 无差异，不作为实验误删。
- [x] 本轮未修改业务代码、环境变量、真实 SQLite、用户图片；未提交/推送/部署。
- [ ] 生产 SHA/tag 或源文件快照及 dist 指纹已由运维取得。
- [ ] 对真实生产基线重新比较完整候选范围，不只比较本地 HEAD。
- [ ] 人工确认 A/B 文件清单；23 个未跟踪正式依赖已完整纳入候选。
- [ ] 原型/历史截图保留仓库但不进入 webroot；测试/fixture 不进入运行包。
- [ ] 用户选择性提交/审核形成不可变候选 SHA（本轮不代执行）。
- [ ] 发布模块、延期模块、负责人、回滚负责人及维护窗口已签字。

## 2. 本地工程与隔离验证

- [x] `npm.cmd run lint` 通过，未引入源码修复差异。
- [x] `npm.cmd run build` 通过；dist/index.html 和 dist/tools/qstart/index.html 存在。
- [x] **发现当前 dist 带 loopback API，因此不批准使用它部署。**
- [x] 前端 51 项 Header/Exchange/裁剪/报头/工具相关测试通过。
- [x] 后端 Exchange 13 项测试通过，含新闻鉴权/CRUD 回归。
- [x] 后端工具图片 8 项测试通过。
- [x] 后端栏目图片 12 项测试通过。
- [x] backend 主要文件和 backup_db.py 共 12 文件 py_compile 通过。
- [x] 隔离 HTTP 带图投稿 → 后端进程完全重启 → 列表/图片持久化 → 管理详情/删除 → 列表与图片清理通过。
- [x] 活跃 WAL 临时数据库用现有 backup API 备份，完整性及记录验证通过。
- [x] 栏目图片 SQL 失败会遗留新文件已复现，列为问题而非偷偷修复。
- [x] 新增文档格式检查及 git diff --check 通过（最终本地检查）。
- [x] 原有 122 个受审查文件内容哈希无变化，仅新增三份发布文档。
- [ ] 未完成：真实浏览器视觉与触摸验收；不能用 SSR/HTTP 测试代替。

## 3. ECS 前置取证（用户提供的现场快照已记录；发布窗口仍须复核）

- [ ] 实际主机、账号、项目根、运行进程、服务管理方式和服务名已确认。
- [ ] 实际 WorkingDirectory、EnvironmentFile、worker/可信代理参数已确认。
- [x] 用户提供的 SSH 实检显示 ECS Python 为 3.12.3；Codex 未独立连接核验，旧 venv 路径仍待发布窗口复核。
- [ ] 新候选独立 venv 安装 requirements、pip check 成功；旧 venv 原路径保留。
- [ ] Pillow 13.0.0、FastAPI、Uvicorn、python-multipart 在候选环境可 import/运行。
- [ ] Node 满足 engines；使用 package-lock 与 npm ci，而非随意升级依赖。
- [x] 用户提供的 SSH 实检确认数据库路径为 `/opt/ai-portal/data/ai_portal.db`；发布窗口仍须由执行人复核实际进程连接。
- [ ] 数据库 journal_mode、integrity_check、schema、表数量已记录。
- [x] 用户提供的 SSH 实检确认持久化 uploads 为 `/opt/ai-portal/uploads/` 且当前入口使用 Nginx；发布窗口仍须复核 alias 与权限。
- [ ] DB 及父目录可写、上传目录可写、Nginx 可读/遍历，未用 chmod 777。
- [ ] 系统/数据盘空间覆盖备份、新旧 venv、源码、dist、uploads 及余量。
- [x] 用户提供的 SSH 实检确认当前入口使用 Nginx；TLS、SPA fallback、API 代理、Cookie 转发与缓存细节仍须在发布窗口复核。
- [ ] 5m 请求体与 5MB 单文件 + multipart 的边界行为已验证/另行处理。
- [x] 用户提供的 SSH 实检确认 `/opt/ai-portal/update.sh` 存在；本轮未执行、未修改，正式部署前仍须单独审阅。

## 4. 备份与迁移

- [ ] 私有备份目录位于 webroot 外；访问权限、空间、保密要求已确认。
- [ ] 所有 DB/uploads 写入方已停，维护窗口已批准。
- [x] 已记录生产备份方式为 `deploy/scripts/backup_db.py` 的 SQLite Backup API；本轮没有对生产数据库执行备份，发布窗口仍须实际执行并验收。
- [ ] 唯一 DB_BACKUP 路径已记录，integrity_check、行数、schema 验证通过。
- [ ] uploads、旧源码、旧 dist、实际私有环境、unit/drop-ins、Nginx 配置已备份。
- [ ] 旧 venv 原路径及 pip freeze 已保存，不原地升级后丢失回滚环境。
- [ ] 备份校验和、图片清单及隔离恢复演练通过，不只检查文件存在。
- [ ] 生产备份副本上幂等迁移两次，旧列数据指纹和编号序列未变。
- [ ] 经批准才对真实 DB 执行候选 database.py；未上传本地 DB/演示数据。
- [ ] banners.banner_type 默认 standard，旧图文数据保持。
- [ ] tools.cover_image_url 默认空，旧工具 icon/动作/状态/排序保持。
- [ ] section_visuals/text_mode 建立或补列成功，历史图片引用保持。
- [ ] exchange_resources、AUTOINCREMENT 和 UTC 日期规则正确，无虚构种子导入。
- [ ] 所有旧表按旧列指纹与备份一致，管理员数据未重建、未注入测试口令。
- [ ] 迁移失败时先检查实际 schema，不盲目回退数据库或 DROP 新字段。

## 5. 生产候选构建与切换

- [ ] 在独立候选目录使用完整批准 SHA 构建，没有读取本地开发 .env。
- [ ] 明确 `VITE_API_BASE_URL=/api`（或批准的等效同源配置）。
- [ ] 产物无 localhost/127.0.0.1:8000、无 /api/api，实际 Network 同源请求正常。
- [ ] Dify Embed 地址经批准，VITE_ 未放入 API Key/Token/口令。
- [ ] dist 有 index、QsTArT，原型 HTML、fixture 和私有配置未暴露。
- [ ] 记录候选 SHA、依赖锁/制品校验和、模块 manifest。
- [ ] 只替换批准的后端源文件，不覆盖 .env、真实 DB、uploads 或其他 patch。
- [ ] systemd 新 venv 切换另行批准，WorkingDirectory 与持久化路径保持。
- [ ] 后端先启动并通过 health/API/鉴权检查，再发布前端。
- [ ] 前端候选目录与旧目录可回退，旧 hashed assets 保留以支持旧页面。
- [ ] 普通目录双 rename 的短暂空窗已告知，或已采用验证过的原子入口方案。
- [ ] 未整份覆盖实际 Nginx/TLS/网关配置；需要修改时先 nginx -t 后 reload。
- [ ] 一期 EXCHANGE_ENABLED=false，未复制本地 enabled=true 的环境文件。

## 6. 首页、Header、新闻、工具人工验收

- [ ] 首页桌面主轴、128px 报头、464px 新闻/右侧槽位无遮挡。
- [ ] 手机导航与内容无横向溢出；Tab/Enter/Focus/reduced-motion 正常。
- [ ] Header 当前页活动态及 /news、/exchange、/tools、/admin 入口正确，无空路由。
- [ ] standard/image_only 混合 Banner 高度稳定、渐隐/CTA/图片/排序/轮播正确。
- [ ] 历史 Banner dify 动作是否有实际记录已核实，若有已安排人工兼容处理。
- [ ] 首页真实已发布新闻最多三条，整条进入正确详情；草稿不公开。
- [ ] 新闻列表、详情直刷和安全外链正常，旧视觉差异已明确接受或列延期。
- [ ] 栏目背景上传、拖动/缩放/确认/取消/深浅色保存和刷新正确。
- [ ] 工具 JSON 旧记录可读；新 Multipart 创建/修改、保留/替换/移除封面正常。
- [ ] 首页封面、渐隐、启动入口无错位；不可用工具不误点击。
- [ ] /tools 完整工具列表、route/static/external 跳转和安全属性保持。
- [ ] QsTArT 静态入口、路由资源存在且可打开。
- [ ] 日历/待办切换、日期、标记、保存、展开与个人数据保留。
- [ ] 右侧槽位无按钮换行或底部遮挡；长内容局部滚动可用。
- [ ] 管理员登录/退出、Cookie Secure/HttpOnly、未登录管理 API 401 正常。
- [ ] 栏目保存失败残留图片风险已接受或另行修复，无自动删除旧图。

## 7. Exchange 一期关闭验收

- [ ] 实际服务开关为 false，公共 GET 和 POST 均 503。
- [ ] /exchange 不冒充只读开放状态，分享表单不会显示虚假的成功编号。
- [ ] 开关关闭后的错误与分享入口反馈经人工确认可接受。
- [ ] 管理 API 不受公开开关替代保护，未登录仍拒绝。
- [ ] 已有 Exchange 图片若敏感，访问边界独立保护；关闭开关不被当作撤图机制。
- [ ] 后端直连端口不能绕过批准的边界。

## 8. Exchange 二期单独启用验收（一期不得勾选）

- [ ] 内网/VPN/网关事实证据已取得，外部请求确实被拒绝。
- [ ] 保护覆盖 /exchange、公开 GET/POST、/uploads/exchange/ 及关联可绕过路径。
- [ ] 可信代理链与实际客户端 IP/限流行为已验证，未信任任意 XFF。
- [ ] 单独批准开关变更与对应服务重启；未默认开启。
- [ ] 专用测试分享收到 201 后才显示服务器生成编号。
- [ ] 无图分享保持编号视觉；有图取景 11:10、导出与最终服务器图一致。
- [ ] 管理列表和完整详情读取同一资源，日期时区正确。
- [ ] 后端重启后记录和图片仍存在，无本地会话冒充持久化。
- [ ] 编号 025/25、标题、关键词搜索正常；最新 200 条范围限制已知。
- [ ] 多条随机轮内无重复，搜索后队列继续；零/一条情况正常。
- [ ] 确认删除后公开列表不再显示，图片正确清理且不影响其他类别/其他投稿。
- [ ] 删除失败/清理待处理会明确提示并被追踪；成功 INFO 日志可审计。
- [ ] 编号不因普通删除复用；不接受客户端指定身份/编号/日期。
- [ ] 大图、伪造 MIME、损坏、动画、超像素、超请求体及限流反馈正确。

## 9. 回滚准备与稳定性观察

- [ ] 纯前端回滚已演练，不触及 DB/uploads。
- [ ] 后端源码+实际 service 配置+旧 venv 可恢复，新前端 API 依赖同步处理。
- [ ] 已确认增量 schema 可保留；恢复旧 DB 需额外审批及新增写入合并方案。
- [ ] 故障 DB/WAL/SHM 处理在停全部写入后按精确路径执行，不用批量删除。
- [ ] 图片回退只恢复映射/缺失文件，不覆盖或删除发布后的新上传。
- [ ] Exchange 紧急关闭方案已记录，同时理解其不阻断静态图片。
- [ ] 上线即刻、观察窗口和下一工作日的服务、5xx/413/429、DB 锁、图片、磁盘检查均记录实际结果。
- [ ] 回滚后旧首页/新闻/工具/后台登录/新旧图片及数据均验收。
- [ ] 备份/旧版本清理由负责人以后另行批准，不自动清理。

## 签字与最终决定

- 候选 SHA / 制品校验和：待填写。
- 生产基线 / DB / uploads / 服务 / 入口：待填写（敏感值记录在受控工单）。
- 生产备份与恢复演练记录：待填写。
- 浏览器验收记录：待填写。
- 一期/二期范围、风险接受项：待填写。
- 发布负责人 / 验收人 / 回滚负责人 / 批准时间：待填写。
- **当前决定：NO-GO；完成阻塞项核实与人工批准后重新评审。**
