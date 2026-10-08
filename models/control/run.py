#!/usr/bin/env python3
"""One public reproduction: python3 models/control/run.py.

Writes only within this directory. Replays three sources with CRuby 4.0.7,
verifies emitted grammars with shape_oracle, runs tests, saves measured counters
and a source manifest. Python stdlib only. No real analyzer run is claimed.
"""
import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
import platform
import subprocess
from pathlib import Path
import model as m
import warm

OWN = Path(__file__).resolve().parent
OUT = OWN / "evidence"


def stable_state(state):
    return {s: sorted(hs) for s, hs in sorted(state.items())}


def truth(p):
    p = m.clone_program(p).solve()
    return p, m.points(p)


def compare_case(name, summary=False):
    original = m.make_case(name, summary)
    queries, eager, summaries = m.Queries(), m.Queries(), m.Summaries()
    delta_prior, previous_state = None, None
    results = {}
    for epoch, p in (("cold", original), ("add_call", m.edit_call(original)), ("delete_call", original)):
        expected_program, expected = truth(p)
        system = m.SlotSystem(p)
        cold, a = m.rounds(system)
        a["exact"] = cold == expected
        # Adds are safe warm seeds; on deletion the global controller rebuilds.
        if epoch == "add_call":
            updated, update_work = m.rounds(system, previous_state)
            update_work["exact"] = updated == expected
        else:
            update_work = {**a, "rebuild": epoch == "delete_call"}
        delta_prior, b = m.datalog(p, delta_prior)
        b["exact"] = m.points(delta_prior) == expected
        queried, c = queries.run(system)  # whole-program diagnostic condition
        c["exact"] = queried == expected
        ordered, ordered_work = eager.run(system, eager=True)
        ordered_work["exact"] = ordered == expected
        summarized, e = summaries.run(system)
        e["exact"] = summarized == expected
        previous_state = expected
        results[epoch] = {"slots": len(system.slots), "site_ids": len(p.sites),
                          "points_to_facts": sum(map(len, expected.values())),
                          "rounds_cold": a, "rounds_incremental": update_work,
                          "datalog": b, "queries": c, "ordered_eager": ordered_work, "summaries": e,
                          "bad_uses": sorted(expected_program.engine.rows("BadUse")),
                          "least_state_sha256": hashlib.sha256(json.dumps(stable_state(expected),
                                                                      sort_keys=True).encode()).hexdigest()}
        if epoch == "delete_call":
            # Deliberately unsafe retain-and-join, against independently cold truth.
            stale = truth(m.edit_call(original))[1]
            bad, bad_work = m.rounds(system, stale)
            excess = sorted((s, h) for s, hs in bad.items() for h in hs if h not in expected[s])
            results[epoch]["unsafe_warm"] = {**bad_work, "exact": bad == expected, "extra_facts": excess}
    exact_program, _ = truth(original)
    graph = m.base.graph_from_sites(exact_program)
    results["equations"] = graph.equations()
    results["independent_regular_check"] = m.regular_crosscheck(name, graph)
    results["independent_root_equations"] = m.independent_root_check(name, graph, summary)
    return results


