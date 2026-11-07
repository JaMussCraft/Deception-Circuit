import json,os
from pathlib import Path
v=Path('/projects/beto/swong2/Alignment')
r=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment')
p=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/deployment/canonical-transfer-manifest.json')
m=json.loads(p.read_text()); out=[]
for src,target in m['namespace_aliases'].items():
 dst=r/Path(src).relative_to(v);Path(target).relative_to(v)
 if os.path.lexists(str(dst)):
  assert dst.is_symlink() and os.readlink(str(dst))==target,str(dst)
  action='unchanged'
 else:
  dst.parent.mkdir(parents=True,exist_ok=True);dst.symlink_to(target);action='created'
 out.append(dict(path=str(dst),target=target,action=action))
print(json.dumps(dict(aliases=out,count=len(out),hash_validation_pending=True),indent=2))
