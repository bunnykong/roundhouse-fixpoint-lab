#!/usr/bin/env python3
"""Assess fresh broad gates independently of the local entrance matrix."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "week/bound-next/results"
OUT = ROOT / "evidence/verification-v1"


def read(path):
    return json.loads(path.read_text())


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f19_pairs, f29_pairs, apps = [], [], []
    missing = []
    f19_path = RESULTS / "f19-bound-v1/summary.json"
    if f19_path.exists():
        f19 = read(f19_path)
        for old in (r for r in f19 if r["arm"] == "s3"):
            new = next(r for r in f19 if r["arm"] == "candidate"
                       and (r["program"], r["stage"]) == (old["program"], old["stage"]))
            old_lines = {v["record_line"] for v in old["violations"]}
            new_lines = {v["record_line"] for v in new["violations"]}
            f19_pairs.append(dict(program=old["program"], stage=old["stage"], records=new["records"],
                rejected_off=old["rejected"], rejected_on=new["rejected"],
                new_rejected_lines=sorted(new_lines - old_lines), coverage_equal=old["coverage"] == new["coverage"],
                coverage=new["coverage"], strict_gate=new["strict_selected_gate"]))
    else:
        missing.append("fresh F19 exports")
    save("f19-pairs.json", f19_pairs)
    if (RESULTS / "f29-bound-v1/summary.json").exists():
        for setting in ("P", "E", "I"):
            old = read(RESULTS / ("f29-bound-v1/s3-" + setting + ".json"))
            new = read(RESULTS / ("f29-bound-v1/candidate-" + setting + ".json"))
            old_rows = {r["record_line"]: r for r in old["arms"]["final"]["observations"]}
            new_rows = {r["record_line"]: r for r in new["arms"]["final"]["observations"]}
            assert old_rows.keys() == new_rows.keys()
            f29_pairs.append(dict(setting=setting, records=new["records"],
                new_rejections=[line for line, row in new_rows.items() if not row["accepted"] and old_rows[line]["accepted"]],
                decisions_equal=old_rows == new_rows, new_unknown_paths=new["paired_components"]["new_unknown_paths"],
                accepted_off=old["arms"]["final"]["accepted"], accepted_on=new["arms"]["final"]["accepted"],
                rejected_off=old["arms"]["final"]["rejected"], rejected_on=new["arms"]["final"]["rejected"],
                selected=new["selected_slots"], observed=new["observed_slots"], no_slot=new["no_slot"],
                missing=new["arms"]["final"]["category_slots"]["missing"]))
    else:
        missing.append("fresh F29 exports")
    save("f29-pairs.json", f29_pairs)
    for app in ("campfire", "mastodon", "chatwoot", "forem", "discourse"):
        path = RESULTS / (app + "-bound-v1/reports.json")
        if not path.exists():
            missing.append(app + " probes")
            continue
        rows = read(path)
        assert len(rows) == 15
        arms, pairs = {}, []
        for old in (r for r in rows if r["arm"] == "s3"):
            new = next(r for r in rows if r["arm"] == "candidate" and r["name"] == old["name"])
            fields = ("digest", "entries", "census", "precision", "loops", "structure")
            pairs.append(dict(name=old["name"], equal={f: old["report"].get(f) == new["report"].get(f) for f in fields},
                              bound_off=old["report"]["bound"], bound_on=new["report"]["bound"]))
        for arm in ("main-compatible", "s3", "candidate"):
            schedules = [r["report"] for r in rows if r["arm"] == arm and r["name"] != "precision"]
            assert len(schedules) == 4
            moved = [sum(sum(v["moved"].values()) for v in r["verify"]) for r in schedules]
            observed_data = all(r["verify"] and r["digest"] and r["entries"] and r["structure"]["end"]
                                for r in schedules)
            structure_equal = all(r["structure"]["end"] == schedules[0]["structure"]["end"] for r in schedules)
            values_equal = all(r["digest"] == schedules[0]["digest"] for r in schedules)
            precision = next(r["report"]["precision"] for r in rows if r["arm"] == arm and r["name"] == "precision")
            arms[arm] = dict(structure_equal=structure_equal, values_equal=values_equal, moved=moved,
                precision=precision, observed_data_complete=observed_data,
                any_order_sample_gate=observed_data and structure_equal and values_equal and not any(moved),
                complete_membership="not certified by this observer")
        apps.append(dict(app=app, pairs=pairs, arms=arms))
    save("app-pairs.json", apps)
    parity_path = RESULTS / "parity-v1/summary.json"
    parity = read(parity_path) if parity_path.exists() else None
    if parity is None:
        missing.append("emission/prepared-suite parity")
    runtime = dict(f19_no_new_rejections=bool(f19_pairs) and not any(r["new_rejected_lines"] for r in f19_pairs),
        f19_coverage_unchanged=bool(f19_pairs) and all(r["coverage_equal"] for r in f19_pairs),
        f29_no_new_rejections=bool(f29_pairs) and not any(r["new_rejections"] for r in f29_pairs),
        f29_no_new_opacity=bool(f29_pairs) and not any(r["new_unknown_paths"] for r in f29_pairs))
    whole = dict(f19_strict_coverage=bool(f19_pairs) and all(r["strict_gate"] for r in f19_pairs),
        all_app_schedule_gates=len(apps) == 5 and all(r["arms"]["candidate"]["any_order_sample_gate"] for r in apps),
        complete_structure_membership=False,
        emission_parity=parity is not None and parity["emission_equal"],
        shared_prepared_suite_parity=parity is not None and parity.get("suite_comparison_complete", True)
            and parity["shared_test_outcomes"] > 0 and not parity["changed_shared_outcomes"]
            and not parity["missing_candidate_tests"] and not parity["candidate_added_failures"])
    summary = dict(condition="reflective-array-20261015-fe6b169e", runtime=runtime, whole_priority=whole,
        incomplete=missing, whole_priority_verdict="confirmed" if all(runtime.values()) and all(whole.values()) else "inconclusive",
        new_runtime_violation=any(r["new_rejected_lines"] for r in f19_pairs)
            or any(r["new_rejections"] or r["new_unknown_paths"] for r in f29_pairs), timed_measurement=False)
    if summary["new_runtime_violation"]:
        summary["whole_priority_verdict"] = "killed"
    save("broad-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
