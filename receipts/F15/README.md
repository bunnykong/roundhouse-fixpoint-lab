# F15: warm replay against the mandatory cold shadow

Six frozen public method-body edits agree with both the in-process cold shadow and a separate
cold check. In one timed pair per edit, the warm check excluding its validation interval takes
**21.55–32.01 times** the separate cold command's wall time. This is a historical latency observation;
it is not a distribution or a latency guarantee for a new machine.

## Sources and condition

Roundhouse branch: `fixpoint-warm`, exact commit `990137f742397a0aecc7efd14869f39c6412ba55`,
based on `fixpoint-staged` `92844f68ea0bef9bfb6d8a8f1b0fc4cad4fff51b`.
The original measured binary was built before the warm commit and stamped with the base SHA;
its source tree is the warm commit's exact tree. Its SHA-256 is retained in every original run row.
A fresh build uses a new unedited seed trace, so the build stamp cannot cause stale-cache reuse.

Original run: `sol-warm` **v2-deadline**, October 8 23:19:59Z through October 9 00:26:28Z, 2026.
Condition: **sol-warm-public-edits-v1**, derived from public-corpus-v1; CRuby 4.0.7;
three edits on Mastodon and three on Discourse; cold then warm; one timed pair per edit.
Both arms use the **same warm-capable binary**. Native hash order was uncontrolled.
This receipt uses that original wall-time series, rather than the later analysis-only warm-edits check.

S3 flags:

```sh
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1
RH_BRK_ALLARMS=1 RH_SCHED=sccq
```

Both arms add `RH_FIXPOINT_DIGEST=1`. Seed and warm commands add `RH_WARM=DIR RH_WARM_SHADOW=1`.
Only the timed warm command adds `RH_WARM_TIMINGS=1`. Cold has `RH_WARM` unset.
The runner sets `RBENV_VERSION=4.0.7` so an app's `.ruby-version` cannot select a different interpreter.
Actual commands are `roundhouse check --continue .` from a scratch copy of the selected pinned app.
Each edit restores the same original file and unedited seed trace; the rule never edits corpus inputs.
Warm commands emit two fixpoint reports (replay then shadow); the runner retains both and checks
their digests against the single `rh-warm` comparison report.

The reported numerator is the raw `rh-warm-wall.check_excluding_shadow_seconds` field.
The denominator is monotonic **whole cold command wall**, including ingest and diagnostics.
The excluded shadow interval includes state fingerprints, cold analysis and comparison.
Warm still includes ingest, cache loading/publication, diagnostics and preparing the validation clone.
`warm_analyze_seconds / cold_analyze_seconds` measures a different scope and is not this fact.

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
python3 -B receipts/F15/rerun.py
python3 -B receipts/F15/recompute.py
```

`--apps mastodon` selects its three edits; `--edit boolean` further selects one.
Optional `--source DIR` and `--work-dir DIR` choose a public source clone and new output directory.
The full suite can take over an hour. Cache files can require several GiB; the script removes them
once an app's measurements finish. All measured commands remain serialized within the script.

## Outputs and fresh verification

- `historical-runs.json`: all 20 original seed, untimed correctness, separate cold and timed warm rows,
  including command walls, timing segments, replay counts, state digests and diagnostic-kind counts.
- `edits.json`: exact body offsets/replacements, source-file hashes, original app pins and edited-tree hashes.
- `rerun-runs.json` and `rerun.json`: fresh seed/correctness/timed rows and timing-pair calculations.
- `build-warm.json`: fresh commit and binary hashes; `rerun.py` and `recompute.py`: executable recipes.
- `app-pins.json` and `provenance.json`: input pins and exact historical series attribution.

Fresh verification reruns **Mastodon's three edits**. The new timing measurements are retained separately
in `rerun.json`; shadow agreement is checked for every seed, correctness check and timed warm check.
The selected command was `python3 -B receipts/F15/rerun.py --apps mastodon`.
All carried-state fields, replay counts and diagnostic-kind counts match the historical series.
Only timings and the rebuilt binary identity differ; the new build is stamped with the committed warm SHA.

The table gives original → fresh values; seconds use the same scope in both runs.

| Edit | Cold wall, s | Warm excluding shadow, s | Ratio |
| --- | --- | --- | --- |
| boolean | 5.568 → 5.174 | 166.349 → 140.191 | 29.88× → 27.09× |
| return-type | 5.272 → 5.206 | 155.345 → 139.999 | 29.47× → 26.89× |
| withdraw-read | 5.359 → 5.210 | 171.575 → 144.200 | 32.01× → 27.68× |

New whole warm command walls, including shadow, are 144.651, 144.433 and 148.768 seconds respectively.
`recompute.py` validates the historical six pairs and the fresh three pairs independently from their raw rows.
The timing segments remain in `rerun-runs.json`; each observation is still one pair per edit.

## Public input pins

Only Mastodon and Discourse are consumed by this frozen edit suite. URLs and tags are in [app-pins.json](app-pins.json), copied from
`corpus/apps.json`. Source inventories are in [../app-trees.json](../app-trees.json).

| App | Commit |
| --- | --- |
| campfire | `90b330024dec3e757c79b6a7e6568f93da8e3148` |
| mastodon | `163f96cee4dea23365bff9b433871e68d20d9ee7` |
| chatwoot | `9f920b549c14491a4e587687a3eed5d21c6ccc7d` |
| forem | `cd665002c660cacfc6d267c5de81206cea7bf9a3` |
| discourse | `343b20f97ef5f6bd70826ee0e993ba348b210fd5` |
