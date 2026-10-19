from typing import Literal
import json
import logging
import sqlite3
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status as http_status
from pydantic import BaseModel, Field, ValidationError, field_validator

from auth_api import get_current_admin
from database import get_db_connection
from image_processing import validate_and_encode_image
from upload_api import MAX_IMAGE_SIZE, UPLOAD_ROOT

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/tools",
    tags=["工具"],
)

admin_router = APIRouter(
    prefix="/api/admin/tools",
    dependencies=[Depends(get_current_admin)],
    tags=["工具管理"],
)


class ToolCreate(BaseModel):
    icon: str = Field(default="", max_length=50)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    status: Literal["available", "integrating", "developing"] = "developing"
    actionType: Literal["none", "route", "static", "external"] = "none"
    actionTarget: str = Field(default="", max_length=1000)
    buttonText: str = Field(default="", max_length=100)
    sortOrder: int = Field(default=0, ge=0)
    isActive: int = Field(default=1, ge=0, le=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        title = value.strip()

        if not title:
            raise ValueError("title 不能为空")

        return title

    @field_validator("icon", "actionTarget", "buttonText")
    @classmethod
    def normalize_text(cls, value):
        return value.strip()


class ToolResponse(ToolCreate):
    id: int
    createdAt: str
    coverImageUrl: str = ""


class ActiveUpdate(BaseModel):
    isActive: int = Field(ge=0, le=1)


class ActiveResponse(BaseModel):
    id: int
    isActive: int


class ToolDeleteResponse(BaseModel):
    message: str
    id: int


TOOL_SELECT = """
    SELECT
        id,
        icon,
        cover_image_url,
        title,
        description,
        status,
        action_type,
        action_target,
        button_text,
        sort_order,
        is_active,
        created_at
    FROM tools
"""


def _serialize_tool(row):
    return {
        "id": row["id"],
        "icon": row["icon"],
        "coverImageUrl": row["cover_image_url"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "actionType": row["action_type"],
        "actionTarget": row["action_target"],
        "buttonText": row["button_text"],
        "sortOrder": row["sort_order"],
        "isActive": row["is_active"],
        "createdAt": row["created_at"],
    }


def _get_tool_row(connection, tool_id):
    return connection.execute(
        f"{TOOL_SELECT} WHERE id = ?",
        (tool_id,),
    ).fetchone()


class ToolEditor(ToolCreate):
    removeImage: bool = False


def _save_tool_editor(tool_id: int | None, payload: str, file: UploadFile | None):
    """Commit fields and the new image reference together; never overwrite old files."""
    try:
        try:
            tool = ToolEditor.model_validate_json(payload)
        except ValidationError as error:
            raise HTTPException(422, json.loads(error.json())) from error
        if file is not None and tool.removeImage:
            raise HTTPException(422, "不能同时上传和清除图片")
        encoded = None if file is None else validate_and_encode_image(
            file.file.read(MAX_IMAGE_SIZE + 1), file.content_type or ""
        )
    finally:
        if file is not None:
            file.file.close()

    connection = get_db_connection()
    new_file = None
    try:
        # Serialize the existing-row read with the update, including image preservation.
        connection.execute("BEGIN IMMEDIATE")
        existing = None if tool_id is None else _get_tool_row(connection, tool_id)
        if tool_id is not None and existing is None:
            raise HTTPException(404, "Tool not found")
        icon = tool.icon if "icon" in tool.model_fields_set else (existing["icon"] if existing else "")
        values = (icon, tool.title, tool.description, tool.status, tool.actionType,
                  tool.actionTarget, tool.buttonText, tool.sortOrder, tool.isActive)
        if tool_id is None:
            cursor = connection.execute(
                "INSERT INTO tools (icon, title, description, status, action_type, "
                "action_target, button_text, sort_order, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                values,
            )
            tool_id = cursor.lastrowid
        else:
            connection.execute(
                "UPDATE tools SET icon=?, title=?, description=?, status=?, action_type=?, "
                "action_target=?, button_text=?, sort_order=?, is_active=? WHERE id=?",
                (*values, tool_id),
            )
        image_url = existing["cover_image_url"] if existing else ""
        if encoded is not None:
            directory = UPLOAD_ROOT / "tools"
            directory.mkdir(parents=True, exist_ok=True)
            filename = f"{uuid4().hex}.webp"
            candidate = directory / filename
            with candidate.open("xb") as destination:
                new_file = candidate
                destination.write(encoded)
            image_url = f"/uploads/tools/{filename}"
        elif tool.removeImage:
            image_url = ""
        connection.execute("UPDATE tools SET cover_image_url=? WHERE id=?", (image_url, tool_id))
        result = _serialize_tool(_get_tool_row(connection, tool_id))
        connection.commit()
        return result
    except Exception as error:
        connection.rollback()
        if new_file is not None:
            try:
                new_file.unlink(missing_ok=True)
            except OSError:
                logger.exception("Could not remove uncommitted tool cover")
        if isinstance(error, (OSError, sqlite3.Error)):
            logger.exception("Failed to save tool editor")
            raise HTTPException(500, "保存失败，原工具和图片保持不变，请重试") from error
        raise
    finally:
        connection.close()


@admin_router.post("", response_model=ToolResponse, status_code=http_status.HTTP_201_CREATED)
def create_tool_editor(payload: str = Form(...), file: UploadFile | None = File(None)):
    return _save_tool_editor(None, payload, file)


@admin_router.put("/{tool_id}", response_model=ToolResponse)
def update_tool_editor(tool_id: int, payload: str = Form(...), file: UploadFile | None = File(None)):
    return _save_tool_editor(tool_id, payload, file)


@admin_router.get("", response_model=list[ToolResponse])
def get_all_tools():
    connection = get_db_connection()

    try:
        rows = connection.execute(
            f"{TOOL_SELECT} ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    finally:
        connection.close()

    return [_serialize_tool(row) for row in rows]


@router.get("", response_model=list[ToolResponse])
def get_active_tools():
    connection = get_db_connection()

    try:
        rows = connection.execute(
            f"{TOOL_SELECT} WHERE is_active = 1 "
            "ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    finally:
        connection.close()

    return [_serialize_tool(row) for row in rows]


@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool_by_id(tool_id: int):
    connection = get_db_connection()

    try:
        row = _get_tool_row(connection, tool_id)
    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )

    return _serialize_tool(row)


@router.post(
    "",
    response_model=ToolResponse,
    status_code=http_status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
def create_tool(tool: ToolCreate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO tools (
                icon,
                title,
                description,
                status,
                action_type,
                action_target,
                button_text,
                sort_order,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tool.icon,
                tool.title,
                tool.description,
                tool.status,
                tool.actionType,
                tool.actionTarget,
                tool.buttonText,
                tool.sortOrder,
                tool.isActive,
            ),
        )
        tool_id = cursor.lastrowid
        connection.commit()
        row = _get_tool_row(connection, tool_id)

        return _serialize_tool(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@router.put("/{tool_id}", response_model=ToolResponse, dependencies=[Depends(get_current_admin)])
def update_tool(tool_id: int, tool: ToolCreate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE tools
            SET
                icon = ?,
                title = ?,
                description = ?,
                status = ?,
                action_type = ?,
                action_target = ?,
                button_text = ?,
                sort_order = ?,
                is_active = ?
            WHERE id = ?
            """,
            (
                tool.icon,
                tool.title,
                tool.description,
                tool.status,
                tool.actionType,
                tool.actionTarget,
                tool.buttonText,
                tool.sortOrder,
                tool.isActive,
                tool_id,
            ),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Tool not found",
            )

        connection.commit()
        row = _get_tool_row(connection, tool_id)

        return _serialize_tool(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@router.patch("/{tool_id}/active", response_model=ActiveResponse, dependencies=[Depends(get_current_admin)])
def update_tool_active_status(tool_id: int, update: ActiveUpdate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "UPDATE tools SET is_active = ? WHERE id = ?",
            (update.isActive, tool_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Tool not found",
            )

        connection.commit()
        return {"id": tool_id, "isActive": update.isActive}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@router.delete("/{tool_id}", response_model=ToolDeleteResponse, dependencies=[Depends(get_current_admin)])
def delete_tool(tool_id: int):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM tools WHERE id = ?",
            (tool_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Tool not found",
            )

        connection.commit()
        return {"message": "Tool deleted", "id": tool_id}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
