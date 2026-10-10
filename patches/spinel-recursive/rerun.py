#!/usr/bin/env python3
"""Build public Spinel and repeat extraction, kernel timing and closed-domain validation."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
SHA='e527d205d274ccdbbca926edaddce386b8c17fa2'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--source',type=Path,help='Optional existing Spinel clone; still checked out at the exact public pin.')
a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
for name in ['programs','signatures','generated','fastpaths']:
    shutil.copytree(HERE/name,out/name,dirs_exist_ok=True)
for name in ['experiment.py','fastpath_experiment.py','validate_fastpaths.py']:
    shutil.copyfile(HERE/name,out/name)
for name in ['bin','evidence','logs','tmp']:(out/name).mkdir(exist_ok=True)
source=out/'spinel'
if not source.exists():
    subprocess.run(['git','clone',str(a.source.resolve() if a.source else 'https://github.com/matz/spinel.git'),str(source)],check=True)
subprocess.run(['git','-C',str(source),'checkout','--detach',SHA],check=True)
subprocess.run(['make','deps'],cwd=source,check=True)
subprocess.run(['make','-j4','NO_CCACHE=1'],cwd=source,check=True)
subprocess.run([sys.executable,'-B','experiment.py','--phase','compile'],cwd=out,check=True)
for name in ['alias','union','untyped']:
    r=subprocess.run([str(source/'bin/spinel_rbs_extract'),str(out/'signatures'/name)],capture_output=True,text=True,check=True)
    (out/'evidence'/(name+'.seed')).write_text(r.stdout)
assert (out/'evidence/alias.seed').read_text()=='class JProbe\n'
subprocess.run([sys.executable,'-B','fastpath_experiment.py'],cwd=out,check=True)
subprocess.run([sys.executable,'-B','validate_fastpaths.py'],cwd=out,check=True)
print(json.dumps(dict(spinel=SHA,scope='new unscored kernel measurement; historical ratios remain separate',
                     evidence='evidence/'),indent=2))
