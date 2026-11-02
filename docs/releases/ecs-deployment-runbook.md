# AI Portal V1.8 — ECS 分阶段发布与回滚手册

> 2026-10-19 现场快照：以下信息来自用户提供的实际 SSH 检查结果，并非 Codex 自行连接 ECS 核验。ECS 源码版本为 `f2e9abe`，Python 为 `3.12.3`，数据库为 `/opt/ai-portal/data/ai_portal.db`，持久化 uploads 为 `/opt/ai-portal/uploads/`，当前入口使用 Nginx，服务器存在 `/opt/ai-portal/update.sh`。生产数据库备份继续使用 `deploy/scripts/backup_db.py` 的 SQLite Backup API。本轮没有执行部署脚本、更新 ECS 或部署；现场值在真正发布窗口仍须由执行人复核。

日期：2026-10-19。**本轮仅编写，没有执行本文生产命令。当前 NO-GO，先解除审查报告的阻塞项。**

本文分“只读取证”与“需要单独授权的变更操作”。所有安装、创建备份、复制、迁移、配置写入、启停、覆盖和恢复都属于后者；不能整篇复制执行。每阶段由负责人核对输出并签字，不使用自动一路到底的脚本。任何输出与预期不符，停止下一步，保留现场。

## Phase 0 — 目标、版本与授权

### 0.1 必须先取得的信息

| 信息 | 当前状态 | 取得方式 |
| --- | --- | --- |
| ECS 主机/账号、批准窗口、执行人与回滚负责人 | 待确认 | 运维确认，不根据项目路径推断主机 |
| 实际生产 SHA/tag/文件指纹、工作区改动 | 待确认 | 运行目录 git 信息及构建文件指纹；无 Git 则保护源快照 |
| 应用根、DB 绝对路径、上传根、Nginx dist root | 待确认 | 实际进程、服务环境、Nginx 配置联合核对 |
| 服务名、服务用户、旧 Python/venv、EnvironmentFile | 待确认 | 实际服务管理配置，不假定模板已安装 |
| Nginx 配置文件、外部 URL/TLS、网关/内网边界 | 待确认 | 生效配置和内外网访问验证 |
| 候选完整 SHA、模块清单、批准的公开 Dify Embed 地址 | 待确认 | 人工验收并选择性提交后固定版本 |

仓库模板写的是 `/opt/ai-portal` 和 systemd `aiportal`；用户提供的 SSH 检查结果确认了上述数据库、uploads、Nginx、Python、源码版本和服务器部署脚本信息，但其余服务管理细节仍不得从模板推断。仓库没有 `update.sh`，服务器 `/opt/ai-portal/update.sh` 本轮未执行、未修改，正式部署前必须单独读审。

先批准：发布首页/Header/工具/栏目背景及必要后端，还是另有缩减范围。不要任意只拿一个 HomeView 文件：新增共享组件、API、依赖与迁移是一个兼容集合。原型、截图和测试不放入 Nginx webroot；测试可保留在代码档案。

一期：`EXCHANGE_ENABLED=false`，会同时关闭公共读写；后台鉴权仍在。二期：内部边界通过后另行批准开放。关闭开关不能屏蔽已经存在的静态图片。

### 0.2 只读取证命令

以下 Bash 变量**必须用已确认值替换**。不要 source 未审查脚本，也不要把整份 `.env` 或 `/proc/.../environ` 输出到终端/工单。

