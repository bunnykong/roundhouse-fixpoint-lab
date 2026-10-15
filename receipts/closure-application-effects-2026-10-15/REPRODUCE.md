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
git -C "$PUBLIC_SOURCE" checkout 37a076d89d02959493b70ec954aabcc3e60544f5
```

Build with the pinned Rust toolchain and native-test Ruby 3.4.4, using the host’s shared resource lock.
For app observations use CRuby 4.0.7 and the [public observer](../../tools/observers/README.md).
From the lab root, with public source built and the chosen app pin checked out:

```sh
python3 tools/observers/obs.py run --bin ./fresh-results/target/release/roundhouse \
  --app campfire --input ./inputs/campfire --jobs 1 \
  --settings unset-v1-a1,1-v0-a0,repeat-v1-a1 \
  --flags receipts/closure-application-effects-2026-10-15/profile.json --label closure-application-effects-fresh
```

The source contains `closure_application` native fixture and breaker tests. The complete registered evidence
uses 38 app cells and sixteen fixture settings; this focused recipe does not replace that matrix. The native
helper replays the saved 38 cells through the published checker; it never reruns Discourse or rehashes the
omitted large raw streams. Both interpreter versions apply to base fixtures; twins use 4.0.7.

The focused native helper is syntax-checked and was not executed during publication:

```sh
SOURCE=./compiler OUTPUT=./fresh-native \
HOST_LOCK_WRAPPER=./tools/observers/lock.py HOST_LOCK_FILE=./host-locks/heavy.lock \
  bash native.sh
```

Resolve all four paths to absolute paths before invocation. The helper owns its Cargo target and uses four jobs.
Inspect the retained exact native selection and counters; this focused control is not the full app matrix.

The actual published checker and its synthetic regression assertions can be exercised without an analyzer:

```sh
python3 replay_apps.py
python3 check_regressions.py
```

The replay includes the complete 38-cell snapshot and a negative with the two completed controls omitted.
The six original regression assertions are retained; only fixture/scan paths are portable.

The focused native helper is syntax-checked and was not executed during publication:

```sh
SOURCE=./compiler OUTPUT=./fresh-native \
HOST_LOCK_WRAPPER=./tools/observers/lock.py HOST_LOCK_FILE=./host-locks/heavy.lock \
  bash native.sh
```

Resolve all four paths to absolute paths before invocation. The helper owns its Cargo target and uses four jobs.
Inspect the retained exact native selection and counters; this focused control is not the full app matrix.

The actual published checker and its synthetic regression assertions can be exercised without an analyzer:

```sh
python3 replay_apps.py
python3 check_regressions.py
```

The replay includes the complete 38-cell snapshot and a negative with the two completed controls omitted.
The six original regression assertions are retained; only fixture/scan paths are portable.
