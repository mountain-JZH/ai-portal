"""Linux ECS read-only evidence collection. Never imports the app or reads secrets into output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess


def run(args):
    result = subprocess.run(args, text=True, capture_output=True, timeout=45)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def emit(kind, **values):
    print(json.dumps({'kind': kind, **values}, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', default='ai-portal.service')
    args = parser.parse_args()
    if os.name != 'posix' or not re.fullmatch(r'[\w@.-]+\.service', args.service):
        parser.error('Run on Linux with the actual systemd service name')
    root = Path('/opt/ai-portal')
    # Only metadata; never systemctl Environment or /proc environ as a whole.
    code, output, error = run(['systemctl', 'show', args.service,
        '-p', 'LoadState', '-p', 'ActiveState', '-p', 'SubState', '-p', 'MainPID',
        '-p', 'User', '-p', 'Group', '-p', 'WorkingDirectory', '-p', 'EnvironmentFiles',
        '-p', 'FragmentPath', '-p', 'DropInPaths'])
    emit('systemd', code=code, properties=output, error=error)
    props = dict(line.split('=', 1) for line in output.splitlines() if '=' in line)
    pid = int(props.get('MainPID') or 0)
    if pid > 1:
        proc = Path('/proc')/str(pid)
        try:
            environment = dict(value.split(b'=', 1) for value in (proc/'environ').read_bytes().split(b'\0') if b'=' in value)
            allowed = ['DATABASE_PATH', 'EXCHANGE_ENABLED', 'SESSION_COOKIE_SECURE']
            selected = {key: environment.get(key.encode(), b'<unset>').decode(errors='replace') for key in allowed}
            # Only startup/module/bind arguments; no arbitrary command line or secret values.
            command = (proc/'cmdline').read_bytes().split(b'\0')
            startup = []
            for index, part in enumerate(command):
                text = part.decode(errors='replace')
                if index == 0 or text in {'uvicorn', 'gunicorn', 'main:app', '--reload', '-m'}:
                    startup.append(text)
                elif index and command[index-1] in {b'--host', b'--port', b'--workers', b'--chdir', b'--app-dir'}:
                    startup.extend([command[index-1].decode(), text])
            emit('process', pid=pid, cwd=str((proc/'cwd').resolve()), exe=str((proc/'exe').resolve()),
                 startup=startup, selected_environment=selected)
            for descriptor in (proc/'fd').iterdir():
                try:
                    target = str(descriptor.resolve())
                    if re.search(r'\.(db|sqlite|sqlite3)(-wal|-shm)?$', target):
                        emit('open_database', path=target)
                except OSError:
                    pass
        except (OSError, ValueError) as exc:
            emit('process_unavailable', error=str(exc))
    for path in [root/'source', root/'backend', root/'frontend/dist', root/'data/ai_portal.db', root/'uploads',
                 root/'release-testing/20261021', root/'release-backups/20261021-pre-upgrade',
                 root/'release-candidates', root/'update.sh']:
        if not path.exists() and not path.is_symlink():
            emit('path', path=str(path), exists=False)
            continue
        code, size, error = run(['du', '-skx', '--', str(path)])
        emit('path', path=str(path), resolved=str(path.resolve()), symlink=path.is_symlink(),
             kib=size.split('\t')[0] if code == 0 else None, error=error)
        if path.is_dir():
            emit('children', path=str(path), entries=[{'name': p.name, 'symlink': p.is_symlink()}
                 for p in sorted(path.iterdir())[:60]])
    for folder in [root/'source', root/'backend']:
        code, head, _ = run(['git', '-C', str(folder), 'rev-parse', 'HEAD'])
        emit('git', path=str(folder), head=head if code == 0 else None)
        for name in ['main.py', 'database.py', 'requirements.txt']:
            p = folder/name
            if p.is_file():
                emit('code_hash', path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    code, output, error = run(['nginx', '-T'])
    directives = re.compile(r'^\s*(?:listen|server_name|root|alias|include|location|proxy_pass|try_files|upstream|server\s+127\.|proxy_set_header\s+(?:Host|X-Forwarded-Proto|Cookie))\b')
    relevant = [line for line in output.splitlines() if line.startswith('# configuration file ') or directives.search(line)]
    emit('nginx', code=code, structure=relevant, diagnostics=error)
    # Report configuration references by file and line number, without printing secret-bearing lines.
    targets = ['release-testing', 'release-candidates', 'release-backups', '/opt/ai-portal', 'update.sh']
    for directory in [Path('/etc/systemd/system'), Path('/etc/nginx'), Path('/etc/cron.d')]:
        if not directory.exists():
            continue
        for config in directory.rglob('*'):
            if not config.is_file():
                continue
            try:
                for line_number, line in enumerate(config.read_text(errors='replace').splitlines(), 1):
                    matches = [value for value in targets if value in line and not line.lstrip().startswith('#')]
                    if matches:
                        emit('config_reference', file=str(config), line=line_number, matches=matches)
            except OSError:
                pass
    update = root/'update.sh'
    if update.is_file():
        data = update.read_bytes()
        emit('update_script', sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
             note='Full private review required before use; never executed by this audit.')
        for number, line in enumerate(data.decode(errors='replace').splitlines(), 1):
            operations = [word for word in ['rsync', '--delete', 'rm ', 'cp ', 'git reset', 'git clean',
                'systemctl', 'pip ', 'npm ', 'sqlite', '.env'] if word in line and not line.lstrip().startswith('#')]
            if operations:
                emit('update_operation', line=number, operations=operations)
    database = root/'data/ai_portal.db'
    if database.is_file():
        # This verifies the known file only. Cross-check process/config evidence to prove it is the active DB.
        connection = sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True, timeout=5)
        try:
            connection.execute('PRAGMA query_only=ON')
            emit('database', path=str(database.resolve()), quick_check=connection.execute('PRAGMA quick_check').fetchall(),
                 journal_mode=connection.execute('PRAGMA journal_mode').fetchone()[0])
            tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            emit('schema_names', tables=sorted(tables))
            for name in ['news', 'banners', 'announcements', 'tools', 'employees', 'admins', 'exchange_resources']:
                if name in tables:
                    emit('row_count', table=name, count=connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
            for name in ['banners', 'tools']:
                if name in tables:
                    columns = {r[1] for r in connection.execute(f'PRAGMA table_info("{name}")')}
                    if {'id', 'action_type', 'action_target'} <= columns:
                        rows = connection.execute(f"SELECT id FROM {name} WHERE action_type='route' AND (action_target='/projects' OR action_target LIKE '/projects/%' OR action_target LIKE '/projects?%' OR action_target='/admin/projects')").fetchall()
                        emit('obsolete_route_record_ids', table=name, ids=[r[0] for r in rows])
        finally:
            connection.close()
    code, output, error = run(['df', '-h', str(root)])
    emit('disk', code=code, output=output, error=error)
    code, output, error = run(['curl', '--max-time', '8', '-sS', '-o', '/dev/null', '-w', '%{http_code}', 'http://127.0.0.1/api/health'])
    emit('local_nginx_health', code=code, http_status=output, error=error)


if __name__ == '__main__':
    main()
