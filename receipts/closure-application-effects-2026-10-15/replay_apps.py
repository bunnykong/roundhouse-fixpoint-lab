#!/usr/bin/env python3
"""Run the published closure checker on 38 saved cells and the missing-control negative."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import rerun
HERE=Path(__file__).resolve().parent
snapshot=rerun.js('supplement/app-evidence.json')
with tempfile.TemporaryDirectory(prefix='closure-saved-replay-') as temp:
    root=Path(temp);scan=root/'scan.json';scan.write_bytes(rerun.data('supplement/scan-apps.json'))
    def check(include_completed):
        labels={name:{} for name in ['spine','S','E','I']}
        for row in snapshot['cells']:
            variant=row.get('variant',row.get('arm'))
            if not include_completed and variant=='E' and row['key'].startswith('discourse/'):continue
            d=root/'cells'/variant/row['key'];d.mkdir(parents=True,exist_ok=True)
            result=dict(row['result'],directory=str(d))
            (d/'result.json').write_text(json.dumps(result))
            if row['report'] is not None:(d/'report.json').write_text(json.dumps(row['report']))
            (d/'stderr.log').write_text(row['sites'])
            labels[variant][row['key']]=dict(valid=row['label_valid'],result=str(d/'result.json'))
        for variant,cells in labels.items():
            d=root/'labels'/variant;d.mkdir(parents=True,exist_ok=True)
            (d/'label.json').write_text(json.dumps(dict(cells=cells)))
        p=subprocess.run([sys.executable,'-B','-I',str(HERE/'native/tools/check_closures.py'),
            '--cache',str(root),'--apps','campfire,forem,chatwoot,mastodon,discourse',
            '--spine','spine','--S','S','--E','E','--I','I','--scan',str(scan),
            '--out',str(root/'check.json')],capture_output=True,text=True)
        out=json.loads((root/'check.json').read_text())
        assert p.returncode==(0 if include_completed else 2),(p.stdout,p.stderr,out)
        assert out['status']==('pass' if include_completed else 'unavailable'),out
        assert not out['failures'],out
        return dict(exit=p.returncode,status=out['status'],problems=out['problems'])
    complete=check(True);negative=check(False)
    print(json.dumps(dict(native_runs=0,cells=38,complete=complete,missing_controls=negative),indent=2))
