#!/usr/bin/env python3
"""Build, fetch, and measure a named public condition with one command."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def main():
    configs = json.loads((ROOT / "patches/configurations.json").read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("configuration", choices=sorted(configs))
    parser.add_argument("--binary", help="Use an already-built executable.")
    parser.add_argument("--set", choices=["micro", "apps", "all"], default="all")
    parser.add_argument("--label")
    args = parser.parse_args()
    if args.binary:
        binary = Path(args.binary).resolve()
    else:
        spec = importlib.util.spec_from_file_location("patch_build", ROOT / "patches/build.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        binary = module.build(configs[args.configuration]["patch"])
    if args.set in ["apps", "all"]:
        subprocess.run(["sh", str(ROOT / "corpus/fetch.sh")], check=True)
    command = [sys.executable, "-B", str(ROOT / "corpus/run.py"), "--binary", str(binary), "--set", args.set]
    if args.label:
        command += ["--label", args.label]
    for key, value in configs[args.configuration]["env"].items():
        command += ["--env", key + "=" + value]
    if args.configuration == "baseline":
        command += ["--reference-micro", "--condition", "public-corpus-v1"]
    return subprocess.call(command)


if __name__ == "__main__":
    sys.exit(main())
