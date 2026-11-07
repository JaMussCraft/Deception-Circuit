"""Stdlib AST-only construction/call-site checks; no native imports or acceptance."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
S = HERE.parent.parent
ORIGINAL = S / 'plan/task23-green-r5/suite/test_a3_prepared_pilot_target.py'
CANDIDATE = HERE / ORIGINAL.name
PRODUCTION = S / 'plan-a3/direction-preallocation-candidate183/component_analysis'

def tree(path):
    return ast.parse(path.read_text())

def named(nodes, name):
    return next(node for node in nodes if getattr(node, 'name', None) == name)

def execute(nodes, namespace):
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), '<extracted exact AST>', 'exec'), namespace)

def require(condition, message):
    if not condition:
        raise ValueError(message)

old, new = tree(ORIGINAL), tree(CANDIDATE)
changed = {'test_prepared_receiver_resource_identity_and_capacity', 'test_prepared_final_barrier_after_all_costly_work'}
assert [ast.dump(n) for n in old.body if getattr(n, 'name', None) not in changed] == [ast.dump(n) for n in new.body if getattr(n, 'name', None) not in changed]
for name in changed:
    before, after = named(old.body, name), named(new.body, name)
    assert ast.dump(before.args) == ast.dump(after.args)
    assert [ast.dump(d) for d in before.decorator_list] == [ast.dump(d) for d in after.decorator_list]
    old_asserts = [ast.dump(n) for n in ast.walk(before) if isinstance(n, ast.Assert)]
    new_asserts = [ast.dump(n) for n in ast.walk(after) if isinstance(n, ast.Assert)]
    assert all(assertion in new_asserts for assertion in old_asserts)
    def rejection_contexts(function):
        return [ast.dump(item.context_expr) for node in ast.walk(function) if isinstance(node, ast.With)
                for item in node.items if isinstance(item.context_expr, ast.Call)
                and ast.unparse(item.context_expr.func) == 'pytest.raises']
    assert rejection_contexts(before) == rejection_contexts(after)

workload = tree(PRODUCTION / 'a3_direction_workload.py')
ns = {}
execute([named(workload.body, n) for n in ('_FrozenJSONDict', '_FrozenJSONList', '_freeze_json')], ns)
freeze = ns['_freeze_json']
refs = {name: freeze({'path': '/'+name, 'files': {'payload.json': {'sha256': 'a'*64, 'nbytes': 1}}}) for name in ('target', 'preparation')}
c = SimpleNamespace(resource_record={'references': refs, 'rows': freeze([{'x': 1}])})
function_old = named(old.body, 'test_prepared_receiver_resource_identity_and_capacity')
function_new = named(new.body, function_old.name)
def record_expr(function):
    return next(n.value for n in function.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'record' for t in n.targets))
results = []
for reference in refs:
    for capacity in (100, 99):
        original = eval(compile(ast.Expression(record_expr(function_old)), '<original record AST>', 'eval'), {'copy': copy, 'c': c})
        assert original['references'][reference] is refs[reference]
        try:
            original['references'][reference]['files']['payload.json']['sha256'] = '0'*64
        except TypeError as exc:
            assert str(exc) == 'validated inventory is immutable'
        else:
            raise AssertionError('original RED missing')
        record = eval(compile(ast.Expression(record_expr(function_new)), '<corrected record AST>', 'eval'), {'json': json, 'c': c})
        assert record == c.resource_record and type(record['references'][reference]) is dict
        record['references'][reference]['files']['payload.json']['sha256'] = '0'*64
        assert refs[reference]['files']['payload.json']['sha256'] == 'a'*64
        # Exact validator's initial reference rejection, no native dependencies.
        validator = named(tree(PRODUCTION/'a3_direction_runtime.py').body, '_validate_prepared_receiver_resources')
        prefix = copy.deepcopy(validator); prefix.body = [validator.body[1]]
        check_ns = {'require': require}
        execute([prefix], check_ns)
        try:
            check_ns[prefix.name](record, references=refs, source_identity=None, environment=None,
                                  actual_host_capacity=capacity, existing_host_obligations=50)
        except ValueError as exc:
            assert str(exc) == 'receiver resources target/source differs'
        else:
            raise AssertionError('validator mismatch did not reject')
        results.append({'reference': reference, 'capacity': capacity, 'old': 'TypeError before validator', 'new': 'construction succeeds; exact validator reference check raises ValueError'})
# Execute exact corrected nested wrappers and exact production final barrier.
fn = named(new.body, 'test_prepared_final_barrier_after_all_costly_work')
assert any(isinstance(n, ast.Call) and ast.unparse(n.func) == 'monkeypatch.setattr' and len(n.args)>1 and isinstance(n.args[1], ast.Constant) and n.args[1].value == 'live_guard' for n in ast.walk(fn))
production_barrier = named(named(tree(PRODUCTION/'a3_direction_runtime.py').body, '_PreparedPilotTarget').body, 'final_publication_barrier')
barrier_results = []
for damage in ('target-payload-restored-mtime', 'descriptor-marker', 'identical-target-tree'):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp); target = root/'target'; prep = root/'prep'
        target.mkdir(); prep.mkdir(); (target/'payload.json').write_text('{}'); (prep/'COMPLETE.json').write_text('{}')
        case = SimpleNamespace(root=root, target_path=target, preparation_path=prep)
        phase = {'final': False, 'mutated': False, 'final_live_guard_calls': 0}; trace = []
        def original_live_guard(*args, **kwargs):
            trace.append('original-live-guard'); return {'fresh': True}
        nsb = dict(require=require, time=time, _PREPARED_TARGET_SEAL=object(),
                   _check_file_witness=lambda witness: trace.append('file-witness'),
                   phase=phase, seam='final-live-guard', damage=damage, c=case,
                   shutil=shutil, os=os, original_live_guard=original_live_guard)
        execute([production_barrier], nsb)
        nsb['original_barrier'] = nsb['final_publication_barrier']
        execute([named(fn.body,n) for n in ('mutate','barrier','live_guard')], nsb)
        def cheap():
            trace.append('cheap-identity')
            if phase['mutated']: raise ValueError('prepared entry identity changed after final witness')
        handle = SimpleNamespace(_seal=nsb['_PREPARED_TARGET_SEAL'], args=None, design=None, protocol=None,
                                 pilot=None, witness=None, _deadline=time.time()+10,
                                 assert_scope=lambda *args: trace.append('scope'), _cheap_identity=cheap,
                                 _set_deadline=lambda evidence: trace.append('fresh-deadline'))
        nsb['live_guard'](None, None, None, None)
        assert not phase['mutated'] and phase['final_live_guard_calls'] == 0
        trace.clear()
        try:
            nsb['barrier'](handle, SimpleNamespace(check_deadline=lambda: trace.append('check-deadline')), {})
        except ValueError as exc:
            assert str(exc) == 'prepared entry identity changed after final witness'
        else:
            raise AssertionError('final barrier did not reject')
        assert phase == {'final': False, 'mutated': True, 'final_live_guard_calls': 1}
        assert trace == ['scope','cheap-identity','file-witness','original-live-guard','fresh-deadline','check-deadline','cheap-identity']
        barrier_results.append({'damage': damage, 'phase': phase, 'trace': trace})
nodeids = json.loads((S/'plan-a3/green-timeout-diagnosis253/full-collected-nodeids.json').read_text())
assert len(nodeids) == len(set(nodeids)) == 223
output = {'kind': 'PURE_AST_CONSTRUCTION_ONLY_NOT_NATIVE_ACCEPTANCE', 'resource_checks': results,
          'final_barrier_checks': barrier_results, 'all_other_AST_unchanged': True,
          'decorators_signatures_original_assertions_preserved': True,
          'historical_nodeids': len(nodeids), 'new_native_collection': False,
          'original_sha256': hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
          'candidate_sha256': hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()}
(HERE/'pure-check.json').write_text(json.dumps(output, indent=2)+'\n')
print(json.dumps(output, indent=2))
