#!/usr/bin/env bash
# Source only this owned setup. All outputs and caches stay in this assignment.
export D=$EXPERIMENT
export RESULTS=$WORKSPACE/phase2/results
export INPUTS=$WORKSPACE/phase2
export PRE=$WORKSPACE/agents
export WEEK="$D/week" LAB="$D/week/lab"
export C="$WEEK/evidence/sources/probe-source" E="$WEEK/evidence" R="$WEEK/evidence/results"
export CARGO_HOME="$WEEK/cargo-home" TMPDIR="$WEEK/tmp"
export CARGO_BUILD_JOBS=4 RBENV_VERSION=4.0.7 PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="$WEEK/pycache"
export GIT_AUTHOR_NAME=bunnykong GIT_COMMITTER_NAME=bunnykong
export GIT_AUTHOR_EMAIL=268838774+bunnykong@users.noreply.github.com
export GIT_COMMITTER_EMAIL=268838774+bunnykong@users.noreply.github.com
unset CARGO_TARGET_DIR
for name in $(compgen -e); do
  case "$name" in RH_*|ROUNDHOUSE_*|SOUND_*|PROBE_BASE) unset "$name";; esac
done
FLOCK="$INPUTS/../workshop/flock.py"
LOCK="$INPUTS/../workshop/heavy.lock"
heavy() { python3 "$FLOCK" --shared "$LOCK" "$@"; }
timed() { python3 "$FLOCK" --exclusive "$LOCK" "$@"; }
law() {
  (cd "$1" && heavy env RBENV_VERSION=3.4.4 CARGO_TARGET_DIR="$1/target-laws" \
    cargo +1.98.1 test --locked --lib "$2" -- --include-ignored --nocapture --test-threads=1)
}
s3_law() {
  (export RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq
   law "$@")
}
