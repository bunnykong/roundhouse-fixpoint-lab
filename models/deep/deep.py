#!/usr/bin/env python3
"""Experiments with convergence, growth, and precision on an extended regular-type workbench
(fold_model.py in this directory extends the base workbench).

  python3 deep.py all                 # every section, written to deep.out
  python3 deep.py newton growth ...   # selected sections

Sections
  newton    EKL Newton on the automaton domain (linear step solved by tie) vs Kleene, fold, ref2, solve
  growth    the Jacobian A (slot-read multiplicities), its Perron root, and measured growth:
            tree nodes (main), automaton states (sharing), fold/ref2 (constant)
  flips     ref2's round count against the number of discrete-fact increases (the Newton-style bound)
  whistle   supercompilation's whistle + msg on the value sequence, ⊥ rigid and ⊥ as a variable
  chains    where the depth backstop fires on acyclic programs (chain9, chain32, deep9), with and
            without origins; orphan generalization (fold-gen); ref1 with the fold as first backstop
  adversary constraints's determinization adversary: exact states, widen_k's collapse, rounds
  fuzz      random systems over the model's vocabulary: when does the covering fold need a backstop?
  shell     the GRS complete shell of the monovariant summary for application at f2's call sites
  split     f2 with head-split summaries: spurious merge arms, cost, RBS overloads; nest3 vs nest3c
"""
import itertools
import random
import sys
import time
from collections import Counter

import fold_model as fm
from fold_model import (Typer, BOT, STR, INT, W, union_many, join, covers, trunc, depth, tree_size, show,
                        show_rbs, tie, solve, mkref, run, kleene, shapes, deep_shapes, gradual_share, widen_k)

K = 5
OUT = []


def say(*parts):
    line = " ".join(str(p) for p in parts)
    print(line)
    OUT.append(line)


def all_shapes(T):
    S = dict(shapes(T))
    S.update(deep_shapes(T))
    return S


def mk(name):
    return lambda T: all_shapes(T)[name][0]


def slots_of(name):
    return list(all_shapes(Typer('concrete'))[name][0])


def truth_for(name):
    return kleene(name, K, mk_eqs=mk(name))


def is_exact(state, truth):
    return state is not None and all(trunc(state[e], K) == truth[e] for e in truth)


def full_solution(name):
    T0 = Typer('concrete')
    eqs = mk(name)(T0)
    try:
        full = solve(eqs, T0)
        if all(eqs[e](full) == full[e] for e in full):
            return full
    except Exception:
        pass
    return None


def prec(state, truth):
    ex, tot = zip(*[gradual_share(state[e], truth[e]) for e in truth])
    return 100 * sum(ex) / max(1, sum(tot))


def go(name, policy, **kw):
    return run(name, None, slots_of(name), policy, mk_eqs=mk(name), **kw)


# --------------------------------------------------------------------------- 1. Newton
class OccEnv:
    """The environment of one Newton linearization: every slot read returns the current
    approximant ν, except the j-th read, which returns the Newton unknown (a reference leaf).
    j=None evaluates f(ν) and counts the reads (the row of the Jacobian)."""

    def __init__(self, nu, j=None):
        self.nu, self.j, self.k, self.reads = nu, j, 0, []

    def __getitem__(self, key):
        i = self.k
        self.k += 1
        self.reads.append(key)
        if self.j is not None and i == self.j:
            return mkref(key)
        return self.nu[key]


def newton(name, max_steps=10, budget=3000):
    """EKL's Newton iteration in the idempotent case, ν⁰ = f(⊥), ν^{i+1} = ν^i ⊔ (Df|ν^i)^* f(ν^i),
    where Df|ν is the one-read-at-a-time linearization and the star is the least solution of the
    linear system Y = f(ν) ⊔ Df|ν(Y), computed exactly by tie (knot-tying with path references)."""
    T = Typer('ref2')                      # projections of the unknown become path references
    eqs = mk(name)(T)
    slots = list(eqs)
    nu = {e: BOT for e in slots}
    T.recursive = set(slots)
    sizes, reads = [], {}
    for step in range(1, max_steps + 1):
        T.terms, T.denot = dict(nu), dict(nu)
        lin = {}
        for e in slots:
            env = OccEnv(nu)
            delta = eqs[e](env)
            reads[e] = len(env.reads)
            lin[e] = union_many(delta, *[eqs[e](OccEnv(nu, j)) for j in range(len(env.reads))])
        Y = tie(lin)
        new = {e: join(nu[e], Y[e]) for e in slots}
        sizes.append(max(v.states() for v in new.values()))
        if new == nu:
            return dict(steps=step - 1, state=nu, sizes=sizes, reads=reads)
        nu = new
        if sizes[-1] > budget:
            break
    return dict(steps=None, state=nu, sizes=sizes, reads=reads)


