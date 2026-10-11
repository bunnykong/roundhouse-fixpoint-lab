#!/usr/bin/env python3
"""Run the corpus's four schedule controls; invoke under the workshop shared lock.

Exit 0 means the observed gates passed, 1 means a recorded difference/movement,
and 2 means an invalid or incomplete run. This does not certify declaration
coverage, monotonicity, Ruby soundness, or arbitrary schedule independence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
SCHEDULES = ("unset", "1", "2", "repeat-unset")
PAIRS = (("unset", "1"), ("unset", "2"), ("1", "2"), ("unset", "repeat-unset"))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def input_hash(path):
    names = subprocess.check_output(["git", "-C", str(path), "ls-files", "-z"], text=True).split("\0")
    digest = hashlib.sha256()
    count = 0
    for name in sorted(n for n in names if n):
        file = path / name
        if file.is_file():
            digest.update(name.encode() + b"\0")
            digest.update(hashlib.sha256(file.read_bytes()).digest())
            count += 1
    if not count:
        raise RuntimeError("empty input inventory")
    return digest.hexdigest(), count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("condition", help="New local result-directory name")
    parser.add_argument("app")
    parser.add_argument("--binary", type=Path, default=ROOT / "bin/roundhouse")
    parser.add_argument("--source", type=Path, default=ROOT / "sources/roundhouse")
    parser.add_argument("--apps", type=Path, default=ROOT / "sources/lab/corpus/apps")
    parser.add_argument("--phase", choices=("observe", "verify", "both"), default="both")
    parser.add_argument("--declarations", action="store_true", help="Require the new S3 declaration shadow output")
    args = parser.parse_args()
    for value in (args.condition, args.app):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            parser.error("condition and app must be simple directory names")
    binary, source, apps = (p.resolve() for p in (args.binary, args.source, args.apps))
    if not binary.is_file() or not (apps / args.app).is_dir():
        parser.error("binary or input directory is missing")
    out = ROOT / "runs" / args.condition / args.app
    out.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith("RH_") and k != "PROBE_BASE"}
    env.update(RH_BIN=str(binary), APPS=str(apps), RBENV_VERSION="4.0.7", TMPDIR=str(ROOT / "tmp"))
    (ROOT / "tmp").mkdir(exist_ok=True)
    input_digest, input_files = input_hash(apps / args.app)
    save(out / "condition.json", {
        "condition": args.condition, "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "source_commit": git(source, "rev-parse", "HEAD"),
        "source_status": git(source, "status", "--porcelain"),
        "input_repository_commit": git(apps / args.app, "rev-parse", "HEAD"),
        "input_status": git(apps / args.app, "status", "--porcelain", "--", "."),
        "input_tree_sha256": input_digest, "input_file_count": input_files,
        "ruby": subprocess.check_output(["ruby", "--version"], env=env, text=True).strip(),
        "rust": subprocess.check_output(["rustc", "+1.98.1", "--version"], env=env, text=True).strip(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "declaration_observer": args.declarations,
        "probe_sha256": hashlib.sha256((source / "tools/research/probe").read_bytes()).hexdigest(),
        "limitations": "Shared-host observations; elapsed times are not benchmarks. See README.md.",
    })
    (out / "source.diff").write_text(git(source, "diff", "HEAD", "--binary") + "\n")
    summary, failed = {}, False
    phases = ("observe", "verify") if args.phase == "both" else (args.phase,)
    for phase in phases:
        reports, audits = {}, {}
        for schedule in SCHEDULES:
            dest = out / phase / schedule
            dest.mkdir(parents=True)
            run_env = env.copy()
            if schedule in ("1", "2"):
                run_env["RH_SHUFFLE"] = schedule
            cmd = ["bash", str(source / "tools/research/probe"), args.app,
                   "RH_FIXPOINT_VERIFY=" + ("0" if phase == "observe" else "1")]
            if phase == "observe":
                cmd.append("RH_STRUCT_DUMP=" + str(dest / "structure.jsonl"))
            if args.declarations:
                cmd.append("RH_DECL_DUMP=" + str(dest / "declarations.jsonl"))
                if args.app == "structure_fixture":
                    cmd.append("RH_DECL_FIXTURE=1")
            start = time.monotonic()
            with (dest / "report.json").open("w") as stdout, (dest / "runner.stderr").open("w") as stderr:
                result = subprocess.run(cmd, cwd=dest, env=run_env, stdout=stdout, stderr=stderr)
            save(dest / "command.json", {"command": cmd, "schedule": schedule,
                 "seconds": time.monotonic() - start, "exit": result.returncode})
            if result.returncode:
                raise RuntimeError("probe failed: " + str(dest))
            report = json.loads((dest / "report.json").read_text())
            if not report.get("digest") or not report.get("structure", {}).get("end", {}).get("digest"):
                raise RuntimeError("missing report digests: " + str(dest))
            reports[schedule] = report
            if args.declarations:
                with (dest / "declarations.jsonl").open() as stream:
                    declaration = json.loads(next(stream))
                if declaration.get("schema") != "rh-declaration-shadow-v1" or not declaration.get("counts", {}).get("accesses"):
                    raise RuntimeError("missing declaration audit counters: " + str(dest))
                save(dest / "declaration-summary.json", declaration)
            if phase == "observe":
                with (dest / "structure.jsonl").open() as stream:
                    audits[schedule] = json.loads(next(stream))["audit"]
        first = reports["unset"]
        row = {
            "same_values": all(r["digest"] == first["digest"] for r in reports.values()),
            "same_aggregate_structure": all(r["structure"]["end"] == first["structure"]["end"]
                                            for r in reports.values()),
            "aggregate_start_equals_end": {s: r["structure"]["start"] == r["structure"]["end"]
                                           for s, r in reports.items()},
        }
        if args.declarations:
            row["declarations"] = {}
            for schedule in SCHEDULES:
                declaration = json.loads((out / phase / schedule / "declaration-summary.json").read_text())
                row["declarations"][schedule] = declaration
                failed |= not declaration["complete"] or not declaration["start_equals_end"]
            row["same_declarations"] = len({d["declaration_start"] for d in row["declarations"].values()}) == 1
            failed |= not row["same_declarations"]
        if phase == "observe":
            row["audits"] = audits
            row["logical_comparisons"] = {}
            for left, right in PAIRS:
                pair = left + "--" + right
                cmd = [sys.executable, "-B", str(source / "tools/struct_diff.py"),
                       str(out / phase / left / "structure.jsonl"),
                       str(out / phase / right / "structure.jsonl"), "--json", "--samples", "3",
                       "--check", "--changes", str(out / phase / (pair + ".changes.jsonl"))]
                with (out / phase / (pair + ".diff.json")).open("w") as stream:
                    result = subprocess.run(cmd, env=env, stdout=stream)
                if result.returncode not in (0, 1):
                    raise RuntimeError("invalid logical comparison: " + pair)
                row["logical_comparisons"][pair] = result.returncode
                failed |= result.returncode == 1
        else:
            row["verify_moved"] = {}
            for schedule, report in reports.items():
                checks = report.get("verify", [])
                if {v["loop"] for v in checks} != {"production", "views_and_tests", "absorb"}:
                    raise RuntimeError("missing verification loops: " + schedule)
                moved = sum(sum(v["moved"].values()) for v in checks)
                row["verify_moved"][schedule] = moved
                failed |= moved != 0
        failed |= not row["same_values"] or not row["same_aggregate_structure"]
        summary[phase] = row
        save(out / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print("sweep: " + str(error), file=sys.stderr)
        sys.exit(2)
