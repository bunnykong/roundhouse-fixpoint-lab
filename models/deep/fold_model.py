#!/usr/bin/env python3
"""Regular-type workbench: fold self-containing unfoldings into exact
recursive types inside Roundhouse's round-based state-entry iteration, and compare with
the fold-by-origin references (ref1, ref2) and with prototype rule M1.

witness_model.py (prototype, imported unchanged) is the M1 baseline. Types here are regular
trees represented as head-deterministic tree automata: a node table (root = state 0) where a
Union state has at most one arm per head (Array, Hash, each leaf): the normal form union_of
(body/mod.rs:2608) imposes by merging spines. Tuples stay distinct arms, as union_of keeps them.

  canonicalize = subset construction (flatten unions, merge same-head arms pointwise)
                 + Moore partition refinement (bisimulation minimization) + DFS numbering,
                 so equal regular types have equal node tables (interned: equality is O(1))
  covers(a, b) = simulation a >= b, coinductive, one visit per state pair
  join(a, b)   = canonicalize(Union{a, b}): union_of lifted to cycles
  fold(n, H)   = for every strict sub-state d of n that covers (leaves rigid) a compound
                 value in the entry's history H (evidence that d is an earlier unfolding of
                 this entry), redirect d to the least general of its ancestors that covers it
                 with the seed as bottom; canonicalize. The redirect ties the knot.
  widen_k(n)   = ARTMC-style backstop: merge states with equal k-truncations (finite range)
  ref1 / ref2  = the fold by origin: a slot read in a recursive component is a
                 reference Rec(slot); projections unfold one level (ref1 copies the level,
                 ref2 returns Rec(slot, path), a position = an automaton state); the slot
                 terms are knot-tied into regular types every round.
  kleene(k)    = ground truth: the depth-k truncation of the plain Kleene chain once it is
                 stable (the least solution to depth k); solve() gives the full regular
                 solution for shapes without projections (knot-tying, Courcelle).

Run: python3 fold_model.py            (table for every shape and policy)
     python3 fold_model.py --trace SHAPE [POLICY]
"""
import sys
import itertools
from collections import defaultdict

sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
import witness_model as m1  # noqa: E402  (prototype model, unchanged)

LEAF_NAME = {'str': 'String', 'int': 'Integer', 'sym': 'Symbol', 'nil': 'nil', 'untyped': 'untyped',
             'var': 'Var', 'widened': 'W', 'bot': '⊥', 'cut': '…'}
HEAD_ORDER = {'leaf': 0, 'array': 1, 'hash': 2, 'tuple': 3, 'union': 4}
COMPOUND = ('array', 'hash', 'tuple', 'union')


# ----------------------------------------------------------------------------- automata
class Reg:
    """A canonical regular type: node table (root 0), DFS-numbered, minimized, interned."""
    __slots__ = ('nodes', 'parent', '_h')

    def __init__(self, nodes, parent):
        self.nodes, self.parent, self._h = nodes, parent, hash(nodes)

    def __eq__(self, o):
        return isinstance(o, Reg) and self.nodes == o.nodes

    def __hash__(self):
        return self._h

    def __repr__(self):
        return show(self)

    @property
    def head(self):
        return self.nodes[0][0]

    def states(self):
        return len(self.nodes)

    def cyclic(self):
        """True when some state reaches itself (DAG sharing alone is not a cycle)."""
        state = {}

        def go(i):
            if state.get(i) == 1:
                return True
            if i in state:
                return False
            state[i] = 1
            if any(go(c) for c in children(self.nodes[i])):
                return True
            state[i] = 2
            return False
        return go(0)

    def arms(self):
        """Root arm states (the root itself when it is not a union)."""
        return self.nodes[0][1] if self.head == 'union' else (0,)


_INTERN = {}


def intern(nodes, parent):
    r = _INTERN.get(nodes)
    if r is None:
        r = _INTERN[nodes] = Reg(nodes, tuple(parent))
    return r


def children(node):
    k = node[0]
    if k == 'leaf':
        return ()
    if k == 'array':
        return (node[1],)
    if k == 'hash':
        return (node[1], node[2])
    return tuple(node[1])  # tuple, union


def remap(node, f):
    k = node[0]
    if k == 'leaf':
        return node
    if k == 'array':
        return ('array', f(node[1]))
    if k == 'hash':
        return ('hash', f(node[1]), f(node[2]))
    if k == 'tuple':
        return ('tuple', tuple(f(c) for c in node[1]))
    return ('union', frozenset(f(c) for c in node[1]))


def embed(G, reg):
    """Copy reg's table into graph G under fresh ids; return its root id."""
    base = len(G)
    for i, n in enumerate(reg.nodes):
        G[base + i] = remap(n, lambda c: base + c)
    return base


def flatten(G, states):
    """Non-union, non-bottom states reachable through union nodes only. An unguarded union
    cycle (X = X | ...) contributes nothing: least-fixpoint semantics."""
    out, seen, todo = set(), set(), list(states)
    while todo:
        s = todo.pop()
        if s in seen:
            continue
        seen.add(s)
        n = G[s]
        if n[0] == 'union':
            todo.extend(n[1])
        elif n != ('leaf', 'bot'):
            out.add(s)
    return out


def determinize(G, root):
    """Subset construction over the 'union = choice' automaton: one arm per head, same-head
    Array/Hash arms merged pointwise (union_of's spine merge), W absorbing, bottom identity."""
    H, memo, counter = {}, {}, itertools.count()

    def det(states):
        key = frozenset(flatten(G, states))
        if key in memo:
            return memo[key]
        r = next(counter)
        memo[key] = r
        arms = [G[s] for s in sorted(key)]
        if any(a == ('leaf', 'widened') for a in arms):
            H[r] = ('leaf', 'widened')
            return r
        if not arms:
            H[r] = ('leaf', 'bot')
            return r
        groups = defaultdict(list)
        for s in sorted(key):
            a = G[s]
            if a[0] == 'leaf':
                groups[('leaf', a[1])].append(a)
            elif a[0] == 'tuple':
                groups[('tuple', s)].append(a)      # tuples are not merged (as union_of)
            else:
                groups[(a[0],)].append(a)
        built = []
        for gkey in sorted(groups, key=repr):
            mem = groups[gkey]
            if gkey[0] == 'leaf':
                built.append(('leaf', gkey[1]))
            elif gkey[0] == 'array':
                built.append(('array', det([a[1] for a in mem])))
            elif gkey[0] == 'hash':
                built.append(('hash', det([a[1] for a in mem]), det([a[2] for a in mem])))
            else:
                built.append(('tuple', tuple(det([c]) for c in mem[0][1])))
        if len(built) == 1:
            H[r] = built[0]
        else:
            ids = []
            for b in built:
                i = next(counter)
                H[i] = b
                ids.append(i)
            H[r] = ('union', frozenset(ids))
        return r

    return H, det([root])


def reachable(H, root):
    seen, todo = set(), [root]
    while todo:
        s = todo.pop()
        if s in seen:
            continue
        seen.add(s)
        todo.extend(children(H[s]))
    return seen


def minimize(H, root):
    """Moore's partition refinement: bisimulation classes (exact on the head-deterministic
    part; a sound, possibly finer, equivalence on unmerged tuple arms)."""
    states = sorted(reachable(H, root))

    def head_sig(n):
        return (n[0], n[1]) if n[0] == 'leaf' else (n[0], len(children(n)))

    sigs = {}
    cls = {s: sigs.setdefault(head_sig(H[s]), len(sigs)) for s in states}
    ncls = len(sigs)
    while True:
        sig = {}
        for s in states:
            n = H[s]
            ch = tuple(sorted(cls[c] for c in n[1])) if n[0] == 'union' else tuple(cls[c] for c in children(n))
            sig[s] = (cls[s], ch)
        ids, new = {}, {}
        for s in states:
            new[s] = ids.setdefault(sig[s], len(ids))
        cls = new
        if len(ids) == ncls:
            return cls
        ncls = len(ids)


