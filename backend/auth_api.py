from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from auth_security import verify_password
from database import get_db_connection


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1000)


class AdminResponse(BaseModel):
    id: int
    username: str


def _unauthorized():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


def get_current_admin(request: Request):
    admin_id = request.session.get("admin_id")

    if not isinstance(admin_id, int):
        raise _unauthorized()

    connection = get_db_connection()

    try:
        row = connection.execute(
            """
            SELECT id, username
            FROM admins
            WHERE id = ? AND is_active = 1
            """,
            (admin_id,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        request.session.clear()
        raise _unauthorized()

    return dict(row)


@router.post("/login", response_model=AdminResponse)
def login(payload: LoginRequest, request: Request):
    username = payload.username.strip()
    connection = get_db_connection()

    try:
        row = connection.execute(
            """
            SELECT id, username, password_hash
            FROM admins
            WHERE username = ? AND is_active = 1
            """,
            (username,),
        ).fetchone()
    finally:
        connection.close()

    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    request.session.clear()
    request.session["admin_id"] = row["id"]

    return {
        "id": row["id"],
        "username": row["username"],
    }


@router.get("/me", response_model=AdminResponse)
def get_me(request: Request):
    return get_current_admin(request)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}
