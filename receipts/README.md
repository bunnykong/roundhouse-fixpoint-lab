# Measurement receipts for the public research corpus

These receipts make F12, F14, F15, F17 and F18's public measurements inspectable and rerunnable.
Every fact has its original raw inputs, a Python reduction, exact Roundhouse revisions and a fresh-clone
measurement script. Output paths and input names are relative; source acquisition uses only public repositories.
The linked fact cells belong to Roundhouse's `docs/research/facts.md` on `fixpoint-research`.

| Fact | Measurement | Receipt |
| --- | --- | --- |
| F12 | Join-memo storage equality | [F12](F12/README.md) |
| F14 | RH_DET error and precision census | [F14](F14/README.md) |
| F15 | Warm replay, mandatory cold shadow, timed edit pairs | [F15](F15/README.md) |
| F17 | Settling witness on upstream main | [F17](F17/README.md) |
| F18 | Keep-unresolved costs and 59 producer witnesses | [F18](F18/README.md) |

From this checkout, recompute the historical numbers with Python 3.9+:

```sh
for fact in F12 F14 F15 F17 F18; do
  python3 -B "receipts/$fact/recompute.py"
done
python3 -B receipts/compare.py
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
