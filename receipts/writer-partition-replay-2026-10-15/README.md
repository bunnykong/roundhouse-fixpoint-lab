# Writer partition replay

Upheld unchanged negative partition/replay counts. This is an unscored research reference, prepared for lead review.

## Fact F60

On October 15 condition `writer-partition-replay-20261015-four-pins`, F47's 2,104 plain-writer partition differences and 548 duplicate-round differences are identical across rebuilt F47 `eda0783b`, spine `ea3ec744`, strict-producer build `2233e2e7` and closure-application build `fdc00ee9`; independent review upholds the counts and source explanation. Each pin checks 32,928 round schedules per writer form, with 16,464 second-round replay comparisons. The spine and strict-producer build lack the reflective container-traversal and touched-destination repairs; their reflective path bypasses the bound, exceeding it in 19,056 schedules. The closure-application build restores the reflective bound and F47's reflective failure vectors. The missing touched-destination update causes the bound failure; the separate container traversal is not exercised by these direct-write fixtures. Every form retains all 418,656 sampled membership checks, which is not a universal soundness proof. Original law exits remain 101; census-wrapper success means negative counts reproduced. The fresh condition sets a 32 MiB stack; independent replay with F47's original unset stack setting gives the same counts. These synthetic results establish unchanged storage-law failures, not application accuracy or performance.

## Condition and pins

Public condition: `writer-partition-replay-20261015-four-pins`.
The [pins](pins.json) identify the already prepared public source snapshots and the recorded originals.
[Pins](pins.json) include all public app commits and toolchain versions; [source equivalence](source-equivalence.json) binds compiler spelling translations.

## Receipt label map

- `p2-v2-s4b-partition-f47-replay-v1` → `writer-partition-replay-20261015-four-pins`.
- `checker-f47-historical-env-v1` → `writer-partition-historical-stack-review-v1`.
- `checker-s4-harvest-mode-ablation-v1` → `writer-partition-harvest-mode-review-v1`.

Only this historical-label map preserves internal condition spellings in public prose. Raw data is not renamed.
`raw/` preserves original bytes after lossless decompression. `derived/` contains disclosed path, label, flag
and fixture-name translations with original, public uncompressed and published-file hashes. No measured
source or original receipt was edited. Native union fields, type shapes, numerical outcomes and failed exits
retain their meaning. Machine series keys retain their recorded values.

## Evidence and independent review

Each pin tests the same 32,928 round schedules per writer form; replay counts only 16,464 second rounds. All original law exits remain 101. A census exit of zero means the negative counts were collected. Reflection bypasses the bound on the spine and strict-producer pin; 19,056 counts exceeded limits, while every reflective-only harvest skips the boundary. The touched-destination repair causes the restored bound; the absent container traversal is not exercised by direct writes. The fresh runs set a 32 MiB stack. The review also reruns F47 with its historical unset stack and gets the same counts. Sampled membership is finite, not universal soundness. The two repair descendants are separate sources.

The [manifest](manifest.json) lists every retained member, report hash, decompressed archive and omission.
Reports, messages and transcripts are omitted from Git. Compiler/app/dependency trees, binaries and repeated
large streams are omitted; captured artifact identities remain in command receipts. Omitted multi-gigabyte
streams are not described as freshly inspected. Public input paths are portable examples.

## Reproduction

```sh
python3 rerun.py saved
```

This verifies retained hashes and recomputes the bounded saved comparisons. Zero means the recorded
confirmation, negative result or missing coverage was reproduced from saved evidence; it starts no analyzer.
The [native recipe](REPRODUCE.md) supplies focused public-source controls. Its commands are syntax-checked,
with no new Cargo build, native app matrix or performance measurement during packaging.
All six public inference frontiers remain open.
