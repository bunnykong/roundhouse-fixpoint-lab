# Budget-dependent expansion memo

Staged Roundhouse `92844f68ea0bef9bfb6d8a8f1b0fc4cad4fff51b`; the opt-in candidate is
[`520ef142`](https://github.com/bunnykong/roundhouse/tree/520ef142b4a4d21235f63b6c5c4a23e5155962fa)
on `fixpoint-budget-cache`, with `RH_FOLD_NOCACHE_BUDGET=1`.
[condition.json](condition.json) fixes the source and condition. The regression is synthetic;
the 31 suspected corpus cases use the five public apps at the lab pins.

```sh
python3 -B receipts/expansion-cache/recompute.py
RH_FOLD=1 RH_FOLD_NOCACHE_BUDGET=1 \
  cargo test --lib later_small_expansion_matches_a_fresh_reader -- --ignored
RH_FOLD=1 cargo test --lib later_small_expansion_matches_a_fresh_reader -- --ignored
```

Run Cargo commands in the pinned fork checkout. The second command must fail with the same witness:
a later small root inherits `Array[untyped]`, while a fresh reader yields `Array[Array[String]]`.
The passing test also retains the large root's cut, authored gradual uncertainty, guarded-cycle
uncertainty and missing-slot pending state. `flag-off.txt` and `flag-on.txt` are raw focused outputs.

`suspected-cases.json` retains all 31 reference-containing losses whose visited slot graph had
no explicit unknown leaf, missing slot or back edge. Each pre-expansion expression already contained
`untyped`; none proves that the budget memo caused its category loss. Candidate corpus effects remain unmeasured.
