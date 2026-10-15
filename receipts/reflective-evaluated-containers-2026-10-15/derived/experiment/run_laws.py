#!/usr/bin/env python3
"""Nonempty next selections with complete raw exits and source receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
C = ROOT / "week/bound-next/sources/probe-source"
OUT = ROOT / "week/bound-next/results"
S3 = dict(RH_FOLD="1", RH_FOLD_SLOTS="1", RH_FOLD_JOIN="1", RH_FOLD_TAIL="1",
          RH_BRK_ALLARMS="1", RH_SCHED="sccq")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(C), *args], text=True).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("label")
    p.add_argument("selection")
    p.add_argument("--flag", choices=("0", "1"), default="1")
    p.add_argument("--expected-exit", type=int, default=0)
    p.add_argument("--default", action="store_true")
    p.add_argument("--integration")
    p.add_argument("--base", action="store_true", help="Inference flags off; repair flag still explicit.")
    a = p.parse_args()
    log = OUT / (a.label + ".log")
    receipt_path = OUT / (a.label + ".json")
    if log.exists() or receipt_path.exists():
        raise SystemExit("Use a fresh label")
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_", "PROVENANCE_", "PROBE_BASE"))}
    env.update(RBENV_VERSION="3.4.4", CARGO_TARGET_DIR=str(C / "target-laws"),
               RH_REFLECT_BOUND=a.flag)
    if not a.base:
        env.update(S3)
    cmd = ["cargo", "+1.98.1", "test", "--locked"]
    cmd += ["--test", a.integration] if a.integration else ["--lib"]
    if not a.default:
        cmd.append(a.selection)
    cmd += ["--", "--nocapture", "--test-threads=1"]
    if not a.default:
        cmd.append("--include-ignored")
    with log.open("w") as f:
        run = subprocess.run(cmd, cwd=C, env=env, stdout=f, stderr=subprocess.STDOUT)
    raw = log.read_text()
    counts = re.findall(r"test result: .*? (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out", raw)
    properties = []
    for line in raw.splitlines():
        m = re.search(r"WRITER-LAW (.*?) \| (.*?) \| (PASS|FAIL) \| (\d+) checks(?: \| (\d+) nodes \| (.*))?", line)
        if m:
            writer, law, result, checks, nodes, witness = m.groups()
            properties.append(dict(writer=writer, law=law, result=result, checks=int(checks),
                                   witness_nodes=int(nodes) if nodes else None, witness=witness))
    binary_paths = re.findall(r"Running (?:unittests .*?|tests/\S+) \((.*?)\)", raw)
    binaries = {p: sha(C / p) for p in binary_paths if (C / p).is_file()}
    data = dict(label=a.label, condition="reflective-evaluated-containers-20261015-fe6b169e",
                command=cmd, cwd=str(C), exit=run.returncode, expected_exit=a.expected_exit,
                source_head=git("rev-parse", "HEAD"), source_diff_sha256=hashlib.sha256(
                    subprocess.check_output(["git", "-C", str(C), "diff", "HEAD"])).hexdigest(),
                source_files_sha256={str(f.relative_to(C)): sha(f) for f in sorted((C / "src").rglob("*.rs"))},
                fixture_sha256={str(f.relative_to(C)): sha(f) for f in sorted((C / "src/analyze/fixpoint_bound/fixtures").rglob("*.rb"))},
                flags={k: v for k, v in sorted(env.items()) if k.startswith(("RH_", "CARGO_", "RBENV_", "RUST_"))},
                log_sha256=sha(log), binary_sha256=binaries, properties=properties,
                results=[dict(zip(("passed", "failed", "ignored", "measured", "filtered"), map(int, row))) for row in counts],
                timed_measurement=False,
                timing_scope="Shared-host durations are diagnostics, not performance measurements.")
    receipt_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: data[k] for k in ("label", "exit", "results")}), flush=True)
    if run.returncode != a.expected_exit or not counts or not any(int(r[0]) + int(r[1]) for r in counts):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
