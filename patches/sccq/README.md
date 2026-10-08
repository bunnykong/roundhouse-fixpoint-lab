# sccq

SCC body-query scheduling with dependency recording and work counters.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sccq
```

Flags:

| Variable | Value |
| --- | --- |
| `RH_SCHED` | `sccq` |
| `RH_SCCQ_STATS` | `1` |

Archived public-corpus-v1: scheduling reduces repeated body work, but hidden state and non-monotone transfers prevent a general identical-answer claim.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sccq.diff).
