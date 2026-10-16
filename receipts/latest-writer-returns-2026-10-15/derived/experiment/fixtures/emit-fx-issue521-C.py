#!/usr/bin/env python3
import hashlib,os
from pathlib import Path
b=Path('$EXPERIMENT/bin/roundhouse')
assert hashlib.sha256(b.read_bytes()).hexdigest()=='d3ab2294525057639c53c7a4235296dc6b048cbe8f6b168c9a724e1fdea3039b'
out=Path(os.environ["RH_STRUCT_DUMP"]).with_name("spinel-out")
os.execv(str(b),[str(b),"--target","spinel","-o",str(out),"."])
