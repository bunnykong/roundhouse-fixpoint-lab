# Latest writer returns

Unscored research reference.

## Fact F64

On condition `latest-writer-returns-20261015-campfire`, each declared writer gets one cell pre-declared Pending; updates replace its latest result and join through the storage normalizer. Campfire's #521 circular-configuration fixture and #964 case pass with the history stabilizer off. At unset order with verification and audit on, two fresh runs reproduce 14 descents each. The verdict remains inconclusive: a frozen collector stalled on an 11.8 MB audit line, and the replacement extractor was written after measurements began. Whole-registry coverage is also unfulfilled; larger apps were not run. Independent light review upholds this verdict.

## Condition and pins

Public condition: `latest-writer-returns-20261015-campfire`.
[Pins](pins.json) identify the public source, app commits and toolchains.
[Source README](https://github.com/bunnykong/roundhouse/blob/7909e786000bae64931e4e0c51c4c163ca14f241/research/latest-writer-returns/README.md) documents the public flags.
[Source equivalence](source-equivalence.json) binds each changed native file. The public Rust port is uncompiled.

## Receipt label map

- `s6-strict-replace-v1` → `latest-writer-returns-20261015-campfire`.
- `s6-current-returns-card-v2` → `current-return-ledger-replay-20261015`.

These raw spellings appear only in the map and unchanged evidence. `raw/` preserves exact decompressed bytes;
`derived/` and `native/` disclose public spelling, path or stated selection copies. The [manifest](manifest.json)
records original, public uncompressed and file hashes, report hashes and omissions. Originals were not edited.

## Evidence and limits

The frozen verdict still returns inconclusive. Its collector stalled on an 11,854,700-byte audit line; the later
extractor carries an explicit freeze gap. Twenty fixture cells are valid, and both required cases pass.
The two retained fresh unset-order observations use verification and audit on and reproduce 14 descents each.
The saved check uses the frozen order and resolver over their native ledgers and complete return/reference basis.
This is a count check; it supplies no causal attribution or follow-up design.

Coverage remains partial: 883 observed slots against 8,849 final registry rows. Larger apps were not run.
The light review checks the decisive repeats and native laws, rather than the whole matrix. Its initial law launch
omitted the required flag and failed two guards; the corrected launch passes all nine laws. Both logs remain.
The original frozen verdict, collector and tests were not repaired to make this result pass.

## Reproduce

From this receipt directory:

```sh
python3 rerun.py saved
python3 -B -m unittest discover -s native -p 'test_*.py' -v
```

These verify retained evidence and synthetic checker controls with zero native analyzers. For focused native checks,
use the exact public source pin and the [public observer lock helper](../../tools/observers/README.md):

```sh
SOURCE=$PWD/compiler OUTPUT=$PWD/native-output \
  HOST_LOCK_WRAPPER=$PWD/tools/observers/lock.py HOST_LOCK_FILE=$PWD/host-locks/heavy.lock \
  bash native.sh
```

Generate the compiler's documented test fixtures first. The shell recipe is syntax-checked and was not executed
during publication. It does not repeat the full app, fixture, emission or suite campaign. Archived helpers retain
original hash guards; their historical native claims refer to the original recorded source and inputs.
