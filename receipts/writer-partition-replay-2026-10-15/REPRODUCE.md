# Reproduce the bounded observation

Run `python3 rerun.py saved` first; it invokes no analyzer. Every fresh run is a new unscored condition.
Acquire public inputs only, at the commits in [pins.json](pins.json). Original command/exit/flag records remain
in the [manifest](manifest.json); do not infer a completed app stage from a focused control.

The retained native harness, original generator and four test-only source patches are indexed under
`experiment/harness` and `supplement/source-harness` in the manifest. Materialize a member with:

```sh
python3 rerun.py extract experiment/harness/writer_law_partitions.rs ./writer_law_partitions.rs
```

Apply the test-only registration to copies of each public pin and retain each pin’s existing helpers.
Use the exact effective flags in its original/census receipt, one test thread, four Cargo jobs, Ruby 3.4.4
and the shared host lock. The native selection is `writer_law_bound_partitions`; the observer selection is
`writer_partition_census`. Fresh runs set `RUST_MIN_STACK=33554432`; separately repeat F47 with it unset.
Original exit 101 is required. Recount failure rows and compare the full vectors, including stored shapes.
