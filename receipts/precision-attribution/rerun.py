#!/usr/bin/env python3
"""Build the pinned public expression census and repeat pairing and switch controls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s

HERE = Path(__file__).resolve().parent
B = dict(RH_BRK_ALLARMS='1', RH_FOLD_JOIN='1')
D = dict(B, RH_FOLD='1', RH_FOLD_SLOTS='1', RH_FOLD_TAIL='1')
ARMS = {'main': {}, 'S3': s.S3, 'S2b': B, 'S2c': D,
        'allarms-only': {'RH_BRK_ALLARMS': '1'}, 'join-only': {'RH_FOLD_JOIN': '1'},
        'S3-no-allarms': {k: v for k, v in s.S3.items() if k != 'RH_BRK_ALLARMS'},
        'S3-no-join': {k: v for k, v in s.S3.items() if k != 'RH_FOLD_JOIN'},
        'S3-no-slots': {k: v for k, v in s.S3.items() if k != 'RH_FOLD_SLOTS'},
        'S3-no-tail': {k: v for k, v in s.S3.items() if k != 'RH_FOLD_TAIL'}}


def main():
    parser = s.parser('precision-attribution')
    parser.add_argument('--arms', nargs='+', choices=list(ARMS), default=['main', 'S3'])
    args = parser.parse_args()
    work, source = s.setup(args)
    s.verify_apps(args.apps, args.app_root.resolve())
    condition = json.loads((HERE / 'condition.json').read_text())
    binaries = {}
    for variant in sorted({'main' if arm == 'main' else 'staged' for arm in args.arms}):
        revision = condition['main' if variant == 'main' else 'staged']
        tree = work / ('source-' + variant)
        patch_root = s.LAB / 'patches/precision-census' / variant
        subprocess.run(['git', '-C', str(source), 'worktree', 'add', '--detach', str(tree), revision], check=True)
        subprocess.run(['git', 'apply', str(patch_root / 'tracked.patch')], cwd=tree, check=True)
        shutil.copyfile(patch_root / 'precdiff_probe.rs', tree / 'src/analyze/precdiff_probe.rs')
        helper = work / ('helper-' + variant)
        helper.mkdir()
        for name in ['prec_census.rs', 'inventory.rs', 'kind.rs']:
            shutil.copyfile(patch_root / name, helper / name)
        manifest = '''[package]
name = "public_precision_census"
version = "0.0.0"
edition = "2021"
[[bin]]
name = "prec-census"
path = "prec_census.rs"
[dependencies]
roundhouse = { path = SOURCE }
serde_json = "1"
'''.replace('SOURCE', json.dumps(str(tree)))
        (helper / 'Cargo.toml').write_text(manifest)
        shutil.copyfile(tree / 'Cargo.lock', helper / 'Cargo.lock')
        target = Path(os.environ.get('CARGO_TARGET_DIR', work / 'target')).resolve()
        command = ['cargo', 'build', '--release', '--manifest-path', str(helper / 'Cargo.toml')]
        with (work / ('build-' + variant + '.log')).open('w') as log:
            subprocess.run(command, cwd=tree, env=dict(s.clean_env(), CARGO_TARGET_DIR=str(target)),
                           stdout=log, stderr=log, check=True)
        binary = work / ('census-' + variant)
        shutil.copyfile(target / 'release/prec-census', binary)
        binary.chmod(0o755)
        binaries[variant] = binary
        s.write(work / ('build-' + variant + '.json'), dict(commit=revision, binary_sha256=s.sha(binary),
                patch_sha256=s.sha(patch_root / 'tracked.patch'), command=['cargo', 'build', '--release']))
    rows = []
    for app in args.apps:
        for arm in args.arms:
            dest = work / 'census' / app / arm
            dest.mkdir(parents=True)
            variant = 'main' if arm == 'main' else 'staged'
            flags = dict(ARMS[arm], RH_PRECDIFF_ROWS=str(dest / 'rows.jsonl'), RH_PRECDIFF_TRACE='1')
            result = subprocess.run([str(binaries[variant]), 'check', '--continue', '.'],
                                    cwd=args.app_root.resolve() / app, env=s.clean_env(flags),
                                    capture_output=True, text=True, timeout=1200)
            counts = [json.loads(line[len('rh-gate: '):]) for line in result.stderr.splitlines()
                      if line.startswith('rh-gate: ')]
            assert result.returncode == 0 and len(counts) == 1
            row = dict(app=app, arm=arm, census=counts[0], flags=ARMS[arm],
                       commit=condition['main' if variant == 'main' else 'staged'])
            s.write(dest / 'counts.json', row)
            rows.append(row)
            print(json.dumps(row), flush=True)
    s.write(work / 'counts.json', rows)
    if {'main', 'S3'} <= set(args.arms):
        subprocess.run([sys.executable, '-B', str(HERE / 'diff_rows.py'), str(work / 'census')], check=True)


if __name__ == '__main__':
    main()
