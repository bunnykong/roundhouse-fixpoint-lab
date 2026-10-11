#!/usr/bin/env python3
"""Run under the workshop shared lock; preserve full diagnostics and exits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", choices=("base", "candidate"))
    parser.add_argument("label")
    parser.add_argument("selection")
    parser.add_argument("--expected-exit", type=int, default=0)
    parser.add_argument("--default", action="store_true")
    parser.add_argument("--integration")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tree = root / "week" / "bound" / args.tree
    output = tree.parent / "results" / args.label
    if output.with_suffix(".json").exists() or output.with_suffix(".log").exists():
        raise SystemExit("Use a fresh output label: " + args.label)
    env = os.environ.copy()
    env.update(RBENV_VERSION="3.4.4", CARGO_TARGET_DIR=str(tree / "target-laws"))
    command = ["cargo", "+1.98.1", "test", "--locked"]
    command += ["--test", args.integration] if args.integration else ["--lib"]
    if not args.default:
        command.append(args.selection)
    command += ["--", "--nocapture", "--test-threads=1"]
    if not args.default:
        command.append("--include-ignored")
    with output.with_suffix(".log").open("w") as log:
        result = subprocess.run(command, cwd=str(tree), env=env, stdout=log, stderr=subprocess.STDOUT)
    text = output.with_suffix(".log").read_text()
    counts = re.findall(r"test result: .*? (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out", text)
    properties = []
    for line in text.splitlines():
        match = re.search(r"WRITER-LAW (.*?) \| (.*?) \| (PASS|FAIL) \| (\d+) checks(?: \| (\d+) nodes \| (.*))?", line)
        if match:
            name, law, status, checks, nodes, witness = match.groups()
            properties.append(dict(writer=name, law=law, result=status, checks=int(checks),
                                   witness_nodes=int(nodes) if nodes else None, witness=witness))
    binaries = re.findall(r"Running (?:unittests .*?|tests/\S+) \((.*?)\)", text)
    binary_hashes = {p: digest(tree / p) for p in binaries if (tree / p).is_file()}
    receipt = dict(tree=args.tree, label=args.label, selection=args.selection, default=args.default,
                   integration=args.integration,
                   condition="reflective-writer-bound-20261011-bf2f052f", command=command, cwd=str(tree),
                   exit=result.returncode, expected_exit=args.expected_exit,
                   source_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(tree), text=True).strip(),
                   source_diff_sha256=hashlib.sha256(subprocess.check_output(["git", "diff", "HEAD"], cwd=str(tree))).hexdigest(),
                   added_source_sha256={p: digest(tree / p) for p in subprocess.check_output(
                       ["git", "ls-files", "--others", "--exclude-standard", "--", "src/"], cwd=str(tree), text=True).splitlines()
                       if (tree / p).is_file()},
                   environment={k: v for k, v in sorted(env.items()) if k.startswith(("RH_", "ROUNDHOUSE_", "CARGO_", "RBENV_", "RUST_", "SOUND_"))},
                   log_sha256=digest(output.with_suffix(".log")), binary_sha256=binary_hashes,
                   results=[dict(zip(("passed", "failed", "ignored", "measured", "filtered"), map(int, row))) for row in counts],
                   properties=properties, timed_measurement=False,
                   timing_scope="Cargo/test-harness durations are shared-host diagnostics, not performance measurements.")
    output.with_suffix(".json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: receipt[k] for k in ("tree", "label", "exit", "results", "binary_sha256")}, indent=2), flush=True)
    if result.returncode != args.expected_exit or not counts or sum(int(row[0]) + int(row[1]) for row in counts) == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
