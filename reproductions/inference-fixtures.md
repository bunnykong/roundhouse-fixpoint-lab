# Historical inference fixtures

These synthetic programs retain the inputs for the public research additions.
Their [conditions and raw comparisons](../receipts/README.md) are historical observations.

## S3 flags with shared types

The pending and destructuring comparisons use a build with shared types and:

```sh
RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq RH_FOLD_TAIL=1
```

[Prototype pins](../receipts/prototypes.json) map each historical snapshot to a public
equivalent whose code differs only in comments. Pending adds `RH_PREC_PENDBOT=1` or
`RH_PREC_PENDVAR=1`; destructuring adds `RH_SOUND=1`.

## Long-name dispatch

[long_name_dispatch/](long_name_dispatch/) retains a three-file chain with a 94-byte ASCII
method name. The old scanner cutoff was 80 bytes; public staged `92844f68` includes the repair.
Compare names scanned for scheduling with names used by dispatch, an extra round, and shuffled visits.
The [receipt](../receipts/long-name/README.md) retains the type and verification outputs.

## Pending bottom

[pend_bot/](pend_bot/), [pend_rec/](pend_rec/), [pend_locals/](pend_locals/) and
[pend_census/](pend_census/) exercise reflective ivars, dynamic methods and recursive walkers.
Bottom means non-return; surviving pending inference exports as unresolved `untyped` in the passing variant.
The [receipt](../receipts/F19/README.md) checks recorded values against final and graph grammars.

## Destructuring

[destructuring_matrix/generate.py](destructuring_matrix/generate.py) crosses four receivers,
nineteen iterators and seven parameter shapes: 532 flows and 836 selected sink slots.
Generate in a scratch copy from this repository root:

```sh
mkdir -p _work
cp -R reproductions/destructuring_matrix _work/destructuring_matrix
python3 _work/destructuring_matrix/generate.py _work/destructuring_matrix > _work/selected-slots.txt
```

Keep the selected slots fixed. Check runtime rejections and unresolved coverage together;
unresolved exports accept values as unknown. The [receipt](../receipts/F20/README.md) retains both checks.
