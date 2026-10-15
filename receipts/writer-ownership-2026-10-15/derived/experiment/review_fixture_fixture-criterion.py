#!/usr/bin/env python3
"""Correct an extra audit condition; preserve every original result and raw receipt."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
initial = json.loads((D / 'gate-audit.json').read_text())
comparisons = json.loads((D / 'comparisons.json').read_text())
pairs = comparisons['matched_comparisons']
keys = ['a/fixture-unset--1', 'a/fixture-unset--baseline-matched', 'a/fixture-1--baseline-matched']
checks = {}
for key in keys:
    p = pairs[key]
    checks[key] = {
        'declarations_equal': p['declarations_equal'],
        'attempts_10_each_no_differences': p['inventories']['attempted']['counts'] == [10, 10]
            and not p['inventories']['attempted']['left_only'] and not p['inventories']['attempted']['right_only'],
        'mutations_10_each_no_differences': p['inventories']['mutation']['counts'] == [10, 10]
            and not p['inventories']['mutation']['left_only'] and not p['inventories']['mutation']['right_only'],
        'all_nine_digests_equal': len(p['digest_equal']) == 9 and all(p['digest_equal'].values()),
    }
assert all(value for check in checks.values() for value in check.values())
assert initial['H1']['confirm']['7_fixture'] is False
assert all(v for k, v in initial['H1']['confirm'].items() if k != '7_fixture')
fold = {label: comparisons['runs'][label]['fold'] for label in
        ['baseline/fixture-unset', 'baseline/fixture-1', 'a/fixture-unset', 'a/fixture-1',
         'off/fixture-unset', 'off/fixture-1']}
assert fold['a/fixture-unset'] == fold['off/fixture-unset'] == fold['baseline/fixture-unset']
assert fold['a/fixture-1'] == fold['off/fixture-1'] == fold['baseline/fixture-1']
review = {
    'condition': initial['condition'],
    'card_criterion': 'H1 confirm 7: fixture identities 10/10 with no differences; nine emitted digests equal to baseline',
    'audit_error': 'The initial script additionally required the full fold report equal across fixture schedules. '
                   'This work-counter requirement is absent from H1.7; Campfire fold equality remains required under H1.4.',
    'registered_checks': checks,
    'fold_accumulations_skipped': {k: v['accumulations_skipped'] for k, v in fold.items()},
    'matched_fixture_fold_reports_equal': True,
    'initial_audit_preserved': str(D / 'gate-audit.json'),
    'initial_script': str(D / 'analyze_residual.initial.py'),
    'initial_script_sha256': hashlib.sha256((D / 'analyze_residual.initial.py').read_bytes()).hexdigest(),
    'corrected_script_sha256': hashlib.sha256((D / 'analyze_residual.py').read_bytes()).hexdigest(),
    'card_sha256': hashlib.sha256((D / 'protocol.md').read_bytes()).hexdigest(),
    'raw_comparisons_unchanged': str(D / 'comparisons.json'),
}
out = deepcopy(initial)
out['H1']['confirm']['7_fixture'] = True
out['H1']['verdict'] = ('killed' if out['H1']['kills'] else 'confirmed'
                        if all(out['H1']['confirm'].values()) else 'inconclusive')
out['review_receipt'] = str(D / 'fixture_criterion-review.json')
for name, value in [('fixture_criterion-review.json', review), ('gate-audit-reviewed.json', out)]:
    path = D / name
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + '\n')
print(json.dumps({'H1': out['H1'], 'H2': out['H2'], 'fixture_review': review}, indent=2))
