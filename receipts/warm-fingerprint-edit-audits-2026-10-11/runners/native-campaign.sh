#!/usr/bin/env bash
# Fresh full replication recipe. This was syntax-checked, not run during publication.
set -euo pipefail
if [ "$#" -ne 2 ]; then
  echo 'usage: bash native-campaign.sh /absolute/fresh/work /absolute/shared-host.lock' >&2
  exit 2
fi
campaign_root="$1"
coordination_lock="$2"
case "$campaign_root" in /*) ;; *) echo 'work must be absolute' >&2; exit 2;; esac
case "$coordination_lock" in /*) ;; *) echo 'lock must be absolute' >&2; exit 2;; esac
test ! -e "$campaign_root"
mkdir -p "$campaign_root/sources" "$campaign_root/trials" "$campaign_root/tmp"
runner_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export WARM_EDIT_AUDITS_WARM="$campaign_root"
export HOST_LOCK_TOOLS="$runner_root" HOST_LOCK_FILE="$coordination_lock"
export CARGO_BUILD_JOBS=4 RBENV_VERSION=4.0.7 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$campaign_root/tmp"
unset CARGO_TARGET_DIR
git clone https://github.com/bunnykong/roundhouse-fixpoint-lab.git "$campaign_root/sources/lab"
git -C "$campaign_root/sources/lab" checkout --detach 76cdb1ea24b0c4c88af4c42c78f567d759b7731d
sh "$campaign_root/sources/lab/corpus/fetch.sh"
git clone https://github.com/bunnykong/roundhouse.git "$campaign_root/trials/base"
git -C "$campaign_root/trials/base" checkout --detach d9ec78c31db361db8818b13153e5ddddee484c57
git clone --branch warm-fingerprint-edit-audits https://github.com/bunnykong/roundhouse.git \
  "$campaign_root/trials/fast"
git -C "$campaign_root/trials/fast" checkout --detach c5dfc633b0b28e0417934b701d92cacfdcc6a5b1
campaign_tools="$campaign_root/trials/fast/tools/research/warm-fingerprint-edit-audits"
for arm in base fast; do
  python3 "$runner_root/flock.py" --shared "$coordination_lock" \
    cargo +1.98.1 build --manifest-path "$campaign_root/trials/$arm/Cargo.toml" \
    --target-dir "$campaign_root/build/$arm" --release --locked --bin roundhouse
done
python3 -B "$campaign_tools/replay_pairs.py" \
  --source "$campaign_root/trials/base" --binary "$campaign_root/build/base/release/roundhouse" \
  --out "$campaign_root/runs/base-six" --condition fingerprint-fresh-base-six
python3 -B "$campaign_tools/replay_pairs.py" \
  --source "$campaign_root/trials/fast" --binary "$campaign_root/build/fast/release/roundhouse" \
  --out "$campaign_root/runs/fast-six-audit" --condition fingerprint-fresh-six-audit \
  --reference "$campaign_root/runs/base-six" --warm-flag RH_WARM_FP_AUDIT=1
python3 -B "$campaign_tools/reduce.py" --audit-only --out "$campaign_root/audit-gates.json"
python3 -B "$campaign_tools/replay_pairs.py" \
  --source "$campaign_root/trials/fast" --binary "$campaign_root/build/fast/release/roundhouse" \
  --out "$campaign_root/runs/fast-five" --condition fingerprint-fresh-five-pairs \
  --reference "$campaign_root/runs/base-six" --pairs 5
python3 -B "$campaign_tools/cold_campaign.py" --out "$campaign_root/runs/cold-five" \
  --condition fingerprint-fresh-cold-five --pairs 5
python3 -B "$campaign_tools/reduce.py" --out "$campaign_root/final-gates.json"
echo 'Inspect final-gates.json: completion, parity, useful cost, regression and 100 ms are separate results.'
