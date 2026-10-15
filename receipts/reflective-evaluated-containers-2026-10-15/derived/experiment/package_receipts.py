#!/usr/bin/env python3
"""Package completed receipts after local source commits and Cargo cleanup."""
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent
C = ROOT / "week/bound-next/sources/probe-source"
E = ROOT / "evidence"
R = ROOT / "week/bound-next/results"
BASE = "fe6b169ea935be900aa51e5a2069a360324a69b0"
NEXT = "38403140379cd69759b0fe6247c6a8c4a48a37a9"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def main():
    subprocess.run(["python3", "-B", str(ROOT / "summarize_partial_suite.py")], check=True)
    prereg = json.loads((E / "advance_prediction-receipt.json").read_text())
    assert sha(ROOT / "protocol.md") == prereg["card_sha256"], "advance_prediction card changed"
    changed_inputs = {path: dict(read_sha256=digest, delivery_sha256=sha(ROOT.parents[1] / path))
                      for path, digest in prereg["input_sha256"].items()
                      if sha(ROOT.parents[1] / path) != digest}
    assert "agents/reflective-array-entrance/RESULT.md" not in changed_inputs, "P6's original report changed"
    for repo in (ROOT, C):
        assert git(repo, "branch", "--show-current") == "reflective-evaluated-containers"
        assert git(repo, "log", "-1", "--format=%ae") == "268838774+bunnykong@users.noreply.github.com"
        assert git(repo, "log", "-1", "--format=%ce") == "268838774+bunnykong@users.noreply.github.com"
        assert git(repo, "log", "-1", "--format=%B").endswith("Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    clean = json.loads((E / "cargo-clean.json").read_text())
    for row in clean:
        assert row["exit"] == 0 and row["files_after"] == 0
        target = Path(row["target"])
        assert not target.exists() or not any(p.is_file() for p in target.rglob("*"))
    patches = {}
    for label, base in [("compiler-from-p6", BASE), ("complete-compiler", NEXT)]:
        patch = subprocess.check_output(["git", "-C", str(C), "diff", base, "HEAD", "--binary"])
        path = E / (label + ".patch.gz")
        with gzip.open(path, "wb") as f:
            f.write(patch)
        patches[label] = sha(path)
    scripts = sorted(ROOT.glob("*.py")) + sorted((ROOT / "week/bound-next/experiments").glob("*.py"))
    runner_paths = scripts + sorted(ROOT.glob("*.sh")) + sorted(ROOT.glob("*.rb"))
    for path in scripts:
        ast.parse(path.read_text(), filename=str(path), feature_version=9)
    local = json.loads((E / "verification-v1/summary.json").read_text())
    broad = json.loads((E / "verification-v1/broad-summary.json").read_text())
    delivery = dict(condition=local["condition"], local_verdict=local["local_verdict"],
        whole_priority_verdict=broad["whole_priority_verdict"],
        source_commit=git(C, "rev-parse", "HEAD"), source_tree=git(C, "rev-parse", "HEAD^{tree}"),
        source_status=git(C, "status", "--porcelain"), base=BASE, next=NEXT,
        advance_prediction_commit=prereg["advance_prediction_commit"], card_sha256=prereg["card_sha256"],
        source_files_sha256={str(p.relative_to(C)): sha(p) for p in sorted((C / "src").rglob("*.rs"))},
        runner_sha256={str(p.relative_to(ROOT)): sha(p) for p in runner_paths},
        read_inputs_changed_at_delivery=changed_inputs,
        patch_sha256=patches, cleanup=clean, performance_measurements=False,
        law_binary_sha256=local["law_binary_sha256"],
        command_scope="All builds, tests, analyses, runtime checks and cleanup used the shared workshop lock.")
    (E / "delivery.json").write_text(json.dumps(delivery, indent=2, sort_keys=True) + "\n")
    (E / "summary.json").write_text(json.dumps(dict(local=local, broad=broad), indent=2, sort_keys=True) + "\n")
    archive_path = E / "receipts.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        for directory in (R, E / "verification-v1", E / "first-iteration-results"):
            if directory.exists():
                for path in sorted(directory.rglob("*")):
                    if path.is_file() and "tree" not in path.relative_to(directory).parts:
                        archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
        for path in sorted(E.iterdir()):
            if path.is_file() and path.name not in ("receipts.tar.gz", "receipts.sha256", "finalize-native.log"):
                archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
        for path in sorted((ROOT / "inherited/p6-results").glob("gate-*.json")):
            archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
        for path in sorted((ROOT / "week/bound-next/experiments").glob("*")):
            if path.is_file():
                archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    digest = sha(archive_path)
    (E / "receipts.sha256").write_text(digest + "  receipts.tar.gz\n")
    print(json.dumps(dict(source_commit=delivery["source_commit"], local_verdict=local["local_verdict"],
        whole_priority_verdict=broad["whole_priority_verdict"], archive_sha256=digest, targets_empty=True)))


if __name__ == "__main__":
    main()
