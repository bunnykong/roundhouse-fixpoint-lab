# sharing-1c

Per-operation Eq/order and reconstruction memoization preserves DAG sharing.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sharing-1c
```

Flags:

None required; unset flags remain off.

Archived public-corpus-v1: the original small suite completes. The inference round cap still applies.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sharing-1c.diff).
