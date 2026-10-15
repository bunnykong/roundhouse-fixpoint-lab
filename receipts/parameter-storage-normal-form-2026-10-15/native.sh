#!/usr/bin/env bash
set -e
: "${SOURCE:?set SOURCE to a clean public compiler checkout}"
: "${OUTPUT:?set OUTPUT to a new output directory}"
: "${HOST_LOCK_WRAPPER:?set HOST_LOCK_WRAPPER to the shared host lock helper}"
: "${HOST_LOCK_FILE:?set HOST_LOCK_FILE to the shared host lock file}"
test ! -e "$OUTPUT"
mkdir -p "$OUTPUT"
OUTPUT=$(cd "$OUTPUT" && pwd)
SOURCE=$(cd "$SOURCE" && pwd)
HOST_LOCK_WRAPPER=$(cd "$(dirname "$HOST_LOCK_WRAPPER")" && pwd)/$(basename "$HOST_LOCK_WRAPPER")
HOST_LOCK_FILE=$(cd "$(dirname "$HOST_LOCK_FILE")" && pwd)/$(basename "$HOST_LOCK_FILE")
export CARGO_BUILD_JOBS=4 CARGO_TARGET_DIR="$OUTPUT/target" RBENV_VERSION=3.4.4
export RH_PARAMETER_REASON_CONSERVE=1 RH_PROVENANCE_PIDENT=1 RH_PROVENANCE_LIFT=1
export RH_PROVENANCE_AUDIT=1 RH_PROVENANCE_READER_VIEW=1
cd "$SOURCE"
capture() {
  name=$1
  shift
  set +e
  python3 "$HOST_LOCK_WRAPPER" --shared "$HOST_LOCK_FILE" "$@" \
    >"$OUTPUT/$name.stdout" 2>"$OUTPUT/$name.stderr"
  rc=$?
  set -e
  printf '%s\n' "$rc" >"$OUTPUT/$name.exit"
  cat "$OUTPUT/$name.stdout"
  cat "$OUTPUT/$name.stderr" >&2
}
trap 'python3 "$HOST_LOCK_WRAPPER" --shared "$HOST_LOCK_FILE" cargo +1.98.1 clean' EXIT
for norm in 0 1; do
  export RH_PARAMETER_STORAGE_NORMAL_FORM=$norm
  capture "normalizer-$norm" cargo +1.98.1 test --locked --lib storage_extended_laws \
    -- --ignored --nocapture --test-threads=1
done
test "$(cat "$OUTPUT/normalizer-0.exit")" = 101
test "$(cat "$OUTPUT/normalizer-1.exit")" = 0
