"""Rust DefaultHasher (SipHash-1-3, zero keys) and the observer's explicit Hash encodings.

The analyzer's type hashes are native observations. This module reconciles the table/vector/map/digest hashes
from those observed component hashes; it does not invent Python hashes in place of native fingerprints.
"""
import struct
MASK=(1<<64)-1
def _rot(x,n): return ((x<<n)|(x>>(64-n)))&MASK
def sip(data):
    state=[0x736f6d6570736575,0x646f72616e646f6d,0x6c7967656e657261,0x7465646279746573]
    def turn():
        a,b,c,d=state
        a=(a+b)&MASK;b=_rot(b,13);b^=a;a=_rot(a,32)
        c=(c+d)&MASK;d=_rot(d,16);d^=c
        a=(a+d)&MASK;d=_rot(d,21);d^=a
        c=(c+b)&MASK;b=_rot(b,17);b^=c;c=_rot(c,32)
        state[:]=[a,b,c,d]
    for i in range(0,len(data)//8*8,8):
        m=int.from_bytes(data[i:i+8],'little');state[3]^=m;turn();state[0]^=m
    tail=data[len(data)//8*8:]
    b=(len(data)&255)<<56 | int.from_bytes(tail,'little')
    state[3]^=b;turn();state[0]^=b;state[2]^=255
    for _ in range(3):turn()
    return state[0]^state[1]^state[2]^state[3]
def u64(x): return struct.pack('<Q',x)
def string(x): return x.encode()+b'\xff'
def vec(values): return u64(len(values))+b''.join(u64(v) for v in values)
def mapping(values): return u64(len(values))+b''.join(string(k)+u64(v) for k,v in sorted(values.items()))
def names(values):
    if values!=sorted(set(values)): raise ValueError('names are not a sorted set')
    return sip(u64(len(values))+b''.join(string(v) for v in values))
def ir_vector(rows):
    return u64(len(rows))+b''.join(struct.pack('<IIIQQ',*r) for r in rows)
def ir_row(row):
    span=row['span']; return [span['file'],span['start'],span['end'],row['hash'],row['note']]
def reconcile(raw, header):
    parts=header['parts'];inventory=header['components']
    for entry, keys in inventory['params'].items():
        expected=[entry+'['+str(i)+']' for i in range(len(keys))]
        if set(keys)!=set(expected): raise ValueError('noncontiguous parameter vector')
        value=sip(vec([raw['params',k]['hash'] for k in expected]))
        if value!=parts['params'][entry]: raise ValueError('parameter vector hash mismatch')
    def bindings(part, prefix, keys):
        return {k[len(prefix):]:raw[part,k]['hash'] for k in keys if k.startswith(prefix)}
    for entry, keys in inventory['controller_bindings'].items():
        expanded=bindings('controller_bindings',entry+':binding:',keys)
        if len(expanded)!=len(keys): raise ValueError('malformed binding component key')
        value=sip(mapping(expanded))
        if value!=parts['controller_bindings'][entry]: raise ValueError('controller binding hash mismatch')
    cache_methods=header.get('cache_binding_methods')
    if not isinstance(cache_methods,dict) or set(cache_methods)!=set(parts['controller_cache']):
        raise ValueError('cache binding method inventory missing')
    for entry, keys in inventory['controller_cache'].items():
        methods=cache_methods[entry]
        if not isinstance(methods,list) or methods!=sorted(set(methods)): raise ValueError('cache method inventory')
        bs={m:sip(mapping(bindings('controller_cache',entry+'#'+m+':binding:',keys))) for m in methods}
        bodies={}
        covered=set()
        for key in keys:
            row=raw['controller_cache',key]
            if row.get('empty_cache'):
                if key!=entry+'#[empty]' or row['hash']!=parts['controller_cache'][entry]: raise ValueError('empty cache marker')
                covered.add(key);continue
            if 'root' in row:
                root=row['root'];prefix=entry+'#'
                if not root.startswith(prefix) or not root.endswith(':body'): raise ValueError('cache body root')
                method=root[len(prefix):-len(':body')]
                bodies.setdefault(method,[]).append(ir_row(row));covered.add(key)
            elif any(key.startswith(entry+'#'+m+':binding:') for m in methods):covered.add(key)
        if covered!=set(keys): raise ValueError('cache components not covered by shape')
        bodies={m:sip(ir_vector(rows)) for m,rows in bodies.items()}
        if sip(mapping(bs)+mapping(bodies))!=parts['controller_cache'][entry]:raise ValueError('cache hash mismatch')
    for (part,key),row in raw.items():
        if part=='block_values':
            n=row['names'];value=sip(b''.join(u64(names(n[k])) for k in ('block_value_methods','relation_derived','materializing_scopes')))
        elif part=='copies':
            n=row['names']
            value=names(n['host']) if key.startswith('host ') else sip(u64(names(n['instance']))+u64(names(n['class'])))
        else:continue
        if value!=row['hash']:raise ValueError('structural names hash mismatch')
    for table, entries in parts.items():
        if format(sip(mapping(entries)),'016x')!=header['digests'][table]:raise ValueError('table digest mismatch '+table)
    if format(sip(ir_vector(header['ir'])),'016x')!=header['digests']['ir']:raise ValueError('IR digest mismatch')
