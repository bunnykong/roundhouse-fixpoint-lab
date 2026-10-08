# sharing-1e

Cached digests and weak interning before recursive wire-order preservation.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sharing-1e
```

Flags:

None required; unset flags remain off.

Rejected: a nested-record serialization law exposes changed insertion order. Kept as a learning counterexample.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sharing-1e.diff).
