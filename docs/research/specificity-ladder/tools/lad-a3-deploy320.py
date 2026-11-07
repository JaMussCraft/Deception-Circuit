from pathlib import Path
import json,hashlib,subprocess,shlex,time,sys
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/producer-deployment320';P=S/'plan-a3/candidate-producer311';cfg=json.loads((O/'draft-config.json').read_text());R=Path(cfg['physical_alignment']);physical=lambda p:str(R/Path(p).relative_to(A));ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2']
def save(n,v):
 with(O/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def remote(code,payload,timeout=60):
 r=subprocess.run(ssh+['python3 -B -c '+shlex.quote(code)],input=json.dumps(payload),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=timeout);return dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time())
if sys.argv[1]=='prepare':
 assert json.loads((O/'actual-host-source-readback.json').read_text())['exit_code']==json.loads((O/'actual-container-smoke.json').read_text())['exit_code']==0
 verdict=S/'plan-a3/candidate-producer311-review/verdict.json';assert hashlib.sha256(verdict.read_bytes()).hexdigest()=='a8169126d1044a99690e6044a602f59ce097969e6ee12f697b57f71c5945c0a8'
 script='#!/bin/bash\nset -euo pipefail\nexport CUDA_VISIBLE_DEVICES=\nexport A3_HOST_PYTHON=/usr/bin/python3\nexport A3_CANDIDATE311_HOST='+shlex.quote(physical(P/'host.py'))+'\nexec bash '+shlex.quote(physical(P/'launch.sh'))+' '+shlex.quote(physical(O/'config.json'))+' "$(cat '+shlex.quote(physical(O/'config.sha256'))+')"\n'
 (O/'dispatch.sh').write_text(script)
 a=['sbatch','--parsable','--hold','--account=cis260361p','--partition=RM','--qos=rm','--nodes=1','--ntasks=1','--cpus-per-task=128','--mem=192G','--time=01:30:00','--no-requeue','--export=ALL,CUDA_VISIBLE_DEVICES=','--chdir='+physical(P),'--job-name=lad-A3-candidate-producer','--output='+physical(O/'slurm-%j.log'),physical(O/'dispatch.sh')];save('submission-argv.json',a)
 code='''import sys,json,subprocess,hashlib
from pathlib import Path
x=json.load(sys.stdin);p=Path(x['path']);assert not p.exists();p.write_text(x['script']);p.chmod(0o700);subprocess.check_call(['bash','-n',str(p)])
a=x['argv'];a=[a[0],'--test-only']+[v for v in a[1:] if v!='--hold'];r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30);print(json.dumps(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,dispatch_sha256=hashlib.sha256(p.read_bytes()).hexdigest())));sys.exit(r.returncode)
'''
 r=remote(code,dict(path=physical(O/'dispatch.sh'),script=script,argv=a));save('actual-ninety-minute-preview.json',r);assert r['exit_code']==0,r['stderr'];print(r['stdout'])
elif sys.argv[1]=='submit':
 assert json.loads((O/'actual-ninety-minute-preview.json').read_text())['exit_code']==0
 a=json.loads((O/'submission-argv.json').read_text());code='''import sys,json,subprocess
x=json.load(sys.stdin);r=subprocess.run(x,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30);print(json.dumps(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)));sys.exit(r.returncode)
''';r=remote(code,a);save('submission.json',r);assert r['exit_code']==0,r['stderr'];v=json.loads(r['stdout']);job=v['stdout'].strip().split(';')[0];assert job.isdigit();save('job.json',dict(job_id=job,cluster='bridges2'));subprocess.run(['research-session','job','add',str(A/'Deception-Circuit/docs/research/specificity-ladder'),'--job-id',job,'--cluster','bridges2','--status','PENDING','--timeout-min','60'],check=True);print('Held CPU job',job)
