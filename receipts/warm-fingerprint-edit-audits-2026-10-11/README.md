# Fingerprint edit audits stop after the three Mastodon comparisons

**Inconclusive; three edited comparisons and cost gates incomplete.** This is an unscored public reference for the October 14–20 research week.
The supplied measurements were made on October 11, 2026; publication packaging adds no native measurement.
The next step is below. The full verdict, including failed and incomplete gates, is retained.

## Recorded result: F42

On October 11 condition `warm-fingerprint-edit-audits-20261011-fast-six-audit`, fingerprint reuse is **inconclusive for the expanded campaign**. All three Mastodon edits pass byte/hash/extra/guard audits, shadow, separate cold and same-path parent parity, with 60,698, 60,698 and 60,701 input comparisons. Only three of six required edited comparisons finish. The Discourse seed passes its audit but is not an edited comparison; its first edited parent command is interrupted at the deadline. Audit-off five-pair useful-cost replication and the separate three-app cold campaign do not complete. Audit-on warm wall excluding shadow is 174.759–181.832 s versus 7.242–7.479 s whole cold, one pair per edit on a shared host, a profile not a benchmark. Missing coverage blocks promotion; the available evidence does not refute the bounded F35 optimization or meet the 100 ms goal.

[Fact row](https://github.com/bunnykong/roundhouse/blob/fixpoint-research/docs/research/facts.md#f42)

## Source and condition

- Public branch: [`warm-fingerprint-edit-audits`](https://github.com/bunnykong/roundhouse/tree/warm-fingerprint-edit-audits).
- Public source: [`c5dfc633`](https://github.com/bunnykong/roundhouse/commit/c5dfc633b0b28e0417934b701d92cacfdcc6a5b1).
- Recorded source: `7166f3e576f3c1e68b454556838013a0c5479f2c`; public base: `d9ec78c31db361db8818b13153e5ddddee484c57`.
- [Pins and toolchains](pins.json); [structured outcome](summary.json).
- [Original/public file hashes, archive members and omissions](recorded-files.json).

The source is a clean snapshot with descriptive labels.
Original binary hashes identify the measured compiler. A translated snapshot has not been rebuilt as a native
compiler during publication. Source labels, test markers and flag names have mechanical translations;
the campaign and calibration helpers also accept portable input and host-lock locations.
Rust/Cargo is 1.98.1, app Ruby is 4.0.7 with Prism, library controls use Ruby 3.4.4, and Python is 3.9+.
Each raw condition records its input pins, flags, source/runner identities and actual exit.

## Evidence

- [final-summary.json.xz](raw/evidence/final-summary.json.xz)
- [results.json.xz](raw/week/warm/runs/fast-six-audit/results.json.xz)
- [runs.json.xz](raw/week/warm/runs/fast-six-audit/runs.json.xz)

All raw files are under `raw/`. Read an xz member with `xz -dc FILE.xz` or use the unpack command below.
Compression is lossless after the declared text translations. Original and public uncompressed hashes are
different identities. Archived inputs were opened recursively and their text members translated separately.
Large omitted relations, ledgers and caches are explicitly listed; their absence is not complete raw coverage.
Agent reports and transcripts are excluded.

## Reproduce

From this receipt directory, validate retained hashes and recompute the bounded outcome without a build:

```sh
python3 -B rerun.py saved
python3 -B rerun.py unpack --work /tmp/warm-fingerprint-edit-audits-evidence
```

Saved mode executes zero native runs. Its exit 0 means the evidence still yields the recorded verdict,
including a killed or inconclusive verdict. It does not turn a failed native gate into a pass.

After the source branch is published, repeat its local controls in a fresh directory:

```sh
python3 -B rerun.py native --work /tmp/warm-fingerprint-edit-audits-fresh \
  --lock /tmp/roundhouse-shared-host.lock
```

Use the same coordination lock path as every other workload on the host. `--source /path/to/checkout`
can supply an existing checkout at the exact public source pin. The helper retains stdout, stderr,
commands, flags and every expected failed exit. Killed native gates leave the outer helper at exit 1.
Local controls do not complete the omitted application, emission, prepared-suite or cost campaigns.
Native timings are fresh observations; never overwrite this receipt or treat one pair as replication.

## Limits and next step

The Discourse seed and saved F30 checks do not count toward edited replication. Audited walls include duplicate fingerprint construction and cannot establish audit-off latency. The legacy codec is unchanged. The default library run retains 43 failures and two ignored cases; later integration binaries do not execute. App-cache payloads are omitted with their recorded hashes and sizes. No five-pair distribution, broader cost result or complete six-edit packet exists.

Reserve the host, finish the three edited Discourse audits, then run five alternating audit-off pairs per edit and the separate parent/candidate cold campaign. Keep the codec experiment separate and report validation time independently.

## Complete the native campaign

The [fresh campaign recipe](runners/native-campaign.sh) clones the exact public candidate, parent and
lab inputs, builds each compiler, runs all edited audits, checks them before five-pair audit-off profiling,
and retains the separate three-app cold campaign. The bundled [host lock helper](runners/flock.py)
uses the existing shared/exclusive lock protocol. Use a reserved host window and the same lock as other work.

```sh
bash runners/native-campaign.sh /tmp/fingerprint-reserved /tmp/roundhouse-shared-host.lock
```

Run the local native mutation controls first. This long recipe was syntax-checked during publication;
it was not executed. It creates fresh observations and does not fill the missing historical comparisons.
The final JSON reports campaign completion, parity, total-warm regression, useful cost and 100 ms separately;
the process exit alone is not a useful-cost verdict. Native command logs retain app diagnostic exits.
