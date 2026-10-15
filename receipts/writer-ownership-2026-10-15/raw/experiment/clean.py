#!/usr/bin/env python3
"""Remove only this experiment's Cargo target, under the caller's heavy lock."""
import json
import os
from pathlib import Path
import subprocess
import time

D = Path(__file__).resolve().parent
env = os.environ.copy()
env.update(CARGO_HOME=str(D / 'cargo-home'), CARGO_TARGET_DIR=str(D / 'target'), CARGO_BUILD_JOBS='4')
command = ['cargo', '+1.98.1', 'clean']
started = time.monotonic()
result = subprocess.run(command, cwd=D / 'source', env=env, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
receipt = {'command': command, 'cwd': str(D / 'source'), 'exit_code': result.returncode,
           'seconds': time.monotonic() - started, 'cargo_target_dir': env['CARGO_TARGET_DIR'],
           'output': result.stdout, 'target_exists_after': (D / 'target').exists()}
(D / 'clean.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2), flush=True)
raise SystemExit(result.returncode)
