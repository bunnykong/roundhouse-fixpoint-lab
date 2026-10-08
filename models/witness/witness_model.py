#!/usr/bin/env python3
"""A small model of Roundhouse's state-entry iteration, for comparing three policies on
public synthetic recursion shapes:

  none   - no widening (pre-#528 behaviour)
  untie  - main's #528 rule: cut a strict subterm equal to the entry's previous value
           (or a union holding all of its variants) to Untyped; returns only
  rule   - prototype rule: fold strict subterms that `cover` a compound value in the
           entry's history (last 3), confirmed on 2 consecutive rounds; revisit -> join;
           cut to a sticky WIDENED marker

Types: ('str',) ('int',) ('sym',) ('untyped',) ('var',) ('widened',) ('array', T)
('hash', K, V) ('union', (T, ...)). union_of mirrors body/mod.rs:2608: flatten, dedupe,
one Array and one Hash spine per union, merged pointwise, canonical sort.
This models the lattice operations, not Roundhouse's body typer.
"""
import sys

STR, INT, SYM, U, VAR, W = ('str',), ('int',), ('sym',), ('untyped',), ('var',), ('widened',)


def arr(t): return ('array', t)
def hsh(k, v): return ('hash', k, v)


def union_of(a, b):
    if a == b:
        return a
    if a == W or b == W:          # the marker is top in state joins: absorbing
        return W
    if a[0] == 'array' and b[0] == 'array':
        return arr(union_of(a[1], b[1]))
    if a[0] == 'hash' and b[0] == 'hash':
        return hsh(union_of(a[1], b[1]), union_of(a[2], b[2]))
    out = []
    for t in (a, b):
        push(t, out)
    out.sort(key=repr)
    return out[0] if len(out) == 1 else ('union', tuple(out))


def push(t, out):
    if t == W or W in out:
        out[:] = [W]
        return
    if t[0] == 'union':
        for v in t[1]:
            push(v, out)
        return
    for i, e in enumerate(out):
        if t[0] == 'array' and e[0] == 'array':
            out[i] = arr(union_of(e[1], t[1]))
            return
        if t[0] == 'hash' and e[0] == 'hash':
            out[i] = hsh(union_of(e[1], t[1]), union_of(e[2], t[2]))
            return
    if t not in out:
        out.append(t)


def union_many(*ts):
    r = ts[0]
    for t in ts[1:]:
        r = union_of(r, t)
    return r


def size(t):
    if t[0] == 'array': return 1 + size(t[1])
    if t[0] == 'hash': return 1 + size(t[1]) + size(t[2])
    if t[0] == 'union': return 1 + sum(size(v) for v in t[1])
    return 1


def depth(t):
    if t[0] == 'array': return 1 + depth(t[1])
    if t[0] == 'hash': return 1 + max(depth(t[1]), depth(t[2]))
    if t[0] == 'union': return 1 + max(depth(v) for v in t[1])
    return 0


def compound(t):
    return t[0] in ('array', 'hash', 'union')


def arms(t):
    return t[1] if t[0] == 'union' else (t,)


def covers(s, o):
    """s covers o: union_of(o, s) == s with rigid leaves (DESIGN.md 3.2)."""
    if s == o or s == W:          # the marker covers everything (top)
        return True
    if o[0] == 'union':
        return all(covers(s, v) for v in o[1])
    if s[0] == 'union':
        return any(covers(w, o) for w in s[1])
    if o[0] == 'array' and s[0] == 'array':
        return covers(s[1], o[1])
    if o[0] == 'hash' and s[0] == 'hash':
        return covers(s[1], o[1]) and covers(s[2], o[2])
    return False


def fold(t, hist, top=True, cut=W):
    """Replace maximal strict subterms covering a compound history value by the cut value."""
    if not top and any(compound(h) and covers(t, h) for h in hist):
        return cut, True
    if t[0] == 'array':
        e, f = fold(t[1], hist, False, cut)
        return arr(e), f
    if t[0] == 'hash':
        k, f1 = fold(t[1], hist, False, cut)
        v, f2 = fold(t[2], hist, False, cut)
        return hsh(k, v), f1 or f2
    if t[0] == 'union':
        parts = [fold(v, hist, False, cut) for v in t[1]]
        if not any(f for _, f in parts):
            return t, False
        return union_many(*[p for p, _ in parts]), True
    return t, False


