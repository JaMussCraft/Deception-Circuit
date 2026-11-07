from pathlib import Path
import hashlib,json,base64,subprocess,shlex,time
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a2-remote-preparation303';O.mkdir(exist_ok=False);R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment')
m=S/'plan-a2-whole-packet289-r2/candidate/manifest.json';v=json.loads(m.read_text());rows=[]
for name,h in v['unchanged_component_files'].items():
 p=Path(name);b=p.read_bytes();assert not p.is_symlink() and hashlib.sha256(b).hexdigest()==h;rows.append(dict(source=name,path=str(R/p.relative_to(A)),sha256=h,bytes=len(b),base64=base64.b64encode(b).decode()))
assert len(rows)==17
payload=dict(root=str(R),files=rows)
code='''import sys,json,base64,hashlib,os,time
from pathlib import Path
v=json.load(sys.stdin);root=Path(v['root']);assert root.resolve()==root;rows=[]
for row in v['files']:
 p=Path(row['path']);p.relative_to(root);assert '..' not in p.parts
 for q in [p]+list(p.parents):assert not q.is_symlink()
 b=base64.b64decode(row['base64']);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
 existed=p.exists()
 if existed:assert p.is_file() and p.read_bytes()==b,'existing immutable path differs'
 else:
  p.parent.mkdir(parents=True,exist_ok=True)
  fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as f:f.write(b)
 assert p.read_bytes()==b
 rows.append(dict(path=str(p),sha256=row['sha256'],bytes=len(b),preexisting=existed))
print(json.dumps(dict(files=rows,observed_unix=time.time(),authority=False,execution=False)))
'''
a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
start=time.monotonic();r=subprocess.run(a,input=json.dumps(payload),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=45)
for row in rows:row.pop('base64')
(O/'source-inventory.json').write_text(json.dumps(dict(files=rows,original_manifest_sha256=hashlib.sha256(m.read_bytes()).hexdigest(),execution_authorized=False),indent=2)+'\n')
(O/'stage-receipt.json').write_text(json.dumps(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed_seconds=time.monotonic()-start,observed_unix=time.time()),indent=2)+'\n')
assert r.returncode==0,r.stderr;v=json.loads(r.stdout);print('Staged/read back',len(v['files']),'unchanged operational source files; no execution authority;',sum(x['bytes'] for x in v['files']),'bytes')
