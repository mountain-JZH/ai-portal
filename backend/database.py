import sqlite3
import os
from pathlib import Path

from auth_security import hash_password
from dotenv import load_dotenv
from project_data import init_project_tables


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
                banner_type TEXT NOT NULL DEFAULT 'standard',
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        banner_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(banners)")
        }
        if "banner_type" not in banner_columns:
            connection.execute(
                "ALTER TABLE banners ADD COLUMN banner_type TEXT NOT NULL DEFAULT 'standard'"
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
                cover_image_url TEXT NOT NULL DEFAULT '',
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

        tool_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(tools)")
        }
        if "cover_image_url" not in tool_columns:
            connection.execute(
                "ALTER TABLE tools ADD COLUMN cover_image_url TEXT NOT NULL DEFAULT ''"
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS section_visuals (
                section_key TEXT PRIMARY KEY NOT NULL
                    CHECK (section_key IN ('home_news', 'home_tools')),
                image_path TEXT NOT NULL,
                text_mode TEXT NOT NULL DEFAULT 'dark'
                    CHECK (text_mode IN ('dark', 'light')),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        section_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(section_visuals)")
        }
        if "text_mode" not in section_columns:
            connection.execute(
                "ALTER TABLE section_visuals ADD COLUMN text_mode TEXT NOT NULL "
                "DEFAULT 'dark' CHECK (text_mode IN ('dark', 'light'))"
            )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS exchange_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                domain TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                external_url TEXT NOT NULL DEFAULT '',
                image_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )

        connection.executescript("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
                can_edit_projects INTEGER NOT NULL DEFAULT 0 CHECK(can_edit_projects IN (0,1)),
                must_change_password INTEGER NOT NULL DEFAULT 1 CHECK(must_change_password IN (0,1)),
                auth_version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                last_login_at TEXT
            );
            CREATE TABLE IF NOT EXISTS employee_sessions (
                token_hash TEXT PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                auth_version INTEGER NOT NULL,
                expires_at REAL NOT NULL,
                admin_id INTEGER REFERENCES admins(id),
                admin_expires_at REAL
            );
            CREATE INDEX IF NOT EXISTS employee_sessions_employee ON employee_sessions(employee_id);
            CREATE TABLE IF NOT EXISTS auth_login_attempts (
                bucket TEXT PRIMARY KEY,
                window_start INTEGER NOT NULL,
                attempts INTEGER NOT NULL
            );
        """)

        init_project_tables(connection)

        # Preserve both identity tables and IDs; never infer admin status from a username.
        employee_columns = {row['name'] for row in connection.execute('PRAGMA table_info(employees)')}
        if 'admin_id' not in employee_columns:
            connection.execute('ALTER TABLE employees ADD COLUMN admin_id INTEGER REFERENCES admins(id)')
        connection.execute('CREATE UNIQUE INDEX IF NOT EXISTS employee_admin_identity ON employees(admin_id) WHERE admin_id IS NOT NULL')

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
