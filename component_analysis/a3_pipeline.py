"""A3 CPU preparation and fail-closed parent loading.

Later execution stages belong to the staged A3 pipeline; this module never loads
weights. Parent reads always use A1's original identity, including its full scope.
"""
from __future__ import annotations
import copy
import csv
import json
import re
from pathlib import Path
from types import SimpleNamespace

from component_analysis import a3_design
from component_analysis import ladder_pipeline as ladder
from dataset import user_inversion_pipeline as common

require=common.require


def load_a1_parents(design_path, selected_path):
    prepared=ladder.read_artifact(design_path)
    require(prepared.get('kind')=='prepared','missing A1 prepared artifact')
    args=SimpleNamespace(**{k:prepared[k] for k in ('tasks','commit','model','model_revision','tokenizer_revision')},groups=str(selected_path))
    selected=ladder.read_selection(args,prepared)
    completion_path=ladder.selection_manifest_path(selected_path)
    evidence=dict(completion=json.loads(completion_path.read_text()),completion_path=str(completion_path.resolve()),
                  completion_file_sha256=common.file_hash(completion_path),
                  prepared_path=str(Path(design_path).resolve()),prepared_file_sha256=common.file_hash(design_path),
                  selected_path=str(Path(selected_path).resolve()),selected_file_sha256=common.file_hash(selected_path))
    return prepared,selected,evidence


def canonical_source_hashes(values, *, a1_repo_root):
    """Comparison lookup only; immutable A1 identities remain untouched."""
    root=Path(a1_repo_root).resolve(); result={}
    for path,digest in values.items():
        candidate=Path(path)
        resolved=str((candidate if candidate.is_absolute() else root/candidate).resolve())
        require(resolved not in result or result[resolved]==digest,'conflicting frozen source path aliases: '+resolved)
        result[resolved]=digest
    return result


def _validate_parent_files(prepared, *, a1_repo_root=ladder.REPO):
    require(prepared['code_hashes']==ladder.code_hashes(),'changed A1 source/code/grader hashes')
    for domain in ('source_hashes','selection_hashes'):
        for path,digest in canonical_source_hashes(prepared[domain],a1_repo_root=a1_repo_root).items():
            require(Path(path).is_file() and common.file_hash(path)==digest,'changed A1 '+domain+': '+path)
    ladder.grader_registry()


def _matched_rows(root, manifest, prepared, *, a1_repo_root=ladder.REPO, tokenizer=None):
    """Inspect materialized source rows, not just claimed build_manifest counts."""
    from datasets import load_from_disk
    from dataset.build_twin_training import _load
    result=copy.deepcopy(manifest); result['parent_fingerprints']={k:copy.deepcopy(prepared[k]) for k in ('source_hashes','tokenizer_identity','grader_sha256')}
    enriched=copy.deepcopy(prepared['rows'])
    canonical_hashes=canonical_source_hashes(prepared['source_hashes'],a1_repo_root=a1_repo_root)
    from scripts.twin_training import _stored_rows
    for task,summary in result['tasks'].items():
        _stored_rows(dict(data_root=str(Path(root).resolve()),sample_caps={s:len(ids) for s,ids in summary['split_ids'].items()}),
                     manifest,task,summary['split_ids'])
        summary['actual_split_ids']={}
        source_rows={}
        for condition,meta in summary['sources'].items():
            for relative,digest in meta['file_hashes'].items():
                source_path=str((Path(meta['path'])/relative).resolve())
                require(canonical_hashes.get(source_path)==digest,'matched source is not frozen A1 input')
                require(common.file_hash(source_path)==digest,'changed matched source hash')
            loaded,fresh=_load(meta['path'])
            require(fresh==meta,'changed matched source metadata')
            source_rows[condition]={split:{r['instance_id']:r for r in rows} for split,rows in loaded.items()}
        for arm in ('D','I'):
            path=Path(root)/arm/task
            dataset=load_from_disk(str(path)); actual={}
            cfg_path=path/'dataset_config.json'
            require(cfg_path.is_file(),'missing actual matched configuration')
            cfg=json.loads(cfg_path.read_text())
            require(cfg.get('split_ids')==summary['split_ids'] and cfg.get('cohort')=='matched' and cfg.get('fleet_ready') is True and cfg.get('source_provenance')=={k:summary['sources'][k] for k in (arm,'H' if arm=='D' else 'I_neutral')},'stale actual matched configuration')
            for split in ('train','validation','test'):
                actual[split]=[]
                indices={c:{r['instance_id']:r for r in enriched[task][c] if r['split']==split} for c in enriched[task]}
                for row in dataset[split]:
                    rid=row['instance_id']; actual[split].append(rid)
                    source=row['source_recipient']; neutral=row['source_reference']
                    reference='H' if arm=='D' else 'I_neutral'
                    require(source==source_rows[arm][split].get(rid) and neutral==source_rows[reference][split].get(rid),
                            'materialized matched source row differs from frozen original')
                    if tokenizer is not None:
                        from dataset.build_twin_training import _pair, LABELS
                        require(row.get('token_proof')==_pair(source,neutral,tokenizer,manifest['max_seq_length']),
                                'stored builder token proof differs from recomputation')
                        require(row.get('label_semantics')==LABELS,'stored label semantics mismatch')
                    peer='H' if arm=='D' else 'user_neutral'
                    for condition,raw in ((arm,source),(peer,neutral)):
                        require(rid in indices[condition], 'actual source not in A1 parent')
                        target=indices[condition][rid]
                        for stream in ('clean','corrupt'):
                            require(target['streams'][stream]['prompt']==raw[stream+'_prompt'],'actual matched prompt differs from A1')
                        fields=('task','template_variant','entity','item_1','item_2','clean_item_d','desig','desig_inv','suffix','ser_wording','pressure')
                        target['semantic_source']={k:raw[k] for k in fields if k in raw}
                        # A1 normalization intentionally omits semantic source wording.
                        for field in ('pressure','request_text','question','designation_text'):
                            if field in raw: target[field]=raw[field]
                    # Canonical D pressure wording defines the cluster in every arm.
                    if arm=='D':
                        require(isinstance(source.get('pressure'),str) and source['pressure'],'missing D pressure wording')
                        for condition in indices:
                            if rid in indices[condition]:
                                indices[condition][rid]['pressure_text']=source['pressure']
                                if condition=='F':
                                    indices[condition][rid]['semantic_source']=dict(indices[arm][rid]['semantic_source'],pressure='')
            summary['actual_split_ids'][arm]=actual
    return result,enriched


