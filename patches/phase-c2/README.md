# phase-c2

Phase C1 integrated with repaired sharing, DAG hashing, and root-join memo policy.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py phase-c2
```

Flags:

| Variable | Value |
| --- | --- |
| `RH_FOLD` | `1` |
| `RH_FOLD_SLOTS` | `1` |
| `RH_FOLD_JOIN` | `1` |
| `RH_BRK_ALLARMS` | `1` |
| `RH_BRK_NOABSORB` | `1` |
| `RH_SCHED` | `sccq` |
| `RH_FOLD_TAIL` | `1` |
| `RH_FOLD_VERIFY` | `1` |
| `RH_SCCQ_STATS` | `1` |

Archived public-corpus-v1, separately named phase-c2a arm: final digests reproduce phase-c1a on the pinned public apps. Production IR verification changes remain; this is not a zero-move certificate for every phase. The a arm omits RH_BRK_NOABSORB.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../phase-c2.diff).
