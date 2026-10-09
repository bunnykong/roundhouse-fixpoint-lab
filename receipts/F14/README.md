# F14: the RH_DET bundle

On the five public apps, S3 plus `RH_DET=1` raises fully typed expressions from
708,499/1,029,377 (**68.83%**) to 728,440/1,029,377 (**70.77%**). It adds 107 error
occurrences and removes 20, for a net **+87**. Of its 84 new dispatch occurrences,
source review marks **80 impossible, four unclear, zero confirmed real**. In **59**,
the complete receiver is `nil` alone. These judgments concern the stated public source flows;
no app-runtime oracle trace was recorded.

## Sources and condition

Roundhouse branch: `fixpoint-onemerge`, exact trial `b64163fe53a8ceb9881fc5a2b5252011a4aa74e0`,
based on `fixpoint-next` `4485e7db7f3e30e15c09800ff807dff29929d223`.
The trial includes the passive complete-receiver census. Baseline and candidate use **one binary**,
differing only by `RH_DET=1`. The original data are `sol-onemerge`'s `public-final` WTO rows,
its original expression census and exhaustive dispatch source review, October 9, 2026.
[provenance.json](provenance.json) hashes their original reductions.

The historical condition is **public-corpus-v1**, CRuby 4.0.7, WTO (no `RH_SHUFFLE`),
with native hash seed 7. `receipts/hash_seed.c` supplies the original macOS entropy hook;
the runner checks its activation. On other systems it records uncontrolled native hash order.
Counts can then differ, and native digests are not promised across platforms or Rust versions.
The saved JSON/CSV can always be recomputed with Python, on any platform. Runs here are untimed;
internal duration counters do not establish performance.

Both arms use S3:

```sh
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1
RH_BRK_ALLARMS=1 RH_SCHED=sccq
```

Probes: `RH_FIXPOINT_DIGEST=1 RH_FIXPOINT_STATS=1 RH_C1_DIGEST=1 RH_ERRGATE=1 RH_PUBLIC_INPUT=1`.
The candidate adds `RH_DET=1`. The fresh recipe applies [precision-observer.patch](precision-observer.patch),
the passive `RH_PRECISION_CENSUS=1` port, instead of the historical separate API census binary.
The categories partition expressions with a type; `Bottom` counts as fully typed. Missing expressions
(**24,795** in each arm) stay separate. Precision is an opacity count, not evidence of soundness.
Each actual analyzer command is `roundhouse check --continue .`, from a pinned app root.

## Commands

Commands run from the root of **this lab checkout**. Use Git, Python 3.9+, CRuby 4.0.7,
Rust 1.98.1 and a native C/build toolchain. The script clones the public Roundhouse fork,
detaches the exact commits below, builds with `cargo build --release --locked` and four jobs,
and rejects changed app inputs. No Rails boot, database or app test suite is involved.
A rerun writes a new scratch directory and keeps build logs and binary hashes there.

```sh
sh corpus/fetch.sh
export CARGO_BUILD_JOBS=4
export CARGO_TARGET_DIR="$PWD/_work/receipt-target"
python3 -B receipts/F14/rerun.py
python3 -B receipts/F14/recompute.py
```

`--apps campfire` selects one app. Optional `--source DIR` and `--work-dir DIR` choose a
public source clone and a new scratch output directory. The default source acquisition is fresh.

## Outputs and fresh verification

- `diagnostics.csv`: the raw error multiset, by app, arm, kind, relative site, operation and multiplicity.
- `census-inputs.json`: every type-census witness needed at a changed diagnostic key, relevant dropped-arm
  witnesses, and the paired completeness metadata. Unchanged sites' observations are omitted.
- `reports.json`: original raw fixpoint reports plus the original emit-expression census categories.
- `dispatch-review.json`: all 84 occurrence-level source judgments, complete before/after receivers,
  source excerpts, reasons and pinned public source links. It also recomputes the 59 nil-only receivers.
- `rerun.json`, `rerun-reports.json`, `rerun-diagnostics.csv`, `rerun-census-inputs.json`:
  fresh results and their raw inputs. `build-F14.json` binds the fresh source, observer and binary.
- `precision-observer.patch`, `rerun.py`, `recompute.py`: the observer and executable recipes.
- `app-pins.json`, `provenance.json`: pins and original-run attribution.

The fresh verification runs both arms on **all five apps** and matches every historical count,
carried-state field, diagnostic multiset and changed-site census witness. Only internal timings differ.
`comparison.json` lists the exact differing fields; `python3 -B receipts/compare.py` verifies this.
Source judgments remain the recorded review, with public evidence available for independent review.

## Public input pins

All five pins are consumed by the default rerun. URLs and tags are in [app-pins.json](app-pins.json), copied from
`corpus/apps.json`. Source inventories are in [../app-trees.json](../app-trees.json).

| App | Commit |
| --- | --- |
| campfire | `90b330024dec3e757c79b6a7e6568f93da8e3148` |
| mastodon | `163f96cee4dea23365bff9b433871e68d20d9ee7` |
| chatwoot | `9f920b549c14491a4e587687a3eed5d21c6ccc7d` |
| forem | `cd665002c660cacfc6d267c5de81206cea7bf9a3` |
| discourse | `343b20f97ef5f6bd70826ee0e993ba348b210fd5` |
