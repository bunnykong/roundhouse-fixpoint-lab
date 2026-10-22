#!/usr/bin/env python3
"""Print proved rows with their source context, for reading proofs by hand. Python 3.9+, standard library only.

Usage: python3 -B audit.py RULE [N] [SEED]. RULE is a checker rule (such as `guard` or `returns`), a pattern or a
dump node kind. Source files are read from APPS, as for checker.rb (default: the lab's corpus/apps).
"""
import json
import lzma
import os
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
APPS = Path(os.environ.get('APPS', HERE.parent.parent / 'corpus' / 'apps'))


def jsonl(path):
    return [json.loads(line) for line in lzma.decompress(path.read_bytes()).decode().splitlines()]


def main():
    rule = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    seed = sys.argv[3] if len(sys.argv) > 3 else 'audit'
    rows = {r['id']: r for r in jsonl(HERE / 'rows.jsonl.xz')}
    pick = [v for v in jsonl(HERE / 'verdicts.jsonl.xz') if v['verdict'] == 'PROVED' and
            (rule in v['rules'] or rule == v['pattern'] or rule == rows[v['id']]['node'])]
    random.Random(seed).shuffle(pick)
    print(f'{len(pick)} proofs with {rule}; showing {min(n, len(pick))}')
    for v in sorted(pick[:n], key=lambda x: x['id']):
        r = rows[v['id']]
        lines = (APPS / r['app'] / v['file']).read_bytes().decode('utf-8', 'replace').split('\n')
        ln = v['line']
        print(f"==== {v['id']} {r['node']} {v['prism_node']} rules={v['rules']}")
        print(f"     {r['app']}/{v['file']}:{ln}")
        print(f"     value={v['value']}\n     type ={v['type'][:200]}")
        for i in range(max(0, ln - 9), min(len(lines), ln + 3)):
            print(('  >> ' if i + 1 == ln else '     ') + lines[i][:150])


if __name__ == '__main__':
    main()
