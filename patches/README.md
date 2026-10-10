# Experimental Roundhouse patches

Each patch applies to the snapshot named by its README or linked receipt. The cumulative configuration
snapshots in [configurations.json](configurations.json) are standalone against
**b28b17b68d1fc879c506765cdc18142518544494**. Choose one of those; they are alternatives and must not be
stacked. Incremental source diffs were composed into these snapshots, including corrected new-file headers.
Only Roundhouse source, its build metadata, and its integration tests occur in the patches.

The auxiliary [long-name probe](long-name-probe.diff) instead updates `src/analyze/c1fp.rs` on the
shared-type snapshot in [its receipt](../receipts/long-name/README.md) and
[condition.json](../receipts/long-name/condition.json); that file is absent from `b28b17b6`.

```sh
python3 patches/check.py
python3 patches/build.py sharing-1g
python3 corpus/reproduce.py phase-c2a --set apps
```

Each configured snapshot has a same-named directory with a short README: purpose, exact flags, and
observed limitations. Auxiliary diffs have recipes in their linked receipts.
[checks.json](checks.json) records baseline applicability and hashes for the cumulative snapshots.
`patches/check.py` checks top-level diffs against `b28b17b6`; the long-name probe requires its separate base.
No Rust compilation result is implied by `git apply --check`.
The public binary build recipe uses Cargo's lockfile and four build jobs.

Stage 1e is retained as a rejected interning experiment: a nested-record law found a wire-order bug.
Stage 1f repairs it; stage 1g adds joins and hashing. Fold2, scheduler, Phase C, and EP3 explore different
convergence/representation policies. The configurations ending in `a` omit the non-absorbing dispatch flag.
All flags are explicit in [configurations.json](configurations.json). Folded type emission remains an
explicit experiment output; input names and inferred types were removed from automatic debug probes.

Archived descriptions refer to **public-corpus-v1** and the original flags. The expanded suite is
**public-lab-v1**. New outcomes, timings, diagnostic differences, and complete-state verification must
be measured under the chosen configuration. The proof applies to its calculus under its hypotheses,
not automatically to these experiment implementations.
