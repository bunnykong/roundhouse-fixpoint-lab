"""Public CRuby trace seeds with explicit source-to-allocation certificates.

record.rb records no allocation provenance. Therefore arbitrary container
parameters are NOT silently assigned to sites. These three hand-lowerings
provide the missing mapping from source semantics. A general adapter would
need origin instrumentation or a checked abstraction certificate.
"""
import sys
sys.dont_write_bytecode = True
import json
import subprocess
from collections import defaultdict
from pathlib import Path
import model as m

OWN = Path(__file__).resolve().parent
ORACLE = m.ROOT / "oracle"
SOURCE = m.ROOT / "reproductions"


def runtime_cycle2():
    p = m.dl.Program("runtime_cycle2/app")
    for i in range(2):
        ctx, nxt = "walk_%d" % i, "walk_%d" % (1 - i)
        param, ret = p.slot(ctx + "/P"), p.slot(ctx + "/R")
        hr, ar = p.slot(ctx + "/hash_recv"), p.slot(ctx + "/array_recv")
        key = p.slot(ctx + "/key")
        p.fact("Filter", param, "hash", hr)
        p.fact("Filter", param, "array", ar)
        p.fact("Load", hr, "key", key)
        p.fact("Load", hr, "value", p.slot(nxt + "/P"))
        p.fact("Load", ar, "elem", p.slot(nxt + "/P"))
        h = p.construct(ret, ctx + "/hash", "hash", {"key": key, "value": p.slot(nxt + "/R")}, False)
        a = p.construct(ret, ctx + "/array", "array", {"elem": nxt + "/R"}, False)
        p.fact("Produce", param, "hash", ret, h)
        p.fact("Produce", param, "array", ret, a)
        for kind in ("int", "str", "nil", "float", "sym"):
            p.fact("Filter", param, kind, ret)
        p.roots[ctx] = ret
    p.literal("key", "str")
    p.literal("one", "int")
    p.literal("x", "str")
    p.construct("literal_inner", "literal_inner_site", "hash", {"key": "key", "value": "x"})
    p.flow("one", "literal_elements")
    p.flow("literal_inner", "literal_elements")
    p.construct("literal_array", "literal_array_site", "array", {"elem": "literal_elements"})
    p.construct("walk_0/P", "literal_outer_site", "hash", {"key": "key", "value": "literal_array"})
    return p


def runtime_argument():
    p = m.dl.Program("runtime_argument/app")
    p.literal("P", "nil")
    p.literal("R", "int")
    p.construct("P", "wrap", "hash", {"key": "P", "value": "P"})
    p.roots = {"payload": "P", "ret": "R"}
    return p


def trace_command(name, output, fuzz=False):
    spec = {
        "canonical": (SOURCE / "f2_merge/app/controllers/trees_controller.rb", "TreesController#index", [], "canonical", "canonical:value",
                      "TreesController#canonical", []),
        "cycle2": (SOURCE / "cycle-2-width-2/app/controllers/trees_controller.rb", "TreesController#index", [],
                   "walk_0,walk_1", "walk_0:value,walk_1:value", "TreesController#walk_0", []),
        "argument_tree": (SOURCE / "argument-tree/app/helpers/application_helper.rb", "ApplicationHelper#carry", [3, None],
                          "carry", "carry:payload", "ApplicationHelper#carry", [6]),
    }[name]
    source, entry, args, returns, params, target, prefix = spec
    command = ["ruby", str(ORACLE / "record.rb"), "--source", str(source), "--entry", entry,
               "--args", json.dumps(args), "--returns", returns, "--params", params, "--output", str(output)]
    if fuzz:
        command += ["--fuzz", target, "--prefix-args", json.dumps(prefix), "--seed", "20261007",
                    "--count", "32", "--depth", "3", "--leaves", "Integer,Float,String,nil"]
    return command