def freeze_semantic_maps(design, tokenizer):
    """Builder-verified bidirectional maps; no D/I token correspondence."""
    from component_analysis import ladder_design
    from dataset.matched_honest import assert_clause_aligned_pair
    result={}
    for task,rows in design['access_rows'].items():
        indexed={(r['condition'],r['instance_id']):r for r in rows}
        maps=[]
        for row in rows:
            if row['condition'] not in ('D','I'): continue
            peer='H' if row['condition']=='D' else 'user_neutral'
            donor=indexed.get((peer,row['instance_id']))
            for stream,left in row['streams'].items():
                entry=dict(instance_id=row['instance_id'],recipient_condition=row['condition'],donor_condition=peer,
                    stream=stream,bidirectional=True,supported=False,recipient_positions=[],donor_positions=[],
                    unsupported_reason='missing or non-exact builder map')
                try:
                    require(donor is not None,'missing semantic twin')
                    right=donor['streams'][stream]
                    require(ladder_design._aligned(left,right),'unsupported role/layout map')
                    if row['condition']=='I':
                        require(ladder_design._request_matches(row,donor,stream),'unsupported user-request map')
                    clause=row.get('request_text') if row['condition']=='I' else row.get('pressure')
                    require(isinstance(clause,str) and clause,'missing builder clause wording')
                    a,b,span=assert_clause_aligned_pair(tokenizer,left['prompt'],right['prompt'],clause,
                                                      max(len(left['tokens']),len(right['tokens'])))
                    require(list(a)==left['tokens'] and list(b)==right['tokens'],'changed semantic tokenization')
                    start,end=span
                    require(len(a)==len(b) and 0<=start<end<=len(a)-1,'unequal/unpadded clause map')
                    require(end-start==len(tokenizer.encode(' '+clause,add_special_tokens=False)),
                            'clause boundary BPE merge')
                    require(all(x==y for pos,(x,y) in enumerate(zip(a,b)) if not start<=pos<end),
                            'tokens differ outside builder clause span')
                    require(a[-1]==b[-1],'builder readout differs')
                    entry.update(supported=True,recipient_positions=list(range(len(a))),donor_positions=list(range(len(b))),
                                 replacement_span=list(span),unsupported_reason=None)
                except (ValueError,AssertionError,IndexError):
                    pass
                maps.append(entry)
        result[task]=maps
    return result


