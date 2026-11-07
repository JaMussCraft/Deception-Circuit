from pathlib import Path
import json,subprocess,os
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');W=D/'.claude/worktrees/specificity-ladder';O=D/'docs/research/specificity-ladder/wrapup'
paths=json.loads((O/'packet-git-files.json').read_text())
for prefix in ['component_analysis','tests','scripts']:
 paths+=subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','--',prefix],cwd=W,universal_newlines=True).splitlines()
for name in ['spec.md','plan-a1.md','plan-a2.md','plan-ladder.md','a1-data-contract.md','a2-cohort-ruling.json']:
 p=W/'docs/research/specificity-ladder'/name;assert p.exists(),str(p);paths.append(str(p.relative_to(W)))
paths=sorted(set(paths));assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=W).strip()
for x in paths:assert (W/x).exists() or (W/x).is_symlink(),x
manifest=O/'branch-source-explicit-files.json';manifest.write_text(json.dumps(paths,indent=2)+'\n')
f=O/'branch-source.pathspec';f.write_bytes(b''.join(x.encode()+b'\0' for x in paths))
r=subprocess.run(['git','add','-f','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True);(O/'branch-source-stage.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=W,universal_newlines=True).splitlines();assert set(staged)<=set(paths)
# This is archival preservation of unfinished research, not a claim of passing tests.
r=subprocess.run(['git','commit','-q','-m','Preserve unfinished specificity-ladder source and research packets for closure'],cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True);(O/'branch-source-commit.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=W,universal_newlines=True).strip();(O/'branch-source-commit.json').write_text(json.dumps(dict(commit=head,files=len(staged),scientific_acceptance=False,new_tests_run=False),indent=2)+'\n');print(head,len(staged),flush=True)