def section_newton():
    say("== 1. Newton on the automaton domain: steps to the least solution")
    say("   A step linearizes every slot read one at a time around ν and solves Y = f(ν) ⊔ Df|ν(Y) exactly with tie.")
    say("   Kleene: round at which the depth-5 truncation stabilizes (it never reaches the solution).")
    say(f"   {'shape':9s} {'reads':>5s} {'Kleene@5':>8s} {'Newton':>7s} {'exact@5':>7s} {'μ-exact':>7s} {'fold':>5s} {'ref2':>5s}  sizes per Newton step")
    rows = []
    for name in ('self', 'cycle2', 'cycle3', 'cycle5', 'merge2', 'param', 'dhole', 'ivar', 'reembed', 'f2',
                 'chain5', 'nested', 'tuple2', 'hashrec'):
        truth, at = truth_for(name)
        full = full_solution(name)
        nw = newton(name)
        fo = go(name, 'fold')
        r2 = go(name, 'ref2')
        ex = is_exact(nw['state'], truth) if nw['steps'] is not None else False
        mu = '-' if full is None else str(nw['steps'] is not None and all(nw['state'][e] == full[e] for e in full))
        steps = str(nw['steps']) if nw['steps'] is not None else 'diverges'
        fr = str(fo.rounds) + ('' if is_exact(fo.state, truth) else '~') if fo.state is not None else '-'
        rr = str(r2.rounds) + ('' if is_exact(r2.state, truth) else '~') if r2.state is not None else '-'
        say(f"   {name:9s} {sum(nw['reads'].values()):5d} {str(at):>8s} {steps:>7s} {str(ex):>7s} {mu:>7s} {fr:>5s} {rr:>5s}  {nw['sizes']}")
        rows.append((name, nw))
    say("   tuple2 = Int | [X, X] and hashrec = Str | Hash[X, X] are the EKL-quadratic shapes (two reads in one monomial).")
    for name, nw in rows:
        if name in ('hashrec', 'f2', 'reembed') and nw['steps'] is not None:
            for e, v in nw['state'].items():
                say(f"      {name} {e} after Newton = {show(v)}")
    say("")


# --------------------------------------------------------------------------- 2. growth and ρ
def jacobian(name):
    """the A: A[i][j] = number of times slot j's previous value appears whole inside slot i's
    new value. Measured by feeding a marker leaf per slot and counting its occurrences in the
    unfolded tree of the result (a projection of a marker is ⊥: a projected read copies only a part)."""
    T = Typer('concrete')
    eqs = mk(name)(T)
    slots = list(eqs)
    marks = {e: fm.leaf(('mark', e)) for e in slots}
    A = {e: Counter() for e in slots}
    for e, f in eqs.items():
        try:
            out = f(dict(marks))
        except Exception:
            continue
        memo = {}

        def count(i, tag):
            if (i, tag) in memo:
                return memo[(i, tag)]
            n = out.nodes[i]
            r = 1 if n == ('leaf', tag) else sum(count(c, tag) for c in fm.children(n))
            memo[(i, tag)] = r
            return r
        for j in slots:
            c = count(0, ('mark', j))
            if c:
                A[e][j] = c
    return slots, A


def jacobian_fd(name, k=9):
    """Newton's derivative in the counting semiring, numerically: the finite-difference Jacobian of
    the tree-size map at the k-th Kleene iterate, J[i][j] = Δsize(f_i) / Δsize(X_j) when slot j alone
    advances one round. Projected and rewritten copies contribute their size fraction."""
    T = Typer('concrete')
    eqs = mk(name)(T)
    slots = list(eqs)
    state = {e: BOT for e in slots}
    seq = [state]
    for _ in range(k + 1):
        state = {e: f(state) for e, f in eqs.items()}
        seq.append(state)
        if sum(tree_size(v) for v in state.values()) > 300_000:
            break
    Xk, Xk1 = seq[-2], seq[-1]
    J = {e: {} for e in slots}
    base = {e: tree_size(eqs[e](Xk)) for e in slots}
    for j in slots:
        dj = tree_size(Xk1[j]) - tree_size(Xk[j])
        if dj <= 0:
            continue
        bumped = dict(Xk)
        bumped[j] = Xk1[j]
        for e in slots:
            d = tree_size(eqs[e](bumped)) - base[e]
            if d:
                J[e][j] = d / dj
    return slots, J


