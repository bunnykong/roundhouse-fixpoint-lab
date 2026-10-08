import sys
sys.dont_write_bytecode = True
import random
import itertools
import json
from pathlib import Path
import unittest
import model as m
import warm


class ControlTests(unittest.TestCase):
    def test_all_shapes_equal_all_points(self):
        for name in m.SHAPES:
            for summary in (False, True):
                with self.subTest(name=name, summary=summary):
                    p = m.make_case(name, summary)
                    truth = m.points(m.clone_program(p).solve())
                    system = m.SlotSystem(p)
                    self.assertEqual(m.rounds(system)[0], truth)
                    self.assertEqual(m.Queries().run(system)[0], truth)
                    self.assertEqual(m.Summaries().run(system)[0], truth)

    def test_add_delete_each_shape(self):
        for name in m.SHAPES:
            for summary in (False, True):
                q, previous, summaries = m.Queries(), None, m.Summaries()
                original = m.make_case(name, summary)
                for p in (original, m.edit_call(original), original):
                    truth = m.points(m.clone_program(p).solve())
                    self.assertEqual(q.run(m.SlotSystem(p))[0], truth, name)
                    self.assertEqual(summaries.run(m.SlotSystem(p))[0], truth, name)
                    previous, _ = m.datalog(p, previous)
                    self.assertEqual(m.points(previous), truth, name)

    def test_chain_canary_counts(self):
        s = m.SlotSystem(m.make_case("chain64"))
        _, a = m.rounds(s)
        _, c = m.Queries().run(s)
        self.assertEqual(a["body_evaluations"], 64 * 65)
        self.assertEqual(a["global_rounds"], 65)
        self.assertEqual(c["body_evaluations"], 64)
        self.assertEqual(c.get("local_scc_rounds", 0), 0)

    def test_green_revalidation_skips_bodies(self):
        s = m.SlotSystem(m.make_case("f2"))
        q = m.Queries()
        first, _ = q.run(s)
        second, work = q.run(s)
        self.assertEqual(first, second)
        self.assertEqual(work.get("body_evaluations", 0), 0)
        self.assertGreater(work["revalidation_edges"], 0)

    def test_changed_implementation_same_answer_keeps_readers_green(self):
        p = m.make_case("chain64")
        q = m.Queries()
        original, _ = q.run(m.SlotSystem(p))
        edited = m.clone_program(p)
        edited.literal("extra_int", "int")
        edited.flow("extra_int", "R63")
        after, work = q.run(m.SlotSystem(edited))
        self.assertEqual({s: after[s] for s in original}, original)
        self.assertEqual(work["body_evaluations"], 2)

    def test_mutation_field_is_a_query_dependency(self):
        p = m.dl.Program("field_update")
        p.literal("one", "int")
        p.literal("s", "str")
        p.construct("array", "site", "array", {"elem": "one"})
        p.fact("Load", "array", "elem", p.slot("out"))
        q = m.Queries()
        original, _ = q.run(m.SlotSystem(p))
        changed = m.clone_program(p)
        changed.fact("Store", "array", "elem", "s")
        after, _ = q.run(m.SlotSystem(changed))
        self.assertEqual(after["out"], {"atom:int", "atom:str"})
        self.assertEqual(after, m.points(m.clone_program(changed).solve()))
        reverted, _ = q.run(m.SlotSystem(p))
        self.assertEqual(reverted, original)

    def test_demand_avoids_unrequested_independent_chain(self):
        p = m.make_case("chain64")
        p.literal("unrelated", "nil")
        _, w = m.Queries().run(m.SlotSystem(p), roots=("unrelated",))
        self.assertEqual(w["body_evaluations"], 1)
        _, w = m.Queries().run(m.SlotSystem(p), roots=("R0",))
        self.assertEqual(w["body_evaluations"], 64)

    def test_demand_materializes_recursive_fields(self):
        p = m.make_case("self")
        got, _ = m.Queries().run(m.SlotSystem(p), roots=("R",))
        truth = m.points(m.clone_program(p).solve())
        for slot in ("R",) + tuple(s for s in p.slots if s.startswith("site:")):
            self.assertEqual(got[slot], truth[slot])

    def test_late_dynamic_target_and_retraction(self):
        original = m.dynamics_case()
        edited = m.clone_program(original)
        edited.literal("recv", "str")
        q = m.Queries()
        for p, heads in ((original, {"atom:int"}),
                         (edited, {"atom:int", "atom:nil"}), (original, {"atom:int"})):
            result, _ = q.run(m.SlotSystem(p))
            self.assertEqual(result["out"], heads)
            self.assertEqual(result, m.points(m.clone_program(p).solve()))

    def test_cycle_cannot_keep_unsupported_seed_on_deletion(self):
        p = m.dl.Program("cycle")
        p.literal("x", "int")
        p.flow("x", "y")
        p.flow("y", "x")
        system = m.SlotSystem(p)
        q = m.Queries()
        old, _ = q.run(system)
        deleted = m.clone_program(p)
        deleted.engine.inputs = [(r, row) for r, row in deleted.engine.inputs if r != "Alloc"]
        new = m.SlotSystem(deleted)
        self.assertTrue(m.rounds(new, old)[0]["y"])
        self.assertFalse(q.run(new)[0]["y"])

    def test_arbitrary_valid_lower_seeds(self):
        rng = random.Random(20261007)
        for name in m.SHAPES:
            s = m.SlotSystem(m.make_case(name))
            truth, cold = m.rounds(s)
            for _ in range(8):
                seed = {k: frozenset(x for x in sorted(v) if rng.randrange(2)) for k, v in truth.items()}
                got, work = m.rounds(s, seed)
                self.assertEqual(got, truth)
                self.assertLessEqual(work["global_rounds"], cold["global_rounds"])

    def test_positive_functions_on_comparable_states(self):
        rng = random.Random(66)
        for name in m.SHAPES:
            p = m.make_case(name)
            s = m.SlotSystem(p)
            heaps = sorted(p.sites)
            for _ in range(5):
                high = {k: frozenset(h for h in heaps if rng.randrange(3) == 0) for k in s.slots}
                low = {k: frozenset(h for h in sorted(v) if rng.randrange(2)) for k, v in high.items()}
                for k in s.slots:
                    self.assertLessEqual(s.eval(k, low, m.Counter()), s.eval(k, high, m.Counter()))

    def test_regular_and_constraints_independent_equations(self):
        for name in ("self", "cycle2", "cycle3", "merge2", "param"):
            p = m.make_case(name).solve()
            graph = m.base.graph_from_sites(p)
            checks = m.regular_crosscheck(name, graph)
            self.assertTrue(all(checks["regular_equation_equality"].values()), name)
            _, expected = m.base.solve_equations(m.base.m1.CASES[name][0])
            for alias, slot in p.roots.items():
                self.assertTrue(graph.below(alias, expected, slot))
                self.assertTrue(expected.below(slot, graph, alias))

    def test_closed_form_root_truth_for_all_eight_conditions(self):
        for name in m.SHAPES:
            for summary in (False, True):
                p = m.make_case(name, summary).solve()
                got = m.base.graph_from_sites(p)
                self.assertTrue(all(m.independent_root_check(name, got, summary).values()), (name, summary))

    def test_actual_ref2_handoff_controller_on_all_shapes(self):
        for name in m.SHAPES:
            result = m.handoff_reference(name)
            self.assertEqual(result["status"], "converged", name)
            self.assertTrue(result["exact"], name)
            self.assertEqual(result["backstops"], 0, name)
            if name == "f2":
                witness = result["array_nil_witness"]
                self.assertFalse(witness["regular_accepts"])
                self.assertTrue(witness["monovariant_call_lowering_accepts"])

    def test_generalization_recovers_box_correlation(self):
        results = m.pure_scheme_examples()
        self.assertTrue(results["monomorphic"]["first_admits_string"])
        self.assertFalse(results["fresh_scheme"]["first_admits_string"])

    def test_f2_head_context_improves_use_without_scheduler_change(self):
        mono = m.make_case("f2").solve()
        context = m.make_case("f2", True).solve()
        self.assertEqual(len(mono.engine.rows("BadUse")), 8)
        self.assertEqual(context.engine.rows("BadUse"), set())


class WarmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        output = Path(__file__).with_name("evidence")
        output.mkdir(exist_ok=True)
        for name in ("canonical", "cycle2", "argument_tree"):
            warm.record(name, output / (name + ".app.jsonl"))
        warm.record("canonical", output / "canonical.external-fuzz.jsonl", fuzz=True)

    def test_all_monotone_functions_on_two_atom_powerset(self):
        sets = tuple(frozenset(i for i in range(2) if mask & (1 << i)) for mask in range(4))
        count = 0
        for images in itertools.product(sets, repeat=4):
            table = dict(zip(sets, images))
            if any(not table[a] <= table[b] for a in sets for b in sets if a <= b):
                continue
            count += 1
            fixed = [s for s in sets if table[s] == s]
            least = next(s for s in fixed if all(s <= t for t in fixed))
            for seed in sets:
                if not seed <= least:
                    continue
                state = seed
                while state != state | table[state]:
                    state |= table[state]
                self.assertEqual(state, least)
        self.assertEqual(count, 36)

    def test_current_public_traces_and_missing_paths(self):
        for name in ("canonical", "cycle2", "argument_tree"):
            path = Path(__file__).with_name("evidence") / (name + ".app.jsonl")
            r = warm.warm_result(name, warm.records(path))
            self.assertTrue(r["seed_below_lfp"])
            self.assertTrue(r["trace_equal"])
            self.assertTrue(r["sparse_equal"])
            self.assertTrue(r["datalog_equal"])
            self.assertTrue(r["queries_equal"])
            self.assertLessEqual(r["trace_warm"]["global_rounds"], r["cold"]["global_rounds"])
            self.assertEqual(r["ideal_full_shape"]["global_rounds"], 1)

    def test_unanalyzed_fuzz_inputs_are_above_app_fixpoint(self):
        path = Path(__file__).with_name("evidence") / "canonical.external-fuzz.jsonl"
        r = warm.warm_result("canonical", warm.records(path))
        self.assertFalse(r["seed_below_lfp"])
        self.assertFalse(r["trace_equal"])

    def test_real_trace_rejects_deliberately_unsound_model(self):
        path = Path(__file__).with_name("evidence") / "canonical.app.jsonl"
        r = warm.unsound_model(warm.records(path))
        self.assertIn(("all/R", "atom:nil"), r["trace_seed_violations"])
        self.assertFalse(r["cold_equals_warm"])

    def test_sound_lift_need_not_be_best_lift(self):
        c = warm.counterexamples()
        r = c["recursive_sample_generalization"]
        self.assertTrue(r["guess_covers_sample"])
        self.assertTrue(r["guess_admits_extra_depth"])
        self.assertFalse(r["guess_below_lfp"])

    def test_monotone_map_can_cycle_above_bottom(self):
        sets = [frozenset(), frozenset(("a",)), frozenset(("b",)), frozenset(("a", "b"))]
        swap = lambda s: frozenset("b" if x == "a" else "a" for x in s)
        self.assertTrue(all(swap(a) <= swap(b) for a in sets for b in sets if a <= b))
        self.assertEqual(swap(swap(sets[1])), sets[1])
        self.assertNotEqual(swap(sets[1]), sets[1])

    def test_nonmonotone_lower_seed_can_change_join_result(self):
        result = warm.counterexamples()["nonmonotone_even_lower_seed"]
        self.assertNotEqual(result["bottom_result"], result["lower_seed_b_result"])
        self.assertEqual(result["lower_seed_b_result"], result["unique_lfp"])


if __name__ == "__main__":
    unittest.main()
