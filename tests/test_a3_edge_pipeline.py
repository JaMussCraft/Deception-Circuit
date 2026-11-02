"""Offline singleton native edge orchestration contracts."""
import copy
import json
import subprocess
from pathlib import Path
import pytest
import torch
from transformers import LlamaConfig, LlamaForCausalLM
from component_analysis import a3_edge_pipeline as p


def source_design():
    rows=[]
    for split, ids in [('train',['a','b','c']),('validation',['v']),('test',['t'])]:
        for rid in ids:
            for condition in ('D','H','F','I','user_neutral'):
                streams={}
                for stream in ('clean','corrupt'):
                    tokens=[1, 5 if condition in ('D','I') else 6, 7 if stream=='clean' else 8, 2]
                    streams[stream]=dict(prompt='abcd', tokens=tokens,attention_mask=[1]*4,readout=3,
                        opposite_token=9,honest_token=10,expected_token=9 if condition in ('D','I') else 10,
                        layout=dict(role_spans=[['text',0,4]],content_spans=[['text',0,4]]),
                        semantic=dict(prompt_utf8_hex='abcd'.encode().hex(),sites=dict(pressure_request=[1],item_designation=[2],question=[0],assistant_readout=[3])))
                rows.append(dict(instance_id=rid,condition=condition,split=split,pressure_text='one' if rid in ('a','b') else 'two',streams=streams))
    maps=[]
    for r in rows:
        if r['condition'] in ('D','I'):
            for stream in ('clean','corrupt'):
                maps.append(dict(instance_id=r['instance_id'],recipient_condition=r['condition'],donor_condition='H' if r['condition']=='D' else 'user_neutral',stream=stream,supported=True,recipient_positions=list(range(4)),donor_positions=list(range(4))))
    return dict(injected=True,tasks={'far_v2':dict(fit_ids=['a','b','c'],selection_ids=['v'],assessment_ids=['t'],edge_nodes=[['head',0,0],['head',1,0]])},access_rows={'far_v2':rows},semantic_twin_maps={'far_v2':maps},utility={},seeds=[42,1,123])


def geometry():
    return dict(num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1)


def test_canonical_batches_use_own_positions_and_parent_maps():
    d=source_design()
    b=p.source_pair(d,'far_v2','train','a','D','clean',purpose='attribution')
    assert b['batch']['positions']['pressure_request']==[[1]]
    assert b['neutral']['condition']=='H'
    assert b['batch']['input_ids'].tolist()==[[1,5,7,2,0]]
    assert b['maps']['rows'][0]['recipient_positions']==list(range(4))
    with pytest.raises(ValueError,match='membership'):
        p.source_pair(d,'far_v2','train','t','D','clean',purpose='attribution')
    with pytest.raises(ValueError,match='attribution'):
        p.source_pair(d,'far_v2','test','t','D','clean',purpose='attribution')
    pair=p.source_pair(d,'far_v2','test','t','D','clean',purpose='assessment')
    assert pair['neutral']['stream']=='corrupt' and pair['neutral']['condition']=='D'
    d['access_rows']['far_v2'][0]['streams']['clean']['semantic']['sites']['question']=[]
    assert 'question' in p.prepare_graph(d,'far_v2',geometry())['unsupported_bins']
    assert any(e['position']=='question' for e in p.prepare_graph(d,'far_v2',geometry())['edges'])


def test_source_rejects_changed_prompt_semantics_mask_and_overlap():
    for mutation in ('bytes','padding','overlap'):
        d=source_design(); r=d['access_rows']['far_v2'][0]
        if mutation=='bytes':r['streams']['clean']['prompt']='wrong'
        if mutation=='padding':r['streams']['clean']['attention_mask'][1]=0
        if mutation=='overlap':d['tasks']['far_v2']['assessment_ids'].append('a')
        with pytest.raises(ValueError):p.source_pair(d,'far_v2','train','a','D','clean',purpose='attribution')


def test_bootstrap_carries_cluster_multiplicity_and_paired_streams():
    d=source_design(); receipt=p.bootstrap(d,'far_v2',42)
    assert len(receipt['cluster_draws'])==2
    counts=receipt['cluster_multiplicities']; weights=receipt['id_weights']
    assert weights[0]==weights[1]
    assert sum(weights)==pytest.approx(1.)
    assert receipt['expanded_n']==sum(counts.get(x,0) for x in ['one','one','two'])


def test_native_attribution_streamed_complete_grid_and_no_vocab_saved():
    d=source_design(); torch.manual_seed(1)
    model=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    graph=p.prepare_graph(d,'far_v2',geometry())
    result=p.fit_rankings(model,d,'far_v2',graph,steps=2,guard=lambda:None)
    assert [r['seed'] for r in result['fits']]==[42,1,123]
    for fit in result['fits']:
        for condition in ('D','I'):
            assert len(fit['rankings'][condition])==len(graph['edges'])
            assert all(isinstance(x['score'],float) for x in fit['rankings'][condition])
    assert 'logits' not in json.dumps(result)


