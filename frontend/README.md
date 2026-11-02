# 信息运维部智能助手平台

基于 Vue 3、Vite 和 Vue Router 的内部 AI 门户前端。

## 本地开发

```sh
npm install
npm run dev
```

## 质量检查

```sh
npm run lint
npm test
npm run build
```

## 目录说明

- `src/components/`：公共与首页功能组件
- `src/views/`：路由页面
- `src/data/`：资源交流展示数据
- `src/utils/`：Todo 与四象限本地存储辅助逻辑
- `public/tools/qstart/`：QsTArT 静态工具

新闻、Banner、公告、工具及资源交流通过 FastAPI API 使用 SQLite 数据。Calendar、Todo、四象限和首页个人时间线（`PersonalTimeline.vue`）使用按员工隔离的浏览器存储。服务端项目看板已经移除。完整版本记录见项目根目录 `README.md`。
