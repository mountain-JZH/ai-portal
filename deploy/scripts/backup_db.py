import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / "backend" / ".env")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create a consistent SQLite backup with the sqlite3 backup API."
    )
    parser.add_argument(
        "--backup-dir",
        help="Destination directory. Overrides the BACKUP_DIR environment variable.",
    )
    return parser.parse_args()


def resolve_paths(backup_dir_argument):
    database_value = os.getenv("DATABASE_PATH", "").strip()

    if not database_value:
        raise RuntimeError("DATABASE_PATH is not set")

    source_path = Path(database_value).expanduser()

    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / "backend" / source_path

    source_path = source_path.resolve()

    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite database does not exist: {source_path}")

    backup_value = backup_dir_argument or os.getenv("BACKUP_DIR", "").strip()

    if not backup_value:
        raise RuntimeError("Set BACKUP_DIR or pass --backup-dir")

    backup_directory = Path(backup_value).expanduser().resolve()
    backup_directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination_path = backup_directory / f"ai_portal_{timestamp}.db"

    if destination_path == source_path:
        raise RuntimeError("Backup destination must differ from the source database")

    return source_path, destination_path


def create_backup(source_path, destination_path):
    source_connection = sqlite3.connect(source_path)
    destination_connection = sqlite3.connect(destination_path)

    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()


def main():
    arguments = parse_arguments()

    try:
        source_path, destination_path = resolve_paths(arguments.backup_dir)
        create_backup(source_path, destination_path)
    except (FileNotFoundError, RuntimeError, sqlite3.Error) as error:
        raise SystemExit(f"Backup failed: {error}") from error

    print(f"Backup created: {destination_path}")


if __name__ == "__main__":
    main()