def validate_assessment_membership(design, parent):
    """Ordered original assessment cohorts and utility bytes remain ancestral."""
    require(set(design['tasks'])==set(parent['tasks']), 'changed assessment task scope')
    require(design['utility']==parent['utility'], 'changed original assessment utilities')
    for task,settings in design['tasks'].items():
        ids=parent['designs'][task]['assessment_ids']
        require(settings['assessment_ids']==ids, 'changed original assessment membership/order')
        expected={(c,r['instance_id']):r for c,values in parent['rows'][task].items()
                  for r in values if r['instance_id'] in set(ids)}
        actual={(r['condition'],r['instance_id']):r for r in design['access_rows'][task]
                if r['instance_id'] in set(ids)}
        require(set(actual)==set(expected), 'changed assessment row coverage')
        for key,row in expected.items():
            # Semantic source enrichment is allowed; all original stream data,
            # labels and exact prompt/token bytes remain immutable.
            for field,value in row.items():
                if field=='streams':
                    require(set(actual[key]['streams'])==set(value),'changed assessment streams')
                    require(all(actual[key]['streams'][stream].get(k)==v for stream,record in value.items()
                                for k,v in record.items()), 'changed assessment prompt/token/label bytes')
                elif field not in ('pressure','pressure_text','pressure_clause','request_text','question','designation_text'):
                    require(actual[key].get(field)==value,'changed assessment row identity')


def assessment_exclusions(parent):
    """Original assessment prompts plus actual donor/source identities and bytes."""
    fixed=[]
    for task,conditions in parent['rows'].items():
        settings=parent['designs'][task]
        donors=copy.deepcopy(settings.get('donors',[]))
        donor_ids=set().union(*(a3_design._utility_identity(row)[0] for row in donors)) if donors else set()
        ids=set(settings['assessment_ids'])|donor_ids
        fixed.extend(copy.deepcopy(row) for values in conditions.values() for row in values
                     if row['instance_id'] in ids)
        fixed.extend(donors)
    for values in parent['utility'].values():
        if isinstance(values,list): fixed.extend(copy.deepcopy(row) for row in values if isinstance(row,dict))
    return fixed


def direction_protocol(design, *, commit, injected_code_hashes=None):
    """Freeze the reviewed operational contract, separately from the A1 identity."""
    from component_analysis import a3_direction_artifacts as artifacts
    require(isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit) is not None,
            'A3 execution requires full source commit')
    if injected_code_hashes is not None:
        require(design.get('injected') is True and isinstance(injected_code_hashes,dict),
                'injected source closure forbidden for production')
        closure=copy.deepcopy(injected_code_hashes)
    else: closure=artifacts.code_hashes()
    protocol=dict(schema_version=1,kind='a3_direction_protocol',commit=commit,code_hashes=closure,
        design_sha256=ladder.design._hash(design),injected=bool(design.get('injected')),
        task_order=list(design['tasks']),candidate_sites={t:v['direction_sites'] for t,v in design['tasks'].items()},
        stream_order=list(ladder.design.STREAMS),seeds=[42,1,123],assessment_orientations=199,calibration_orientations=32,
        bootstrap=dict(assessment=2000,assessment_seed=9001,power=2000,power_seed=19001),
        confirmatory_tasks=['far_v2','ser_v2'],descriptive_tasks=['sdr_v2'],
        utility_membership={k:copy.deepcopy(design[k]) for k in ('ioi_validation','mmlu_validation','ioi_validation_maps','mmlu_validation_maps')},
        original_utility_sha256=ladder.design._hash(design['utility']),
        operations=dict(primary=dict(mechanism='opposite_designation_subspace_interchange',ioi='item_swap',mmlu=['subspace_zero','centered_H']),
            primary_families=['learned','assessment_null','calibration_null'],
            secondary=dict(families=['learned','nuisance'],tasks=['mechanism','ioi'],operations=['subspace_zero','centered_H']),
            steering=dict(families=['learned','nuisance','assessment_null:0'],signs=[-1,1],tasks=['mechanism','ioi','mmlu']),
            controls=['no_op','positive_control','perturbation_diagnostics']),
        numeric_profile=dict(dtype='bfloat16',backend='existing native inference hooks',readout='last unpadded assistant readout',
                             gradients=False,matched_shape_controls=True),
        limits=dict(direction_M1_gpu_hours=0.5,all_M1_gpu_hours=2,direction_M2_gpu_hours=9,A3_gpu_hours=40),
        validation_mmlu=dict(candidate_seed=2,candidate_count=128,n=32,source_split='test',analysis_split='validation',
                             selection='first unique disjoint candidates; no redraw/network/outcome filtering'),
        finalization=dict(requires_complete_runtime=True,injected_forbidden=True,pilot_forbidden=True))
    if injected_code_hashes is not None: protocol['injected_source_closure']=closure
    return protocol


