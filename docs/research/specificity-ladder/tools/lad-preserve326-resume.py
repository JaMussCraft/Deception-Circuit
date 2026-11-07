from pathlib import Path
import hashlib,json,shutil,subprocess,time
A=Path('/projects/beto/swong2/Alignment');P=A/'Deception-Circuit/docs/research/specificity-ladder';W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';inventory=W/'.superpowers/sdd/plan-evidence-preservation326/inventory.json'
v=json.loads(inventory.read_text());dst=Path(v['destination_root']);assert dst==P/'reports/cpu-evidence-326'
for row in v['files']:
 p=Path(row['source']);q=Path(row['relative_destination']);assert not q.is_absolute() and '..' not in q.parts
 data=p.read_bytes();assert len(data)==row['size'] and hashlib.sha256(data).hexdigest()==row['sha256'],str(p)
copied=[];lint=[];raw=[];rows=[]
for row in v['files']:
 p=Path(row['source']);q=dst/row['relative_destination'];q.parent.mkdir(parents=True,exist_ok=True)
 if not q.exists():
  with q.open('xb') as f:f.write(p.read_bytes())
 assert hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256']
 if q.suffix=='.md':
  r=subprocess.run(['research-session','lint',str(q)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
  lint.append(dict(path=str(q),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
  if r.returncode:
   out=q.with_suffix('.md.raw');assert not out.exists();q.rename(out);raw.append(dict(original_relative_destination=row['relative_destination'],raw_relative_destination=str(out.relative_to(dst)),reason='Immutable source Markdown contains pre-existing lint violations; preserved byte-for-byte as raw evidence.'));q=out
 new=dict(row);new['relative_destination']=str(q.relative_to(dst));rows.append(new);copied.append(str(q.relative_to(A/'Deception-Circuit')))
v['files']=rows;v['raw_markdown_notes']=raw
for name,data in [('preservation-manifest.json',v),('root-copy-check.json',dict(files=len(rows),bytes=sum(x['size'] for x in rows),all_hashes_verified=True,observed_unix=time.time(),markdown_lint=lint,raw_markdown_notes=raw))]:
 with(dst/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
 copied.append(str((dst/name).relative_to(A/'Deception-Circuit')))
Path('/tmp/lad-commit326-paths.json').write_text(json.dumps(copied,indent=2)+'\n');print(json.dumps(dict(files=len(rows),bytes=sum(x['size'] for x in rows),raw_markdown=raw)))
