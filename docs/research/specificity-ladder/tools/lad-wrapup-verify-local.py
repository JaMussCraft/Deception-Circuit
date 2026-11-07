from pathlib import Path
import os,json
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');W=D/'.claude/worktrees/specificity-ladder';O=D/'docs/research/specificity-ladder/wrapup';results=[];bad=[]
for name in ['outputs','logs']:
 count=links=bytes_=0
 for root,ds,fs in os.walk(W/name,followlinks=False):
  for n in ds+fs:
   src=Path(root)/n;dst=D/src.relative_to(W)
   if src.is_symlink():
    links+=1
    if not dst.is_symlink() or os.readlink(src)!=os.readlink(dst):bad.append(str(src))
   elif src.is_file():
    count+=1;size=src.stat().st_size;bytes_+=size
    if not dst.is_file() or dst.stat().st_size!=size:bad.append(str(src))
 results.append(dict(root=name,source_regular_files=count,source_links=links,source_bytes=bytes_))
(O/'local-output-verification.json').write_text(json.dumps(dict(results=results,mismatches=bad,success=not bad),indent=2)+'\n');print(json.dumps(dict(results=results,mismatches=len(bad))))
