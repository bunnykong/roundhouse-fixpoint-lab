#!/usr/bin/env python3
"""Fresh same-binary exports against F29's frozen P/E/I observations.

Runtime traces are reused as fixed observations; compiler exports are new.
The graph grammar is final-only here, not a graph soundness certificate.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BOUND = ROOT / "week/bound-next"
LAB = ROOT / "week/lab"
C = BOUND / "sources/probe-source"
ADAPTER = BOUND / "adapter"
FROZEN = LAB / "receipts/discourse-trace-2026-10-10"
OUT = BOUND / "results/f29-bound-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_"))}
    target = BOUND / "scratch/provenance-target"
    env.update(CARGO_TARGET_DIR=str(target), RBENV_VERSION="4.0.7")
    command = ["cargo", "+1.98.1", "build", "--locked", "--example", "reflective_sound_types"]
    with (OUT / "build.log").open("w") as log:
        subprocess.run(command, cwd=C, env=env, stdout=log, stderr=log, check=True)
    binary = target / "debug/examples/reflective_sound_types"
    for arm, flag in [("s3", "0"), ("candidate", "1")]:
        dest = OUT / arm
        command = [sys.executable, "-B", str(ADAPTER / "export.py"), "--binary", str(binary),
                   "--role", "s3", "--source", str(C), "--app", str(LAB / "corpus/apps/discourse"),
                   "--selection", str(FROZEN / "selection.json"), "--lab", str(LAB),
                   "--output", str(dest), "--condition", "reflective-evaluated-containers-f29-reflective-bound-20261015-v1",
                   "--candidate-env", "RH_REFLECT_BOUND=" + flag]
        with (OUT / (arm + "-export.log")).open("w") as log:
            subprocess.run(command, env=env, stdout=log, stderr=log, check=True)
    rows = []
    for setting in ("P", "E", "I"):
        for arm in ("s3", "candidate"):
            command = [sys.executable, "-B", str(ADAPTER / "compare.py"), "--lab", str(LAB),
                       "--trace", str(FROZEN / ("traces/" + setting + ".jsonl")),
                       "--export", str(OUT / arm), "--slots", str(FROZEN / "slots.json"),
                       "--output", str(OUT / (arm + "-" + setting + ".json")), "--require-membership"]
            if arm == "candidate":
                command += ["--baseline-export", str(OUT / "s3")]
            with (OUT / (arm + "-" + setting + ".log")).open("w") as log:
                run = subprocess.run(command, env=env, stdout=log, stderr=log)
            if run.returncode not in (0, 1):
                raise RuntimeError("invalid F29 checker evidence")
            data = json.loads((OUT / (arm + "-" + setting + ".json")).read_text())
            rows.append(dict(arm=arm, setting=setting, raw_exit=run.returncode,
                             records=data["records"], selected=data["selected_slots"],
                             observed=data["observed_slots"], no_slot=data["no_slot"],
                             accepted=data["arms"]["final"]["accepted"],
                             rejected=data["arms"]["final"]["rejected"],
                             missing=data["arms"]["final"]["category_slots"]["missing"],
                             new_unknown_paths=data.get("paired_components", {}).get("new_unknown_paths")))
    receipt = dict(condition="reflective-evaluated-containers-f29-reflective-bound-20261015-v1", rows=rows,
                   binary_sha256=sha(binary), selection_sha256=sha(FROZEN / "selection.json"),
                   native_exporter_sha256=sha(C / "examples/reflective_sound_types.rs"),
                   cargo_lock_sha256=sha(C / "Cargo.lock"),
                   traces_sha256={s: sha(FROZEN / ("traces/" + s + ".jsonl")) for s in ("P", "E", "I")},
                   adapter_sha256={p.name: sha(p) for p in ADAPTER.glob("*.py")},
                   fresh_static_exports=True, saved_runtime_observations=True,
                   timed_measurement=False, graph_certificate=False)
    (OUT / "summary.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
