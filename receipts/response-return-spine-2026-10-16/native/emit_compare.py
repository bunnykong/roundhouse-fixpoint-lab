#!/usr/bin/env python3
"""E1 receipt: emit every input x target with ONE binary, RH_RESPONSE_RETURNS unset ("off") and =1 ("on").

usage: emit_compare.py --bin BIN --checkout ROUNDHOUSE_CHECKOUT --out DIR
The checkout supplies fixtures/ (real-blog and store must be generated there; see its DEVELOPMENT.md).
The four repro apps come from this kit. Ambient RH_*/ROUNDHOUSE_* variables are cleared.
Writes DIR/{off,on}/<input>/<target>/{tree,stderr.txt} and DIR/compare.json, which verdict.py reads.
"""
import argparse
import concurrent.futures as cf
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess

KIT = Path(__file__).resolve().parent
FIXTURES = ["tiny-blog", "tiny-api", "tiny-blog-uuid", "real-blog", "store", "roda-blog", "gem-capabilities/historical/base"]
REPROS = ["use-app", "tail-app", "void-app", "probe-app"]
TARGETS = ["crystal", "csharp", "elixir", "go", "kotlin", "python", "rust", "swift", "typescript",
           "typescript-worker", "ruby", "jruby", "spinel"]
BASE_ENV = {k: v for k, v in os.environ.items() if not k.startswith(("RH_", "ROUNDHOUSE_"))}
ARMS = {"off": {"RH_RESPONSE_RETURNS": "0"}, "on": {"RH_RESPONSE_RETURNS": "1"}}


def inputs(checkout):
    frontier = KIT.parents[2]
    campfire = json.loads((frontier / "phase2/observers/apps.json").read_text())["campfire"]["path"]
    return [(f.replace("/", "-"), str(Path(checkout) / "fixtures" / f)) for f in FIXTURES] + \
           [(r, str(KIT / "repro" / r)) for r in REPROS] + [("campfire", str(frontier / campfire))]


def changed_lines(a, b):
    """Removed and added lines of one file, without context, capped at 40."""
    if a is None or b is None:
        return ["(only " + ("on" if a is None else "off") + ")"]
    diff = difflib.unified_diff(a.read_text(errors="replace").splitlines(), b.read_text(errors="replace").splitlines(), n=0, lineterm="")
    return [l for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---"))][:40]


def run(binary, checkout, out, arm, name, path, target):
    dest = out / arm / name / target
    dest.mkdir(parents=True, exist_ok=True)
    env = dict(BASE_ENV, **ARMS[arm])
    proc = subprocess.run([binary, "--target", target, path, "-o", str(dest / "tree")], cwd=checkout,
                          env=env, capture_output=True, text=True, timeout=900)
    err = proc.stderr.replace(str(dest), "<OUT>").replace(str(KIT), "<KIT>").replace(str(checkout), "<CHECKOUT>")
    (dest / "stderr.txt").write_text(err)
    return (arm, name, target), (proc.returncode, hashlib.sha256(err.encode()).hexdigest())


def tree(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob("*")) if p.is_file()} if path.exists() else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", required=True)
    ap.add_argument("--checkout", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out, checkout = Path(a.out).resolve(), Path(a.checkout).resolve()
    for need in ("real-blog", "store"):
        if not (checkout / "fixtures" / need).is_dir():
            raise SystemExit(f"fixtures/{need} is missing in {checkout}; generate it first")
    jobs = [(a.bin, checkout, out, arm, n, p, t) for arm in ARMS for n, p in inputs(checkout) for t in TARGETS]
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        done = dict(pool.map(lambda j: run(*j), jobs))
    rows = []
    for n, _ in inputs(checkout):
        for t in TARGETS:
            (eo, so), (en, sn) = done[("off", n, t)], done[("on", n, t)]
            to, tn = tree(out / "off" / n / t / "tree"), tree(out / "on" / n / t / "tree")
            changed = sorted(k for k in set(to) | set(tn) if to.get(k) != tn.get(k))
            base = {arm: out / arm / n / t / "tree" for arm in ARMS}
            rows.append(dict(input=n, target=t, files=[len(to), len(tn)], exit=[eo, en], identical_files=to == tn,
                             identical_stderr=so == sn, identical=to == tn and so == sn and eo == en,
                             changed_files=changed[:50],
                             changed_lines={k: changed_lines(base["off"] / k if k in to else None,
                                                             base["on"] / k if k in tn else None) for k in changed[:10]}))
    sha = hashlib.sha256(Path(a.bin).read_bytes()).hexdigest()
    rec = {"arms": {"off": ARMS["off"], "on": ARMS["on"]}, "binary_sha256": {"off": sha, "on": sha},
           "checkout": str(checkout), "pairs": len(rows), "identical": sum(r["identical"] for r in rows), "rows": rows}
    (out / "compare.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if k != "rows"}))


if __name__ == "__main__":
    main()