def canon_key(Q, c, depth=0):
    """Order key for union arms. Heads are distinct except for tuples, which can tie; ties are
    broken by a depth-bounded unfolding (enough for the model; the Tuple spine normalization
    of DESIGN.md 3.4 would make this unnecessary)."""
    n = Q[c]
    if n[0] == 'leaf':
        return (0, str(n[1]))
    if depth > 5:
        return (HEAD_ORDER[n[0]], len(children(n)))
    return (HEAD_ORDER[n[0]], len(children(n)), tuple(canon_key(Q, x, depth + 1) for x in ordered(Q, n, depth + 1)))


def ordered(Q, n, depth=0):
    if n[0] == 'union':
        return sorted(n[1], key=lambda c: canon_key(Q, c, depth))
    return list(children(n))


def number(Q, root):
    order, parent = {}, []

    def visit(c, par):
        if c in order:
            return
        order[c] = len(order)
        parent.append(par)
        for ch in ordered(Q, Q[c]):
            visit(ch, order[c])

    visit(root, None)
    nodes = [None] * len(order)
    for c, i in order.items():
        n = Q[c]
        if n[0] == 'union':
            nodes[i] = ('union', tuple(order[x] for x in ordered(Q, n)))
        else:
            nodes[i] = remap(n, lambda x: order[x])
    return intern(tuple(nodes), parent)


def canonicalize(G, root):
    for _ in range(8):
        H, r = determinize(G, root)
        cls = minimize(H, r)
        Q = {}
        for s, c in cls.items():
            if c not in Q:
                n = H[s]
                Q[c] = ('union', frozenset(cls[x] for x in n[1])) if n[0] == 'union' else remap(n, lambda x: cls[x])
        degenerate = any(n[0] == 'union' and len(n[1]) < 2 for n in Q.values())
        G, root = Q, cls[r]
        if not degenerate:
            return number(Q, root)
    raise RuntimeError('canonicalize did not settle')


# ------------------------------------------------------------------------- constructors
def leaf(tag):
    return canonicalize({0: ('leaf', tag)}, 0)


STR, INT, SYM, NIL, U, VAR, W, BOT = (leaf(t) for t in ('str', 'int', 'sym', 'nil', 'untyped', 'var', 'widened', 'bot'))


def arr(t):
    G = {}
    r = embed(G, t)
    G[len(G)] = ('array', r)
    return canonicalize(G, len(G) - 1)


def hsh(k, v):
    G = {}
    rk, rv = embed(G, k), embed(G, v)
    G[len(G)] = ('hash', rk, rv)
    return canonicalize(G, len(G) - 1)


def tup(*ts):
    G = {}
    rs = [embed(G, t) for t in ts]
    G[len(G)] = ('tuple', tuple(rs))
    return canonicalize(G, len(G) - 1)


def union_many(*ts):
    G = {}
    rs = [embed(G, t) for t in ts]
    G[len(G)] = ('union', frozenset(rs))
    return canonicalize(G, len(G) - 1)


def union_of(a, b):
    return union_many(a, b)


join = union_of


def sub(reg, state):
    """The regular type rooted at `state` of reg."""
    if state == 0:
        return reg
    return canonicalize({i: n for i, n in enumerate(reg.nodes)}, state)


# -------------------------------------------------------------------- covers (simulation)
def sim(a, i, b, j, bottom=()):
    """a[i] >= b[j]: every tree of b[j] is a tree of a[i]. Leaves are rigid except the tags in
    `bottom` (the seed ⊥; in the side-table variant also the Untyped shown at a cut), which
    sit below everything. Head-determinism forces the matching, so the visited pairs are the
    only candidate simulation: one visit per pair."""
    A, B = a.nodes, b.nodes
    visited = set()

    def go(p, q):
        if (p, q) in visited:
            return True
        visited.add((p, q))
        np_, nq = A[p], B[q]
        if np_ == ('leaf', 'widened'):
            return True
        if nq[0] == 'leaf' and (nq[1] in bottom or ('cut' in bottom and is_cut(nq[1]))):
            return True
        if nq[0] == 'union':
            return all(go(p, c) for c in nq[1])
        parms = np_[1] if np_[0] == 'union' else (p,)
        if nq[0] == 'leaf':
            return any(A[r] == nq for r in parms)
        if nq[0] == 'array':
            rs = [r for r in parms if A[r][0] == 'array']
            return bool(rs) and go(A[rs[0]][1], nq[1])
        if nq[0] == 'hash':
            rs = [r for r in parms if A[r][0] == 'hash']
            return bool(rs) and go(A[rs[0]][1], nq[1]) and go(A[rs[0]][2], nq[2])
        rs = [r for r in parms if A[r][0] == 'tuple' and len(A[r][1]) == len(nq[1])]
        for r in rs:  # existential over unmerged tuple arms: snapshot the hypothesis set
            snap = set(visited)
            if all(go(x, y) for x, y in zip(A[r][1], nq[1])):
                return True
            visited.clear()
            visited.update(snap)
        return False

    return go(i, j)


def covers(a, b, bottom=()):
    return sim(a, 0, b, 0, bottom)


# --------------------------------------------------------------------------- the fold
def compound(t):
    return t.head in COMPOUND


def arm_heads(reg, i):
    """The top-level shape of a state: its arm heads (leaf tags, array, hash, tuple arity)."""
    out = set()
    for a in (reg.nodes[i][1] if reg.nodes[i][0] == 'union' else (i,)):
        n = reg.nodes[a]
        out.add(('leaf', n[1]) if n[0] == 'leaf' else ('tuple', len(n[1])) if n[0] == 'tuple' else (n[0],))
    return frozenset(out)


def fold(n, hist, bottom=('bot',), cut=None, guard=True, generalize=False):
    """Fold n against the entry's history.

    Witness: a state d under at least one constructor (an arm of the root union covering the
    previous value is growth by union, not nesting) that covers, with rigid leaves, a compound
    value in the history: d is an earlier unfolding of this entry.
    Target (cut=None): among d's ancestors that cover d with the seed as bottom, the one with
    the fewest arms beyond d's own (the same pattern, anti-unification), nearest on ties; d is
    redirected to it, which ties the knot. With cut='widened', d becomes the marker (rule M1
    in this framework). Returns (folded, witnesses folded, witnesses without a target)."""
    redirect, orphans = {}, 0
    hist = [h for h in hist if compound(h)]
    guarded = [False] * n.states()
    for d in range(1, n.states()):
        p = n.parent[d]
        guarded[d] = guarded[p] or n.nodes[p][0] in ('array', 'hash', 'tuple')
    for d in range(1, n.states()):
        if n.nodes[d][0] not in COMPOUND or (guard and not guarded[d]):
            continue
        if not any(sim(n, d, h, 0) for h in hist):
            continue
        if cut is not None:
            redirect[d] = ('cut',)
            continue
        cands, a = [], n.parent[d]
        while a is not None:
            if a not in redirect and sim(n, a, n, d, bottom):
                cands.append(a)
            a = n.parent[a]
        if not cands:
            orphans += 1
            if generalize:                      # supercompilation's msg step: no instance -> abstract
                redirect[d] = ('cut',)
                GENERALIZED[0] += 1
            continue
        # the target is an earlier occurrence of d's own pattern: same arm set; a covering
        # ancestor with more arms (the root, late in the chain) is a different pattern and
        # would over-approximate, so without a same-shaped ancestor d waits (orphan)
        shape = arm_heads(n, d)
        same = [a for a in cands if arm_heads(n, a) == shape]
        if not same:
            orphans += 1
            if generalize:                      # least generalization: the nearest covering ancestor
                redirect[d] = cands[0]
                GENERALIZED[0] += 1
            continue
        redirect[d] = same[0]
    if not redirect:
        return n, 0, orphans
    G = {i: node for i, node in enumerate(n.nodes)}
    if cut is not None or any(t == ('cut',) for t in redirect.values()):
        G[len(G)] = ('leaf', cut if cut is not None else 'widened')
        cut_state = len(G) - 1

    def target(s):
        while s in redirect:
            s = redirect[s]
            if s == ('cut',):
                return cut_state
        return s

    G = {i: remap(node, target) for i, node in G.items()}
    out = canonicalize(G, 0)
    SOUNDNESS[0] += 1
    if not sim(out, 0, n, 0, bottom):
        SOUNDNESS[1] += 1                      # T1 says this never happens
    return out, len(redirect), orphans


