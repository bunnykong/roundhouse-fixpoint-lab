# Measurement receipts for the public research corpus

These receipts make F12, F14, F15 and F17–F31's public measurements inspectable and rerunnable.
Receipts retain original inputs or omitted-file hashes, a Python reduction, exact Roundhouse revisions and a
fresh-clone measurement script. Output paths and input names are relative; source acquisition uses only public repositories.
The linked fact cells belong to Roundhouse's `docs/research/facts.md` on `fixpoint-research`.

| Fact | Measurement | Receipt |
| --- | --- | --- |
| F12 | Join-memo storage equality | [F12](F12/README.md) |
| F14 | RH_DET error and precision census | [F14](F14/README.md) |
| F15 | Warm replay, mandatory cold shadow, timed edit pairs | [F15](F15/README.md) |
| F17 | Settling witness on upstream main | [F17](F17/README.md) |
| F18 | Keep-unresolved costs and 59 producer witnesses | [F18](F18/README.md) |
| F19 | Pending-return comparisons on four public programs | [F19](F19/README.md) |
| F20 | 532-flow destructuring matrix and runtime comparison | [F20](F20/README.md) |
| F21 | Spinel extraction and manual kernel references | [F21](F21/README.md) |
| F22–F24, F26–F28 | October 10 current-main baseline, parity and source witness | [baseline-2026-10-10](baseline-2026-10-10/README.md) |
| F25 | Finite writer-law inventory and counterexamples | [writer-laws](writer-laws/README.md) |
| F29 | Discourse test reads, runtime membership and coverage limits | [discourse-trace-2026-10-10](discourse-trace-2026-10-10/README.md) |
| F30 | Warm replay port, six-edit parity and exclusive phase profiles on a shared host | [warm-profile-2026-10-10](warm-profile-2026-10-10/README.md) |
| F31 | Logical slots, writers, transient routes and repeat/coverage controls | [structure-dump-2026-10-10](structure-dump-2026-10-10/README.md) |

The remaining additions are small source or observation receipts:

| Material | Receipt |
| --- | --- |
| Writer-rule implementation boundaries | [writer-boundaries](writer-boundaries/README.md) |
| Structure and dependency contract | [structure-contract](structure-contract/README.md) |
| Public-app precision attribution | [precision-attribution](precision-attribution/README.md) |
| Budget-dependent expansion cache | [expansion-cache](expansion-cache/README.md) |
| Warm-cache guards and scheduling reads | [cache-guards](cache-guards/README.md) |
| Arena ownership and type-ID lifetimes | [type-id-lifetimes](type-id-lifetimes/README.md) |
| Long literal dispatch name | [long-name](long-name/README.md) |

All historical prototype hashes map to the executable-equivalent, comment-scrubbed public snapshots
in [prototypes.json](prototypes.json). [moved-files.json](moved-files.json) maps the relocated proof
and Ruby fixture files. [files.json](files.json) inventories every added or changed file, excluding itself.
Every count stays attached to its exact condition.

From this checkout, recompute the historical numbers with Python 3.9+:

```sh
for fact in F12 F14 F15 F17 F18; do
  python3 -B "receipts/$fact/recompute.py"
done
python3 -B receipts/compare.py
python3 -B receipts/check_additions.py
```

Each receipt's `rerun.py` clones Roundhouse unless `--source` supplies an existing public clone.
Fetch the pinned apps with `sh corpus/fetch.sh` before the app measurements. F17 uses only the
lab's small settling fixture. Rust builds use four jobs and honor `CARGO_TARGET_DIR`.
Run live measurements one at a time on a shared host. New timing values are separate observations.
Historical native hash controls are macOS-specific; the offline reductions are portable.

Shared `support.py` handles clean environments, input verification, source builds and output reduction.
`matrix.py` encodes diagnostic multiplicities as CSV and retains changed-site census witnesses as JSON;
`errgate.py` is the unchanged comparator from Roundhouse `b64163fe` (Apache-2.0; see the lab's NOTICE).
`app-trees.json` records the historical public source inventories, independently of fetch.sh's local manifest updates.
`hash_seed.c` contains the original entropy-control policy and reports activation.
