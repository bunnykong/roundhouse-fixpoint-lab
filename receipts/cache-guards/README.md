# Cache guards and scheduling reads

Historical warm-replay v1 on staged `92844f68`; source delta is [warm-v1.patch](warm-v1.patch).
Applying it reconstructs Git tree `2e1db24b0744a0d6fb52c22ed171c52898a7fdd1`, a tree identity
rather than a published commit pin. All twelve source-file hashes are in
[v1-source-manifest.json](v1-source-manifest.json).
V2 is public `990137f742397a0aecc7efd14869f39c6412ba55` on `fixpoint-warm`.
[condition.json](condition.json) pins flags, sources and apps; [edits.json](edits.json) fixes the edits.
The raw v1 correctness records retain both cold and warm complete-state digests and mismatch contexts.

```sh
python3 -B receipts/cache-guards/recompute.py
sh corpus/fetch.sh
python3 -B receipts/cache-guards/rerun.py
python3 -B receipts/F15/rerun.py --work-dir _work/warm-v2
```

V1 restored cache guards as scheduler edges and failed five edited-input cold shadows.
V2 stores actual scheduling reads separately, isolates each evaluation's collector, and discards
guard-validation reads. `v2-tests.txt` retains the class-key guard regression; it creates no
scheduler edge. State values, dependency metadata and controller contexts all belong to replay correctness.

The v1 runner builds the pinned base plus patch with `cargo build --release --locked`,
then seeds and replays `roundhouse check --continue .` with the exact edits and flags.
`--apps mastodon --edit boolean` selects one case. Native hash order was uncontrolled;
the five-failure count belongs to the archived six-edit series. A fresh run retains its own results.
