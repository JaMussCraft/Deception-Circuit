"""Only extracted original stdlib rejection statements, not a native integration."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parent
C=S/'plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate'
D=S/'plan-a2-task4-deployment324/run-01/base39-tmp'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def require(ok,msg):
 if not ok:raise ValueError(msg)
def fn(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
common=ast.parse((C/'gpu/common.py').read_text());helper=ast.parse((C/'root/helper.py').read_text());observations={}
# Use completed actual BASE paths read-only. Execute only the original score
# presence prefix, never the full bank reader, normalizer or model code.
roots=[path for path in D.glob('test_whole_chain_normal_*') if not path.is_symlink()]
assert len(roots)==1
root=roots[0]/'MAIN'
node=fn(common,'_bank_binding')
ns=dict(Path=Path,c={'main_root':str(root)},allow_score=False,require=require)
try:exec(compile(ast.Module(body=node.body[:3],type_ignores=[]),'ORIGINAL_BANK_PREFIX','exec'),ns)
except ValueError as error:assert str(error)=='score already exists or is symlink';observations['completed_score']=str(error)
else:raise AssertionError('existing score not rejected')
case=D/'test_transfer_failure_cannot_c0';config=read(case/'evidence/bound-config.json');manifest=read(config['input_manifest']);name=config['minimum_registry_paths'][0];path=Path(name);digest=manifest['ordinary_sha256'][name]
loop=next(n for n in fn(common,'input_closure').body if isinstance(n,ast.For));predicate=next(n for n in loop.body if isinstance(n,ast.Expr))
ns=dict(path=path,digest=digest,sha=sha,name=name,require=require)
try:exec(compile(ast.Module(body=[predicate],type_ignores=[]),'ORIGINAL_INPUT_PREDICATE','exec'),ns)
except ValueError as error:assert str(error)=='ordinary input changed: '+name;observations['catalogue']=str(error)
else:raise AssertionError('retained tamper not rejected')
claim=P/'evidence/pure-existing.claim';claim.write_bytes(b'prior claim remains')
prior=claim.read_bytes();ns=dict(Path=Path)
exec(compile(ast.Module(body=[fn(helper,'exclusive')],type_ignores=[]),'ORIGINAL_EXCLUSIVE','exec'),ns)
try:ns['exclusive'](claim,b'must not replace')
except FileExistsError as error:assert error.filename==str(claim);observations['claim_filename']=error.filename
else:raise AssertionError('exclusive claim replaced')
assert claim.read_bytes()==prior
result=dict(scope='extracted original stdlib guard characterization only',observations=observations,claim_bytes_preserved=True,native_imports=False,pytest=False)
(P/'evidence/retry-probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
