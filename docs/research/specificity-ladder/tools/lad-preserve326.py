from pathlib import Path
import hashlib,json,shutil,subprocess,time
A=Path('/projects/beto/swong2/Alignment');P=A/'Deception-Circuit/docs/research/specificity-ladder';W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';inventory=W/'.superpowers/sdd/plan-evidence-preservation326/inventory.json'
v=json.loads(inventory.read_text());dst=Path(v['destination_root']);assert dst==P/'reports/cpu-evidence-326';assert not dst.exists()
for row in v['files']:
 p=Path(row['source']);q=Path(row['relative_destination']);assert not q.is_absolute() and '..' not in q.parts
 data=p.read_bytes();assert len(data)==row['size'] and hashlib.sha256(data).hexdigest()==row['sha256'],str(p)
dst.mkdir();copied=[];lint=[]
for row in v['files']:
 p=Path(row['source']);q=dst/row['relative_destination'];q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 assert hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256'];copied.append(str(q.relative_to(A/'Deception-Circuit')))
 if q.suffix=='.md':
  r=subprocess.run(['research-session','lint',str(q)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
  lint.append(dict(path=str(q),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
  if r.returncode:raise RuntimeError('preserved raw Markdown lint failure: '+str(q))
shutil.copyfile(inventory,dst/'preservation-manifest.json');copied.append(str((dst/'preservation-manifest.json').relative_to(A/'Deception-Circuit')))
receipt=dict(files=len(v['files']),bytes=sum(x['size'] for x in v['files']),all_hashes_verified=True,observed_unix=time.time(),markdown_lint=lint)
(dst/'root-copy-check.json').write_text(json.dumps(receipt,indent=2)+'\n');copied.append(str((dst/'root-copy-check.json').relative_to(A/'Deception-Circuit')))
Path('/tmp/lad-commit326-paths.json').write_text(json.dumps(copied,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['files','bytes','all_hashes_verified']}))
