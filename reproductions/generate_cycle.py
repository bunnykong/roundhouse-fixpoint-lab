#!/usr/bin/env python3
"""Generate mutually recursive methods in a minimal Rails-shaped fixture.

usage: generate_cycle.py <out-dir> --cycle C --width W

A controller action calls `walk_0`; methods `walk_0 .. walk_{C-1}` form a ring (each recurses into
the next; C=1 is plain self-recursion). Each method has W container branches that recurse:
W=1 Array (`map`), W=2 Array + Hash (`transform_values`). Runtime depth is that of the literal.
"""
import argparse
import pathlib

BRANCH = {
    "Array": "value.map {{ |v| {callee}(v) }}",
    "Hash": "value.transform_values {{ |v| {callee}(v) }}",
}
ORDER = ["Hash", "Array"]


def method(i, cycle, width):
    callee = f"walk_{(i + 1) % cycle}"
    kinds = [k for k in ORDER if k in (["Array"] if width == 1 else ORDER)]
    lines = [f"  def walk_{i}(value)"]
    for j, kind in enumerate(kinds):
        kw = "if" if j == 0 else "elsif"
        lines.append(f"    {kw} value.is_a?({kind})")
        lines.append("      " + BRANCH[kind].format(callee=callee))
    lines += ["    else", "      value", "    end", "  end"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--cycle", type=int, default=2)
    ap.add_argument("--width", type=int, default=2, choices=[1, 2])
    a = ap.parse_args()
    literal = '[1, [2, ["x"]]]' if a.width == 1 else '{ "a" => [1, { "b" => "x" }] }'
    controller = "\n".join([
        "class TreesController < ApplicationController",
        "  def index",
        f"    @tree = walk_0({literal})",
        "  end",
        "",
        "  private",
        "",
        "\n\n".join(method(i, a.cycle, a.width) for i in range(a.cycle)),
        "end",
        "",
    ])
    files = {
        "Gemfile": 'source "https://rubygems.org"\ngem "rails"\n',
        "config/routes.rb": 'Rails.application.routes.draw do\n  root "trees#index"\nend\n',
        "db/schema.rb": "ActiveRecord::Schema[8.0].define(version: 1) do\nend\n",
        "app/controllers/application_controller.rb": "class ApplicationController < ActionController::Base\nend\n",
        "app/controllers/trees_controller.rb": controller,
        "app/views/trees/index.html.erb": "<%= @tree %>\n",
    }
    out = pathlib.Path(a.out)
    for rel, text in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    size = sum((out / rel).stat().st_size for rel in files)
    print(f"{out} cycle={a.cycle} width={a.width} bytes={size}")


if __name__ == "__main__":
    main()
