#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/session.sh"
export CARGO_NET_OFFLINE=true
status=0
(cd "$C" && heavy env RBENV_VERSION=3.4.4 CARGO_TARGET_DIR="$C/target-laws" \
 cargo +1.98.1 test --locked) > "$R/pending-factorial/default-suite.log" 2>&1 || status=$?
echo "$status" > "$R/pending-factorial/default-suite.exit"
printf 'Default suite exit: %s\n' "$status"
exit "$status"