def charpoly_roots_max(M):
    """Perron root of a small non-negative integer matrix: largest real root of the characteristic
    polynomial, by Faddeev–LeVerrier coefficients and bisection on [0, max row sum]."""
    n = len(M)
    if n == 0:
        return 0.0
    # Faddeev-LeVerrier: c_n = 1, M_k = M (M_{k-1} + c_{n-k+1} I), c_{n-k} = -tr(M_k)/k
    I = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    coeffs = [0.0] * (n + 1)
    coeffs[n] = 1.0
    Mk = [[0.0] * n for _ in range(n)]
    for k in range(1, n + 1):
        prev = [[Mk[i][j] + coeffs[n - k + 1] * I[i][j] for j in range(n)] for i in range(n)]
        Mk = [[sum(M[i][l] * prev[l][j] for l in range(n)) for j in range(n)] for i in range(n)]
        coeffs[n - k] = -sum(Mk[i][i] for i in range(n)) / k

    def p(x):
        return sum(c * x ** i for i, c in enumerate(coeffs))
    hi = max(sum(row) for row in M) + 1.0
    # the Perron root is the largest real root; scan from hi downward for a sign change
    xs = [hi * i / 2000.0 for i in range(2001)]
    vals = [p(x) for x in xs]
    for i in range(len(xs) - 1, 0, -1):
        if vals[i] == 0:
            return xs[i]
        if (vals[i] > 0) != (vals[i - 1] > 0):
            a, b = xs[i - 1], xs[i]
            for _ in range(60):
                m = (a + b) / 2
                if (p(m) > 0) == (p(a) > 0):
                    a = m
                else:
                    b = m
            return (a + b) / 2
    return 0.0


def section_growth():
    say("== 2. The Jacobian A (embedded copies), its Perron root ρ, the finite-difference Jacobian, and measured growth")
    say("   A counts whole copies of a slot's previous value (the definition); J_fd is Newton's derivative of the")
    say("   tree-size map at Kleene round 9 (projected and rewritten copies count their size fraction).")
    say("   tree nodes = what main stores (no sharing); states = the interned automaton; ratio = last-round growth factor.")
    say(f"   {'shape':9s} {'ρ(A)':>6s} {'ρ(J_fd)':>7s} {'tree ratio':>10s} {'Δstates/round':>13s} {'fold states':>11s} {'ref2 states':>11s}  A")
    for name in ('self', 'cycle2', 'cycle3', 'cycle5', 'merge2', 'param', 'dhole', 'f2', 'reembed', 'tuple2',
                 'hashrec', 'nest3', 'chain5', 'adv4'):
        slots, A = jacobian(name)
        M = [[A[a][b] for b in slots] for a in slots]
        rho = charpoly_roots_max(M)
        _, J = jacobian_fd(name)
        rho_fd = charpoly_roots_max([[J[a].get(b, 0.0) for b in slots] for a in slots])
        T = Typer('concrete')
        eqs = mk(name)(T)
        state = {e: BOT for e in slots}
        trees, states = [], []
        for r in range(1, 13):
            state = {e: f(state) for e, f in eqs.items()}
            trees.append(sum(tree_size(v) for v in state.values()))
            states.append(sum(v.states() for v in state.values()))
            if trees[-1] > 2_000_000:
                break
        ratio = trees[-1] / trees[-2] if len(trees) > 1 and trees[-2] else float('nan')
        dstates = (states[-1] - states[-4]) / 3 if len(states) > 3 else float('nan')
        fo, r2 = go(name, 'fold'), go(name, 'ref2')
        fs = sum(v.states() for v in fo.state.values()) if fo.state else '-'
        rs = sum(v.states() for v in r2.state.values()) if r2.state else '-'
        Astr = "; ".join(f"{a}←{dict(A[a])}" for a in slots if A[a]) if len(slots) <= 6 else f"{len(slots)} slots"
        say(f"   {name:9s} {rho:6.3f} {rho_fd:7.3f} {ratio:10.3f} {dstates:13.1f} {str(fs):>11s} {str(rs):>11s}  {Astr}")
    say("   Reading: ρ(A) predicts family 1 (whole copies: ×2, ×3) and is blind to family 2: f2's copy matrix is 0 yet")
    say("   f2 grows (×1.4 here, ×2.00 in the app), because its growth flows through projections and merge (rewritten")
    say("   copies). The finite-difference Jacobian sees both. Sharing makes growth additive (Δstates is the number of new")
    say("   syntax-site states per round, F20's 'about 9') except where the exact automaton is itself exponential (adv4);")
    say("   the fold and ref2 are constant.")
    say("")


# --------------------------------------------------------------------------- 3. flips bound
def facts_of(denot, terms):
    """The discrete facts a ref2 round can add: (slot, arm head) of each denotation, plus the set of
    path references in the terms. Narrowing and dispatch guards read only these."""
    F = set()
    for e, v in denot.items():
        for h in fm.arm_heads(v, 0):
            if h != ('leaf', 'bot'):        # an unresolved slot's ⊥ is the absence of a fact
                F.add((e, h))
    if terms:
        for e, t in terms.items():
            for n in t.nodes:
                if n[0] == 'leaf' and isinstance(n[1], tuple) and n[1][0] == 'ref':
                    F.add(('ref', e, n[1][1], n[1][2]))
    return F


