import json,re
from pathlib import Path

def load(path, keys=None):
    rows = {}
    references = {}
    with path.open() as f:
        fp = json.loads(next(f))
        for line in f:
            v = json.loads(line)
            k = (v['part'], v['key'])
            if k[0] == 'returns': references['return:' + k[1]] = v['ty']
            if k[0] == 'side_table': references[k[1]] = v['ty']
            if keys is not None and k not in keys: continue
            assert k not in rows, k
            rows[k] = v
    def resolve(t, seen, proofs):
        if isinstance(t, list): return [resolve(v,seen,proofs) for v in t]
        if not isinstance(t,dict): return t
        if t.get('kind') == 'rec':
            key=t['slot'];lookup=key
            match=re.fullmatch(r'Some\(Ret \{ class: ClassId\(Symbol\(("(?:\\.|[^"])*")\)\), method: Symbol\(("(?:\\.|[^"])*")\), class_side: (true|false) \}\)',key)
            if match:
                c,m,side=match.groups();lookup='return:'+json.loads(c)+('.' if side=='true' else '#')+json.loads(m)
            if lookup not in references or key in seen:
                proofs[key]={'unexpanded': 'cycle' if key in seen else 'missing'}
                return t
            value=references[lookup]
            proofs[key]={'lookup':lookup,'value':value}
            return resolve(value,seen|{key},proofs)
        return {k:resolve(v,seen,proofs) for k,v in t.items()}
    if keys is not None:
        for r in rows.values():
            proofs={}
            r['resolved_ty']=resolve(r.get('ty'),set(),proofs)
            r['reference_expansions']=proofs
    return fp, rows


def sig(row):
    if row is None: return None
    return (row.get('hash'), row.get('note'), row.get('module'))
