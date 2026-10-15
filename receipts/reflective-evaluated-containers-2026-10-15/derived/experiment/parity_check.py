#!/usr/bin/env python3
"""Fresh next/control flags-off emissions and shared prepared-suite outcomes."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
BOUND = ROOT / "week/bound-next"
LAB = ROOT / "week/lab"
C = BOUND / "sources/probe-source"
BASE = BOUND / "sources/control"
OUT = BOUND / "results/parity-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location("baseline_rerun", LAB / "receipts/baseline-2026-10-10/rerun.py")
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_", "PROVENANCE_", "PROBE_BASE"))}
    env.update(RBENV_VERSION="3.4.4", RH_REFLECT_BOUND="0", CARGO_BUILD_JOBS="4")
    original_gem_paths = subprocess.check_output(
        ["ruby", "-e", "puts Gem.path.join(':')"], env=env, text=True).strip()
    env.update(GEM_HOME=str(ROOT / "week/test-gems"),
               GEM_PATH=str(ROOT / "week/test-gems") + ":" + original_gem_paths)
    subprocess.run(["ruby", "-rsqlite3", "-e", "puts SQLite3::VERSION"], env=env, check=True)
    manifests, suites = {}, {}
    for label, tree in [("candidate", C), ("control", BASE)]:
        baseline.fixtures(tree)
        example = tree / "examples/emit_all_compare.rs"
        example.parent.mkdir(exist_ok=True)
        shutil.copyfile(LAB / "receipts/baseline-2026-10-10/emit_all.rs", example)
        arm = OUT / label
        arm.mkdir()
        native_env = dict(env, CARGO_TARGET_DIR=str(BOUND / "scratch/provenance-target"))
        command = ["cargo", "+1.98.1", "build", "--release", "--locked", "--example", "emit_all_compare"]
        with (arm / "emission-build.log").open("w") as log:
            subprocess.run(command, cwd=tree, env=native_env, stdout=log, stderr=log, check=True)
        binary = BOUND / "scratch/provenance-target/release/examples/emit_all_compare"
        with (arm / "pairs.jsonl").open("w") as stdout, (arm / "emission.stderr").open("w") as stderr:
            subprocess.run([str(binary), str(arm / "tree")], cwd=tree, env=native_env,
                           stdout=stdout, stderr=stderr, check=True)
        pairs = [json.loads(s) for s in (arm / "pairs.jsonl").read_text().splitlines()]
        if len(pairs) != 105 or any("error" in r for r in pairs):
            raise RuntimeError("Incomplete flags-off emission campaign")
        manifests[label] = {str(p.relative_to(arm / "tree")): sha(p)
                            for p in sorted((arm / "tree").rglob("*")) if p.is_file()}
        write(arm / "manifest.json", manifests[label])
        write(arm / "emission-receipt.json", dict(binary_sha256=sha(binary), pairs=len(pairs),
              files=len(manifests[label]), flags={"RH_REFLECT_BOUND": "0"},
              native_exporter_sha256=sha(example), cargo_lock_sha256=sha(tree / "Cargo.lock"),
              source_head=subprocess.check_output(["git", "-C", str(tree), "rev-parse", "HEAD"], text=True).strip()))
        native_env["CARGO_TARGET_DIR"] = str(C / "target-laws")
        command = ["cargo", "+1.98.1", "test", "--locked", "--no-fail-fast", "--", "--test-threads=1"]
        with (arm / "suite.log").open("w") as log:
            run = subprocess.run(command, cwd=tree, env=native_env, stdout=log, stderr=log)
        raw = (arm / "suite.log").read_text()
        inventory = {}
        executable = "unknown"
        for line in raw.splitlines():
            if "Running unittests" in line or "Running tests/" in line:
                executable = line.strip().split(" (")[0].split("Running ", 1)[1]
            m = re.match(r"test (\S+) \.\.\. (ok|FAILED|ignored.*)", line)
            if m:
                name, outcome = m.groups()
                inventory[executable + "::" + name] = outcome.split(",")[0]
        if not inventory:
            raise RuntimeError("Empty prepared suite inventory")
        suites[label] = inventory
        write(arm / "suite-receipt.json", dict(command=command, exit=run.returncode,
              gem_home=env["GEM_HOME"], gem_path=env["GEM_PATH"],
              inventory=inventory, failure_names=sorted(n for n, s in inventory.items() if s == "FAILED"),
              counts={kind: sum(s == kind for s in inventory.values()) for kind in ("ok", "FAILED", "ignored")},
              log_sha256=sha(arm / "suite.log"), timed_measurement=False))
        print(json.dumps({"arm": label, "suite_exit": run.returncode, "selected": len(inventory)}), flush=True)
    shared = set(suites["control"]) & set(suites["candidate"])
    changed = {n: [suites["control"][n], suites["candidate"][n]] for n in sorted(shared)
               if suites["control"][n] != suites["candidate"][n]}
    added = {n: suites["candidate"][n] for n in sorted(set(suites["candidate"]) - set(suites["control"]))}
    summary = dict(condition="reflective-evaluated-containers-next-flags-off-prepared-parity-20261015-v2-local-sqlite",
                   emission_pairs=105, emission_files=len(manifests["candidate"]),
                   emission_equal=manifests["control"] == manifests["candidate"],
                   shared_test_outcomes=len(shared), changed_shared_outcomes=changed, added_outcomes=added,
                   missing_candidate_tests=sorted(set(suites["control"]) - set(suites["candidate"])),
                   candidate_added_failures=sorted(n for n, s in added.items() if s == "FAILED"),
                   timed_measurement=False)
    write(OUT / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
