"""Stdlib/source-only contract probe. Never imports native or production code."""
import ast,copy,hashlib,json
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent
S=P.parent
OLD=S/'plan-plan-a2-full-score-operational186/task3/green270-r3'
C=OLD/'closure/sdd/plan-a2-full-score-operational186/candidate'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
# Execute only the tiny pre-existing budget fixture function, extracted from
# its AST into a stdlib namespace. No test module imports or pytest execution.
source=C/'tests/test_full_score_release.py'
tree=ast.parse(source.read_text())
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='budget_fixture')
module=ast.Module(body=[function],type_ignores=[]);ast.fix_missing_locations(module)
namespace={'copy':copy};exec(compile(module,str(source),'exec'),namespace)
config=json.loads((C/'gpu/config.template.json').read_text())
ledger,mapping,g=namespace['budget_fixture'](SimpleNamespace(SOURCE=config['commit']),7200)
assert 'groups_file_sha256' not in g
try:
    identity=dict(purpose='A2 original source50e full scoring',source_commit=config['commit'],groups_sha256=g['groups_file_sha256'],main_root=g['main_root'])
except KeyError as error:
    failure=str(error)
else:raise AssertionError('old fixture did not reproduce mandatory-field failure')
assert sha(config['groups'])==config['groups_file_sha256']
# Static declaration and consumer evidence; no module import/native call.
common=ast.parse((C/'gpu/common.py').read_text())
config_guard=next(n for n in common.body if isinstance(n,ast.FunctionDef) and n.name=='validate_config')
assert "groups_file_sha256" in (C/'gpu/common.py').read_text()
helper=ast.parse((C/'root/helper.py').read_text())
collector=next(n for n in helper.body if isinstance(n,ast.FunctionDef) and n.name=='collect_native_closure')
reads=sorted({n.slice.value for n in ast.walk(collector) if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='g' and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str)})
result=dict(kind='SOURCE_ONLY_FIXTURE_CONTRACT_DIAGNOSIS',production_imported=False,native_imported=False,pytest_run=False,
    observed_failure=failure,budget_fixture_keys=sorted(g),native_collector_config_reads=reads,
    missing_identity_fields=[k for k in ('groups_file_sha256','main_root') if k not in g],
    accepted_identity=dict(source_commit=config['commit'],groups_file_sha256=config['groups_file_sha256'],main_root=config['main_root'],groups=config['groups']),
    actual_groups_raw_sha256=sha(config['groups']),source_pins={str(p):sha(p) for p in (source,C/'tests/test_full_score_root_integration.py',C/'root/helper.py',C/'gpu/config.template.json',C/'gpu/common.py')},
    root_cause='budget-only fixture reused at full scoring identity boundary before native normalization',
    production_change_required=False)
(P/'diagnosis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
