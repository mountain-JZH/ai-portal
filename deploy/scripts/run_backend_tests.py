"""Run each integration suite in its own process (module-level app/DB/upload state)."""
from pathlib import Path
import argparse
import json
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report-dir')
args = parser.parse_args()
failed = []
results, logs = [], []
for suite in sorted((root / 'backend/tests').glob('test_*.py')):
    print(f'Running {suite.name}', flush=True)
    result = subprocess.run([sys.executable, str(suite)], cwd=root,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout, flush=True)
    logs.append(suite.name + '\n' + result.stdout)
    count = re.search(r'Ran (\d+) tests?', result.stdout)
    results.append({'suite': suite.name, 'returncode': result.returncode,
                    'tests': int(count[1]) if count else None})
    if result.returncode:
        failed.append(suite.name)
if args.report_dir:
    report = Path(args.report_dir)
    report.mkdir(parents=True, exist_ok=True)
    (report/'backend-tests.log').write_text('\n'.join(logs), encoding='utf-8')
    (report/'backend-test-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
if failed:
    raise SystemExit('Failed suites: ' + ', '.join(failed))
print('All backend suites passed.')