def section_flips():
    say("== 3. ref2's rounds against the discrete facts it discovers (the Newton-style bound)")
    say("   Inside a component every structural read is a reference, so a round's terms depend on the previous")
    say("   denotations only through heads (narrowing, dispatch guards). Claim: every non-final round adds a fact.")
    say(f"   {'shape':9s} {'rounds':>6s} {'facts per round':>40s} {'strictly increasing until the last':>34s}")
    for name in ('self', 'cycle2', 'cycle5', 'dhole', 'f2', 'f2h', 'reembed', 'nest3', 'chain5', 'adv4', 'tuple2'):
        seq = []

        def hook(r, denot, terms, seq=seq):
            seq.append(facts_of(denot, terms))
        r2 = go(name, 'ref2', hook=hook, backstop=None)
        counts = [len(f) for f in seq]
        increasing = all(seq[i] < seq[i + 1] for i in range(len(seq) - 2))  # the last round repeats
        say(f"   {name:9s} {r2.rounds:6d} {str(counts):>40s} {str(increasing):>34s}")
        if not increasing:
            for i in range(len(seq) - 2):
                if not seq[i] < seq[i + 1]:
                    say(f"             round {i + 1}→{i + 2}: removed {sorted(map(str, seq[i] - seq[i + 1]))[:4]}, added {sorted(map(str, seq[i + 1] - seq[i]))[:4]}")
    say("   chain5's rounds come from its acyclic part (no component): there the bound is the DAG depth, not facts.")
    say("")


# --------------------------------------------------------------------------- 4. whistle
def section_whistle():
    say("== 4. Supercompilation's whistle + msg on the value sequence (no depth constant, backstop off)")
    say("   whistle: ⊥ rigid (any earlier value embeds in the next Kleene iterate) | whistle-v: ⊥ is a variable")
    say("   m1x and fold are the sticky baselines; fold-rel is the fold that accumulates on revisits only (releases).")
    say(f"   {'shape':9s} {'policy':10s} {'status':14s} {'rounds':>6s} {'fires':>5s} {'exact@5':>7s} {'prec@4':>6s} {'= M1 (m1x)':>10s}  result")
    for name in ('self', 'cycle2', 'dhole', 'param', 'chain5', 'chain9', 'deep9', 'reembed', 'f2', 'tuple2'):
        truth, _ = truth_for(name)
        m1 = go(name, 'm1x', backstop=None, rounds=12)
        for pol in ('m1x', 'whistle', 'whistle-v', 'fold', 'fold-rel'):
            r = go(name, pol, backstop=None, rounds=12)
            if r.state is None:
                say(f"   {name:9s} {pol:10s} {r.status:14s} {r.rounds:6d}")
                continue
            same = str(m1.state is not None and r.state == m1.state)
            ex = is_exact(r.state, truth)
            say(f"   {name:9s} {pol:10s} {r.status:14s} {r.rounds:6d} {r.folds:5d} {str(ex):>7s} {prec(r.state, truth):5.0f}% {same:>10s}  "
                + "; ".join(f"{e}={show(v)}" for e, v in r.state.items())[:150])
    say("   Reading: with ⊥ rigid the whistle fires at the first growth round and generalizes the pending to W: rule M1's")
    say("   cut, one round earlier. Its W is not sticky, so on a finite chain the cut is re-derived once the pending")
    say("   resolves (no ⊥ left to embed) and the result is exact: M1's chain misfire is accumulation, not the witness.")
    say("   whistle-v fills ⊥-holes instead of generalizing them: on a Kleene chain nothing is ever generalized, and nothing")
    say("   terminates. There is no third setting: the whistle is either M1 or inert.")
    say("")


