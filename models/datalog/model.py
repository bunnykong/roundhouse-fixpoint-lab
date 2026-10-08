#!/usr/bin/env python3
"""Finite allocation-site inference, using fact-at-a-time semi-naive Datalog.

Python standard library only. This is a hand-lowered IR model, not a Ruby parser
or a claim of exact concrete Ruby semantics. All constructors, fields, contexts
and rules are finite before solving. No widening and no convergence cap.
"""
from collections import Counter, defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Atom:
    rel: str
    args: tuple


def atom(rel, *args):
    return Atom(rel, args)


def variable(value):
    return isinstance(value, str) and value.startswith("?")


@dataclass(frozen=True)
class Rule:
    name: str
    head: Atom
    body: tuple


class Engine:
    """Positive, range-restricted rules, indexed joins and one queued delta/fact.

    Every complete grounding fires exactly once: choose the latest inserted body
    fact as pivot, breaking a repeated-fact tie by the first body position. This
    is asynchronous semi-naive evaluation, not repeated scans of all rules.
    There is no recursively constructed domain value or opaque lattice callback.
    """
    def __init__(self):
        self.facts = defaultdict(dict)  # relation -> tuple -> insertion timestamp
        self.indexes = defaultdict(dict)
        self.triggers = defaultdict(list)
        self.rules = []
        self.queue = deque()
        self.serial = 0
        self.work = Counter()
        self.firings = Counter()
        self.inputs = []

    def rule(self, name, head, *body):
        assert body, "put ground facts in the input relations"
        bound = {x for a in body for x in a.args if variable(x)}
        assert all(not variable(x) or x in bound for x in head.args)
        rule = Rule(name, head, body)
        self.rules.append(rule)
        for i, premise in enumerate(body):
            self.triggers[premise.rel].append((rule, i))

    def add(self, rel, *row, input_fact=False):
        row = tuple(row)
        self.work["insert_attempts"] += 1
        if row in self.facts[rel]:
            return False
        self.serial += 1
        self.facts[rel][row] = self.serial
        for mask, index in self.indexes[rel].items():
            index[tuple(row[i] for i in mask)].append((row, self.serial))
        self.queue.append((rel, row, self.serial))
        self.work["facts_inserted"] += 1
        self.work["queue_peak"] = max(self.work["queue_peak"], len(self.queue))
        if input_fact:
            self.inputs.append((rel, row))
        return True

    @staticmethod
    def match(pattern, row, env):
        if len(pattern) != len(row):
            return None
        env = dict(env)
        for name, value in zip(pattern, row):
            if variable(name):
                if name in env and env[name] != value:
                    return None
                env[name] = value
            elif name != value:
                return None
        return env

    def query(self, premise, env):
        mask = tuple(i for i, x in enumerate(premise.args) if not variable(x) or x in env)
        key = tuple(env[x] if variable(x) else x for i, x in enumerate(premise.args) if i in mask)
        if mask not in self.indexes[premise.rel]:
            index = defaultdict(list)
            for row, stamp in self.facts[premise.rel].items():
                index[tuple(row[i] for i in mask)].append((row, stamp))
            self.indexes[premise.rel][mask] = index
        return tuple(self.indexes[premise.rel][mask].get(key, ()))

    def solve(self):
        while self.queue:
            rel, row, stamp = self.queue.popleft()
            self.work["delta_facts_processed"] += 1
            for rule, pivot in self.triggers[rel]:
                env = self.match(rule.body[pivot].args, row, {})
                if env is None:
                    continue
                rest = tuple(i for i in range(len(rule.body)) if i != pivot)

                def join(remaining, bindings):
                    if not remaining:
                        self.firings[rule.name] += 1
                        self.work["rule_firings"] += 1
                        values = tuple(bindings[x] if variable(x) else x for x in rule.head.args)
                        self.add(rule.head.rel, *values)
                        return
                    # Prefer the most bound index; tie by body position.
                    pos = min(remaining, key=lambda i: (-sum(
                        not variable(x) or x in bindings for x in rule.body[i].args), i))
                    premise = rule.body[pos]
                    for candidate, arrival in self.query(premise, bindings):
                        self.work["join_candidates"] += 1
                        if arrival > stamp or (arrival == stamp and pos < pivot):
                            continue
                        extended = self.match(premise.args, candidate, bindings)
                        if extended is not None:
                            join(tuple(i for i in remaining if i != pos), extended)

                join(rest, env)
        return self

    def rows(self, rel):
        return set(self.facts[rel])

    def stats(self):
        return {**dict(self.work), "firings_by_rule": dict(sorted(self.firings.items())),
                "relation_sizes": {r: len(xs) for r, xs in sorted(self.facts.items()) if xs},
                "worklist_empty": not self.queue, "global_body_rounds": None}


