import sqlite3
from pathlib import Path


# backend 文件夹路径
BASE_DIR = Path(__file__).resolve().parent

# SQLite 数据库文件路径
DATABASE_PATH = BASE_DIR / "ai_portal.db"


def get_db_connection():
    """
    创建数据库连接。
    """

    connection = sqlite3.connect(DATABASE_PATH)

    # 查询结果可以通过字段名访问
    connection.row_factory = sqlite3.Row

    return connection


def init_database():
    """
    初始化数据库。
    如果 news 表不存在，就创建它。
    """

    connection = get_db_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT DEFAULT '',
            content TEXT DEFAULT '',
            source TEXT DEFAULT '',
            source_type TEXT DEFAULT '',
            publish_date TEXT DEFAULT '',
            keywords TEXT DEFAULT '',
            url TEXT DEFAULT '',
            is_published INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def seed_news():
    """
    如果数据库中还没有新闻，
    自动写入 3 条演示数据。
    """

    connection = get_db_connection()

    result = connection.execute(
        "SELECT COUNT(*) AS count FROM news"
    ).fetchone()

    if result["count"] == 0:

        demo_news = [
            (
                "新能源充电基础设施持续完善",
                "充电基础设施建设持续推进，公共充电服务能力不断提升。",
                "随着新能源汽车保有量增长，充电基础设施建设持续推进。运营企业也在逐步提升设备运维、客服服务和数字化管理能力。",
                "演示数据",
                "行业资讯",
                "2026-09-12",
                "新能源,充电桩,数字化",
                "",
                1,
            ),
            (
                "信息运维数字化工具持续优化",
                "内部信息化工具逐步覆盖数据处理、知识查询等业务场景。",
                "通过轻量化工具和内部智能助手，可以减少重复性人工操作，提高信息处理效率和业务标准化水平。",
                "演示数据",
                "内部动态",
                "2026-09-11",
                "信息化,运维,AI",
                "",
                1,
            ),
            (
                "AI 技术加速企业知识管理应用",
                "企业知识库和智能问答正在成为 AI 落地的重要方向。",
                "通过知识库、RAG 和大模型能力，企业可以将分散的制度、操作手册和业务资料统一组织，并提供自然语言查询能力。",
                "演示数据",
                "AI资讯",
                "2026-09-10",
                "AI,RAG,知识库",
                "",
                1,
            ),
        ]

        connection.executemany(
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
            demo_news,
        )

        connection.commit()

        print("已写入 3 条演示新闻")

    else:
        print("数据库已有新闻，不重复写入演示数据")

    connection.close()


if __name__ == "__main__":

    init_database()

    seed_news()

    print("数据库初始化完成")
    print(f"数据库位置：{DATABASE_PATH}")