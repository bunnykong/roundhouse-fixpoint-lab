#!/usr/bin/env bash
set -uo pipefail
source $EXPERIMENT/session.sh
if [ "${1:-}" != --locked-child ]; then
  heavy bash "$0" --locked-child "$@"
  exit $?
fi
shift
# This entire child is already below the shared workshop flock wrapper.
heavy() { "$@"; }
label=${1:?fresh F29 receipt label required}
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
capture build heavy env CARGO_TARGET_DIR="$E/scratch/provenance-target" \
  cargo +1.98.1 build --release --locked --manifest-path "$C/Cargo.toml" \
  --example parameter_reason_sound_types || exit $?
binary="$E/scratch/provenance-target/release/examples/parameter_reason_sound_types"
frozen="$LAB/receipts/discourse-trace-2026-10-10"
for arm in s3 audit candidate; do
  audit=0; repair=0
  if [ "$arm" != s3 ]; then audit=1; fi
  if [ "$arm" = candidate ]; then repair=1; fi
  capture "$arm-export" heavy python3 -B "$WEEK/sound/candidate_export.py" \
    --binary "$binary" --role s3 --source "$C" --app "$LAB/corpus/apps/discourse" \
    --selection "$frozen/selection.json" --lab "$LAB" --output "$dest/$arm" \
    --condition "parameter-bottom-initialization-20261015-134457dc-$label-shared-host" \
    --candidate-env "RH_PROVENANCE_AUDIT=$audit" --candidate-env "RH_PARAMETER_REASON_CONSERVE=$repair" || exit $?
done
for setting in P E I; do
  capture "$setting-audit" heavy python3 -B "$WEEK/sound/adapter/compare.py" \
    --lab "$LAB" --trace "$frozen/traces/$setting.jsonl" --export "$dest/audit" \
    --baseline-export "$dest/s3" --slots "$frozen/slots.json" \
    --output "$dest/$setting-audit.json" --require-membership
  capture "$setting-candidate" heavy python3 -B "$WEEK/sound/adapter/compare.py" \
    --lab "$LAB" --trace "$frozen/traces/$setting.jsonl" --export "$dest/candidate" \
    --baseline-export "$dest/audit" --slots "$frozen/slots.json" \
    --output "$dest/$setting-candidate.json" --require-membership
done
