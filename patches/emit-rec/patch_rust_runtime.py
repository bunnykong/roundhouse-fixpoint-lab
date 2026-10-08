#!/usr/bin/env python3
"""Harness patch for an emitted Rust crate (applied to baseline and treatment alike).

On the base tree (b28b17b6 lineage) the emitted runtime's `Base#controller_name` and
`Base#controller_path` fail `cargo check` for every app, plain real-blog included (6 errors:
ActiveSupport not found, Base has no Display, a Value/String mismatch). Nothing in the crate
calls them; their bodies become `unimplemented!()`. Usage: patch_rust_runtime.py <crate-dir>
"""
import re, sys, pathlib
p = pathlib.Path(sys.argv[1]) / "src/action_controller_base.rs"
lines = p.read_text().split("\n")
out, skip, n = [], False, 0
for line in lines:
    if not skip and re.match(r"    pub fn controller_(name|path)\(&self\) -> String \{$", line):
        out.append(line)
        out.append('        unimplemented!("harness: not called")')
        skip, n = True, n + 1
        continue
    if skip:
        if line == "    }":
            out.append(line)
            skip = False
        continue
    out.append(line)
p.write_text("\n".join(out))
print(f"patched {n} runtime methods in {p}")
