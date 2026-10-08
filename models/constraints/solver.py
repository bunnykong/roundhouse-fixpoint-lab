#!/usr/bin/env python3
"""Finite, monomorphic Simple-sub-style bound propagation and data reification.

This is a deliberately restricted experiment, not an MLsub implementation or a
Ruby checker. Positive joins, negative meets, function variance and nominal call
uses are supported by the constraint solver. Reification accepts only covariant
data and uses witness_model's one-spine-per-head abstraction. All variable and
constructor identities are allocated before saturation; saturation allocates none.
"""
from collections import Counter, defaultdict, deque
from dataclasses import dataclass


def subset_blowup(length):
    """The nth wrapper from the Integer leaf must be a Hash."""
    s = Solver()
    q = [s.var("Q%d" % i) for i in range(length + 1)]
    st = s.node("str")
    s.add(s.join(s.node("array", q[0]), s.node("hash", st, q[0]),
                 s.node("hash", st, q[1])), q[0])
    for i in range(1, length):
        s.add(s.join(s.node("array", q[i + 1]), s.node("hash", st, q[i + 1])), q[i])
    s.add(s.node("int"), q[-1])
    s.solve()
    return s, Graph(s, {"Q0": q[0]})


@dataclass(frozen=True)
class Node:
    kind: str
    args: tuple = ()
    name: str = ""


class Solver:
    def __init__(self):
        self.nodes, self.intern = [], {}
        self.lower, self.upper = defaultdict(set), defaultdict(set)
        self.queue, self.seen = deque(), set()
        self.methods, self.work = {}, Counter()

    def node(self, kind, *args, name=""):
        node = Node(kind, tuple(args), name)
        if node not in self.intern:
            self.intern[node] = len(self.nodes)
            self.nodes.append(node)
        return self.intern[node]

    def var(self, name):
        return self.node("var", name=name)

    def join(self, *args):
        flat = set()
        for arg in args:
            n = self.nodes[arg]
            flat.update(n.args if n.kind == "join" else (arg,))
        if len(flat) == 1:
            return next(iter(flat))
        return self.node("join", *sorted(flat))

    def add(self, low, high):
        self.work["constraint_requests"] += 1
        if (low, high) not in self.seen:
            self.seen.add((low, high))
            self.queue.append((low, high))
            self.work["queue_peak"] = max(self.work["queue_peak"], len(self.queue))

    def solve(self):
        count = len(self.nodes)
        while self.queue:
            low, high = self.queue.popleft()
            self.work["pairs_processed"] += 1
            a, b = self.nodes[low], self.nodes[high]
            if low == high or a.kind == "bottom" or b.kind == "top":
                continue
            if a.kind == "join":
                for child in a.args:
                    self.add(child, high)
            elif b.kind == "meet":
                for child in b.args:
                    self.add(low, child)
            elif a.kind == "var":
                self.upper[low].add(high)
                for bound in sorted(self.lower[low]):
                    self.add(bound, high)
                # Store both ends of a variable edge: necessary for later facts.
                if b.kind == "var":
                    self.lower[high].add(low)
                    for bound in sorted(self.upper[high]):
                        self.add(low, bound)
            elif b.kind == "var":
                self.lower[high].add(low)
                for bound in sorted(self.upper[high]):
                    self.add(low, bound)
            elif b.kind == "use":
                signature = self.methods.get((a.kind, b.name))
                if signature is None:
                    raise TypeError("missing method %s on %s" % (b.name, a.kind))
                fn = self.nodes[signature]
                if fn.kind != "fn" or len(fn.args) != len(b.args):
                    raise TypeError("call arity mismatch")
                for actual, formal in zip(b.args[:-1], fn.args[:-1]):
                    self.add(actual, formal)
                self.add(fn.args[-1], b.args[-1])
            elif a.kind == b.kind and a.name == b.name and len(a.args) == len(b.args):
                for i, (left, right) in enumerate(zip(a.args, b.args)):
                    if a.kind == "fn" and i < len(a.args) - 1:
                        self.add(right, left)
                    else:
                        self.add(left, right)
            else:
                raise TypeError("incompatible constraint: %s <= %s" % (a, b))
        assert len(self.nodes) == count, "saturation must not allocate type nodes"
        return self


