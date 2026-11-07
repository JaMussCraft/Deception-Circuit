"""Tiny SIGKILL check of proposed observation block; no runtime/fixture imports."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
sys.dont_write_bytecode = True
import tempfile
import time

HERE = Path(__file__).resolve().parent
FAILED = HERE.parent / 'task23-red-r1'
source_path = HERE / 'run_packet.py.proposed'
source = source_path.read_text(); tree = ast.parse(source)
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
outer = next(n for n in main.body if isinstance(n, ast.Try))
loop = next(n for n in outer.body if isinstance(n, ast.For))
body = loop.body
start = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'row' for t in n.targets))
end = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'cases' for t in n.targets))
spec = importlib.util.spec_from_file_location('failed_packet_helpers', FAILED / 'run_packet.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
started = time.perf_counter()
with tempfile.TemporaryDirectory(prefix='a3-observer-proposal209-', dir='/tmp') as temporary:
    output = Path(temporary); manifest = {'results': {}}
    def save(): (output / 'run_manifest.json').write_text(json.dumps(manifest))
    namespace = dict(vars(module), sub=output, env=dict(os.environ), name='base', python=sys.executable,
        argv=[sys.executable, '-c', 'import os,signal;os.kill(os.getpid(),signal.SIGKILL)'], manifest=manifest, save=save)
    try:
        exec(compile(ast.Module(body=body[start:end], type_ignores=[]), str(source_path), 'exec'), namespace)
    except RuntimeError as error:
        saved = json.loads((output / 'run_manifest.json').read_text())['results']['base']
        assert saved['pytest_exit_code'] == -signal.SIGKILL
        assert saved['termination_signal'] == signal.SIGKILL
        assert saved['status'] == 'MISSING_JUNIT' and saved['junit_present'] is False
        assert saved['normal_completion'] is False
        assert 'without JUnit; no RED evidence' in str(error)
        evidence = dict(status='PROPOSED_OBSERVER_KILL_CASE_PASS', raw_child_returncode=saved['pytest_exit_code'],
            termination_signal=saved['termination_signal'], saved_status=saved['status'], RED_accepted=False,
            missing_JUnit_explicit=True, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            active_source_and_result_bytes_changed=False, transient_cache_side_effect='bytecode-side-effect.json', model_loaded=False, wall_seconds=time.perf_counter()-started)
    else: raise AssertionError('missing JUnit must fail explicitly')
(HERE / 'observer-proposal-result.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
print(json.dumps(evidence, sort_keys=True))
