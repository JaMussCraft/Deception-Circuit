"""Bounded stdlib-only logger/child-status checks; never run the fixture or pytest."""
import ast
import gc
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
sys.dont_write_bytecode = True
import tempfile
import time
from types import SimpleNamespace
import weakref

PACKET = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


started = time.perf_counter()
preflight = module('r2_stage_recorder_unit', PACKET / 'fixture_preflight.py')
runtime_path = PACKET.parents[1] / 'plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py'
rt_tree = ast.parse(runtime_path.read_text())
observation = next(n for n in rt_tree.body if isinstance(n, ast.FunctionDef) and n.name == '_prepared_process_observation')
space = dict(os=os, Path=Path)
exec(compile(ast.Module(body=[observation], type_ignores=[]), str(runtime_path), 'exec'), space)
with tempfile.TemporaryDirectory(prefix='a3-r2-pure-', dir='/tmp') as temporary:
    root = Path(temporary)
    recorder = preflight.StageRecorder(root / 'logger', space['_prepared_process_observation'])
    holder = SimpleNamespace()
    def recurse(n): return 1 if n == 0 else 1 + holder.call(n-1)
    holder.call = recorder.watch(recurse, 'freeze_graph')
    assert holder.call(8) == 9
    rows = [json.loads(line) for line in (root / 'logger/stages.jsonl').read_text().splitlines()]
    assert len(rows) == 2 and [row['event'] for row in rows] == ['enter', 'exit']
    assert not recorder.stack and recorder.depth['freeze_graph'] == 0
    class Payload: pass
    payload = Payload(); reference = weakref.ref(payload)
    wrapped = recorder.watch(lambda value: 1, 'retained_graph_walk')
    assert wrapped(payload) == 1
    del payload; gc.collect(); assert reference() is None
    def bad(): raise ValueError('unit failure')
    try: recorder.watch(bad, 'guard')()
    except ValueError: pass
    else: raise AssertionError('original exception must propagate')
    assert not recorder.stack and recorder.depth['guard'] == 0
    rows = [json.loads(line) for line in (root / 'logger/stages.jsonl').read_text().splitlines()]
    assert rows[-1]['event'] == 'error' and rows[-1]['error_type'] == 'ValueError'
    assert all('observations' in row and 'wall_seconds' in row for row in rows)
    assert json.loads((root / 'logger/run_manifest.json').read_text())['last_event'] == rows[-1]

    runner = module('r2_packet_unit', PACKET / 'run_packet.py')
    tree = ast.parse((PACKET / 'run_packet.py').read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    outer = next(n for n in main.body if isinstance(n, ast.Try))
    loop = next(n for n in outer.body if isinstance(n, ast.For)); body = loop.body
    def predecessor(phase):
        sub = root / phase; sub.mkdir(); manifest = dict(results={})
        def save(): (sub / 'run_manifest.json').write_text(json.dumps(manifest))
        return dict(vars(runner), sub=sub, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), name='base',
            python=sys.executable, manifest=manifest, save=save)
    kill = [sys.executable, '-c', 'import os,signal;os.kill(os.getpid(),signal.SIGKILL)']
    start = next(i for i,n in enumerate(body) if isinstance(n, ast.Assign)
        and any(isinstance(t,ast.Name) and t.id == 'row' for t in n.targets))
    end = next(i for i,n in enumerate(body) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id == 'argv' for t in n.targets))
    ns = predecessor('oracle'); ns['oracle_cmd'] = kill
    try: exec(compile(ast.Module(body=body[start:end], type_ignores=[]), '<exact r2 oracle observer>', 'exec'), ns)
    except AssertionError: pass
    else: raise AssertionError('killed oracle must fail')
    oracle = json.loads((ns['sub'] / 'run_manifest.json').read_text())['results']['base']
    assert oracle['oracle_preflight']['exit_code'] == -9 and oracle['oracle_preflight']['termination_signal'] == 9
    assert oracle['status'] == 'ORACLE_FAILED' and oracle['normal_completion'] is False
    assert (ns['sub'] / 'oracle.stdout').exists() and (ns['sub'] / 'oracle.stderr').exists()

    start = next(i for i,n in enumerate(body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name)
        and n.value.func.value.id == 'row' and n.value.func.attr == 'update'
        and any(k.arg == 'status' and isinstance(k.value,ast.Constant) and k.value.value == 'PYTEST_STARTED'
            for k in n.value.keywords))
    end = next(i for i,n in enumerate(body) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id == 'cases' for t in n.targets))
    ns = predecessor('pytest'); ns.update(argv=kill, row=dict(normal_completion=False))
    ns['manifest']['results']['base'] = ns['row']
    try: exec(compile(ast.Module(body=body[start:end], type_ignores=[]), '<exact r2 pytest observer>', 'exec'), ns)
    except RuntimeError as error: assert 'without JUnit; no RED evidence' in str(error)
    else: raise AssertionError('killed pytest must not be RED')
    observed = json.loads((ns['sub'] / 'run_manifest.json').read_text())['results']['base']
    assert observed['pytest_exit_code'] == -9 and observed['termination_signal'] == 9
    assert observed['status'] == 'MISSING_JUNIT' and observed['junit_present'] is False
    assert observed['normal_completion'] is False

result = dict(status='PURE_PACKET_CHECKS_PASS', exit_code=0, recursive_calls=9, recursive_expected_events=2,
    recursive_observed_events=2, argument_graph_retained=False, original_exception_propagated=True,
    oracle_raw_kill_preserved=-9, pytest_raw_kill_preserved=-9, missing_JUnit_explicit=True,
    RED_accepted=False, full_preflight_executed=False, pytest_executed=False, model_loaded=False,
    wall_seconds=time.perf_counter()-started)
(PACKET / 'pure-check-results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
