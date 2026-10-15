#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DEST="$HERE/reruns/$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p "$DEST"
cp "$HERE/protocol.md" "$HERE/run-card.sh" "$HERE/summarize.py" "$HERE/audit.py" "$HERE/clean.sh" "$DEST/"
bash "$HERE/setup.sh" "$DEST" > "$DEST/setup.log" 2>&1
source "$DEST/session.sh"
trap 'bash "$DEST/clean.sh"' EXIT
cp "$HERE/patches/0001-lineage-factorial.patch" "$DEST/patches/"
(cd "$C" && git am "$DEST/patches/0001-lineage-factorial.patch") > "$DEST/patch-apply.log" 2>&1
bash "$DEST/run-card.sh" > "$DEST/run-card.log" 2>&1
python3 "$DEST/summarize.py" "$DEST" > "$DEST/summary.stdout"
python3 "$DEST/audit.py" "$DEST" > "$DEST/audit.stdout"
printf 'Rerun receipts: %s\n' "$DEST/week/evidence/results/pending-factorial"
