from pathlib import Path
import json,hashlib,math
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');P=W/'outputs/_analyses/specificity-ladder/a2-bridges2-20261102';E=W/'docs/research/specificity-ladder/reports/125-a2-bridges-scientific-readiness-evidence'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ref=json.loads((W/'.superpowers/sdd/plan-a2-bridges2/reference-check/reference-schema.json').read_text())['references'];proposal=json.loads((P/'scientific-replacement-proposal.json').read_text());fleetpath=W/'outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json';fleet=json.loads(fleetpath.read_text());assert sha(fleetpath)==proposal['original_fleet_plan_sha256'];out={}
for arm in ('D','I'):
    original_path=Path(ref[arm]['receipt']['path']);assert sha(original_path)==ref[arm]['receipt']['sha256'];old=json.loads(original_path.read_text());rp=P/'returned-receipts'/('sdr_v2-'+arm+'-seed42.json');new=json.loads(rp.read_text())
    for key in ('purpose','actual_epochs','planned_epochs','task','condition','seed','execution_commit','source_commit','source_hashes','build_hash','build_manifest_sha256','config_file_sha256','build_manifest_file_sha256','frozen_config_sha256','resolved_config_sha256','dataset_config_sha256','selected_ids','counts','argv','output_dir'):
        if key=='argv':assert old[key][2:]==new[key][2:]
        else:assert old[key]==new[key],key
    assert new['status']=='success' and new['exit_code']==0 and new['errors']==[] and not new['test_runner_injected'] and not new['test_clock_injected'];assert new['gpu_count']==1 and 'H100' in new['gpu_devices'][0] and new['environment']['SLURM_CLUSTER_NAME']=='bridges2'
    path=P/'returned-native'/Path(new['output_dir']).name;identical={};native={}
    for name,info in ref[arm]['artifacts'].items():
        original=Path(info['path']);target=path/name;assert sha(original)==info['sha256']==old['artifact_sha256'][name];assert sha(target)==new['artifact_sha256'][name]
        identical[name]=sha(original)==sha(target);native[name]=json.loads(target.read_text())
    assert all(identical[n] for n in ('config.json','active_nodes.json','results.json','history.json'))
    results=native['results.json'];history=native['history.json']['node'];mask=native['active_nodes.json'];summaries={}
    for key in ('baseline','node_eval'):
        rows=results[key]['outputs'];assert [r['instance_id'] for r in rows]==new['selected_ids']['test'];assert len(rows)==952
        for r in rows:
            assert all(k in r for k in ('target','distractor','chosen_word','logit_target','logit_distractor','logit_difference'))
            assert all(math.isfinite(r[k]) for k in ('logit_target','logit_distractor','logit_difference'))
        summaries[key]={'rows':len(rows),'all_row_fields_exact':identical['results.json']}
    assert [e['epoch'] for e in history['evals']]==[0,10,20]
    for ev in history['evals']:assert [r['instance_id'] for r in ev['outputs']]==new['selected_ids']['validation']
    assert all(len(history[k])==20 for k in ('epochs','loss','kl','task','sparsity','lr'))
    def leaves(v):
        if isinstance(v,dict):return [x for y in v.values() for x in leaves(y)]
        if isinstance(v,list):return [x for y in v for x in leaves(y)]
        return [v]
    binary=leaves(mask['masks']);assert len(binary)==1056 and all(v in (0,1) for v in binary)
    heads=sum(len(v) for v in mask['active_heads'].values());mlps=len(mask['active_mlps'])
    prediction=new['total_seconds']-new['pruning_seconds']+new['pruning_seconds']*500/new['actual_epochs'];minutes=math.ceil(prediction*1.2/60)
    out[arm]={'original_receipt_sha256':sha(original_path),'returned_receipt_sha256':sha(rp),'artifact_byte_identity':identical,'pretraining_rows':{'test':len(results['baseline']['outputs']),'validation_epoch0':len(history['evals'][0]['outputs'])},'results':summaries,'validation_epochs':[ev['epoch'] for ev in history['evals']],'validation_rows_each':len(history['evals'][0]['outputs']),'binary_mask_entries':len(binary),'active_heads':heads,'active_mlps':mlps,'observed_total_seconds':new['total_seconds'],'observed_pruning_seconds':new['pruning_seconds'],'projected_process_seconds':prediction,'buffered_requested_minutes':minutes}
for cell in proposal['cells']:
    original=next(c for c in fleet['cells'] if (c['task'],c['condition'],c['seed'])==(cell['task'],cell['condition'],cell['seed']));assert original==cell['original_fleet_cell'];assert cell['timing_receipt_sha256']==out[cell['condition']]['returned_receipt_sha256'];assert cell['requested_minutes']==out[cell['condition']]['buffered_requested_minutes'];assert math.isclose(cell['reserved_gpu_hours'],cell['requested_minutes']/60)
    expected_out=W/'outputs/_training_specificity_ladder/a2-h200'/('sdr_v2_'+cell['condition']+'_seed'+str(cell['seed'])+'_heads-mlp_b8cf3de656d58e28')
    # Exact output name is resolved by the frozen scientific plan later; record only existing canonical receipt here.
    cell['reviewer_canonical_receipt_absent']=not Path(original['receipt']).exists() and not Path(original['receipt']).is_symlink()
assert len(proposal['cells'])==6 and math.isclose(sum(c['reserved_gpu_hours'] for c in proposal['cells']),proposal['new_reserved_gpu_hours'])
assert math.isclose(proposal['combined_before']+proposal['new_reserved_gpu_hours'],proposal['combined_after']) and proposal['combined_after']<proposal['combined_cap']
result={'kind':'independent_stored_native_and_proposal_review','arms':out,'proposal_sha256':sha(P/'scientific-replacement-proposal.json'),'exact_original_six_cell_bytes':True,'original_charges_retained_proposal_only':True,'canonical_receipts_absent_at_local_inspection':all(c['reviewer_canonical_receipt_absent'] for c in proposal['cells']),'new_gpu_hours':proposal['new_reserved_gpu_hours'],'combined_before':proposal['combined_before'],'combined_after':proposal['combined_after'],'combined_cap':proposal['combined_cap'],'model_or_remote_calls':False,'scientific_admission':False};(E/'native-and-proposal-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
