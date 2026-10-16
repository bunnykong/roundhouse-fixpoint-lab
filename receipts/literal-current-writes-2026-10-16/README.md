# Literal current writes

Unscored research reference.

## Fact F65

On condition `literal-current-writes-20261015-chatwoot`, typing empty literals from their declarations and current writes, without an old stamp, is killed on Chatwoot. It rejects heatmap Integer and nil values that the control admits; CRuby reproduces both. The writer set missed nested element writes. Independent light review reproduces the counterexample. This rejects the tested repair, not all literal feedback.

## Condition and pins

[Pins](pins.json) identify the public compiler, inputs and toolchains.
[Source README](https://github.com/bunnykong/roundhouse/blob/15b142ddcb10c11a7e5c9a97107a7f5b9dc5cbbf/research/literal-current-writes/README.md) describes the public controls.
[Source equivalence](source-equivalence.json) binds the changed native files. The public Rust port is uncompiled.

## Receipt label map

- `s9-literals-v1` → `literal-current-writes-20261015-chatwoot`.

Raw spellings occur only in this map and unchanged evidence. The [manifest](manifest.json) records original,
public uncompressed and file hashes. `raw/` preserves exact decompressed bytes; `derived/` and `native/`
contain disclosed public spelling or path copies. Original evidence was not edited. Reports remain outside Git;
their hashes bind the original builder and upheld independent review.

## Evidence and limits

The packet retains the exact changed heatmap types, CRuby values and probe shapes, all four row comparisons,
frozen admission checker and 83 checker tests. The control admits the sparse Integer/nil example; the candidate
prints nested String arrays and rejects it. The complete input also supplies an Integer counterexample.
The independent light review runs two fresh Chatwoot cells and the witness; it does not repeat the full matrix.

The final library checks pass 1,258 tests in each mode, with 26 default ignores. Earlier fixture-setup failures
and their killed receipt remain separate. `data_factory_constants` was never compiled by this library-only gate.
Other changed values remain unwitnessed; Discourse, emission and typing ceilings were not measured.

## Reproduce

From this receipt directory:

```sh
python3 rerun.py saved
python3 -B -m unittest discover -s native -p 'test_verdict.py' -v
```

The saved command verifies hashes and replays bounded verdict/admission checks, not the omitted app streams.
The checker commands exercise retained synthetic controls. Both use zero native analyzers. Python source ports
retain assertions; the compressed boundary fixture is read losslessly by the portable regression helper.
Synthetic freeze tests hash the public source-equivalence record in place of the omitted narrative protocol.
The original protocol hash stays in the recorded freeze; assertions and the required-file count are retained.

For a focused native check, use the pinned compiler and the [public lock helper](../../tools/observers/README.md):

```sh
SOURCE=$PWD/compiler OUTPUT=$PWD/native-output \
  HOST_LOCK_WRAPPER=$PWD/tools/observers/lock.py HOST_LOCK_FILE=$PWD/host-locks/heavy.lock \
  bash native.sh
```

Prepare documented compiler fixtures first. The shell recipe is syntax-checked, unexecuted during publication,
and does not repeat the full app matrix or default suite. Full streams, binaries and app copies are omitted;
retained compact receipts preserve their captured identities and the original failures.
