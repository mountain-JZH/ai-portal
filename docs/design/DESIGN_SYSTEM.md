# AI Portal 当前 UI 设计规范

基线日期：2026-11-02。适用于当前工作区源码，不表示线上版本或视觉重构已验收。

2026-11-02 精简：已移除服务端项目看板及其导航、后台局部主题。首页独立个人时间线改名为 `PersonalTimeline.vue`，存储键及行为保留。其他模块主题不变。

## 1. 证据、范围与使用方式

- **已确认**：可直接在模板、CSS、组件逻辑或路由中找到的实现。下文未特别标注的数值均属此类；“确认”指源码定义，不代表浏览器实测。
- **代码推断**：由多处实现归纳出的设计规律或可能的级联结果，尚未作为独立产品规范确认。
- **未来建议**：供后续讨论的改进，不是当前实现，也不自动授权改造。

项目根目录为 `D:\workspace\ai-portal`。前端位于 `frontend/`，使用 Vue 单文件组件、JavaScript、Vue Router 和原生 CSS；`frontend/package.json` 声明 Vue `^3.5.40`、Vue Router `^5.2.0`、Vite `^8.1.5`，这是依赖声明范围，不是已验证安装版本。未声明 UI 组件库、Tailwind 或 Sass。入口为 `frontend/src/main.js` → `App.vue` → `router/index.js`；主 CSS 为 `assets/main.css`，导入 `admin-content.css`。后端目录存在 FastAPI / SQLite 实现，本规范不调整后端契约。

本文源码路径未加前缀时均相对 `frontend/src/`。引用以“文件 + 选择器／符号”为定位依据，避免行号随代码修改失效。先识别目标模块，再复用其现有组件和变量；不要仅因全局存在 `--color-primary` 就用蓝紫色覆盖所有模块。

本轮仅做静态分析，未启动服务或进行浏览器视觉、触控、对比度、截图和字体加载验收。`artifacts/` 下的设计实验 HTML 不属于路由生效样式，不能代替源码。

## 2. 设计定位与模块边界

**代码推断：整体是企业内部工作门户，处于分模块演进状态。** 当前主要有两类设计语言：

| 语言 | 已确认的实现依据 | 适用范围 |
| --- | --- | --- |
| 编辑式、扁平、明亮的工作台 | 石墨色文字、白／浅灰表面、黄色和荧光绿标记、细边框、局部弱阴影、大标题与紧凑数据并置 | 门户 Header、首页局部、登录／改密、互通有无、部分后台内容 |
| 蓝紫色、柔和阴影的卡片式企业界面 | `main.css :root` 蓝紫主色、冷灰背景、圆角、渐变按钮／品牌块和悬浮阴影 | 新闻中心与详情、独立工具中心、助手外壳、多数管理后台、门户 Footer |

不能将其描述为已经统一的全站黄绿主题，也不能将全站概括为玻璃拟态。半透明与渐变出现在局部；QsTArT 是单独的半透明深蓝工具界面。

**代码推断的延续原则**：信息可读优先；通过标题、分隔线、留白和卡片分组；品牌强调与业务状态分开；交互反馈轻量；模块主题局部生效。现有断点、阴影和字体并非全站统一设计尺度。

## 3. 颜色 Token

### 3.1 全局生效 Token

定义：`assets/main.css :root`。

| CSS 变量 | 真实值 | 当前含义 |
| --- | --- | --- |
| `--color-bg` | `#f7f9fc` | body 默认背景 |
| `--color-surface` | `#ffffff` | 卡片／表单表面 |
| `--color-surface-soft` | `#f4f7fb` | 柔和表面、表头、Footer |
| `--color-glass` | `rgba(255, 255, 255, 0.76)` | 已声明的半透明值；不等于全站都使用 |
| `--color-text` | `#152033` | 主文字 |
| `--color-text-secondary` | `#526075` | 正文／次级文字 |
| `--color-muted` | `#8995a8` | 辅助文字 |
| `--color-border` | `#e1e7f0` | 普通边框 |
| `--color-border-strong` | `#cdd7e5` | 表单／强调边框 |
| `--color-primary` | `#5b5bd6` | 蓝紫主色 |
| `--color-primary-soft` | `#eef2ff` | 选中／浅主色表面 |

