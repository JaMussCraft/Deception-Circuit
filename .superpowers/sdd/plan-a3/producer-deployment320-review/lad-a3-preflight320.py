from pathlib import Path
import json,hashlib,subprocess,shlex,time
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/producer-deployment320';P=S/'plan-a3/candidate-producer311';R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a3-producer-2ba697d7f5fd/Alignment');ctx=json.loads((P/'context.json').read_text());inventory=json.loads((O/'transport-inventory.json').read_text());inputs=json.loads((O/'input-rehash317.json').read_text());aliases=json.loads((S/'plan-a3/producer-input-inventory317/inventory.json').read_text())['input_aliases'];cfg=json.loads((P/'config.template.json').read_text());run_root=Path(ctx['canonical_namespace_proposal']).parent.parent
cfg.update(candidate_commit=ctx['candidate_commit'],export=ctx['source_working_directory'],canonical=ctx['canonical_namespace_proposal'],run_root=str(run_root),cluster='bridges2',account='cis260361p',partition='RM',qos='rm',cpus=128,memory_bytes=192*1024**3,allocation_seconds=5400,child_cap_seconds=5040,physical_alignment=str(R),virtual_alignment=str(A),image=ctx['proposed_environment_context']['image'],image_sha256=ctx['proposed_environment_context']['image_sha256'],packed_env=ctx['proposed_environment_context']['packed_env'],python=ctx['proposed_environment_context']['container_python'],candidate_source=ctx['candidate_source'],inputs=ctx['inputs'],input_files=[{k:x[k] for k in ('path','sha256','bytes')} for x in inputs['files']],input_aliases=aliases,packet_manifest=dict(path=str(P/'manifest.json'),sha256=hashlib.sha256((P/'manifest.json').read_bytes()).hexdigest()),storage_free_bytes_required=64*1024**3)
assert cfg['job_id'] is None and cfg['kind']=='UNBOUND_CANDIDATE_ONLY'
with(O/'draft-config.json').open('x') as f:json.dump(cfg,f,indent=2);f.write('\n')
code='''import sys,json,os,hashlib,subprocess,time,importlib.util
from pathlib import Path
x=json.load(sys.stdin);cfg=x['config'];A=Path(cfg['virtual_alignment']);R=Path(cfg['physical_alignment'])
def physical(p):
 p=Path(p)
 for virtual,real in [(A,R),(Path('/work/nvme/beto/swong2/hub'),Path('/ocean/projects/cis260361p/swong2/hf/hub'))]:
  try:return real/p.relative_to(virtual)
  except ValueError:pass
 return p
for row in x['inventory']['files']:
 p=physical(row['path']);assert p.is_file() and not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],str(p)
for row in cfg['input_aliases']:
 p=physical(row['path']);t=row['literal_target']
 if str(p).startswith(str(R)):
  p.parent.mkdir(parents=True,exist_ok=True)
  if p.is_symlink():assert os.readlink(str(p))==t
  else:assert not p.exists();p.symlink_to(t)
 else:assert p.is_symlink() and os.readlink(str(p))==t
for row in cfg['input_files']:
 p=physical(row['path']);b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],str(p)
packet=physical(x['packet']);sys.path.insert(0,str(packet));import common;import host
common.check_packet(cfg,lambda p:host.physical(cfg,p));facts=common.check_sources(cfg,lambda p:host.physical(cfg,p));assert common.sha(cfg['image'])==cfg['image_sha256']
draft=physical(x['draft']);draft.parent.mkdir(parents=True,exist_ok=True)
with draft.open('x') as f:json.dump(cfg,f,indent=2);f.write('\\n')
root=physical(cfg['run_root']);assert not root.exists();root.mkdir(parents=True,mode=0o700);assert root.resolve()==root and not list(root.iterdir())
smoke=physical(x['smoke']);smoke.mkdir(parents=True,mode=0o700);(smoke/'child').mkdir(mode=0o700)
r=subprocess.run(['/usr/bin/python3','-B',str(packet/'host.py'),'--dry-run'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20);assert r.returncode==0,r.stderr
print(json.dumps(dict(source=facts,regular_staged_files=len(x['inventory']['files']),input_files=len(cfg['input_files']),aliases=len(cfg['input_aliases']),host_python=sys.version,host_executable=sys.executable,host_dryrun=json.loads(r.stdout),private_root=str(root),private_mode=oct(root.stat().st_mode&0o7777),private_uid=root.stat().st_uid,own_uid=os.getuid(),root_empty=True,canonical_absent=not physical(cfg['canonical']).exists(),available_bytes=os.statvfs(str(root)).f_bavail*os.statvfs(str(root)).f_frsize,observed_unix=time.time())))
'''
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2'];smoke=O/'unbound-container-smoke';payload=dict(config=cfg,inventory=inventory,packet=str(P),draft=str(O/'draft-config.json'),smoke=str(smoke));start=time.monotonic();r=subprocess.run(ssh+['python3 -B -c '+shlex.quote(code)],input=json.dumps(payload),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=90)
with(O/'actual-host-source-readback.json').open('x') as f:json.dump(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed_seconds=time.monotonic()-start),f,indent=2)
assert r.returncode==0,r.stderr;v=json.loads(r.stdout);print(json.dumps(v,indent=2))
