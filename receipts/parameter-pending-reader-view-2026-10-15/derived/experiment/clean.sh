#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/session.sh"
names=(laws provenance)
[ -d "$E/scratch/default-control-target" ] && names+=(default-control)
for name in "${names[@]}"; do
  case "$name" in
    laws) target="$C/target-laws";;
    provenance) target="$E/scratch/provenance-target";;
    default-control) target="$E/scratch/default-control-target";;
  esac
  status=0
  (cd "$C" && heavy env CARGO_TARGET_DIR="$target" cargo +1.98.1 clean) \
     > "$R/pending-factorial/clean-$name.log" 2>&1 || status=$?
  echo "$status" > "$R/pending-factorial/clean-$name.exit"
  [ "$status" -eq 0 ] || exit "$status"
done
python3 - "$D" <<'PY'
from pathlib import Path
import json,sys,datetime
D=Path(sys.argv[1])
paths=[D/'week/evidence/sources/probe-source/target-laws',D/'week/evidence/scratch/provenance-target',
       D/'week/evidence/scratch/default-control-target']
# Cargo can keep an empty directory containing only its cache bookkeeping.
remaining={str(p.relative_to(D)): [str(f.relative_to(p)) for f in p.rglob('*') if f.is_file()] if p.exists() else [] for p in paths}
assert all(not files for files in remaining.values()),remaining
(D/'week/evidence/results/pending-factorial/cleanup.json').write_text(json.dumps({
 'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'targets':remaining,'clean_exit_codes':{p.name.removeprefix('clean-').removesuffix('.exit'):int(p.read_text())
   for p in (D/'week/evidence/results/pending-factorial').glob('clean-*.exit')}},indent=2)+'\n')
PY
