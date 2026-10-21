"""Compatibility endpoints for the single account login, not administrator elevation."""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from employee_security import denied, get_current_employee

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1000)


class AdminResponse(BaseModel):
    id: int
    username: str


def get_current_admin(request: Request):
    employee = get_current_employee(request)
    if not employee["admin_id"] or not employee["admin_active"]:
        raise denied("ADMIN_AUTH_REQUIRED", 403)
    return {"id": employee["admin_id"], "username": employee["admin_username"]}


@router.post("/login")
def login(payload: LoginRequest, request: Request):
    # Old clients perform a fresh unified login; no second-factor state survives.
    from employee_api import Credentials, login as account_login
    return account_login(Credentials(**payload.model_dump()), request)


@router.get("/me", response_model=AdminResponse)
def get_me(request: Request):
    return get_current_admin(request)


@router.post("/logout")
def logout(request: Request):
    from employee_api import logout as account_logout
    return account_logout(request)
