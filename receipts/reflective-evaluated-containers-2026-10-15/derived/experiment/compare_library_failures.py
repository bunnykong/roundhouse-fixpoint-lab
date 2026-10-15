#!/usr/bin/env python3
"""Reproduce the flag-on library failures on an independent, unchanged P6 copy."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
C = ROOT / "week/bound-next/sources/probe-source"
BASE = ROOT / "week/bound-next/sources/p6-control"
OUT = ROOT / "week/bound-next/results/p6-library-controls"
PIN = "fe6b169ea935be900aa51e5a2069a360324a69b0"
SELECTIONS = ["stats_are_per_analyze", "action_controller_runtime_emit_typechecks_hotspots",
              "rbs_ivar_decls_stamp_empty_array_initializers"]


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    subprocess.run(["git", "clone", "--no-hardlinks", str(C), str(BASE)], check=True)
    head = subprocess.check_output(["git", "-C", str(BASE), "rev-parse", "HEAD"], text=True).strip()
    assert head == PIN
    spec = importlib.util.spec_from_file_location("baseline_rerun", ROOT / "week/lab/receipts/baseline-2026-10-10/rerun.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.fixtures(BASE)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_", "PROVENANCE_", "PROBE_BASE"))}
    env.update(RBENV_VERSION="3.4.4", CARGO_TARGET_DIR=str(C / "target-laws"), CARGO_BUILD_JOBS="4",
        RH_REFLECT_BOUND="1", RH_FOLD="1", RH_FOLD_SLOTS="1", RH_FOLD_JOIN="1", RH_FOLD_TAIL="1",
        RH_BRK_ALLARMS="1", RH_SCHED="sccq")
    rows = []
    for selection in SELECTIONS:
        command = ["cargo", "+1.98.1", "test", "--locked", "--lib", selection,
                   "--", "--nocapture", "--test-threads=1"]
        log_path = OUT / (selection + ".log")
        with log_path.open("w") as log:
            run = subprocess.run(command, cwd=BASE, env=env, stdout=log, stderr=log)
        raw = log_path.read_text()
        counts = re.findall(r"test result: .*? (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out", raw)
        assert run.returncode in (0, 101) and counts and sum(int(v) for v in counts[-1][:2]) > 0
        rows.append(dict(selection=selection, command=command, exit=run.returncode, counts=counts,
            log_sha256=hashlib.sha256(log_path.read_bytes()).hexdigest()))
        print(json.dumps(rows[-1]), flush=True)
    receipt = dict(condition="reflective-evaluated-containers-20261015-fe6b169e/p6-library-controls", source_head=head,
        source_status=subprocess.check_output(["git", "-C", str(BASE), "status", "--porcelain"], text=True),
        flags={k: v for k, v in env.items() if k.startswith(("RH_", "CARGO_", "RBENV_"))}, rows=rows,
        timed_measurement=False, scope="Focused unchanged-P6 controls for the three candidate flag-on library failures")
    (OUT / "summary.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
