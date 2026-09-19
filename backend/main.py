import os

import requests

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from news_api import router as news_router


load_dotenv()


DIFY_API_URL = os.getenv("DIFY_API_URL")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")


app = FastAPI()

app.include_router(news_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


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