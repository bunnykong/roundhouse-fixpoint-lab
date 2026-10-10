#!/usr/bin/env python3
"""Replay the frozen public edits with the exact historical warm-v1 source patch."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s

HERE = Path(__file__).resolve().parent


def observe(binary, app, flags, output):
    output.mkdir(parents=True)
    command = [str(binary), 'check', '--continue', '.']
    with (output / 'stdout.log').open('w') as so, (output / 'stderr.log').open('w') as se:
        result = subprocess.run(command, cwd=app, env=s.clean_env(flags), stdout=so, stderr=se, timeout=1200)
    reports = {}
    for line in (output / 'stderr.log').read_text().splitlines():
        if line.startswith(('rh-fixpoint: {', 'rh-warm: {')):
            label, data = line.split(': ', 1)
            reports.setdefault(label, []).append(json.loads(data))
    assert len(reports.get('rh-warm', [])) == 1, 'missing mandatory cold shadow'
    warm = reports['rh-warm'][0]
    assert result.returncode in (0, 1, 3)
    assert (result.returncode == 3) == (warm['shadow'] == 'fail')
    return dict(exit_code=result.returncode, command=['roundhouse', 'check', '--continue', '.'], reports=reports)


def main():
    parser = s.parser('cache-guards')
    parser.set_defaults(apps=['mastodon', 'discourse'])
    parser.add_argument('--edit', action='append', choices=['boolean', 'return-type', 'withdraw-read'])
    args = parser.parse_args()
    if set(args.apps) - {'mastodon', 'discourse'}:
        parser.error('the edit suite contains only Mastodon and Discourse')
    work, source = s.setup(args)
    s.verify_apps(args.apps, args.app_root.resolve())
    condition = json.loads((HERE / 'condition.json').read_text())
    assert s.sha(HERE / 'warm-v1.patch') == condition['v1_patch_sha256']
    binaries, _ = s.build(source, work, 'warm-v1', condition['base'], patches=[HERE / 'warm-v1.patch'])
    tree = work / 'source-warm-v1'
    subprocess.run(['git', 'add', '-A'], cwd=tree, check=True)
    actual = subprocess.check_output(['git', 'write-tree'], cwd=tree, text=True).strip()
    assert actual == condition['v1_tree'], 'source patch changed the recorded tree'
    binary = Path(binaries['roundhouse'])
    frozen = json.loads((HERE / 'edits.json').read_text())['cases']
    rows = []
    for name in args.apps:
        app = work / 'apps' / name
        app.parent.mkdir(exist_ok=True)
        shutil.copytree(args.app_root.resolve() / name, app, symlinks=True, ignore=shutil.ignore_patterns('.git'))
        seed = work / 'caches' / (name + '-seed')
        seed.mkdir(parents=True)
        flags = dict(s.S3, RH_FIXPOINT_DIGEST='1', RH_WARM_SHADOW='1', RH_WARM=str(seed))
        row = observe(binary, app, flags, work / 'runs' / (name + '-seed'))
        assert row['reports']['rh-warm'][0]['shadow'] == 'pass'
        rows.append(dict(label=name + '-seed', **row))
        for entry in frozen:
            if entry['app'] != name or (args.edit and entry['kind'] not in args.edit):
                continue
            path = app / entry['file']
            original = path.read_bytes()
            assert s.sha(path) == entry['original_file_sha256']
            label = name + '-' + entry['kind']
            cache = work / 'caches' / label
            cache.mkdir()
            shutil.copy2(seed / 'evaluations.json', cache / 'evaluations.json')
            path.write_bytes(original[:entry['start']] + entry['replacement'].encode() + original[entry['end']:])
            try:
                assert s.sha(path) == entry['edited_file_sha256']
                row = observe(binary, app, dict(flags, RH_WARM=str(cache)), work / 'runs' / label)
                rows.append(dict(label=label, **row))
                s.write(work / 'observations.json', rows)
                print(json.dumps(dict(label=label, shadow=row['reports']['rh-warm'][0]['shadow'])), flush=True)
            finally:
                path.write_bytes(original)
                shutil.rmtree(cache)
        shutil.rmtree(seed)
    s.write(work / 'observations.json', rows)


if __name__ == '__main__':
    main()
