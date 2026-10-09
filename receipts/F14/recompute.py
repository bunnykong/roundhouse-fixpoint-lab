#!/usr/bin/env python3
"""Recompute the RH_DET trial's totals and source-review counts from its raw receipts."""
import collections
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matrix
HERE = Path(__file__).resolve().parent
result = matrix.reduce(matrix.read_inputs(HERE), json.loads((HERE / 'reports.json').read_text()))
rows = json.loads((HERE / 'dispatch-review.json').read_text())['rows']
review = dict(dispatch_occurrences=len(rows), judgments=dict(collections.Counter(r['judgment'] for r in rows)),
              nil_only_receivers=sum(r['receiver_full_after'] == ['nil'] for r in rows))
assert len(rows) == 84 and review['judgments'] == {'impossible': 80, 'unclear': 4}
assert review['nil_only_receivers'] == 59
p = result['pooled']
assert (p['s3']['typed'], p['s3']['fully_typed'], p['det']['fully_typed']) == (1029377, 708499, 728440)
assert (p['s3']['errors'], p['det']['errors'], p['det']['new_only'], p['det']['old_only']) == (6370, 6457, 107, 20)
print(json.dumps(dict(pooled=p, source_review=review), indent=2, sort_keys=True))
