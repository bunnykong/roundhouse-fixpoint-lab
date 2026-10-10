#!/usr/bin/env python3
"""Regenerate the twenty public-app dumps and divergence maps in a new directory."""
import argparse
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

import recompute


HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
APPS = ("campfire", "mastodon", "chatwoot", "forem", "discourse")
S3 = dict(RH_FOLD="1", RH_FOLD_SLOTS="1", RH_FOLD_JOIN="1", RH_FOLD_TAIL="1",
          RH_BRK_ALLARMS="1", RH_SCHED="sccq", RH_FIXPOINT_VERIFY="0",
          RH_FIXPOINT_DIGEST="1", RH_FIXPOINT_STATS="1")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()


def environment():
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("RH_", "ROUNDHOUSE_", "BUNDLE_"))
           and k not in ("PROBE_BASE", "RUBYOPT", "RUBYLIB", "GEM_HOME", "GEM_PATH",
                         "DYLD_INSERT_LIBRARIES", "LD_PRELOAD")}
    env.update(RBENV_VERSION="4.0.7", CARGO_BUILD_JOBS="4", NO_COLOR="1")
    return env


def verify_inputs(app_root, pins, apps):
    common = load("structure_corpus_common", LAB / "corpus/common.py")
    for app in apps:
        path = app_root / app
        if not (path / ".git").is_dir() or git(path, "rev-parse", "HEAD") != pins[app]["commit"]:
            raise RuntimeError("Missing or wrong app commit: " + app)
        digest, files = common.inventory(path)
        if digest != pins[app]["tree_sha256"] or len(files) != pins[app]["files"]:
            raise RuntimeError("Changed app tree: " + app)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True, help="new output directory")
    parser.add_argument("--source", type=Path, help="clean checkout at the exact structure-dump commit")
    parser.add_argument("--binary", type=Path, help="prebuilt binary from that source; its hash is recorded")
    parser.add_argument("--apps", type=Path, default=LAB / "corpus/apps")
    parser.add_argument("--app", action="append", choices=APPS, help="limit the run to selected apps; default all five")
    parser.add_argument("--lock", type=Path, default=LAB / "_work/analysis.lock",
                        help="shared host analysis lock; use the same path as other heavy runs")
    args = parser.parse_args()
    pins = recompute.read(HERE / "pins.json")
    work, app_root = args.work_dir.resolve(), args.apps.resolve()
    work.mkdir(parents=True, exist_ok=False)
    lock_path = args.lock.resolve()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    env = environment()
    apps = args.app or APPS
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    condition = "structure-rerun-" + stamp
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        source = args.source.resolve() if args.source else work / "rh"
        if not args.source:
            subprocess.run(["git", "clone", "https://github.com/bunnykong/roundhouse.git", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "checkout", "--detach", pins["source_commit"]], check=True)
        if git(source, "rev-parse", "HEAD") != pins["source_commit"]:
            raise RuntimeError("Wrong source commit")
        if git(source, "rev-parse", "HEAD^{tree}") != pins["source_tree"] or git(source, "status", "--porcelain"):
            raise RuntimeError("Changed source tree")
        if args.binary:
            binary = args.binary.resolve()
        else:
            target = work / "target"
            build_env = dict(env, CARGO_TARGET_DIR=str(target), RBENV_VERSION="3.4.4")
            with (work / "build.log").open("w") as log:
                subprocess.run(["cargo", "+1.98.1", "build", "--release", "--locked", "--bin", "roundhouse"],
                               cwd=source, env=build_env, stdout=log, stderr=log, check=True)
            binary = target / "release/roundhouse"
        binary_sha = recompute.sha256(binary)
        verify_inputs(app_root, pins["inputs"], apps)
        for app in apps:
            for schedule in ("unset", "1", "2", "repeat-unset"):
                run = work / "runs" / app / schedule
                run.mkdir(parents=True)
                dump = run / "structure.jsonl"
                flags = dict(S3, RH_BIN=str(binary), APPS=str(app_root), RH_STRUCT_DUMP=str(dump))
                if schedule in ("1", "2"):
                    flags["RH_SHUFFLE"] = schedule
                command = ["bash", str(source / "tools/research/probe"), app,
                           "RH_FIXPOINT_VERIFY=0", "RH_STRUCT_DUMP=" + str(dump)]
                started = datetime.now(timezone.utc).isoformat()
                begin = time.monotonic()
                with (run / "report.json").open("w") as report, (run / "driver.stderr").open("w") as log:
                    process = subprocess.run(command, cwd=run, env=dict(env, **flags), stdout=report, stderr=log)
                seconds = time.monotonic() - begin
                if process.returncode:
                    raise RuntimeError(app + "/" + schedule + ": probe failed")
                with dump.open() as stream:
                    header = json.loads(next(stream))
                receipt = dict(app=app, schedule=schedule, condition=condition,
                               source_commit=pins["source_commit"], source_tree=pins["source_tree"],
                               binary_sha256=binary_sha, command=command, flags=flags, cwd=str(run),
                               input=pins["inputs"][app], started_utc=started, exit=process.returncode,
                               seconds=seconds, dump_bytes=dump.stat().st_size,
                               dump_sha256=recompute.sha256(dump), dump_header=header,
                               probe_sha256=recompute.sha256(source / "tools/research/probe"))
                recompute.write(run / "receipt.json", receipt)
                print(app + "/" + schedule + " recorded", flush=True)
        verify_inputs(app_root, pins["inputs"], apps)
        for app in apps:
            for left, right in recompute.PAIRS:
                pair = left + "--" + right
                run = work / "runs" / app
                command = ["python3", "-B", str(source / "tools/struct_diff.py"),
                           str(run / left / "structure.jsonl"), str(run / right / "structure.jsonl"),
                           "--json", "--samples", "3", "--changes", str(run / (pair + ".changes.jsonl"))]
                with (run / (pair + ".diff.json")).open("w") as report:
                    subprocess.run(command, stdout=report, check=True, env=env)
        a, b = recompute.build_maps(work)
        recompute.write(work / "evidence/divergence-map.json", a)
        recompute.write(work / "evidence/map-summary.json", b)
        recompute.write(work / "rerun.json", dict(condition=condition, source_commit=pins["source_commit"],
                                                binary_sha256=binary_sha, app_root=str(app_root),
                                                apps=list(apps),
                                                schedules=["unset", "1", "2", "repeat-unset"],
                                                native_hash_order="uncontrolled"))
    print("Dumps and maps: " + str(work), flush=True)


if __name__ == "__main__":
    main()
