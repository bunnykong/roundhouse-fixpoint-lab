#!/usr/bin/env python3
"""Recompute the public baseline from archived output; no analyzer execution."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tarfile

ROOT = Path(__file__).resolve().parent
LAB = ROOT.parents[1]
sys.path.insert(0, str(LAB / 'corpus'))
from metrics import Reducer

APPS = ('campfire', 'mastodon', 'chatwoot', 'forem', 'discourse')
SEEDS = ('unset', '1', '2')


def read(path):
    return json.loads((ROOT / path).read_text())


def log(path):
    p = ROOT / path
    return gzip.open(p, 'rt') if p.suffix == '.gz' else p.open()


def moved(report):
    assert report['verify'], 'No verification round recorded'
    return sum(sum(row['moved'].values()) for row in report['verify'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-error-census', action='store_true', help='Skip the 15 paired raw-log reductions.')
    parser.add_argument('--app-root', type=Path, help='Also verify Discourse source hashes and source-to-IR spans.')
    args = parser.parse_args()
    expected = read('evidence/baseline-summary.json')
    archive = read('archive.json')
    for entry in archive['files']:
        assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['archived_sha256']
    fixture_inventory = read('generated-fixtures.json')
    with tarfile.open(ROOT / 'generated-fixtures.tar.gz', 'r:gz') as bundle:
        actual = {row.name: hashlib.sha256(bundle.extractfile(row).read()).hexdigest()
                  for row in bundle.getmembers() if row.isfile()}
    wanted = {fixture['fixture'] + '/' + row['path']: row['sha256']
              for fixture in fixture_inventory for row in fixture['files']}
    assert actual == wanted
    rows, native, errors = [], [], {}
    for app in APPS:
        kind_counts = {}
        for label in ('main', 'staged', 'next'):
            prefix = 'runs/native/{}/{}/'.format(label, app)
            reducer = Reducer()
            for filename in ('stdout.txt.gz', 'stderr.txt.gz'):
                with log(prefix + filename) as stream:
                    for line in stream:
                        reducer.feed(line)
            data = reducer.data()
            receipt = read(prefix + 'receipt.json')
            for key in ('errors_by_kind', 'warnings_by_kind', 'summary_counts',
                        'counts_agree_with_summary', 'diagnostics_complete'):
                assert data[key] == receipt[key], (app, label, key)
            assert data['diagnostics_complete'] and receipt['exit'] in (0, 1)
            kind_counts[label] = data['errors_by_kind']
        assert kind_counts['main'] == kind_counts['staged'] == kind_counts['next']
        native.append(dict(app=app, errors=kind_counts))
        for mode in ('base', 's3'):
            prefix = 'runs/probe/{}/{}/'.format(app, mode)
            precision = read(prefix + 'precision-unset/report.json')
            schedules = [read(prefix + 'schedule-' + seed + '/report.json') for seed in SEEDS]
            repeat = read(prefix + 'repeat-unset/report.json')
            p = precision['precision']
            assert p['fully_typed'] + p['untyped_anywhere'] + p['var_without_untyped'] == p['typed']
            same_structure = len({r['structure']['end']['digest'] for r in schedules}) == 1
            same_values = all(r['digest'] == schedules[0]['digest'] for r in schedules)
            verification = [moved(r) for r in schedules]
            row = dict(app=app, mode=mode, precision=p, loops_verify0=precision['loops'],
                       verify_moved=verification, same_structure=same_structure, same_values=same_values,
                       structure_digests=[r['structure']['end']['digest'] for r in schedules],
                       value_digests=[r['digest'] for r in schedules],
                       repeat_same_structure=repeat['structure']['end']['digest'] == schedules[0]['structure']['end']['digest'],
                       repeat_same_values=repeat['digest'] == schedules[0]['digest'],
                       any_order_pass=same_structure and same_values and not any(verification))
            old = next(r for r in expected['rows'] if (r['app'], r['mode']) == (app, mode))
            assert all(row[k] == old[k] for k in row), (app, mode)
            rows.append(row)
        errors[app] = {}
        for seed in SEEDS:
            old = read('runs/probe/{}/errgate-{}.json'.format(app, seed))['summary']
            if not args.skip_error_census:
                with tempfile.TemporaryDirectory(prefix='public-census-') as directory:
                    paths = []
                    for mode in ('base', 's3'):
                        path = Path(directory) / (mode + '.stderr')
                        compressed = ROOT / 'runs/probe' / app / mode / ('schedule-' + seed) / ('probe-' + app + '.stderr.gz')
                        with gzip.open(compressed, 'rb') as stream:
                            path.write_bytes(stream.read())
                        paths.append(str(path))
                    output = subprocess.check_output([sys.executable, str(ROOT / 'errgate.py')] + paths, text=True)
                summary = json.loads(output.splitlines()[-1].split(': ', 1)[1])
                assert summary == old, (app, seed, 'error census differs')
            errors[app][seed] = old
        print('checked ' + app, file=sys.stderr, flush=True)
    aggregate = {}
    for mode in ('base', 's3'):
        chosen = [r for r in rows if r['mode'] == mode]
        totals = {key: sum(r['precision'][key] for r in chosen) for key in chosen[0]['precision']}
        assert totals == expected['aggregate'][mode]['precision']
        aggregate[mode] = dict(precision=totals, fully_typed_percent=100 * totals['fully_typed'] / totals['typed'],
                               verify_unshuffled=sum(r['verify_moved'][0] for r in chosen),
                               any_order_pass_apps=sum(r['any_order_pass'] for r in chosen),
                               apps_with_cap=sum(any(v['end'] != 'settled' for v in r['loops_verify0'].values()) for r in chosen))
    manifests = {label: read('evidence/' + label + '-emission-manifest.json') for label in ('main', 'staged', 'next')}
    assert manifests['main'] == manifests['staged'] == manifests['next']
    pairs = {}
    suites = {}
    for label in manifests:
        pairs[label] = [json.loads(line) for line in (ROOT / 'emission' / label / 'pairs.jsonl').read_text().splitlines()]
        assert len(pairs[label]) == 105 and not any('error' in r for r in pairs[label])
        for selection in ('lib', 'suite'):
            with log('evidence/{}-{}.log.gz'.format(label, selection)) as stream:
                text = stream.read()
            summaries = re.findall(r'^test result: .*? (\d+) passed; (\d+) failed; (\d+) ignored;', text, re.M)
            counts = [sum(int(row[i]) for row in summaries) for i in range(3)]
            saved = read('evidence/{}-{}.json'.format(label, selection))
            assert counts == [saved['passed'], saved['failed'], saved['ignored']]
            suites[label + '/' + selection] = dict(zip(('passed', 'failed', 'ignored'), counts))
    assert pairs['main'] == pairs['staged'] == pairs['next']
    witness = read('evidence/f8-summary.json')
    ir = {mode: read('runs/f8/' + mode + '/data-ivar-types.json') for mode in ('base', 's3')}
    assert len(ir['base']) == len(ir['s3']) == witness['inspected_reads'] == 28
    for mode in ir:
        by_span = {(r['span']['start'], r['span']['end']): r for r in ir[mode]}
        for row in witness['rows']:
            span = (row['span']['start'], row['span']['end'])
            assert by_span[span]['ty'] == row[mode + '_ty']
    integer_lines = [r['line'] for r in witness['rows'] if r['s3_ty'].get('kind') == 'hash'
                     and r['s3_ty']['value'].get('kind') == 'int']
    assert integer_lines == witness['integer_only_receiver_lines'] == [55, 56, 57]
    if args.app_root:
        for file in witness['source_files']:
            source = (args.app_root / 'discourse' / file['path']).read_bytes()
            assert hashlib.sha256(source).hexdigest() == file['sha256']
            if file['path'] == 'app/jobs/base.rb':
                for row in witness['rows']:
                    start, end = row['span']['start'], row['span']['end']
                    assert source[start:end] == b'@data' and source[:start].count(b'\n') + 1 == row['line']
    result = dict(condition=expected['condition'], aggregate=aggregate, rows=rows, native_parity=native,
                  emission_pairs=105, emission_unique_files=len(manifests['main']), suites=suites,
                  error_census=errors, raw_error_census_recomputed=not args.skip_error_census,
                  f8_integer_only_receiver_lines=integer_lines)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
