#!/usr/bin/env python3
"""Rerun S3, RH_DET and the opt-in keep-unresolved rule."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matrix

if __name__ == '__main__':
    matrix.rerun('F18', '7e4b0d52baec5d119fdae4b74c631de1cd431bfc', keep=True)
