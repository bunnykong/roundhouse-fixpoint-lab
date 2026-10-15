#!/usr/bin/env bash
set -uo pipefail
source $EXPERIMENT/session.sh
label=${1:?new local-check label required}
dest="$R/$label"
mkdir "$dest" || exit 2
capture() {
  local name=$1; shift
  "$@" > "$dest/$name.log" 2>&1
  local result=$?
  printf '%s\n' "$result" > "$dest/$name.exit"
  printf '%s exit=%s\n' "$name" "$result"
}
RH_PROVENANCE_AUDIT=1 RH_PARAMETER_REASON_CONSERVE=0 capture contracts s3_law "$C" producer_reason_provenance_contract
RH_PROVENANCE_AUDIT=1 RH_PARAMETER_REASON_CONSERVE=1 capture parameters s3_law "$C" writer_law_parameter_reason_conservation
RH_PROVENANCE_AUDIT=0 RH_PARAMETER_REASON_CONSERVE=1 capture repair-without-audit s3_law "$C" writer_law_parameter_reason_conservation_grouping_and_values
RH_PROVENANCE_AUDIT=0 RH_PARAMETER_REASON_CONSERVE=1 capture storage-without-audit s3_law "$C" writer_law_parameter_reason_conservation_tag_only_storage
RH_PROVENANCE_AUDIT=1 RH_PARAMETER_REASON_CONSERVE=0 capture repair-off-negative s3_law "$C" writer_law_parameter_reason_conservation_pending_and_legacy
capture returns s3_law "$C" writer_law_return_evidence
capture return-controls s3_law "$C" writer_law_return_control_
