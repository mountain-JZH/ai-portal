from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator

from database import get_db_connection


router = APIRouter(
    prefix="/api/news",
    tags=["新闻"]
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


@router.post(
    "",
    response_model=NewsResponse,
    status_code=status.HTTP_201_CREATED,
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
