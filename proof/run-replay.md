# Abstract run and replay proofs

`Certificate.lean` proves `Run.eq_kleene` and checks the twin-operator control.
`Edit.lean` proves `Record.Valid`, `IncRun.eq_kleene`, and `incrementalSolve_eq_kleene`,
with `replayAgainst_old_keeps_cycle` and `incomplete_reads_not_least` as deletion controls.
These are finite fact models; they do not certify the Rust analyzer or Ruby semantics.

From this repository root, with elan and the pinned dependencies:

```sh
(cd proof && lake exe cache get && lake build)
python3 -B reproductions/routing_model.py
```

Lean is pinned to 4.34.1; `lake-manifest.json` pins Mathlib and dependencies.
The routing model compares routing chosen at first evaluation with fixed routing:
the former has different answers with zero descents; the latter has one answer.
