# sccq-tests

The scheduler with its regression tests bundled into the same baseline snapshot.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sccq-tests
```

Flags:

| Variable | Value |
| --- | --- |
| `RH_SCHED` | `sccq` |
| `RH_SCCQ_STATS` | `1` |

Scheduler regression coverage is included. Apply checks do not substitute for compiling or running the Rust tests.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sccq-tests.diff).
