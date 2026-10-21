"""Employee login and administrator-managed accounts. No public registration."""

import secrets
from contextlib import closing
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from auth_api import get_current_admin
from auth_security import hash_password, verify_password
from database import get_db_connection
from employee_security import (employee_response, get_current_employee, limit_login,
                               resolve_employee, start_employee_session, token_hash)

router = APIRouter(prefix="/api/employee", tags=["Employee authentication"])
admin_router = APIRouter(prefix="/api/admin/employees", tags=["Employees"],
                         dependencies=[Depends(get_current_admin)])
_dummy_hash = hash_password(secrets.token_urlsafe(32))


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1000)


class PasswordChange(BaseModel):
    currentPassword: str = Field(min_length=1, max_length=1000)
    newPassword: str = Field(min_length=12, max_length=128)


class EmployeeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    department: str = Field(min_length=1, max_length=100)
    isActive: bool = True
    canEditProjects: bool = False

    @field_validator("name", "department")
    @classmethod
    def trim_required(cls, value):
        if not value.strip():
            raise ValueError("不能为空")
        return value.strip()


class EmployeeCreate(EmployeeUpdate):
    username: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{2,63}$")
    temporaryPassword: str = Field(min_length=12, max_length=128)


class PasswordReset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    temporaryPassword: str = Field(min_length=12, max_length=128)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def employee_row(connection, employee_id):
    row = connection.execute("SELECT e.*,a.username AS admin_username,a.is_active AS admin_active FROM employees e LEFT JOIN admins a ON a.id=e.admin_id WHERE e.id=?", (employee_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "员工账号不存在")
    return row


@router.get("/csrf")
def csrf(request: Request):
    if not isinstance(request.session.get("csrf"), str):
        request.session["csrf"] = secrets.token_hex(32)
    return {"csrfToken": request.session["csrf"]}


@router.post("/login")
def login(payload: Credentials, request: Request):
    username = payload.username.strip().lower()
    limit_login(request, username, "employee")
    with closing(get_db_connection()) as connection, connection:
        row = connection.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchone()
        admin = connection.execute("SELECT * FROM admins WHERE id=?", (row['admin_id'],)).fetchone() if row and row['admin_id'] else None
        if row is None:
            admin = connection.execute("SELECT * FROM admins WHERE lower(username)=?", (username,)).fetchone()
        credential = admin if admin is not None else row
        valid = verify_password(payload.password, credential['password_hash'] if credential else _dummy_hash)
        if not valid and row and not row['admin_id']:
            collision = connection.execute("SELECT * FROM admins WHERE lower(username)=?", (username,)).fetchone()
            if collision and collision['is_active'] and verify_password(payload.password, collision['password_hash']):
                raise HTTPException(409, '管理员与员工账号重名但未关联，请在本地核实身份；未合并或覆盖账号')
        if not valid or credential is None or not credential['is_active'] or (row and not row['is_active']) or (row and row['admin_id'] and admin is None):
            raise HTTPException(401, "账号或密码错误，或账号已停用")
        connection.execute("BEGIN IMMEDIATE")
        if admin is not None:
            fresh_admin = connection.execute('SELECT * FROM admins WHERE id=?', (admin['id'],)).fetchone()
            if not fresh_admin or not fresh_admin['is_active'] or fresh_admin['password_hash'] != admin['password_hash']:
                raise HTTPException(401, '账号状态已变化，请重新登录')
        if row is None:
            # Only possession of the existing administrator password can establish this link.
            if connection.execute('SELECT 1 FROM employees WHERE username=? OR admin_id=?', (username, admin['id'])).fetchone():
                raise HTTPException(409, '账号关联已变化，请重新登录核对')
            identity = connection.execute('INSERT INTO employees(username,name,department,password_hash,must_change_password,admin_id) VALUES(?,?,?,?,0,?)',
                                          (username, admin['username'], '平台管理', admin['password_hash'], admin['id'])).lastrowid
            row = employee_row(connection, identity)
        fresh = employee_row(connection, row["id"])
        if not fresh["is_active"] or fresh["auth_version"] != row["auth_version"] or fresh['admin_id'] != row['admin_id']:
            raise HTTPException(401, "账号状态已变化，请重新登录")
        connection.execute("UPDATE employees SET last_login_at=? WHERE id=?", (utc_now(), row["id"]))
        start_employee_session(request, fresh, connection)
        result = employee_response(employee_row(connection, row["id"]))
    return {**result, "csrfToken": request.session["csrf"]}


@router.get("/me")
def me(request: Request):
    return {**employee_response(resolve_employee(request, True)), "csrfToken": request.session["csrf"]}


@router.post("/logout")
def logout(request: Request):
    token = request.session.get("employee_sid")
    if isinstance(token, str):
        with closing(get_db_connection()) as connection, connection:
            connection.execute("DELETE FROM employee_sessions WHERE token_hash=?", (token_hash(token),))
    request.session.clear()
    return {"message": "已退出员工及管理员会话"}


@router.post("/password")
def change_password(payload: PasswordChange, request: Request):
    employee = resolve_employee(request, True)
    limit_login(request, employee["username"], "password-change")
    with closing(get_db_connection()) as connection:
        credential = connection.execute('SELECT password_hash FROM admins WHERE id=?', (employee['admin_id'],)).fetchone() if employee['admin_id'] else employee
    if not credential or not verify_password(payload.currentPassword, credential["password_hash"]):
        raise HTTPException(400, "当前密码不正确")
    if verify_password(payload.newPassword, credential["password_hash"]):
        raise HTTPException(400, "新密码不能与当前密码相同")
    encoded = hash_password(payload.newPassword)
    with closing(get_db_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        # Do not overwrite an administrator reset that happened during hashing.
        row = employee_row(connection, employee["id"])
        if not row["is_active"] or row["auth_version"] != employee["auth_version"]:
            raise HTTPException(401, "会话已失效，请重新登录")
        if row['admin_id']:
            updated = connection.execute('UPDATE admins SET password_hash=? WHERE id=? AND is_active=1 AND password_hash=?',
                                         (encoded, row['admin_id'], credential['password_hash']))
            if updated.rowcount != 1:
                raise HTTPException(401, '账号状态已变化，请重新登录')
        connection.execute("UPDATE employees SET password_hash=?,must_change_password=0,auth_version=auth_version+1 WHERE id=?",
                           (encoded, employee["id"]))
        connection.execute("DELETE FROM employee_sessions WHERE employee_id=?", (employee["id"],))
        row = employee_row(connection, employee["id"])
        start_employee_session(request, row, connection)
        result = employee_response(row)
    return {**result, "csrfToken": request.session["csrf"]}


@admin_router.get("")
def list_employees():
    with closing(get_db_connection()) as connection:
        return [employee_response(row) for row in connection.execute("SELECT e.*,a.username AS admin_username,a.is_active AS admin_active FROM employees e LEFT JOIN admins a ON a.id=e.admin_id ORDER BY e.id")]


@admin_router.post("", status_code=201)
def create_employee(payload: EmployeeCreate):
    import sqlite3
    try:
        with closing(get_db_connection()) as connection, connection:
            if connection.execute('SELECT 1 FROM admins WHERE lower(username)=?', (payload.username.lower(),)).fetchone():
                raise HTTPException(409, '账号属于现有管理员，请使用统一登录，不可创建重名员工')
            cursor = connection.execute(
                "INSERT INTO employees(username,name,department,password_hash,is_active,can_edit_projects,must_change_password) VALUES(?,?,?,?,?,?,0)",
                (payload.username.lower(), payload.name, payload.department, hash_password(payload.temporaryPassword),
                 int(payload.isActive), int(payload.canEditProjects)),
            )
            return employee_response(employee_row(connection, cursor.lastrowid))
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "员工账号已存在") from error


@admin_router.put("/{employee_id}")
def update_employee(employee_id: int, payload: EmployeeUpdate, request: Request):
    current = get_current_employee(request)
    if employee_id == current["id"] and not payload.isActive:
        raise HTTPException(400, "不能停用当前正在管理的员工账号")
    with closing(get_db_connection()) as connection, connection:
        employee_row(connection, employee_id)
        connection.execute("UPDATE employees SET name=?,department=?,is_active=?,can_edit_projects=? WHERE id=?",
                           (payload.name, payload.department, int(payload.isActive), int(payload.canEditProjects), employee_id))
        if not payload.isActive:
            connection.execute("UPDATE employees SET auth_version=auth_version+1 WHERE id=?", (employee_id,))
            connection.execute("DELETE FROM employee_sessions WHERE employee_id=?", (employee_id,))
        return employee_response(employee_row(connection, employee_id))


@admin_router.post("/{employee_id}/reset-password")
def reset_password(employee_id: int, payload: PasswordReset):
    encoded = hash_password(payload.temporaryPassword)
    with closing(get_db_connection()) as connection, connection:
        row = employee_row(connection, employee_id)
        if row['admin_id']:
            connection.execute('UPDATE admins SET password_hash=? WHERE id=?', (encoded, row['admin_id']))
        connection.execute("UPDATE employees SET password_hash=?,must_change_password=0,auth_version=auth_version+1 WHERE id=?",
                           (encoded, employee_id))
        connection.execute("DELETE FROM employee_sessions WHERE employee_id=?", (employee_id,))
    return {"message": "密码已重置，旧会话已撤销；使用新密码重新登录"}
