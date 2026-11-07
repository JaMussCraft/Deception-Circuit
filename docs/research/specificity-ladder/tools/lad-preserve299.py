from pathlib import Path
import hashlib,json,subprocess
A=Path('/projects/beto/swong2/Alignment');D=A/'Deception-Circuit';P=D/'docs/research/specificity-ladder';S=D/'.claude/worktrees/specificity-ladder/.superpowers/sdd';O=P/'reports/cpu-evidence-299';O.mkdir(exist_ok=True)
inv=S/'plan-evidence-preservation299/inventory.json';v=json.loads(inv.read_text());assert not v['missing_or_ambiguous'] and not v['receipt_mismatches'];rows=[];paths=[]
def add(src,dst,expected=None):
 src=Path(src);dst=Path(dst);assert src.is_file() and not src.is_symlink();b=src.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected:assert len(b)==expected['bytes'] and h==expected['sha256'],str(src)
 dst.parent.mkdir(parents=True,exist_ok=True)
 if src!=dst and not dst.exists():
  with dst.open('xb') as f:f.write(b)
 assert dst.read_bytes()==b
 if any(r['preserved']==str(dst.relative_to(D)) for r in rows):return
 rows.append(dict(original=str(src),preserved=str(dst.relative_to(D)),bytes=len(b),sha256=h));paths.append(str(dst.relative_to(D)))
for row in v['files']:
 rel=Path(row['destination']);assert not rel.is_absolute() and '..' not in rel.parts
 src=Path(row['source']);dst=src if src.is_relative_to(P/'reports') else O/rel
 add(src,dst,row)
add(inv,O/'selected-source-inventory.json')
for folder in ['plan-a3/sharded-deployment293','plan-a2-task4-deployment298']:
 p=S/folder
 for f in sorted(p.iterdir()):
  if f.is_file() and f.suffix in ('.json','.sha256','.py','.sh'):add(f,O/'sdd'/folder/f.name)
 if 'sharded-deployment' in folder:
  for slot in ['base-0','base-1','mgnp-0','mgnp-1']:
   for f in sorted((p/slot).iterdir()):
    if f.is_file() and f.suffix in ('.json','.sha256','.sh'):add(f,O/'sdd'/folder/slot/f.name)
q=S/'plan/task23-green-r8-sharded'
for n in ['run_packet.py','aggregate.py','selector.py','supervisor.py','partition.json','source-pins.json','transport-inventory.json','cpu.sbatch','bridges/host.py','bridges/inner.py','bridges/transport229.py','bridges/launch.sh','bridges/manifest.json']:
 add(q/n,O/'r8-controls'/n)
for folder in ['plan-a2-whole-packet289-r2','plan-a2-whole-packet-review296-r2']:
 p=S/folder
 for f in p.iterdir():
  if f.is_file():add(f,O/'sdd'/folder/f.name)
 if folder.endswith('289-r2'):
  for f in (p/'candidate').iterdir():
   if f.is_file():add(f,O/'sdd'/folder/'candidate'/f.name)
  f=p/'candidate/tests/test_full_score_integration.py';add(f,O/'sdd'/folder/'candidate/tests'/f.name)
for n in ['lad-a3-monitor273.py','lad-a3-fetch273.py','lad-a3-shards293.py','lad-a3-release293.py','lad-a3-monitor293.py','lad-a3-fetch293.py','lad-a2-green288.py','lad-a2-task4-298.py','lad-preserve299-first.py','lad-preserve299.py']:
 add(Path('/tmp')/n,O/'root-helpers'/n)
for n in ['276-handback.md','278-handback.md','279-handback.md','281-handback.md','284-handback.md','286-handback.md','289-handback.md','289-r2-handback.md','299-evidence-preservation-handback.md']:
 f=P/'reports'/n
 if f.exists():add(f,f)
manifest=O/'preservation-manifest.json';manifest.write_text(json.dumps(dict(files=rows,scope='Explicit completed terminal evidence, selected source corrections and current deployment controls; not a full candidate export or new scientific acceptance.'),indent=2)+'\n');paths.append(str(manifest.relative_to(D)))
for n in ['RESUME.md','WORKLOG.md','state.json','worklog.json']:
 paths.append(str((P/n).relative_to(D)))
paths=sorted(set(paths));Path('/tmp/lad-commit299-paths.json').write_text(json.dumps(paths,indent=2)+'\n')
fail=[]
for p in paths:
 if p.endswith('.md'):
  r=subprocess.run(['research-session','lint',str(D/p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
  if r.returncode:fail.append(dict(path=p,stdout=r.stdout,stderr=r.stderr))
(O/'markdown-lint-results.json').write_text(json.dumps(dict(failures=fail),indent=2)+'\n')
paths.append(str((O/'markdown-lint-results.json').relative_to(D)));Path('/tmp/lad-commit299-paths.json').write_text(json.dumps(paths,indent=2)+'\n')
print(json.dumps(dict(files=len(rows),bytes=sum(r['bytes'] for r in rows),commit_paths=len(paths),lint_failures=fail)))
