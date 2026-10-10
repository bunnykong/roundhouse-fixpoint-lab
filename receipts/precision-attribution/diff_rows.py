#!/usr/bin/env python3
"""Join by source identity, retain duplicate/synthetic accounting, reconcile the census exactly."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import argparse
import re
P=Path(__file__).resolve().parent
RANK={'full':2,'var':1,'untyped':0}

def key(x):return x['file'],x['start'],x['end'],x['kind']
def load(path):
 rows=defaultdict(list);counts=Counter()
 for line in path.open():
  x=json.loads(line);rows[key(x)].append(x);counts[x['category']]+=1
 return rows,counts

def discriminator(x):
 return json.dumps(x['owner'],sort_keys=True),x['symbol'],x['root'],x['seq']
def dump(path,x):path.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')

def compare(dest,left,right,label):
 total=Counter();per={}
 changes=dest/(label+'-changes.jsonl');unmatched=dest/(label+'-unmatched.jsonl')
 with changes.open('w') as cw,unmatched.open('w') as uw:
  for app in ('campfire','mastodon','chatwoot','forem','discourse'):
   ap=dest/app/left/'rows.jsonl';bp=dest/app/right/'rows.jsonl'
   if not ap.exists() or not bp.exists() or not (ap.parent/'counts.json').exists() or not (bp.parent/'counts.json').exists():continue
   a,ca=load(ap);b,cb=load(bp);s=Counter();trans=Counter();unmatched_categories={left:Counter(),right:Counter()}
   s['left_rows']=sum(ca.values());s['right_rows']=sum(cb.values())
   s['left_rec_rows']=sum(bool(re.search(r'\bRec\[\d+\]',r['type'])) for rs in a.values() for r in rs)
   s['right_rec_rows']=sum(bool(re.search(r'\bRec\[\d+\]',r['type'])) for rs in b.values() for r in rs)
   for k in sorted(a.keys()|b.keys()):
    aa=sorted(a.get(k,()),key=discriminator);bb=sorted(b.get(k,()),key=discriminator)
    n=min(len(aa),len(bb))
    if len(aa)==len(bb)==1:s['unique_key_pairs']+=1
    elif n:s['duplicate_key_pairs']+=n;s['duplicate_keys']+=1
    for x,y in zip(aa,bb):
     if x['symbol']!=y['symbol'] or x['owner']!=y['owner']:
      s['ambiguous_pairs']+=1
      for arm,row in ((left,x),(right,y)):
       unmatched_categories[arm][row['category']]+=1
       uw.write(json.dumps(dict(app=app,arm=arm,reason='ambiguous duplicate',row=row))+'\n')
      continue
     s['matched']+=1
     if k[0]=='<synthetic>':s['synthetic_pairs']+=1
     else:s['source_pairs']+=1
     trans[x['category']+'->'+y['category']]+=1
     delta=RANK[y['category']]-RANK[x['category']]
     s['less_precise']+=int(delta<0);s['more_precise']+=int(delta>0)
     s['equal_category']+=int(delta==0);s['different_printed_type']+=int(x['type']!=y['type'])
     if delta:
      cw.write(json.dumps(dict(app=app,direction='loss' if delta<0 else 'gain',step=delta,
              left=x,right=y),sort_keys=True)+'\n')
    for arm,rows in ((left,aa[n:]),(right,bb[n:])):
     s[arm+'_unmatched']+=len(rows)
     for x in rows:
      unmatched_categories[arm][x['category']]+=1
      uw.write(json.dumps(dict(app=app,arm=arm,reason='unmatched key multiplicity',row=x))+'\n')
   # Reconcile by category, including unmatched rows independently.
   expected_left=json.loads((dest/app/left/'counts.json').read_text())['census']
   expected_right=json.loads((dest/app/right/'counts.json').read_text())['census']
   for cats,c in ((ca,expected_left),(cb,expected_right)):
    assert cats['full']==c['fully_typed'] and cats['var']==c['var_without_untyped'] and cats['untyped']==c['untyped_anywhere']
   assert s['matched']+s[left+'_unmatched']+s['ambiguous_pairs']==s['left_rows']
   assert s['matched']+s[right+'_unmatched']+s['ambiguous_pairs']==s['right_rows']
   s['full_net']=cb['full']-ca['full'];s['untyped_net']=cb['untyped']-ca['untyped'];s['var_net']=cb['var']-ca['var']
   s['precision_score_net']=2*s['full_net']+s['var_net']
   s['matched_score_net']=sum(n*(RANK[end]-RANK[start]) for edge,n in trans.items() for start,end in [edge.split('->')])
   for category in RANK:
    matched_net=sum(n*((end==category)-(start==category)) for edge,n in trans.items() for start,end in [edge.split('->')])
    unmatched_net=unmatched_categories[right][category]-unmatched_categories[left][category]
    assert matched_net+unmatched_net==cb[category]-ca[category]
   per[app]=dict(s,transitions=dict(trans),left_categories=dict(ca),right_categories=dict(cb),
                 join_rate=s['matched']/max(s['left_rows'],s['right_rows']),
                 unmatched_categories={arm:dict(cs) for arm,cs in unmatched_categories.items()})
   total.update(s)
   print(app,'joined',s['matched'],'lost',s['less_precise'],'gained',s['more_precise'],'full net',s['full_net'],'untyped net',s['untyped_net'],flush=True)
 summary=dict(condition='five public apps at corpus/apps.json pins',left=left,right=right,per_app=per,pooled=dict(total),
              join_rate=total['matched']/max(total['left_rows'],total['right_rows']) if total['left_rows'] else None)
 dump(dest/(label+'-summary.json'),summary)
 print(json.dumps(summary['pooled']),flush=True)
 return summary

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('--left',default='main');ap.add_argument('--right',default='S3')
 a=ap.parse_args();compare(a.input,a.left,a.right,a.left+'-'+a.right)
if __name__=='__main__':main()
