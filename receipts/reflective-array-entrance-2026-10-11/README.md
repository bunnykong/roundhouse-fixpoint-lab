# A reflective write in an Array escapes the harvest walker

**Killed by an uncovered reflective Array entrance.** This is an unscored public reference for the October 14–20 research week.
The supplied measurements were made on October 11, 2026; publication packaging adds no native measurement.
The next step is below. The full verdict, including failed and incomplete gates, is retained.

## Recorded result: F43

On October 11 condition `reflective-array-entrance-reflective-bound-next38403140-20261011-v1-shared-host`, the tagged/shared reflective destination port is **killed by an uncovered evaluated entrance**. A native Ruby method puts `instance_variable_set` inside an Array element. Direct harvest returns the eligible destination, but the body walker records no destination or touch; Ruby 4.0.7 executes it and stores an Array of depth seventeen ending in Integer 1. The flag-on entrance selector has four passes and two failures, exit 101. Covered checks pass 450 eligible writes and 19,968 finite memberships with zero added opacity relative to the same plain bound. Separate partition controls retain 2,104 partition and 548 duplicate-round differences. App/export, emission and broader integration gates stop before execution; the passing covered transfer does not establish complete writer coverage.

[Fact row](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/facts.md#f43)

## Source and condition

- Public branch: [`reflective-array-entrance`](https://github.com/bunnykong/roundhouse/tree/reflective-array-entrance).
- Public source: [`0ffb1333`](https://github.com/bunnykong/roundhouse/commit/0ffb133352ff6d8c3873eb5e949e6287312475e9).
- Recorded source: `fe6b169ea935be900aa51e5a2069a360324a69b0`; public base: `38403140379cd69759b0fe6247c6a8c4a48a37a9`.
- [Pins and toolchains](pins.json); [structured outcome](summary.json).
- [Original/public file hashes, archive members and omissions](recorded-files.json).

The source is a clean snapshot with descriptive labels.
Original binary hashes identify the measured compiler. A translated snapshot has not been rebuilt as a native
compiler during publication. Source labels, test markers and flag names have mechanical translations;
the campaign and calibration helpers also accept portable input and host-lock locations.
Rust/Cargo is 1.98.1, app Ruby is 4.0.7 with Prism, library controls use Ruby 3.4.4, and Python is 3.9+.
Each raw condition records its input pins, flags, source/runner identities and actual exit.

## Evidence

- [summary.json](raw/evidence/entrance-verification-v1/summary.json)
- [uncovered-entrance.json](raw/evidence/entrance-verification-v1/uncovered-entrance.json)
- [runtime-array.json](raw/evidence/runtime-array.json)
- [gate-entrances-on.log.xz](raw/week/bound-next/results/gate-entrances-on.log.xz)

All raw files are under `raw/`. Read an xz member with `xz -dc FILE.xz` or use the unpack command below.
Compression is lossless after the declared text translations. Original and public uncompressed hashes are
different identities. Archived inputs were opened recursively and their text members translated separately.
Large omitted relations, ledgers and caches are explicitly listed; their absence is not complete raw coverage.
Agent reports and transcripts are excluded.

## Reproduce

From this receipt directory, validate retained hashes and recompute the bounded outcome without a build:

```sh
python3 -B rerun.py saved
python3 -B rerun.py unpack --work /tmp/reflective-array-entrance-evidence
```

Saved mode executes zero native runs. Its exit 0 means the evidence still yields the recorded verdict,
including a killed or inconclusive verdict. It does not turn a failed native gate into a pass.

After the source branch is published, repeat its local controls in a fresh directory:

```sh
python3 -B rerun.py native --work /tmp/reflective-array-entrance-fresh \
  --lock /tmp/roundhouse-shared-host.lock
```

Use the same coordination lock path as every other workload on the host. `--source /path/to/checkout`
can supply an existing checkout at the exact public source pin. The helper retains stdout, stderr,
commands, flags and every expected failed exit. Killed native gates leave the outer helper at exit 1.
Local controls do not complete the omitted application, emission, prepared-suite or cost campaigns.
Native timings are fresh observations; never overwrite this receipt or treat one pair as replication.

## Limits and next step

The Array entrance gap is inherited; returning successful destinations does not cause it. Most passing entrances use structural IR with stamped right-hand-side types; the Array counterexample is native ingestion plus a separate Ruby runtime witness. Finite membership is sampled, reason equality is relative to the same plain bound, and that bound already adds four opaque paths. Partition and pairwise failures are independent of the entrance kill. Fresh app/export/emission/default-suite gates were stopped, not passed.

Audit evaluated child expressions beginning with Array elements before extending the visitor. Retain the successful-destination port, failing entrance tests and independent partition failures, then resume the app/export and integration gates.

## Repeat the Ruby execution witness

The [runtime companion](runners/reproduce_runtime.rb) invokes the exact public source fixture.
Use Ruby 4.0.7 and pass its full path from the pinned candidate checkout:

```sh
RBENV_VERSION=4.0.7 ruby runners/reproduce_runtime.rb \
  /path/to/source/src/analyze/fixpoint_bound/fixtures/reflective_array.rb
```

This proves the write executes and records its stored depth and leaf. The native Rust entrance tests
separately establish that the walker misses it. Publication checked Ruby syntax without a new runtime run.
