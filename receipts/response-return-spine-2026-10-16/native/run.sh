#!/bin/bash
# Response-return protocol v2 (phase2/void-top/response-protocol.md), condition response-return-spine-witnesses-20261016.
# usage: run.sh WORK STEP   with STEP one of: build suite emission reference campfire rest verdict
# WORK is the builder's own directory under examples/. Steps run in that order; `campfire`
# must print primary CONFIRMED before `rest` runs (the Campfire stop rule).
set -euo pipefail
F=$WORKSPACE
K=$(cd "$(dirname "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
export CARGO_HOME="$F/agents/response-return-spine/cargo-home" CARGO_NET_OFFLINE=true
WORK=${1:?work dir}; STEP=${2:?step}
SRC=$WORK/repo; BIN=$WORK/bin/roundhouse; export CARGO_BUILD_JOBS=4 CARGO_TARGET_DIR=$WORK/target
OBS="python3 $F/phase2/observers/obs.py"
mkdir -p "$WORK/bin" "$WORK/receipts"

python3 -B -I "$K/verify_freeze.py" "$WORK" "$STEP"

case "$STEP" in
build)
  echo 'Build and native checks are tools/build_native.py; source is already composed.'
  exit 2
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
reference)
  # Campfire alone before the stop decision; later-app references run inside the guarded rest stage.
  SPINE=$F/agents/fixpoint-spine/bin/roundhouse
  echo "fb93bd1b1883778a255588e20be4dfae4bb14d5745523d8abd2fa46064ee264d  $SPINE" | shasum -a 256 -c -
  $OBS run --bin "$SPINE" --app campfire --settings unset-v0-a0,1-v0-a0,2-v0-a0,repeat-v0-a0,unset-v1-a1 \
    --flags $K/profiles/R.json --label response-return-spine-response-returns-spine-ownership-off-nostab
  ;;
campfire)
  for arm in C T; do
    $OBS run --bin "$BIN" --app campfire --settings unset-v0-a0,1-v0-a0,2-v0-a0,repeat-v0-a0,unset-v1-a1 \
      --flags $K/profiles/$arm.json --label response-return-spine-response-returns-$arm
  done
  python3 -I $K/verdict.py --stage campfire --suite "$WORK/receipts/suite.json" --emission "$WORK/emission/compare.json" --out "$WORK/verdict-campfire"
  ;;
rest)
  python3 -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1]))["primary"]["verdict"] == "CONFIRMED" else "Campfire stop rule: not CONFIRMED")' "$WORK/verdict-campfire/verdict.json"
  SPINE=$F/agents/fixpoint-spine/bin/roundhouse
  echo "fb93bd1b1883778a255588e20be4dfae4bb14d5745523d8abd2fa46064ee264d  $SPINE" | shasum -a 256 -c -
  for app in forem chatwoot mastodon; do
    $OBS run --bin "$SPINE" --app $app --settings unset-v0-a0,repeat-v0-a0,unset-v1-a1 --flags $K/profiles/R.json \
      --label response-return-spine-response-returns-spine-ownership-off-nostab
  done
  for app in forem chatwoot mastodon; do for arm in C T; do
    $OBS run --bin "$BIN" --app $app --settings unset-v0-a0,repeat-v0-a0,unset-v1-a1 --flags $K/profiles/$arm.json --label response-return-spine-response-returns-$arm
  done; done
  for app in forem mastodon; do
    $OBS run --bin "$SPINE" --app $app --settings unset-v0-a0,1-v0-a0,2-v0-a0,repeat-v0-a0 \
      --flags $K/profiles/RA.json --label response-return-spine-response-returns-spine-ownership-on
  done
  for app in forem mastodon; do for arm in CA TA; do
    $OBS run --bin "$BIN" --app $app --settings unset-v0-a0,1-v0-a0,2-v0-a0,repeat-v0-a0 --flags $K/profiles/$arm.json --label response-return-spine-response-returns-$arm
  done; done
  $OBS run --bin "$SPINE" --app discourse --settings unset-v0-a0 --flags $K/profiles/R.json \
    --label response-return-spine-response-returns-spine-ownership-off-nostab --timeout 5400 || true
  for arm in C T; do  # report-only; Discourse runs one at a time (apps.json max_parallel=1)
    $OBS run --bin "$BIN" --app discourse --settings unset-v0-a0 --flags $K/profiles/$arm.json --label response-return-spine-response-returns-$arm --timeout 5400 || true
  done
  ;;
verdict)
  python3 -I $K/verdict.py --stage all --emission "$WORK/emission/compare.json" --suite "$WORK/receipts/suite.json" --out "$WORK/verdict"
  ;;
*) echo "unknown step $STEP"; exit 2 ;;
esac
