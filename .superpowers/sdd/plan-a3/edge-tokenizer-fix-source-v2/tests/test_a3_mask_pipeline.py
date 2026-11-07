"""Task5b CPU contracts; no pretrained weights or assessment selection."""
import copy
import subprocess
from pathlib import Path

import pytest
import torch
from component_analysis import a3_mask as core


def driver():
    from component_analysis import a3_mask_pipeline
    return a3_mask_pipeline


def tiny():
    from transformers import LlamaConfig
    from models.llama_node import PrunableLlamaForCausalLM, PruningConfig, apply_pruning_wrappers
    torch.manual_seed(73)
    model = PrunableLlamaForCausalLM(LlamaConfig(hidden_size=8, intermediate_size=12,
        num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1,
        vocab_size=17, attn_implementation='eager'))
    apply_pruning_wrappers(model, PruningConfig())
    support = core.configure_candidates(model, [('head',0,0),('mlp',0,0)])
    chunks=[]
    for condition in ('D','I','H'):
        ids=torch.tensor([[[1,2,3],[3,2,1]]])
        chunks.append([core.MaskChunk(('fit',),torch.zeros(1,2),torch.zeros(1,2,17),
            dict(input_ids=ids, neutral_input_ids=ids.roll(1,-1), attention_mask=torch.ones_like(ids),
                 opposite_ids=torch.full((1,2),7),honest_ids=torch.full((1,2),3)),torch.full((1,2),3))])
    return model,support,chunks


def test_safe_checkpoint_roundtrip_and_corruption(tmp_path):
    p=driver(); model,support,(ds,ins,hs)=tiny()
    opt=torch.optim.Adam(support.parameters(),lr=.01)
    state=core.make_checkpoint(model,support,opt,ds,ins,identity={'source':'tiny'},update=0)
    path=tmp_path/'checkpoint'; p.write_checkpoint(path,state)
    saved=p.read_checkpoint(path)
    assert saved['support']==state['support']
    assert torch.equal(saved['rng']['cpu'],state['rng']['cpu'])
    assert not any('weight' in name for name in saved['gates'])
    with (path/'state.json').open('a') as handle: handle.write(' ')
    with pytest.raises(ValueError,match='digest|complete'): p.read_checkpoint(path)


def test_native_update_validation_export_and_exact_resume(tmp_path):
    p=driver(); model,support,(ds,ins,hs)=tiny()
    opt=torch.optim.Adam(support.parameters(),lr=.01)
    identity={'source':'tiny'}
    core.streamed_update(model,support,opt,ds,ins,core.native_chunk_forward,g_d_fit=torch.tensor(2.),identity=identity)
    state=core.make_checkpoint(model,support,opt,ds,ins,identity=identity,update=1)
    p.write_checkpoint(tmp_path/'one',state)
    core.streamed_update(model,support,opt,ds,ins,core.native_chunk_forward,g_d_fit=torch.tensor(2.),identity=identity)
    expected=copy.deepcopy(model.state_dict()); rng=core.rng_state()
    core.restore_checkpoint(p.read_checkpoint(tmp_path/'one'),model,support,opt,ds,ins,identity=identity)
    core.streamed_update(model,support,opt,ds,ins,core.native_chunk_forward,g_d_fit=torch.tensor(2.),identity=identity)
    for name,value in model.state_dict().items(): torch.testing.assert_close(value,expected[name],rtol=0,atol=0)
    assert torch.equal(core.rng_state()['cpu'],rng['cpu'])
    receipt=p.binary_parity(model,ds+ins)
    assert receipt['max_abs_error']==0 and receipt['rows']==4
    changed=copy.deepcopy(ds); changed[0].ids=('changed',)
    with pytest.raises(ValueError): core.restore_checkpoint(state,model,support,opt,changed,ins,identity=identity)


def test_schedule_never_stops_after_validation_pass():
    p=driver(); updates=[]; validations=[]
    def update(index): updates.append(index)
    def validate(index):
        validations.append(index)
        return {'update':index,'eligible':True,'removed':[['head',0,0]]}
    result=p.schedule(update,validate,start=0,injected=True)
    assert updates==list(range(1,201)) and validations==list(range(20,201,20))
    assert result['selected']['update']==20 and result['completed_updates']==200
    with pytest.raises(ValueError): p.schedule(update,validate,start=201,injected=True)


def test_selection_fail_closed_and_frozen_without_assessment():
    p=driver()
    rows=[dict(update=i,eligible=i>=40,removed=[['head',0,0]]) for i in range(20,201,20)]
    assert p.select_checkpoint(rows)['update']==40
    assert p.select_checkpoint([dict(r,eligible=False) for r in rows])['update']==200
    with pytest.raises(ValueError): p.select_checkpoint(rows[:-1])
    with pytest.raises(ValueError): p.select_checkpoint([dict(r,split='test') for r in rows])


def test_random_controls_are_typed_fixed_and_keep_duplicates():
    p=driver(); candidates=[('head',0,i) for i in range(4)]+[('mlp',0,0)]
    selected=[('head',0,1),('mlp',0,0)]
    a=p.random_controls(candidates,selected,seed=42)
    assert len(a)==19 and a==p.random_controls(candidates[::-1],selected,seed=42)
    assert all(sum(k[0]=='head' for k in row)==sum(k[0]=='mlp' for k in row)==1 for row in a)
    assert p.random_controls(candidates,candidates,seed=42)==[sorted(candidates)]*19
    with pytest.raises(ValueError): p.random_controls(candidates,[('head',9,9)],seed=42)


