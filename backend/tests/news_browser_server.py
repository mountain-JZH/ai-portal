"""Disposable browser-test API. Never loads the development database or uploads."""
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='ai-portal-news-browser-') as directory:
        root = Path(directory)
        os.environ.update(DATABASE_PATH=str(root / 'test.db'),
            SESSION_SECRET=os.environ.pop('NEWS_BROWSER_SESSION_SECRET'),
            ADMIN_USERNAME=os.environ.pop('NEWS_BROWSER_ADMIN_USERNAME'),
            ADMIN_PASSWORD=os.environ.pop('NEWS_BROWSER_ADMIN_PASSWORD'),
            SESSION_COOKIE_SECURE='false', EXCHANGE_ENABLED='false')
        import upload_api
        upload_api.UPLOAD_ROOT = root / 'uploads'
        import main
        from database import get_db_connection
        sample = Path(__file__).with_name('fixtures').joinpath('news-brief.md').read_text(encoding='utf-8-sig')
        with get_db_connection() as connection:
            for title, content, kind, published in [
                ('普通新闻测试', '普通正文\n\n**保留原文**', '行业资讯', 1),
                ('新能源行业早报｜2026-11-16', sample, '新能源行业早报', 1),
                ('隔离草稿', sample, '新能源行业早报', 0),
            ]:
                connection.execute('INSERT INTO news (title,content,source_type,publish_date,is_published) VALUES (?,?,?,?,?)',
                    (title, content, kind, '2026-11-16', published))
        import uvicorn
        uvicorn.run(main.app, host='127.0.0.1', port=18080, log_level='warning')
