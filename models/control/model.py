#!/usr/bin/env python3
"""Control strategies over one finite, positive, site-based abstraction.

No Ruby parser, Salsa implementation, general MLsub checker, widening or cap.
The imported Datalog engine is unchanged. Its input instructions are also
compiled into pure slot -> points-to-set functions for rounds and SCC queries.
These 'body evaluations' are lowered slot bodies, NOT Ruby method executions.
"""
import sys
sys.dont_write_bytecode = True
import importlib.util
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dl = load("control_datalog", ROOT / "models/datalog/model.py")
_previous_model = sys.modules.get("model")
sys.modules["model"] = dl  # cases.py's unqualified import; restored below
base = load("baselines", ROOT / "models/datalog/baselines.py")
cases = load("control_cases", ROOT / "models/datalog/cases.py")
if _previous_model is None:
    sys.modules.pop("model", None)
else:
    sys.modules["model"] = _previous_model
_previous_path = list(sys.path)
fold = load("control_fold", ROOT / "models/fold/fold_model.py")
sys.path[:] = _previous_path
sub = base.round1  # constraints/solver.py
EMPTY = frozenset()


def clone_program(p):
    q = dl.Program(p.name)
    q.engine = dl.Engine()
    dl.core_rules(q.engine)
    q.sites, q.slots, q.roots = dict(p.sites), set(p.slots), dict(p.roots)
    for rel, row in p.engine.inputs:
        q.fact(rel, *row)
    return q


def points(p):
    out = {s: set() for s in p.slots}
    for slot, heap in p.engine.rows("Pt"):
        out[slot].add(heap)
    return {s: frozenset(v) for s, v in out.items()}


def make_case(name, summary=False):
    if name in ("self", "cycle2", "cycle3", "merge2", "param"):
        return cases.witness(name)
    if name == "f2":
        return f2_program(summary)
    if name == "reembed_safe":
        return cases.reembed(True)
    if name == "chain64":
        return cases.chain(64)
    raise KeyError(name)


SHAPES = ("self", "cycle2", "cycle3", "merge2", "param", "f2", "reembed_safe", "chain64")


def f2_program(summary=False):
    """Reuse the earlier lowering, keeping Float in the frozen scalar domain.

    The base app has no Float. The add-call experiment does, and Ruby's else
    branch must preserve it. Head contexts include that potential callee from
    the start, rather than assuming a closed call graph from the initial app.
    """
    p = cases.f2_merge("arg_head" if summary else "mono")
    if summary:
        remap = lambda value: "float/" + value[4:] if value.startswith("str/") else value
        for site, (kind, fields) in list(p.sites.items()):
            if site.startswith("str/"):
                p.site(remap(site), kind, fields)
        for slot in list(p.slots):
            if slot.startswith("str/"):
                p.slot(remap(slot))
        for rel, row in list(p.engine.inputs):
            if rel in ("Kind", "Field", "Select"):
                continue
            if any(v.startswith("str/") for v in row):
                new = tuple(remap(v) for v in row)
                if rel in ("Formal", "Return"):
                    new = ("float",) + new[1:]
                p.fact(rel, *new)
    contexts = [ctx for ctx, _ in p.engine.rows("Formal")]
    for ctx in contexts:
        p.fact("Filter", ctx + "/P", "float", ctx + "/R")
    for call in ("inner_call", "outer_call", "hash_value_call", "array_value_call"):
        p.fact("Select", call, "float", "float" if summary else "all")
    p.fact("Unsupported", "merge", "float")
    return p


def edit_call(p):
    """Add a call argument contribution; existing identities/old condition frozen.

    For pure return equations, the call passes Float to a synthetic identity
    callee whose result joins the selected slot. Deletion removes that call's
    Flow fact. This tests retraction of interprocedural data, not Ruby parsing.
    """
    q = clone_program(p)
    q.literal("edit/actual", "float")
    if p.name.startswith("f2_merge/"):
        q.fact("Invoke", "edit_call", "edit/actual", q.slot("edit/result"))
        for call, kind, ctx in p.engine.rows("Select"):
            if call == "inner_call":
                q.fact("Select", "edit_call", kind, ctx)
        return q
    target = "R63" if p.name == "chain64" else next(iter(p.roots.values()))
    q.flow("edit/actual", "edit/identity/P")
    q.flow("edit/identity/P", "edit/identity/R")
    q.flow("edit/identity/R", target)
    return q


