"""Run from pending: python3 -B -m unittest models.cyclic_eq.test_cyclic_eq."""
from itertools import product
import unittest

from .compare import Automaton as A, Congruence, Session, equivalent, included, simulation
from .fixtures import adversary, constraints, canonical, doubled, regular, lower_records, random_cyclic, renamed, workbench_shapes
from .tree import tree_included
from .compatibility import frozen_equal
from .reference import repaired_canonical


def tree_oracle(left, right, limit=5000):
    """Unpruned bottom-up powerset saturation of BOTH automata (test oracle)."""
    from .compare import children, head, remap
    nodes = left.nodes + tuple(remap(n, len(left.nodes)) for n in right.nodes)
    rules = []
    for p in range(len(nodes)):
        todo, seen = [p], set()
        while todo:
            q = todo.pop()
            if q in seen:
                continue
            seen.add(q)
            n = nodes[q]
            if n[0] == "union":
                todo.extend(n[1])
            elif n != ("leaf", "bot"):
                if n == ("leaf", "widened"):
                    raise ValueError("small oracle excludes top")
                rules.append((p, head(n), children(n)))
    heads = {h: len(cs) for _, h, cs in rules}
    reached = set()
    changed = True
    while changed:
        changed = False
        snapshot = tuple(reached)
        for h, arity in heads.items():
            for masks in product(snapshot, repeat=arity):
                mask = sum(1 << p for p in {p for p, tag, cs in rules if tag == h and
                                           all(m & (1 << c) for m, c in zip(masks, cs))})
                if mask & (1 << left.root) and not mask & (1 << (len(left.nodes) + right.root)):
                    return False
                if mask not in reached:
                    reached.add(mask)
                    changed = True
                    if len(reached) > limit:
                        return None
    return True


