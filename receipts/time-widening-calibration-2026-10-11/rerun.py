#!/usr/bin/env python3
"""Validate saved evidence, unpack it, or repeat the named local controls.

Saved mode runs no compiler or Ruby app. Native mode repeats only the local
controls documented in README.md; it does not complete omitted app/cost campaigns.
Python 3.9+. Native Rust controls require Rust 1.98.1 and Ruby 3.4.4.
"""
import argparse
import fcntl
import gzip
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / 'pins.json').read_text())


def contents(path):
    value = path.read_bytes()
    if path.suffix == '.xz':
        return lzma.decompress(value)
    if path.suffix == '.gz':
        return gzip.decompress(value)
    return value


def raw(relative):
    for suffix in ('', '.xz', '.gz'):
        path = HERE / 'raw' / (relative + suffix)
        if path.is_file():
            return contents(path).decode()
    raise FileNotFoundError(relative)


def data(relative):
    return json.loads(raw(relative))


def marked(text, marker):
    return [json.loads(line.split(marker, 1)[1]) for line in text.splitlines() if marker in line]


def saved():
    manifest = json.loads((HERE / 'recorded-files.json').read_text())
    for row in manifest['files']:
        path = HERE / row['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['file_sha256'], row['file']
        assert hashlib.sha256(contents(path)).hexdigest() == row['public_uncompressed_sha256'], row['file']
    result = dict(condition=PINS['condition'], files_checked=len(manifest['files']), native_runs=0)
    name = PINS['proposed_branch']
    if name == 'native-parameter-reason-seeds':
        prefix = 'week/evidence/results/'
        log = raw(prefix + 'seed-arrival-v1/parameters.log')
        seed, = marked(log, 'PARAMETER-SEED-ARRIVAL ')
        assert seed['same_inputs'] == ['Bottom', 'Int'] and seed['integer_membership_both']
        assert seed['int_first'] == 'Int' and seed['bottom_first_origins'] == ['$:Pending']
        assert not seed['native_storage_equal'] and seed['int_first_origins'] == []
        assert 'FAILED. 4 passed; 1 failed; 0 ignored' in log
        assert data(prefix + 'seed-arrival-v1/condition.json')['gate_exit'] == 101
        handoff = data(prefix + 'handoff-summary.json')
        assert handoff['audit_only_all_reports_equal'] and handoff['all_paired_diagnostics_equal']
        for arm in handoff['f19']['arms'].values():
            assert (arm['records'], arm['selected'], arm['missing'], arm['rejected']) == (78, 45, 5, 0)
        result.update(verdict='killed', seed_witness=seed)
    elif name == 'warm-lossless-storage':
        log = raw('evidence/committed-storage.log')
        cases = marked(log, 'warm-storage-case: ')
        storage, = marked(log, 'warm-storage-summary: ')
        assert len(cases) == 20 and all(row['preserved'] and row['before'] == row['after'] for row in cases)
        assert storage['reason_sets'] == 7 and storage['codec']['cache_schema'] == 3
        assert storage['codec']['encoded_values'] == storage['codec']['decoded_values'] == 20
        assert storage['negative_controls_rejected'] == 2
        summary = data('evidence/summary.json')
        assert summary['verdict'] == 'confirmed-bounded'
        assert len(summary['support_rows']) == 24 and all(row['shadow'] == 'pass' for row in summary['support_rows'])
        assert len(summary['compatibility']['cases']) == 5
        assert all(row['evaluations']['incompatible_cache'] == 1 and row['evaluations']['loaded'] == 0
                   for row in summary['compatibility']['cases'])
        for row in summary['provenance']['cases']:
            assert row['revisit']['read_invalidated'] == row['revisit']['typed'] == 1
            assert row['revisit']['replayed'] == 0 and row['repeat']['replayed'] == 1
        assert len(summary['provenance']['cases']) == 3
        assert summary['diagnostics']['diagnostics'] == 1
        assert summary['legacy_control']['expanded_losses'] == 17 and summary['legacy_control']['exit'] == 101
        assert 'ok. 18 passed; 0 failed; 0 ignored' in raw('evidence/committed-warm-suite.log')
        result.update(verdict='confirmed within bounded storage gates', payloads=len(cases), support_rows=24)
    elif name == 'declaration-access-coverage':
        explanations = data('evidence/membership-explanations-final.json')
        assert explanations['all_have_final_access_witness'] and len(explanations['members']) == 18
        headers = []
        for app in ('structure_fixture', 'campfire'):
            label = 'declaration-access-coverage-20261011-v4-' + app
            for schedule in ('unset', '1', '2', 'repeat-unset'):
                rows = [json.loads(line) for line in raw('week/structure/runs/' + label + '/' + app +
                        '/observe/' + schedule + '/declarations.jsonl.excerpt').splitlines()]
                header = rows[0]
                assert header['declaration_start'] == header['declaration_end']
                assert header['raw_inventory_exhausted'] is False and header['complete'] is False
                assert header['counts']['uninstrumented_accesses'] is None
                for kind, field in (('attempt', 'attempted_writers'), ('mutation', 'successful_writers')):
                    assert sum(isinstance(row, list) and row[0] == kind for row in rows) == header['counts'][field]
                assert header['counts']['missing_memberships'] == (0 if app == 'structure_fixture' else 39337)
                assert header['counts']['routing_guard_failures'] == (0 if app == 'structure_fixture' else 8)
                headers.append(header)
        compact = data('evidence/compact-final.json')
        assert all(row['values_match'] and row['diagnostic_bytes_match'] for row in compact['apps'].values())
        result.update(verdict='inconclusive', old_memberships_witnessed=18, schedule_headers=len(headers), raw_coverage='partial')
    elif name == 'time-widening-calibration':
        root = 'week/sound/evidence/'
        summary = data(root + 'calibration-criteria-v1/summary.json')
        assert summary['verdict'] == 'confirmed' and all(summary['checks'].values())
        assert not any(summary['kill_criteria'].values()) and not summary['fresh_runtime']
        outcomes = {}
        for label, expected, exits in (
                ('widening-time-v1', (127, 0), [0, 0, 0]),
                ('widening-without-time-v1', (125, 2), [0, 0, 1]),
                ('erasure-regression-v1', (127, 0), [1, 1, 1])):
            reports = [data(root + label + '/' + setting + '.json') for setting in ('P', 'E', 'I')]
            totals = tuple(sum(row['arms']['final'][field] for row in reports) for field in ('accepted', 'rejected'))
            assert totals == expected
            assert [row['gate_exit'] for row in data(root + label + '/summary.json')['results']] == exits
            assert all(row['selected_slots'] == 28 and row['no_slot'] == 0 for row in reports)
            assert len({r['slot'] for report in reports for r in report['coverage'] if r['observed']}) == 27
            outcomes[label] = dict(accepted=totals[0], rejected=totals[1], exits=exits)
        result.update(verdict='confirmed bounded synthetic control', controls=outcomes)
    elif name == 'warm-fingerprint-edit-audits':
        summary = data('evidence/final-summary.json')
        packet = summary['conditions']['fast-six-audit']
        assert packet['native_runs'] == 11 and packet['completed_pairs'] == 3 and not packet['completed_packet']
        assert not summary['generality_completed'] and not summary['five_pair_campaign_completed']
        assert not summary['cold_campaign_completed']
        runs = data('week/warm/runs/fast-six-audit/runs.json')
        by_label = {row['label']: row for row in runs}
        comparisons = []
        for edit, count in (('boolean', 60698), ('return-type', 60698), ('withdraw-read', 60701)):
            warm = by_label['mastodon-' + edit + '-1-warm']
            cold = by_label['mastodon-' + edit + '-1-cold']
            wr = warm['reports']['rh-warm'][0]
            counters = wr['fingerprint_components']['counters']
            assert wr['shadow'] == 'pass'
            assert all(counters[field] == count for field in
                       ('input_calls', 'input_audit_comparisons', 'guard_audit_comparisons', 'extra_audit_comparisons'))
            for field in ('digest', 'entries'):
                assert warm['reports']['rh-fixpoint'][0][field] == cold['reports']['rh-fixpoint'][0][field]
            for field in ('diagnostics', 'summaries', 'normalized_diagnostics_sha256'):
                assert warm[field] == cold[field]
            assert packet['groups']['mastodon-' + edit]['parent_same_root_parity']
            comparisons.append(dict(edit=edit, comparisons=count))
        result.update(verdict='inconclusive', completed_edits=comparisons, required_edits=6)
    elif name == 'reflective-array-entrance':
        prefix = 'evidence/entrance-verification-v1/'
        summary = data(prefix + 'summary.json')
        assert summary['verdict'] == 'killed' and summary['cut_policy_unchanged']
        native = data(prefix + 'uncovered-entrance.json')['native_on'][0]
        assert native['reflective_calls'] == 1 and native['successful_destination'] == 'x'
        assert native['stored_destinations'] == [] and native['touched'] == []
        runtime = data('evidence/runtime-array.json')
        assert runtime['stored'] and runtime['array_depth'] == 17 and runtime['leaf_value'] == 1
        entrances = data('week/bound-next/results/gate-entrances-on.json')
        assert entrances['exit'] == 101
        assert 'FAILED. 4 passed; 2 failed; 0 ignored' in raw('week/bound-next/results/gate-entrances-on.log')
        assert summary['additional_opacity_vs_plain'] == 0
        metric, = summary['metrics']['gate-partitions']
        assert (metric['partition_round_schedules'], metric['partition_differences'],
                metric['duplicate_round_differences']) == (32928, 2104, 548)
        result.update(verdict='killed', uncovered_entrance=native, runtime_witness=runtime)
    print(json.dumps(result, indent=2, sort_keys=True))


def unpack(destination):
    destination.mkdir(parents=True, exist_ok=False)
    for row in json.loads((HERE / 'recorded-files.json').read_text())['files']:
        relative = Path(row['file']).relative_to('raw')
        if relative.suffix in ('.xz', '.gz'):
            relative = relative.with_suffix('')
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents(HERE / row['file']))


