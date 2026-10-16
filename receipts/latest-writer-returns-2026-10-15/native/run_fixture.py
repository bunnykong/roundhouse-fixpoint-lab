#!/usr/bin/env python3
"""Fixture-specific adapter over obs.py's raw transport; never accepts its failed app schema blindly."""
import argparse,json,os,re,subprocess,sys
from pathlib import Path
import evidence as E
import verdict_returns as V
BASE={'block_values','constants','controller_cache','ir','params','returns'}
REQUIRED={'issue521':BASE,'issue964':BASE|{'attributes'}}
KNOWN=set(V.DIGESTS)
METHODS={'issue521':{'config':('app/models/probe.rbs','self.config'),'load!':('app/models/probe/configuration.rbs','self.load!')},
 'issue964':{m:('app/models/prefs.rbs','self.'+m) for m in ('mode','c','d','e')}}

def tables_valid(fixture,arm,tables):
 # C keeps its native shape. K/K1 may create only known tables; required six/seven stay required.
 return set(tables)==REQUIRED[fixture] if arm=='C' else REQUIRED[fixture]<=set(tables)<=KNOWN

def parsed_return(line):
 m=re.fullmatch(r'\s*def\s+(?:self\.)?[\w!?=]+:\s*(.+)\s*',line)
 if not m:raise ValueError('incomplete def signature')
 text=m[1];require_arrow='->' in text
 E.require(require_arrow,'no return arrow')
 # Whole-file RBS parser has already established syntactic completeness.
 return text.rsplit('->',1)[1].strip()

def adapt(result,fixture,arm,binary_sha,tree_sha,flags,setting):
 p=Path(result['directory']);reasons=[];report=None
 def check(ok,why):
  if not ok:reasons.append(why)
 check(result['metrics']['exit_code']==0 and not result['metrics']['timed_out'],'emitter incomplete')
 check(result['setting']==E.obs.setting(setting),'setting identity')
 check(result['key']['runtime']['ruby_version'].startswith('ruby 4.0.7 '),'runtime identity')
 check(result['input_tree_sha256']==tree_sha,'fixture tree identity')
 check(result['key']['binary_sha256']==E.sha(Path(result['binary'])),'wrapper binary identity')
 expected=dict(E.obs.COMMON,**flags,RH_FIXPOINT_VERIFY='1',RH_PROVENANCE_AUDIT='1')
 if setting.startswith(('1-','2-')):expected['RH_SHUFFLE']=setting[0]
 actual={k:v for k,v in result['key']['rh_flags'].items() if k not in E.obs.DUMPS}
 check(actual==expected,'effective profile identity')
 reports=[json.loads(l[13:]) for l in (p/'stderr.log').read_text().splitlines() if l.startswith('rh-fixpoint: ')]
 check(len(reports)==1,'native completion report')
 if reports:
  report=reports[0];check(tables_valid(fixture,arm,report['digest']),'fixture table inventory')
  check(set(report['loops'])==set(V.LOOPS),'native loop inventory')
 expected_files=E.read(E.D/(fixture+'-rbs-files.json'));output=p/'spinel-out'
 rbs={str(x.relative_to(output)):x for x in output.rglob('*.rbs')}
 check(set(rbs)==set(expected_files),'complete expected RBS file inventory')
 parse='ARGV.each { |p| RBS::Parser.parse_signature(File.read(p)) }'
 env=dict(os.environ,RBENV_VERSION='3.4.4')
 parsed=subprocess.run(['ruby','-rrbs','-e',parse,*[str(rbs[k]) for k in sorted(rbs)]],env=env,capture_output=True,text=True)
 check(parsed.returncode==0,'whole-file RBS parse: '+parsed.stderr[:300])
 rets={}
 for method,(file,name) in METHODS[fixture].items():
  if file not in rbs:check(False,'missing RBS '+file);continue
  lines=[l for l in rbs[file].read_text().splitlines() if re.match(r'\s*def '+re.escape(name)+r':',l)]
  check(len(lines)==1,'complete unique def '+name)
  if len(lines)==1:
   try:rets[method]=parsed_return(lines[0])
   except ValueError as e:check(False,str(e))
 # The observer rejects tiny native shapes before artifact reduction. Only this expected shape error is waived.
 if not result['valid']:
  check('expected exactly ten value digests' in str(result.get('error')),'non-schema observer failure')
 return {'valid':not reasons,'returns':rets,'receipt':str(p/'result.json'),'reasons':reasons,
 'native_tables':sorted(report['digest']) if report else None,'rbs_sha256':{k:E.sha(v) for k,v in rbs.items()},
 'native_binary_sha256':binary_sha,'tree_sha256':tree_sha}

def main():
 p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True)
 p.add_argument('--id',choices=list(REQUIRED),required=True);p.add_argument('--arm',choices=['C','K','K1'],required=True)
 p.add_argument('--flags',type=Path,default=E.D/'profile.json');p.add_argument('--cache',type=Path,default=E.D/'receipts/fixtures-cache')
 p.add_argument('--out',type=Path,default=E.D/'receipts/fixtures');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 binary=a.binary.resolve();sha=E.sha(binary);label='fx-'+a.id+'-'+a.arm;wrapper=a.out/('emit-'+label+'.py')
 wrapper.write_text('#!/usr/bin/env python3\nimport hashlib,os\nfrom pathlib import Path\nb=Path('+repr(str(binary))+')\nassert hashlib.sha256(b.read_bytes()).hexdigest()=='+repr(sha)+'\nout=Path(os.environ["RH_STRUCT_DUMP"]).with_name("spinel-out")\nos.execv(str(b),[str(b),"--target","spinel","-o",str(out),"."])\n');wrapper.chmod(0o755)
 flags=dict(E.read(a.flags),RH_CONTRIBUTOR_VALUES='1',RH_CURRENT_RETURN_REPLACE='0' if a.arm=='C' else '1')
 if a.arm=='K1':flags['RH_CURRENT_RETURN_IVAR_PENDING']='0'
 cmd=[sys.executable,str(E.F/'phase2/observers/obs.py'),'run','--bin',str(wrapper),'--input',str(a.fixture.resolve()),'--app','schedule-row-strict-'+a.id,'--settings',','.join(V.SCHEDULES),'--label',label,'--cache-root',str(a.cache),'--jobs','1','--timeout','240']
 for k,v in flags.items():cmd+=['--flag',k+'='+v]
 with (a.out/(label+'.log')).open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 tree,_=E.obs.inventory(a.fixture.resolve());E.require(tree==E.read(E.D/'fixture-pins.json')[a.id]['tree_sha256'],'frozen fixture tree changed');E.require(E.sha(binary)==sha,'native binary changed');result={}
 for setting in V.SCHEDULES:
  r,folder=E.raw_cell(a.cache,label,'schedule-row-strict-'+a.id,setting)
  result[setting]=adapt(r,a.id,a.arm,sha,tree,flags,setting)
 E.save(a.out/(a.id+'-'+a.arm+'.json'),result)
 print(json.dumps({'fixture':a.id,'arm':a.arm,'transport_exit':rc,'cells':{s:{k:v for k,v in r.items() if k in ('valid','returns','reasons','native_tables')} for s,r in result.items()}},indent=1))
 return 0 if all(c['valid'] for c in result.values()) else 2
if __name__=='__main__':sys.exit(main())
