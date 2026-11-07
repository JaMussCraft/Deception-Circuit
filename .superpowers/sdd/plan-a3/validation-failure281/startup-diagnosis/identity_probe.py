"""Extracted identity expression/guards only; no native imports or record reads."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).parents[2] / 'direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py'
tree = ast.parse(SOURCE.read_text())
builder = next(n for n in tree.body if getattr(n, 'name', None) == '_completed_pilot_index')
record = next(n.value for n in builder.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'record' for t in n.targets))
process = next(k.value for k in record.keywords if k.arg == 'process')
validator = next(n for n in tree.body if getattr(n, 'name', None) == '_validate_startup_record')
guards = [n for n in validator.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
          and any(isinstance(a, ast.Constant) and a.value in
                  ('startup record process/job differs', 'startup record process differs from linked shard')
                  for a in n.value.args)]
assert len(guards) == 2
guard_code = compile(ast.Module(body=guards, type_ignores=[]), str(SOURCE), 'exec')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def check(process_value, expected_job, expected_pid):
    exec(guard_code, dict(record={'process': process_value}, expected_job_id=expected_job,
                          expected_pid=expected_pid, require=require))


results = []
for label, environment, injected, expected in [
        ('injected-no-slurm', {}, True, 'injected-cpu'),
        ('injected-slurm', {'SLURM_JOB_ID': '50319108'}, True, '50319108'),
        ('production-no-slurm', {}, False, 'host-cpu'),
        ('production-slurm', {'SLURM_JOB_ID': '50319108'}, False, '50319108')]:
    # os stand-in isolates the expression; the real environment is never altered.
    value = eval(compile(ast.Expression(process), str(SOURCE), 'eval'),
                 dict(os=SimpleNamespace(environ=environment, getpid=lambda: 741),
                      design={'injected': injected}, scenarios=[]))
    assert value == {'pid': 741, 'job_id': expected, 'scenario_references': []}
    check(value, expected, 741)
    rejected = []
    for damage, job, pid in [('wrong-job', expected + ':wrong', 741), ('wrong-pid', expected, 742)]:
        try:
            check(value, job, pid)
        except ValueError:
            rejected.append(damage)
        else:
            raise AssertionError(damage + ' accepted')
    old_rejects = False
    try:
        check(value, 'injected-cpu', None)
    except ValueError:
        old_rejects = True
    assert old_rejects is (expected != 'injected-cpu')
    results.append(dict(case=label, expected_job=expected, hardcoded_injected_rejects=old_rejects,
                        correct_identity_passes=True, rejected=rejected))
print(json.dumps(dict(scope='NON_NATIVE_EXTRACTED_PROCESS_EXPRESSION_AND_TWO_GUARDS_ONLY',
                      cases=results), indent=2))