### 3.2 首页局部 Token

定义：`assets/homepage.css .home, .masthead-preview-theme`，不定义在 `:root`。`body:has(.home)` 将首页 body 背景设为 `#ffffff`。

| CSS 变量 | 真实值 | 当前含义 |
| --- | --- | --- |
| `--home-surface` / `--home-subtle` | `#ffffff` / `#f5f6f7` | 白色／浅灰表面 |
| `--home-text` / `--home-secondary` / `--home-muted` | `#22292c` / `#586165` / `#697378` | 主／次／辅助文字 |
| `--home-border` / `--home-border-strong` | `#e5e8e9` / `#c9cfd2` | 分隔与输入边框 |
| `--home-yellow` | `#f7b334` | 精选边框、品牌强调 |
| `--home-green` | `#8dfc08` | 工具入口文字底部荧光标记 |
| `--home-earth` | `#6d5b55` | 类型文字、焦点等局部强调 |

`WorkCalendar.vue .home-workspace` 另将内部 `--color-*` 重映射至上述中性色，其中 `--color-primary: #22292c`、`--color-primary-soft: #eceff0`。这不是根变量变更；`PlannerExpandPanel` 及其其他子组件不自动获得该重映射。

同文件的非颜色 Token 也保留原名，供维护时定位：

| CSS 变量 | 真实值 |
| --- | --- |
| `--home-radius` | `12px` |
| `--home-masthead-height` | `128px` |
| `--home-slot-height` | `464px` |
| `--home-news-row-height` | `112px` |
| `--home-motion-fast` / `--home-motion` | `140ms` / `220ms` |
| `--home-ease` | `cubic-bezier(.2, .8, .2, 1)` |
| `--home-font` | 下文系统字体栈，原值见 `homepage.css` |

### 3.3 其他模块的真实局部颜色

| 来源与作用域 | 定义 |
| --- | --- |
| `AppHeader.vue .header` | `--header-bg: #ffffff`；foreground `#22292c`；muted `#6d5b55`；active `#f7b334`；brand-green `#8dfc08`；底边 `#e6e9ea` |
| `SectionMasthead.vue` | 默认文字 `#22292c` / `#586165`；`.is-light` 为 `#fff` / `#f1f3f3`；图片失败恢复深色文字 |
| `assets/exchange.css .exchange-page` | `--white: #fff`、`--mist: #f5f6f7`、`--ink: #22292c`、`--yellow: #f7b334`、`--green: #8dfc08`、`--earth: #6d5b55`、`--muted: #677174`、`--line: #e1e5e4` |
| `assets/employee-login.css` | 黄色品牌面／主按钮 `#f7b334`；hover `#efaa29`；荧光标记 `#8dfc08`；输入边框 `#ccd1d3`；错误 `#a72435` |
| `ToolGrid.vue .tool-action`，独立工具中心 | 渐变 `linear-gradient(135deg, #4f7cff, #655ce7)`；不是全局主色别名 |

这些同义局部变量目前没有统一映射层。文档中的颜色角色只是索引，不是新增到源码的 Token。

### 3.4 状态色与分类色

