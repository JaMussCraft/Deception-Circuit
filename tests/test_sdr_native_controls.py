"""Prospective native controls: CPU contracts, no real-model inference."""
import copy
import json
from pathlib import Path
import pytest
from scripts import sdr_native_controls as n

ROOT = Path(__file__).resolve().parents[1]

class Tokenizer:
    def encode(self, text, add_special_tokens=False):
        assert not add_special_tokens
        return list(range(1, len(text.split()) + 1))
    def decode(self, ids, **kwargs):
        return ' '.join(map(str, ids))

@pytest.fixture
def protocol(tmp_path, monkeypatch):
    cache = tmp_path / 'cache'
    cache.mkdir()
    for name in ('config.json', 'generation_config.json'):
        (cache / name).write_text(json.dumps({'eos_token_id': [128001,128008,128009]}))
    (cache / 'tokenizer.json').write_text('{}')
    monkeypatch.setattr(n, 'load_tokenizer', lambda _: Tokenizer())
    return n.build_protocol(ROOT/'dataset/deception_pools', cache)

def test_panel_exact_counts_order_disjointness_and_coverage(protocol):
    p = protocol
    assert len(p['main']) == 3072 and len(p['calibration']) == 64
    assert len({r['id'] for r in p['main']+p['calibration']}) == 3136
    assert len({tuple(f['pair']) for f in p['fixtures']}) == 34
    assert [f['template'] for f in p['fixtures'][:32]].count('audit') == 16
    assert [f['pair'] for f in p['fixtures'][:32]]==[list(v) for v in n.rank('native-controls-pair',{tuple(sorted(v)) for v in json.loads((ROOT/'dataset/deception_pools/item_pairs.json').read_text())})[:32]]
    for f in p['fixtures'][:32]:
        assert len([r for r in p['main'] if r['fixture_id']==f['id']]) == 96
    for f in p['fixtures'][32:]:
        rows = [r for r in p['calibration'] if r['fixture_id']==f['id']]
        assert len(rows)==32
        for key, levels in n.FACTORS.items():
            assert {r['factors'][key] for r in rows} == set(levels)
    assert p['payload']['sequence_length'] % 32 == 0
    assert p['payload']['sequence_length'] == ((p['payload']['max_prompt_length']+95)//32)*32
    n.verify_protocol(p)

def test_literal_render_and_clause_triplets(protocol):
    for template in ('audit','lab'):
        f=next(f for f in protocol['fixtures'] if f['template']==template)
        rows=n.factor_rows(f)
        for row in rows:
            assert '.THE DAMAGING ONE' in row['system']
            assert row['truth_name']==f['pair'][row['factors']['truth']]
            assert row['favored_name']==f['pair'][row['factors']['favored']]
        assert len({r['system'].rsplit(' ',1)[0] for r in rows})>1
        a,b,c=rows[0],rows[2],rows[4]
        assert a['system'].removesuffix(a['clause'])==b['system'].removesuffix(b['clause'])==c['system'].removesuffix(c['clause'])

def test_tamper_source_and_cache_fail(protocol):
    bad=copy.deepcopy(protocol);bad['main'][0]['truth_name']='wrong'
    with pytest.raises(ValueError): n.verify_protocol(bad)
    Path(protocol['provenance']['cache']) .joinpath('config.json').write_text('{}')
    with pytest.raises(ValueError): n.verify_protocol(protocol)

def test_batch_fixed_shape_logical_append_and_dummy():
    ids,mask,real=n.make_batch([{'id':'x','ids':[7,8]}],batch_size=8,sequence_length=32,device='cpu')
    assert ids.shape==mask.shape==(8,32)
    assert ids[0,:3].tolist()==[7,8,0] and mask.sum(1).tolist()==[2,1,1,1,1,1,1,1]
    assert real==['x']
    with pytest.raises(ValueError): n.make_batch([{'id':'x','ids':list(range(33))}],batch_size=8,sequence_length=32,device='cpu')

def test_numerics_full_vocab_greedy_and_nonfinite():
    import torch
    a=torch.tensor([[0., 1e-6]])
    assert n.compare_vectors(a,a)['pass']
    b=torch.tensor([[1e-6,0.]])
    assert not n.compare_vectors(a,b)['pass']
    assert not n.compare_vectors(a,torch.full_like(a,float('nan')))['pass']

def test_blind_views_and_join_requires_independent_complete_labels(protocol,tmp_path):
    gens=[{'id':r['id'],'text':'same','finish':'eos','protocol_hash':protocol['scientific_hash']} for r in protocol['main']]
    views=n.export_blind_views(protocol,gens)
    assert all(set(v)=={'view_id','text','options','finish'} for v in views)
    assert len(views)==32
    paths=[]
    for annotator in ('one','two'):
        path=tmp_path/(annotator+'.json')
        path.write_text(json.dumps({'annotator':annotator,'independent':True,'protocol_hash':protocol['scientific_hash'],'views_hash':n.digest(views),'labels':[{'view_id':v['view_id'],'candidate':None,'kind':'explicit_refusal','format_ok':False} for v in views]}));paths.append(path)
    joined=n.join_annotations(protocol,gens,paths)
    assert len(joined)==3072 and not any(r['correct'] for r in joined)
    with pytest.raises(ValueError): n.join_annotations(protocol,gens,[paths[0],paths[0]])
    paths[1].write_text('{}')
    with pytest.raises(ValueError): n.join_annotations(protocol,gens,paths)

def test_analysis_constructed_gate_and_collateral(protocol):
    rows=[]
    for r in protocol['main']:
        conflict=r['factors']['truth']!=r['factors']['favored']
        correct=not(r['factors']['task']=='report' and r['factors']['condition']=='C' and conflict)
        rows.append({**r,'correct':correct,'non_relevant':not correct,'kind':'commitment','candidate':r['factors']['truth'] if correct else r['factors']['favored'],'format_ok':True,'controls':[{'control':'repeat','pass':True},{'control':'empty_hook','pass':True}]})
    result=n.analyze_panel(protocol,rows)
    assert result['behavior_go'] and result['denominators']['neutral_report']==512
    assert result['denominators']['retrieval']==1536
    assert result['bootstrap']['replicates']==10000
    for r in rows:
        if r['factors']['task']=='retrieval' and r['factors']['condition']=='C':
            r.update(correct=False,non_relevant=False,kind='explicit_refusal')
    result=n.analyze_panel(protocol,rows)
    assert not result['behavior_go'] and 'retrieval_collateral_C-A' in result['failed_criteria']

def test_forecast_full_cap_and_operations_separation(protocol):
    ops={'hardware_class':'H200','reserved_seconds':999999,'deadline_utc':'2099-01-01T00:00:00+00:00','startup_buffer_seconds':10,'io_buffer_seconds':20,'shutdown_buffer_seconds':30}
    n.verify_operations(ops)
    forecast=n.forecast_main(protocol,{'max_forward_seconds':2.,'control_seconds':3.,'startup_seconds':4.,'io_seconds':5.},ops)
    assert forecast['generation_forwards']==384*64
    assert forecast['required_seconds'] >= 384*66*2+60+12
    before=protocol['scientific_hash'];ops['reserved_seconds']+=1
    assert protocol['scientific_hash']==before

def test_complete_batch_mixed_eos_fixed_slots_and_self_control(protocol,monkeypatch):
    import torch
    from types import SimpleNamespace
    from component_analysis import hooks
    from scripts import sdr_routing_pilot as pilot
    p=copy.deepcopy(protocol);p['payload']['eos']=[3];p['_calibration']=True
    calls=[]
    def capture(model,ids,mask,*,components,replacements=None):
        calls.append((ids.clone(),mask.clone(),components,replacements))
        assert replacements is None or hooks.READOUT_KEY not in replacements
        return SimpleNamespace(outputs={key:torch.zeros(8,ids.shape[1],2) for key in components},readout=mask.sum(-1)-1)
    def logits(model,cap):
        result=torch.zeros(8,5,dtype=torch.float32)
        result[:,4]=1.
        result[0,3]=2.
        if int(cap.readout[1])>=protocol['main'][1]['length']+1: result[1,3]=2.
        return result
    monkeypatch.setattr(hooks,'device_and_dtype',lambda _:('cpu',torch.float32))
    monkeypatch.setattr(hooks,'all_component_keys',lambda _:[('embed',0,0),hooks.READOUT_KEY])
    monkeypatch.setattr(hooks,'capture_forward',capture);monkeypatch.setattr(pilot,'capture_logits',logits)
    monkeypatch.setattr(n,'load_tokenizer',lambda _:Tokenizer())
    rows=p['main'][:2];result=n.complete_batch(object(),rows,p)
    assert result[0]['generated_ids']==[3] and result[1]['generated_ids']==[4,4,3]
    assert result[0]['finish']==result[1]['finish']=='eos'
    assert all(tuple(x[0].shape)==(8,p['payload']['sequence_length']) for x in calls)
    assert all(x[1][0].sum()==rows[0]['length'] for x in calls)
    assert all(len(r['controls'])==4 and all(c['pass'] for c in r['controls']) for r in result)


def test_cap_keeps_64_tokens(protocol,monkeypatch):
    import torch
    from types import SimpleNamespace
    from component_analysis import hooks
    from scripts import sdr_routing_pilot as pilot
    monkeypatch.setattr(hooks,'device_and_dtype',lambda _:('cpu',torch.float32))
    monkeypatch.setattr(hooks,'capture_forward',lambda model,ids,mask,**kwargs:SimpleNamespace(readout=mask.sum(-1)-1))
    monkeypatch.setattr(pilot,'capture_logits',lambda model,cap:torch.tensor([[0.,1.]]*8))
    monkeypatch.setattr(n,'load_tokenizer',lambda _:Tokenizer())
    result=n.complete_batch(object(),protocol['main'][:1],protocol)[0]
    assert len(result['generated_ids'])==64 and result['finish']=='capped'
    assert result['logical_readouts']==list(range(protocol['main'][0]['length']-1,protocol['main'][0]['length']+63))


def test_rounded_length_capacity_abort_and_hash_ids(protocol):
    fixture=protocol['fixtures'][0]
    assert fixture['id']=='nc-'+n.digest(['native-controls-fixture',20261021,fixture['template'],fixture['entity'],fixture['pair']])[:16]
    r=protocol['main'][0];f=r['factors']
    assert r['id']==f"{fixture['id']}:{f['wording']}:t{f['truth']}:o{f['order']}:f{f['favored']}:{f['condition']}:{f['task']}"
    bad=copy.deepcopy(protocol);bad['payload']['sequence_length']=32;bad['scientific_hash']=n.digest(bad['payload'])
    with pytest.raises(ValueError,match='length'): n.verify_protocol(bad)


def test_annotations_disagreement_and_cap_override(protocol,tmp_path):
    gens=[{'id':r['id'],'text':'quoted and rejected option','finish':'capped','protocol_hash':protocol['scientific_hash']} for r in protocol['main']]
    views=n.export_blind_views(protocol,gens);paths=[]
    for i,kind in enumerate(('commitment','qualified_ambiguous','contradictory')):
        path=tmp_path/f'{i}.json';path.write_text(json.dumps({'annotator':str(i),'independent':True,'protocol_hash':protocol['scientific_hash'],'views_hash':n.digest(views),'labels':[{'view_id':v['view_id'],'candidate':0 if kind=='commitment' else None,'kind':kind,'format_ok':True} for v in views]}));paths.append(path)
    with pytest.raises(ValueError,match='unadjudicated'): n.join_annotations(protocol,gens,paths[:2])
    joined=n.join_annotations(protocol,gens,paths)
    assert all(r['kind']=='capped' and not r['correct'] and not r['non_relevant'] for r in joined)


def test_operation_validation_rejects_missing_deadline_and_buffers():
    for operations in ({},{'hardware_class':'H200','reserved_seconds':1,'deadline_utc':'2099-01-01T00:00:00+00:00'}):
        with pytest.raises(ValueError): n.verify_operations(operations)

def test_final_analysis_requires_numerical_coverage(protocol):
    rows=[]
    for r in protocol['main']:
        rows.append({**r,'kind':'commitment','candidate':r['factors']['truth'],'correct':True,'non_relevant':False,'format_ok':True,'controls':[]})
    result=n.analyze_panel(protocol,rows)
    assert not result['behavior_go'] and 'numerical_coverage' in result['failed_criteria']

def perfect_panel(protocol):
    return [{**r,'kind':'commitment','candidate':r['factors']['favored'] if r['factors']['task']=='report' and r['factors']['condition']=='C' else r['factors']['truth'],'correct':not(r['factors']['task']=='report' and r['factors']['condition']=='C' and r['factors']['favored']!=r['factors']['truth']),'non_relevant':r['factors']['task']=='report' and r['factors']['condition']=='C' and r['factors']['favored']!=r['factors']['truth'],'format_ok':True,'controls':[{'control':'repeat','pass':True},{'control':'empty_hook','pass':True}]} for r in protocol['main']]


def test_capability_block_26_of_32_boundary_and_adverse_refusal(protocol):
    rows=perfect_panel(protocol)
    block=[r for r in rows if r['template']=='audit' and all(r['factors'][k]==v for k,v in {'wording':'A','truth':0,'order':0,'task':'report','condition':'A'}.items())]
    assert len(block)==32
    for r in block[:6]: r.update(kind='explicit_refusal',candidate=None,correct=False,non_relevant=False)
    a=n.analyze_panel(protocol,rows)
    key='capability_block:'+n.canonical(['audit','A',0,0,'report','A'])
    assert a['gates'][key]['pass']
    block[6].update(kind='coherent_evasion',candidate=None,correct=False,non_relevant=False)
    b=n.analyze_panel(protocol,rows)
    assert not b['gates'][key]['pass'] and not b['behavior_go']


def test_template_and_wording_effect_reversals_stop_and_bootstrap_repeats(protocol):
    rows=perfect_panel(protocol)
    a=n.analyze_panel(protocol,rows);b=n.analyze_panel(protocol,rows)
    assert a['bootstrap']==b['bootstrap'] and a['behavior_go']
    for r in rows:
        if r['template']=='lab' and r['factors']['task']=='report' and r['factors']['condition']=='C':
            r.update(candidate=r['factors']['truth'],correct=True,non_relevant=False)
    result=n.analyze_panel(protocol,rows)
    assert result['report_contrasts']['A']==.5
    assert 'template:lab:C-A' in result['failed_criteria']


def test_main_calibration_binding_rejected_before_model_load(protocol,tmp_path,monkeypatch):
    ops={'hardware_class':'H200','reserved_seconds':100000,'deadline_utc':'2099-01-01T00:00:00+00:00','startup_buffer_seconds':1,'io_buffer_seconds':1,'shutdown_buffer_seconds':1,'calibration_path':str(tmp_path/'receipt.json')}
    monkeypatch.setattr(n,'runtime_identity',lambda _: {'class':'H200','name':'NVIDIA H200','capability':[9,0],'memory':1,'count':1})
    binding=n.runtime_binding(protocol,n.runtime_identity(ops))
    binding['sequence_length']+=32
    Path(ops['calibration_path']).write_text(json.dumps({'mode':'calibration','status':'completed','numerical_pass':True,'completed_rows':64,'binding':binding}))
    with pytest.raises(ValueError,match='calibration mismatch'): n.run_main(protocol,tmp_path/'main',ops)
    assert not (tmp_path/'main').exists()

def test_partial_batch_keeps_tokens_and_failed_numerical_receipt(protocol,monkeypatch):
    import torch
    from types import SimpleNamespace
    from component_analysis import hooks
    from scripts import sdr_routing_pilot as pilot
    snapshots=[];calls=[0]
    p={**protocol,'_checkpoint_batch':lambda rows,stats:snapshots.append(copy.deepcopy((rows,stats)))}
    monkeypatch.setattr(hooks,'device_and_dtype',lambda _:('cpu',torch.float32))
    monkeypatch.setattr(hooks,'capture_forward',lambda model,ids,mask,**kwargs:SimpleNamespace(readout=mask.sum(-1)-1))
    def logits(model,cap):
        calls[0]+=1
        return torch.tensor([[0.,1. if calls[0]==1 else 2.]]*8)
    monkeypatch.setattr(pilot,'capture_logits',logits)
    with pytest.raises(ValueError,match='numerical control'): n.complete_batch(object(),p['main'][:1],p)
    rows,stats=snapshots[-1]
    assert rows[0]['controls'][0]['pass'] is False and stats['physical_forwards']==3

def test_forecast_checkpoint_io_uses_full_cap_counts_and_panel_growth(protocol):
    ops={'hardware_class':'H200','reserved_seconds':9999999,'deadline_utc':'2099-01-01T00:00:00+00:00','startup_buffer_seconds':1,'io_buffer_seconds':1,'shutdown_buffer_seconds':1}
    cal={'max_forward_seconds':1.,'control_seconds':2.,'startup_seconds':3.,'io_seconds':4.,'max_active_checkpoint_seconds':.1,'max_panel_checkpoint_seconds':.2}
    forecast=n.forecast_main(protocol,cal,ops)
    assert forecast['active_checkpoint_count']==384*(64+2+64)
    assert forecast['panel_checkpoint_count']==384*2+4
    assert forecast['checkpoint_io_seconds']>=forecast['active_checkpoint_count']*.1+forecast['panel_checkpoint_count']*.2*48


def test_allocation_deadline_binding_preserves_science_and_binds_proposal():
    proposal={'deadline_utc':'2099-01-01T00:00:00+00:00','shutdown_buffer_seconds':30,'reserved_seconds':600}
    bound=n.bind_allocation_operations(proposal,allocation_end=1000,allocation_start=400)
    assert bound['deadline_utc']=='1970-01-01T00:16:40+00:00'
    assert bound['proposal_hash']==n.digest(proposal)
    assert bound['reserved_seconds']==600
    assert proposal['deadline_utc'].startswith('2099')

# Sharding amendment: timing-only ranges and a single shared decoding path.
def shard_inputs(protocol,tmp_path,monkeypatch):
    p=copy.deepcopy(protocol);p['provenance']['code_commit']='a'*40;p['provenance_hash']=n.digest(p['provenance'])
    hardware={'class':'A100','name':'NVIDIA A100-SXM4-40GB','capability':[8,0],'memory':42405855232,'count':1}
    cal={'mode':'calibration','status':'completed','completed_rows':64,'controls_rows':64,'numerical_pass':True,'binding':n.runtime_binding(p,hardware),'max_forward_seconds':.5001186539884657,'max_active_checkpoint_seconds':.2579433477949351,'max_panel_checkpoint_seconds':.3328207810409367,'startup_seconds':26.179541178047657,'control_seconds':6.894779563648626,'io_seconds':9.83199412515387,'premodel_seconds':52.}
    cancel=tmp_path/'cancel.json';cancel.write_text(json.dumps({'job_id':'23101635','state':'TERMINAL_CANCELLED_ZERO_ATTEMPTS','model_attempts':0,'source_unlock_evidence':True}))
    ops={'hardware_class':'A100','reserved_seconds':3600,'deadline_utc':'2099-01-01T00:00:00+00:00','startup_buffer_seconds':120,'io_buffer_seconds':120,'shutdown_buffer_seconds':90,'registry_root':str((tmp_path/'registry').resolve()),'zero_attempt_receipt':str(cancel)}
    monkeypatch.setattr(n,'SHARD_RELEASE_PATH',tmp_path/'release.json')
    return p,cal,ops


def test_shard_timing_plan_exact_ranges_science_and_no_outcomes(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch)
    before=copy.deepcopy(p['payload']);plan=n.build_shard_plan(p,cal,ops)
    assert plan['batch_size']==30 and len(plan['ranges'])==13
    assert [r['batch_range'] for r in plan['ranges']]==[[i,min(i+30,384)] for i in range(0,384,30)]
    assert [rowid for r in plan['ranges'] for rowid in r['row_ids']]==[r['id'] for r in p['main']]
    assert plan['premodel_headroom_seconds']==120 and plan['release_margin_seconds']==60
    assert p['payload']==before
    assert plan['ranges'][0]['forecast']['panel_payload_growth_factor']==48
    altered={**cal,'irrelevant_responses':['different response'],'mean_tokens':1}
    assert n.build_shard_plan(p,altered,ops)['ranges']==plan['ranges']
    cal2={**cal,'premodel_seconds':200}
    assert n.build_shard_plan(p,cal2,ops)['batch_size']<30
    with pytest.raises(ValueError,match='fit'): n.build_shard_plan(p,{**cal,'max_forward_seconds':99999},ops)
    n.verify_shard_plan(p,cal,plan)
    bad=copy.deepcopy(plan);bad['ranges'][1]['batch_range'][0]-=1
    with pytest.raises(ValueError): n.verify_shard_plan(p,cal,bad)


def activate_plan(p,plan,tmp_path):
    registry=Path(plan['registry_root']);registry.mkdir()
    inventory=registry/'operator-inventory.json'
    inventory.write_text(json.dumps({'scientific_hash':p['scientific_hash'],'plan_hash':plan['plan_hash'],'monolithic_submissions':[],'outputs':[]}))
    n.SHARD_RELEASE_PATH.write_text(json.dumps({'status':'activated','scientific_hash':p['scientific_hash'],'provenance_hash':p['provenance_hash'],'plan_hash':plan['plan_hash'],'registry_root':plan['registry_root'],'operator_inventory_path':str(inventory)}))
    return inventory


def test_claim_exclusive_across_output_paths_and_orphan_blocks(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops)
    inventory=activate_plan(p,plan,tmp_path)
    outs=[str((tmp_path/name).resolve()) for name in ('first','alternate')]
    inv=json.loads(inventory.read_text());inv['outputs']=outs;inventory.write_text(json.dumps(inv))
    claim=n.claim_main_shard(p,plan,0,{'output':outs[0],'job_id':'test1','operations_hash':'ops'})
    assert claim['batch_range']==[0,30]
    with pytest.raises(ValueError,match='claim'): n.claim_main_shard(p,copy.deepcopy(plan),0,{'output':outs[1],'job_id':'test2','operations_hash':'ops'})
    assert len(list((Path(plan['registry_root'])/'invocations').glob('*.json')))==2
    assert len(list((Path(plan['registry_root'])/'claims').glob('*.json')))==1
    with pytest.raises(ValueError,match='activated'): n.run_main(p,tmp_path/'monolith',ops)


def completed_shards(p,cal,plan,tmp_path,inventory):
    outputs=[]
    for segment in plan['ranges']:
        index=segment['index'];out=tmp_path/f'shard-{index}';out.mkdir();outputs.append(out)
        inv=json.loads(inventory.read_text());inv['outputs'].append(str(out.resolve()));inventory.write_text(json.dumps(inv))
        ops={**plan['policy'],'deadline_utc':'2099-01-01T00:00:00+00:00'};n.atomic_json(out/'operations.json',ops)
        claim=n.claim_main_shard(p,plan,index,{'output':str(out),'job_id':f'cpu-{index}','operations_hash':n.digest(ops)})
        first,stop=segment['batch_range'];gens=[]
        for position,row in enumerate(p['main'][8*first:8*stop]):
            controls=[{'control':name,'pass':True,'finite':True,'max_abs_error':0.,'identical_greedy':True,'tolerance':1e-5,'bitwise':True} for name in ('repeat','empty_hook')]
            gens.append({'id':row['id'],'protocol_hash':p['scientific_hash'],'plan_hash':plan['plan_hash'],'global_batch_index':first+position//8,'physical_slot':position%8,'shard_index':index,'attempt_number':1,'generated_ids':[p['payload']['eos'][0]],'logical_readouts':[row['length']-1],'text':row['stem']+' answer','finish':'eos','status':'completed','controls':controls})
        n.atomic_json(out/'generations.json',gens)
        receipt={'mode':'main-shard','status':'completed','numerical_pass':True,'completed_rows':len(gens),'controls_rows':len(gens),'binding':cal['binding'],'plan_hash':plan['plan_hash'],'shard_index':index,'batch_range':[first,stop],'claim_hash':n.digest(claim),'predecessor_hash':claim['predecessor_hash'],'physical_forwards':3*(stop-first),'actual_gpu_seconds':10.,'allocation_elapsed_seconds':15.,'operations_hash':n.digest(ops)}
        n.atomic_json(out/'receipt.json',receipt);(out/'attempts').mkdir()
        for batch in range(first,stop):
            n.atomic_json(out/'attempts'/f'{batch:03d}.json',{'global_batch_index':batch,'row_ids':[r['id'] for r in p['main'][8*batch:8*(batch+1)]],'claim_hash':n.digest(claim),'attempt_number':1})
        n._claim_outcome(plan,claim,'completed',artifact_hashes={name:n.file_hash(out/name) for name in ('receipt.json','generations.json','operations.json')},attempt_hashes={f.name:n.file_hash(f) for f in (out/'attempts').glob('*.json')})
    return outputs


def test_merge_requires_complete_registry_not_selected_good_outputs(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);inventory=activate_plan(p,plan,tmp_path)
    outputs=completed_shards(p,cal,plan,tmp_path,inventory)
    result=n.merge_shards(p,cal,plan,list(reversed(outputs)),tmp_path/'merged')
    assert result['status']=='completed' and result['planned_rows']==result['completed_rows']==3072
    merged=json.loads((tmp_path/'merged/generations.json').read_text())
    assert [r['id'] for r in merged]==[r['id'] for r in p['main']]
    assert len(n.export_blind_views(p,merged))>0
    with pytest.raises(ValueError): n.merge_shards(p,cal,plan,outputs[:-1],tmp_path/'missing')
    assert not (tmp_path/'missing/generations.json').exists()
    # A failed extra invocation cannot be hidden by passing only the good dirs.
    n._exclusive_json(Path(plan['registry_root'])/'invocations'/'extra.json',{'output':str(tmp_path/'unknown'),'shard_index':0})
    with pytest.raises(ValueError): n.merge_shards(p,cal,plan,outputs,tmp_path/'bad')


def test_merge_rejects_changed_bytes_controls_slots_and_attempts(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);inventory=activate_plan(p,plan,tmp_path)
    outputs=completed_shards(p,cal,plan,tmp_path,inventory)
    genpath=outputs[0]/'generations.json';original=genpath.read_text();gens=json.loads(original);gens[0]['physical_slot']=7;genpath.write_text(json.dumps(gens))
    with pytest.raises(ValueError): n.merge_shards(p,cal,plan,outputs,tmp_path/'slot')
    genpath.write_text(original)
    attempt=outputs[0]/'attempts/000.json';attempt.write_text('{}')
    with pytest.raises(ValueError): n.merge_shards(p,cal,plan,outputs,tmp_path/'attempt')


def fake_execution(monkeypatch,p,cal):
    import torch
    from types import SimpleNamespace
    from component_analysis import hooks
    hf=SimpleNamespace(config=SimpleNamespace(use_cache=True),training=False)
    hf.eval=lambda:None
    monkeypatch.setattr(n,'runtime_identity',lambda _:cal['binding']['hardware'])
    monkeypatch.setattr(hooks,'load_analysis_model',lambda *a,**kw:object())
    monkeypatch.setattr(hooks,'_hf',lambda _:hf)
    monkeypatch.setattr(hooks,'device_and_dtype',lambda _:('cuda',torch.bfloat16))
    monkeypatch.setattr(hooks,'attention_implementation',lambda _:'sdpa')
    monkeypatch.setattr(torch.cuda,'max_memory_allocated',lambda:0)
    monkeypatch.setattr(torch.cuda,'max_memory_reserved',lambda:0)
    calls=[]
    def complete(model,rows,protocol):
        calls.append([r['id'] for r in rows]);result=[]
        for slot,r in enumerate(rows):
            result.append({'id':r['id'],'protocol_hash':p['scientific_hash'],'physical_slot':slot,'generated_ids':[p['payload']['eos'][0]],'logical_readouts':[r['length']-1],'finish':'eos','text':r['stem'],'status':'completed','controls':[{'control':name,'pass':True,'finite':True,'max_abs_error':0.,'identical_greedy':True,'tolerance':1e-5,'bitwise':True} for name in ('repeat','empty_hook')],'runtime':{'physical_forwards':3,'max_forward_seconds':.01,'control_seconds':.001}})
        return result
    monkeypatch.setattr(n,'complete_batch',complete)
    return calls


def test_shared_runtime_exact_global_slots_successor_and_tamper_stop(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);inventory=activate_plan(p,plan,tmp_path)
    calpath=tmp_path/'cal.json';calpath.write_text(json.dumps(cal));ops={**ops,'calibration_path':str(calpath)}
    out=tmp_path/'actual-shard';inv=json.loads(inventory.read_text());inv['outputs']=[str(out.resolve())];inventory.write_text(json.dumps(inv))
    calls=fake_execution(monkeypatch,p,cal)
    receipt=n.run_main_shard(p,out,ops,plan,0)
    assert receipt['completed_rows']==240 and len(calls)==30
    assert calls==[[r['id'] for r in p['main'][i:i+8]] for i in range(0,240,8)]
    rows=json.loads((out/'generations.json').read_text())
    assert [(r['global_batch_index'],r['physical_slot']) for r in rows]==[(i//8,i%8) for i in range(240)]
    assert (out/'attempts/029.json').exists()
    # Changed predecessor bytes must stop successor before model/rows, not only merge.
    (out/'generations.json').write_text('[]')
    second=tmp_path/'second';inv['outputs'].append(str(second.resolve()));inventory.write_text(json.dumps(inv))
    with pytest.raises(ValueError,match='drift'): n.run_main_shard(p,second,ops,plan,1)
    assert len(calls)==30 and not second.exists()


def test_runtime_attempted_failure_retains_ids_and_blocks_successors(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);inventory=activate_plan(p,plan,tmp_path)
    calpath=tmp_path/'cal.json';calpath.write_text(json.dumps(cal));ops={**ops,'calibration_path':str(calpath)}
    out=tmp_path/'failed';inv=json.loads(inventory.read_text());inv['outputs']=[str(out.resolve())];inventory.write_text(json.dumps(inv));fake_execution(monkeypatch,p,cal)
    def interrupted(model,rows,protocol):
        partial=[{'id':r['id'],'generated_ids':[7],'controls':[],'finish':'pending'} for r in rows]
        protocol['_checkpoint_batch'](partial,{'physical_forwards':1,'max_forward_seconds':.1,'control_seconds':0.})
        raise TimeoutError('test allocation deadline')
    monkeypatch.setattr(n,'complete_batch',interrupted)
    with pytest.raises(TimeoutError): n.run_main_shard(p,out,ops,plan,0)
    rows=json.loads((out/'generations.json').read_text())
    assert len(rows)==240 and sum(r['status']=='error' for r in rows)==8
    assert rows[0]['generated_ids']==[7] and rows[0]['global_batch_index']==0
    assert sum(r['status']=='unattempted' for r in rows)==232
    later=str((tmp_path/'later').resolve());inv['outputs'].append(later);inventory.write_text(json.dumps(inv))
    with pytest.raises(ValueError,match='failed'): n.claim_main_shard(p,plan,1,{'output':later,'operations_hash':'ops'})


def test_concurrent_claims_at_most_one_and_all_conflicts_recorded(protocol,tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);inventory=activate_plan(p,plan,tmp_path)
    outputs=[str((tmp_path/f'out{i}').resolve()) for i in range(2)]
    inv=json.loads(inventory.read_text());inv['outputs']=outputs;inventory.write_text(json.dumps(inv))
    def attempt(path):
        try: return n.claim_main_shard(p,plan,0,{'output':path,'operations_hash':'ops'})
        except ValueError: return None
    with ThreadPoolExecutor(max_workers=2) as executor: result=list(executor.map(attempt,outputs))
    assert sum(r is not None for r in result)==1
    assert len(n._registry_records(plan,'invocations'))==2
    assert len(n._registry_records(plan,'claims'))==1
    assert len(n._registry_records(plan,'outcomes'))==1


def test_shard_cli_dryrun_no_claim_and_merge_dryrun_no_generations(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);activate_plan(p,plan,tmp_path)
    paths={}
    for name,obj in [('protocol',p),('calibration',cal),('operations',ops),('plan',plan)]:
        path=tmp_path/(name+'.json');path.write_text(json.dumps(obj));paths[name]=path
    n.main(['--mode','main-shard','--protocol',str(paths['protocol']),'--operations',str(paths['operations']),'--calibration',str(paths['calibration']),'--shard-plan',str(paths['plan']),'--shard-index','0','--output',str(tmp_path/'dry'),'--dry-run'])
    assert not (Path(plan['registry_root'])/'claims').exists()
    dry=json.loads((tmp_path/'dry/dry-run.json').read_text())
    assert dry['model_loaded'] is False and dry['rows']==240
    assert dry['release_status']=='blocked_pending_actual_GPU_identity_verification'


def test_cli_source_preflight_failure_is_durably_registered(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);inventory=activate_plan(p,plan,tmp_path)
    out=tmp_path/'preflight';inv=json.loads(inventory.read_text());inv['outputs']=[str(out.resolve())];inventory.write_text(json.dumps(inv))
    # Source/protocol validation must happen after registration for an approved plan.
    p['main'][0]['truth_name']='drift'
    paths={}
    for name,obj in [('protocol',p),('calibration',cal),('operations',ops),('plan',plan)]:
        path=tmp_path/(name+'.json');path.write_text(json.dumps(obj));paths[name]=path
    with pytest.raises(ValueError):
        n.main(['--mode','main-shard','--protocol',str(paths['protocol']),'--operations',str(paths['operations']),'--calibration',str(paths['calibration']),'--shard-plan',str(paths['plan']),'--shard-index','0','--output',str(out)])
    assert len(n._registry_records(plan,'invocations'))==1
    assert list(n._registry_records(plan,'outcomes').values())[0]['status']=='failed'
    assert not out.exists()


def test_same_existing_output_cli_attempt_still_registers_conflict(protocol,tmp_path,monkeypatch):
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);inventory=activate_plan(p,plan,tmp_path)
    out=tmp_path/'existing';out.mkdir();inv=json.loads(inventory.read_text());inv['outputs']=[str(out.resolve())];inventory.write_text(json.dumps(inv))
    n.claim_main_shard(p,plan,0,{'output':str(out),'operations_hash':'old'})
    paths={}
    for name,obj in [('protocol',p),('calibration',cal),('operations',ops),('plan',plan)]:
        path=tmp_path/(name+'.json');path.write_text(json.dumps(obj));paths[name]=path
    with pytest.raises(ValueError): n.main(['--mode','main-shard','--protocol',str(paths['protocol']),'--operations',str(paths['operations']),'--calibration',str(paths['calibration']),'--shard-plan',str(paths['plan']),'--shard-index','0','--output',str(out)])
    assert len(n._registry_records(plan,'invocations'))==2
    assert len(n._registry_records(plan,'outcomes'))==1


@pytest.mark.parametrize('failure',['headroom','remaining'])
def test_shard_time_gates_stop_before_model(protocol,tmp_path,monkeypatch,failure):
    from datetime import datetime,timedelta,timezone
    from component_analysis import hooks
    p,cal,ops=shard_inputs(protocol,tmp_path,monkeypatch);plan=n.build_shard_plan(p,cal,ops);inventory=activate_plan(p,plan,tmp_path)
    calpath=tmp_path/'cal.json';calpath.write_text(json.dumps(cal));ops={**ops,'calibration_path':str(calpath)}
    if failure=='headroom': ops['allocation_start_utc']=(datetime.now(timezone.utc)-timedelta(seconds=1000)).isoformat()
    else: ops['deadline_utc']=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat()
    out=tmp_path/'timeblocked';inv=json.loads(inventory.read_text());inv['outputs']=[str(out.resolve())];inventory.write_text(json.dumps(inv));fake_execution(monkeypatch,p,cal)
    monkeypatch.setattr(hooks,'load_analysis_model',lambda *a,**kw:pytest.fail('time gate must precede model loading'))
    with pytest.raises(ValueError,match='headroom' if failure=='headroom' else 'forecast'): n.run_main_shard(p,out,ops,plan,0)
    assert not (out/'attempts').exists()
    assert list(n._registry_records(plan,'outcomes').values())[0]['status']=='failed'


def test_wrapper_binds_scheduler_start_instead_of_wrapper_entry(tmp_path):
    import os,subprocess,sys
    from datetime import datetime,timezone
    bindir=tmp_path/'bin';bindir.mkdir();scontrol=bindir/'scontrol';scontrol.write_text("#!/bin/sh\necho 'JobId=stub StartTime=2026-10-21T11:00:00 EndTime=2026-10-21T12:00:00'\n");scontrol.chmod(0o755)
    stub=tmp_path/'python-stub';stub.write_text('#!'+sys.executable+'\nimport os,json\nprint(json.dumps({k:os.environ[k] for k in ["SDR_NATIVE_ALLOCATION_START","SDR_NATIVE_ALLOCATION_END","SDR_NATIVE_WRAPPER_ENTRY"]}))\n');stub.chmod(0o755)
    env={**os.environ,'PATH':str(bindir)+':'+os.environ['PATH'],'SLURM_JOB_ID':'stub','SDR_NATIVE_PYTHON':str(stub),'TZ':'UTC'}
    env.pop('SLURM_JOB_START_TIME',None);env.pop('SLURM_JOB_END_TIME',None)
    result=subprocess.run(['bash',str(ROOT/'scripts/jobs/run_sdr_native_controls.sh'),'--dry-run'],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    timing=json.loads(result.stdout)
    assert int(timing['SDR_NATIVE_ALLOCATION_START'])==int(datetime(2026,10,21,11,tzinfo=timezone.utc).timestamp())
    assert int(timing['SDR_NATIVE_ALLOCATION_END'])-int(timing['SDR_NATIVE_ALLOCATION_START'])==3600
