#!/usr/bin/env bash
# Invoke under the workshop shared flock. Fresh receipt labels are mandatory.
set -uo pipefail
source $EXPERIMENT/session.sh
heavy() { "$@"; }
label=${1:?fresh label required}
mode=${2:?baseline or candidate required}
dest="$R/$label"
mkdir "$dest" || exit 2
capture() {
  local name=$1; shift
  "$@" > "$dest/$name.log" 2>&1
  local status=$?
  printf '%s\n' "$status" > "$dest/$name.exit"
  printf '%s exit=%s\n' "$name" "$status"
  return "$status"
}
git -C "$C" rev-parse HEAD > "$dest/source-head.txt"
git -C "$C" diff HEAD --binary > "$dest/source.patch"
shasum -a 256 "$D/protocol.md" "$C/Cargo.lock" \
  "$C/src/analyze/parameter_conservation.rs" "$C/src/analyze/parameter_conservation/tests.rs" \
  "$C/src/analyze/mod.rs" > "$dest/input.sha256"
RH_PROVENANCE_AUDIT=1 RH_PARAMETER_REASON_CONSERVE=1 capture seed-arrival s3_law "$C" \
  writer_law_parameter_reason_conservation_seed_arrival
status=$?
if [ "$mode" = baseline ]; then exit "$status"; fi
if [ "$mode" != candidate ]; then exit 2; fi
RH_PROVENANCE_AUDIT=1 RH_PARAMETER_REASON_CONSERVE=1 capture row-laws s3_law "$C" \
  writer_law_parameter_reason_conservation_row_
rows_status=$?
RH_PROVENANCE_AUDIT=0 RH_PARAMETER_REASON_CONSERVE=1 capture row-laws-without-audit s3_law "$C" \
  writer_law_parameter_reason_conservation_row_
audit_status=$?
if [ "$status" != 0 ] || [ "$rows_status" != 0 ] || [ "$audit_status" != 0 ]; then exit 1; fi
