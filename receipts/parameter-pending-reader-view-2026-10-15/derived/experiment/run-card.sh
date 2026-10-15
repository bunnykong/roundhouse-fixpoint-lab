#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/session.sh"
export CARGO_NET_OFFLINE=true
mkdir -p "$R/pending-factorial"
for arm in 00 10 01 11; do
  status=0
  RH_PROVENANCE_AUDIT=1 RH_PARAMETER_REASON_CONSERVE=1 RH_PROVENANCE_PIDENT=${arm:0:1} RH_PROVENANCE_LIFT=${arm:1:1} \
    s3_law "$C" provenance_lineage_factorial > "$R/pending-factorial/A$arm.log" 2>&1 || status=$?
  echo "$status" > "$R/pending-factorial/A$arm.exit"
  grep '^PENDING-FACTORIAL ' "$R/pending-factorial/A$arm.log" > "$R/pending-factorial/A$arm.json" || true
  [ "$status" -eq 0 ] || exit "$status"
done
(cd "$C" && heavy env CARGO_TARGET_DIR="$E/scratch/provenance-target" \
  cargo +1.98.1 build --release --locked --bin roundhouse) > "$R/pending-factorial/build.log" 2>&1
PROBE="$E/sources/lab/receipts/baseline-2026-10-10/probe"
for arm in b1 b3; do
  for s in unset seed-1 seed-2 unset-repeat; do
    out="$R/pending-factorial-campfire/$arm/$s"; mkdir -p "$out"
    X=(RH_FIXPOINT_VERIFY=1 RH_PRECISION_CENSUS=1 RH_ERRGATE=1 RH_PUBLIC_INPUT=1 RH_PROVENANCE_AUDIT=1
       RH_PARAMETER_REASON_CONSERVE=1 RH_PROVENANCE_PIDENT=1 RH_PROVENANCE_LIFT=1 RH_PROVENANCE_ROWDUMP=1)
    [ "$arm" = b3 ] && X+=(RH_PROVENANCE_READER_VIEW=1)
    case $s in seed-1) X+=(RH_SHUFFLE=1);; seed-2) X+=(RH_SHUFFLE=2);; esac
    status=0
    (cd "$out" && RH_BIN="$E/scratch/provenance-target/release/roundhouse" APPS="$E/scratch/apps" \
       PROBE_BASE=0 heavy bash "$PROBE" campfire "${X[@]}" > stdout.json) \
       > "$out/launcher.stdout" 2> "$out/launcher.stderr" || status=$?
    echo "$status" > "$out/probe.exit"
    printf '%s\n' "${X[@]}" > "$out/flags.txt"
    [ "$status" -eq 0 ] || exit "$status"
  done
done
