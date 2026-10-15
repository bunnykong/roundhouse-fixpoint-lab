# Reproduce the bounded observation

Run `python3 rerun.py saved` first; it invokes no analyzer. Every fresh run is a new unscored condition.
Acquire public inputs only, at the commits in [pins.json](pins.json). Original command/exit/flag records remain
in the [manifest](manifest.json); do not infer a completed app stage from a focused control.

```sh
PUBLIC_SOURCE=./compiler
OUTPUT=./fresh-results
export CARGO_BUILD_JOBS=4
export CARGO_TARGET_DIR="$PWD/$OUTPUT/target"
git clone https://github.com/bunnykong/roundhouse.git "$PUBLIC_SOURCE"
git -C "$PUBLIC_SOURCE" checkout a3c3b4502dbc550387d6fddbcf491093b575f5e6
```

Build with the pinned Rust toolchain and native-test Ruby 3.4.4, using the host’s shared resource lock.
For app observations use CRuby 4.0.7 and the [public observer](../../tools/observers/README.md).
From the lab root, with public source built and the chosen app pin checked out:

```sh
python3 tools/observers/obs.py run --bin ./fresh-results/target/release/roundhouse \
  --app campfire --input ./inputs/campfire --jobs 1 \
  --settings unset-v1-a1,1-v1-a1,2-v1-a1,repeat-v1-a1 \
  --flags receipts/schedule-row-attribution-2026-10-15/profile.json --label schedule-row-attribution-fresh
```

The source snapshot is an observation build. Use `RH_CONTRIBUTOR_VALUES=1` with the explicit research profile;
keep raw dumps and reason/value observers separate. Diagnostic probes are interventions, not safe repairs.
The saved catalog reduction retains capped statuses and new varying rows. Issue #964 has a separate
seven-table fixture/reducer; never fill the strict ten-table observer’s missing tables.
