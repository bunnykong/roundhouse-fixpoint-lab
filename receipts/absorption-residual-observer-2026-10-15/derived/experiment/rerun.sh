#!/usr/bin/env bash
# Rebuild and rerun the card in a new receipt directory; preserve original evidence.
set -euo pipefail
cd "$(dirname "$0")"
source ./session.sh
OUT=${1:-"$R/absorption-observer-rerun-$(date -u +%Y%m%dT%H%M%SZ)"}
case "$OUT" in "$R"/*) ;; *) echo "receipt directory must be under $R" >&2; exit 2;; esac
mkdir "$OUT"
mkdir "$OUT/gates"
cleanup() {
  local run_status=$?
  set +e
  heavy bash "$D/staging/clean_targets.sh" "$OUT/gates" > "$OUT/gates/clean-driver.log" 2>&1
  local cleanup_status=$?
  if [ "$run_status" -eq 0 ] && [ "$cleanup_status" -ne 0 ]; then run_status=$cleanup_status; fi
  exit "$run_status"
}
trap cleanup EXIT
set +e
RH_PROVENANCE_AUDIT=1 RH_PARAMETER_REASON_CONSERVE=0 s3_law "$C" absorption_residual_cell_laws \
  > "$OUT/gates/laws.log" 2>&1
law_status=$?
echo "$law_status" > "$OUT/gates/laws.exit"
RH_PROVENANCE_AUDIT=1 RH_PARAMETER_REASON_CONSERVE=0 s3_law "$C" producer_reason_provenance_contract \
  > "$OUT/gates/contracts.log" 2>&1
contract_status=$?
echo "$contract_status" > "$OUT/gates/contracts.exit"
set -e
heavy python3 -B "$E/experiments/app_check.py" --output "$OUT/campfire" \
  --candidate-env RH_PROVENANCE_AUDIT=1 --candidate-env RH_ABSORPTION_RESIDUAL=1 > "$OUT/gates/app-run.log" 2>&1
python3 -B "$D/staging/analyze_app.py" --root "$OUT/campfire" --output-dir "$OUT/gates" \
  > "$OUT/gates/campfire-summary.json"
logs=()
for name in precision unset seed-1 seed-2 unset-repeat; do
  logs+=("$OUT/campfire/candidate/$name/probe-campfire.stderr")
done
python3 -B "$D/staging/bijection.py" "${logs[@]}" --output "$OUT/gates/bijection.json"
mkdir "$OUT/discourse"
(cd "$OUT/discourse" && RH_BIN="$E/scratch/provenance-target/release/roundhouse" \
  APPS="$E/scratch/apps" PROBE_BASE=0 heavy bash \
  "$E/sources/lab/receipts/baseline-2026-10-10/probe" discourse \
  RH_FIXPOINT_VERIFY=0 RH_PUBLIC_INPUT=1 RH_PROVENANCE_AUDIT=1 RH_ABSORPTION_RESIDUAL=1 > stdout.json)
python3 -B "$D/staging/bijection.py" "$OUT/discourse/probe-discourse.stderr" \
  --output "$OUT/gates/discourse-bijection.json"
python3 -B "$D/staging/discourse_witnesses.py" --reduction "$OUT/gates/discourse-bijection.json" \
  --log "$OUT/discourse/probe-discourse.stderr" --output-dir "$OUT/gates" \
  > "$OUT/gates/discourse-witnesses.log"
printf 'Laws: %s; contracts: %s; receipts: %s\n' "$law_status" "$contract_status" "$OUT"
python3 -B - "$OUT/gates" <<'PY'
import json
from pathlib import Path
import sys
gate = Path(sys.argv[1])
assert (gate / 'laws.exit').read_text().strip() == '0', 'native law failure'
assert (gate / 'contracts.exit').read_text().strip() == '0', 'provenance contract failure'
pairs = json.loads((gate / 'campfire-paired-differences.json').read_text())['audit--candidate']
assert len(pairs) == 5
assert all(row['ordinary_report_equal'] and row['diagnostics_equal'] and row['digests_equal']
           for row in pairs), 'answer-neutrality failure'
rows = json.loads((gate / 'bijection.json').read_text())['runs']
precision = next(row for row in rows if Path(row['receipt']).parent.name == 'precision')
assert precision['R_size'] and not precision['L_minus_R'], 'coverage failure'
assert precision['all_extra_have_nested_survivor'], 'unexplained residual atom'
discourse = json.loads((gate / 'discourse-bijection.json').read_text())['runs'][0]
if discourse['L_minus_R']:
    print('Registered coverage kill: optional Discourse precision has uncovered loss pairs')
    sys.exit(1)
print('Registered card gates: confirmed')
PY
