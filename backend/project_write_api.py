"""Employee-authorized writes and read-only immutable history, with optimistic locking."""
from contextlib import closing
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, create_model

from database import get_db_connection
from employee_security import get_current_employee, require_project_editor
from project_data import FIELDS, TAIL_FIELDS, STAGES, key
from project_changes import NODE_IDS, TEXT_FIELDS, differences, metadata, record_changes, utc_now
from projects_api import employee_project
from project_updates import update_index

router = APIRouter(prefix="/api/projects", tags=["Project maintenance"], dependencies=[Depends(get_current_employee)])
EDITABLE = tuple(field for field in [*FIELDS, *TAIL_FIELDS] if field not in {"serial", "progressUpdate"})
ShortText = Annotated[str, StringConstraints(strict=True, max_length=3000)]
LongText = Annotated[str, StringConstraints(strict=True, max_length=50000)]
ProjectFields = create_model("ProjectFields", __config__=ConfigDict(extra="forbid"),
    **{field: ((LongText if field in TEXT_FIELDS or field in FIELDS[11:] else ShortText) | None, None) for field in EDITABLE},
    stages=(list[Annotated[str, StringConstraints(strict=True, max_length=2000)] | None], Field(default=None, min_length=11, max_length=11)))


class PatchProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(strict=True, ge=1)
    changes: ProjectFields


def writable_data(payload, existing=None):
    result = dict(existing) if existing is not None else dict.fromkeys([*FIELDS, *TAIL_FIELDS])
    if existing is None:
        result["stages"] = [None] * 11
    incoming = payload.model_dump(exclude_unset=True)
    if "stages" in incoming and incoming["stages"] is None:
        raise HTTPException(422, "必须提交完整的 11 个节点，允许每个节点为空")
    result.update(incoming)
    # Only actual, explicit node edits synchronize AC; unrelated writes retain it.
    if "stages" in incoming and incoming["stages"] != (existing or {}).get("stages"):
        active = next((i for i, value in enumerate(incoming["stages"]) if value == "进行中"), None)
        if active is not None:
            result["currentStage"] = STAGES[active]
        elif existing is not None:
            result["currentStage"] = existing.get("currentStage")
    if not isinstance(result.get("name"), str) or not key(result["name"]):
        raise HTTPException(422, "项目名称必填")
    return result


def unique_identity(connection, project, excluding=0):
    if connection.execute("SELECT 1 FROM projects WHERE name_key=? AND id<>?", (key(project["name"]), excluding)).fetchone():
        raise HTTPException(409, "项目名称重复，请核对，不能合并已有项目")
    resource = key(project.get("resource"))
    if resource and connection.execute("SELECT 1 FROM projects WHERE resource_key=? AND id<>?", (resource, excluding)).fetchone():
        raise HTTPException(409, "资源来源已被其他项目使用，请核对项目匹配关系")


def read_row(connection, project_id):
    row = connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "项目不存在")
    return row


def response(connection, row):
    updates = update_index(connection, row["id"]).get(row["id"], {})
    return employee_project({**json.loads(row["data"]), **metadata(row)}, updates)


@router.post("", status_code=201)
def create_project(payload: ProjectFields, request: Request, employee=Depends(require_project_editor)):
    project = writable_data(payload)
    with closing(get_db_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        employee = require_project_editor(request)
        unique_identity(connection, project)
        now = utc_now()
        cursor = connection.execute("""INSERT INTO projects(name_key,resource_key,data,imported_at,import_id,
            version,created_at,created_employee_id,updated_at,last_edit_source) VALUES(?,?,?,'',0,1,?,?,?,'employee')""",
            (key(project["name"]), key(project.get("resource")), json.dumps(project, ensure_ascii=False), now, employee["id"], now))
        project_id = cursor.lastrowid
        record_changes(connection, project_id, {}, project, employee, 1, now, creating=True)
        return response(connection, read_row(connection, project_id))


@router.patch("/{project_id}")
def edit_project(project_id: int, payload: PatchProject, request: Request, employee=Depends(require_project_editor)):
    with closing(get_db_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        employee = require_project_editor(request)
        row = read_row(connection, project_id)
        if row["version"] != payload.version:
            raise HTTPException(409, "该项目已被其他人员更新，请重新加载并核对修改内容。")
        old = json.loads(row["data"])
        project = writable_data(payload.changes, old)
        unique_identity(connection, project, project_id)
        if not differences(old, project):
            return {**response(connection, row), "unchanged": True}
        now, version = utc_now(), row["version"] + 1
        connection.execute("""UPDATE projects SET name_key=?,resource_key=?,data=?,version=?,updated_at=?,last_edit_source='employee'
            WHERE id=? AND version=?""", (key(project["name"]), key(project.get("resource")), json.dumps(project, ensure_ascii=False),
                                         version, now, project_id, payload.version))
        record_changes(connection, project_id, old, project, employee, version, now)
        return response(connection, read_row(connection, project_id))


@router.get("/{project_id}/history")
def history(project_id: int, field: str = Query("", max_length=100),
            limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    if field and field not in {*EDITABLE, *NODE_IDS, "serial", "progressUpdate", "__created__"}:
        raise HTTPException(422, "不支持的历史字段")
    with closing(get_db_connection()) as connection:
        project = read_row(connection, project_id)
        where, args = "project_id=?", [project_id]
        if field:
            where += " AND field_name=?"
            args.append(field)
        total = connection.execute(f"SELECT COUNT(*) FROM project_change_logs WHERE {where}", args).fetchone()[0]
        records = connection.execute(f"SELECT * FROM project_change_logs WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?", (*args, limit, offset)).fetchall()
        items = [{**dict(row), "old_value": json.loads(row["old_value"]), "new_value": json.loads(row["new_value"])} for row in records]
        return {"project": {"id": project_id, "name": json.loads(project["data"])["name"], "version": project["version"]},
                "items": items, "total": total, "offset": offset, "limit": limit}
