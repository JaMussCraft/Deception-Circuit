from pathlib import Path
import os,json,subprocess
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');P=D/'docs/research/specificity-ladder';O=P/'wrapup';paths=[]
for root,dirs,files in os.walk(P,followlinks=False):
 for n in files:
  f=Path(root)/n
  if not f.is_symlink():assert f.stat().st_size<100000000,str(f)
  paths.append(str(f.relative_to(D)))
paths+=json.loads((O/'packet-git-files.json').read_text())
for f in (D/'.superpowers/sdd/plan-a3/producer-deployment320/terminal').rglob('*'):
 if f.is_file() or f.is_symlink():paths.append(str(f.relative_to(D)))
paths+=['.superpowers/sdd/plan-a3/producer-deployment320/terminal-fetch.json']
paths+=['docs/research/'+n for n in ['INDEX.md','FINDINGS.md','directions.json','DIRECTIONS.md','SESSIONS.md','ledger.json']]
paths=sorted(set(paths));assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=D).strip()
for n in paths:assert (D/n).exists() or (D/n).is_symlink(),n
# Explicit list contains only this direction, its packet carry-over, and the requested registry views.
(O/'primary-commit-files.json').write_text(json.dumps(paths,indent=2)+'\n');paths.append(str((O/'primary-commit-files.json').relative_to(D)))
f=Path('/tmp/lad-wrapup-primary.pathspec');f.write_bytes(b''.join(n.encode()+b'\0' for n in paths))
r=subprocess.run(['git','add','-f','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=D,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True);assert r.returncode==0,r.stderr
staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=D,universal_newlines=True).splitlines();assert set(staged)<=set(paths)
print('Staged owned closure files',len(staged),flush=True)
r=subprocess.run(['git','commit','-q','-m','Preserve specificity-ladder closure, registered A2 result and carry-over artifacts'],cwd=D,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True);assert r.returncode==0,r.stderr
print(subprocess.check_output(['git','rev-parse','HEAD'],cwd=D,universal_newlines=True).strip(),flush=True)
