from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from auth_api import get_current_admin
from database import get_db_connection


banner_router = APIRouter(
    prefix="/api/banners",
    tags=["Banner"],
)

banner_admin_router = APIRouter(
    prefix="/api/admin/banners",
    dependencies=[Depends(get_current_admin)],
    tags=["Banner 管理"],
)

announcement_router = APIRouter(
    prefix="/api/announcements",
    tags=["平台公告"],
)

announcement_admin_router = APIRouter(
    prefix="/api/admin/announcements",
    dependencies=[Depends(get_current_admin)],
    tags=["平台公告管理"],
)


class BannerAction(BaseModel):
    type: Literal["none", "route", "external", "dify"] = "none"
    target: str = Field(default="", max_length=1000)

    @field_validator("target")
    @classmethod
    def normalize_target(cls, value):
        return value.strip()


class BannerCreate(BaseModel):
    category: str = Field(default="", max_length=50)
    date: str = Field(default="", max_length=20)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    buttonText: str = Field(default="", max_length=100)
    image: str = Field(default="", max_length=1000)
    action: BannerAction = Field(default_factory=BannerAction)
    sortOrder: int = Field(default=0, ge=0)
    isActive: int = Field(default=1, ge=0, le=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        title = value.strip()

        if not title:
            raise ValueError("title 不能为空")

        return title

    @field_validator("category", "date", "description", "buttonText", "image")
    @classmethod
    def normalize_text(cls, value):
        return value.strip()


class BannerResponse(BannerCreate):
    id: int
    createdAt: str


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=1000)
    date: str = Field(default="", max_length=20)
    sortOrder: int = Field(default=0, ge=0)
    isActive: int = Field(default=1, ge=0, le=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        title = value.strip()

        if not title:
            raise ValueError("title 不能为空")

        return title

    @field_validator("summary", "date")
    @classmethod
    def normalize_text(cls, value):
        return value.strip()


class AnnouncementResponse(AnnouncementCreate):
    id: int
    createdAt: str


class ActiveUpdate(BaseModel):
    isActive: int = Field(ge=0, le=1)


class ActiveResponse(BaseModel):
    id: int
    isActive: int


class ContentDeleteResponse(BaseModel):
    message: str
    id: int


BANNER_SELECT = """
    SELECT
        id,
        category,
        publish_date,
        title,
        description,
        button_text,
        image,
        action_type,
        action_target,
        sort_order,
        is_active,
        created_at
    FROM banners
"""

ANNOUNCEMENT_SELECT = """
    SELECT
        id,
        title,
        summary,
        publish_date,
        sort_order,
        is_active,
        created_at
    FROM announcements
"""


def _serialize_banner(row):
    return {
        "id": row["id"],
        "category": row["category"],
        "date": row["publish_date"],
        "title": row["title"],
        "description": row["description"],
        "buttonText": row["button_text"],
        "image": row["image"],
        "action": {
            "type": row["action_type"],
            "target": row["action_target"],
        },
        "sortOrder": row["sort_order"],
        "isActive": row["is_active"],
        "createdAt": row["created_at"],
    }


def _serialize_announcement(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "summary": row["summary"],
        "date": row["publish_date"],
        "sortOrder": row["sort_order"],
        "isActive": row["is_active"],
        "createdAt": row["created_at"],
    }


def _get_banner_row(connection, banner_id):
    return connection.execute(
        f"{BANNER_SELECT} WHERE id = ?",
        (banner_id,),
    ).fetchone()


def _get_announcement_row(connection, announcement_id):
    return connection.execute(
        f"{ANNOUNCEMENT_SELECT} WHERE id = ?",
        (announcement_id,),
    ).fetchone()


@banner_admin_router.get("", response_model=list[BannerResponse])
def get_all_banners():
    connection = get_db_connection()

    try:
        rows = connection.execute(
            f"{BANNER_SELECT} ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    finally:
        connection.close()

    return [_serialize_banner(row) for row in rows]


@banner_router.get("", response_model=list[BannerResponse])
def get_active_banners():
    connection = get_db_connection()

    try:
        rows = connection.execute(
            f"{BANNER_SELECT} WHERE is_active = 1 ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    finally:
        connection.close()

    return [_serialize_banner(row) for row in rows]


@banner_router.get("/{banner_id}", response_model=BannerResponse)
def get_banner_by_id(banner_id: int):
    connection = get_db_connection()

    try:
        row = _get_banner_row(connection, banner_id)
    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found",
        )

    return _serialize_banner(row)


@banner_router.post(
    "",
    response_model=BannerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
def create_banner(banner: BannerCreate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO banners (
                category,
                publish_date,
                title,
                description,
                button_text,
                image,
                action_type,
                action_target,
                sort_order,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                banner.category,
                banner.date,
                banner.title,
                banner.description,
                banner.buttonText,
                banner.image,
                banner.action.type,
                banner.action.target,
                banner.sortOrder,
                banner.isActive,
            ),
        )
        banner_id = cursor.lastrowid
        connection.commit()
        row = _get_banner_row(connection, banner_id)

        return _serialize_banner(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@banner_router.put("/{banner_id}", response_model=BannerResponse, dependencies=[Depends(get_current_admin)])
def update_banner(banner_id: int, banner: BannerCreate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE banners
            SET
                category = ?,
                publish_date = ?,
                title = ?,
                description = ?,
                button_text = ?,
                image = ?,
                action_type = ?,
                action_target = ?,
                sort_order = ?,
                is_active = ?
            WHERE id = ?
            """,
            (
                banner.category,
                banner.date,
                banner.title,
                banner.description,
                banner.buttonText,
                banner.image,
                banner.action.type,
                banner.action.target,
                banner.sortOrder,
                banner.isActive,
                banner_id,
            ),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found",
            )

        connection.commit()
        row = _get_banner_row(connection, banner_id)

        return _serialize_banner(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@banner_router.patch("/{banner_id}/active", response_model=ActiveResponse, dependencies=[Depends(get_current_admin)])
def update_banner_active_status(banner_id: int, update: ActiveUpdate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "UPDATE banners SET is_active = ? WHERE id = ?",
            (update.isActive, banner_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found",
            )

        connection.commit()
        return {"id": banner_id, "isActive": update.isActive}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@banner_router.delete("/{banner_id}", response_model=ContentDeleteResponse, dependencies=[Depends(get_current_admin)])
def delete_banner(banner_id: int):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM banners WHERE id = ?",
            (banner_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found",
            )

        connection.commit()
        return {"message": "Banner deleted", "id": banner_id}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@announcement_admin_router.get("", response_model=list[AnnouncementResponse])
def get_all_announcements():
    connection = get_db_connection()

    try:
        rows = connection.execute(
            f"{ANNOUNCEMENT_SELECT} ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    finally:
        connection.close()

    return [_serialize_announcement(row) for row in rows]


@announcement_router.get("", response_model=list[AnnouncementResponse])
def get_active_announcements():
    connection = get_db_connection()

    try:
        rows = connection.execute(
            f"{ANNOUNCEMENT_SELECT} WHERE is_active = 1 ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    finally:
        connection.close()

    return [_serialize_announcement(row) for row in rows]


@announcement_router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement_by_id(announcement_id: int):
    connection = get_db_connection()

    try:
        row = _get_announcement_row(connection, announcement_id)
    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )

    return _serialize_announcement(row)


@announcement_router.post(
    "",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
def create_announcement(announcement: AnnouncementCreate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO announcements (
                title,
                summary,
                publish_date,
                sort_order,
                is_active
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                announcement.title,
                announcement.summary,
                announcement.date,
                announcement.sortOrder,
                announcement.isActive,
            ),
        )
        announcement_id = cursor.lastrowid
        connection.commit()
        row = _get_announcement_row(connection, announcement_id)

        return _serialize_announcement(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@announcement_router.put("/{announcement_id}", response_model=AnnouncementResponse, dependencies=[Depends(get_current_admin)])
def update_announcement(announcement_id: int, announcement: AnnouncementCreate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE announcements
            SET
                title = ?,
                summary = ?,
                publish_date = ?,
                sort_order = ?,
                is_active = ?
            WHERE id = ?
            """,
            (
                announcement.title,
                announcement.summary,
                announcement.date,
                announcement.sortOrder,
                announcement.isActive,
                announcement_id,
            ),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found",
            )

        connection.commit()
        row = _get_announcement_row(connection, announcement_id)

        return _serialize_announcement(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@announcement_router.patch("/{announcement_id}/active", response_model=ActiveResponse, dependencies=[Depends(get_current_admin)])
def update_announcement_active_status(announcement_id: int, update: ActiveUpdate):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "UPDATE announcements SET is_active = ? WHERE id = ?",
            (update.isActive, announcement_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found",
            )

        connection.commit()
        return {"id": announcement_id, "isActive": update.isActive}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@announcement_router.delete(
    "/{announcement_id}",
    response_model=ContentDeleteResponse,
    dependencies=[Depends(get_current_admin)],
)
def delete_announcement(announcement_id: int):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM announcements WHERE id = ?",
            (announcement_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found",
            )

        connection.commit()
        return {"message": "Announcement deleted", "id": announcement_id}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
