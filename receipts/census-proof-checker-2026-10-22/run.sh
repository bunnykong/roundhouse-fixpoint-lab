#!/bin/sh
# Rerun the checker's tests and the checker, then compare every output with the published one.
# Needs CRuby 4.0.7 (Prism 1.8.1), Python 3.9+ and checkouts of the pinned apps: run `sh corpus/fetch.sh`
# from the lab root, or set APPS to a directory with campfire, forem, chatwoot and mastodon at the same pins.
# Starts no analyzer. About 20 seconds.
set -eu
cd "$(dirname "$0")"
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
unxz() { python3 -B -c 'import lzma, sys; sys.stdout.buffer.write(lzma.open(sys.argv[1]).read())' "$1"; }
unxz rows.jsonl.xz > "$W/rows.jsonl"
unxz f72-rows.jsonl.xz > "$W/f72-rows.jsonl"
ruby test_checker.rb
ruby checker.rb "$W/rows.jsonl" "$W/verdicts.jsonl"
ruby checker.rb "$W/f72-rows.jsonl" "$W/f72-verdicts.jsonl"
PC_ABLATE_USES=1 ruby checker.rb "$W/f72-rows.jsonl" "$W/f72-ablated.jsonl"
unxz verdicts.jsonl.xz | cmp - "$W/verdicts.jsonl"
cmp f72-verdicts.jsonl "$W/f72-verdicts.jsonl"
cmp f72-ablated.jsonl "$W/f72-ablated.jsonl"
python3 -B validate.py "$W"
cmp agreement.tsv "$W/agreement.tsv"
cmp bound.json "$W/bound.json"
echo "all outputs match the published ones"
