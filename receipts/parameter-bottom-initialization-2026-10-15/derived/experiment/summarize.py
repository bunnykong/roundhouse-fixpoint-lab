#!/usr/bin/env python3
"""Reduce this cycle's raw receipts; invoke under the shared workshop flock."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

D = Path(__file__).resolve().parent
R = D / "week/evidence/results"
C = D / "week/evidence/sources/probe-source"
BASE = "134457dcac997512896e4239835130ae1425d1e4"
CONDITION = "parameter-bottom-initialization-20261015-134457dc"
label = sys.argv[1]
dest = R / (label + "-analysis")
dest.mkdir(exist_ok=False)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def git(*args):
    return subprocess.check_output(["git", "-C", str(C), *args], text=True).strip()


def command(args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


reducers = {}
for kind in ("app", "f19", "f29"):
    with (dest / (kind + ".log")).open("w") as log:
        run = subprocess.run([sys.executable, "-B", str(D / "staging" / ("analyze_" + kind + ".py")), label],
                             stdout=log, stderr=log)
    reducers[kind] = run.returncode
    (dest / (kind + ".exit")).write_text(str(run.returncode) + "\n")

summary = {
    "condition": CONDITION,
    "label": label,
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "timing_claim": False,
    "card_sha256": digest(D / "protocol.md"),
    "advance_prediction": read(D / "protocol.timestamp.json"),
    "reducers": reducers,
    "base": BASE,
    "source_head": git("rev-parse", "HEAD"),
    "source_branch": git("branch", "--show-current"),
    "source_status": git("status", "--porcelain"),
    "changed_paths": git("diff", "--name-only", BASE).splitlines(),
    "toolchains": {
        "rustc": command(["rustc", "+1.98.1", "--version"]),
        "cargo": command(["cargo", "+1.98.1", "--version"]),
        "ruby_tests": command(["ruby", "--version"], env=dict(os.environ, RBENV_VERSION="3.4.4")),
        "ruby_apps": command(["ruby", "--version"], env=dict(os.environ, RBENV_VERSION="4.0.7")),
    },
    "cargo_lock_sha256": digest(C / "Cargo.lock"),
    "source_files_sha256": {str(p.relative_to(C)): digest(p) for p in sorted((C / "src").rglob("*.rs"))},
    "helper_files_sha256": {str(p.relative_to(D)): digest(p) for p in sorted(D.glob("*.sh"))},
}
original_tests = subprocess.check_output(["git", "-C", str(C), "show",
                                         BASE + ":src/analyze/parameter_conservation/tests.rs"])
summary["p1_test_file_preserved_as_prefix"] = (C / "src/analyze/parameter_conservation/tests.rs").read_bytes().startswith(original_tests)
summary["card_unchanged"] = summary["card_sha256"] == summary["advance_prediction"]["sha256"]
summary["patch_sha256"] = hashlib.sha256(subprocess.check_output(
    ["git", "-C", str(C), "diff", BASE, "--binary"])).hexdigest()
(dest / "source.patch").write_bytes(subprocess.check_output(["git", "-C", str(C), "diff", BASE, "--binary"]))

summary["raw_exits"] = {str(p.relative_to(R)): int(p.read_text()) for p in sorted(R.rglob("*.exit"))}
test_results = {}
for directory in ("baseline-v1", "candidate-v1", label + "-local", label + "-suite"):
    for p in sorted((R / directory).glob("*.log")):
        text = p.read_text()
        results = re.findall(r"test result: (\w+)\. (\d+) passed; (\d+) failed; (\d+) ignored;", text)
        if results:
            test_results[str(p.relative_to(R))] = [dict(status=s, passed=int(a), failed=int(b), ignored=int(c))
                                                   for s, a, b, c in results]
summary["test_results"] = test_results


def marked(path, marker):
    rows = [json.loads(line.split(marker, 1)[1]) for line in path.read_text().splitlines() if marker in line]
    assert len(rows) == 1, (path, marker, len(rows))
    return rows[0]


summary["seed_before"] = marked(R / "baseline-v1/seed-arrival.log", "PARAMETER-SEED-ARRIVAL ")
summary["seed_after"] = marked(R / "candidate-v1/seed-arrival.log", "PARAMETER-SEED-ARRIVAL ")
summary["row_laws"] = {name: marked(R / "candidate-v1" / (name + ".log"), "PARAMETER-ROW-LAWS ")
                       for name in ("row-laws", "row-laws-without-audit")}
summary["row_storage_equal_across_audit"] = summary["row_laws"]["row-laws"] == summary["row_laws"]["row-laws-without-audit"]
summary["row_allocation"] = marked(R / "candidate-v1/row-laws.log", "PARAMETER-ROW-ALLOCATION ")

required = {}
for name, population in (("contracts", 4), ("parameters", 7), ("repair-without-audit", 1),
                         ("storage-without-audit", 1), ("returns", 5)):
    path = R / (label + "-local") / (name + ".exit")
    required["local-" + name] = int(path.read_text()) == 0
    result = test_results[str((path.with_suffix(".log")).relative_to(R))]
    required["nonempty-" + name] = all(row["passed"] == population and row["failed"] == 0 for row in result)
for name in ("seed-arrival", "row-laws", "row-laws-without-audit"):
    required["focused-" + name] = int((R / "candidate-v1" / (name + ".exit")).read_text()) == 0
required["original-tests-unchanged"] = summary["p1_test_file_preserved_as_prefix"]
required["advance_prediction-unchanged"] = summary["card_unchanged"]
required["audit-independent-storage"] = summary["row_storage_equal_across_audit"]
required["baseline-reproduced"] = (int((R / "baseline-v1/seed-arrival.exit").read_text()) == 101
                                   and not summary["seed_before"]["native_storage_equal"])
required["seed-fixed"] = (summary["seed_after"]["native_storage_equal"]
                           and summary["seed_after"]["integer_membership_both"]
                           and summary["seed_after"]["bottom_first_origins"] == ["$:Pending"]
                           and summary["seed_after"]["int_first_origins"] == ["$:Pending"])
for name, failures_expected in (("repair-off-negative", 1), ("return-controls", 2)):
    required["retained-red-" + name] = int((R / (label + "-local") / (name + ".exit")).read_text()) == 101
    result = test_results[label + "-local/" + name + ".log"][-1]
    required["nonempty-red-" + name] = result["passed"] == 0 and result["failed"] == failures_expected

default_log = R / (label + "-suite/default.log")
default_text = default_log.read_text()
failures = re.findall(r"^    ([a-zA-Z_][a-zA-Z0-9_:]+)$", default_text, flags=re.M)
expected_failures = {"emit::rust::library::value_union_emit_tests::action_controller_runtime_emit_typechecks_hotspots",
                     "runtime_src::tests::rbs_ivar_decls_stamp_empty_array_initializers"}
summary["default_failures"] = failures
required["default-inherited-failures-only"] = set(failures) == expected_failures
default_result = test_results[str(default_log.relative_to(R))][-1]
required["default-test-population-retained"] = (default_result["passed"] == 1142
                                               and default_result["failed"] == 2
                                               and default_result["ignored"] == 16)
for name in ("action_controller_runtime_emit_typechecks_hotspots", "rbs_ivar_decls_stamp_empty_array_initializers"):
    required["m3-control-" + name] = int((R / (label + "-suite") / ("control-" + name + ".exit")).read_text()) == 101
    result = test_results[label + "-suite/control-" + name + ".log"][-1]
    required["nonempty-m3-control-" + name] = result["passed"] == 0 and result["failed"] == 1

for kind, code in reducers.items():
    required["reducer-" + kind] = code == 0
if not any(reducers.values()):
    app, f19, f29 = (read(R / name) for name in ("campfire-analysis.json", "f19-analysis.json", "f29-analysis.json"))
    summary["f19"] = f19
    summary["f29"] = f29
    f29_root = R / (label + "-f29")
    summary["f29_export_pairs"] = {}
    for left, right in (("s3", "audit"), ("audit", "candidate")):
        before, after = (read(f29_root / arm / "raw.json") for arm in (left, right))
        summary["f29_export_pairs"][left + "--" + right] = {
            "final_bytes_equal": (f29_root / left / "final.rbs").read_bytes() == (f29_root / right / "final.rbs").read_bytes(),
            "graph_bytes_equal": (f29_root / left / "graph.rbs").read_bytes() == (f29_root / right / "graph.rbs").read_bytes(),
            "changed_raw_aliases": [alias for alias in sorted(set(before) | set(after)) if before.get(alias) != after.get(alias)],
        }
    summary["campfire"] = {
        "pairs": {key: [dict(name=row["name"], ordinary_report_equal=row["ordinary_report_equal"],
                             diagnostics_equal=row["diagnostics_equal"], differences=len(row["ordinary_differences"]))
                        for row in rows] for key, rows in app["pairs"].items()},
        "audits": {arm: [dict(name=row["name"], counters=row["counters"], writers=row["writers"],
                              complete_writer_inventory=row["complete_writer_inventory"])
                          for row in rows] for arm, rows in app["audits"].items()},
        "precision_reports": app["precision_reports"],
        "schedule_reports": app["schedule_reports"],
    }
    required["audit-report-diagnostic-parity"] = all(row["ordinary_report_equal"] and row["diagnostics_equal"]
                                                    for row in app["pairs"]["s3--audit"])
    required["campfire-native-nonzero-lossless"] = all(
        row["counters"]["parameter_repair_merges"] > 0
        and row["counters"]["parameter_type_origin_losses"] == 0
        and row["counters"]["parameter_output_origin_losses"] == 0
        for row in app["audits"]["candidate"])
    required["f19-no-new-rejection-or-opacity"] = all(
        not row["new_opaque_aliases"] and not row["new_missing"] and row["membership_violations_equal"]
        for pair in f19["pairs"].values() for row in pair.values())
    required["f29-no-new-rejection-or-opacity"] = (f29["component_gate_passed"] and not f29["newly_rejected"]
        and not f29["acceptance_with_new_opacity"] and all(row["candidate_components"]["passed"]
        and row["audit_components"]["passed"] for row in f29["settings"]))
    native = f29["native_audits"]["candidate"]
    required["f29-native-nonzero-lossless"] = (native["parameter_repair_merges"] > 0
        and native["parameter_type_origin_losses"] == 0 and native["parameter_output_origin_losses"] == 0)
    summary["broader_gates"] = {
        "f19_strict_selected_gate": f19["arms"]["candidate"]["strict_selected_gate"],
        "f29_required_membership_exits": [row["candidate_exit"] for row in f29["settings"]],
        "default_suite_exit": int((R / (label + "-suite/default.exit")).read_text()),
        "whole_program_confirmation": False,
    }
summary["initialization_criteria"] = required
summary["narrow_initialization_passed"] = all(required.values())
(dest / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps({"condition": CONDITION, "narrow_initialization_passed": all(required.values()),
                  "criteria": required, "broader_gates": summary.get("broader_gates")}, indent=2))
sys.exit(0 if all(required.values()) else 1)
