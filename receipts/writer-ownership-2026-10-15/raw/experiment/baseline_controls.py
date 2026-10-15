#!/usr/bin/env python3
"""Complete baseline controls at the copied input path, under the caller's heavy lock."""
import json
from pathlib import Path
import subprocess
import sys

D = Path(__file__).resolve().parent
W = D / 'workshop'
index = {'campfire-' + s: p for s, p in json.loads((D / 'baseline-pair.json').read_text()).items()}
for app, schedules in [('campfire', ('2', 'repeat-unset')), ('fixture', ('unset', '1'))]:
    for schedule in schedules:
        result = subprocess.run([sys.executable, '-B', 'lib/run.py', app, schedule], cwd=W,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        label = app + '-' + schedule
        index[label] = result.stdout.strip()
        (D / ('baseline-control-' + label + '.log')).write_text(result.stderr + result.stdout)
        (D / 'baseline-control-index.json').write_text(json.dumps(index, indent=2) + '\n')
        print(result.stderr, end='', flush=True)
        print(result.stdout, end='', flush=True)

# This authorized continuation stays under the caller's master lock. The
# scientific runners and their frozen input/observer conditions stay unchanged.
import runpy
runpy.run_path(str(D / 'continue_from_baseline.py'), run_name='__main__')