SOUNDNESS = [0, 0]  # folds checked, violations of fold(n) ⊒ n


def truncation(reg, i, k):
    """k-truncation of state i as a hashable finite tree: constructors deeper than k levels
    become 'cut'; leaves stay visible; unions do not count as a level."""
    n = reg.nodes[i]
    if n[0] == 'leaf':
        return n
    if n[0] == 'union':
        return ('union', frozenset(truncation(reg, c, k) for c in children(n)))
    if k == 0:
        return 'cut'
    return (n[0],) + tuple(truncation(reg, c, k - 1) for c in children(n))


def widen_k(n, k):
    """ARTMC-style backstop: merge all states sharing a k-truncation (a finite range), then
    determinize. Sound (adds arms only); bounds the state count, so it terminates anything."""
    groups = defaultdict(list)
    for i in range(n.states()):
        if n.nodes[i][0] in COMPOUND:
            groups[truncation(n, i, k)].append(i)
    merged = [g for g in groups.values() if len(g) > 1]
    if not merged:
        return n, 0
    G = {i: node for i, node in enumerate(n.nodes)}
    rep = {}
    for g in merged:
        u = len(G)
        G[u] = ('union', frozenset(g))
        for i in g:
            rep[i] = u
    for i in range(n.states()):
        G[i] = remap(n.nodes[i], lambda c: rep.get(c, c))
    return canonicalize(G, rep.get(0, 0)), len(merged)


GENERALIZED = [0]  # orphan witnesses generalized by the fold-gen policy (extended workbench)


def tree_size(reg):
    """Nodes of the unfolded tree (what main stores: no sharing). Finite for acyclic types."""
    memo = {}

    def go(i):
        if i in memo:
            return memo[i]
        n = reg.nodes[i]
        memo[i] = 1 + sum(go(c) for c in children(n))
        return memo[i]
    return go(0)


def embeds(h, n, bottom_var=False):
    """Homeomorphic embedding h ⊴ n on the tree unfoldings (acyclic values: Kleene iterates).
    Coupling: same head, children embed pairwise (union arms: each arm of h in some arm of n).
    Diving: h embeds in a child of n. With bottom_var, ⊥ is a variable: it embeds in anything."""
    H, N = h.nodes, n.nodes
    memo = {}

    def go(p, q):
        key = (p, q)
        if key in memo:
            return memo[key]
        memo[key] = False
        hp, nq = H[p], N[q]
        r = False
        if hp[0] == 'leaf':
            r = (bottom_var and hp[1] == 'bot') or hp == nq
        elif hp[0] == nq[0]:
            if hp[0] == 'union':
                r = all(any(go(a, b) for b in nq[1]) for a in hp[1])
            elif hp[0] == 'tuple':
                r = len(hp[1]) == len(nq[1]) and all(go(a, b) for a, b in zip(hp[1], nq[1]))
            else:
                r = all(go(a, b) for a, b in zip(children(hp), children(nq)))
        if not r:
            r = any(go(p, c) for c in children(nq))
        memo[key] = r
        return r
    return go(0, 0)


def msg_generalize(h, n, fill_bottom=False):
    """Supercompilation's generalization step on types: the most specific generalization of h and n
    (Plotkin/Reynolds anti-unification), with every mismatch replaced by the absorbing marker W.
    Union arms are matched by head; arms only n has are new information and are kept. With
    fill_bottom, a hole whose earlier side is the pending seed ⊥ is filled with n's side (a pending
    value getting resolved is not growth), so only resolved structure can be generalized."""
    G, memo, copied = {}, {}, {}

    def put(node):
        G[len(G)] = node
        return len(G) - 1

    def go(p, q):
        if (p, q) in memo:
            return memo[(p, q)]
        hp, nq = h.nodes[p], n.nodes[q]
        if fill_bottom and hp == ('leaf', 'bot'):
            r = copy(q)
        elif hp[0] == 'leaf' and nq[0] == 'leaf':
            r = put(nq if hp == nq else ('leaf', 'widened'))
        elif hp[0] == nq[0] == 'array':
            r = put(('array', go(hp[1], nq[1])))
        elif hp[0] == nq[0] == 'hash':
            r = put(('hash', go(hp[1], nq[1]), go(hp[2], nq[2])))
        elif hp[0] == nq[0] == 'tuple' and len(hp[1]) == len(nq[1]):
            r = put(('tuple', tuple(go(a, b) for a, b in zip(hp[1], nq[1]))))
        elif hp[0] == 'union' and nq[0] == 'union':
            by_head = {arm_heads(h, a): a for a in hp[1]}
            kids = []
            for b in nq[1]:
                a = by_head.get(arm_heads(n, b))
                kids.append(go(a, b) if a is not None else copy(b))
            r = put(('union', frozenset(kids)))
        else:  # different constructors (a leaf or a constructor against a union included): a variable
            r = put(('leaf', 'widened'))
        memo[(p, q)] = r
        return r

    def copy(q):
        if q in copied:
            return copied[q]
        nq = n.nodes[q]
        r = put(remap(nq, copy)) if nq[0] != 'union' else put(('union', frozenset(copy(c) for c in nq[1])))
        copied[q] = r
        return r

    return canonicalize(G, go(0, 0))


def depth(reg):
    """Constructor depth (unions don't count); cycles contribute nothing beyond the back edge."""
    def go(i, path):
        if i in path:
            return 0
        n = reg.nodes[i]
        if n[0] == 'leaf':
            return 0
        step = 0 if n[0] == 'union' else 1
        return step + max(go(c, path | {i}) for c in children(n))
    return go(0, frozenset())


def trunc(reg, k):
    """Truncation at k constructor levels as a canonical finite type (cut leaf below)."""
    G = {}

    def go(i, d):
        n = reg.nodes[i]
        if n[0] not in ('leaf', 'union') and d == k:
            G[len(G)] = ('leaf', 'cut')
            return len(G) - 1
        if n[0] == 'leaf':
            G[len(G)] = n
            return len(G) - 1
        kids = [go(c, d + (0 if n[0] == 'union' else 1)) for c in children(n)]
        G[len(G)] = ('array', kids[0]) if n[0] == 'array' else ('hash', kids[0], kids[1]) if n[0] == 'hash' \
            else ('tuple', tuple(kids)) if n[0] == 'tuple' else ('union', frozenset(kids))
        return len(G) - 1

    return canonicalize(G, go(0, 0))


# --------------------------------------------------------------------- projections
def is_ref(t):
    n = t.nodes[0]
    return n[0] == 'leaf' and isinstance(n[1], tuple) and n[1][0] == 'ref'


def mkref(slot, path=()):
    tag = ('ref', slot, tuple(path))
    LEAF_NAME[tag] = f"Rec({slot}{''.join('.' + (s if isinstance(s, str) else 'tup%d' % s[1]) for s in path)})"
    return leaf(tag)


def ref_parts(t):
    tag = t.nodes[0][1]
    return tag[1], tag[2]


def select(reg, state, sel):
    """Children of state `state` reached by selector sel (hv, hk, ae, ('ti', i)), through unions."""
    out = []
    arms = reg.nodes[state][1] if reg.nodes[state][0] == 'union' else (state,)
    for a in arms:
        n = reg.nodes[a]
        if sel == 'hv' and n[0] == 'hash':
            out.append(n[2])
        elif sel == 'hk' and n[0] == 'hash':
            out.append(n[1])
        elif sel == 'ae' and n[0] == 'array':
            out.append(n[1])
        elif isinstance(sel, tuple) and n[0] == 'tuple' and sel[1] < len(n[1]):
            out.append(n[1][sel[1]])
    return out


