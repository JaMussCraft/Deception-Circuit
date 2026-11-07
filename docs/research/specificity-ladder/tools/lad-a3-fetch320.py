from pathlib import Path
import base64,hashlib,json,shlex,subprocess,time
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/producer-deployment320';cfg=json.loads((O/'config.json').read_text());R=Path(cfg['physical_alignment']);root=str(R/Path(cfg['run_root']).relative_to(A));log=str(R/(O/('slurm-'+cfg['job_id']+'.log')).relative_to(A))
names=['host-before.json','command.json','child.stdout','child.stderr','supervisor-terminal.json','host-terminal.json','child/child-start.json','child/cache-namespace.json','child/source-before.json','child/source-after.json','child/native-phases.jsonl','child/saved-objects.json','child/run_manifest.json','child/canonical/pilot-target-inventory/prefit/COMPLETE.json','child/canonical/pilot-target-preparation/prefit/COMPLETE.json','child/canonical/pilot-target-preparation/prefit/payload.json','child/canonical/inventory/prefit/COMPLETE.json']
code='''import base64,hashlib,json,subprocess,time
from pathlib import Path
p=Path(%r);log=Path(%r)
accounting=subprocess.check_output(['sacct','-n','-X','-j','50319720','-o','JobIDRaw,State,ExitCode,ElapsedRaw,NodeList','-P'],universal_newlines=True,timeout=15)
rows=[r.split('|') for r in accounting.splitlines() if r.strip()];assert len(rows)==1 and rows[0][0]=='50319720'
assert rows[0][1].split()[0] in ('COMPLETED','FAILED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','CANCELLED'),accounting
step_accounting=subprocess.check_output(['sacct','-n','-j','50319720','-o','JobIDRaw,State,ExitCode,ElapsedRaw,MaxRSS,AllocCPUS,ReqMem,NodeList','-P'],universal_newlines=True,timeout=15)
files=[];absent=[];oversized=[];total=0
for name,f in [(n,p/n) for n in %r]+[('slurm-output.log',log)]:
 if not f.exists():absent.append(name);continue
 assert f.is_file() and not f.is_symlink(),str(f)
 size=f.stat().st_size
 if size>16*1024**2:oversized.append(dict(name=name,path=str(f),bytes=size));continue
 total+=size;assert total<64*1024**2
 data=f.read_bytes();assert len(data)==size
 files.append(dict(name=name,path=str(f),bytes=size,sha256=hashlib.sha256(data).hexdigest(),base64=base64.b64encode(data).decode('ascii')))
print(json.dumps(dict(actual_job_id='50319720',accounting=accounting,step_accounting=step_accounting,observed_unix=time.time(),files=files,absent=absent,oversized=oversized)))
'''%(root,log,names)
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2']
out=O/'terminal';assert not out.exists(),'exclusive fetch already used'
r=subprocess.run(ssh+['python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=60)
if r.returncode:
 failure=O/('terminal-fetch-failure-'+str(time.time_ns())+'.json');failure.write_text(json.dumps(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),indent=2)+'\n');raise RuntimeError(r.stderr)
v=json.loads(r.stdout);out.mkdir();rows=[]
for row in v['files']:
 data=base64.b64decode(row.pop('base64'));assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 q=out/row['name'];assert '..' not in Path(row['name']).parts;q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(data)
 assert hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256'];rows.append(row)
v['files']=rows;v['all_fetched_hashes_verified']=True
with(O/'terminal-fetch.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(dict(accounting=v['accounting'],files=len(rows),bytes=sum(r['bytes'] for r in rows),absent=v['absent'],oversized=v['oversized'])))
