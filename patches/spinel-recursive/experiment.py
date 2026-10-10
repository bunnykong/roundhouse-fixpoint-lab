#!/usr/bin/env python3
"""Pinned, isolated Spinel/CRuby experiment; commands and raw timings are retained."""
import argparse
import hashlib
import json
import os
import pathlib
import platform
import statistics
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent
SPINEL = ROOT / "spinel/bin/spinel"
ENV = dict(os.environ, TMPDIR=str(ROOT / "tmp"))
CASES = {"canonical": 500000, "cycle": 1000000, "tree_sum": 2000000}


def run(args, label, timeout=120):
    start = time.perf_counter()
    proc = subprocess.run([str(a) for a in args], cwd=ROOT, env=ENV,
                          capture_output=True, text=True, timeout=timeout)
    record = {"label": label, "argv": [str(a) for a in args],
              "seconds": time.perf_counter() - start, "returncode": proc.returncode,
              "stdout": proc.stdout, "stderr": proc.stderr}
    with (ROOT / "evidence/commands.jsonl").open("a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def compile_cases():
    result = {}
    for name in CASES:
        source = ROOT / "programs" / (name + ".rb")
        comp = run([SPINEL, source, "--warn-widen", "-o", ROOT / "bin" / name], name + "-compile")
        emit = run([SPINEL, source, "-c", "-o", ROOT / "generated" / (name + ".c")], name + "-emit-c")
        types = run([SPINEL, source, "--emit-types"], name + "-types")
        (ROOT / "evidence" / (name + ".types.json")).write_text(types["stdout"])
        (ROOT / "logs" / (name + ".compile.log")).write_text(comp["stdout"] + comp["stderr"])
        oracle = run(["ruby", "--disable-gems", source, "1"], name + "-oracle")
        native = run([ROOT / "bin" / name, "1"], name + "-native-output") if comp["returncode"] == 0 else None
        result[name] = {"compile": comp, "emit": emit,
                        "oracle": oracle, "native": native,
                        "matches": native is not None and native["returncode"] == 0 and
                                   native["stdout"] == oracle["stdout"],
                        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        print(name, "compile", comp["returncode"], "matches", result[name]["matches"], flush=True)
    (ROOT / "evidence/compile.json").write_text(json.dumps(result, indent=2) + "\n")


def benchmark(repeats):
    result = {}
    for name, iterations in CASES.items():
        source = ROOT / "programs" / (name + ".rb")
        engines = {"cruby": ["ruby", "--disable-gems", "--disable-yjit", source],
                   "cruby_yjit": ["ruby", "--disable-gems", "--yjit", source],
                   "spinel": [ROOT / "bin" / name]}
        expected = run(engines["cruby"] + ["1"], name + "-bench-oracle")["stdout"]
        samples = {engine: [] for engine in engines}
        startup = {engine: [] for engine in engines}
        for engine, command in engines.items():
            for i in range(3):
                record = run(command + ["1"], name + "-" + engine + "-startup")
                if record["returncode"] or record["stdout"] != expected:
                    raise RuntimeError(record)
                startup[engine].append(record["seconds"])
            record = run(command + [str(iterations)], name + "-" + engine + "-warmup")
            if record["returncode"] or record["stdout"] != expected:
                raise RuntimeError(record)
        # Rotate engine order between repetitions; no concurrent timed runs.
        keys = list(engines)
        for i in range(repeats):
            for engine in keys[i % len(keys):] + keys[:i % len(keys)]:
                record = run(engines[engine] + [str(iterations)], name + "-" + engine + "-sample")
                if record["returncode"] or record["stdout"] != expected:
                    raise RuntimeError(record)
                samples[engine].append(record["seconds"])
        medians = {key: statistics.median(value) for key, value in samples.items()}
        result[name] = {"iterations": iterations, "seconds": samples, "median_seconds": medians,
                        "startup_seconds": startup,
                        "cruby_over_spinel": medians["cruby"] / medians["spinel"],
                        "yjit_over_spinel": medians["cruby_yjit"] / medians["spinel"],
                        "output": expected}
        print(name, json.dumps(result[name]), flush=True)
        (ROOT / "evidence/benchmark.json").write_text(json.dumps(result, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["compile", "bench", "all"], default="all")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    manifest = {"spinel_sha": run(["git", "-C", ROOT / "spinel", "rev-parse", "HEAD"], "spinel-sha")["stdout"].strip(),
                "roundhouse_sha": "b28b17b68d1fc879c506765cdc18142518544494",
                "ruby": run(["ruby", "--version"], "ruby-version")["stdout"].strip(),
                "spinel_version": run([SPINEL, "--version"], "spinel-version")["stdout"].strip(),
                "cc": run(["cc", "--version"], "cc-version")["stdout"].strip(),
                "platform": platform.platform(), "machine": platform.machine(),
                "compile_flags": "default -O2; default int overflow raise; no compiler source changes",
                "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    assert "ruby 4.0.7 " in manifest["ruby"], manifest
    (ROOT / "evidence/environment.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if args.phase in ["compile", "all"]:
        compile_cases()
    if args.phase in ["bench", "all"]:
        benchmark(args.repeats)


if __name__ == "__main__":
    main()
