#!/usr/bin/env python3
"""Look up recorded slot values in the contributor-classify value-probe dumps (no analyzer run).

  values.py APP SERIES SCHEDULE PART REGEX [REGEX ...]

APP in forem|chatwoot|mastodon, SERIES in baseline|a, SCHEDULE in unset|1|2|repeat, PART e.g. returns|params.
Prints key and the raw debug type for every record whose key matches one of the regexes (full match).
Condition of the dumps: ownership-runtime-value-probes-20261015-f78d995f (reproduces ownership-runtime-values-20261015-f78d995f digests).
"""
import json
import re
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parents[2] / "ownership-runtime-values/observer-cache"


def dump(app, series, schedule):
    label = json.loads((CACHE / "labels" / ("contributor-values-%s-%s" % (series, app)) / "label.json").read_text())
    cell = label["cells"]["%s/%s-v0-a0" % (app, schedule)]
    d = Path(cell["result"]).parent
    hits = sorted(d.glob("**/contributor-values.jsonl"))
    if not hits:
        raise SystemExit("no contributor-values.jsonl under " + str(d))
    return hits[-1]


def main(argv):
    app, series, schedule, part = argv[:4]
    pats = [re.compile(p) for p in argv[4:]]
    path = dump(app, series, schedule)
    with path.open() as fh:
        for line in fh:
            if '"part":"%s"' % part not in line:
                continue
            r = json.loads(line)
            if r.get("part") != part:
                continue
            if any(p.fullmatch(r.get("key", "")) for p in pats):
                print("%-70s %s" % (r["key"], r.get("debug", "")[:160]))


if __name__ == "__main__":
    main(sys.argv[1:])
