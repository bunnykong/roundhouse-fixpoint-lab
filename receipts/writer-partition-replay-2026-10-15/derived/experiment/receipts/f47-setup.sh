#!/usr/bin/env bash
# Source only this task-local setup in Bash.
export TASK_ROOT=$EXPERIMENT
export FRONTIER=$WORKSPACE
export RESULTS="$TASK_ROOT" INPUTS="$FRONTIER/phase2" PRE="$FRONTIER/agents"
export WEEK="$TASK_ROOT/week" LAB="$TASK_ROOT/week/lab"
export BOUND="$WEEK/bound-next" C="$WEEK/bound-next/sources/probe-source"
export NEXT=38403140379cd69759b0fe6247c6a8c4a48a37a9
export LAB_PIN=76cdb1ea24b0c4c88af4c42c78f567d759b7731d
export CARGO_HOME="$WEEK/cargo-home" TMPDIR="$WEEK/tmp"
export CARGO_BUILD_JOBS=4 RBENV_VERSION=4.0.7 PYTHONDONTWRITEBYTECODE=1
export GIT_AUTHOR_NAME='Bunny Kong' GIT_COMMITTER_NAME='Bunny Kong'
export GIT_AUTHOR_EMAIL=268838774+bunnykong@users.noreply.github.com
export GIT_COMMITTER_EMAIL=268838774+bunnykong@users.noreply.github.com
unset CARGO_TARGET_DIR
for name in $(compgen -e); do
  case "$name" in RH_*|ROUNDHOUSE_*|SOUND_*|PROBE_BASE) unset "$name";; esac
done
heavy() { python3 "$FRONTIER/workshop/flock.py" --shared "$FRONTIER/workshop/heavy.lock" "$@"; }
timed() { python3 "$FRONTIER/workshop/flock.py" --exclusive "$FRONTIER/workshop/heavy.lock" "$@"; }
fresh() {
  git clone --no-hardlinks --no-checkout "$1" "$2" || return
  git -C "$2" checkout --detach "$3"
}
law() {
  (cd "$1" && heavy env RBENV_VERSION=3.4.4 CARGO_TARGET_DIR="$1/target-laws" \
    cargo +1.98.1 test --locked --lib "$2" -- --include-ignored --nocapture --test-threads=1)
}
writer_law_summary() {
  (export RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq
   law "$@")
}
