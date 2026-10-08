# sharing-1b-bound

A shared-payload arm with the same explicit depth/node bound hooks.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sharing-1b-bound
```

Flags:

| Variable | Value |
| --- | --- |
| `RH_BOUND` | `1` |

A bounded comparison control. Bounds are a precision policy, not an exactness or leastness guarantee.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sharing-1b-bound.diff).
