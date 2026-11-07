from pathlib import Path
import subprocess,shlex,json,time,sys
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/sharded-deployment293';root='/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r8-sharded/jobs'
code='''from pathlib import Path
import json,time,subprocess
out={}
for job in ['50319331','50319334']:
 p=Path(%r)/('job-'+job);e=p/'child/execution';row={}
 for stage in ['baseline','oracle','suite']:
  f=p/(stage+'-terminal.json')
  if f.is_file():
   d=json.loads(f.read_text());row[stage]=dict(exit_code=d.get('exit_code'),normal_completion=d.get('normal_completion'),seconds=d.get('finished',0)-d.get('started',0),error=d.get('error'))
 f=p/'host-after.json'
 if f.is_file():row['host_after']=json.loads(f.read_text())
 f=e/'run_manifest.json'
 if f.is_file():
  m=json.loads(f.read_text());row['status']=m.get('status');row['error']=m.get('error')
 f=e/'events.jsonl'
 if f.is_file():
  rows=[]
  for line in f.read_text().splitlines():
   try:rows.append(json.loads(line))
   except ValueError:pass
  finished=[x for x in rows if x['event']=='item-finish'];failed=[x for x in rows if x.get('outcome')=='failed'];starts=[x for x in rows if x['event']=='item-start'];row['progress']=dict(finished=len(finished),requested=len(rows[0].get('requested',[])) if rows else 0,failed_phases=[dict(nodeid=x['nodeid'],when=x['when'],longrepr=x.get('longrepr')) for x in failed],last=starts[-1]['nodeid'] if starts else None,seconds_since_last_event=time.time()-rows[-1]['unix_seconds'] if rows else None)
 out[job]=row
raw=subprocess.check_output(['sacct','-n','-X','-j','50319331,50319334','-o','JobIDRaw,State,ExitCode,ElapsedRaw','-P'],universal_newlines=True,timeout=15)
print(json.dumps(dict(jobs=out,accounting=raw,observed_unix=time.time())))
'''%root
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=35);mon=O/'monitor';mon.mkdir(exist_ok=True)
with(mon/(str(int(time.time()))+'.json')).open('x') as f:json.dump(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),f,indent=2)
assert r.returncode==0,r.stderr;x=json.loads(r.stdout);print(x['accounting'].strip())
for j,row in x['jobs'].items():
 brief={k:v for k,v in row.items() if k!='host_after'}
 if 'progress' in brief:
  brief['progress']=dict(brief['progress']);brief['progress']['failed_phases']=[dict(nodeid=f['nodeid'],when=f['when'],last_line=(f.get('longrepr') or '').splitlines()[-1:]) for f in brief['progress']['failed_phases']]
 print(j,json.dumps(brief))
 if row.get('host_after'):print('host_after',j,json.dumps({k:row['host_after'].get(k) for k in ['status','exit_code','source_checks_complete','allocation_checks_complete','postcheck_error']}))
r=subprocess.run(['sacct','-n','-X','-j','23636235,23636244,23631878,23631880','-o','JobIDRaw,State,ExitCode,ElapsedRaw','-P'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15);print('Delta',r.stdout.strip(),r.stderr)
