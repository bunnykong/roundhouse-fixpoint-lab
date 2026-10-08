# ep3-m2

Handoff-only folding with identity-carrying cuts and exact tie-back at stores.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py ep3-m2
```

Flags:

| Variable | Value |
| --- | --- |
| `RH_EP3` | `2` |

Archived public-corpus-v1: recursive examples can be tighter, but identity alone does not guarantee bounded cost; main transfer imprecision remains visible to the runtime oracle.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../ep3-m2.diff).
