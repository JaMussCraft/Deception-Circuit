from pathlib import Path
import hashlib,json,shutil
A=Path('/projects/beto/swong2/Alignment');D=A/'Deception-Circuit';P=D/'docs/research/specificity-ladder';S=D/'.claude/worktrees/specificity-ladder/.superpowers/sdd';O=P/'reports/root-cpu-deployments-273-275';O.mkdir(exist_ok=False);rows=[]
def add(src,rel):
 src=Path(src);assert src.is_file() and not src.is_symlink();dst=O/rel;dst.parent.mkdir(parents=True,exist_ok=True);b=src.read_bytes();dst.write_bytes(b);assert dst.read_bytes()==b;rows.append(dict(original=str(src),preserved=str(dst.relative_to(D)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
p=S/'plan-a3/sharded-deployment273'
for f in sorted(p.iterdir()):
 if f.is_file():add(f,Path('a3-deployment273')/f.name)
for slot in ['base-0','base-1','mgnp-0','mgnp-1']:
 for f in sorted((p/slot).iterdir()):
  if f.is_file() and f.suffix in ('.json','.sh','.sha256'):add(f,Path('a3-deployment273')/slot/f.name)
for src,rel in [(S/'plan-a3/sharded-deployment273-review','a3-review273'),(S/'plan-a3/sharded-validation-review272/r2','a3-review272-r2'),(S/'plan-a2-task3-deployment275','a2-deployment275'),(S/'plan-a2-task3-review274','a2-review274')]:
 for f in sorted(src.iterdir()):
  if f.is_file() and f.suffix in ('.json','.sh','.py'):add(f,Path(rel)/f.name)
q=S/'plan/task23-green-r6-r2-sharded'
for n in ['run_packet.py','aggregate.py','selector.py','supervisor.py','partition.json','source-pins.json','transport-inventory.json','cpu.sbatch','bridges/host.py','bridges/inner.py','bridges/transport229.py','bridges/launch.sh','bridges/manifest.json']:
 add(q/n,Path('a3-r6-r2-controls')/n)
q=S/'plan-plan-a2-full-score-operational186/task3/green270-r3'
for n in ['run_cpu.sh','run_cpu_green.py','resources.json','packet-pins.json','original-source-pins.json','native-snapshot.json']:
 add(q/n,Path('a2-green270-r3-controls')/n)
for n in ['lad-a3-shards273.py','lad-a3-release273.py','lad-a2-green275.py']:add(Path('/tmp')/n,Path('root-helpers')/n)
(O/'preservation-manifest.json').write_text(json.dumps(dict(files=rows,scope='Explicit control, review and deployment evidence; no recursive fixture/output trees copied'),indent=2)+'\n')
paths=[str((O/'preservation-manifest.json').relative_to(D))]+[r['preserved'] for r in rows]
for n in ['259-r2-handback.md','269-r2-handback.md','272-r2-handback.md','273-handback.md','274-handback.md']:paths.append(str((P/'reports'/n).relative_to(D)))
for n in ['RESUME.md','WORKLOG.md','state.json','worklog.json']:paths.append(str((P/n).relative_to(D)))
Path('/tmp/lad-commit277-paths.json').write_text(json.dumps(paths,indent=2)+'\n');print(len(rows),'preserved files;',sum(r['bytes'] for r in rows),'bytes;',len(paths),'explicit commit paths')