def native(work, lock, source):
    work.mkdir(parents=True, exist_ok=False)
    logs = work / 'logs'
    logs.mkdir()
    (work / 'tmp').mkdir()
    env = {key:value for key,value in os.environ.items()
           if not key.startswith(('RH_', 'ROUNDHOUSE_', 'SOUND_', 'PROBE_BASE'))}
    env.update(CARGO_BUILD_JOBS='4', CARGO_TARGET_DIR=str(work / 'build'),
               RBENV_VERSION='3.4.4', PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(work / 'tmp'))
    number = [0]

    def run(label, command, cwd=work, flags=None, expected=0, minimum_tests=None):
        number[0] += 1
        output = logs / (str(number[0]) + '-' + label + '.log')
        with lock.open('a') as stream, output.open('w') as target:
            fcntl.flock(stream, fcntl.LOCK_SH)
            try:
                process = subprocess.run(command, cwd=cwd, env=dict(env, **(flags or {})), stdout=target, stderr=target)
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)
        output.with_suffix('.json').write_text(json.dumps(dict(command=command, exit=process.returncode,
            expected_exit=expected, flags=flags or {}), indent=2) + '\n')
        assert process.returncode == expected, str(output)
        if minimum_tests is not None:
            counts = re.findall(r'test result: .*? (\d+) passed; (\d+) failed;', output.read_text())
            total = sum(int(a) + int(b) for a,b in counts)
            if not counts:
                total = sum(int(value) for value in re.findall(r'Ran (\d+) tests?', output.read_text()))
            assert total >= minimum_tests, str(output)

    if source is None:
        source = work / 'source'
        run('clone', ['git', 'clone', '--branch', PINS['proposed_branch'],
                      'https://github.com/bunnykong/roundhouse.git', str(source)])
        run('pin', ['git', 'checkout', '--detach', PINS['public_source']], source)
    assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'], text=True).strip() == PINS['public_source']
    name = PINS['proposed_branch']
    s3 = dict(RH_FOLD='1', RH_FOLD_SLOTS='1', RH_FOLD_JOIN='1', RH_FOLD_TAIL='1',
              RH_BRK_ALLARMS='1', RH_SCHED='sccq')
    tests = ['cargo', '+1.98.1', 'test', '--release', '--locked']
    tail = ['--', '--include-ignored', '--nocapture', '--test-threads=1']
    if name == 'native-parameter-reason-seeds':
        run('parameter-seed-gate', tests + ['--lib', 'writer_law_parameter_reason_conservation'] + tail,
            source, dict(s3, RH_PARAMETER_REASON_CONSERVE='1', RH_PROVENANCE_AUDIT='1'), 101, 5)
    elif name == 'warm-lossless-storage':
        run('warm-suite', tests + ['--test', 'warm_check'] + tail, source,
            dict(RH_WARM_LOSSLESS_CODEC='1'), 0, 18)
        run('reason-invalidation', tests + ['--lib', 'warm_provenance_invalidation'] + tail, source,
            dict(RH_WARM_LOSSLESS_CODEC='1'), 0, 1)
        run('legacy-storage-negative', tests + ['--test', 'warm_check', 'warm_storage_fidelity'] + tail,
            source, dict(RH_WARM_LOSSLESS_CODEC='0'), 101, 1)
    elif name == 'declaration-access-coverage':
        for selection, minimum in (('declaration_shadow', 7), ('structure_dump', 5)):
            run(selection, tests + ['--lib', selection] + tail, source, expected=0, minimum_tests=minimum)
    elif name == 'time-widening-calibration':
        evidence = work / 'evidence'
        unpack(evidence)
        lab = HERE.parents[1]
        flags = dict(SOUND_LAB=str(lab), SOUND_CALIBRATION_EVIDENCE=str(evidence / 'week/sound/evidence'))
        for directory, pattern, minimum in ((source / 'tools/sound-calibration/scripts', 'test_widening_time.py', 8),
                                           (source / 'tools/sound-exporter', 'test_component_gate.py', 13),
                                           (source / 'tools/sound-exporter', 'test_contract.py', 8)):
            run(pattern, [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(directory),
                          '-p', pattern, '-v'], flags=flags, minimum_tests=minimum)
    elif name == 'warm-fingerprint-edit-audits':
        run('fingerprint-canaries', tests + ['--lib', 'warm_fp_'] + tail, source,
            dict(RH_FOLD='1', RH_WARM_FP_AUDIT='1'), 0, 6)
        run('warm-suite', tests + ['--test', 'warm_check'] + tail, source, expected=0, minimum_tests=16)
    elif name == 'reflective-array-entrance':
        for selection, expected, minimum in (('writer_law_reflective_ivar_bound', 0, 1),
                                             ('writer_law_ivar_batch_bound', 0, 1),
                                             ('writer_law_bound_reflective_', 101, 6),
                                             ('writer_law_bound_partitions', 101, 1)):
            run(selection, tests + ['--lib', selection] + tail, source,
                dict(s3, RH_REFLECT_BOUND='1'), expected, minimum)
    killed = name in ('native-parameter-reason-seeds', 'reflective-array-entrance')
    print(json.dumps(dict(local_commands=number[0], expected_failures_retained=killed,
        complete_app_campaign=False, output=str(work)), indent=2))
    return 1 if killed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('saved', 'unpack', 'native'), nargs='?', default='saved')
    parser.add_argument('--work', type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--lock', type=Path)
    args = parser.parse_args()
    if args.mode == 'saved':
        saved()
        return 0
    if args.work is None:
        parser.error('unpack and native require a fresh --work directory')
    if args.mode == 'unpack':
        unpack(args.work.resolve())
        return 0
    if args.lock is None:
        parser.error('native requires the shared host --lock file')
    return native(args.work.resolve(), args.lock.resolve(), args.source.resolve() if args.source else None)


if __name__ == '__main__':
    sys.exit(main())