```bash
APP_ROOT='__CONFIRM_ABSOLUTE_APP_ROOT__'
SERVICE='__CONFIRM_SYSTEMD_SERVICE_NAME__'
SERVICE_USER='__CONFIRM_SERVICE_USER__'
OLD_PYTHON='__CONFIRM_RUNNING_VENV_PYTHON_ABSOLUTE_PATH__'
DB_PATH='__CONFIRM_EFFECTIVE_DATABASE_ABSOLUTE_PATH__'
UPLOADS='__CONFIRM_PERSISTENT_UPLOADS_ABSOLUTE_PATH__'
DIST='__CONFIRM_NGINX_DIST_ABSOLUTE_PATH__'
NGINX_CONF='__CONFIRM_ACTIVE_SERVER_CONFIG_ABSOLUTE_PATH__'
PUBLIC_ORIGIN='__CONFIRM_HTTPS_ORIGIN__'

for value in "$APP_ROOT" "$SERVICE" "$SERVICE_USER" "$OLD_PYTHON" "$DB_PATH" "$UPLOADS" "$DIST" "$NGINX_CONF" "$PUBLIC_ORIGIN"; do
  case "$value" in *__CONFIRM*|'') printf 'STOP: unresolved value\n' >&2; exit 1;; esac
done

systemctl show "$SERVICE" -p FragmentPath -p DropInPaths -p MainPID -p User -p Group -p WorkingDirectory -p ExecStart -p EnvironmentFiles
systemctl is-active "$SERVICE"
git -C "$APP_ROOT" status --short
git -C "$APP_ROOT" rev-parse HEAD
git -C "$APP_ROOT" log -5 --oneline
"$OLD_PYTHON" --version
"$OLD_PYTHON" -m pip show Pillow fastapi uvicorn python-multipart
node --version
npm --version
readlink -f "$APP_ROOT" "$DB_PATH" "$UPLOADS" "$DIST"
df -h "$APP_ROOT" "$DB_PATH" "$UPLOADS"
du -sh "$DB_PATH" "$UPLOADS" "$DIST"
namei -l "$DB_PATH" "$UPLOADS" "$DIST"
sudo -u "$SERVICE_USER" test -r "$DB_PATH"
sudo -u "$SERVICE_USER" test -w "$DB_PATH"
sudo -u "$SERVICE_USER" test -w "$(dirname "$DB_PATH")"
```

如不是 systemd/Git checkout，记录真实进程管理方式/文件快照，先重新制定对应切换步骤，不继续套用本文 systemd 命令。确认 Nginx worker 身份和上传目录遍历/读权限，以及后端用户对 uploads 的创建权限。`test -w` 只作权限预检，不能证明磁盘、ACL、实际写入一定成功。

由有权限的运维在服务器本地阅读 `sudo nginx -T`、实际 unit/drop-ins 和 EnvironmentFile。输出可能含内部地址/敏感配置，禁止原样粘贴到公开文档。核对：dist root、SPA fallback、API loopback 代理、uploads alias、TLS、上传大小、缓存、内网保护及后端端口是否能被外部绕过。

如需核对正在运行的进程环境，只输出白名单字段：

```bash
PID="$(systemctl show "$SERVICE" -p MainPID --value)"
sudo env REVIEW_PID="$PID" "$OLD_PYTHON" - <<'PY'
import os
from pathlib import Path
pid = int(os.environ['REVIEW_PID'])
assert pid > 1
raw = Path(f'/proc/{pid}/environ').read_bytes().split(b'\0')
values = dict(item.split(b'=', 1) for item in raw if b'=' in item)
for key in (b'DATABASE_PATH', b'EXCHANGE_ENABLED', b'SESSION_COOKIE_SECURE'):
    print(key.decode(), '=', values.get(key, b'<unset>').decode(errors='replace'))
print('cwd =', Path(f'/proc/{pid}/cwd').resolve())
print('exe =', Path(f'/proc/{pid}/exe').resolve())
PY
```

`DATABASE_PATH` 未设置时默认值基于该运行代码的 backend 路径；相对值也基于 backend。多 worker 时确认实际 worker PID/配置一致；主进程环境不是所有 worker 的绝对证明。用只读连接检查选定 DB 的 schema、integrity_check、journal_mode 及旧表数量，不打印管理员数据。若实际进程打开的 SQLite 文件与解析结果不一致，停止。

### 0.3 放行门槛

- Python ≥3.11 且候选依赖实装通过；Node 满足 package.json engines。
- 候选 SHA 包含审查清单中的所有必要新文件；当前本地 HEAD 不包含未跟踪新功能，不可直接作为候选。
- 本地/预发布浏览器验收通过；新闻中心旧视觉作为已知范围接受。
- 备份空间至少覆盖 DB、uploads、旧源码/配置、旧 venv、旧 dist、新 venv、新构建与临时文件并留充足余量；不使用本地上传大小估算 ECS。
- 已核准维护窗口及“后端先、前端后”的短暂不可用影响；Exchange 一期开关明确为 false。

