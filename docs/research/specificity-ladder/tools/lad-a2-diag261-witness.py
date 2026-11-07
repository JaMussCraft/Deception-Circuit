from pathlib import Path
import hashlib,json,time,subprocess,shlex
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');S=W/'.superpowers/sdd';P=S/'plan-a2-fresh-cpu-timing239-r2';O=P/'root-deployment261'
old=json.loads((S/'plan-a2-full-score-bridges-cpu-proposal199/root-genuine-proof-r2/job-50316939/transfer-attestation.json').read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
rows={}
for n,r in old['current_catalogues'].items():
 b=Path(n).read_bytes();row={'virtual':n,'physical':r['physical'],'bytes':len(b),'sha256':sha(b)}
 row['delta_capture']=dict(cluster='delta',path=n,bytes=len(b),sha256=sha(b),observed_unix=time.time());rows[n]=row
with(O/'catalogue-capture.json').open('x') as f:json.dump(rows,f,indent=2)
code='''import json,sys,time,hashlib
from pathlib import Path
x=json.load(sys.stdin);result={}
for n,r in x.items():
 p=Path(r['physical']);assert p.is_file() and not p.is_symlink();b=p.read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],str(p)
 result[n]=dict(cluster='bridges2',path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),observed_unix=time.time())
print(json.dumps(result))
'''
a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
r=subprocess.run(a,input=json.dumps(rows),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=45)
with(O/'catalogue-remote-readback.json').open('x') as f:json.dump(dict(command=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time()),f,indent=2)
r.check_returncode();remote=json.loads(r.stdout)
for n,row in rows.items():
 b=Path(n).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'];row['remote']=remote[n];row['delta_reread']=dict(cluster='delta',path=n,bytes=len(b),sha256=sha(b),observed_unix=time.time())
w=dict(complete=True,adapter_manifest_sha256='c43d084973d38dbb2367b269879f23cc2d42383784f65d9abde937d4232573e6',actual_job_id='23624978',source_files=511,ordinary_inputs=422,immutable_original_inputs=418,current_catalogue_inputs=4,literal_source_links=4,catalogues_are_snapshots_not_continuous_Delta=True,current_catalogues=rows,scope='Fresh catalogue capture/readback/reread for diagnostic261; source and immutable input closure are checked by the actual unchanged child. Not a reused prior proof witness.')
with(O/'current-catalogue-witness.json').open('x') as f:json.dump(w,f,indent=2);f.write('\n')
print('fresh witness',sha((O/'current-catalogue-witness.json').read_bytes()))
