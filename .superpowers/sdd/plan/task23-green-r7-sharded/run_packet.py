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
from closure_preflight import check_context

PACKET = Path(__file__).resolve().parent
CANDIDATE = PACKET.parents[1] / 'plan-a3/direction-preallocation-candidate282'
ORACLE = PACKET.parents[1] / 'plan-a3/direction-metadata-optionA-candidate'
TEST = 'test_a3_prepared_pilot_target.py'
ENVS = {'base': '/sw/external/python/anaconda3/bin/python3.9', 'mgnp': '/u/swong2/.conda/envs/mgnp/bin/python'}
PINS = dict(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
    VECLIB_MAXIMUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1',
    DC_RUN_MANIFEST_GIT='0', CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pins():
    manifest = json.loads((PACKET / 'source-pins.json').read_text())
    for group, root in [('candidate', CANDIDATE), ('oracle', ORACLE), ('packet', PACKET), ('baseline', PACKET / 'baseline-source')]:
        for relative, digest in manifest[group].items():
            assert sha(root / relative) == digest, 'source pin mismatch: ' + str(root / relative)
    check_context(PACKET / 'baseline-source', manifest['baseline'])
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
    return [python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'selector','--import-mode=importlib',
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


def source_identity():
    return dict(revision='r7-sharded', runtime_sha256=sha(CANDIDATE/'component_analysis/a3_direction_runtime.py'),
        fixture_sha256=sha(PACKET/'suite'/TEST), partition_sha256=sha(PACKET/'partition.json'),
        source_pins_sha256=sha(PACKET/'source-pins.json'))


def main():
    from aggregate import validate_partition, verify_events, verify_junit, verify_controls
    parser=argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--oracle-proof', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--environment',choices=['base','mgnp'],required=False)
    parser.add_argument('--shard',type=int,choices=[0,1],required=False)
    parser.add_argument('--stage',choices=['baseline','oracle','suite'])
    args=parser.parse_args(); pins=check_pins()
    partition=json.loads((PACKET/'partition.json').read_text());validate_partition(partition)
    if args.dry_run:
        print(json.dumps(dict(packet=str(PACKET),source=source_identity(),expected_collection=223,
            shard_counts=[112,111],environment=PINS,baseline_context=check_context(PACKET/'baseline-source',pins['baseline']),
            commands={name:shlex.join(command(py,PACKET/('example-'+name))) for name,py in ENVS.items()},
            stage_caps=dict(baseline=610,oracle=90,suite=3600),allocation_seconds=4800,
            actual_job=None,actual_config=None,scheduler_calls=0,imports_executed=False,full_suite_accepted=False,
            execution_authorized=False),indent=2));return
    assert args.output is not None
    if args.oracle_proof:
        print(json.dumps(oracle_proof(args.output),sort_keys=True));return
    assert args.environment is not None and args.shard is not None and args.stage is not None
    assert os.environ.get('A3_HOST_BOUND')=='1', 'native execution requires reviewed actual host binding'
    assert sys.executable==ENVS[args.environment], 'wrong exact interpreter'
    pytest_module=importlib.import_module('pytest')
    interpreter_provenance=dict(python_version=sys.version,pytest_version=pytest_module.__version__,pytest_origin=pytest_module.__file__)
    python=ENVS[args.environment]; output=args.output.resolve(); manifest_path=output/'run_manifest.json'
    nodes=partition['shards'][str(args.shard)]['execution_order']
    if args.stage=='baseline':
        output.mkdir(parents=True,exist_ok=False)
        manifest=dict(status='STARTED',commit='538109e809285b6ddc45d42df8786270a65f7b12',source_commit_role='accepted worktree baseline; isolated revisions bound by exact source pins',environment=args.environment,shard=args.shard,python=python,executable=sys.executable,
            job_id=os.environ['SLURM_JOB_ID'],cluster=os.environ['SLURM_CLUSTER_NAME'],output=str(output),
            source_before=source_identity(),source_after=None,source_pins=pins,interpreter_provenance=interpreter_provenance,collected=[],executed=[],
            normal_completion=False,full_suite_accepted=False,model_loaded=False,execution_authorized=False,exit_code=None,
            artifacts={})
    else:
        manifest=json.loads(manifest_path.read_text())
        assert manifest['interpreter_provenance']==interpreter_provenance
        assert manifest['source_before']==source_identity() and manifest['environment']==args.environment and manifest['shard']==args.shard
        assert manifest['job_id']==os.environ['SLURM_JOB_ID'] and manifest['output']==str(output)
    def save():
        temp=output/'manifest.new'
        with temp.open('w') as stream:
            json.dump(manifest,stream,indent=2,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(temp,manifest_path)
    def ref(path):return dict(path=str(path),sha256=sha(path))
    save()
    env=dict(os.environ,**PINS);env['PYTHONPATH']=str(PACKET)+os.pathsep+str(CANDIDATE)
    env.update(A3_T1_CANDIDATE=str(CANDIDATE),A3_T1_OUTPUT=str(output),
        A3_SHARD_PARTITION=str(PACKET/'partition.json'),A3_SHARD=str(args.shard),A3_SHARD_EVENTS=str(output/'events.jsonl'))
    # Host is the sole process-group supervisor. Every stage descendant remains in
    # its inherited host-owned group, including baseline's inner pytest.
    try:
        if args.stage=='baseline':
            argv=[python,str(PACKET/'baseline_red.py'),'--python',python,'--output',str(output/'baseline-red')]
        elif args.stage=='oracle':
            assert 'baseline' in manifest['artifacts']
            argv=[python,str(PACKET/'run_packet.py'),'--oracle-proof','--output',str(output)]
        else:
            assert {'baseline','oracle'}<=set(manifest['artifacts'])
            argv=command(python,output)
        manifest.update(status=args.stage.upper()+'_STARTED');save()
        started=time.time()
        with (output/(args.stage+'.stdout')).open('xb') as stdout,(output/(args.stage+'.stderr')).open('xb') as stderr:
            result=subprocess.run(argv,env=env,cwd=str(PACKET),stdout=stdout,stderr=stderr)
        finished=time.time()
        manifest.update(status=args.stage.upper()+'_EXITED',raw_stage_exit_code=result.returncode);save()
        # Raw child status is durable before any source, XML or control parsing.
        assert result.returncode==0
        check_pins();assert manifest['source_before']==source_identity()
        if args.stage=='baseline':
            manifest['artifacts']['baseline']=ref(output/'baseline-red/run_manifest.json')
        elif args.stage=='oracle':
            oracle=json.loads((output/'oracle.stdout').read_text())
            (output/'oracle.json').write_text(json.dumps(oracle)+'\n')
            manifest['artifacts']['oracle']=ref(output/'oracle.json')
        else:
            collected=json.loads((output/'collected-nodeids.json').read_text())['nodes']
            events=[json.loads(line) for line in (output/'events.jsonl').read_text().splitlines()]
            assert all(events[0][key]==value for key,value in interpreter_provenance.items())
            verify_events(events,nodes,partition['full_collection'],python)
            verify_junit((output/'junit.xml').read_text(),nodes)
            for name,path in [('events',output/'events.jsonl'),('junit',output/'junit.xml'),('preflight',output/'fixture-preflight/run_manifest.json'),('candidate_origins',output/'candidate-origins.json')]:
                manifest['artifacts'][name]=ref(path)
            verify_controls(manifest['artifacts'],output)
            assert collected==partition['full_collection']
            manifest.update(status='SHARD_GREEN',normal_completion=True,exit_code=0,source_after=source_identity(),
                child_exit_code=result.returncode,child_normal_completion=True,child_started=started,child_finished=finished,
                child_deadline=float(os.environ['A3_STAGE_DEADLINE']),collected=collected,executed=nodes)
            assert finished<manifest['child_deadline']
        save()
    except BaseException as error:
        manifest.update(status='FAILED',normal_completion=False,exit_code=1,error=repr(error),source_after=source_identity());save();raise


if __name__=='__main__':main()
