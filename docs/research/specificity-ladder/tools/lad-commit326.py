from pathlib import Path
import json,subprocess
repo=Path('/projects/beto/swong2/Alignment/Deception-Circuit');p=repo/'docs/research/specificity-ladder'
paths=json.loads(Path('/tmp/lad-commit307-paths.json').read_text())+json.loads(Path('/tmp/lad-commit326-paths.json').read_text())
for n in range(308,327):
 for f in (p/'reports').glob(str(n)+'-*.md'):paths.append(str(f.relative_to(repo)))
paths=sorted(set(paths));assert all(x.startswith('docs/research/specificity-ladder/') for x in paths)
for name in paths:
 f=repo/name;assert f.is_file(),name
 if f.suffix=='.md':subprocess.run(['research-session','lint',str(f)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
r=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=str(repo),universal_newlines=True);assert not r.strip(),r
f=Path('/tmp/lad-commit326-pathspec');f.write_bytes(b''.join(x.encode()+b'\0' for x in paths))
subprocess.run(['git','add','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=str(repo),check=True,timeout=60)
staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=str(repo),universal_newlines=True).splitlines();assert set(staged)<=set(paths)
print(json.dumps(dict(explicit_paths=len(paths),staged_paths=len(staged),all_markdown_lint=True)))