def core_rules(e):
    a, rule = atom, e.rule
    rule("allocation", a("Pt", "?x", "?h"), a("Alloc", "?x", "?h"))
    rule("flow", a("Pt", "?y", "?h"), a("Flow", "?x", "?y"), a("Pt", "?x", "?h"))
    rule("load", a("Flow", "?cell", "?out"), a("Load", "?recv", "?f", "?out"),
         a("Pt", "?recv", "?h"), a("Field", "?h", "?f", "?cell"))
    rule("store", a("Flow", "?value", "?cell"), a("Store", "?recv", "?f", "?value"),
         a("Pt", "?recv", "?h"), a("Field", "?h", "?f", "?cell"))
    rule("filter", a("Pt", "?out", "?h"), a("Filter", "?src", "?kind", "?out"),
         a("Pt", "?src", "?h"), a("Kind", "?h", "?kind"))
    rule("produce", a("Pt", "?out", "?new"), a("Produce", "?src", "?kind", "?out", "?new"),
         a("Pt", "?src", "?h"), a("Kind", "?h", "?kind"))
    rule("key_to_string", a("Pt", "?out", "atom:str"), a("ToString", "?src", "?out"),
         a("Pt", "?src", "?h"))
    # A finite context table, selected by call site and *argument* head.
    rule("call_target", a("Target", "?call", "?arg", "?out", "?ctx"),
         a("Invoke", "?call", "?arg", "?out"), a("Pt", "?arg", "?h"),
         a("Kind", "?h", "?kind"), a("Select", "?call", "?kind", "?ctx"))
    rule("call_argument", a("Pt", "?param", "?h"),
         a("Target", "?call", "?arg", "?out", "?ctx"), a("Pt", "?arg", "?h"),
         a("Kind", "?h", "?kind"), a("Select", "?call", "?kind", "?ctx"),
         a("Formal", "?ctx", "?param"))
    rule("call_return", a("Flow", "?ret", "?out"),
         a("Target", "?call", "?arg", "?out", "?ctx"), a("Return", "?ctx", "?ret"))
    rule("call_active", a("Active", "?ctx"), a("Target", "?c", "?a", "?o", "?ctx"))
    # Dynamic method dispatch (one positional argument in this small IR).
    rule("dispatch", a("Dispatch", "?c", "?arg", "?out", "?p", "?r"),
         a("Send", "?c", "?recv", "?method", "?arg", "?out"),
         a("Pt", "?recv", "?h"), a("Kind", "?h", "?kind"),
         a("Method", "?kind", "?method", "?p", "?r"))
    rule("dispatch_argument", a("Flow", "?arg", "?p"),
         a("Dispatch", "?c", "?arg", "?out", "?p", "?r"))
    rule("dispatch_return", a("Flow", "?r", "?out"),
         a("Dispatch", "?c", "?arg", "?out", "?p", "?r"))
    rule("yield_argument", a("Flow", "?arg", "?p"), a("Yield", "?block", "?arg", "?out"),
         a("Pt", "?block", "?h"), a("Block", "?h", "?p", "?r"))
    rule("yield_return", a("Flow", "?r", "?out"), a("Yield", "?block", "?arg", "?out"),
         a("Pt", "?block", "?h"), a("Block", "?h", "?p", "?r"))
    # Unknown-key Hash#merge: a fresh site, with covariant read summaries.
    rule("merge_pair", a("MergePair", "?left", "?right", "?out", "?new"),
         a("Merge", "?x", "?y", "?out", "?new"), a("Pt", "?x", "?left"),
         a("Kind", "?left", "hash"), a("Pt", "?y", "?right"), a("Kind", "?right", "hash"))
    rule("merge_result", a("Pt", "?out", "?new"), a("MergePair", "?l", "?r", "?out", "?new"))
    for side in ("l", "r"):
        rule("merge_" + side, a("Flow", "?src", "?dst"),
             a("MergePair", "?l", "?r", "?out", "?new"), a("Field", "?" + side, "?f", "?src"),
             a("Field", "?new", "?f", "?dst"))
    # Unsupported is an extensional, closed-world table, never absence of Pt.
    rule("bad_use", a("BadUse", "?call", "?kind"), a("Use", "?call", "?src", "?method"),
         a("Pt", "?src", "?h"), a("Kind", "?h", "?kind"), a("Unsupported", "?method", "?kind"))


SCALARS = ("str", "int", "sym", "nil", "float", "model_u", "model_var")


