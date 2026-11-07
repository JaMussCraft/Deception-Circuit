from pathlib import Path
import hashlib,json,base64,subprocess,shlex,time
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/candidate-source310';R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment');v=json.loads((O/'candidate-source.json').read_text());rows=[]
for row in v['files']:
 p=Path(row['export_path']);b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];rows.append(dict(path=str(R/p.relative_to(A)),sha256=row['sha256'],bytes=len(b),mode=0o755 if row['git_mode']=='100755' else 0o644,base64=base64.b64encode(b).decode()))
for n in ['candidate-source.json','git-provenance.json']:
 p=O/n;b=p.read_bytes();rows.append(dict(path=str(R/p.relative_to(A)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),mode=0o644,base64=base64.b64encode(b).decode()))
aliases=[dict(path=str(R/(Path(v['export_root'])/r['relative']).relative_to(A)),target=str(R/Path(r['literal_target']).relative_to(A)),sha256=r['source_pin_sha256']) for r in v['registry_aliases']]
code='''import sys,json,base64,hashlib,os,time
from pathlib import Path
v=json.load(sys.stdin);rows=[]
for r in v['files']:
 p=Path(r['path']);assert '..' not in p.parts
 for q in [p]+list(p.parents):assert not q.is_symlink()
 b=base64.b64decode(r['base64']);assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'];existed=p.exists()
 if existed:assert p.is_file() and p.read_bytes()==b,'immutable source conflict'
 else:
  p.parent.mkdir(parents=True,exist_ok=True)
  fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL,r['mode'])
  with os.fdopen(fd,'wb') as f:f.write(b)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];rows.append(dict(path=str(p),sha256=r['sha256'],bytes=len(b),preexisting=existed))
for r in v['aliases']:
 p=Path(r['path']);p.parent.mkdir(parents=True,exist_ok=True)
 if p.is_symlink():assert os.readlink(str(p))==r['target']
 else:assert not p.exists();p.symlink_to(r['target'])
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
print(json.dumps(dict(files=rows,aliases=v['aliases'],observed_unix=time.time(),execution_authorized=False,source_publication=False)))
'''
a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)];start=time.monotonic();r=subprocess.run(a,input=json.dumps(dict(files=rows,aliases=aliases)),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=90)
with(O/'remote-source-stage.json').open('x') as z:json.dump(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time(),elapsed_seconds=time.monotonic()-start),z,indent=2)
assert r.returncode==0,r.stderr;out=json.loads(r.stdout);print('Staged/read back',len(out['files']),'regular source/control files plus',len(out['aliases']),'registry aliases; no execution or publication authority')
