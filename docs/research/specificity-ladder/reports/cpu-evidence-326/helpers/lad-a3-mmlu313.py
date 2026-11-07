from pathlib import Path
import json,hashlib,subprocess,shlex,time
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/input-staging313';O.mkdir(exist_ok=False);local=Path('/work/nvme/beto/swong2/hub/datasets--cais--mmlu');remote='/ocean/projects/cis260361p/swong2/hf/hub/datasets--cais--mmlu';files=[];aliases=[]
for p in sorted(local.rglob('*')):
 if p.is_symlink():aliases.append(dict(relative=str(p.relative_to(local)),target=str(p.readlink())))
 elif p.is_file():
  b=p.read_bytes();files.append(dict(relative=str(p.relative_to(local)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
assert (local/'refs/main').read_text().strip()=='c30699e8356da336a370243923dbaf21066bb9fe'
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2']
check="from pathlib import Path;p=Path("+repr(remote)+");assert not p.exists() and not p.is_symlink();print('new destination absent')"
r=subprocess.run(ssh+['python3 -B -c '+shlex.quote(check)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30);assert r.returncode==0,r.stderr
inventory=dict(local_root=str(local),remote_root=remote,files=files,aliases=aliases,revision='c30699e8356da336a370243923dbaf21066bb9fe',scope='Cached original dataset assets only; no dataset evaluation or model execution')
(O/'mmlu-input-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
a=['rsync','-rl','--no-perms','--no-times','--checksum','-e',shlex.join(ssh[:-1]),'--',str(local)+'/',ssh[-1]+':'+remote+'/'];start=time.monotonic();r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=120)
(O/'mmlu-transfer.json').write_text(json.dumps(dict(argv=a,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed_seconds=time.monotonic()-start),indent=2)+'\n');assert r.returncode==0,r.stderr
code='''from pathlib import Path
import sys,json,hashlib,time
v=json.load(sys.stdin);root=Path(v['remote_root'])
for x in v['files']:
 p=root/x['relative'];assert p.is_file() and not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
for x in v['aliases']:
 p=root/x['relative'];assert p.is_symlink() and str(p.readlink())==x['target'];p.resolve().relative_to(root);assert p.is_file()
print(json.dumps(dict(files=len(v['files']),aliases=len(v['aliases']),bytes=sum(x['bytes'] for x in v['files']),revision=(root/'refs/main').read_text().strip(),all_hashes_match=True,model_loaded=False,observed_unix=time.time())))
'''
# Path.readlink is newer than host3.6; use its original os.readlink equivalent.
code=code.replace('import sys,json,hashlib,time','import sys,json,hashlib,time,os').replace('str(p.readlink())','os.readlink(str(p))')
r=subprocess.run(ssh+['python3 -B -c '+shlex.quote(code)],input=json.dumps(inventory),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=35)
(O/'mmlu-readback.json').write_text(json.dumps(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,observed_unix=time.time()),indent=2)+'\n');assert r.returncode==0,r.stderr;print(r.stdout)