## Phase 1 — 发布前一致性备份（写入备份；停服需另行批准）

前置：Phase 0 通过，备份根为 webroot 之外的受限目录，容量足够。环境/服务配置备份可能包含秘密，采用限制权限及批准的加密/异地机制，不提交 Git。

确认并填写：`BACKUP_PARENT`、`RELEASE_ID`、实际 EnvironmentFile、实际 systemd 主配置及 drop-in 路径。本文不虚构它们。

```bash
# [写入] 仅新建本次唯一备份目录；既有同名目录必须停止，不能覆盖。
BACKUP_PARENT='__CONFIRM_ABSOLUTE_PRIVATE_BACKUP_PARENT__'
RELEASE_ID='__CONFIRM_UNIQUE_RELEASE_ID__'
case "$BACKUP_PARENT/$RELEASE_ID" in *__CONFIRM*) exit 1;; esac
test "${BACKUP_PARENT#/}" != "$BACKUP_PARENT" && test "$BACKUP_PARENT" != /
case "$RELEASE_ID" in ''|*/*|*..*) exit 1;; esac
umask 077
BACKUP="$BACKUP_PARENT/$RELEASE_ID"
mkdir -- "$BACKUP" || exit 1
mkdir -- "$BACKUP/db" "$BACKUP/config"

# [停服] 暂停所有数据库和上传写入方，不仅此 unit；确认维护窗口已批准。
sudo systemctl stop "$SERVICE"
systemctl is-active "$SERVICE"   # 应为 inactive，非零退出是预期；不要盲用 set -e 吞掉后续判断
```

检查 cron/其他 worker/运维脚本都不再写 DB/uploads。若不能停写，需要另行设计数据库与图片的一致快照，不要继续将两个不同时点的备份称为一致。停服失败即停止备份后的切换流程。

```bash
# [写入备份] 现有脚本用 SQLite backup API，WAL 情况不能只 cp 活跃 .db。
# 若旧生产源码无此脚本，使用已审阅候选包中相同脚本的绝对路径替换。
DATABASE_PATH="$DB_PATH" "$OLD_PYTHON" "$APP_ROOT/deploy/scripts/backup_db.py" --backup-dir "$BACKUP/db"
find "$BACKUP/db" -maxdepth 1 -type f -name '*.db' -print
```

保存并核对唯一实际输出为 `DB_BACKUP`。不要用宽泛通配符恢复。只读验证：

```bash
DB_BACKUP='__CONFIRM_EXACT_CREATED_BACKUP_DB__'
case "$DB_BACKUP" in *__CONFIRM*) exit 1;; esac
env REVIEW_DB="$DB_BACKUP" "$OLD_PYTHON" - <<'PY'
import os, sqlite3
from pathlib import Path
p = Path(os.environ['REVIEW_DB']).resolve(strict=True)
c = sqlite3.connect(p.as_uri() + '?mode=ro', uri=True)
try:
    result = c.execute('PRAGMA integrity_check').fetchall()
    assert result == [('ok',)], result
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for name in ('news', 'banners', 'announcements', 'tools', 'admins', 'section_visuals', 'exchange_resources'):
        if name in tables:
            print(name, c.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
    print('backup integrity OK')
finally:
    c.close()
PY

# [写入备份] 不修改源文件，保留上传与当前前端；目标目录必须首次创建。
tar -C "$UPLOADS" -cpf "$BACKUP/uploads.tar" .
tar -C "$DIST" -cpf "$BACKUP/frontend-dist.tar" .
tar -C "$APP_ROOT" --exclude=backend/.venv --exclude='backend/__pycache__' -cpf "$BACKUP/backend-source-and-config.tar" backend
tar -tf "$BACKUP/uploads.tar" > "$BACKUP/uploads.manifest"
tar -tf "$BACKUP/frontend-dist.tar" > "$BACKUP/dist.manifest"
sha256sum "$DB_BACKUP" "$BACKUP/uploads.tar" "$BACKUP/frontend-dist.tar" "$BACKUP/backend-source-and-config.tar" > "$BACKUP/SHA256SUMS"
```

