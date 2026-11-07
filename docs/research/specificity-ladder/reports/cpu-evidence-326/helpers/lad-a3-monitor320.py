from pathlib import Path
import json,subprocess,shlex,time
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/producer-deployment320';c=json.loads((O/'config.json').read_text());R=Path(c['physical_alignment']);root=str(R/Path(c['run_root']).relative_to(A));log=str(R/(O/('slurm-'+c['job_id']+'.log')).relative_to(A))
code='''import json,subprocess,time
from pathlib import Path
p=Path(%r);out=dict(accounting=subprocess.check_output(['sacct','-n','-X','-j','50319720','-o','JobIDRaw,State,ExitCode,ElapsedRaw,NodeList','-P'],universal_newlines=True,timeout=15),observed_unix=time.time())
for n in ['host-terminal.json','supervisor-terminal.json','child/run_manifest.json','child/cache-namespace.json']:
 f=p/n
 if f.exists():out[n]=json.loads(f.read_text())
f=p/'child/native-phases.jsonl'
if f.exists():
 rows=[]
 for line in f.read_text().splitlines():
  try:rows.append(json.loads(line))
  except ValueError:pass
 out['phase_records']=len(rows);out['latest_phases']=rows[-3:]
for name,f in [('stderr',p/'child.stderr'),('slurm_log',Path(%r))]:
 if f.exists():
  with f.open('rb') as z:z.seek(max(0,f.stat().st_size-3000));out[name]=z.read().decode(errors='replace')
print(json.dumps(out))
'''%(root,log)
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2'];r=subprocess.run(ssh+['python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=35);d=O/'monitor';d.mkdir(exist_ok=True)
with(d/(str(time.time_ns())+'.json')).open('x') as f:json.dump(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),f,indent=2)
assert r.returncode==0,r.stderr;v=json.loads(r.stdout);print(v['accounting'].strip());brief={k:x for k,x in v.items() if k not in ('accounting','host-terminal.json','supervisor-terminal.json','latest_phases')};brief['latest_phases']=[{k:r.get(k) for k in ('operation','status','wall_seconds','normal_completion','error','model_loaded','execution_authorized')} for r in v.get('latest_phases',[])];print(json.dumps(brief)[:4000])
if 'host-terminal.json' in v:print('host terminal',json.dumps(v['host-terminal.json'])[:2500])
