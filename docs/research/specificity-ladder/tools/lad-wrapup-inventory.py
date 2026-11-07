import os,json,subprocess,shlex,time
from pathlib import Path
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/wrapup')
code=r'''import os,json,time
base='/ocean/projects/cis260361p/swong2'; selected=[];logs=[]; top=[]
for root,dirs,files in os.walk(base,followlinks=False):
 rel=os.path.relpath(root,base)
 if rel=='.':top=sorted(dirs)
 dirs[:]=[d for d in dirs if d not in ('.git','hf','envs','containers','__pycache__','.cache','.conda') and not os.path.islink(os.path.join(root,d))]
 for d in dirs:
  p=os.path.join(root,d)
  if (root.endswith('/outputs/_analyses') or root.endswith('/outputs/_studies')) and d.startswith('specificity-ladder'):selected.append(p)
 for f in files:
  if f.endswith(('.log','.out','.err')) or (f.startswith('slurm-') and f.endswith('.txt')):logs.append(os.path.join(root,f))
print(json.dumps(dict(base=base,top=top,output_roots=selected,logs=logs,observed_unix=time.time())))
'''
cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=120)
(P/'remote-discovery.json').write_text(r.stdout);(P/'remote-discovery.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
v=json.loads(r.stdout);print(json.dumps(dict(top=v['top'],output_roots=v['output_roots'],log_count=len(v['logs'])),indent=2))