上面的 backend 备份可能含 `.env`，所以 BACKUP 必须私有；源目录若还有自定义 DB 应已记录，不把这个 tar 当作 DB 一致性备份。人工按已确认清单另外复制 EnvironmentFile、unit/drop-ins、Nginx 配置（逐个精确文件）至 `$BACKUP/config`，记录旧 Python/venv 路径及 pip freeze。不得把密钥写进公开 release manifest。

保留旧 venv **原路径不变**；若必须原地升级，先完整快照旧 venv 并验证可回到原路径，禁止用原地 pip upgrade 后假称可回滚。新 venv 使用独立稳定路径，见 Phase 3。

把压缩包恢复到隔离目录，校验解包文件数量/大小/校验和、DB 可打开及若干引用图片存在。备份可用性和备份路径须记录后才允许迁移。单有 tar 文件或 sha256sum 不代表完成恢复演练。

## Phase 2 — 运行环境与持久目录（先检查，创建属于写操作）

实际有效目录至少涵盖 `banners`、`news`、`tools`、`sections`、`exchange`。如缺失，**经授权后**只在已确认的持久化 UPLOADS 下 `mkdir -p`；核对后端用户可写，Nginx 可读。不执行宽泛 chown/chmod，不 chmod 777，不递归更改未核实目标。

关键不变量：`backend/upload_api.py` 根据源码父目录确定上传根。本文后续保持 APP_ROOT/backend 不变。若采用 versioned release/symlink，必须先证明每个版本看到同一 uploads，且与 Nginx alias 相同；否则停止该切换方案。DB 使用已确认绝对 DATABASE_PATH，不跟着版本根迁移。

检查磁盘/依赖安装能力后再准备新环境；Pillow 13.0.0 不支持 Python 3.10。不能在生产现场擅改 requirements 来“装得上”。

## Phase 3 — 不可变候选与构建（只写独立候选，不碰运行数据）

前置：用户人工批准并形成包含所有必要新文件的完整候选 SHA。本轮不替用户 commit/push。候选源来自可信仓库/制品传输；不打包整个脏工作区，更不能用 git add . 收集私有配置。

```bash
CANDIDATE_SHA='__CONFIRM_FULL_APPROVED_SHA__'
STAGING_PARENT='__CONFIRM_PRIVATE_STAGING_PARENT__'
VENV_PARENT='__CONFIRM_STABLE_VENV_PARENT_OUTSIDE_REPLACED_SOURCE__'
PYTHON_BIN='__CONFIRM_PYTHON_3_11_OR_LATER__'
case "$CANDIDATE_SHA/$STAGING_PARENT/$VENV_PARENT/$PYTHON_BIN" in *__CONFIRM*) exit 1;; esac
test "${STAGING_PARENT#/}" != "$STAGING_PARENT" && test "$STAGING_PARENT" != /
test "${VENV_PARENT#/}" != "$VENV_PARENT" && test "$VENV_PARENT" != /
CANDIDATE="$STAGING_PARENT/$RELEASE_ID"
NEW_VENV="$VENV_PARENT/$RELEASE_ID"
test ! -e "$CANDIDATE" && test ! -e "$NEW_VENV" || exit 1

# [写入候选] 只创建本次目录；源仓库和 SHA 必须先验证。
mkdir -- "$CANDIDATE"
( set -o pipefail; git -C "$APP_ROOT" archive "$CANDIDATE_SHA" | tar -xf - -C "$CANDIDATE" ) || exit 1
"$PYTHON_BIN" -m venv "$NEW_VENV"
"$NEW_VENV/bin/python" -m pip install -r "$CANDIDATE/backend/requirements.txt"
"$NEW_VENV/bin/python" -m pip check
```

新 venv 留在最终稳定路径，**不要创建后再重命名 venv**（脚本 shebang 含绝对路径）。服务用户需可遍历和执行新 venv。安装失败不影响旧 venv，但仍应退出候选准备并恢复已停止的旧服务。

前端在无本地开发 `.env` 的候选副本构建：