def test_immutable_restart_and_exact_coverage(tmp_path):
    calls=[]
    inventory=dict(expected_keys=[['a'],['b']],identity={'commit':'a'*40})
    p.execute(inventory,tmp_path,lambda key:calls.append(key) or {'key':key},guard=lambda:None)
    p.execute(inventory,tmp_path,lambda key:pytest.fail('recomputed'),guard=lambda:None,resume=True)
    assert len(calls)==2
    with pytest.raises(ValueError):p.execute(dict(inventory,expected_keys=[['a']]),tmp_path,lambda key:None,guard=lambda:None,resume=True)


def test_actual_wrapper_dry_run_has_no_output_writes(tmp_path):
    path=tmp_path/'d.json'; path.write_text(json.dumps(source_design()))
    out=tmp_path/'absent'
    command=['bash','scripts/jobs/specificity_a3_edges.sh','--dry-run','--stage','prepare','--design',str(path),'--commit','a'*40,'--work-dir',str(out)]
    result=subprocess.run(command,text=True,capture_output=True,env={**__import__('os').environ,'DC_PYTHON':__import__('sys').executable})
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['dry_run'] is True
    assert not out.exists()


def fake_edges():
    spec=dict(key='assistant_readout',semantic_bin='assistant_readout',receiver_kinds=['readout'])
    return [dict(sender=['head',0,i],receiver=['readout',0,0],position='assistant_readout',position_spec=spec) for i in range(20)]


def test_signed_ranking_gate_first_and_budget_ties():
    grid=fake_edges(); rankings=[dict(edge=e,score=(-100 if i==0 else 2 if i in (1,2) else 0)) for i,e in enumerate(grid)]
    ordered=p.rank_edges(rankings,grid)
    assert ordered[0]==grid[1] and ordered[1]==grid[2] and ordered[-1]==grid[0]
    diagnostics=[dict(budget=b,edges=ordered[:b],complete=True,interpretable=True,point_pass=True,D_fraction=.8,I_fraction=.1) for b in (1,4,16)]
    assert p.choose_budget(diagnostics)['budget']==1
    diagnostics[0]['complete']=False
    assert p.choose_budget(diagnostics)['budget']==4
    for x in diagnostics:x['interpretable']=False
    assert p.choose_budget(diagnostics)['status']=='blocked'


def test_nulls_are_torch_seeded_sequential_and_allow_duplicate_draws():
    grid=fake_edges()[:2]
    selected=grid[:1]
    nulls=p.matched_nulls(grid,selected,seed=42)
    generator=torch.Generator().manual_seed(10042)
    expected=[grid[torch.randperm(2,generator=generator)[0].item()] for _ in range(19)]
    assert [x[0] for x in nulls['sets']]==expected
    assert nulls['possible_sets']==2 and nulls['duplicate_draws']>=17
    assert nulls['informative']
    assert not p.matched_nulls(grid[:1],selected,seed=42)['informative']


def test_validation_exact_joint_selection_and_frozen_transfer_with_tiny_model():
    d=source_design(); torch.manual_seed(6)
    model=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    graph=p.prepare_graph(d,'far_v2',geometry())
    selected=[e for e in graph['edges'] if e['position']=='assistant_readout'][:1]
    rows=p.score_mechanism(model,d,'far_v2','validation',selected,guard=lambda:None)
    assert len(rows)==10 and all(r['split']=='validation' for r in rows)
    assert all('intact_margin' in r and 'patched_margin' in r for r in rows)
    assert all(r['estimand']==p.ESTIMAND for r in rows)
    report=p.summarize_rows(rows,expected_ids=['v'])
    assert not report['complete'] and 'IOI' in report['blocked_cells']
    with pytest.raises(ValueError,match='coverage'):
        p.summarize_rows(rows[:-1],expected_ids=['v'])
    transfer=p.score_mechanism(model,d,'far_v2','test',selected,guard=lambda:None)
    assert {r['instance_id'] for r in transfer}=={'t'}


def test_workload_inventory_rejects_missing_nodes_seeds_nulls_and_costs():
    from component_analysis import a3_edge_workload as w
    inventory=w.freeze_inventory(source_design(),{'far_v2':p.prepare_graph(source_design(),'far_v2',geometry())},stage='fit',identity={'commit':'a'*40})
    w.validate_inventory(inventory)
    for mutation in ('seed','coverage','hash'):
        bad=copy.deepcopy(inventory)
        if mutation=='seed':bad['seeds']=[42,1]
        if mutation=='coverage':bad['expected_keys'].pop()
        if mutation=='hash':bad['inventory_sha256']='f'*64
        with pytest.raises(ValueError):w.validate_inventory(bad)
    with pytest.raises(ValueError):w.project_cost(inventory,[])


