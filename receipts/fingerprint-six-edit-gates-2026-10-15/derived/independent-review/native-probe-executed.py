#!/usr/bin/env python3
"""Run the builder's sealed binaries and check functions on fresh frozen inputs."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

BASE = Path(__file__).resolve().parent
WARM = BASE / "week/warm"
os.environ.update(WARM_EDIT_AUDITS_WARM=str(WARM), TMPDIR=str(WARM / ".tmp"),
                  PYTHONDONTWRITEBYTECODE="1", RBENV_VERSION="4.0.7",
                  PROFILE_STOP_UTC="2026-10-15T08:35:00+00:00")
sys.dont_write_bytecode = True
sys.path.insert(0, str(WARM / "scripts"))
from replay_pairs import f30, pair_ok, identity
from locked_command import run as locked_run

LOCK_ROOT = Path("$WORKSPACE/workshop")
CONDITION = "rv-fingerprint-six-edit-gates-20261015-audit"
OUT = WARM / "runs/native-probe"
OUT.mkdir(parents=True, exist_ok=False)
APP = OUT / "apps/mastodon"
APP.parent.mkdir(parents=True)
source = WARM / "sources/lab/corpus/apps/mastodon"
shutil.copytree(source, APP, symlinks=True, ignore=shutil.ignore_patterns(".git"))
frozen = json.loads((f30.RECEIPT / "edits.json").read_text())
cases = [c for c in frozen["cases"] if c["app"] == "mastodon"]
assert f30.COMMON.inventory(APP)[0] == cases[0]["input_tree_sha256"]
rows, results = [], []


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def batch(label, commands):
    path = OUT / (label + "-commands.json")
    write(path, dict(condition=CONDITION, lock_mode="shared", batch=label, commands=commands))
    command = [sys.executable, str(LOCK_ROOT / "flock.py"), str(LOCK_ROOT / "heavy.lock"),
               sys.executable, "-B", str(WARM / "scripts/native_batch.py"), "--spec", str(path)]
    print(datetime.datetime.now(datetime.timezone.utc).isoformat(), label, flush=True)
    locked_run(command, env=os.environ.copy())
    found = {}
    for item in commands:
        dest = Path(item["out"])
        row = json.loads((dest / "run.json").read_text())
        headers = [line.replace(str(APP), "$APP")
                   for line in (dest / "stderr.log").read_text().splitlines()
                   if re.match(r"^(?:.*?:\d+:\d+:\s*)?(error|warning|note)\[([a-z_][a-z_0-9]*)\]:", line)]
        row["normalized_diagnostics_sha256"] = hashlib.sha256("\n".join(sorted(headers)).encode()).hexdigest()
        write(dest / "run.json", row)
        rows.append(dict(label=dest.name, **row))
        found[dest.name] = row
    write(OUT / "runs.json", rows)
    return found


def item(label, arm, flags):
    return dict(binary=str(WARM / "binaries" / (arm + "-roundhouse")),
                app=str(APP), out=str(OUT / "runs" / label), flags=flags)


def audit(row):
    report = row["reports"]["rh-warm"][0]
    components = report["fingerprint_components"]
    c = components["counters"]
    return (components["audit_enabled"] and c["input_calls"] > 0
            and c["input_calls"] == c["input_audit_comparisons"] == c["guard_audit_comparisons"]
            and c["extra_calls"] > 0 and c["extra_calls"] == c["extra_audit_comparisons"])


try:
    for schedule in ("unset", "1", "2", "unset-repeat"):
        flags = dict(f30.S3)
        if schedule in ("1", "2"):
            flags["RH_SHUFFLE"] = schedule
        seed = OUT / "caches" / (schedule + "-seed")
        seed.mkdir(parents=True)
        warm_flags = dict(flags, RH_WARM=str(seed), RH_WARM_SHADOW="1",
                          RH_WARM_TIMINGS="1", RH_WARM_FP_AUDIT="1")
        label = schedule + "-seed"
        seed_row = batch(label, [item(label, "fast", warm_flags)])[label]
        assert f30.shadow_match(seed_row) and audit(seed_row), label
        seed_file = seed / "evaluations.json"
        seed_sha = f30.sha(seed_file)
        selected = cases if schedule == "unset" else [c for c in cases if c["kind"] == "boolean"]
        for case in selected:
            path = APP / case["file"]
            original = path.read_bytes()
            assert f30.sha(path) == case["original_file_sha256"]
            assert original[case["start"]:case["end"]].decode() == case["old_body"]
            label = schedule + "-" + case["kind"]
            cache = OUT / "caches" / label
            cache.mkdir()
            path.write_bytes(original[:case["start"]] + case["replacement"].encode() + original[case["end"]:])
            try:
                assert f30.sha(path) == case["edited_file_sha256"]
                assert f30.COMMON.inventory(APP)[0] == case["edited_tree_sha256"]
                warm = item(label + "-warm", "fast", dict(warm_flags, RH_WARM=str(cache)))
                warm.update(restore_seed=str(seed_file), restore_dest=str(cache / "evaluations.json"),
                            seed_sha256=seed_sha)
                commands = [item(label + "-parent", "base", flags),
                            item(label + "-cold", "fast", flags), warm]
                group = batch(label, commands)
                p, c, w = (group[label + suffix] for suffix in ("-parent", "-cold", "-warm"))
                result = dict(schedule=schedule, edit=case["kind"],
                              cold_parent_parity=identity(p) == identity(c),
                              warm_shadow_cold_parity=pair_ok(c, w), complete_audit=audit(w),
                              seed_sha256=seed_sha, edited_tree_sha256=case["edited_tree_sha256"],
                              evaluations=w["reports"]["rh-warm"][0]["evaluations"],
                              fingerprint_components=w["reports"]["rh-warm"][0]["fingerprint_components"])
                results.append(result)
                write(OUT / "results.json", dict(condition=CONDITION, comparisons=results))
                print(json.dumps({k:v for k,v in result.items() if k not in ("fingerprint_components", "evaluations")}), flush=True)
            finally:
                path.write_bytes(original)
                assert f30.COMMON.inventory(APP)[0] == case["input_tree_sha256"]
finally:
    write(OUT / "restoration.json", dict(condition=CONDITION,
          restored=f30.COMMON.inventory(APP)[0] == cases[0]["input_tree_sha256"],
          completed=len(results), expected=6))
