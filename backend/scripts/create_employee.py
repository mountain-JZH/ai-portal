"""Local-only employee bootstrap. Passwords are read interactively, never as arguments."""

import argparse
from contextlib import closing
from getpass import getpass
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auth_security import hash_password
from database import DATABASE_PATH, get_db_connection, init_database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--department", required=True)
    parser.add_argument("--allow-additional", action="store_true", help="Explicit local recovery if employees already exist")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{2,63}", args.username):
        parser.error("账号需为 3–64 位英文、数字、点、下划线或短横线")
    if not 1 <= len(args.name.strip()) <= 80 or not 1 <= len(args.department.strip()) <= 100:
        parser.error("请填写有效姓名和部门")
    print(f"将操作数据库：{DATABASE_PATH}；不会修改现有管理员。")
    if input("确认创建员工账号，请输入 CREATE：") != "CREATE":
        raise SystemExit("已取消")
    password = getpass("初始密码（12–128 位，输入不回显）：")
    if not 12 <= len(password) <= 128 or getpass("再次输入：") != password:
        raise SystemExit("密码长度不合规或两次输入不同")
    encoded = hash_password(password)
    del password
    init_database()
    with closing(get_db_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0] and not args.allow_additional:
            raise SystemExit("已有员工，请通过后台创建；本地恢复需明确 --allow-additional")
        if connection.execute("SELECT 1 FROM employees WHERE username=?", (args.username,)).fetchone():
            raise SystemExit("该员工账号已存在，未覆盖")
        if connection.execute('SELECT 1 FROM admins WHERE lower(username)=?', (args.username.lower(),)).fetchone():
            raise SystemExit('账号属于现有管理员，请使用统一登录或管理员密码设置工具')
        connection.execute("INSERT INTO employees(username,name,department,password_hash,must_change_password) VALUES(?,?,?,?,0)",
                           (args.username.lower(), args.name.strip(), args.department.strip(), encoded))
    print("员工已创建；请安全交付密码，统一登录后自动识别权限，可在平台主动修改密码。")


if __name__ == "__main__":
    main()
