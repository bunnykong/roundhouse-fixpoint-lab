# F18: keep a surviving Var unresolved

Of RH_DET's 59 nil-only dispatch receivers, the recorded producer review attributes **52** to
permanent dispatch fallbacks: **28** modeled classes missing the method, **21** unmodeled receivers,
and **three** String fallbacks. **Seven** are other inference gaps; **zero** are classified as pending.
Keeping surviving Vars unresolved removes all **59** targets. Errors absent from S3 fall from
**107 to 11**, but fully typed falls to **64.01%** (S3: **68.83%**); **97 of 147** errors that
vanish against S3 are classified as hidden by uncertainty.

## Sources and condition

Roundhouse branch: `fixpoint-onemerge`. Trial: `b64163fe53a8ceb9881fc5a2b5252011a4aa74e0`.
Keep-unresolved rule: `493253bae9a252c5dc25635d58c88d5150923b80`.
The measured passive precision-census child is `7e4b0d52baec5d119fdae4b74c631de1cd431bfc`;
the rerun builds that exact **public** source. S3, DET and keep use one binary.
Original source: `sol-saferule`'s October 9 `final` series, 45 runs: three repeats per app/arm.
The published raw first repeats reproduce every number; `repeats.json` retains each repeat's
precision, loop endings, carried-state digest, error count and normalized diagnostic hash.

The historical condition is **public-corpus-v1**, CRuby 4.0.7, WTO (no `RH_SHUFFLE`),
with native hash seed 7. `receipts/hash_seed.c` supplies the original macOS entropy hook;
the runner checks its activation. On other systems it records uncontrolled native hash order.
Counts can then differ, and native digests are not promised across platforms or Rust versions.
The saved JSON/CSV can always be recomputed with Python, on any platform. Runs here are untimed;
internal duration counters do not establish performance.

All arms use S3:

```sh
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1
RH_BRK_ALLARMS=1 RH_SCHED=sccq
```

Probes: `RH_FIXPOINT_DIGEST=1 RH_FIXPOINT_STATS=1 RH_C1_DIGEST=1 RH_ERRGATE=1 RH_PUBLIC_INPUT=1`.
All arms add `RH_PRECISION_CENSUS=1`; DET adds `RH_DET=1`; keep also adds `RH_DET_KEEP_UNRESOLVED=1`.
Actual commands are `roundhouse check --continue .` from each selected pinned app's root.
Fully typed excludes any-depth Var or `untyped`, and uses **1,029,377** present types as denominator;
**24,795** missing expressions remain separate. `Bottom` counts as fully typed.

The 59 producer rows are **causal source annotations**, backed by recorded dispatch branches,
harvest histories, inferred registry states and pinned source links. `trace.py` freshly records
those producers using the exact passive [trace-observer.patch](trace-observer.patch).
It verifies the recorded producer queries, remaining Vars and identified fallback branches;
the causal chains and other-gap labels still require source review. Neither that trace nor H/E/R/U
census labels certify app-runtime soundness or support. Hidden errors are not counted as fixes.

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
python3 -B receipts/F18/rerun.py
python3 -B receipts/F18/trace.py
python3 -B receipts/F18/recompute.py
```

`--apps forem` selects one app in either live runner. Optional `--source DIR` and `--work-dir DIR`
choose a public source clone and new scratch directory. `trace.py` separately builds the pinned source
plus its passive observer; its file/slot allowlists are public and included here.

## Outputs and fresh verification

- `diagnostics.csv`, `census-inputs.json`: raw error multisets and every observation needed at any key changing
  among S3, DET and keep. The reducer independently recomputes all new/vanished classifications.
- `reports.json`: raw original precision categories and complete fixpoint reports for each first repeat.
- `trace-59.json`: every occurrence's producer, source chain, raw branch/harvest/registry witnesses,
  review ID, before/after receivers and pinned public links. It preserves all 59 annotations.
- `repeats.json`: all 45 original repeat observations; `provenance.json`: historical source attribution.
- `rerun.json`, `rerun-reports.json`, `rerun-diagnostics.csv`, `rerun-census-inputs.json`:
  fresh matrix results and raw inputs. `build-F18.json` binds the fresh source and binary.
- `trace-rerun.json` and `build-trace.json`: new producer witnesses and observer/source/binary identity.
- `trace-observer.patch`, `trace-files.txt`, `trace-slots.txt`: the exact passive producer observer.
- `rerun.py`, `trace.py`, `recompute.py`: executable measurements and offline reductions.
- `app-pins.json`: the immutable public pins.

Fresh matrix verification reruns all three arms on **all five apps** and matches every historical count,
carried-state field, diagnostic multiset and changed-site census witness. Only internal timings differ.
`comparison.json` lists the differing fields; `python3 -B receipts/compare.py` verifies this.
Producer re-execution is retained separately in `trace-rerun.json`.
It covers **59 targets and 95 producer queries**. All distinct producer states, recorded fallback branches
and harvest states match. Two histories have different repetition counts: `mastodon-29`'s width lookup
has **2 → 6** observations; `chatwoot-01`'s `create!` has **10 → 12**. No distinct observed state changes.
`trace-rerun.json` retains those raw repetitions and their exact differences; `recompute.py` checks them.

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
