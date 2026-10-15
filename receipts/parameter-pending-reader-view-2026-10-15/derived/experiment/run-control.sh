#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/session.sh"
export CARGO_NET_OFFLINE=true
CONTROL="$E/sources/default-control"
for name in rbs_ivar_decls_stamp_empty_array_initializers action_controller_runtime_emit_typechecks_hotspots; do
  status=0
  (cd "$CONTROL" && heavy env RBENV_VERSION=3.4.4 CARGO_TARGET_DIR="$E/scratch/default-control-target" \
     cargo +1.98.1 test --locked --lib "$name" -- --nocapture --test-threads=1) \
      > "$R/pending-factorial/control-$name.log" 2>&1 || status=$?
  echo "$status" > "$R/pending-factorial/control-$name.exit"
done