def test_selection_freezes_three_seed_families_and_nineteen_nulls_before_assessment():
    grid=fake_edges()
    fits=dict(kind='a3_edge_fit',split='train',steps=8,graph_sha256=p.digest({'edges':grid}),fits=[dict(seed=s,rankings={c:[dict(edge=e,score=float(20-i)) for i,e in enumerate(grid)] for c in ('D','I')}) for s in p.SEEDS])
    def evaluator(selected):
        return dict(complete=True,interpretable=True,point_pass=True,D_fraction=.7,I_fraction=.1)
    frozen=p.select_from_fit(fits,{'edges':grid},evaluator=evaluator,injected=True)
    assert len(frozen['families'])==6
    assert all(len(f['nulls']['sets'])==19 and f['budget']==1 for f in frozen['families'])
    p.validate_selection(frozen,{'edges':grid})
    bad=copy.deepcopy(frozen);bad['families'][0]['nulls']['sets'].pop()
    with pytest.raises(ValueError):p.validate_selection(bad,{'edges':grid})
    with pytest.raises(ValueError):p.select_from_fit(dict(fits,split='test'),{'edges':grid},evaluator=evaluator,injected=True)
    with pytest.raises(ValueError):p.select_from_fit(fits,{'edges':grid},evaluator=evaluator,injected=False)


def test_native_utility_cells_are_blocked_without_semantic_support():
    d=source_design();edge=next(e for e in p.prepare_graph(d,'far_v2',geometry())['edges'] if e['position']=='pressure_request')
    rows=p.score_utilities(None,d,'far_v2','validation',[edge],guard=lambda:None)
    assert {r['condition'] for r in rows}=={'IOI','MMLU_zero','MMLU_h_mean'}
    assert all(not r['supported'] and 'readout' in r['reason'] for r in rows)


def test_pilot_exact_eight_validation_ids_and_no_assessment():
    with pytest.raises(ValueError,match='eight'):
        p.pilot_stability(None,source_design(),'far_v2',{},guard=lambda:None)


def test_gate_first_maximizes_D_not_D_minus_I():
    grid=fake_edges()
    values=[dict(budget=b,edges=grid[:b],complete=True,interpretable=True,point_pass=True,D_fraction=d,I_fraction=i) for b,d,i in [(1,.7,.0),(4,.8,.2),(16,.75,.1)]]
    assert p.choose_budget(values)['budget']==4
    for value in values:value['point_pass']=False
    assert p.choose_budget(values)['budget']==1


def test_prepare_binds_ruling_bytes_source_code_and_complete_parent(tmp_path,monkeypatch):
    from component_analysis import a3_direction_artifacts as a
    design=source_design();design['direction_protocol']={'commit':'a'*40}
    monkeypatch.setattr(a,'validate_live',lambda *args,**kwargs:dict(injected=True))
    prepared=p.prepare(design,geometry(),commit='a'*40,registry_paths=[],output=tmp_path/'prepared')
    assert prepared['rules']==p.RULES
    assert prepared['ruling']['sha256']
    assert p.authority.read_object(tmp_path/'prepared')==prepared
    p.validate_prepared(prepared,design,registry_paths=[])
    bad=copy.deepcopy(prepared);bad['ruling']['sha256']='f'*64
    with pytest.raises(ValueError):p.validate_prepared(bad,design,registry_paths=[])


def test_pilot_native_parity_and_receiver_vjp_actual_tiny():
    d=source_design();torch.manual_seed(1)
    model=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    batch=p.source_pair(d,'far_v2','validation','v','D','clean',purpose='attribution')['batch']
    evidence=p.native_pilot_checks(model,batch,[('q',1,0),('k',1,0),('v',1,0),('mlp_in',1,0),('readout',0,0)])
    assert evidence['argmax_equal'] and evidence['max_readout_error']<1e-5
    assert len(evidence['vjps'])==5
    assert len(evidence['gradient_value_comparisons'])==5
    assert all(r['max_scaled_error']<=1 and r['expected_argmax']==r['observed_argmax'] for r in evidence['gradient_value_comparisons'])
    assert all(v['passed'] for v in evidence['vjps'])


def test_unsupported_fit_cell_keeps_graph_and_blocks_rank_without_zero_score():
    d=source_design()
    for r in d['access_rows']['far_v2']:
        if r['condition']=='D' and r['split']=='train':r['streams']['clean']['semantic']['sites']['question']=[]
    torch.manual_seed(1)
    model=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    graph=p.prepare_graph(d,'far_v2',geometry())
    fitted=p.fit_rankings(model,d,'far_v2',graph,steps=2,guard=lambda:None)
    records=fitted['fits'][0]['rankings']['D']
    assert any(r['edge']['position']=='question' and r['score'] is None and not r['supported'] for r in records)
    selected=p.select_from_fit(fitted,graph,evaluator=lambda edges:dict(complete=False,interpretable=False,point_pass=False),injected=True)
    assert all(f['status']=='blocked' for f in selected['families'] if f['ranking_condition']=='D')


def test_runtime_rejects_final_injected_or_partial_summary():
    for injected,pilot,complete in [(True,False,True),(False,True,True),(False,False,False)]:
        with pytest.raises(ValueError):p.final_guard(dict(injected=injected,pilot=pilot,complete=complete,source_commit='a'*40))


