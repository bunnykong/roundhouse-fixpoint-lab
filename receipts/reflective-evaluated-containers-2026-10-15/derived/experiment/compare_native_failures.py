#!/usr/bin/env python3
"""Focused unchanged-P6 controls for the flag-on integration failures."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from compare_library_failures import ROOT, C, BASE, PIN
from run_laws import S3

OUT = ROOT / "week/bound-next/results/p6-native-controls"


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    head = subprocess.check_output(["git", "-C", str(BASE), "rev-parse", "HEAD"], text=True).strip()
    assert head == PIN
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_", "PROVENANCE_", "PROBE_BASE"))}
    env.update(S3, RBENV_VERSION="3.4.4", CARGO_TARGET_DIR=str(C / "target-laws"),
               CARGO_BUILD_JOBS="4", RH_REFLECT_BOUND="1")
    rows = []
    for suite, selection in [("analyze", "array_to_h_without_a_block_reads_each_element_as_a_pair"),
                             ("runtime_src_integration", "every_runtime_method_body_concretely_typed")]:
        command = ["cargo", "+1.98.1", "test", "--locked", "--test", suite, selection,
                   "--", "--nocapture", "--test-threads=1"]
        path = OUT / (suite + ".log")
        with path.open("w") as log:
            run = subprocess.run(command, cwd=BASE, env=env, stdout=log, stderr=log)
        counts = re.findall(r"test result: .*? (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out", path.read_text())
        assert run.returncode in (0, 101) and counts and sum(int(v) for v in counts[-1][:2]) > 0
        rows.append(dict(suite=suite, selection=selection, command=command, exit=run.returncode,
                         counts=counts, log_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print(json.dumps(rows[-1]), flush=True)
    receipt = dict(condition="reflective-evaluated-containers-20261015-fe6b169e/p6-native-controls", source_head=head,
        flags={k: v for k, v in env.items() if k.startswith(("RH_", "CARGO_", "RBENV_"))}, rows=rows,
        timed_measurement=False, scope="Focused unchanged-P6 controls; no whole-suite pass is claimed")
    (OUT / "summary.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
