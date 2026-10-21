import os
import mimetypes

import requests

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from auth_api import router as auth_router
from content_api import (
    announcement_admin_router,
    announcement_router,
    banner_admin_router,
    banner_router,
)
from database import get_db_connection, init_database
from exchange_api import router as exchange_router, admin_router as exchange_admin_router, ExchangeSubmissionGuard
from news_api import (
    admin_router as news_admin_router,
    router as news_router,
)
from tools_api import admin_router as tools_admin_router, router as tools_router
from upload_api import UPLOAD_ROOT, router as upload_router
from projects_api import ProjectImportBodyLimit, router as projects_router, employee_router as employee_projects_router
from project_write_api import router as project_write_router
from employee_api import router as employee_router, admin_router as employee_admin_router
from employee_security import EMPLOYEE_TTL
from portal_access import PortalAccess
from pathlib import Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from section_visuals_api import (
    admin_router as section_visuals_admin_router,
    router as section_visuals_router,
)


load_dotenv()


DIFY_API_URL = os.getenv("DIFY_API_URL")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET environment variable is required")


init_database()


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_error_without_secrets(request, error):
    # Pydantic's default response can echo invalid password inputs.
    return JSONResponse({"detail": [{key: item[key] for key in ("type", "loc", "msg") if key in item}
                                    for item in error.errors()]}, status_code=422)

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
# Windows MIME registries may omit WebP; serve newly cropped images consistently.
mimetypes.add_type("image/webp", ".webp")
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")

qstart_directory = Path(__file__).resolve().parent.parent / "frontend" / "dist" / "tools" / "qstart"
if not qstart_directory.is_dir():
    qstart_directory = Path(__file__).resolve().parent.parent / "frontend" / "public" / "tools" / "qstart"
if qstart_directory.is_dir():
    app.mount("/tools/qstart", StaticFiles(directory=qstart_directory, html=True), name="qstart")

app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(employee_admin_router)
app.include_router(projects_router)
app.include_router(employee_projects_router)
app.include_router(project_write_router)
app.add_middleware(ProjectImportBodyLimit)
app.include_router(news_router)
app.include_router(news_admin_router)
app.include_router(banner_router)
app.include_router(banner_admin_router)
app.include_router(announcement_router)
app.include_router(announcement_admin_router)
app.include_router(tools_router)
app.include_router(tools_admin_router)
app.include_router(upload_router)
app.include_router(section_visuals_router)
app.include_router(section_visuals_admin_router)
app.include_router(exchange_router)
app.include_router(exchange_admin_router)
app.add_middleware(ExchangeSubmissionGuard)
app.add_middleware(PortalAccess)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie=os.getenv("SESSION_COOKIE_NAME", "ai_portal_admin_session"),
    max_age=EMPLOYEE_TTL,
    same_site="lax",
    https_only=os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/api/health")
def health_check():
    connection = get_db_connection()

    try:
        connection.execute("SELECT 1").fetchone()
    finally:
        connection.close()

    return {"status": "ok"}


@app.get("/api/hello")
def hello():
    return {
        "message": "你好，我是 FastAPI 后端"
    }


@app.post("/api/chat")
def chat(request: ChatRequest):

    url = f"{DIFY_API_URL}/chat-messages"

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {},
        "query": request.message,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": "ai-portal-user"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        return {
            "answer": data["answer"]
        }

    except Exception as error:
        print("调用 Dify 失败：", error)

        return {
            "answer": "调用智能助手失败，请检查后端日志。"
        }
