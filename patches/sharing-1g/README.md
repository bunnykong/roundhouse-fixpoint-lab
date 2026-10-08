# sharing-1g

Memoized root joins and DAG hashing on top of the repaired shared representation.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sharing-1g
```

Flags:

None required; unset flags remain off.

Archived public-corpus-v1: small-suite completion is retained. Completion does not establish a least fixpoint.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sharing-1g.diff).