@dataclass(frozen=True)
class Transfer:
    """A stable contribution with an explicit conservative dependency set."""
    key: tuple
    deps: frozenset
    fn: object


class SlotSystem:
    def __init__(self, p):
        self.program = p
        self.bodies = {s: [] for s in p.slots}
        rows = defaultdict(list)
        for rel, row in p.engine.inputs:
            rows[rel].append(row)
        kinds = {h: k for h, k in rows["Kind"]}
        fields = {(h, f): c for h, f, c in rows["Field"]}
        field_cells = defaultdict(set)
        for (_, f), cell in fields.items():
            field_cells[f].add(cell)

        def emit(dst, key, deps, fn):
            self.bodies.setdefault(dst, []).append(Transfer(key, frozenset(deps), fn))

        def read_field(st, recv, field):
            return frozenset(h for site in st[recv] if (site, field) in fields
                             for h in st[fields[site, field]])

        def has(st, src, kind):
            return any(kinds[h] == kind for h in st[src])

        for dst, heap in rows["Alloc"]:
            emit(dst, ("Alloc", dst, heap), (), lambda st, h=heap: frozenset((h,)))
        for src, dst in rows["Flow"]:
            emit(dst, ("Flow", src, dst), (src,), lambda st, s=src: st[s])
        for recv, f, dst in rows["Load"]:
            emit(dst, ("Load", recv, f, dst), {recv} | field_cells[f],
                 lambda st, r=recv, f=f: read_field(st, r, f))
        for recv, f, value in rows["Store"]:
            for (heap, field), cell in fields.items():
                if field == f:
                    emit(cell, ("Store", recv, f, value, heap), (recv, value),
                         lambda st, r=recv, v=value, h=heap: st[v] if h in st[r] else EMPTY)
        for src, kind, dst in rows["Filter"]:
            emit(dst, ("Filter", src, kind, dst), (src,),
                 lambda st, s=src, k=kind: frozenset(h for h in st[s] if kinds[h] == k))
        for src, kind, dst, new in rows["Produce"]:
            emit(dst, ("Produce", src, kind, dst, new), (src,),
                 lambda st, s=src, k=kind, h=new: frozenset((h,)) if has(st, s, k) else EMPTY)
        for src, dst in rows["ToString"]:
            emit(dst, ("ToString", src, dst), (src,),
                 lambda st, s=src: frozenset(("atom:str",)) if st[s] else EMPTY)
        formal, returns = dict(rows["Formal"]), dict(rows["Return"])
        select = {(c, k): ctx for c, k, ctx in rows["Select"]}
        for call, arg, dst in rows["Invoke"]:
            for ctx in sorted(set(select.values())):
                allowed = frozenset(k for (c, k), v in select.items() if c == call and v == ctx)
                if not allowed:
                    continue
                emit(formal[ctx], ("InvokeArg", call, arg, ctx), (arg,),
                     lambda st, a=arg, ks=allowed: frozenset(h for h in st[a] if kinds[h] in ks))
                emit(dst, ("InvokeRet", call, arg, ctx, returns[ctx]), (arg, returns[ctx]),
                     lambda st, a=arg, ks=allowed, r=returns[ctx]:
                     st[r] if any(kinds[h] in ks for h in st[a]) else EMPTY)
        for left, right, dst, new in rows["Merge"]:
            emit(dst, ("Merge", left, right, dst, new), (left, right),
                 lambda st, l=left, r=right, n=new:
                 frozenset((n,)) if has(st, l, "hash") and has(st, r, "hash") else EMPTY)
            for (heap, field), cell in fields.items():
                if heap != new:
                    continue
                deps = {left, right} | field_cells[field]

                def merge_fields(st, l=left, r=right, f=field):
                    if not (has(st, l, "hash") and has(st, r, "hash")):
                        return EMPTY
                    return frozenset(h for src in (l, r) for site in st[src]
                                     if kinds[site] == "hash" and (site, f) in fields
                                     for h in st[fields[site, f]])
                emit(cell, ("MergeField", left, right, new, field), deps, merge_fields)
        for call, recv, method, arg, dst in rows["Send"]:
            for kind, meth, param, ret in rows["Method"]:
                if method != meth:
                    continue
                emit(param, ("SendArg", call, recv, kind, arg, param), (recv, arg),
                     lambda st, r=recv, a=arg, k=kind: st[a] if has(st, r, k) else EMPTY)
                emit(dst, ("SendRet", call, recv, kind, ret), (recv, ret),
                     lambda st, r=recv, out=ret, k=kind: st[out] if has(st, r, k) else EMPTY)
        for recv, arg, dst in rows["Yield"]:
            for heap, param, ret in rows["Block"]:
                emit(param, ("YieldArg", recv, arg, heap), (recv, arg),
                     lambda st, b=recv, a=arg, h=heap: st[a] if h in st[b] else EMPTY)
                emit(dst, ("YieldRet", recv, ret, heap), (recv, ret),
                     lambda st, b=recv, r=ret, h=heap: st[r] if h in st[b] else EMPTY)
        handled = {"Kind", "Field", "Alloc", "Flow", "Load", "Store", "Filter", "Produce", "ToString",
                   "Formal", "Return", "Select", "Invoke", "Merge", "Send", "Method", "Yield", "Block",
                   "Use", "Unsupported"}
        assert set(rows) <= handled, set(rows) - handled
        self.slots = tuple(sorted(self.bodies))
        self.deps = {s: set().union(*(t.deps for t in ts)) for s, ts in self.bodies.items()}
        self.keys = {s: tuple(sorted(t.key for t in ts)) for s, ts in self.bodies.items()}
        self.readers = {s: set() for s in self.slots}
        for dst, reads in self.deps.items():
            for src in reads:
                self.readers[src].add(dst)

    def bottom(self):
        return {s: EMPTY for s in self.slots}

    def eval(self, slot, state, work):
        work["body_evaluations"] += 1
        work["instruction_evaluations"] += len(self.bodies[slot])
        out = set()
        for transfer in self.bodies[slot]:
            out.update(transfer.fn(state))
        return frozenset(out)


