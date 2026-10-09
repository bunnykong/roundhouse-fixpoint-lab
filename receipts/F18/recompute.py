#!/usr/bin/env python3
"""Recompute keep-unresolved's error/precision costs and the 59 producer annotations."""
import collections
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matrix
HERE = Path(__file__).resolve().parent
raw = matrix.read_inputs(HERE)
result = matrix.reduce(raw, json.loads((HERE / 'reports.json').read_text()))
rows = json.loads((HERE / 'trace-59.json').read_text())['rows']
for row in rows:
    arms = raw[row['app']]
    target = row['target']
    assert any(d['site'] == target['site'] and d['op'] == target['method'] for d in arms['det']['diagnostics'])
    assert not any(d['site'] == target['site'] and d['op'] == target['method'] for d in arms['keep']['diagnostics'])
trace = dict(rows=len(rows), classes=dict(collections.Counter(r['classification'] for r in rows)),
             subtypes=dict(collections.Counter(r['subtype'] for r in rows)), targets_removed=len(rows))
assert trace['classes'] == {'dispatch-fallback': 52, 'other': 7}
assert (trace['subtypes']['class-missing'], trace['subtypes']['receiver-unmodeled'],
        trace['subtypes']['primitive-string']) == (28, 21, 3)
p = result['pooled']
assert (p['det']['new_only'], p['keep']['new_only'], p['keep']['old_only'],
        p['keep']['vanished']['hidden'], p['keep']['fully_typed']) == (107, 11, 147, 97, 658885)
result = dict(pooled=p, producer_annotations=trace)
if (HERE / 'trace-rerun.json').exists():
    fresh = json.loads((HERE / 'trace-rerun.json').read_text())
    assert fresh['commit'] == '7e4b0d52baec5d119fdae4b74c631de1cd431bfc'
    originals = {row['id']: row for row in rows}
    assert len(fresh['rows']) == len(rows) == 59
    assert {row['id'] for row in fresh['rows']} == set(originals)
    differences = []
    queries = 0
    for row in fresh['rows']:
        original = originals[row['id']]
        assert (row['app'], row['classification'], row['subtype']) == (
            original['app'], original['classification'], original['subtype'])
        assert len(row['producer_evidence']) == len(original['producer_evidence'])
        for arm, old_arm in [('s3', 's31'), ('det', 'det1')]:
            old_harvest = {json.dumps(h, sort_keys=True) for group in original['harvest_evidence']
                           if group['arm'] == old_arm for h in group['history']}
            new_harvest = {json.dumps(h, sort_keys=True) for h in row['harvest_evidence'][arm]}
            assert old_harvest == new_harvest
        for old, new in zip(original['producer_evidence'], row['producer_evidence']):
            queries += 1
            assert old['query'] == new['query'] and new['observations']
            query = new['query']
            for observation in new['observations']:
                assert all(observation.get(k) == v for k, v in query.items() if k != 'path')
                assert observation['path'].endswith(query['path'])
            if row['classification'] == 'dispatch-fallback':
                assert any('Var' in r.get('result', r.get('ty', '')) for r in new['observations'])
                expected = {tag for r in old['observations'] for tag in r.get('fallbacks', [])}
                actual = {tag for r in new['observations'] for tag in r.get('fallbacks', [])}
                assert not expected - actual
            old_counts = collections.Counter(json.dumps(r, sort_keys=True) for r in old['observations'])
            new_counts = collections.Counter(json.dumps(r, sort_keys=True) for r in new['observations'])
            assert set(old_counts) == set(new_counts)
            assert new['observations_equal_to_historical'] == (old_counts == new_counts)
            if old_counts != new_counts:
                differences.append(dict(id=row['id'], query=query,
                                        historical_count=sum(old_counts.values()), fresh_count=sum(new_counts.values()),
                                        states_equal=set(old_counts) == set(new_counts),
                                        only_historical=[json.loads(r) for r in sorted((old_counts - new_counts).elements())],
                                        only_fresh=[json.loads(r) for r in sorted((new_counts - old_counts).elements())]))
    recorded = fresh['differing_producer_observations']
    assert [{k: v for k, v in row.items() if k != 'states_equal'} for row in differences] == recorded
    result['fresh_producer_trace'] = dict(rows=59, queries=queries,
                                        producer_states_match=True, harvest_states_match=True,
                                        differing_observations=[{k: v for k, v in d.items()
                                                                if k not in ('only_historical', 'only_fresh')}
                                                               for d in differences])
print(json.dumps(result, indent=2, sort_keys=True))
