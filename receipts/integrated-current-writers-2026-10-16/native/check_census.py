"""Independently recount the supplied census from its TSV, without running its emitter."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import random
import os

CENSUS = Path(os.environ['CENSUS_ROOT'])
SEED = 'integrated-current-writers-census-20261016'
SEEDS = json.loads(Path(__file__).with_name('census-seeds.json').read_text())['python_version2_integer_seeds']
SIZES = {'chatwoot': (40, 15), 'mastodon': (30, 10), 'forem': (30, 10)}
rows = list(csv.DictReader((CENSUS / 'rows.tsv').open(), delimiter='\t'))
summary = json.loads((CENSUS / 'summary.json').read_text())
assert len(rows) == len({r['id'] for r in rows}) == 6233
assert len({(r['app'], r['table'], r['key']) for r in rows}) == len(rows)
assert all(r['selected'] in ('True', 'False') for r in rows)


def exact_interval(N, n, k):
    denominator = math.comb(N, n)
    accepted = []
    for successes in range(N + 1):
        low_tail = high_tail = 0
        for x in range(max(0, n - N + successes), min(successes, n) + 1):
            mass = math.comb(successes, x) * math.comb(N - successes, n - x)
            if x <= k:
                low_tail += mass
            if x >= k:
                high_tail += mass
        if min(low_tail, high_tail) * 40 >= denominator:
            accepted.append(successes)
    return [min(accepted), max(accepted)]


def wilson(k, n):
    z = 1.959963984540054
    denominator = 1 + z ** 2 / n
    center = (k / n + z ** 2 / (2 * n)) / denominator
    radius = z * math.sqrt((k / n) * (1 - k / n) / n + z ** 2 / (4 * n ** 2)) / denominator
    return [center - radius, center + radius]


result = {'seed_prefix': SEED, 'apps': {}, 'input_sha256': {}}
for name in ('rows.tsv', 'summary.json'):
    result['input_sha256'][name] = hashlib.sha256((CENSUS / name).read_bytes()).hexdigest()
for app, sizes in SIZES.items():
    app_rows = sorted((r for r in rows if r['app'] == app), key=lambda r: (r['table'], r['key']))
    expected = summary[app]
    assert len(app_rows) == expected['narrowed']
    reasons = Counter()
    for r in app_rows:
        dropped = set(json.loads(r['dropped_reasons']))
        reasons.update(dropped)
        assert set(d['reason'] for d in json.loads(r['dropped_arms'])) == dropped
        assert r['stratum'] == ('concrete_nil' if dropped & {'concrete', 'nil'} else 'unknown')
    assert dict(reasons) == expected['reason_counts']
    assert reasons['Pending'] == 0
    app_result = {'narrowed': len(app_rows), 'reason_counts': dict(reasons), 'strata': {}}
    for stratum, n in zip(('concrete_nil', 'unknown'), sizes):
        eligible = [r for r in app_rows if r['stratum'] == stratum]
        seed = SEED + '/' + app + '/' + stratum
        chosen = set(random.Random(SEEDS[app + "/" + stratum]).sample([r['id'] for r in eligible], n))
        selected = [r for r in eligible if r['selected'] == 'True']
        assert chosen == {r['id'] for r in selected}
        counts = Counter(r['verdict'] for r in selected)
        assert not (set(counts) - {'SOUND', 'UNSOUND', 'INHERITED_UNSOUND'})
        k = counts['UNSOUND']
        families = Counter(r['family'] for r in selected if r['verdict'] == 'UNSOUND')
        N = len(eligible)
        interval = exact_interval(N, n, k)
        s = expected['strata'][stratum]
        assert (s['population'], s['sample']) == (N, n)
        assert s['complete'] is True
        assert s['verdicts'] == dict(counts)
        assert s['families'] == dict(families)
        assert s['loss_rate'] == k / n
        assert s['finite_population_95']['count'] == interval
        assert s['finite_population_95']['rate'] == [x / N for x in interval]
        assert s['finite_population_95']['confidence'] == 0.95
        assert all(abs(a - b) < 1e-12 for a, b in zip(s['wilson_95'], wilson(k, n)))
        app_result['strata'][stratum] = {
            'seed': seed, 'population': N, 'sample': n, 'verdicts': dict(counts),
            'loss_rate': k / n, 'finite_population_95_count': interval,
            'selected_ids': sorted(chosen), 'families': dict(families), 'matches': True,
        }
        print(app, stratum, 'population', N, 'losses/sample', str(k) + '/' + str(n), 'interval', interval)
    families = Counter(r['family'] for r in app_rows if r['selected'] == 'True' and r['verdict'] == 'UNSOUND')
    assert expected['sample_families'] == dict(families)
    app_result['sample_families'] = dict(families)
    app_result['broad_families'] = {
        'array': sum(n for f, n in families.items() if 'array' in f or f == 'loop mutation omitted'),
        'hash': sum(n for f, n in families.items() if 'hash' in f),
        'missing_callers_writers': sum(n for f, n in families.items() if 'array' not in f and 'hash' not in f and f != 'loop mutation omitted'),
    }
    result['apps'][app] = app_result
selected = [r for r in rows if r['selected'] == 'True']
counts = dict(Counter(r['verdict'] for r in selected))
assert len(selected) == 135
assert counts == {'SOUND': 75, 'UNSOUND': 54, 'INHERITED_UNSOUND': 6}
targets = [r['id'] for r in rows if r['selected'] == 'False' and r['verdict'] != 'NOT_SAMPLED']
assert targets == ['C1431', 'C1432']
assert sum(r['verdict'] == 'NOT_SAMPLED' for r in rows) == 6096
result.update(rows=len(rows), sampled_rows=len(selected), sample_verdicts=counts,
              targeted_outside_sample=targets, unadjudicated=6096, passed=True)
Path('census-check.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS: all six seeded samples, all summary counts and intervals; targeted rows excluded.')
