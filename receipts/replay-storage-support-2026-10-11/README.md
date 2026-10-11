# Native replay storage and cycle support withdrawal

**Verdict: Checks confirmed; current storage killed against native fidelity.** October 11, 2026. Unscored public reference.

On October 11 condition `replay-storage-support-20261011-storage-support`, the warm-base canaries are **confirmed as bounded checks**, while **current storage is killed against native fidelity**: five of eight nonempty payload round trips lose Pending/Unresolved reasons or ordered record fields, although all eight pass ordinary type equality. The support-deletion matrix passes 24/24 rows; an injected stale cycle is rejected by shadow at exit 3 and publication is refused. A moved-source fixture replays 14/14 evaluations and matches fresh persisted writes. Both Mastodon withdrawal arms match shadow, separate cold and the candidate’s same-path parent. Scope: one pair, shared host, a profile not a benchmark; no production codec or scheduler change, complete dependency certificate, selective replay approval or speed improvement follows.

## Pins and condition

Condition: `replay-storage-support-20261011-storage-support`. Labels are descriptive translations of the recorded experiment labels.

- Published base: [`d9ec78c31db361db8818b13153e5ddddee484c57`](https://github.com/bunnykong/roundhouse/tree/d9ec78c31db361db8818b13153e5ddddee484c57).
- Recorded experiment source: `fa084d7932b21baae84db260e725d70256c685ef`.
- Proposed fork branch: [`replay-storage-support`](https://github.com/bunnykong/roundhouse/tree/replay-storage-support).
- Public source: [`2717deedbd49c1c68d8e945520b74bc317077ae9`](https://github.com/bunnykong/roundhouse/tree/2717deedbd49c1c68d8e945520b74bc317077ae9).
- Frozen input lab: [`76cdb1ea`](https://github.com/bunnykong/roundhouse-fixpoint-lab/tree/76cdb1ea24b0c4c88af4c42c78f567d759b7731d).

Mastodon `163f96cee4dea23365bff9b433871e68d20d9ee7`, frozen withdraw-read edit; recorded test source `fa084d79` over `d9ec78c3`. Native flag and test-hook names are translated in the public snapshot; the measured binaries retain their original hashes. Rust/Cargo 1.98.1, four build jobs, locked dependencies; app checks use CRuby 4.0.7 with Prism, library controls use CRuby 3.4.4, and recording used Python 3.9.6.

Snapshot: yes; internal names and helper paths were translated mechanically. No new native Rust run is implied by publication. Recorded binary hashes name the measured artifacts. [Pins](pins.json), [summary](summary.json) and [file hashes and omissions](recorded-files.json) retain the evidence boundaries.

## Results

| Check | Result |
| --- | --- |
| Native payload cases | 3 preserve / 5 lose |
| Ordinary type equality | 8/8 pass |
| Support-deletion rows | 24/24 pass |
| Moved-source evaluations replayed | 14/14 |
| Injected stale cycle | shadow exit 3 |
| Full warm_check suite | 15 pass / 1 fail |
| Explicit storage selection | exit 101 |
| Explicit support selection | exit 0 |

| Profile scope | Parent | Guards |
| --- | ---: | ---: |
| Warm excluding shadow / s | 148.497 | 149.093 |
| Whole warm command / s | 156.601 | 157.533 |
| Whole cold command / s | 8.757 | 8.669 |
| Fingerprints / s | 132.463 | 132.925 |
| Warm RSS / MiB | 11,382 | 11,306 |

## Commands

From the lab root, validate file hashes and recompute the bounded saved checks:

```sh
RECEIPT=receipts/replay-storage-support-2026-10-11
python3 -B "$RECEIPT/rerun.py" saved
```

For fresh native candidate checks, use an empty work directory and set `RESEARCH_LOCK` to the host lock shared by all other analysis jobs. Native mode clones the exact public pins, captures commands and expected failing exits, and creates new observations:

```sh
python3 -B "$RECEIPT/rerun.py" native \
  --work "$PWD/fresh-replay-storage-support" --lock "$RESEARCH_LOCK"
```

[Rerun script](rerun.py) and [portable runners](runners/) preserve the original checker/observer conventions. Native reproduction needs the proposed fork branches pushed first. Saved checks require neither a source clone nor a compiler build. They validate retained evidence; they do not turn a failing native gate into a pass.

## Caveats

One pair, shared host, a profile not a benchmark. Native timing uses the exclusive coordination lock and excludes its waits. Both withdrawal profiles preserve shadow, separate cold, diagnostic contents and nonempty state inventories; guards also match a fresh parent at the same edited path. Pending and Unresolved become Gradual directly and nested, and reversed record fields become sorted. Those five losses keep the storage assertion red. Tag-erasure and order controls are rejected by the stronger comparator. Six support variants cover sole/two/distinct arms, receiver sides, defaults and controller actions. Poisoning five cycle records gives nonzero replay, a shadow return mismatch and refused publication, with the cache unchanged. This is an injected checker control, not an observed natural stale-cycle failure. Moved spans/FileId and persisted write geometry match fresh typing; diagnostics are empty in that fixture. No complete affected-closure/component/read certificate authorizes selective replay. The original warm pin plus tests was run, separately from the fingerprint candidate. No production codec, compression, scheduling or speed repair was made. The deliberately unignored failing storage test prevents a green CI claim; full default and emission suites were not run. Large application evaluation caches are omitted, while small native fixture caches and all command outputs remain in this packet.

Raw files use portable path placeholders and descriptive labels; original and public SHA-256 hashes are separate. Numeric measurements, diagnostic messages, type shapes and failed exits are preserved. Gzip/xz compression is lossless after those declared text translations. Existing frozen lab inputs and previous receipts are unchanged.