```bash
cd "$CANDIDATE/frontend" || exit 1
# [写入候选 node_modules/dist] npm ci 按 lockfile；不在运行 dist 原地构建。
npm ci
# VITE_ 是浏览器公开内容；这里填经批准的 Embed 地址或空，不放任何 Key/Token。
DIFY_EMBED_PUBLIC_URL='__CONFIRM_APPROVED_PUBLIC_EMBED_URL_OR_EMPTY__'
case "$DIFY_EMBED_PUBLIC_URL" in *__CONFIRM*) exit 1;; esac
VITE_API_BASE_URL=/api VITE_DIFY_EMBED_URL="$DIFY_EMBED_PUBLIC_URL" npm run build
test -f dist/index.html && test -f dist/tools/qstart/index.html || exit 1
if grep -R -nE 'https?://(localhost|127\.0\.0\.1):8000' dist/assets --include='*.js'; then
  printf 'STOP: development API in artifact\n' >&2
  exit 1
fi
find dist -type f \( -iname '*studio*' -o -iname '*discovery-lab*' -o -iname '*design-system*' \) -print
```

最后 find 预期无实验入口；同时核对打包文件清单、无 exchangeDemo 样例内容、无私密配置/凭据。只把 `frontend/dist` 内容作为 webroot，不发布 artifacts/src/tests/.env。检查 grep 命令确实正常运行，不能把工具失败当作无匹配。

记录候选 SHA、requirements/package-lock 校验和、构建环境、产物 sha256 manifest、资源清单。构建变量公开但实际公司地址不要写入公开文档。当前本地默认 dist 已确认不合格，不能替代此步骤。

## Phase 4 — 备份后幂等迁移（写入生产 DB，须明确批准）

前置：所有写入方已停；备份与恢复演练完成；新解释器及依赖准备成功；真实 DB_PATH 再次确认；不复制本地 DB。

先在“备份副本”运行候选 `database.py` 两次，比较旧表/旧列哈希并检查新 schema，证明对该生产快照兼容。这是写入测试副本，不是生产迁移；避免测试副本初始化默认管理员，保留真实既有 admins。

下面指纹检查可比较迁移后旧数据与备份，不输出内容或口令散列本身，只输出是否相等。迁移前应先对备份与实际 DB 执行一次比较，证明备份时点一致；迁移后再次执行。若期间允许写入，比较失效，需重新建立一致窗口。

```bash
env REVIEW_BEFORE="$DB_BACKUP" REVIEW_AFTER="$DB_PATH" "$NEW_VENV/bin/python" - <<'PY'
import hashlib, json, os, sqlite3
from pathlib import Path
def connect(key):
    p = Path(os.environ[key]).resolve(strict=True)
    return sqlite3.connect(p.as_uri() + '?mode=ro', uri=True)
def quote(s):
    return '"' + s.replace('"', '""') + '"'
def fingerprint(c, table, columns):
    rows = c.execute('SELECT ' + ','.join(map(quote, columns)) + ' FROM ' + quote(table)).fetchall()
    # 次序无关、保留重复行；只比较旧列，不因新增列误报。
    encoded = sorted(json.dumps(row, ensure_ascii=True, default=lambda v: v.hex()) for row in rows)
    return len(rows), hashlib.sha256('\n'.join(encoded).encode()).hexdigest()
a, b = connect('REVIEW_BEFORE'), connect('REVIEW_AFTER')
try:
    assert a.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    assert b.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    tables = [r[0] for r in a.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    for table in tables:
        columns = [r[1] for r in a.execute('PRAGMA table_info(' + quote(table) + ')')]
        before, after = fingerprint(a, table, columns), fingerprint(b, table, columns)
        assert before == after, 'old data changed: ' + table
        print(table, 'old-column data unchanged, rows=', before[0])
    # AUTOINCREMENT 序列不得倒退；未写入时保留已有编号序列。
    if a.execute("SELECT 1 FROM sqlite_master WHERE name='sqlite_sequence'").fetchone():
        for name, seq in a.execute('SELECT name,seq FROM sqlite_sequence'):
            row = b.execute('SELECT seq FROM sqlite_sequence WHERE name=?', (name,)).fetchone()
            assert row and row[0] >= seq, 'sequence regressed: ' + name
finally:
    a.close(); b.close()
PY
```