def test_staged_prepare_and_fit_cli_injected_model_never_finalize(tmp_path,monkeypatch):
    design=source_design();design['direction_protocol']={'commit':'a'*40}
    monkeypatch.setattr(p.artifacts,'validate_live',lambda *a,**k:{'injected':True})
    monkeypatch.setattr(p,'_read_design',lambda path:design)
    monkeypatch.setattr(p,'execution_guard',lambda *a,**k:lambda:None)
    prepared=p.prepare(design,geometry(),commit='a'*40,registry_paths=[],output=tmp_path/'prepared')
    torch.manual_seed(9)
    def loader(*args):
        return LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    args=['--stage','fit','--design','fixture','--prepared',str(tmp_path/'prepared'),'--commit','a'*40,'--work-dir',str(tmp_path/'run'),'--steps','8']
    p.main(args,model_loader=loader)
    result=p.authority.read_object(tmp_path/'run'/'fit')
    assert result['kind']=='a3_edge_fit_complete' and result['injected']
    assert set(result['tasks'])=={'far_v2'}
    with pytest.raises(ValueError):p.main(args,model_loader=loader)
    for stage in ('select','assess','summarize'):
        stage_args=args.copy();stage_args[1]=stage
        p.main(stage_args,model_loader=loader if stage!='summarize' else None)
    summary=p.authority.read_object(tmp_path/'run'/'summary')
    assert not summary['finalized'] and not summary['runtime_identity']['complete']
    assert all(x['status']=='blocked_selection' for x in summary['reports'])
    final_args=args.copy();final_args[1]='summarize';final_args.append('--final')
    with pytest.raises(ValueError):p.main(final_args)


def test_guard_delegates_fresh_root_authority_with_own_caps(monkeypatch):
    from types import SimpleNamespace
    calls=[]
    monkeypatch.setattr(p,'validate_prepared',lambda *a,**k:{'source':'fresh'})
    monkeypatch.setattr(p.authority,'normalize_ledger',lambda *a,**k:{'ledger':'fresh'})
    context=object();monkeypatch.setattr(p.authority,'make_authority_context',lambda *a,**k:context)
    monkeypatch.setattr(p.authority,'validate_reservation',lambda *a,**k:calls.append(k) or {'root':'actual'})
    args=SimpleNamespace(registry=['protected'],ledger_snapshot='live',reservation='root',work_dir='out')
    guard=p.execution_guard({'injected':False},{},args,{'identity':{'commit':'a'*40}})
    assert guard()['source']=='fresh';guard()
    assert len(calls)==2 and calls[0]['subphase']=='edges' and calls[0]['subphase_limits']=={'M1':.75,'M4':9}
    assert callable(calls[0]['inventory_validator'])
    assert all(c['authority_context'] is context for c in calls)


def test_effective_receiver_equality_rejects_silently_wrong_clamp():
    torch.manual_seed(11)
    d=source_design();model=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    graph=p.prepare_graph(d,'far_v2',geometry());edge=next(e for e in graph['edges'] if e['receiver'][0]=='readout')
    item=p.source_pair(d,'far_v2','validation','v','D','clean',purpose='validation')
    result=p.core.exact_edge_patch(model,item['batch'],item['neutral'],edges=[edge],maps=item['maps'])
    assert all(r['equal'] for r in p.verify_effective_clamps(model,result))
    result['receiver_outputs'][('readout',0,0)]+=1
    with pytest.raises(ValueError,match='effective receiver'):p.verify_effective_clamps(model,result)


def test_caller_control_dict_cannot_replace_root_anchored_evidence(tmp_path):
    path=tmp_path/'admission';p.authority.publish_object(path,dict(edge_control_references={'model_loading':{'sha':'root'}}))
    guard={'reservation':{'reservation':{'admission_path':str(path)}}}
    with pytest.raises(ValueError,match='root admission'):
        p.bind_root_evidence(guard,{'model_loading':{'sha':'caller'}})
    assert p.bind_root_evidence(guard,{'model_loading':{'sha':'root'}})['edge_control_references']['model_loading']['sha']=='root'


def test_independent_plain_inference_readout_matches_native_tiny():
    torch.manual_seed(21);d=source_design()
    model=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    batch=p.source_pair(d,'far_v2','validation','v','D','clean',purpose='attribution')['batch']
    actual=p.plain_inference_observation(model,batch)
    expected=p._observation(p.core.native_forward(model,batch,capture_sites=[]),batch)
    assert actual['margin']==pytest.approx(expected['margin']) and actual['fp32_argmax']==expected['fp32_argmax']
    assert actual['input_ids']==batch['input_ids'].tolist() and actual['physical_batch_size']==1
    assert 'logits' not in actual


def test_complete_toy_control_has_actual_raw_IG_and_endpoint_values():
    receipt=p.complete_toy_control()
    assert receipt['software_control'] and receipt['scores']==[10.,0.]
    assert receipt['intact_margin']==14 and receipt['donor_margin']==receipt['clamped_margin']==4
    assert receipt['source_sha256'] and receipt['endpoint_equal']


