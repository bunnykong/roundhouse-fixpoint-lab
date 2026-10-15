#!/usr/bin/env python3
"""Localize provenance residue. Diagnostic only: this script gives no verdict."""
from collections import Counter
import json
from pathlib import Path
import subprocess

D = Path(__file__).resolve().parent
C = 'structure-success-2-20261015-bf56edf9'
R = D / 'workshop/theory/runs' / (C + '-h3')
index = json.loads((D / 'series-index.json').read_text())


def load(name):
    rows = [json.loads(l) for l in (R / name).read_text().splitlines()]
    by_site = {json.dumps([r['emit_body'], r['site']], sort_keys=True): r for r in rows}
    assert len(rows) == len(by_site), 'emit-body/site reference collision'
    return by_site


left, right = load('unset.dump'), load('two.dump')
changes = [{'emit_body': left[k]['emit_body'], 'site': left[k]['site'],
            'unset_kinds': left[k]['untyped_kinds'], 'two_kinds': right[k]['untyped_kinds'],
            'unset_type_hash': left[k]['type_hash'], 'two_type_hash': right[k]['type_hash']}
           for k in sorted(left.keys() & right.keys()) if left[k] != right[k]]
observer_controls = {}
reconciliation = {}
for s, rows in [('unset', left), ('2', right)]:
    report = json.loads((Path(index['h3']['campfire-' + s]) / 'report.json').read_text())
    regular = json.loads((Path(index['both']['campfire-' + s]) / 'report.json').read_text())
    observer_controls[s] = {k: report[k] == regular[k] for k in ('digest', 'census', 'entries', 'loops', 'fold')}
    compact = json.loads((Path(index['h3']['campfire-' + s]) / 'compact.json').read_text())
    original = json.loads((Path(index['both']['campfire-' + s]) / 'compact.json').read_text())
    observer_controls[s].update({k: compact[k] == original[k] for k in ('declaration_hashes', 'identities')})
    counts = {name: sum(bool(r['untyped_kinds'] & (1 << bit)) for r in rows.values())
              for bit, name in enumerate(('pending', 'gradual', 'unresolved'))}
    reconciliation[s] = {'rows': len(rows), 'by_provenance': counts,
                         'matches_census': len(rows) == report['census']['untyped_anywhere']
                         and counts == report['census']['untyped_by_provenance']}
    assert reconciliation[s]['matches_census']
for name in ('unset.dump', 'two.dump'):
    with (R / (name + '.sorted')).open('wb') as out:
        subprocess.run(['sort', str(R / name)], stdout=out, check=True)
with (R / 'sorted-diff.txt').open('wb') as out:
    difference = subprocess.run(['diff', str(R / 'unset.dump.sorted'), str(R / 'two.dump.sorted')], stdout=out)
assert difference.returncode in (0, 1)
result = {'status': 'H3 diagnostic only; no confirm or kill attaches',
          'condition': C + '-h3', 'bits': {'pending': 1, 'gradual': 2, 'unresolved': 4},
          'site_counts': [len(left), len(right)], 'left_only': [left[k] for k in sorted(left.keys() - right.keys())],
          'right_only': [right[k] for k in sorted(right.keys() - left.keys())],
          'changed_sites': changes, 'changed_site_count': len(changes),
          'all_shared_type_hashes_equal': all(left[k]['type_hash'] == right[k]['type_hash']
                                             for k in left.keys() & right.keys()),
          'census_reconciliation': reconciliation, 'observer_controls': observer_controls,
          'kind_transitions': dict(Counter(str(c['unset_kinds']) + '->' + str(c['two_kinds']) for c in changes)),
          'sorted_diff_exit': difference.returncode}
(R / 'site-list.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2, sort_keys=True))
