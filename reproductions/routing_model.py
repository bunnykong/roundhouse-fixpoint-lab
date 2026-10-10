#!/usr/bin/env python3
"""Three finite scheduling experiments (no dependencies, Python 3.9+).

Domain: a slot holds a frozenset of value arms; pending = frozenset() = bottom.
Each writer is re-evaluated against the current state when a slot it reads changes.
Per-writer entries; the published slot is the join (union) over writers.

E1  monotone transfers: every random schedule gives one answer, equal to Kleene's
    least fixpoint; per-writer overwrite == inflationary join in every run.
E2  narrowing's empty-survivor fallback (remove_nil(Nil) = Nil): the inflationary
    join settles but keeps a transient (schedule-dependent answers); per-writer
    overwrite != join in the schedules that saw the transient (a descent).  The best
    transformer (bottom for an empty survivor) restores E1.
E3  structure by discovery: the transfer executed at a position is chosen from the
    state at its first evaluation (inline vs reference).  Both
    candidate transfers are monotone, every run has zero descents and overwrite ==
    join, yet the answers differ by schedule.  Only a structure digest sees it.
"""
import itertools
import random

NIL, INT, STR = "Nil", "Int", "Str"
BOT = frozenset()


def remove_nil_fallback(x):
    s = x - {NIL}
    return s if s else x            # today's rule: empty survivor -> return the input


def remove_nil_best(x):
    return x - {NIL}                # best transformer: empty survivor -> bottom


def solve(writers, order, mode="join", max_steps=10_000):
    """writers: list of (name, dst, reads, fn). Returns (state, descents, steps, structure)."""
    entries = {}                    # (writer name) -> value
    state = {}                      # slot -> published join over writers
    structure = {}                  # E3: per-writer routing decided at first evaluation
    descents = 0
    queue = list(order)
    seen = set(queue)
    steps = 0
    by_slot = {}
    for w in writers:
        for r in w[2]:
            by_slot.setdefault(r, []).append(w)
    while queue:
        steps += 1
        if steps > max_steps:
            return None, descents, steps, structure
        w = queue.pop(0)
        seen.discard(w[0])
        name, dst, reads, fn = w
        inputs = [state.get(r, BOT) for r in reads]
        new = fn(inputs, structure, name)
        old = entries.get(name, BOT)
        if not new >= old:
            descents += 1
        if mode == "join":
            new = new | old
        entries[name] = new
        pub = frozenset().union(*(v for (n2, d2, _, _), v in
                                  zip(writers, (entries.get(x[0], BOT) for x in writers)) if d2 == dst))
        if state.get(dst, BOT) != pub:
            state[dst] = pub
            for w2 in by_slot.get(dst, []):
                if w2[0] not in seen:
                    seen.add(w2[0])
                    queue.append(w2)
    return state, descents, steps, structure


def digest(state):
    return tuple(sorted((k, tuple(sorted(v))) for k, v in state.items()))


def run_all(writers, label, trials=300, seed=1):
    rnd = random.Random(seed)
    out = {}
    for mode in ("join", "last"):
        digests, desc, unsettled = set(), 0, 0
        for _ in range(trials):
            order = writers[:]
            rnd.shuffle(order)
            st, d, steps, _ = solve(writers, order, mode)
            if st is None:
                unsettled += 1
                continue
            digests.add(digest(st))
            desc += d
        out[mode] = (digests, desc, unsettled)
    j, l = out["join"], out["last"]
    print(f"{label}")
    print(f"  join : {len(j[0])} distinct answer(s), {j[1]} descents over {trials} runs, {j[2]} unsettled")
    print(f"  last : {len(l[0])} distinct answer(s), {l[1]} descents over {trials} runs, {l[2]} unsettled")
    print(f"  one shared answer in both modes: {j[0] == l[0] and len(j[0]) == 1 and j[2] == l[2] == 0}")
    for dg in sorted(j[0] | l[0]):
        print("   ", dict((k, "|".join(v) or "bot") for k, v in dg))
    return out


def program(narrow):
    # p: parameter row with two call-site writers; n: narrowing site reading p; r: return reading n.
    return [
        ("site1", "p", (), lambda i, s, w: frozenset({NIL})),
        ("site2", "p", (), lambda i, s, w: frozenset({INT})),
        ("narrow", "n", ("p",), lambda i, s, w: narrow(i[0])),
        ("ret", "r", ("n",), lambda i, s, w: i[0] | {STR}),
    ]


def program_discovery(fixed):
    # The transfer at n is chosen at its first evaluation: if p is still pending the site is
    # typed "inline" (identity, no projection) and keeps that routing; otherwise it becomes a
    # reference and projects.  Both routings are monotone functions.
    def narrow(i, s, w):
        if fixed:
            s[w] = "ref"
        elif w not in s:
            s[w] = "inline" if i[0] == BOT else "ref"
        return i[0] if s[w] == "inline" else remove_nil_best(i[0])
    return [
        ("site1", "p", (), lambda i, s, w: frozenset({NIL})),
        ("site2", "p", (), lambda i, s, w: frozenset({INT})),
        ("narrow", "n", ("p",), narrow),
        ("ret", "r", ("n",), lambda i, s, w: i[0] | {STR}),
    ]


def kleene(writers):
    state = {}
    while True:
        new = {}
        for name, dst, reads, fn in writers:
            v = fn([state.get(r, BOT) for r in reads], {"narrow": "ref"}, name)
            new[dst] = new.get(dst, BOT) | v
        if new == state:
            return state
        state = new


if __name__ == "__main__":
    print("E1: monotone transfers (best-transformer narrowing)")
    e1 = run_all(program(remove_nil_best), "  program(remove_nil_best)")
    assert e1["join"][0] == {digest(kleene(program(remove_nil_best)))}, "E1 must equal Kleene lfp"
    print("E2: narrowing fallback (today's rule)")
    e2 = run_all(program(remove_nil_fallback), "  program(remove_nil_fallback)")
    print("E3: structure by discovery (both routings monotone)")
    e3 = run_all(program_discovery(fixed=False), "  program_discovery(fixed=False)")
    e3f = run_all(program_discovery(fixed=True), "  program_discovery(fixed=True)")
    print()
    print("E1 one answer, zero descents:", len(e1["join"][0]) == 1 and e1["last"][1] == 0)
    print("E2 join keeps a transient (several answers):", len(e2["join"][0]) > 1)
    print("E2 overwrite != join somewhere, descents > 0:", e2["join"][0] != e2["last"][0] or e2["last"][1] > 0)
    print("E3 several answers with ZERO descents and overwrite == join per run:",
          len(e3["join"][0]) > 1 and e3["last"][1] == 0 and e3["join"][1] == 0)
    print("E3 fixed routing: one answer:", len(e3f["join"][0]) == 1)
