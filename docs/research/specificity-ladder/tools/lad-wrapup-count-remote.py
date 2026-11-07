from pathlib import Path
import json,subprocess,shlex
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');O=D/'docs/research/specificity-ladder/wrapup';plans=json.loads((O/'fetch-plan.json').read_text());tasks=[dict(source=p['remote_root']+'/'+rel,destination=rel) for p in plans for rel in p['paths']]
tasks+=[dict(source='/ocean/projects/cis260361p/swong2/_specificity-ladder-wrapup-20261107/'+r,destination=r) for r in ['logs/bridges2','outputs/_analyses/specificity-ladder/bridges2-staging','containers']]
code=r'''import os,json,time
from pathlib import Path
out=[]
for t in TASKS:
 root=Path(t['source']);files=links=bytes_=dirs_count=0
 for p,ds,fs in os.walk(str(root),followlinks=False):
  dirs_count+=1
  for n in ds:
   q=Path(p)/n
   if q.is_symlink():links+=1
  for n in fs:
   if n=='token' or n=='.bashrc' or n.endswith('.lock'):continue
   q=Path(p)/n
   if q.is_symlink():links+=1
   else:files+=1;bytes_+=q.stat().st_size
 t.update(files=files,links=links,bytes=bytes_,directories=dirs_count,exists=root.exists());out.append(t)
print(json.dumps(dict(entries=out,observed_unix=time.time())))
'''.replace('TASKS',repr(tasks))
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=300)
(O/'remote-final-counts.json').write_text(r.stdout);(O/'remote-final-counts.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
print(json.dumps(json.loads(r.stdout),indent=2))
