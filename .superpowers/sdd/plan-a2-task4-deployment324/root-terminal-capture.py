from pathlib import Path
import hashlib,json,subprocess,time,xml.etree.ElementTree as ET
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a2-task4-deployment324';run=O/'run-01'
r=subprocess.run(['sacct','-X','-j','23638286','--format=JobIDRaw,State,ExitCode,ElapsedRaw,NodeList','-P'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
assert r.returncode==0;rows=[x.split('|') for x in r.stdout.splitlines() if x.startswith('23638286|')];assert len(rows)==1;state=rows[0][1]
assert state.split()[0] in ('COMPLETED','FAILED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','CANCELLED'),state
v=json.loads((run/'RESULT.json').read_text());assert v['actual_job_id']=='23638286';files=[];summary=[]
for name in ['RESULT.json','run_manifest.json','base39-identity.json','mgnp-identity.json','base39.log','base39.xml','mgnp.log','mgnp.xml']:
 p=run/name;data=p.read_bytes();files.append(dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
p=O/'slurm-23638286.log';data=p.read_bytes();files.append(dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
for obs in v['observations']:
 cases=list(ET.parse(str(run/(obs['environment']+'.xml'))).getroot().iter('testcase'))
 failed=[c.get('name') for c in cases if c.find('failure') is not None];errors=[c.get('name') for c in cases if c.find('error') is not None];skipped=[c.get('name') for c in cases if c.find('skipped') is not None]
 assert obs['tests']==len(cases) and failed==obs['failed_names'] and errors==obs['error_names'] and skipped==obs['skipped_names']
 summary.append(dict(environment=obs['environment'],tests=len(cases),passed=obs['passed'],failed_names=failed,error_names=errors,skipped_names=skipped,elapsed_seconds=obs['elapsed_seconds']))
for name,value in [('terminal-accounting.json',dict(stdout=r.stdout,stderr=r.stderr,exit_code=r.returncode,observed_unix=time.time())),('terminal-inventory.json',dict(files=files,summary=summary,actual_job_id='23638286',result_status=v['status'],native_acceptance=False))]:
 with(O/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps(dict(accounting=r.stdout,summary=summary,files=len(files))))
