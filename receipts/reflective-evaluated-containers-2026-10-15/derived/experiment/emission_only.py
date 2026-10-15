#!/usr/bin/env python3
"""Complete byte parity while leaving the unfinished prepared-suite bar red."""
import hashlib
import datetime
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
BOUND = ROOT / "week/bound-next"
C = BOUND / "sources/probe-source"
BASE = BOUND / "sources/control"
LAB = ROOT / "week/lab"
OUT = BOUND / "results/parity-v1"
OLD = BOUND / "results/parity-unprepared-v1/candidate"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    receipt = json.loads((OLD / "emission-receipt.json").read_text())
    candidate = json.loads((OLD / "manifest.json").read_text())
    pairs = [json.loads(s) for s in (OLD / "pairs.jsonl").read_text().splitlines()]
    assert len(pairs) == receipt["pairs"] == 105 and not any("error" in r for r in pairs)
    assert all(sha(OLD / "tree" / name) == digest for name, digest in candidate.items())
    assert sha(C / "examples/emit_all_compare.rs") == receipt["native_exporter_sha256"]
    assert sha(C / "Cargo.lock") == receipt["cargo_lock_sha256"]
    deadline = datetime.datetime(2026, 10, 15, 7, 5, tzinfo=datetime.timezone.utc)
    if datetime.datetime.now(datetime.timezone.utc) >= deadline:
        summary = dict(condition="reflective-evaluated-containers-20261015-fe6b169e/emission-budget-stop",
            emission_pairs=105, emission_files=len(candidate), emission_equal=False,
            emission_comparison_complete=False, candidate_source=str(OLD), candidate_receipt=receipt,
            shared_test_outcomes=0, changed_shared_outcomes={}, added_outcomes={},
            missing_candidate_tests=[], candidate_added_failures=[], suite_comparison_complete=False,
            suite_status="Host lock exhausted the native-work budget; no matched prepared-suite result.",
            stop_reason="Reserve the final 20 minutes for verification, local commits and cargo clean.",
            timed_measurement=False)
        (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    spec = importlib.util.spec_from_file_location("baseline_rerun", LAB / "receipts/baseline-2026-10-10/rerun.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.fixtures(BASE)
    example = BASE / "examples/emit_all_compare.rs"
    shutil.copyfile(LAB / "receipts/baseline-2026-10-10/emit_all.rs", example)
    assert sha(example) == receipt["native_exporter_sha256"]
    arm = OUT / "control"
    arm.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_", "PROVENANCE_", "PROBE_BASE"))}
    env.update(RBENV_VERSION="3.4.4", RH_REFLECT_BOUND="0", CARGO_BUILD_JOBS="4",
               CARGO_TARGET_DIR=str(BOUND / "scratch/provenance-target"))
    command = ["cargo", "+1.98.1", "build", "--release", "--locked", "--example", "emit_all_compare"]
    with (arm / "emission-build.log").open("w") as log:
        subprocess.run(command, cwd=BASE, env=env, stdout=log, stderr=log, check=True)
    binary = BOUND / "scratch/provenance-target/release/examples/emit_all_compare"
    with (arm / "pairs.jsonl").open("w") as stdout, (arm / "emission.stderr").open("w") as stderr:
        subprocess.run([str(binary), str(arm / "tree")], cwd=BASE, env=env, stdout=stdout, stderr=stderr, check=True)
    control_pairs = [json.loads(s) for s in (arm / "pairs.jsonl").read_text().splitlines()]
    assert len(control_pairs) == 105 and not any("error" in r for r in control_pairs)
    control = {str(p.relative_to(arm / "tree")): sha(p) for p in sorted((arm / "tree").rglob("*")) if p.is_file()}
    (arm / "manifest.json").write_text(json.dumps(control, indent=2, sort_keys=True) + "\n")
    summary = dict(condition="reflective-evaluated-containers-20261015-fe6b169e/emission-only",
        emission_pairs=105, emission_files=len(candidate), emission_equal=candidate == control,
        candidate_source=str(OLD), candidate_receipt=receipt, control_binary_sha256=sha(binary),
        control_head=subprocess.check_output(["git", "-C", str(BASE), "rev-parse", "HEAD"], text=True).strip(),
        control_exporter_sha256=sha(example), shared_test_outcomes=0, changed_shared_outcomes={},
        added_outcomes={}, missing_candidate_tests=[], candidate_added_failures=[],
        suite_comparison_complete=False,
        suite_status="Initial candidate default suite stopped on missing sqlite3; corrected paired suite was not executed within the budget.",
        timed_measurement=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