def rounds(system, seed=None):
    state, work = system.bottom(), Counter()
    if seed:
        state.update({s: frozenset(v) for s, v in seed.items() if s in state})
    while True:
        work["global_rounds"] += 1
        nxt = {s: state[s] | system.eval(s, state, work) for s in system.slots}
        if nxt == state:
            return state, dict(work)
        state = nxt


def components(deps):
    """Tarjan; returned SCCs are in dependency-first order."""
    serial, numbers, low, stack, active, out = 0, {}, {}, [], set(), []

    def visit(v):
        nonlocal serial
        numbers[v] = low[v] = serial
        serial += 1
        stack.append(v)
        active.add(v)
        for w in sorted(deps[v]):
            if w not in numbers:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in active:
                low[v] = min(low[v], numbers[w])
        if low[v] == numbers[v]:
            group = []
            while True:
                w = stack.pop()
                active.remove(w)
                group.append(w)
                if w == v:
                    break
            out.append(tuple(sorted(group)))
    for slot in sorted(deps):
        if slot not in numbers:
            visit(slot)
    return out


class Queries:
    """Memoized SCC queries with dependency value revalidation across revisions.

    This uses a conservative static dependency superset, not Salsa internals.
    Dirty cycles restart at bottom; changed dependencies can remove values.
    Query lookup/revalidation and body work are counted separately.
    """
    def __init__(self):
        self.cache = {}

    def run(self, system, roots=None, eager=False, seed=None):
        state, work = system.bottom(), Counter(global_rounds=0)
        if seed:
            state.update({s: frozenset(v) for s, v in seed.items() if s in state})
        groups = components(system.deps)
        group_for = {s: i for i, g in enumerate(groups) for s in g}
        done = set()

        def query(i):
            work["query_lookups"] += 1
            if i in done:
                return
            group = groups[i]
            external = sorted(set().union(*(system.deps[s] for s in group)) - set(group))
            for other in sorted({group_for[d] for d in external}):
                query(other)
            fingerprint = (tuple((s, system.keys[s]) for s in group),
                           tuple((s, state[s]) for s in external))
            work["revalidation_edges"] += len(external)
            previous = self.cache.get(group)
            if previous is not None and previous[0] == fingerprint:
                state.update(previous[1])
                work["green_components"] += 1
            else:
                cyclic = len(group) > 1 or group[0] in system.deps[group[0]]
                while True:
                    nxt = {s: state[s] | system.eval(s, state, work) for s in group}
                    if cyclic:
                        work["local_scc_rounds"] += 1
                    same = all(state[s] == nxt[s] for s in group)
                    state.update(nxt)
                    if same or not cyclic:
                        break
                self.cache[group] = (fingerprint, {s: state[s] for s in group})
                work["computed_components"] += 1
            done.add(i)

        demanded = system.slots if eager or roots is None else roots
        todo, materialized = deque(demanded), set()
        while todo:
            slot = todo.popleft()
            if slot in materialized:
                continue
            materialized.add(slot)
            query(group_for[slot])
            # A returned reference is not a fully observed type until its
            # reachable field cells have been requested as well.
            for heap in sorted(state[slot]):
                for field in system.program.sites[heap][1]:
                    todo.append(heap + "." + field)
        work["queried_slots"] = sum(len(groups[i]) for i in done)
        return state, dict(work)


