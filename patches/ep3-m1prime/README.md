# ep3-m1prime

Handoff-only resemblance folding with an anonymous cut and bounded views.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py ep3-m1prime
```

Flags:

| Variable | Value |
| --- | --- |
| `RH_EP3` | `1` |

Archived public-corpus-v1: the parameter-only grammar is tight, but resemblance can fold acyclic chains; normal completion is not exactness.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../ep3-m1prime.diff).