| 场景 | 已确认配色 | 定义位置 |
| --- | --- | --- |
| 后台成功提示 | 背景 `#eff8f4`；文字 `#356b55`；边框 `#cfe8dc` | `admin-content.css .content-status-success` |
| 后台错误提示 | 背景 `#fcf3f3`；文字 `#9b4545`；边框 `#ecd1d1` | `.content-status-error` |
| 后台启用标签 | 背景 `#eaf5f0`；文字 `#3f765f` | `.content-state.is-active` |
| 默认后台标签 | 背景 `#f1f3f6`；文字 `var(--color-muted)` | `.content-state` |
| 工具可用 | 背景 `#ecf8f2`；文字 `#28745b` | `ToolGrid.vue .tool-status--available` |
| 工具待接入 | 背景 `#fff7e5`；文字 `#9a6a18` | `.tool-status--integrating` |
| 新闻通知／宣贯／行业动态标签 | `#edf4ff` / `#476d9f`；`#f2eefb` / `#725f99`；`#eaf5f0` / `#3f765f`（背景／文字） | `NewsView.vue .type` 及修饰类 |
| 四象限类别 | `#D95C5C`、`#D59A32`、`#4D7ED9`、`#4FA879` | `utils/quadrantStorage.js QUADRANTS`，同时配三角／圆／方／菱形 |
| 四象限空／完成 | `#8B95A7` / `#4FA879` | `QUADRANT_STATUS_COLORS` |
| 日历绿／黄／红标记 | 主色 `#35a86b` / `#d59a18` / `#df5660`；浅色 `#eff9f3` / `#fff8e8` / `#fff1f2` | `WorkCalendar.vue --marker-color / --marker-soft` |

**延续规则**：按原组件的业务语义使用颜色；荧光绿品牌标记不自动代表成功状态。全局尚无统一 success / warning / danger 变量。

## 4. 字体与排版

### 4.1 字族

- 全局 `main.css body`：`Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif`。
- 首页 `--home-font`、Header、登录、Exchange：`-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif`。首页通过相关组件引用，不等同 `.home` 为所有后代统一设置 font-family；HeroBanner 未显式使用 `--home-font`。
- Exchange 的代码片段另用 `ui-monospace, 'SFMono-Regular', Consolas, monospace`。
- `main.css` 让 button / input / textarea / select 继承字体。本轮检索未发现前端源码的 `@font-face` 或 Google Fonts 引入，不能保证 Inter 实际存在，最终回退取决于设备。

### 4.2 已采用的文字层级

| 场景／选择器 | 字号／字重／行高／字距 |
| --- | --- |
| 新闻列表 `NewsView .page-header h1`、公共后台 `.content-page-header h1` | `40px` / 未显式声明，保留 h1 默认粗体行为 / `1.25`；移动端 `32px` |
| 新闻详情 `NewsDetailView h1` | `40px / 默认标题字重 / 1.3`；≤600px 为 `30px` |
| 新闻详情 `.summary` / `.content p` | `18px / 1.8`；`17px / 1.85`；≤600px 正文 `16px / 1.9` |
| 首页栏目 `SectionMasthead h2` / `p` | `24px / 600 / 1.25 / normal`；`14px / 400 / 1.5 / normal` |
| 首页新闻 `.news-title` / `.news-summary` | `16px / 600 / 21px`；`13px / 20px`；标题、摘要各截断两行 |
| 首页工具 `h3` / `p` | `18px / 600 / 1.35`；`14px / 400 / 1.55`；各限两行 |
| Header `.brand-title` / `.nav-link` | `25px / 700 / 1.4`；`15px / 500 / 24px`，当前项 `600` |
| 登录品牌 h1 / 表单 h2 | `clamp(46px, 5.4vw, 88px) / 700 / 1.04 / -.045em`；`30px / 700` |
| Exchange `.intro h1` | `clamp(32px, 4vw, 46px) / 650 / 1.2 / -.04em`；≤760px 36px，≤430px 32px |
| 后台普通表格／标签 | `14px` 表格正文；`12px` 表头与状态；公共标签字重 `600` |

全局没有 `--font-size-*` 或统一标题 reset，也没有统一 body line-height。辅助字号存在 8–13px、字重存在 650／780 等局部值，不应误写为标准化排版尺度。**未来建议**：统一字号、行高和最小可读文字前，先检查密集看板与小屏的承载能力。