@dataclass(frozen=True)
class Summary:
    """A positive guarded equation scheme with free boundary variables.

    Local variables are fresh for each instantiation. Captured heap cells stay
    boundary variables, not generalized mutable state. This is a restricted
    compositional summary language, not principal MLsub scheme inference.
    """
    local: tuple
    formal: tuple
    cyclic: bool

    def instantiate(self, system, arguments, work):
        state = {**arguments, **{s: EMPTY for s in self.local}}
        while True:
            nxt = {s: state[s] | system.eval(s, state, work) for s in self.local}
            if self.cyclic:
                work["local_scc_rounds"] += 1
            same = all(state[s] == nxt[s] for s in self.local)
            state.update(nxt)
            if same or not self.cyclic:
                return {s: state[s] for s in self.local}


class Summaries:
    """Bottom-up SCC schemes, with finite head-specialized method instances.

    The eight-case comparison uses only positive guarded schemes. The true
    forall/fresh-variable Simple-sub experiment is pure_scheme_examples().
    Retains prior instances for this three-revision experiment; production
    would need revision GC and measured summary-size limits.
    """
    def __init__(self):
        self.templates, self.instances = {}, {}

    def run(self, system):
        state, work = system.bottom(), Counter(global_rounds=0)
        for group in components(system.deps):
            external = tuple(sorted(set().union(*(system.deps[s] for s in group)) - set(group)))
            template_key = (tuple((s, system.keys[s]) for s in group), external)
            work["summary_lookups"] += 1
            if template_key not in self.templates:
                self.templates[template_key] = Summary(group, external,
                                                       len(group) > 1 or group[0] in system.deps[group[0]])
                work["summary_builds"] += 1
            template = self.templates[template_key]
            arguments = {s: state[s] for s in template.formal}
            key = (template_key, tuple(arguments.items()))
            work["boundary_arguments"] += len(arguments)
            if key not in self.instances:
                self.instances[key] = template.instantiate(system, arguments, work)
                work["summary_instantiations"] += 1
            else:
                work["cached_instances"] += 1
            state.update(self.instances[key])
        work["retained_instances"] = len(self.instances)
        return state, dict(work)


