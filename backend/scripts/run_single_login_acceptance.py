"""Windows-only isolated acceptance server. Fresh synthetic SQLite/uploads; no reload or real data."""
import argparse
from contextlib import closing
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import tempfile


def protect_credentials(values, target):
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    raw = json.dumps(values).encode('utf-8')
    buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    source, output = Blob(len(raw), buffer), Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    crypt.CryptProtectData.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptProtectData.restype = wintypes.BOOL
    if not crypt.CryptProtectData(ctypes.byref(source), 'AI Portal temporary acceptance', None, None, None, 1, ctypes.byref(output)):
        raise ctypes.WinError(ctypes.get_last_error())
    kernel = ctypes.WinDLL('kernel32')
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    try:
        target.write_bytes(ctypes.string_at(output.data, output.size))
    finally:
        kernel.LocalFree(output.data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8002)
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('This local launcher protects temporary credentials with Windows DPAPI.')
    with closing(socket.socket()) as probe:
        try:
            probe.bind(('127.0.0.1', args.port))
        except (OSError, OverflowError):
            parser.error('Port unavailable. No existing service was stopped.')
    root = Path(tempfile.mkdtemp(prefix='ai-portal-single-login-'))
    identities = {
        'admin': {'username': 'adminMO', 'password': secrets.token_urlsafe(24)},
        'market': {'username': 'market-demo', 'password': secrets.token_urlsafe(24)},
        'employee': {'username': 'employee-demo', 'password': secrets.token_urlsafe(24)},
    }
    # Set every database-related option before importing any application module.
    os.environ.update(DATABASE_PATH=str(root/'acceptance.db'), SESSION_SECRET=secrets.token_urlsafe(48),
        SESSION_COOKIE_NAME='ai_portal_single_login_acceptance', SESSION_COOKIE_SECURE='false',
        ADMIN_USERNAME='adminMO', ADMIN_PASSWORD=identities['admin']['password'], EXCHANGE_ENABLED='false')
    backend = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend))
    import upload_api
    upload_api.UPLOAD_ROOT = root/'uploads'
    from main import app
    from database import DATABASE_PATH, get_db_connection
    from auth_security import hash_password
    from scripts.set_admin_password import set_password
    from PIL import Image
    assert DATABASE_PATH.resolve() == (root/'acceptance.db').resolve()
    for category in ['banners', 'news', 'tools']:
        folder=root/'uploads'/category
        folder.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (1200, 316), (245, 246, 247)).save(folder/'acceptance.webp', 'WEBP')
    with closing(get_db_connection()) as connection, connection:
        set_password(connection, 'adminMO', hash_password(identities['admin']['password']))
        for role, name in [('market', 'Local Team Tester'), ('employee', 'Local Employee Tester')]:
            identity=identities[role]
            connection.execute('INSERT INTO employees(username,name,department,password_hash,must_change_password) VALUES(?,?,?,?,0)',
                (identity['username'], name, 'Isolated Acceptance', hash_password(identity['password'])))
        connection.execute('INSERT INTO news(title,summary,content,source_type,publish_date,is_published) VALUES(?,?,?,?,?,1)',
            ('本地验收示例新闻', '完全虚构，仅用于登录与内容显示验收。', '本条内容不是正式新闻，也未从原开发库复制。', '通知', '2026-10-21'))
        connection.execute("INSERT INTO banners(title,description,button_text,image,action_type,action_target,is_active) VALUES(?,?,?,?,?,?,1)",
            ('单次登录 · 隔离验收', '本环境仅含虚构测试数据，不是原开发环境。', '查看新闻', '/uploads/banners/acceptance.webp', 'route', '/news'))
        for title, action, target, status in [('验收 · Dify 助手','route','/assistant','available'),
                ('验收 · QsTArT','static','/tools/qstart/index.html','available'),
                ('验收 · 待开放工具','none','','developing')]:
            connection.execute('INSERT INTO tools(title,description,action_type,action_target,status,is_active) VALUES(?,?,?,?,?,1)',
                (title,'虚构示例入口，不连接真实业务系统。',action,target,status))
    protect_credentials(identities, root/'credentials.dpapi')
    state={'database':str(DATABASE_PATH),'directory':str(root),'backend':f'http://127.0.0.1:{args.port}',
           'usernames':{role:identity['username'] for role,identity in identities.items()},
           'cookieName':'ai_portal_single_login_acceptance','syntheticOnly':True}
    (root/'session.json').write_text(json.dumps(state,ensure_ascii=True),encoding='utf-8')
    del identities
    os.environ.pop('ADMIN_PASSWORD', None)
    print(json.dumps(state,ensure_ascii=True),flush=True)
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=args.port,reload=False,access_log=False,log_level='warning')


if __name__=='__main__':
    main()
