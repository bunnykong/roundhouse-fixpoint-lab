#!/usr/bin/env python3
"""Run the public Python/Ruby regression suites in isolated interpreters."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
(ROOT / "corpus/test-tmp").mkdir(parents=True, exist_ok=True)
commands = [
    ["-m", "unittest", "discover", "-s", "oracle", "-p", "test_oracle.py"],
    ["-m", "unittest", "discover", "-s", "corpus", "-p", "test_harness.py"],
    ["-m", "unittest", "discover", "-s", "models/datalog", "-p", "test_model.py"],
    ["-m", "unittest", "discover", "-s", "models/control", "-p", "test_model.py"],
    ["-m", "unittest", "models.cyclic_eq.test_cyclic_eq", "models.cyclic_eq.test_permutation"],
]
for command in commands:
    subprocess.run([sys.executable, "-B"] + command, cwd=ROOT,
                   env=dict(os.environ, TMPDIR=str(ROOT / "corpus/test-tmp")), check=True)
print("All public regression suites passed.")
