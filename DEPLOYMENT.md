# AI Portal 单机部署指南

本文面向普通 Linux ECS，使用 Nginx 托管 Vue 静态文件，并将 `/api` 反向代理到仅监听 `127.0.0.1:8000` 的 FastAPI。数据库继续使用 SQLite。本指南不依赖特定云厂商，也不使用 Docker。

## 1. 推荐目录

```text
/opt/ai-portal/
├─ backend/
│  ├─ .venv/
│  └─ .env
├─ frontend/
│  └─ dist/
├─ data/
│  └─ ai_portal.db
├─ uploads/
│  ├─ banners/
│  └─ news/
├─ backups/
└─ deploy/
```

数据库和 `uploads` 都属于生产持久化数据，不要放入 `frontend/dist`，不要通过 Git 管理，也不要在代码发布时覆盖。

## 2. 准备服务器

以下命令以 Debian/Ubuntu 系发行版为例，其他发行版请替换包管理命令：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx nodejs npm git
```

确认版本满足项目要求：

```bash
python3 --version
node --version
npm --version
nginx -v
```

创建非 root 服务账号和目录。账号名称可以调整，但需同步修改 systemd 模板：

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin aiportal
sudo mkdir -p /opt/ai-portal
sudo chown -R aiportal:aiportal /opt/ai-portal
```

## 3. 上传项目

可通过 Git 拉取或将项目文件上传到 `/opt/ai-portal`。不要上传本机 `.env`、`.venv`、数据库或 `node_modules`。

```bash
cd /opt/ai-portal
sudo -u aiportal git clone <repository-url> .
sudo -u aiportal mkdir -p data backups uploads/banners uploads/news
```

如果采用文件上传，请保持同样的目录结构和属主权限。

## 4. 创建后端虚拟环境

```bash
cd /opt/ai-portal/backend
sudo -u aiportal python3 -m venv .venv
sudo -u aiportal .venv/bin/python -m pip install --upgrade pip
sudo -u aiportal .venv/bin/python -m pip install -r requirements.txt
```

## 5. 配置后端环境变量

```bash
cd /opt/ai-portal/backend
sudo -u aiportal cp .env.example .env
sudo chmod 600 .env
sudo chown aiportal:aiportal .env
```

编辑 `.env`，至少设置：

```dotenv
ADMIN_USERNAME=<initial-admin-name>
ADMIN_PASSWORD=<strong-initial-password>
SESSION_SECRET=<long-random-secret>
SESSION_COOKIE_SECURE=true
DATABASE_PATH=/opt/ai-portal/data/ai_portal.db
BACKUP_DIR=/opt/ai-portal/backups
```

如继续使用现有 Dify 后端能力，再按实际环境填写 `DIFY_API_URL` 和 `DIFY_API_KEY`。不要把 `.env` 提交到 Git。

可使用系统工具生成 Session Secret，例如：

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 6. 初始化数据库和初始管理员

从 backend 目录执行：

```bash
cd /opt/ai-portal/backend
sudo -u aiportal .venv/bin/python database.py
```

`database.py` 会读取 backend `.env`，创建 `news`、`banners`、`announcements`、`tools` 和 `admins` 表。仅当 `admins` 为空且管理员环境变量完整时才创建初始管理员；重复执行不会重复创建。

确认数据库权限：

```bash
sudo chown aiportal:aiportal /opt/ai-portal/data/ai_portal.db
sudo chmod 600 /opt/ai-portal/data/ai_portal.db
```

## 7. 构建前端生产文件

生产环境使用同源相对 API `/api`：

```bash
cd /opt/ai-portal/frontend
sudo -u aiportal cp .env.production.example .env.production
sudo -u aiportal npm install
sudo -u aiportal npm run build
```

确认以下文件存在：

```bash
test -f dist/index.html
test -f dist/tools/qstart/index.html
```

`.env.production` 只包含公开构建配置，不应包含密码或后端 Secret。

## 8. 配置 Nginx

复制模板并检查静态目录：

```bash
sudo cp /opt/ai-portal/deploy/nginx/ai-portal.conf.example /etc/nginx/sites-available/ai-portal
sudo ln -s /etc/nginx/sites-available/ai-portal /etc/nginx/sites-enabled/ai-portal
sudo nginx -t
sudo systemctl reload nginx
```

模板使用 `server_name _;`。正式使用域名时可替换为实际域名；HTTPS 证书配置不在本阶段范围内。SPA 路由由 `try_files` 回退到 `index.html`，QsTArT 继续作为 `/tools/qstart/index.html` 静态文件提供。

`/uploads/` 通过 Nginx `alias` 映射到 `/opt/ai-portal/uploads/`，其中 Banner 和新闻图片分别保存在 `uploads/banners` 与 `uploads/news`。该目录必须作为持久化数据单独保留，更新代码或重新构建前端时不得覆盖。

## 9. 配置 systemd

```bash
sudo cp /opt/ai-portal/deploy/systemd/ai-portal.service.example /etc/systemd/system/ai-portal.service
sudo systemctl daemon-reload
sudo systemctl enable ai-portal
sudo systemctl start ai-portal
```

生产 Uvicorn 不使用 `--reload`，只监听服务器本机：

```text
127.0.0.1:8000
```

## 10. 验证服务

在服务器本机验证 FastAPI：

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/news
```

健康接口应返回：

```json
{"status":"ok"}
```

再通过 Nginx 地址验证门户、登录、新闻、工具及 QsTArT。生产浏览器只访问 Nginx，不直接访问端口 8000。

## 11. 查看日志

FastAPI/Uvicorn 日志进入 systemd journal：

```bash
sudo systemctl status ai-portal
sudo journalctl -u ai-portal
sudo journalctl -u ai-portal -f
```

Nginx 使用系统默认 `access.log` 和 `error.log`，常见位置为 `/var/log/nginx/`。

## 12. 手动备份 SQLite

备份脚本使用 Python `sqlite3.Connection.backup()`，可以在服务运行时获得一致备份，不要把直接复制正在写入的数据库作为唯一备份方案。

```bash
cd /opt/ai-portal
sudo -u aiportal backend/.venv/bin/python deploy/scripts/backup_db.py \
  --backup-dir /opt/ai-portal/backups
```

输出文件类似：

```text
/opt/ai-portal/backups/ai_portal_20260923_220000.db
```

未来如需定时备份，可由系统管理员在确认保留周期后配置 cron 或 systemd timer；本项目当前不自动创建定时任务。

## 13. 更新版本

更新前先备份数据库：

```bash
cd /opt/ai-portal
sudo -u aiportal backend/.venv/bin/python deploy/scripts/backup_db.py \
  --backup-dir /opt/ai-portal/backups
```

然后更新代码和依赖：

```bash
sudo systemctl stop ai-portal
cd /opt/ai-portal
sudo -u aiportal git pull --ff-only
sudo -u aiportal backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
sudo -u aiportal npm install
sudo -u aiportal npm run build
sudo systemctl start ai-portal
sudo nginx -t && sudo systemctl reload nginx
```

最后重新执行健康检查和主要页面回归。

## 14. 回滚

1. 停止 FastAPI：`sudo systemctl stop ai-portal`。
2. 将代码切回已确认可用的发布版本。
3. 仅在确认数据库变更不兼容且确实需要时，保留当前数据库副本后再从备份恢复。
4. 检查 `/opt/ai-portal/data/ai_portal.db` 的所有者和权限。
5. 重新安装对应版本依赖、构建前端并启动服务。
6. 检查 `/api/health`、日志和门户主要路径。

恢复数据库前必须确认备份时间和业务影响，避免覆盖仍需保留的新数据。
