# Lossless native storage through a versioned warm codec

**Confirmed for bounded storage gates.** This is an unscored public reference for the October 14–20 research week.
The supplied measurements were made on October 11, 2026; publication packaging adds no native measurement.
The next step is below. The full verdict, including failed and incomplete gates, is retained.

## Recorded result: F39

On October 11 condition `warm-lossless-storage-20261011-lossless-storage-v1`, schema 3 is **confirmed within the bounded storage gates** through the production codec API: twenty native payloads preserve all seven nonempty reason sets and ordered record fields. Three reason-only changes invalidate and revisit readers; a nonempty diagnostic remaps correctly; five incompatible-cache controls start cold; 24 support rows and all 18 warm tests pass. The same-binary disabled codec loses seventeen of twenty payloads, including five of the original eight, at exit 101. Mastodon withdrawal matches shadow, separate cold and a same-path parent. Scope: one pair per arm, shared host, a profile not a benchmark; the broader default suite remains red. This repairs the tested storage boundary, while full replay, cold validation and the producer/coverage obligations remain.

[Fact row](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/facts.md#f39)

## Source and condition

- Public branch: [`warm-lossless-storage`](https://github.com/bunnykong/roundhouse/tree/warm-lossless-storage).
- Public source: [`2dbbe1b1`](https://github.com/bunnykong/roundhouse/commit/2dbbe1b1d2a88f25bde538df73ef8d13276660f4).
- Recorded source: `71b09336a7d0341c2620eafbb202b6f2f65fc431`; public base: `d9ec78c31db361db8818b13153e5ddddee484c57`.
- [Pins and toolchains](pins.json); [structured outcome](summary.json).
- [Original/public file hashes, archive members and omissions](recorded-files.json).

The source is a clean snapshot with descriptive labels.
Original binary hashes identify the measured compiler. A translated snapshot has not been rebuilt as a native
compiler during publication. Source labels, test markers and flag names have mechanical translations;
the campaign and calibration helpers also accept portable input and host-lock locations.
Rust/Cargo is 1.98.1, app Ruby is 4.0.7 with Prism, library controls use Ruby 3.4.4, and Python is 3.9+.
Each raw condition records its input pins, flags, source/runner identities and actual exit.

## Evidence

- [committed-storage.log.xz](raw/evidence/committed-storage.log.xz)
- [committed-provenance.log.xz](raw/evidence/committed-provenance.log.xz)
- [committed-warm-suite.log.xz](raw/evidence/committed-warm-suite.log.xz)
- [summary.json.xz](raw/evidence/summary.json.xz)

The [native reason contract](raw/native-reason-contract.md) defines the complete reason mask and ordered fields.
Committed native fixture outputs and legacy controls are retained under `raw/week/warm/results/`.

All raw files are under `raw/`. Read an xz member with `xz -dc FILE.xz` or use the unpack command below.
Compression is lossless after the declared text translations. Original and public uncompressed hashes are
different identities. Archived inputs were opened recursively and their text members translated separately.
Large omitted relations, ledgers and caches are explicitly listed; their absence is not complete raw coverage.
Agent reports and transcripts are excluded.

## Reproduce

From this receipt directory, validate retained hashes and recompute the bounded outcome without a build:

```sh
python3 -B rerun.py saved
python3 -B rerun.py unpack --work /tmp/warm-lossless-storage-evidence
```

Saved mode executes zero native runs. Its exit 0 means the evidence still yields the recorded verdict,
including a killed or inconclusive verdict. It does not turn a failed native gate into a pass.

After the source branch is published, repeat its local controls in a fresh directory:

```sh
python3 -B rerun.py native --work /tmp/warm-lossless-storage-fresh \
  --lock /tmp/roundhouse-shared-host.lock
```

Use the same coordination lock path as every other workload on the host. `--source /path/to/checkout`
can supply an existing checkout at the exact public source pin. The helper retains stdout, stderr,
commands, flags and every expected failed exit. Killed native gates leave the outer helper at exit 1.
Local controls do not complete the omitted application, emission, prepared-suite or cost campaigns.
Native timings are fresh observations; never overwrite this receipt or treat one pair as replication.

## Limits and next step

Twenty checked shapes do not certify arbitrary recursive graphs, pointer sharing, all producers or all contexts. Ordinary type equality retains its legacy behavior. The default screen stops at 1,097 passes, 43 failures and one ignored library test; missing generated fixtures and two inherited assertions remain. Mastodon costs are one pair per arm on a shared host, a profile not a benchmark. Codec warm wall excluding shadow is 146.220 s versus 7.431 s whole cold; useful latency, compression and speed promotion remain open.

Retain schema/identity rejection, exact native shape tests, full chronological replay and mandatory cold validation. Integrate only with a separately justified producer/completion carrier; broaden shapes, contexts and app edits in a new condition.
