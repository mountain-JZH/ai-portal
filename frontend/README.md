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
npm run build
```

## 目录说明

- `src/components/`：公共与首页功能组件
- `src/views/`：路由页面
- `src/data/`：Banner、公告和工具配置数据
- `src/utils/`：Todo 与四象限本地存储辅助逻辑
- `public/tools/qstart/`：QsTArT 静态工具

门户的 Banner、公告和工具使用前端 JSON，Calendar、Todo、四象限及项目数据使用浏览器 localStorage；新闻模块通过 FastAPI API 读取和管理 SQLite 数据。完整版本记录与下一阶段计划见项目根目录 `README.md`。