def proj(reg, sel):
    """Structural projection of a concrete regular type: the sub-type at the selector (⊥ if none)."""
    kids = select(reg, 0, sel)
    if not kids:
        return BOT
    return union_many(*[sub(reg, c) for c in kids])


def leaf_arms(reg):
    """Narrowing to the non-container arms (the `else` of `case value when Hash … when Array`)."""
    ls = [sub(reg, a) for a in reg.arms() if reg.nodes[a][0] == 'leaf' and reg.nodes[a][1] != 'bot']
    return union_many(*ls) if ls else BOT


class Typer:
    """The constructor and projection vocabulary the shape equations use. mode 'concrete'
    operates on regular types; 'ref1' and 'ref2' are the fold-by-origin levels: a read
    of a recursive slot is Rec(slot); a projection unfolds one level (ref1 copies that level
    from the slot's current term, ref2 returns Rec(slot, path))."""
    STR, INT, SYM, NIL, U, VAR = STR, INT, SYM, NIL, U, VAR
    arr, hsh, tup, union_of, union_many = staticmethod(arr), staticmethod(hsh), staticmethod(tup), \
        staticmethod(union_of), staticmethod(union_many)

    def __init__(self, mode='concrete', seed=BOT):
        self.mode, self.R0, self.P0 = mode, seed, seed
        self.terms, self.denot, self.recursive = {}, {}, set()

    # --- environment the equations read
    def env(self, state):
        if self.mode == 'concrete':
            return state
        return {e: (mkref(e) if e in self.recursive else self.denot[e]) for e in state}

    # --- one level of unfolding of a reference
    def unfold_term(self, ref, guard=0):
        """ref1: the current term of the slot at the reference's path (one level copied)."""
        slot, path = ref_parts(ref)
        cur = [self.terms[slot]] if slot in self.terms else []
        for sel in path:
            nxt = []
            for t in cur:
                for c in select(t, 0, sel):
                    s = sub(t, c)
                    nxt.append(self.unfold_term(s, guard + 1) if is_ref(s) and guard < 4 else s)
            cur = nxt
        parts = [t for t in cur if t != BOT]
        return union_many(*parts) if parts else BOT

    def unfold_denot(self, ref):
        """The previous round's denotation at the reference's path (structure questions)."""
        slot, path = ref_parts(ref)
        cur = self.denot.get(slot, BOT)
        for sel in path:
            cur = proj(cur, sel)
        return cur

    def _proj(self, x, sel):
        if is_ref(x):
            if self.mode == 'ref2':
                slot, path = ref_parts(x)
                return mkref(slot, path + (sel,))
            return self._proj(self.unfold_term(x), sel)
        kids = select(x, 0, sel)
        parts = []
        for c in kids:
            s = sub(x, c)
            parts.append(self._proj_through(s))
        # Extension: a reference that is an arm of a union (elem(Rec(S) | nil)) projects too; the
        # original copy dropped it (⊥), which made ref2 inexact on 2 of 120 fuzzed systems
        for a in x.arms():
            s = sub(x, a)
            if is_ref(s):
                parts.append(self._proj(s, sel))
        parts = [p for p in parts if p != BOT]
        return union_many(*parts) if parts else BOT

    def _proj_through(self, s):
        return s  # a selected child (may itself be a reference leaf: kept as such)

    def hvalue(self, x):
        return self._proj(x, 'hv')

    def hkey(self, x):
        return self._proj(x, 'hk')

    def elem(self, x):
        return self._proj(x, 'ae')

    def leaves(self, x):
        """Narrowing: the leaf arms. On a reference, unfold through the denotation."""
        if is_ref(x):
            return leaf_arms(self.unfold_denot(x))
        parts = []
        for a in x.arms():
            s = sub(x, a)
            if is_ref(s):
                parts.append(leaf_arms(self.unfold_denot(s)))
            elif x.nodes[a][0] == 'leaf' and x.nodes[a][1] != 'bot':
                parts.append(s)
        parts = [p for p in parts if p != BOT]
        return union_many(*parts) if parts else BOT

    def has_hash(self, x):
        d = self.unfold_denot(x) if is_ref(x) else x
        return any(d.nodes[a][0] == 'hash' for a in d.arms()) or \
            any(is_ref(sub(d, a)) and self.has_hash(sub(d, a)) for a in d.arms())

    def merge(self, x, y):
        """Hash#merge: Hash[K_x | K_y, V_x | V_y] when x has a Hash arm, else ⊥ (no Hash yet)."""
        if not self.has_hash(x):
            return BOT
        return hsh(union_of(self.hkey(x), self.hkey(y)), union_of(self.hvalue(x), self.hvalue(y)))


# ------------------------------------------------------------------------- knot-tying
def tie(terms):
    """Resolve a system of terms with reference leaves into regular types: Rec(slot) is the
    slot's root, Rec(slot, path) the set of states reached by following the path from it,
    through unions and through other references at their current resolution. Resolutions
    are computed as a least fixpoint (they only grow), so a reference seen through another
    reference is never resolved against a stale assumption; an unguarded regress is ⊥."""
    G, roots = {}, {}
    for e, t in terms.items():
        roots[e] = embed(G, t)
    refs = {s: n[1] for s, n in G.items() if n[0] == 'leaf' and isinstance(n[1], tuple) and n[1][0] == 'ref'}
    tags = set(refs.values())
    assign = {tag: frozenset() for tag in tags}

    def expand(states):
        out, seen, todo = set(), set(), list(states)
        while todo:
            s = todo.pop()
            if s in seen:
                continue
            seen.add(s)
            n = G[s]
            if n[0] == 'union':
                todo.extend(n[1])
            elif s in refs:
                todo.extend(assign[refs[s]])
            else:
                out.add(s)
        return out

    def follow(tag):
        slot, path = tag[1], tag[2]
        if slot not in roots:
            return frozenset()
        cur = {roots[slot]}
        for sel in path:
            nxt = set()
            for s in expand(cur):
                n = G[s]
                if sel == 'hv' and n[0] == 'hash':
                    nxt.add(n[2])
                elif sel == 'hk' and n[0] == 'hash':
                    nxt.add(n[1])
                elif sel == 'ae' and n[0] == 'array':
                    nxt.add(n[1])
                elif isinstance(sel, tuple) and n[0] == 'tuple' and sel[1] < len(n[1]):
                    nxt.add(n[1][sel[1]])
            cur = nxt
        return frozenset(expand(cur))

    changed = True
    while changed:
        changed = False
        for tag in tags:
            new = assign[tag] | follow(tag)
            if new != assign[tag]:
                assign[tag] = new
                changed = True
    for s, tag in refs.items():
        G[s] = ('union', assign[tag] - {s}) if assign[tag] - {s} else ('leaf', 'bot')
    return {e: canonicalize(dict(G), roots[e]) for e in terms}


def solve(eqs, T):
    """Ground truth for projection-free shapes: evaluate each equation on reference leaves and
    knot-tie (Courcelle: a guarded regular system has a unique regular solution)."""
    refs = {e: mkref(e) for e in eqs}
    return tie({e: f(refs) for e, f in eqs.items()})


def dependencies(eqs, T):
    """Which slots each equation reads (probe with a recording environment)."""
    deps = {}
    for e, f in eqs.items():
        read = set()

        class Rec(dict):
            def __getitem__(self, k):
                read.add(k)
                return BOT
        try:
            f(Rec())
        except Exception:
            pass
        deps[e] = read
    return deps


def recursive_slots(eqs, T):
    deps = dependencies(eqs, T)
    rec = set()
    for e in eqs:
        seen, todo = set(), list(deps[e])
        while todo:
            x = todo.pop()
            if x == e:
                rec.add(e)
                break
            if x in seen:
                continue
            seen.add(x)
            todo.extend(deps.get(x, ()))
    return rec


