#!/usr/bin/env python3
"""One command for frozen public inputs, supervised checks, and safe aggregates."""
import argparse
from collections import Counter
import datetime
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
from common import ROOT, LAB_ROOT, file_sha, inventory, verify, write_json
import watchdog
from preflight import running_checks

DEFAULTS = {"micro": (4.0, 120.0), "apps": (40.0, 1200.0)}
REFERENCE_MICRO = {"cycle-2-width-2", "cycle-3-width-2", "f2_merge", "param", "ivar", "merge2", "exact", "merge",
                   "argument-tree", "tuple-1", "tuple-2", "tuple-3", "chain-64"}
LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")
def wait_for_other_checks():
    last = 0
    while True:
        state = running_checks()
        if state["processes"] == 0:
            return state
        if time.monotonic() - last >= 30:
            print(json.dumps({"event": "waiting_for_other_checks", **state}), flush=True)
            last = time.monotonic()
        time.sleep(5)


def options():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--env", action="append", nargs="+", default=[], metavar="K=V")
    parser.add_argument("--set", choices=("micro", "apps", "all"), default="all")
    parser.add_argument("--label")
    parser.add_argument("--limit-gib", type=float)
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--condition", default="public-lab-v1")
    parser.add_argument("--reference-micro", action="store_true", help="Use the original 13-case subset.")
    parser.add_argument("--_locked", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def summary(run, rows):
    lines = ["# Corpus run: " + run["label"], "",
             "Condition: **" + run["condition"] + "**. One process per input; host timings are descriptive.",
             "Binary: " + run["binary"]["path"].split("/")[-1] + ". Exact hashes and environment: [run.json](run.json).",
             "Limits: micro 4 GiB / 120 s; apps 40 GiB / 1,200 s unless overridden in run.json.", "",
             "A completed check may report errors. Killed checks have partial diagnostic counts.",
             "RSS uses max(wait4 peak, sampled peak); wall time is the child wrapper's wait4 interval.",
             "Completion is not a convergence certificate. See each input's rh_dyn object.", "",
             "| Input | Outcome | GiB | Seconds |",
             "| --- | --- | ---: | ---: |"]
    for row in rows:
        outcome = row["outcome"] + ("/" + row["reason"] if row["reason"] else "")
        lines.append("| %s | %s | %.3f | %.3f |" %
                     (row["app"], outcome, row["peak_gib"], row["wall_seconds"]))
    lines.extend(["", "| Input | Errors | Warnings | Gradual |", "| --- | ---: | ---: | ---: |"])
    for row in rows:
        counts = row.get("summary_counts")
        complete = row.get("diagnostics_complete") and row["outcome"] == "completed"
        values = ((counts["parse_errors"] + counts["errors"], counts["warnings"], row["gradual_untyped"])
                  if complete else ("—", "—", "—"))
        lines.append("| %s | %s | %s | %s |" % ((row["app"],) + values))
    lines.extend(["", "Per-kind counts, probe rounds, terminal signature changes and kill reasons:",
                  "[results.json](results.json). No checker diagnostic message text is retained.", "",
                  "Forem's pin is its newest available stable tag (2021), a historical condition.",
                  "Results must be compared with the same input tree, binary base, flags and limits.", ""])
    (ROOT / "results" / run["label"] / "SUMMARY.md").write_text("\n".join(lines))


def execute(args, binary, overrides, groups):
    label = args.label or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + binary.name[:40]
    if not LABEL.fullmatch(label):
        print(json.dumps({"error": "invalid_label"}))
        return 2
    destination = ROOT / "results" / label
    if destination.exists():
        print(json.dumps({"error": "label_already_exists", "label": label}))
        return 2
    manifest_path = ROOT / "MANIFEST.json"
    if not manifest_path.exists():
        print(json.dumps({"error": "missing_manifest", "prepare": "sh corpus/fetch.sh"}))
        return 2
    manifest = json.loads(manifest_path.read_text())
    changed = verify(manifest, groups)
    if changed:
        print(json.dumps({"error": "changed_inputs", "inputs": changed}))
        return 2
    # Keep app runs first-class but place the quick regression suite first.
    inputs = sorted((item for item in manifest["inputs"] if item["set"] in groups
                     and (not args.reference_micro or item["set"] == "apps" or item["id"] in REFERENCE_MICRO)),
                    key=lambda item: (item["set"] != "micro", item["id"]))
    destination.mkdir(parents=True)
    run = {"schema_version": 1, "condition": args.condition, "label": label,
           "status": "running", "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "binary": {"path": binary.name, "sha256": file_sha(binary)},
           "set": args.set, "environment_overrides": overrides,
           "environment_policy": "Strip inherited RH_*, ROUNDHOUSE_*, BUNDLE_*, Ruby/Gem overrides; see watchdog.py.",
           "fixed_environment": {"ROUNDHOUSE_TIMINGS": "1", "NO_COLOR": "1", "RUST_BACKTRACE": "0",
                                 "LC_ALL": "C", "TZ": "UTC", "PYTHONDONTWRITEBYTECODE": "1",
                                 "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"},
           "host": {"platform": platform.platform(), "machine": platform.machine(),
                    "python": platform.python_version(), "logical_cpus": os.cpu_count()},
           "limits": {group: {"gib": args.limit_gib if args.limit_gib is not None else DEFAULTS[group][0],
                             "seconds": args.seconds if args.seconds is not None else DEFAULTS[group][1]}
                      for group in sorted(groups)},
           "resource_lock": "corpus/run.lock",
           "manifest_sha256": file_sha(manifest_path),
           "runner_sha256": {name: file_sha(ROOT / name) for name in
                             ("run.py", "watchdog.py", "child_exec.py", "metrics.py", "common.py", "preflight.py")},
           "input_ids": [item["id"] for item in inputs]}
    (destination / "harness").mkdir()
    for name in run["runner_sha256"]:
        shutil.copy2(ROOT / name, destination / "harness" / name)
    run["host"]["load_average_at_start"] = list(os.getloadavg())
    write_json(destination / "run.json", run)
    rows = []
    harness_failed = False
    for item in inputs:
        group, name = item["set"], item["id"]
        overlap = wait_for_other_checks() if args._locked else None
        caps = run["limits"][group]
        output = destination / "cases" / name
        try:
            result = watchdog.run_check(output, binary, LAB_ROOT / item["path"],
                                        caps["gib"], caps["seconds"], overrides)
        except Exception as exc:
            # No exception message: it may contain content supplied by a checker.
            result = {"outcome": "failed", "reason": "harness_error", "exception_kind": type(exc).__name__,
                      "peak_gib": 0.0, "wall_seconds": 0.0, "summary_counts": None,
                      "diagnostics_complete": False}
            harness_failed = True
        result.update(app=name, set=group, input_tree_sha256=item["tree_sha256"],
                      input_commit=item.get("commit"), condition=args.condition,
                      binary_sha256=run["binary"]["sha256"], environment_overrides=overrides,
                      overlap_preflight=overlap)
        if inventory(LAB_ROOT / item["path"])[0] != item["tree_sha256"]:
            result["input_changed_during_run"] = True
            harness_failed = True
        if file_sha(binary) != run["binary"]["sha256"]:
            result["binary_changed_during_run"] = True
            harness_failed = True
        if result["outcome"] == "failed" or (result["outcome"] == "completed" and not result.get("diagnostics_complete")):
            harness_failed = True
        write_json(output / "result.json", result)
        rows.append(result)
        write_json(destination / "results.json", rows)
        summary(run, rows)
        print(json.dumps({"event": "check_result", "app": name, "outcome": result["outcome"],
                          "reason": result["reason"], "peak_gib": round(result["peak_gib"], 3),
                          "wall_seconds": round(result["wall_seconds"], 3),
                          "errors_by_kind": result.get("errors_by_kind", {}),
                          "warnings_by_kind": result.get("warnings_by_kind", {}),
                          "gradual_untyped": result.get("gradual_untyped"),
                          "diagnostics_complete": result.get("diagnostics_complete", False)}), flush=True)
        if result["reason"] == "interrupted":
            harness_failed = True
            break
    run.update(status="finished" if len(rows) == len(inputs) else "interrupted",
               finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               outcome_counts=dict(Counter(row["outcome"] for row in rows)),
               harness_valid=not harness_failed)
    write_json(destination / "run.json", run)
    summary(run, rows)
    print(json.dumps({"event": "run_finished", "label": label, "inputs": len(rows),
                      "outcomes": run["outcome_counts"], "harness_valid": run["harness_valid"]}), flush=True)
    # Resource-limit kills are valid experimental outcomes, not harness failures.
    return 2 if harness_failed else 0


def main():
    args = options()
    for number in (args.limit_gib, args.seconds):
        if number is not None and (not math.isfinite(number) or number <= 0):
            print(json.dumps({"error": "invalid_limit"}))
            return 2
    binary = Path(args.binary).expanduser().resolve()
    if not binary.is_file() or not os.access(binary, os.X_OK):
        print(json.dumps({"error": "binary_not_executable"}))
        return 2
    overrides = {}
    for assignment in (assignment for group in args.env for assignment in group):
        key, separator, value = assignment.partition("=")
        if not separator or not ENV_KEY.fullmatch(key):
            print(json.dumps({"error": "invalid_environment_assignment"}))
            return 2
        overrides[key] = value
    groups = {"micro", "apps"} if args.set == "all" else {args.set}
    from lock import locked
    with locked():
        wait_for_other_checks()
        return execute(args, binary, overrides, groups)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(json.dumps({"error": "interrupted"}), flush=True)
        sys.exit(130)
    except Exception as exc:
        print(json.dumps({"error": "runner_failed", "exception_kind": type(exc).__name__}), flush=True)
        sys.exit(2)