## 5. 布局、留白与响应式

### 5.1 页面壳与主要网格

| 范围 | 源码定义 |
| --- | --- |
| 门户壳 `App.vue` | flex 纵向、`min-height:100vh`、内容 flex:1；非 admin/auth 布局在允许渲染时显示 Header 和 Footer |
| 默认文档 | `main.css`：body `min-width:320px`；html `overflow-y:scroll` 与 `scrollbar-gutter:stable`，为纵向滚动条保留空间 |
| 首页 `HomeView.vue` | 宽 `calc(100% - 48px)`、max 1200px、顶部 32px；新闻／工作区列 `minmax(0,2.2fr) minmax(310px,.9fr)`，gap 40px，顶部间距 48px |
| 首页固定槽位 | `homepage.css`：栏目头 128px、新闻／工作区槽 464px、新闻行 112px × 3；工作区具体覆盖见 `WorkCalendar.vue .home-workspace` |
| Header | max 1600px、宽 `calc(100% - 96px)`、主体 min-height 87px，三列品牌／导航／签名，另有账号行 |
| Footer | max 1200px、宽 `calc(100% - 48px)`、min-height 96px |
| 新闻列表／详情 | 外层 max 1200px；列表 3 列、gap 24px；详情正文 max 860px；列表上下 padding 56/96px，详情 48/96px |
| 独立工具 | `ToolGrid` detailed 两列、卡片 min-height 244px；首页 home 四列正方形卡、gap 16px |
| Exchange | `.exchange-inner` max 1280px、padding `46px 40px 28px`；主发现卡左右 `1.06fr / 1fr`，封面比例 11:10 |
| 后台壳 | `AdminLayout` max 1440px、宽 `calc(100% - 48px)`；左导航 220px；内容 padding `40px 0 80px 40px`，页面 max 1200px |
| 公共后台表单 | `admin-content.css .content-form` max 900px、padding 32px；双列 gap `22px 24px`；输入／选择框高 44px |

**代码推断**：常见空间值为 8、12、16、20、24、32、40、48px，但存在 38、42、22、28px 等值；没有统一 spacing Token，也不是严格 8px 网格。

### 5.2 真实断点，不合并成虚构的全站断点

| 模块 | 生效规则摘要 |
| --- | --- |
| Header | ≤1250px 缩边距和列宽；≤1000px 导航另起一行；≤600px 两侧 16px、字号收缩；无汉堡菜单实现 |
| 首页 | ≤1024px gap 24px、侧栏 min 300px；≤768px 主区单列；≤600px 容器减 32px；栏目头 ≤480px 纵向布局、h2 22px / 30px |
| 首页工具 | ≤1050px 两列；≤600px 单列 |
| 新闻列表 | ≤1099px 两列；≤767px 单列、gap 18px、h1 32px |
| 新闻详情／工具页／助手 | ≤600px 各自调整容器和标题；工具 detailed 在 ≤900px 先改单列 |
| 后台壳 | ≤1024px 侧栏 190px；≤768px 侧栏改顶部五列导航；≤500px 两列导航；≤360px 隐藏 AI 品牌块 |
| 公共后台内容 | ≤767px 标题／操作纵排、表单单列；表格保留 min-width 900px，通过外层横向滚动；新闻管理自有表格 min-width 850px |
| Exchange | ≥1500px、≤1120px、≤760px、≤430px 布局规则，另有 ≤500px 局部规则；≤760px 发现卡单列 |
| 登录／改密 | ≤760px 品牌与表单从左右分栏改上下排列 |

`BannerSlide.vue` 另使用容器查询 `@container banner-frame (max-width:600px)` 和 `cqw` 排版单位；它依据容器宽度，不应混同 viewport 媒体查询。

## 6. 圆角、阴影与组件复用

