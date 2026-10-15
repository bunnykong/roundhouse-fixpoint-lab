#!/usr/bin/env bash
# Run under the workshop's shared lock. Writes only inside this preparation notes.
set -euo pipefail
D=$(cd "$(dirname "$0")/.." && pwd)
src="$D/sources/probe-source"
pin=38403140379cd69759b0fe6247c6a8c4a48a37a9
if [ ! -d "$src" ]; then
  git -C "$D/sources/roundhouse" worktree add --detach "$src" "$pin"
fi
test "$(git -C "$src" rev-parse HEAD)" = "$pin"
if ! cmp -s "$D/experiments/provenance_probe.rs" "$src/src/analyze/body/producer_reason_provenance_probe.rs"; then
  cp "$D/experiments/provenance_probe.rs" "$src/src/analyze/body/producer_reason_provenance_probe.rs"
fi
python3 - "$src/src/analyze/body/mod.rs" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
include='\n#[cfg(test)]\nmod producer_reason_provenance_probe;\n'
s=p.read_text()
if include not in s:
    p.write_text(s+include)
PY
export CARGO_HOME="$D/scratch/cargo-home" CARGO_TARGET_DIR="$D/scratch/provenance-target"
export TMPDIR="$D/scratch/tmp" CARGO_BUILD_JOBS=4
export RH_FOLD=1 RH_FOLD_SLOTS=1 RH_FOLD_JOIN=1 RH_FOLD_TAIL=1 RH_BRK_ALLARMS=1 RH_SCHED=sccq
mkdir -p "$TMPDIR" "$CARGO_HOME"
cd "$src"
case "${1:-observe}" in
  contract|pending|guard)
    selected=producer_reason_provenance_contract
    [ "$1" != pending ] || selected=producer_reason_pending_contract
    [ "$1" != guard ] || selected=producer_reason_guard_contract
    cargo +1.98.1 test --locked --lib "$selected" -- --ignored --nocapture --test-threads=1 ;;
  observe)
    cargo +1.98.1 test --locked --lib producer_reason_provenance_observe -- --nocapture --test-threads=1 ;;
  *) echo 'usage: provenance.sh [observe|contract|pending|guard]' >&2; exit 2 ;;
esac
