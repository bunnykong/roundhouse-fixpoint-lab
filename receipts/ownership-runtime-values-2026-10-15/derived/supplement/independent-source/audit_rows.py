#!/usr/bin/env python3
"""Independent recount and concrete-class admission checks for the recorded research condition rows."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRONTIER = HERE.parent / "frontier"
CLASSIFY = FRONTIER / "agents/ownership-runtime-values"
INTEGRATOR = FRONTIER / "agents/ownership-runtime-integration"
TOP = ("top",)


def normalize(t):
    kind = t.get("kind")
    if kind in (None, "untyped", "var"):
        return frozenset([TOP])
    if kind == "union":
        result = frozenset(a for v in t["variants"] for a in normalize(v))
        return frozenset([TOP]) if TOP in result else result
    if kind == "class":
        atom = (kind, t["id"], tuple(normalize(a) for a in t.get("args", [])))
    elif kind == "array":
        atom = (kind, normalize(t["elem"]))
    elif kind == "hash":
        atom = (kind, normalize(t["key"]), normalize(t["value"]))
    elif kind == "fn":
        atom = (kind, normalize(t.get("ret") or {}))
    else:
        assert kind in ("nil", "str", "bool", "sym"), t
        atom = (kind,)
    return frozenset([atom])


def atom_subset(a, b):
    if b == TOP or a == b:
        return True
    if a == TOP or a[0] != b[0]:
        return False
    if a[0] == "class":
        return (a[1] == b[1] and len(a[2]) == len(b[2])
                and all(subset(x, y) for x, y in zip(a[2], b[2])))
    if a[0] in ("array", "hash", "fn"):
        return all(subset(x, y) for x, y in zip(a[1:], b[1:]))
    return False


def subset(a, b):
    return all(any(atom_subset(x, y) for y in b) for x in a)


def relation(b, a):
    if b is None or a is None:
        return "STRUCT"
    b, a = normalize(b), normalize(a)
    if a == b:
        return "EQ"
    small, large = subset(a, b), subset(b, a)
    return "EQ" if small and large else "NARROW" if small else "WIDEN" if large else "INCOMP"


def admits(t, ruby_class):
    k = t["kind"]
    if k in ("untyped", "var"):
        return True
    if k == "union":
        return any(admits(v, ruby_class) for v in t["variants"])
    if k == "class":
        return t["id"] == ruby_class
    return ruby_class in {"nil": {"NilClass"}, "str": {"String"},
                          "bool": {"TrueClass", "FalseClass"}, "sym": {"Symbol"},
                          "array": {"Array"}, "hash": {"Hash"}}.get(k, set())


def result_type(t):
    # A Lambda row records its result type, so apply the callee observation to that result.
    return t["ret"] if t.get("kind") == "fn" else t


def has_class(t, name):
    if isinstance(t, dict):
        return (t.get("kind") == "class" and t.get("id") == name
                or any(has_class(v, name) for v in t.values()))
    return isinstance(t, list) and any(has_class(v, name) for v in t)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = CLASSIFY / "receipts/rows.jsonl"
    rows = [json.loads(line) for line in source.open()]
    replay = json.loads((HERE / "runtime-replay.json").read_text())
    frozen = json.loads((CLASSIFY / "receipts/runtime-witnesses-v3.json").read_text())
    # Ruby's default object strings include nondeterministic allocation addresses.
    scrub = lambda x: re.sub(r"0x[0-9a-f]+", "0xADDRESS", json.dumps(x, sort_keys=True))
    assert scrub(replay) == scrub(frozen)
    assert len(replay["observations"]) == 35
    observations = {o["label"]: o for o in replay["observations"]}
    observed_classes = {o["ruby_class"] for o in observations.values()}
    expected_rel = {r["row_id"]: r["relation"] for r in csv.DictReader(
        (INTEGRATOR / "evidence/runtime-rows.tsv").open(), delimiter="\t")}
    expected_ver = {r["row_id"]: r["verdict"] for r in csv.DictReader(
        (INTEGRATOR / "evidence/narrow-verdicts.tsv").open(), delimiter="\t")}
    counts, families, parts, computed = Counter(), Counter(), Counter(), []
    for r in rows:
        b = (r.get("baseline_row") or {}).get("resolved_ty")
        a = (r.get("arm_row") or {}).get("resolved_ty")
        rel = relation(b, a)
        assert rel == expected_rel[r["row_id"]], r["row_id"]
        counts[rel] += 1
        family, witness_classes, verdict = None, [], None
        if rel == "NARROW":
            method = r["root_method"].split("#")[-1]
            if r["app"] == "forem":
                family, witness_classes = "Forem render/redirect", ["String"]
            elif method in {"check_account_suspension", "permanent_unavailability_response",
                            "temporary_suspension_response"}:
                family, witness_classes = "Mastodon suspension", ["String"]
            elif r["root_method"] == "Api::Web::EmbedsController#show":
                family, witness_classes = "Mastodon embeds (source inference; supplemented)", ["String"]
            elif method == "first_lang_string" and r["part"] == "returns":
                family, witness_classes = "JSON-LD return", ["Integer", "String"]
            elif has_class(a, "Admin::ActionLog"):
                family, witness_classes = "log_action", ["Admin::ActionLog"]
            elif method == "pundit_user":
                family, witness_classes = "pundit_user", ["NilClass", "Account"]
            if family:
                assert set(witness_classes) <= observed_classes
                checks = [(c, admits(result_type(b), c), admits(result_type(a), c))
                          for c in witness_classes]
                assert all(b_ok for _, b_ok, _ in checks), r["row_id"]
                verdict = "UNSOUND_W" if any(not a_ok for _, _, a_ok in checks) else "SOUND_W"
                assert verdict == expected_ver[r["row_id"]], (r["row_id"], checks)
                families[family] += 1
                parts[(verdict, r["app"], r["part"])] += 1
            else:
                checks = []
        else:
            checks = []
        computed.append({"row_id": r["row_id"], "app": r["app"], "schedule": r["schedule"],
                         "part": r["part"], "root_method": r["root_method"], "key": r["key"],
                         "relation": rel, "family": family, "verdict": verdict,
                         "checks": [{"class": c, "main_admits": x, "variant_admits": y} for c, x, y in checks]})
    verdict_counts = Counter(r["verdict"] for r in computed if r["verdict"])
    assert verdict_counts == {"UNSOUND_W": 578, "SOUND_W": 900}, verdict_counts
    source_checks = []
    for s in replay["sources"]:
        path = Path(s["path"])
        assert sha(path) == s["sha256"], path
        source_checks.append({"path": str(path), "method": s["method"], "line": s["line"],
                              "sha256": s["sha256"]})
    integrity = json.loads((CLASSIFY / "receipts/integrity.json").read_text())
    for p in ["receipts/rows.jsonl", "receipts/runtime-witnesses-v3.json", "witnesses/ownership.rb"]:
        assert sha(CLASSIFY / p) == integrity["files"][p]
    result = {"condition": "ownership-runtime-values-20261015-f78d995f", "rows": len(rows),
              "distinct_keys": len({(r["app"], r["part"], r["key"]) for r in rows}),
              "classification": Counter(r["class"] for r in rows), "relations": counts,
              "verdicts_checked_by_admission": verdict_counts, "families": families,
              "parts": {"/".join(k): v for k, v in parts.items()},
              "ruby": replay["ruby"], "replayed_observations": len(observations),
              "replay_matches_after_scrubbing_object_addresses": True,
              "source_method_hashes_checked": len(source_checks),
              "input_sha256": {str(source): sha(source),
                               str(CLASSIFY / "receipts/runtime-witnesses-v3.json"):
                               sha(CLASSIFY / "receipts/runtime-witnesses-v3.json")}}
    (HERE / "recount.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "checked-rows.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in computed))
    (HERE / "witness-source-checks.json").write_text(json.dumps(source_checks, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
