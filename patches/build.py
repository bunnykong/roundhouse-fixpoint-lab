#!/usr/bin/env python3
"""Build one independent experiment on the pinned Roundhouse source."""
import argparse
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "b28b17b68d1fc879c506765cdc18142518544494"


def build(name, check_only=False):
    patch = ROOT / "patches" / (name + ".diff")
    if name != "baseline" and not patch.is_file():
        raise ValueError("Unknown configuration: " + name)
    source = ROOT / "_work" / ("roundhouse-" + name)
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "fetch", "--depth=1",
                        "https://github.com/rubys/roundhouse.git", BASE], check=True)
        subprocess.run(["git", "-C", str(source), "checkout", "-q", "--detach", "FETCH_HEAD"], check=True)
        if name != "baseline":
            subprocess.run(["git", "-C", str(source), "apply", "--check", str(patch)], check=True)
            subprocess.run(["git", "-C", str(source), "apply", str(patch)], check=True)
    head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if head != BASE:
        raise ValueError("Build source has the wrong commit")
    if check_only:
        return source
    subprocess.run(["cargo", "build", "--locked", "--release", "--bin", "roundhouse"], cwd=source,
                   env=dict(os.environ, CARGO_BUILD_JOBS="4"), check=True)
    return source / "target/release/roundhouse"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("configuration")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    print(build(args.configuration, args.check_only).relative_to(ROOT))


if __name__ == "__main__":
    main()
