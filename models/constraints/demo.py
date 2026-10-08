#!/usr/bin/env python3
"""Show compact constraints and exponential eager graph reification."""
import json
from solver import subset_blowup

rows = []
for length in [2, 4, 8]:
    solver, graph = subset_blowup(length)
    rows.append({"length": length, "constraint_nodes": len(solver.nodes),
                 "determinized_states": len(graph.states), "expected": 2 ** length + 1})
    assert len(graph.states) == 2 ** length + 1
print(json.dumps({"condition": "nth-from-end Hash; positive covariant data", "rows": rows}, indent=2))
