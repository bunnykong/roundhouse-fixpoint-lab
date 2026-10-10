"""Recompute historical kernel ratios and check extraction/compilation observations."""
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
timings = json.loads((HERE/'fastpaths.json').read_text())
compile_rows = json.loads((HERE/'compile.json').read_text())
validation = json.loads((HERE/'validation.json').read_text())
rows = []
for name, expected in [('canonical',2.05),('cycle',2.85),('tree_sum',3.80)]:
    r = timings[name]
    assert all(len(r['seconds'][arm])==7 for arm in ['control','fast'])
    ratio = statistics.median(r['seconds']['control'])/statistics.median(r['seconds']['fast'])
    assert round(ratio,2)==expected
    c = compile_rows[name]
    assert c['compile']['returncode']==0 and c['native']['stdout']==c['oracle']['stdout']
    v = validation[name]
    assert v['values']==96 and all(v[k] for k in ['control_matches_cruby','fast_matches_cruby','gc_stress_matches'])
    rows.append(dict(program=name,ratio_of_medians=round(ratio,2),pairs=7,validated_trees=v['values'],
                     control_range=[min(r['seconds']['control']),max(r['seconds']['control'])],
                     replacement_range=[min(r['seconds']['fast']),max(r['seconds']['fast'])]))
assert (HERE/'alias.seed').read_text()=='class JProbe\n'
for name in ['union','untyped']:
    assert 'cmeth echo poly poly' in (HERE/(name+'.seed')).read_text()
print(json.dumps(rows,indent=2,sort_keys=True))
