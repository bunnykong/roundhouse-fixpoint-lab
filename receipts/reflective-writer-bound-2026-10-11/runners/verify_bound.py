#!/usr/bin/env python3
"""Evaluate the move's bounded gate, separating inherited partition failures."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "week" / "bound" / "results"
GUARD = ROOT / "scripts"


def read(label):
    return json.loads((RESULTS / (label + ".json")).read_text())


def records(label, prefix):
    rows = []
    for line in (RESULTS / (label + ".log")).read_text().splitlines():
        match = re.search(re.escape(prefix) + r" (\{.*\})$", line)
        if match:
            rows.append(json.loads(match.group(1)))
    return rows


def property_rows(receipt, writer):
    return [row for row in receipt["properties"] if row["writer"] == writer]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-suffix", default="")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Use a fresh output label")
    args.output.mkdir(parents=True)
    labels = ["reflect-before", "batch-before", "bound-before", "reflect-after", "batch-after",
              "entrances", "membership-canaries", "partitions", "bound-after", "default-library",
              "default-library-control", "reflective-integration"]
    label_paths = {label: label + args.candidate_suffix if label in
        ("reflect-after", "batch-after", "entrances", "membership-canaries", "partitions", "bound-after", "default-library")
        else label for label in labels}
    receipts = {label: read(path) for label, path in label_paths.items()}
    for label, receipt in receipts.items():
        # The first extra default-library attempt exposed missing fixtures;
        # retain its original expectation and compare its failures to control.
        assert receipt["exit"] == receipt["expected_exit"] or label == "default-library", label
        assert len(receipt["results"]) == 1, label
        result = receipt["results"][0]
        assert result["passed"] + result["failed"] > 0, label
        assert all(row["checks"] > 0 for row in receipt["properties"]), label
    control = receipts["bound-before"]
    candidate = receipts["bound-after"]
    inherited = {}
    for writer in ("bound/join_ivar_slot", "bound/unify_param_ty", "fixpoint_bound/boundary-universe"):
        before = property_rows(control, writer)
        after = property_rows(candidate, writer)
        assert before and before == after, writer
        inherited[writer] = before
    types = records(label_paths["entrances"], "BOUND-ENTRANCE-TYPE")
    assert types and len({row["case"] for row in types}) == len(types)
    sys.path.insert(0, str(GUARD))
    from component_gate import paired_components
    plain = {str(row["case"]): row["plain"] for row in types}
    reflective = {str(row["case"]): row["reflective"] for row in types}
    original = {str(row["case"]): row["input"] for row in types}
    paired = paired_components(reflective, plain)
    assert paired["passed"] and paired["new_unknown_paths"] == 0
    (args.output / "paired-components.json").write_text(json.dumps(paired, indent=2, sort_keys=True) + "\n")
    expected_cuts = paired_components(plain, original)
    (args.output / "existing-bound-opacity.json").write_text(json.dumps(expected_cuts, indent=2, sort_keys=True) + "\n")
    (args.output / "boundary-types.json").write_text(json.dumps(types, indent=2, sort_keys=True) + "\n")
    witnesses = records(label_paths["partitions"], "BOUND-ENTRANCE-PARTITION")
    (args.output / "partition-counterexamples.json").write_text(json.dumps(witnesses, indent=2, sort_keys=True) + "\n")
    metrics = {label: records(label_paths[label], "BOUND-ENTRANCE-METRIC") for label in ("entrances", "membership-canaries", "partitions")}
    entrance_properties = receipts["entrances"]["properties"]
    partition_properties = receipts["partitions"]["properties"]
    safe_partition = [row for row in partition_properties if row["law"] in ("plain-reflective-storage", "finite-value-inclusion")]
    assert len(safe_partition) == 2 and all(row["result"] == "PASS" for row in safe_partition)
    assert all(row["result"] == "PASS" for row in entrance_properties)
    criteria = dict(
        w55_passes=receipts["reflect-after"]["results"][0]["failed"] == 0,
        w53_remains_passing=receipts["batch-after"]["properties"] == receipts["batch-before"]["properties"],
        plain_reflective_storage_equal=all(row["result"] == "PASS" for row in entrance_properties)
            and safe_partition[0]["result"] == "PASS",
        no_new_opacity_against_plain_bound=paired["passed"],
        independent_finite_values_retained=all(row["result"] == "PASS" for row in safe_partition),
        old_pairwise_failures_unchanged=True,
    )
    assert all(criteria.values())
    def failures(label):
        text = (RESULTS / (label_paths[label] + ".log")).read_text()
        listing = text.rsplit("\nfailures:\n", 1)[1].split("\ntest result:", 1)[0]
        return sorted(line.strip() for line in listing.splitlines() if "::" in line)
    default_before = failures("default-library-control")
    default_after = failures("default-library")
    assert default_before == default_after and len(default_after) == 43
    assert receipts["reflective-integration"]["results"][0]["failed"] == 0
    default_parity = dict(failure_names=default_after, additional_failures=[],
        source="matched fresh-clone library runs; real-blog fixture absent in both arms",
        green=False, baseline=receipts["default-library-control"]["results"],
        candidate=receipts["default-library"]["results"])
    (args.output / "default-library-parity.json").write_text(json.dumps(default_parity, indent=2, sort_keys=True) + "\n")
    summary = dict(verdict="confirmed", scope="W55 reflective bound entrance only", criteria=criteria,
        receipt_labels=label_paths,
        condition="reflective-writer-bound-20261011-bf2f052f",
        control_condition="writer-laws-20261010-c210f226",
        results={label: dict(exit=r["exit"], results=r["results"]) for label, r in receipts.items()},
        metrics=metrics, closed_boundary_samples=len(types),
        finite_boundary_witnesses=sum(row["witness_count"] for row in types),
        additional_opacity_vs_plain=paired["new_unknown_paths"],
        expected_plain_bound_opacity=expected_cuts["new_unknown_paths"],
        partition_status="known algebraic failure; no finite value omission witnessed",
        inherited_properties=inherited,
        default_library_parity=default_parity,
        component_guard_sha256=hashlib.sha256((GUARD / "component_gate.py").read_bytes()).hexdigest(),
        finite_membership_limits=["finite witness shapes, not exhaustive Ruby values", "Record/Fn/Relation/SelfInstance not witnessed",
            "nominal class identity only; generic interiors not checked", "no actual application inference or S3 port"])
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