def datalog(p, prior=None):
    """Additions reuse the actual engine; deletion falls back to full rebuild."""
    inputs = set(p.engine.inputs)
    old = set(prior.engine.inputs) if prior else set()
    reuse = prior is not None and old <= inputs
    q = prior if reuse else clone_program(p)
    if reuse:
        q.sites, q.slots, q.roots = dict(p.sites), set(p.slots), dict(p.roots)
        q.engine.work.clear()
        q.engine.firings.clear()
        for rel, row in sorted(inputs - old):
            q.fact(rel, *row)
    q.solve()
    return q, {**q.engine.stats(), "reused": reuse,
               "deletion_rebuild": prior is not None and not reuse}


def pure_scheme_examples():
    """Actual fresh instantiation of forall a. a -> Array[a], using constraints's solver.

    A deliberately small algebraic-subtyping fragment, not general Ruby
    polymorphism. Environment/captured mutable variables must not be quantified.
    """
    def instantiate(shared):
        s = sub.Solver()
        generic = s.var("shared") if shared else None
        roots = {}
        for call, atom in (("integer_call", "int"), ("string_call", "str")):
            a = generic if shared else s.var(call + "/a")
            r = s.node("array", a)
            fn = s.node("fn", a, r)
            out = s.var(call + "/out")
            expected = s.node("fn", s.node(atom), out)
            s.add(fn, expected)  # contravariant argument, covariant result
            roots[call] = out
        s.solve()
        g = sub.Graph(s, roots)
        return {"pairs": s.work["pairs_processed"], "equations": g.equations(),
                "first_admits_string": g.accepts("integer_call", ("array", ("str",)))}
    return {"monomorphic": instantiate(True), "fresh_scheme": instantiate(False)}


def regular_crosscheck(name, graph):
    """Independent regular equations for the five shared equation conditions."""
    if name not in ("self", "cycle2", "cycle3", "merge2", "param"):
        return None
    typer = fold.Typer()
    eqs, initial = fold.shapes(typer)[name]
    truth = fold.solve(eqs, typer)
    # Convert an constraints comparison graph to regular's canonical regular graph.
    def convert(root):
        g = {}
        for i, transitions in enumerate(graph.states):
            arms = []
            for head, children in transitions.items():
                n = len(graph.states) + len(g)
                tag = {"model_u": "untyped", "model_var": "var"}.get(head, head)
                g[n] = (tag, *children) if children else ("leaf", tag)
                arms.append(n)
            g[i] = ("union", frozenset(arms)) if arms else ("leaf", "bot")
        return fold.canonicalize(g, root)
    matches = {key: convert(graph.roots[key.lower()]) == ty for key, ty in truth.items()}
    old = fold.run(name, eqs, initial, "ref2")
    return {"regular_equation_equality": matches, "ref2_status": old.status,
            "ref2_sweeps_including_verification": old.rounds + 1,
            "ref2_body_evaluations": (old.rounds + 1) * len(eqs),
            "ref2_backstops": old.backstops}


def independent_root_check(name, graph, summary=False):
    """Closed-form expected root equations, separate from slot instruction IR.

    f2's head-summary condition distinguishes values under a Hash from values
    under an Array. This is exact for the specified site/head abstraction, not
    for concrete depths, keys, equality, mutation or program termination.
    """
    if name in ("self", "cycle2", "cycle3", "merge2", "param"):
        _, expected = base.solve_equations(base.m1.CASES[name][0])
        names = {alias: alias.upper() for alias in graph.roots}
    else:
        s = sub.Solver()
        nil, integer, string = (s.node(k) for k in ("nil", "int", "str"))
        if name == "chain64":
            roots = {alias: integer for alias in graph.roots}
        elif name == "reembed_safe":
            b = s.var("B")
            s.add(s.node("record_b", s.join(nil, b)), b)
            roots = {"b": b, "r": s.join(nil, s.node("record_a", b))}
        elif name == "f2" and not summary:
            j = s.var("J")
            s.add(s.join(nil, integer, string, s.node("array", j), s.node("hash", string, j)), j)
            roots = {"inner": j, "tree": j}
        elif name == "f2":
            h = s.var("H")
            a = s.node("array", s.join(integer, string, h))
            s.add(s.node("hash", string, s.join(a, h, integer, nil)), h)
            roots = {"inner": h, "tree": h}
        else:
            raise KeyError(name)
        s.solve()
        expected = sub.Graph(s, roots)
        names = {name: name for name in roots}
    return {name: graph.below(name, expected, other) and expected.below(other, graph, name)
            for name, other in names.items()}