class Graph:
    """Deterministic head/spine graph; NOT general semantic-subtyping automata.

    A state is a set of constructor nodes, after epsilon closure of joins and
    lower bounds. Equal constructor heads merge children pointwise, exactly the
    abstraction used for Array/Hash in the witness model. Subset construction is
    finite but has an exponential worst case. States are bisimulation-minimized.
    """
    def __init__(self, solver, roots):
        self.work = Counter()
        self.states, self.roots = [], {}
        subsets, pending = {}, deque()

        def state(seeds):
            todo, visited, heads = list(seeds), set(), set()
            while todo:
                ref = todo.pop()
                if ref in visited:
                    continue
                visited.add(ref)
                self.work["epsilon_visits"] += 1
                node = solver.nodes[ref]
                if node.kind == "var":
                    todo.extend(sorted(solver.lower[ref]))
                elif node.kind == "join":
                    todo.extend(node.args)
                elif node.kind == "bottom":
                    pass
                elif node.kind in ("fn", "meet", "use"):
                    raise TypeError("data-only reification")
                else:
                    heads.add(ref)
            tops = {r for r in heads if solver.nodes[r].kind == "top"}
            key = frozenset(tops or heads)
            if key not in subsets:
                subsets[key] = len(self.states)
                self.states.append(None)
                pending.append(key)
            return subsets[key]

        for name, root in roots.items():
            self.roots[name] = state((root,))
        while pending:
            key = pending.popleft()
            groups = defaultdict(list)
            for ref in sorted(key):
                node = solver.nodes[ref]
                groups[node.kind].append(node.args)
                self.work["constructor_visits"] += 1
            transitions = {}
            for head, terms in sorted(groups.items()):
                assert len({len(term) for term in terms}) == 1
                transitions[head] = tuple(state(children) for children in zip(*terms))
            self.states[subsets[key]] = transitions
        self.raw_states = len(self.states)
        self.minimize()

    def minimize(self):
        colors = [0] * len(self.states)
        while True:
            classes, nxt = {}, []
            self.work["partition_passes"] += 1
            for transitions in self.states:
                signature = tuple((h, tuple(colors[c] for c in cs)) for h, cs in transitions.items())
                nxt.append(classes.setdefault(signature, len(classes)))
                self.work["partition_state_visits"] += 1
            if nxt == colors:
                break
            colors = nxt
        states = [None] * len(set(colors))
        for i, transitions in enumerate(self.states):
            states[colors[i]] = {h: tuple(colors[c] for c in cs) for h, cs in transitions.items()}
        self.states = states
        self.roots = {name: colors[root] for name, root in self.roots.items()}

    def sizes(self):
        return {"states_before_minimize": self.raw_states, "states": len(self.states),
                "constructor_arms": sum(len(s) for s in self.states),
                "child_edges": sum(len(cs) for s in self.states for cs in s.values())}

    def accepts(self, name, term):
        """Membership for finite constructor witnesses, not Ruby heap semantics."""
        def visit(state, value):
            transitions = self.states[state]
            if "top" in transitions:
                return True
            head, children = value[0], value[1:]
            refs = transitions.get(head)
            return refs is not None and len(refs) == len(children) and all(
                visit(ref, child) for ref, child in zip(refs, children))
        return visit(self.roots[name], term)

    def below(self, name, other, other_name):
        """Sufficient coinductive structural inclusion for this covariant fragment."""
        todo, seen = [(self.roots[name], other.roots[other_name])], set()
        while todo:
            left, right = todo.pop()
            if (left, right) in seen:
                continue
            seen.add((left, right))
            a, b = self.states[left], other.states[right]
            if "top" in b:
                continue
            for head, children in a.items():
                if head not in b or len(children) != len(b[head]):
                    return False
                todo.extend(zip(children, b[head]))
        return True

    def equations(self):
        labels = {}
        for name, root in self.roots.items():
            labels.setdefault(root, name)
        for i, s in enumerate(self.states):
            if any(s.values()) and i not in labels:
                labels[i] = "T%d" % i
        names = {"str": "String", "int": "Integer", "sym": "Symbol", "nil": "Nil",
                 "array": "Array", "hash": "Hash", "model_u": "U_model",
                 "model_var": "V_model", "top": "Widened", "float": "Float"}

        def render(state, expand=False):
            if not expand and state in labels:
                return labels[state]
            arms = []
            for head, children in self.states[state].items():
                atom = names.get(head, head)
                if children:
                    atom += "[" + ", ".join(render(c) for c in children) + "]"
                arms.append(atom)
            return " | ".join(arms) or "Bottom"
        lines = ["%s = %s" % (label, render(state, True)) for state, label in labels.items()]
        for name, root in self.roots.items():
            if labels.get(root) != name:
                lines.append("%s = %s" % (name, render(root)))
        return lines
