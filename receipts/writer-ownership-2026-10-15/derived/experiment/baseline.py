#!/usr/bin/env python3
"""Run under the shared workshop lock; reproduce the advance_prediction baseline pair."""
import json
from pathlib import Path
import subprocess
import sys

D = Path(__file__).resolve().parent
W = D / 'workshop'
pair = {}
for schedule in ('unset', '1'):
    # run.sh delegates to this exact runner. The caller already holds the
    # user-required master lock, so avoid consuming a second shared slot.
    result = subprocess.run([sys.executable, '-B', 'lib/run.py', 'campfire', schedule], cwd=W, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    pair[schedule] = result.stdout.strip()
    (D / ('baseline-' + schedule + '.log')).write_text(result.stderr + result.stdout)
    print(result.stderr, end='', flush=True)
    print(result.stdout, end='', flush=True)
(D / 'baseline-pair.json').write_text(json.dumps(pair, indent=2) + '\n')
result = subprocess.run(['./diff.sh', pair['unset'], pair['1']], cwd=W, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
(D / 'baseline-diff.txt').write_text(result.stdout)
print(result.stdout, end='', flush=True)
result = subprocess.run(['./diff.sh', pair['unset'], pair['1'], '--json'], cwd=W,
                        stdout=subprocess.PIPE, check=True)
(D / 'baseline-diff.json').write_bytes(result.stdout)
diff = json.loads(result.stdout)
assert diff['declarations_equal']
assert diff['attempt']['counts'] == [740, 740]
assert diff['mutation']['counts'] == [678, 678]
for key, names in [('left_only', {'require_authentication', 'terminate_current_session'}),
                   ('right_only', {'resume_session', 'start_new_session_for'})]:
    actual = {json.loads(row[2])[2] for row in diff['mutation'][key]}
    assert actual == names, (key, actual)
print('PASS: baseline reproduces the advance_prediction four identities.', flush=True)
