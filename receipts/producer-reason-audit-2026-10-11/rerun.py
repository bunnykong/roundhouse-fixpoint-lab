#!/usr/bin/env python3
"""Check retained evidence, or rerun the bounded native experiment in a fresh directory.

Python 3.9+. Native mode needs Git, Rust 1.98.1, Ruby 4.0.7/Prism,
Ruby 3.4.4 for library controls, and the same host coordination lock as other runs.
Expected failures remain failures in the captured logs.
"""
import argparse
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import sys

RECEIPT = Path(__file__).resolve().parent
PINS = json.loads((RECEIPT / 'pins.json').read_text())


def bytes_of(path):
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == '.gz' else lzma.decompress(data) if path.suffix == '.xz' else data


def raw(relative):
    for ending in ('', '.gz', '.xz'):
        path = RECEIPT / 'raw' / (relative + ending)
        if path.exists():
            return bytes_of(path).decode()
    raise FileNotFoundError(relative)


def data(relative):
    return json.loads(raw(relative))


def saved():
    manifest = json.loads((RECEIPT / 'recorded-files.json').read_text())
    for row in manifest['files']:
        path = RECEIPT / row['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['file_sha256'], row['file']
        assert hashlib.sha256(bytes_of(path)).hexdigest() == row['public_uncompressed_sha256'], row['file']
    name = PINS['proposed_branch']
    result = dict(condition=PINS['condition'], files_checked=len(manifest['files']), native_runs=0)
    if name == 'component-opacity-gate':
        s = data('week/sound/evidence/verification/summary.json')
        assert (s['selected'], s['observed'], s['observations'], s['missing'], s['no_slot']) == (28, 27, 127, 0, 0)
        assert s['original_decisions_unchanged']
        assert s['controls']['erasure-after']['gate_exits'] == [1, 1, 1]
        assert s['controls']['widening-after']['gate_exits'] == [0, 0, 1]
        assert s['checks']['component_guard_allows_concrete_widening']
        assert not s['checks']['concrete_widening_membership_passes']
        result.update(verdict='inconclusive', widening_rejections=s['controls']['widening-after']['rejected'])
    elif name == 'declaration-attempt-mutation':
        compact = data('evidence/compact-final.json')
        counts = {}
        for app in ('structure_fixture', 'campfire'):
            label = 'declaration-fixture-v2' if app == 'structure_fixture' else 'declaration-campfire-v2'
            for schedule in ('unset', '1', '2', 'repeat-unset'):
                rows = [json.loads(line) for line in raw('week/structure/runs/' + label + '/' + app +
                        '/observe/' + schedule + '/declarations.jsonl.excerpt').splitlines()]
                header = rows[0]
                attempts = sum(isinstance(row, list) and row[0] == 'attempt' for row in rows)
                mutations = sum(isinstance(row, list) and row[0] == 'mutation' for row in rows)
                assert attempts == header['counts']['attempted_writers']
                assert mutations == header['counts']['successful_writers']
                assert header['declaration_start'] == header['declaration_end']
                assert not header['complete'] and not header['raw_inventory_exhausted']
                if app == 'structure_fixture':
                    assert sum(isinstance(row, list) and row[0] == 'missing' for row in rows) == 18
                counts[app] = header['counts']
            assert compact['apps'][app]['values_match']
            assert compact['apps'][app]['diagnostic_bytes_match']
        assert counts['structure_fixture']['missing_memberships'] == 18
        result.update(verdict='killed', fixture_missing=18, counts=counts)
    elif name == 'producer-reason-audit':
        audit = data('week/evidence/results/campfire-final/candidate/precision/producer-evidence.json')
        assert audit['parameter_losses_by_kind']['Gradual'] == 72
        assert audit['parameter_losses_by_kind']['Unresolved'] == 234
        assert audit['equal_merges'] == 37628 and audit['tag_only_changes'] == 23
        rows = data('week/evidence/results/f19-final/summary.json')
        assert len(rows) == 16 and all(row['rejected'] == 0 for row in rows)
        for arm in ('s3', 'candidate'):
            selected = [row for row in rows if row['arm'] == arm and row['stage'] == 'final']
            assert sum(row['records'] for row in selected) == 78
            assert sum(len(row['coverage']['missing']) for row in selected) == 5
        result.update(verdict='killed', parameter_reason_losses=audit['parameter_losses_by_kind'])
    elif name == 'warm-fingerprint-components':
        def pair(label):
            rows = data('week/warm/runs/' + label + '/runs.json')
            return next(row for row in rows if row['label'].endswith('-1-warm'))
        totals = []
        for label in ('base-boolean', 'a-fast'):
            row = pair(label)
            report = row['reports']['rh-warm'][0]
            seconds = report['phases']['seconds']
            buckets = ('fingerprints', 'input_fingerprints', 'class_fingerprints', 'value_fingerprints',
                       'fp_expression_encoding', 'fp_context_encoding', 'fp_class_keys',
                       'fp_recursive_metadata', 'fp_extra_construction', 'fp_final_encoding', 'fp_final_hashing')
            totals.append(sum(seconds.get(bucket, 0) for bucket in buckets))
        s = json.loads((RECEIPT / 'summary.json').read_text())
        assert totals == [s['base']['fingerprint_seconds'], s['fast']['fingerprint_seconds']]
        ratio = totals[0] / totals[1]
        assert ratio >= 2 and s['fingerprint_speedup'] == ratio
        assert s['fast']['warm_excluding_shadow_seconds'] > s['fast']['cold_command_seconds']
        result.update(verdict='confirmed, bounded edit only', fingerprint_ratio=ratio, fingerprint_seconds=totals)
    elif name == 'reflective-writer-bound':
        s = data('evidence/verification-complete/summary.json')
        assert all(s['criteria'].values()) and s['additional_opacity_vs_plain'] == 0
        logs = raw('week/bound/results/partitions-final.log')
        metric = [json.loads(line.split('BOUND-ENTRANCE-METRIC ', 1)[1]) for line in logs.splitlines()
                  if 'BOUND-ENTRANCE-METRIC ' in line]
        assert metric
        assert data('week/bound/results/partitions-final.json')['exit'] == 101
        assert data('week/bound/results/reflect-after-final.json')['exit'] == 0
        result.update(verdict='confirmed, narrow writer repair', partition_metrics=metric)
    elif name == 'replay-storage-support':
        s = json.loads((RECEIPT / 'summary.json').read_text())
        assert len(s['storage_cases']) == 8
        assert sum(not row['preserved'] for row in s['storage_cases']) == 5
        assert all(row['ordinary_equal'] for row in s['storage_cases'])
        assert s['support_summary'][0]['completed_rows'] == 24
        assert not s['support_summary'][0]['failed_variants']
        assert not s['selective_replay_authorized']
        result.update(verdict='checks confirmed; current storage killed', storage_losses=5, support_rows=24)
    print(json.dumps(result, indent=2, sort_keys=True))


@contextmanager
def host_lock(path, exclusive=False):
    with path.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def native(work, lock):
    work.mkdir(parents=True, exist_ok=False)
    (work / 'logs').mkdir()
    (work / 'sources').mkdir()
    (work / 'scratch/tmp').mkdir(parents=True)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('RH_', 'ROUNDHOUSE_', 'SOUND_', 'PROBE_BASE'))}
    env.update(CARGO_BUILD_JOBS='4', CARGO_TARGET_DIR=str(work / 'build'),
               TMPDIR=str(work / 'scratch/tmp'), RBENV_VERSION='4.0.7',
               PYTHONDONTWRITEBYTECODE='1')
    count = [0]

    def run(label, command, cwd=work, flags=None, expected=(0,), exclusive=False):
        count[0] += 1
        label = str(count[0]) + '-' + label
        actual_env = dict(env, **(flags or {}))
        with host_lock(lock, exclusive), (work / 'logs' / (label + '.log')).open('w') as stream:
            completed = subprocess.run(command, cwd=cwd, env=actual_env, stdout=stream, stderr=stream)
        (work / 'logs' / (label + '.json')).write_text(json.dumps(dict(
            command=command, cwd=str(cwd), exit=completed.returncode, expected=list(expected),
            flags=flags or {}, exclusive_lock=exclusive), indent=2) + '\n')
        if completed.returncode not in expected:
            raise RuntimeError('Unexpected exit for ' + label + ': ' + str(completed.returncode))

    def clone(pin, dest, repository='https://github.com/bunnykong/roundhouse.git', branch=None):
        command = ['git', 'clone'] + (['--branch', branch] if branch else []) + [repository, str(dest)]
        run('clone-' + dest.name, command)
        run('pin-' + dest.name, ['git', 'checkout', '--detach', pin], dest)

    candidate = work / 'sources/probe-source'
    base = work / 'sources/base'
    lab = work / 'sources/lab'
    clone(PINS['public_source'], candidate, branch=PINS['proposed_branch'])
    clone(PINS['public_base'], base)
    clone(PINS['recorded_lab'], lab, 'https://github.com/bunnykong/roundhouse-fixpoint-lab.git')
    (lab.parent / 'tmp').mkdir(exist_ok=True)
    name = PINS['proposed_branch']
    if name in ('declaration-attempt-mutation', 'producer-reason-audit', 'warm-fingerprint-components',
                'replay-storage-support'):
        run('fetch-corpus', ['sh', str(lab / 'corpus/fetch.sh')])
    scripts = work / 'scripts'
    if (RECEIPT / 'runners').exists():
        shutil.copytree(RECEIPT / 'runners', scripts)
    else:
        scripts.mkdir()
    s3 = dict(RH_FOLD='1', RH_FOLD_SLOTS='1', RH_FOLD_JOIN='1', RH_FOLD_TAIL='1',
              RH_BRK_ALLARMS='1', RH_SCHED='sccq')
    tests = ['cargo', '+1.98.1', 'test', '--locked', '--lib']
    tail = ['--', '--include-ignored', '--nocapture', '--test-threads=1']

    if name == 'component-opacity-gate':
        adapter = candidate / 'tools/sound-exporter'
        run('component-tests', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(adapter),
                               '-p', 'test_component_gate.py', '-v'], flags=dict(SOUND_LAB=str(lab)))
        run('published-contract-tests', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(adapter),
                                        '-p', 'test_contract.py', '-v'])
        os.symlink(adapter, work / 'adapter')
        os.symlink(lab, work / 'lab')
        for variant in ('value-erasure', 'concrete-widening'):
            run(variant, [sys.executable, '-B', str(scripts / 'opacity_control.py'), '--variant', variant,
                          '--output', str(work / variant)])
    elif name == 'declaration-attempt-mutation':
        for label, source in (('control', base), ('declaration', candidate)):
            target = work / ('build-' + label)
            run('build-' + label, ['cargo', '+1.98.1', 'build', '--release', '--locked', '--bin', 'roundhouse'],
                source, dict(CARGO_TARGET_DIR=str(target)))
            for app in ('structure_fixture', 'campfire'):
                apps = source / 'tools/research' if app == 'structure_fixture' else lab / 'corpus/apps'
                command = [sys.executable, '-B', str(scripts / 'sweep.py'), label + '-' + app, app,
                           '--source', str(source), '--binary', str(target / 'release/roundhouse'), '--apps', str(apps)]
                if label == 'declaration':
                    command.append('--declarations')
                run(label + '-' + app, command, expected=(1,))
    elif name == 'producer-reason-audit':
        run('contracts', tests + ['producer_reason_provenance_contract'] + tail, candidate,
            dict(s3, RH_PROVENANCE_AUDIT='1', RBENV_VERSION='3.4.4'))
        run('accumulator', tests + ['writer_law_return_evidence'] + tail, candidate,
            dict(s3, RBENV_VERSION='3.4.4'))
        run('failing-next-controls', tests + ['writer_law_return_control_'] + tail, candidate,
            dict(RBENV_VERSION='3.4.4'), expected=(101,))
        (work / 'experiments').mkdir()
        shutil.copyfile(scripts / 'export_audit.rs', work / 'experiments/export_audit.rs')
        for helper, label in (('f19_check.py', 'f19'), ('app_check.py', 'campfire')):
            run(label, [sys.executable, '-B', str(scripts / helper), '--source', str(candidate),
                        '--output', str(work / label), '--candidate-env', 'RH_PROVENANCE_AUDIT=1'])
    elif name in ('warm-fingerprint-components', 'replay-storage-support'):
        for label, source in (('base', base), ('candidate', candidate)):
            run('build-' + label, ['cargo', '+1.98.1', 'build', '--release', '--locked', '--bin', 'roundhouse'],
                source, dict(CARGO_TARGET_DIR=str(work / ('build-' + label))))
        release_tests = ['cargo', '+1.98.1', 'test', '--release', '--locked']
        test_flags = dict(CARGO_TARGET_DIR=str(work / 'build-candidate'), WARM_TEST_RECEIPTS=str(work / 'native'))
        if name == 'warm-fingerprint-components':
            run('fingerprint-canaries', release_tests + ['--lib', 'warm_fp_'] + tail, candidate,
                dict(test_flags, RH_FOLD='1', RH_WARM_FP_AUDIT='1'))
        run('warm-tests', release_tests + ['--test', 'warm_check'] + tail, candidate, test_flags,
            expected=(0,) if name == 'warm-fingerprint-components' else (101,))
        if name == 'replay-storage-support':
            for selection, expected in (('warm_storage_fidelity', (101,)), ('warm_support_deletion_matrix', (0,))):
                run(selection, release_tests + ['--test', 'warm_check', selection] +
                    ['--', '--exact', '--nocapture', '--test-threads=1'], candidate, test_flags, expected)
        edit = 'boolean' if name == 'warm-fingerprint-components' else 'withdraw-read'
        for label, source in (('base', base), ('candidate', candidate)):
            command = [sys.executable, '-B', str(scripts / 'replay_pairs.py'),
                       '--source', str(source), '--binary', str(work / ('build-' + label) / 'release/roundhouse'),
                       '--app', 'mastodon', '--edit', edit, '--out', str(work / label),
                       '--condition', name + '-fresh-' + label]
            if label == 'candidate':
                command += ['--reference', str(work / 'base')]
            run(label + '-profile', command, exclusive=True)
        if name == 'warm-fingerprint-components':
            run('byte-audit', [sys.executable, '-B', str(scripts / 'replay_pairs.py'), '--source', str(candidate),
                              '--binary', str(work / 'build-candidate/release/roundhouse'), '--app', 'mastodon',
                              '--edit', 'boolean', '--out', str(work / 'audit'), '--reference', str(work / 'base'),
                              '--condition', name + '-fresh-audit', '--warm-flag', 'RH_WARM_FP_AUDIT=1'], exclusive=True)
    elif name == 'reflective-writer-bound':
        bound = work / 'week/bound'
        (bound / 'results').mkdir(parents=True)
        os.symlink(base, bound / 'base')
        os.symlink(candidate, bound / 'candidate')

        def law(tree, label, selection, expected=0, extra=()):
            run(label, [sys.executable, '-B', str(scripts / 'run_laws.py'), tree, label, selection,
                        '--expected-exit', str(expected)] + list(extra))

        law('base', 'reflect-before', 'writer_law_reflective_ivar_bound', 101)
        law('base', 'batch-before', 'writer_law_ivar_batch_bound')
        law('base', 'bound-before', 'writer_law_bound_', 101)
        law('base', 'default-library-control', 'ALL', 101, ('--default',))
        law('candidate', 'reflect-after-final', 'writer_law_reflective_ivar_bound')
        law('candidate', 'batch-after-final', 'writer_law_ivar_batch_bound')
        law('candidate', 'entrances-final', 'writer_law_bound_reflective_')
        law('candidate', 'membership-canaries-final', 'writer_law_bound_membership_canaries')
        law('candidate', 'partitions-final', 'writer_law_bound_partitions', 101)
        law('candidate', 'bound-after-final', 'writer_law_bound_', 101)
        law('candidate', 'default-library-final', 'ALL', 101, ('--default',))
        law('candidate', 'reflective-integration', 'instance_variable_set', 0, ('--integration', 'analyze'))
        run('finite-verifier', [sys.executable, '-B', str(scripts / 'verify_bound.py'),
                               '--candidate-suffix=-final', '--output', str(work / 'verified')])
    print(json.dumps(dict(condition=name + '-fresh', native_commands=count[0], output=str(work),
                          meaning='Fresh observations; inspect logs and failing gates. No timing replication claim.'), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('saved', 'native'), nargs='?', default='saved')
    parser.add_argument('--work', type=Path)
    parser.add_argument('--lock', type=Path)
    args = parser.parse_args()
    if args.mode == 'saved':
        saved()
    else:
        if args.work is None or args.lock is None:
            parser.error('native requires a fresh --work directory and the shared host --lock file')
        native(args.work.resolve(), args.lock.resolve())


if __name__ == '__main__':
    main()
