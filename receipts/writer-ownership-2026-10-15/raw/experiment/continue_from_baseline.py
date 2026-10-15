#!/usr/bin/env python3
"""Continue under the baseline job's existing master lock after its controls."""
from pathlib import Path
import runpy
import time

D = Path(__file__).resolve().parent
deadline = time.monotonic() + 300
if not (D / 'checks-default.json').exists():
    print('Waiting for the already-running default test job before committing.', flush=True)
while not (D / 'checks-default.json').exists():
    if time.monotonic() >= deadline:
        raise SystemExit('Default tests still running; release this lock lease and inspect them.')
    time.sleep(2)
runpy.run_path(str(D / 'commit_candidate.py'), run_name='__main__')
runpy.run_path(str(D / 'execute_candidate.py'), run_name='__main__')
