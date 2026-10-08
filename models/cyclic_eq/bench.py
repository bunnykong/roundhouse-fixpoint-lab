"""Serial public benchmark; all artifacts are local, stdlib only.

python3 -B -m models.cyclic_eq.bench --output models/cyclic_eq/evidence
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import time
import csv

from .compare import Automaton, equivalent, included
from .fixtures import LAB_ROOT, adversary, constraints, canonical, doubled, regular, random_cyclic, renamed, workbench_shapes
from .reference import repaired_canonical
from .tree import tree_included
from .compatibility import frozen_equal


def measure(fn, repetitions):
    first = fn()
    samples = []
    for _ in range(repetitions):
        t = time.perf_counter()
        result = fn()
        elapsed = (time.perf_counter() - t) * 1000
        samples.append((elapsed, result))
        assert result.holds == first.holds
    sample = sorted(samples, key=lambda p: p[0])[len(samples) // 2]
    result = sample[1]
    return {"holds": result.holds, "method": result.method, "reason": result.reason,
            "median_ms": round(statistics.median(p[0] for p in samples), 6), "stats": result.stats,
            "timing_samples_ms": [round(p[0], 6) for p in samples]}


def eager_from_compact(oracle, a):
    solver = oracle.Solver()
    refs = [solver.var("state%d" % i) for i in range(len(a.nodes))]
    for i, n in enumerate(a.nodes):
        if n[0] == "union":
            term = solver.join(*(refs[c] for c in n[1]))
        elif n[0] in ("array", "hash"):
            term = solver.node(n[0], *(refs[c] for c in n[1:]))
        else:
            term = solver.node({"bot": "bottom", "widened": "top"}.get(n[1], n[1]))
        solver.add(term, refs[i])
    solver.solve()
    return oracle.Graph(solver, {"root": refs[a.root]})


def adversarial(oracle, repetitions):
    rows = []
    for n in (4, 8, 12, 16, 20):
        a, solver = adversary(n, oracle)
        b = renamed(a, 1307)
        changed = Automaton(tuple(("leaf", "sym") if node == ("leaf", "int") else node for node in b.nodes), b.root)
        variants = [("renamed copy", b, True), ("two disjoint copies in a union", doubled(b), True),
                    ("Integer leaf changed to Symbol", changed, False)]
        for condition, b, expected in variants:
            row = {"condition": "constraints nth-from-end Hash; " + condition, "n": n,
                   "compact_left_nodes": len(a.nodes), "compact_right_nodes": len(b.nodes),
                   "solver_pairs": solver.work["pairs_processed"],
                   "eager_minimal_states_formula": 2 ** n + 1,
                   "expected_equal": expected, "expected_included": expected}
            row["HKC"] = measure(lambda: equivalent(a, b, fast=False, seconds=3), repetitions)
            row["antichain"] = measure(lambda: included(a, b, fast=False, budget=400_000, seconds=3),
                                        1 if n >= 12 else repetitions)
            row["simulation_eq"] = measure(lambda: equivalent(a, b, seconds=3), repetitions)
            row["simulation_inc"] = measure(lambda: included(a, b, seconds=3), repetitions)
            row["tree_antichain"] = measure(lambda: tree_included(a, b, seconds=3), repetitions)
            if n <= 12:
                t = time.perf_counter()
                graph = oracle.Graph(solver, {"Q0": solver.var("Q0")})
                other = eager_from_compact(oracle, b)
                inc = graph.below("Q0", other, "root")
                eq = inc and other.below("root", graph, "Q0")
                row["eager"] = {"ms_single_sample": round((time.perf_counter() - t) * 1000, 6),
                                **graph.sizes(), "right_states": len(other.states), "work": dict(graph.work),
                                "equal": eq, "included": inc,
                                "scope": "left Graph + encode/solve right graph + right Graph + two comparisons"}
                assert graph.sizes()["states"] == 2 ** n + 1
                assert eq is expected and inc is expected
                row["eager_oracle_agreement"] = all(row[k]["holds"] == (eq if k in ("HKC", "simulation_eq") else inc)
                                                     for k in ("HKC", "antichain", "simulation_eq",
                                                               "simulation_inc", "tree_antichain"))
            else:
                row["eager"] = {"status": "not run; exponential output above 4097-state oracle cap"}
                row["eager_oracle_agreement"] = None
            rows.append(row)
            print("adversary", n, condition, "HKC", row["HKC"]["stats"].get("hkc_expanded"),
                  "AC", row["antichain"]["holds"], row["antichain"]["stats"].get("antichain_expanded"), flush=True)
    return rows


def check_pairs(oracle, pairs):
    counts = Counter()
    discrepancies, timings = [], {k: [] for k in ("HKC", "antichain", "fast_eq", "fast_inc", "frozen_equal", "oracle")}
    visits = {k: 0 for k in timings}
    canonical_cache, repaired_cache = {}, {}

    def reg(a):
        if a not in canonical_cache:
            canonical_cache[a] = canonical(oracle, a)
        return canonical_cache[a]

    def fixed(a):
        if a not in repaired_cache:
            repaired_cache[a] = repaired_canonical(oracle, a)
        return repaired_cache[a]

    pair_rows = []
    for label, a, b in pairs:
        t = time.perf_counter()
        ca, cb = reg(a), reg(b)
        expected_eq, expected_inc = ca == cb, oracle.covers(cb, ca)
        timings["oracle"].append((time.perf_counter() - t) * 1000)
        counts["pairs"] += 1
        counts["canonical_states_materialized"] += len(ca.nodes) + len(cb.nodes)
        results = {
            "HKC": equivalent(a, b, fast=False), "antichain": included(a, b, fast=False),
            "fast_eq": equivalent(a, b), "fast_inc": included(a, b),
            "frozen_equal": frozen_equal(a, b, oracle=oracle, fast=False)}
        for key, result in results.items():
            expected = expected_eq if key in ("HKC", "fast_eq", "frozen_equal") else expected_inc
            counts[key + "_agreements"] += result.holds == expected
            counts[key + "_true"] += result.holds is True
            counts[key + "_unknown"] += result.holds is None
            counts[key + "_choice_game"] += "choice-game" in result.method
            counts[key + "_simulation_fast"] += result.method in ("simulation", "bisimulation")
            timings[key].append(result.elapsed_ms)
            visits[key] += result.stats.get("hkc_expanded", 0) + result.stats.get("antichain_expanded", 0) + \
                           result.stats.get("game_pairs", 0) + result.stats.get("simulation_pairs", 0)
            if result.holds != expected:
                discrepancies.append({"label": label, "algorithm": key, "actual": result.holds,
                                      "frozen_oracle": expected, "left": a.nodes, "left_root": a.root,
                                      "right": b.nodes, "right_root": b.root,
                                      "repaired_canonical_equal": fixed(a) == fixed(b)})
        if results["HKC"].holds == (fixed(a) == fixed(b)):
            counts["repaired_equality_agreements"] += 1
        pair_rows.append({"label": label, "frozen_equal": expected_eq, "frozen_included": expected_inc,
                          "results": {key: {"holds": value.holds, "method": value.method,
                                            "elapsed_ms": value.elapsed_ms, "stats": value.stats}
                                      for key, value in results.items()}})
    return {"counts": dict(counts), "discrepancies": discrepancies,
            "time_ms": {k: {"sum": round(sum(v), 6), "median": round(statistics.median(v), 6),
                            "max": round(max(v), 6)} for k, v in timings.items()},
            "pairs_visited_total": visits,
            "pair_rows": pair_rows,
            "oracle_timing_note": "memoized canonicalization plus covers; not a cold per-pair canonicalization baseline"}


def shapes(oracle):
    shapes = workbench_shapes(oracle)
    roots = [(name + ":" + slot, a) for name, slots in shapes.items() for slot, a in slots.items()]
    pairs = [(name + " vs " + other, a, b) for name, a in roots for other, b in roots]
    for name, a in roots:
        pairs.extend(((name + " renamed", a, renamed(a)), (name + " doubled", a, doubled(a))))
    result = check_pairs(oracle, pairs)
    result["shapes"] = {name: {slot: len(a.nodes) for slot, a in slots.items()} for name, slots in shapes.items()}
    return result


def randoms(oracle, count):
    pairs = []
    for seed in range(count):
        a = random_cyclic(seed, size=8 + seed % 3, records=True, bottom=True)
        pairs.extend((("random %d renamed" % seed, a, renamed(a, seed + 123)),
                      ("random %d unrelated" % seed, a,
                       random_cyclic(seed + 10_000, size=8 + seed % 3, records=True, bottom=True))))
        if seed % 4 == 0:
            pairs.append(("random %d doubled" % seed, a, doubled(a)))
    return check_pairs(oracle, pairs)


def tree_checks(count):
    from .test_cyclic_eq import tree_oracle
    rows, complete, agreement = [], 0, 0
    # The independent unpruned powerset oracle stays feasible on tiny cycles.
    for seed in range(count):
        a = random_cyclic(seed, size=5, records=True)
        b = renamed(a) if seed % 2 else random_cyclic(seed + 700, size=5, records=True)
        if any(n == ("leaf", "widened") for n in a.nodes + b.nodes):
            continue
        expected = tree_oracle(a, b)
        actual = tree_included(a, b)
        complete += expected is not None
        agreement += expected is not None and actual.holds == expected
        rows.append({"seed": seed, "oracle": expected, "holds": actual.holds,
                     "time_ms": actual.elapsed_ms, "stats": actual.stats})
    return {"oracle_complete": complete, "agreements": agreement, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=LAB_ROOT / "models/cyclic_eq/evidence")
    parser.add_argument("--repetitions", type=int, default=7)
    parser.add_argument("--random-count", type=int, default=240)
    args = parser.parse_args()
    allowed = LAB_ROOT / "models/cyclic_eq"
    if not args.output.resolve().is_relative_to(allowed.resolve()):
        parser.error("output must stay inside models/cyclic_eq")
    if args.repetitions < 1 or args.random_count < 1:
        parser.error("counts must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    oa, of = constraints(), regular()
    sources = list(Path(__file__).parent.glob("*.py")) + [
        LAB_ROOT / "models/constraints/solver.py", LAB_ROOT / "models/constraints/solver.py",
        LAB_ROOT / "models/fold/fold_model.py", LAB_ROOT / "models/fold/witness_model.py"]
    result = {"condition": "cyclic-eq-v1; public synthetic types; rigid bot covers; pointwise Hash/Array joins",
              "timestamp_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
              "platform": platform.platform(), "repetitions": args.repetitions,
              "timing_scope": "cold Session/epsilon preprocessing plus comparison; median wall time on shared host",
              "source_sha256": {str(p.relative_to(LAB_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    result["adversary"] = adversarial(oa, args.repetitions)
    result["shapes"] = shapes(of)
    print("shapes", result["shapes"]["counts"], flush=True)
    result["random"] = randoms(of, args.random_count)
    print("random", result["random"]["counts"], flush=True)
    result["finite_tree"] = tree_checks(80)
    (args.output / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    with (args.output / "adversary.csv").open("w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(("condition", "n", "algorithm", "holds", "median_ms", "obligations", "reason"))
        for row in result["adversary"]:
            for key in ("HKC", "antichain", "simulation_eq", "simulation_inc", "tree_antichain"):
                r = row[key]
                s = r["stats"]
                visits = s.get("hkc_expanded", s.get("antichain_expanded", s.get("simulation_pairs", s.get("tree_popped", 0))))
                writer.writerow((row["condition"], row["n"], key, r["holds"], r["median_ms"], visits, r["reason"]))
    print("wrote", args.output / "results.json", flush=True)


if __name__ == "__main__":
    main()