`main.css :root` 圆角：xs 6px、sm 8px、md 10px、lg 14px、xl 16px。首页 `--home-radius` 为 12px；HeroBanner 为 8px。不存在全站唯一卡片圆角。

全局阴影原值：

```css
--shadow-soft: 0 3px 14px rgba(42, 61, 89, 0.04);
--shadow-card: 0 7px 22px rgba(42, 61, 89, 0.055);
--shadow-hover: 0 12px 28px rgba(42, 61, 89, 0.09);
--shadow-float: 0 16px 38px rgba(65, 78, 148, 0.14);
```

| 组件／样式 | 可直接引用的现有规则 |
| --- | --- |
| 门户导航 `AppHeader` | 当前项字重 600 + 黄色 2px 下划线；隐藏伪元素预留加粗宽度；hover 下划线 opacity .45；焦点为石墨色 2px outline |
| 后台导航 `AdminLayout` | 42px 最小高、8px 圆角，蓝紫浅底选中 |
| 栏目头 `SectionMasthead` | 链接整块可点；128px 高、32px 水平内边距、24px gap；背景图 cover；支持 dark/light 与图片失败回退；preview 模式用 div |
| HeroBanner / BannerSlide | 容器比例 3.8、最小高 220px；标准文字叠图与 image_only；圆形箭头、底部圆点；具体 CTA 使用黄色深字。不能把所有 Banner 都假定有文字 |
| 新闻卡 `NewsView` | 10px 圆角、16:9 封面、body padding 22px；标题两行、摘要三行；无图时按类型生成浅色渐变封面 |
| 工具卡 `ToolGrid` | 复用组件时必须选择 home / detailed 模式；首页正方形封面区域渐隐、底部文字和荧光入口；独立工具中心保留图标、状态标签及渐变操作按钮 |
| 工作区 `WorkCalendar` | 日历七列；Todo 完成图标 16px 圆形勾选；本地标记色与任务拖动反馈；首页局部变量覆盖，不推广到全局 |
| 四象限 `PriorityMatrix` | 默认 2×2，≤420px 单列；颜色与符号共同区分类别；接收任务拖放，弹出分类任务详情 |
| 公共后台按钮 | `.content-primary-action` padding 11px 20px、8px 圆角、紫底白字；表单提交按钮高 44px、min-width 120px；表格操作是文字按钮，不是全部实心按钮 |
| 公共后台输入 | `.content-form-field` label 14px、gap 9px；border strong、radius 8px；textarea min-height 110px、line-height 1.7、可纵向调整；focus 改主色边框 |
| 后台表格 | `.content-table` 表头 12px、正文 14px；单元格 padding 17px 18px；行 hover 柔和底色；无统一第三方 DataTable |
| 登录表单 | 表单最大 380px、gap 20px，输入／主按钮 min-height 48px、8px 圆角；错误以文本 role=alert 显示 |
| Exchange 控件 | 分享按钮荧光绿、高 44px、8px 圆角；普通 `.control` 为白底细边框、高度至少 44px、6px 圆角；primary 是石墨底白字 |
| 图片编辑 | `SectionImageCropper` + `ImageCropFrame` 提供取景和预览；栏目图片尺寸来自 `config/sectionVisuals.js`，新闻栏目输出 1646×256、工具栏目 2400×256；不是页面固定宽度 |

后台 Banner / 公告 / 工具采用 `.content-*` 公共样式；新闻增改页仍有自己的 `.form-*` 样式。现有组件库是源码组件和 CSS 约定，尚无统一 Button / Input / Modal 基础组件。

## 7. 交互与反馈

### 7.1 悬停、选中、加载与过渡

