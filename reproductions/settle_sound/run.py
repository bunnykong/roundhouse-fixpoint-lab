#!/usr/bin/env python3
"""Build and check all four merged-back normalizer arms against the saved trace."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
FLAGS = dict(RH_FOLD='1', RH_FOLD_SLOTS='1', RH_FOLD_JOIN='1', RH_BRK_ALLARMS='1',
             RH_FOLD_TAIL='1', RH_SCHED='sccq')
ARMS = [('main', '194f26cfaaada2a654e5f65949012f396706a275', False),
        ('main-flowfix', 'origin/main-flowfix', False),
        ('staged', 'origin/fixpoint-staged', True),
        ('sound', 'origin/fixpoint-sound', True)]


def clean_env():
    return {k: v for k, v in os.environ.items()
            if not k.startswith(('RH_', 'ROUNDHOUSE_', 'BUNDLE_'))}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(source, output):
    binaries = {}
    commits = {}
    target = output / 'cargo-target'
    env = dict(clean_env(), CARGO_BUILD_JOBS='4', CARGO_TARGET_DIR=str(target))
    for name, revision, _ in ARMS:
        commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', revision], text=True).strip()
        commits[name] = commit
        tree = output / ('source-' + name)
        subprocess.run(['git', '-C', str(source), 'worktree', 'add', '--detach', str(tree), commit], check=True)
        shutil.copyfile(HERE / 'settle_probe.rs', tree / 'src/bin/settle-probe.rs')
        with (output / ('build-' + name + '.log')).open('w') as log:
            subprocess.run(['cargo', 'build', '--release', '--locked', '--bin', 'roundhouse',
                            '--bin', 'settle-probe'], cwd=tree, env=env, stdout=log, stderr=log, check=True)
        binaries[name] = {}
        for binary in ('roundhouse', 'settle-probe'):
            dest = output / (name + '-' + binary)
            shutil.copy2(target / 'release' / binary, dest)
            binaries[name][binary] = str(dest)
    return binaries, commits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Roundhouse clone with the three public branches fetched')
    parser.add_argument('--binaries', type=Path, help='JSON map of prebuilt CLI and probe binaries')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--oracle', type=Path, default=LAB / 'oracle/check.py')
    args = parser.parse_args()
    if bool(args.source) == bool(args.binaries):
        parser.error('choose exactly one of --source or --binaries')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.binaries:
        supplied = json.loads(args.binaries.read_text())
        binaries, commits = supplied['binaries'], supplied['commits']
    else:
        binaries, commits = build(args.source.resolve(), out)
    spec = importlib.util.spec_from_file_location('shape_check', args.oracle)
    checker = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = checker
    spec.loader.exec_module(checker)
    slots = json.loads((HERE / 'slots.json').read_text())
    rows = []
    for name, _, folded in ARMS:
        env = dict(clean_env(), RH_FIXPOINT_STATS='1', NO_COLOR='1')
        if folded:
            env.update(FLAGS)
        cli = subprocess.run([binaries[name]['roundhouse'], 'check', '--continue', str(HERE)],
                             env=env, capture_output=True, text=True)
        (out / (name + '.check.log')).write_text(cli.stdout + cli.stderr)
        if cli.returncode not in (0, 1):
            raise RuntimeError(name + ': check failed to run; inspect the saved log')
        probe = subprocess.run([binaries[name]['settle-probe'], str(HERE)], env=env,
                               capture_output=True, text=True, check=True)
        (out / (name + '.probe.log')).write_text(probe.stderr)
        exported = json.loads(probe.stdout)
        source = ''.join('type ' + key + ' = ' + value + '\n'
                         for key, value in sorted(exported['types'].items()))
        (out / (name + '.rbs')).write_text(source)
        report = checker.check_records(checker.Grammar(source), checker.load_records(HERE / 'trace.jsonl'), slots)
        row = dict(arm=name, commit=commits[name], check_exit=cli.returncode,
                   loops=exported['loops'], records=report['records'],
                   rejected=report['records'] - report['accepted'],
                   binary_sha256={key: sha256(value) for key, value in binaries[name].items()})
        stats = [json.loads(line.split(': ', 1)[1]) for line in cli.stderr.splitlines()
                 if line.startswith('rh-fixpoint: ')]
        if stats:
            if stats[-1]['loops'] != exported['loops']:
                raise RuntimeError(name + ': CLI stats and fixpoint_rounds() disagree')
            row['stats'] = stats[-1]
        (out / (name + '.oracle.json')).write_text(json.dumps(report, indent=2) + '\n')
        rows.append(row)
        print(json.dumps(row), flush=True)
    verify = subprocess.run([binaries['sound']['roundhouse'], 'check', '--continue', str(HERE)],
                            env=dict(clean_env(), **FLAGS, RH_FIXPOINT_STATS='1', RH_FIXPOINT_VERIFY='1'),
                            capture_output=True, text=True)
    if verify.returncode not in (0, 1):
        raise RuntimeError('fixed staged verification failed to run')
    (out / 'sound.verify.log').write_text(verify.stdout + verify.stderr)
    verification = [json.loads(line.split(': ', 1)[1]) for line in verify.stderr.splitlines()
                    if line.startswith('rh-fixpoint: ')][-1]
    result = dict(condition='settle-sound-published-v1', rows=rows, verification=verification,
                  input_sha256=sha256(HERE / 'app/controllers/trees_controller.rb'),
                  trace_sha256=sha256(HERE / 'trace.jsonl'))
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
