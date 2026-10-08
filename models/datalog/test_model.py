"""Correctness and precision checks, not timing assertions."""
import random
import unittest

from model import Engine, Program, TypeGraph, atom
from cases import witness, f2_merge, argument_tree, reembed, chain, acyclic_site_pollution, from_equations
from baselines import m1, solve_equations, graph_from_sites, run_m1, extra_equations


def naive_closure(rules, inputs):
    """Independent full-scan evaluator: oracle for the delta join implementation."""
    facts = {}
    for rel, row in inputs:
        facts.setdefault(rel, set()).add(row)
    while True:
        additions = set()
        for rule in rules:
            bindings = [{}]
            for premise in rule.body:
                following = []
                for env in bindings:
                    for row in tuple(facts.get(premise.rel, ())):
                        out = dict(env)
                        valid = len(premise.args) == len(row)
                        for symbol, value in zip(premise.args, row):
                            if symbol.startswith("?"):
                                if symbol in out and out[symbol] != value:
                                    valid = False
                                out[symbol] = value
                            elif symbol != value:
                                valid = False
                        if valid:
                            following.append(out)
                bindings = following
            for env in bindings:
                row = tuple(env.get(x, x) for x in rule.head.args)
                if row not in facts.get(rule.head.rel, ()):
                    additions.add((rule.head.rel, row))
        if not additions:
            return {k: v for k, v in facts.items() if v}
        for rel, row in additions:
            facts.setdefault(rel, set()).add(row)


def clone_inputs(program, inputs):
    e = Engine()
    for r in program.engine.rules:
        e.rule(r.name, r.head, *r.body)
    for rel, row in inputs:
        e.add(rel, *row, input_fact=True)
    return e


class DeltaTests(unittest.TestCase):
    def test_complete_closure_matches_independent_naive_engine(self):
        programs = [witness(n) for n in m1.CASES] + [argument_tree(), reembed(), reembed(True)]
        programs += [f2_merge(n) for n in ("mono", "call1", "arg_head", "receiver_type")]
        for p in programs:
            expected = naive_closure(p.engine.rules, p.engine.inputs)
            p.solve()
            actual = {r: set(v) for r, v in p.engine.facts.items() if v}
            self.assertEqual(expected, actual, p.name)

    def test_insertion_order_independence_and_once_per_grounding(self):
        p = f2_merge("call1").solve()
        expected = {r: set(v) for r, v in p.engine.facts.items() if v}
        for seed in range(12):
            facts = list(p.engine.inputs)
            random.Random(seed).shuffle(facts)
            e = clone_inputs(p, facts).solve()
            self.assertEqual(expected, {r: set(v) for r, v in e.facts.items() if v})
            self.assertEqual(p.engine.firings, e.firings)

    def test_repeated_premise_fires_once(self):
        e = Engine()
        e.rule("twice", atom("Q", "?x"), atom("P", "?x"), atom("P", "?x"))
        e.add("P", "a")
        e.solve()
        self.assertEqual(e.firings["twice"], 1)

    def test_no_work_on_second_solve_and_no_new_identities(self):
        p = f2_merge("arg_head")
        old = (dict(p.sites), set(p.slots))
        p.solve()
        counts = p.engine.stats()
        p.solve()
        self.assertEqual(counts, p.engine.stats())
        self.assertEqual(old, (p.sites, p.slots))

    def test_chain_64_without_cap(self):
        p = chain().solve()
        g = TypeGraph(p)
        self.assertEqual(p.engine.work["rule_firings"], 64)
        self.assertTrue(all(g.heads(s) == {"int"} for s in p.roots.values()))
        eqs, initial = extra_equations("chain")
        limited, _ = run_m1("chain", eqs, initial, rounds=12)
        self.assertFalse(limited["converged"])
        self.assertEqual(limited["body_evaluations"], 64 * 12)
        full, _ = run_m1("chain", eqs, initial, rounds=70)
        self.assertEqual(full["reported_rounds"], 64)

    def test_incremental_store_reaches_old_load(self):
        p = Program("mutation")
        p.literal("i", "int")
        p.literal("s", "str")
        p.construct("a", "a_site", "array", {"elem": "i"})
        p.fact("Load", "a", "elem", p.slot("read"))
        p.solve()
        self.assertEqual(TypeGraph(p).heads("read"), {"int"})
        previous = p.engine.work["rule_firings"]
        p.fact("Store", "a", "elem", "s")
        p.solve()
        self.assertEqual(TypeGraph(p).heads("read"), {"str", "int"})
        self.assertEqual(p.engine.work["rule_firings"] - previous, 3)

    def test_blocks_and_dynamic_dispatch_propagate_late_arguments(self):
        p = Program("block")
        p.site("closure", "block", ())
        p.fact("Alloc", p.slot("b"), "closure")
        p.fact("Block", "closure", p.slot("bp"), p.slot("br"))
        p.construct("br", "body_array", "array", {"elem": "bp"})
        p.literal("actual", "int")
        p.fact("Yield", "b", "actual", p.slot("yielded"))
        p.site("object", "Object", ())
        p.fact("Alloc", p.slot("receiver"), "object")
        p.fact("Method", "Object", "m", p.slot("mp"), p.slot("mr"))
        p.flow("mp", "mr")
        p.fact("Send", "call", "receiver", "m", "yielded", p.slot("result"))
        p.solve()
        self.assertTrue(TypeGraph(p).accepts("result", ("array", ("int",))))
        p.literal("actual", "str")
        p.solve()
        self.assertTrue(TypeGraph(p).accepts("result", ("array", ("str",))))

    def test_removal_requires_rederivation_of_cycle(self):
        p = Program("delete")
        p.literal("x", "int")
        p.flow("x", "y")
        p.flow("y", "x")
        p.solve()
        self.assertEqual(TypeGraph(p).heads("y"), {"int"})
        remaining = [(r, row) for r, row in p.engine.inputs if r != "Alloc"]
        rebuilt = clone_inputs(p, remaining).solve()
        self.assertFalse(rebuilt.rows("Pt"))
        # An old positive cycle's derived Pt facts cannot be retained on deletion.
        self.assertTrue(p.engine.rows("Pt"))


