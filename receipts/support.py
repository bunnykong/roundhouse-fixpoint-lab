"""Public-only receipt helpers (Python 3.9+, no third-party packages)."""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

LAB = Path(__file__).resolve().parents[1]
APPS = ('campfire', 'mastodon', 'chatwoot', 'forem', 'discourse')
S3 = dict(RH_FOLD='1', RH_FOLD_SLOTS='1', RH_FOLD_JOIN='1', RH_FOLD_TAIL='1',
          RH_BRK_ALLARMS='1', RH_SCHED='sccq')
FORK = 'https://github.com/bunnykong/roundhouse.git'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def clean_env(flags=None):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('RH_', 'ROUNDHOUSE_', 'BUNDLE_'))
           and k not in ('RUBYOPT', 'RUBYLIB', 'GEM_HOME', 'GEM_PATH', 'DYLD_INSERT_LIBRARIES')}
    env.update(NO_COLOR='1', CARGO_BUILD_JOBS='4', PYTHONDONTWRITEBYTECODE='1', RBENV_VERSION='4.0.7')
    env.update(flags or {})
    return env


def parser(fact, apps=True):
    p = argparse.ArgumentParser()
    p.add_argument('--work-dir', type=Path, default=LAB / '_work' / ('receipt-' + fact))
    p.add_argument('--source', type=Path, help='Existing Roundhouse clone; otherwise clone the public fork.')
    if apps:
        p.add_argument('--apps', nargs='+', choices=APPS, default=list(APPS))
        p.add_argument('--app-root', type=Path, default=LAB / 'corpus/apps')
    return p


def setup(args):
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    source = args.source.resolve() if args.source else work / 'roundhouse'
    if not args.source:
        subprocess.run(['git', 'clone', FORK, str(source)], check=True)
    return work, source


def build(source, work, name, revision, patches=(), exporter=None):
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', revision], text=True).strip()
    tree = work / ('source-' + name)
    subprocess.run(['git', '-C', str(source), 'worktree', 'add', '--detach', str(tree), commit], check=True)
    for patch in patches:
        subprocess.run(['git', 'apply', str(Path(patch).resolve())], cwd=tree, check=True)
    names = ['roundhouse']
    if exporter:
        dest = tree / 'src/bin/settle-probe.rs'
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(exporter, dest)
        names.append('settle-probe')
    target = Path(os.environ.get('CARGO_TARGET_DIR', work / 'cargo-target')).resolve()
    env = dict(clean_env(), CARGO_TARGET_DIR=str(target))
    command = ['cargo', 'build', '--release', '--locked']
    for binary in names:
        command += ['--bin', binary]
    print('building ' + name + ' at ' + commit, flush=True)
    with (work / ('build-' + name + '.log')).open('w') as log:
        subprocess.run(command, cwd=tree, env=env, stdout=log, stderr=log, check=True)
    binaries = {}
    for binary in names:
        dest = work / (name + '-' + binary)
        shutil.copy2(target / 'release' / binary, dest)
        binaries[binary] = str(dest)
    receipt = dict(commit=commit, patches={Path(p).name: sha(p) for p in patches},
                   exporter_sha256=sha(exporter) if exporter else None,
                   binaries={n: sha(p) for n, p in binaries.items()}, command=command,
                   rustc=subprocess.check_output(['rustc', '--version'], cwd=tree, text=True).strip())
    write(work / ('build-' + name + '.json'), receipt)
    return binaries, commit


def verify_apps(names, root):
    common = load('receipt_corpus_common', LAB / 'corpus/common.py')
    pins = {p['id']: p for p in json.loads((LAB / 'corpus/apps.json').read_text())}
    manifest = json.loads((LAB / 'receipts/app-trees.json').read_text())
    for app in names:
        path = root / app
        if not path.is_dir():
            raise RuntimeError('Missing app: run sh corpus/fetch.sh first')
        commit = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
        digest, _ = common.inventory(path)
        if commit != pins[app]['commit'] or digest != manifest[app]['tree_sha256']:
            raise RuntimeError('Changed public input: ' + app)


def scrub(value, roots=()):
    if isinstance(value, str):
        for root in sorted(map(str, roots), key=len, reverse=True):
            value = value.replace(root + '/', '')
            value = value.replace(root, '.')
        if re.search(r'/(?:Users|home|private)/', value):
            raise ValueError('unstripped local path: ' + value[:100])
        return value
    if isinstance(value, list):
        return [scrub(v, roots) for v in value]
    if isinstance(value, dict):
        return {scrub(k, roots): scrub(v, roots) for k, v in value.items()}
    return value


def seed_hook(work, seed):
    if platform.system() != 'Darwin':
        print('Native hash seed hook is macOS-only; this rerun records uncontrolled hash order.', file=sys.stderr)
        return {}
    library = work / 'hash-seed.dylib'
    if not library.exists():
        subprocess.run(['cc', '-dynamiclib', '-O2', '-std=c11',
                        str(LAB / 'receipts/hash_seed.c'), '-o', str(library)], check=True)
    return dict(DYLD_INSERT_LIBRARIES=str(library), RH_HASHSEED=str(seed))


def run_check(binary, app, flags, output):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    with (output / 'stdout.log').open('w') as so, (output / 'stderr.log').open('w') as se:
        p = subprocess.run([str(binary), 'check', '--continue', '.'], cwd=app,
                           env=clean_env(flags), stdout=so, stderr=se, timeout=1200)
    wall = time.monotonic() - started
    if p.returncode not in (0, 1):
        raise RuntimeError('check exited ' + str(p.returncode) + '; inspect stderr.log')
    lines = (output / 'stderr.log').read_text().splitlines()
    diagnostics = collections.defaultdict(collections.Counter)
    reports = collections.defaultdict(list)
    for line in lines:
        m = re.match(r'^(?:.*?:\d+:\d+:\s*)?(error|warning|note)\[([a-z_][a-z_0-9]*)\]:', line)
        if m:
            diagnostics[m[1]][m[2]] += 1
        if line.startswith('rh-') and ': {' in line:
            prefix, data = line.split(': ', 1)
            if prefix in ('rh-fixpoint', 'rh-hashseed', 'rh-warm', 'rh-warm-wall', 'rh-warm-save', 'rh-det-unresolved'):
                reports[prefix].append(json.loads(data))
    expected_reports = 2 if flags.get('RH_WARM') else 1
    if len(reports['rh-fixpoint']) != expected_reports:
        raise RuntimeError('expected ' + str(expected_reports) + ' complete fixpoint reports')
    if flags.get('RH_WARM'):
        if len(reports['rh-warm']) != 1 or reports['rh-warm'][0].get('shadow') != 'pass':
            raise RuntimeError('missing or failed mandatory cold shadow')
        warm = reports['rh-warm'][0]
        if (reports['rh-fixpoint'][0]['digest'] != warm['warm_digest']
                or reports['rh-fixpoint'][1]['digest'] != warm['cold_digest']
                or warm['warm_digest'] != warm['cold_digest']):
            raise RuntimeError('warm/shadow fixpoint reports disagree with the comparison')
    if flags.get('DYLD_INSERT_LIBRARIES'):
        if len(reports['rh-hashseed']) != 1 or reports['rh-hashseed'][0].get('calls', 0) <= 0:
            raise RuntimeError('native hash-seed hook was inactive')
    row = dict(exit_code=p.returncode, command=['roundhouse', 'check', '--continue', '.'],
               wall_seconds=wall, diagnostics=dict(diagnostics), reports=dict(reports))
    write(output / 'run.json', row)
    return row
