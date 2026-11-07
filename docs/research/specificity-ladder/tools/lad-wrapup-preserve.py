from pathlib import Path
import os,json,shutil,hashlib,subprocess
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');W=D/'.claude/worktrees/specificity-ladder';P=D/'docs/research/specificity-ladder';O=P/'wrapup'
# Preserve local-only direction records; primary current records win collisions.
rows=[]
for root,dirs,files in os.walk(W/'docs/research/specificity-ladder',followlinks=False):
 for name in files:
  src=Path(root)/name;rel=src.relative_to(W/'docs/research/specificity-ladder');dst=P/rel
  if src.is_symlink():
   if not dst.exists() and not dst.is_symlink():dst.parent.mkdir(parents=True,exist_ok=True);os.symlink(os.readlink(src),dst)
   continue
  if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);os.link(src,dst);action='added'
  elif src.stat().st_size==dst.stat().st_size and hashlib.sha256(src.read_bytes()).digest()==hashlib.sha256(dst.read_bytes()).digest():action='same'
  else:
   dst=O/'worktree-direction-variants'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
   if not dst.exists():os.link(src,dst)
   action='variant'
  rows.append(dict(source=str(src),destination=str(dst.relative_to(D)),action=action,bytes=src.stat().st_size))
(O/'direction-preservation.json').write_text(json.dumps(rows,indent=2)+'\n')
# Explicit temporary helper files, not their scratch output trees.
helpers=[];dest=P/'tools';dest.mkdir(exist_ok=True)
for src in sorted(Path('/tmp').glob('lad-*')):
 if src.is_file() and src.suffix in ('.py','.sh'):
  dst=dest/src.name
  if dst.exists():assert src.read_bytes()==dst.read_bytes()
  else:shutil.copyfile(src,dst)
  helpers.append(dict(path=str(dst.relative_to(D)),bytes=dst.stat().st_size,sha256=hashlib.sha256(dst.read_bytes()).hexdigest()))
(O/'helpers-preservation.json').write_text(json.dumps(helpers,indent=2)+'\n')
print(json.dumps(dict(direction_files=len(rows),variants=sum(r['action']=='variant' for r in rows),helpers=len(helpers))))
