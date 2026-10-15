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
git -C "$PUBLIC_SOURCE" checkout ec932bb31fb32b2659bc3707eb536fa0e36ba484
```

Build with the pinned Rust toolchain and native-test Ruby 3.4.4, using the host’s shared resource lock.
For app observations use CRuby 4.0.7 and the [public observer](../../tools/observers/README.md).
From the lab root, with public source built and the chosen app pin checked out:

```sh
python3 tools/observers/obs.py run --bin ./fresh-results/target/release/roundhouse \
  --app campfire --input ./inputs/campfire --jobs 1 \
  --settings unset-v0-a0,1-v0-a0,2-v0-a0,repeat-v0-a0 \
  --flags receipts/declared-contributor-join-2026-10-15/profile.json --label declared-contributor-join-fresh
```

Repeat both off/off and on/on observer pairs, holding each pair fixed. Inspect module and includer returns
separately, the 23 added aliases and the absent stored callback. Larger-app stages remain unrun.

The focused native helper is syntax-checked and was not executed during publication:

```sh
SOURCE=./compiler OUTPUT=./fresh-native \
HOST_LOCK_WRAPPER=./tools/observers/lock.py HOST_LOCK_FILE=./host-locks/heavy.lock \
  bash native.sh
```

Resolve all four paths to absolute paths before invocation. The helper owns its Cargo target and uses four jobs.
Inspect the retained exact native selection and counters; this focused control is not the full app matrix.

The focused native helper is syntax-checked and was not executed during publication:

```sh
SOURCE=./compiler OUTPUT=./fresh-native \
HOST_LOCK_WRAPPER=./tools/observers/lock.py HOST_LOCK_FILE=./host-locks/heavy.lock \
  bash native.sh
```

Resolve all four paths to absolute paths before invocation. The helper owns its Cargo target and uses four jobs.
Inspect the retained exact native selection and counters; this focused control is not the full app matrix.
