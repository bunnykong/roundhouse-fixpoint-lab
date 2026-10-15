#!/usr/bin/env bash
set -euo pipefail
RECEIPT=$(cd "$(dirname "$0")" && pwd)
: "${SOURCE_ROOT:?Set the matching public source checkout}"
: "${NATIVE_OUTPUT:?Set a fresh output directory}"
: "${HOST_LOCK_TOOLS:?Set the directory containing flock.py}"
: "${HOST_LOCK_FILE:?Set the shared host lock file}"
mkdir "$NATIVE_OUTPUT"
NATIVE_OUTPUT=$(cd "$NATIVE_OUTPUT" && pwd)
git clone --quiet --no-hardlinks "$SOURCE_ROOT" "$NATIVE_OUTPUT/source"
cd "$NATIVE_OUTPUT/source"
git checkout --quiet 9c834701e82955f0ccad553ff2932cb5f8e3738d
export CARGO_TARGET_DIR="$NATIVE_OUTPUT/target" CARGO_BUILD_JOBS=4 CARGO_INCREMENTAL=0
export PYTHONDONTWRITEBYTECODE=1 RBENV_VERSION=3.4.4
for name in $(compgen -e); do
    case "$name" in RH_*|ROUNDHOUSE_*|PROBE_BASE) unset "$name";; esac
done
export RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq
heavy() { python3 "$HOST_LOCK_TOOLS/flock.py" "$HOST_LOCK_FILE" "$@"; }
cleanup() { heavy cargo +1.98.1 clean --manifest-path Cargo.toml > "$NATIVE_OUTPUT/clean.log" 2>&1; }
trap cleanup EXIT
run_test() {
    local label="$1" selector="$2"
    shift 2
    set +e
    heavy env "$@" cargo +1.98.1 test --release --locked --lib "$selector" -- \
        --include-ignored --nocapture --test-threads=1 > "$NATIVE_OUTPUT/$label.log" 2>&1
    local status=$?
    set -e
    printf '%s\n' "$status" > "$NATIVE_OUTPUT/$label.exit"
    cat "$NATIVE_OUTPUT/$label.log"
}
set +e
heavy cargo +1.98.1 test --release --locked --test warm_storage_fidelity -- --nocapture --test-threads=1 \
    > "$NATIVE_OUTPUT/storage.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$NATIVE_OUTPUT/storage.exit"
cat "$NATIVE_OUTPUT/storage.log"
export RBENV_VERSION=4.0.7
heavy cargo +1.98.1 build --release --locked --bin emit_reason_controls > "$NATIVE_OUTPUT/build-emission.log" 2>&1
for configuration in base settle scramble; do
    unset RH_SETTLE_REASON RH_SCRAMBLE_REASONS
    case "$configuration" in settle) export RH_SETTLE_REASON=unresolved;; scramble) export RH_SCRAMBLE_REASONS=1;; esac
    heavy "$CARGO_TARGET_DIR/release/emit_reason_controls" "$NATIVE_OUTPUT/emission-$configuration" \
        > "$NATIVE_OUTPUT/emission-$configuration.jsonl" 2> "$NATIVE_OUTPUT/emission-$configuration.stderr"
done
diff -rq "$NATIVE_OUTPUT/emission-base" "$NATIVE_OUTPUT/emission-settle"
diff -rq "$NATIVE_OUTPUT/emission-base" "$NATIVE_OUTPUT/emission-scramble"
