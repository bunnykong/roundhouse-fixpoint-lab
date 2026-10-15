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
git checkout --quiet cc149e46c6c6d4cc21120c50e0859d148d35f3fd
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
cat "$RECEIPT/reproduce-tests/residual-tests.rs" >> src/analyze/parameter_conservation/tests.rs
run_test residual-cell-laws absorption_residual_cell_laws RH_PARAMETER_REASON_CONSERVE=0 RH_ABSORPTION_RESIDUAL=1
for schedule in unset 1 2 repeat; do
    unset RH_SHUFFLE
    case "$schedule" in 1|2) export RH_SHUFFLE="$schedule";; esac
    run_test "residual-witness-$schedule" residual_witness_ \
        RH_PARAMETER_REASON_CONSERVE=0 RH_PROVENANCE_AUDIT=1 RH_ABSORPTION_RESIDUAL=1
done
