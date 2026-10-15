# Fingerprint six edit gates

Inconclusive: six audits pass; candidate cost replication is absent; review upheld. This packet is an unscored public reference; publication packaging ran no native compiler.

## Fact F48

On October 15 condition `fingerprint-six-edit-gates-20261015-1fbfee1a`, the six edited audits all pass for native candidate `1fbfee1a` against parent `d9ec78c3`: three edits each on Mastodon `163f96ce` and Discourse `343b20f9`, with zero disagreements across 60,698–60,701 and 136,947–136,952 input/extra/guard comparisons per edit respectively, plus shadow, separate-cold and same-path parent parity. Independent review upholds the inconclusive verdict and rechecks the raw receipts; additional Mastodon schedule probes preserve parity within each schedule without establishing schedule independence. Parent profiles complete 1/6, candidate cost pairs 0/30 and broader cold pairs 2/15. Thus this closes F42's six-edit correctness coverage gap while leaving the cost gates unassessed. No candidate timing, useful-cost, total-warm regression or 100 ms claim follows. The cold oracle's reason omission, record normalization and diagnostic-comparison scope remain limits; exact incremental replay and soundness remain open.

## Conditions and source

Public condition: `fingerprint-six-edit-gates-20261015-1fbfee1a`. Problem 5; six edited correctness audits, zero of thirty candidate cost pairs, no timing claim.
The [pins](pins.json) distinguish recorded sources, their published bases and the prepared source snapshot.
[Source equivalence](source-equivalence.json) binds each changed compiler file to its measured hash.
The [public source](https://github.com/bunnykong/roundhouse/tree/0a62c8ef1dcd2f998fb75a839dd3a0c50cbf4c83) is on `fingerprint-six-edit-gates`.
Only declared flag, example and path translations separate its compiler files from the measured source.
The snapshot was not recompiled during publication. Source helper adaptations have syntax checks only.
The registration has an earlier Git commitment; its hash and chronology are retained in the evidence.


## Receipt label map

Historical identifiers in byte-preserved machine records map to these public conditions:

- `fingerprint-gates-20261015-1fbfee1a` → `fingerprint-six-edit-gates-20261015-1fbfee1a`.

Schedule/configuration suffixes retain their meanings. A replacement registration is a separate condition.
Raw receipt bytes were never edited to rename a condition. `raw/` files retain original bytes after
lossless decompression. `derived/` files are explicitly normalized publication copies with workstation
paths and internal labels replaced. Their original and published hashes differ and are both retained.
Derived file references describe the recorded layout; use the manifest to locate retained files.
No numerical outcome, failed exit or type shape was repaired during packaging.

## Evidence and review

The [manifest](manifest.json) lists every retained file, original SHA-256, public uncompressed SHA-256,
published-file SHA-256, archive layers and explicit omissions. `experiment/` identifies measured evidence;
`independent-review/` identifies the separate review's native receipts and reductions.
The verdict above includes the review's conclusion, including any overturned builder confirmation.

Full compiler/dependency copies, app caches, binaries, reports and transcripts are omitted. Large repeated
relations or ledgers have hashes and sizes in the omission list; compact identity sets, full named
counterexamples, command records and structured reductions remain. Archives were opened recursively,
and text members were inspected separately. Compressed files require decompression before inspection.

One original seed-check capture combines a lock-wait line with JSON. It is preserved whole as a command
capture and is not counted as a parsed structured result; the complete audit reducer uses separate records.

## Reproduction and limits

```sh
python3 rerun.py saved
```

This checks hashes and recomputes the decisive bounded counts or negative witness from retained evidence.
An exit zero means the saved reduction agrees, including killed or incomplete experimental gates.
It is not a new native confirmation. [Native instructions](REPRODUCE.md) and `native.sh` provide focused
controls in a fresh source/output copy. Their recipes were syntax-checked, without a native replay here.
The original full commands, flags and exits remain in the manifest-indexed evidence. Broad campaign,
default-suite, app export and integration failures remain recorded; focused controls do not replace them.
All five public research problems stay open.
