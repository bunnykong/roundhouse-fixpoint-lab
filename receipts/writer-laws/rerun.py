#!/usr/bin/env python3
"""Rerun the writer-law selection at its published pin; analyzer policy unchanged."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
PIN = 'bf2f052ff34a240dab0cb05b1185c0e3ad571888'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, required=True, help='Must not exist.')
    parser.add_argument('--source', type=Path, help='Existing public clone; a detached worktree is created.')
    parser.add_argument('--default-suite', action='store_true', help='Also record the entire inherited default suite.')
    args = parser.parse_args()
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    source = args.source.resolve() if args.source else work / 'roundhouse'
    if not args.source:
        subprocess.run(['git', 'clone', 'https://github.com/bunnykong/roundhouse.git', str(source)], check=True)
    tree = work / 'harness'
    subprocess.run(['git', '-C', str(source), 'worktree', 'add', '--detach', str(tree), PIN], check=True)
    if args.default_suite:
        recipe = ROOT.parent / 'baseline-2026-10-10/rerun.py'
        spec = importlib.util.spec_from_file_location('baseline_fixture_recipe', recipe)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.fixtures(tree)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('RH_', 'ROUNDHOUSE_'))}
    env.update(CARGO_BUILD_JOBS='4', CARGO_TARGET_DIR=str(work / 'cargo-target'),
               RBENV_VERSION='3.4.4', RUST_TEST_THREADS='1')
    commands = [('enabled', ['cargo', 'test', '--locked', '--lib', 'writer_law_', '--', '--nocapture', '--test-threads=1']),
                ('all', ['cargo', 'test', '--locked', '--lib', 'writer_law_', '--', '--include-ignored', '--nocapture', '--test-threads=1'])]
    if args.default_suite:
        commands.append(('default-suite', ['cargo', 'test', '--locked', '--no-fail-fast', '--', '--test-threads=1']))
    receipts = []
    for name, command in commands:
        with (work / (name + '.log')).open('wb') as log:
            result = subprocess.run(command, cwd=tree, env=env, stdout=log, stderr=log)
        receipts.append(dict(selection=name, command=command, exit=result.returncode, commit=PIN,
                             base=(ROOT / 'BASE_SHA').read_text().strip(),
                             expected_exit=0 if name == 'enabled' else 101))
        (work / 'commands.json').write_text(json.dumps(receipts, indent=2) + '\n')
        if result.returncode != receipts[-1]['expected_exit']:
            raise SystemExit('Unexpected selection exit; retain ' + str(work / (name + '.log')))
    print('Fresh law outputs: ' + str(work))


if __name__ == '__main__':
    main()
