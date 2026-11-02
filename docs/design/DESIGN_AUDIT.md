# AI Portal 现有设计审计

2026-11-02：项目看板相关页面和专属样式已移除；以下仅保留现有模块审计，不构成全站重设计授权。

审计日期：2026-11-01。范围为当前工作区前端与现有文档；只记录，不执行改造。

证据分级沿用 [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)：源码确认、代码推断、未来建议。本轮未运行浏览器，因此下述尺寸、交互和视觉语言均为源码事实或明确的归纳；不代表线上截图与实际设备验收。

## 1. 页面结构与主题分布

路由依据：`frontend/src/router/index.js`；页面壳依据：`frontend/src/App.vue`。下表的 views / assets / components 路径均相对 `frontend/src/`。auth / admin 不显示普通门户 Header / Footer；普通门户是否渲染还受当前员工状态控制。

| 页面／路由 | 已确认的设计实现 | 差异、硬编码与后续候选 |
| --- | --- | --- |
| 首页 `/`，`HomeView.vue` | 1200px 内容区；Hero、新闻／日历两栏、展开 Planner、home 工具卡；`homepage.css` 局部黄绿中性色 | 与全局冷灰紫色并存；新闻槽 464px、单行 112px 固定；工具正方形卡与两行文案槽位需验证长内容。未来候选：真实内容下检查裁切和密度 |
| 新闻 `/news`，`NewsView.vue` | 紫色英文眉题、40px h1、短下划线、三列封面卡、10px 圆角和阴影 | 与首页同一新闻内容采用两套视觉：分类浅色标签／首页土色小字、封面卡／固定行列表；不能据此直接判为缺陷或擅自迁移 |
| 新闻详情 `/news/:id`，`NewsDetailView.vue` | 860px 正文、40px 标题、18px 摘要、17px 正文；关键词和来源框；loading/404/error | 详情类型统一淡紫，列表按类别区分；独立手写返回、空态、正文样式。未来候选：确认分类语义是否应一致 |
| 工具 `/tools`，`ToolsView.vue` + `ToolGrid.vue` detailed | 紫色页头、两列工具卡、图标、状态、渐变按钮 | 同组件 home 模式是四列正方形卡、封面渐隐、荧光入口；未来维护必须分别检查两种模式，不能全局覆盖 `.tool-card` |
| 助手 `/assistant`，`DifyAssistantView.vue` | 紫色页头、14px 圆角白框；iframe 容器高 `calc(100vh - 248px)`、最小 700px，手机最小 620px；未配置提示 | 外框遵循旧主题；iframe 内部由外部服务决定，无法从仓库确认字体与配色。未来候选：短屏高度与双滚动验证 |
| 互通有无 `/exchange`，`ExchangeView.vue` + `exchange.css` | max 1280px、白底、大编号、单条发现卡、11:10 封面、荧光绿分享、石墨按钮、原生 dialog | 接近首页编辑式语言，但 muted `#677174`、line `#e1e5e4` 与首页不同；专用样式较长；未来候选：长标题、无图、搜索失败、提交和取景小屏验收 |
| 登录 `/login`、改密 `/change-password`，`LoginView.vue` / `ChangePasswordView.vue` | `employee-login.css`：黄色品牌面、荧光 PORTAL、大英文标题、380px 表单、48px 控件；auth 独立外壳 | 与紫色后台壳不同；760px 断点，不等同后台 768px；改密页次要退出按钮没有复用主按钮 class，外观需现场确认 |
| `/admin/login` | 重定向 `/login`，保留 query 并设置默认目标 `/admin` | 没有独立“管理员登录页”设计，不应按历史文档补写一套不存在的页面 |
| 后台首页 `/admin`，`AdminDashboardView.vue` | 紫色壳、三列新闻统计、38px 数字、白卡和快捷入口；≤900px 单列 | 40px 页标题与统计区样式在本页单独定义 |
| 新闻管理 `/admin/news`、`/new`、`/:id/edit` | `NewsAdminView` 自定义表格 min 850px；`NewsCreateView` / `NewsEditView` 自定义 max 900px 双列表单 | 与 `admin-content.css` 重复页头、表格、表单、状态提示；公共表格 min 900px。未来候选：先比较差异再抽公共组件 |
| Banner `/admin/content/banners`、`/new`、`/:id/edit` | `BannerAdminView` / `BannerFormView` 使用 `.content-*`，附加 Banner 预览、图像取景、上传状态与模式表单 | 紫色业务表单包裹黄／灰 Banner 预览；预览嵌入使用容器规则，不是整个后台已改黄绿主题 |
| 栏目视觉 `/admin/content/banners/sections` | `SectionVisualsAdminView`、`MastheadPreview`、`SectionImageCropper`：28px h1、12px 白卡、中性按钮、dark/light 文字模式 | 子页面偏中性，而壳仍紫色；局部大量 HEX 和按钮规则。栏目预览专用 `.masthead-preview-theme` 不应上移到 root |
| 公告 `/admin/content/announcements`、`/new`、`/:id/edit` | `AnnouncementAdminView` / `AnnouncementFormView` 的 `.content-*` 公共表格、状态、表单 | 紫色公共内容系统；删除依赖 window.confirm；与新闻独立表单存在实现重复 |
| 工具管理 `/admin/tools`、`/new`、`/:id/edit` | `ToolAdminView` / `ToolFormView` 使用 `.content-*`，带工具预览与业务状态配置 | 配置状态、入口行为与前台卡片联动；预览范围需分清 home/detailed，不把工具状态当门户主题色 |
| 分享管理 `/admin/exchange`，`ExchangeAdminView.vue` | `.content-*` 列表和后台独立详情 dialog | 与前台发现卡不同；后台删除 confirm、详情弹层与四象限实现不同。未来候选：统一关闭与焦点验收标准 |
| 员工管理 `/admin/employees`，`EmployeesAdminView.vue` | max 1100px，28px 标题、620px 编辑卡、42px 输入、38px 按钮、黄底提交、横向表格滚动 | 位于紫色后台外壳内的黄／中性表单；6px 控件圆角，不同于公共表单 8px；大量局部硬编码 |
| QsTArT `frontend/public/tools/qstart/index.html` | 独立 HTML、内联 CSS／JS、1480px 容器、深蓝渐变头与半透明面板；1050/900/760/600px 响应式 | 不走 Vue 布局；颜色、圆角、alert/confirm 自成体系；源码声明外部 XLSX CDN，不等于本轮已加载或验证。未来候选：按独立工具范围验收 |

