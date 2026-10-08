# Experimental Roundhouse patches

Each `.diff` is a standalone snapshot against **b28b17b68d1fc879c506765cdc18142518544494**.
Choose one; the cumulative snapshots are alternatives and must not be stacked. Incremental source diffs
were composed into these snapshots, including corrected new-file headers. Only Roundhouse source,
its build metadata, and its integration tests occur in the patches.

```sh
python3 patches/check.py
python3 patches/build.py sharing-1g
python3 corpus/reproduce.py phase-c2a --set apps
```

Every patch has a same-named directory with a short README: purpose, exact flags, and observed limitations.
[checks.json](checks.json) records baseline applicability and snapshot hashes. No Rust compilation result
is implied by `git apply --check`. The public binary build recipe uses Cargo's lockfile and four build jobs.

Stage 1e is retained as a rejected interning experiment: a nested-record law found a wire-order bug.
Stage 1f repairs it; stage 1g adds joins and hashing. Fold2, scheduler, Phase C, and EP3 explore different
convergence/representation policies. The configurations ending in `a` omit the non-absorbing dispatch flag.
All flags are explicit in [configurations.json](configurations.json). Folded type emission remains an
explicit experiment output; input names and inferred types were removed from automatic debug probes.

Archived descriptions refer to **public-corpus-v1** and the original flags. The expanded suite is
**public-lab-v1**. New outcomes, timings, diagnostic differences, and complete-state verification must
be measured under the chosen configuration. The proof applies to its calculus under its hypotheses,
not automatically to these experiment implementations.
