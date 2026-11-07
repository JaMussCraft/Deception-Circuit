from pathlib import Path
import json,subprocess,shlex,base64,hashlib,time
O=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-deployment264');out=O/'actual-50318613';out.mkdir(exist_ok=False)
code='''from pathlib import Path
import json,subprocess,base64,hashlib,time
root=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254-r3/jobs/job-50318613')
names=['host-before.json','host-after.json','phase-0.json','phase-1.json','command-0.json','command-1.json']
for phase in ['six-failure-traces','next-122']:
 for rel in ['inner-mounts.json','pytest.stdout','pytest.stderr','collected-nodeids.json','candidate-origins.json','fixture-preflight/stages.jsonl','fixture-preflight/run_manifest.json','diagnostic-events/events.jsonl','junit.xml']:
  if(root/phase/rel).is_file():names.append(phase+'/'+rel)
rows=[]
for name in names:
 p=root/name;assert p.is_file() and not p.is_symlink();b=p.read_bytes();rows.append(dict(name=name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),base64=base64.b64encode(b).decode()))
accounting=subprocess.check_output(['sacct','-j','50318613','-X','-n','-P','--format=JobID,State,ExitCode,ElapsedRaw,AllocCPUS,ReqMem,NodeList,Start,End'],universal_newlines=True)
print(json.dumps(dict(actual_job_id='50318613',files=rows,accounting=accounting,observed_unix=time.time(),explicit_terminal_files_only=True)))
'''
a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=40);r.check_returncode();x=json.loads(r.stdout)
for row in x['files']:
 p=out/row['name'];p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(row.pop('base64'));assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'];p.write_bytes(b);assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
(out/'fetch-receipt.json').write_text(json.dumps(x,indent=2)+'\n');print('fetched',len(x['files']),'terminal files',x['accounting'])
