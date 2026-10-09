#!/usr/bin/env python3
"""Recompute the public join-memo comparisons without building Roundhouse."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import support as s

raw = json.loads(Path(__file__).with_name('historical.json').read_text())
result = {}
for app, arms in raw.items():
    left, right = arms['join-base'], arms['memo']
    fields = ('digest', 'entries', 'loops', 'census', 'provenance_leaves', 'structure', 'bound', 'harvest_untie_cut')
    equal = {k: left['fixpoint'][k] == right['fixpoint'][k] for k in fields}
    equal.update({k: left[k] == right[k] for k in ('errors_by_kind', 'warnings_by_kind', 'notes_by_kind',
                                                  'summary_counts', 'split_digests')})
    equal['diagnostic_content_hash'] = (left['diagnostic_output_identity']['line_multiset_sha256']
                                         == right['diagnostic_output_identity']['line_multiset_sha256'])
    assert all(equal.values()), (app, equal)
    assert left['diagnostics_complete'] and right['diagnostics_complete']
    leaves = left['fixpoint']['provenance_leaves']
    result[app] = dict(all_compared_fields_equal=True,
                      logical_untyped_leaves={k: leaves[k] for k in ('pending', 'gradual', 'unresolved')},
                      loops=left['fixpoint']['loops'])
print(json.dumps(result, indent=2, sort_keys=True))