def handoff_reference(name):
    """Run regular's actual ref2 controller, with two explicitly labeled adapters.

    Safe re-embedding uses regular's generic Hash projection, which forgets record
    labels; the main controller comparison retains the precise record sites.
    The imported runner's diagnostic cap is raised for chain64, never hit.
    """
    original_shapes = fold.shapes

    def expanded(typer):
        shapes = original_shapes(typer)
        shapes["chain64"] = ({"R%d" % i: (lambda env, j=i + 1: env["R%d" % j]) for i in range(63)},
                             {"R%d" % i: typer.R0 for i in range(64)})
        shapes["chain64"][0]["R63"] = lambda env: typer.INT
        shapes["reembed_safe"] = ({"F": lambda env: typer.union_many(typer.NIL,
            typer.hsh(typer.SYM, typer.hsh(typer.SYM, typer.union_of(typer.NIL, typer.hvalue(env["F"])))) )},
                                    {"F": typer.R0})
        return shapes

    fold.shapes = expanded
    try:
        typer = fold.Typer()
        equations, initial = expanded(typer)[name]
        result = fold.run(name, equations, initial, "ref2", rounds=128)
    finally:
        fold.shapes = original_shapes
    if name in ("self", "cycle2", "cycle3", "merge2", "param", "chain64"):
        expected = fold.solve(equations, typer)
    elif name == "f2":
        # regular's f2_R copies projected input children; it does not flow the
        # single monomorphic recursive callee return into every map/to_h cell.
        # Its least equations are therefore more correlated than our full
        # monovariant call lowering. Compare its own semantics explicitly.
        h, a = fold.mkref("H"), fold.mkref("A")
        solved = fold.tie({"H": fold.hsh(fold.STR, fold.union_many(fold.INT, fold.NIL, a, h)),
                           "A": fold.arr(fold.union_many(fold.INT, fold.STR, h)),
                           "R": fold.union_many(fold.NIL, fold.INT, fold.STR, a, h)})
        expected = {"R": solved["R"], "P": solved["R"]}
    else:
        expected = fold.tie({"F": fold.union_of(fold.NIL, fold.hsh(fold.SYM, fold.mkref("B"))),
                             "B": fold.hsh(fold.SYM, fold.union_of(fold.NIL, fold.mkref("B")))})
        expected = {"F": expected["F"]}
    details = {"status": result.status, "exact": result.state == expected,
            "sweeps_including_verification": result.rounds + 1,
            "equation_body_evaluations": (result.rounds + 1) * len(equations),
            "backstops": result.backstops,
            "same_semantics_as_main": name not in ("f2", "reembed_safe"),
            "condition": "regular/ref2/generic-Hash-safe" if name == "reembed_safe" else (
                "regular/ref2/f2-projected-children" if name == "f2" else "regular/ref2")}
    if name == "f2":
        details["array_nil_witness"] = {
            "regular_accepts": fold.covers(result.state["R"], fold.arr(fold.NIL)),
            "monovariant_call_lowering_accepts": dl.TypeGraph(make_case("f2").solve()).accepts(
                "tree", ("array", ("nil",)))}
    return details


def dynamics_case():
    """Late target discovery: the receiver selects a new callee after an edit."""
    p = dl.Program("dynamic_dispatch")
    p.literal("recv", "int")
    p.literal("arg", "str")
    p.literal("int/R", "int")
    p.literal("str/R", "nil")
    p.slot("int/P"), p.slot("str/P"), p.slot("out")
    p.fact("Method", "int", "m", "int/P", "int/R")
    p.fact("Method", "str", "m", "str/P", "str/R")
    p.fact("Send", "call", "recv", "m", "arg", "out")
    p.roots = {"out": "out"}
    return p