## 2. 跨页面审计事项

以下优先级仅用于未来排查顺序，不表示已安排改造。

| 编号 | 证据级别／现象 | 具体源码依据 | 建议与影响 |
| --- | --- | --- | --- |
| A01 | 已确认：两类主题并存 | `main.css :root` 与 `homepage.css`、`exchange.css` | 先确定是否保持分模块演进；不能把旧视觉自动视为待删除实现 |
| A02 | 已确认：相近颜色重复命名／硬编码 | `--home-*`、`--header-*`、`--ink` 等；登录与员工管理大量直接 HEX | 未来可建立共享语义映射，但作用域和业务状态仍应独立 |
| A03 | 已确认：表头／表单／空态重复 | `NewsView`、`ToolsView`、`DifyAssistantView`、`NewsAdminView`、`NewsCreateView`、`NewsEditView` 与 `.content-*` | 提取前先比较 850/900px 表格、padding、错误状态及上传流程，避免机械合并 |
| A04 | 已确认：尺寸体系不同 | 卡片圆角 8/9/10/12/14px；表单高度 42/44/48px；max-width 1100/1200/1280/1440px | 当前按模块延续；未来组件化需要明确密度和适用容器 |
| A05 | 已确认：字体栈与字重不统一 | body Inter；Header/首页相关组件系统字体；Exchange 650 | 未发现字体资源声明；不同系统字体和非标准可用字重的实际效果待测，不能承诺统一渲染 |
| A06 | 已确认：断点分散 | 767/768、760、650、600、930、1099 等；`BannerSlide` 容器查询 | 未来可整理断点意图，不能直接替换成单一框架断点；测临界宽度及中间尺寸 |
| A07 | 已确认：CSS 后段覆盖 | `WorkCalendar` 末段 home variant；`ToolGrid` 末段 home variant | 阅读与文档以最终级联为准。不能只摘第一处规则 |
| A08 | 已移除 | 原项目专属非 scoped CSS 已随模块删除 | 其他模块保持原作用域，不推广主题 |
| A09 | 已确认 + 推断：首页不是所有组件都完整中性化 | `.home-workspace` 内重映射；`PlannerExpandPanel` 兄弟组件没有该变量祖先；`PriorityMatrix` Teleport 到 body 仍引用 `--color-*` | 可能看到全局紫色与首页中性并存；应检查计算样式和弹层截图后决定，不擅自扩大覆盖 |
| A10 | 已确认：确认与弹层实现分散 | 原生 dialog、Teleport section、就地 DeleteConfirm、window.confirm 并存 | 四象限焦点约束与滚动行为仍需验收。未来统一检查焦点约束、Esc、背景滚动和关闭恢复 |
| A11 | 已确认：减少动态效果覆盖不完整 | 各组件媒体查询；HeroBanner 5000ms 计时；HomeView planner 过渡 | reduced-motion 下 CSS 取消过渡不代表轮播停播；触屏、键盘与可选暂停策略待设计确认 |
| A12 | 已确认：密集文字与固定槽位 | 首页新闻三行固定高度、工具文字行槽与遮罩 | 未来验证长中文、跨年标签、浏览器缩放、390px 和无图情形；不从静态值直接宣称内容溢出 |
| A13 | 已确认：缺少统一状态组件和 Token | 成功／错误色分布多个文件，loading 文本／骨架／页内反馈分别实现 | 可先整理统一语义与文案，再决定组件化；不把品牌荧光绿替代现有成功绿 |
| A14 | 代码推断：门户壳与正文主题衔接值得核对 | Header 黄绿 max1600；Footer 冷灰 max1200；Exchange max1280 | 是源码层面的宽度／主题差异；是否视觉不协调需截图和产品判断 |

