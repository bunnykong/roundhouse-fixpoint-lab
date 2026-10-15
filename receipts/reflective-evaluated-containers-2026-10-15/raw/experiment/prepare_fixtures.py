#!/usr/bin/env python3
"""Restore and verify the immutable archived prepared-suite fixtures locally."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAB = ROOT / "week/lab"
SOURCE = ROOT / "week/bound-next/sources/probe-source"
spec = importlib.util.spec_from_file_location("baseline_rerun", LAB / "receipts/baseline-2026-10-10/rerun.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.fixtures(SOURCE)
pins = json.loads((LAB / "receipts/baseline-2026-10-10/evidence/emission-inputs.json").read_text())
(ROOT / "evidence/fixture-pins.json").write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n")
print("Archived generated fixtures verified against pinned inventory")