def test_control_validation_recomputes_raw_source_comparisons(tmp_path):
    d=source_design();raw=dict(software_control=True,source=str(p.ladder.REPO/'tests/test_a3_edges.py'),source_sha256=p.common.file_hash(p.ladder.REPO/'tests/test_a3_edges.py'),scores=[10.,0.],intact_margin=14.,donor_margin=4.,clamped_margin=4.,endpoint_equal=True)
    body=dict(kind='a3_edge_execution_control_v1',control='complete_toy_endpoint',identity={'commit':'a'*40},producer='a3_edge_pipeline',actual_execution=True,source_code_hashes=p.code_hashes(),raw=raw,passed=True,complete=True)
    p.validate_control(body,d,{'commit':'a'*40})
    changed=copy.deepcopy(body);changed['raw']['clamped_margin']=9
    with pytest.raises(ValueError):p.validate_control(changed,d,{'commit':'a'*40})


def eight_validation_design():
    d=source_design();d['tasks']['far_v2']['selection_ids']=['v'+str(i) for i in range(8)]
    rows=d['access_rows']['far_v2'];d['access_rows']['far_v2']=[r for r in rows if r['split']!='validation']
    for i in range(8):
        for row in rows:
            if row['split']=='validation':d['access_rows']['far_v2'].append(dict(copy.deepcopy(row),instance_id='v'+str(i)))
    maps=d['semantic_twin_maps']['far_v2'];d['semantic_twin_maps']['far_v2']=[m for m in maps if m['instance_id']!='v']
    for i in range(8):
        for m in maps:
            if m['instance_id']=='v':d['semantic_twin_maps']['far_v2'].append(dict(copy.deepcopy(m),instance_id='v'+str(i)))
    return d


def test_actual_pilot_produces_independent_serial_controls_before_later_admission(tmp_path):
    torch.manual_seed(31);d=eight_validation_design()
    first=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    baseline=p.pilot_baselines(first,d,guard=lambda:None)
    second=copy.deepcopy(first)
    identity={'commit':'a'*40,'injected':True}
    refs=p.produce_pilot_controls(second,d,identity,baseline,guard=lambda:None,root=tmp_path/'controls')
    assert set(refs)=={'model_loading','serial_geometry','complete_toy_endpoint'}
    for ref in refs.values():p.validate_control(p.authority.read_object(ref['path']),d,identity)
    graph=p.prepare_graph(d,'far_v2',geometry())
    stability=p.pilot_stability(second,d,'far_v2',graph,guard=lambda:None)
    assert stability['instance_ids']==['v'+str(i) for i in range(8)]
    assert set(stability['conditions'])=={'D','I'}


def test_assessment_rows_reject_wrong_ids_and_invented_supported_utility():
    d=source_design()
    rows=[dict(condition=c,instance_id='t',stream=s,supported=False,pressure_id='two',split='test') for c in p.CONDITIONS for s in p.STREAMS]
    result={'rows':rows,'utility_rows':[],'summary':{'complete':True,'point_pass':True}}
    raw=p.recompute_panel(d,'far_v2',result)
    assert raw['complete'] is False and raw['point_pass'] is False
    changed=copy.deepcopy(result);changed['rows'][0]['instance_id']='training'
    with pytest.raises(ValueError):p.recompute_panel(d,'far_v2',changed)


def test_edge_bootstrap_plan_keeps_cluster_multiplicity_and_shared_utilities():
    d=source_design();d['utility']['ioi']=[{'instance_id':'u0'},{'instance_id':'u1'}];d['utility']['mmlu']=[{'instance_id':'m0'},{'instance_id':'m1'}]
    plan=p.paired_bootstrap_plan(d,n_boot=4)
    assert len(plan)==4
    assert all(set(x['far_v2'])=={'t'} and len(x['IOI'])==2 and len(x['MMLU'])==2 for x in plan)
    assert plan==p.paired_bootstrap_plan(d,n_boot=4)


def test_serial_physical_width_is_frozen_from_source_without_moving_own_readout():
    d=source_design()
    row=next(r for r in d['access_rows']['far_v2'] if r['condition']=='I' and r['split']=='validation')
    for s in row['streams'].values():
        s['tokens'].append(3);s['attention_mask'].append(1);s['readout']=4;s['prompt']='abcde';s['semantic']['prompt_utf8_hex']='abcde'.encode().hex();s['semantic']['sites']['assistant_readout']=[4]
    pair=p.source_pair(d,'far_v2','train','a','D','clean',purpose='attribution')
    assert pair['batch']['input_ids'].tolist()==[[1,5,7,2,0,0]]
    assert pair['batch']['attention_mask'].tolist()==[[1,1,1,1,0,0]]
    assert pair['batch']['readout'].tolist()==[3]
    assert pair['batch']['positions']['assistant_readout']==[[3]]


