"""Back up the current source tree, including uncommitted files, without runtime data."""
import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    destination = Path(args.destination).resolve()
    if destination == root or root in destination.parents:
        parser.error('Backup must be outside the source tree')
    excluded_dirs = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'dist',
                     '.cache', '.pytest_cache', '.ruff_cache', 'uploads', 'backups',
                     'private-data', 'local-private', 'acceptance-data', '.idea', '.aws', '.ssh'}
    excluded_files = ['*.db*', '*.sqlite*', '*.pyc', '*.pyo', '*.log', '*.tmp', '*.temp',
                      '*.bak', '*.backup', '*.pem', '*.key', '*.p12', '*.pfx', '*.jks',
                      '*.keystore', 'id_rsa*', 'id_ed25519*', 'credentials*', '*password*.txt',
                      '*password*.json', '*.private.html', '*.business-data.html', '*.xlsx', '*.xls']
    files, excluded = [], []
    def walk(folder):
        for item in sorted(folder.iterdir()):
            relative = item.relative_to(root).as_posix()
            name = item.name.lower()
            if item.is_symlink():
                raise RuntimeError(f'Review symlink before backup: {relative}')
            if item.is_dir():
                if name in excluded_dirs:
                    excluded.append(relative + '/')
                else:
                    walk(item)
            elif ((name.startswith('.env') and not name.endswith('.example'))
                  or any(fnmatch.fnmatch(name, pattern) for pattern in excluded_files)
                  or relative == 'artifacts/project-dashboard/项目推进看板_2026-10-20.html'):
                excluded.append(relative)
            else:
                data = item.read_bytes()
                if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:sk-proj-|sk-ant-)[A-Za-z0-9_-]{20,}', data):
                    raise RuntimeError(f'Potential real secret; review required: {relative}')
                files.append((relative, data))
    walk(root)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain=v1', '-uall'], cwd=root, text=True)
    destination.mkdir(parents=True, exist_ok=False)
    archive = destination / 'source.zip'
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files}
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for name, data in files:
            z.writestr(name, data)
    with tempfile.TemporaryDirectory(prefix='ai-portal-restore-') as temp:
        restored = Path(temp)
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            z.extractall(restored)
        actual = {p.relative_to(restored).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in restored.rglob('*') if p.is_file()}
        assert actual == hashes, 'Restored file hashes differ'
    report = dict(head=head, file_count=len(files), source_bytes=sum(len(d) for _, d in files),
                  archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                  restore_verified=True, files=hashes, excluded=excluded, git_status=status)
    (destination / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (destination / 'HEAD.txt').write_text(head + '\n', encoding='ascii')
    (destination / 'RESTORE.txt').write_text(
        'Extract source.zip into an empty directory. Verify every file against manifest.json files SHA256.\n'
        'Runtime secrets, databases, uploads and environments are intentionally excluded.\n'
        'Use the local backup tag for committed history; source.zip preserves the working tree.\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in {'files', 'excluded', 'git_status'}}, indent=2))
    print(destination)


if __name__ == '__main__':
    main()
