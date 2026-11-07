"""Static preservation and extracted identity checks; no native module imports."""
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
SDD = HERE.parents[1]
OLD = SDD / 'plan/task23-green-r6-r2-sharded/suite/test_a3_direction_runtime.py'
NEW = HERE / 'tests/test_a3_direction_runtime.py'
RUNTIME = SDD / 'plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py'
NAME = 'test_completed_index_startup_is_measured_conditionally_and_charged_per_job'


def dump(node):
    return ast.dump(node, include_attributes=False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


a, b = OLD.read_text(), NEW.read_text()
ta, tb = ast.parse(a), ast.parse(b)
compile(a, str(OLD), 'exec'); compile(b, str(NEW), 'exec')
assert len(ta.body) == len(tb.body)
for na, nb in zip(ta.body, tb.body):
    if getattr(na, 'name', None) != NAME:
        assert dump(na) == dump(nb)
old = next(n for n in ta.body if getattr(n, 'name', None) == NAME)
new = next(n for n in tb.body if getattr(n, 'name', None) == NAME)
assert dump(old.args) == dump(new.args) and [dump(n) for n in old.decorator_list] == [dump(n) for n in new.decorator_list]


class NormalizeOriginal(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute) and node.func.attr == '_validate_startup_record':
            for keyword in node.keywords:
                if keyword.arg == 'expected_job_id':
                    keyword.value = ast.Name(id='expected_job_id', ctx=ast.Load())
                elif keyword.arg == 'expected_pid':
                    keyword.value = ast.parse('expected_pid+1', mode='eval').body
        return node


# Every original statement remains, allowing only the requested call-argument changes.
normalized = NormalizeOriginal().visit(copy.deepcopy(old))
positive = next(n for n in normalized.body if isinstance(n, ast.Assert)
                and any(isinstance(c, ast.Attribute) and c.attr == '_validate_startup_record' for c in ast.walk(n)))
call = next(n for n in ast.walk(positive) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == '_validate_startup_record')
call.keywords.append(ast.keyword(arg='expected_pid', value=ast.Name(id='expected_pid', ctx=ast.Load())))
remaining = list(new.body)
for statement in normalized.body:
    index = next((i for i, n in enumerate(remaining) if dump(n) == dump(statement)), None)
    assert index is not None, ast.dump(statement)
    # Added nodes may intervene; the original order must remain exact.
    remaining = remaining[index + 1:]
old_asserts = sum(isinstance(n, ast.Assert) for n in ast.walk(old))
new_asserts = sum(isinstance(n, ast.Assert) for n in ast.walk(new))
assert new_asserts == old_asserts + 1
calls = [n for n in ast.walk(new) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr == '_validate_startup_record']
assert len(calls) == 5
assert all(not isinstance(k.value, ast.Constant) for n in calls for k in n.keywords if k.arg == 'expected_job_id')
captures = [n for n in new.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in ('expected_job_id', 'expected_pid') for t in n.targets)]
assert len(captures) == 2
first_capture = min(new.body.index(n) for n in captures)
first_construction = next(i for i,n in enumerate(new.body) if any(isinstance(c, ast.Name) and c.id == '_fake_pilot_inputs' for c in ast.walk(n)))
assert first_capture < first_construction
capture_code = compile(ast.Module(body=captures, type_ignores=[]), str(NEW), 'exec')
rt = ast.parse(RUNTIME.read_text())
validator = next(n for n in rt.body if getattr(n, 'name', None) == '_validate_startup_record')
guards = [n for n in validator.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
          and any(isinstance(v, ast.Constant) and v.value in ('startup record process/job differs', 'startup record process differs from linked shard') for v in n.value.args)]
assert len(guards) == 2
guard_code = compile(ast.Module(body=guards, type_ignores=[]), str(RUNTIME), 'exec')
checks = []
for environment, expected in [({}, 'injected-cpu'), ({'SLURM_JOB_ID': '50319108'}, '50319108'), ({'SLURM_JOB_ID': ''}, '')]:
    namespace = dict(os=SimpleNamespace(environ=environment, getpid=lambda: 741))
    exec(capture_code, namespace)
    assert namespace['expected_job_id'] == expected and namespace['expected_pid'] == 741
    outcomes = []
    for call in calls:
        values = {k.arg: eval(compile(ast.Expression(k.value), str(NEW), 'eval'), namespace) for k in call.keywords}
        guard_ns = dict(record={'process': {'job_id': expected, 'pid': 741}}, require=require, expected_pid=None)
        guard_ns.update(values)
        try:
            exec(guard_code, guard_ns)
        except ValueError:
            outcomes.append('reject')
        else:
            outcomes.append('pass')
    assert outcomes == ['pass', 'reject', 'reject', 'pass', 'pass'], outcomes
    checks.append(dict(environment=environment, independent_expected_job=expected, validator_call_outcomes=outcomes))
payload = dict(scope='NON_NATIVE_STATIC_AND_EXTRACTED_IDENTITY_ARGUMENTS_GUARDS_ONLY',
               original=str(OLD), draft=str(NEW), original_sha256=hashlib.sha256(a.encode()).hexdigest(),
               draft_sha256=hashlib.sha256(b.encode()).hexdigest(),
               changed_function=NAME, all_other_top_level_asts_equal=True, original_statement_order_preserved=True,
               original_assertions=old_asserts, draft_assertions=new_asserts, identity_specimens=checks)
(HERE / 'scope-pins.json').write_text(json.dumps(payload, indent=2) + '\n')
(HERE / 'test_a3_direction_runtime.diff').write_text(''.join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile=str(OLD), tofile=str(NEW))))
print(json.dumps(payload, indent=2))
