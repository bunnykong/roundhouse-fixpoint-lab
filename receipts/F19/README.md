# Pending returns: runtime comparison

CRuby 4.0.7; four synthetic programs; final exported types and recursive graph grammars.
All arms use the six S3 flags in [conditions.json](conditions.json) with the shared-type build.
The baseline has no precision flag. `RH_PREC_PENDBOT=1` stores pending returns as bottom and
propagates it through dispatch; `RH_PREC_PENDVAR=1` keeps pending returns unresolved.

Public equivalents: bottom [`6769165f`](https://github.com/bunnykong/roundhouse/tree/6769165fbc578751f5834234c579d306159223e2), pending-Var [`3985d9f7`](https://github.com/bunnykong/roundhouse/tree/3985d9f7006ea4b20f8c33281d62b3d0fd70d738).
[prototypes.json](../prototypes.json) records the historical SHAs and comment-only mapping.
The original histories have internal labels and nonconforming author metadata, so those histories
remain local. The published equivalents retain the executable code of each measured snapshot.

```sh
python3 -B receipts/F19/recompute.py
python3 -B receipts/inference.py record F19 --output _work/traces
python3 -B receipts/inference.py rerun F19 --output _work/F19
```

The reduction checks each value against the saved grammar: baseline 0, bottom 52
(7/10/4/31 by program), pending-Var 0. It also checks that the five conversion chains retain
Integer in the passing variant. Unknown exports accept any value; this covers these programs only.
Trace metadata uses repository-relative paths and records both historical and relocated source hashes.
