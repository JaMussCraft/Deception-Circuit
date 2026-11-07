"""Brief read-only reproduction of the exact capture() ordinary-input loop body."""
import ast, hashlib, json
from pathlib import Path
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
A=W/'.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/proof-adapter-r2'
H=W/'.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-H100-R5/job-50189932'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
c=json.loads((H/'config.json').read_text()); m=Path(c['input_manifest']); assert sha(m)==c['input_manifest_sha256']; inputs=json.loads(m.read_text())
source=ast.parse((A/'proof_guards.py').read_text()); capture=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='capture')
loop=next(n for n in capture.body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [x.id for x in n.target.elts]==['n','row'])
unit=ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])); code=compile(unit,str(A/'proof_guards.py'),'exec')
closure=json.loads((A/'transfer-closure.json').read_text()); rows=[]
for r in closure['fresh_catalogues']:
 p=Path(r['virtual']); old=inputs['ordinary_files'][str(p)]; failure=None
 try: exec(code,{'inputs':{'ordinary_files':{str(p):old}},'Path':Path,'sha':sha})
 except AssertionError as e: failure=str(e)
 rows.append(dict(path=str(p),historical=old,current_bytes=p.stat().st_size,current_sha256=sha(p),actual_guard_assertion=failure))
assert len(rows)==4 and all(r['path'] in inputs['ordinary_files'] for r in rows)
print(json.dumps(dict(historical_manifest_sha256=sha(m),historical_manifest_catalogue_policy=inputs['current_catalogue_handling'],rows=rows,scope='only extracted real four-row predicate; no full capture/model/remote work'),indent=2))
