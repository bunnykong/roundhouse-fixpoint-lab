"""Check the focused red/green regression and the 31 rejected budget attributions."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
off=(HERE/'flag-off.txt').read_text();on=(HERE/'flag-on.txt').read_text()
assert 'test result: FAILED. 0 passed; 1 failed' in off
assert 'test result: ok. 1 passed; 0 failed' in on
rows=json.loads((HERE/'suspected-cases.json').read_text())
assert len(rows)==31
for r in rows:
    g=r['graph']
    assert 'Rec[' in r['before_expansion']['type']
    assert r['before_expansion']['category']=='untyped' and r['expression']['category']=='untyped'
    assert not(g['leaf_counts'].get('untyped') or g['back_edges'] or g['missing'] or g.get('root_explicit_bottom'))
print(json.dumps(dict(condition=json.loads((HERE/'condition.json').read_text()),
                     focused_off='failed as expected',focused_on='passed',
                     suspected_cases=31,already_untyped_before_expansion=31,corpus_effect='unmeasured'),indent=2))
