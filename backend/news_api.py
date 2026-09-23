from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from auth_api import get_current_admin
from database import get_db_connection


router = APIRouter(
    prefix="/api/news",
    tags=["新闻"]
)

admin_router = APIRouter(
    prefix="/api/admin/news",
    dependencies=[Depends(get_current_admin)],
    tags=["新闻管理"],
)


class NewsCreate(BaseModel):
    title: str = Field(min_length=1)
    summary: str = ""
    content: str = ""
    source: str = ""
    source_type: str = ""
    publish_date: str = ""
    keywords: str = ""
    url: str = ""
    is_published: int = Field(default=1, ge=0, le=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        title = value.strip()

        if not title:
            raise ValueError("title 不能为空")

        return title


class NewsResponse(NewsCreate):
    id: int
    created_at: str


class NewsDeleteResponse(BaseModel):
    message: str
    id: int


class NewsPublishUpdate(BaseModel):
    is_published: int = Field(ge=0, le=1)


class NewsPublishResponse(BaseModel):
    id: int
    is_published: int


@admin_router.get("", response_model=list[NewsResponse])
def get_all_news():
    """
    获取全部新闻，供新闻管理页面使用。
    """

    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                title,
                summary,
                content,
                source,
                source_type,
                publish_date,
                keywords,
                url,
                is_published,
                created_at
            FROM news
            ORDER BY publish_date DESC, id DESC
            """
        ).fetchall()
    finally:
        connection.close()

    return [dict(row) for row in rows]


@router.get("")
def get_news():
    """
    获取所有已发布新闻。
    """

    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            title,
            summary,
            content,
            source,
            source_type,
            publish_date,
            keywords,
            url,
            created_at
        FROM news
        WHERE is_published = 1
        ORDER BY publish_date DESC, id DESC
        """
    ).fetchall()

    connection.close()

    news_list = []

    for row in rows:
        news_list.append(dict(row))

    return news_list


@router.get("/{news_id}", response_model=NewsResponse)
def get_news_by_id(news_id: int):
    """
    根据新闻 id 获取单条新闻。
    """

    connection = get_db_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                title,
                summary,
                content,
                source,
                source_type,
                publish_date,
                keywords,
                url,
                is_published,
                created_at
            FROM news
            WHERE id = ?
            """,
            (news_id,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found",
        )

    return dict(row)


@router.put("/{news_id}", response_model=NewsResponse, dependencies=[Depends(get_current_admin)])
def update_news(news_id: int, news: NewsCreate):
    """
    更新指定 id 的新闻，并返回更新后的完整新闻对象。
    """

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE news
            SET
                title = ?,
                summary = ?,
                content = ?,
                source = ?,
                source_type = ?,
                publish_date = ?,
                keywords = ?,
                url = ?,
                is_published = ?
            WHERE id = ?
            """,
            (
                news.title,
                news.summary,
                news.content,
                news.source,
                news.source_type,
                news.publish_date,
                news.keywords,
                news.url,
                news.is_published,
                news_id,
            ),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News not found",
            )

        connection.commit()

        row = connection.execute(
            """
            SELECT
                id,
                title,
                summary,
                content,
                source,
                source_type,
                publish_date,
                keywords,
                url,
                is_published,
                created_at
            FROM news
            WHERE id = ?
            """,
            (news_id,),
        ).fetchone()

        return dict(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@router.patch("/{news_id}/publish", response_model=NewsPublishResponse, dependencies=[Depends(get_current_admin)])
def update_news_publish_status(news_id: int, update: NewsPublishUpdate):
    """
    快捷更新指定新闻的发布状态。
    """

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE news
            SET is_published = ?
            WHERE id = ?
            """,
            (update.is_published, news_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News not found",
            )

        connection.commit()

        return {
            "id": news_id,
            "is_published": update.is_published,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@router.delete("/{news_id}", response_model=NewsDeleteResponse, dependencies=[Depends(get_current_admin)])
def delete_news(news_id: int):
    """
    删除指定 id 的新闻。
    """

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM news WHERE id = ?",
            (news_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News not found",
            )

        connection.commit()

        return {
            "message": "News deleted",
            "id": news_id,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@router.post(
    "",
    response_model=NewsResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
def create_news(news: NewsCreate):
    """
    新增一条新闻，并返回刚创建的完整新闻对象。
    """

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO news (
                title,
                summary,
                content,
                source,
                source_type,
                publish_date,
                keywords,
                url,
                is_published
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                news.title,
                news.summary,
                news.content,
                news.source,
                news.source_type,
                news.publish_date,
                news.keywords,
                news.url,
                news.is_published,
            ),
        )

        news_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT
                id,
                title,
                summary,
                content,
                source,
                source_type,
                publish_date,
                keywords,
                url,
                is_published,
                created_at
            FROM news
            WHERE id = ?
            """,
            (news_id,),
        ).fetchone()

        return dict(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
