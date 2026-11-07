"""Tiny stdlib-only execution of the failed runner's exact observation block."""
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
PACKET = HERE.parent / 'task23-red-r1'
source_path = PACKET / 'run_packet.py'
source = source_path.read_text(); tree = ast.parse(source)
main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
outer = next(node for node in main.body if isinstance(node, ast.Try))
loop = next(node for node in outer.body if isinstance(node, ast.For))
body = loop.body
start = next(i for i, node in enumerate(body) if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'result' for t in node.targets))
end = next(i for i, node in enumerate(body) if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'cases' for t in node.targets)) + 1
fragment = ast.Module(body=body[start:end], type_ignores=[])
spec = importlib.util.spec_from_file_location('failed_packet_observer_source', source_path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
started = time.perf_counter()
with tempfile.TemporaryDirectory(prefix='a3-observer209-', dir='/tmp') as directory:
    namespace = dict(vars(module), sub=Path(directory), env=dict(os.environ),
        argv=[sys.executable, '-c', 'import os,signal;os.kill(os.getpid(),signal.SIGKILL)'])
    try:
        exec(compile(fragment, str(source_path), 'exec'), namespace)
    except FileNotFoundError as error:
        result = namespace['result']
        assert result.returncode == -signal.SIGKILL
        assert not (Path(directory) / 'junit.xml').exists()
        evidence = dict(status='EXACT_OBSERVER_FAILURE_REPRODUCED',
            child_returncode=result.returncode, child_signal=-result.returncode,
            observed_exception=type(error).__name__, junit_present=False,
            process_row_not_reached='row' not in namespace,
            source_path=str(source_path), source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            source_lines=[body[start].lineno, body[end-1].end_lineno],
            model_loaded=False, production_or_fixture_run=False,
            wall_seconds=time.perf_counter()-started)
    else:
        raise AssertionError('expected the exact missing-JUnit observer failure')
(HERE / 'observer-repro-result.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
print(json.dumps(evidence, sort_keys=True))
