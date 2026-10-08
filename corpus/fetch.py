#!/usr/bin/env python3
"""Acquire only the five public repositories at their exact commit pins."""
import argparse
import json
from pathlib import Path
import subprocess
from common import LAB_ROOT, ROOT, inventory, write_json
from lock import locked


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Check existing clones without downloading.")
    args = parser.parse_args()
    with locked():
        pins = json.loads((ROOT / "apps.json").read_text())
        manifest = json.loads((ROOT / "MANIFEST.json").read_text())
        for pin in pins:
            path = LAB_ROOT / pin["path"]
            if not path.exists():
                if args.verify:
                    raise SystemExit("Missing clone: " + pin["id"])
                path.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "init", "-q", str(path)], check=True)
                git(path, "remote", "add", "origin", pin["repository_url"])
                git(path, "fetch", "--depth=1", "origin", pin["commit"])
                git(path, "checkout", "-q", "--detach", "FETCH_HEAD")
            if not (path / ".git").is_dir() or git(path, "rev-parse", "HEAD") != pin["commit"]:
                raise SystemExit("Wrong commit: " + pin["id"])
            if git(path, "status", "--porcelain", "--untracked-files=all"):
                raise SystemExit("Changed input: " + pin["id"])
            digest, files = inventory(path)
            item = next(i for i in manifest["inputs"] if i["id"] == pin["id"])
            if item.get("tree_sha256") and item["tree_sha256"] != digest:
                raise SystemExit("Changed tree: " + pin["id"])
            item.update(tree_sha256=digest, git_tree=git(path, "rev-parse", "HEAD^{tree}"), file_count=len(files))
            print(pin["id"], pin["commit"], "verified", flush=True)
        write_json(ROOT / "MANIFEST.json", manifest)


if __name__ == "__main__":
    main()
