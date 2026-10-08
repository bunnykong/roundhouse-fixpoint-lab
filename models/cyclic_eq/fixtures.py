"""Public compact adversary and deterministic, seeded cyclic input generators."""
import importlib.util
from pathlib import Path
import random
import sys

from .compare import Automaton, children, remap

LAB_ROOT = Path(__file__).resolve().parents[2]


def load_oracle(name, relative):
    filename = LAB_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    sys.path.insert(0, str(filename.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def regular():
    return load_oracle("cyclic_eq_regular", "models/fold/fold_model.py")


def constraints():
    return load_oracle("cyclic_eq_constraints", "models/constraints/solver.py")


def from_solver(solver, root):
    nodes = []
    for i, n in enumerate(solver.nodes):
        if n.kind == "var":
            nodes.append(("union", tuple(sorted(solver.lower[i]))))
        elif n.kind == "join":
            nodes.append(("union", n.args))
        elif n.kind in ("array", "hash"):
            nodes.append((n.kind,) + n.args)
        else:
            nodes.append(("leaf", {"top": "widened", "bottom": "bot",
                                   "model_u": "untyped", "model_var": "var"}.get(n.kind, n.kind)))
    return Automaton(tuple(nodes), root)


def adversary(n, oracle):
    """Same allocations/constraints as constraints subset_blowup, before Graph()."""
    s = oracle.Solver()
    q = [s.var("Q%d" % i) for i in range(n + 1)]
    st = s.node("str")
    s.add(s.join(s.node("array", q[0]), s.node("hash", st, q[0]),
                 s.node("hash", st, q[1])), q[0])
    for i in range(1, n):
        s.add(s.join(s.node("array", q[i + 1]), s.node("hash", st, q[i + 1])), q[i])
    s.add(s.node("int"), q[-1])
    s.solve()
    return from_solver(s, q[0]), s


def renamed(automaton, seed=1):
    order = list(range(len(automaton.nodes)))
    random.Random(seed).shuffle(order)
    ids = {old: new for new, old in enumerate(order)}
    nodes = []
    for old in order:
        n = automaton.nodes[old]
        if n[0] == "leaf":
            nodes.append(n)
        elif n[0] in ("array", "hash"):
            nodes.append((n[0],) + tuple(ids[c] for c in children(n)))
        elif n[0] == "record":
            nodes.append(("record", tuple((k, ids[c]) for k, c in n[1])))
        else:
            nodes.append((n[0], tuple(ids[c] for c in n[1])))
    return Automaton(tuple(nodes), ids[automaton.root])


def doubled(automaton):
    nodes = automaton.nodes + tuple(remap(n, len(automaton.nodes)) for n in automaton.nodes)
    return Automaton(nodes + (("union", (automaton.root, automaton.root + len(automaton.nodes))),), len(nodes))


def random_cyclic(seed, size=8, tuples=True, records=False, bottom=False):
    rng = random.Random(seed)
    nodes = [("leaf", "str"), ("leaf", "int")]
    kinds = ["array", "hash", "union", "leaf"] + (["tuple"] if tuples else []) + (["record"] if records else [])
    for i in range(2, size):
        kind = rng.choice(kinds)
        if kind == "leaf":
            nodes.append((kind, rng.choice(["str", "int", "sym", "nil", "widened"] + (["bot"] if bottom else []))))
        elif kind == "array":
            nodes.append((kind, rng.randrange(size)))
        elif kind == "hash":
            nodes.append((kind, rng.randrange(size), rng.randrange(size)))
        elif kind == "record":
            nodes.append((kind, tuple((k, rng.randrange(size)) for k in ("a", "b")[:rng.randrange(1, 3)])))
        else:
            nodes.append((kind, tuple(rng.randrange(size) for _ in range(rng.randrange(1, 4)))))
    # Guarantee a reachable guarded cycle, plus observable rigid leaves.
    nodes[2] = ("union", (0, 1, 3, 4))
    nodes[3] = ("array", 2)
    return Automaton(tuple(nodes), 2 if seed % 3 else size - 1)


def lower_records(a):
    """Exact-key Records -> Tuples with rigid key tags, for the regular oracle.

    Every Tuple receives a 'tuple_kind' tag so it cannot collide with a Record.
    Constructor depth changes; only equality/inclusion is used as an oracle.
    """
    nodes = list(a.nodes)
    for i, n in enumerate(a.nodes):
        if n[0] == "record":
            cs = []
            tag = len(nodes)
            nodes.append(("leaf", ("record_keys", tuple(k for k, _ in n[1]))))
            cs.append(tag)
            cs.extend(c for _, c in n[1])
            nodes[i] = ("tuple", tuple(cs))
        elif n[0] == "tuple":
            tag = len(nodes)
            nodes.append(("leaf", ("tuple_kind",)))
            nodes[i] = ("tuple", (tag,) + n[1])
    return Automaton(tuple(nodes), a.root)


def canonical(oracle, a):
    a = lower_records(a)
    return oracle.canonicalize(dict(enumerate(a.nodes)), a.root)


def workbench_shapes(oracle):
    out = {}
    typer = oracle.Typer()
    for name, (eqs, init) in oracle.shapes(typer).items():
        result = oracle.run(name, eqs, init, "ref2")
        if result.status != "converged":
            raise AssertionError((name, result.status))
        out[name] = {slot: Automaton.from_reg(reg) for slot, reg in result.state.items()}
    return out
