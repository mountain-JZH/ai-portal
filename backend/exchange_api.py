"""Exchange resources: immediate publishing, bounded requests, existing admin auth."""

from collections import OrderedDict, deque
from datetime import datetime, timezone
import json
import logging
import os
import re
import sqlite3
from threading import Lock
from time import monotonic
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from starlette.responses import JSONResponse

from auth_api import get_current_admin
from database import get_db_connection
from image_processing import validate_and_encode_image
from upload_api import MAX_IMAGE_SIZE, UPLOAD_ROOT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/exchange", tags=["Exchange"])
admin_router = APIRouter(
    prefix="/api/admin/exchange", tags=["Exchange administration"],
    dependencies=[Depends(get_current_admin)],
)


def exchange_enabled():
    # Explicit opt-in only AFTER the site's internal network boundary is verified.
    return os.getenv("EXCHANGE_ENABLED", "").lower() in {"1", "true", "yes"}


def require_exchange_enabled():
    if not exchange_enabled():
        raise HTTPException(503, "互通有无暂未开放")


class SubmissionLimiter:
    """Per-process, bounded sliding windows. Never reads client-supplied proxy headers."""

    def __init__(self, per_peer=10, total=60, seconds=60):
        self.per_peer, self.total, self.seconds = per_peer, total, seconds
        self.peers = OrderedDict()
        self.all_requests = deque()
        self.lock = Lock()

    def allow(self, peer):
        with self.lock:
            now = monotonic()
            while self.all_requests and self.all_requests[0] <= now - self.seconds:
                self.all_requests.popleft()
            if len(self.all_requests) >= self.total:
                return False
            timestamps = self.peers.setdefault(peer, deque())
            self.peers.move_to_end(peer)
            while timestamps and timestamps[0] <= now - self.seconds:
                timestamps.popleft()
            if len(timestamps) >= self.per_peer:
                return False
            timestamps.append(now)
            self.all_requests.append(now)
            while len(self.peers) > 1024:
                self.peers.popitem(last=False)
            return True


submission_limiter = SubmissionLimiter()
MAX_REQUEST_BYTES = MAX_IMAGE_SIZE + 64 * 1024


