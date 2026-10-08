#!/usr/bin/env python3
"""Check every independent snapshot against a clean pinned checkout."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "b28b17b68d1fc879c506765cdc18142518544494"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=ROOT / "_work/apply-check")
    args = parser.parse_args()
    source = args.checkout.resolve()
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "fetch", "--depth=1",
                        "https://github.com/rubys/roundhouse.git", BASE], check=True)
        subprocess.run(["git", "-C", str(source), "checkout", "-q", "--detach", "FETCH_HEAD"], check=True)
    command = ["git", "-C", str(source)]
    if subprocess.check_output(command + ["rev-parse", "HEAD"], text=True).strip() != BASE:
        raise SystemExit("Wrong baseline commit")
    if subprocess.check_output(command + ["status", "--porcelain"], text=True).strip():
        raise SystemExit("Checkout must be clean")
    rows = []
    for patch in sorted((ROOT / "patches").glob("*.diff")):
        result = subprocess.run(command + ["apply", "--check", str(patch)], capture_output=True, text=True)
        rows.append({"patch": patch.name, "base": BASE, "exit_code": result.returncode})
        print(patch.name, "PASS" if result.returncode == 0 else "FAIL")
        if result.returncode:
            print(result.stderr)
    print(json.dumps({"patches": len(rows), "failures": sum(r["exit_code"] != 0 for r in rows)}))
    return 1 if any(r["exit_code"] for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