def untie(t, prior, top=True):
    """Main's #528 cut: a strict subterm equal to prior, or a union holding all of prior's
    variants, becomes Untyped (harvest_return.rs:60)."""
    if not compound(prior):
        return t
    if not top:
        if t == prior:
            return U
        if prior[0] == 'union' and t[0] == 'union' and all(v in t[1] for v in prior[1]):
            rest = [untie(v, prior, False) for v in t[1] if v not in prior[1]]
            return union_many(*(rest + [U]))
    if t[0] == 'array':
        return arr(untie(t[1], prior, False))
    if t[0] == 'hash':
        return hsh(untie(t[1], prior, False), untie(t[2], prior, False))
    if t[0] == 'union':
        return union_many(*[untie(v, prior, False) for v in t[1]])
    return t


def to_untyped(t):
    """What the typer sees in the side-table variant: the marker read as Untyped."""
    if t == W: return U
    if t[0] == 'array': return arr(to_untyped(t[1]))
    if t[0] == 'hash': return hsh(to_untyped(t[1]), to_untyped(t[2]))
    if t[0] == 'union': return union_many(*[to_untyped(v) for v in t[1]])
    return t


def run(name, eqs, init, policy, rounds=36, budget=200_000):
    state = dict(init)
    hist = {e: [v] for e, v in state.items()}
    seen = {e: {v} for e, v in state.items()}
    acc = {e: False for e in state}
    pending = {e: False for e in state}
    for r in range(1, rounds + 1):
        seen_by_typer = {e: to_untyped(v) for e, v in state.items()} if policy == 'side' else state
        new = {e: f(seen_by_typer) for e, f in eqs.items()}
        nxt = {}
        for e, n in new.items():
            old = state[e]
            if policy == 'untie' and e.startswith('R'):
                n = untie(n, old)
            elif policy in ('rule', 'rule_u', 'side') and n != old:
                if acc[e] or (n in seen[e]):
                    n = union_of(old, n)
                    acc[e] = True
                folded, did = fold(n, hist[e][-3:], cut=(U if policy == 'rule_u' else W))
                if did and (pending[e] or acc[e]):
                    n = folded
                    acc[e] = True
                pending[e] = did
            nxt[e] = n
        if nxt == state:
            return f"{name:9s} {policy:5s}: converged after {r - 1} rounds; " + \
                   "; ".join(f"{e}: size {size(v)} depth {depth(v)}" for e, v in state.items())
        state = nxt
        for e, v in state.items():
            hist[e].append(v)
            seen[e].add(v)
        if max(size(v) for v in state.values()) > budget:
            return f"{name:9s} {policy:5s}: GROWS, size > {budget} at round {r}"
    return f"{name:9s} {policy:5s}: no fixpoint in {rounds} rounds; " + \
           "; ".join(f"{e}: size {size(v)} depth {depth(v)}" for e, v in state.items())


def f(r):  # sanitize-like body: Str | Array[r] | Hash[Sym, r]
    return union_many(STR, arr(r), hsh(SYM, r))


def g(r):  # a different body in the cycle, so the methods' values differ
    return union_many(INT, arr(r), hsh(STR, r))


def h(r):
    return union_many(SYM, arr(r), hsh(INT, r))


CASES = {
    # self-recursion (#528's chatwoot case): converges under untie on main
    'self': ({'R': lambda s: f(s['R'])}, {'R': U}),
    # prototype (2,2): walk_0 -> walk_1 -> walk_0, Array + Hash branches
    'cycle2': ({'R0': lambda s: f(s['R1']), 'R1': lambda s: g(s['R0'])}, {'R0': U, 'R1': U}),
    'cycle3': ({'R0': lambda s: f(s['R1']), 'R1': lambda s: g(s['R2']), 'R2': lambda s: h(s['R0'])},
               {'R0': U, 'R1': U, 'R2': U}),
    # merge2: a second Array spine merges into the recursive Array branch
    'merge2': ({'R': lambda s: union_many(STR, arr(s['R']), arr(arr(STR)), hsh(U, s['R']))}, {'R': U}),
    # param: deep({inner: acc, size: n}) with external site {} -> Hash spine merge
    'param': ({'P': lambda s: union_of(hsh(VAR, VAR), hsh(SYM, union_of(s['P'], INT)))}, {'P': VAR}),
}

if __name__ == '__main__':
    for name, (eqs, init) in CASES.items():
        for policy in ('none', 'untie', 'rule_u', 'rule', 'side'):
            print(run(name, eqs, init, policy))
