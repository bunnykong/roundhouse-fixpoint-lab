#!/usr/bin/env python3
"""Run the corpus probe on one pinned app; keep precision and verification separate.

Run under the workshop shared lock. This wrapper does not run the runtime oracle.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

D = Path(__file__).resolve().parents[1]
LAB = D / "sources/lab"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=D / "sources/probe-source")
    p.add_argument("--app", choices=["campfire", "mastodon", "chatwoot", "forem", "discourse"], default="campfire")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--candidate-env", action="append", default=[], metavar="RH_FLAG=VALUE")
    a = p.parse_args()
    source, output = a.source.resolve(), a.output.resolve()
    source.relative_to(D)
    output.relative_to(D)
    candidate = {}
    for item in a.candidate_env:
        name, value = item.split("=", 1)
        if not name.startswith("RH_") or not name.replace("_", "").isalnum():
            p.error("candidate controls must be RH_ environment names")
        if not any(name in f.read_text() for f in (source / "src").rglob("*.rs")):
            p.error("candidate control is not implemented: " + name)
        candidate[name] = value
    output.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_", "PROVENANCE_", "PROBE_BASE"))}
    env.update(CARGO_HOME=str(D / "scratch/cargo-home"), CARGO_BUILD_JOBS="4",
               CARGO_TARGET_DIR=str(D / "scratch/provenance-target"), TMPDIR=str(D / "scratch/tmp"),
               RBENV_VERSION="4.0.7")
    Path(env["CARGO_HOME"]).mkdir(parents=True, exist_ok=True)
    Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
    pin = next(x for x in json.loads((LAB / "corpus/apps.json").read_text()) if x["id"] == a.app)
    apps = D / "scratch/apps"
    app = apps / a.app
    if not app.exists():
        app.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(app)], check=True)
        git(app, "remote", "add", "origin", pin["repository_url"])
        git(app, "fetch", "--depth=1", "origin", pin["commit"])
        git(app, "checkout", "--detach", "FETCH_HEAD")
    if git(app, "rev-parse", "HEAD") != pin["commit"] or git(app, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("changed app input: " + str(app))
    build = ["cargo", "+1.98.1", "build", "--release", "--locked", "--bin", "roundhouse"]
    with (output / "build.log").open("w") as log:
        subprocess.run(build, cwd=source, env=env, stdout=log, stderr=log, check=True)
    binary = Path(env["CARGO_TARGET_DIR"]) / "release/roundhouse"
    probe = LAB / "receipts/baseline-2026-10-10/probe"
    env.update(RH_BIN=str(binary), APPS=str(apps))
    arms = [("main-compatible", True, {k: "0" for k in candidate}),
            ("s3", False, {k: "0" for k in candidate})]
    if "RH_PROVENANCE_AUDIT" in candidate:
        arms.append(("audit", False, dict({k: "0" for k in candidate}, RH_PROVENANCE_AUDIT="1")))
    if candidate:
        arms.append(("candidate", False, candidate))
    results = []
    for arm, base, extra in arms:
        for name, verify, schedule in [("precision", "0", None), ("unset", "1", None),
                                       ("seed-1", "1", "1"), ("seed-2", "1", "2"),
                                       ("unset-repeat", "1", None)]:
            dest = output / arm / name
            dest.mkdir(parents=True)
            flags = dict(extra, RH_FIXPOINT_VERIFY=verify, RH_PRECISION_CENSUS="1",
                         RH_ERRGATE="1", RH_PUBLIC_INPUT="1")
            if schedule:
                flags["RH_SHUFFLE"] = schedule
            command = ["bash", str(probe), a.app] + [k + "=" + v for k, v in sorted(flags.items())]
            run = subprocess.run(command, cwd=dest, env=dict(env, PROBE_BASE="1" if base else "0"),
                                 text=True, capture_output=True, timeout=300)
            (dest / "runner.stderr").write_text(run.stderr)
            (dest / "stdout.json").write_text(run.stdout)
            if run.returncode:
                raise RuntimeError("probe failed: " + str(dest))
            report = json.loads(run.stdout)
            results.append(dict(arm=arm, name=name, flags=flags, probe_base=base, report=report,
                                timing_claim=False))
    comparisons = [("main-compatible", "s3")]
    if candidate:
        comparisons += [("s3", "candidate"), ("main-compatible", "candidate")]
    if "RH_PROVENANCE_AUDIT" in candidate:
        comparisons += [("s3", "audit"), ("audit", "candidate")]
    for left, right in comparisons:
        logs = [output / arm / "precision" / ("probe-" + a.app + ".stderr") for arm in (left, right)]
        run = subprocess.run(["python3", "-B", str(source / "tools/errgate.py"), *map(str, logs)],
                             text=True, capture_output=True, check=True)
        (output / (left + "--" + right + ".census.txt")).write_text(run.stdout)
    (output / "source.diff").write_text(git(source, "diff", "HEAD"))
    receipt = dict(app=pin, app_tree=git(app, "rev-parse", "HEAD^{tree}"),
                   source_head=git(source, "rev-parse", "HEAD"), source_status=git(source, "status", "--porcelain"),
                   source_diff_sha256=sha(output / "source.diff"), binary_sha256=sha(binary),
                   source_files_sha256={str(f.relative_to(source)): sha(f)
                                        for f in sorted((source / "src").rglob("*.rs"))},
                   cargo_lock_sha256=sha(source / "Cargo.lock"), probe_sha256=sha(probe),
                   lab_head=git(LAB, "rev-parse", "HEAD"), build=build,
                   candidate_env=candidate, helper_sha256=sha(Path(__file__)),
                   ruby=subprocess.check_output(["ruby", "--version"], env=env, text=True).strip(),
                   condition="producer_reason-" + a.app + "-paired-probe-v1-shared-host")
    (output / "condition.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    (output / "reports.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output), "reports": len(results),
                      "runtime_oracle": "not run; use alongside f19_check.py and app traces"}))


if __name__ == "__main__":
    main()
