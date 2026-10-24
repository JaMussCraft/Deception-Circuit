"""CPU contract tests; no model/API/notebook execution."""
from pathlib import Path
import importlib.util
import json
from types import SimpleNamespace
import pytest
import torch
ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def cc():
    path=ROOT/'scripts/sdr_cue_circuits.py'
    assert path.exists(), 'cue-circuit runner is not implemented'
    spec=importlib.util.spec_from_file_location('cue_circuit_test_module',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
@pytest.fixture
def fixtures():return json.loads((ROOT/'.superpowers/sdd/plan-sdr-cue-probe/freeze-final-5f74d0c/protocol.json').read_text())['fixtures']
def test_exact_named_panel_and_independent_example_order(cc,fixtures):
    rows=[r for f in fixtures[:8] for r in cc.factor_rows(f)]
    assert len(rows)==384 and len({r['prompt'] for r in rows})==384
    assert [r['factors']['task'] for r in rows[:3]]==['report','report','retrieval']
    for r in rows:
        f=r['factors'];p=r['pair'];noun='reading' if r['template']=='lab' else 'result'
        assert set(f)=={'record_order','question_order','truth','favored','task','example_order'}
        assert '.THE DAMAGING' in r['system'] and r['truth_name']==p[f['truth']]
        assert r['prompt'].startswith('<|begin_of_text|>') and r['prompt'].endswith(r['stem'])
        if f['task']=='report':assert r['user'].endswith(f'"The {noun} I will show you is {p[1-f["example_order"]]}".')
        else:assert f['example_order'] is None
def test_donor_involutions_and_exact_directed_pair_order(cc,fixtures):
    rows=[r for f in fixtures[:8] for r in cc.factor_rows(f)]
    for r in rows:r.update(ids=list(range(100)),length=100)
    pairs=cc.make_pairs(rows);by_id={r['id']:r for r in rows}
    assert len(pairs)==640 and [p['axis'] for p in pairs[:5]]==['E','T','E','T','T']
    lookup={(p['recipient_id'],p['axis']):p for p in pairs}
    for p in pairs:
        assert lookup[p['donor_id'],p['axis']]['donor_id']==p['recipient_id']
        a=by_id[p['recipient_id']]['factors'];b=by_id[p['donor_id']]['factors']
        assert [k for k in a if a[k]!=b[k]]==['example_order' if p['axis']=='E' else 'truth']
        assert p['position_map']==list(range(100))
def test_original_heads_and_coherent_ranked_controls(cc):
    families,bindings=cc.select_families();sets={k:{tuple(x) for x in v['heads']} for k,v in families.items()}
    assert [len(sets[k]) for k in ('D','H','F','S','A','B','J')]==[69,56,68,32,22,11,33]
    assert sets['J']==sets['A']|sets['B'] and not sets['A']&sets['B']
    assert sets['C_J']==sets['C_A']|sets['C_B'] and not sets['C_A']&sets['C_B']
    union=sets['D']|sets['H']|sets['F'];assert len(union)==103
    for k in ('D','H','F','S','A','B','J'):
        assert not sets['C_'+k]&union
        assert families[k]['layer_counts']==families['C_'+k]['layer_counts']
    assert len(bindings)==4
def test_prefix_pack_compact_immutable_dummy_and_generated_false(cc):
    key=('head',2,3);backing=torch.arange(8*224*256).reshape(8,224,256).float()
    bank=cc.pack_bank(SimpleNamespace(outputs={key:backing[:,:,:128]}),[key],[{'id':'a','length':5},{'id':'b','length':7}],'cpu')
    assert bank[key].value.is_contiguous() and bank[key].value.untyped_storage().nbytes()==8*224*128*4
    mask=bank[key].positions;assert mask.sum()==12 and not mask[2:].any() and not mask[0,5:].any()
    saved=bank[key].value.clone();backing.zero_();assert torch.equal(saved,bank[key].value)
    natural=torch.ones_like(saved)*-1;changed=cc.checked_assignment(natural,bank[key])
    assert torch.equal(changed[~mask],natural[~mask]) and torch.equal(changed[mask],saved[mask])
@pytest.mark.parametrize('change',['nan','inf','tolerance','greedy','dtype','shape'])
def test_full_vocabulary_failures(cc,change):
    a=torch.tensor([1.,0.,-1.]);b=a.clone()
    if change=='nan':b[-1]=float('nan')
    if change=='inf':b[-1]=float('inf')
    if change=='tolerance':b[-1]+=2e-5
    if change=='greedy':a=torch.tensor([0.,0.,-1.]);b=torch.tensor([0.,1e-7,-1.])
    if change=='dtype':b=b.double()
    if change=='shape':b=b[:2]
    with pytest.raises(ValueError):cc.compare_full(a,b)
def test_weighted_forecast_cold_once_warm_and_io_counts(cc):
    p={'payload':{'families':{k:{'heads':[['head',i,0]]} for i,k in enumerate(cc.FAMILY_ORDER)}}}
    counts=cc.operation_counts(p);assert sum(counts.values())==147648
    assert cc.WRITE_COUNTS==dict(attempt=1168,terminal=1168,progress=1170,metadata=3,assembly=1,emergency=1)
    c={'timings':{k:{'count':2,'cold':2.,'warm_max':1.} for k in counts},'io_timings':{k:{'cold':.2,'warm_max':.1,'count':8} for k in cc.WRITE_COUNTS},'startup_seconds':3.,'premodel_seconds':4.,'packing_max_seconds':.5,'final_audit_seconds':2.}
    c['main_audit']=dict(method=cc.AUDIT_METHOD,seconds=2.,rows=9344,batches=1168,controls=574208,cap=64);c['audit_read_timings']={k:dict(count=8,cold=.2,warm_max=.1) for k in ('attempt','terminal')}
    ops={k:5. for k in ('startup_buffer_seconds','premodel_headroom_seconds','shutdown_buffer_seconds','safety_margin_seconds')};ops['reserved_seconds']=1e7
    f=cc.forecast_main(p,c,ops);assert f['compute_seconds']==sum(2.+(n-1) for n in counts.values()) and f['margin_multiplier']==1.25
    c['timings'][next(iter(counts))]['count']=1
    with pytest.raises(ValueError,match='recurrent'):cc.forecast_main(p,c,ops)
def test_journal_reconstructs_attempted_incomplete_without_progress_inference(cc,tmp_path):
    ids=[str(i) for i in range(9344)];p={'scientific_hash':'f'*64,'payload':{'main':[{'id':x,'stem':'s'} for x in ids[:384]],'interventions':[{'id':x,'recipient_id':'0'} for x in ids[384:]]}}
    (tmp_path/'attempts').mkdir();(tmp_path/'terminals').mkdir();cc.exclusive_json(tmp_path/'attempts/0000.json',{'batch_id':'0000','row_ids':ids[:8]})
    rows=cc.reconstruct(p,tmp_path);assert len(rows)==9344 and [r['status'] for r in rows[:9]]==['attempted-incomplete']*8+['unattempted']
    with pytest.raises(ValueError,match='occupied'):cc.exclusive_json(tmp_path/'attempts/0000.json',{})
def test_indicator_anchors_and_full_zero_triples(cc):
    r={'pair':['a','b'],'factors':dict(truth=0,example_order=0,record_order=1,question_order=0,favored=1,task='report')};d={**r,'factors':{**r['factors'],'truth':1}}
    y=cc.indicators(dict(kind='commitment',candidate=1,format_ok=False),r,d)
    assert y['R']==0 and y['D']==1 and y['ER']==0 and y['ED']==0 and y['X1']==1
    y=cc.indicators(dict(kind='explicit_refusal',candidate=None,format_ok=True),r,d);assert y['R']==y['D']==0 and y['residual']==1
    c=cc.category_counts([]);assert len(c['triples'])==729 and len(c['transitions'])==81

def test_six_bounded_schemas_reject_unbounded_fields_and_overflow(cc):
    class Tokenizer:
        def __len__(self):return 3
        def decode(self,ids,**kwargs):return ['a','\\','☃'][ids[0]]
    payload={'main':[{'id':'x'*80,'stem':'s'*32}],'interventions':[{'id':'p'*25,'recipient_id':'x'*80}],'calibration':[{'id':'c'*23,'stem':'s'*32}],'families':{k:{'heads':[['head',1,0]]} for k in cc.FAMILY_ORDER}}
    bounds=cc.record_bounds(payload,Tokenizer())
    assert set(bounds['ceilings'])==set(cc.WRITE_COUNTS)
    for kind in cc.WRITE_COUNTS:
        sample=cc.maximum_record(kind,bounds,protocol={'payload':payload,'provenance':{'code_commit':'UNCOMMITTED'},'scientific_hash':'a'*64,'provenance_hash':'b'*64})
        assert len(cc.encoded(sample))<=bounds['ceilings'][kind]
        if kind!='metadata':cc.validate_record(kind,sample,bounds)
    bad=cc.maximum_record('attempt',bounds);bad['unbounded_trace']='x'
    with pytest.raises(ValueError):cc.validate_record('attempt',bad,bounds)
    bad=cc.maximum_record('assembly',bounds);bad[0]['raw_text']='x'*(bounds['limits']['text_bytes']+1)
    with pytest.raises(ValueError):cc.validate_record('assembly',bad,bounds)

def test_decode_sustains_prefix_every_step_and_repeats_patch(cc,monkeypatch):
    from component_analysis import hooks
    from scripts import sdr_routing_pilot
    key=('head',1,2);calls=[]
    class Tokenizer:
        def decode(self,ids,**kwargs):return ''.join(map(str,ids))
    monkeypatch.setattr(hooks,'device_and_dtype',lambda model:(torch.device('cpu'),torch.float32))
    def capture(model,ids,mask,*,components,replacements=None):
        calls.append((ids.clone(),mask.clone(),replacements))
        if replacements:
            assert torch.equal(replacements[key].positions[0],torch.arange(224)<3)
            assert not replacements[key].positions[1:].any()
        logits=torch.zeros(8,7);logits[:,2 if int(mask[0].sum())<5 else 6]=1
        outputs={key:torch.ones(8,224,128)}
        return SimpleNamespace(outputs=outputs,logits=logits)
    monkeypatch.setattr(hooks,'capture_forward',capture)
    monkeypatch.setattr(sdr_routing_pilot,'capture_logits',lambda model,c:c.logits)
    row=dict(id='r',ids=[1,2,3],length=3,stem='S',family='D')
    bank=cc.pack_bank(SimpleNamespace(outputs={key:torch.ones(8,224,128)}),[key],[row],'cpu')
    monkeypatch.setattr(cc,'EOS',[6])
    p={'scientific_hash':'f'*64,'payload':{'vocab_size':7},'_tokenizer':Tokenizer()}
    state=cc.decode_batch(object(),[row],p,replacements=bank)
    assert state['rows'][0]['generated_ids']==[2,2,6]
    assert state['rows'][0]['logical_readouts']==[2,3,4]
    assert len(calls)==6 and len(state['controls'])==3
    assert [int(c[1][0].sum()) for c in calls]==[3,3,4,4,5,5]
    assert torch.equal(bank[key].value,torch.ones(8,224,128))

def test_stress_exact_390_calls_and_261_checks_per_slot(cc,monkeypatch):
    from component_analysis import hooks
    from scripts import sdr_routing_pilot
    key=('head',1,2);calls=[]
    monkeypatch.setattr(hooks,'device_and_dtype',lambda model:(torch.device('cpu'),torch.float32))
    monkeypatch.setattr(hooks,'all_component_keys',lambda model:[key,hooks.READOUT_KEY])
    def capture(model,ids,mask,*,components,replacements=None):
        calls.append((int(mask[0].sum()),tuple(components),replacements))
        assert hooks.READOUT_KEY not in (replacements or {})
        return SimpleNamespace(outputs={key:torch.ones(8,224,128)},logits=torch.zeros(8,7))
    monkeypatch.setattr(hooks,'capture_forward',capture);monkeypatch.setattr(sdr_routing_pilot,'capture_logits',lambda m,c:c.logits)
    tokenizer=SimpleNamespace(decode=lambda ids,**kwargs:' test'*len(ids))
    rows=[dict(id=f'c{i}',ids=[1,2,3],length=3,stem='S',family='D') for i in range(8)]
    p={'scientific_hash':'f'*64,'payload':{'vocab_size':7},'_tokenizer':tokenizer}
    state=cc.decode_batch(object(),rows,p,stress=True,donor_rows=rows,family_keys=[key])
    assert len(calls)==390 and len(state['controls'])==112*261//14
    assert all(r['generated_ids']==[1296]*64 and r['finish']=='stress' for r in state['rows'])
    assert all(len(r['logical_readouts'])==64 for r in state['rows'])
    # Setup2, then ordinary6, full2, then next step. Full controls are after P-repeat.
    assert [c[0] for c in calls[:11]]==[3]*10+[4]
    assert calls[8][1]==(key,hooks.READOUT_KEY)
    assert calls[9][2][key].positions.sum()==24
    assert calls[-1][2][key].positions.sum()==8*66

def test_caught_kernel_failure_keeps_all_physical_ids(cc,monkeypatch):
    from component_analysis import hooks
    from scripts import sdr_routing_pilot
    monkeypatch.setattr(hooks,'device_and_dtype',lambda m:(torch.device('cpu'),torch.float32))
    count=[0]
    def forward(m,ids,mask,**kwargs):
        count[0]+=1;logits=torch.zeros(8,7)
        if count[0]==2:logits[0,6]=float('nan')
        return SimpleNamespace(logits=logits)
    monkeypatch.setattr(hooks,'capture_forward',forward);monkeypatch.setattr(sdr_routing_pilot,'capture_logits',lambda m,c:c.logits)
    rows=[dict(id=f'r{i}',ids=[1],length=1,stem='S') for i in range(8)]
    state={};p={'scientific_hash':'f'*64,'payload':{'vocab_size':7},'_tokenizer':SimpleNamespace(decode=lambda ids,**kw:'')}
    with pytest.raises(ValueError,match='finite'):cc.decode_batch(object(),rows,p,state=state)
    assert [r['id'] for r in state['rows']]==[r['id'] for r in rows]
    assert all(r['status']=='error' for r in state['rows'])

def test_blind_exact_view_dedup_join_and_finish_override(cc,tmp_path):
    main=[dict(id='r',pair=['a','b'],stem='S')];interventions=[dict(id='p',recipient_id='r')]
    bounds={'limits':dict(id_bytes=1,text_bytes=100)}
    p={'scientific_hash':'f'*64,'payload':dict(main=main,interventions=interventions,record_bounds=bounds)}
    gens=[cc.generation(dict(id=x,stem='S'),'f'*64,0,'completed') for x in ('r','p')]
    for g in gens:g.update(finish='eos',text='S a',raw_text='S a',continuation=' a',raw_continuation=' a',generated_ids=[1],logical_readouts=[1])
    views=cc.export_blind_views(p,gens);assert len(views)==1 and set(views[0])=={'view_id','text','options','finish'}
    paths=[]
    for person in ('fresh1','fresh2'):
        path=tmp_path/(person+'.json');doc=dict(annotator=person,fresh=True,independent=True,protocol_hash=p['scientific_hash'],views_hash=cc.digest(views),rubric_sha256=cc.cue.BRIEF_SHA,labels=[dict(view_id=views[0]['view_id'],kind='commitment',candidate=0,format_ok=False)])
        path.write_text(json.dumps(doc));paths.append(path)
    joined=cc.join_annotations(p,gens,paths);assert len(joined['rows'])==2 and joined['rows'][0]['candidate']==0
    doc=json.loads(paths[1].read_text());doc['labels'][0]['candidate']=True;paths[1].write_text(json.dumps(doc))
    with pytest.raises(ValueError,match='candidate'):cc.join_annotations(p,gens,paths)

def test_operations_source_hardware_and_nonfit_stop_before_model(cc):
    from datetime import datetime,timedelta,timezone
    ops={k:5. for k in cc.OP_FIELDS-{'hardware_class','deadline_utc'}};ops.update(hardware_class='H200',deadline_utc=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat())
    cc.validate_operations(ops)
    with pytest.raises(ValueError,match='fit'):cc._fit({'required_seconds':6.},ops)
    ops['unbounded']='x'
    with pytest.raises(ValueError,match='strict'):cc.validate_operations(ops)

def test_metadata_constructor_is_full_structure_with_finite_hash_and_ceiling_slots(cc):
    class Tokenizer:
        def __len__(self):return 1
        def decode(self,*args,**kwargs):return 'a'
    payload={'main':[{'id':'r','stem':'S'}],'interventions':[{'id':'i'}],'calibration':[{'id':'c','stem':'S'}]}
    provenance={'code_commit':'UNCOMMITTED','source_hashes':{'file.py':'1'*64},'cache':'/cache','software':{'python':'fixed'}}
    bounds=cc.record_bounds(payload,Tokenizer(),provenance)
    protocol={'payload':{**payload,'record_bounds':bounds},'scientific_hash':'a'*64,'provenance':provenance,'provenance_hash':'b'*64}
    maximum=cc.metadata_maximum(protocol,bounds)
    assert set(maximum)==set(protocol) and maximum['payload']['main']==payload['main']
    assert len(maximum['provenance']['code_commit'])==40
    assert all(x==999999999999999 for x in maximum['payload']['record_bounds']['ceilings'].values())
    assert cc._measure(maximum)[1]==bounds['metadata_protocol_hash']
    overall=cc.maximum_record('metadata',bounds,protocol=protocol)
    assert cc._measure(overall)==(bounds['ceilings']['metadata'],bounds['construction_hashes']['metadata'])
    assert len(cc.encoded(protocol))<=bounds['ceilings']['metadata']
    control=cc.maximum_record('terminal',bounds);control['controls'][0]['control']='patched_repeat'
    cc.validate_record('terminal',control,bounds)

@pytest.mark.parametrize('field', ['hash','capture_ids','capture_keys','attempt_family','timing_key','control_name'])
def test_nested_schema_fields_are_finite_or_exact_enums(cc,field):
    bounds={'limits':{'id_bytes':80,'text_bytes':100,'binding_bytes':4096},'ceilings':{k:999999999999999 for k in cc.WRITE_COUNTS}}
    kind='terminal';record=cc.maximum_record(kind,bounds)
    if field=='hash':record['controls'][0]['expected_sha256']='\0'*64
    if field=='capture_ids':record['captures'][0]['row_ids'][0]='x'*81
    if field=='capture_keys':record['captures'][0]['keys'][0]=['head',31,'x'*10000]
    if field=='attempt_family':kind='attempt';record=cc.maximum_record(kind,bounds);record['family']='x'*10000
    if field=='timing_key':record['timings']={'\0'*64:next(iter(record['timings'].values()))}
    if field=='control_name':record['controls'][0]['control']='\0'*14
    with pytest.raises(ValueError):cc.validate_record(kind,record,bounds)

@pytest.mark.parametrize('field', ['attempt_axis','attempt_phase','batch_id','capture_shape','capture_dtype','progress_phase','progress_hash','metadata_commit','metadata_extra','forecast_terms'])
def test_all_structural_fields_reject_unbounded_or_noncanonical_values(cc,field):
    bounds={'limits':{'id_bytes':80,'text_bytes':100,'binding_bytes':4096},'ceilings':{k:999999999999999 for k in cc.WRITE_COUNTS}}
    kind='terminal';record=cc.maximum_record(kind,bounds)
    if field.startswith('attempt_'):
        kind='attempt';record=cc.maximum_record(kind,bounds);record[field[8:]]='\0'*100
    if field=='batch_id':record['batch_id']='\0'*9
    if field=='capture_shape':record['captures'][0]['values'][0]['shape']=[8.,224.,128.]
    if field=='capture_dtype':record['captures'][0]['values'][0]['dtype']='\0'*14
    if field.startswith('progress_'):
        kind='progress';record=cc.maximum_record(kind,bounds);record['phase' if field.endswith('phase') else 'scientific_hash']='\0'*64
    if field.startswith('metadata_'):
        kind='metadata';record={'payload':{},'provenance':{'code_commit':'\0'*40},'scientific_hash':cc.digest({}),'provenance_hash':cc.digest({'code_commit':'\0'*40})}
        if field.endswith('extra'):record['payload']['extra']='x'*10000;record['scientific_hash']=cc.digest(record['payload'])
    if field=='forecast_terms':
        kind='metadata';record=cc._empty_forecast();record['counts']={'x':1};record['compute_terms']={'x':{'extra':'x'*10000}}
    with pytest.raises(ValueError):cc.validate_record(kind,record,bounds)

def test_metadata_ceiling_covers_explicit_operations_and_forecast_maxima(cc):
    class Tokenizer:
        def __len__(self):return 1
        def decode(self,*args,**kwargs):return 'a'
    payload={'main':[{'id':'r','stem':'S'}],'interventions':[{'id':'i'}],'calibration':[{'id':'c','stem':'S'}]}
    bounds=cc.record_bounds(payload,Tokenizer(),{'code_commit':'UNCOMMITTED'})
    assert hasattr(cc,'operational_maxima')
    for candidate in cc.operational_maxima():
        assert len(cc.encoded(candidate))<=bounds['ceilings']['metadata']

def test_complete_synthetic_panel_fixed_triples_interactions_and_natural_denominators(cc,fixtures):
    main=[r for f in fixtures[:8] for r in cc.factor_rows(f)]
    for row in main:row.update(length=100,ids=list(range(100)))
    pairs=cc.make_pairs(main)
    interventions=[dict(id=pair['id']+':'+family,pair_id=pair['id'],recipient_id=pair['recipient_id'],donor_id=pair['donor_id'],family=family) for family in cc.FAMILY_ORDER for pair in pairs]
    labels=[]
    for row in main:
        labels.append(dict(id=row['id'],view_id=cc.digest(row['id']),kind='commitment',candidate=row['factors']['truth'],format_ok=True,finish='eos'))
    for row in interventions:
        labels.append(dict(id=row['id'],view_id=cc.digest(row['id']),kind='explicit_refusal',candidate=None,format_ok=False,finish='eos'))
    p={'scientific_hash':'a'*64,'payload':dict(main=main,pairs=pairs,interventions=interventions,fixtures=fixtures)}
    joined={'protocol_hash':'a'*64,'rubric_sha256':cc.cue.BRIEF_SHA,'rows':labels}
    result=cc.analyze_panel(p,joined)
    assert len(result['row_audit'])==8960
    assert {key:value['n'] for key,value in result['natural'].items()}==dict(example_report=128,truth_report=128,truth_retrieval=64)
    assert result['natural']['example_report']['groups']['committed_same']==128
    assert result['natural']['truth_report']['groups']['committed_flip']==128
    for family in cc.FAMILY_ORDER:
        for axis_task,count in [('E/report',256),('T/report',256),('T/retrieval',128)]:
            summary=result['inventory'][family][axis_task]['overall']
            assert summary['n']==count and sum(summary['triples'].values())==count and len(summary['triples'])==729
            assert sum(summary['transitions'].values())==count and len(summary['transitions'])==81
            assert sum(summary['donor_output_groups'].values())==count
            assert summary['indicators']['R']['delta']==-1 and summary['indicators']['residual']['delta']==1
        assert result['report_E_minus_T'][family]['R']['E_minus_T']==0
        assert result['report_vs_retrieval_T'][family]['n']==128
        assert result['report_vs_retrieval_T'][family]['means']['R']['difference']==0
    interaction=result['interactions']['overall']['indicators']['R']
    assert interaction['target']==interaction['outside']==1 and interaction['difference']==0

def test_commit_rebind_and_fixed_width_source_hash_changes_preserve_science(cc):
    class Tokenizer:
        def __len__(self):return 1
        def decode(self,*args,**kwargs):return 'a'
    base={'main':[{'id':'r','stem':'S'}],'interventions':[{'id':'i'}],'calibration':[{'id':'c','stem':'S'}]}
    science=[]
    for commit,source in [('UNCOMMITTED','a'*64),('1'*40,'b'*64)]:
        payload=json.loads(json.dumps(base));provenance={'code_commit':commit,'source_hashes':{'script.py':source},'software':{'python':'fixed'},'cache':'/fixed/cache'}
        payload['record_bounds']=cc.record_bounds(payload,Tokenizer(),provenance);science.append(cc.digest(payload))
    assert science[0]==science[1]

def test_local_allocation_binding_retains_proposal_and_actual_bounds(cc):
    from datetime import datetime,timedelta,timezone
    now=datetime.now(timezone.utc);ops=dict(hardware_class='H200',reserved_seconds=3600,deadline_utc=(now+timedelta(hours=2)).isoformat(),startup_buffer_seconds=120,premodel_headroom_seconds=1200,shutdown_buffer_seconds=90,safety_margin_seconds=120)
    bound=cc.bind_allocation_operations(ops,allocation_start=now.timestamp()-5,allocation_end=now.timestamp()+3595)
    cc.validate_operations(bound)
    assert bound['proposal_hash']==cc.digest(ops) and bound['proposal_reserved_seconds']==3600
    assert bound['proposal_deadline_utc']==ops['deadline_utc']
    assert datetime.fromisoformat(bound['deadline_utc']).timestamp()==now.timestamp()+3595
    assert datetime.fromisoformat(bound['allocation_start_utc']).timestamp()==now.timestamp()-5
    assert bound['shutdown_buffer_seconds']==90


def test_forecast_requires_measured_full_main_audit_and_read_bounds(cc):
    p={'payload':{'families':{k:{'heads':[['head',i,0]]} for i,k in enumerate(cc.FAMILY_ORDER)}}};counts=cc.operation_counts(p)
    receipt={'timings':{k:dict(count=2,cold=1.,warm_max=1.) for k in counts},'io_timings':{k:dict(count=8,cold=.1,warm_max=.1) for k in cc.WRITE_COUNTS},'startup_seconds':1.,'premodel_seconds':1.,'packing_max_seconds':.1,'final_audit_seconds':.001}
    ops={k:1. for k in ('startup_buffer_seconds','premodel_headroom_seconds','shutdown_buffer_seconds','safety_margin_seconds')}
    with pytest.raises(ValueError,match='main.audit'):cc.forecast_main(p,receipt,ops)
    receipt['main_audit']=dict(method=cc.AUDIT_METHOD,seconds=10.,rows=9344,batches=1168,controls=574208,cap=64)
    receipt['audit_read_timings']={k:dict(count=8,cold=.2,warm_max=.1) for k in ('attempt','terminal')}
    forecast=cc.forecast_main(p,receipt,ops)
    assert forecast['audit_seconds']==10.+(.2+1167*.1)+(.2+2335*.1)
    assert forecast['audit_terms']['read_terms']['terminal']['count']==2336
    receipt['main_audit']['rows']=112
    with pytest.raises(ValueError,match='main.audit'):cc.forecast_main(p,receipt,ops)


def test_virtual_fullcap_main_journal_reuses_exact_reconstruction_and_control_audit(cc):
    protocol=json.loads((ROOT/'.superpowers/sdd/plan-sdr-cue-circuits/freeze-provisional-resume/protocol.json').read_text())
    # Geometry is unchanged; short permitted strings keep this regression small.
    protocol['payload']['record_bounds']['limits']['text_bytes']=3
    reader,paths=cc.synthetic_main_reader(protocol)
    rows,count=cc._coverage(protocol,Path('.'),calibration=False,reader=reader,paths=paths)
    assert len(rows)==9344 and len(paths['attempts'])==len(paths['terminals'])==1168
    assert count==574208 and all(len(row['generated_ids'])==64 and row['finish']=='capped' for row in rows)
    damaged=paths['terminals'][48]
    def bad_reader(path):
        value=reader(path)
        if Path(path)==damaged:value['controls'].pop()
        return value
    with pytest.raises(ValueError,match='exact numerical coverage'):
        cc._coverage(protocol,Path('.'),calibration=False,reader=bad_reader,paths=paths)


def test_real_branch_fake_calibration_and_main_validate_metadata_and_fixed_journal_counts(cc,monkeypatch,tmp_path):
    from datetime import datetime,timedelta,timezone
    from collections import Counter
    from component_analysis import hooks
    protocol=json.loads((ROOT/'.superpowers/sdd/plan-sdr-cue-circuits/freeze-provisional-resume/protocol.json').read_text())
    protocol['provenance']['code_commit']='1'*40
    class Tokenizer:
        def __len__(self):return 1
        def decode(self,*args,**kwargs):return 'a'
    payload=protocol['payload'];payload.pop('record_bounds');payload['record_bounds']=cc.record_bounds(payload,Tokenizer(),protocol['provenance'])
    protocol['scientific_hash']=cc.digest(payload);protocol['provenance_hash']=cc.digest(protocol['provenance'])
    now=datetime.now(timezone.utc)
    ops=dict(hardware_class='H200',reserved_seconds=3600,deadline_utc=(now+timedelta(hours=1)).isoformat(),startup_buffer_seconds=120,premodel_headroom_seconds=1200,shutdown_buffer_seconds=90,safety_margin_seconds=120)
    monkeypatch.setenv('SDR_CC_ALLOCATION_START',str(now.timestamp()-5));monkeypatch.setenv('SDR_CC_ALLOCATION_END',str(now.timestamp()+3590))
    monkeypatch.setattr(cc,'verify_protocol',lambda p:None)
    monkeypatch.setattr(cc.n,'runtime_identity',lambda o:dict(memory=10**12,name='FAKE H200'))
    monkeypatch.setattr(cc.n,'load_tokenizer',lambda cache:Tokenizer())
    hf=SimpleNamespace(config=SimpleNamespace(use_cache=True,vocab_size=7));monkeypatch.setattr(cc.cue,'_load_model',lambda p:(object(),hf))
    monkeypatch.setattr(torch.cuda,'reset_peak_memory_stats',lambda:None);monkeypatch.setattr(torch.cuda,'max_memory_allocated',lambda:1024)
    stored={};writes=[];bounds=payload['record_bounds'];real_reconstruct=cc.reconstruct
    def publish(path,kind,value,limits,**kwargs):
        cc.validate_record(kind,value,limits)
        key=str(path)
        if not kwargs.get('replace') and key in stored:raise ValueError('occupied immutable fake journal')
        stored[key]=cc.canonical(value);writes.append((key,kind));return .000001
    def read(path):return json.loads(stored[str(path)])
    def reconstruction(p,journal,*,calibration=False,reader=None,paths=None):
        inventory={kind:sorted(Path(key) for key in stored if Path(key).parent==Path(journal)/kind) for kind in ('attempts','terminals')}
        return real_reconstruct(p,journal,calibration=calibration,reader=reader or read,paths=inventory)
    monkeypatch.setattr(cc,'publish',publish);monkeypatch.setattr(cc,'read_json',read);monkeypatch.setattr(cc,'reconstruct',reconstruction)
    monkeypatch.setattr(cc,'benchmark_io',lambda *args:({kind:dict(count=8,cold=.000001,warm_max=.000001) for kind in cc.WRITE_COUNTS},.000048))
    monkeypatch.setattr(cc,'benchmark_main_audit',lambda *args:(dict(method=cc.AUDIT_METHOD,seconds=.001,rows=9344,batches=1168,controls=574208,cap=64),{kind:dict(count=8,cold=.000001,warm_max=.000001) for kind in ('attempt','terminal')}))
    monkeypatch.setattr(cc,'file_hash',lambda path:bounds['construction_hashes'][Path(path).name.split('-')[1]])
    def decode(model,rows,runtime,*,stress,donor_rows,family_keys,timer,state):
        family=rows[0].get('family') or '';out=[];controls=[]
        for slot,original in enumerate(rows):
            row=cc.generation(original,protocol['scientific_hash'],slot,'completed');tokens=[1296]*64 if stress else [cc.EOS[0]]
            row.update(generated_ids=tokens,logical_readouts=list(range(original['length']-1,original['length']-1+len(tokens))),finish='stress' if stress else 'eos');out.append(row)
            for step in range(len(tokens)):
                names=('repeat','empty','self','patched_repeat') if stress else ('patched_repeat',) if family else ('repeat','empty')
                for name in names:
                    controls.append(dict(row_id=original['id'],control=name,step=step,family=family,finite=True,bitwise=True,max_abs_error=0.,identical_greedy=True,tolerance=1e-5,expected_sha256='f'*64,observed_sha256='f'*64))
            if stress:
                for name,step in [('setup_capture',0),('full_capture',0),('full_self',0),('full_capture',63),('full_self',63)]:
                    controls.append(dict(row_id=original['id'],control=name,step=step,family=family,finite=True,bitwise=True,max_abs_error=0.,identical_greedy=True,tolerance=1e-5,expected_sha256='f'*64,observed_sha256='f'*64))
        captures=[]
        if family:
            for bank,source in [('donor',donor_rows)]+([('recipient',rows)] if stress else []):
                captures.append(dict(bank=bank,family=family,row_ids=[r['id'] for r in source],keys=[list(k) for k in family_keys],values=[dict(key=list(k),shape=[8,224,128],dtype='torch.bfloat16',sha256='f'*64,positions_sha256='f'*64) for k in family_keys]))
        readout=[hooks.READOUT_KEY]
        counts={cc.signature(readout,[],'plain'):128 if stress else 2 if not family else 0,cc.signature(readout,[],'empty'):64 if stress else 1 if not family else 0}
        if family:
            counts[cc.signature(list(family_keys)+readout,[],'plain')]=2 if stress else 1
            counts[cc.signature(readout,list(family_keys),'replace')]=192 if stress else 2
        if stress:counts[cc.digest('full_capture')]=2;counts[cc.digest('full_self')]=2
        for key,count in counts.items():
            for _ in range(count):timer.record(key,.000001)
        state.update(rows=out,controls=controls,captures=captures,packing_seconds=.000001,error='')
    monkeypatch.setattr(cc,'decode_batch',decode)
    calibration=tmp_path/'calibration';receipt=cc.run(protocol,ops,calibration,calibration=True)
    assert receipt['status']=='completed' and receipt['physical_forwards']==5460 and receipt['numerical_pass']
    assert Counter(kind for path,kind in writes)==dict(metadata=3,progress=16,attempt=14,terminal=14,assembly=1)
    bound=read(calibration/'operations.json');assert bound['proposal_hash']==cc.digest(ops) and bound['deadline_utc']==bound['allocation_end_utc']
    writes.clear();main=tmp_path/'main';result=cc.run(protocol,ops,main,calibration=False,calibration_dir=calibration)
    assert result['status']=='completed' and len(read(main/'generations.json'))==9344
    assert Counter(kind for path,kind in writes)==dict(metadata=3,progress=1170,attempt=1168,terminal=1168,assembly=1)
    assert len(read(calibration/'generations.json'))==112 and hf.config.use_cache is True

def test_changed_forecast_maximum_obeys_its_own_strict_nested_schema(cc):
    forecast=cc.operational_maxima()[1]
    cc.validate_forecast(forecast)
    assert set(forecast['audit_terms']['read_terms'])=={'attempt','terminal'}

def test_allocation_binding_uses_serialized_timestamp_precision(cc):
    from datetime import datetime,timedelta,timezone
    now=datetime.now(timezone.utc);ops=dict(hardware_class='H200',reserved_seconds=3600,deadline_utc=(now+timedelta(hours=2)).isoformat(),startup_buffer_seconds=120,premodel_headroom_seconds=1200,shutdown_buffer_seconds=90,safety_margin_seconds=120)
    cc.bind_allocation_operations(ops,allocation_start=now.timestamp()-5.1234567,allocation_end=now.timestamp()+3500.9876543)
