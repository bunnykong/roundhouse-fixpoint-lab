#!/usr/bin/env python3
"""Verify the pre-run kit commit and hash manifest, then append a stage-start receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

work = Path(sys.argv[1]).resolve()
manifest_path = work / 'receipts/kit-manifest.json'
expected = json.loads(manifest_path.read_text())
kit = work / 'kit'
actual = {}
for p in sorted(kit.rglob('*')):
    if p.is_symlink():
        actual[p.relative_to(kit).as_posix()] = 'symlink:' + str(p.readlink())
    elif p.is_file():
        actual[p.relative_to(kit).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
assert actual == expected, 'frozen kit changed'
commit = (work / 'receipts/kit-commit.txt').read_text().strip()
assert subprocess.run(['git', '-C', str(work), 'diff', '--quiet', commit, '--', 'kit'], check=False).returncode == 0
assert subprocess.run(['git', '-C', str(work), 'cat-file', '-e', commit + ':kit/run.sh'], check=False).returncode == 0
with (work / 'receipts/stage-starts.jsonl').open('a') as out:
    out.write(json.dumps(dict(stage=sys.argv[2], utc=datetime.now(timezone.utc).isoformat(), kit_commit=commit,
                             manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest())) + '\n')
print('frozen kit verified at', commit, 'for', sys.argv[2], flush=True)
