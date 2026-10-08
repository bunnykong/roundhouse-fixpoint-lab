# sharing-1b

Copy-on-write shared vectors, parameters, and ordered record maps.

Base: **b28b17b68d1fc879c506765cdc18142518544494**. Apply this snapshot alone to a clean checkout.

```sh
python3 corpus/reproduce.py sharing-1b
```

Flags:

None required; unset flags remain off.

Archived public-corpus-v1: lower feedback-merge peak; recursive cycles still reach memory limits.

The snapshot passed `git apply --check` during packaging. These are archived observations, not new timing measurements.
Input-bearing debug output was removed; aggregate counters remain. See [the patch](../sharing-1b.diff).