def record(name, out, fuzz=False):
    version = subprocess.check_output(["ruby", "--version"], text=True).strip()
    if not version.startswith("ruby 4.0.7 "):
        raise RuntimeError("CRuby 4.0.7 required: " + version)
    command = trace_command(name, out, fuzz)
    done = subprocess.run(command, capture_output=True, text=True, check=True)
    portable = [str(Path(c).relative_to(m.ROOT)) if c.startswith(str(m.ROOT) + "/") else c for c in command]
    return {"command": portable, "ruby": version, "stderr": done.stderr.strip()}


def records(path):
    data = [json.loads(line) for line in path.read_text().splitlines()]
    if not data or data[0].get("ruby") != "4.0.7":
        raise ValueError("trace version mismatch")
    if data[-1].get("kind") != "complete":
        raise ValueError("incomplete trace")
    if data[-1].get("exceptions") or any(x.get("kind") == "error" for x in data):
        raise ValueError("failed trace")
    return [r for r in data if r.get("kind") == "value"]


ATOMS = {"Integer": "int", "Float": "float", "String": "str", "Symbol": "sym", "nil": "nil"}


def trace_seed(name, events):
    seed = defaultdict(set)

    def scalar(value):
        return "atom:" + ATOMS[value["tag"]]

    def canonical(value, phase, seen):
        # No heap cycles are produced by these public programs. Snapshot refs
        # to shared finite children can still be resolved by the id map.
        if "ref" in value:
            value = seen[value["ref"]]
        else:
            seen[value["id"]] = value
        tag = value["tag"]
        if tag not in ("Array", "Hash"):
            return scalar(value)
        next_phase = "walk_%d" % (1 - int(phase[-1])) if name == "cycle2" else phase
        if tag == "Array":
            site = phase + ("/array" if name == "cycle2" else "/map")
            for child in value["items"]:
                seed[site + ".elem"].add(canonical(child, next_phase, seen))
        else:
            site = phase + ("/hash" if name == "cycle2" else "/to_h")
            for pair in value["entries"]:
                key = pair["key"]
                if "ref" in key:
                    key = seen[key["ref"]]
                else:
                    seen[key["id"]] = key
                seed[site + ".key"].add(scalar(key))
                seed[site + ".value"].add(canonical(pair["value"], next_phase, seen))
        return site

    def payload(value, seen):
        if "ref" in value:
            value = seen[value["ref"]]
        else:
            seen[value["id"]] = value
        if value["tag"] == "Hash":
            for pair in value["entries"]:
                seed["wrap.key"].add(payload(pair["key"], seen))
                seed["wrap.value"].add(payload(pair["value"], seen))
            return "wrap"
        return scalar(value)

    for event in events:
        value, slot = event["value"], event["slot"]
        if name == "argument_tree":
            if ":param:payload" in slot:
                seed["P"].add(payload(value, {}))
            elif slot.endswith(":return"):
                seed["R"].add(scalar(value))
        else:
            phase = slot.split("#", 1)[1].split(":", 1)[0] if name == "cycle2" else "all"
            if slot.endswith(":return"):
                seed[phase + "/R"].add(canonical(value, phase, {}))
            elif value.get("tag") in ATOMS:
                seed[phase + "/P"].add(scalar(value))
    return {s: frozenset(hs) for s, hs in seed.items()}


def warm_result(name, events):
    p = m.make_case("f2") if name == "canonical" else (
        runtime_cycle2() if name == "cycle2" else runtime_argument())
    system = m.SlotSystem(p)
    truth, cold = m.rounds(system)
    seed = trace_seed(name, events)
    sparse = trace_seed(name, [e for e in events if e["value"].get("tag") in ATOMS][:1])
    warm, work = m.rounds(system, seed)
    missed, partial = m.rounds(system, sparse)
    violations = sorted((s, h) for s, hs in seed.items() for h in hs if h not in truth[s])
    full, verified = m.rounds(system, truth)
    dcold = m.clone_program(p).solve()
    dwarm = m.clone_program(p)
    for slot, heaps in sorted(seed.items()):
        for heap in sorted(heaps):
            dwarm.engine.add("Pt", slot, heap)
    dwarm.solve()
    qcold, qcold_work = m.Queries().run(system)
    qwarm, qwarm_work = m.Queries().run(system, seed=seed)
    return {"values": len(events), "seed_facts": sum(map(len, seed.values())),
            "seed_below_lfp": not violations, "violations": violations,
            "cold": cold, "trace_warm": work, "sparse_trace": partial,
            "trace_equal": warm == truth, "sparse_equal": missed == truth,
            "ideal_full_shape": verified, "ideal_equal": full == truth,
            "datalog_cold": dcold.engine.stats(), "datalog_warm": dwarm.engine.stats(),
            "datalog_equal": m.points(dcold) == m.points(dwarm),
            "queries_cold": qcold_work, "queries_warm": qwarm_work, "queries_equal": qcold == qwarm,
            "truth_facts": sum(map(len, truth.values()))}


