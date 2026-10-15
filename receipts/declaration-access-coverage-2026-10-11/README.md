# Closing declaration misses while retaining partial access coverage

**Inconclusive; fixture mappings repaired, raw coverage partial.** This is an unscored public reference for the October 14–20 research week.
The supplied measurements were made on October 11, 2026; publication packaging adds no native measurement.
The next step is below. The full verdict, including failed and incomplete gates, is retained.

## Recorded result: F40

On October 11 conditions `declaration-access-coverage-20261011-v4-structure_fixture` and `declaration-access-coverage-20261011-v4-campfire`, the declaration continuation is **inconclusive**. All eighteen prior fixture misses have final access witnesses; the fixture has zero observed missing memberships or routing rejections across unset/1/2/unset-repeat, with fixed start/end declarations. All sixteen observer/control value and diagnostic comparisons agree. Nine raw entrance groups remain partial and the uninstrumented event count is unknown, so zero observed misses cannot confirm completeness. Campfire still has 39,337 missing memberships, eight routing rejections and 29 unmapped expression sites. Its declaration/attempt sets agree while controller mutations and some activation inputs differ. Both inputs retain schedule-dependent answers despite zero extra-round movement; complete routing and any-order inference remain open.

[Fact row](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/facts.md#f40)

## Source and condition

- Public branch: [`declaration-access-coverage`](https://github.com/bunnykong/roundhouse/tree/declaration-access-coverage).
- Public source: [`bf56edf9`](https://github.com/bunnykong/roundhouse/commit/bf56edf9e74ce2481e43e473de87466aac96283c).
- Recorded source: `bf56edf9e74ce2481e43e473de87466aac96283c`; public base: `abda389cbf30b7c0219d766134e0522b2ffe346f`.
- [Pins and toolchains](pins.json); [structured outcome](summary.json).
- [Original/public file hashes, archive members and omissions](recorded-files.json).

The source is the retained measured history.
Original binary hashes identify the measured compiler. A translated snapshot has not been rebuilt as a native
compiler during publication. Source labels, test markers and flag names have mechanical translations;
the campaign and calibration helpers also accept portable input and host-lock locations.
Rust/Cargo is 1.98.1, app Ruby is 4.0.7 with Prism, library controls use Ruby 3.4.4, and Python is 3.9+.
Each raw condition records its input pins, flags, source/runner identities and actual exit.

## Evidence

- [membership-explanations-final.json](raw/evidence/membership-explanations-final.json)
- [compact-final.json.xz](raw/evidence/compact-final.json.xz)
- [controller-traces-final.json.xz](raw/evidence/controller-traces-final.json.xz)

All raw files are under `raw/`. Read an xz member with `xz -dc FILE.xz` or use the unpack command below.
Compression is lossless after the declared text translations. Original and public uncompressed hashes are
different identities. Archived inputs were opened recursively and their text members translated separately.
Large omitted relations, ledgers and caches are explicitly listed; their absence is not complete raw coverage.
Agent reports and transcripts are excluded.

## Reproduce

From this receipt directory, validate retained hashes and recompute the bounded outcome without a build:

```sh
python3 -B rerun.py saved
python3 -B rerun.py unpack --work /tmp/declaration-access-coverage-evidence
```

Saved mode executes zero native runs. Its exit 0 means the evidence still yields the recorded verdict,
including a killed or inconclusive verdict. It does not turn a failed native gate into a pass.

After the source branch is published, repeat its local controls in a fresh directory:

```sh
python3 -B rerun.py native --work /tmp/declaration-access-coverage-fresh \
  --lock /tmp/roundhouse-shared-host.lock
```

Use the same coordination lock path as every other workload on the host. `--source /path/to/checkout`
can supply an existing checkout at the exact public source pin. The helper retains stdout, stderr,
commands, flags and every expected failed exit. Killed native gates leave the outer helper at exit 1.
Local controls do not complete the omitted application, emission, prepared-suite or cost campaigns.
Native timings are fresh observations; never overwrite this receipt or treat one pair as replication.

## Limits and next step

The full relation and repeated access streams are too large for this receipt. Explicit excerpts preserve every attempt/mutation and selected raw accesses; the complete hashes, native reports, old membership witnesses and controller traces remain. Raw read/write entrances and producer identity are still partial. Relation cardinalities are not materialized-edge or memory measurements. The library screen retains 43 failures; whole-app soundness and schedule-independent values are not established.

Complete the static inventory and operation witnesses for all nine raw groups, beginning with closure retro-stamp writes. Justify generated-view routing from original producers, retain the frozen declaration relation and repeat controls, then trace the controller input histories.

## Native declaration sweeps

The [sweep helper](runners/sweep.py) is the recorded four-schedule runner with descriptive labels.
Copy it into a fresh output directory before running it; outputs are adjacent to that copy.
Use the exact source/binary from pins.json, Ruby 4.0.7 and the shared host lock.

```sh
cp runners/sweep.py /tmp/declaration-fresh/sweep.py
python3 -B /tmp/declaration-fresh/sweep.py fresh-fixture structure_fixture \
  --source /path/to/source --binary /path/to/roundhouse \
  --apps /path/to/source/tools/research --declarations
```

Create `/tmp/declaration-fresh` first. Repeat on the pinned Campfire input with its corpus apps path,
then use a separate label and source/binary for the `abda389c` control. Exit 1 records inherited
schedule disagreement; exit 2 is an invalid run. Full streams can be large. Publication ran saved
reductions and Python syntax checks, without new native sweeps.
