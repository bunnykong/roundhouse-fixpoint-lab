#!/usr/bin/env bash
set -o pipefail

TASK_DIR=$(cd "$(dirname "$0")" && pwd)
source "$TASK_DIR/setup.sh"
export PROFILE_STOP_UTC="${PROVENANCE_STOP_UTC:-$(date -u -v+3H +%Y-%m-%dT%H:%M:%S+00:00)}"
C3="$WARM_DIR/trials/codec"
S3=(RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq)
if [ "$#" -gt 0 ]; then
  case "$1" in *[!a-zA-Z0-9_-]*|'') printf 'Use a simple new rerun label.\n' >&2; exit 2;; esac
  E="$D/reruns/$1/evidence"
  R="$WARM_DIR/runs/$1"
  mkdir -p "$E" "$R"
else
  E="$D/evidence"
  R="$WARM_DIR/runs"
fi
: > "$E/exits.tsv"
PROVENANCE_NATIVE_DONE=0
record() { printf '%s\t%s\n' "$1" "$2" >> "$E/exits.tsv"; }
cleanup() {
  heavy cargo +1.98.1 clean --manifest-path "$C3/Cargo.toml" --target-dir "$WARM_DIR/build/codec" \
    > "$E/clean.log" 2>&1
  record clean "$?"
  if [ "$PROVENANCE_NATIVE_DONE" = 1 ]; then
    python3 -B "$D/audit.py" --evidence "$E" --runs "$R" > "$E/audit-summary.json"
    record audit "$?"
  fi
}
trap cleanup EXIT

if [ "${PROVENANCE_BUILD_DONE:-0}" != 1 ]; then
  warm_build codec > "$E/build.log" 2>&1
  status=$?; record build-roundhouse "$status"
  [ "$status" -eq 0 ] || exit "$status"
  heavy cargo +1.98.1 build --manifest-path "$C3/Cargo.toml" --target-dir "$WARM_DIR/build/codec" \
    --release --locked --offline --bin emit_reason_controls >> "$E/build.log" 2>&1
  status=$?; record build-emitter "$status"
  [ "$status" -eq 0 ] || exit "$status"
else
  record build-predriver 0
fi
shasum -a 256 "$WARM_DIR/build/codec/release/roundhouse" \
  "$WARM_DIR/build/codec/release/emit_reason_controls" > "$E/binaries-before-storage.sha256"
export RH_WARM_LOSSLESS_CODEC=1 WARM_TEST_RECEIPTS="$E/native"
warm_check codec warm_storage_fidelity > "$E/storage.log" 2>&1
record storage "$?"
unset RH_WARM_LOSSLESS_CODEC WARM_TEST_RECEIPTS
shasum -a 256 "$WARM_DIR/build/codec/release/roundhouse" \
  "$WARM_DIR/build/codec/release/emit_reason_controls" > "$E/binaries.sha256"

EMIT="$WARM_DIR/build/codec/release/emit_reason_controls"
for arm in base settle scramble; do
  case $arm in base) X=();; settle) X=(RH_SETTLE_REASON=unresolved);; scramble) X=(RH_SCRAMBLE_REASONS=1);; esac
  (cd "$C3" && heavy env "${S3[@]}" RH_FIXPOINT_STATS=1 "${X[@]}" "$EMIT" "$E/emit-$arm" \
    > "$E/emit-$arm.jsonl" 2> "$E/emit-$arm.stderr")
  record "emit-$arm" "$?"
done
diff -r "$E/emit-base" "$E/emit-settle" > "$E/diff-settle.txt"
record diff-settle "$?"
diff -r "$E/emit-base" "$E/emit-scramble" > "$E/diff-scramble.txt"
record diff-scramble "$?"
diff "$E/emit-base.jsonl" "$E/emit-settle.jsonl" > "$E/diff-settle-jsonl.txt"
record diff-settle-jsonl "$?"
diff "$E/emit-base.jsonl" "$E/emit-scramble.jsonl" > "$E/diff-scramble-jsonl.txt"
record diff-scramble-jsonl "$?"

provenance_trial() {
  local label="$1"; shift
  heavy python3 -B "$WARM_DIR/scripts/replay_pairs.py" \
    --binary "$WARM_DIR/build/codec/release/roundhouse" --source "$C3" \
    --condition "reason_controls-$label" --out "$R/$label" \
    --app mastodon --edit withdraw-read --pairs 1 --stats "$@" \
    > "$E/trial-$label.log" 2>&1
  record "trial-$label" "$?"
}
provenance_trial legacy-g
provenance_trial legacy-u --provenance-flag RH_SETTLE_REASON=unresolved
provenance_trial lossless-g --warm-flag RH_WARM_LOSSLESS_CODEC=1
provenance_trial lossless-u --warm-flag RH_WARM_LOSSLESS_CODEC=1 --provenance-flag RH_SETTLE_REASON=unresolved
PROVENANCE_NATIVE_DONE=1