# --------------------------------------------------------------------------- 5. chains and backstops
def section_chains():
    say("== 5. Where the depth backstop ∇_k fires on acyclic programs, with and without origins")
    say(f"   {'shape':9s} {'policy':10s} {'backstop':9s} {'status':14s} {'rounds':>6s} {'folds':>5s} {'back':>4s} {'orph':>4s} {'gen':>3s} {'exact@5':>7s} {'prec@4':>6s}  result (first slot)")
    for name in ('deep9', 'chain9', 'chain32', 'chain5', 'reembed', 'f2', 'nest3', 'param', 'dhole', 'cycle5'):
        truth, _ = truth_for(name)
        for pol, bs in (('fold', (8, 3)), ('fold', None), ('fold-rel', (8, 3)), ('fold-rel', None), ('fold-gen', (8, 3)),
                        ('ref1', (8, 3)), ('ref1f', (8, 3)), ('ref1f', None), ('ref2', (8, 3)), ('ref2', None)):
            if name in ('deep9', 'chain9', 'chain32') and pol in ('fold-gen', 'ref1f'):
                continue
            fm.GENERALIZED[0] = 0
            r = go(name, pol, backstop=bs, rounds=48)
            bsname = 'D=8,k=3' if bs else 'none'
            if r.state is None:
                say(f"   {name:9s} {pol:10s} {bsname:9s} {r.status:14s} {r.rounds:6d}")
                continue
            first = next(iter(r.state))
            say(f"   {name:9s} {pol:10s} {bsname:9s} {r.status:14s} {r.rounds:6d} {r.folds:5d} {r.backstops:4d} {r.orphans:4d} {fm.GENERALIZED[0]:3d} "
                f"{str(is_exact(r.state, truth)):>7s} {prec(r.state, truth):5.0f}%  {first}={show(r.state[first])[:110]}")
    say("   Reading: deep9 is a constant nested nine deep: ∇_k widens it under every policy that applies ∇_k by depth,")
    say("   origins included (ref2 with the backstop is inexact on chain9 and chain32 too). The backstop must be gated to")
    say("   component slots, or F18's long acyclic chains are widened. Orphan generalization (fold-gen) trades f2's")
    say("   exactness for earlier termination where fold's waiting was right; it never helps on these shapes.")
    say("")


# --------------------------------------------------------------------------- 6. adversary
def section_adversary():
    say("== 6. constraints's determinization adversary (the N-th wrapper from the Integer leaf is a Hash)")
    say("   Policies run with the depth backstop off (with it on, ∇_8 fires on the acyclic Q1…QN chain at N = 10).")
    say(f"   {'N':>3s} {'exact states Q0':>15s} {'solve ms':>8s} {'widen_k(3) states':>17s} {'widened ⊒ exact':>15s} {'widened == exact':>16s} "
        f"{'fold rounds/states/μ-exact':>26s} {'ref2 rounds/states/μ-exact':>26s}")
    for N in (4, 6, 8, 10):
        name = 'adv%d' % N
        t0 = time.time()
        full = full_solution(name)
        ms = 1000 * (time.time() - t0)
        q0 = full['Q0']
        wid, merged = widen_k(q0, 3)
        fo = go(name, 'fold', budget=5000, rounds=48, backstop=None)
        r2 = go(name, 'ref2', budget=5000, rounds=48, backstop=None)
        fs = f"{fo.rounds}/{fo.state['Q0'].states()}/{fo.state['Q0'] == q0}" if fo.state else fo.status
        rs = f"{r2.rounds}/{r2.state['Q0'].states()}/{r2.state['Q0'] == q0}" if r2.state else r2.status
        say(f"   {N:3d} {q0.states():15d} {ms:8.1f} {wid.states():17d} {str(covers(wid, q0)):>15s} {str(wid == q0):>16s} {fs:>26s} {rs:>26s}")
    say("   Reading: the exact answer has 2^(N+1)+2 states and no round sequence to whistle on; widen_k(3) collapses it to")
    say("   15 states (sound, imprecise from N = 6). ref2 reaches the exact type in N + 1 rounds (the acyclic chain's depth).")
    say("   The covering fold is not a solver for this family. The family is a cost problem for eager determinization")
    say("   (cyclic-eq's lane: keep the NFA, decide equality with HKC/antichains), not a termination problem.")
    say("")


# --------------------------------------------------------------------------- 7. fuzz
LEAVES = ('str', 'int', 'sym', 'nil')


def gen_ast(rng, slots, d):
    r = rng.random()
    if d == 0 or r < 0.2:
        return ('read', rng.choice(slots)) if rng.random() < 0.6 else ('leaf', rng.choice(LEAVES))
    # tuples are excluded: union_of keeps tuple arms apart, which makes the model's simulation check
    # existential (exponential on deep tuple nests) and is the known failure point of every symbolic
    # method here (DESIGN 3.4); the Array/Hash vocabulary is the one the backstop question is about
    kind = rng.choice(['arr', 'arr', 'hsh', 'hsh', 'union', 'union', 'hv', 'ae', 'leaves', 'merge'])
    if kind in ('arr', 'hv', 'ae', 'leaves'):
        return (kind, gen_ast(rng, slots, d - 1))
    if kind == 'hsh':
        return ('hsh', ('leaf', rng.choice(('str', 'sym'))), gen_ast(rng, slots, d - 1))
    if kind == 'merge':
        return ('merge', gen_ast(rng, slots, d - 1), ('hsh', ('leaf', 'str'), ('leaf', rng.choice(LEAVES))))
    return (kind, gen_ast(rng, slots, d - 1), gen_ast(rng, slots, d - 1))


