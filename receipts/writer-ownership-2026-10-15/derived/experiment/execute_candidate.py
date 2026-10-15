#!/usr/bin/env python3
"""Sequential candidate stages; caller holds the required master heavy lock."""
import json
from pathlib import Path
import subprocess
import sys

D = Path(__file__).resolve().parent


def stage(label, script, *args):
    print('START ' + label, flush=True)
    with (D / (label + '.log')).open('wb') as out:
        r = subprocess.run([sys.executable, '-B', script, *args], cwd=D, stdout=out, stderr=subprocess.STDOUT)
    print('END ' + label + ': exit ' + str(r.returncode), flush=True)
    if r.returncode:
        raise SystemExit(r.returncode)


assert (D / 'baseline-control-index.json').exists(), 'finish fresh baseline controls before starting'
stage('build', 'build.py')
stage('matrix', 'run_residual.py')
stage('analysis', 'analyze_residual.py')
audit = json.loads((D / 'gate-audit.json').read_text())
print(json.dumps({h: audit[h] for h in ('H1', 'H2')}, indent=2), flush=True)
if any('extended focus required' in reason for reason in audit['H1']['kills']):
    raise SystemExit('registered_protocol says to extend focus, report the changed slot, and stop; retain target for that probe.')
stage('h3', 'run_residual.py', 'h3')
stage('h3-analysis', 'analyze_h3.py')
stage('receipt-audit', 'verify_receipts.py')
stage('clean', 'clean.py')