# ------------------------------------------------------------------------ views, printing
def view(reg, k, cut, slot=None):
    """Unfold reg, taking each back edge at most k-1 times along a path; the k-th occurrence of
    a state on the path becomes `cut`. k=1, cut=W is M1's shape. cut='cut' makes a leaf that
    remembers the slot and state it stands for (('cut', slot, state)): the side-table typer's
    view, whose cuts are references back into the stored μ-types (see resolve_cuts). That is
    Rec(slot, position): the side-table step, done right, is ref2."""
    G = {}

    def go(i, path):
        if path.count(i) >= k:
            G[len(G)] = ('leaf', ('cut', slot, i) if cut == 'cut' else cut)
            return len(G) - 1
        n = reg.nodes[i]
        if n[0] == 'leaf':
            G[len(G)] = n
            return len(G) - 1
        kids = [go(c, path + [i]) for c in children(n)]
        node = ('array', kids[0]) if n[0] == 'array' else ('hash', kids[0], kids[1]) if n[0] == 'hash' \
            else ('tuple', tuple(kids)) if n[0] == 'tuple' else ('union', frozenset(kids))
        G[len(G)] = node
        return len(G) - 1

    return canonicalize(G, go(0, []))


def resolve_cuts(n, stored):
    """Store step of the side table: every cut leaf ('cut', slot, i) in the typer's output n is
    state i of the stored μ-type of `slot` it was unfolded from; tie it back."""
    G = {}
    rn = embed(G, n)
    roots = {}
    for s in list(G):
        node = G[s]
        if node[0] == 'leaf' and isinstance(node[1], tuple) and node[1][0] == 'cut':
            _, slot, i = node[1]
            if slot not in roots:
                roots[slot] = embed(G, stored[slot])
            G[s] = ('union', frozenset([roots[slot] + i]))
    return canonicalize(G, rn)


def is_cut(tag):
    return tag == 'cut' or (isinstance(tag, tuple) and tag[0] == 'cut')


def show(reg):
    """A μ-term: back-edge targets are bound with μ; shared acyclic states are expanded."""
    nodes = reg.nodes
    targets = set()

    def scan(i, path):
        if i in path:
            targets.add(i)
            return
        for c in children(nodes[i]):
            scan(c, path + (i,))

    scan(0, ())
    names = {t: 'XYZVWT'[k % 6] for k, t in enumerate(sorted(targets))}

    def go(i, path):
        n = nodes[i]
        if i in path:
            return names[i]
        if n[0] == 'leaf':
            body = LEAF_NAME.get(n[1], str(n[1]))
        elif n[0] == 'array':
            body = f"Array[{go(n[1], path + (i,))}]"
        elif n[0] == 'hash':
            body = f"Hash[{go(n[1], path + (i,))}, {go(n[2], path + (i,))}]"
        elif n[0] == 'tuple':
            body = "[" + ", ".join(go(c, path + (i,)) for c in n[1]) + "]"
        else:
            body = " | ".join(go(c, path + (i,)) for c in n[1])
        if i in targets:
            return f"μ{names[i]}.({body})"
        return f"({body})" if n[0] == 'union' and path else body

    return go(0, ())


def show_rbs(reg, name='t'):
    """RBS: one alias per back-edge target (the root included), bodies inline otherwise."""
    nodes = reg.nodes
    targets = {0}

    def scan(i, path):
        if i in path:
            targets.add(i)
            return
        for c in children(nodes[i]):
            scan(c, path + (i,))

    scan(0, ())
    alias = {t: (name if k == 0 else f"{name}{k}") for k, t in enumerate(sorted(targets))}
    out = []

    def go(i, top):
        n = nodes[i]
        if i in alias and not top:
            return alias[i]
        if n[0] == 'leaf':
            return {'str': 'String', 'int': 'Integer', 'sym': 'Symbol', 'nil': 'nil', 'untyped': 'untyped',
                    'var': 'untyped', 'widened': 'untyped', 'bot': 'bot'}.get(n[1], 'untyped')
        if n[0] == 'array':
            return f"Array[{go(n[1], False)}]"
        if n[0] == 'hash':
            return f"Hash[{go(n[1], False)}, {go(n[2], False)}]"
        if n[0] == 'tuple':
            return "[" + ", ".join(go(c, False) for c in n[1]) + "]"
        return " | ".join(go(c, False) for c in n[1])

    for t in sorted(targets):
        out.append(f"type {alias[t]} = {go(t, True)}")
    return "\n".join(out)


def from_m1(t):
    """prototype tuple types -> Reg."""
    k = t[0]
    if k == 'array':
        return arr(from_m1(t[1]))
    if k == 'hash':
        return hsh(from_m1(t[1]), from_m1(t[2]))
    if k == 'union':
        return union_many(*[from_m1(v) for v in t[1]])
    return leaf(k)


def gradual_share(result, truth, k=4):
    """Share of the positions of truth (to depth k) that `result` types exactly. A position is
    gradual once W, or untyped standing in for structure, or a cut, sits at or above it."""
    total = exact = 0

    def go(ti, ri, d, gradual):
        nonlocal total, exact
        if d == k:
            return
        tn = truth.nodes[ti]
        if tn[0] == 'leaf' and tn[1] in ('bot', 'cut'):
            return
        total += 1
        rn = result.nodes[ri] if ri is not None else None
        if gradual or rn is None or rn == ('leaf', 'widened') or (rn == ('leaf', 'untyped') and tn != rn) \
                or rn[0] != tn[0] or (tn[0] == 'leaf' and rn != tn):
            gradual = True
        else:
            exact += 1
        if tn[0] == 'union':
            for c in tn[1]:
                tc = truth.nodes[c]
                match = None
                if not gradual:
                    for rc in rn[1]:
                        rcn = result.nodes[rc]
                        if rcn[0] == tc[0] and (tc[0] != 'leaf' or rcn == tc):
                            match = rc
                            break
                go(c, match, d, gradual or match is None)
        else:
            tk = children(tn)
            rk = children(rn) if (rn is not None and not gradual) else ()
            for idx, c in enumerate(tk):
                go(c, rk[idx] if idx < len(rk) else None, d + 1, gradual)

    go(0, 0, 0, False)
    return exact, total