大数据库应分块计算指纹而非一次装入内存；本代码面向当前小型门户，先确认生产体积。输出/失败即停止，不忽略差异。

```bash
# [迁移写入] 主机 EnvironmentFile 已按审批保留原值；不要注入测试账号或新的 SESSION_SECRET。
# 脚本 load_dotenv 读取候选目录配置；此处显式传入有效 DB，且不开 Exchange。
DATABASE_PATH="$DB_PATH" EXCHANGE_ENABLED=false "$NEW_VENV/bin/python" "$CANDIDATE/backend/database.py"
DATABASE_PATH="$DB_PATH" EXCHANGE_ENABLED=false "$NEW_VENV/bin/python" "$CANDIDATE/backend/database.py"
```

核对实际 schema：`banners.banner_type` 默认 standard、`tools.cover_image_url` 默认空、section_visuals 和 text_mode、exchange_resources AUTOINCREMENT；旧列/旧数据指纹完全不变。重跑不是错误恢复的替代品：若首次失败，先检查实际 DDL 状态和原因。无凭据初始化条件下如果原生产 admins 为空，不能让新服务以无管理员状态上线，需另行审批账号初始化。

若候选副本中存在不应有的 `.env` 或继承了测试管理员环境，应先停止。显式 `database.py` 不要求 SESSION_SECRET；服务启动要求它，由生产原配置提供，不在命令中打印。

## Phase 5 — 后端先、前端后（覆盖源码/配置/重启均需批准）

### 5.1 后端切换

1. 保持 `$APP_ROOT/backend` 路径不变、DB/uploads/原 `.env` 不动。按已批准 manifest 把候选 `backend/*.py` 和 `requirements.txt` 复制到该目录；不要覆盖 `.env`、`.venv`、数据库、uploads 或用户自定义脚本。**这是覆盖源码操作，只有备份通过并有审批才执行。**
2. 若旧源码有本地 patch，先合并决策，不能用整树同步抹掉。保留旧源码归档及旧 venv 原路径。
3. 核对原 unit 的 WorkingDirectory/EnvironmentFile；一期在实际有效配置中明确 `EXCHANGE_ENABLED=false`，保留 DATABASE_PATH、SESSION_SECRET、管理员和其他原值。不要拷贝本地 env。
4. 如确认为 systemd：经审批对实际服务创建本次 drop-in，清空旧 ExecStart 并指定 `$NEW_VENV/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000`；**端口、参数、worker 数量及其他必要旧参数以实际服务为准，不因模板随意丢弃**。WorkingDirectory 不变，环境文件沿用。drop-in 可能影响代理信任行为，需保留实际限制，不使用 `forwarded-allow-ips=*`。
5. 精确记录 drop-in 文件路径和原内容。写入 unit/drop-in 属生产配置变更；未批准则不能自动切换新 venv，停止该部分。

```bash
# [配置生效/启动] 仅 unit/drop-in 发生经批准修改时 daemon-reload。
sudo systemctl daemon-reload
sudo systemctl start "$SERVICE"
systemctl is-active "$SERVICE"
sudo journalctl -u "$SERVICE" --since '-5 minutes' --no-pager
```

日志只在受控终端检查，不向公开工单复制凭据/内部地址。确认 health、旧 JSON 工具公开接口、栏目接口、未登录管理 401、Exchange 关闭 503。后端失败：不发布新前端，立即执行后端回滚。

### 5.2 前端切换

只发布已校验的新 dist。**不要**在正在服务的 dist 执行 npm build。使用与实际 DIST 同一文件系统的唯一候选目录，保留当前 dist 归档及原目录；把上版 `assets/` 中缺失的新旧 hashed 文件合并到新候选的 assets（不能覆盖新 index 或新资源）：

