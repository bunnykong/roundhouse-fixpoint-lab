# phase-c1

Fold plus scheduler with complete-state fingerprints and corrected convergence handoffs.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py phase-c1
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

Archived public-corpus-v1, separately named phase-c1a arm: absorb verification is stable, but production IR verification still changes on Forem and Mastodon. The a arm omits RH_BRK_NOABSORB. Observed loop convergence is narrower than the Lean theorem.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../phase-c1.diff).
