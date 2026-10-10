"""Count cold-shadow failures from saved public edited-input observations."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
records=json.loads((HERE/'public-series-precommit-correctness.json').read_text())
rows=[dict(edit=r['label'],shadow=r['warm']['shadow'],exit_code=r['exit_code'],
           mismatch=r['warm'].get('mismatch')) for r in records]
assert sum(r['shadow']=='fail' for r in rows)==5
focused=json.loads((HERE/'focused-committed-v2.json').read_text())
assert focused['exit_code']==0 and focused['passed']==13 and focused['failed']==0
assert 'test cache_guards_do_not_add_scheduler_dependencies ... ok' in (HERE/'v2-tests.txt').read_text()
print(json.dumps(dict(v1=rows,failed_shadows=5,v2_regression='passed'),indent=2,sort_keys=True))