## 3. 既有文档与代码的差异

本轮保留所有既有文档原内容。新规范依据实际代码；历史说明不是当前主题授权。

| 文档 | 已发现差异 | 处理方式 |
| --- | --- | --- |
| `frontend/README.md` 目录／数据来源说明 | 仍写 旧版数据来源说明已更新；内容来自 API，个人时间线来自浏览器存储 | 已同步当前 README，不改变其他功能 |
| 根 `README.md` V2.4 等历史章节 | 写普通门户免登录、尚无普通用户／角色体系等；顶部现状及 `App.vue`、`routeAccess.js` 已体现员工入口和权限分流 | 保留历史内容；根 README 已说明早期记录不代表当前流程，不把历史内容写成新规范 |
| `docs/releases/release-readiness-review.md` Header 验收表 | 旧审查为历史快照；当前路由已移除该模块 | 保留原审查记录；当前路由结构按源码记录，不改写历史验收结论 |
| `artifacts/design-system-v1*.html` 等设计实验 | 存在版本号与多种预览，不由路由直接引用为页面样式 | 仅视为实验产物；`homepage.css` 的 V1.2 注释也仅限其局部实现，不代表全站版本 |

## 4. 未确认事项与建议的后续验收

- 未确认：当前运行服务／生产构建对应哪个提交、账号权限下实际页面内容、后台配置的 Banner／栏目图、图片网络失败时的实际观感、外部助手主题、设备字体回退。
- 未确认：色彩对比度是否达标、浏览器 zoom、320px 最小宽度下全站无横向溢出、触屏拖放、键盘循环、原生 dialog 的跨浏览器细节。
- 建议先做只读截图／交互验收：1440/1280/930/390px，补充各模块断点两侧；使用真实长文本、空／错／加载状态、无图与自定义浅／深栏目头。需要数据时优先隔离环境，不触及生产导入或改写。
- 产品确认后才讨论统一 Token、基础组件、主题迁移。所有候选先进入 [STYLE_EXPLORATIONS.md](STYLE_EXPLORATIONS.md)，经明确授权实施后再更新生效规范。

## 5. 维护记录

| 日期 | 范围 | 结果 |
| --- | --- | --- |
| 2026-11-01 | 当前源码静态盘点、路由／变量／样式／交互审计 | 建立基线；未修改业务源码，未执行视觉重构或部署；浏览器验收待补 |
