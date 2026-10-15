# Ownership pending composition

Killed: value equality passes, storage laws fail. This is an unscored research reference. The lead reviews the prepared publication commits.

## Fact F51

On October 15 condition `ownership-pending-composition-20261015-e248de81`, composing declared writer ownership (F44) with Pending as an identity (F45) keeps all ten Campfire `90b33002` value digests equal across unset/1/2/independent-repeat with verification and audit on. The composition is nevertheless **killed by its storage-law gate**: stored Array and Hash contents arrive unnormalized, yielding 177 idempotence failures among 1,296 pairs and six Pending-identity failures among 36 samples, exit 101. Independent review upholds the kill and reproduces the counts under every requested schedule. It also shows that audit and verification can each change observed reasons. F45 already records these counts; this is the composition experiment itself. Scope is Campfire and the finite native law samples; exact-storage inequality establishes neither runtime value loss nor reason-level schedule independence.

## Condition and source

Public condition: `ownership-pending-composition-20261015-e248de81`. Campfire only; 36 native law samples; no runtime value-loss claim.
The [pins](pins.json) distinguish recorded and proposed public sources, app inputs and toolchains.
The [public source](https://github.com/bunnykong/roundhouse/tree/ff36c138afce581bc77c22a2d3c475ab8d3a3e23) is the proposed `ownership-pending-composition` snapshot. The [source equivalence](source-equivalence.json) records every changed compiler file after declared flag, output-prefix, identifier and path translations. This public snapshot was not recompiled.

## Receipt label map

Historical machine identifiers map to these descriptive public conditions:

- `c4c5-compose-20261015-e248de81` → `ownership-pending-composition-20261015-e248de81`.
- `c4c5-tags-auditoff-20261015-e248de81` → `ownership-pending-composition-audit-off-20261015-e248de81`.
- `c4c5-tags-noverify-20261015-e248de81` → `ownership-pending-composition-no-verification-20261015-e248de81`.
- `rv-c4c5-auditon-noverify-20261015-e248de81` → `ownership-pending-composition-audit-only-review-20261015-e248de81`.
- `rv-c5-card4-debug-oracle-v1` → `parameter-storage-normal-form-debug-review-v1`.

Schedule/configuration suffixes retain their meaning. Original data was not edited to rename a condition.
`raw/` preserves exact bytes after lossless decompression. `derived/` contains disclosed normalized copies,
with original, public uncompressed and published-file hashes recorded separately. Their path references describe
the recorded layout; the [manifest](manifest.json) locates each retained member. Native numerical outcomes,
type shapes, failed exits and missing observations are retained. Series `a` in historical three-app records
means ownership enabled; `baseline` means the matched control.

## Evidence and review

The manifest binds builder/review report hashes, all retained members, opened archive layers and omissions.
Reports and transcripts are not copied into Git. `experiment/` identifies the builder's measurements;
`independent-review/` identifies the separate review's evidence. Repeated diagnostic streams, full large dumps,
source/dependency/app copies and binaries are omitted explicitly. Captured identities remain in command receipts;
multi-gigabyte omitted streams are not rehashed during publication. No original measured source was modified.

The registered default suite remains red (1,142 passed, two failed, 20 ignored); integration suites stopped before execution. The extra audit-on/verification-off control changes reason attribution without changing the storage-law kill.

## Reproduction

```sh
python3 rerun.py saved
```

This verifies the packet's hashes and recomputes its bounded counts or negative comparisons from saved evidence.
Zero means the saved reduction agrees, including killed or incomplete gates. It runs no native analyzer.
The [native recipe](REPRODUCE.md) describes focused controls on public source/input copies. It was syntax-checked,
without a new Cargo build, app campaign, integration run or benchmark during packaging.
All public inference frontiers remain open.
