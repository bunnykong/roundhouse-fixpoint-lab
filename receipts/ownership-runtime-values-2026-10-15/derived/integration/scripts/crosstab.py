#!/usr/bin/env python3
"""Cross-tabulate runtime classifier's support-census columns against prior classifier's per-row classes.

Reads recorded data only (condition ownership-runtime-values-20261015-f78d995f):
  * runtime classifier's census inputs: agents/ownership-generalization/{evidence/*-unset-copyrows-origins.txt, runs/*/*/*/compact.json}
  * prior classifier's table: agents/ownership-runtime-values/receipts/rows.tsv

For every spliced return slot (target C#name) it prints the census column under arm A at each schedule
(none = no own support; inf = own support, module informative; masked = own support, module uninformative)
and prior classifier's class and resolved transition for the slot's `returns` row at that schedule, if it changed.
Run: python3 -I crosstab.py > ../evidence/crosstab.txt
"""
import csv
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

F = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("census", F / "phase2/contributor-ownership/support_census.py")
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)
GEN = F / "agents/ownership-generalization"
ROWS = F / "agents/ownership-runtime-values/receipts/rows.tsv"
SCHED = {"unset": "unset", "1": "1", "2": "2", "repeat": "repeat-unset"}

csv.field_size_limit(1 << 30)
rows = defaultdict(dict)  # (app, schedule, key) -> row, for returns part only
allrows = []
with ROWS.open() as fh:
    for r in csv.DictReader(fh, delimiter="\t"):
        allrows.append(r)
        if r["part"] == "returns":
            rows[(r["app"], r["schedule"])][r["key"]] = r

out = {}
for app in ("forem", "chatwoot", "mastodon"):
    pairs = census.spliced_rows(app)
    by_target = defaultdict(set)
    for t, m in pairs:
        by_target[t].add(m)
    targets = sorted(by_target)
    table = {}
    for series in ("a", "baseline"):
        for sched, csched in SCHED.items():
            concrete, attempt, mutation = census.inventories(GEN / "runs" / series / app / csched / "compact.json")
            for t in targets:
                own = t in concrete
                mod = any(m in concrete for m in by_target[t])
                col = "none" if not own else ("inf" if mod else "masked")
                table.setdefault(t, {})[(series, sched)] = (col, mod)
    print("==", app, len(targets), "spliced targets")
    counts = Counter()
    for t in targets:
        name = t[0] + "#" + t[2] if t[1] == "instance" else t[0] + ".#" + t[2]
        cols = [table[t][("a", s)][0] for s in SCHED]
        changed = []
        for s in SCHED:
            r = rows[(app, s)].get(name)
            if r:
                changed.append("%s:%s:%s:%s=>%s" % (s, r["row_id"], r["class"][0], r["resolved_baseline_value"], r["resolved_arm_value"]))
        mods = sorted("%s" % m[0] for m in by_target[t])
        key = (cols[0], bool(changed))
        counts[key] += 1
        print("%-70s a-cols=%s modules=%s" % (name, "/".join(cols), ",".join(mods)))
        for c in changed:
            print("      ", c)
    print("  summary (a/unset column, returns changed in any schedule):", dict(counts))
    # returns rows in prior classifier's table that are not spliced targets
    names = {(t[0] + "#" + t[2]) for t in targets}
    extra = sorted({k for s in SCHED for k in rows[(app, s)] if k not in names})
    print("  changed return keys that are not spliced targets:", len(extra))
    for k in extra:
        vals = ["%s:%s:%s:%s=>%s" % (s, rows[(app, s)][k]["row_id"], rows[(app, s)][k]["class"][0],
                                     rows[(app, s)][k]["resolved_baseline_value"], rows[(app, s)][k]["resolved_arm_value"])
                for s in SCHED if k in rows[(app, s)]]
        print("    ", k, " | ".join(vals))
