#!/usr/bin/env bash
set -euo pipefail
: "${SOURCE:?Set SOURCE to the pinned public compiler checkout}"
: "${OUTPUT:?Set OUTPUT to a fresh absolute output directory}"
: "${HOST_LOCK_WRAPPER:?Set HOST_LOCK_WRAPPER to the public observer lock helper}"
: "${HOST_LOCK_FILE:?Set HOST_LOCK_FILE to the shared host lock}"
mkdir -p "$OUTPUT"
export CARGO_TARGET_DIR="$OUTPUT/target" CARGO_BUILD_JOBS=4 RBENV_VERSION=3.4.4 RUST_MIN_STACK=33554432
while IFS='=' read -r name value; do
  case "$name" in RH_*) unset "$name" ;; esac
done < <(env)
cd "$SOURCE"
test -d fixtures/real-blog
python3 "$HOST_LOCK_WRAPPER" --exclusive "$HOST_LOCK_FILE"   cargo +1.98.1 test --locked --lib -- --test-threads=4 > "$OUTPUT/library.log" 2>&1
export RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq
export RH_PARAMETER_REASON_CONSERVE=1 RH_PROVENANCE_PIDENT=1 RH_PROVENANCE_LIFT=1
export RH_PARAMETER_STORAGE_NORMAL_FORM=1 RH_PROVENANCE_READER_VIEW=1
export RH_CLOSURE_APPLY=1 RH_CLOSURE_SITES=1 RH_SPLICED_WRITER_OWNERSHIP=0 RH_SKIP_RETURN_STABILIZE=0
python3 "$HOST_LOCK_WRAPPER" --exclusive "$HOST_LOCK_FILE"   cargo +1.98.1 test --locked --lib writer_partition_partition_census -- --ignored --nocapture --test-threads=1   > "$OUTPUT/partition-census.log" 2>&1
set +e
python3 "$HOST_LOCK_WRAPPER" --exclusive "$HOST_LOCK_FILE"   cargo +1.98.1 test --locked --lib writer_law_bound_partitions -- --ignored --nocapture --test-threads=1   > "$OUTPUT/partition-negative.log" 2>&1
status=$?
set -e
test "$status" -eq 101
