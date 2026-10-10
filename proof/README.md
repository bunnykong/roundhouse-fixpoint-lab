# Lean proof

The finite-site inference core is machine-checked in Lean 4.34.1 with Mathlib 4.34.1.
Install Lean's elan toolchain manager, then run this command from `proof/`:

```sh
lake exe cache get && lake build
```

The lockfile pins dependency revisions. The build checks every theorem and the executable `#guard` tests.
No build output or dependency cache is distributed. [PROOF.md](PROOF.md) states the hypotheses and scope.
This proves the calculus, its lowering, and its concrete-language soundness theorem; transferring those
results to the current analyzer requires the listed implementation obligations.

[Run replay and certified edits](run-replay.md) states the assumptions checked by
`ProofLean/Certificate.lean` and `ProofLean/Edit.lean`. The
[routing model](../reproductions/routing_model.py) gives finite counterexamples to weaker assumptions.

For JSON input relations in the format documented in `ProofLean/Oracle.lean`:

```sh
lake env lean --run ProofLean/Oracle.lean INPUT.json
```
