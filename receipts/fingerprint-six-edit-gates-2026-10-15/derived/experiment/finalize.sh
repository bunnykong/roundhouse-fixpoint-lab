#!/usr/bin/env bash
# Invoke once under the shared workshop lock after both cost controllers have exited.
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd)
W="$D/week/warm"
export EXPERIMENT_ROOT="$D" WARM_EDIT_AUDITS_WARM="$W"
export CARGO_HOME="$W/.cargo" TMPDIR="$W/.tmp"
export CARGO_BUILD_JOBS=4 CARGO_INCREMENTAL=0 CARGO_NET_OFFLINE=true
export RBENV_VERSION=4.0.7 PYTHONDONTWRITEBYTECODE=1
unset CARGO_TARGET_DIR PROFILE_STOP_UTC
cleaned=0
cleanup() {
    if [[ "$cleaned" == 0 ]]; then
        for arm in base fast; do
            cargo +1.98.1 clean --manifest-path "$W/trials/$arm/Cargo.toml" \
                --target-dir "$W/build/$arm" > "$D/evidence/clean-$arm.log" 2>&1
        done
        cleaned=1
    fi
}
trap cleanup EXIT
python3 -B "$D/preserve_binaries.py"
python3 -B "$D/summarize.py"
python3 -B "$D/verify.py"
cleanup
trap - EXIT
python3 -B "$D/verify.py" --cleaned
python3 -B "$D/make_result.py"
glowy preview "$D/protocol.md" > "$D/evidence/card-preview.log" 2>&1
glowy preview "$D/RESULT.md" > "$D/evidence/result-preview.log" 2>&1
