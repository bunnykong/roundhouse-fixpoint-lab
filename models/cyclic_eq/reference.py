"""Local experimental repair of regular's Moore refinement, for validation only.

Union successors are a SET of classes, so neither their raw multiplicity nor
the number of pre-minimization arms belongs in the initial color. This file
does not modify the frozen oracle. Its bounded Tuple ordering is inherited.
"""
from .compare import children


def set_minimize(oracle, graph, root):
    states = sorted(oracle.reachable(graph, root))
    signatures = {}
    classes = {}
    for s in states:
        n = graph[s]
        sig = (n[0], n[1]) if n[0] == "leaf" else ("union",) if n[0] == "union" else (n[0], len(children(n)))
        classes[s] = signatures.setdefault(sig, len(signatures))
    while True:
        ids, new = {}, {}
        for s in states:
            n = graph[s]
            cs = tuple(sorted({classes[c] for c in n[1]})) if n[0] == "union" else tuple(classes[c] for c in children(n))
            sig = (classes[s], cs)
            new[s] = ids.setdefault(sig, len(ids))
        if len(set(new.values())) == len(set(classes.values())):
            return new
        classes = new


def repaired_canonical(oracle, automaton):
    from .fixtures import lower_records
    a = lower_records(automaton)
    graph, root = dict(enumerate(a.nodes)), a.root
    for _ in range(8):
        graph, root = oracle.determinize(graph, root)
        classes = set_minimize(oracle, graph, root)
        quotient = {}
        for s, c in classes.items():
            if c not in quotient:
                n = graph[s]
                quotient[c] = (("union", frozenset(classes[x] for x in n[1])) if n[0] == "union"
                               else oracle.remap(n, lambda x: classes[x]))
        graph, root = quotient, classes[root]
        if not any(n[0] == "union" and len(n[1]) < 2 for n in graph.values()):
            return oracle.number(graph, root)
    raise RuntimeError("experimental normalization did not settle")
