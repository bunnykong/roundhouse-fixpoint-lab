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
git checkout --quiet 18875a967b8cafa5e45006358bba57a11968c5c4
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
export RBENV_VERSION=4.0.7 RH_FIXPOINT_VERIFY=0 RH_FIXPOINT_DIGEST=1 RH_FIXPOINT_STATS=1
: "${APP_ROOT:?Set Campfire at the pinned commit, including its prerequisites}"
heavy cargo +1.98.1 build --release --locked --bin roundhouse > "$NATIVE_OUTPUT/build.log" 2>&1
for configuration in off ownership stabilize both; do
    ownership=0; stabilize=0
    case "$configuration" in ownership) ownership=1;; stabilize) stabilize=1;; both) ownership=1; stabilize=1;; esac
    for schedule in unset 1 2 repeat; do
        out="$NATIVE_OUTPUT/$configuration-$schedule"
        mkdir "$out"
        unset RH_SHUFFLE
        case "$schedule" in 1|2) export RH_SHUFFLE="$schedule";; esac
        set +e
        (cd "$APP_ROOT" && heavy env RH_SPLICED_WRITER_OWNERSHIP="$ownership" \
            RH_SKIP_RETURN_STABILIZE="$stabilize" RH_REASON_SITE_CENSUS="$out/reasons.jsonl" \
            RH_DECL_DUMP="$out/declarations.jsonl" RH_STRUCT_DUMP="$out/structure.jsonl" \
            "$CARGO_TARGET_DIR/release/roundhouse" check --continue .) > "$out/stdout.log" 2> "$out/stderr.log"
        status=$?
        set -e
        printf '%s\n' "$status" > "$out/exit"
    done
done
