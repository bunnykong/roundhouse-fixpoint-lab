"""Check witness values against the control and candidate types recorded for their rows.

Reads the JSON lines printed by the witness programs. Admission uses the F61 runtime-set
relation in tools/probe/runtime_sets.py with the census's rules for unions and containers.
Exits 0 only if every value has its recorded type, the control type admits it and the
candidate type rejects it. Python 3.9+, standard library only; starts no analyzer.
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'tools' / 'probe'))
import runtime_sets as sets  # noqa: E402

sets.VAR_TOP = True  # a raw type variable admits every value


def normalize(t):
    if isinstance(t, list):
        return [normalize(x) for x in t]
    if not isinstance(t, dict):
        return t
    if t.get('kind') == 'class' and t.get('id') == 'Time':
        return {'kind': 'time'}
    if t.get('kind') == 'class' and t.get('id', '').startswith('Arel::Nodes::'):
        return {'kind': 'class', 'id': 'Arel::Node', 'args': []}
    return {k: normalize(v) for k, v in t.items()}


def admits(t, value):
    t, value = normalize(t), normalize(value)
    if sets.top(t) or sets.empty(value):
        return True
    if value['kind'] == 'union':
        return all(admits(t, v) for v in value['variants'])
    if t['kind'] == 'union':
        return any(admits(v, value) for v in t['variants'])
    if t['kind'] == value['kind'] == 'hash':
        return admits(t['key'], value['key']) and admits(t['value'], value['value'])
    if t['kind'] == value['kind'] == 'array':
        return admits(t['elem'], value['elem'])
    if t['kind'] == value['kind'] == 'class' and t.get('id') == value.get('id'):
        return len(t.get('args', [])) == len(value.get('args', [])) and all(
            admits(a, b) for a, b in zip(t.get('args', []), value.get('args', [])))
    try:
        return sets.covers(t, value)
    except KeyError:
        return None


def main(paths):
    if not paths:
        print('usage: check.py WITNESS_OUTPUT.jsonl ...')
        return 2
    rows = {r['census_id']: r for r in json.loads((HERE.parent / 'losses.json').read_text())['rows']}
    failures = 0
    for path in paths:
        for line in Path(path).read_text().splitlines():
            obs = json.loads(line)
            row = rows[obs['row']]
            recorded = any(obs['type'] == o['type'] for o in row['observations'])
            control, candidate = admits(row['control'], obs['type']), admits(row['candidate'], obs['type'])
            ok = recorded and control is True and candidate is False
            failures += not ok
            print(f"{obs['row']:6} {row['family']:32} {obs['inspect'][:48]:48} "
                  f"recorded={recorded} control={control} candidate={candidate} "
                  f"{'LOSS reproduced' if ok else 'MISMATCH'}")
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
