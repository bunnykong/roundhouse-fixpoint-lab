# A Time-inclusive widening calibrates the component gate

**Confirmed for bounded checker calibration.** This is an unscored public reference for the October 14–20 research week.
The supplied measurements were made on October 11, 2026; publication packaging adds no native measurement.
The next step is below. The full verdict, including failed and incomplete gates, is retained.

## Recorded result: F41

On October 11 synthetic condition `time-widening-calibration-f29-concrete-widening-time-20261011-v1`, Integer | String | nil | Time is **confirmed as the bounded widening control**: it admits all 127 saved F29 observations, adds zero opaque paths and exits 0/0/0 for P/E/I. The fixed 28 selections retain 27 observed reads, zero missing types and zero unmapped observations. The historical Time-omitting widening remains 125/2 accepted/rejected with exits 0/0/1; erasure admits 127 values but adds eight opaque value paths and is rejected at 1/1/1. Reordering unions passes, all 29 Python checks pass, and original main/S3 decisions remain 127/0 and 91/36. These are saved traces and synthetic exports, without a compiler repair, fresh Ruby observations or a whole-program soundness claim.

[Fact row](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/facts.md#f41)

## Source and condition

- Public branch: [`time-widening-calibration`](https://github.com/bunnykong/roundhouse/tree/time-widening-calibration).
- Public source: [`f78c3975`](https://github.com/bunnykong/roundhouse/commit/f78c397552cfc2189f393c5fd19bb69ce0fb23c1).
- Recorded source: `63e7814732485b5c122222169ca11cc9c0d38dac`; public base: `8f7c1af7bcaa6e5376d465d5f5ffda03702522fd`.
- [Pins and toolchains](pins.json); [structured outcome](summary.json).
- [Original/public file hashes, archive members and omissions](recorded-files.json).

The source is a clean snapshot with descriptive labels.
Original binary hashes identify the measured compiler. A translated snapshot has not been rebuilt as a native
compiler during publication. Source labels, test markers and flag names have mechanical translations;
the campaign and calibration helpers also accept portable input and host-lock locations.
Rust/Cargo is 1.98.1, app Ruby is 4.0.7 with Prism, library controls use Ruby 3.4.4, and Python is 3.9+.
Each raw condition records its input pins, flags, source/runner identities and actual exit.

## Evidence

- [summary.json](raw/week/sound/evidence/calibration-criteria-v1/summary.json)
- [summary.json](raw/week/sound/evidence/widening-time-v1/summary.json)
- [summary.json](raw/week/sound/evidence/erasure-regression-v1/summary.json)

All raw files are under `raw/`. Read an xz member with `xz -dc FILE.xz` or use the unpack command below.
Compression is lossless after the declared text translations. Original and public uncompressed hashes are
different identities. Archived inputs were opened recursively and their text members translated separately.
Large omitted relations, ledgers and caches are explicitly listed; their absence is not complete raw coverage.
Agent reports and transcripts are excluded.

## Reproduce

From this receipt directory, validate retained hashes and recompute the bounded outcome without a build:

```sh
python3 -B rerun.py saved
python3 -B rerun.py unpack --work /tmp/time-widening-calibration-evidence
```

Saved mode executes zero native runs. Its exit 0 means the evidence still yields the recorded verdict,
including a killed or inconclusive verdict. It does not turn a failed native gate into a pass.

After the source branch is published, repeat its local controls in a fresh directory:

```sh
python3 -B rerun.py native --work /tmp/time-widening-calibration-fresh \
  --lock /tmp/roundhouse-shared-host.lock
```

Use the same coordination lock path as every other workload on the host. `--source /path/to/checkout`
can supply an existing checkout at the exact public source pin. The helper retains stdout, stderr,
commands, flags and every expected failed exit. Killed native gates leave the outer helper at exit 1.
Local controls do not complete the omitted application, emission, prepared-suite or cost campaigns.
Native timings are fresh observations; never overwrite this receipt or treat one pair as replication.

## Limits and next step

The Time control is a new synthetic condition; historical exports and the failed historical positive-control expectation remain visible. Membership and coverage come from saved public observations, with an unobserved interval tick. Existing opacity and renderer limits remain. No compiler build, application execution or native soundness improvement follows from these Python controls.

Use the calibrated paired component guard on separately labeled fresh semantic-candidate exports. Keep membership and coverage separate, preserve the interval-read hole, and reduce hostname and nil job_id witnesses independently.
