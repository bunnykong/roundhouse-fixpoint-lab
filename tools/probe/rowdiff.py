import importlib.util
from pathlib import Path
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("row_values",D/"row_values.py")
stratum2=importlib.util.module_from_spec(spec);spec.loader.exec_module(stratum2)

def parent(part,key):
 if part=='params':return key.rsplit('[',1)[0]
 if part=='controller_cache':return key.split('#',1)[0]
 return key
