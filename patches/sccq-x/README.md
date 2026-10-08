# sccq-x

The scheduler with expression caching selected as a separate compiled arm.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sccq-x
```

Flags:

| Variable | Value |
| --- | --- |
| `RH_SCHED` | `sccq` |
| `RH_SCCQ_STATS` | `1` |

Expression caching has separate invalidation obligations. Compare outputs and complete-state verification, not timing alone.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sccq-x.diff).
