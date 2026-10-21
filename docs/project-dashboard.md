# 项目管理员 Excel 导入说明

员工入口 /projects，管理员受控导入入口 /admin/projects。唯一登录页为 /login；管理员登录一次获得服务端管理权限，不再执行二次认证。市场部维护权限不授予系统管理权限。

日常维护已转为网页。Excel 仅供管理员初始化或受控批量导入，不向普通员工开放，不覆盖已被网页维护的不同内容。认证、上线、账号兼容见 [部署指南](../DEPLOYMENT.md)；当前维护与历史见 [project-maintenance.md](project-maintenance.md)。

## 导入契约

- 只接受 .xlsx，保持 Sheet1、前三行多级表头和 A～AG 顺序；最大 4 MB。
- A 为原台账序号，不是数据库永久 ID；B/C 为组长/负责人，D/E 为资源/项目名。
- F～K 为管理权、所有权、时序/价值评级、客户类型、片区；L～Q 为各业务规模原文。
- R～AB 为固定 11 节点，AC 为原始当前阶段，AD/AE/AF 为三项完整文字，AG 为原进度标记。
- 保留特殊节点状态、长文本、未知单位及实际数值；不推断前置节点完成。与/&/＆第三节点别名按受控规则匹配。
- 读取已保存公式结果，不执行公式；缺少缓存、宏、外部工作簿/连接、异常表头或超限压缩包阻止导入。
- 上限 10000 条数据行、32 MB 解压大小、2500 个 ZIP 条目。真实公司文件只能在批准的受控环境核验，不提交 Git。

## 预览、确认及冲突

1. 选择文件，检查新增/更新/未变化/跳过、逐行预览及错误。
2. 预览只保存短期、绑定管理员和数据修订的令牌，不写业务项目。取消预览不删除项目。
3. 确认事务重新验证令牌、数据库修订及权限；已被其他操作改变时返回 409，整批失败而不是部分覆盖。
4. 名称与资源冲突、同批重复或存在网页维护过的不同内容均拒绝；不自动合并、强制覆盖或删除未出现在 Excel 中的旧项目。
5. 实际变化更新版本并留痕，管理员导入来源独立标记。初始化记录不是项目进展更新。
6. 名称和资源同时变化且无关联时，导入无法可靠识别“全部改名”；应使用网页维护已有项目，禁止用导入猜测合并。

## 权限与统计

所有 /api/admin/projects 接口由统一会话及服务端 get_current_admin 保护，写请求另需 CSRF。未登录 401，非管理员 403；市场部项目维护授权不允许导入。

员工看板使用真实 SQLite：四视角、同一 B/D 数据源。完成数仅计精确“已完成”；有多个“进行中”时 B 卡选择固定顺序最靠前者。导入保留 AC 原文；网页实际编辑节点且存在进行中时才同步 AC。

今日更新 KPI、1/7/30 日范围和编号旁日期来自实际业务修改日志，按北京时间去重，排除创建/初始导入/基线/无变化/仅 AG 变化。管理员旧阶段分布仍可核对 AC，不与员工 B 卡显示解析混淆。

## API

| 操作 | 接口 |
| --- | --- |
| 管理汇总与详情 | GET /api/admin/projects、GET /api/admin/projects/{id} |
| 上传预览 | POST /api/admin/projects/imports/preview，FormData 字段 file |
| 确认 | POST /api/admin/projects/imports/confirm，提交预览 token |
| 取消本人预览 | DELETE /api/admin/projects/imports/preview/{token} |

管理 UI 使用 ProjectDashboard、ProjectDetail、ProjectStageProgress 和 projects.css，它们仍被正式导入页引用，不能当作废弃实验删除。

## 安全本地验收

只使用新版 backend/scripts/run_single_login_acceptance.py 和 copy_acceptance_password.ps1，流程见 [认证文档](employee-authentication.md)。它们生成临时 SQLite、虚构数据与 DPAPI 保护的临时密码，不读取原库或真实 HTML。

旧 run_project_demo.py、run_project_acceptance.py 不属于生产依赖，文件保留但被本次拟提交清单排除；不要运行其旧密码输出流程，不把它们的日志、凭据或生成工作簿提交 Git。

## 验证

后端各 test_*.py 使用独立进程，临时 DB/uploads；前端执行 node --test --test-concurrency=1 tests/*.test.mjs、非修复模式 Lint 与同源生产 Build。真实浏览器、实际 Excel 及生产代理均需另行授权验收，自动化不替代。
