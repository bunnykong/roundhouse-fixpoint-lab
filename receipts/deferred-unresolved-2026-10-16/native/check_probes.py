"""Lightweight deferral-protocol reducer probes; no compiler or application is invoked."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KIT = ROOT / "deferred_unresolved"
sys.path.insert(0, str(KIT))
import verdict as v

NATIVE = ROOT / "probe-native"
v.write_native(NATIVE)


def respec(store, arm, app, setting, update, boundary=None, pins=None):
    cell = copy.deepcopy(store.data[(arm, app, setting)])
    cell["rows"].update(copy.deepcopy(update))
    cell["rows"] = {k: x for k, x in cell["rows"].items() if x is not None}
    if boundary is not None:
        cell["boundary"].update(copy.deepcopy(boundary))
    cell["obs"]["value_digests"] = v.digests_of(v.fake_rows(cell["rows"])[0])
    store.data[(arm, app, setting)] = cell
    if pins is not None:
        pins["cells"][app + "/" + setting]["digests"] = cell["obs"]["value_digests"]


def run(name, mutate, expected):
    store, pins, kpins, targets = v.fixture()
    mutate(store, pins)
    result = v.evaluate(store, pins, kpins, targets, NATIVE)
    deciding = [{k: c[k] for k in ("check", "scope", "status", "detail")}
                for c in result["checks"] if c["mandatory"] and c["status"] != "pass"]
    return {"probe": name, "required_by_card": expected, "actual": result["verdict"],
            "family_verdicts": result["family_verdicts"],
            "records": deciding}


def change_n(store, pins, kind):
    key = ("N", "campfire", "unset-v1-a1")
    d = copy.deepcopy(store.data[key])
    if kind == "cap":
        d["obs"]["loops"]["production"]["end"] = "ran_to_cap"
        d["report"]["worklist"]["engine"]["cap_hits"] = 1
    elif kind == "verify":
        d["obs"]["verify"] = []
    elif kind == "pending":
        d["obs"]["reason_census"]["untyped_by_provenance"]["pending"] = 1
    elif kind == "report":
        d["report"] = None
    store.data[key] = d


def legal_n_merge(store, pins):
    # Ty::canonical_min under A1 merges provenance recursively in semantically
    # equal Array variants. No Gradual or Unresolved evidence is lost.
    def array(t):
        return {"kind": "array", "elem": t}
    before = v.union(array(v.G), array(v.U), v.NIL)
    after = v.union(array({"kind": "untyped", "reasons": ["Gradual", "Unresolved"]}), v.NIL)
    assert v._blind(before) == v._blind(after)
    for s in v.S:
        setting = s + "-v1-a1"
        for arm in ("C", "D", "DS", "N", "DSN"):
            ty = after if arm in ("N", "DSN") else before
            update = {("returns", "Merge#value"): {"ty": ty}}
            respec(store, arm, "campfire", setting, update,
                   boundary=update if arm in ("DS", "DSN") else None,
                   pins=pins if arm == "C" else None)


def changed_varying_row(store, pins):
    for s in v.S:
        setting = s + "-v1-a1"
        before = v.INT if s == "unset" else v.STR
        respec(store, "C", "forem", setting,
               {("returns", "NonTarget#varying"): {"ty": before}}, pins=pins)
        respec(store, "DS", "forem", setting,
               {("returns", "NonTarget#varying"): {"ty": {"kind": "bool"}}},
               boundary={("returns", "NonTarget#varying"): {"ty": v.INT}})


def fail_and_unknown(store, pins):
    for s in v.S:
        update = {("returns", "K#k"): {"ty": v.STR},
                  ("params", "M#m[0]"): {"ty": v.union(v.USER, {"kind": "untyped"})}}
        respec(store, "DS", "campfire", s + "-v1-a1", update, boundary=update)


def nested_fail_and_unknown(store, pins):
    before = {"kind": "tuple", "elems": [v.INT, v.U]}
    after = {"kind": "tuple", "elems": [v.STR, {"kind": "untyped"}]}
    for s in v.S:
        setting = s + "-v1-a1"
        for arm in ("C", "D", "DS", "N", "DSN"):
            ty = after if arm == "DS" else before
            update = {("returns", "Tuple#mixed"): {"ty": ty}}
            respec(store, arm, "campfire", setting, update,
                   boundary=update if arm in ("DS", "DSN") else None,
                   pins=pins if arm == "C" else None)


def unchanged_missing_provenance(store, pins):
    for s in v.S:
        for arm in ("C", "D", "DS", "N", "DSN"):
            update = {("returns", "Missing#reason"): {"ty": {"kind": "untyped"}}}
            respec(store, arm, "campfire", s + "-v1-a1", update,
                   boundary=update if arm in ("DS", "DSN") else None,
                   pins=pins if arm == "C" else None)


def malformed_n_type(store, pins):
    for s in v.S:
        respec(store, "N", "campfire", s + "-v1-a1",
               {("params", "Dup#d[0]"): {"ty": {"kind": "union", "variants": 42}}})


def raw_incomplete_ir():
    folder = ROOT / "probe-incomplete-ir"
    folder.mkdir(exist_ok=True)
    digests = dict.fromkeys(v.TABLES, "native-pinned-digest")
    header = {"part": "fingerprint", "parts": {t: {} for t in v.TABLES if t != "ir"},
              "ir": [[1, 0, 1, 42, 7]], "digests": digests}
    # The header records an IR node, but no row for it is present.
    (folder / "contributor-values.jsonl").write_text(json.dumps(header) + "\n")
    store = object.__new__(v.ObsStore)
    store.cell = lambda *_: ({"value_digests": digests}, str(folder), {})
    got = store._rows("DS", "campfire", "unset-v1-a1", "final")
    return {"probe": "raw dump omits the IR node named in its fingerprint",
            "required_by_card": "unavailable", "actual": "accepted" if got is not None else "unavailable"}


results = [run("baseline", lambda *_: None, "CONFIRMED")]
for kind in ("cap", "verify", "pending", "report"):
    want = "KILLED" if kind in ("cap", "pending") else "INCONCLUSIVE"
    results.append(run("N missing INV: " + kind, lambda a, b, k=kind: change_n(a, b, k), want))
results += [run("N's lawful equal-arm provenance merge", legal_n_merge, "CONFIRMED"),
            run("stratum 2 changes a non-target C-varying row to a new concrete type", changed_varying_row, "KILLED"),
            run("direction has a violation and missing provenance together", fail_and_unknown, "INCONCLUSIVE"),
            run("one tuple has a violation and missing provenance together", nested_fail_and_unknown, "INCONCLUSIVE"),
            run("unchanged untyped row lacks provenance", unchanged_missing_provenance, "INCONCLUSIVE"),
            run("malformed N type: family N must be inconclusive too", malformed_n_type, "INCONCLUSIVE"),
            raw_incomplete_ir()]
(ROOT / "probe-results.json").write_text(json.dumps(results, indent=2) + "\n")
for r in results:
    print(r["probe"] + ": " + r["actual"] + " (card requires " + r["required_by_card"] + ")")
    if r["probe"].startswith("malformed N"):
        print("  family verdicts: " + json.dumps(r["family_verdicts"], sort_keys=True))

for r in results:
    assert r["actual"].startswith(r["required_by_card"]), r
    if r["probe"].startswith("malformed N"):
        assert r["family_verdicts"]["N"].startswith("INCONCLUSIVE"), r
print("All second-check probes pass")