def test_H_bank_is_ancestral_both_stream_unpadded_token_pool(monkeypatch):
    from component_analysis import a3_native
    d=source_design();rows=[]
    for rid,tokens in [('a',[1,2]),('v',[8,9,10,11])]:
        r=copy.deepcopy(next(r for r in d['access_rows']['far_v2'] if r['instance_id']==rid and r['condition']=='H'))
        for stream in p.STREAMS:
            s=r['streams'][stream];s.update(tokens=tokens,attention_mask=[1]*len(tokens),readout=len(tokens)-1,prompt='x'*len(tokens))
        rows.append(r)
    contract=dict(source_ids=['a','v'],rows=rows,source_sha256=p.digest(rows))
    from types import SimpleNamespace
    model=torch.nn.Linear(2,2).eval().requires_grad_(False)
    model.config=SimpleNamespace(hidden_size=2,num_hidden_layers=1,num_attention_heads=1,num_key_value_heads=1,_attn_implementation='eager')
    d['tasks']['far_v2']['edge_nodes']=[['head',0,0]]
    d['access_rows']['far_v2']=[r for r in d['access_rows']['far_v2'] if r['condition']!='H']+rows
    def native(model,batch,*,capture_sites):
        z=batch['input_ids'].float()
        # Explicit projected additive head representation, not raw head coordinates.
        return {'additive':{site:torch.stack([2*z,-z],-1) for site in capture_sites}}
    monkeypatch.setattr(a3_native,'native_forward',native)
    selected=[fake_edges()[0]]
    bank=p.h_mean_bank(model,d,'far_v2',selected,guard=lambda:None,bank_sources=contract)
    mean=(1+2+8+9+10+11)/6
    torch.testing.assert_close(bank['values'][('head',0,0)],torch.tensor([2*mean,-mean]))
    assert bank['provenance']['unpadded_tokens']==12 and bank['provenance']['source_ids']==['a','v']
    assert bank['provenance']['splits']==['train','validation']
    assert bank['provenance']['weighting']=='equal unpadded token; both streams'
    assert not torch.allclose(bank['values'][('head',0,0)],torch.tensor([2*((2+11)/2),-((2+11)/2)]))


