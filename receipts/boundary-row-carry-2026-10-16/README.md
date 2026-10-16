# Boundary row carry

Unscored research reference.

## Fact F67

On condition `boundary-row-carry-20261016-campfire`, carrying derived boundary rows and retracting unobserved Pending placeholders is killed on Campfire, with and without deduplication. At unset order with verification and audit on, settlement still rewrites 26 values, or 584 with latest-writer replacement. Both layered variants retain three forbidden event families. Deferring Unresolved to quiescence did not remove premature labels. Independent light review reproduces the failures. Forem and Chatwoot were not run; this rejects the implementation, not stratification in general.

## Condition and pins

[Pins](pins.json) identify the public compiler, inputs and toolchains.
[Source README](https://github.com/bunnykong/roundhouse/blob/b0b2cd145f8128d9c9597e70076eb7b04304823e/research/boundary-row-carry/README.md) describes the public controls.
[Source equivalence](source-equivalence.json) binds the changed native files. The public Rust port is uncompiled.

## Receipt label map

- `c6c-boundary-carry-4cd2f8f6-v2` → `boundary-row-carry-20261016-campfire`.
- `rv-c6c-copied-input-unset-v1-a1` → `boundary-row-carry-copied-input-review`.

Raw spellings occur only in this map and unchanged evidence. The [manifest](manifest.json) records original,
public uncompressed and file hashes. `raw/` preserves exact decompressed bytes; `derived/` and `native/`
contain disclosed public spelling or path copies. Original evidence was not edited. Reports remain outside Git;
their hashes bind the original builder and upheld independent review.

## Variants

The native keys are retained: C is control; DS adds deferral and stratification; N adds deduplication;
DSN combines both; K adds latest-writer replacement; KN, KDS and KDSN combine those named changes.
D defers without stratification. A and AN are the stratified result families without and with deduplication.
These keys identify recorded variants, not separate public facts.

## Evidence and limits

The frozen reducer has 301 mandatory passes, 208 failures and no unavailable mandatory records. Both
stratified families are killed. At unset order with verification and audit on, DS and DSN each rewrite 26
Pending values; KDS and KDSN each rewrite 584. These are calls, not distinct inputs. Final Pending is zero.
Both layered variants retain reference-switch, late-Unresolved and placeholder-flip events.
The light review reruns DS and KDSN at that setting and independently reduces the saved matrix.

The implementation does not cover complete canonical input slots. Its outside-set counter counts rejected
lookups; its zero upper-stratum Unresolved counter is not a usable answer census. Neither establishes the kill.
The default library stage retains two failures, with 1,255 passes and 29 ignores. Selected integrations compiled
but did not execute; `data_factory_constants` was excluded. The queued doc stage was interrupted, exit 130.
Forem and Chatwoot remained gated off. No general refutation of stratification follows.

## Reproduce

From this receipt directory:

```sh
python3 rerun.py saved
python3 -B native/regressions.py
python3 -B -c 'import sys; sys.path.insert(0, "native"); import regressions; sys.exit(regressions.selftest())'
```

The saved command verifies hashes and replays bounded verdict/admission checks, not the omitted app streams.
The checker commands exercise retained synthetic controls. Both use zero native analyzers. Python source ports
retain assertions; the compressed boundary fixture is read losslessly by the portable regression helper.
Original helper hash guards are mapped to the previously published helper manifest.

For a focused native check, use the pinned compiler and the [public lock helper](../../tools/observers/README.md):

```sh
SOURCE=$PWD/compiler OUTPUT=$PWD/native-output \
  HOST_LOCK_WRAPPER=$PWD/tools/observers/lock.py HOST_LOCK_FILE=$PWD/host-locks/heavy.lock \
  bash native.sh
```

Prepare documented compiler fixtures first. The shell recipe is syntax-checked, unexecuted during publication,
and does not repeat the full app matrix or default suite. Full streams, binaries and app copies are omitted;
retained compact receipts preserve their captured identities and the original failures.
