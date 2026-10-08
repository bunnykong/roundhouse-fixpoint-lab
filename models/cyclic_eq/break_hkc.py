"""A compact permutation family that defeats HKC's union-context pruning.

python3 -B -m models.cyclic_eq.break_hkc --output models/cyclic_eq/evidence/permutation.json
Rotation and an adjacent transposition generate S_n. Start with k=n//2
states. All C(n,k) reachable subsets are incomparable; no strict union context
of a previously related k-subset helps relate another k-subset.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import time

from .bench import eager_from_compact, measure
from .compare import Automaton, equivalent, included
from .fixtures import LAB_ROOT, constraints, renamed
from .tree import tree_included


def permutation(n):
    if n < 2:
        raise ValueError("n must be >= 2")
    nodes = [None] * n + [("leaf", "str"), ("leaf", "int")]
    for i in range(n):
        array, hash_ = len(nodes), len(nodes) + 1
        swap = 1 if i == 0 else 0 if i == 1 else i
        nodes.extend((("array", (i + 1) % n), ("hash", n, swap)))
        nodes[i] = ("union", (array, hash_, n + 1) if i == 0 else (array, hash_))
    root = len(nodes)
    nodes.append(("union", tuple(range(n // 2))))
    return Automaton(tuple(nodes), root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=LAB_ROOT / "models/cyclic_eq/evidence/permutation.json")
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to((LAB_ROOT / "models/cyclic_eq").resolve()):
        parser.error("output must stay inside models/cyclic_eq")
    oracle = constraints()
    result = {"condition": "permutation-k-subsets-v1; renamed copies; simulation off for HKC/AC",
              "timestamp_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
              "source_sha256": {str(p.relative_to(LAB_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in Path(__file__).parent.glob("*.py")}, "rows": []}
    for n in (4, 8, 12, 16, 20):
        a, repetitions = permutation(n), 3 if n <= 8 else 1
        b = renamed(a, 2134)
        row = {"n": n, "compact_nodes_each": len(a.nodes), "k": n // 2,
               "reachable_k_subsets_formula": math.comb(n, n // 2), "expected_equal": True}
        for key, fn in (("HKC", lambda: equivalent(a, b, fast=False, seconds=3)),
                        ("antichain", lambda: included(a, b, fast=False, seconds=3)),
                        ("simulation_eq", lambda: equivalent(a, b, seconds=3)),
                        ("simulation_inc", lambda: included(a, b, seconds=3)),
                        ("tree_antichain", lambda: tree_included(a, b, seconds=3))):
            row[key] = measure(fn, repetitions)
        if n == 12:
            row["HKC_raised_budget"] = measure(lambda: equivalent(a, b, fast=False, budget=10_000_000, seconds=5), 1)
        if n <= 12:
            t = time.perf_counter()
            graph, other = eager_from_compact(oracle, a), eager_from_compact(oracle, b)
            row["eager"] = {"states": len(graph.states), "equal": graph.below("root", other, "root") and
                            other.below("root", graph, "root"), "ms_single": (time.perf_counter() - t) * 1000}
        result["rows"].append(row)
        print(n, "subsets", row["reachable_k_subsets_formula"],
              "HKC", row["HKC"]["holds"], row["HKC"]["stats"].get("hkc_expanded"),
              row["HKC"]["median_ms"], flush=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
