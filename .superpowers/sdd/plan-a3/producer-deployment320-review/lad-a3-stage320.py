from pathlib import Path
import json,hashlib,os,subprocess,shlex,time,stat
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/producer-deployment320';P=S/'plan-a3/candidate-producer311';R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a3-producer-2ba697d7f5fd/Alignment')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
v=json.loads((S/'plan-a3/candidate-source310/candidate-source.json').read_text());i=json.loads((S/'plan-a3/producer-input-inventory317/inventory.json').read_text());verified=json.loads((O/'input-rehash317.json').read_text());assert not verified['errors'] and len(verified['files'])==326;rows={};external=[]
def add(path,digest,size=None):
 p=Path(path);p.relative_to(A)
 if str(p) in rows:assert rows[str(p)]['sha256']==digest;return
 assert not p.is_symlink();b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==digest
 if size is not None:assert len(b)==size
 rows[str(p)]=dict(path=str(p),relative=str(p.relative_to(A)),sha256=digest,bytes=len(b),mode=stat.S_IMODE(p.stat().st_mode)&0o777)
for x in v['files']:add(x['export_path'],x['sha256'],x['bytes'])
for x in json.loads((P/'manifest.json').read_text())['files']:add(x['path'],x['sha256'],x['bytes'])
for p in [P/'manifest.json',S/'plan-a3/candidate-source310/git-provenance.json'] :add(p,sha(p))
for x in verified['files']:
 if Path(x['path']).is_relative_to(A):add(x['path'],x['sha256'],x['bytes'])
 else:external.append(x)
root=O/'source-tree';root.mkdir(exist_ok=False)
for x in rows.values():
 b=Path(x['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==x['sha256'];p=root/x['relative'];p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
 p.chmod(x['mode'])
listing=O/'transfer-files.txt';listing.write_text(''.join(x['relative']+'\n' for x in rows.values()))
manifest=dict(physical_alignment=str(R),virtual_alignment=str(A),files=list(rows.values()),external_input_files=external,input_aliases=i['input_aliases'],scope='Private immutable staging for provisional CPU-only producer; no actual job/admission or promotion')
(O/'transport-inventory.json').write_text(json.dumps(manifest,indent=2)+'\n')
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2']
code="from pathlib import Path;p=Path("+repr(str(R))+");assert not p.exists() and not p.is_symlink();p.parent.mkdir(mode=0o700,parents=True,exist_ok=False);p.mkdir(mode=0o700);assert p.resolve()==p;print('created private staging root')"
r=subprocess.run(ssh+['python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30)
with(O/'private-root-create.json').open('x') as f:json.dump(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),f,indent=2)
assert r.returncode==0,r.stderr
transport=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none'];argv=['rsync','-rl','--no-perms','--no-times','--checksum','--files-from='+str(listing),'-e',shlex.join(transport),'--',str(root)+'/', 'b2dtn:'+str(R)+'/'];start=time.monotonic();r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=180)
with(O/'transfer.json').open('x') as f:json.dump(dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed_seconds=time.monotonic()-start),f,indent=2)
assert r.returncode==0,r.stderr;print('Staged',len(rows),'regular files',sum(x['bytes'] for x in rows.values()),'bytes to dedicated Alignment; external HF inputs',len(external),'remain separately bound; aliases/readback next')