- 全局 `--transition-fast:180ms ease`、`--transition-normal:220ms ease`；首页 `--home-motion-fast:140ms`、`--home-motion:220ms`，ease 为 `cubic-bezier(.2,.8,.2,1)`。
- 新闻与工具可点卡片 hover `translateY(-2px)`、增强边框和阴影；首页入口箭头 hover / focus 向右 3px，active 卡片回到原位；未接入工具保持不可操作状态。
- `HomeView` planner 展开用 max-height / margin / opacity / transform 过渡；`PlannerExpandPanel` 在拖动任务或四象限弹层打开时对时间线加弱化和禁止指针交互。
- `HeroBanner` 多张时每 5000ms 轮播，手动切换重启计时；淡入淡出 250ms。CSS 减少动态效果仅取消过渡，当前 JS 计时器不据此停止。
- `NewsView` / `NewsDetailView` 有 loading、错误、空／404 文本状态；`ToolGrid` 有静态骨架块、空与错误状态；不把骨架误写成全站 shimmer 动画。
- 表单提交时按钮禁用并更新文案，禁用透明度与 cursor 按模块不同：公共提交 .58 / not-allowed；登录 .6 / wait。成功／失败多以页内提示体现，没有全站 Toast 系统。

### 7.2 弹层与确认

- 分享表单：`exchange/ExchangeSubmitForm` 原生 dialog，宽 `min(620px,calc(100% - 24px))`、max-height `calc(100dvh - 32px)`、内部滚动；含焦点转移／恢复、提交禁用、成功反馈与图片取景流程。
- 四象限：`PriorityMatrix` 使用 Teleport 到 body 的自定义弹层，role=dialog、aria-modal、Esc 和遮罩关闭；不能据此宣称已实现与原生 dialog 相同的焦点约束和背景锁。
- `DeleteConfirm` 是就地确认块，role=alertdialog、Esc 取消、28px 高操作按钮；多数后台删除用 `window.confirm`，并非统一使用此组件。

### 7.3 焦点与减少动态效果

全局焦点为 `3px solid rgba(91,91,214,.24)`、offset 3px。Header、首页栏目、登录和 Exchange 存在局部覆盖。保留实际可见焦点，不移除后仅依赖 hover。

Header、HeroBanner、SectionMasthead、首页 NewsList、首页 ToolGrid、WorkCalendar、Exchange 有 `prefers-reduced-motion` 规则，但覆盖面不等于全站：`HomeView` planner 与若干旧组件仍有独立过渡。键盘、触屏和 reduced-motion 的端到端效果待实测。

## 8. 适用范围外的独立工具

`frontend/public/tools/qstart/index.html` 是独立 HTML 工具，不经 Vue Router 的页面布局。其 `:root` 采用背景 `#eef2f7`、半透明表面 `rgba(255,255,255,.84)`、深蓝 `#081739` / `#06112c`、蓝 `#3a63ba`、绿 `#00a665`、橙 `#ff9700`、红 `#d92d20`，圆角 14/10px，容器 max 1480px。使用系统字体、深蓝渐变头部与 backdrop-filter。保留其工具边界，不自动套门户首页 Token。实际入口可用性受工具配置和认证影响，本轮未运行验证。

## 9. 维护约定与未来建议

1. 新 UI 任务先查路由归属、现有组件与样式作用域，只读取相关章节；纯后端任务无须读取全文。
2. 延续已有界面时优先复用同模块组件和 Token；新增跨模块组件前说明默认主题、覆盖入口和受影响页面。
3. 对颜色、字体、布局、交互语义等实质变更，先说明当前值与拟议值、涉及路由及理由；用户未授权时不自行改变方向。
4. 实现发生变化后同步更新本文件和相关审计项，保留证据来源；静态规则与浏览器验收分别记录。
5. **未来建议，尚未实施**：建立语义状态色、排版和间距 Token；减少重复表单／表头 CSS；统一弹层可访问性；讨论是否迁移旧模块。候选方案只记录到 [STYLE_EXPLORATIONS.md](STYLE_EXPLORATIONS.md)，不会自动覆盖本文基线。
