#!/usr/bin/env python3
"""Cached, explicitly named Roundhouse observers (Python 3.9, standard library)."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCHEMA = 1
CONDITION = "cached-observers-20261015-source-rebuild"
SCHEDULES = ("unset", "1", "2", "repeat")
COMMON = dict(RH_FOLD="1", RH_FOLD_SLOTS="1", RH_FOLD_JOIN="1", RH_FOLD_TAIL="1",
              RH_BRK_ALLARMS="1", RH_SCHED="sccq", RH_FIXPOINT_DIGEST="1",
              RH_FIXPOINT_STATS="1", RH_PRECISION_CENSUS="1", RH_PUBLIC_INPUT="1", RH_ERRGATE="1")
DUMPS = {"RH_REASON_SITE_CENSUS": "census.jsonl", "RH_STRUCT_DUMP": "structure.jsonl",
         "RH_DECL_DUMP": "declarations.jsonl"}
FIELDS = ("value_digests", "reason_census", "reason_rows", "successful_writes",
          "law_violation_counts", "diagnostics", "loops", "verify", "exit_code")
ARTIFACT_FIELDS = ("reason_rows", "successful_writes")


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temp), str(path))
    finally:
        if temp.exists():
            temp.unlink()


@contextmanager
def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def normalize(value, root):
    """Retain full identities, including nested JSON strings; make the app root relative."""
    if isinstance(value, str):
        return value.replace(str(root), ".")
    if isinstance(value, list):
        return [normalize(v, root) for v in value]
    if isinstance(value, dict):
        return {normalize(k, root): normalize(v, root) for k, v in value.items()}
    return value


def inventory(root, ancestors=()):
    """Same path/bytes/mode/link identity used by the generalization inventory."""
    root = Path(root)
    rows = []
    for base, dirs, files in os.walk(str(root), followlinks=False):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        links = [d for d in dirs if (Path(base) / d).is_symlink()]
        dirs[:] = [d for d in dirs if d not in links]
        for name in sorted(files + links):
            if name == ".git":
                continue
            p = Path(base) / name
            row = {"path": p.relative_to(root).as_posix()}
            if p.is_symlink():
                target = p.resolve()
                # Hash external link contents too: link text alone is insufficient for a cache.
                row.update(kind="symlink", target=os.readlink(str(p)))
                if not target.exists():
                    row["resolved_kind"] = "missing"
                elif target.is_dir():
                    row["resolved_kind"] = "directory"
                    if str(target) in ancestors or target == root.resolve():
                        row["resolved_tree_sha256"] = "cycle"
                    else:
                        _, nested = inventory(target, ancestors + (str(root.resolve()),))
                        row["resolved_tree_sha256"] = digest(nested)
                else:
                    row.update(resolved_kind="file", resolved_sha256=sha(target))
            else:
                stat = p.stat()
                row.update(kind="file", sha256=sha(p), bytes=stat.st_size,
                           executable=bool(stat.st_mode & 0o111))
            rows.append(row)
    rows.sort(key=lambda row: row["path"])
    # Keep the earlier inventory's tree digest; enrich the cache manifest with link dependencies.
    original = [{k: v for k, v in row.items() if not k.startswith("resolved_")} for row in rows]
    return digest(original), rows


def setting(name):
    name = name.replace("repeat-unset-", "repeat-")
    match = re.fullmatch(r"(unset|1|2|repeat)-v([01])-a([01])", name)
    if not match:
        raise ValueError("invalid setting: " + name + "; use e.g. unset-v1-a1 or 1-v0-a0")
    schedule, verify, audit = match.groups()
    return {"name": name, "schedule": schedule, "verification": verify == "1", "audit": audit == "1"}


def all_settings():
    return [setting("%s-v%d-a%d" % (s, v, a)) for s in SCHEDULES for v in (1, 0) for a in (1, 0)]


def key_payload(binary_sha256, manifest_sha256, flags, schedule, runtime=None):
    return {"schema": SCHEMA, "binary_sha256": binary_sha256,
            "input_manifest_sha256": manifest_sha256,
            "rh_flags": {k: v for k, v in sorted(flags.items()) if k.startswith("RH_")},
            "schedule": schedule, "runtime": runtime or {}}


def cache_key(binary_sha256, manifest_sha256, flags, schedule, runtime=None):
    return digest(key_payload(binary_sha256, manifest_sha256, flags, schedule, runtime))


def environment(flags):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("RH_", "ROUNDHOUSE_", "SOUND_", "PROVENANCE_")) and k != "PROBE_BASE"}
    env.update(RBENV_VERSION="4.0.7", LC_ALL="C", HEAVY_LOCK_MODE="shared")
    # rbenv shims can otherwise leave a different Ruby first on PATH.
    rbenv = shutil.which("rbenv", path=env.get("PATH"))
    if rbenv:
        ruby = subprocess.check_output([rbenv, "which", "ruby"], env=env, text=True).strip()
        env["PATH"] = str(Path(ruby).parent) + os.pathsep + env.get("PATH", "")
    env.update(flags)
    return env


def runtime_identity(env):
    ruby = shutil.which("ruby", path=env.get("PATH"))
    if not ruby:
        raise ValueError("CRuby 4.0.7 is required")
    version = subprocess.check_output([ruby, "--version"], env=env, text=True).strip()
    if not version.startswith("ruby 4.0.7 "):
        raise ValueError("expected CRuby 4.0.7, got " + version)
    return {"ruby_version": version, "ruby_sha256": sha(Path(ruby).resolve()), "platform": sys.platform}


def load_input(args, cache):
    config = read(HERE / "apps.json")
    spec = config.get(args.app, {})
    if args.input is None and not spec:
        raise ValueError("unknown app; provide --input for a public app")
    app = Path(args.input) if args.input else ROOT / spec["path"]
    app = app.resolve()
    if not (app / "app").is_dir():
        raise ValueError("not a Rails input: " + str(app))
    tree, entries = inventory(app)
    if not args.input and spec.get("tree_sha256") and tree != spec["tree_sha256"]:
        raise ValueError("pinned app input changed: " + args.app)
    if args.input:
        spec = dict(spec)
        spec.pop("commit", None)
        if (app / ".git").exists():
            spec["commit"] = subprocess.check_output(
                ["git", "-C", str(app), "rev-parse", "HEAD"], text=True).strip()
    manifest = {"schema": 1, "tree_sha256": tree, "entries": entries}
    manifest_sha = digest(manifest)
    path = cache / "inputs" / (manifest_sha + ".json")
    with lock(cache / "locks" / (manifest_sha + ".input.lock")):
        if path.exists() and read(path) != manifest:
            raise ValueError("input manifest cache corruption")
        if not path.exists():
            save(path, manifest)
    return app, manifest_sha, tree, spec


def artifact(path, value):
    save(path, value)
    return {"file": path.name, "sha256": sha(path), "count": len(value)}


def reduce_outputs(directory, root, code):
    reports, audits, laws = [], [], {}
    diagnostic_counts = {}
    # Large provenance reports remain in raw stderr; parse only their bounded counters.
    with (directory / "stderr.log").open(errors="replace") as stream:
        for line in stream:
            if line.startswith("rh-fixpoint: "):
                reports.append(json.loads(line[len("rh-fixpoint: "):]))
            elif line.startswith("rh-provenance-audit: "):
                audits.append(json.loads(line[len("rh-provenance-audit: "):]))
            elif line.startswith(("STORAGE-EXTENDED ", "PENDING-FACTORIAL ", "STORAGE-NORMAL-FORM ")):
                kind, data = line.split(" ", 1)
                laws[kind] = json.loads(data).get("counts", {})
            match = re.search(r"\b(warning|error)\[([^\]]+)\]:", line)
            if match:
                kind = match[1] + "/" + match[2]
                diagnostic_counts[kind] = diagnostic_counts.get(kind, 0) + 1
    if len(reports) != 1:
        raise ValueError("expected one rh-fixpoint report, got " + str(len(reports)))
    report = reports[0]
    if not isinstance(report.get("digest"), dict) or len(report["digest"]) != 10:
        raise ValueError("expected exactly ten value digests")
    save(directory / "report.json", report)
    for i, audit in enumerate(audits):
        # Origin losses are exposed violations; missing instrumentation is not zero violations.
        exposed = {k: v for k, v in audit.items() if k in (
            "parameter_type_origin_losses", "parameter_output_origin_losses", "parameter_losses_by_kind")}
        if exposed:
            laws["producer_evidence_" + str(i)] = exposed
    obs = {"value_digests": report["digest"], "reason_census": report.get("census"),
           "reason_rows": None, "successful_writes": None,
           "law_violation_counts": laws or None, "diagnostics": diagnostic_counts,
           "loops": report.get("loops"), "verify": report.get("verify"), "exit_code": code}
    path = directory / "census.jsonl"
    if path.exists():
        rows = {}
        counts = dict(pending=0, gradual=0, unresolved=0)
        with path.open() as stream:
            for line in stream:
                row = normalize(json.loads(line), root)
                identity = {k: v for k, v in row.items() if k not in ("untyped_kinds", "type_hash")}
                key = canonical(identity)
                if key in rows:
                    raise ValueError("duplicate reason census identity")
                rows[key] = {"untyped_kinds": row["untyped_kinds"], "type_hash": row["type_hash"]}
                for bit, name in enumerate(("pending", "gradual", "unresolved")):
                    counts[name] += bool(row["untyped_kinds"] & (1 << bit))
        census = report.get("census", {})
        if len(rows) != census.get("untyped_anywhere") or counts != census.get("untyped_by_provenance"):
            raise ValueError("reason rows do not reconcile with native census")
        obs["reason_rows"] = artifact(directory / "reason-rows.json", rows)
    path = directory / "declarations.jsonl"
    if path.exists():
        identities = set()
        with path.open("rb") as stream:
            header = json.loads(next(stream))
            if header.get("schema") != "rh-declaration-shadow-v1":
                raise ValueError("unsupported declaration schema")
            for line in stream:
                if line.startswith(b'["mutation",'):
                    identities.add(canonical(normalize(json.loads(line)[1:], root)))
        if len(identities) != header["counts"]["successful_writers"]:
            raise ValueError("successful-write identity count does not reconcile")
        obs["successful_writes"] = artifact(directory / "successful-writes.json",
                                              [json.loads(v) for v in sorted(identities)])
        save(directory / "declaration-header.json", normalize(header, root))
    path = directory / "structure.jsonl"
    if path.exists():
        with path.open("rb") as stream:
            header = json.loads(next(stream))
        save(directory / "structure-header.json", normalize(header, root))
    return obs


def run_child(request):
    """Executed inside the shared slot; wait4 measures this analyzer, never other cells."""
    out = Path(request["directory"])
    env = environment(request["flags"])
    env["TMPDIR"] = str(out)
    command = [request["binary"], "check", "--continue", "."]
    started = time.monotonic()
    child = None

    def stop(signum, frame):
        if child is not None:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    timed_out = False
    with (out / "stdout.log").open("wb") as stdout, (out / "stderr.log").open("wb") as stderr:
        child = subprocess.Popen(command, cwd=request["input"], env=env, stdout=stdout,
                                 stderr=stderr, start_new_session=True)
        deadline = started + request["timeout"]
        try:
            while True:
                pid, status, usage = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    break
                if time.monotonic() >= deadline:
                    timed_out = True
                    os.killpg(child.pid, signal.SIGKILL)
                    _, status, usage = os.wait4(child.pid, 0)
                    break
                time.sleep(0.05)
        except BaseException:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.wait4(child.pid, 0)
            raise
        code = os.waitstatus_to_exitcode(status)
        child.returncode = code
    metrics = {"wall_seconds": time.monotonic() - started,
               "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
               "cpu_seconds": usage.ru_utime + usage.ru_stime,
               "peak_rss_bytes": int(usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)),
               "exit_code": code, "timed_out": timed_out, "ended_utc": now()}
    save(out / "metrics.json", metrics)
    return 0


def observed(result, field):
    parts = field.split(".")
    value = result["observations"].get(parts[0])
    if parts[0] in ARTIFACT_FIELDS and value is not None:
        path = Path(result["directory"]) / value["file"]
        if sha(path) != value["sha256"]:
            raise ValueError("corrupt observation artifact: " + str(path))
        value = read(path)
    for part in parts[1:]:
        value = value.get(part) if isinstance(value, dict) else None
    return value


def differences(left, right, fields=FIELDS):
    changes = {}
    for field in fields:
        a, b = observed(left, field), observed(right, field)
        if a != b:
            detail = {"left_sha256": digest(a), "right_sha256": digest(b)}
            if isinstance(a, dict) and isinstance(b, dict):
                keys = sorted(set(a) | set(b))
                detail["changed_keys"] = [k for k in keys if k not in a or k not in b or a[k] != b[k]]
            changes[field] = detail
    return changes


def checked_result(path):
    result = read(path)
    # Raw dumps are hashed at capture. Warm reads check sizes and rehash the small observations.
    for name, expected in result.get("artifacts", {}).items():
        p = Path(result["directory"]) / name
        if (not p.is_file() or p.stat().st_size != expected["bytes"]
                or (p.stat().st_size < 1024 * 1024 and sha(p) != expected["sha256"])):
            raise ValueError("corrupt cached artifact: " + str(p))
    for field in ARTIFACT_FIELDS:
        if result.get("observations", {}).get(field) is not None:
            observed(result, field)
    return result


def one_cell(args, cache, binary_sha, app, manifest_sha, tree, spec, runtime, extra, cell):
    flags = dict(COMMON)
    for k, v in extra.items():
        if v is None:
            flags.pop(k, None)
        else:
            flags[k] = str(v)
    flags.update(RH_FIXPOINT_VERIFY=str(int(cell["verification"])), RH_PROVENANCE_AUDIT=str(int(cell["audit"])))
    if cell["schedule"] in ("1", "2"):
        flags["RH_SHUFFLE"] = cell["schedule"]
    # A deterministic capture path makes the *actual*, complete RH environment part of the key.
    prekey = cache_key(binary_sha, manifest_sha, dict(flags, **DUMPS), cell["schedule"], runtime)
    stage = cache / "capture" / prekey
    flags.update({k: str(stage / name) for k, name in DUMPS.items()})
    key = cache_key(binary_sha, manifest_sha, flags, cell["schedule"], runtime)
    object_dir = cache / "objects" / key[:2] / key
    baseline = object_dir / "baseline.json"
    recovered = object_dir / "accepted.json"
    taint = object_dir / "inconsistent.json"

    def cached_reference():
        # References and their artifacts are immutable and published atomically. A reader must
        # not queue behind a slow --fresh run when a complete reference already exists.
        reference = recovered if recovered.exists() else baseline
        result = checked_result(reference)
        inconsistent = taint.exists()
        return {"cache_key": key, "result": str(reference), "cache_hit": True,
                "analyzer_runs": 0, "fresh_match": False if inconsistent else None,
                "valid": result["valid"] and not inconsistent}

    if baseline.exists() and not args.fresh:
        return cached_reference()
    with lock(cache / "locks" / (key + ".lock")):
        reference = recovered if recovered.exists() else baseline
        if baseline.exists() and not args.fresh:
            return cached_reference()
        object_dir.mkdir(parents=True, exist_ok=True)
        if stage.exists():
            abandoned = object_dir / "attempts" / ("interrupted-" + uuid.uuid4().hex)
            abandoned.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(stage), str(abandoned))
        stage.mkdir(parents=True)
        attempt = object_dir / "attempts" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                                              + "-" + uuid.uuid4().hex[:10])
        request = {"binary": str(args.bin), "input": str(app), "directory": str(stage),
                   "flags": flags, "timeout": args.timeout}
        save(stage / "request.json", request)
        wrapper = getattr(args, "lock_wrapper", HERE / "lock.py")
        heavy_lock = getattr(args, "lock_file", HERE / "cache/heavy.lock")
        wrapped = [sys.executable, str(wrapper), "--shared",
                   str(heavy_lock), sys.executable, str(Path(__file__).resolve()),
                   "_cell", str(stage / "request.json")]
        started = time.monotonic()
        receipt = {"schema": SCHEMA, "condition": CONDITION, "app": args.app, "setting": cell,
                   "cache_key": key, "key": key_payload(binary_sha, manifest_sha, flags, cell["schedule"], runtime),
                   "started_utc": now(), "binary": str(args.bin), "input": str(app),
                   "input_pin": spec.get("commit"), "input_tree_sha256": tree,
                   "tool_sha256": sha(Path(__file__)), "wrapped_command": wrapped,
                   "inference_environment": flags, "directory": str(attempt)}
        save(stage / "launch.json", receipt)
        # This config is a memory constraint, independent of analyzer behavior and app semantics.
        serial = spec.get("max_parallel") == 1
        serial_path = Path(heavy_lock).parent / ("observer-memory-" + digest(args.app) + ".lock")
        with (lock(serial_path) if serial else lock(cache / "locks" / (key + ".launch.lock"))):
            with (stage / "launcher.log").open("wb") as log:
                env = os.environ.copy()
                env["HEAVY_LOCK_MODE"] = "shared"
                status = subprocess.call(wrapped, env=env, stdout=log, stderr=subprocess.STDOUT)
        receipt.update(ended_utc=now(), total_seconds=time.monotonic() - started,
                       launcher_exit_code=status, valid=False, observations={})
        try:
            receipt["metrics"] = read(stage / "metrics.json")
            code = receipt["metrics"]["exit_code"]
            receipt["observations"] = reduce_outputs(stage, app, code)
            if status or code not in (0, 1) or receipt["metrics"]["timed_out"]:
                raise ValueError("analyzer did not complete successfully")
            after_tree, after_rows = inventory(app)
            after_manifest = digest({"schema": 1, "tree_sha256": after_tree, "entries": after_rows})
            if sha(args.bin) != binary_sha or after_manifest != manifest_sha:
                raise ValueError("binary or input changed during the cell")
            receipt["valid"] = True
        except (OSError, ValueError, KeyError, StopIteration) as error:
            receipt["error"] = str(error)
        receipt["artifacts"] = {p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                                for p in sorted(stage.iterdir()) if p.is_file()}
        attempt.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(stage), str(attempt))
        save(attempt / "result.json", receipt)
        fresh_match, fresh_changes = None, {}
        if baseline.exists():
            old = checked_result(reference)
            if receipt["valid"] and old["valid"]:
                fresh_changes = differences(old, receipt)
                fresh_match = not fresh_changes
            elif receipt["valid"]:
                # Retain the failed first attempt, but allow an explicit successful retry to be cached.
                if not recovered.exists():
                    save(recovered, receipt)
            else:
                fresh_match, fresh_changes = False, {"valid": False}
            save(attempt / "fresh-comparison.json", {"cache_key": key, "baseline": str(reference),
                                                     "identical_observations": fresh_match,
                                                     "differences": fresh_changes})
            if fresh_match is False and receipt["valid"] and old["valid"] and not taint.exists():
                save(taint, {"first_inconsistent_attempt": str(attempt), "differences": fresh_changes})
        else:
            save(baseline, receipt)
        return {"cache_key": key, "result": str(attempt / "result.json"), "cache_hit": False,
                "analyzer_runs": 1, "fresh_match": fresh_match,
                "valid": receipt["valid"] and not taint.exists(),
                "fresh_differences": fresh_changes}


def label_path(cache, name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
        raise ValueError("label must contain only letters, digits, dots, underscores and hyphens")
    return cache / "labels" / name / "label.json"


def label_rows(label):
    rows = []
    for name, ref in sorted(label["cells"].items()):
        result = read(ref["result"])
        m = result.get("metrics", {})
        wall = "%.2fs / %.2fs" % (m.get("wall_seconds", 0), m.get("cpu_seconds", 0))
        rss = "%.3f GiB" % (m.get("peak_rss_bytes", 0) / (1024 ** 3))
        state = "cached" if ref["cache_hit"] else "fresh" if ref["fresh_match"] is not None else "ran"
        if not ref["valid"] or ref["fresh_match"] is False:
            state = "FAIL"
        rows.append("| %s | %s | %s | %s |" % (name, state, wall, rss))
    return rows


def run(args):
    started = time.monotonic()
    args.bin = args.bin.resolve()
    if not args.bin.is_file() or not os.access(str(args.bin), os.X_OK):
        raise ValueError("--bin must be an executable file")
    cache = args.cache_root.resolve()
    path = label_path(cache, args.label)
    cells = all_settings() if args.matrix else [setting(n.strip()) for n in (args.settings or "unset-v1-a1").split(",")]
    if len({s["name"] for s in cells}) != len(cells):
        raise ValueError("duplicate settings")
    extra = read(args.flags) if args.flags else {}
    for flag in args.flag:
        if "=" not in flag:
            raise ValueError("--flag requires RH_NAME=value")
        k, v = flag.split("=", 1)
        extra[k] = v
    protected = set(DUMPS) | {"RH_FIXPOINT_VERIFY", "RH_PROVENANCE_AUDIT", "RH_SHUFFLE"}
    if any(not k.startswith("RH_") or k in protected for k in extra):
        raise ValueError("profile flags must be RH_*; schedules, verification, audit and dumps are owned by settings")
    binary_sha = sha(args.bin)
    app, manifest_sha, tree, spec = load_input(args, cache)
    runtime = runtime_identity(environment({}))
    references = {}
    with ThreadPoolExecutor(max_workers=1 if spec.get("max_parallel") == 1 else args.jobs) as pool:
        futures = {pool.submit(one_cell, args, cache, binary_sha, app, manifest_sha, tree,
                               spec, runtime, extra, cell): cell for cell in cells}
        for future in as_completed(futures):
            cell = futures[future]
            ref = future.result()
            references[args.app + "/" + cell["name"]] = ref
            print("%s %s %s" % ("CACHE" if ref["cache_hit"] else "RUN", args.app, cell["name"]), flush=True)
    with lock(path.with_suffix(".lock")):
        label = read(path) if path.exists() else {"schema": SCHEMA, "condition": CONDITION,
                                                  "label": args.label, "cells": {}, "invocations": []}
        for name, ref in references.items():
            if name in label["cells"] and label["cells"][name]["cache_key"] != ref["cache_key"]:
                raise ValueError("label already has a different condition for " + name + "; choose a new label")
            label["cells"][name] = ref
        invocation = {"ended_utc": now(), "app": args.app, "settings": [c["name"] for c in cells],
                      "analyzer_runs": sum(r["analyzer_runs"] for r in references.values()),
                      "cache_hits": sum(r["cache_hit"] for r in references.values()), "fresh": args.fresh,
                      "elapsed_seconds": time.monotonic() - started}
        label["invocations"].append(invocation)
        save(path, label)
        markdown = ["# Observer label " + args.label, "", "Condition: `" + CONDITION + "`. Shared-host profiles.", "",
                    "| App / setting | Source | Wall / CPU | Peak RSS |", "| --- | --- | --- | --- |"] + label_rows(label)
        path.with_suffix(".md").write_text("\n".join(markdown) + "\n")
    print(canonical(invocation))
    print(str(path))
    return int(any(not r["valid"] or r["fresh_match"] is False for r in references.values()))


def load_label(cache, name):
    return read(label_path(cache, name))


def label_records(label):
    records = {}
    for name, ref in label["cells"].items():
        result = read(ref["result"])
        taint = Path(result["directory"]).parents[1] / "inconsistent.json"
        if not ref["valid"] or ref.get("fresh_match") is False or taint.exists():
            result["valid"] = False
        records[name] = result
    return records


def compare(args):
    cache = args.cache_root.resolve()
    a, b = load_label(cache, args.left), load_label(cache, args.right)
    ar, br = label_records(a), label_records(b)
    rows = []
    for name in sorted(set(a["cells"]) | set(b["cells"])):
        if name not in a["cells"] or name not in b["cells"]:
            row = {"setting": name, "status": "missing", "missing_from": args.left if name not in a["cells"] else args.right}
        else:
            left, right = ar[name], br[name]
            delta = differences(left, right)
            state = "different" if delta else "equal"
            if not left["valid"] or not right["valid"]:
                state = "invalid"
            row = {"setting": name, "status": state, "differences": delta,
                   "left_valid": left["valid"], "right_valid": right["valid"],
                   "unavailable": [f for f in FIELDS if observed(left, f) is None or observed(right, f) is None]}
        rows.append(row)
        print(row["status"].upper() + " " + name + " " + ",".join(row.get("differences", {}))
              + ("; unavailable=" + ",".join(row["unavailable"]) if row.get("unavailable") else ""))
    result = {"condition": CONDITION, "left": args.left, "right": args.right, "cells": rows}
    out = cache / "comparisons" / (args.left + "--" + args.right + "--" + uuid.uuid4().hex[:8])
    save(out.with_suffix(".json"), result)
    out.with_suffix(".md").write_text("# Observer comparison\n\n`%s` versus `%s`; condition `%s`.\n\n"
        "| Setting | Verdict | Changed fields |\n| --- | --- | --- |\n%s\n" % (
            args.left, args.right, CONDITION, "\n".join("| %s | %s | %s |" % (
                r["setting"], r["status"], ", ".join(r.get("differences", {})) or "none") for r in rows)))
    print(str(out.with_suffix(".json")))
    return int(any(r["status"] == "missing" or r.get("left_valid") is False or r.get("right_valid") is False for r in rows))


def reason_delta(left, right):
    return {"changes": [{"identity": json.loads(k), "left": left[k], "right": right[k]}
                        for k in sorted(set(left) & set(right)) if left[k] != right[k]],
            "left_only": [{"identity": json.loads(k), **left[k]} for k in sorted(set(left) - set(right))],
            "right_only": [{"identity": json.loads(k), **right[k]} for k in sorted(set(right) - set(left))]}


def check_claim(claim, records, other=None):
    """Pure claim evaluator. A missing cell/field or invalid run always fails closed."""
    settings = claim.get("settings", [])
    apps = claim.get("apps", [])
    if not settings or not apps or not claim.get("name"):
        raise ValueError("every claim needs name, apps and explicit nonempty settings")
    field = claim.get("field", "value_digests")
    if field.split(".")[0] not in FIELDS:
        raise ValueError("unknown observer field: " + field)
    kind = claim.get("kind", "equal")
    if kind not in ("equal", "equals", "changed_keys", "reason_delta", "zero"):
        raise ValueError("unknown claim kind: " + kind)
    if kind == "equal" and len(settings) < 2:
        raise ValueError("equal needs at least two settings; singleton equalities are vacuous")
    verdicts = []
    for app in apps:
        base_name = app + "/" + claim.get("baseline", settings[0])
        for name in settings:
            setting(name)
            full = app + "/" + name
            result = records.get(full)
            v = {"claim": claim["name"], "setting": full, "field": field, "passed": False}
            try:
                if result is None or not result["valid"]:
                    raise ValueError("missing or invalid cell")
                actual = observed(result, field)
                if actual is None:
                    raise ValueError("observer field is unavailable in this binary/setting")
                expected = claim.get("expected_by_setting", {}).get(full, claim.get("expected"))
                if kind in ("equal", "reason_delta", "changed_keys"):
                    peer_name = full if kind == "changed_keys" else base_name
                    peer = (other or {}).get(peer_name) if kind == "changed_keys" else records.get(peer_name)
                    if peer is None or not peer["valid"]:
                        raise ValueError("missing or invalid comparison cell: " + peer_name)
                    before = observed(peer, field)
                    if before is None:
                        raise ValueError("comparison observer is unavailable")
                    if kind == "equal":
                        passed = before == actual
                    elif kind == "changed_keys":
                        if not isinstance(before, dict) or not isinstance(actual, dict) or not isinstance(expected, list):
                            raise ValueError("changed_keys needs dictionary observations and an expected list")
                        changed = sorted(k for k in set(before) | set(actual)
                                         if k not in before or k not in actual or before[k] != actual[k])
                        passed = changed == sorted(expected)
                        v["changed_keys"] = changed
                    else:
                        actual = reason_delta(before, actual)
                        passed = actual == expected
                        v["observed_delta"] = actual
                elif kind == "equals":
                    if "expected" not in claim and full not in claim.get("expected_by_setting", {}):
                        raise ValueError("equals needs an expected value")
                    passed = actual == expected
                else:
                    def zero(value):
                        if isinstance(value, dict):
                            return all(zero(x) for x in value.values())
                        return type(value) in (int, float) and value == 0
                    passed = zero(actual)
                v["passed"] = passed
                if not passed:
                    v["reason"] = "observation differs from the named equality/expectation"
            except (KeyError, OSError, ValueError) as error:
                v["reason"] = str(error)
            verdicts.append(v)
    return verdicts


def claims(args):
    cache = args.cache_root.resolve()
    label = load_label(cache, args.label)
    records = label_records(label)
    spec = read(args.spec)
    verdicts = []
    for claim in spec["claims"]:
        other = None
        if claim.get("against"):
            other_label = load_label(cache, claim["against"])
            other = label_records(other_label)
        verdicts.extend(check_claim(claim, records, other))
    if not verdicts:
        raise ValueError("claim specification is empty")
    result = {"condition": CONDITION, "label": args.label, "spec_sha256": sha(args.spec),
              "passed": all(v["passed"] for v in verdicts), "verdicts": verdicts}
    out = label_path(cache, args.label).parent / ("claims-" + uuid.uuid4().hex[:8])
    save(out.with_suffix(".json"), result)
    lines = ["# Observer claims", "", "Label `%s`; condition `%s`." % (args.label, CONDITION), "",
             "| Claim | Setting | Verdict |", "| --- | --- | --- |"]
    for v in verdicts:
        status = "PASS" if v["passed"] else "FAIL"
        print(status + " " + v["setting"] + " " + v["claim"] + (": " + v["reason"] if "reason" in v else ""))
        lines.append("| %s | %s | %s |" % (v["claim"], v["setting"], status))
    out.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(str(out.with_suffix(".json")))
    return int(not result["passed"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run", help="run missing cells; report cached cells without invoking the analyzer")
    p.add_argument("--bin", type=Path, required=True)
    p.add_argument("--app", required=True)
    p.add_argument("--input", type=Path, help="override the configured public input path")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--settings", help="comma-separated named settings")
    group.add_argument("--matrix", choices=("full",))
    p.add_argument("--label", required=True)
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--flags", type=Path, help="JSON map of RH_* overrides; null unsets a flag")
    p.add_argument("--flag", action="append", default=[])
    p.add_argument("--jobs", type=int, default=6)
    p.add_argument("--timeout", type=float, default=1800)
    p.add_argument("--lock-wrapper", type=Path, default=HERE / "lock.py")
    p.add_argument("--lock-file", type=Path, default=HERE / "cache/heavy.lock")
    p.set_defaults(func=run)
    p = sub.add_parser("compare", help="compare two recorded labels, setting by setting")
    p.add_argument("left")
    p.add_argument("right")
    p.set_defaults(func=compare)
    p = sub.add_parser("claims", help="check explicit equalities against recorded cells")
    p.add_argument("label")
    p.add_argument("--spec", type=Path, required=True)
    p.set_defaults(func=claims)
    for p in (sub.choices["run"], sub.choices["compare"], sub.choices["claims"]):
        p.add_argument("--cache-root", type=Path, default=HERE / "cache")
    p = sub.add_parser("_cell", help=argparse.SUPPRESS)
    p.add_argument("request", type=Path)
    p.set_defaults(func=lambda args: run_child(read(args.request)))
    args = parser.parse_args(argv)
    if hasattr(args, "jobs") and (args.jobs < 1 or args.jobs > 6 or args.timeout <= 0):
        parser.error("--jobs must be 1..6 and --timeout must be positive")
    try:
        return args.func(args)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print("obs: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
