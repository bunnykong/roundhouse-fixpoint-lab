#!/usr/bin/env python3
"""Run each repro in both orders and show what changes. Python 3.9+, standard library only.

Usage: python3 -B check.py ROUNDHOUSE [--record]

ROUNDHOUSE is a binary built from upstream main. Each pair under repros/ has two variants that differ only in
the order of two methods, two files or two filters. Both are copied to a temporary directory and run through
`roundhouse check --continue --no-hotspots .` and `roundhouse --target ruby --allow-unsupported . -o OUT`.
The script prints each order's exit code, diagnostics and watched signatures, says whether the orders differ,
and compares every result with recorded.json, which upstream main 2cd9e5d9 and 958b48fa both reproduce. It exits
1 if any result differs from the recording; a main that fixes a shape prints SAME for it and fails the check.
--record rewrites recorded.json from the given binary instead.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ORDERS = ('as-written', 'swapped')
# Signatures to compare besides the diagnostics: shape 2 shows its difference only in the getter's type.
WATCH = {'2-ivar-index-write': ['Bag#t'], '9-filter-ivars': ['P.show']}


def run(binary, app):
    env = dict(os.environ, LC_ALL='C')
    chk = subprocess.run([binary, 'check', '--continue', '--no-hotspots', '.'], cwd=app, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    out = app.parent / (app.name + '-rbs')
    subprocess.run([binary, '--target', 'ruby', '--allow-unsupported', '.', '-o', str(out)], cwd=app, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600, check=True)
    roots = (os.path.realpath(app) + '/', str(app) + '/')
    diagnostics = sorted(line.replace(roots[0], '').replace(roots[1], '').strip() for line in chk.stdout.splitlines()
                         if re.search(r'(error|warning)\[', line))
    signatures = {}
    for f in sorted((out / 'sig' / 'app').rglob('*.rbs')):
        owner = None
        for line in f.read_text().splitlines():
            m = re.match(r'\s*(?:class|module) ([\w:]+)', line)
            if m:
                owner = m.group(1)
            m = re.match(r'\s*def (self\.)?([\w?!=]+): (.*)$', line)
            if m and owner:
                signatures[owner + ('.' if m.group(1) else '#') + m.group(2)] = m.group(3)
    return chk.returncode, diagnostics, signatures


def main():
    args = [a for a in sys.argv[1:] if a != '--record']
    if len(args) != 1:
        print(__doc__)
        return 2
    binary = str(Path(args[0]).resolve())
    record = '--record' in sys.argv
    recorded = json.loads((HERE / 'recorded.json').read_text()) if not record else {}
    results, failures = {}, []
    for pair in sorted(p.name for p in (HERE / 'repros').iterdir() if p.is_dir()):
        got = {}
        with tempfile.TemporaryDirectory() as tmp:
            for order in ORDERS:
                app = Path(tmp) / order
                shutil.copytree(HERE / 'repros' / pair / order, app)
                code, diagnostics, signatures = run(binary, app)
                got[order] = dict(exit=code, diagnostics=diagnostics,
                                  signatures={k: signatures.get(k) for k in WATCH.get(pair, [])})
        got['differs'] = got['as-written'] != got['swapped']
        results[pair] = got
        print(f"== {pair}: {'DIFFERS' if got['differs'] else 'SAME'} across the two orders")
        for order in ORDERS:
            r = got[order]
            print(f'  {order}: exit {r["exit"]}')
            for line in r['diagnostics']:
                print(f'    {line}')
            for k, v in r['signatures'].items():
                print(f'    {k}: {v}')
        if not record and got != recorded.get(pair):
            failures.append(pair)
    if record:
        (HERE / 'recorded.json').write_text(json.dumps(results, indent=1) + '\n')
        print('recorded.json written')
        return 0
    if failures or set(recorded) != set(results):
        print('differs from recorded.json: ' + ', '.join(failures or sorted(set(recorded) ^ set(results))))
        return 1
    print('every result matches recorded.json: shapes 2, 5, 6, 7 and 9 change with order; the two scope checks do not')
    return 0


if __name__ == '__main__':
    sys.exit(main())
