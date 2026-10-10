#!/usr/bin/env python3
"""A block-binding matrix for RH_SOUND (receivers × methods × parameter shapes).

Writes app/controllers/trees_controller.rb under the output directory and prints the --params list for
record.rb. Each flow is a private method `f<i>(r)` that calls one iterator on one receiver with one
parameter shape and passes the first and the last named parameter to their own sinks. Every block
returns a constant that suits its method, so CRuby runs every flow without raising.
usage: gen_matrix.py <out_dir>
"""
import sys
from pathlib import Path

RECEIVERS = {
    "hash": '{ "b" => 1, "c" => 2 }',
    "pairs": '[["b", 1], ["c", 2]]',
    "ragged": '"1:2,3".split(",").map { |s| s.split(":") }',
    "ints": "[1, 2, 3]",
}
# method -> (call prefix, block return); `%s` is the block.
METHODS = {
    "each": (".each %s", "nil"),
    "map": (".map %s", "nil"),
    "select": (".select %s", "true"),
    "reject": (".reject %s", "false"),
    "each_with_index": (".each_with_index %s", "nil"),
    "sort_by": (".sort_by %s", "0"),
    "min_by": (".min_by %s", "0"),
    "group_by": (".group_by %s", "0"),
    "sum": (".sum %s", "0"),
    "filter_map": (".filter_map %s", "nil"),
    "flat_map": (".flat_map %s", "[]"),
    "count": (".count %s", "true"),
    "find": (".find %s", "false"),
    "any?": (".any? %s", "false"),
    "partition": (".partition %s", "true"),
    "each_slice": (".each_slice(2) %s", "nil"),
    "each_cons": (".each_cons(2) %s", "nil"),
    "each_with_object": (".each_with_object([]) %s", "nil"),
    "inject": (".inject(0) %s", "0"),
}
SHAPES = {
    "a": ("|a|", ["a"]),
    "ab": ("|a, b|", ["a", "b"]),
    "a_": ("|a, |", ["a"]),
    "arest": ("|a, *r|", ["a"]),
    "pab": ("|(a, b)|", ["a", "b"]),
    "pabc": ("|(a, b), c|", ["a", "c"]),
    "apbc": ("|a, (b, c)|", ["a", "c"]),
}


def main():
    out = Path(sys.argv[1])
    flows, defs, sinks, params = [], [], [], []
    i = 0
    for rk, rv in RECEIVERS.items():
        for mk, (call, ret) in METHODS.items():
            for sk, (shape, names) in SHAPES.items():
                sink_calls = []
                for n in dict.fromkeys([names[0], names[-1]]):
                    sname = f"s{i}_{n}"
                    sinks.append(f"  def {sname}(x) = x")
                    params.append(f"TreesController#{sname}:x")
                    sink_calls.append(f"{sname}({n})")
                block = "{ " + shape + " " + "; ".join(sink_calls) + "; " + ret + " }"
                if mk == "inject":  # the block's value is the next accumulator
                    block = "{ " + shape + " " + "; ".join(sink_calls) + "; 0 }"
                defs.append(f"  # {rk} {mk} {shape}\n  def f{i} = ({rv}){call % block}")
                flows.append(f"f{i}")
                i += 1
    src = ["class TreesController < ApplicationController", "  def index",
           "    @tree = [" + ", ".join(flows) + "]", "  end", "", "  private", ""]
    src += defs + [""] + sinks + ["end", ""]
    (out / "app/controllers").mkdir(parents=True, exist_ok=True)
    (out / "app/controllers/trees_controller.rb").write_text("\n".join(src))
    print(",".join(params))


if __name__ == "__main__":
    main()
