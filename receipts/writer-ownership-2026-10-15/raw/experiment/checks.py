#!/usr/bin/env python3
"""Record an offline Cargo check under the caller's heavy lock."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

D = Path(__file__).resolve().parent
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('RH_', 'ROUNDHOUSE_', 'SOUND_')) and k != 'PROBE_BASE'}
env.update(CARGO_HOME=str(D / 'cargo-home'), CARGO_TARGET_DIR=str(D / 'target'),
           CARGO_BUILD_JOBS='4', TMPDIR=str(D / 'tmp'), RBENV_VERSION='3.4.9',
           CARGO_NET_GIT_FETCH_WITH_CLI='true', GIT_CONFIG_GLOBAL='/dev/null')
command = ['cargo', '+1.98.1', 'test', '--locked', '--offline'] + sys.argv[1:]
started = time.monotonic()
result = subprocess.run(command, cwd=D / 'source', env=env)
ruby = subprocess.run(['ruby', '--version'], env=env, text=True,
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
receipt = {'command': command, 'exit_code': result.returncode,
           'seconds': time.monotonic() - started,
           'ruby': ruby.stdout.strip(), 'ruby_version_exit': ruby.returncode,
           'environment': {k: env[k] for k in ('CARGO_HOME', 'CARGO_TARGET_DIR', 'CARGO_BUILD_JOBS', 'RBENV_VERSION')}}
(D / (os.environ.get('CHECKS_LABEL', 'checks') + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2), flush=True)
raise SystemExit(result.returncode)
