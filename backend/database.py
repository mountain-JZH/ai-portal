import sqlite3
import os
from pathlib import Path

from auth_security import hash_password
from dotenv import load_dotenv


# backend 文件夹路径
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _resolve_database_path():
    configured_path = os.getenv("DATABASE_PATH", "").strip()

    if not configured_path:
        return BASE_DIR / "ai_portal.db"

    database_path = Path(configured_path).expanduser()

    if not database_path.is_absolute():
        database_path = BASE_DIR / database_path

    return database_path.resolve()


# 默认使用 backend/ai_portal.db，生产环境可通过 DATABASE_PATH 覆盖。
DATABASE_PATH = _resolve_database_path()


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
    在现有数据库中补齐项目所需的数据表。
    """

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = get_db_connection()

    try:
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS banners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT DEFAULT '',
                publish_date TEXT DEFAULT '',
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                button_text TEXT DEFAULT '',
                image TEXT DEFAULT '',
                action_type TEXT DEFAULT 'none',
                action_target TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                publish_date TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                icon TEXT DEFAULT '',
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'developing',
                action_type TEXT DEFAULT 'none',
                action_target TEXT DEFAULT '',
                button_text TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        admin_count = connection.execute(
            "SELECT COUNT(*) FROM admins"
        ).fetchone()[0]
        admin_username = os.getenv("ADMIN_USERNAME", "").strip()
        admin_password = os.getenv("ADMIN_PASSWORD", "")

        if admin_count == 0 and admin_username and admin_password:
            connection.execute(
                """
                INSERT INTO admins (username, password_hash)
                VALUES (?, ?)
                """,
                (admin_username, hash_password(admin_password)),
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":

    init_database()

    print("数据库初始化完成")
    print(f"数据库位置：{DATABASE_PATH}")
