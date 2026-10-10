#!/usr/bin/env python3
"""Differential check of manual fast paths on a deterministic finite JSON-tree corpus."""
import json
import os
import random
import subprocess
from experiment import ROOT, SPINEL, run
from fastpath_experiment import cc, specialize


def ruby(value):
    if value is None:
        return "nil"
    if isinstance(value, dict):
        return "{ " + ", ".join(json.dumps(k) + " => " + ruby(v) for k, v in value.items()) + " }"
    if isinstance(value, list):
        return "[" + ", ".join(ruby(v) for v in value) + "]"
    return json.dumps(value)


def main():
    rng = random.Random(610527)

    def tree(depth):
        if depth <= 0 or rng.random() < 0.35:
            return rng.choice([None, rng.randrange(-30, 31), "x", "two words", ""])
        if rng.random() < 0.5:
            return [tree(depth - 1) for _ in range(rng.randrange(5))]
        keys = ["k" + str(i) for i in range(rng.randrange(5))]
        rng.shuffle(keys)
        return {key: tree(depth - 1) for key in keys}

    values = [None, 0, -1, "", [], {}, [1, 2], {"z": [], "a": None}, [[{"a": [2]}]]]
    values += [tree(5) for _ in range(87)]
    (ROOT / "evidence/validation-values.json").write_text(json.dumps(values, indent=2) + "\n")
    functions = {"canonical": "canonical", "cycle": "walk_0", "tree_sum": "sum_leaves"}
    result = {}
    for case, function in functions.items():
        source = (ROOT / "programs" / (case + ".rb")).read_text()
        source += "\n" + "\n".join("puts " + function + "(" + ruby(v) + ").inspect" for v in values) + "\n"
        rb = ROOT / "programs" / (case + "_validation.rb")
        rb.write_text(source)
        generated = ROOT / "generated" / (case + "_validation.c")
        emit = run([SPINEL, rb, "-c", "-o", generated], case + "-validation-emit")
        assert emit["returncode"] == 0, emit
        fast = ROOT / "generated" / (case + "_validation_fast.c")
        fast.write_text(specialize(generated.read_text(), case))
        control_binary = ROOT / "bin" / (case + "_validation_control")
        fast_binary = ROOT / "bin" / (case + "_validation_fast")
        cc(generated, control_binary, case + "-validation-control-cc")
        cc(fast, fast_binary, case + "-validation-fast-cc")
        oracle = run(["ruby", "--disable-gems", rb, "1"], case + "-validation-oracle")
        control = run([control_binary, "1"], case + "-validation-control")
        native = run([fast_binary, "1"], case + "-validation-fast")
        result[case] = {"values": len(values), "seed": 610527,
                        "oracle_returncode": oracle["returncode"],
                        "control_returncode": control["returncode"], "fast_returncode": native["returncode"],
                        "control_matches_cruby": control["stdout"] == oracle["stdout"],
                        "fast_matches_cruby": native["stdout"] == oracle["stdout"]}
        (ROOT / "evidence" / (case + "-validation-oracle.txt")).write_text(oracle["stdout"])
        (ROOT / "evidence" / (case + "-validation-control.txt")).write_text(control["stdout"])
        (ROOT / "evidence" / (case + "-validation-fast.txt")).write_text(native["stdout"])
        stress = subprocess.run([str(fast_binary), "1"], cwd=ROOT,
                                env=dict(os.environ, TMPDIR=str(ROOT / "tmp"), SPINEL_GC_STRESS="2"),
                                capture_output=True, text=True, timeout=60)
        result[case]["gc_stress_matches"] = stress.returncode == 0 and stress.stdout == oracle["stdout"]
        (ROOT / "logs" / (case + "-validation-gc-stress.log")).write_text(stress.stderr)
        print(case, json.dumps(result[case]), flush=True)
        (ROOT / "evidence/validation.json").write_text(json.dumps(result, indent=2) + "\n")
        assert all([oracle["returncode"] == 0, control["returncode"] == 0, native["returncode"] == 0,
                    result[case]["control_matches_cruby"], result[case]["fast_matches_cruby"],
                    result[case]["gc_stress_matches"]]), result[case]


if __name__ == "__main__":
    main()
