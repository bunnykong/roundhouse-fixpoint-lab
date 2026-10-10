#!/usr/bin/env python3
"""Replay the receipt, or run its three Discourse tests in a fresh measurement directory."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
PINS = json.loads((HERE / 'pins.json').read_text())
SETTINGS = json.loads((HERE / 'runtime-settings.json').read_text())
FORK_URL = 'https://github.com/bunnykong/roundhouse.git'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, *, env=None, cwd=None, log=None):
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('w') as stream:
            subprocess.run(list(map(str, command)), env=env, cwd=cwd, check=True,
                           stdout=stream, stderr=subprocess.STDOUT)
    else:
        subprocess.run(list(map(str, command)), env=env, cwd=cwd, check=True)


def clone_pin(url, destination, pin):
    run(['git', 'clone', '--no-hardlinks', '--no-checkout', url, destination])
    run(['git', '-C', destination, 'checkout', '--detach', pin])
    run(['git', '-C', destination, 'remote', 'set-url', '--push', 'origin', 'DISABLED'])


def adapter_path(supplied, out):
    if supplied:
        adapter = supplied.resolve()
    else:
        clone = out / 'adapter-source'
        clone_pin(FORK_URL, clone, PINS['public_adapter'])
        adapter = clone / PINS['public_adapter_path']
    for name, digest in read(HERE / 'adapter-files.json').items():
        if sha(adapter / name) != digest:
            raise ValueError('adapter file changed: ' + name)
    return adapter


def compare(adapter, trace, exported, output, baseline=None, log=None):
    command = [sys.executable, '-B', adapter / 'compare.py', '--lab', LAB,
               '--trace', trace, '--export', exported, '--slots', HERE / 'slots.json',
               '--output', output]
    if baseline:
        command += ['--baseline-export', baseline]
    run(command, log=log)
    return read(output)


def summarize(comparisons):
    slots, selection = read(HERE / 'slots.json'), read(HERE / 'selection.json')
    per_slot = {slot: dict(alias=alias, selection=selection[alias], settings={})
                for slot, alias in slots.items()}
    summary, observed = [], set()
    for setting in SETTINGS:
        name = setting['id']
        main, s3 = comparisons[name]['main'], comparisons[name]['s3']
        if main['no_slot'] or s3['no_slot']:
            raise ValueError('unbound runtime observation')
        for arm, result in [('main', main), ('s3', s3)]:
            stage = result['arms']['final']
            if stage['category_slots'].get('missing', 0):
                raise ValueError('missing selected static type')
            if [stage['accepted'], stage['rejected']] != setting[arm]:
                raise ValueError('membership counts changed: ' + name + ' ' + arm)
            if result['records'] != setting['observations'] or result['observed_slots'] != setting['observed_slots']:
                raise ValueError('coverage changed: ' + name)
        main_rows = {r['record_line']: r for r in main['arms']['final']['observations']}
        counts = Counter()
        for row in s3['arms']['final']['observations']:
            peer = main_rows[row['record_line']]
            if row['slot'] != peer['slot']:
                raise ValueError('paired slot differs')
            slot = row['slot']
            observed.add(slot)
            counts[slot] += 1
            per_slot[slot]['settings'].setdefault(name, []).append(dict(
                trace='traces/' + name + '.jsonl', record_line=row['record_line'],
                main='accept' if peer['accepted'] else 'reject',
                s3='accept' if row['accepted'] else 'reject',
                main_categories=peer['categories'], s3_categories=row['categories']))
        summary.append(dict(setting=name, observations=main['records'], observed_slots=main['observed_slots'],
            main=setting['main'], s3=setting['s3'], no_slot=0,
            missing_selected_types=0,
            main_accepted_with_uncertainty=main['arms']['final']['accepted_with_uncertainty'],
            s3_accepted_with_uncertainty=s3['arms']['final']['accepted_with_uncertainty']))
    union = dict(observations=sum(s['observations'] for s in summary),
                 observed_slots=len(observed), selected_slots=len(slots),
                 main=[sum(s['main'][i] for s in summary) for i in range(2)],
                 s3=[sum(s['s3'][i] for s in summary) for i in range(2)],
                 no_slot=0, missing_selected_types=0,
                 unobserved_slots=sorted(set(slots) - observed))
    if (union['observations'], union['observed_slots'], union['main'], union['s3']) != (127, 27, [127, 0], [91, 36]):
        raise ValueError('declared runtime-setting union changed')
    return dict(condition=PINS['condition'], settings=summary, union=union), per_slot


def replay(adapter, out):
    for row in read(HERE / 'recorded-files.json')['files']:
        if sha(HERE / row['file']) != row['published_sha256']:
            raise ValueError('recorded file changed: ' + row['file'])
    comparisons = {}
    for setting in SETTINGS:
        name = setting['id']
        comparisons[name] = {}
        for arm in ['main', 's3', 's3-instrumented']:
            output = out / (name + '-' + arm + '.json')
            row = compare(adapter, HERE / 'traces' / (name + '.jsonl'), HERE / 'exports' / arm,
                          output, HERE / 'exports/main' if arm != 'main' else None,
                          out / (name + '-' + arm + '.log'))
            if row != read(HERE / 'comparisons' / (name + '-' + arm + '.json')):
                raise ValueError('per-observation decisions changed: ' + name + ' ' + arm)
            comparisons[name][arm] = row
    summary, per_slot = summarize(comparisons)
    write(out / 'summary.json', summary)
    write(out / 'per-slot-decisions.json', per_slot)
    for arm in ['main', 's3']:
        repeat = compare(adapter, HERE / 'traces/P-repeat.jsonl', HERE / 'exports' / arm,
                         out / ('P-repeat-' + arm + '.json'),
                         HERE / 'exports/main' if arm == 's3' else None,
                         out / ('P-repeat-' + arm + '.log'))
        stage = repeat['arms']['final']
        if [stage['accepted'], stage['rejected']] != SETTINGS[0][arm] or repeat['observed_slots'] != 24:
            raise ValueError('primary recorder repeat changed: ' + arm)
    for filename, actual in [('summary.json', summary), ('per-slot-decisions.json', per_slot)]:
        if (HERE / filename).exists() and read(HERE / filename) != actual:
            raise ValueError('saved reduction differs: ' + filename)
    run([sys.executable, '-B', LAB / 'receipts/F17/recompute.py'], log=out / 'F17-recompute.log')
    print(json.dumps(summary, indent=2))
    print('All saved decisions match; P repeat matches; historical F17 recomputes.')


def live(adapter, work):
    version = subprocess.check_output(['ruby', '-e', 'print RUBY_VERSION'], text=True)
    if version != PINS['ruby']:
        raise ValueError('select CRuby ' + PINS['ruby'] + ' before a live run')
    # Avoid inheriting logging, analyzer or Bundler settings from another condition.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('RH_', 'ROUNDHOUSE_', 'SOUND_', 'DISCOURSE_', 'BUNDLE_', 'GEM_'))}
    if 'SOUND_DOCKER_LOCK' in os.environ:
        env['SOUND_DOCKER_LOCK'] = os.environ['SOUND_DOCKER_LOCK']
    env.update(CARGO_BUILD_JOBS='4', PYTHONDONTWRITEBYTECODE='1',
               GEM_HOME=str(work / 'gems'), BUNDLE_USER_HOME=str(work / 'tmp/bundle'),
               GEM_SPEC_CACHE=str(work / 'tmp/gem-spec-cache'),
               BUNDLE_GEMFILE=str(work / 'runtime/Gemfile'), BUNDLE_WITHOUT='development')
    for part in ['logs', 'tmp', 'runtime', 'session']:
        (work / part).mkdir(exist_ok=True)
    shutil.copytree(adapter, work / 'adapter', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    clone_pin(str(LAB), work / 'lab', PINS['lab'])
    for arm in ['main', 's3']:
        clone_pin(FORK_URL, work / arm, PINS['arms'][arm]['source'])
    app = work / 'lab/corpus/apps/discourse'
    app.parent.mkdir(parents=True, exist_ok=True)
    clone_pin('https://github.com/discourse/discourse.git', app, PINS['discourse'])
    clone_pin(str(app), work / 'runtime/discourse', PINS['discourse'])
    run(['ruby', work / 'adapter/prepare_slots.rb', app,
         work / 'lab/receipts/baseline-2026-10-10/evidence/f8-summary.json', work / 'session/discourse'],
        env=env, log=work / 'logs/selection.log')
    for name in ['selection.json', 'slots.json']:
        if (work / 'session/discourse' / name).read_bytes() != (HERE / name).read_bytes():
            raise ValueError('fresh selection changed: ' + name)
    shutil.copy2(work / 'session/discourse/instrumented-base.rb', work / 'runtime/discourse/app/jobs/base.rb')
    for name in ['Gemfile', 'Gemfile.lock']:
        text = (app / name).read_text().replace('ruby "~> 3.4"', 'ruby "~> 4.0"')
        text = text.replace('ruby 3.4.7p58', 'ruby 4.0.7p0')
        for part in ['core', 'tooling', 'converters', 'importer']:
            relative = 'migrations/' + part
            text = text.replace('path: "' + relative + '"', 'path: "' + str(app / relative) + '"')
            text = text.replace('remote: ' + relative, 'remote: ' + str(app / relative))
        (work / 'runtime' / name).write_text(text)
    # The lockfile pins Bundler and all gem versions; installation does not update it.
    run(['gem', 'install', 'bundler', '-v', '4.0.11', '--no-document'], env=env,
        log=work / 'logs/bundler.log')
    gem_bin = work / 'gems/bin'
    env['PATH'] = str(gem_bin) + os.pathsep + env['PATH']
    run([gem_bin / 'bundle', 'install', '--jobs', '4'], env=env,
        cwd=work / 'runtime/discourse', log=work / 'logs/bundle-install.log')
    run([sys.executable, '-B', work / 'adapter/build.py', '--work', work, '--roles', 'main', 's3'],
        env=env, log=work / 'logs/build.log')
    comparisons = {}
    for arm in ['main', 's3']:
        run([sys.executable, '-B', work / 'adapter/export.py', '--binary', work / ('bin/' + arm + '-sound-types'),
             '--role', arm, '--source', work / arm, '--app', app,
             '--selection', work / 'session/discourse/selection.json', '--lab', work / 'lab',
             '--output', work / 'session/discourse' / arm], env=env,
            log=work / ('logs/export-' + arm + '.log'))
    for setting in SETTINGS:
        name = setting['id']
        command = [sys.executable, '-B', work / 'adapter/docker_session.py',
                   '--work', work, '--output', work / 'session' / name]
        if setting['environment'].get('DISCOURSE_LOG_SIDEKIQ'):
            command.append('--force-logging')
        if setting['environment'].get('DISCOURSE_LOG_SIDEKIQ_INTERVAL'):
            command.append('--interval')
        command.append(setting['test'])
        run(command, env=env, log=work / ('logs/test-' + name + '.log'))
        comparisons[name] = {}
        for arm in ['main', 's3']:
            comparisons[name][arm] = compare(
                work / 'adapter', work / 'session' / name / 'trace.jsonl', work / 'session/discourse' / arm,
                work / 'session' / name / (arm + '.json'),
                work / 'session/discourse/main' if arm == 's3' else None,
                work / ('logs/compare-' + name + '-' + arm + '.log'))
    summary, per_slot = summarize(comparisons)
    write(work / 'summary.json', summary)
    write(work / 'per-slot-decisions.json', per_slot)
    print(json.dumps(summary, indent=2))
    print('Fresh runtime values are new observations; retain their own hashes and environment receipts.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['replay', 'live'], nargs='?', default='replay')
    parser.add_argument('--adapter', type=Path, help='exact checked adapter directory; otherwise fetch the pinned fork')
    parser.add_argument('--output', type=Path, help='new output directory (default: a temporary directory)')
    args = parser.parse_args()
    if args.output:
        out = args.output.resolve()
        out.mkdir(parents=True, exist_ok=False)
    else:
        out = Path(tempfile.mkdtemp(prefix='discourse-sound-trace-'))
    adapter = adapter_path(args.adapter, out)
    if args.mode == 'live':
        live(adapter, out)
    else:
        replay(adapter, out)
    print('Output: ' + str(out))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('rerun failed: ' + str(error), file=sys.stderr)
        sys.exit(2)