class ExchangeSubmissionGuard:
    """Reject before multipart parsing; cap even chunked bodies in a bounded buffer."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"].rstrip("/") != "/api/exchange":
            return await self.app(scope, receive, send)
        if not exchange_enabled():
            return await JSONResponse({"detail": "互通有无暂未开放"}, 503)(scope, receive, send)
        peer = (scope.get("client") or ("unknown", 0))[0]
        if not submission_limiter.allow(peer):
            return await JSONResponse({"detail": "提交过于频繁，请稍后重试"}, 429,
                                      headers={"Retry-After": "60"})(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "无效的请求长度"}, 400)(scope, receive, send)
        if length < 0 or length > MAX_REQUEST_BYTES:
            return await JSONResponse({"detail": "请求过大，图片最大 5MB"}, 413)(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > MAX_REQUEST_BYTES:
                return await JSONResponse({"detail": "请求过大，图片最大 5MB"}, 413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        return await self.app(scope, bounded_receive, send)


class ExchangeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=90)
    description: str = Field(min_length=1, max_length=1500)
    reason: str = Field(default="", max_length=600)
    domain: Literal["光伏与储能", "AI 与办公", "软件运维", "项目与管理", "工作方法"]
    type: Literal["文章", "工具", "视频", "书籍", "工作经验"]
    tags: list[str] = Field(default_factory=list, max_length=8)
    externalUrl: str = Field(default="", max_length=2048)

    @field_validator("title", "description", "reason", "externalUrl", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        result = []
        for tag in value:
            tag = tag.strip()
            if not tag or len(tag) > 40:
                raise ValueError("关键词必须为 1–40 个字符")
            if tag not in result:
                result.append(tag)
        return result

    @field_validator("externalUrl")
    @classmethod
    def validate_url(cls, value):
        if not value:
            return value
        try:
            url = urlsplit(value)
            if (url.scheme.lower() not in {"http", "https"} or not url.hostname
                    or url.username or url.password or "\\" in value
                    or any(char.isspace() or ord(char) < 32 for char in value)):
                raise ValueError()
            _ = url.port
        except ValueError as error:
            raise ValueError("链接仅支持有效的 HTTP/HTTPS 地址") from error
        return value


def serialize_resource(row):
    return {
        "id": row["id"], "displayNumber": str(row["id"]).zfill(3),
        "title": row["title"], "description": row["description"], "reason": row["reason"],
        "domain": row["domain"], "type": row["resource_type"], "tags": json.loads(row["tags"]),
        "externalUrl": row["external_url"], "imageUrl": row["image_path"], "createdAt": row["created_at"],
    }


def get_resource(connection, resource_id):
    row = connection.execute("SELECT * FROM exchange_resources WHERE id=?", (resource_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "分享不存在或已删除")
    return row


def controlled_image_path(image_url):
    if not re.fullmatch(r"/uploads/exchange/[a-f0-9]{32}\.webp", image_url):
        return None
    root = UPLOAD_ROOT.resolve()
    directory = root / "exchange"
    candidate = directory / image_url.rsplit("/", 1)[-1]
    if directory.is_symlink() or candidate.is_symlink() or candidate.resolve().parent != directory.resolve():
        return None
    return candidate


@router.get("", dependencies=[Depends(require_exchange_enabled)])
def list_public_resources(limit: int = Query(200, ge=1, le=200), beforeId: int | None = Query(None, ge=1, le=9_223_372_036_854_775_807)):
    connection = None
    try:
        connection = get_db_connection()
        rows = connection.execute(
            "SELECT * FROM exchange_resources WHERE (? IS NULL OR id < ?) ORDER BY id DESC LIMIT ?",
            (beforeId, beforeId, limit),
        ).fetchall()
        return [serialize_resource(row) for row in rows]
    except sqlite3.Error as error:
        logger.exception("Exchange read failed")
        raise HTTPException(500, "读取分享失败，请稍后重试") from error
    finally:
        if connection is not None:
            connection.close()


@router.post("", status_code=201, dependencies=[Depends(require_exchange_enabled)])
def create_resource(payload: str = Form(...), file: UploadFile | None = File(None)):
    try:
        try:
            data = ExchangeCreate.model_validate_json(payload)
        except ValidationError as error:
            raise HTTPException(422, "内容校验失败：" + "; ".join(item["msg"] for item in error.errors())) from error
        encoded = None if file is None else validate_and_encode_image(
            file.file.read(MAX_IMAGE_SIZE + 1), file.content_type or "",
        )
    finally:
        if file is not None:
            file.file.close()
    connection, new_file = None, None
    try:
        connection = get_db_connection()
        connection.execute("BEGIN IMMEDIATE")
        image_url = ""
        if encoded is not None:
            directory = UPLOAD_ROOT / "exchange"
            directory.mkdir(parents=True, exist_ok=True)
            image_url = f"/uploads/exchange/{uuid4().hex}.webp"
            candidate = controlled_image_path(image_url)
            if candidate is None:
                raise OSError("Unsafe exchange image directory")
            with candidate.open("xb") as destination:
                new_file = candidate
                destination.write(encoded)
        created_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        cursor = connection.execute(
            "INSERT INTO exchange_resources (title,description,reason,domain,resource_type,tags,external_url,image_path,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (data.title, data.description, data.reason, data.domain, data.type,
             json.dumps(data.tags, ensure_ascii=False), data.externalUrl, image_url, created_at),
        )
        resource = serialize_resource(get_resource(connection, cursor.lastrowid))
        connection.commit()
        return resource
    except Exception as error:
        if connection is not None:
            connection.rollback()
        if new_file is not None:
            try:
                new_file.unlink(missing_ok=True)
            except OSError:
                logger.exception("Exchange uncommitted image cleanup failed")
        if isinstance(error, (OSError, sqlite3.Error)):
            logger.exception("Exchange save failed")
            raise HTTPException(500, "服务器保存失败，请稍后重试") from error
        raise
    finally:
        if connection is not None:
            connection.close()


@admin_router.get("")
def list_admin_resources(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=1_000_000)):
    connection = get_db_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM exchange_resources ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?", (limit, offset),
        ).fetchall()
        total = connection.execute("SELECT COUNT(*) FROM exchange_resources").fetchone()[0]
        return {"items": [serialize_resource(row) for row in rows], "total": total}
    except sqlite3.Error as error:
        raise HTTPException(500, "读取管理列表失败") from error
    finally:
        connection.close()


@admin_router.get("/{resource_id}")
def admin_resource_detail(resource_id: int = Path(ge=1, le=9_223_372_036_854_775_807)):
    connection = get_db_connection()
    try:
        return serialize_resource(get_resource(connection, resource_id))
    finally:
        connection.close()


@admin_router.delete("/{resource_id}")
def delete_resource(resource_id: int = Path(ge=1, le=9_223_372_036_854_775_807)):
    connection = get_db_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = get_resource(connection, resource_id)
        connection.execute("DELETE FROM exchange_resources WHERE id=?", (resource_id,))
        connection.commit()
    except Exception as error:
        connection.rollback()
        logger.warning("Exchange delete id=%s result=failed", resource_id)
        if isinstance(error, sqlite3.Error):
            raise HTTPException(500, "删除失败，分享保持不变") from error
        raise
    finally:
        connection.close()
    # Never remove media until the database deletion has actually committed.
    pending = False
    candidate = controlled_image_path(row["image_path"])
    if row["image_path"] and candidate is None:
        pending = True
        logger.warning("Exchange image path rejected during cleanup id=%s", resource_id)
    if candidate is not None:
        try:
            candidate.unlink(missing_ok=True)
        except OSError:
            pending = True
            logger.exception("Exchange image cleanup failed id=%s", resource_id)
    logger.info("Exchange delete id=%s at=%s result=%s", resource_id,
                datetime.now(timezone.utc).isoformat(), "deleted_cleanup_pending" if pending else "deleted")
    return {"id": resource_id, "message": "分享已删除", "imageCleanupPending": pending}