# ------------------------------------------------------------------------------ shapes
def shapes(T):
    f = lambda r: T.union_many(T.STR, T.arr(r), T.hsh(T.SYM, r))      # sanitize-like
    g = lambda r: T.union_many(T.INT, T.arr(r), T.hsh(T.STR, r))
    h = lambda r: T.union_many(T.SYM, T.arr(r), T.hsh(T.INT, r))
    k = lambda r: T.union_many(T.STR, T.INT, T.arr(r))
    l = lambda r: T.union_many(T.SYM, T.hsh(T.STR, r), T.arr(r))
    S = {
        # the five shapes of witness_model.py, equations verbatim
        'self': ({'R': lambda s: f(s['R'])}, {'R': T.R0}),
        'cycle2': ({'R0': lambda s: f(s['R1']), 'R1': lambda s: g(s['R0'])}, {'R0': T.R0, 'R1': T.R0}),
        'cycle3': ({'R0': lambda s: f(s['R1']), 'R1': lambda s: g(s['R2']), 'R2': lambda s: h(s['R0'])},
                   {'R0': T.R0, 'R1': T.R0, 'R2': T.R0}),
        'merge2': ({'R': lambda s: T.union_many(T.STR, T.arr(s['R']), T.arr(T.arr(T.STR)), T.hsh(T.U, s['R']))},
                   {'R': T.R0}),
        'param': ({'P': lambda s: T.union_of(T.hsh(T.VAR, T.VAR), T.hsh(T.SYM, T.union_of(s['P'], T.INT)))},
                  {'P': T.P0}),
        # the recursive position carries an extra arm (Array[R | Int]): the exact answer has two
        # states, so a fold to the root would over-approximate
        'dhole': ({'R': lambda s: T.union_many(T.STR, T.arr(T.union_of(s['R'], T.INT)), T.hsh(T.SYM, s['R']))},
                  {'R': T.R0}),
        # a 5-cycle: period longer than M1's history of 3
        'cycle5': ({'R0': lambda s: f(s['R1']), 'R1': lambda s: g(s['R2']), 'R2': lambda s: h(s['R3']),
                    'R3': lambda s: k(s['R4']), 'R4': lambda s: l(s['R0'])},
                   {e: T.R0 for e in ('R0', 'R1', 'R2', 'R3', 'R4')}),
        # controls that must not fold: a 3-chain, and a genuinely nested constant type
        'chain': ({'F': lambda s: T.arr(s['H']), 'H': lambda s: T.arr(s['K']), 'K': lambda s: T.INT},
                  {'F': T.R0, 'H': T.R0, 'K': T.R0}),
        'nested': ({'F': lambda s: T.arr(T.arr(T.U))}, {'F': T.R0}),
    }
    if getattr(T, 'hvalue', None) is not None:
        # constraints's finite chain: five methods each wrapping the next in an Array. A resemblance
        # witness sees A^k[⊥] ⊇ A^(k-1)[⊥] every round until the chain resolves
        S['chain5'] = ({'F0': lambda s: T.arr(s['F1']), 'F1': lambda s: T.arr(s['F2']), 'F2': lambda s: T.arr(s['F3']),
                        'F3': lambda s: T.arr(s['F4']), 'F4': lambda s: T.arr(s['F5']), 'F5': lambda s: T.INT},
                       {e: T.R0 for e in ('F0', 'F1', 'F2', 'F3', 'F4', 'F5')})
        # the re-embedded projection: f(n) = n.zero? ? nil : { a: { b: f(n - 1)[:a] } }
        # (symbol-keyed literals modelled as Hash[Symbol, ·], so [:a] is the hash-value projection)
        S['reembed'] = ({'F': lambda s: T.union_many(T.NIL, T.hsh(T.SYM, T.hsh(T.SYM, T.hvalue(s['F']))))},
                        {'F': T.R0})
        # prototype f2_merge.rb as described in the model: the canonicalizer's return re-enters
        # its parameter rewritten by `merge`, two levels deeper, in two positions; the Hash branch
        # keeps the narrowed receiver's value structure (which is what makes the copy inexact)
        def f2_R(s):
            P = s['P']
            return T.union_many(T.hsh(T.STR, T.hvalue(P)), T.arr(T.elem(P)), T.leaves(P))

        def f2_P(s):
            R, P = s['R'], s['P']
            lit = T.hsh(T.STR, T.arr(T.union_of(T.INT, T.STR)))                       # { "b" => [1, "x"] }
            fed = T.hsh(T.STR, T.union_of(T.merge(R, T.hsh(T.STR, T.INT)),             # "a" => inner.merge("d" => 2)
                                          T.arr(T.merge(R, T.hsh(T.STR, T.NIL)))))     # "c" => [inner.merge("e" => nil)]
            return T.union_many(lit, fed, T.hvalue(P), T.elem(P))                      # recursive call sites
        S['f2'] = ({'R': f2_R, 'P': f2_P}, {'R': T.R0, 'P': T.P0})
    return S


def deep_shapes(T):
    """Additional synthetic shapes (kept apart so the original table is unchanged).

    tuple2, hashrec: branching recursion (two recursive positions in ONE constructor): the
      EKL-quadratic case, where Newton's approximants are stratified by derivation-tree dimension.
    ivar: an ivar fed from itself (F23: recursion with no call-graph cycle; same equation as a method).
    chainN: N acyclic Array-wrapping methods (F18's long chains); deep9: a constant nested 9 deep.
    nest3 / nest3c: the breaker's tag(tag(tag(x))) (F26), monovariant / one summary per call site.
    advN: constraints's determinization adversary (the N-th wrapper from the Integer leaf is a Hash).
    f2h: f2 with the return split by the argument's head (the GRS complete-shell refinement).
    """
    S = {}
    seed = {}

    def wrap(k, inner):
        t = inner
        for _ in range(k):
            t = T.arr(t)
        return t
    S['tuple2'] = ({'X': lambda s: T.union_of(T.INT, T.tup(s['X'], s['X']))}, {'X': T.R0})
    S['hashrec'] = ({'X': lambda s: T.union_of(T.STR, T.hsh(s['X'], s['X']))}, {'X': T.R0})
    S['ivar'] = ({'I': lambda s: T.union_many(T.STR, T.arr(s['I']))}, {'I': T.R0})
    S['deep9'] = ({'F': lambda s: wrap(9, T.INT)}, {'F': T.R0})
    for N in (9, 32):
        eqs = {}
        for i in range(N):
            eqs['F%d' % i] = (lambda j: lambda s: T.arr(s['F%d' % (j + 1)]))(i)
        eqs['F%d' % N] = lambda s: T.INT
        S['chain%d' % N] = (eqs, {e: T.R0 for e in eqs})
    tag = lambda x: T.hsh(T.STR, T.union_of(x, T.arr(T.union_of(x, T.hsh(T.STR, T.INT)))))
    S['nest3'] = ({'P': lambda s: T.union_of(T.INT, s['R']), 'R': lambda s: tag(s['P'])}, {'P': T.R0, 'R': T.R0})
    S['nest3c'] = ({'P1': lambda s: T.INT, 'R1': lambda s: tag(s['P1']), 'P2': lambda s: s['R1'],
                    'R2': lambda s: tag(s['P2']), 'P3': lambda s: s['R2'], 'R3': lambda s: tag(s['P3'])},
                   {e: T.R0 for e in ('P1', 'R1', 'P2', 'R2', 'P3', 'R3')})
    for N in (4, 6, 8, 10):
        eqs = {'Q0': lambda s: T.union_many(T.arr(s['Q0']), T.hsh(T.STR, s['Q0']), T.hsh(T.STR, s['Q1']))}
        for i in range(1, N):
            eqs['Q%d' % i] = (lambda j: lambda s: T.union_of(T.arr(s['Q%d' % (j + 1)]), T.hsh(T.STR, s['Q%d' % (j + 1)])))(i)
        eqs['Q%d' % N] = lambda s: T.INT
        S['adv%d' % N] = (eqs, {e: T.R0 for e in eqs})
    if getattr(T, 'hvalue', None) is not None:
        # f2 with the summary split by the argument's head: Rh (Hash in), Ra (Array in), Rl (leaf in).
        # The two merge sites pass a Hash literal, so they read Rh; the recursive sites read all rows.
        def f2h_P(s):
            Rh, P = s['Rh'], s['P']
            lit = T.hsh(T.STR, T.arr(T.union_of(T.INT, T.STR)))
            fed = T.hsh(T.STR, T.union_of(T.merge(Rh, T.hsh(T.STR, T.INT)), T.arr(T.merge(Rh, T.hsh(T.STR, T.NIL)))))
            return T.union_many(lit, fed, T.hvalue(P), T.elem(P))
        S['f2h'] = ({'Rh': lambda s: T.hsh(T.STR, T.hvalue(s['P'])), 'Ra': lambda s: T.arr(T.elem(s['P'])),
                     'Rl': lambda s: T.leaves(s['P']), 'P': f2h_P},
                    {'Rh': T.R0, 'Ra': T.R0, 'Rl': T.R0, 'P': T.P0})
    return S


# --------------------------------------------------------------------------- iteration
class Result:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def run_m1(name, eqs, init, policy, rounds=36, budget=200_000):
    """prototype run(), with its functions, returning the final state."""
    state = dict(init)
    hist = {e: [v] for e, v in state.items()}
    seen = {e: {v} for e, v in state.items()}
    acc = {e: False for e in state}
    pending = {e: False for e in state}
    for r in range(1, rounds + 1):
        seen_by_typer = {e: m1.to_untyped(v) for e, v in state.items()} if policy == 'side' else state
        new = {e: f(seen_by_typer) for e, f in eqs.items()}
        nxt = {}
        for e, n in new.items():
            old = state[e]
            if policy == 'untie' and e.startswith('R'):
                n = m1.untie(n, old)
            elif policy in ('rule', 'side') and n != old:
                if acc[e] or (n in seen[e]):
                    n = m1.union_of(old, n)
                    acc[e] = True
                folded, did = m1.fold(n, hist[e][-3:], cut=m1.W)
                if did and (pending[e] or acc[e]):
                    n = folded
                    acc[e] = True
                pending[e] = did
            nxt[e] = n
        if nxt == state:
            return Result(status='converged', rounds=r - 1, state={e: from_m1(v) for e, v in state.items()},
                          size=max(m1.size(v) for v in state.values()), folds='-')
        state = nxt
        for e, v in state.items():
            hist[e].append(v)
            seen[e].add(v)
        if max(m1.size(v) for v in state.values()) > budget:
            return Result(status=f'GROWS >{budget}', rounds=r, state=None)
    return Result(status=f'no fixpoint/{rounds}', rounds=rounds, state={e: from_m1(v) for e, v in state.items()},
                  size=max(m1.size(v) for v in state.values()), folds='-')