class Program:
    def __init__(self, name):
        self.name, self.engine = name, Engine()
        core_rules(self.engine)
        self.sites, self.slots, self.roots = {}, set(), {}
        for kind in SCALARS:
            self.site("atom:" + kind, kind, ())

    def fact(self, rel, *args):
        self.engine.add(rel, *args, input_fact=True)

    def slot(self, name):
        self.slots.add(name)
        return name

    def site(self, name, kind, fields):
        shape = (kind, tuple(fields))
        if name in self.sites:
            assert self.sites[name] == shape
            return name
        self.sites[name] = shape
        self.fact("Kind", name, kind)
        for field in fields:
            self.fact("Field", name, field, self.slot(name + "." + field))
        return name

    def literal(self, slot, kind):
        self.slot(slot)
        self.fact("Alloc", slot, "atom:" + kind)
        return slot

    def flow(self, src, dst):
        self.slot(src)
        self.slot(dst)
        self.fact("Flow", src, dst)
        return dst

    def construct(self, dst, site, kind, fields, unconditional=True):
        self.slot(dst)
        self.site(site, kind, fields)
        for field, src in fields.items():
            self.flow(src, site + "." + field)
        if unconditional:
            self.fact("Alloc", dst, site)
        return site

    def solve(self):
        before = (len(self.slots), len(self.sites))
        self.engine.solve()
        assert before == (len(self.slots), len(self.sites))
        return self

    def stats(self):
        return {"slots": len(self.slots), "sites_including_atoms": len(self.sites),
                "constructor_sites": sum(k not in SCALARS for k, _ in self.sites.values()),
                **self.engine.stats()}


class TypeGraph:
    """Print only existing field/slot sets; never powerset-determinize the graph.

    Equal points-to sets share an alias. Distinct sites remain alternatives; the
    separate comparison adapter applies round 1's head/spine abstraction.
    Finite constructor membership is not a cyclic-heap/sharing predicate.
    """
    names = {"str": "String", "int": "Integer", "sym": "Symbol", "nil": "nil",
             "float": "Float", "model_u": "UModel", "model_var": "VModel"}

    def __init__(self, program):
        self.program = program
        points = defaultdict(set)
        for slot, site in program.engine.rows("Pt"):
            points[slot].add(site)
        self.points = {s: frozenset(points[s]) for s in program.slots}

    def heads(self, slot):
        return {self.program.sites[h][0] for h in self.points.get(slot, ())}

    def accepts(self, slot, term):
        def visit(state, value):
            for site in state:
                kind, fields = self.program.sites[site]
                if value[0] != kind or len(value) - 1 != len(fields):
                    continue
                if all(visit(self.points[site + "." + f], child) for f, child in zip(fields, value[1:])):
                    return True
            return False
        return visit(self.points.get(slot, ()), term)

    def productive_records(self):
        """Productivity for least finite trees; generic Array/Hash allow empties.

        Required record fields must have a productive alternative. This is a
        post-saturation grammar check, not termination/exception analysis.
        """
        good = {s for s, (k, _) in self.program.sites.items() if not k.startswith("record_")}
        while True:
            more = {s for s, (k, fs) in self.program.sites.items() if k.startswith("record_") and
                    all(self.points[s + "." + f] & good for f in fs)}
            if more <= good:
                return good
            good |= more

    def equations(self, productive_only=False):
        allowed = self.productive_records() if productive_only else set(self.program.sites)
        points = {slot: frozenset(h for h in hs if h in allowed) for slot, hs in self.points.items()}
        labels, pending, lines = {}, deque(), []
        roots = self.program.roots

        def name(state, hint=None):
            compound = any(self.program.sites[s][1] for s in state)
            if hint is None and not compound:
                return " | ".join(sorted(self.names.get(self.program.sites[s][0],
                    self.program.sites[s][0]) for s in state)) or "bot"
            if state not in labels:
                labels[state] = hint or "t%d" % len(labels)
                pending.append(state)
            return labels[state]

        for alias, slot in roots.items():
            name(points.get(slot, frozenset()), alias)
        while pending:
            state = pending.popleft()
            arms = set()
            for site in sorted(state):
                kind, fields = self.program.sites[site]
                children = [name(points[site + "." + f]) for f in fields]
                if kind == "array":
                    text = "Array[%s]" % children[0]
                elif kind == "hash":
                    text = "Hash[%s, %s]" % tuple(children)
                elif kind.startswith("record_"):
                    text = "{ " + ", ".join(f + ": " + c for f, c in zip(fields, children)) + " }"
                else:
                    text = self.names.get(kind, kind)
                arms.add(text)
            lines.append("type %s = %s" % (labels[state], " | ".join(sorted(arms)) or "bot"))
        for alias, slot in roots.items():
            label = labels[points.get(slot, frozenset())]
            if alias != label:
                lines.append("type %s = %s" % (alias, label))
        return lines
