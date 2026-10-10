# Destructuring matrix

CRuby 4.0.7; 4 receivers × 19 iterators × 7 parameter shapes = 532 flows, 836 selected sink slots.
Use S3 flags with the shared-type build; `RH_SOUND=1` activates each repair.
Pins and flags are in [conditions.json](conditions.json). Public equivalents:
initial [`4eaf354c`](https://github.com/bunnykong/roundhouse/tree/4eaf354c46f48acbde2239b15fcc5a2de41f61dc), repaired [`c508e18b`](https://github.com/bunnykong/roundhouse/tree/c508e18b996d05ff33844ddcfd654557eeddf6c0).
[prototypes.json](../prototypes.json) maps the local historical SHAs to comment-only equivalents.

```sh
python3 -B receipts/F20/recompute.py
python3 -B receipts/inference.py record F20 --output _work/traces
python3 -B receipts/inference.py rerun F20 --output _work/F20
```

The reduction checks the saved values and reports unique rejected slots: 155 baseline,
116 initial, 0 repaired; the initial repair introduces 51 regressions and fixes 90 slots.
The repaired exporter still marks 362 selected slots unresolved. Check both counts;
zero rejections alone cannot establish coverage. Historical source hashes remain in trace metadata.