def prepare(*, a1_design, a1_selected, matched_root, historical_csv, root_ruling,
            tokenizer, registry_paths=(), output=None, a1_repo_root=ladder.REPO,
            commit=None, injected_code_hashes=None):
    """Validate CPU provenance and freeze; no call to A1 freeze_design/draw_sample.

    The output is immutable. ``output=None`` validates without writing. Fixtures
    may call freeze_a3 directly; production preparation requires actual files.
    """
    from dataset.build_twin_training import _hash as matched_hash
    from component_analysis.ladder_tasks import _ioi_candidates, mmlu_rows, ioi_item_swap_maps, mmlu_calibration_maps
    p,s,evidence=load_a1_parents(a1_design,a1_selected)
    _validate_parent_files(p,a1_repo_root=a1_repo_root)
    fresh_identity=common.tokenizer_identity(tokenizer,p['tokenizer_revision'],injected=p.get('injected',False))
    require(fresh_identity==p['tokenizer_identity'],'changed tokenizer identity')
    ladder.validate_tokenization(p,tokenizer)
    path=Path(matched_root)/'build_manifest.json'; original=json.loads(path.read_text())
    core={k:v for k,v in original.items() if k!='build_hash'}
    require(original.get('build_hash')==matched_hash(core),'changed matched manifest hash')
    matched,enriched=_matched_rows(matched_root,original,p,a1_repo_root=a1_repo_root,tokenizer=tokenizer)
    # Enrichment is source text only: preserve the original parent payload hash.
    history=dict(rows=list(csv.DictReader(Path(historical_csv).open())),source_hashes={str(Path(historical_csv).resolve()):common.file_hash(historical_csv)},
                 selection_completion=evidence['completion'])
    # freeze_a3 validates immutable original A1 hash first; enrich the resulting
    # semantic/cluster metadata through a separate explicit source adapter.
    history['source_rows']=enriched
    result=a3_design.freeze_a3(p,s,matched,history,root_ruling=root_ruling)
    fixed=list(p['utility']['ioi'])
    validation=a3_design.eligible_ioi(_ioi_candidates(tokenizer,count=1000,seed=2),fixed,n=100)
    require(len(validation)==100,'insufficient unique eligible seed-2 IOI validation prompts')
    result.update(ioi_validation=validation,ioi_validation_seed=2,parent_evidence=evidence,
                  a1_repo_root=str(Path(a1_repo_root).resolve()),
                  reused_a2_validator_sha256=common.file_hash(ladder.REPO/'scripts/twin_training.py'),
                  matched_build_path=str(path.resolve()),matched_build_file_sha256=common.file_hash(path))
    fixed_assessment=assessment_exclusions(p)
    candidates,candidate_manifest=mmlu_rows(tokenizer,n=128,seed=2)
    require(len(candidates)==128, 'canonical MMLU candidate count mismatch')
    result['mmlu_validation']=a3_design.eligible_mmlu(candidates,fixed_assessment,n=32)
    result['mmlu_validation_candidates_manifest']=copy.deepcopy(candidate_manifest)
    result['mmlu_validation_candidates_manifest']['grader_registry']=ladder.grader_registry()
    result['mmlu_validation_candidates_manifest']['grader_sha256']=p['grader_sha256']
    result['ioi_validation_maps']=ioi_item_swap_maps(validation)
    result['mmlu_validation_maps']=mmlu_calibration_maps(result['mmlu_validation'])
    result['semantic_twin_maps']=freeze_semantic_maps(result,tokenizer)
    for rows in result['access_rows'].values():
        for row in rows:
            pair=dict(clean_prompt=row['streams']['clean']['prompt'],corrupt_prompt=row['streams']['corrupt']['prompt'],
                      clean_item_d=row['streams']['clean']['honest_item'],corrupt_item_d=row['streams']['corrupt']['honest_item'])
            for stream,record in row['streams'].items():
                source=dict(row,**record,stream=stream,designation_source=pair)
                record['semantic']=a3_design.semantic_record(source,tokenizer)
    result['registry_hashes']=a3_design.validate_access(result,list(registry_paths))
    validate_assessment_membership(result,p)
    protocol=direction_protocol(result,commit=commit,injected_code_hashes=injected_code_hashes)
    result['direction_protocol']=protocol
    result['direction_protocol_sha256']=ladder.design._hash(protocol)
    if output is not None:
        target=Path(output)
        require(target.name=='design.json','canonical A3 output must be NEW_ROOT/design.json')
        def writer(root):
            ladder.write_artifact(root/'design.json',result)
            ladder.write_artifact(root/'direction_protocol.json',protocol)
        common.publish(target.parent,writer)
    return result


def main(argv=None, *, tokenizer=None, model_loader=None):
    """Lazy stage boundary; partial implementations must not silently succeed."""
    import argparse
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--experiment',required=True,choices=('directions',))
    parser.parse_known_args(argv)
    try:
        from component_analysis.a3_direction_pipeline import main as dispatch
    except ModuleNotFoundError as error:
        if error.name!='component_analysis.a3_direction_pipeline': raise
        raise ValueError('A3 direction stages are not implemented; complete runtime required') from error
    return dispatch(argv,tokenizer=tokenizer,model_loader=model_loader)


if __name__=='__main__':
    main()
