#!/usr/bin/env bash
# Source this local setup; it runs no build, test or analysis.
export EXPERIMENT_ROOT=$EXPERIMENT
export D="$EXPERIMENT_ROOT"
export WEEK="$D/week"
export LAB="$WEEK/lab"
export WARM_DIR="$WEEK/warm"
export PRE=$WORKSPACE/agents
export CARGO_HOME="$WEEK/cargo-home"
export TMPDIR="$WEEK/tmp"
export CARGO_BUILD_JOBS=4 CARGO_INCREMENTAL=0 CARGO_NET_OFFLINE=true
export RUST_MIN_STACK=33554432
export RBENV_VERSION=4.0.7 PYTHONDONTWRITEBYTECODE=1
export GIT_AUTHOR_NAME=bunnykong GIT_COMMITTER_NAME=bunnykong
export GIT_AUTHOR_EMAIL=268838774+bunnykong@users.noreply.github.com
export GIT_COMMITTER_EMAIL=268838774+bunnykong@users.noreply.github.com
export PROFILE_STOP_UTC="${PROFILE_STOP_UTC:-2026-10-11T15:07:00+00:00}"
unset CARGO_TARGET_DIR
for name in $(compgen -e); do
  case "$name" in RH_*|ROUNDHOUSE_*|SOUND_*|PROBE_BASE) unset "$name";; esac
done
FLOCK=$WORKSPACE/workshop/flock.py
LOCK=$WORKSPACE/workshop/heavy.lock
heavy() { python3 "$FLOCK" --shared "$LOCK" "$@"; }
timed() { python3 "$FLOCK" --exclusive "$LOCK" "$@"; }
fresh() {
  git clone --no-hardlinks --no-checkout "$1" "$2" || return
  git -C "$2" checkout --detach "$3"
}
warm_build() {
  heavy cargo +1.98.1 build --manifest-path "$WARM_DIR/trials/$1/Cargo.toml" \
    --target-dir "$WARM_DIR/build/$1" --release --locked --offline --bin roundhouse
}
warm_check() {
  heavy cargo +1.98.1 test --manifest-path "$WARM_DIR/trials/$1/Cargo.toml" \
    --target-dir "$WARM_DIR/build/$1" --release --locked --offline --test warm_check "$2" \
    -- --nocapture --test-threads=1
}
warm_trial() {
  local label="$1" tree="$2"
  shift 2
  timed python3 -B "$WARM_DIR/scripts/replay_pairs.py" \
    --binary "$WARM_DIR/build/$tree/release/roundhouse" --source "$WARM_DIR/trials/$tree" \
    --condition "warm-lossless-storage-20261011-$label" --out "$WARM_DIR/runs/$label" "$@"
}