class PrecisionTests(unittest.TestCase):
    def test_frozen_five_and_argument_match_equation_graph(self):
        for name in list(m1.CASES) + ["argument_tree"]:
            eqs, init = m1.CASES[name] if name in m1.CASES else extra_equations(name)
            p = (witness(name) if name in m1.CASES else argument_tree()).solve()
            _, exact = solve_equations(eqs)
            got = graph_from_sites(p)
            _, wide = run_m1(name, eqs, init)
            for key in eqs:
                self.assertTrue(got.below(key.lower(), exact, key))
                self.assertTrue(exact.below(key, got, key.lower()))
                self.assertTrue(got.below(key.lower(), wide, key))

    def test_five_strict_precision_witnesses(self):
        for name, (eqs, init) in m1.CASES.items():
            p = witness(name).solve()
            term = ("float",)
            if name == "param":
                term = ("hash", ("sym",), term)
            else:
                for _ in range({"cycle2": 2, "cycle3": 3}.get(name, 1)):
                    term = ("array", term)
            slot = next(iter(eqs))
            self.assertFalse(TypeGraph(p).accepts(slot, term))
            _, wide = run_m1(name, eqs, init)
            self.assertTrue(wide.accepts(slot, term))

    def test_cycle_phase_is_not_scc_identity(self):
        g = TypeGraph(witness("cycle2").solve())
        self.assertTrue(g.accepts("R0", ("array", ("int",))))
        self.assertFalse(g.accepts("R0", ("array", ("str",))))

    def test_context_recovers_f2_receiver_head(self):
        for mode in ("mono", "receiver_type", "call1", "arg_head"):
            p = f2_merge(mode).solve()
            if mode in ("call1", "arg_head"):
                self.assertEqual(TypeGraph(p).heads("inner"), {"hash"})
                self.assertEqual(TypeGraph(p).heads("tree"), {"hash"})
                self.assertFalse(p.engine.rows("BadUse"))
            else:
                self.assertEqual(TypeGraph(p).heads("inner"), {"hash", "array", "str", "int", "nil"})
                self.assertEqual(len(p.engine.rows("BadUse")), 8)

    def test_f2_context_still_loses_finite_shape(self):
        p = f2_merge("arg_head").solve()
        g = TypeGraph(p)
        # Actual inner = {"b" => [1,"x"]}; abstraction also permits nil value.
        self.assertTrue(g.accepts("inner", ("hash", ("str",), ("nil",))))
        self.assertFalse(g.accepts("inner", ("hash", ("str",), ("str",))))

    def test_argument_tree_loses_equal_depth_relation(self):
        g = TypeGraph(argument_tree().solve())
        nil = ("nil",)
        matched = ("hash", nil, nil)
        mismatched = ("hash", nil, matched)
        self.assertTrue(g.accepts("P", matched))
        self.assertTrue(g.accepts("P", mismatched))
        self.assertFalse(g.accepts("P", ("float",)))

    def test_reembed_nil_error_and_unproductive_records(self):
        p = reembed().solve()
        self.assertEqual(p.engine.rows("BadUse"), {("recursive_index", "nil")})
        self.assertEqual(TypeGraph(p).equations(productive_only=True), ["type r = nil", "type b = bot"])
        safe = reembed(True).solve()
        self.assertFalse(safe.engine.rows("BadUse"))
        g = TypeGraph(safe)
        term = ("nil",)
        for _ in range(64):
            term = ("record_b", term)
            self.assertTrue(g.accepts("inner_result", term))
        self.assertFalse(g.accepts("inner_result", ("record_b", ("float",))))

    def test_shared_site_can_lose_acyclic_precision(self):
        p = acyclic_site_pollution().solve()
        g = TypeGraph(p)
        self.assertTrue(g.accepts("first", ("array", ("str",))))

    def test_native_site_union_does_not_merge_record_or_hash_products(self):
        p = Program("correlation")
        p.literal("i", "int")
        p.literal("s", "str")
        p.construct("r", "h1", "hash", {"key": "i", "value": "s"})
        p.construct("r", "h2", "hash", {"key": "s", "value": "i"})
        p.roots["r"] = "r"
        p.solve()
        crossed = ("hash", ("int",), ("int",))
        self.assertFalse(TypeGraph(p).accepts("r", crossed))
        self.assertTrue(graph_from_sites(p).accepts("r", crossed))

    def test_native_printer_has_no_subset_state_explosion(self):
        from cases import subset_equations
        p = from_equations("subset12", subset_equations(12)).solve()
        s, g = solve_equations(subset_equations(12), outputs=["Q0"])
        self.assertEqual(g.raw_states, 4097)
        self.assertLess(len(TypeGraph(p).equations()), 30)
        self.assertEqual(len(s.nodes), 52)


if __name__ == "__main__":
    unittest.main()
