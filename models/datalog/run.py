#!/usr/bin/env python3
"""Solve the public finite-site cases and print facts and work counters."""
import json
from cases import witness, argument_tree, chain, f2_merge, reembed


def main():
    cases = [witness(n) for n in ["self", "cycle2", "cycle3", "merge2", "param"]]
    cases += [argument_tree(), chain(64), f2_merge("mono"), reembed(False), reembed(True)]
    rows = []
    for p in cases:
        p.solve()
        rows.append({"case": p.name, "facts": len(p.engine.rows("Pt")), "work": dict(p.engine.work)})
    print(json.dumps({"condition": "finite-sites/positive-mono", "cases": rows}, indent=2))


if __name__ == "__main__":
    main()
