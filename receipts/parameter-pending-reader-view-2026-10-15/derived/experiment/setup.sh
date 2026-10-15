#!/usr/bin/env bash
set -euo pipefail
D=${1:-$(cd "$(dirname "$0")" && pwd)}
ROOT=$WORKSPACE
C1="$ROOT/agents/parameter-pending-value_only"
mkdir -p "$D/week/evidence/results/pending-factorial" "$D/week/evidence/scratch/tmp" "$D/week/tmp" "$D/patches"
C="$D/week/evidence/sources/probe-source"
git clone --no-hardlinks "$C1/week/evidence/sources/probe-source" "$C"
git -C "$C" switch -c parameter-pending-reader-view a7b6d3f8e7908581588662970804fc4d6dc53784
cp -R "$C1/week/evidence/sources/probe-source/fixtures/real-blog" \
  "$C1/week/evidence/sources/probe-source/fixtures/store" "$C/fixtures/"
git clone --no-hardlinks "$C1/week/evidence/sources/lab" "$D/week/evidence/sources/lab"
cp -R "$C1/week/cargo-home" "$D/week/cargo-home"
ln -s ../../cargo-home "$D/week/evidence/scratch/cargo-home"
cp -RL "$C1/week/evidence/scratch/apps" "$D/week/evidence/scratch/apps"
sed "s#^export D=.*#export D=$D#" "$C1/session.sh" > "$D/session.sh"
cp "$C1/week/evidence/results/pending-value_only-campfire/reports.json" "$D/week/evidence/results/pending-factorial/registered protocol-reports.json"