def run(name, eqs, init, policy, rounds=40, budget=3000, trace=False, backstop=(8, 3), mk_eqs=None, hook=None):
    """Policies: none | m1x (M1 re-implemented here: witness -> W, history 3, confirmation) |
    fold | fold0 (no confirmation) | fold-h3 (history 3) | fold-side1 (typer sees the 1-unfolding
    with untyped at the cut; seed untyped as in Roundhouse) | ref1 | ref2.
    Extended policies: whistle / whistle-v (supercompilation's whistle + msg generalization on
    the slot's value sequence, with ⊥ rigid / as a variable) | fold-gen (fold whose persistent
    orphans are generalized as supercompilation would) | ref1f (level 1 with the covering fold as
    the first backstop). backstop=None disables ∇_k; mk_eqs builds ad-hoc systems for a Typer;
    hook(round, denotations, terms) observes every round."""
    T = Typer('ref1' if policy in ('ref1', 'ref1f') else 'ref2' if policy == 'ref2' else 'concrete')
    # side table: the typer sees the 1-unfolding with a distinct cut leaf (M2's marker, gradual
    # at dispatch); the fold treats the cut as bottom when it looks for a target
    bottom = ('bot', 'cut') if policy == 'fold-side1' else ('bot',)
    init = {e: T.R0 for e in init}
    eqs = mk_eqs(T) if mk_eqs else shapes(T)[name][0]
    confirm = policy not in ('fold0',)
    history = 3 if policy in ('m1x', 'm1g', 'fold-h3') else None
    view_k = 1 if policy == 'fold-side1' else None
    state = dict(init)
    if T.mode != 'concrete':
        T.recursive = recursive_slots(eqs, T)
        T.terms = {e: v for e, v in state.items()}
        T.denot = dict(state)
    hist = {e: [v] for e, v in state.items()}
    thist = {e: [v] for e, v in state.items()}   # term history (ref1f)
    seen = {e: {v} for e, v in state.items()}
    acc = {e: False for e in state}
    pending = {e: False for e in state}
    folds = joins = backstops = orphans = 0
    for r in range(1, rounds + 1):
        if T.mode != 'concrete':
            env = T.env(state)
            new_terms = {e: f(env) for e, f in eqs.items()}
            nxt_terms = {}
            for e, n in new_terms.items():
                old = T.terms[e]
                if e in T.recursive:
                    n = join(old, n) if old != BOT else n          # monotone handoff (lead's design)
                if policy == 'ref1f' and n != old:
                    folded, did, orph = fold(n, thist[e], ('bot',))
                    orphans += orph
                    if did and (pending[e] or acc[e]):
                        n = folded
                        folds += did
                        acc[e] = True
                    pending[e] = bool(did)
                if backstop and depth(n) > backstop[0]:
                    n, b = widen_k(n, backstop[1])
                    backstops += b
                nxt_terms[e] = n
            nxt = tie(nxt_terms)
            if hook:
                hook(r, nxt, nxt_terms)
            if trace:
                for e in nxt:
                    print(f"  r{r} {e}: term {show(nxt_terms[e])}\n        = {show(nxt[e])}")
            if nxt == state and nxt_terms == T.terms:
                return Result(status='converged', rounds=r - 1, state=state, folds=folds, joins=0,
                              backstops=backstops, orphans=orphans, size=max(v.states() for v in state.values()))
            T.terms, T.denot, state = nxt_terms, nxt, nxt
            for e in nxt_terms:
                thist[e].append(nxt_terms[e])
            if max(v.states() for v in state.values()) > budget:
                return Result(status=f'GROWS >{budget}', rounds=r, state=None)
            continue
        typer_view = {e: (view(v, view_k, 'cut', e) if view_k else v) for e, v in state.items()}
        new = {e: f(typer_view) for e, f in eqs.items()}
        nxt = {}
        for e, n in new.items():
            old = state[e]
            note = []
            if view_k:
                if n == typer_view[e] or sim(old, 0, n, 0, bottom):
                    n = old                               # the stored μ-type explains the typer's output
                    note.append('explained')
                else:
                    n = resolve_cuts(n, state)            # cuts are references into the stored μ-types
            if n != old and policy in ('whistle', 'whistle-v'):
                # Kruskal whistle on the slot's own value sequence: an earlier value embeds
                # homeomorphically in the new one -> generalize (msg, mismatches -> W)
                emb = [h for h in hist[e] if compound(h) and h != n and embeds(h, n, bottom_var=policy == 'whistle-v')]
                if emb:
                    g = msg_generalize(emb[-1], n, fill_bottom=policy == 'whistle-v')
                    if g != n:
                        n = g
                        folds += 1
                        acc[e] = True
                        note.append('whistle')
                if n != old and n in seen[e]:
                    n = join(old, n)
                    joins += 1
                    acc[e] = True
            elif n != old and policy != 'none':
                hs = hist[e] if history is None else hist[e][-3:]
                if view_k:
                    hs = hs + [resolve_cuts(typer_view[e], state)]
                folded, did, orph = fold(n, hs, bottom, cut='widened' if policy in ('m1x', 'm1g') else None,
                                         guard=policy != 'm1x',  # m1x keeps M1's unguarded 'strict subterm'
                                         generalize=(policy == 'fold-gen' and pending[e]))
                orphans += orph
                if did and (pending[e] or acc[e] or not confirm):
                    n = folded
                    folds += did
                    acc[e] = True
                    note.append(f'fold×{did}')
                elif did:
                    note.append('witness(pending)')
                pending[e] = bool(did)
                # accumulate only on a revisit or a non-monotone step; a fold's result already
                # covers the old value, and union_of's unmerged tuple arms make a redundant
                # join non-idempotent (two tuple arms where one would do)
                # fold-rel (extended workbench): release instead of sticking: accumulate on revisits only, so a
                # fold or cut made while the pending was pending is re-derived once the pending resolves
                if n != old and (n in seen[e] or (acc[e] and policy != 'fold-rel' and not covers(n, old, bottom))):
                    j = join(old, n)
                    joins += (j != n)
                    n = j
                    acc[e] = True
                    note.append('join')
                if backstop and not n.cyclic() and depth(n) > backstop[0]:
                    n, b = widen_k(n, backstop[1])
                    backstops += b
                    if b:
                        note.append(f'backstop×{b}')
                        acc[e] = True
            nxt[e] = n
            if trace:
                print(f"  r{r} {e}: {show(n)}  {note}")
        if hook:
            hook(r, nxt, None)
        if nxt == state:
            return Result(status='converged', rounds=r - 1, state=state, folds=folds, joins=joins,
                          backstops=backstops, orphans=orphans, size=max(v.states() for v in state.values()))
        state = nxt
        for e, v in state.items():
            hist[e].append(v)
            seen[e].add(v)
        if max(v.states() for v in state.values()) > budget:
            return Result(status=f'GROWS >{budget}', rounds=r, state=None)
    return Result(status=f'no fixpoint/{rounds}', rounds=rounds, state=state, folds=folds, joins=joins,
                  backstops=backstops, orphans=orphans, size=max(v.states() for v in state.values()))


