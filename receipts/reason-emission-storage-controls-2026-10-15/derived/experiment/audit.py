#!/usr/bin/env python3
"""Collect the registered provenance observations without stopping at the first difference."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KINDS = ("pending", "gradual", "unresolved")


def read(path):
    return json.loads(path.read_text())


def differences(left, right, prefix=""):
    if isinstance(left, dict) and isinstance(right, dict):
        out = []
        for key in sorted(set(left) | set(right)):
            out.extend(differences(left.get(key), right.get(key), prefix + "/" + key))
        return out
    return [] if left == right else [{"path": prefix, "left": left, "right": right}]


def shape_without_reasons(report):
    report = copy.deepcopy(report)
    report["census"].pop("untyped_by_provenance")
    return report


def timing_path(path):
    key = path.rsplit("/", 1)[-1]
    return key.endswith("_secs") or key.startswith(("secs_", "t_"))


def command_identity(row):
    fp = row["reports"]["rh-fixpoint"][0]
    return dict(exit=row["exit"], digest=fp["digest"], entries=fp["entries"],
                diagnostics=row["diagnostics"], summaries=row["summaries"],
                diagnostic_content=row["normalized_diagnostics_sha256"])


def inventory(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob("*")) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=ROOT / "evidence")
    parser.add_argument("--runs", type=Path, default=ROOT / "week/warm/runs")
    args = parser.parse_args()
    e, runs = args.evidence, args.runs
    out = dict(condition="reason-emission-storage-controls-20261015-71b09336")
    out["exits"] = dict(line.split("\t") for line in (e / "exits.tsv").read_text().splitlines())
    emission = {}
    for arm in ("base", "settle", "scramble"):
        pairs = [json.loads(line) for line in (e / ("emit-" + arm + ".jsonl")).read_text().splitlines()]
        reports = [json.loads(line.split(": ", 1)[1])
                   for line in (e / ("emit-" + arm + ".stderr")).read_text().splitlines()
                   if line.startswith("rh-fixpoint: ")]
        emission[arm] = dict(pair_count=len(pairs), pairs=pairs, analysis_count=len(reports),
            settled_exprs=sum(r["reason_settled_exprs"] for r in reports),
            scrambled_nodes=sum(r["reason_scrambled"] for r in reports),
            reports=reports, files=inventory(e / ("emit-" + arm)),
            receipts=[str(e / ("emit-" + arm + suffix)) for suffix in (".jsonl", ".stderr")])
    for arm in ("settle", "scramble"):
        emission[arm]["tree_differences"] = differences(emission["base"]["files"], emission[arm]["files"])
        emission[arm]["pair_differences"] = differences(emission["base"]["pairs"], emission[arm]["pairs"])
    out["emission"] = emission
    arms = {}
    for arm in ("legacy-g", "legacy-u", "lossless-g", "lossless-u"):
        path = runs / arm
        if not (path / "runs.json").exists():
            arms[arm] = dict(incomplete=True, stage="no completed command receipt",
                             metadata=read(path / "metadata.json") if (path / "metadata.json").exists() else None,
                             receipt=str(path / "runs.json"))
            continue
        rows = read(path / "runs.json")
        metadata = read(path / "metadata.json")
        flag_audit = {r["label"]: {key: r["flags"].get(key) == value
                                   for key, value in metadata["candidate_provenance_flags"].items()}
                      for r in rows}
        warm = next((r for r in rows if r["label"].endswith("-1-warm")), None)
        cold = next((r for r in rows if r["label"].endswith("-1-cold")), None)
        if warm is None or cold is None:
            arms[arm] = dict(incomplete=True, metadata=metadata, provenance_flag_propagation=flag_audit,
                             available_rows=rows, receipt=str(path / "runs.json"))
            continue
        wf, sf = warm["reports"]["rh-fixpoint"]
        cf = cold["reports"]["rh-fixpoint"][0]
        report = warm["reports"]["rh-warm"][0]
        arms[arm] = dict(
            warm=wf, shadow=sf, cold=cf,
            warm_census=wf["census"]["untyped_by_provenance"],
            shadow_census=sf["census"]["untyped_by_provenance"],
            cold_census=cf["census"]["untyped_by_provenance"],
            warm_settled=wf["reason_settled_exprs"], cold_settled=cf["reason_settled_exprs"],
            warm_report=report,
            warm_cold_identity_differences=differences(command_identity(warm), command_identity(cold)),
            warm_cold_census_differences=differences(wf["census"], cf["census"]),
            metadata=metadata, provenance_flag_propagation=flag_audit,
            receipts=[str(path / "runs" / r["label"] / "run.json") for r in (warm, cold)],
            cold_diagnostics=cold["diagnostics"], warm_diagnostics=warm["diagnostics"],
            cold_identity=command_identity(cold), cold_flags=cold["flags"],
        )
    out["arms"] = arms
    policy = {}
    for codec in ("legacy", "lossless"):
        g, u = arms[codec + "-g"], arms[codec + "-u"]
        if g.get("incomplete") or u.get("incomplete"):
            policy[codec] = dict(incomplete=True)
            continue
        delta = {k: u["cold_census"][k] - g["cold_census"][k] for k in KINDS}
        policy[codec] = dict(
            reason_delta_u_minus_g=delta,
            other_fixpoint_differences=differences(shape_without_reasons(g["cold"]), shape_without_reasons(u["cold"])),
            diagnostics_differences=differences(g["cold_diagnostics"], u["cold_diagnostics"]),
            delta_bounded=(0 <= -delta["gradual"] <= g["cold_settled"] and
                           0 <= delta["unresolved"] <= g["cold_settled"]),
            pending_zero=g["cold_census"]["pending"] == u["cold_census"]["pending"] == 0,
            cold_identity_differences=differences(g["cold_identity"], u["cold_identity"]),
        )
        policy[codec]["non_timing_fixpoint_differences"] = [
            diff for diff in policy[codec]["other_fixpoint_differences"] if not timing_path(diff["path"])]
    out["cold_policy_comparisons"] = policy
    if not any(arms[a].get("incomplete") for a in ("legacy-g", "lossless-g")):
        left, right = arms["legacy-g"], arms["lossless-g"]
        control_diffs = differences(shape_without_reasons(left["cold"]), shape_without_reasons(right["cold"]))
        out["same_flag_cold_control"] = dict(
            arms=["legacy-g", "lossless-g"], flags_equal=left["cold_flags"] == right["cold_flags"],
            fixpoint_differences=control_diffs,
            non_timing_fixpoint_differences=[d for d in control_diffs if not timing_path(d["path"])],
            cold_identity_differences=differences(left["cold_identity"], right["cold_identity"]))
    for arm, data in arms.items():
        if data.get("incomplete"):
            continue
        data["warm_minus_cold_reasons"] = {k: data["warm_census"][k] - data["cold_census"][k] for k in KINDS}
        if data["warm_census"]["pending"] == data["cold_census"]["pending"] == 0:
            data["gradual_and_unresolved_overlap"] = {
                role: data[role + "_census"]["gradual"] + data[role + "_census"]["unresolved"]
                      - data[role]["census"]["untyped_anywhere"]
                for role in ("warm", "cold")}
    (e / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"emission": {a: {k: r[k] for k in ("pair_count", "settled_exprs", "scrambled_nodes")}
                                  for a, r in emission.items()},
                      "arms": {a: {k: r[k] for k in ("warm_census", "cold_census", "warm_settled", "cold_settled",
                                                           "warm_minus_cold_reasons", "warm_cold_identity_differences",
                                                           "incomplete") if k in r}
                               for a, r in arms.items()},
                      "cold_policy_comparisons": policy}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
