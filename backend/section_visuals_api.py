"""Two fixed homepage mastheads; independent of the Banner carousel."""

import logging
import sqlite3
from uuid import uuid4
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict

from image_processing import validate_and_encode_image
from auth_api import get_current_admin
from database import get_db_connection
from upload_api import MAX_IMAGE_SIZE, UPLOAD_ROOT


router = APIRouter(prefix="/api/section-visuals", tags=["Section visuals"])
admin_router = APIRouter(
    prefix="/api/admin/section-visuals",
    tags=["Section visuals administration"],
    dependencies=[Depends(get_current_admin)],
)
SECTION_TITLES = {"home_news": "最新动态", "home_tools": "AI 与常用工具"}
logger = logging.getLogger(__name__)


def read_section_visuals():
    connection = get_db_connection()
    try:
        rows = {
            row["section_key"]: dict(row)
            for row in connection.execute("SELECT * FROM section_visuals")
        }
    finally:
        connection.close()

    return [
        {
            "sectionKey": key,
            "title": title,
            "image": rows.get(key, {}).get("image_path", ""),
            "textMode": rows.get(key, {}).get("text_mode", "dark"),
            "updatedAt": rows.get(key, {}).get("updated_at"),
        }
        for key, title in SECTION_TITLES.items()
    ]


@router.get("")
def get_public_section_visuals():
    return read_section_visuals()


@admin_router.get("")
def get_admin_section_visuals():
    return read_section_visuals()


@admin_router.put("/{section_key}")
def save_section_visual(
    section_key: str, file: UploadFile = File(...),
    textMode: Literal["dark", "light"] | None = Form(None),
):
    try:
        if section_key not in SECTION_TITLES:
            raise HTTPException(400, "无效的栏目，只允许 home_news 或 home_tools")
        content = file.file.read(MAX_IMAGE_SIZE + 1)
        encoded = validate_and_encode_image(content, file.content_type or "")
    finally:
        file.file.close()

    filename = f"{uuid4().hex}.webp"
    directory = UPLOAD_ROOT / "sections"
    image_path = f"/uploads/sections/{filename}"
    connection = get_db_connection()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        # Exclusive creation: never overwrite an existing file, including old images.
        with (directory / filename).open("xb") as destination:
            destination.write(encoded)
        connection.execute(
            """
            INSERT INTO section_visuals (section_key, image_path, text_mode, updated_at)
            VALUES (?, ?, COALESCE(?, 'dark'), strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            ON CONFLICT(section_key) DO UPDATE SET
                image_path = excluded.image_path,
                text_mode = COALESCE(?, section_visuals.text_mode),
                updated_at = excluded.updated_at
            """,
            (section_key, image_path, textMode, textMode),
        )
        updated = connection.execute(
            "SELECT updated_at, text_mode FROM section_visuals WHERE section_key = ?", (section_key,)
        ).fetchone()
        connection.commit()
    except (OSError, sqlite3.Error) as error:
        connection.rollback()
        # Do not garbage-collect uploads here: old effective images must remain intact.
        logger.exception("Failed to save section visual")
        raise HTTPException(500, "保存失败，原背景保持不变，请重试") from error
    finally:
        connection.close()

    return {
        "sectionKey": section_key,
        "title": SECTION_TITLES[section_key],
        "image": image_path,
        "updatedAt": updated["updated_at"],
        "textMode": updated["text_mode"],
    }


class SectionTextUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    textMode: Literal["dark", "light"]


@admin_router.patch("/{section_key}")
def update_section_text(section_key: str, payload: SectionTextUpdate):
    if section_key not in SECTION_TITLES:
        raise HTTPException(400, "无效的栏目，只允许 home_news 或 home_tools")
    connection = get_db_connection()
    try:
        connection.execute(
            """
            INSERT INTO section_visuals (section_key, image_path, text_mode, updated_at)
            VALUES (?, '', ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            ON CONFLICT(section_key) DO UPDATE SET
                text_mode = excluded.text_mode, updated_at = excluded.updated_at
            """,
            (section_key, payload.textMode),
        )
        row = connection.execute(
            "SELECT * FROM section_visuals WHERE section_key = ?", (section_key,)
        ).fetchone()
        connection.commit()
    except sqlite3.Error as error:
        connection.rollback()
        logger.exception("Failed to update section text mode")
        raise HTTPException(500, "保存失败，原文字颜色保持不变，请重试") from error
    finally:
        connection.close()
    return {
        "sectionKey": section_key, "title": SECTION_TITLES[section_key],
        "image": row["image_path"], "textMode": row["text_mode"],
        "updatedAt": row["updated_at"],
    }
