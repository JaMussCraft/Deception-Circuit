"""Replay only identity-building AST statements with stdlib stand-ins.
No pytest, production/native module imports, actual ledger or MAIN writes.
"""
import ast,copy,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;R=P/'candidate-r4'
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()
def target(node,name):return isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets)
def execute(body,namespace,filename):
    tree=ast.Module(body=body,type_ignores=[]);ast.fix_missing_locations(tree);exec(compile(tree,filename,'exec'),namespace)
helper=ast.parse((R/'root/helper.py').read_text())
source=ast.literal_eval(next(n.value for n in helper.body if target(n,'SOURCE')))
namespace={'copy':copy,'json':json,'m':SimpleNamespace(SOURCE=source,sha=sha),'t1':SimpleNamespace(GPU=R/'gpu')}
budget_tree=ast.parse((R/'tests/test_full_score_release.py').read_text())
budget=next(n for n in budget_tree.body if isinstance(n,ast.FunctionDef) and n.name=='budget_fixture')
execute([budget],namespace,'budget-fixture-stdlib-only')
ledger,mapping,g=namespace['budget_fixture'](namespace['m'],7200)
namespace.update(ledger=ledger,mapping=mapping,g=g,SOURCE=source)
func=next(n for n in ast.parse((R/'tests/test_full_score_root_integration.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='test_original_native_normalizer_preserves_full_mapping_chain')
start=next(i for i,n in enumerate(func.body) if target(n,'owning'))
end=next(i for i,n in enumerate(func.body) if target(n,'expected_identity'))
assert end>=start
execute(func.body[start:end+1],namespace,'corrected-identity-stdlib-only')
collector=next(n for n in helper.body if isinstance(n,ast.FunctionDef) and n.name=='collect_native_closure')
identity_node=next(n for n in collector.body if target(n,'identity'))
execute([identity_node],namespace,'unchanged-production-identity-expression-only')
assert namespace['identity']==namespace['expected_identity']
assert ledger['reservations'][1]['output_dir']==mapping['entries'][1]['actual_entry']['output_dir']==g['main_root']
result=dict(kind='SOURCE_ONLY_CORRECTED_IDENTITY_REPLAY',status='PASS',python=sys.version,
    identity=namespace['identity'],actual_groups_raw_sha256=sha(namespace['owning']['groups']),
    production_imported=False,native_imported=False,pytest_run=False,full_GREEN_run=False,
    actual_ledger_or_MAIN_written=False)
label='base39' if sys.version_info[:2]==(3,9) else 'mgnp'
(P/('identity-replay-'+label+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
