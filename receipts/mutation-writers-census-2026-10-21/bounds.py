"""Recompute the census counts and loss bounds from the retained rows.

Standard library only; starts no analyzer and runs no Ruby. Counts come from sample.tsv,
retained.tsv and losses.json; populations come from bounds.json. Exits 1 on any mismatch.
"""
import collections
import csv
import json
from math import comb
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SCHEDULES = ('unset', '1', '2', 'repeat')


def rows(name):
    with open(HERE / name, newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def upper(N, n, k, alpha_denominator):
    """Largest K with P[Hypergeometric(N, K, n) <= k] > 1/alpha_denominator, in exact integers."""
    if not N:
        return 0
    total = comb(N, n)

    def accepted(K):
        tail = sum(comb(K, x) * comb(N - K, n - x) for x in range(max(0, n - (N - K)), min(k, K, n) + 1))
        return tail * alpha_denominator > total

    lo, hi = k, N
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if accepted(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def main():
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f'{label}: computed {got}, recorded {want}')

    recorded = json.loads((HERE / 'bounds.json').read_text())
    sample = rows('sample.tsv')
    retained = rows('retained.tsv')
    losses = json.loads((HERE / 'losses.json').read_text())

    check('sample rows', len(sample), recorded['sample'])
    check('status counts', dict(collections.Counter(r['status'] for r in sample)), recorded['status_counts'])
    for r in sample:
        verdicts = {r[s] for s in SCHEDULES}
        # One row (F465) is an empty explicit-argument contribution with no runtime value to check.
        want = {'LOSS'} if r['status'] == 'UNSOUND' else (
            {'EMPTY_CONTRIBUTION'} if r['census_id'] == 'F465' else {'PASS'})
        check(f"{r['census_id']} verdicts", verdicts, want)

    population = 0
    conformance = detection = 0
    estimate = 0.0
    for s in recorded['strata']:
        mine = [r for r in sample if (r['app'], r['stratum']) == (s['app'], s['stratum'])]
        status = collections.Counter(r['status'] for r in mine)
        N, n, k, u = s['population'], len(mine), status['UNSOUND'], status['WITNESS_ONLY']
        name = f"{s['app']}/{s['stratum']}"
        check(f'{name} sample', n, s['sample'])
        check(f'{name} losses', k, s['losses'])
        check(f'{name} witness-only', u, s['witness_only'])
        check(f'{name} source-supported', status['SOURCE_SUPPORTED'], s['source_supported'])
        check(f'{name} detection 95%', upper(N, n, k, 20), s['detection_upper_95'])
        check(f'{name} conformance 95%', upper(N, n, k + u, 20), s['conformance_upper_95'])
        check(f'{name} detection simultaneous', upper(N, n, k, 80), s['detection_upper_simultaneous'])
        check(f'{name} conformance simultaneous', upper(N, n, k + u, 80), s['conformance_upper_simultaneous'])
        population += N
        conformance += upper(N, n, k + u, 80)
        detection += upper(N, n, k, 80)
        if n:
            estimate += N * k / n
    check('population', population, recorded['population'])
    check('conformance upper count', conformance, 2202)
    check('detection upper count', detection, 1021)
    check('conformance upper rate', conformance / population, recorded['conformance_upper_simultaneous'])
    check('detection upper rate', detection / population, recorded['detection_upper_simultaneous'])
    check('detection estimate', round(estimate / population, 12), round(recorded['detection_point_estimate'], 12))

    checks = collections.Counter(r[s] for r in retained for s in SCHEDULES)
    check('F72 losing rows, replay checks', dict(checks), {'PASS': 208, 'LOSS': 16})
    still_failing = sorted(r['f72_census_id'] for r in retained if any(r[s] == 'LOSS' for s in SCHEDULES))
    check('F72 rows still failing', still_failing, ['C2311', 'C2428', 'M2643', 'M586'])

    loss_rows = losses['rows']
    check('distinct losing rows', len(loss_rows), 21)
    check('losing rows not among F72 witnessed losses', sum(r['f72_census_id'] is None for r in loss_rows), 17)
    check('families', dict(collections.Counter(r['family'] for r in loss_rows)), losses['family_counts'])
    check('losses on all four schedules', all(set(r['verdicts'].values()) == {'LOSS'} for r in loss_rows), True)
    sampled = {r['census_id'] for r in sample if r['status'] == 'UNSOUND'}
    check('sampled losses listed', {r['census_id'] for r in loss_rows if r['set'] == 'sample'}, sampled)
    check('F72 losses listed', {r['f72_census_id'] for r in loss_rows if r['f72_census_id']}, set(still_failing))

    if failures:
        print('\n'.join(failures))
        return 1
    print(f'sample {len(sample)} rows: ' + ', '.join(f'{k} {v}' for k, v in sorted(recorded['status_counts'].items())))
    print(f'F72 losing rows replayed: 208 PASS, 16 LOSS checks; still failing: {", ".join(still_failing)}')
    print(f'losing rows: 21 distinct, 17 not among F72 witnessed losses; families {losses["family_counts"]}')
    print(f'conformance bound (unproved rows counted as losses), simultaneous 95%: '
          f'{conformance}/{population} = {conformance / population:.4%}')
    print(f'detection-only bound, simultaneous 95%: {detection}/{population} = {detection / population:.4%}; '
          f'weighted estimate {estimate / population:.4%}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
