"""Explicit local admin setup/recovery. No main import, defaults, plaintext arguments or logging."""
import argparse
from getpass import getpass
from pathlib import Path
import re
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auth_security import hash_password


def set_password(connection, username, encoded):
    """Caller owns the transaction; preserve existing accounts and immutable identity IDs."""
    columns = {r['name'] for r in connection.execute('PRAGMA table_info(employees)')}
    if not columns:
        raise ValueError('该数据库尚无员工表，请先在副本验证新版初始化；本工具不会重建数据库')
    if 'admin_id' not in columns:
        connection.execute('ALTER TABLE employees ADD COLUMN admin_id INTEGER REFERENCES admins(id)')
    connection.execute('CREATE UNIQUE INDEX IF NOT EXISTS employee_admin_identity ON employees(admin_id) WHERE admin_id IS NOT NULL')
    admins = connection.execute('SELECT * FROM admins WHERE lower(username)=?', (username.lower(),)).fetchall()
    if len(admins) > 1:
        raise ValueError('存在大小写冲突的管理员账号，未自动合并')
    admin = admins[0] if admins else None
    employee = connection.execute('SELECT * FROM employees WHERE username=?', (username,)).fetchone()
    linked = connection.execute('SELECT * FROM employees WHERE admin_id=?', (admin['id'],)).fetchone() if admin else None
    if employee and (not admin or employee['admin_id'] != admin['id']):
        raise ValueError('同名员工尚未明确关联，不能自动覆盖或升级；请先人工核实身份')
    if admin and not admin['is_active'] or linked and not linked['is_active']:
        raise ValueError('账号已停用，本工具不自动重新启用账号')
    if admin:
        admin_id = admin['id']
        connection.execute('UPDATE admins SET password_hash=? WHERE id=?', (encoded, admin_id))
    else:
        admin_id = connection.execute('INSERT INTO admins(username,password_hash) VALUES(?,?)', (username, encoded)).lastrowid
    if linked:
        employee_id = linked['id']
        connection.execute('UPDATE employees SET password_hash=?,must_change_password=0,auth_version=auth_version+1 WHERE id=?', (encoded, employee_id))
    else:
        employee_id = connection.execute('INSERT INTO employees(username,name,department,password_hash,must_change_password,admin_id) VALUES(?,?,?,?,0,?)',
                                         (username.lower(), username, '平台管理', encoded, admin_id)).lastrowid
    connection.execute('DELETE FROM employee_sessions WHERE employee_id=? OR admin_id=?', (employee_id, admin_id))
    return admin_id, employee_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path, help='Explicit existing SQLite path')
    parser.add_argument('--username', default='adminMO')
    args = parser.parse_args()
    target = args.database.resolve()
    if not target.is_file():
        parser.error('数据库必须是已存在的文件；不会新建空库')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{2,63}', args.username):
        parser.error('账号格式不合规')
    print(f'数据库：{target}')
    print(f'账号：{args.username}；将设置统一登录密码，保留已有 ID 与业务数据，并撤销该账号旧会话。')
    if input('确认操作此数据库，请输入 SET ADMIN：') != 'SET ADMIN':
        raise SystemExit('已取消，未写入')
    password = getpass('新密码（12–128 位，输入不回显）：')
    if not 12 <= len(password) <= 128 or getpass('再次输入：') != password:
        raise SystemExit('长度不合规或两次输入不同，未写入')
    encoded = hash_password(password)
    del password
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute('BEGIN IMMEDIATE')
            set_password(connection, args.username, encoded)
    except (ValueError, sqlite3.Error) as error:
        raise SystemExit(str(error)) from None
    finally:
        connection.close()
    print('管理员统一登录已配置；密码未输出，请通过 /login 登录。')


if __name__ == '__main__':
    main()
