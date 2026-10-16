#!/usr/bin/env python3
"""Default suite minus one named target (v2), with pre-enumerated binaries/tests and process-completion receipts.
Caller holds both heavy.lock and suite.lock. Ambient research flags are cleared.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

work = Path(sys.argv[1]).resolve()
receipts = work / 'receipts'
checkout = work / 'repo'
env = {k: v for k, v in os.environ.items() if not k.startswith(('RH_', 'ROUNDHOUSE_', 'SOUND_', 'PROVENANCE_')) and k != 'PROBE_BASE'}
env.update(CARGO_TARGET_DIR=str(work / 'target'), CARGO_BUILD_JOBS='4', RBENV_VERSION='3.4.4')
base = ['cargo', 'test', '--release', '--locked', '-j', '4']
# Spine v3 fixes the Cow assertion, so every integration target is selected.
EXCLUDED = {}
meta_proc = subprocess.run(['cargo', 'metadata', '--no-deps', '--format-version', '1', '--locked'], cwd=checkout, env=env,
                           capture_output=True, text=True, check=True)
tests = sorted(t['name'] for pkg in json.loads(meta_proc.stdout)['packages'] for t in pkg['targets'] if 'test' in t['kind'])
missing = sorted(set(EXCLUDED) - set(tests))
assert not missing, 'excluded targets not found: ' + str(missing)
select = ['--lib', '--bins'] + [x for t in tests if t not in EXCLUDED for x in ('--test', t)]
(receipts / 'suite-selection.json').write_text(json.dumps(dict(excluded=EXCLUDED, test_targets=len(tests),
                                                             selected_test_targets=len(tests) - len(EXCLUDED)), indent=1) + '\n')
start = time.time()
with (receipts / 'suite-inventory-build.jsonl').open('w') as out, (receipts / 'suite-inventory-build.log').open('w') as err:
    proc = subprocess.run(base + select + ['--no-run', '--message-format=json'], cwd=checkout, env=env, stdout=out, stderr=err)
if proc.returncode:
    raise SystemExit('suite inventory build failed: ' + str(proc.returncode))
artifacts = {}
for line in (receipts / 'suite-inventory-build.jsonl').open():
    row = json.loads(line)
    if row.get('reason') == 'compiler-artifact' and row.get('profile', {}).get('test') and row.get('executable'):
        src = Path(row['target']['src_path']).relative_to(checkout).as_posix()
        label = 'lib' if src == 'src/lib.rs' else Path(src).stem
        assert label not in artifacts, label
        artifacts[label] = row['executable']
inventory = {}
for label, executable in sorted(artifacts.items()):
    proc = subprocess.run([executable, '--list', '--format', 'terse'], cwd=checkout, env=env, capture_output=True, text=True, check=True)
    inventory[label] = sorted(line[:-6] for line in proc.stdout.splitlines() if line.endswith(': test'))
# Enumerate doctests separately with --list; it executes no test bodies.
proc = subprocess.run(base + ['--doc', '--', '--list', '--format', 'terse'], cwd=checkout, env=env, capture_output=True, text=True, check=True)
(receipts / 'suite-doctest-inventory.log').write_text(proc.stdout + proc.stderr)
inventory['doc:roundhouse'] = sorted(line[:-6] for line in proc.stdout.splitlines() if line.endswith(': test'))
(receipts / 'suite-inventory.json').write_text(json.dumps(inventory, indent=1) + '\n')
print('suite inventory:', len(inventory), 'binaries;', sum(map(len, inventory.values())), 'tests', flush=True)
for arm in ('off', 'on'):
    arm_env = dict(env)
    arm_env['RH_RESPONSE_RETURNS'] = '1' if arm == 'on' else '0'
    log = receipts / ('suite-' + arm + '.log')
    log.with_suffix('.inventory.json').write_text(json.dumps(inventory, indent=1) + '\n')
    began = time.time()
    print('suite', arm, 'start', flush=True)
    with log.open('w') as out:
        proc = subprocess.run(base + select + ['--no-fail-fast'], cwd=checkout, env=arm_env, stdout=out, stderr=subprocess.STDOUT)
        doc = subprocess.run(base + ['--doc', '--no-fail-fast'], cwd=checkout, env=arm_env, stdout=out, stderr=subprocess.STDOUT)
    codes = [proc.returncode, doc.returncode]
    meta = dict(completed=True, exit_code=max(codes) if all(c in (0, 101) for c in codes) else codes, exit_codes=codes,
                started=began, finished=time.time(), command=[base + select + ['--no-fail-fast'], base + ['--doc', '--no-fail-fast']],
                excluded=EXCLUDED, research_flags={k: v for k, v in arm_env.items() if k.startswith(('RH_', 'ROUNDHOUSE_'))})
    log.with_suffix('.process.json').write_text(json.dumps(meta, indent=1) + '\n')
    print('suite', arm, 'exit', proc.returncode, flush=True)
print('total seconds', time.time() - start, flush=True)
