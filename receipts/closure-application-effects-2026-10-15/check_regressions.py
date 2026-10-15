#!/usr/bin/env python3
"""Run unchanged checker assertions with public, freshly generated fixture inputs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import rerun
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='closure-checker-regressions-') as temp:
    root=Path(temp);fixtures=root/'fixtures'
    generated=subprocess.run([sys.executable,'-B',str(HERE/'native/tools/gen_fixtures.py'),str(fixtures)],capture_output=True,text=True)
    assert generated.returncode==0,(generated.stdout,generated.stderr)
    scan=root/'scan.json';scan.write_bytes(rerun.data('supplement/scan-fixtures.json'))
    env=dict(os.environ,CLOSURE_FIXTURES=str(fixtures),CLOSURE_SCAN=str(scan))
    test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(HERE/'native/tools'),'-p','test_checkers.py','-v'],env=env,capture_output=True,text=True)
    sys.stdout.write(test.stdout);sys.stderr.write(test.stderr)
    assert test.returncode==0 and 'Ran 6 tests' in test.stderr