def kleene(name, k=5, rounds=30, budget=40000, mk_eqs=None):
    """Depth-k truncation of the Kleene chain once stable for 3 rounds: the least solution to
    depth k, and the yardstick every policy is measured against."""
    T = Typer('concrete')
    if mk_eqs:
        eqs = mk_eqs(T)
        init = list(eqs)
    else:
        eqs, init = shapes(T)[name]
    state = {e: T.R0 for e in init}
    stable, last = 0, None
    for r in range(1, rounds + 1):
        state = {e: f(state) for e, f in eqs.items()}
        cur = {e: trunc(v, k) for e, v in state.items()}
        stable = stable + 1 if cur == last else 0
        last = cur
        if stable >= 3:
            return cur, r
        if max(v.states() for v in state.values()) > budget:
            break
    return last, None


# -------------------------------------------------------------------------------- main
POLICIES = ('none', 'untie', 'M1:rule', 'M1:side', 'm1x', 'm1g', 'fold', 'fold-h3', 'fold-side1', 'ref1', 'ref2')
PROJECTION_SHAPES = ('reembed', 'f2')


def m1_namespace():
    return type('NS', (), dict(STR=m1.STR, INT=m1.INT, SYM=m1.SYM, U=m1.U, VAR=m1.VAR, arr=staticmethod(m1.arr),
                               hsh=staticmethod(m1.hsh), union_of=staticmethod(m1.union_of),
                               union_many=staticmethod(m1.union_many), R0=m1.U, P0=m1.VAR))()


def main(argv):
    T0 = Typer('concrete')
    S = shapes(T0)
    S_m1 = shapes(m1_namespace())
    if len(argv) > 2 and argv[1] == '--trace':
        pol = argv[3] if len(argv) > 3 else 'fold'
        print(f"trace {argv[2]} under {pol}:")
        r = run(argv[2], *S[argv[2]], policy=pol, trace=True)
        print(r.status, r.rounds)
        return
    K = 5
    print("Policies: none | untie (#528) | M1:rule, M1:side (prototype code, 5 original shapes) | m1x (M1's cut in this")
    print("framework: witness -> W, history 3, 2-round confirmation; M1's unguarded 'strict subterm') | m1g (same, witness")
    print("under a constructor) | fold (mu fold, full history) | fold-h3 (history 3) | fold-side1 (typer sees the 1-unfolding")
    print("with cuts; cuts are (slot, state) references tied back at store) | ref1, ref2 (fold by origin, levels 1 and 2).")
    print(f"exact@{K}: the result agrees with the Kleene chain to depth {K} (the least solution to that depth). mu-exact: equals")
    print("the full regular solution (shapes without projections). size: tree nodes (M1 code) or automaton states. prec@4:")
    print("share of positions to depth 4 typed exactly (W, a stand-in untyped, or a cut counts as gradual below it).\n")
    summary = []
    for name, (eqs, init) in S.items():
        truth, at = kleene(name, K)
        print(f"== {name}  (Kleene truncation at depth {K} stable after round {at})")
        full = None
        if name not in PROJECTION_SHAPES:
            full = solve(eqs, T0)
            if not all(eqs[e](full) == full[e] for e in full):
                full = None
        if full is not None:
            for e, t in full.items():
                print(f"   least solution {e} = {show(t)}   [{t.states()} states]")
        else:
            for e, t in truth.items():
                print(f"   least solution to depth {K}: {e} = {show(t)}")
        print(f"   {'policy':11s} {'status':14s} {'rounds':>6s} {'size':>5s} {'folds':>5s} {'back':>4s} {'orph':>4s} "
              f"{'exact@5':>7s} {'μ-exact':>7s} {'prec@4':>6s}")
        for pol in POLICIES:
            if pol in ('none', 'untie', 'M1:rule', 'M1:side'):
                if name not in S_m1:
                    continue
                r = run_m1(name, *S_m1[name], {'none': 'none', 'untie': 'untie', 'M1:rule': 'rule', 'M1:side': 'side'}[pol])
            else:
                r = run(name, eqs, init, pol)
            if r.state is None:
                print(f"   {pol:11s} {r.status:14s} {r.rounds:6d}")
                summary.append((name, pol, r.status, r.rounds, None, None))
                continue
            exact = all(trunc(r.state[e], K) == truth[e] for e in truth)
            mu = '-' if full is None else str(all(r.state[e] == full[e] for e in full))
            ex, tot = zip(*[gradual_share(r.state[e], truth[e]) for e in truth])
            prec = 100 * sum(ex) / max(1, sum(tot))
            back, orph = getattr(r, 'backstops', '-'), getattr(r, 'orphans', '-')
            print(f"   {pol:11s} {r.status:14s} {r.rounds:6d} {r.size:5} {str(r.folds):>5s} {str(back):>4s} {str(orph):>4s} "
                  f"{str(exact):>7s} {mu:>7s} {prec:5.0f}%")
            summary.append((name, pol, r.status, r.rounds, exact, prec))
            show_types = pol in ('M1:rule', 'fold', 'ref2') or (pol == 'm1x' and name not in S_m1) \
                or (pol == 'ref1' and name in PROJECTION_SHAPES) or (pol in ('m1x', 'fold') and name == 'chain5')
            if show_types:
                for e, v in r.state.items():
                    print(f"               {e} = {show(v)}")
        print()
    print("== Summary (rounds to converge; '-' = no fixpoint or growth)")
    pols = [p for p in POLICIES]
    print(f"   {'shape':8s} " + " ".join(f"{p:>10s}" for p in pols))
    for name in S:
        row = {}
        for (n_, pol, status, rounds, exact, prec) in summary:
            if n_ == name:
                row[pol] = f"{rounds}{'' if exact else '~'}" if status == 'converged' else '-'
        print(f"   {name:8s} " + " ".join(f"{row.get(p, ''):>10s}" for p in pols))
    print("   (a number is the round count; '~' marks a result that is not exact to depth 5; blank = not applicable)")
    print(f"\n== T1 check: {SOUNDNESS[0]} folds performed, {SOUNDNESS[1]} violated fold(n) ⊒ n")
    print("\n== Projection check: prototype M1 result vs view_1 / view_2 of the fold's μ-type with the back edge cut to W")
    for name in ('self', 'cycle2', 'cycle3', 'merge2', 'param', 'dhole'):
        a = run_m1(name, *S_m1[name], 'rule').state
        b = run(name, *S[name], 'fold').state
        for e in a:
            v1, v2 = view(b[e], 1, 'widened'), view(b[e], 2, 'widened')
            rel = 'M1 == view_1(fold)' if a[e] == v1 else 'M1 == view_2(fold)' if a[e] == v2 else \
                  'M1 ⊒ view_1(fold), strictly' if covers(a[e], v1) else 'view_1(fold) ⊒ M1' if covers(v1, a[e]) else 'incomparable'
            print(f"   {name:8s} {e}: {rel}")
    print("\n== RBS for the J-like walker (cycle2, R0), as an emitter would print it (rbs 3.10.0 validates this form):")
    b = run('cycle2', *S['cycle2'], 'fold').state
    print(show_rbs(b['R0'], 'json'))
    print("\n== f2 (prototype canonicalizer) as RBS, from ref2:")
    f2 = run('f2', *S['f2'], 'ref2').state
    print(show_rbs(f2['R'], 'canonical'))
    print("\n== Lattice laws on regular types (sample of cyclic and finite types):")
    sample = [STR, INT, U, arr(STR), hsh(SYM, INT), union_many(STR, INT), arr(union_many(STR, arr(STR))),
              b['R0'], b['R1'], view(b['R0'], 1, 'untyped'), solve(S['dhole'][0], T0)['R'], f2['R']]
    ok = True
    for x in sample:
        for y in sample:
            ok &= join(x, y) == join(y, x) and covers(join(x, y), x) and covers(join(x, y), y) and join(x, x) == x
            if covers(x, y) and covers(y, x):
                ok &= x == y
            for z in sample:
                ok &= join(join(x, y), z) == join(x, join(y, z))
    print(f"   join commutative, associative, idempotent, an upper bound; covers antisymmetric: {ok} ({len(sample)} types)")


if __name__ == '__main__':
    main(sys.argv)
