#!/usr/bin/env python3
"""Manual C specialization of unchanged generated drivers, isolated from the compiler."""
import argparse
import difflib
import json
import os
import re
import statistics
import subprocess
from experiment import CASES, ROOT, run

FUNCTIONS = {"canonical": ["sp_canonical"], "cycle": ["sp_walk_0", "sp_walk_1"],
             "tree_sum": ["sp_rb_sum_leaves"]}


def function_span(source, function):
    pattern = re.compile(r"static (?:inline )?sp_RbVal " + function + r"\(sp_RbVal lv_value\) \{")
    matches = list(pattern.finditer(source))
    assert len(matches) == 1, (function, len(matches))
    match = matches[0]
    depth = 1
    i = match.end()
    while depth:
        ch = source[i]
        if source[i:i + 2] == "/*":
            i = source.index("*/", i + 2) + 2
            continue
        if source[i:i + 2] == "//":
            i = source.index("\n", i + 2)
            continue
        if ch in ['"', "'"]:
            quote = ch
            i += 1
            while source[i] != quote:
                i += 2 if source[i] == "\\" else 1
            i += 1
            continue
        depth += (ch == "{") - (ch == "}")
        i += 1
    return match.start(), i


def specialize(source, case):
    common = (ROOT / "fastpaths/common.h").read_text()
    replacement = (ROOT / "fastpaths" / (case + ".h")).read_text()
    first = True
    for function in FUNCTIONS[case]:
        start, end = function_span(source, function)
        source = source[:start] + (common + "\n" + replacement if first else "") + source[end:]
        first = False
    return source


def cc(source, dest, label):
    record = run(["cc", "-O2", "-ffp-contract=off", "-DSP_INT_OVERFLOW_MODE_RAISE", "-Wno-all",
                  "-Wno-unknown-warning-option", "-Wno-alloc-size-larger-than", "-Wno-format-truncation",
                  "-I", ROOT / "spinel/lib", source, ROOT / "spinel/lib/libspinel_rt.a",
                  "-lm", "-Wl,-dead_strip", "-o", dest], label)
    if record["returncode"]:
        raise RuntimeError(record["stderr"])
    return record


def allocation(case, engine, iterations):
    dest = ROOT / "evidence" / (case + "-" + engine + "-alloc-" + str(iterations) + ".txt")
    record = subprocess.run([str(ROOT / "bin" / (case + "_" + engine)), str(iterations).zfill(3)], cwd=ROOT,
                            env=dict(os.environ, TMPDIR=str(ROOT / "tmp"), SPINEL_ALLOC_REPORT=str(dest)),
                            capture_output=True, text=True, timeout=60)
    assert record.returncode == 0, record.stderr
    totals = {"objects": 0, "object_payload_bytes": 0, "named_counts": {}}
    for line in dest.read_text().splitlines():
        if line.startswith("alloc;"):
            name, count = line[6:].rsplit(" ", 1)
            name = "unnamed-scanner" if name.startswith("scan_") else name
            totals["objects"] += int(count)
            totals["named_counts"][name] = totals["named_counts"].get(name, 0) + int(count)
        elif line.startswith("# bytes "):
            totals["object_payload_bytes"] += int(line.rsplit(" ", 1)[1])
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--alloc-only", action="store_true")
    args = parser.parse_args()
    if args.alloc_only:
        result_path = ROOT / "evidence/fastpaths.json"
        results = json.loads(result_path.read_text())
        for case in CASES:
            for engine in ["control", "fast"]:
                small, large = allocation(case, engine, 1), allocation(case, engine, 100)
                results[case]["allocation"][engine] = {
                    "one": small, "hundred": large, "argv": ["001", "100"],
                    "objects_per_iteration": (large["objects"] - small["objects"]) / 99,
                    "payload_bytes_per_iteration": (large["object_payload_bytes"] - small["object_payload_bytes"]) / 99}
        result_path.write_text(json.dumps(results, indent=2) + "\n")
        return
    results = {}
    for case in CASES:
        base = ROOT / "generated" / (case + ".c")
        original = base.read_text()
        native = specialize(original, case)
        dest = ROOT / "generated" / (case + "_fast.c")
        dest.write_text(native)
        (ROOT / "evidence" / (case + "-fast.diff")).write_text(
            "".join(difflib.unified_diff(original.splitlines(True), native.splitlines(True),
                                         fromfile=base.name, tofile=dest.name)))
        cc(base, ROOT / "bin" / (case + "_control"), case + "-control-cc")
        cc(dest, ROOT / "bin" / (case + "_fast"), case + "-fast-cc")
    # Build phase is complete before any measured runtime; timed children run serially.
    for case, iterations in CASES.items():
        binaries = {engine: ROOT / "bin" / (case + "_" + engine) for engine in ["control", "fast"]}
        expected = run([ROOT / "bin" / case, "1"], case + "-fast-oracle")["stdout"]
        samples = {engine: [] for engine in binaries}
        for engine, binary in binaries.items():
            warm = run([binary, str(iterations)], case + "-" + engine + "-warm")
            assert warm["returncode"] == 0 and warm["stdout"] == expected, warm
        for i in range(7):
            order = ["control", "fast"] if i % 2 == 0 else ["fast", "control"]
            for engine in order:
                record = run([binaries[engine], str(iterations)], case + "-" + engine + "-sample")
                assert record["returncode"] == 0 and record["stdout"] == expected, record
                samples[engine].append(record["seconds"])
        alloc = {}
        for engine in binaries:
            small = allocation(case, engine, 1)
            large = allocation(case, engine, 100)
            alloc[engine] = {"one": small, "hundred": large,
                             "objects_per_iteration": (large["objects"] - small["objects"]) / 99,
                             "payload_bytes_per_iteration":
                                 (large["object_payload_bytes"] - small["object_payload_bytes"]) / 99}
        medians = {engine: statistics.median(values) for engine, values in samples.items()}
        results[case] = {"iterations": iterations, "seconds": samples, "median_seconds": medians,
                         "control_over_fast": medians["control"] / medians["fast"],
                         "allocation": alloc, "output": expected,
                         "scope": "manually specialized C over existing boxed representation; unchanged generated driver"}
        print(case, json.dumps(results[case]), flush=True)
        (ROOT / "evidence/fastpaths.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