def reads_of(ast):
    if ast[0] == 'read':
        return {ast[1]}
    if ast[0] == 'leaf':
        return set()
    return set().union(*[reads_of(a) for a in ast[1:]])


def compile_ast(ast, T):
    k = ast[0]
    if k == 'leaf':
        c = getattr(T, {'str': 'STR', 'int': 'INT', 'sym': 'SYM', 'nil': 'NIL'}[ast[1]])
        return lambda s: c
    if k == 'read':
        return lambda s: s[ast[1]]
    subs = [compile_ast(a, T) for a in ast[1:]]
    ops = {'arr': lambda s: T.arr(subs[0](s)), 'hsh': lambda s: T.hsh(subs[0](s), subs[1](s)),
           'tup': lambda s: T.tup(subs[0](s), subs[1](s)), 'union': lambda s: T.union_of(subs[0](s), subs[1](s)),
           'hv': lambda s: T.hvalue(subs[0](s)), 'ae': lambda s: T.elem(subs[0](s)),
           'leaves': lambda s: T.leaves(subs[0](s)), 'merge': lambda s: T.merge(subs[0](s), subs[1](s))}
    return ops[k]


def show_ast(ast):
    k = ast[0]
    if k == 'leaf':
        return ast[1]
    if k == 'read':
        return ast[1]
    return k + "(" + ", ".join(show_ast(a) for a in ast[1:]) + ")"


def section_fuzz(count=120, seed=20261007):
    say(f"== 7. Fuzz: {count} random systems over the model's vocabulary (seed {seed}); 1–3 slots, depth ≤ 3")
    rng = random.Random(seed)
    tally = Counter()
    examples = []
    made = 0
    while made < count:
        n = rng.choice((1, 2, 2, 3))
        slots = ['S%d' % i for i in range(n)]
        asts = {s: gen_ast(rng, slots, 3) for s in slots}
        if not all(reads_of(a) for a in asts.values()):
            continue
        # keep systems with at least one slot in a cycle (acyclic ones converge trivially)
        deps = {s: reads_of(a) for s, a in asts.items()}
        rec = set()
        for s in slots:
            seen, todo = set(), list(deps[s])
            while todo:
                x = todo.pop()
                if x == s:
                    rec.add(s)
                    break
                if x in seen:
                    continue
                seen.add(x)
                todo.extend(deps[x])
        if not rec:
            continue
        made += 1

        def mk_eqs(T, asts=asts):
            return {s: compile_ast(a, T) for s, a in asts.items()}
        print(f"   [{made}]", end="", flush=True)
        try:
            truth, at = kleene('fuzz', K, rounds=24, budget=1500, mk_eqs=mk_eqs)
        except Exception as ex:  # a projection on a tuple position etc.
            tally['kleene error'] += 1
            continue
        if at is None:
            tally['kleene unstable to depth 5 within 24 rounds / 1500 states'] += 1
            continue
        res = {}
        for pol, bs in (('fold', None), ('fold', (8, 3)), ('ref2', None), ('ref2', (8, 3))):
            try:
                r = run('fuzz', None, slots, pol, mk_eqs=mk_eqs, backstop=bs, rounds=30, budget=1200)
            except Exception as ex:
                r = fm.Result(status='error ' + type(ex).__name__, rounds=0, state=None, backstops=0, orphans=0, folds=0)
            res[(pol, bs is not None)] = r
        fnb, fb, r2, r2b = res[('fold', False)], res[('fold', True)], res[('ref2', False)], res[('ref2', True)]
        tally['systems'] += 1
        tally['fold, no backstop: converged'] += fnb.state is not None and fnb.status == 'converged'
        tally['fold, no backstop: exact@5'] += is_exact(fnb.state, truth)
        tally['fold + ∇: converged'] += fb.state is not None and fb.status == 'converged'
        tally['fold + ∇: exact@5'] += is_exact(fb.state, truth)
        tally['fold + ∇: backstop fired'] += bool(fb.state is not None and fb.backstops)
        tally['ref2, no backstop: converged'] += r2.state is not None and r2.status == 'converged'
        tally['ref2, no backstop: exact@5'] += is_exact(r2.state, truth)
        tally['ref2 + ∇: backstop fired'] += bool(r2b.state is not None and r2b.backstops)
        tally['ref2 + ∇: exact@5'] += is_exact(r2b.state, truth)
        if not (fnb.state is not None and fnb.status == 'converged') and len(examples) < 6:
            examples.append(('fold without backstop does not converge', asts, fnb.status, fb.status, fb.backstops,
                             is_exact(fb.state, truth), r2.status, is_exact(r2.state, truth)))
        elif fnb.state is not None and fnb.status == 'converged' and not is_exact(fnb.state, truth) and len(examples) < 6:
            examples.append(('fold converged but inexact', asts, fnb.status, fb.status, fb.backstops,
                             is_exact(fb.state, truth), r2.status, is_exact(r2.state, truth)))
        if r2.state is not None and not is_exact(r2.state, truth) and len(examples) < 8:
            examples.append(('ref2 inexact', asts, fnb.status, fb.status, fb.backstops, is_exact(fb.state, truth),
                             r2.status, is_exact(r2.state, truth)))
    for k, v in sorted(tally.items()):
        say(f"   {k:48s} {v}")
    say("   Examples (system; fold/no-∇ status; fold+∇ status, firings, exact; ref2 status, exact):")
    for tag, asts, a, b, c, d, e, f in examples:
        say(f"   - {tag}: " + "; ".join(f"{s} = {show_ast(x)}" for s, x in asts.items()))
        say(f"       fold/no-∇ {a}; fold+∇ {b} ({c} firings, exact {d}); ref2 {e} (exact {f})")
    say("")


