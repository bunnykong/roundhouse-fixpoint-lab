#!/usr/bin/env bash
set -u
: "${SOURCE:?Set SOURCE to the public compiler checkout}"
: "${OUTPUT:?Set OUTPUT to a fresh absolute output directory}"
: "${HOST_LOCK_WRAPPER:?Set HOST_LOCK_WRAPPER to the public lock helper}"
: "${HOST_LOCK_FILE:?Set HOST_LOCK_FILE to the shared host lock}"
mkdir -p "$OUTPUT"
export CARGO_TARGET_DIR="$OUTPUT/target" CARGO_BUILD_JOBS=4
cd "$SOURCE" || exit 1
while IFS='=' read -r name value; do
  case "$name" in RH_*) unset "$name" ;; esac
done < <(env)
for f in 000 100 010 110 001 111; do
  env RH_PROVENANCE_STRICT_STUBS=${f:0:1} RH_PROVENANCE_STRICT_XFER=${f:1:1} RH_PROVENANCE_CONGRUENT=${f:2:1} RBENV_VERSION=3.4.4 \
    python3 "$HOST_LOCK_WRAPPER" "$HOST_LOCK_FILE" cargo +1.98.1 test --locked --lib provenance_strict_producer_strictness -- \
    --ignored --nocapture --test-threads=1 > "$OUTPUT/harness-$f.log" 2>&1
  rc=$?; echo "$rc" > "$OUTPUT/harness-$f.exit"
  echo "harness $f exit $rc"
  [ "$rc" = 0 ] || exit "$rc"
done
LAW=(RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq RH_FIXPOINT_DIGEST=1
     RH_FIXPOINT_STATS=1 RH_PRECISION_CENSUS=1 RH_ERRGATE=1 RH_PUBLIC_INPUT=1 RH_FIXPOINT_VERIFY=1 RH_PROVENANCE_AUDIT=1
     RH_PARAMETER_REASON_CONSERVE=1 RH_PROVENANCE_PIDENT=1 RH_PROVENANCE_LIFT=1 RH_PROVENANCE_READER_VIEW=1 RH_SPLICED_WRITER_OWNERSHIP=1
     RH_SKIP_RETURN_STABILIZE=1 RH_PARAMETER_STORAGE_NORMAL_FORM=1)
for x in 0 1; do for t in storage_extended_laws provenance_lineage_factorial; do
  env "${LAW[@]}" RH_PROVENANCE_STRICT_XFER=$x RBENV_VERSION=3.4.4 python3 "$HOST_LOCK_WRAPPER" "$HOST_LOCK_FILE" cargo +1.98.1 test \
    --locked --lib "$t" -- --ignored --nocapture --test-threads=1 > "$OUTPUT/laws-x$x-$t.log" 2>&1
  rc=$?; echo "$rc" > "$OUTPUT/laws-x$x-$t.exit"
  echo "law $x $t exit $rc"
  [ "$rc" = 0 ] || exit "$rc"
done; done
