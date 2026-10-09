#!/usr/bin/env python3
"""Rerun the RH_DET trial, including paired error multiset and precision counts."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matrix

if __name__ == '__main__':
    matrix.rerun('F14', 'b64163fe53a8ceb9881fc5a2b5252011a4aa74e0',
                 (Path(__file__).with_name('precision-observer.patch'),))