def counterexamples():
    # Monotone map with two fixed points; checking F(C) == C proves no leastness.
    identity = lambda s: s
    # Unique fixed point {a,b}, but an inflationary join of a non-monotone F
    # can trap a proper pre-fixed point. Both warm and bottom start <= lfp(F).
    def nonmono(s):
        if s == frozenset():
            return frozenset(("a",))
        if s == frozenset(("b",)):
            return frozenset(("a", "b"))
        if s == frozenset(("a", "b")):
            return s
        return frozenset()

    def close(fn, initial):
        state = frozenset(initial)
        while True:
            nxt = state | fn(state)
            if nxt == state:
                return sorted(state)
            state = nxt
    # A precise finite return A[A[Int]] can be soundly covered by a guessed
    # recursion J = Int | A[J], but the latter admits A^3[Int].
    exact = m.fold.arr(m.fold.arr(m.fold.INT))
    generalized = m.fold.tie({"J": m.fold.union_of(m.fold.INT, m.fold.arr(m.fold.mkref("J")))})["J"]
    forbidden = m.fold.arr(m.fold.arr(m.fold.arr(m.fold.INT)))
    return {
        "verification_not_leastness": {"F": "identity", "least": [], "candidate": ["str"],
                                       "candidate_is_fixed": identity(frozenset(("str",))) == frozenset(("str",))},
        "monotone_antichain_cycle": {"F": "swap a and b", "bottom_fixed": [],
                                    "orbit": [["a"], ["b"], ["a"]], "monotone": True},
        "nonmonotone_even_lower_seed": {"unique_lfp": ["a", "b"],
                                       "bottom_result": close(nonmono, ()),
                                       "lower_seed_b_result": close(nonmono, ("b",)),
                                       "empty_le_a_but_Fempty_not_le_Fa": True},
        "recursive_sample_generalization": {"sample": "[[1]]", "precise": "Array[Array[Integer]]",
                                            "guess": "J = Integer | Array[J]",
                                            "guess_covers_sample": m.fold.covers(generalized, exact),
                                            "guess_below_lfp": m.fold.covers(exact, generalized),
                                            "guess_admits_extra_depth": m.fold.covers(generalized, forbidden)},
        # Sound gamma containment by itself says nothing about an arbitrary
        # lifting; top is sound too. Best alpha(sample) is needed for the proof.
        "sound_nonminimal_lift": {"runtime": "1", "lfp": "Integer", "lift": "Integer | String",
                                  "both_contain_value": True, "lift_below_lfp": False},
        "rbs_upper_bound": {"source_return": "1", "declared": "Integer | String",
                            "cold_lfp": ["Integer"], "warm_result": ["Integer", "String"]},
    }


def unsound_model(events):
    p = m.make_case("f2")
    # Deliberately omit the nil-preserving scalar branch from the abstract
    # body; Ruby source and trace remain unchanged. This is a fault injection.
    p.engine.inputs = [(r, row) for r, row in p.engine.inputs
                       if not (r == "Filter" and row == ("all/P", "nil", "all/R"))]
    system = m.SlotSystem(p)
    cold, _ = m.rounds(system)
    seed = trace_seed("canonical", events)
    got, work = m.rounds(system, seed)
    extra = sorted((s, h) for s, hs in seed.items() for h in hs if h not in cold[s])
    return {"fault": "omit canonical's nil-preserving return rule", "trace_seed_violations": extra,
            "cold_equals_warm": got == cold, "warm": work}
