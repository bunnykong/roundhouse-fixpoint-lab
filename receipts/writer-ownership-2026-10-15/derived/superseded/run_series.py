#!/usr/bin/env python3
"""Run an exact card series while the caller holds the workshop lock."""
import json
import os
from pathlib import Path
import subprocess
import sys

D = Path(__file__).resolve().parent
W = D / 'workshop'
C = 'structure-success-20261015-bf56edf9'
FLAGS = {'a': ['RH_SPLICED_WRITER_OWNERSHIP=1'], 'b': ['RH_SKIP_RETURN_STABILIZE=1'],
         'both': ['RH_SPLICED_WRITER_OWNERSHIP=1', 'RH_SKIP_RETURN_STABILIZE=1'], 'off': []}
series = sys.argv[1]
label = sys.argv[2] if len(sys.argv) > 2 else series
env = os.environ.copy()
env['CANDIDATE_SOURCE_COMMIT'] = subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], cwd=D / 'source', text=True).strip()
index_path = D / 'series-index.json'
index = json.loads(index_path.read_text()) if index_path.exists() else {}
assert label not in index, 'use a new series label to preserve recorded runs'
index[label] = {}
for app, schedules in [('campfire', ('unset', '1', '2', 'repeat-unset')),
                       ('fixture', ('unset', '1'))]:
    for schedule in schedules:
        command = [sys.executable, '-B', 'theory/run_candidate.py', '--binary', str(D / 'bin/roundhouse'),
                   '--condition', C]
        for flag in FLAGS[series]:
            command += ['--flag', flag]
        command += [app, schedule]
        result = subprocess.run(command, cwd=W, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stderr, end='', flush=True)
        print(result.stdout, end='', flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
        index[label][app + '-' + schedule] = result.stdout.strip()
        index_path.write_text(json.dumps(index, indent=2) + '\n')
print('Recorded series ' + label, flush=True)