```bash
# [写入候选] NEXT_DIST 必须为 DIST 同级已批准的唯一新目录，不是 DIST 本身。
NEXT_DIST='__CONFIRM_UNIQUE_DIST_NEXT_PATH_ON_SAME_FILESYSTEM__'
PREVIOUS_DIST='__CONFIRM_UNIQUE_DIST_PREVIOUS_PATH_ON_SAME_FILESYSTEM__'
case "$NEXT_DIST/$PREVIOUS_DIST" in *__CONFIRM*) exit 1;; esac
test "$NEXT_DIST" != "$DIST" && test "$PREVIOUS_DIST" != "$DIST" || exit 1
test ! -e "$NEXT_DIST" && test ! -e "$PREVIOUS_DIST" || exit 1
mkdir -- "$NEXT_DIST"
cp -a "$CANDIDATE/frontend/dist/." "$NEXT_DIST/"
if test -d "$DIST/assets"; then
  mkdir -p "$NEXT_DIST/assets"
  cp -an "$DIST/assets/." "$NEXT_DIST/assets/"
fi
```

核对 Nginx 可读取新目录、index/入口 hash 对应、QsTArT 存在。实际 DIST 若是 symlink，**不要使用下面普通目录方案**，改为经批准的原子 symlink 切换并保持持久化路径独立。

```bash
# [覆盖入口] 已确认两个路径属于同一前端父目录且不是应用根/持久目录。
# 普通目录两次 rename 存在短暂空窗，仅在批准维护窗口执行；第二步失败立即恢复第一步。
test ! -L "$DIST" || exit 1
mv -- "$DIST" "$PREVIOUS_DIST" || exit 1
if ! mv -- "$NEXT_DIST" "$DIST"; then
  mv -- "$PREVIOUS_DIST" "$DIST"
  exit 1
fi
```

此操作不碰 backend、DB、uploads。普通目录方案不能称为无中断原子发布。仅静态文件更新通常不需 reload Nginx；本轮不要求改生产 Nginx。只有另外批准实际配置变更时，先 `sudo nginx -t` 成功再 reload。不要把仓库 HTTP 示例整份替换已上线 TLS/网关配置。

## Phase 6 — 上线验证（读取为主，测试写入另行批准）

```bash
# 以下为公开读取，不携带管理员 Cookie。
curl -fsS "$PUBLIC_ORIGIN/api/health"
curl -fsS "$PUBLIC_ORIGIN/api/news"
curl -fsS "$PUBLIC_ORIGIN/api/tools"
curl -fsS "$PUBLIC_ORIGIN/api/section-visuals"
curl -sS -o /dev/null -w '%{http_code}\n' "$PUBLIC_ORIGIN/api/exchange"    # 一期应 503
curl -sS -o /dev/null -w '%{http_code}\n' "$PUBLIC_ORIGIN/api/admin/exchange"  # 未登录应 401
curl -sS -o /dev/null -w '%{http_code}\n' "$PUBLIC_ORIGIN/exchange"        # SPA shell 可为 200，不代表功能已开放
```

检查 `/`、`/news`、已有 `/news/:id`、`/tools`、`/assistant`、`/exchange` 直接刷新；后台登录及新增管理入口；Banner 混合类型和动作；工具可用/不可用及内部/外链；QsTArT；栏目背景及文字深浅；日历/待办/展开；手机溢出与键盘焦点。API 200 不能代替这些人工验收。

图片须从**现有合法返回路径**抽查 200、Content-Type、文件可解码；不使用猜测 UUID，不打印内部链接。用浏览器 Network 确认请求同源、没有访问访问者自己的 localhost、没有 `/api/api`、旧 chunk 无 404。

一期分享表单应明确报未开放，不能出现成功编号；false 同时阻止公开列表，不承诺只读模式。不要为测试在生产擅自启用；如需真实新建/上传/删除，必须有批准的专用测试记录范围及清理清单，不碰既有投稿。

二期放行 Exchange 前：从公司内外分别测试页面、GET、POST、静态图片、直连 8000（如可路由），确保外部无法绕过网关；管理 API 仍独立鉴权。经过正式批准才修改实际有效环境开关并重启对应服务。投稿成功、图持久化、进程重启后读取、后台完整详情、删除与图清理、无图及多条随机均需验收。不能仅放行页面而漏保护 API/图片。

## Phase 7 — 稳定性观察

