#!/usr/bin/env python3
"""Build only the local candidate, under the shared workshop lock."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

D = Path(__file__).resolve().parent
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('RH_', 'ROUNDHOUSE_', 'SOUND_')) and k != 'PROBE_BASE'}
env.update(CARGO_HOME=str(D / 'cargo-home'), CARGO_TARGET_DIR=str(D / 'target'),
           CARGO_BUILD_JOBS='4', GIT_CONFIG_GLOBAL='/dev/null',
           GIT_OPTIONAL_LOCKS='0', CARGO_NET_GIT_FETCH_WITH_CLI='true',
           TMPDIR=str(D / 'tmp'), RBENV_VERSION='4.0.7')
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=D / 'source', text=True).strip()
command = ['cargo', '+1.98.1', 'build', '--release', '--locked', '--offline', '--bin', 'roundhouse']
started = time.monotonic()
result = subprocess.run(command, cwd=D / 'source', env=env)
receipt = {'source_commit': commit, 'source_branch': 'writer-ownership-initial', 'command': command,
           'build_seconds': time.monotonic() - started, 'exit_code': result.returncode,
           'environment': {k: env[k] for k in ('CARGO_HOME', 'CARGO_TARGET_DIR', 'CARGO_BUILD_JOBS', 'RBENV_VERSION')},
           'rust': subprocess.check_output(['rustc', '+1.98.1', '--version'], env=env, text=True).strip()}
if result.returncode == 0:
    (D / 'bin').mkdir(exist_ok=True)
    shutil.copy2(D / 'target/release/roundhouse', D / 'bin/roundhouse')
    receipt['binary_sha256'] = hashlib.sha256((D / 'bin/roundhouse').read_bytes()).hexdigest()
(D / 'build.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2), flush=True)
raise SystemExit(result.returncode)
