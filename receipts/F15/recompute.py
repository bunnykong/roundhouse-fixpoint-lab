#!/usr/bin/env python3
"""Recompute the six historical cold-wall / shadow-excluded-warm timing pairs."""
import json
import math
from pathlib import Path
HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / 'historical-runs.json').read_text())
pairs = []
for cold in rows:
    if not cold['timed'] or not cold['label'].endswith('-cold'):
        continue
    warm = next(r for r in rows if r['label'] == cold['label'][:-4] + 'warm')
    report = warm['warm']
    assert report['shadow'] == 'pass' and report['warm_digest'] == report['cold_digest']
    assert report['warm_digest'] == cold['fixpoint']['digest']
    assert report['evaluations']['loaded'] > 0
    for field in ('errors_by_kind', 'warnings_by_kind', 'notes_by_kind', 'summary_counts'):
        assert warm['diagnostics'][field] == cold['diagnostics'][field]
    seconds = warm['warm_wall']['check_excluding_shadow_seconds']
    pairs.append(dict(app=cold['app'], edit=cold['edit']['kind'], cold_wall_seconds=cold['wall_seconds'],
                      warm_check_excluding_shadow_seconds=seconds, full_warm_wall_seconds=warm['wall_seconds'],
                      ratio=seconds / cold['wall_seconds'], shadow='pass'))
assert len(pairs) == 6
ratios = [p['ratio'] for p in pairs]
assert round(min(ratios), 2) == 21.55 and round(max(ratios), 2) == 32.01
result = dict(historical=dict(pairs=pairs, minimum_ratio=min(ratios), maximum_ratio=max(ratios)))

if (HERE / 'rerun-runs.json').exists():
    fresh = json.loads((HERE / 'rerun-runs.json').read_text())
    saved = json.loads((HERE / 'rerun.json').read_text())['pairs']
    fresh_pairs = []
    comparisons = []
    for row in fresh:
        reports = row['reports']
        if 'rh-warm' in reports:
            wr = reports['rh-warm'][0]
            assert len(reports['rh-warm']) == 1 and len(reports['rh-fixpoint']) == 2
            assert wr['shadow'] == 'pass' and wr['first_difference'] is None
            assert wr['warm_digest'] == wr['cold_digest']
            assert reports['rh-fixpoint'][0]['digest'] == wr['warm_digest']
            assert reports['rh-fixpoint'][1]['digest'] == wr['cold_digest']
        if not row['label'].endswith('-cold'):
            continue
        label = row['label'][:-5]
        app, edit = label.split('-', 1)
        warm = next(r for r in fresh if r['label'] == label + '-warm')
        correctness = next(r for r in fresh if r['label'] == label + '-correctness')
        wr = warm['reports']['rh-warm'][0]
        assert wr['evaluations']['loaded'] > 0
        assert wr['warm_digest'] == row['reports']['rh-fixpoint'][0]['digest']
        assert correctness['reports']['rh-warm'][0]['warm_digest'] == wr['warm_digest']
        assert row['diagnostics'] == warm['diagnostics'] == correctness['diagnostics']
        seconds = warm['reports']['rh-warm-wall'][0]['check_excluding_shadow_seconds']
        pair = dict(app=app, edit=edit, cold_wall_seconds=row['wall_seconds'],
                    warm_check_excluding_shadow_seconds=seconds,
                    full_warm_wall_seconds=warm['wall_seconds'],
                    shadow_matches=True, diagnostic_kinds_equal=True,
                    ratio=seconds / row['wall_seconds'])
        stored = next(p for p in saved if (p['app'], p['edit']) == (app, edit))
        for key, value in pair.items():
            assert math.isclose(value, stored[key], rel_tol=1e-12) if isinstance(value, float) else value == stored[key]
        fresh_pairs.append(pair)
        old = next(r for r in rows if r['timed'] and r['app'] == app
                   and r['edit']['kind'] == edit and r['label'].endswith('-warm'))
        old_kinds = {new: old['diagnostics'][previous] for new, previous in
                     [('error', 'errors_by_kind'), ('warning', 'warnings_by_kind'), ('note', 'notes_by_kind')]}
        comparisons.append(dict(app=app, edit=edit,
                                diagnostic_kinds_match_historical=warm['diagnostics'] == old_kinds,
                                fixpoint_matches_historical=warm['reports']['rh-fixpoint'][1] == old['fixpoint'],
                                replay_counts_match_historical=wr['evaluations'] == old['warm']['evaluations'],
                                digest_matches_historical=wr['warm_digest'] == old['warm']['warm_digest']))
    assert len(fresh_pairs) == len(saved)
    result['fresh'] = dict(pairs=fresh_pairs, comparisons=comparisons)

print(json.dumps(result, indent=2))