def oracle_check(name, path):
    p = m.make_case("f2") if name == "canonical" else (
        warm.runtime_cycle2() if name == "cycle2" else warm.runtime_argument())
    if name == "canonical":
        p.roots = {"canonical_arg": "all/P", "canonical_ret": "all/R"}
        slots = {"TreesController#canonical:param:value": "canonical_arg",
                 "TreesController#canonical:return": "canonical_ret"}
    elif name == "cycle2":
        p.roots = {"walk_%d_%s" % (i, kind): "walk_%d/%s" % (i, suffix)
                   for i in range(2) for kind, suffix in (("arg", "P"), ("ret", "R"))}
        slots = {"TreesController#walk_%d:%s" % (i, event): "walk_%d_%s" % (i, alias)
                 for i in range(2) for event, alias in (("param:value", "arg"), ("return", "ret"))}
    else:
        p.roots = {"payload": "P", "ret": "R"}
        slots = {"ApplicationHelper#carry:param:payload": "payload", "ApplicationHelper#carry:return": "ret"}
    p.solve()
    rbs, mapping = OUT / (name + ".rbs"), OUT / (name + ".slots.json")
    rbs.write_text("\n".join(m.dl.TypeGraph(p).equations()) + "\n")
    mapping.write_text(json.dumps(slots, indent=2) + "\n")
    command = [sys.executable, str(warm.ORACLE / "check.py"), str(path), str(rbs),
               "--slots", str(mapping), "--json"]
    done = subprocess.run(command, text=True, capture_output=True)
    (OUT / (name + ".oracle.json")).write_text(done.stdout)
    if done.returncode:
        raise RuntimeError(done.stdout + done.stderr)
    portable = [str(Path(c).relative_to(m.ROOT)) if c.startswith(str(m.ROOT) + "/") else c for c in command]
    return {"command": portable, "exit_code": done.returncode, "report": name + ".oracle.json"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"condition": "finite-sites/positive-mono/v2; Float modeled before edit; all slots demanded; no caps",
               "counting": "slot-body evaluations vs grounded rule firings; not runtime speedups",
               "cases": {}, "summary_fragment": {}, "traces": {}, "counterexamples": warm.counterexamples()}
    for name in m.SHAPES:
        results["cases"][name] = compare_case(name)
        results["cases"][name]["handoff_reference"] = m.handoff_reference(name)
        # Positive SCC summary fragment: fresh finite argument-head instances
        # at f2, closed (no polymorphic free input) schemes for other shapes.
        # Not a full MLsub implementation; generalization/instantiation is
        # independently exercised below with the unchanged Simple-sub solver.
        results["summary_fragment"][name] = compare_case(name, summary=True)
    results["polymorphic_instantiation"] = m.pure_scheme_examples()
    for name in ("canonical", "cycle2", "argument_tree"):
        path = OUT / (name + ".app.jsonl")
        invocation = warm.record(name, path)
        events = warm.records(path)
        results["traces"][name] = {**warm.warm_result(name, events), "record": invocation,
                                   "oracle": oracle_check(name, path)}
        if name == "canonical":
            results["counterexamples"]["unsound_model"] = warm.unsound_model(events)
    # An intentionally mismatched harness: added Float calls are not in the app
    # analyzed above. It is a bad seed for that condition, not a theorem failure.
    path = OUT / "canonical.external-fuzz.jsonl"
    invocation = warm.record("canonical", path, fuzz=True)
    results["traces"]["wrong_harness"] = {**warm.warm_result("canonical", warm.records(path)),
                                         "record": invocation}
    tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(OWN),
                            "-p", "test_*.py", "-v"], text=True, capture_output=True, cwd=m.ROOT)
    (OUT / "tests.log").write_text(tests.stdout + tests.stderr)
    if tests.returncode:
        raise RuntimeError(tests.stdout + tests.stderr)
    for path in OWN.glob("*.py"):
        ast.parse(path.read_text(), filename=str(path), feature_version=(3, 9))
    results["validation"] = {"tests_exit": tests.returncode, "python39_syntax": True}
    (OUT / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    inputs = list(OWN.glob("*.py")) + [m.ROOT / p for p in (
        "models/datalog/model.py", "models/datalog/cases.py", "models/datalog/baselines.py",
        "models/fold/fold_model.py", "models/fold/witness_model.py",
        "models/witness/witness_model.py", "models/constraints/solver.py",
        "oracle/record.rb", "oracle/check.py")]
    inputs += [m.ROOT / cmd for item in results["traces"].values() for cmd in item["record"]["command"]
               if cmd.endswith(".rb")]
    manifest = {"python": platform.python_version(), "platform": platform.platform(),
                "command": "python3 models/control/run.py",
                "sha256": {str(p.relative_to(m.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(set(inputs))}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    for name, r in results["cases"].items():
        cold = r["cold"]
        print(name, "rounds", cold["rounds_cold"]["body_evaluations"],
              cold["rounds_cold"]["global_rounds"], "queries", cold["queries"]["body_evaluations"],
              "delta", cold["datalog"]["rule_firings"])
    for name, r in results["traces"].items():
        print(name, "cold/warm/sparse", *(r[k]["global_rounds"] for k in ("cold", "trace_warm", "sparse_trace")),
              "equal", r["trace_equal"], "below", r["seed_below_lfp"])
    print("Evidence:", OUT.relative_to(m.ROOT))


if __name__ == "__main__":
    main()
