import json,subprocess,shlex
from pathlib import Path
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');O=D/'docs/research/specificity-ladder/wrapup';plans=json.loads((O/'fetch-plan.json').read_text())
code=r'''import os,json,hashlib
from pathlib import Path
archive=Path('/ocean/projects/cis260361p/swong2/_specificity-ladder-wrapup-20261107');rows=[];excluded=[]
prune={'__pycache__','.git','.pytest_cache','arrays','source-tree','transfer-tree','basetemp','tmp','fixtures','fixture-preflight','outputs','data','dataset','datasets'}
for rootname in ROOTS:
 root=Path(rootname)/'.superpowers/sdd'
 if not root.exists():continue
 ns=Path(rootname).parts[5]
 for p,dirs,files in os.walk(str(root),followlinks=False):
  keep=[]
  for d in dirs:
   q=Path(p)/d
   if d in prune or d.endswith('-tmp') or d.startswith('pytest-') or d.startswith('test_'):
    excluded.append(str(q));continue
   if q.is_symlink():
    dst=archive/'.superpowers/sdd'/q.relative_to(root);dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists() and not dst.is_symlink():os.symlink(os.readlink(str(q)),str(dst))
    continue
   keep.append(d)
  dirs[:]=keep
  for n in files:
   q=Path(p)/n
   if n=='token' or n.endswith(('.lock','.pyc','.npy','.npz','.pt','.safetensors','.arrow','.parquet','.sif')) or n.startswith('core.'):
    excluded.append(str(q));continue
   if not q.is_symlink() and q.stat().st_size>90000000:excluded.append(str(q));continue
   rel=q.relative_to(root);dst=archive/'.superpowers/sdd'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
   if q.is_symlink():
    if not dst.exists() and not dst.is_symlink():os.symlink(os.readlink(str(q)),str(dst))
   elif not dst.exists():os.link(str(q),str(dst))
   elif q.read_bytes()!=dst.read_bytes():
    dst=archive/'outputs/_analyses/specificity-ladder/bridges2-staging/packet-variants'/ns/rel;dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():os.link(str(q),str(dst))
   rows.append(dict(source=str(q),destination=str(dst.relative_to(archive)),bytes=0 if q.is_symlink() else q.stat().st_size,symlink=q.is_symlink()))
print(json.dumps(dict(files=rows,excluded_generated=excluded)))
'''.replace('ROOTS',repr([p['remote_root'] for p in plans]))
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=180)
(O/'remote-packet-mirror.json').write_text(r.stdout);(O/'remote-packet-mirror.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr;x=json.loads(r.stdout);print(len(x['files']),len(x['excluded_generated']),flush=True)
