# Small reproductions

These are self-written Ruby fixtures with Rails-shaped source layouts. Static analysis needs no gems,
database, server, or application boot. The individual README lines explain the behavior being tested.
The unsafe re-embedding is intentionally an execution error; use its safe counterpart for runtime traces.

```sh
python3 reproductions/generate_cycle.py _work/cycle --cycle 2 --width 2
python3 corpus/run.py --binary ./roundhouse --set micro
```

The original reference uses 13 fixtures. The expanded lab suite also includes non-monotone transfers,
hidden state, receiver identity, safe and unsafe re-embedding, and long branching rings.

The [inference fixtures](inference-fixtures.md) add four pending-return programs, a generated
destructuring matrix and a long literal-dispatch witness. Their CRuby traces and inference comparisons
are retained in [F19](../receipts/F19/README.md), [F20](../receipts/F20/README.md) and
[long-name](../receipts/long-name/README.md).
