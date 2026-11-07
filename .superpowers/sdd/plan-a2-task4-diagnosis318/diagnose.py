#!/usr/bin/env python3
"""Read-only artifact/source-boundary diagnosis; no native/application imports."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

P=Path(__file__).resolve().parent;S=P.parent
R=S/'plan-a2-task4-deployment315/run-01'
T=S/'plan-a2-whole-packet-correction312/packet-r3'
C=S/'plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate'
SOURCE=Path(json.loads((T/'dependencies.json').read_text())['original_runtime'])
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
read=lambda path:json.loads(Path(path).read_text())

def require(ok,message):
    if not ok:raise ValueError(message)

def ref(path):
    path=Path(path)
    return dict(path=str(path),files={p.name:dict(nbytes=p.stat().st_size,sha256=sha(p)) for p in path.iterdir() if p.is_file()})

def main():
    helper_tree=ast.parse((C/'root/helper.py').read_text())
    authenticate=next(n for n in helper_tree.body if isinstance(n,ast.FunctionDef) and n.name=='authenticate_cutover')
    condition=next(n for n in authenticate.body if isinstance(n,ast.If))
    expression=condition.body[0]
    compiled=compile(ast.fix_missing_locations(ast.Module(body=[expression],type_ignores=[])),'ORIGINAL_CUTOVER_PREDICATE','exec')
    pairs=[];case_groups={}
    fixture_dirs=['test_transfer_failure_cannot_c'+str(i) for i in range(6)]+[
        'test_entry_failure_has_zero_sc'+str(i) for i in range(11)]+['test_consumed_partial_is_prese0','test_actual_consumer_rejects_w0']
    for environment in ('base39','mgnp'):
        cases=list(ET.parse(str(R/(environment+'.xml'))).getroot().iter('testcase'))
        failures={c.get('name'):(c.find('failure').text or '') for c in cases if c.find('failure') is not None}
        groups=dict(stale_geometry=sum('stale A2 model_geometry' in value for value in failures.values()),
            stage_not_reached=sum("assert 'stage' in j.events" in value for value in failures.values()),
            direct_lineage=sum('unauthorized new transition or changed preserved native lineage' in value for value in failures.values()))
        assert len(cases)==33 and len(failures)==20 and groups==dict(stale_geometry=1,stage_not_reached=6,direct_lineage=13)
        case_groups[environment]=dict(tests=33,passed=13,failed=20,errors=sum(c.find('error') is not None for c in cases),
            skips=sum(c.find('skipped') is not None for c in cases),groups=groups)
        for directory in fixture_dirs:
            root=R/(environment+'-tmp')/directory
            cutover=read(root/'cutover.json');origin=read(root/'native/origin/payload.json')
            active=read(root/'native/successors/mapping-000001/payload.json')
            references=[ref(row['path']) for row in cutover['mapping_lineage_references']]
            normalized=dict(active_mapping_reference=ref(cutover['active_mapping_reference']['path']),
                mapping_lineage_references=references,original_snapshot_path=active['ledger_snapshot_path'])
            checks=dict(active_mapping_reference_matches=cutover['active_mapping_reference']==normalized['active_mapping_reference'],
                full_lineage_references_match=cutover['mapping_lineage_references']==references,
                seal_matches_origin_snapshot=cutover['ledger_sha256']==sha(origin['ledger_snapshot_path']),
                seal_matches_active_snapshot=cutover['ledger_sha256']==sha(active['ledger_snapshot_path']),
                canonical_equals_active_snapshot=(root/'native/ledger.json').read_bytes()==Path(active['ledger_snapshot_path']).read_bytes())
            assert checks==dict(active_mapping_reference_matches=True,full_lineage_references_match=True,
                seal_matches_origin_snapshot=True,seal_matches_active_snapshot=False,canonical_equals_active_snapshot=True)
            ns=dict(need=require,value=cutover,normalized=normalized,sha=sha)
            try:exec(compiled,ns)
            except ValueError as error:assert str(error)=='unauthorized new transition or changed preserved native lineage'
            else:raise AssertionError('wrong snapshot anchor must reject')
            # Hypothetical predicate-only value in memory, never an emitted
            # attestation, new binding or change to actual evidence.
            hypothetical=copy.deepcopy(cutover);hypothetical['ledger_sha256']=sha(active['ledger_snapshot_path'])
            ns['value']=hypothetical;exec(compiled,ns)
            request=read(root/'request.json');marker=Path(request['GPU_WAITING_marker_path'])
            q=read(root/'CPU/COMPLETE.json')
            pairs.append(dict(environment=environment,fixture=directory,
                cutover_path=str(root/'cutover.json'),seal_sha256=cutover['ledger_sha256'],
                origin_snapshot=origin['ledger_snapshot_path'],active_snapshot=active['ledger_snapshot_path'],
                active_snapshot_sha256=sha(active['ledger_snapshot_path']),checks=checks,
                original_predicate_rejects=True,hypothetical_correct_active_anchor_passes_predicate=True,
                WAITING_raw_copy_matches=(root/'CPU/WAITING.json').read_bytes()==marker.read_bytes(),
                WAITING_expected_hash_matches=sha(marker)==request['GPU_WAITING_marker_sha256']==q['waiting_sha256'],
                CPU_GPU_request_identity_matches=q['bound_gpu_config_sha256']==request['final_GPU_bound_config_sha256'],
                CPU_support_mask_sha256=q['support_reason_mask_sha256']))
    receipt=read(R/'base39-tmp/test_whole_chain_normal_native0/MAIN/groups.json')['payload']
    frozen=receipt['model_geometry'];model=receipt['model_identity']['model'];revision=receipt['model_identity']['model_revision']
    repository='models--'+model.replace('/','--')
    hub=Path(os.environ.get('HF_HUB_CACHE',os.environ.get('HUGGINGFACE_HUB_CACHE',str(Path(os.environ.get('HF_HOME',str(Path.home()/'.cache/huggingface')))/'hub'))))
    original_hub=Path('/work/nvme/beto/swong2')
    paths=dict(original=original_hub/repository/'snapshots'/revision/'config.json',
               observed_shell_default=hub/repository/'snapshots'/revision/'config.json')
    pipeline_tree=ast.parse((SOURCE/'component_analysis/a2_pipeline.py').read_text())
    geometry_fn=copy.deepcopy(next(n for n in pipeline_tree.body if isinstance(n,ast.FunctionDef) and n.name=='model_geometry_receipt'))
    class ResolverBoundary(ast.NodeTransformer):
        def visit_ImportFrom(self,node):return None if node.module=='huggingface_hub' else node
    geometry_fn=ResolverBoundary().visit(geometry_fn)
    design_tree=ast.parse((SOURCE/'component_analysis/ladder_design.py').read_text())
    hash_fn=copy.deepcopy(next(n for n in design_tree.body if isinstance(n,ast.FunctionDef) and n.name=='_hash'))
    ns=dict(Path=Path,require=require,hashlib=hashlib,json=json,
        a1=SimpleNamespace(common=SimpleNamespace(read_json=read,file_hash=sha)))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[hash_fn,geometry_fn],type_ignores=[])),'ORIGINAL_GEOMETRY_SOURCE_WITH_RESOLVER_BOUNDARY','exec'),ns)
    ns['hash_content']=ns['_hash'];geometries={};config_paths={}
    for label,path in paths.items():
        assert path.is_file()
        ns['hf_hub_download']=lambda *a,_path=path,**kw:str(_path)
        geometries[label]=ns['model_geometry_receipt'](dict(injected=False,model=model,model_revision=revision))
        config_paths[label]=dict(snapshot=str(path),resolved=str(path.resolve()),raw_sha256=sha(path))
    assert geometries['original']==frozen
    original=geometries['original'];default=geometries['observed_shell_default']
    assert original['geometry']==default['geometry']
    source_differences=[key for key in original['source'] if original['source'][key]!=default['source'][key]]
    assert source_differences==['path'] and default!=frozen
    catalogue_checks=[]
    for route,record in receipt['grader_binding']['routes'].items():
        data=read(route);own=next(row for row in data['directions'] if row['id']=='specificity-ladder')
        foreign=[]
        for row in data['directions']:
            if row['id']=='specificity-ladder':continue
            declarations={key:row[key] for key in ('do_not_touch','archive','legacy_scratch') if row.get(key)}
            if row.get('frozen_grader_sha256') is not None:declarations['frozen_grader_sha256']=row['frozen_grader_sha256']
            if declarations:foreign.append(dict(id=row['id'],declarations=declarations))
        foreign=sorted(foreign,key=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False))
        catalogue_checks.append(dict(route=route,own_entry_matches=own==record['own_entry'],foreign_declarations_match=foreign==record['foreign_declarations'],
            top_matches={key:value for key,value in data.items() if key not in ('directions','updated')}==record['top']))
    packet_pins=read(T/'packet-pins.json')
    for name,digest in packet_pins.items():assert sha(T/name)==digest
    components=read(T/'candidate/manifest.json')['unchanged_component_files']
    for path,digest in components.items():assert sha(path)==digest
    result=dict(kind='READ_ONLY_SOURCE_AND_EXTRACTED_PREDICATE_DIAGNOSIS',actual_job='23637408',case_groups=case_groups,
        actual_result=read(R/'RESULT.json'),raw_evidence={name:dict(path=str(R/name),sha256=sha(R/name)) for name in ('RESULT.json','base39.log','base39.xml','mgnp.log','mgnp.xml','run_manifest.json')},
        lineage=dict(classification='FIXTURE_SNAPSHOT_ANCHOR_MISMATCH',pairs=pairs,production_guard_correct=True,
            field='cutover.ledger_sha256',cause='Fixture seals pre-transition origin old.json; native original_snapshot_path is the preserved snapshot of the active successor, new.json. Mapping/lineage references match; only snapshot anchor fails.',
            original_source=dict(normalize=str(SOURCE/'component_analysis/a3_direction_runtime.py')+':335',authenticate=str(C/'root/helper.py')+':138')),
        geometry=dict(classification='FIXTURE_ENVIRONMENT_NAMESPACE_MISMATCH_SOURCE_REPLAY',observed_runtime_failure='stale A2 model_geometry in both actual logs',
            frozen=frozen,replayed=geometries,config_paths=config_paths,only_different_field='model_geometry.source.path',
            observed_current_shell_environment={key:os.environ.get(key) for key in ('HF_HOME','HF_HUB_CACHE','HUGGINGFACE_HUB_CACHE','TRANSFORMERS_CACHE','XDG_CACHE_HOME')},
            replay_scope='Original metadata-only geometry function with only external resolver supplied a known path; no huggingface/native/application import or actual resolver invocation.',
            evidence_limit='Actual job HF environment and fresh_geometry object were not captured. Actual stale-geometry exception is observed; nested-hub resolver path is a deterministic source replay under the observed submission-shell environment, not a fabricated job observation.',
            source_cause='Observer inherits HF variables and never establishes the original wrappers HF_HUB_CACHE=/work/nvme/beto/swong2 or offline env before native imports. HF_HOME alone defaults to HF_HOME/hub. Both config files have identical bytes/numerical geometry; absolute resolved path is part of frozen provenance.'),
        downstream_sweep=dict(WAITING_contract='All38 diagnosed publish-bound artifacts retain exact raw copy and expected hashes; regression33 passed.',
            current_grader_projection=catalogue_checks,
            support_placeholder=dict(observed_synthetic_CPU_hash=pairs[0]['CPU_support_mask_sha256'],accepted_proof249_285_hash='73002c8b74d13947aeb9bf1f6e09d50544b549ea51ab00a50b9510bd6404ffd8',
                classification='SOURCE_LEVEL_FULL_FIXTURE_PROVENANCE_INCONSISTENCY_NOT_NEW_GUARD_FAILURE',
                note='Small synthetic constructor uses8*64 in all cases. Full fixture constructs native domain but never propagates its actual CPU-format support digest into that synthetic child proof. Current root checks only format/counts, so this is not the observed failure or a proven next thrown guard. A future full-case fixture may bind its actually reconstructed support hash before sealing; never alter real frozen proof.'),
            native_remaining='Runtime source hashes, referenced all18 comparison, complete bank contract/tokenizer/numerical environment, actual full support construction, publication/consumer/audits remain unexecuted beyond current failures. No blanket downstream-green claim.'),
        production_components_unchanged=len(components),active_packet_pins_sha256=sha(T/'packet-pins.json'),active_packet_edited=False,
        native_imports=False,local_full_tests=False,fixture_edits=False,real_authority_mutated=False,
        minimal_future_proposal=['Construct cutover from the returned normalized active snapshot SHA, then immediately call original authenticate_cutover with that same normalized object before expensive later fixture work.',
            'Establish exact original HF_HUB_CACHE/TRANSFORMERS_CACHE/offline environment before importing project/HF modules; retain original S cwd and frozen receipt/geometry bytes. Do not rewrite geometry or bypass native validation.',
            'Preserve raw-byte regression and stage assertions; add a native-data-free predicate/schema preflight over temporary evidence and deterministic environment checks so construction errors fail before a full job.',
            'For the full case, consider replacing the synthetic support placeholder with the exact already-reconstructed CPU-format digest before its own prospective proof is sealed; no new reconstruction or real proof mutation.',
            'Root consolidates and authorizes one corrected packet only after reviewing this diagnosis; this task creates none.'])
    (P/'diagnosis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(actual_cases_per_environment=33,failures_per_environment=20,lineage_artifact_pairs=len(pairs),lineage_only_wrong_field='ledger_sha256',geometry_only_replayed_difference='source.path',components_unchanged=len(components),fixture_edits=False)))
if __name__=='__main__':main()