def complete_design_and_model():
    from component_analysis.ladder_tasks import ioi_item_swap_maps
    d=eight_validation_design();d['direction_protocol']={'commit':'a'*40,'numeric_profile':{'dtype':'torch.float32','backend':'eager'},'workload':{'hidden_size':8,'vocabulary_size':16,'dtype_bytes':4}}
    d['tasks']['far_v2']['edge_nodes']=[['head',layer,head] for layer in (0,1) for head in (0,1)]
    for source,n in [('ioi',100),('mmlu',32)]:
        for split,offset in [('validation',0),('test',n)]:
            rows=[]
            for i in range(n):
                j=i+offset;streams={}
                for stream in p.STREAMS:
                    tokens=[3 if source=='ioi' else 4,j//16,j%16,7 if stream=='clean' else 8,2]
                    prompt=''.join(chr(65+x) for x in tokens)
                    streams[stream]=dict(tokens=tokens,attention_mask=[1]*5,readout=4,prompt=prompt,layout=dict(role_spans=[['text',0,5]],content_spans=[['text',0,5]]),honest_token=10,opposite_token=9,expected_token=10)
                rid=source+'-'+split+'-'+str(i)
                rows.append(dict(instance_id=rid,condition=source.upper(),split='generated' if source=='ioi' else 'test',analysis_split='validation' if split=='validation' else 'assessment',source_id=rid,source_hash=p.digest(streams),streams=streams,honest_token=10,opposite_token=9,expected_token=10))
            if split=='validation':d[source+'_validation']=rows
            else:d['utility'][source]=rows
            if source=='ioi':
                if split=='validation':d['ioi_validation_maps']=ioi_item_swap_maps(rows)
                else:d['utility']['ioi_maps']=ioi_item_swap_maps(rows)
    torch.manual_seed(9)
    model=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    with torch.no_grad():
        for layer in model.model.layers:
            layer.self_attn.q_proj.weight.zero_();layer.self_attn.k_proj.weight.zero_()
            layer.mlp.down_proj.weight.zero_()
        model.model.embed_tokens.weight[8].copy_(model.model.embed_tokens.weight[7])
    # Construct a biased synthetic readout before any fixture attribution, so
    # canonical D/H and I/neutral denominators are positive in this known toy.
    from component_analysis.a3_native import _native_norm
    directions=[]
    for stream in p.STREAMS:
        item=p.source_pair(d,'far_v2','train','a','D',stream,purpose='attribution')
        states=[]
        for name in ('batch','neutral'):
            out=p.core.native_forward(model,item[name],capture_sites=[('readout',0,0)])
            states.append(_native_norm(model.model.norm,out['incoming'][('readout',0,0)])[0,item[name]['readout'][0]].float())
        directions.append(states[0]-states[1])
    axis=sum(directions)
    with torch.no_grad():
        model.lm_head.weight.zero_();model.lm_head.weight[9].copy_(axis*1e5);model.lm_head.weight[10].copy_(-axis*1e5)
    return d,model


def test_complete_tiny_native_staged_path_reports_scientific_failure_not_missing_assay(tmp_path,monkeypatch):
    assert callable(p.cached_assessment_panel)
    d,model=complete_design_and_model()
    monkeypatch.setattr(p.artifacts,'validate_live',lambda *a,**k:{'injected':True})
    monkeypatch.setattr(p,'_read_design',lambda path:d)
    monkeypatch.setattr(p,'execution_guard',lambda *a,**k:lambda:None)
    p.prepare(d,geometry(),commit='a'*40,registry_paths=[],output=tmp_path/'prepared')
    args=['--stage','fit','--design','fixture','--prepared',str(tmp_path/'prepared'),'--commit','a'*40,'--work-dir',str(tmp_path/'run'),'--pilot-evidence',str(tmp_path/'run'/'pilot')]
    for stage in ('pilot','fit','select','assess','summarize'):
        run=args.copy();run[1]=stage
        p.main(run,model_loader=(lambda *a:copy.deepcopy(model)) if stage!='summarize' else None)
    summary=p.authority.read_object(tmp_path/'run'/'summary')
    assert summary['runtime_identity']['complete'] is True
    assert not summary['finalized']
    panels=list((tmp_path/'run'/'panels').iterdir());panel=p.authority.read_object(panels[0])
    assert all(r['source_split']==('generated' if r['condition']=='IOI' else 'test') and r['analysis_split']=='assessment' for r in panel['utility_rows'])
    assert all(r['status']!='blocked_selection' for r in summary['reports'])
    assert all(not s['point_pass'] and s['edge_assay_ready'] for r in summary['reports'] for s in r['selected_seeds'])
    from component_analysis import a3_edge_workload as w
    prepared=p.authority.read_object(tmp_path/'prepared');identity=p._stage_identity(d,prepared)
    fit=p.authority.read_object(tmp_path/'run'/'fit');selected=p.authority.read_object(tmp_path/'run'/'selection')
    for stage in ('select','assess'):
        inv=w.freeze_inventory(d,prepared['graphs'],stage=stage,identity=identity,bank_sources=prepared['bank_sources'],fit=fit if stage=='select' else None,selected=selected if stage=='assess' else None)
        receipt=p.collect_profile_measurements(copy.deepcopy(model),d,prepared,inv,guard=lambda:None,root=tmp_path/stage)
        p.validate_measurement_receipt(receipt,d,prepared,identity)
        forecast=w.project_cost(inv,[receipt],capacities={'host_bytes':10**12,'disk_bytes':10**12})
        assert forecast['complete'] and forecast['unique_exact_sets']>0
    run=args.copy();run[1]='summarize';run.append('--final')
    with pytest.raises(ValueError):p.main(run)


def test_shape_complete_measured_inventory_has_positive_injected_admission_and_capacity_failures(tmp_path):
    from component_analysis import a3_edge_workload as w
    assert callable(p.collect_profile_measurements)
    d,model=complete_design_and_model();d=eightify(d)
    d['direction_protocol']['numeric_profile']={'dtype':'torch.float32','backend':'eager'}
    d['direction_protocol']['workload']={'hidden_size':8,'vocabulary_size':16,'dtype_bytes':4}
    graph=p.prepare_graph(d,'far_v2',geometry())
    prepared={'graphs':{'far_v2':graph},'bank_sources':p.ancestral_bank_sources(d)}
    identity={'commit':'a'*40,'injected':True,'numeric_profile':d['direction_protocol']['numeric_profile']}
    inventory=w.freeze_inventory(d,prepared['graphs'],stage='fit',identity=identity,bank_sources=prepared['bank_sources'])
    measurement=p.collect_profile_measurements(model,d,prepared,inventory,guard=lambda:None,root=tmp_path)
    proposal=w.project_cost(inventory,[measurement],capacities={'host_bytes':10**12,'disk_bytes':10**12})
    assert proposal['complete'] and proposal['gpu_hours']>=0 and not proposal['authority']
    bad=copy.deepcopy(measurement);bad['measurements'].pop()
    with pytest.raises(ValueError):w.project_cost(inventory,[bad],capacities={'host_bytes':10**12,'disk_bytes':10**12})
    with pytest.raises(ValueError):w.project_cost(inventory,[measurement],capacities={'host_bytes':1,'disk_bytes':1})
    bad=copy.deepcopy(measurement);bad['runtime']['geometry']['hidden_size']+=1
    with pytest.raises(ValueError):w.project_cost(inventory,[bad],capacities={'host_bytes':10**12,'disk_bytes':10**12})


def eightify(d):
    if d['tasks']['far_v2']['selection_ids']==['v'+str(i) for i in range(8)]:return copy.deepcopy(d)
    d=copy.deepcopy(d);old=d['access_rows']['far_v2'];vals=[r for r in old if r['split']=='validation']
    d['access_rows']['far_v2']=[r for r in old if r['split']!='validation']
    d['tasks']['far_v2']['selection_ids']=['v'+str(i) for i in range(8)]
    for i in range(8):
        d['access_rows']['far_v2'].extend(dict(copy.deepcopy(r),instance_id='v'+str(i)) for r in vals)
    maps=d['semantic_twin_maps']['far_v2'];vmap=[m for m in maps if m['instance_id']=='v']
    d['semantic_twin_maps']['far_v2']=[m for m in maps if m['instance_id']!='v']
    for i in range(8):d['semantic_twin_maps']['far_v2'].extend(dict(copy.deepcopy(m),instance_id='v'+str(i)) for m in vmap)
    return d


def test_real_A1_unpadded_stream_schema_derives_mask_without_caller_assertion():
    d=source_design()
    for row in d['access_rows']['far_v2']:
        for stream in row['streams'].values():del stream['attention_mask']
    d['access_rows']['far_v2'][0]['streams']['clean']['tokens'][1]=0
    before=copy.deepcopy(d)
    item=p.source_pair(d,'far_v2','train','a','D','clean',purpose='attribution')
    assert item['batch']['attention_mask'].tolist()==[[1,1,1,1,0]]
    assert item['batch']['input_ids'][0,1]==0 and d==before


def test_pilot_midpoint_cache_resumes_exact_coverage_without_recomputation(tmp_path):
    d=eight_validation_design();torch.manual_seed(7)
    model=LlamaForCausalLM(LlamaConfig(hidden_size=8,intermediate_size=12,num_hidden_layers=2,num_attention_heads=2,num_key_value_heads=1,vocab_size=16,attn_implementation='eager')).eval().requires_grad_(False)
    grid=p.prepare_graph(d,'far_v2',geometry());edge=next(e for e in grid['edges'] if e['receiver'][0]=='readout')
    graph={'edges':[edge]}
    first=p.pilot_stability(model,d,'far_v2',graph,guard=lambda:None,cache_root=tmp_path/'pilot-cache',identity={'commit':'a'*40})
    second=p.pilot_stability(None,d,'far_v2',graph,guard=lambda:None,cache_root=tmp_path/'pilot-cache',identity={'commit':'a'*40},resume=True)
    assert first==second
    assert first['instance_ids']==d['tasks']['far_v2']['selection_ids']


def test_all_source_stream_fields_are_checked_against_original_parent():
    d=source_design();parent={'rows':{'far_v2':{c:[copy.deepcopy(r) for r in d['access_rows']['far_v2'] if r['condition']==c] for c in p.CONDITIONS}}}
    p.validate_original_streams(d,parent)
    for mutation in ('tokens','labels','readout','prompt'):
        changed=copy.deepcopy(d);s=changed['access_rows']['far_v2'][0]['streams']['clean']
        if mutation=='tokens':s['tokens'][0]=12
        elif mutation=='labels':s['honest_token']=11
        elif mutation=='readout':s['readout']=2
        else:s['prompt']='caller claim'
        with pytest.raises(ValueError):p.validate_original_streams(changed,parent)


def test_original_A3_file_bytes_remain_separate_from_derived_batch_digest(tmp_path,monkeypatch):
    d=source_design();d['kind']='specificity_ladder_a3_design';d['direction_protocol']={'commit':'a'*40}
    monkeypatch.setattr(p.artifacts,'validate_live',lambda *a,**k:{'injected':True})
    path=tmp_path/'design.json';p.ladder.write_artifact(path,d)
    prepared=p.prepare(d,geometry(),commit='a'*40,registry_paths=[],design_path=path)
    assert prepared['design_reference']['sha256']==p.common.file_hash(path)
    path.write_text(path.read_text()+'\n')
    with pytest.raises(ValueError):p.validate_prepared(prepared,d,registry_paths=[])


def test_actual_wrapper_works_when_Slurm_executes_a_spooled_script(tmp_path):
    import os,sys
    spool=tmp_path/'spool';spool.mkdir();script=spool/'slurm_script'
    script.write_text(Path('scripts/jobs/specificity_a3_edges.sh').read_text())
    design=tmp_path/'fixture.json';design.write_text(json.dumps(source_design()))
    run=subprocess.run(['bash',str(script),'--dry-run','--stage','pilot','--design',str(design),'--commit','a'*40,'--work-dir',str(tmp_path/'no-write')],text=True,capture_output=True,
        env={**os.environ,'DC_PYTHON':sys.executable,'SLURM_JOB_ID':'software-wrapper-fixture','SLURM_SUBMIT_DIR':str(Path.cwd())})
    assert run.returncode==0,run.stderr
    assert json.loads(run.stdout)['model_loaded'] is False and not (tmp_path/'no-write').exists()


def test_dry_run_rejects_untyped_production_input_and_never_queries_CUDA(tmp_path,monkeypatch):
    source=tmp_path/'source.json';source.write_text(json.dumps({'injected':False}))
    monkeypatch.setattr(torch.cuda,'is_available',lambda:pytest.fail('CUDA queried by dry-run'))
    args=['--dry-run','--stage','pilot','--design',str(source),'--commit','a'*40,'--work-dir',str(tmp_path/'absent')]
    with pytest.raises(ValueError):p.main(args)
    source.write_text(json.dumps(source_design()))
    result=p.main(args)
    assert not result['source_admitted'] and not result['execution_authorized'] and not (tmp_path/'absent').exists()
