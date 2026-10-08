"""Bounded compatibility with the frozen workbench's literal canonical tables.

HKC proves bisimulation, while that canonicalizer can over-refine duplicate
cyclic Tuple choices. Positive answers containing Tuple/Record therefore use
a bounded legacy canonicalization. The main comparison engine never needs it.
"""
from collections import defaultdict
from time import perf_counter

from .compare import Comparison, Exhausted, equivalent
from .fixtures import regular, lower_records


def legacy_canonical(oracle, automaton, stats, max_states, deadline):
    a = lower_records(automaton)
    graph, root = dict(enumerate(a.nodes)), a.root

    def check():
        if perf_counter() > deadline:
            raise Exhausted("legacy canonicalization time budget")

    def determinize(g, r):
        """regular determinize, preserving its allocation/order, with a state cap."""
        table, memo = {}, {}
        count = 0

        def allocate():
            nonlocal count
            check()
            if count >= max_states:
                raise Exhausted("legacy canonicalization state budget")
            count += 1
            stats["legacy_states_allocated"] = stats.get("legacy_states_allocated", 0) + 1
            return count - 1

        def det(states):
            key = frozenset(oracle.flatten(g, states))
            if key in memo:
                return memo[key]
            p = allocate()
            memo[key] = p
            arms = [g[s] for s in sorted(key)]
            if any(n == ("leaf", "widened") for n in arms):
                table[p] = ("leaf", "widened")
                return p
            if not arms:
                table[p] = ("leaf", "bot")
                return p
            groups = defaultdict(list)
            for s in sorted(key):
                n = g[s]
                label = ("leaf", n[1]) if n[0] == "leaf" else ("tuple", s) if n[0] == "tuple" else (n[0],)
                groups[label].append(n)
            built = []
            for label in sorted(groups, key=repr):
                mem = groups[label]
                if label[0] == "leaf":
                    built.append(("leaf", label[1]))
                elif label[0] == "array":
                    built.append(("array", det([n[1] for n in mem])))
                elif label[0] == "hash":
                    built.append(("hash", det([n[1] for n in mem]), det([n[2] for n in mem])))
                else:
                    built.append(("tuple", tuple(det([c]) for c in mem[0][1])))
            if len(built) == 1:
                table[p] = built[0]
            else:
                ids = []
                for n in built:
                    q = allocate()
                    table[q] = n
                    ids.append(q)
                table[p] = ("union", frozenset(ids))
            return p
        new_root = det([r])
        return table, new_root

    for _ in range(8):
        graph, root = determinize(graph, root)
        check()
        classes = oracle.minimize(graph, root)
        quotient = {}
        for s, c in classes.items():
            if c not in quotient:
                n = graph[s]
                quotient[c] = (("union", frozenset(classes[x] for x in n[1])) if n[0] == "union"
                               else oracle.remap(n, lambda x: classes[x]))
        graph, root = quotient, classes[root]
        check()
        if not any(n[0] == "union" and len(n[1]) < 2 for n in graph.values()):
            return oracle.number(graph, root)
    raise Exhausted("legacy canonicalization iteration budget")


def frozen_equal(left, right, *, oracle=None, max_states=4097, seconds=3, **kwargs):
    """Exact legacy table equality on completed queries; None means unknown.

    General positive cyclic-choice queries can need eager canonicalization;
    this compatibility API makes that cost explicit rather than emulating a
    canonicalizer bug inside HKC. Plain Array/Hash adversaries stay on HKC.
    """
    start = perf_counter()
    result = equivalent(left, right, seconds=seconds, **kwargs)
    if result.holds is not True or not any(n[0] in ("tuple", "record") for n in left.nodes + right.nodes):
        return result
    stats = dict(result.stats)
    try:
        o = oracle if oracle is not None else regular()
        a = legacy_canonical(o, left, stats, max_states, start + seconds)
        b = legacy_canonical(o, right, stats, max_states, start + seconds)
        return Comparison(a == b, "HKC+legacy-table", stats, (perf_counter() - start) * 1000)
    except (Exhausted, RecursionError) as exc:
        return Comparison(None, "budget", stats, (perf_counter() - start) * 1000, str(exc))