# --------------------------------------------------------------------------- 8. GRS shell
def section_shell():
    say("== 8. The GRS complete shell of the monovariant (rectangle) summary for application at f2's call sites")
    H = ('hash', 'array', 'int', 'str', 'nil')
    subsets = [frozenset(c) for r in range(len(H) + 1) for c in itertools.combinations(H, r)]

    def rect(D, R):
        return frozenset((i, o) for i in D for o in R)

    def app(G, a):
        return frozenset(o for (i, o) in G if i in a)

    def inv(a, y):  # max {G : app_a(G) ⊆ y}
        return frozenset((i, o) for i in H for o in H if i not in a or o in y)

    def closure(family, G):
        c = frozenset((i, o) for i in H for o in H)
        for F in family:
            if G <= F:
                c &= F
        return c

    rectangles = {rect(D, R) for D in subsets for R in subsets}
    canonical = frozenset([('hash', 'hash'), ('array', 'array'), ('int', 'int'), ('str', 'str'), ('nil', 'nil')])
    say(f"   heads H = {list(H)}; the monovariant domain is the {len(rectangles)} rectangles D×R of ℘(H×H).")
    say(f"   canonical's head relation G = {{(h,h)}}: ρ_mono(G) = {sorted(closure(rectangles, canonical))[:3]}… (the full square);")
    say(f"   app_{{hash}}(G) = {sorted(app(canonical, frozenset(['hash'])))} but app_{{hash}}(ρ_mono(G)) = {sorted(app(closure(rectangles, canonical), frozenset(['hash'])))}: incomplete.")
    for label, args in (("f2's merge sites: a = {hash}; recursive sites: a = H", [frozenset(['hash']), frozenset(H)]),
                        ("one site per head", [frozenset([h]) for h in H])):
        gens = set(rectangles)
        for a in args:
            for y in subsets:
                gens.add(inv(a, y))
        # Moore closure: intersections of generators; computed structurally since the generators are
        # rectangles and column constraints: elements are per-atom (of the Boolean algebra the a's
        # generate) independent output sets intersected with a rectangle
        atoms = {}
        for i in H:
            atoms.setdefault(frozenset(a for a in args if i in a), set()).add(i)
        if label.startswith("one site"):
            n_elems = "2^25 (every relation: one output set per head)"
            fam = None
        else:
            fam = set()
            cells = list(atoms.values())
            for D in subsets:
                for R in subsets:
                    for y in subsets:
                        fam.add(frozenset((i, o) for i in D for o in R if (i not in args[0]) or (o in y)))
            n_elems = str(len(fam))
        say(f"   operations: {label}")
        say(f"      atoms of the argument sets: {[sorted(c) for c in atoms.values()]} -> {len(atoms)} context cells")
        say(f"      complete shell size: {n_elems}")
        if fam is not None:
            ok = True
            rng = random.Random(1)
            for _ in range(60):
                G = frozenset(p for p in rect(frozenset(H), frozenset(H)) if rng.random() < 0.4)
                for a in args:
                    ok &= app(closure(fam, G), a) == app(G, a)
            say(f"      completeness check (60 random relations, both operations): {ok}")
            say(f"      canonical through the shell: app_{{hash}} = {sorted(app(closure(fam, canonical), frozenset(['hash'])))}, "
                f"app_H = {sorted(app(closure(fam, canonical), frozenset(H)))}")
            # minimality: dropping the hash column generators breaks completeness
            say(f"      without the a={{hash}} generators (rectangles only): app_{{hash}} = {sorted(app(closure(rectangles, canonical), frozenset(['hash'])))}")
    say("   Reading: the least complete refinement is one independent summary per atom of the argument sets the program")
    say("   actually passes: for f2, {Hash} against everything else (2 cells), which is coarser than one context per call")
    say("   site (4) and than one per head (5). Lifted from heads to types, each cell's entry is the body typed once on")
    say("   that cell: the relational signature '(Hash) -> Hash[String, …] & (other) -> …' printed as RBS overloads.")
    say("")


