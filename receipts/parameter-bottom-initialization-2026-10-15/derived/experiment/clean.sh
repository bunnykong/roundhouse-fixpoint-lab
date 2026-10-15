#!/usr/bin/env bash
# Invoke under the workshop shared flock after all own builds have stopped.
set -uo pipefail
source $EXPERIMENT/session.sh
label=${1:-cleanup-v1}
case "$label" in *[!A-Za-z0-9_-]*|'') exit 2;; esac
dest="$R/$label"
mkdir "$dest" || exit 2
status=0
for pair in laws:"$C/target-laws" native:"$E/scratch/provenance-target" \
  control:"$E/sources/suite-control/target-laws"; do
  name=${pair%%:*}
  target=${pair#*:}
  cargo +1.98.1 clean --manifest-path "$C/Cargo.toml" --target-dir "$target" \
    > "$dest/$name.log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$dest/$name.exit"
  printf 'clean-%s exit=%s\n' "$name" "$code"
  if [ "$code" != 0 ]; then status=1; fi
done
exit "$status"
