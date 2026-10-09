# F12: join-memo storage equality

The join-memo fix changes no carried-state digest, diagnostic-kind count or logical
`untyped` provenance-leaf count on the five pinned public apps. This supplies the previously
missing join-memo measurement behind F12. The interner fix and its tag correction remain
the earlier result cited by F12's milestone-2 receipt.

## Sources and condition

Both revisions are on Roundhouse's `fixpoint-next` history:

- Interner fixed, join memo unchanged: `060a91d84b55681504374ebb0f9baa7829930b38`.
- Join memo fixed: `4485e7db7f3e30e15c09800ff807dff29929d223`.

The original run is `sol-tieoff-a` lane 1, October 9, 2026. Only its five public-app
rows are included. [provenance.json](provenance.json) identifies that run and hashes this public projection.
The same [leaf-observer.patch](leaf-observer.patch) is applied to both source trees. It only
counts logical leaves per final emit-bound expression, traversing shared types without double
charging the observer's computation. Each expression occurrence still contributes its leaves.
S3 bypasses the join memo: this matrix checks the published S3 path; the fix's provenance
regressions cover the memo path with folding off. It does not claim the memo was exercised by S3.

The historical condition is **public-corpus-v1**, CRuby 4.0.7, WTO (no `RH_SHUFFLE`),
with native hash seed 1. `receipts/hash_seed.c` supplies the original macOS entropy hook;
the runner checks its activation. On other systems it records uncontrolled native hash order.
Counts can then differ, and native digests are not promised across platforms or Rust versions.
The saved JSON/CSV can always be recomputed with Python, on any platform. Runs here are untimed;
internal duration counters do not establish performance.

S3 flags:

```sh
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1
RH_BRK_ALLARMS=1 RH_SCHED=sccq
```

Observer flags: `RH_FIXPOINT_DIGEST=1 RH_FIXPOINT_STATS=1 RH_PROVENANCE_LEAVES=1 RH_C1_DIGEST=1`.
Extra-round verification is off. Each actual analyzer command is `roundhouse check --continue .`,
from the selected app's root, with those flags and `RH_HASHSEED=1` plus the entropy hook.

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
python3 -B receipts/F12/rerun.py
python3 -B receipts/F12/recompute.py
```

`--apps campfire` selects one app. `--source DIR` uses an existing public clone;
`--work-dir DIR` chooses a new output directory. Both are optional; the default clones from scratch.

## Outputs and fresh verification

- `historical.json`: the raw public S0 reports, component and split digests, logical leaf counts,
  diagnostic counts and completion markers, for both arms of the original measurement.
- `rerun-reports.json` and `rerun.json`: fresh public reports and the four between-arm equality checks.
- `build-join-base.json` and `build-memo.json`: source commits, observer-patch and binary hashes.
- `leaf-observer.patch`, `rerun.py`, `recompute.py`: the exact passive observer and executable recipes.
- `app-pins.json` and `provenance.json`: input identities and historical run attribution.

Fresh verification reruns both arms on **all five apps**. Carried digests, loop endings,
provenance leaves and diagnostic-kind counts match the historical reports and each other.
Internal worklist timing fields differ; they are excluded from the equality claim.
`comparison.json` lists each changed timing field; `python3 -B receipts/compare.py` verifies the match.

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
