"""Recompute priority-sensitive allocation from each retained paired loss and its controls."""
from collections import Counter
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
rows=[json.loads(l) for l in (HERE/'loss-controls.jsonl').open()]
stages=Counter()
overlap=0
for row in rows:
    c=row['controls']
    def rec(arm):return bool(c.get(arm) and c[arm]['recovers'])
    if rec('S2c'):stage='S3 worklist/order sensitivity'
    elif rec('S3-no-allarms'):stage='S2b all-arms sensitivity'
    elif rec('S3-no-join'):stage='S2b join sensitivity'
    elif rec('S3-no-slots'):stage='S2c slot-cycle sensitivity'
    elif rec('S3-no-tail'):stage='S2c tail elimination sensitivity'
    elif rec('S2b'):stage='S2c reference/slot sensitivity'
    elif rec('join-only') and not rec('allarms-only'):stage='S2b all-arms or interaction'
    elif rec('allarms-only') and not rec('join-only'):stage='S2b join or interaction'
    elif any(z is None for z in c.values()):stage='control data incomplete'
    else:stage='persistent staged loss; trace required'
    assert stage==row['stage']
    stages[stage]+=1
    overlap+=sum(rec(k) for k in c)>1
expected=json.loads((HERE/'loss-evidence-summary.json').read_text())
assert len(rows)==expected['losses']==4823 and dict(stages)==expected['stage']
print(json.dumps(dict(condition=json.loads((HERE/'condition.json').read_text()),
                     losses=len(rows),priority_allocation=dict(stages),rows_recovered_by_multiple_controls=overlap),
                 indent=2,sort_keys=True))
