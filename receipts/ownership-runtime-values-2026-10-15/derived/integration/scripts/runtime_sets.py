#!/usr/bin/env python3
"""Runtime-set classification of the 2,658 RESEARCH_PROFILE rows (recorded data only; no analyzer run).

Input: agents/ownership-runtime-values/receipts/rows.jsonl (condition ownership-runtime-values-20261015-f78d995f).
Reading: a type denotes the set of Ruby values it admits. `untyped` admits every value; a raw `Var`
prints as `untyped` (src/rbs.rs:1188 on the spine), so the primary reading treats it as admitting every
value too. The sensitivity reading `--var-pending` treats `Var` as admitting nothing (a pure pending
placeholder). nil, String, Symbol, bool, classes, Array/Hash/Fn are the usual sets; a union is a union.
Class subtyping is not modeled (different class names are incomparable), which can only over-report
NARROW/INCOMP, never hide one.

Relation of arm A to baseline at each row:
  EQ      same admitted set (includes every change that adds or drops an arm beside a remaining untyped)
  WIDEN   arm admits strictly more
  NARROW  arm admits strictly less: some value baseline admitted is now excluded
  INCOMP  each admits something the other excludes
  STRUCT  a storage cell exists on one side only (added/removed side-table or parameter cell)

Output: JSON summary to stdout; per-row TSV with --rows FILE.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROWS = Path(__file__).resolve().parents[2] / "ownership-runtime-values/receipts/rows.jsonl"
VAR_TOP = True


def top(t):
    k = t.get("kind")
    if k == "untyped":
        return True
    if k == "var":
        return VAR_TOP
    if k == "union":
        return any(top(v) for v in t["variants"])
    if k is None:  # bare effects record: no value shape recorded
        return True
    return False


def empty(t):
    k = t.get("kind")
    if k == "var":
        return not VAR_TOP
    if k == "union":
        return all(empty(v) for v in t["variants"])
    return False


def arms(t):
    if t.get("kind") == "union":
        out = []
        for v in t["variants"]:
            out.extend(arms(v))
        return out
    return [t]


def covers(a, b):
    """[[a]] contains [[b]]."""
    if empty(b):
        return True
    if top(a):
        return True
    if b.get("kind") == "union":
        return all(covers(a, v) for v in b["variants"] if not empty(v))
    if top(b):
        return False
    return any(covers1(x, b) for x in arms(a) if not empty(x))


def covers1(a, b):
    ka, kb = a.get("kind"), b.get("kind")
    if top(a):
        return True
    if ka != kb:
        return False
    if ka in ("nil", "str", "sym", "bool"):
        return True
    if ka == "class":
        aa, ba = a.get("args") or [], b.get("args") or []
        return a.get("id") == b.get("id") and len(aa) == len(ba) and all(covers(x, y) for x, y in zip(aa, ba))
    if ka == "array":
        return covers(a["elem"], b["elem"])
    if ka == "hash":
        return covers(a["key"], b["key"]) and covers(a["value"], b["value"])
    if ka == "fn":
        ra, rb = a.get("ret") or {"kind": None}, b.get("ret") or {"kind": None}
        return covers(ra, rb)
    return a == b


def relation(b, a):
    if b is None or a is None:
        return "STRUCT"
    ab, ba = covers(a, b), covers(b, a)
    if ab and ba:
        return "EQ"
    if ab:
        return "WIDEN"
    if ba:
        return "NARROW"
    return "INCOMP"


def show(t):
    k = t.get("kind")
    if k == "union":
        return " | ".join(show(v) for v in t["variants"])
    if k == "class":
        args = t.get("args") or []
        name = t.get("id")
        return name + ("[" + ", ".join(show(x) for x in args) + "]" if args else "")
    if k == "array":
        return "Array[%s]" % show(t["elem"])
    if k == "hash":
        return "Hash[%s, %s]" % (show(t["key"]), show(t["value"]))
    if k == "fn":
        return "Fn->%s" % show(t.get("ret") or {"kind": None})
    if k == "var":
        return "Var"
    if k is None:
        return "?"
    return {"untyped": "U", "nil": "nil", "str": "String", "sym": "Symbol", "bool": "Boolean"}.get(k, k)


def excluded(b, a):
    """Top-level baseline arms (or 'anything outside arm' for an untyped arm) that the arm no longer admits."""
    out = []
    for x in arms(b):
        if empty(x):
            continue
        if top(x) and not top(a):
            out.append("ANY-OUTSIDE(%s)" % show(a))
        elif not covers(a, x):
            out.append(show(x))
    return sorted(set(out))


def main():
    global VAR_TOP
    p = argparse.ArgumentParser()
    p.add_argument("--var-pending", action="store_true")
    p.add_argument("--rows")
    args = p.parse_args()
    VAR_TOP = not args.var_pending
    tally = Counter()
    by = defaultdict(Counter)
    lines = []
    for line in ROWS.open():
        r = json.loads(line)
        b = (r.get("baseline_row") or {}).get("resolved_ty")
        a = (r.get("arm_row") or {}).get("resolved_ty")
        rel = relation(b, a)
        tally[rel] += 1
        by[(r["app"], r["class"])][rel] += 1
        lost = excluded(b, a) if rel in ("NARROW", "INCOMP") else []
        lines.append("\t".join([r["row_id"], r["app"], r["schedule"], r["part"], r["root_method"], r["class"], rel,
                                show(b) if b else "absent", show(a) if a else "absent", ";".join(lost)]))
    if args.rows:
        Path(args.rows).write_text("row_id\tapp\tschedule\tpart\troot_method\tclassification_label\trelation\tbaseline\tarm\texcluded\n"
                                   + "\n".join(lines) + "\n")
    print(json.dumps({"var_reading": "top" if VAR_TOP else "pending", "relation": tally,
                      "by_app_and_classification_label": {"%s/%s" % k: v for k, v in sorted(by.items())}}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
