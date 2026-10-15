# Native parameter reasons expose an arrival-dependent seed rule

**Killed by native seed arrival priority.** This is an unscored public reference for the October 14–20 research week.
The supplied measurements were made on October 11, 2026; publication packaging adds no native measurement.
The next step is below. The full verdict, including failed and incomplete gates, is retained.

## Recorded result: F38

On October 11 condition `native-parameter-reason-seeds-native-seed-arrival-breaker-v1-shared-host`, the opt-in native parameter repair is **killed by arrival-dependent initialization**. The same Bottom/Integer contributions through fold and bound produce Integer | Pending when Bottom arrives first, but Integer alone in reverse order. The native selector has four passes and one failure, exit 101; the failing assertion is retained. Standalone reason/value/grouping checks pass, and instrumented Campfire/Discourse parameter joins report zero input reason losses with repair enabled, without certifying all producers. Fresh exports keep F19's five missing selections and F29's 36 rejected observations. A reason-preserving join plus first-observation initialization does not establish per-writer completion or justified priority; the repair remains disabled by default.

[Fact row](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/facts.md#f38)

## Source and condition

- Public branch: [`native-parameter-reason-seeds`](https://github.com/bunnykong/roundhouse/tree/native-parameter-reason-seeds).
- Public source: [`af9c85be`](https://github.com/bunnykong/roundhouse/commit/af9c85bebe805ebe848528a92b6654fd19a4daf2).
- Recorded source: `134457dcac997512896e4239835130ae1425d1e4`; public base: `38403140379cd69759b0fe6247c6a8c4a48a37a9`.
- [Pins and toolchains](pins.json); [structured outcome](summary.json).
- [Original/public file hashes, archive members and omissions](recorded-files.json).

The source is a clean snapshot with descriptive labels.
Original binary hashes identify the measured compiler. A translated snapshot has not been rebuilt as a native
compiler during publication. Source labels, test markers and flag names have mechanical translations;
the campaign and calibration helpers also accept portable input and host-lock locations.
Rust/Cargo is 1.98.1, app Ruby is 4.0.7 with Prism, library controls use Ruby 3.4.4, and Python is 3.9+.
Each raw condition records its input pins, flags, source/runner identities and actual exit.

## Evidence

- [parameters.log.xz](raw/week/evidence/results/seed-arrival-v1/parameters.log.xz)
- [condition.json](raw/week/evidence/results/seed-arrival-v1/condition.json)
- [handoff-summary.json.xz](raw/week/evidence/results/handoff-summary.json.xz)

All raw files are under `raw/`. Read an xz member with `xz -dc FILE.xz` or use the unpack command below.
Compression is lossless after the declared text translations. Original and public uncompressed hashes are
different identities. Archived inputs were opened recursively and their text members translated separately.
Large omitted relations, ledgers and caches are explicitly listed; their absence is not complete raw coverage.
Agent reports and transcripts are excluded.

## Reproduce

From this receipt directory, validate retained hashes and recompute the bounded outcome without a build:

```sh
python3 -B rerun.py saved
python3 -B rerun.py unpack --work /tmp/native-parameter-reason-seeds-evidence
```

Saved mode executes zero native runs. Its exit 0 means the evidence still yields the recorded verdict,
including a killed or inconclusive verdict. It does not turn a failed native gate into a pass.

After the source branch is published, repeat its local controls in a fresh directory:

```sh
python3 -B rerun.py native --work /tmp/native-parameter-reason-seeds-fresh \
  --lock /tmp/roundhouse-shared-host.lock
```

Use the same coordination lock path as every other workload on the host. `--source /path/to/checkout`
can supply an existing checkout at the exact public source pin. The helper retains stdout, stderr,
commands, flags and every expected failed exit. Killed native gates leave the outer helper at exit 1.
Local controls do not complete the omitted application, emission, prepared-suite or cost campaigns.
Native timings are fresh observations; never overwrite this receipt or treat one pair as replication.

## Limits and next step

Standalone join matrices did not cover first-observation initialization. Instrumented loss counts are repeated events, not a complete origin census. Legacy Var, unique source ancestry and per-writer completion remain unresolved. The return accumulator is test-only. Flags-off library tests retain two inherited failures; no new app execution, native warm test or full CI pass is claimed.

Keep the failing seed test. Represent allocation, observed values, permanent unknown reasons and completion per writer before another native parameter repair. Retain F19/F29 failures and trace unresolved origins.
