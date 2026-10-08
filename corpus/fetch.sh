#!/bin/sh
# Exact commit pins are read from apps.json; application sources stay untracked.
set -eu
cd "$(dirname "$0")/.."
exec python3 -B corpus/fetch.py "$@"
