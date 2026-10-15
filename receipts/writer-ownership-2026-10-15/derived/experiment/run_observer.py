#!/usr/bin/env python3
"""Execute the unchanged registered_protocol matrix under the caller's master heavy lock."""
import json
import os
from pathlib import Path
import subprocess
import sys

D = Path(__file__).resolve().parent
W = D / 'workshop'
C = 'writer-ownership-20261015-bf56edf9'
FLAGS = {'a': ['RH_SPLICED_WRITER_OWNERSHIP=1'], 'b': ['RH_SKIP_RETURN_STABILIZE=1'],
         'both': ['RH_SPLICED_WRITER_OWNERSHIP=1', 'RH_SKIP_RETURN_STABILIZE=1'], 'off': []}
env = os.environ.copy()
env['CANDIDATE_SOURCE_COMMIT'] = subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], cwd=D / 'source', text=True).strip()
index_file = D / 'series-index.json'
index = json.loads(index_file.read_text()) if index_file.exists() else {}


def run(series, app, schedule, extra=()):
    key = app + '-' + schedule
    assert key not in index.get(series, {}), 'recorded runs are immutable'
    command = [sys.executable, '-B', 'theory/run_candidate.py',
               '--binary', str(D / 'bin/roundhouse'), '--condition', C + '-' + series]
    for flag in FLAGS.get(series, FLAGS['both']) + list(extra):
        command += ['--flag', flag]
    command += [app, schedule]
    result = subprocess.run(command, cwd=W, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(series + '/' + key, flush=True)
    print(result.stderr + result.stdout, end='', flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    index.setdefault(series, {})[key] = result.stdout.strip()
    index_file.write_text(json.dumps(index, indent=2) + '\n')


if sys.argv[1:] == ['h3']:
    out = W / 'theory/runs' / (C + '-h3')
    out.mkdir(parents=True, exist_ok=True)
    for schedule, name in [('unset', 'unset.dump'), ('2', 'two.dump')]:
        assert not (out / name).exists(), 'preserve recorded H3 dumps'
        run('h3', 'campfire', schedule, ['RH_REASON_SITE_CENSUS=' + str(out / name)])
else:
    for schedule in ('unset', '1', '2', 'repeat-unset'):
        for series in ('a', 'b', 'both', 'off'):
            run(series, 'campfire', schedule)
    for schedule in ('unset', '1'):
        for series in ('a', 'off'):
            run(series, 'fixture', schedule)
