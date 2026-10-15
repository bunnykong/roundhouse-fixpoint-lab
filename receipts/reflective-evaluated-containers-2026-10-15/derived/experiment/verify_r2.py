#!/usr/bin/env python3
"""Verify local entrance evidence; retain broader and composition failures."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
C = ROOT / "week/bound-next/sources/probe-source"
RESULTS = ROOT / "week/bound-next/results"
OUT = ROOT / "evidence/verification-v1"
BASE = "fe6b169ea935be900aa51e5a2069a360324a69b0"
NEXT = "38403140379cd69759b0fe6247c6a8c4a48a37a9"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text())


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def records(label, prefix):
    rows = []
    for line in (RESULTS / (label + ".log")).read_text().splitlines():
        m = re.search(re.escape(prefix) + r" (\{.*\})$", line)
        if m:
            rows.append(json.loads(m.group(1)))
    return rows


def git(*args):
    return subprocess.check_output(["git", "-C", str(C), *args], text=True)


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    labels = ("reflect-off", "reflect-on", "batch-off", "batch-on", "entrances-off", "entrances-on",
              "membership-on", "partitions-on", "pairwise-off", "pairwise-on", "parameter-schedule", "boundary-on")
    receipts = {label: load(RESULTS / (label + ".json")) for label in labels}
    binaries = set()
    for label, r in receipts.items():
        assert r["condition"] == "reflective-evaluated-containers-20261015-fe6b169e", label
        assert r["exit"] == r["expected_exit"], label
        assert len(r["results"]) == 1 and sum(row["passed"] + row["failed"] for row in r["results"]) > 0
        assert sha(RESULTS / (label + ".log")) == r["log_sha256"], label
        assert r["binary_sha256"], label
        binaries.update(r["binary_sha256"].values())
        for relative, digest in r["source_files_sha256"].items():
            assert sha(C / relative) == digest, (label, relative)
        for relative, digest in r["fixture_sha256"].items():
            assert sha(C / relative) == digest, (label, relative)
        assert all(p["checks"] > 0 for p in r["properties"])
    assert len(binaries) == 1, "all law comparisons must use the same binary"
    baseline = {s: load(RESULTS / (s + ".json")) for s in ("baseline-native-array", "baseline-containers")}
    for label, r in baseline.items():
        assert r["exit"] == 101 and r["results"][0]["failed"] > 0
        assert r["source_files_sha256"]["src/analyze/mod.rs"] == hashlib.sha256(
            subprocess.check_output(["git", "-C", str(C), "show", BASE + ":src/analyze/mod.rs"])).hexdigest()
    assert receipts["batch-off"]["properties"] == receipts["batch-on"]["properties"]
    assert receipts["pairwise-off"]["properties"] == receipts["pairwise-on"]["properties"]
    p6 = ROOT / "inherited/p6-results"
    for new, old in [("batch-on", "gate-batch-on"), ("pairwise-on", "gate-pairwise-on"),
                     ("parameter-schedule", "gate-parameter"), ("partitions-on", "gate-partitions")]:
        assert receipts[new]["properties"] == load(p6 / (old + ".json"))["properties"], new
    types = records("entrances-on", "REFLECTIVE-ENTRANCE-TYPE")
    containers = records("entrances-on", "P2R2-CONTAINER")
    assert types and containers
    sys.path.insert(0, str(ROOT / "week/bound-next/adapter"))
    from component_gate import paired_components
    for name, rows in [("original", types), ("containers", containers)]:
        assert len(rows) == len({str(row["case"]) for row in rows})
        assert all(row["native_plain"] == row["native_reflective"] and
                   row["plain_reasons"] == row["reflective_reasons"] for row in rows)
        control = {str(row["case"]): row["plain"] for row in rows}
        candidate = {str(row["case"]): row["reflective"] for row in rows}
        original = {str(row["case"]): row["input"] for row in rows}
        relative = paired_components(candidate, control)
        assert relative["passed"] and relative["new_unknown_paths"] == 0
        dump(name + "-components.json", relative)
        dump(name + "-inherited-opacity.json", paired_components(control, original))
        dump(name + "-types.json", rows)
    native = records("entrances-on", "P2R2-NATIVE")
    assert len(native) == 10 and all(row["eligible"] and row["storage_matches_plain"] for row in native)
    neighbours = records("entrances-on", "P2R2-NEIGHBOUR")
    assert len(neighbours) == 6
    assert all(row["actual_touched"] == row["expected_touched"] for row in neighbours)
    assert any(row["method"] == "write_forwarded_keywords" and "ForwardKeywordsWithPairs" in row["ir_kinds"]
               for row in neighbours)
    neighbour_baseline = load(RESULTS / "baseline-neighbours.json")
    assert neighbour_baseline["exit"] == 101 and neighbour_baseline["results"][0]["failed"] == 3
    dump("native-neighbours.json", neighbours)
    runtime = load(ROOT / "evidence/runtime-containers.json")
    assert runtime["ruby"] == "4.0.7" and len(runtime["cases"]) == 15
    assert all(row["stored"] and row["array_depth"] == 17 and row["leaf"] == 1 for row in runtime["cases"])
    assert len(runtime["deferred_controls"]) == 2 and all(not row["stored"] for row in runtime["deferred_controls"])
    original = git("show", NEXT + ":src/analyze/fixpoint_bound.rs")
    current = (C / "src/analyze/fixpoint_bound.rs").read_text()
    for name in ("writer_law_tests", "writer_law_partitions", "writer_law_tagged",
                 "writer_law_entrance_coverage", "writer_law_container_entrances"):
        current = current.replace("#[cfg(test)]\nmod " + name + ";\n", "")
    current = current.replace("#[cfg(test)]\nmod writer_law_container_neighbours;\n", "")
    current = current.replace("const MAX_NODES: usize = 512;\n\n\n", "const MAX_NODES: usize = 512;\n\n")
    assert current == original, "production cut policy must be unchanged"
    assert not git("diff", BASE, "--", "src/analyze/ivar_set.rs"), "eligibility/merge changed"
    partitions = records("partitions-on", "REFLECTIVE-ENTRANCE-PARTITION")
    dump("partition-counterexamples.json", partitions)
    metrics = {label: records(label, "REFLECTIVE-ENTRANCE-METRIC") + records(label, "P2R2-METRIC")
               for label in ("entrances-on", "membership-on", "partitions-on")}
    integration = {p.stem: load(p) for p in RESULTS.glob("integration-*-on.json")}
    if (RESULTS / "default-lib-on.json").exists():
        integration["default-lib-on"] = load(RESULTS / "default-lib-on.json")
    integration_summary = {label: dict(exit=r["exit"], results=r["results"]) for label, r in integration.items()}
    dump("integration.json", integration_summary)
    summary = dict(condition="reflective-evaluated-containers-20261015-fe6b169e", local_verdict="confirmed",
        whole_priority_verdict="inconclusive", law_binary_sha256=next(iter(binaries)),
        reason="Container entrances match the existing complete-body bound; broad integration is assessed separately.",
        cut_policy_unchanged=True, eligibility_unchanged=True, original_boundary_rows=len(types),
        container_boundary_rows=len(containers), native_entrances=native, runtime_cases=len(runtime["cases"]),
        native_neighbours=neighbours,
        metrics=metrics, partition_status="separately red; identical to P6", integration=integration_summary,
        receipts={label: dict(exit=r["exit"], results=r["results"], properties=r["properties"])
                  for label, r in receipts.items()}, timed_measurement=False)
    dump("summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("local_verdict", "whole_priority_verdict", "container_boundary_rows",
                                            "runtime_cases", "metrics", "integration")}, indent=2))


if __name__ == "__main__":
    main()