def test_wrapper_dry_run_no_weights_no_writes(tmp_path):
    wrapper=Path(__file__).resolve().parents[1]/'scripts/jobs/specificity_a3_mask.sh'
    result=subprocess.run(['bash',str(wrapper),'--dry-run','--stage','fit','--design',str(tmp_path/'missing'),
                           '--commit','a'*40,'--work-dir',str(tmp_path/'output')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'a3_mask_pipeline' in result.stdout and not (tmp_path/'output').exists()


def test_source_adapter_excludes_test_and_requires_verified_own_twin_map():
    p=driver()
    streams={s:dict(tokens=[1,2,3],readout=2,opposite_token=7,honest_token=3,expected_token=7) for s in ('clean','corrupt')}
    rows=[dict(instance_id='fit',split='train',condition=c,streams=copy.deepcopy(streams)) for c in ('D','I','H','user_neutral','F')]
    design=dict(tasks={'far_v2':dict(fit_ids=['fit'],selection_ids=['val'],assessment_ids=['test'])},
                access_rows={'far_v2':rows},semantic_twin_maps={'far_v2':[dict(instance_id='fit',recipient_condition=c,donor_condition=d,
                    stream=s,supported=True,recipient_positions=[0,1,2],donor_positions=[0,1,2])
                    for c,d in [('D','H'),('I','user_neutral')] for s in ('clean','corrupt')]})
    chunks=p.source_chunks(design,'far_v2','train','D',chunk_size=1,device='cpu')
    assert chunks[0].ids==('fit',) and chunks[0].payload['input_ids'].shape==(1,2,3)
    with pytest.raises(ValueError): p.source_chunks(design,'far_v2','test','D',chunk_size=1,device='cpu',fitting=True)
    design['semantic_twin_maps']['far_v2'][0]['supported']=False
    with pytest.raises(ValueError,match='map'):p.source_chunks(design,'far_v2','train','D',chunk_size=1,device='cpu')


def test_validation_ratio_of_means_is_distinct_from_raw_choice():
    p=driver()
    records=[]
    for condition,base,patched in [('D',3.,2.),('H',1.,1.),('I',3.,2.6),('user_neutral',1.,1.),('F',1.,1.),('IOI',1.,1.)]:
        records.extend(dict(instance_id=str(i),stream=s,condition=condition,intact_margin=base,patched_margin=patched,
                    intact_accuracy=1.,patched_accuracy=1.) for i in range(2) for s in ('clean','corrupt'))
    gate=p.validation_gates(records,epsilon=1e-6)
    assert gate['D_fraction']==.5 and abs(gate['I_fraction']-.2)<1e-12 and gate['eligible']
    with pytest.raises(ValueError):p.validation_gates([r for r in records if r['condition']!='F'],epsilon=1e-6)


def test_exported_hooks_match_native_binary_for_head_and_whole_mlp():
    p=driver();model,support,(ds,ins,hs)=tiny()
    for removed in ([],[('head',0,0)],[('mlp',0,0)],list(support.candidates)):
        with p.binary_mode(model,removed),torch.no_grad():
            dual=core.native_chunk_forward(model,ds[0])['logits']
            independent=p.exported_forward(model,ds[0],removed)
        torch.testing.assert_close(dual,independent,atol=1e-7,rtol=1e-6)


def test_mask_inventory_contains_every_update_arm_validation_and_transfer():
    from component_analysis import a3_mask_workload as w
    design={'tasks':{t:dict(fit_ids=['fit'],selection_ids=['validation'],assessment_ids=['test']) for t in ('far_v2','ser_v2','sdr_v2')},
            'ioi_validation':[{'instance_id':'iv'}],'utility':{'ioi':[{'instance_id':'ioi'}],'mmlu':[{'instance_id':'mmlu'}]}}
    inventory=w.build_inventory(design,identity={'commit':'a'*40},chunk_size=1,finish_reserve_seconds=60)
    keys=inventory['expected_keys']
    assert len([k for k in keys if k[0]=='update' and k[-1]=='D_replay_backward'])==1200
    assert len([k for k in keys if k[0]=='checkpoint'])==1200
    assert {k[2] for k in keys if k[0]=='assessment'}=={'far_v2','ser_v2','sdr_v2'}
    changed=copy.deepcopy(inventory);changed['expected_keys']=keys[:-1];changed['inventory_sha256']=w.inventory_digest(changed)
    with pytest.raises(ValueError):w.validate_inventory(changed)


def test_frozen_new30_reads_json_links_only():
    p=driver();reference=p.new30_reference()
    assert reference['status']=='available' and len(reference['removed'])==30
    assert reference['ancestry']['update']==832 and reference['ancestry']['run']=='all-W-init10'
    assert all(not path.endswith('.pt') for path in reference['files'])


def test_source_bound_preparation_refuses_missing_canonical_parents(tmp_path):
    p=driver()
    with pytest.raises((ValueError,FileNotFoundError)):
        p.prepare_mask(tmp_path/'missing',commit='a'*40,chunk_size=1,registry_paths=[])


def test_hbank_uses_both_streams_and_unpadded_token_weights():
    p=driver();model,support,_=tiny()
    rows=[dict(instance_id='one',split='train',condition='H',streams={
        'clean':dict(tokens=[1,2,3],readout=2),'corrupt':dict(tokens=[3,2,1],readout=2)})]
    called=[]
    bank=p.collect_h_bank(model,rows,support.candidates,guard=lambda:called.append(True))
    assert bank['n_tokens']==6 and bank['n_instances']==1 and len(bank['values'])==2 and called
    assert all(torch.isfinite(torch.tensor(r['value'])).all() for r in bank['values'])


def test_atomic_driver_boundary_rejects_changed_rng_bytes(tmp_path):
    p=driver();model,support,(ds,ins,_)=tiny();opt=torch.optim.Adam(support.parameters(),lr=.01)
    state=core.make_checkpoint(model,support,opt,ds,ins,identity={},update=0)
    p._publish_boundary(tmp_path/'boundary',state,{'identity':{},'validations':[]})
    restored,driver_state=p._read_boundary(tmp_path/'boundary')
    assert torch.equal(restored['rng']['cpu'],state['rng']['cpu'])
    target=tmp_path/'boundary/core/state.json';target.write_text(target.read_text().replace('bytes','altered_bytes',1))
    with pytest.raises(ValueError):p._read_boundary(tmp_path/'boundary')


def test_positive_readout_recovery_handles_different_prompt_widths():
    p=driver();model,support,_=tiny()
    model.eval()
    ids=torch.tensor([[1,2,3]]);donor=torch.tensor([[4,5,6,7]])
    receipt=p.positive_readout(model,ids,torch.ones_like(ids),donor,torch.ones_like(donor))
    assert receipt['passed'] and receipt['max_abs_logit_error']<1e-5


def test_validation_rejects_changed_condition_membership_and_per_stream_gap():
    p=driver();rows=[]
    for condition,margin in [('D',3.),('H',1.),('I',3.),('user_neutral',1.),('F',1.)]:
        for stream in ('clean','corrupt'):
            rows.append(dict(instance_id='one',stream=stream,condition=condition,intact_margin=margin,patched_margin=margin,
                intact_accuracy=1.,patched_accuracy=1.))
    rows.append(dict(rows[0],condition='IOI'))
    changed=copy.deepcopy(rows);changed[0]['instance_id']='different'
    with pytest.raises(ValueError):p.validation_gates(changed,epsilon=1e-6)
    changed=copy.deepcopy(rows);changed[0]['intact_margin']=0
    with pytest.raises(ValueError):p.validation_gates(changed,epsilon=1e-6)


def test_actual_module_dry_run_is_no_write_no_weight(tmp_path):
    import sys
    result=subprocess.run([sys.executable,'-m','component_analysis.a3_mask_pipeline','--dry-run','--stage','fit',
        '--design',str(tmp_path/'missing'),'--commit','a'*40,'--work-dir',str(tmp_path/'output')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert '"weights_loaded": false' in result.stdout and not (tmp_path/'output').exists()


def toy_design(model):
    """Explicit nonproduction paired task; labels expose a positive intact gap."""
    p=driver()
    with p.binary_mode(model,[]),torch.no_grad():
        d=p._single_logits(model,torch.tensor([[1,2,3]]),torch.ones(1,3,dtype=torch.long))[0]
        h=p._single_logits(model,torch.tensor([[4,5,6]]),torch.ones(1,3,dtype=torch.long))[0]
    delta=d-h;opposite=int(delta.argmax());honest=int(delta.argmin())
    design=dict(injected=True,tasks={},access_rows={},semantic_twin_maps={})
    for task in ('far_v2','ser_v2','sdr_v2'):
        design['tasks'][task]=dict(fit_ids=['fit'],selection_ids=['val'],assessment_ids=['test'])
        design['access_rows'][task]=[];design['semantic_twin_maps'][task]=[]
        for split,rid in [('train','fit'),('validation','val'),('test','test')]:
            for condition in ('D','I','H','F','user_neutral'):
                neutral=condition in ('H','user_neutral','F');tokens=[4,5,6] if neutral else [1,2,3]
                streams={stream:dict(tokens=tokens,readout=2,prompt='toy '+condition,layout={'role_spans':[['text',0,3]],'content_spans':[['text',0,3]]},
                    opposite_token=opposite,honest_token=honest,expected_token=honest if neutral else opposite,user_request_span=[1,2],
                    honest_word='a',opposite_word='b',honest_item='a') for stream in ('clean','corrupt')}
                design['access_rows'][task].append(dict(task=task,condition=condition,instance_id=rid,split=split,streams=streams,
                    source_hash='f'*64,pressure_text='same toy wording',pressure_id='toy',template_variant='toy',request_text='toy',
                    item_pair='a/b',designation_polarity='x',item_polarity=1,pressure_slot=0,request_id='toy'))
            for condition,peer in [('D','H'),('I','user_neutral')]:
                for stream in ('clean','corrupt'):
                    design['semantic_twin_maps'][task].append(dict(instance_id=rid,recipient_condition=condition,donor_condition=peer,stream=stream,
                        supported=True,recipient_positions=[0,1,2],donor_positions=[0,1,2]))
    def utility(task,rid,split):
        record=dict(tokens=[1,2,3],readout=2,layout={'role_spans':[['text',0,3]],'content_spans':[['text',0,3]]})
        return dict(instance_id=rid,source_id=rid,question_hash=rid,gold_letter='B' if rid.endswith('2') else 'A',task=task,condition=task.upper(),split=split,analysis_split=split,source_hash='f'*64,
            expected_token=honest,honest_token=honest,opposite_token=opposite,choice_tokens=[honest]+[i for i in range(17) if i!=honest][:3],
            streams={'clean':record,'corrupt':dict(record,tokens=[4,5,6])})
    from component_analysis.ladder_tasks import ioi_item_swap_maps,mmlu_calibration_maps
    design['ioi_validation']=[utility('ioi','iv','validation')]
    design['mmlu_validation']=[utility('mmlu','mv','validation'),utility('mmlu','mv2','validation')]
    design['ioi_validation_maps']=ioi_item_swap_maps(design['ioi_validation'])
    design['mmlu_validation_maps']=mmlu_calibration_maps(design['mmlu_validation'])
    design['utility']={'ioi':[utility('ioi','it','test')],'mmlu':[utility('mmlu','mt','test'),utility('mmlu','mt2','test')]}
    design['utility']['ioi_maps']=ioi_item_swap_maps(design['utility']['ioi'])
    design['utility']['mmlu_maps']=mmlu_calibration_maps(design['utility']['mmlu'])
    return design


def test_frozen_widths_include_donors_and_preserve_readouts():
    p=driver();model,support,_=tiny();design=toy_design(model)
    widths=p.execution_widths(design,hbank_rows={})
    execution=p.execution_design(design,widths)
    chunks=p.source_chunks(execution,'far_v2','train','D',chunk_size=1,device='cpu')
    assert chunks[0].payload['input_ids'].shape[-1]==4
    assert chunks[0].payload['attention_mask'].tolist()==[[[True,True,True,False]]*2]
    assert chunks[0].token_counts.tolist()==[[3,3]]
    assert design['access_rows']['far_v2'][0]['streams']['clean']['tokens']==[1,2,3]


def test_actual_validation_only_pilot_covers_all_classes_and_is_nonfinal(tmp_path):
    p=driver();model,support,_=tiny();design=toy_design(model)
    widths=p.execution_widths(design,hbank_rows={})
    prepared=dict(injected=True,identity={'injected':True,'numeric_profile':{'hardware':'injected_cpu','dtype':'float32','backend':'eager'}},
        candidates=[list(k) for k in support.candidates],chunk_size=1,updates=200,validation_every=20,widths=widths)
    receipt=p.mask_pilot(model,design,prepared,output=tmp_path,guard=lambda:{},injected=True)
    assert receipt['complete'] and receipt['timing_only'] and not receipt['final'] and receipt['injected']
    assert set(receipt['measurements'])=={'base_proof','targets','update','validation','binary_parity','checkpoint','selection','guard_initial','guard',
        'H_bank:far_v2','H_bank:ser_v2','H_bank:sdr_v2','assessment:far_v2','assessment:ser_v2','assessment:sdr_v2'}
    assert all(a['source_split']=='validation' for a in receipt['arm_measurements'])
    assert not (tmp_path/'selected').exists()
    with pytest.raises(ValueError):p.train_constrained(model,design,prepared,seed=42,arm='constrained',checkpoint_dir=tmp_path/'fit',guard=lambda:{})


def cost_fixture():
    from component_analysis import a3_mask_workload as w
    profile={'hardware':'H200','dtype':'bfloat16','backend':'sdpa','vocab_size':17}
    identity={'commit':'a'*40,'numeric_profile':profile}
    design={'tasks':{t:dict(fit_ids=['fit'],selection_ids=['val'],assessment_ids=['test']) for t in ('far_v2','ser_v2','sdr_v2')},
        'ioi_validation':[{'instance_id':'iv'}],'mmlu_validation':[{'instance_id':'mv'}],
        'utility':{'ioi':[{'instance_id':'it'}],'mmlu':[{'instance_id':'mt'}]}}
    widths={t:{c:4 for c in ('D','I','H','F','user_neutral')} for t in design['tasks']};widths.update(ioi=4,mmlu=4)
    inventory=w.build_inventory(design,identity=identity,chunk_size=1,finish_reserve_seconds=1,widths=widths,new30={'status':'available'})
    classes=['base_proof','targets','update','validation','binary_parity','checkpoint','selection','guard_initial','guard']
    classes += [kind+':'+task for kind in ('H_bank','assessment') for task in design['tasks']]
    measurement=dict(seconds=1e-6,rows=1,numeric_profile=profile,widths=widths,source_split='validation',scope={})
    receipt=dict(kind='a3_mask_pilot_v2',base_identity='f'*64,identity=identity,complete=True,exit_code=0,hardware='NVIDIA H200',injected=False,
        arms=['constrained','unconstrained'],arm_measurements=[dict(arm=a,source_split='validation',purpose='validation_timing',chunks=1) for a in ('constrained','unconstrained')],
        measurements={c:[copy.deepcopy(measurement)] for c in classes},startup_seconds=0,validation_measured=True,two_D_passes_measured=True,
        timing_only=True,final=False,purpose='validation_timing',widths=widths,host_peak_bytes=1,peak_memory_bytes=1,boundary_bytes=100,
        gpu_capacity_bytes=10**12,target_inventory_sha256=inventory['inventory_sha256'],reservation_id='pilot',allocation_job_id='job',
        output_dir='/tmp/mask-cost-fixture',pilot_inventory_sha256='e'*64)
    ledger=dict(kind='a3_root_ledger_snapshot_v1',root_supplied=True,snapshot_sha256='f'*64,current_snapshot_sha256='f'*64,
        age_seconds=0,max_age_seconds=900,expected_identity=identity,entries=[dict(id='pilot',phase='M1',subphase='masks',state='completed',
            reserved_gpu_hours=.75,actual_gpu_hours=.01,inventory_sha256='e'*64,
            actual_entry={'job_id':'job','source_commit':'a'*40,'output_dir':'/tmp/mask-cost-fixture'})],expected_entry_ids=['pilot'],contingency_gpu_hours=6,
        storage_capacities={tier:dict(pool=tier,available_bytes=10**12) for tier in ('host_ram','cache_disk','output_disk','scratch_disk')})
    return inventory,receipt,ledger


def test_cost_uses_additive_m1_and_m5_caps_and_full_target_capacity():
    from component_analysis import a3_mask_workload as w
    inventory,receipt,ledger=cost_fixture()
    result=w.project_cost([receipt],inventory,ledger)
    assert not result['execution_authorized'] and result['counts']['update']==1200
    assert result['storage_admission']['required']['output_disk']>0
    bad=copy.deepcopy(ledger);bad['storage_capacities']['output_disk']['available_bytes']=1
    with pytest.raises(ValueError):w.project_cost([receipt],inventory,bad)
    failed=copy.deepcopy(ledger);failed['entries'][0]['state']='failed'
    with pytest.raises(ValueError):w.project_cost([receipt],inventory,failed)
    missing=copy.deepcopy(receipt);del missing['measurements']['assessment:ser_v2']
    with pytest.raises(ValueError):w.project_cost([missing],inventory,ledger)
    changed=copy.deepcopy(receipt);changed['widths']['far_v2']['I']=5
    with pytest.raises(ValueError):w.project_cost([changed],inventory,ledger)
    injected=copy.deepcopy(receipt);injected['injected']=True
    with pytest.raises(ValueError):w.project_cost([injected],inventory,ledger)


def test_inventory_binds_h_bank_and_all_native_adapter_classes():
    from component_analysis import a3_mask_workload as w
    inventory,receipt,ledger=cost_fixture()
    assert inventory['counts']['assessment:far_v2']==123 and inventory['counts']['assessment:ser_v2']==122
    assert inventory['counts']['validation']==60 and inventory['counts']['selection']==6
    assert inventory['storage_requirements']['tiers']['host_ram']>0


def test_inventory_storage_bound_survives_completed_json_roundtrip():
    import json
    from component_analysis import a3_mask_workload as w
    inventory,_,_=cost_fixture()
    w.validate_inventory(json.loads(json.dumps(inventory)))


def test_full_native_training_freezes_complete_history_without_test_access(tmp_path):
    p=driver();model,support,_=tiny();design=toy_design(model)
    for task in design['access_rows']:
        design['access_rows'][task]=[r for r in design['access_rows'][task] if r['split']!='test']
    widths=p.execution_widths(design,hbank_rows={})
    prepared=dict(injected=True,identity={'injected':True,'source':'tiny-native'},candidates=[list(k) for k in support.candidates],
        chunk_size=1,updates=200,validation_every=20,widths=widths)
    result=p.train_constrained(model,design,prepared,seed=42,arm='constrained',checkpoint_dir=tmp_path/'run',guard=lambda:{})
    assert result['completed_updates']==200 and not result['assessment_accessed']
    assert len(p.frozen_validation_history(result))==10
    assert (tmp_path/'run/update-000200').is_dir()
    assert len(list((tmp_path/'run/validation').iterdir()))==10
    changed=copy.deepcopy(result);changed['completed_checkpoint_sha256']='0'*64
    with pytest.raises(ValueError):p.frozen_validation_history(changed)


def test_interrupted_publication_reuses_only_identical_boundary_and_validation(tmp_path):
    p=driver();model,support,(ds,ins,_)=tiny();optimizer=torch.optim.Adam(support.parameters(),lr=.01)
    state=core.make_checkpoint(model,support,optimizer,ds,ins,identity={'run':'tiny'},update=0)
    metadata={'identity':{'run':'tiny'},'validations':[]}
    p._publish_boundary(tmp_path/'boundary',state,metadata)
    p._publish_boundary(tmp_path/'boundary',state,metadata)
    with pytest.raises(ValueError):p._publish_boundary(tmp_path/'boundary',state,dict(metadata,validations=[{}]))
    evidence={'kind':'a3_mask_validation_v1','identity':{'run':'tiny'},'result':{'rows':[]}}
    p.publish_validation(tmp_path/'validation',evidence)
    p.publish_validation(tmp_path/'validation',evidence)
    with pytest.raises(ValueError):p.publish_validation(tmp_path/'validation',dict(evidence,result={'rows':[{}]}))


def test_genuine_completed_root_authority_context_and_live_failure(tmp_path):
    import json
    import time
    from types import SimpleNamespace
    from component_analysis import a3_direction_runtime as authority
    p=driver();inventory,_,_=cost_fixture();identity=inventory['identity']
    root=tmp_path/'output';root.mkdir()
    actual=dict(id='mask-r1',job_id='100',cluster='injected-cpu',account='test',partition='test',gpus=1,
        requested_minutes=12,reserved_gpu_hours=.2,actual_seconds=None,source_commit=identity['commit'],output_dir=str(root),
        status='running',manifest_hash=inventory['inventory_sha256'])
    live=tmp_path/'ledger.json';live.write_text(json.dumps({'reservations':[actual]}))
    original=tmp_path/'original-ledger.json';original.write_bytes(live.read_bytes())
    upper=tmp_path/'upper';authority.publish_object(upper,inventory)
    admission=dict(kind='a3_root_fit_admission_v1',id='mask-envelope',identity=identity,
        upper_inventory_sha256=inventory['inventory_sha256'],max_gpu_hours=1.,reservation_ids=['mask-r1'])
    admission['admission_sha256']=authority.workload.digest(admission)
    admission_path=tmp_path/'admission';authority.publish_object(admission_path,admission)
    mapping=dict(kind='a3_root_ledger_mapping_v1',ledger_path=str(live),ledger_snapshot_path=str(original),
        ledger_sha256=authority.common.file_hash(original),expected_entry_ids=['mask-r1'],
        entries=[dict(reservation_id='mask-r1',experiment='A3',phase='M5',subphase='masks',
            inventory_sha256=inventory['inventory_sha256'],original_reserved_gpu_hours=.2,actual_entry=actual,
            reservation_lineage=dict(admission_id='mask-envelope',admission_sha256=admission['admission_sha256'],
                max_gpu_hours=1.,upper_inventory_sha256=inventory['inventory_sha256'],reserved_gpu_hours=.2))],
        original_admission_paths=[str(admission_path)],storage_capacities={'host_ram':{'pool':'ram','available_bytes':10**12}},
        contingency_gpu_hours=6,max_age_seconds=900)
    mapping_path=tmp_path/'mapping';authority.publish_object(mapping_path,mapping)
    reservation=dict(kind='a3_root_execution_reservation_v1',identity=identity,inventory_sha256=inventory['inventory_sha256'],
        reservation_id='mask-r1',actual_entry={key:actual[key] for key in authority.RESERVATION_FIELDS},
        admission_path=str(admission_path),admission_reference=authority.object_reference(admission_path),
        admission_sha256=admission['admission_sha256'],upper_inventory_path=str(upper),end_time_unix=time.time()+600,minimum_shard_seconds=1)
    allocation_start=int(time.time())-1
    allocation=dict(kind='a3_injected_slurm_allocation_v1',injected=True,job_id='100',cluster='injected-cpu',account='test',
        partition='test',gpus=1,state='RUNNING',start_time_unix=allocation_start,end_time_unix=allocation_start+720,time_limit_seconds=720)
    allocation_path=tmp_path/'allocation';authority.publish_object(allocation_path,allocation)
    reservation['injected_allocation_path']=str(allocation_path)
    reservation['end_time_unix']=time.time()-100  # submit-time deadlines never authorize or block a queued job
    reservation_path=tmp_path/'reservation';authority.publish_object(reservation_path,reservation)
    args=SimpleNamespace(stage='fit',seed=42,arm='constrained',task=None,group=None,ledger_snapshot=str(mapping_path),
        reservation=str(reservation_path),inventory=str(upper),work_dir=str(root),admission=str(admission_path))
    first=p.mask_reservation(args,inventory,injected=True)
    second=p.mask_reservation(args,inventory,injected=True)
    assert first['original_reserved_gpu_hours']==second['original_reserved_gpu_hours']==.2
    assert args._mask_authority_context is not None
    changed=dict(actual,status='failed',actual_seconds=1)
    live.write_text(json.dumps({'reservations':[changed]}))
    with pytest.raises(ValueError):p.mask_reservation(args,inventory,injected=True)


def test_validation_strict_five_percent_boundary_does_not_round_into_pass():
    p=driver();rows=[]
    for condition,base,patched in [('D',3.,2.),('H',1.,1.),('I',3.,2.6),('user_neutral',1.,1.),('F',1.,1.),('IOI',1.,1.)]:
        for stream in ('clean','corrupt'):
            rows.append(dict(instance_id='one',stream=stream,condition=condition,intact_margin=base,patched_margin=patched,
                intact_accuracy=.55 if condition=='H' else 1.,patched_accuracy=.6 if condition=='H' else 1.))
    assert not p.validation_gates(rows,epsilon=1e-6)['eligible']


def test_changed_native_model_and_malformed_rng_reject_before_resume(tmp_path):
    p=driver();model,support,(ds,ins,_)=tiny();optimizer=torch.optim.Adam(support.parameters(),lr=.01)
    state=core.make_checkpoint(model,support,optimizer,ds,ins,identity={},update=0)
    bad=copy.deepcopy(state);bad['rng']['cpu']=torch.zeros(5,dtype=torch.uint8)
    p.write_checkpoint(tmp_path/'bad-rng',bad)
    with pytest.raises(ValueError,match='RNG'):p.read_checkpoint(tmp_path/'bad-rng')
    with torch.no_grad():model.model.norm.weight[0]+=1
    with pytest.raises(ValueError):core.restore_checkpoint(state,model,support,optimizer,ds,ins,identity={})


def test_changed_protocol_rejects_before_any_parent_or_model_access():
    from types import SimpleNamespace
    p=driver()
    prepared=dict(kind='a3_mask_prepared_v1',injected=False,candidates=[['head',17,24]],chunk_size=1,seeds=[42,1,123],
        arms=['constrained','unconstrained'],updates=200,validation_every=20,validation_donors='opposite designation',root_ruling={},
        random_controls={'count':19},timing_protocol={},new30={'status':'missing_comparison'},hbank_sources={},widths={})
    prepared['identity']={'mask_protocol_sha256':p.digest(p.mask_protocol(prepared))}
    prepared['random_controls']['count']=18
    with pytest.raises(ValueError,match='frozen mask'):
        p._live_mask(prepared,SimpleNamespace())


def test_actual_native_assessment_has_complete_controls_floors_and_source_failures(tmp_path):
    p=driver();model,support,_=tiny();design=toy_design(model)
    widths=p.execution_widths(design,hbank_rows={});design=p.execution_design(design,widths)
    prepared=dict(injected=True,identity={'injected':True,'source':'tiny-assessment'},candidates=[list(k) for k in support.candidates],widths=widths,hbank_sources={})
    rows=[r for r in design['access_rows']['far_v2'] if r['condition']=='H' and r['split']=='train']
    bank_path=tmp_path/'H-bank'
    prepared['hbank_sources']['far_v2']={'ids':['fit'],'rows_sha256':p.digest(rows),'n_tokens':6}
    bank=p.collect_publish_bank(model,rows,support.candidates,guard=lambda:{},prepared=prepared,task='far_v2',
        output=bank_path,purpose='scientific_H_bank')
    prepared['hbank_sources']['far_v2']={'ids':['fit'],'rows_sha256':p.digest(rows),'n_tokens':6}
    removed=[list(k) for k in support.candidates]
    result=p.assess_group(model,design,prepared,task='far_v2',name='tiny-selected',removed=removed,bank=bank,parent=None,guard=lambda:{})
    from component_analysis.a3_direction_runtime import object_reference
    result['H_bank_reference']=object_reference(bank_path)
    result['run_manifest_reference']=p.publish_run_manifest(tmp_path/'runs',prepared,stage='assess',evidence={'rows':len(result['rows'])})
    assert p.validate_assessment_result(result,design,prepared,task='far_v2',name='tiny-selected',removed=removed)['complete']
    assert {r['operation'] for r in result['rows'] if r['condition']=='MMLU'}=={'zero','h_mean','self_replay','empty'}
    missing=copy.deepcopy(result);missing['rows'].pop()
    with pytest.raises(ValueError):p.validate_assessment_result(missing,design,prepared,task='far_v2',name='tiny-selected',removed=removed)
    missing=copy.deepcopy(result);missing['positive_controls'].pop()
    with pytest.raises(ValueError):p.validate_assessment_result(missing,design,prepared,task='far_v2',name='tiny-selected',removed=removed)
    wrong=copy.deepcopy(result);wrong['split']='validation'
    with pytest.raises(ValueError):p.validate_assessment_result(wrong,design,prepared,task='far_v2',name='tiny-selected',removed=removed)


def test_update_forecast_accounts_for_reviewed_whole_cohort_hash_per_callback():
    from component_analysis import a3_mask_workload as w
    inventory,receipt,ledger=cost_fixture()
    baseline=w.project_cost([receipt],inventory,ledger)['operation_seconds']['update']
    design={'tasks':copy.deepcopy(inventory['scope']['tasks']),
        'ioi_validation':[{'instance_id':i} for i in inventory['scope']['ioi_validation']],
        'mmlu_validation':[{'instance_id':i} for i in inventory['scope']['mmlu_validation']],
        'utility':{task:[{'instance_id':i} for i in inventory['scope'][task]] for task in ('ioi','mmlu')}}
    design['tasks']['far_v2']['fit_ids']=['fit','fit2']
    larger=w.build_inventory(design,identity=inventory['identity'],chunk_size=1,finish_reserve_seconds=1,widths=inventory['scope']['widths'],new30=inventory['scope']['new30_reference'])
    receipt['target_inventory_sha256']=larger['inventory_sha256']
    estimate=w.project_cost([receipt],larger,ledger)['operation_seconds']['update']
    assert estimate==pytest.approx(4*baseline)


def test_raw_target_choices_do_not_relabel_fractional_margin_removal():
    p=driver();rows=[]
    for condition in ('D','I','H','F','user_neutral'):
        rows.append(dict(condition=condition,operation='item_swap',supported=True,opposite_token=7,
            intact_target_choice=1.,patched_target_choice=1.,intact_native_margin=3.,patched_native_margin=2.,
            intact_argmax=7,patched_argmax=7,intact_native_argmax=7,patched_native_argmax=7))
    rates=p.raw_choice_rates(rows,operation='item_swap')
    assert rates['D']['intact_opposite_over_honest']==rates['D']['patched_opposite_over_honest']==1.
    assert rates['D']['patched_native_full_vocab_opposite']==1.


def test_actual_a1_parent_schema_derives_masks_without_serialized_attention():
    from component_analysis import ladder_pipeline as ladder,ladder_design
    p=driver();path=Path(__file__).resolve().parents[1]/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json'
    parent=ladder.read_artifact(path);conditions=parent['rows']['far_v2']
    indexed={c:{r['instance_id']:r for r in values if r['split']=='train'} for c,values in conditions.items()}
    rid=sorted(set.intersection(*(set(rows) for rows in indexed.values())))[0]
    rows=[copy.deepcopy(indexed[c][rid]) for c in indexed]
    assert all('attention_mask' not in record for row in rows for record in row['streams'].values())
    maps=[]
    for condition in ('D','I'):
        recipient=indexed[condition][rid]
        for stream in ('clean','corrupt'):
            mapping=ladder_design.donor_plan(recipient,rows,operation='h_twin',stream=stream,seed=1)
            assert mapping['supported']
            maps.append(dict(mapping,instance_id=rid,stream=stream))
    design=dict(tasks={'far_v2':dict(fit_ids=[rid],selection_ids=[],assessment_ids=[])},
        access_rows={'far_v2':rows},semantic_twin_maps={'far_v2':maps})
    for condition in ('D','I'):
        chunk=p.source_chunks(design,'far_v2','train',condition,chunk_size=1,device='cpu')[0]
        lengths=[len(indexed[condition][rid]['streams'][s]['tokens']) for s in ('clean','corrupt')]
        assert chunk.token_counts.tolist()==[lengths]
        assert chunk.payload['attention_mask'].sum(-1).tolist()==[lengths]
    damaged=copy.deepcopy(design)
    next(r for r in damaged['access_rows']['far_v2'] if r['condition']=='D')['streams']['clean']['attention_mask']=[0]
    with pytest.raises(ValueError,match='attention|mask'):
        p.source_chunks(damaged,'far_v2','train','D',chunk_size=1,device='cpu')


def test_missing_reference_blocks_complete_phase_cost_instead_of_omitting_comparison():
    from component_analysis import a3_mask_workload as w
    inventory,receipt,ledger=cost_fixture()
    inventory['scope']['new30_reference']={'status':'missing_comparison'}
    inventory['storage_requirements']=w.storage_requirements(inventory)
    inventory['inventory_sha256']=w.inventory_digest(inventory)
    receipt['target_inventory_sha256']=inventory['inventory_sha256']
    with pytest.raises(ValueError,match='reference|comparison'):
        w.project_cost([receipt],inventory,ledger)


def test_wrapper_clean_cluster_cache_resolves_pinned_metadata_offline(tmp_path):
    import json
    import os
    import sys
    import shlex
    root=Path(__file__).resolve().parents[1]
    probe=tmp_path/'cache_probe.py'
    probe.write_text("""import json, os
from transformers.utils.hub import cached_file
model='meta-llama/Llama-3.1-8B-Instruct'
revision='0e9e39f249a16976918f6564b8830bc894c89659'
assert os.environ['HF_HOME']==os.environ['DC_HF_HOME']
assert os.environ['HF_HUB_CACHE']==os.environ['DC_HF_HOME']
assert os.environ['DC_CLUSTER']=='delta'
assert all(os.environ[k]=='1' for k in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE'))
assert os.path.isfile(os.environ['SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE'])
paths={name:cached_file(model,name,revision=revision,local_files_only=True) for name in ('config.json','model.safetensors.index.json')}
from pathlib import Path
index=json.loads(Path(paths['model.safetensors.index.json']).read_text())
assert all((Path(paths['model.safetensors.index.json']).parent/name).is_file() for name in set(index['weight_map'].values()))
print(json.dumps(dict(cache=os.environ['HF_HUB_CACHE'],metadata=paths,weights_loaded=False)))
""")
    executable=tmp_path/'cache_probe.sh'
    executable.write_text('#!/usr/bin/env bash\nexec '+shlex.quote(sys.executable)+' -B '+shlex.quote(str(probe))+' "$@"\n')
    executable.chmod(0o700)
    environ=dict(os.environ)
    for key in ('HF_HOME','DC_HF_HOME','HF_HUB_CACHE','TRANSFORMERS_CACHE','HUGGINGFACE_HUB_CACHE','DC_CLUSTER','DC_CLUSTER_NAME'):
        environ.pop(key,None)
    environ['A3_MASK_PYTHON']=str(executable)
    result=subprocess.run(['bash',str(root/'scripts/jobs/specificity_a3_mask.sh'),'--dry-run','--stage','pilot',
        '--design',str(tmp_path/'missing'),'--commit','a'*40,'--work-dir',str(tmp_path/'output')],
        env=environ,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    evidence=json.loads(result.stdout.splitlines()[-1])
    assert evidence['weights_loaded'] is False and all(Path(p).is_file() for p in evidence['metadata'].values())
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('mode',['slurm_chdir','explicit_root','wrong_cwd','wrong_override','stale_copy'])
def test_spooled_mask_wrapper_authenticates_worktree_before_dispatch(tmp_path,mode):
    import json
    import os
    import sys
    import shutil
    root=Path(__file__).resolve().parents[1]
    spooled=tmp_path/'spool/job123/slurm_script';spooled.parent.mkdir(parents=True)
    shutil.copy2(root/'scripts/jobs/specificity_a3_mask.sh',spooled)
    if mode=='stale_copy':spooled.write_text(spooled.read_text()+'# stale submitted script\n')
    environ=dict(os.environ,SLURM_JOB_ID='simulated-dry-run',A3_MASK_PYTHON=sys.executable)
    environ.pop('SPECIFICITY_A3_MASK_REPO_ROOT',None)
    # SLURM_SUBMIT_DIR does not override the actual --chdir execution directory.
    environ['SLURM_SUBMIT_DIR']=str(root)
    cwd=root if mode in ('slurm_chdir','stale_copy') else tmp_path
    if mode=='explicit_root':environ['SPECIFICITY_A3_MASK_REPO_ROOT']=str(root)
    if mode=='wrong_override':environ['SPECIFICITY_A3_MASK_REPO_ROOT']=str(tmp_path)
    result=subprocess.run(['bash',str(spooled),'--dry-run','--stage','pilot','--design',str(tmp_path/'missing'),
        '--commit','a'*40,'--work-dir',str(tmp_path/'output')],cwd=cwd,env=environ,capture_output=True,text=True)
    if mode in ('slurm_chdir','explicit_root'):
        assert result.returncode==0,result.stderr
        evidence=json.loads(result.stdout.splitlines()[-1])
        assert evidence['weights_loaded'] is False and evidence['execution_authorized'] is False
    else:
        assert result.returncode!=0 and 'worktree' in result.stderr
    assert not (tmp_path/'output').exists()


def bank_review_case(tmp_path):
    p=driver();model,support,_=tiny();design=toy_design(model)
    widths=p.execution_widths(design,hbank_rows={});design=p.execution_design(design,widths)
    geometry=dict(num_layers=model.config.num_hidden_layers,num_heads=model.config.num_attention_heads,
        hidden_size=model.config.hidden_size,intermediate_size=model.config.intermediate_size,vocab_size=model.config.vocab_size)
    prepared=dict(injected=True,identity={'injected':True,'source':'bank-review108','model_geometry':geometry},
        candidates=[list(k) for k in support.candidates],new30={'status':'missing_comparison'},widths=widths,hbank_sources={})
    rows=[r for r in design['access_rows']['far_v2'] if r['condition']=='H' and r['split']=='train']
    prepared['hbank_sources']['far_v2']=dict(ids=[r['instance_id'] for r in rows],rows_sha256=p.digest(rows),n_tokens=6)
    bank=p.collect_publish_bank(model,rows,support.candidates,guard=lambda:{},prepared=prepared,task='far_v2',
        output=tmp_path/'valid-bank',purpose='scientific_H_bank')
    return p,model,support,design,prepared,bank


@pytest.mark.parametrize('kind',['head','mlp'])
@pytest.mark.parametrize('bad',['scalar','singleton','nested','short','long','nan','infinity','boolean'])
def test_exported_h_mean_rejects_broadcastable_or_nonfinite_vectors(tmp_path,kind,bad):
    p,model,support,design,prepared,bank=bank_review_case(tmp_path)
    values={tuple(v['key']):copy.deepcopy(v['value']) for v in bank['values']}
    key=next(k for k in values if k[0]==kind);width=len(values[key])
    malformed={'scalar':0.,'singleton':[0.],'nested':[[0.]*width],'short':[0.]*(width-1),
        'long':[0.]*(width+1),'nan':[float('nan')]*width,'infinity':[float('inf')]*width,'boolean':[False]*width}
    values[key]=malformed[bad]
    chunk=p.source_chunks(design,'far_v2','test','D',chunk_size=1,device='cpu',fitting=False,donor='opposite')[0]
    with pytest.raises(ValueError,match='bank|vector|finite'):
        p.exported_forward(model,chunk,[key],operation='h_mean',mean_bank=values)


@pytest.mark.parametrize('damage',['singleton','duplicate','missing','extra','negative_layer','outside_layer','outside_head',
    'mlp_coordinate','wrong_kind','geometry','profile','runtime','base','instances','tokens','domain','source_ids'])
def test_assessment_rejects_invalid_bank_before_any_forward(tmp_path,monkeypatch,damage):
    p,model,support,design,prepared,bank=bank_review_case(tmp_path)
    broken=copy.deepcopy(bank)
    if damage=='singleton':broken['values'][0]['value']=[0.]
    elif damage=='duplicate':broken['values'].append(copy.deepcopy(broken['values'][0]))
    elif damage=='missing':broken['values'].pop()
    elif damage=='extra':broken['values'].append(dict(key=['head',0,1],value=[0.]*4))
    elif damage=='negative_layer':broken['values'][0]['key'][1]=-1
    elif damage=='outside_layer':broken['values'][0]['key'][1]=1
    elif damage=='outside_head':broken['values'][0]['key'][2]=2
    elif damage=='mlp_coordinate':next(v for v in broken['values'] if v['key'][0]=='mlp')['key'][2]=1
    elif damage=='wrong_kind':broken['values'][0]['key'][0]='mlp_output'
    elif damage=='geometry':broken['model_geometry']['hidden_size']=2
    elif damage=='profile':broken['execution_geometry']['padded_width']+=1
    elif damage=='runtime':broken['runtime_identity']='0'*64
    elif damage=='base':broken['base_identity']='0'*64
    elif damage=='instances':broken['n_instances']+=1
    elif damage=='tokens':broken['n_tokens']+=1
    elif damage=='domain':broken['source_rows_sha256']='0'*64
    elif damage=='source_ids':broken['source_ids']=['another-source']
    monkeypatch.setattr(p,'_single_logits',lambda *args,**kwargs:pytest.fail('forward before typed bank admission'))
    with pytest.raises(ValueError,match='bank|geometry|support|source|profile'):
        p.assess_group(model,design,prepared,task='far_v2',name='invalid-bank',removed=[['head',0,0]],
            bank=broken,parent=None,guard=lambda:{})


def test_final_intake_rejects_completed_singleton_bank_and_changed_geometry_proof(tmp_path):
    p,model,support,design,prepared,bank=bank_review_case(tmp_path)
    removed=[list(k) for k in support.candidates]
    result=p.assess_group(model,design,prepared,task='far_v2',name='bank-review108',removed=removed,bank=bank,parent=None,guard=lambda:{})
    from component_analysis.a3_direction_runtime import object_reference,publish_object
    result['run_manifest_reference']=p.publish_run_manifest(tmp_path/'runs',prepared,stage='assess',evidence={'rows':len(result['rows'])})
    result['H_bank_reference']=object_reference(tmp_path/'valid-bank')
    p.validate_assessment_result(result,design,prepared,task='far_v2',name='bank-review108',removed=removed)
    for label,mutate in [('singleton',lambda b:[v.update(value=[0.]) for v in b['values']]),
            ('geometry',lambda b:b['model_geometry'].update(hidden_size=2))]:
        broken=copy.deepcopy(bank);mutate(broken);path=tmp_path/('bad-'+label);publish_object(path,broken)
        changed=copy.deepcopy(result);changed['H_bank_reference']=object_reference(path)
        with pytest.raises(ValueError,match='bank|geometry|vector'):
            p.validate_assessment_result(changed,design,prepared,task='far_v2',name='bank-review108',removed=removed)


def test_valid_bank_preserves_zero_removal_group(tmp_path):
    p,model,support,design,prepared,bank=bank_review_case(tmp_path)
    result=p.assess_group(model,design,prepared,task='far_v2',name='intact',removed=[],bank=bank,parent=None,guard=lambda:{})
    assert result['complete'] and all(r['intact_margin']==r['patched_margin'] for r in result['rows'] if r['supported'])


@pytest.mark.parametrize('change',['geometry','runtime','base'])
def test_bank_reuse_checks_actual_current_model_before_forward(tmp_path,monkeypatch,change):
    p,model,support,design,prepared,bank=bank_review_case(tmp_path)
    if change=='geometry':model.config.hidden_size=16
    elif change=='runtime':model.model.norm.variance_epsilon*=2
    else:
        with torch.no_grad():model.model.norm.weight[0]+=1
    monkeypatch.setattr(p,'_single_logits',lambda *args,**kwargs:pytest.fail('forward with changed bank model'))
    with pytest.raises(ValueError,match='bank|geometry|profile|proof'):
        p.assess_group(model,design,prepared,task='far_v2',name='changed-model',removed=[],bank=bank,parent=None,guard=lambda:{})


def test_cpu_bank_geometry_proof_cannot_redeclare_native_preparation():
    p=driver();geometry=copy.deepcopy(p.NATIVE_BANK_GEOMETRY)
    prepared={'injected':False,'identity':{'model_geometry':geometry,'numeric_profile':{'dtype':'bfloat16'}}}
    proof=dict(model_geometry=copy.deepcopy(geometry),runtime_identity='a'*64,base_identity='b'*64,dtype='torch.bfloat16')
    p._expected_bank_model_proof(prepared,proof=proof)
    changed=copy.deepcopy(proof);changed['model_geometry']['hidden_size']=32
    with pytest.raises(ValueError):p._expected_bank_model_proof(prepared,proof=changed)
    forged=copy.deepcopy(prepared);forged['identity']['model_geometry']=changed['model_geometry']
    with pytest.raises(ValueError):p._expected_bank_model_proof(forged,proof=changed)
    changed=copy.deepcopy(proof);changed['dtype']='torch.float64'
    with pytest.raises(ValueError):p._expected_bank_model_proof(prepared,proof=changed)


@pytest.mark.parametrize('damage',['duplicate','missing','extra','profile','runtime','base','instances','tokens','domain','source_ids'])
def test_final_intake_revalidates_completed_bank_support_and_source(tmp_path,damage):
    p,model,support,design,prepared,bank=bank_review_case(tmp_path)
    removed=[]
    result=p.assess_group(model,design,prepared,task='far_v2',name='intact',removed=removed,bank=bank,parent=None,guard=lambda:{})
    from component_analysis.a3_direction_runtime import object_reference,publish_object
    result['run_manifest_reference']=p.publish_run_manifest(tmp_path/'runs',prepared,stage='assess',evidence={'rows':len(result['rows'])})
    broken=copy.deepcopy(bank)
    if damage=='duplicate':broken['values'].append(copy.deepcopy(broken['values'][0]))
    elif damage=='missing':broken['values'].pop()
    elif damage=='extra':broken['values'].append(dict(key=['head',0,1],value=[0.]*4))
    elif damage=='profile':broken['execution_geometry']['padded_width']+=1
    elif damage=='runtime':broken['runtime_identity']='0'*64
    elif damage=='base':broken['base_identity']='0'*64
    elif damage=='instances':broken['n_instances']+=1
    elif damage=='tokens':broken['n_tokens']+=1
    elif damage=='domain':broken['source_rows_sha256']='0'*64
    else:broken['source_ids']=['wrong-source']
    path=tmp_path/'completed-bad';publish_object(path,broken);result['H_bank_reference']=object_reference(path)
    with pytest.raises(ValueError,match='bank|source|profile|support'):
        p.validate_assessment_result(result,design,prepared,task='far_v2',name='intact',removed=removed)
