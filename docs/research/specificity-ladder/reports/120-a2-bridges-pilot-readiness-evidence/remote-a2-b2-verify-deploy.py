from pathlib import Path
import json,hashlib,tarfile,os,stat,datetime
P=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-20261102');M=json.loads((P/'deployment/transfer-manifest.json').read_text());A=Path(M['physical_remote_root']);V=Path(M['namespace_root'])
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
for r in M['files']:
 p=A/r['relative_path'];assert p.is_file() and p.stat().st_size==r['nbytes'] and digest(p)==r['sha256'],str(p)
W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';parent=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5';S=json.loads((parent/'snapshot.json').read_text());archive=parent/'application.tar';assert digest(archive)==S['archive_sha256'];R=A/Path(S['runtime_root']).relative_to(V)
assert not R.exists(),str(R);R.mkdir()
with tarfile.open(str(archive)) as t:
 for m in t.getmembers():assert not m.name.startswith('/') and '..' not in Path(m.name).parts and (m.isfile() or m.isdir()),m.name
 assert set(m.name for m in t.getmembers() if m.isfile())==set(S['source_files_sha256'])
 t.extractall(str(R))
for name,h in S['source_files_sha256'].items():
 p=R/name;assert p.is_file() and not p.is_symlink() and digest(p)==h,name
for name,target in S['live_links'].items():
 physical=A/Path(target).relative_to(V)
 if name!='docs/research/held_out.json':physical.mkdir(parents=True,exist_ok=True)
 assert physical.exists(),str(physical)
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists() and not p.is_symlink();p.symlink_to(target)
for p in sorted(R.rglob('*'),key=lambda p:len(p.parts),reverse=True):
 if p.is_symlink():continue
 p.chmod(0o555 if p.is_dir() or p.stat().st_mode&0o111 else 0o444)
R.chmod(0o555);image=P/'containers/ubuntu2204.sif';image.chmod(0o444)
for name in ('logs','receipts','timing','runtime-home'): (P/name).mkdir(exist_ok=True)
virtual_pilot=W/'outputs/_analyses/specificity-ladder/a2-bridges2-timing';virtual_pilot.mkdir(exist_ok=True)
result=dict(kind='a2_bridges2_verified_namespace_deployment_v1',checked_at=datetime.datetime.utcnow().isoformat()+'Z',source_commit=S['application_commit'],source_files=len(S['source_files_sha256']),transferred_files=len(M['files']),transferred_bytes=M['total_bytes'],source_archive_sha256=S['archive_sha256'],snapshot_sha256=digest(parent/'snapshot.json'),transfer_manifest_sha256=digest(P/'deployment/transfer-manifest.json'),physical_alignment_root=str(A),virtual_alignment_root=str(V),physical_runtime_root=str(R),virtual_runtime_root=S['runtime_root'],live_links=S['live_links'],image=str(image),image_sha256=digest(image),image_bytes=image.stat().st_size,source_ordinary_readonly=True,scientific_execution_authorized=False)
(P/'deployment/verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
