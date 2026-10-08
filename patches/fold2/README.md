# fold2

Origin-aware fold references, slot dependencies, revisit joins, and all-arm binding.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py fold2
```

Flags:

| Variable | Value |
| --- | --- |
| `RH_FOLD` | `1` |
| `RH_FOLD_SLOTS` | `1` |
| `RH_FOLD_JOIN` | `1` |
| `RH_BRK_ALLARMS` | `1` |
| `RH_BRK_NOABSORB` | `1` |

Archived public-corpus-v1: verified unbounded fixpoints on Campfire, Forem, and Mastodon. Chatwoot and Discourse retain residual limitations; this is not a universal convergence proof.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../fold2.diff).
