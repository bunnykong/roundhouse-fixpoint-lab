#!/usr/bin/env bash
# One-command rerun on the delivered branch. It preserves every raw gate exit.
set -uo pipefail
source $EXPERIMENT/session.sh
label=${1:?provide a fresh receipt label, for example replay-01}
case "$label" in *[!A-Za-z0-9_-]*|'') exit 2;; esac
mkdir "$R/$label-driver" || exit 2
dest="$R/$label-driver"
capture() {
  local name=$1; shift
  "$@" > "$dest/$name.log" 2>&1
  local result=$?
  printf '%s\n' "$result" > "$dest/$name.exit"
  printf '%s exit=%s\n' "$name" "$result"
}
capture local bash "$D/run-local.sh" "$label-local"
capture f19 heavy python3 -B "$E/experiments/f19_check.py" \
  --output "$R/$label-f19" --candidate-env RH_PROVENANCE_AUDIT=1 --candidate-env RH_PARAMETER_REASON_CONSERVE=1
capture campfire heavy python3 -B "$E/experiments/app_check.py" \
  --output "$R/$label-campfire" --candidate-env RH_PROVENANCE_AUDIT=1 --candidate-env RH_PARAMETER_REASON_CONSERVE=1
capture f29 bash "$D/run-f29.sh" "$label-f29"
capture suite bash "$D/run-suite.sh" "$label-suite"
heavy python3 -B "$D/staging/reproduce_status.py" "$label"
