#!/bin/bash
# Response-return protocol (phase2/void-top/protocol.md), condition response-return-values-20261015-stabilization-on.
# usage: run.sh WORK STEP   with STEP one of: build suite emission campfire rest verdict
# WORK is the builder's own directory under examples/. Steps run in that order; `campfire`
# must print primary CONFIRMED before `rest` runs (the Campfire stop rule).
set -euo pipefail
F=$WORKSPACE
K=$(cd "$(dirname "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
WORK=${1:?work dir}; STEP=${2:?step}
SRC=$WORK/src; BIN=$WORK/bin/roundhouse; export CARGO_BUILD_JOBS=4 CARGO_TARGET_DIR=$WORK/target
OBS="python3 $F/phase2/observers/obs.py"
mkdir -p "$WORK/bin" "$WORK/receipts"

python3 -B -I "$K/verify_freeze.py" "$WORK" "$STEP"

case "$STEP" in
build)
  # Spine ea3ec744 + the research condition row observer (validated output-preserving) + the flagged change.
  [ -d "$SRC" ] || { mkdir -p "$SRC"; git -C $F/agents/storage-repair-five-apps/repo archive ea3ec7441d95926ae7febbe028279cf2e6b8680e | tar -x -C "$SRC"; }
  ( cd "$SRC" && patch -p1 --forward < $K/instrumentation.patch \
      && patch -p1 --forward < $K/spine-response-returns.patch )
  shasum -a 256 $K/instrumentation.patch $K/spine-response-returns.patch > "$WORK/receipts/patches.sha256"
  ( cd "$SRC" && python3 $F/workshop/flock.py --shared $F/workshop/heavy.lock cargo build --release --locked --bin roundhouse -j 4 )
  cp "$CARGO_TARGET_DIR/release/roundhouse" "$BIN"; shasum -a 256 "$BIN" | tee "$WORK/receipts/binary.sha256"
  # Generated fixtures for E1 (not checked in upstream); recorded by hash.
  for f in real-blog store; do rsync -a --exclude node_modules --exclude tmp --exclude log \
      $F/examples/generated-fixtures/$f "$SRC/fixtures/"; done
  ( cd "$SRC/fixtures" && find real-blog store -type f -print0 | sort -z | xargs -0 shasum -a 256 ) > "$WORK/receipts/generated-fixtures.sha256"
  ;;
suite)
  # L1: full default suite, flag off then on, one at a time under the suite lock. Ruby 3.4 for the suite;
  # emit-and-run tests need the sqlite3 gem (install it into $WORK/gems, never into the shared Ruby).
  G=$WORK/gems; [ -d "$G" ] || env -u GEM_HOME -u GEM_PATH RBENV_VERSION=3.4.4 gem install sqlite3 --install-dir "$G" --no-document
  DEF=$(RBENV_VERSION=3.4.4 ruby -e 'print Gem.default_dir')
  export RBENV_VERSION=3.4.4 GEM_HOME="$G" GEM_PATH="$G:$DEF"
  python3 $F/workshop/flock.py $F/workshop/heavy.lock \
    python3 $F/workshop/flock.py --exclusive $F/workshop/suite.lock python3 -B -I $K/run_suite.py "$WORK"
  python3 -I $K/suite_receipt.py "$WORK/receipts/suite-off.log" "$WORK/receipts/suite-on.log" > "$WORK/receipts/suite.json"
  ;;
emission)
  python3 $F/workshop/flock.py $F/workshop/heavy.lock python3 -B -I $K/emit_compare.py --bin "$BIN" --checkout "$SRC" --out "$WORK/emission"
  ;;
campfire)
  for arm in C T; do
    $OBS run --bin "$BIN" --app campfire --settings unset-v0-a0,1-v0-a0,2-v0-a0,repeat-v0-a0,unset-v1-a1 \
      --flags $K/profiles/$arm.json --label s7rr-$arm
  done
  python3 -I $K/verdict.py --stage campfire --suite "$WORK/receipts/suite.json" --emission "$WORK/emission/compare.json" --out "$WORK/verdict-campfire"
  ;;
rest)
  python3 -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1]))["primary"]["verdict"] == "CONFIRMED" else "Campfire stop rule: not CONFIRMED")' "$WORK/verdict-campfire/verdict.json"
  for app in forem chatwoot mastodon; do for arm in C T; do
    $OBS run --bin "$BIN" --app $app --settings unset-v0-a0,repeat-v0-a0,unset-v1-a1 --flags $K/profiles/$arm.json --label s7rr-$arm
  done; done
  for app in forem mastodon; do for arm in CA TA; do
    $OBS run --bin "$BIN" --app $app --settings unset-v0-a0,1-v0-a0,2-v0-a0,repeat-v0-a0 --flags $K/profiles/$arm.json --label s7rr-$arm
  done; done
  for arm in C T; do  # report-only; Discourse runs one at a time (apps.json max_parallel=1)
    $OBS run --bin "$BIN" --app discourse --settings unset-v0-a0 --flags $K/profiles/$arm.json --label s7rr-$arm --timeout 5400 || true
  done
  ;;
verdict)
  python3 -I $K/verdict.py --stage all --emission "$WORK/emission/compare.json" --suite "$WORK/receipts/suite.json" --out "$WORK/verdict"
  ;;
*) echo "unknown step $STEP"; exit 2 ;;
esac
