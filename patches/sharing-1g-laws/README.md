# sharing-1g-laws

Stage 1g with the consolidated final DAG and nested-wire law tests.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sharing-1g-laws
```

Flags:

None required; unset flags remain off.

The final law suite preserves Eq/Hash and nested record serialization contracts.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sharing-1g-laws.diff).
