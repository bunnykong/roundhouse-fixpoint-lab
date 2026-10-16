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
python3 "$HOST_LOCK_WRAPPER" "$HOST_LOCK_FILE" \
  cargo +1.98.1 test --locked --lib strict_stub_completion -- --test-threads=1 > "$OUTPUT/completion.log" 2>&1
