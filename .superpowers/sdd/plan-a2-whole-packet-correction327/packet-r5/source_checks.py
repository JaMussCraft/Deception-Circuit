#!/usr/bin/env python3
"""Brief stdlib/source-only checks; no native imports, pytest or integration."""
import ast
import copy
import hashlib
import json
import math
import re
from pathlib import Path
from types import SimpleNamespace

P=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
read=lambda path:json.loads(Path(path).read_text())

def function(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def compile_nodes(nodes,namespace):
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'SOURCE_ONLY_AST','exec'),namespace)
def require(ok,msg):
    if not ok:raise ValueError(msg)

def main():
    meta=read(P/'dependencies.json');frozen=Path(meta['frozen_task3_packet'])
    common=frozen/'closure/sdd/plan-a2-full-score-operational186/candidate/gpu/common.py'
    tree=ast.parse(common.read_text());test_tree=ast.parse((P/'candidate/tests/test_full_score_integration.py').read_text())
    constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('W','SOURCE')}
    original_MAIN=constants['W']+'/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'
    temporary_MAIN=str(P/'evidence/SOURCE-ONLY-MAIN-NOT-CREATED')
    g=dict(main_root=temporary_MAIN,actual_job_id='456',reservation_id='new',resources={'CPUs':2},
        resource_proof='resource',capacity_proof='capacity',operational_admission='admission')
    for key in ('packet_manifest_sha256','groups_file_sha256','bank_file_sha256','bank_manifest_sha256',
        'input_manifest_sha256','model_cache_proof_sha256','resource_proof_sha256','capacity_proof_sha256'):g[key]='a'*64
    # Same first-two-original-assertion probe used by independent296.
    release_fn=function(tree,'validate_release')
    prefix=ast.FunctionDef(name='release_prefix',args=release_fn.args,body=release_fn.body[:2],decorator_list=[],returns=None,type_comment=None)
    if 'type_params' in ast.FunctionDef._fields:prefix.type_params=[]
    ns=dict(C=g,MAIN=original_MAIN,SOURCE=constants['SOURCE'],CONFIG='synthetic-config',sha=lambda p:'a'*64,require=require)
    compile_nodes([prefix],ns)
    release=dict(phase='full_score',full_scoring_admitted=True,actual_job_id='456',reservation_id='new',
        source_commit=constants['SOURCE'],main_root=temporary_MAIN,bound_config_sha256='a'*64,resources=g['resources'])
    try:ns['release_prefix'](release)
    except ValueError as error:assert str(error)=='release actual binding'
    else:raise AssertionError('original historical MAIN must reject temporary namespace')
    route_ns=dict(SOURCE=Path(meta['original_runtime']),META=meta)
    compile_nodes([function(test_tree,'route_main')],route_ns)
    guard=SimpleNamespace(S=str(meta['original_runtime']),SOURCE=meta['original_source_commit'],MAIN=original_MAIN,C=g,
        full_score_command=lambda config:['bash',str(Path(meta['original_runtime'])/'scripts/jobs/specificity_a2.sh'),'--work-dir',config['main_root']])
    route_ns['route_main'](guard,g,SimpleNamespace(setattr=setattr))
    ns['MAIN']=guard.MAIN;ns['release_prefix'](release)
    assert guard.S==meta['original_runtime'] and guard.MAIN==temporary_MAIN
    resource=dict(complete=True,independently_accepted=True,proof181_accepted=True,resources=g['resources'],
        reviewed_components={key:True for key in ('host_memory','gpu_memory','storage','work_ratio','cost')},synthetic_fixture=True)
    capacity=dict(complete=True,independently_accepted=True,resources=g['resources'],actual_job_id='456',synthetic_fixture=True)
    admission=dict(accepted=True,complete=True,phase='full_score',source_commit=constants['SOURCE'],actual_job_id='456',
        reservation_id='new',main_root=temporary_MAIN,resources=g['resources'],reader_safe_cutover_complete=True,
        native_successor_complete=True,synthetic_fixture=True)
    admission.update({k:v for k,v in g.items() if k.endswith('_sha256')})
    docs=dict(resource=resource,capacity=capacity,admission=admission)
    ns.update(read=lambda key:docs[key])
    compile_nodes([function(tree,'reviewed_admission')],ns)
    assert ns['reviewed_admission']()==resource
    rejections={}
    for label,doc,key,value,expected in [
        ('resource-review','resource','independently_accepted',False,'genuine independently reviewed resource'),
        ('capacity-job','capacity','actual_job_id','wrong','actual reviewed placement/capacity'),
        ('admission-scope','admission','phase','prefix4','new root operational admission'),
        ('reader-cutover','admission','native_successor_complete',False,'completed reader-safe native mapping transition')]:
        prior=copy.deepcopy(docs[doc]);docs[doc][key]=value
        try:ns['reviewed_admission']()
        except ValueError as error:assert expected in str(error);rejections[label]=str(error)
        else:raise AssertionError('actual admission body accepted damaged fixture')
        docs[doc]=prior
    counts={}
    for node in test_tree.body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
            count=1
            for decorator in node.decorator_list:
                if isinstance(decorator,ast.Call) and isinstance(decorator.func,ast.Attribute) and decorator.func.attr=='parametrize':count*=len(ast.literal_eval(decorator.args[1]))
            counts[node.name]=count
    old=ast.parse((Path(meta['predecessor_packet'])/'candidate/tests/test_full_score_integration.py').read_text())
    old_tests=[n for n in old.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    for old_test in old_tests:
        new_test=function(test_tree,old_test.name)
        assert [ast.dump(d) for d in old_test.decorator_list]==[ast.dump(d) for d in new_test.decorator_list]
        old_assertions=[ast.dump(n) for n in ast.walk(old_test) if isinstance(n,ast.Assert)]
        new_assertions=[ast.dump(n) for n in ast.walk(new_test) if isinstance(n,ast.Assert)]
        assert all(n in new_assertions for n in old_assertions),old_test.name
    assert sum(counts.values())==33
    lineage_source=ast.unparse(function(test_tree,'native_lineage'))
    assert "ledger_sha256=m.sha(normalized['original_snapshot_path'])" in lineage_source
    assert 'm.authenticate_cutover(producer.b, g, normalized)' in lineage_source
    joined_source=ast.unparse(function(test_tree,'joined'))
    assert joined_source.index('native_lineage(')<joined_source.index('full_native_score(')
    full_source=ast.unparse(function(test_tree,'full_native_score'))
    assert 'boundary.validate_domain_identity(' in full_source
    assert 'support_sha256' in full_source
    assert 'geometry-from-prepared.json' in full_source
    group_source=ast.unparse(function(test_tree,'full_group_binding'))
    assert 'p.model_geometry_receipt(metadata)' in group_source
    assert 'geometry-before-context.json' in group_source
    support=read(meta['accepted_support_evidence']['path'])
    assert sha(meta['accepted_support_evidence']['path'])==meta['accepted_support_evidence']['sha256']
    assert support['verified']['support_reason_mask_sha256']==meta['accepted_native_support_reason_mask_sha256']
    observer_tree=ast.parse((P/'run_cpu.py').read_text())
    env_node=next(node for node in observer_tree.body if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='A2_HF_ENV')
    env_scope={}
    compile_nodes([env_node],env_scope)
    required_HF=dict(HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    assert env_scope['A2_HF_ENV']==required_HF
    # New construction expressions run in memory against preserved diagnosis
    # inputs; this is not native normalization, a new attestation or a proof.
    diagnostic=read(meta['diagnosis318']['path'])
    assert sha(meta['diagnosis318']['path'])==meta['diagnosis318']['sha256']
    pair=diagnostic['lineage']['pairs'][0]
    original_attestation=read(pair['cutover_path']);attestation=copy.deepcopy(original_attestation)
    normalized=dict(active_mapping_reference=attestation['active_mapping_reference'],
        mapping_lineage_references=attestation['mapping_lineage_references'],original_snapshot_path=pair['active_snapshot'])
    update=next(node for node in function(test_tree,'native_lineage').body if isinstance(node,ast.Expr)
        and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
        and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='attestation')
    scope=dict(attestation=attestation,normalized=normalized,g={'mapping_origin_sha256':attestation['mapping_origin_sha256']},
        m=SimpleNamespace(sha=sha))
    compile_nodes([update],scope)
    assert attestation['ledger_sha256']==sha(normalized['original_snapshot_path'])
    assert attestation['ledger_sha256']!=original_attestation['ledger_sha256']
    helper_tree=ast.parse((frozen/'closure/sdd/plan-a2-full-score-operational186/candidate/root/helper.py').read_text())
    predicate=next(node for node in function(helper_tree,'authenticate_cutover').body if isinstance(node,ast.If)).body[0]
    predicate_scope=dict(value=attestation,normalized=normalized,need=require,sha=sha)
    compile_nodes([predicate],predicate_scope)
    assert read(pair['cutover_path'])==original_attestation
    geom=diagnostic['geometry']['frozen'];revision=geom['source']['model_revision']
    repo='models--'+geom['source']['model'].replace('/','--')
    expected_config=Path(required_HF['HF_HUB_CACHE'])/repo/'snapshots'/revision/'config.json'
    assert str(expected_config.resolve())==geom['source']['path'] and sha(expected_config)==geom['source']['file_sha256']
    # Prove that the new pre-seal field assignment flows through the unchanged
    # normal COMPLETE constructor. No disk proof is written or re-signed.
    cpu_root=Path(pair['cutover_path']).parent/'CPU'
    source_result=read(cpu_root/'guard-result.json');source_result_hash=sha(cpu_root/'guard-result.json')
    result=copy.deepcopy(source_result)
    digest=meta['accepted_native_support_reason_mask_sha256']
    assign=next(node for node in function(test_tree,'rebind').body if isinstance(node,ast.If)
        and any(isinstance(child,ast.Assign) and isinstance(child.targets[0],ast.Subscript)
            and isinstance(child.targets[0].slice,ast.Constant) and child.targets[0].slice.value=='support_reason_mask_sha256'
            for child in node.body))
    compile_nodes([assign],dict(result=result,support_sha256=digest,META=meta))
    cpu_tree=ast.parse((frozen/'closure/sdd/plan-a2-full-score-operational186/candidate/cpu/supervisor.py').read_text())
    constructor_scope=dict(require=require,math=math,re=re,copy=copy,SOURCE=meta['original_source_commit'],
        CATALOGUES=tuple(result['source_before']['catalogues']))
    compile_nodes([function(cpu_tree,'number'),function(cpu_tree,'validate_child_completion')],constructor_scope)
    config=read(cpu_root.parent/'CPU-bound.json');request=read(cpu_root.parent/'request.json');child=read(cpu_root/'child-execution.json')
    complete=constructor_scope['validate_child_completion'](config,request,child,result,now=1201.)
    assert complete['support_reason_mask_sha256']==digest
    assert sha(cpu_root/'guard-result.json')==source_result_hash and read(cpu_root/'guard-result.json')==source_result
    observer=ast.unparse(function(observer_tree,'main'))
    assert observer.index('env.update(A2_HF_ENV)')<observer.index('subprocess.check_output')

    native_source=ast.unparse(function(test_tree,'native_modules'))
    bind_source=ast.unparse(function(test_tree,'rebind'))
    assert 'monkeypatch.chdir(str(SOURCE))' in native_source
    assert native_source.index('t1.save(observation_path, namespace)')<native_source.index("assert str(hf.HF_HUB_CACHE)")
    assert native_source.index('t1.save(observation_path, namespace)')<native_source.index("import_module('component_analysis.a2_pipeline')")
    assert "write_bytes(marker_bytes)" in bind_source
    assert "('WAITING.json', w)" not in bind_source
    assert "result['support_reason_mask_sha256'] = support_sha256" in bind_source
    assert bind_source.index("result['support_reason_mask_sha256'] = support_sha256")<bind_source.index('validate_child_completion(')
    restore=ast.unparse(function(test_tree,'restore_root_gates'))
    consumer=ast.unparse(function(test_tree,'consumer'))
    assert 'real_verify(b, g, c)' in restore and 'return original()' in restore
    assert 'return real_reviewed_admission()' in consumer
    assert "setattr(guard, 'packet'" not in consumer and "setattr(guard, 'input_closure'" not in consumer
    for path in (P/'run_cpu.py',P/'source_checks.py'):ast.parse(path.read_text())
    for path in [P/'dependencies.json',P/'packet-pins.json']+list((P/'candidate').rglob('*.json')):read(path)
    manifest=read(P/'candidate/manifest.json')
    assert len(manifest['unchanged_component_files'])==17
    for path,digest in manifest['unchanged_component_files'].items():assert sha(path)==digest
    for path,digest in read(P/'packet-pins.json').items():assert sha(P/path)==digest
    assert all(value is None for value in read(P/'candidate/root-release-contract.json')['actual_bindings'].values())
    result=dict(kind='STDLIB_AST_SOURCE_ONLY_NO_NATIVE_TESTS',case_counts=counts,total_cases=33,
        original33_test_decorators_and_assertions_preserved=True,unchanged_components=17,
        consolidated321=dict(active_snapshot_constructor_and_early_authentication=True,HF_before_native_imports=True,
            actual_geometry_HF_evidence_capture=True,original_domain_validator_used=True,support_bound_before_COMPLETE=True,
            accepted_support_sha256=meta['accepted_native_support_reason_mask_sha256'],
            active_anchor_expression_original_predicate_replay=True,flat_config_raw_path_SHA_match=True,
            support_assignment_original_constructor_copy_flow=True,pure_probe_inputs_unchanged=True),
        B1_actual_admission_body_source_rejections=rejections,B1_root_and_consumer_spies_delegate=True,
        B2_original_MAIN_prefix_rejects=True,B2_routed_MAIN_prefix_accepts=True,B2_original_runtime_preserved=True,
        packet_pins_sha256=sha(P/'packet-pins.json'),integration_test_sha256=sha(P/'candidate/tests/test_full_score_integration.py'),
        native_imports=False,pytest_runs=0,actual_binding_nulls=True)
    (P/'evidence/source-check.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
