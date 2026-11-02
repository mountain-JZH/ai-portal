"""Package a reviewed working tree and built frontend without secrets or runtime data."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = Path(args.output).resolve()
    if not (root/'frontend/dist/index.html').is_file():
        parser.error('Build the production frontend first')
    if output.exists() or output.with_suffix(output.suffix+'.manifest.json').exists():
        parser.error('Use a new output filename; never overwrite a fixed candidate')
    removed = ['backend/projects_api.py', 'backend/project_data.py', 'backend/project_write_api.py',
               'backend/project_changes.py', 'backend/project_updates.py',
               'frontend/src/views/ProjectsView.vue', 'frontend/src/views/ProjectsAdminView.vue',
               'frontend/src/views/ProjectEditView.vue']
    assert all(not (root/name).exists() for name in removed)
    files = set()
    for folder in ['backend', 'deploy']:
        for p in (root/folder).rglob('*'):
            if any(part in {'.venv', '__pycache__', 'node_modules', '.pytest_cache'} for part in p.parts):
                continue
            if p.is_file() and (p.suffix == '.py' or p.name in {'requirements.txt', '.env.example'}
                                or p.name.endswith('.example')):
                if p.name.startswith('run_project_'):
                    continue
                files.add(p)
    for folder in ['frontend/dist', 'frontend/src', 'frontend/public', 'frontend/tests']:
        files.update(p for p in (root/folder).rglob('*') if p.is_file())
    for name in ['package.json', 'package-lock.json', 'vite.config.js', 'jsconfig.json',
                 'index.html', '.env.example', '.env.production.example']:
        files.add(root/'frontend'/name)
    values = {}
    for p in sorted(files):
        assert not p.is_symlink(), p
        name = p.relative_to(root).as_posix()
        assert not (p.name.startswith('.env') and not p.name.endswith('.example')), name
        assert p.suffix not in {'.db', '.sqlite', '.sqlite3', '.key', '.pem'}, name
        values[name] = p.read_bytes()
    manifest = {'base_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                'provenance': 'uncommitted reviewed working tree; base_head alone is not this candidate',
                'requires_production_approval': True,
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in values.items()}}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, 'w:gz', format=tarfile.PAX_FORMAT) as archive:
        for name, data in values.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), 0o644, 0
            archive.addfile(info, io.BytesIO(data))
    with tarfile.open(output, 'r:gz') as archive:
        restored = {member.name: hashlib.sha256(archive.extractfile(member).read()).hexdigest()
                    for member in archive.getmembers()}
        assert restored == manifest['files'], 'Candidate archive hashes differ'
    manifest.update(archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                    file_count=len(values), archive_bytes=output.stat().st_size, archive_verified=True)
    output.with_suffix(output.suffix+'.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'files'}, indent=2))
    print(output)


if __name__ == '__main__':
    main()
