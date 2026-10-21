"""Employee project reads and administrator-owned transactional import previews."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import secrets
import time

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from auth_api import get_current_admin
from employee_security import get_current_employee
from project_changes import metadata, record_changes, differences
from project_updates import update_index, update_metadata, update_now, in_update_range
from database import get_db_connection
from project_data import (BUSINESS_FIELDS, FIELDS, TAIL_FIELDS, MAX_FILE_SIZE, STAGES, enrich, key,
                          parse_workbook, plan_import)


router = APIRouter(prefix="/api/admin/projects", tags=["Projects"],
                   dependencies=[Depends(get_current_admin)])
employee_router = APIRouter(prefix="/api/projects", tags=["Employee projects"],
                           dependencies=[Depends(get_current_employee)])

BUSINESS_GROUPS = {"光伏": ("pvArea", "pvCapacity"), "储能": ("storageCapacity",),
                   "充电桩": ("chargingScale",), "分布式能源": ("energyType", "energyScale")}


def meaningful(value):
    return value is not None and str(value).strip().upper() not in {
        "", "/", "／", "-", "—", "无", "暂无", "未填写", "不涉及", "N/A", "NA"}


def employee_project(project, updates=None, now=None):
    # Explicit read contract: future JSON/import metadata is not exposed by accident.
    result = enrich({field: project.get(field) for field in
                     [*FIELDS, *TAIL_FIELDS, "stages", "id", "importedAt", "importId", "version", "createdAt", "updatedAt", "lastEditSource"]})
    result["businessTypes"] = [name for name, fields in BUSINESS_GROUPS.items()
                               if any(meaningful(project.get(field)) for field in fields)]
    result.update(update_metadata(updates or {}, now or update_now()))
    return result


@employee_router.get("")
def employee_dashboard(
    view: str = Query("overview", pattern="^(overview|daily|people|business)$"),
    search: str = Query("", max_length=300), stage: str = Query("", max_length=100),
    district: str = Query("", max_length=200), owner: str = Query("", max_length=200),
    leader: str = Query("", max_length=200), priority: str = Query("", max_length=200),
    coordination: bool = False,
    role: str = Query("owner", pattern="^(owner|leader)$"),
    person: str = Query("", max_length=200), business: list[str] = Query(default=[]),
    sort: str = Query("priority", pattern="^(priority|updated|name)$"),
    update_days: int = Query(1, ge=1, le=30),
):
    if update_days not in {1, 7, 30}:
        raise HTTPException(422, "更新范围仅支持今日、近 7 天或近 30 天")
    if len(business) > 4 or any(name not in BUSINESS_GROUPS for name in business):
        raise HTTPException(422, "业务类型仅支持光伏、储能、充电桩、分布式能源")
    with closing(get_db_connection()) as connection:
        connection.execute("BEGIN")  # Data and its log projection share one read snapshot.
        now = update_now()
        updates = update_index(connection)
        projects = [employee_project(project, updates.get(project["id"]), now) for project in rows(connection)]
        latest_import = latest(connection)
    needle = search.strip().casefold()

    def selected(p):
        if view == "daily":
            return in_update_range(p["latestBusinessUpdateAt"], now, update_days)
        if view == "people":
            return not person or p.get(role) == person
        if view == "business":
            return not business or bool(set(business).intersection(p["businessTypes"]))
        hay = " ".join(str(p.get(field) or "") for field in
                       ["name", "resource", "leader", "owner", "district", "situation", "nextStep", "coordination"])
        return ((not needle or needle in hay.casefold()) and
                (not stage or p["stageGroup"] == stage) and
                (not district or p.get("district") == district) and
                (not owner or p.get("owner") == owner) and
                (not leader or p.get("leader") == leader) and
                (not priority or str(p.get("priority") or "").startswith(priority)) and
                (not coordination or p["needsCoordination"]) and
                (not business or bool(set(business).intersection(p["businessTypes"]))))

    filtered = [p for p in projects if selected(p)]

    def priority_rank(p):
        return next((i for i, label in enumerate(("甲", "乙", "丙"))
                     if str(p.get("priority") or "").startswith(label)), 9)

    if view == "daily" or sort == "updated":
        filtered.sort(key=lambda p: (p["latestBusinessUpdateAt"] or "", p["id"]), reverse=True)
    else:
        filtered.sort(key=lambda p: (str(p.get("name") or "") if sort == "name" else priority_rank(p), p["id"]))
    return {"projects": filtered, "filteredCount": len(filtered), "stages": STAGES,
            "updatesAsOf": now.isoformat(),
            "businessFields": BUSINESS_FIELDS, "latestImport": latest_import,
            "summary": {"total": len(projects), "updated": sum(p["updated"] for p in projects),
                        "priority": sum(str(p.get("priority") or "").startswith("甲") for p in projects),
                        "coordination": sum(p["needsCoordination"] for p in projects),
                        "operational": sum(p["isOperational"] for p in projects)},
            "distribution": [{"name": name, "count": sum(p["stageGroup"] == name for p in projects)}
                             for name in [*STAGES, "未明确"]],
            "businessCounts": {name: sum(name in p["businessTypes"] for p in projects) for name in BUSINESS_GROUPS},
            "personCounts": {field: {name: sum(p.get(field) == name for p in projects)
                                      for name in sorted({p[field] for p in projects if p.get(field)})}
                             for field in ["leader", "owner"]},
            "options": {field: sorted({p[field] for p in projects if p.get(field)})
                        for field in ["leader", "owner", "district", "priority"]}}


@employee_router.get("/{project_id}")
def employee_detail(project_id: int):
    with closing(get_db_connection()) as connection:
        connection.execute("BEGIN")
        row = connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(404, "项目不存在")
        updates = update_index(connection, project_id).get(project_id, {})
        return employee_project({**json.loads(row["data"]), **metadata(row)}, updates)


def rows(connection):
    return [{**json.loads(row["data"]), **metadata(row)} for row in connection.execute("SELECT * FROM projects ORDER BY id")]


def revision(connection):
    snapshot = [tuple(row) for row in connection.execute("SELECT * FROM projects ORDER BY id")]
    snapshot.append(tuple(connection.execute("SELECT COALESCE(MAX(id), 0) FROM project_imports").fetchone()))
    return hashlib.sha256(json.dumps(snapshot, ensure_ascii=False).encode()).hexdigest()


def latest(connection):
    row = connection.execute("SELECT id, imported_at, counts FROM project_imports ORDER BY id DESC LIMIT 1").fetchone()
    return {"id": row["id"], "importedAt": row["imported_at"], "counts": json.loads(row["counts"])} if row else None


@router.get("")
def dashboard(search: str = Query("", max_length=300), stage: str = Query("", max_length=100),
              district: str = Query("", max_length=200), focus: str = Query("", pattern="^(|priority|coordination|operational)$")):
    with closing(get_db_connection()) as connection:
        all_projects = [enrich(project) for project in rows(connection)]
        latest_import = latest(connection)
    distribution = [{"name": name, "count": sum(p["stageGroup"] == name for p in all_projects)}
                    for name in [*STAGES, "未明确"]]
    needle = search.strip().casefold()
    filtered = [p for p in all_projects if (not needle or needle in " ".join(
        str(p.get(field) or "") for field in ["name", "owner", "resource", "leader", "district", "situation", "nextStep", "coordination"]).casefold())
        and (not stage or p["stageGroup"] == stage)
        and (not district or p["district"] == district)
        and (not focus or p[{"priority": "isPriority", "coordination": "needsCoordination", "operational": "isOperational"}[focus]])]
    return {
        "summary": {"total": len(all_projects), "priority": sum(p["isPriority"] for p in all_projects),
                    "coordination": sum(p["needsCoordination"] for p in all_projects),
                    "operational": sum(p["isOperational"] for p in all_projects)},
        "distribution": distribution, "projects": filtered, "filteredCount": len(filtered),
        "coordination": [p for p in all_projects if p["needsCoordination"]],
        "districts": sorted({p["district"] for p in all_projects if p["district"]}),
        "latestImport": latest_import, "stages": STAGES, "businessFields": BUSINESS_FIELDS,
    }


@router.post("/imports/preview")
def preview(file: UploadFile = File(...), admin=Depends(get_current_admin)):
    try:
        if not (file.filename or "").lower().endswith(".xlsx"):
            raise HTTPException(400, "仅支持 .xlsx 原始台账，不支持 .xls 或含宏的 .xlsm")
        if file.content_type not in {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/octet-stream", "application/zip"}:
            raise HTTPException(400, "上传文件类型必须为 Excel .xlsx")
        content = file.file.read(MAX_FILE_SIZE + 1)
        incoming, skipped, warnings, errors = parse_workbook(content)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    finally:
        file.file.close()
    with closing(get_db_connection()) as connection, connection:
        # Lock the snapshot so previews never combine different database revisions.
        connection.execute("BEGIN IMMEDIATE")
        counts, operations, conflicts = plan_import(incoming, rows(connection))
        errors.extend(conflicts)
        for item in operations:
            if item["id"] is not None and item["action"] == "updated":
                current = connection.execute("SELECT last_edit_source FROM projects WHERE id=?", (item["id"],)).fetchone()
                if current["last_edit_source"] == "employee":
                    errors.append(f"第 {item['row']} 行对应项目已有网页维护内容，禁止 Excel 覆盖；请通过项目维护页核对。")
        counts["invalid"] = skipped + sum("缺少项目名称" in error for error in errors)
        counts["skipped"] = skipped
        payload = {"counts": counts, "operations": operations, "warnings": warnings}
        token = None
        if not errors:
            token = secrets.token_urlsafe(32)
            connection.execute("DELETE FROM project_import_previews WHERE expires_at < ? OR admin_id = ?",
                               (int(time.time()), admin["id"]))
            connection.execute("INSERT INTO project_import_previews VALUES (?, ?, ?, ?, ?)",
                               (token, admin["id"], int(time.time()) + 1800, revision(connection),
                                json.dumps(payload, ensure_ascii=False)))
    return {"token": token, "canConfirm": not errors, "counts": counts,
            "warnings": warnings, "errors": errors,
            "rows": [{**item, "project": enrich(item["project"])} for item in operations]}


class ConfirmImport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=20, max_length=100)


@router.post("/imports/confirm")
def confirm(payload: ConfirmImport, admin=Depends(get_current_admin), employee=Depends(get_current_employee)):
    with closing(get_db_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        preview_row = connection.execute("SELECT * FROM project_import_previews WHERE token = ? AND admin_id = ?",
                                         (payload.token, admin["id"])).fetchone()
        if preview_row is None or preview_row["expires_at"] < time.time():
            raise HTTPException(409, "预览已取消、过期或已被使用，请重新上传")
        if revision(connection) != preview_row["base_revision"]:
            raise HTTPException(409, "项目台账已发生变化，请重新上传并核对预览")
        data = json.loads(preview_row["payload"])
        now = datetime.now(timezone.utc).isoformat()
        import_id = connection.execute(
            "INSERT INTO project_imports (imported_at, admin_id, counts) VALUES (?, ?, ?)",
            (now, admin["id"], json.dumps(data["counts"]))).lastrowid
        for item in data["operations"]:
            project = item["project"]
            encoded = json.dumps(project, ensure_ascii=False)
            if item["id"] is None:
                cursor = connection.execute("INSERT INTO projects (name_key, resource_key, data, imported_at, import_id,created_at,last_edit_source) VALUES (?, ?, ?, ?, ?,?,'admin_import')",
                                   (key(project["name"]), key(project["resource"]), encoded, now, import_id, now))
                record_changes(connection, cursor.lastrowid, {}, project, employee, 1, now, "admin_import", admin["id"], creating=True)
            else:
                existing = connection.execute("SELECT * FROM projects WHERE id=?", (item["id"],)).fetchone()
                old = json.loads(existing["data"])
                changed = bool(differences(old, project))
                if changed and existing["last_edit_source"] == "employee":
                    raise HTTPException(409, "项目已有网页维护内容，禁止 Excel 覆盖")
                version = existing["version"] + int(changed)
                connection.execute("UPDATE projects SET data=?,imported_at=?,import_id=?,version=?,updated_at=?,last_edit_source=? WHERE id=?",
                                   (encoded, now, import_id, version, now if changed else existing["updated_at"],
                                    "admin_import" if changed else existing["last_edit_source"], item["id"]))
                if changed:
                    record_changes(connection, item["id"], old, project, employee, version, now, "admin_import", admin["id"])
        connection.execute("DELETE FROM project_import_previews WHERE token = ?", (payload.token,))
        return {"id": import_id, "importedAt": now, "counts": data["counts"]}


@router.delete("/imports/preview/{token}")
def cancel_preview(token: str, admin=Depends(get_current_admin)):
    with closing(get_db_connection()) as connection, connection:
        connection.execute("DELETE FROM project_import_previews WHERE token = ? AND admin_id = ?", (token, admin["id"]))
    return {"cancelled": True}


@router.get("/{project_id}")
def detail(project_id: int):
    with closing(get_db_connection()) as connection:
        row = connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "项目不存在")
    return enrich({**json.loads(row["data"]), **metadata(row)})


class ProjectImportBodyLimit:
    """Bound multipart transport before Starlette parses or spools an upload."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/admin/projects/imports/preview":
            await self.app(scope, receive, send)
            return
        from starlette.responses import JSONResponse
        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > MAX_FILE_SIZE + 64 * 1024:
                await JSONResponse({"detail": "上传请求超过 4 MB 文件与表单允许范围"}, status_code=413)(scope, receive, send)
                return
            messages.append(message)
            if not message.get("more_body", False):
                break
        iterator = iter(messages)

        async def replay():
            try:
                return next(iterator)
            except StopIteration:
                return await receive()

        await self.app(scope, replay, send)
