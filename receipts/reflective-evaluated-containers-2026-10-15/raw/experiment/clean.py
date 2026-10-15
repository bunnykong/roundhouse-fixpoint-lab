#!/usr/bin/env python3
"""Clean every task-local Cargo target while the caller holds the shared lock."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
C = ROOT / "week/bound-next/sources/probe-source"
rows = []
with (ROOT / "evidence/cargo-clean.log").open("w") as log:
    for target in [C / "target-laws", ROOT / "week/bound-next/scratch/provenance-target"]:
        target.resolve().relative_to(ROOT)
        command = ["cargo", "+1.98.1", "clean", "--target-dir", str(target)]
        before = sum(p.is_file() for p in target.rglob("*")) if target.exists() else 0
        run = subprocess.run(command, cwd=C, stdout=log, stderr=log)
        after = sum(p.is_file() for p in target.rglob("*")) if target.exists() else 0
        rows.append(dict(target=str(target), command=command, exit=run.returncode,
                         files_before=before, files_after=after))
        assert run.returncode == 0 and after == 0
(ROOT / "evidence/cargo-clean.json").write_text(json.dumps(rows, indent=2) + "\n")
print(json.dumps(rows, indent=2))
if (ROOT / "evidence/verification-v1/summary.json").exists() and (ROOT / "evidence/verification-v1/broad-summary.json").exists():
    subprocess.run(["python3", "-B", str(ROOT / "package_receipts.py")], cwd=ROOT, check=True)
