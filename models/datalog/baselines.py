"""Read-only adapters to the two earlier executable models.

No source is changed and no bytecode is written beside imported model files.
M1's widening policy is called unmodified. Its counter includes the final
unchanged-state transfer used to detect convergence.
"""
import importlib.util
from collections import Counter
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


m1 = load("witness_model", ROOT / "models/witness/witness_model.py")
round1 = load("constraint_solver", ROOT / "models/constraints/solver.py")


def translate(solver, term, refs):
    if term[0] == "slot":
        return refs[term[1]]
    if term[0] == "union":
        return solver.join(*(translate(solver, t, refs) for t in term[1]))
    head = {"untyped": "model_u", "var": "model_var", "widened": "top"}.get(term[0], term[0])
    return solver.node(head, *(translate(solver, t, refs) for t in term[1:]))


def solve_equations(equations, outputs=None):
    solver = round1.Solver()
    refs = {key: solver.var(key) for key in equations}
    symbolic = {key: ("slot", key) for key in equations}
    for key, fn in equations.items():
        solver.add(translate(solver, fn(symbolic), refs), refs[key])
    solver.solve()
    graph = round1.Graph(solver, refs if outputs is None else {key: refs[key] for key in outputs})
    return solver, graph


def graph_from_sites(program):
    """Head/spine *comparison view*, excluded from the Datalog engine counters.

    This intentionally forgets alternative-site correlation to match round 1's
    abstraction. It is NOT an independent baseline for projection/dispatch.
    """
    solver = round1.Solver()
    refs = {slot: solver.var(slot) for slot in program.slots}
    constructors = {}
    for site, (kind, fields) in program.sites.items():
        constructors[site] = solver.node(kind, *(refs[site + "." + f] for f in fields))
    for slot, site in sorted(program.engine.rows("Pt")):
        solver.add(constructors[site], refs[slot])
    solver.solve()
    return round1.Graph(solver, {name: refs[s] for name, s in program.roots.items()})


def run_m1(name, equations, initial, rounds=36):
    trace, evaluations = [], 0
    first = next(iter(equations))
    wrapped, calls = {}, Counter()
    originals = {n: getattr(m1, n) for n in ("union_of", "push", "covers", "fold")}
    for key, fn in equations.items():
        def body(state, _key=key, _fn=fn):
            nonlocal evaluations
            evaluations += 1
            if _key == first:
                trace.append(dict(state))
            return _fn(state)
        wrapped[key] = body
    try:
        for name_, original in originals.items():
            def counted(*args, _name=name_, _fn=original, **kwargs):
                calls[_name] += 1
                return _fn(*args, **kwargs)
            setattr(m1, name_, counted)
        message = m1.run(name, wrapped, initial, "rule", rounds=rounds)
    finally:
        for name_, fn in originals.items():
            setattr(m1, name_, fn)
    converged = "converged after" in message
    # If capped, trace[-1] is the INPUT to the final transfer, not the final result.
    # Do not publish that row as a converged type.
    final = trace[-1] if converged else None
    solver = round1.Solver()
    if final is not None:
        graph = round1.Graph(solver, {k: translate(solver, t, {}) for k, t in final.items()})
    else:
        graph = None
    result = {"message": message, "converged": converged,
              "reported_rounds": len(trace) - 1 if converged else None,
              "sweeps_executed": len(trace), "body_evaluations": evaluations,
              "recursive_function_calls": dict(calls),
              "equations": graph.equations() if graph is not None else None}
    return result, graph


def extra_equations(name, length=64):
    if name == "argument_tree":
        return {"P": lambda s: m1.union_of(("nil",), m1.hsh(s["P"], s["P"])),
                "R": lambda s: m1.INT}, {"P": m1.VAR, "R": m1.U}
    if name == "chain":
        eqs = {"R%d" % i: (lambda s, j=i + 1: s["R%d" % j]) for i in range(length - 1)}
        eqs["R%d" % (length - 1)] = lambda s: m1.INT
        return eqs, {key: m1.U for key in eqs}
    raise KeyError(name)
