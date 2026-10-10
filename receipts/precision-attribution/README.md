# Pairing and control sensitivity

Five public apps at [the lab pins](../public-app-pins.json); main `194f26cf` without stage flags,
staged `92844f68` with S3 flags. Exact flags and priority are in [condition.json](condition.json).
`diff_rows.py` pairs app-relative file, byte start/end and kind, then uses owner, symbol, root
and traversal occurrence for duplicates; inferred type is never a pairing key.
`collect_causes.py` documents the declared priority. `loss-controls.jsonl` retains the 4,823
paired loss rows and their control responses; `controls-counts.json` retains each arm's census.

```sh
python3 -B receipts/precision-attribution/recompute.py
sh corpus/fetch.sh
python3 -B receipts/precision-attribution/rerun.py
```

Priority allocation is a sensitivity description. Controls overlap; category recovery can erase
runtime arms or worsen other rows. Neither recovery totals nor eligible guards count sound repairs.
The paired summary preserves unmatched and missing-annotation counts separately.

The live census builds [the public observation helpers](../../patches/precision-census/) against
the two exact pins with four Cargo jobs. `--apps campfire` selects one app; `--arms main S3 S2b
S2c allarms-only join-only S3-no-allarms S3-no-join S3-no-slots S3-no-tail` selects all controls.
Each command is `prec-census check --continue .` at the pinned app root; no app boot is needed.
The runner sets `RH_PRECDIFF_ROWS` and `RH_PRECDIFF_TRACE=1`, and records new rows separately.
Native hash order is uncontrolled, so a new run may differ from the retained historical observations.

The public-source recheck on Campfire pairs all 32,535 annotated rows, with 11 category
losses and no gains. [release-recheck](release-recheck/) retains this separate observation.
