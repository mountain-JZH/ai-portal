"""One revocable session; effective privileges are read from server-side identities."""

import hashlib
import secrets
import time
from contextlib import closing

from fastapi import HTTPException, Request

from database import get_db_connection

EMPLOYEE_TTL = 7 * 24 * 60 * 60


def denied(code="EMPLOYEE_AUTH_REQUIRED", status=401):
    messages = {
        "EMPLOYEE_AUTH_REQUIRED": "请先登录员工账号",
        "ADMIN_AUTH_REQUIRED": "没有系统管理权限",
        "PASSWORD_CHANGE_REQUIRED": "首次登录或密码重置后，请先修改密码",
        "PROJECT_EDITOR_REQUIRED": "没有项目维护权限",
    }
    return HTTPException(status, {"code": code, "message": messages[code]})


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def employee_response(row):
    row = dict(row)
    admin = bool(row.get('admin_id') and row.get('admin_active'))
    return {
        "id": row["id"], "username": row["username"], "name": row["name"],
        "department": row["department"], "isActive": bool(row["is_active"]),
        "canEditProjects": admin or bool(row["can_edit_projects"]),
        "isAdmin": admin,
        "admin": {"id": row['admin_id'], "username": row['admin_username']} if admin else None,
        # Testing phase: keep the old column for compatibility, but do not force a second gate.
        "mustChangePassword": False,
        "createdAt": row["created_at"], "lastLoginAt": row["last_login_at"],
    }


def resolve_employee(request: Request, allow_password_change=False):
    token = request.session.get("employee_sid")
    if not isinstance(token, str) or len(token) != 64:
        raise denied()
    digest = token_hash(token)
    with closing(get_db_connection()) as connection:
        row = connection.execute(
            "SELECT e.*, a.username AS admin_username, a.is_active AS admin_active, "
            "s.expires_at, s.auth_version AS session_version "
            "FROM employee_sessions s JOIN employees e ON e.id=s.employee_id "
            "LEFT JOIN admins a ON a.id=e.admin_id "
            "WHERE s.token_hash=?", (digest,),
        ).fetchone()
    if (row is None or not row["is_active"] or row["expires_at"] <= time.time()
            or row["session_version"] != row["auth_version"]
            or (row['admin_id'] is not None and not row['admin_active'])):
        request.session.clear()
        raise denied()
    request.state.employee_session_hash = digest
    return dict(row)


def get_current_employee(request: Request):
    return resolve_employee(request)


def require_project_editor(request: Request):
    employee = get_current_employee(request)
    if not employee["can_edit_projects"] and not (employee['admin_id'] and employee['admin_active']):
        raise denied("PROJECT_EDITOR_REQUIRED", 403)
    return employee


def start_employee_session(request, employee, connection):
    # Rotate on login/change-password; never accept a caller-selected session ID.
    old = request.session.get("employee_sid")
    if isinstance(old, str):
        connection.execute("DELETE FROM employee_sessions WHERE token_hash=?", (token_hash(old),))
    token = secrets.token_hex(32)
    connection.execute("DELETE FROM employee_sessions WHERE expires_at<=?", (time.time(),))
    connection.execute(
        "INSERT INTO employee_sessions(token_hash,employee_id,auth_version,expires_at) VALUES(?,?,?,?)",
        (token_hash(token), employee["id"], employee["auth_version"], time.time() + EMPLOYEE_TTL),
    )
    request.session.clear()
    request.session.update(employee_sid=token, csrf=secrets.token_hex(32))


def limit_login(request, username, kind):
    """SQLite fixed windows shared across workers and process restarts; no passwords logged."""
    peer = request.client.host if request.client else "unknown"
    now = int(time.time())
    buckets = [(f"{kind}:peer:{peer}", 20), (f"{kind}:account:{username.casefold()}", 8)]
    with closing(get_db_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM auth_login_attempts WHERE window_start<=?", (now - 300,))
        for raw, limit in buckets:
            key = token_hash(raw)
            row = connection.execute("SELECT attempts FROM auth_login_attempts WHERE bucket=?", (key,)).fetchone()
            if row and row["attempts"] >= limit:
                raise HTTPException(429, "尝试过于频繁，请稍后再试", headers={"Retry-After": "300"})
        # Bound persistent tracking even under a large number of invented usernames.
        count = connection.execute("SELECT COUNT(*) FROM auth_login_attempts").fetchone()[0]
        if count >= 4096:
            raise HTTPException(429, "登录服务繁忙，请稍后再试", headers={"Retry-After": "300"})
        for raw, _ in buckets:
            connection.execute(
                "INSERT INTO auth_login_attempts(bucket,window_start,attempts) VALUES(?,?,1) "
                "ON CONFLICT(bucket) DO UPDATE SET attempts=attempts+1", (token_hash(raw), now),
            )
