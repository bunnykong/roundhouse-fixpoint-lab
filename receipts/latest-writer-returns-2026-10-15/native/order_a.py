#!/usr/bin/env python3
"""Mine an research condition return ledger: publication sequences for named methods, and descents.

A descent is a `replace` event whose current value is not >= its superseded value in a
chosen order. Orders:
  A  untyped (non-pending) is top and absorbs; pending/Var is bottom; arms by inclusion.
  B  untyped is an ordinary arm; pending is bottom; Var is bottom.
  B2 like B but Var is an ordinary arm (evidence).
"""
import json, sys, collections

def is_pending(t):
    return t.get('kind') == 'untyped' and t.get('reasons') == ['Pending']
def is_untyped(t):
    return t.get('kind') == 'untyped' and not is_pending(t)
def arms(t):
    return list(t['variants']) if t.get('kind') == 'union' else [t]
def atom_eq(a, b):
    return json.dumps(strip(a), sort_keys=True) == json.dumps(strip(b), sort_keys=True)
def strip(t):
    if isinstance(t, dict):
        return {k: strip(v) for k, v in t.items() if k != 'reasons'}
    if isinstance(t, list):
        return [strip(x) for x in t]
    return t
def leq(a, b, order):
    # a <= b ?
    if is_pending(a) or a.get('kind') == 'bottom': return True
    if a.get('kind') == 'var' and order != 'B2': return True
    if order == 'A' and any(is_untyped(x) for x in arms(b)): return True
    if a.get('kind') == 'union':
        return all(leq(x, b, order) for x in a['variants'])
    for y in arms(b):
        if leq_arm(a, y, order): return True
    return False
def leq_arm(a, y, order):
    ka, ky = a.get('kind'), y.get('kind')
    if ka == 'untyped' and ky == 'untyped': return True
    if ka == 'var' and ky == 'var': return True
    if ka != ky: return False
    if ka == 'array': return leq(a['elem'], y['elem'], order)
    if ka == 'hash': return leq(a['key'], y['key'], order) and leq(a['value'], y['value'], order)
    if ka == 'tuple':
        return len(a['elems']) == len(y['elems']) and all(leq(p, q, order) for p, q in zip(a['elems'], y['elems']))
    if ka == 'class':
        return a.get('id') == y.get('id') and len(a.get('args', [])) == len(y.get('args', [])) and all(leq(p, q, order) for p, q in zip(a.get('args', []), y.get('args', [])))
    if ka == 'record':
        fa, fy = a.get('row', {}).get('fields', {}), y.get('row', {}).get('fields', {})
        return all(k in fy and leq(v, fy[k], order) for k, v in fa.items())
    if ka == 'fn': return atom_eq(a, y)
    return atom_eq(a, y)

def main():
    path = sys.argv[1]; names = sys.argv[2].split(',') if len(sys.argv) > 2 else []
    out_prefix = sys.argv[3] if len(sys.argv) > 3 else None
    seqs = collections.defaultdict(list)
    descents = {o: collections.Counter() for o in ('A', 'B', 'B2')}
    descent_examples = {o: [] for o in ('A', 'B', 'B2')}
    nrep = 0; nfirst = 0; writers = set(); snapshot = None
    with open(path) as f:
        for line in f:
            e = json.loads(line)
            ev = e.get('event')
            if ev == 'replace':
                nrep += 1; w = e['writer']; writers.add(w)
                cur = e['current']['native_ty']; sup = e['superseded']
                if sup is None: nfirst += 1
                if any(n in w for n in names):
                    seqs[w].append((e['version'], sup['debug'] if sup else None, e['current']['debug']))
                if sup is not None:
                    s = sup['native_ty']
                    for o in ('A', 'B', 'B2'):
                        if not leq(s, cur, o):
                            descents[o][w] += 1
                            if len(descent_examples[o]) < 400:
                                descent_examples[o].append({'writer': w, 'version': e['version'], 'from': sup['debug'], 'to': e['current']['debug']})
            elif ev == 'snapshot':
                snapshot = e
    print('replace events', nrep, 'first writes', nfirst, 'writers with events', len(writers))
    for o in ('A', 'B', 'B2'):
        c = descents[o]
        print('order', o, 'descending events', sum(c.values()), 'writers with a descent', len(c))
    if snapshot:
        rows = {r['slot']: r for r in snapshot['slots']}
        print('snapshot slots', len(rows), 'writers', len(snapshot['writers']), 'routes', len(snapshot['routes']))
        for n in names:
            for slot, r in rows.items():
                if n in slot:
                    st = r['stored']['debug'] if r.get('stored') else None
                    print('SLOT', slot, '| members', len(r['members']), '| aggregate', r['aggregate']['debug'], '| stored', st)
    for w, s in seqs.items():
        print('WRITER', w)
        for v, a, b in s:
            print('   v%d: %s  ==>  %s' % (v, a, b))
    if out_prefix:
        json.dump({'descents': {o: dict(descents[o]) for o in descents}, 'examples': descent_examples,
                   'sequences': {w: s for w, s in seqs.items()}}, open(out_prefix + '.json', 'w'), indent=1)

if __name__ == '__main__':
    main()
