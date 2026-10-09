# F17: the settling reproduction on current main

The original October 9 check on main `9b2dd5e9` still gave the historical membership pattern:
main settles and rejects **6 of 12** saved values; the restored-flow control caps and rejects **0**;
S3 with the corrected rules settles and rejects **0**.

The new check pins upstream main to **`1ce9969564303ebe1bf5b8ca3304f982272079c1`**, fetched
October 9, 2026. The membership counts still match. Production still caps in the flow control;
its **absorb loop settles at zero-based round 9**, whereas the historical flow control capped absorb.
This observed loop difference is retained, rather than relabeled as an exact table match.

## Sources and condition

The input is the lab's [settle_sound](../../reproductions/settle_sound/README.md), condition
**settle-sound-published-v1**, with its unchanged source, 12 saved CRuby 4.0.7 values and slot map.
No corpus app is analyzed by this check. Lab input snapshot:
`e3d9f189f2065440458f9d2d7ecb536f9efeed0a` (the same fixture and runner as the earlier receipt).

Roundhouse source identities:

- Original current-main rerun: upstream `main`, `9b2dd5e9720705ca3cf4e9d4f21e5f0e998cdfba`.
- Fresh current-main rerun: upstream `main`, `1ce9969564303ebe1bf5b8ca3304f982272079c1`.
- Original flow-control delta: `194f26cfaaada2a654e5f65949012f396706a275` to
  `main-flowfix` `a7e06b1ea9b486c894e803f98158533141d957a6`.
- Fixed S3 control: `fixpoint-sound`, `96cdea9a1e6e6bb32a267a247d72f99b98a50b70`.

[flow-fix.patch](flow-fix.patch) is the exact historical two-file control.
[flow-fix-current.patch](flow-fix-current.patch) ports that same yielded-value destructuring control
onto the fresh main pin, preserving main's newer nested-parameter parsing. The historical patch no
longer applies verbatim there. The fresh control's exact diff and hash are retained; it is an uncommitted
experimental overlay, not an upstream branch. No source-change cause is claimed for the absorb difference.

The script reuses the lab's unchanged `run.py`, `settle_probe.rs`, slot map, trace and oracle;
it changes only the arm list and supplies freshly built binaries through `--binaries`.
Both CLI and API must agree on loop endings. `RH_FIXPOINT_STATS=1` is used on every arm.
Only fixed S3 enables:

```sh
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1
RH_BRK_ALLARMS=1 RH_SCHED=sccq
```

The fixed S3 extra-round control also enables `RH_FIXPOINT_VERIFY=1`. All recorded movement counts are zero.
Native hash order is uncontrolled. Loop rounds are zero-based `LoopEnd::Settled` values;
`not_run` does not mean a settled absorb loop. Oracle membership is for the 12 snapshots,
not a soundness theorem for every execution.

## Commands

Run from this lab checkout with Git, Python 3.9+ and Rust 1.98.1/native Cargo dependencies:

```sh
export CARGO_BUILD_JOBS=4
export CARGO_TARGET_DIR="$PWD/_work/receipt-target"
python3 -B receipts/F17/rerun.py
python3 -B receipts/F17/recompute.py
```

The default clones the public fork and fetches the **pinned** upstream main SHA.
`--latest-main` fetches a new main and records its SHA; the control overlay may require adaptation
if upstream changes its contexts. `--source DIR`, `--work-dir DIR` and `--main-sha SHA` are optional.
The actual lab commands are `roundhouse check --continue reproductions/settle_sound` and
`settle-probe reproductions/settle_sound`, with the flags above. The fixed S3 CLI is repeated
with the extra-round flag; the Python oracle then checks each generated RBS grammar.

## Outputs

- `historical.json`: original current-main, flow-control and fixed-S3 loop/membership/API receipts.
- `historical-*.rbs` and `historical-*.oracle.json`: original inferred grammars and full membership reports.
- `rerun.json`: fresh source SHAs, loop endings, memberships, binary hashes and fixed-S3 verification.
- `rerun-*.rbs`, `rerun-*.oracle.json`: fresh inferred grammars and full membership reports.
- `build-main.json`, `build-main-flowfix.json`, `build-sound.json`: exact fresh source, overlay/exporter
  and binary hashes. `provenance.json` attributes the original `sol-tieoff-a` lane-2 rerun.
- `flow-fix*.patch`, `rerun.py`, `recompute.py`: exact controls and executable recipes.

`recompute.py` reruns the oracle from the saved grammars and the lab trace without building Rust.

## Public input pins

The five lab pins below are recorded for reference; none is consumed by the settling fixture. URLs and tags are in [app-pins.json](app-pins.json), copied from
`corpus/apps.json`. Source inventories are in [../app-trees.json](../app-trees.json).

| App | Commit |
| --- | --- |
| campfire | `90b330024dec3e757c79b6a7e6568f93da8e3148` |
| mastodon | `163f96cee4dea23365bff9b433871e68d20d9ee7` |
| chatwoot | `9f920b549c14491a4e587687a3eed5d21c6ccc7d` |
| forem | `cd665002c660cacfc6d267c5de81206cea7bf9a3` |
| discourse | `343b20f97ef5f6bd70826ee0e993ba348b210fd5` |
