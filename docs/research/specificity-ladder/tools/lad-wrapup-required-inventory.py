from pathlib import Path
import json,subprocess,shlex
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');O=D/'docs/research/specificity-ladder/wrapup';plans=json.loads((O/'required-fetch-receipts.json').read_text())
code=r'''from pathlib import Path
import os,json
out=[]
for plan in PLANS:
 base=Path(plan['remote_root'])
 for rel in plan['paths']:
  root=base/rel
  if not root.exists():out.append(dict(root=str(root),destination_root=rel,exists=False,files=[]));continue
  rows=[]
  for p,ds,fs in os.walk(str(root),followlinks=False):
   for n in list(ds)+fs:
    q=Path(p)/n
    if n in ('token','.bashrc') or n.endswith('.lock'):continue
    if q.is_symlink():rows.append(dict(relative=str(q.relative_to(base)),kind='symlink',target=os.readlink(str(q))))
    elif q.is_file():rows.append(dict(relative=str(q.relative_to(base)),kind='file',bytes=q.stat().st_size))
  out.append(dict(root=str(root),destination_root=rel,exists=True,files=rows))
print(json.dumps(out))
'''.replace('PLANS',repr(plans))
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=120);(O/'required-file-inventory.json').write_text(r.stdout);assert r.returncode==0,r.stderr;rows=json.loads(r.stdout);print('roots',len(rows),'entries',sum(len(x['files']) for x in rows))
