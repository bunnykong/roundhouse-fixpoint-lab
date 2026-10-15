#!/usr/bin/env python3
"""Reduce registered receipts without changing the card's gates."""
from pathlib import Path
import json, re, sys
D = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
R = D/'week/evidence/results/pending-factorial'
A = D/'week/evidence/results/pending-factorial-campfire'
condition = 'pending-value-reason-identity-20261015-a7b6d3f8'
write = lambda name, obj: (R/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
laws = ['comm','idem','evidence','assoc','fold2','fold3','pid']
factorial = {}
for arm in ['00','10','01','11']:
    text = (R/('A'+arm+'.log')).read_text()
    lines = [x.split('PENDING-FACTORIAL ',1)[1] for x in text.splitlines() if 'PENDING-FACTORIAL ' in x]
    assert len(lines)==1, (arm,len(lines))
    report = json.loads(lines[0])
    write('A'+arm+'-report.json', report)
    assert report['arm']==list(arm)
    assert (R/('A'+arm+'.exit')).read_text().strip()=='0'
    factorial[arm] = report
expected = {
 '00': {'assoc':False,'fold2':True,'fold3':True,'pid':True,'seed_ok':False,'no_early_never':True},
 '10': {'assoc':True,'fold2':True,'fold3':True,'pid':True,'seed_ok':True,'no_early_never':True},
 '01': {'assoc':False,'fold2':True,'fold3':True,'pid':True,'seed_ok':False,'no_early_never':True},
 '11': {'assoc':False,'fold2':False,'fold3':False,'pid':False,'seed_ok':True,'no_early_never':True},
}
cells=[]
for arm, report in factorial.items():
    for law in laws:
        got=report['counts'].get(law,0)
        want=expected[arm].get(law,False)
        cells.append({'arm':'A'+arm,'law':law,'count':got,'predicted_nonzero':want,'matches':bool(got)==want})
    for flag in ['seed_ok','no_early_never']:
        got=report[flag]
        cells.append({'arm':'A'+arm,'law':flag,'flag':got,'predicted':expected[arm][flag],
                      'matches':got==expected[arm][flag]})
write('factorial-summary.json',{'condition':condition,'arms':factorial,'cells':cells,
 'matched_cells':sum(x['matches'] for x in cells),'total_cells':len(cells)})
old=json.loads((R/'registered_protocol-reports.json').read_text())
old={x['name']:x['report'] for x in old if x['arm']=='candidate' and x['name']!='precision'}
reports={}; rows={}; comparisons={}; row_diffs={}
for arm in ['b1','b3']:
    reports[arm]={}; rows[arm]={}; row_diffs[arm]={}
    for schedule in ['unset','seed-1','seed-2','unset-repeat']:
        p=A/arm/schedule
        assert (p/'probe.exit').read_text().strip()=='0'
        reports[arm][schedule]=json.loads((p/'stdout.json').read_text())
        ls=[x.removeprefix('rh-parameter-rows: ') for x in (p/'probe-campfire.stderr').read_text().splitlines()
            if x.startswith('rh-parameter-rows: ')]
        assert len(ls)==1,(arm,schedule,len(ls))
        rows[arm][schedule]=json.loads(ls[0])
        (p/'rows.json').write_text(json.dumps(rows[arm][schedule],indent=2,sort_keys=True)+'\n')
        (p/'condition.json').write_text(json.dumps({'condition':condition,'arm':arm,'schedule':schedule,
           'verification':True,'probe_base':False,'timing_claim':False},indent=2)+'\n')
    for schedule in ['seed-1','seed-2','unset-repeat']:
        first=rows[arm]['unset']; second=rows[arm][schedule]
        diffs=[]
        for key in sorted(first.keys()|second.keys()):
            a,b=first.get(key),second.get(key)
            if a is None or b is None or a['full']!=b['full']:
                diffs.append({'key':key,'ref_unset':None if a is None else a['ref'],
                              'ref_schedule':None if b is None else b['ref'],
                              'known_equal':a is not None and b is not None and a['known']==b['known'],
                              'unset':a,'schedule':b})
        row_diffs[arm][schedule]=diffs
for schedule in ['unset','seed-1','seed-2','unset-repeat']:
    new=reports['b1'][schedule]['digest']; prev=old[schedule]['digest']
    comparisons[schedule]={k:{'b1':new.get(k),'registered_protocol':prev.get(k),'equal':new.get(k)==prev.get(k)}
                           for k in sorted(new.keys()|prev.keys())}
b3_digest={}
for table in reports['b3']['unset']['digest']:
    vals={s:r['digest'][table] for s,r in reports['b3'].items()}
    b3_digest[table]={'values':vals,'all_equal':len(set(vals.values()))==1,
       'unset_seed1_repeat_equal':len({v for s,v in vals.items() if s!='seed-2'})==1}
h_b1=all(x['equal'] for tables in comparisons.values() for x in tables.values())
h_b3=all(b3_digest[k]['all_equal'] for k in ['ir','side_table','controller_cache']) and b3_digest['returns']['unset_seed1_repeat_equal']
pdiffs=row_diffs['b3']['seed-1']
h_b3p=bool(pdiffs) and all(x['ref_unset'] and x['ref_schedule'] and x['known_equal'] for x in pdiffs)
write('campfire-reports.json',{'condition':condition,'arms':reports})
write('digest-comparison.json',{'condition':condition,'b1_vs_value_only':comparisons,'b3_schedules':b3_digest,
 'h_b1':h_b1,'h_b3':h_b3,'h_b3p':h_b3p})
write('row-differences.json',{'condition':condition,'arms':row_diffs})
summary={'condition':condition,'factorial_matched':sum(x['matches'] for x in cells),'factorial_total':len(cells),
         'factorial_counts':{a:r['counts'] for a,r in factorial.items()},'h_b1':h_b1,'h_b3':h_b3,'h_b3p':h_b3p,
         'row_difference_counts':{a:{s:len(v) for s,v in schedules.items()} for a,schedules in row_diffs.items()}}
write('summary.json',summary)
print(json.dumps(summary,indent=2))
