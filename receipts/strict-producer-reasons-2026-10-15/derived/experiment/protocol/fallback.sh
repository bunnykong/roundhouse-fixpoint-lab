#!/usr/bin/env bash
# fallback.sh OUTROOT LABEL PROFILE APP SETTINGS BIN
# Only if phase2/observers/obs.py cannot run. Writes OUTROOT/LABEL/APP/SETTING/{stderr.log,census.jsonl,report.json,exit}
# with obs.py's default flags plus PROFILE, so verdict.py --fallback-root OUTROOT reduces them with obs.py's reducer.
# SETTINGS is a comma list such as unset-v0-a0,1-v1-a1. Each analyzer run takes one shared heavy-lock slot.
set -o pipefail
out=${1:?outroot}; label=${2:?label}; profile=${3:?profile}; app=${4:?app}; settings=${5:?settings}; bin=${6:?bin}
F=$WORKSPACE
for v in $(env | sed -n 's/^\(RH_[A-Z0-9_]*\)=.*/\1/p'); do unset "$v"; done
path=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]]["path"])' \
  "$F/phase2/observers/apps.json" "$app") || exit 2
apps=$(cd "$F/$(dirname "$path")" && pwd); name=$(basename "$path")
mapfile_profile=$(python3 -c 'import json,sys; print(" ".join(k+"="+v for k,v in sorted(json.load(open(sys.argv[1])).items()) if v is not None))' "$profile")
IFS=',' read -r -a cells <<< "$settings"
for setting in "${cells[@]}"; do
  [[ "$setting" =~ ^(unset|1|2|repeat)-v([01])-a([01])$ ]] || { echo "bad setting $setting" >&2; exit 2; }
  s=${BASH_REMATCH[1]}; v=${BASH_REMATCH[2]}; a=${BASH_REMATCH[3]}
  X=(RH_FIXPOINT_VERIFY=$v RH_PROVENANCE_AUDIT=$a RH_PRECISION_CENSUS=1 RH_ERRGATE=1 RH_PUBLIC_INPUT=1)
  case $s in 1) X+=(RH_SHUFFLE=1);; 2) X+=(RH_SHUFFLE=2);; esac
  R="$out/$label/$app/$setting"; mkdir -p "$R"
  [ -e "$R/exit" ] && continue  # never overwrite a recorded cell
  (cd "$R" && RH_BIN="$bin" APPS="$apps" PROBE_BASE=0 RBENV_VERSION=4.0.7 LC_ALL=C \
    python3 "$F/workshop/flock.py" "$F/workshop/heavy.lock" bash "$F/agents/parameter-storage-normal-form/probe" "$name" \
    "${X[@]}" $mapfile_profile RH_REASON_SITE_CENSUS="$R/census.jsonl" > report.json; echo $? > exit.tmp)
  mv "$R/probe-$name.stderr" "$R/stderr.log" 2>/dev/null; mv "$R/exit.tmp" "$R/exit"
done
