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
