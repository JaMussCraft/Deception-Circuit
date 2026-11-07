#!/usr/bin/env python3
"""Bounded stdlib/extracted-source diagnosis of actual Task4 fixture failures."""
import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

P=Path(__file__).resolve().parent;S=P.parent
R=S/'plan-a2-task4-deployment298/run-01'
C=S/'plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate'
SOURCE=Path(json.loads((S/'plan-a2-whole-packet289-r2/dependencies.json').read_text())['original_runtime'])
sha=lambda data:hashlib.sha256(data).hexdigest()

def main():
    tree=ast.parse((C/'root/helper.py').read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='capture_cpu')
    guard=next(n for n in function.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and any(isinstance(a,ast.Constant) and a.value=='CPU immutable WAITING copy' for a in n.value.args))
    observations=[]
    def need(ok,message):
        if not ok:raise ValueError(message)
    dirs=['test_entry_failure_has_zero_sc'+str(i) for i in range(11)]+['test_consumed_partial_is_prese0','test_actual_consumer_rejects_w0']
    for environment in ('base39','mgnp'):
        cases=list(ET.parse(str(R/(environment+'.xml'))).getroot().iter('testcase'))
        failures={c.get('name'):c.find('failure').text for c in cases if c.find('failure') is not None}
        assert len(failures)==14
        assert sum('CPU immutable WAITING copy' in (value or '') for value in failures.values())==13
        assert 'FileNotFoundError' in failures['test_whole_chain_normal_native_full_publication']
        for directory in dirs:
            root=R/(environment+'-tmp')/directory
            request_path=root/'request.json';r=json.loads(request_path.read_text())
            marker=Path(r['GPU_WAITING_marker_path']);cpu=root/'CPU';copy_path=cpu/'WAITING.json'
            actual=marker.read_bytes();copied=copy_path.read_bytes()
            assert sha(actual)==r['GPU_WAITING_marker_sha256'] and sha(copied)!=r['GPU_WAITING_marker_sha256']
            assert json.loads(actual)==json.loads(copied)
            ns=dict(need=need,sha_bytes=sha,root=cpu,r=r,files={str(copy_path):copied})
            compiled=compile(ast.fix_missing_locations(ast.Module(body=[guard],type_ignores=[])),'ORIGINAL_RAW_GUARD_SOURCE','exec')
            try:exec(compiled,ns)
            except ValueError as error:assert str(error)=='CPU immutable WAITING copy'
            else:raise AssertionError('actual mismatch must reject')
            ns['files'][str(copy_path)]=actual;exec(compiled,ns)
            tampered=actual+b' ';assert json.loads(tampered)==json.loads(actual)
            ns['files'][str(copy_path)]=tampered
            try:exec(compiled,ns)
            except ValueError as error:assert str(error)=='CPU immutable WAITING copy'
            else:raise AssertionError('whitespace tamper must reject')
            # Both unchanged production writers use indent2/no sort + newline.
            production_roundtrip=(json.dumps(json.loads(actual),indent=2,allow_nan=False)+'\n').encode()
            assert production_roundtrip==actual
            observations.append(dict(environment=environment,fixture=directory,marker=str(marker),CPU_copy=str(copy_path),
                request=str(request_path),request_sha256=sha(request_path.read_bytes()),expected_sha256=r['GPU_WAITING_marker_sha256'],
                actual_marker_sha256=sha(actual),CPU_copy_sha256=sha(copied),actual_bytes=len(actual),copy_bytes=len(copied),
                parsed_equal=True,unchanged_production_serialization_roundtrip_exact=True,
                original_raw_guard_rejects_old_copy=True,original_raw_guard_accepts_exact_bytes=True,
                original_raw_guard_rejects_equal_JSON_whitespace_tamper=True))
    relative=Path('data/datasets/far_v2/dataset_config.json')
    cwd=dict(failed_observer_cwd=str(R),relative_source_reference=str(relative),
        source_runtime=str(SOURCE),absent_from_observer_output=not (R/relative).exists(),present_from_original_runtime=(SOURCE/relative).is_file(),
        original_native_cwd_contract=dict(CPU=str(C/'cpu/validate-phase.py')+':320',host=str(C/'gpu/host-launch.py')+':72'),
        original_native_call_not_changed=True)
    assert cwd['absent_from_observer_output'] and cwd['present_from_original_runtime']
    result=dict(kind='ACTUAL_FAILURE_BYTES_PLUS_EXTRACTED_GUARD_ONLY',classification='FIXTURE_ONLY_TWO_DISTINCT_CAUSES',
        actual_job='23636443',cluster='delta',failed_cases_per_environment=14,WAITING_copy_failures_per_environment=13,
        native_cwd_failures_per_environment=1,production_changed=False,observations=observations,cwd=cwd,
        cause='rebind saves GPU marker with t1.save(sort_keys=True), then serializes the earlier insertion-ordered w with helper.encoded(no sort) into CPU WAITING. JSON semantics agree but authenticated raw bytes differ. Full native fixture calls original relative-path readers from observer output rather than original runtime S.',
        native_imports=False,integration_tests_run=False,actual_failed_files_modified=False)
    (P/'evidence/diagnosis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(classification=result['classification'],actual_byte_pairs=len(observations),WAITING_failures_per_environment=13,cwd_failures_per_environment=1,production_changed=False)))
if __name__=='__main__':main()
