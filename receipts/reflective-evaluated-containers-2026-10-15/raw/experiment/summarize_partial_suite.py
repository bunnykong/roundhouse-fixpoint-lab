#!/usr/bin/env python3
"""Preserve the interrupted prerequisite-failing default suite as non-passing evidence."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def main():
    path = ROOT / "week/bound-next/results/parity-unprepared-v1/candidate/suite.log"
    raw = path.read_text()
    executable = "unknown"
    inventory = {}
    targets = []
    for line in raw.splitlines():
        if "Running unittests" in line or "Running tests/" in line:
            executable = line.strip().split(" (")[0].split("Running ", 1)[1]
            targets.append(executable)
        match = re.match(r"test (\S+) \.\.\. (ok|FAILED|ignored.*)", line)
        if match:
            name, outcome = match.groups()
            inventory[executable + "::" + name] = outcome.split(",")[0]
    data = dict(condition="reflective-array-20261015-fe6b169e/unprepared-default-suite",
        completed=False, interrupted=True, outer_exit=1, shared_comparison_performed=False,
        reason="The candidate default suite lacked sqlite3 under Ruby 3.4.4. Preserve failures; do not call this prepared parity.",
        log_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), targets_started=targets,
        observed_counts={kind: sum(s == kind for s in inventory.values()) for kind in ("ok", "FAILED", "ignored")},
        observed_failure_names=sorted(name for name, value in inventory.items() if value == "FAILED"),
        inventory=inventory, timed_measurement=False)
    (ROOT / "evidence/partial-suite.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: data[k] for k in ("completed", "observed_counts", "reason")}))


if __name__ == "__main__":
    main()