# --------------------------------------------------------------------------- 9. head split and nest3
def section_split():
    say("== 9. f2 with head-split summaries (f2h), and manufactured recursion (nest3 against nest3c)")
    truth, _ = truth_for('f2')
    mono = go('f2', 'ref2')
    split = go('f2h', 'ref2')
    th, _ = truth_for('f2h')
    R, P = mono.state['R'], mono.state['P']
    Rh, Ra, Rl, Ph = (split.state[e] for e in ('Rh', 'Ra', 'Rl', 'P'))
    say(f"   mono (ref2, {mono.rounds} rounds): merge receiver = R with arms {sorted(h[0] if h[0] != 'leaf' else h[1] for h in fm.arm_heads(R, 0))}")
    say(f"   split (ref2, {split.rounds} rounds): merge receiver = Rh with arms {sorted(h[0] if h[0] != 'leaf' else h[1] for h in fm.arm_heads(Rh, 0))}")
    spurious_mono = 2 * (len(fm.arm_heads(R, 0)) - 1)
    spurious_split = 2 * (len(fm.arm_heads(Rh, 0)) - 1)
    say(f"   spurious receiver arms at the two merge sites: mono {spurious_mono}, split {spurious_split} (the reframer's Datalog model: 8 → 0)")
    say(f"   same parameter type: {P == Ph}; mono R == Rh | Ra | Rl: {R == union_many(Rh, Ra, Rl)}; split exact@5: {is_exact(split.state, th)}")
    say(f"   cost: body rows typed per round: mono 1, head-split 3 (Hash, Array, leaf), one-call-site 4, GRS least 2")
    say("   RBS, the head-split summary as overloads (what the shell's cells print as):")
    say(f"      def canonical: (Hash[untyped, untyped]) -> {show_rbs(Rh, 'h').splitlines()[0].split(' = ', 1)[1]}")
    say(f"                   | (Array[untyped]) -> {show_rbs(Ra, 'a').splitlines()[0].split(' = ', 1)[1]}")
    say(f"                   | (Integer | String | nil) -> {show_rbs(Rl, 'l').splitlines()[0].split(' = ', 1)[1]}")
    for alias in show_rbs(Rh, 'h').splitlines()[1:]:
        say(f"      {alias}")
    say("")
    t3, _ = truth_for('nest3')
    t3c, _ = truth_for('nest3c')
    m = go('nest3', 'ref2')
    c = go('nest3c', 'ref2')
    say(f"   nest3 (monovariant tag(tag(tag(x)))), ref2 in {m.rounds} rounds, exact@5 {is_exact(m.state, t3)}:")
    for e, v in m.state.items():
        say(f"      {e} = {show(v)}")
    say(f"   nest3c (one summary per call site), ref2 in {c.rounds} rounds, exact@5 {is_exact(c.state, t3c)}:")
    for e, v in c.state.items():
        say(f"      {e} = {show(v)}")
    say("   Reading: the monovariant system's cycle P ← R ← P is manufactured by the shared parameter row; the refined")
    say("   system is acyclic and its type is finite. Recursion is manufactured iff the complete-shell refinement breaks")
    say("   the slot-graph cycle; canonical's cycle (R reads hvalue(P) of a value produced from R) survives every")
    say("   context refinement, so it is inherent.")
    say("")


SECTIONS = {'newton': section_newton, 'growth': section_growth, 'flips': section_flips, 'whistle': section_whistle,
            'chains': section_chains, 'adversary': section_adversary, 'fuzz': section_fuzz, 'shell': section_shell,
            'split': section_split}


def main(argv):
    names = argv[1:] or ['all']
    if names == ['all']:
        names = list(SECTIONS)
    t0 = time.time()
    for n in names:
        t1 = time.time()
        SECTIONS[n]()
        say(f"   [{n}: {time.time() - t1:.1f}s]\n")
    say(f"total {time.time() - t0:.1f}s")
    if names == list(SECTIONS):
        with open(__file__.rsplit('/', 1)[0] + '/deep.out', 'w') as f:
            f.write("\n".join(OUT) + "\n")


if __name__ == '__main__':
    # the coinductive simulation and canonicalization recurse once per state pair along a path:
    # the adversary's 2^N-state automata need more than CPython's default depth
    import threading
    sys.setrecursionlimit(1_000_000)
    threading.stack_size(1 << 29)
    t = threading.Thread(target=main, args=(sys.argv,))
    t.start()
    t.join()
