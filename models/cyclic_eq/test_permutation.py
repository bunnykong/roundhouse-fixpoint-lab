"""HKC's exponential family must stay beside the favorable constraints canary."""
import math
import unittest

from .break_hkc import permutation
from .compare import equivalent, included
from .fixtures import canonical, regular, renamed


class PermutationCanary(unittest.TestCase):
    def test_hkc_visits_all_incomparable_subsets(self):
        for n in (4, 8, 12):
            a = permutation(n)
            result = equivalent(a, renamed(a), fast=False, budget=10_000_000)
            self.assertTrue(result.holds)
            self.assertEqual(result.stats["hkc_expanded"], math.comb(n, n // 2) + 1)
            self.assertTrue(equivalent(a, renamed(a)).holds)
            self.assertTrue(included(a, renamed(a)).holds)

    def test_frozen_oracle_on_feasible_permutation(self):
        a = permutation(4)
        oracle = regular()
        self.assertEqual(canonical(oracle, a), canonical(oracle, renamed(a)))


if __name__ == "__main__":
    unittest.main()
