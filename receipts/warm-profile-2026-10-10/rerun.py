#!/usr/bin/env python3
"""Rerun the pinned six-edit warm profile; new runs get a separate condition."""
import argparse
import collections
import fcntl
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
RECEIPT = Path(__file__).resolve().parent
LAB = RECEIPT.parents[1]
PINS = json.loads((RECEIPT / 'pins.json').read_text())
CONDITION = None
S3 = dict(RH_FOLD='1', RH_FOLD_SLOTS='1', RH_FOLD_JOIN='1', RH_FOLD_TAIL='1',
          RH_BRK_ALLARMS='1', RH_SCHED='sccq', RH_FIXPOINT_DIGEST='1')

def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

COMMON = load('warm_port_corpus', LAB / 'corpus/common.py')

def environment(flags):
    env = {k:v for k,v in os.environ.items() if not k.startswith(('RH_', 'ROUNDHOUSE_', 'BUNDLE_'))
           and k not in ('GEM_HOME', 'GEM_PATH', 'RUBYOPT', 'RUBYLIB', 'DYLD_INSERT_LIBRARIES')}
    env.update(flags, NO_COLOR='1', RBENV_VERSION='4.0.7', ROUNDHOUSE_TIMINGS='1')
    return env

def check(binary, app, flags, output):
    output.mkdir(parents=True, exist_ok=False)
    command = [str(binary), 'check', '--continue', '.']
    env = environment(flags)
    start_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    timeout = 1800
    if os.environ.get('PROFILE_STOP_UTC'):
        deadline = datetime.datetime.fromisoformat(os.environ['PROFILE_STOP_UTC'])
        remaining = (deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        if remaining <= 0:
            raise RuntimeError('The task time limit has been reached')
        timeout = min(timeout,remaining)
    start = time.monotonic()
    with (output/'stdout.log').open('w') as out, (output/'stderr.log').open('w') as err:
        completed = subprocess.run(command, cwd=app, env=env, stdout=out, stderr=err, timeout=timeout)
    seconds = time.monotonic()-start
    reports = collections.defaultdict(list)
    diagnostics = collections.defaultdict(collections.Counter)
    contents = []
    timings = []
    summaries = []
    for line in (output/'stderr.log').read_text().splitlines():
        if line.startswith('rh-') and ': {' in line:
            prefix, data = line.split(': ', 1)
            reports[prefix].append(json.loads(data))
        match = re.match(r'^(?:.*?:\d+:\d+:\s*)?(error|warning|note)\[([a-z_][a-z_0-9]*)\]:', line)
        if match:
            diagnostics[match[1]][match[2]] += 1
            contents.append(line)
        if line.startswith('roundhouse-check: ') and ' — ' in line:
            summaries.append(line.split(' — ', 1)[1])
        match = re.match(r'^roundhouse-timing: (.*): ([0-9.]+)s \(peak rss (\d+) MB\)$', line)
        if match:
            timings.append(dict(phase=match[1], seconds=float(match[2]), peak_rss_mb=int(match[3])))
    row = dict(exit=completed.returncode, command=command, cwd=str(app), flags=flags,
               condition=CONDITION, binary_sha256=sha(binary), started_utc=start_utc,
               timeout_seconds=timeout,
               finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               wall_seconds=seconds, reports=dict(reports), diagnostics=dict(diagnostics),
               diagnostic_content_sha256=hashlib.sha256('\n'.join(sorted(contents)).encode()).hexdigest(),
               summaries=summaries, timings=timings,
               peak_rss_mb=max((t['peak_rss_mb'] for t in timings), default=None))
    write(output/'run.json', row)
    if row['exit'] not in (0,1,3):
        raise RuntimeError('check did not complete: '+str(output))
    expected = 2 if 'RH_WARM' in flags else 1
    assert len(reports['rh-fixpoint']) == expected, str(output)
    if expected == 2:
        assert len(reports['rh-warm']) == 1, str(output)
    return row

def shadow_match(row):
    report = row['reports']['rh-warm'][0]
    fp = row['reports']['rh-fixpoint']
    return (row['exit'] in (0,1) and report['shadow'] == 'pass'
            and report['first_difference'] is None
            and fp[0]['entries'] == fp[1]['entries']
            and fp[0]['digest'] == report['warm_digest'] == report['cold_digest'] == fp[1]['digest'])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, help='Use a prebuilt binary stamped with the pinned commit')
    parser.add_argument('--source', type=Path, help='Use an existing clean source checkout at the pin')
    parser.add_argument('--condition', help='Label this new run independently of the recorded profile')
    parser.add_argument('--lock', type=Path, default=LAB/'_work/analysis.lock')
    parser.add_argument('--apps', type=Path, default=LAB/'corpus/apps')
    parser.add_argument('--work-dir', type=Path, default=LAB/'_work'/('warm-profile-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')))
    parser.add_argument('--app', action='append', choices=('mastodon','discourse'))
    parser.add_argument('--edit', action='append', choices=('boolean','return-type','withdraw-read'))
    args = parser.parse_args()
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    global CONDITION
    CONDITION = args.condition or ('warm-profile-rerun-' + PINS['recorded_commit'][:8] + '-'
                                  + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    assert CONDITION != PINS['condition'], 'A rerun must have its own condition'
    args.lock.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = args.lock.open('a')
    print('Waiting for the shared analysis lock', flush=True)
    fcntl.flock(lock_handle, fcntl.LOCK_EX)
    if args.binary:
        binary = args.binary.resolve()
    else:
        source = args.source.resolve() if args.source else work/'source'
        if not args.source:
            subprocess.run(['git', 'clone', '--no-checkout',
                            'https://github.com/bunnykong/roundhouse.git', str(source)], check=True)
            subprocess.run(['git', '-C', str(source), 'checkout', '--detach',
                            PINS['recorded_commit']], check=True)
        head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        tree = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD^{tree}'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
        assert head == PINS['recorded_commit'] and tree == PINS['source_tree'] and not dirty
        target = work/'target'
        build_env = environment({})
        build_env.update(CARGO_BUILD_JOBS='4', CARGO_INCREMENTAL='0', CARGO_TARGET_DIR=str(target))
        command = ['cargo', '+1.98.1', 'build', '--release', '--locked', '--bin', 'roundhouse']
        with (work/'build.log').open('w') as log:
            subprocess.run(command, cwd=source, env=build_env, stdout=log, stderr=subprocess.STDOUT, check=True)
        binary = work/'roundhouse'
        shutil.copy2(target/'release/roundhouse', binary)
        write(work/'build.json', dict(commit=head, tree=tree, command=command,
              jobs=4, binary_sha256=sha(binary), condition=CONDITION))
    version = subprocess.check_output([str(binary), '--version'], text=True).strip()
    assert PINS['recorded_commit'][:8] in version, version
    frozen = json.loads((RECEIPT/'edits.json').read_text())
    write(work/'inputs.json', dict(frozen, profile_condition=CONDITION))
    write(work/'environment.json', dict(condition=CONDITION, binary_version=version,
          binary_sha256=sha(binary), command=['check', '--continue', '.'],
          flags=S3, app_ruby='4.0.7', lock=str(args.lock.resolve())))
    version = subprocess.check_output(['ruby','-e','require "prism"; print RUBY_ENGINE, " ", RUBY_VERSION'],
                                     env=environment({}), text=True)
    assert version == 'ruby 4.0.7', version
    pairs, rows, inputs = [], [], {}
    for name in args.app or ('mastodon','discourse'):
        source = args.apps.resolve()/name
        entries = [e for e in frozen['cases'] if e['app'] == name and (not args.edit or e['kind'] in args.edit)]
        assert entries
        pin = entries[0]
        original_tree, files = COMMON.inventory(source)
        git_metadata = (source/'.git').exists()
        commit = (subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
                  if git_metadata else None)
        assert original_tree == pin['input_tree_sha256']
        assert not git_metadata or commit == pin['input_commit']
        inputs[name] = dict(source=str(source), tree_sha256=original_tree, files=len(files),
                           git_metadata=git_metadata, observed_commit=commit,
                           frozen_commit=pin['input_commit'])
        write(work/'app-inputs.json', inputs)
        app = work/'apps'/name
        app.parent.mkdir(exist_ok=True)
        shutil.copytree(source,app,symlinks=True,ignore=shutil.ignore_patterns('.git'))
        seed = work/'caches'/(name+'-seed')
        seed.mkdir(parents=True)
        print('Seeding '+name,flush=True)
        seed_row = check(binary,app,dict(S3,RH_WARM=str(seed),RH_WARM_SHADOW='1',RH_WARM_TIMINGS='1'),
                         work/'runs'/(name+'-seed'))
        rows.append(dict(label=name+'-seed',**seed_row))
        write(work/'runs.json',rows)
        assert shadow_match(seed_row), 'seed cold-shadow mismatch: '+name
        seed_sha = sha(seed/'evaluations.json')
        seed_bytes = (seed/'evaluations.json').stat().st_size
        for entry in entries:
            label = name+'-'+entry['kind']
            path = app/entry['file']
            original = path.read_bytes()
            assert sha(path) == entry['original_file_sha256']
            assert original[entry['start']:entry['end']].decode() == entry['old_body']
            changed = original[:entry['start']] + entry['replacement'].encode() + original[entry['end']:]
            cache = work/'caches'/label
            cache.mkdir()
            path.write_bytes(changed)
            try:
                assert sha(path) == entry['edited_file_sha256']
                assert COMMON.inventory(app)[0] == entry['edited_tree_sha256']
                subprocess.run(['ruby','-c',str(path)],env=environment({}),stdout=subprocess.DEVNULL,check=True)
                flags = dict(S3,RH_WARM=str(cache),RH_WARM_SHADOW='1',RH_WARM_TIMINGS='1')
                print('Correctness '+label,flush=True)
                shutil.copy2(seed/'evaluations.json',cache/'evaluations.json')
                correctness = check(binary,app,flags,work/'runs'/(label+'-correctness'))
                rows.append(dict(label=label+'-correctness',**correctness))
                write(work/'runs.json',rows)
                print('Cold profile '+label,flush=True)
                cold = check(binary,app,S3,work/'runs'/(label+'-cold'))
                rows.append(dict(label=label+'-cold',**cold))
                shutil.copy2(seed/'evaluations.json',cache/'evaluations.json')
                assert sha(cache/'evaluations.json') == seed_sha
                print('Warm profile '+label,flush=True)
                warm = check(binary,app,flags,work/'runs'/(label+'-warm'))
                rows.append(dict(label=label+'-warm',**warm))
                report = warm['reports']['rh-warm'][0]
                match = (shadow_match(warm) and shadow_match(correctness)
                         and cold['exit'] == warm['exit'] == correctness['exit']
                         and report['evaluations']['loaded'] > 0
                         and report['warm_digest'] == cold['reports']['rh-fixpoint'][0]['digest']
                         and warm['reports']['rh-fixpoint'][0]['entries'] == cold['reports']['rh-fixpoint'][0]['entries']
                         and correctness['reports']['rh-warm'][0]['warm_digest'] == report['warm_digest']
                         and cold['diagnostics'] == warm['diagnostics'] == correctness['diagnostics']
                         and cold['diagnostic_content_sha256'] == warm['diagnostic_content_sha256']
                             == correctness['diagnostic_content_sha256']
                         and cold['summaries'] == warm['summaries'] == correctness['summaries'])
                assert report.get('phases') and cold['summaries'] and report['evaluations']['loaded'] > 0
                for part in ('returns','ir','sccq_dependencies','sccq_contexts','sccq_entry_contexts'):
                    assert warm['reports']['rh-fixpoint'][0]['entries'].get(part,0) > 0, part
                pair = dict(app=name,edit=entry['kind'],condition=CONDITION,shadow_matches=match,
                    loaded=report['evaluations']['loaded'],evaluations=report['evaluations'],
                    seed_cache_bytes=seed_bytes,seed_cache_sha256=seed_sha,
                    published_cache_bytes=(cache/'evaluations.json').stat().st_size,
                    phases=report.get('phases'),ingest_seconds=report.get('ingest_seconds'),
                    shadow_clone_seconds=report.get('shadow_clone_seconds'),
                    warm_analysis_seconds=report.get('warm_analyze_seconds'),
                    shadow_analysis_seconds=report.get('cold_analyze_seconds'),shadow_seconds=report.get('shadow_seconds'),
                    save_seconds=warm['reports'].get('rh-warm-save',[{}])[0].get('seconds'),
                    published_trace_cleanup_seconds=warm['reports'].get('rh-warm-cleanup',[{}])[0].get('published_records_drop_seconds'),
                    warm_excluding_shadow_seconds=warm['reports'].get('rh-warm-wall',[{}])[0].get('check_excluding_shadow_seconds'),
                    cold_wall_seconds=cold['wall_seconds'],full_warm_wall_seconds=warm['wall_seconds'],
                    cold_analysis_seconds=next((t['seconds'] for t in cold['timings'] if t['phase']=='analyze'),None),
                    peak_rss_mb=warm['peak_rss_mb'],cold_peak_rss_mb=cold['peak_rss_mb'],
                    diagnostic_contents_equal=cold['diagnostic_content_sha256']==warm['diagnostic_content_sha256'])
                pairs.append(pair)
                write(work/'runs.json',rows)
                write(work/'results.json',dict(condition=CONDITION,binary_sha256=sha(binary),pairs=pairs))
                print(json.dumps({k:pair[k] for k in ('app','edit','shadow_matches','cold_wall_seconds',
                           'warm_excluding_shadow_seconds','phases')}),flush=True)
            finally:
                path.write_bytes(original)
                shutil.rmtree(cache)
        assert COMMON.inventory(app)[0] == original_tree
        shutil.rmtree(seed)
        assert COMMON.inventory(source)[0] == original_tree
    assert len(pairs) == sum(1 for e in frozen['cases'] if (not args.app or e['app'] in args.app)
                            and (not args.edit or e['kind'] in args.edit))
    return 0 if all(p['shadow_matches'] for p in pairs) else 1

if __name__ == '__main__':
    sys.exit(main())
