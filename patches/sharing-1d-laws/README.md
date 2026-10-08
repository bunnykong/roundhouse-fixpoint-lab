# sharing-1d-laws

Stage 1d plus independent DAG equality, hashing, rewriting, and substitution laws.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sharing-1d-laws
```

Flags:

None required; unset flags remain off.

The independent law checks are included as Roundhouse integration tests. Compile/run them after applying the patch.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sharing-1d-laws.diff).