class CyclicComparisons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = regular()

    def agree(self, a, b):
        ca, cb = canonical(self.oracle, a), canonical(self.oracle, b)
        for fast in (False, True):
            eq, inc = equivalent(a, b, fast=fast), included(a, b, fast=fast)
            self.assertEqual(eq.holds, repaired_canonical(self.oracle, a) == repaired_canonical(self.oracle, b),
                             ("eq", fast, a, b, eq))
            self.assertEqual(frozen_equal(a, b, oracle=self.oracle, fast=fast).holds, ca == cb)
            self.assertEqual(inc.holds, self.oracle.covers(cb, ca), ("inc", fast, a, b, inc))

    def test_union_find_requires_union_congruence(self):
        s = Session(A((("leaf", "str"),)), A((("leaf", "int"),)), None, None)
        cc = Congruence(s)
        cc.add(3, 4)
        self.assertTrue(cc.contains(3 | 8, 4 | 8))
        self.assertFalse(cc.contains(1, 4))  # no cancellation law for union
        cc.add(4, 16)
        self.assertTrue(cc.contains(3 | 32, 16 | 32))

    def test_unproductive_cycles_bottom_and_top(self):
        bot = A((("union", (0,)),))
        cycle = A((("array", 0),))
        top = A((("leaf", "widened"),))
        leaf = A((("leaf", "str"),))
        for a, b in product((bot, cycle, top, leaf), repeat=2):
            self.agree(a, b)
        self.assertFalse(included(bot, leaf).holds)  # covers has rigid bottom
        self.assertTrue(tree_included(bot, leaf).holds)  # empty finite language
        self.assertTrue(tree_included(cycle, bot).holds)
        self.assertFalse(equivalent(cycle, bot).holds)
        self.assertTrue(tree_included(cycle, top).holds)
        self.assertFalse(tree_included(top, leaf).holds)

    def test_hash_pointwise_merge(self):
        a = A((("union", (1, 2)), ("hash", 3, 4), ("hash", 4, 3),
               ("leaf", "str"), ("leaf", "int")))
        b = A((("hash", 1, 1), ("union", (2, 3)), ("leaf", "str"), ("leaf", "int")))
        self.agree(a, b)
        self.assertTrue(equivalent(a, b, fast=False).holds)
        self.assertFalse(tree_included(b, a).holds)  # cross products absent in a

    def test_cover_bottom_modes(self):
        leaves = [A((("leaf", t),)) for t in ("bot", "str", "var", "untyped", "widened", ("cut", "P", 2))]
        samples = leaves + [A((("array", 1), ("leaf", t))) for t in ("bot", "var", "str")]
        for bottom in ((), ("bot",), ("bot", "cut"), ("bot", "var", "untyped")):
            for a, b in product(samples, repeat=2):
                ca, cb = canonical(self.oracle, a), canonical(self.oracle, b)
                expected = self.oracle.covers(cb, ca, bottom)
                self.assertEqual(included(a, b, bottom=bottom, fast=False).holds, expected)
                self.assertEqual(included(a, b, bottom=bottom).holds, expected)

    def test_tuple_correlation_and_cover_is_not_equality(self):
        split = A((("union", (1, 2)), ("tuple", (3,)), ("tuple", (4,)),
                   ("leaf", "str"), ("leaf", "int")))
        joined = A((("tuple", (1,)), ("union", (2, 3)), ("leaf", "str"), ("leaf", "int")))
        self.agree(joined, split)
        self.assertFalse(included(joined, split).holds)
        self.assertTrue(tree_included(joined, split).holds)
        redundant = A(joined.nodes + (("tuple", (2,)), ("union", (0, 4))), 5)
        self.agree(joined, redundant)
        self.assertTrue(included(joined, redundant).holds)
        self.assertTrue(included(redundant, joined).holds)
        self.assertFalse(equivalent(joined, redundant).holds)

    def test_records_preserve_keys_and_correlations(self):
        a = A((("record", (("b", 1), ("a", 2))), ("leaf", "str"), ("leaf", "int")))
        b = A((("record", (("a", 2), ("b", 1))), ("leaf", "str"), ("leaf", "int")))
        self.agree(a, b)
        missing = A((("record", (("a", 1),)), ("leaf", "int")))
        self.agree(a, missing)
        self.assertFalse(tree_included(a, missing).holds)

    def test_cyclic_existential_backtracking(self):
        a = A((("union", (1, 2)), ("tuple", (0, 3)), ("tuple", (0, 4)),
               ("leaf", "str"), ("leaf", "int")))
        b = A((("union", (1, 2)), ("tuple", (0, 3)), ("tuple", (4, 4)),
               ("leaf", "str"), ("leaf", "int")))
        self.agree(a, b)

    def test_all_workbench_shapes(self):
        shapes = workbench_shapes(self.oracle)
        self.assertEqual(len(shapes), 12)
        roots = [a for slots in shapes.values() for a in slots.values()]
        for a in roots:
            self.agree(a, renamed(a))
            self.agree(a, doubled(a))
        for a, b in product(roots, repeat=2):
            self.agree(a, b)

    def test_seeded_random_workbench(self):
        for seed in range(90):
            a = random_cyclic(seed, records=True, bottom=True)
            self.agree(a, renamed(a, seed + 10))
            self.agree(a, random_cyclic(seed + 500, records=True, bottom=True))

    def test_adversary_is_identical_and_hkc_linear(self):
        oracle = constraints()
        compact, s = adversary(4, oracle)
        original_s, eager = oracle.subset_blowup(4)
        self.assertEqual(s.nodes, original_s.nodes)
        self.assertEqual(dict(s.lower), dict(original_s.lower))
        self.assertEqual(len(eager.states), 17)
        for n in (4, 8, 12, 16, 20):
            a, _ = adversary(n, oracle)
            result = equivalent(a, renamed(a), fast=False)
            self.assertTrue(result.holds, result)
            self.assertLessEqual(result.stats["hkc_expanded"], 4 * n + 10)
            self.assertTrue(included(a, doubled(a), fast=True).holds)

    def test_budget_is_unknown(self):
        a = A((("array", 0),))
        for fn in (equivalent, included, simulation, tree_included):
            self.assertIsNone(fn(a, a, budget=0).holds)

    def test_frozen_canonicalizer_duplicate_cycle_counterexample(self):
        a = A((("union", (1, 2)), ("leaf", "str"), ("tuple", (0,))))
        b = doubled(a)
        ca, cb = canonical(self.oracle, a), canonical(self.oracle, b)
        self.assertNotEqual(ca, cb)
        self.assertTrue(self.oracle.covers(ca, cb))
        self.assertTrue(self.oracle.covers(cb, ca))
        self.assertTrue(equivalent(a, b, fast=False).holds)
        self.assertFalse(frozen_equal(a, b, oracle=self.oracle).holds)
        self.assertIsNone(frozen_equal(a, b, oracle=self.oracle, max_states=1).holds)

    def test_exact_tree_against_unpruned_powerset(self):
        samples = [
            A((("union", (1, 2)), ("array", 0), ("leaf", "str"))),
            A((("union", (1, 2)), ("tuple", (0, 0)), ("leaf", "str"))),
            A((("union", (1, 2)), ("hash", 0, 0), ("leaf", "int"))),
            A((("union", (1, 2)), ("record", (("a", 0),)), ("leaf", "str"))),
            A((("leaf", "bot"),)),
        ]
        for a, b in product(samples, repeat=2):
            self.assertEqual(tree_included(a, b).holds, tree_oracle(a, b), (a, b))


if __name__ == "__main__":
    unittest.main()
