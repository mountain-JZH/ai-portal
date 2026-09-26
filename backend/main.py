import os

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
from news_api import (
    admin_router as news_admin_router,
    router as news_router,
)
from tools_api import admin_router as tools_admin_router, router as tools_router
from upload_api import UPLOAD_ROOT, router as upload_router


load_dotenv()


DIFY_API_URL = os.getenv("DIFY_API_URL")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET environment variable is required")


init_database()


app = FastAPI()

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="ai_portal_admin_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
)

app.include_router(auth_router)
app.include_router(news_router)
app.include_router(news_admin_router)
app.include_router(banner_router)
app.include_router(banner_admin_router)
app.include_router(announcement_router)
app.include_router(announcement_admin_router)
app.include_router(tools_router)
app.include_router(tools_admin_router)
app.include_router(upload_router)


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
