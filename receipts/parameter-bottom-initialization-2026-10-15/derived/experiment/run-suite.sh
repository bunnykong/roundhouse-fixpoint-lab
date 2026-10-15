#!/usr/bin/env bash
set -uo pipefail
source $EXPERIMENT/session.sh
if [ "${1:-}" != --locked-child ]; then
  heavy bash "$0" --locked-child "$@"
  exit $?
fi
shift
# Keep fixture checks and the serial suite/control commands under one shared lock.
heavy() { "$@"; }
label=${1:?fresh suite receipt label required}
dest="$R/$label"
mkdir "$dest" || exit 2
capture() {
  local name=$1; shift
  "$@" > "$dest/$name.log" 2>&1
  local result=$?
  printf '%s\n' "$result" > "$dest/$name.exit"
  printf '%s exit=%s\n' "$name" "$result"
  return "$result"
}
if [ ! -e "$C/fixtures/real-blog" ]; then
  capture fixtures heavy python3 -B "$D/staging/prepare_fixtures.py" || exit $?
fi
(cd "$C" && capture default heavy env RBENV_VERSION=3.4.4 CARGO_TARGET_DIR="$C/target-laws" \
  cargo +1.98.1 test --locked -- --test-threads=1)
control="$E/sources/suite-control"
if [ ! -d "$control" ]; then
  git clone --no-hardlinks --no-checkout "$C" "$control" || exit $?
  git -C "$control" checkout --detach d83849d3f7750b0121390f0c89a52ec81ad84b6e || exit $?
  cp -R "$C/fixtures/real-blog" "$control/fixtures/real-blog"
  cp -R "$C/fixtures/store" "$control/fixtures/store"
fi
for test in action_controller_runtime_emit_typechecks_hotspots rbs_ivar_decls_stamp_empty_array_initializers; do
  (cd "$control" && capture "control-$test" heavy env RBENV_VERSION=3.4.4 CARGO_TARGET_DIR="$control/target-laws" \
    cargo +1.98.1 test --locked --lib "$test" -- --nocapture --test-threads=1)
done
control_status=$?
exit "$control_status"
