"""Check the retained integration regression lines and exact prototype conditions."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
shape=(HERE/'shape-tests.txt').read_text()
structure=(HERE/'structure-tests.txt').read_text()
for name in ['shape_assignment_keeps_framework_runtime_refusals','syntax_return_tuples_concatenate_as_arrays']:
    assert name+' ... ok' in shape
for name in ['structure_return_slots_preserve_inferred_closures',
             'structure_scalar_children_have_position_slots_and_closures_have_results']:
    assert name+' ... ok' in structure
conditions=json.loads((HERE/'conditions.json').read_text())
assert all(r['exit']==0 for r in conditions)
print(json.dumps(dict(conditions=conditions,shape=shape.splitlines(),structure=structure.splitlines()),indent=2))
