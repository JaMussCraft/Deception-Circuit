from pathlib import Path
import ast, hashlib, json, time
p=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r3')
start=time.monotonic()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(p/'packet-pins.json')=='ccdc7493aae4f4e45ed35d1d6ed67fd1b0c5ced36808449a364f464cb9203bf5'
assert sha(p/'original-source-pins.json')=='56c763fbbd910a890e3fdeafe87337257d82dceb182916f0d3d7b93c64dad0e7'
counts={}
for manifest in ('packet-pins.json','original-source-pins.json'):
    entries=json.loads((p/manifest).read_text())
    for name,digest in entries.items():
        path=p/name if manifest=='packet-pins.json' else Path(name)
        assert sha(path)==digest,str(path)
        assert time.monotonic()-start<25
    counts[manifest]=len(entries)
c=p/'closure/sdd/plan-a2-full-score-operational186/candidate'
files=[c/'root/helper.py']+list((c/'tests').glob('test_full_score_root_*.py'))+[p/'run_cpu_green.py']
for path in files:ast.parse(path.read_text(),filename=str(path))
result=dict(scope='stdlib hashes and AST only',manifest_member_counts=counts,syntax_files=len(files),helper_sha256=sha(c/'root/helper.py'),seconds=time.monotonic()-start,result='PASS')
Path(__file__).with_name('checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
