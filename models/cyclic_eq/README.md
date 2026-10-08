# Compact cyclic comparison

Immutable node tables support regular head/spine comparison and finite ranked-tree language inclusion.
Hash/Array spines join pointwise; Tuple/Record choices retain correlations. Records use sorted exact keys.
Leaves are rigid, and `widened` is top. Python 3.9+ standard library only.

```sh
python3 -B -m unittest models.cyclic_eq.test_cyclic_eq models.cyclic_eq.test_permutation
python3 -B -m models.cyclic_eq.bench --output models/cyclic_eq/evidence
python3 -B -m models.cyclic_eq.break_hkc --output models/cyclic_eq/evidence/permutation.json
```

`equivalent` uses HKC and a choice-game fallback. `included` implements head/spine coverage with antichains.
`simulation` is sufficient: a negative result is inconclusive. `tree_included` decides finite ranked-tree
inclusion with bottom-up antichains and witnesses. `frozen_equal` preserves the earlier canonicalizer's behavior.
These semantics differ on alternative Tuple and Hash products.

`holds=None` records exhausted budgets; it is never an equality or inclusion answer. The permutation family
also has an exponential reachable-subset count. Compact representation alone does not make every comparison cheap.
