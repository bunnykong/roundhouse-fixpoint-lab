#!/usr/bin/env python3
"""One timed cold/warm pair per frozen public edit; the cold shadow is mandatory."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s

HERE = Path(__file__).resolve().parent
REVISION = '990137f742397a0aecc7efd14869f39c6412ba55'


def main():
    p = s.parser('F15')
    p.set_defaults(apps=['mastodon', 'discourse'])
    p.add_argument('--edit', action='append', choices=['boolean', 'return-type', 'withdraw-read'])
    args = p.parse_args()
    if set(args.apps) - {'mastodon', 'discourse'}:
        p.error('the frozen edit suite contains only Mastodon and Discourse')
    work, source = s.setup(args)
    s.verify_apps(args.apps, args.app_root.resolve())
    ruby_env = s.clean_env()
    ruby = subprocess.check_output(['ruby', '-e', 'print RUBY_ENGINE, " ", RUBY_VERSION'],
                                   env=ruby_env, text=True)
    if ruby != 'ruby 4.0.7':
        raise RuntimeError('Use CRuby 4.0.7; found ' + ruby)
    binaries, commit = s.build(source, work, 'warm', REVISION)
    binary = Path(binaries['roundhouse'])
    frozen = json.loads((HERE / 'edits.json').read_text())['cases']
    flags = dict(s.S3, RH_FIXPOINT_DIGEST='1')
    raw, pairs = [], []
    common = s.load('warm_receipt_corpus_common', s.LAB / 'corpus/common.py')
    for app_name in args.apps:
        app = work / 'apps' / app_name
        app.parent.mkdir(exist_ok=True)
        shutil.copytree(args.app_root.resolve() / app_name, app, symlinks=True,
                        ignore=shutil.ignore_patterns('.git'))
        seed = work / 'caches' / (app_name + '-seed')
        seed.mkdir(parents=True)
        row = s.run_check(binary, app, dict(flags, RH_WARM=str(seed), RH_WARM_SHADOW='1'),
                          work / 'runs' / (app_name + '-seed'))
        if row['reports']['rh-warm'][0]['shadow'] != 'pass':
            raise RuntimeError('seed disagrees with cold shadow')
        raw.append(dict(label=app_name + '-seed', **row))
        for entry in frozen:
            if entry['app'] != app_name or (args.edit and entry['kind'] not in args.edit):
                continue
            label = app_name + '-' + entry['kind']
            path = app / entry['file']
            original = path.read_bytes()
            if s.sha(path) != entry['original_file_sha256']:
                raise RuntimeError('changed edit input: ' + entry['file'])
            changed = original[:entry['start']] + entry['replacement'].encode() + original[entry['end']:]
            cache = work / 'caches' / label
            cache.mkdir()
            path.write_bytes(changed)
            try:
                if s.sha(path) != entry['edited_file_sha256']:
                    raise RuntimeError('edited file differs from frozen suite')
                digest, _ = common.inventory(app)
                if digest != entry['edited_tree_sha256']:
                    raise RuntimeError('edited tree differs from frozen suite')
                subprocess.run(['ruby', '-c', str(path)], env=ruby_env, check=True, stdout=subprocess.DEVNULL)
                warm_flags = dict(flags, RH_WARM=str(cache), RH_WARM_SHADOW='1')
                shutil.copy2(seed / 'evaluations.json', cache / 'evaluations.json')
                correctness = s.run_check(binary, app, warm_flags, work / 'runs' / (label + '-correctness'))
                raw.append(dict(label=label + '-correctness', **correctness))
                if correctness['reports']['rh-warm'][0]['shadow'] != 'pass':
                    raise RuntimeError('untimed shadow mismatch')
                shutil.copy2(seed / 'evaluations.json', cache / 'evaluations.json')
                cold = s.run_check(binary, app, flags, work / 'runs' / (label + '-cold'))
                warm = s.run_check(binary, app, dict(warm_flags, RH_WARM_TIMINGS='1'),
                                   work / 'runs' / (label + '-warm'))
                wr = warm['reports']['rh-warm'][0]
                warm_wall = warm['reports']['rh-warm-wall'][0]
                matches = wr['shadow'] == 'pass' and wr['warm_digest'] == wr['cold_digest']
                matches = matches and wr['evaluations']['loaded'] > 0
                matches = matches and wr['warm_digest'] == cold['reports']['rh-fixpoint'][0]['digest']
                diagnostics_match = warm['diagnostics'] == cold['diagnostics']
                pair = dict(app=app_name, edit=entry['kind'], cold_wall_seconds=cold['wall_seconds'],
                            warm_check_excluding_shadow_seconds=warm_wall['check_excluding_shadow_seconds'],
                            full_warm_wall_seconds=warm['wall_seconds'], shadow_matches=matches,
                            diagnostic_kinds_equal=diagnostics_match,
                            ratio=warm_wall['check_excluding_shadow_seconds'] / cold['wall_seconds'])
                pairs.append(pair)
                raw.extend([dict(label=label + '-cold', **cold), dict(label=label + '-warm', **warm)])
                s.write(work / 'runs.json', raw)
                s.write(work / 'results.json', dict(commit=commit, pairs=pairs, condition='sol-warm-public-edits-v1'))
                print(json.dumps(pair), flush=True)
                if not matches or not diagnostics_match:
                    raise RuntimeError('edited warm check differs from cold')
            finally:
                path.write_bytes(original)
                shutil.rmtree(cache)
        shutil.rmtree(seed)
    s.verify_apps(args.apps, args.app_root.resolve())


if __name__ == '__main__':
    main()
