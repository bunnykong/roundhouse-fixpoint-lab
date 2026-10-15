#!/usr/bin/env python3
"""Freeze delivery identities and receipt hashes after committing and cleaning."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

D = Path(__file__).resolve().parent
R = D / "week/evidence/results"
C = D / "week/evidence/sources/probe-source"
label = sys.argv[1]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(path, *args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(path), *args], text=True).strip()


def read(path):
    return json.loads(path.read_text())


manifest = {}
for path in (R / (label + "-f19/condition.json"), R / (label + "-campfire/condition.json"),
             *(R / (label + "-f29") / arm / "receipt.json" for arm in ("s3", "audit", "candidate"))):
    receipt = read(path)
    mismatches = [name for name, expected in receipt["source_files_sha256"].items() if sha(C / name) != expected]
    helper = (D / "week/evidence/experiments/f19_check.py" if path.parent.name.endswith("-f19") else
              D / "week/evidence/experiments/app_check.py" if path.parent.name.endswith("-campfire") else
              D / "week/sound/candidate_export.py")
    if "exporter_sha256" in receipt:
        exporter = C / "examples" / ("producer_reason_sound_types.rs" if path.parent.name.endswith("-f19")
                                     else "parameter_reason_sound_types.rs")
        if sha(exporter) != receipt["exporter_sha256"]:
            mismatches.append(str(exporter.relative_to(C)))
    manifest[str(path.relative_to(D))] = dict(source_files=len(receipt["source_files_sha256"]), mismatches=mismatches,
                                            cargo_lock_equal=sha(C / "Cargo.lock") == receipt["cargo_lock_sha256"],
                                            helper_equal=sha(helper) == receipt["helper_sha256"])

targets = (C / "target-laws", D / "week/evidence/scratch/provenance-target",
           D / "week/evidence/sources/suite-control/target-laws")
index = {str(p.relative_to(D)): dict(bytes=p.stat().st_size, sha256=sha(p))
         for p in sorted(R.rglob("*")) if p.is_file() and p.name != "receipt-index.json"}
(R / "receipt-index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
source_metadata = git(C, "log", "-1", "--format=%H%n%an%n%ae%n%cn%n%ce%n%B").splitlines()
expected_email = "268838774+bunnykong@users.noreply.github.com"
checks = {
    "measured_source_matches_delivery": all(not row["mismatches"] and row["cargo_lock_equal"] and row["helper_equal"]
                                            for row in manifest.values()),
    "source_clean": not bool(git(C, "status", "--porcelain")),
    "branch_correct": git(C, "branch", "--show-current") == "parameter-bottom-initialization",
    "author_committer_correct": source_metadata[2] == expected_email and source_metadata[4] == expected_email,
    "coauthor_trailer_correct": source_metadata[-1] == "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
    "card_unchanged": sha(D / "protocol.md") == read(D / "protocol.timestamp.json")["sha256"],
    "all_targets_cleaned": all(not target.exists() for target in targets),
    "clean_exits_zero": all(int((R / "cleanup-v1" / (name + ".exit")).read_text()) == 0 for name in ("laws", "native", "control")),
}
result = {
    "condition": "parameter-bottom-initialization-20261015-134457dc",
    "source_commit": source_metadata[0],
    "source_branch": git(C, "branch", "--show-current"),
    "commit_metadata": source_metadata,
    "measured_source_comparisons": manifest,
    "checks": checks,
    "lab_pin": git(D / "week/lab", "rev-parse", "HEAD"),
    "app_pins": {app: git(D / "week/lab/corpus/apps" / app, "rev-parse", "HEAD") for app in ("campfire", "discourse")},
    "p1_source_pin": git(D.parent / "native-parameter-reason-seeds/week/evidence/sources/probe-source", "rev-parse", "HEAD"),
    "p1_source_status": git(D.parent / "native-parameter-reason-seeds/week/evidence/sources/probe-source", "status", "--porcelain"),
    "receipt_count": len(index),
    "receipt_index_sha256": sha(R / "receipt-index.json"),
    "summary_sha256": sha(R / (label + "-analysis/summary.json")),
    "runner_files_sha256": {str(p.relative_to(D)): sha(p) for p in sorted({
        *D.glob("*.sh"), *D.glob("*.py"), *D.glob("staging/*.py"),
        *D.glob("week/evidence/experiments/*.py"), *D.glob("week/sound/**/*.py")})},
    "missing_supplied_research workspace_paths": [str(D.parents[1] / name) for name in (
        "docs/pitfalls.md", "tools/cohort_index.py", "tools/test_scrub.py",
        "tools/test_clojure_artifacts.py", "tools/test_clojure_lane.py", "tools/brief_check.py")
        if not (D.parents[1] / name).exists()],
    "target_paths": {str(target.relative_to(D)): target.exists() for target in targets},
}
(D / "delivery.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"checks": checks, "source_commit": source_metadata[0], "receipts": len(index)}, indent=2))
sys.exit(0 if all(checks.values()) else 1)