批准观察窗口（建议上线后立即、15–30 分钟、下一工作日），记录负责人及实际结果：服务 uptime/restart、5xx/413/429、DB 锁/权限错误、图片 404、登录 Cookie、磁盘增长、旧 chunk、图片清理失败。不要编造监控已正常。备份和旧版本保留至明确批准清理，不能自动删除。

## 回滚矩阵

### R1：仅前端故障

保持新后端/增量 schema 和所有数据。经批准，把当前 DIST 移至唯一故障目录、PREVIOUS_DIST 恢复为原 DIST；与发布同样先核实绝对路径/同父目录/非 symlink，失败立即恢复原入口。不要删除故障产物，保留定位证据。校验旧 index、assets、QsTArT、新闻/工具路由；保留新旧 hashed assets 兼容已打开页面。旧前端不能依赖本地开发 .env，使用已验证的旧 dist。

### R2：后端无法启动/关键 API 回归

1. 批准停服务及所有写入方，保全当前日志、DB 一致性快照与 uploads。
2. 按备份 manifest 恢复旧 `.py`/requirements，恢复原 unit/drop-in 指向**旧 venv 原路径**；不恢复 `.env` 到过期值、不覆盖 DB/uploads。新版本独有模块可暂留磁盘而不注册，不能使用批量删除清理。
3. 已确认 additive 的列/表通常保留，不 DROP；旧源码对其兼容须先在快照验证。若新前端依赖新 API，连同前端回退。
4. 需要时 daemon-reload，然后启动实际服务；检查旧首页、news/tools、管理员登录、DB 和图片。启动失败停止重复重启，检查原因。

如果原环境被原地升级，只恢复代码不够；必须恢复已验证的旧依赖环境。本手册推荐并行 venv 避免这个问题。

### R3：迁移/DB 兼容问题

优先回退应用并保留增量 schema；本次无必要做逆向删除。**恢复旧 DB 是第二次高风险审批，不是自动回滚默认动作。**

- 停所有新旧写入方，确认没有其他 worker/脚本连接；快照当前故障 DB（backup API）和 uploads。
- 计算发布后的新增/编辑/删除差异；恢复旧快照会丢失这些写入，包括 AUTOINCREMENT 序列。要先导出并核准数据重放/合并方案，不能让已有公开编号重新指向其他资源。
- 验证旧备份，在隔离恢复文件检查 integrity、旧数据、图片引用和编号序列；绝不复制单个活跃 WAL 主文件当作恢复。
- 经明确批准后，在完全停写状态把实际 DB 及其同名 WAL/SHM **精确路径**移至受限隔离备份位置，再将验证过的恢复文件替换到原绝对 DB_PATH，恢复正确 owner/mode。不要用广泛 glob、rm -rf 或删目录；若无法确认旧 sidecar 已安全处置，停止恢复。
- 重启前确认旧事务日志不会被错误应用到恢复 DB；复核数据、序列、uploads 引用。因这一步有数据丢失风险，实际命令应由掌握现场路径和差异的运维单独审核，不提供可误复制的一键覆盖命令。

### R4：图片存储故障

先检查稳定 UPLOADS 是否被版本路径改变、alias/权限是否不一致；恢复正确映射通常优于还原旧目录。既有和新图片一律保留，不把旧 uploads.tar 整体覆盖当前目录。必要时从备份仅补回确认缺失的文件（UUID 及引用核对），冲突转人工；绝不删除新上传图片以“匹配旧库”。

### R5：Exchange 异常

经批准将实际有效 `EXCHANGE_ENABLED=false` 并重启实际服务（当前实现不是自动热更新配置）；确认公共 GET/POST 503、管理仍鉴权。此开关不能修复全站故障，也不能阻断 `/uploads/exchange/`；如有敏感图片泄露，需同时启动经批准的网关/静态路径阻断事件流程，不以删除用户文件代替保护。

### 回滚完成标准

旧首页、新闻/工具、管理员登录正常；DB 旧记录和新增记录按批准策略保存；新旧上传图片可读；无启动/模块缺失/数据库锁阻塞；Exchange 状态符合批准决策。记录回滚版本、时间、数据差异、遗留风险，保持备份，不自动清理或重新发布。
