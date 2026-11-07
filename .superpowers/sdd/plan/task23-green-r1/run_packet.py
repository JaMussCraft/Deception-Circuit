"""Root-run frozen dual-env CPU evidence. Dry-run is stdlib-only; no scheduler calls."""
import argparse
import ast
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import shlex
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PACKET = Path(__file__).resolve().parent
CANDIDATE = PACKET.parents[1] / 'plan-a3/direction-preallocation-candidate183'
ORACLE = PACKET.parents[1] / 'plan-a3/direction-metadata-optionA-candidate'
TEST = 'test_a3_prepared_pilot_target.py'
ENVS = {'base': '/sw/external/python/anaconda3/bin/python3.9', 'mgnp': '/u/swong2/.conda/envs/mgnp/bin/python'}
PINS = dict(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
    VECLIB_MAXIMUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1',
    DC_RUN_MANIFEST_GIT='0', CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pins():
    manifest = json.loads((PACKET / 'source-pins.json').read_text())
    for group, root in [('candidate', CANDIDATE), ('oracle', ORACLE), ('packet', PACKET)]:
        for relative, digest in manifest[group].items():
            assert sha(root / relative) == digest, 'source pin mismatch: ' + str(root / relative)
    return manifest


def expected_new_count():
    tree = ast.parse((PACKET / 'suite' / TEST).read_text()); total = 0
    for item in tree.body:
        if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
            n = 1
            for dec in item.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == 'parametrize':
                    n *= len(dec.args[1].elts)
            total += n
    return total


def expected_functions():
    scope=json.loads((PACKET/'verification-scope.json').read_text())
    counts=dict(scope['existing_regression_case_counts'])
    tree=ast.parse((PACKET/'suite'/TEST).read_text())
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
            count=1
            for dec in node.decorator_list:
                if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr=='parametrize':
                    count*=len(dec.args[1].elts)
            counts[node.name]=count
    return counts


def expected_count(): return sum(expected_functions().values())


def command(python, output):
    suite = PACKET / 'suite'
    nodes=json.loads((PACKET/'verification-scope.json').read_text())['existing_regression_nodes']
    return [python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider','--import-mode=importlib',
        '--confcutdir=' + str(suite),'--rootdir=' + str(suite), '--basetemp=' + str(output / 'tmp'),
        '--junitxml=' + str(output / 'junit.xml'), str(suite / TEST)] + [str(suite / Path(node.split('::')[0]).name)+'::'+node.split('::')[1] for node in nodes]


def origin_assert(root):
    sys.path.insert(0, str(root))
    names = ['component_analysis.a3_direction_runtime', 'component_analysis.a3_direction_artifacts',
        'component_analysis.a3_direction_workload', 'dataset.user_inversion_pipeline',
        'tests.a3_direction_native_scenario', 'tests.test_a3_direction_runtime']
    origins = {}
    for name in names:
        mod = importlib.import_module(name); path = Path(mod.__file__).resolve()
        assert path.is_relative_to(root.resolve()), (name, str(path), str(root))
        origins[name] = str(path)
    return origins


def oracle_proof(output):
    before = check_pins(); origins = origin_assert(ORACLE)
    r = importlib.import_module('component_analysis.a3_direction_runtime')
    value = {'a': -0.0, 'text': 'λ雪', 'tuple': (True, None, 7)}
    path = output / 'ordinary'; r.publish_object(path, value)
    expected = b'{"a": -0.0, "text": "\\u03bb\\u96ea", "tuple": [true, null, 7]}\n'
    assert (path / 'payload.json').read_bytes() == expected
    assert r.read_object(path) == {'a': -0.0, 'text': 'λ雪', 'tuple': [True, None, 7]}
    assert check_pins() == before
    return dict(origins=origins, payload_bytes=len(expected), expected_payload_bytes=len(expected),
        payload_sha256=hashlib.sha256(expected).hexdigest(), complete=True, exit_code=0,
        model_loaded=False, execution_authorized=False)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--mode', choices=['GREEN'], default='GREEN')
    parser.add_argument('--output', type=Path); parser.add_argument('--oracle-proof', action='store_true')
    parser.add_argument('--environment',choices=['base','mgnp','both'],default='both')
    args = parser.parse_args(); pins = check_pins()
    if args.dry_run:
        print(json.dumps(dict(packet=str(PACKET), candidate=str(CANDIDATE), oracle=str(ORACLE),
            expected_test_count=expected_count(), environment=PINS,
            commands={name: shlex.join(command(py, PACKET / ('example-' + name))) for name, py in ENVS.items()},
            cpu_only=True, scheduler_calls=0, imports_executed=False), indent=2)); return
    assert args.output is not None
    if args.oracle_proof:
        print(json.dumps(oracle_proof(args.output), sort_keys=True)); return
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    start = time.time()
    manifest = dict(status='STARTED', mode=args.mode, commit='538109e809285b6ddc45d42df8786270a65f7b12',
        source_commit_role='accepted worktree baseline; isolated candidate changes identified by source pins',
        candidate=str(CANDIDATE), oracle=str(ORACLE), source_pins=pins,
        host=socket.gethostname(), platform=platform.platform(), job_id=os.environ.get('SLURM_JOB_ID'),
        cluster=os.environ.get('SLURM_CLUSTER_NAME'), started_unix=start, threadpins=PINS, results={},
        model_loaded=False, execution_authorized=False)
    def save(): (output / 'run_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    save()
    try:
        for name, python in ENVS.items():
            if args.environment not in ('both',name):continue
            env = dict(os.environ, **PINS); env['PYTHONPATH'] = str(CANDIDATE)
            env['A3_T1_CANDIDATE'] = str(CANDIDATE); env['A3_T1_OUTPUT'] = str(output / name)
            sub = output / name; sub.mkdir()
            oracle_cmd = [python, str(PACKET / 'run_packet.py'), '--oracle-proof', '--output', str(sub)]
            row = dict(python=python, status='ORACLE_STARTED', normal_completion=False,
                oracle_preflight=dict(argv=oracle_cmd, status='STARTED', exit_code=None))
            manifest['results'][name] = row; save()
            try:
                oracle = subprocess.run(oracle_cmd, env=env, cwd=str(PACKET), capture_output=True, text=True, timeout=90)
            except subprocess.TimeoutExpired as error:
                def oracle_decoded(value): return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
                (sub / 'oracle.stdout').write_text(oracle_decoded(error.stdout))
                (sub / 'oracle.stderr').write_text(oracle_decoded(error.stderr))
                row.update(status='ORACLE_TIMEOUT')
                row['oracle_preflight'].update(status='TIMEOUT', timed_out=True, timeout_seconds=90,
                    stdout_path=str(sub / 'oracle.stdout'), stderr_path=str(sub / 'oracle.stderr'))
                save(); raise RuntimeError('oracle preflight timed out; no RED evidence') from error
            (sub / 'oracle.stdout').write_text(oracle.stdout); (sub / 'oracle.stderr').write_text(oracle.stderr)
            row['oracle_preflight'].update(status='EXITED' if oracle.returncode == 0 else 'FAILED',
                exit_code=oracle.returncode, termination_signal=-oracle.returncode if oracle.returncode < 0 else None,
                stdout_path=str(sub / 'oracle.stdout'), stderr_path=str(sub / 'oracle.stderr'))
            row.update(status='ORACLE_EXITED' if oracle.returncode == 0 else 'ORACLE_FAILED'); save()
            assert oracle.returncode == 0, name + ' oracle preflight failed'
            argv = command(python, sub); check_pins()
            row.update(python=python, argv=argv, status='PYTEST_STARTED',
                pytest_exit_code=None, normal_completion=False)
            save()
            try:
                result = subprocess.run(argv, env=env, cwd=str(PACKET), capture_output=True, text=True, timeout=2100)
            except subprocess.TimeoutExpired as error:
                def decoded(value): return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
                (sub / 'pytest.stdout').write_text(decoded(error.stdout))
                (sub / 'pytest.stderr').write_text(decoded(error.stderr))
                row.update(status='PYTEST_TIMEOUT', timed_out=True, timeout_seconds=2100,
                    stdout_path=str(sub / 'pytest.stdout'), stderr_path=str(sub / 'pytest.stderr'))
                save(); raise RuntimeError('pytest timed out; no RED evidence') from error
            (sub / 'pytest.stdout').write_text(result.stdout); (sub / 'pytest.stderr').write_text(result.stderr)
            row.update(status='PYTEST_EXITED', pytest_exit_code=result.returncode,
                termination_signal=-result.returncode if result.returncode < 0 else None,
                stdout_path=str(sub / 'pytest.stdout'), stderr_path=str(sub / 'pytest.stderr'))
            save()  # Preserve raw child status BEFORE source checks or XML parsing.
            check_pins()
            junit = sub / 'junit.xml'
            if not junit.is_file():
                row.update(status='MISSING_JUNIT', junit_present=False,
                    fixture_preflight_manifest=str(sub / 'fixture-preflight/run_manifest.json'))
                save(); raise RuntimeError('pytest exited %s without JUnit; no RED evidence' % result.returncode)
            cases = ET.parse(sub / 'junit.xml').getroot().findall('.//testcase')
            failures = [case for case in cases if case.find('failure') is not None]
            errors = [case for case in cases if case.find('error') is not None]
            skipped = [case for case in cases if case.find('skipped') is not None]
            row.update(python=python, argv=argv, pytest_exit_code=result.returncode,
                observed_cases=len(cases), expected_cases=expected_count(), failures=len(failures),
                errors=len(errors), skipped=len(skipped), oracle=json.loads(oracle.stdout),
                source_pins_before_after_equal=True)
            manifest['results'][name] = row; save()
            assert len(cases) == expected_count() and not errors and not skipped, row
            groups = json.loads((PACKET / 'test-groups.json').read_text())
            row['tasks'] = {}
            for task in ('T1', 'T2', 'T3','existing'):
                chosen = [case for case in cases if groups['functions'][case.attrib['name'].split('[', 1)[0]] == task]
                row['tasks'][task] = dict(cases=len(chosen), expected=groups['expected_cases'][task],
                    failures=sum(case.find('failure') is not None for case in chosen))
                assert len(chosen) == groups['expected_cases'][task], row
            observed={}
            for case in cases:
                function=case.attrib['name'].split('[',1)[0]
                observed[function]=observed.get(function,0)+1
            assert observed==expected_functions(),dict(observed=observed,expected=expected_functions())
            row['per_function_case_counts']=observed
            row['collected_nodes_reference']=str(sub/'collected-nodeids.json')
            save()
            if args.mode == 'RED':
                assert result.returncode == 1, row
                assert row['tasks']['T1']['failures'] == 0, row
                for task in ('T2', 'T3'):
                    assert row['tasks'][task]['failures'] == row['tasks'][task]['cases'], row
                for case in failures:
                    failure = case.find('failure'); text = failure.get('message', '')
                    assert 'AttributeError' in text and any(name in text for name in (
                        'prepare_pilot_target', 'load_prepared_pilot_target',
                        '_validate_prepared_receiver_resources', '_PreparedPilotTarget')), text
            else:
                assert result.returncode == 0 and not failures, row
            row.update(status=args.mode + '_EXPECTED', normal_completion=True); save()
        manifest.update(status=args.mode + '_EXPECTED', normal_completion=True, exit_code=0)
    except BaseException as error:
        manifest.update(status='FAILED', normal_completion=False, error=repr(error), exit_code=1)
        raise
    finally:
        manifest.update(ended_unix=time.time(), wall_seconds=time.time() - start); save()


if __name__ == '__main__': main()
