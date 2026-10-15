#!/usr/bin/env python3
from pathlib import Path
import datetime, hashlib, json, subprocess, sys, re
D=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
R=D/'week/evidence/results/pending-factorial'
C=D/'week/evidence/sources/probe-source'
git=lambda *a:subprocess.check_output(['git','-C',str(C),*a],text=True).strip()
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base='a7b6d3f8e7908581588662970804fc4d6dc53784'
original=subprocess.check_output(['git','-C',str(C),'show',base+':src/analyze/parameter_conservation/tests.rs'])
current=(C/'src/analyze/parameter_conservation/tests.rs').read_bytes()
harness=re.search(r'```rust\n(fn evidence\(o:.*?\n})\n```',(D/'protocol.md').read_text(),re.S).group(1)
assert current == original+b'\n'+harness.encode()+b'\n'
changed=git('diff','--name-only',base).splitlines()
assert set(changed)=={'src/analyze/mod.rs','src/analyze/parameter_conservation.rs',
 'src/analyze/parameter_conservation/tests.rs','src/ide.rs','src/ty.rs',
 'examples/producer_reason_sound_types.rs','examples/parameter_reason_sound_types.rs'}
# The uninstrumented concern writer and sccq remain byte-identical.
for relative in ['src/analyze/sccq.rs','src/analyze/fold.rs']:
    assert (C/relative).read_bytes()==subprocess.check_output(['git','-C',str(C),'show',base+':'+relative])
metadata={'condition':'pending-value-reason-identity-20261015-a7b6d3f8',
 'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'head':git('rev-parse','HEAD'),'base':base,'branch':git('branch','--show-current'),
 'commit':git('show','-s','--format=fuller','HEAD'),
 'card_sha256':hashfile(D/'protocol.md'), 'harness_verbatim':True,'original_assertions_unchanged':True,
 'changed_sources':changed,'working_tree':git('status','--short','--untracked-files=no'),
 'source_sha256':{p:hashfile(C/p) for p in changed},
 'cargo_lock_sha256':hashfile(C/'Cargo.lock'),
 'patch_sha256':hashfile(D/'patches/0001-lineage-factorial.patch'),
 'scripts_sha256':{p.name:hashfile(p) for p in [D/n for n in
    ['setup.sh','session.sh','run-card.sh','run-validation.sh','run-control.sh','clean.sh','rerun.sh',
     'summarize.py','audit.py','report.py','implement.py']] if p.exists()},
 'probe_sha256':hashfile(D/'week/evidence/sources/lab/receipts/baseline-2026-10-10/probe'),
 'toolchain':{'rustc':subprocess.check_output(['rustc','+1.98.1','--version'],text=True).strip(),
              'cargo':subprocess.check_output(['cargo','+1.98.1','--version'],text=True).strip()},
 'binary_sha256':hashfile(D/'week/evidence/scratch/provenance-target/release/roundhouse'),
 'timing_claim':False}
if (R/'precommit-source.json').exists():
    assert all(metadata['source_sha256'][p]==h for p,h in json.loads((R/'precommit-source.json').read_text())['sources'].items())
for key in ['author','committer']:
    assert git('show','-s','--format=%'+('ae' if key=='author' else 'ce'))=='268838774+bunnykong@users.noreply.github.com'
assert git('log','-1','--format=%B').endswith('Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
(R/'integrity.json').write_text(json.dumps(metadata,indent=2)+'\n')
artifacts=[p for p in (D/'week/evidence/results').rglob('*') if p.is_file() and p.name not in ['sha256.json']]
(R/'sha256.json').write_text(json.dumps({str(p.relative_to(D)):hashfile(p) for p in sorted(artifacts)},indent=2)+'\n')
print(json.dumps({k:metadata[k] for k in ['head','branch','harness_verbatim','original_assertions_unchanged','working_tree']},indent=2))
