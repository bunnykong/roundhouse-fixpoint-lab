import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import inference
print(json.dumps(inference.recompute("F20"),indent=2,sort_keys=True))
