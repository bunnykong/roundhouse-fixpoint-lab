#!/usr/bin/env python3
"""Rerun the pinned public baseline in a fresh owned directory, serially."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parent
LAB = ROOT.parents[1]
APPS = ('campfire', 'mastodon', 'chatwoot', 'forem', 'discourse')
PINS = dict(main='c210f226346b462214866b5756b457ad53f647b1',
            staged='5716ddf368aa1df850b7d02906f91976bb8e573a',
            next='38403140379cd69759b0fe6247c6a8c4a48a37a9')
BASE = dict(RH_FOLD='0', RH_FOLD_SLOTS='0', RH_FOLD_JOIN='0', RH_FOLD_TAIL='0',
            RH_BRK_ALLARMS='0', RH_SCHED='rounds')
S3 = dict(RH_FOLD='1', RH_FOLD_SLOTS='1', RH_FOLD_JOIN='1', RH_FOLD_TAIL='1',
          RH_BRK_ALLARMS='1', RH_SCHED='sccq')
sys.path.insert(0, str(LAB / 'corpus'))
from common import inventory
from metrics import Reducer


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith(('RH_', 'ROUNDHOUSE_', 'PROBE_'))}
    env.update(CARGO_BUILD_JOBS='4', RBENV_VERSION='4.0.7')
    return env


def fixtures(tree):
    # These generated Rails fixtures are archived byte for byte, including executable modes.
    with tarfile.open(ROOT / 'generated-fixtures.tar.gz', 'r:gz') as archive:
        for entry in archive.getmembers():
            name = Path(entry.name)
            if not entry.isfile() or name.is_absolute() or '..' in name.parts:
                raise ValueError('Unexpected fixture archive entry')
            path = tree / 'fixtures' / name
            if path.exists():
                data = archive.extractfile(entry).read()
                if path.read_bytes() != data:
                    raise ValueError('Existing fixture differs: ' + entry.name)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.extractfile(entry).read())
                path.chmod(entry.mode)
    pins = json.loads((ROOT / 'evidence/emission-inputs.json').read_text())
    for row in pins['fixtures']:
        digest, files = inventory(tree / 'fixtures' / row['fixture'])
        if digest != row['digest'] or len(files) != row['files']:
            raise ValueError('Fixture pin differs: ' + row['fixture'])


def build(work, source, label, env):
    tree = work / 'sources' / label
    tree.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', '-C', str(source), 'worktree', 'add', '--detach', str(tree), PINS[label]], check=True)
    target = work / 'cargo-target'
    build_env = dict(env, CARGO_TARGET_DIR=str(target), RBENV_VERSION='3.4.4')
    command = ['cargo', 'build', '--release', '--locked', '--bin', 'roundhouse']
    with (work / ('build-' + label + '.log')).open('wb') as log:
        subprocess.run(command, cwd=tree, env=build_env, stdout=log, stderr=log, check=True)
    binary = work / 'binaries' / ('roundhouse-' + label)
    binary.parent.mkdir(exist_ok=True)
    shutil.copy2(target / 'release/roundhouse', binary)
    write(work / ('build-' + label + '.json'), dict(commit=PINS[label], command=command,
          binary_sha256=sha(binary), tree=subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=tree, text=True).strip()))
    return tree, binary, build_env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, required=True, help='Must not exist; outputs are a new condition.')
    parser.add_argument('--source', type=Path, help='Existing public Roundhouse clone, only used for detached worktrees.')
    parser.add_argument('--app-root', type=Path, default=LAB / 'corpus/apps')
    parser.add_argument('--skip-emission', action='store_true')
    parser.add_argument('--suites', action='store_true', help='Also run default lib/full selections, with Ruby 3.4.4.')
    args = parser.parse_args()
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    source = args.source.resolve() if args.source else work / 'roundhouse'
    env = environment()
    if not args.source:
        subprocess.run(['git', 'clone', 'https://github.com/bunnykong/roundhouse.git', str(source)], check=True)
    app_root = args.app_root.resolve()
    public = {r['id']: r for r in json.loads((LAB / 'corpus/apps.json').read_text())}
    inputs = {r['id']: r for r in json.loads((ROOT / 'evidence/inputs.json').read_text())['apps']}
    for app in APPS:
        path = app_root / app
        head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
        digest, files = inventory(path)
        if head != public[app]['commit'] or head != inputs[app]['head'] or digest != inputs[app]['digest']:
            raise ValueError('Changed public input: ' + app)
        if len(files) != inputs[app]['files']:
            raise ValueError('Changed input inventory: ' + app)
    write(work / 'condition.json', dict(recorded_condition='fixpoint-current-main-20261010-c210f226',
          rerun_started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), pins=PINS,
          note='Fresh rerun outputs; historical timings and host binary hashes are not expectations.'))
    binaries = {}
    emissions = {}
    for label in PINS:
        tree, binary, build_env = build(work, source, label, env)
        binaries[label] = binary
        if not args.skip_emission or args.suites:
            fixtures(tree)
        if not args.skip_emission:
            harness = tree / 'src/bin/astra_emit_all.rs'
            if harness.exists():
                raise ValueError('Harness path already exists')
            shutil.copyfile(ROOT / 'emit_all.rs', harness)
            try:
                subprocess.run(['cargo', 'build', '--release', '--locked', '--bin', 'astra_emit_all'],
                               cwd=tree, env=build_env, check=True)
            finally:
                harness.unlink()
            output = work / 'emission' / label
            output.mkdir(parents=True)
            with (output / 'pairs.jsonl').open('wb') as stdout, (output / 'stderr.log').open('wb') as stderr:
                subprocess.run([str(work / 'cargo-target/release/astra_emit_all'), str(output / 'tree')],
                               cwd=tree, env=build_env, stdout=stdout, stderr=stderr, check=True)
            emissions[label] = {str(p.relative_to(output / 'tree')): sha(p)
                                for p in (output / 'tree').rglob('*') if p.is_file()}
            write(output / 'manifest.json', emissions[label])
            pairs = [json.loads(line) for line in (output / 'pairs.jsonl').read_text().splitlines()]
            if len(pairs) != 105 or any('error' in r for r in pairs):
                raise ValueError('Emission selection incomplete')
        if args.suites:
            for selection, command in [('lib', ['cargo', 'test', '--locked', '--lib']),
                                       ('suite', ['cargo', 'test', '--locked', '--no-fail-fast'])]:
                with (work / (label + '-' + selection + '.log')).open('wb') as log:
                    result = subprocess.run(command, cwd=tree, env=build_env, stdout=log, stderr=log)
                write(work / (label + '-' + selection + '.json'), dict(command=command, exit=result.returncode))
        for app in APPS:
            output = work / 'runs/native' / label / app
            output.mkdir(parents=True)
            command = [str(binary), 'check', '--continue', '.']
            start = time.monotonic()
            with (output / 'stdout.txt').open('wb') as stdout, (output / 'stderr.txt').open('wb') as stderr:
                result = subprocess.run(command, cwd=app_root / app, env=env, stdout=stdout, stderr=stderr, timeout=900)
            reducer = Reducer()
            for name in ('stdout.txt', 'stderr.txt'):
                for line in (output / name).read_text().splitlines():
                    reducer.feed(line)
            write(output / 'receipt.json', dict(command=command, cwd=str(app_root / app), flags={},
                  commit=PINS[label], binary_sha256=sha(binary), input=inputs[app], exit=result.returncode,
                  elapsed_seconds=time.monotonic() - start, metrics=reducer.data()))
            if result.returncode not in (0, 1) or not reducer.data()['diagnostics_complete']:
                raise ValueError('Native analysis incomplete')
    if emissions and not emissions['main'] == emissions['staged'] == emissions['next']:
        raise ValueError('Flags-off emission differs; keep all rerun outputs')
    # Preserve the source-level F8 inspection separately from aggregate precision.
    tree = work / 'sources/next'
    subprocess.run(['cargo', 'build', '--release', '--locked', '--bin', 'dump_ir'],
                   cwd=tree, env=dict(env, CARGO_TARGET_DIR=str(work / 'cargo-target')), check=True)
    diagnostic = work / 'binaries/dump_ir-next'
    shutil.copy2(work / 'cargo-target/release/dump_ir', diagnostic)
    for mode in ('base', 's3'):
        output = work / 'runs/f8' / mode
        output.mkdir(parents=True)
        flags = dict(BASE if mode == 'base' else S3, RH_FIXPOINT_VERIFY='0')
        command = [str(diagnostic), str(app_root / 'discourse'), '--select',
                   'Jobs::Base::JobInstrumenter', '--format', 'json']
        with (output / 'class-ir.txt').open('wb') as stdout, (output / 'stderr.txt').open('wb') as stderr:
            subprocess.run(command, cwd=output, env=dict(env, ROUNDHOUSE_INGEST_SURVEY='1', **flags),
                           stdout=stdout, stderr=stderr, check=True, timeout=900)
        text = (output / 'class-ir.txt').read_text()
        data = json.loads(text[text.index('{'):])
        write(output / 'class-ir.json', data)
        ivars = []

        def visit(value, path):
            if isinstance(value, dict):
                node = value.get('node')
                if isinstance(node, dict) and node.get('kind') == 'ivar' and node.get('name', '').lstrip('@') == 'data':
                    ivars.append(dict(path=path, span=value.get('span'), ty=value.get('ty')))
                for key, child in value.items():
                    visit(child, path + '.' + key)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, path + '[' + str(index) + ']')

        visit(data, 'class')
        write(output / 'data-ivar-types.json', ivars)
        write(output / 'receipt.json', dict(command=command, flags=flags, commit=PINS['next'],
              binary_sha256=sha(diagnostic), input=inputs['discourse'], ROUNDHOUSE_INGEST_SURVEY='1'))
    for app in APPS:
        for mode in ('base', 's3'):
            for check, seed in [('precision', None), ('schedule', None), ('schedule', '1'),
                                ('schedule', '2'), ('repeat', None)]:
                flags = dict(BASE if mode == 'base' else S3, RH_FIXPOINT_VERIFY='1',
                             RH_FIXPOINT_DIGEST='1', RH_FIXPOINT_STATS='1', RH_PRECISION_CENSUS='1')
                extra = ['RH_PRECISION_CENSUS=1']
                if check == 'precision':
                    flags['RH_FIXPOINT_VERIFY'] = '0'
                    extra.append('RH_FIXPOINT_VERIFY=0')
                else:
                    flags.update(RH_ERRGATE='1', RH_PUBLIC_INPUT='1')
                    extra += ['RH_ERRGATE=1', 'RH_PUBLIC_INPUT=1']
                run_env = dict(env, RH_BIN=str(binaries['next']), APPS=str(app_root))
                if mode == 'base':
                    run_env['PROBE_BASE'] = '1'
                if seed:
                    flags['RH_SHUFFLE'] = seed
                    run_env['RH_SHUFFLE'] = seed
                output = work / 'runs/probe' / app / mode / (check + '-' + (seed or 'unset'))
                output.mkdir(parents=True)
                command = ['bash', str(ROOT / 'probe'), app] + extra
                with (output / 'report.json').open('wb') as stdout, (output / 'driver.stderr').open('wb') as stderr:
                    subprocess.run(command, cwd=output, env=run_env, stdout=stdout, stderr=stderr, timeout=900, check=True)
                write(output / 'receipt.json', dict(command=command, flags=flags, probe_base=mode == 'base',
                      commit=PINS['next'], binary_sha256=sha(binaries['next']), probe_sha256=sha(ROOT / 'probe'), input=inputs[app]))
        for seed in ('unset', '1', '2'):
            paths = [str(work / 'runs/probe' / app / mode / ('schedule-' + seed) / ('probe-' + app + '.stderr'))
                     for mode in ('base', 's3')]
            command = [sys.executable, str(ROOT / 'errgate.py')] + paths
            text = subprocess.check_output(command, text=True)
            output = work / 'runs/probe' / app / ('errgate-' + seed + '.txt')
            output.write_text(text)
            write(output.with_suffix('.json'), dict(command=command, summary=json.loads(text.splitlines()[-1].split(': ', 1)[1])))
        print('completed ' + app, flush=True)
    print('Fresh public outputs: ' + str(work))


if __name__ == '__main__':
    main()
