"""Compact cyclic type comparison; see README.md for the two semantics."""
from .compare import Automaton, Comparison, equivalent, included, simulation
from .tree import tree_included
from .compatibility import frozen_equal

__all__ = ["Automaton", "Comparison", "equivalent", "included", "simulation", "tree_included", "frozen_equal"]
