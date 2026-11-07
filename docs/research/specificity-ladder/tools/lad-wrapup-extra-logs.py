from pathlib import Path
import json,subprocess,shlex
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');O=D/'docs/research/specificity-ladder/wrapup'
code=r'''from pathlib import Path
import os,json,re
base=Path('/ocean/projects/cis260361p/swong2');archive=base/'_specificity-ladder-wrapup-20261107';rows=[]
for p,ds,fs in os.walk(str(base),followlinks=False):
 ds[:]=[d for d in ds if d not in ('.git','hf','envs','containers','__pycache__','.cache','.conda') and not d.startswith('_specificity-ladder-wrapup') and not os.path.islink(os.path.join(p,d))]
 for n in fs:
  if re.search(r'(\.log(?:\.\d+|\.gz)?|\.out|\.err|\.stdout|\.stderr)$',n) or n in ('stdout','stderr') or (n.startswith(('slurm-','job')) and n.endswith('.txt')):
   src=Path(p)/n;dst=archive/'logs/bridges2'/src.relative_to(base);dst.parent.mkdir(parents=True,exist_ok=True)
   if not dst.exists():os.link(str(src),str(dst))
   rows.append(dict(source=str(src),destination=str(dst.relative_to(archive)),bytes=src.stat().st_size))
print(json.dumps(dict(logs=rows)))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=120);(O/'all-job-logs.json').write_text(r.stdout);assert r.returncode==0,r.stderr;print(len(json.loads(r.stdout)['logs']))
