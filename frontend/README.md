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
- `src/data/`：Banner、新闻、公告和工具数据
- `src/utils/`：Todo 与四象限本地存储辅助逻辑
- `public/tools/qstart/`：QsTArT 静态工具

门户 V1 主体目前使用前端 JSON 与浏览器 localStorage，不依赖后端 API。FastAPI 后端保留在项目根目录的 `backend/`。
