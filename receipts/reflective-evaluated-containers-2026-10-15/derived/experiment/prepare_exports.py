#!/usr/bin/env python3
"""Prepare task-local fresh exporters and explicitly forward the repair flag."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
BOUND = ROOT / "week/bound-next"
C = BOUND / "sources/probe-source"
INPUT = ROOT.parent / "component-opacity-gate/week/sound/adapter"
ADAPTER = BOUND / "adapter"
ADAPTER.mkdir(exist_ok=True)
for name in ("compare.py", "component_gate.py", "oracle_ext.py"):
    shutil.copyfile(INPUT / name, ADAPTER / name)
export = (INPUT / "export.py").read_text()
export = export.replace("    a = p.parse_args()", """    p.add_argument('--candidate-env', action='append', default=[], metavar='RH_FLAG=VALUE')
    a = p.parse_args()
    candidate = {}
    for item in a.candidate_env:
        name, value = item.split('=', 1)
        if name != 'RH_REFLECT_BOUND' or value not in ('0', '1'):
            p.error('this condition permits only RH_REFLECT_BOUND=0/1')
        if not any(name in f.read_text() for f in (a.source/'src').rglob('*.rs')):
            p.error('candidate flag is not implemented')
        candidate[name] = value""")
export = export.replace("    env.update(flags)", "    flags.update(candidate)\n    flags['RH_FIXPOINT_VERIFY']='1' if a.verify else '0'\n    env.update(flags)")
old = """    if status:
        diff = subprocess.check_output(['git','-C',str(a.source),'diff','HEAD','--binary'])
        if not a.overlay or a.overlay.read_bytes()!=diff or '??' in status:
            raise ValueError('unexpected measured source modification: '+status)
"""
new = """    # A semantic candidate is a new condition, never an observation overlay.
    diff = subprocess.check_output(['git','-C',str(a.source),'diff','HEAD','--binary'])
    (out/'source.diff').write_bytes(diff)
    source_files = {str(f.relative_to(a.source)):digest(f)
                    for f in sorted((a.source/'src').rglob('*.rs'))}
"""
assert old in export
export = export.replace(old, new)
export = export.replace("source_clean=not bool(status), input=input_pin,",
    "source_clean=not bool(status), source_status=status, input=input_pin,\n        source_files_sha256=source_files, source_diff_sha256=digest(out/'source.diff'),\n        semantic_candidate=True, candidate_env=candidate,")
export = export.replace("exact observation-only git diff including the staged new module",
                        "unused historical overlay option; semantic source changes are recorded directly")
(ADAPTER / "export.py").write_text(export)
helper = (INPUT / "sound_types.rs").read_text()
start = helper.index('#[cfg(feature = "s3")]')
end = helper.index("// Serde intentionally")
helper = helper[:start] + 'fn provenance(t: &Ty) -> Option<String> { t.provenance().map(|p| format!("{p:?}").to_lowercase()) }\n\n' + helper[end:]
helper = helper.replace('Ty::Fn { ret, .. } => v["ret"] = raw(ret),', '''Ty::Fn { params, block, ret, .. } => {
            v["ret"] = raw(ret);
            for (i, p) in params.iter().enumerate() { v["params"][i]["ty"] = raw(&p.ty); }
            if let Some(b) = block { v["block"] = raw(b); }
        },''')
example = C / "examples/reflective_sound_types.rs"
example.parent.mkdir(exist_ok=True)
example.write_text(helper)
print("Prepared fresh tagged exporter and copied component/membership checker")
