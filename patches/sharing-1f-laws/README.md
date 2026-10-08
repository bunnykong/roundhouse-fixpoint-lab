# sharing-1f-laws

Stage 1f plus persistent-cache invalidation and DAG-operation laws.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sharing-1f-laws
```

Flags:

None required; unset flags remain off.

The laws exercise unique mutation, copied mutation, deserialization, and cache invalidation.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sharing-1f-laws.diff).
