#!/usr/bin/env python3
"""Recompute the new public receipt reductions without rebuilding measured programs."""
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
for name in ['F19', 'F20', 'F21', 'writer-boundaries', 'precision-attribution',
             'expansion-cache', 'cache-guards', 'long-name']:
    subprocess.run([sys.executable, '-B', str(LAB / 'receipts' / name / 'recompute.py')], check=True)
subprocess.run([sys.executable, '-B', str(LAB / 'reproductions/routing_model.py')], check=True)
print('All addition reductions passed.')
