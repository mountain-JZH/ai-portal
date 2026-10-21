"""Explicit employee login for existing temporary-database integration fixtures."""
import asyncio
from contextlib import closing
from http.cookies import SimpleCookie
import json

TEST_EMPLOYEE_PASSWORD = "fixture-employee-password-only"


def seed_employee():
    from database import get_db_connection
    from auth_security import hash_password
    with closing(get_db_connection()) as connection, connection:
        row = connection.execute("SELECT id FROM employees WHERE username='fixture-employee'").fetchone()
        if not row:
            connection.execute("INSERT INTO employees(username,name,department,password_hash,must_change_password) VALUES(?,?,?,?,0)",
                               ("fixture-employee", "Fixture", "Tests", hash_password(TEST_EMPLOYEE_PASSWORD)))


def employee_session(app, raw_call):
    seed_employee()
    status, headers, body = asyncio.run(raw_call(app, "GET", "/api/employee/csrf"))
    assert status == 200
    cookies = SimpleCookie(); cookies.load(headers[b"set-cookie"].decode())
    cookie = "; ".join(f"{k}={v.value}" for k, v in cookies.items())
    status, headers, body = asyncio.run(raw_call(app, "POST", "/api/employee/login",
        json.dumps({"username": "fixture-employee", "password": TEST_EMPLOYEE_PASSWORD}).encode(),
        {"cookie": cookie, "content-type": "application/json", "x-csrf-token": json.loads(body)["csrfToken"]}))
    assert status == 200, body
    cookies.load(headers[b"set-cookie"].decode())
    return "; ".join(f"{k}={v.value}" for k, v in cookies.items()), json.loads(body)["csrfToken"]


def http_employee_login(session, origin):
    result = session.get(origin + "/api/employee/csrf", timeout=5)
    session.headers["X-CSRF-Token"] = result.json()["csrfToken"]
    response = session.post(origin + "/api/employee/login", json={
        "username": "fixture-employee", "password": TEST_EMPLOYEE_PASSWORD}, timeout=5)
    assert response.status_code == 200, response.text
    session.headers["X-CSRF-Token"] = response.json()["csrfToken"]
