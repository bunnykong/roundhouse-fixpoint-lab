#!/bin/bash
set -euo pipefail
K=$(cd "$(dirname "$0")" && pwd)
WORK=$(dirname "$K")
python3 -B -I "$K/verify_freeze.py" "$WORK" replay
python3 -B -I "$K/verdict.py" --stage campfire --emission "$WORK/emission/compare.json" \
  --suite "$WORK/receipts/suite.json" --out "$WORK/replayed-campfire"
if [ -f "$WORK/verdict/verdict.json" ]; then
  python3 -B -I "$K/verdict.py" --stage all --emission "$WORK/emission/compare.json" \
    --suite "$WORK/receipts/suite.json" --out "$WORK/replayed"
fi
