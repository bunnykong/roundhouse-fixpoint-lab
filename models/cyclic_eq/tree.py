"""CIAA-style bottom-up antichains for exact finite ranked-tree inclusion.

Unlike compare.included, this does NOT merge Hash/Array spines or require a
single covering Tuple arm. Union is ordinary nondeterministic choice.
Each antichain entry (p,S) has a witness accepted at small-state p, whose
complete set of accepting big-states is S. Keep only minimal S for each p.
"""
from collections import defaultdict, deque
from itertools import product
from time import perf_counter

from .compare import Comparison, Exhausted, Session, bits, children, head


def tree_included(left, right, *, budget=1_000_000, seconds=None):
    start, session = perf_counter(), None
    try:
        session = Session(left, right, budget, seconds)
        top_id = len(session.nodes)
        alphabet = {head(n) for n in session.nodes if n[0] != "union" and n != ("leaf", "bot")
                    and n != ("leaf", "widened")}
        # Top ranges over all rigid leaves, including a tag absent in both inputs.
        fresh = ("cyclic_eq_fresh",)
        while ("leaf", fresh) in alphabet:
            fresh += (0,)
        alphabet.add(("leaf", fresh))

        def arity(h):
            return {"leaf": 0, "array": 1, "hash": 2}.get(h[0],
                    h[1] if h[0] == "tuple" else len(h[1]) if h[0] == "record" else 0)

        def rules(state):
            mask = session.top if state == top_id else session.normalize(1 << state)
            if mask == session.top:
                return [(h, (top_id,) * arity(h)) for h in sorted(alphabet, key=repr)]
            return [(head(session.nodes[s]), children(session.nodes[s])) for s in bits(mask)]

        small_rules, big_rules, parents = [], defaultdict(list), defaultdict(list)
        for p in list(range(len(left.nodes))) + [top_id]:
            for h, cs in rules(p):
                rid = len(small_rules)
                small_rules.append((p, h, cs))
                for i, child in enumerate(cs):
                    parents[child].append((rid, i))
        for q in list(range(len(left.nodes), top_id)) + [top_id]:
            for h, cs in rules(q):
                big_rules[h].append((q, cs))
        retained, witnesses, pending = defaultdict(set), {}, deque()

        def insert(p, mask, witness):
            session.check()
            session.stats["tree_generated"] += 1
            if any(old & mask == old for old in retained[p]):
                session.stats["tree_pruned"] += 1
                return False
            removed = {old for old in retained[p] if old & mask == mask}
            retained[p].difference_update(removed)
            retained[p].add(mask)
            witnesses[(p, mask)] = witness
            pending.append((p, mask))
            session.stats["tree_inserted"] += 1
            session.stats["tree_peak"] = max(session.stats["tree_peak"], sum(len(s) for s in retained.values()))
            session.stats["tree_max_width"] = max(session.stats["tree_max_width"], len(retained[p]))
            if p == left.root and not (mask & (1 << (len(left.nodes) + right.root))):
                return True
            return False

        def post(h, masks):
            out = 0
            for q, cs in big_rules.get(h, ()):
                session.check()
                session.stats["tree_transition_checks"] += 1
                if all(m & (1 << c) for m, c in zip(masks, cs)):
                    out |= 1 << q
            return out

        def reject(witness):
            result = session.finish(False, "finite-tree-antichain")
            result.witness = witness
            return result

        for p, h, cs in small_rules:
            if not cs:
                witness = (h, ())
                if insert(p, post(h, ()), witness):
                    return reject(witness)
        while pending:
            p, mask = pending.popleft()
            if mask not in retained[p]:
                continue
            session.stats["tree_popped"] += 1
            for rid, forced in parents[p]:
                owner, h, cs = small_rules[rid]
                choices = [(mask,) if i == forced else tuple(sorted(retained[c])) for i, c in enumerate(cs)]
                for masks in product(*choices):
                    session.check()
                    witness = (h, tuple(witnesses[(c, m)] for c, m in zip(cs, masks)))
                    if insert(owner, post(h, masks), witness):
                        return reject(witness)
        session.stats["tree_retained"] = sum(len(s) for s in retained.values())
        return session.finish(True, "finite-tree-antichain")
    except Exhausted as exc:
        if session is not None:
            return session.finish(None, "budget", str(exc))
        return Comparison(None, "budget", {}, (perf_counter() - start) * 1000, str(exc))
