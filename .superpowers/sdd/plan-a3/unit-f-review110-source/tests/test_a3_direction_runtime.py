"""Direction runtime contracts with tiny CPU-only injected execution."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
import torch


def runtime():
    from component_analysis import a3_direction_runtime
    return a3_direction_runtime


@pytest.mark.parametrize('args',[
    ['--stage','fit','--action','freeze'],
    ['--stage','assess','--panel','assessment','--final'],
    ['--stage','pilot','--action','capture'],
    ['--stage','select','--action','score','--panel','calibration'],
    ['--stage','prepare','--action','inventory','--inventory-stage','unknown'],
])
def test_unknown_stage_combinations_reject_before_io(args,tmp_path):
    with pytest.raises((ValueError,SystemExit)):
        runtime().main(['--experiment','directions','--design',str(tmp_path/'absent'),
            '--commit','a'*40,'--work-dir',str(tmp_path),*args])
    assert list(tmp_path.iterdir())==[]


def test_capture_adapter_complete_train_cache_from_real_runner_sink(tmp_path,monkeypatch):
    from tests.test_a3_direction_fit import fixture
    from component_analysis import a3_direction_runner as runner
    p,d,pr,cache,metadata,arrays=fixture(tmp_path)
    def capture(model,batches,*,sites,sink,identity):
        assert identity['numeric_profile']==pr['fit_cache']['capture_identity']['numeric_profile']
        for b in batches:
            rows=[]
            for rid in b.ids:
                j=d['tasks']['far_v2']['fit_ids'].index(rid)
                s=('clean','corrupt').index(b.stream)
                rows.append(dict(task=b.task,condition=b.condition,stream=b.stream,instance_id=rid,
                    record=b.records[0],heads=[dict(site=sites[0],value=torch.tensor(arrays['t0_s0_'+b.condition][j,s]))]))
            sink(dict(identity=identity,rows=rows,projections=[dict(site=sites[0],value=torch.eye(2))]))
    monkeypatch.setattr(runner,'capture_readouts',capture)
    # Source fixture omits labels; only the source row resolver is injected.
    from tests.test_a3_direction_runner import batch
    def batches(design,source,split,ids,condition,stream,profile):
        b=batch(stream)
        from dataclasses import replace
        return [replace(b,ids=[rid],input_ids=b.input_ids[:1],attention_mask=b.attention_mask[:1],
            readout=b.readout[:1],opposite_token=b.opposite_token[:1],honest_token=b.honest_token[:1],
            expected_token=b.expected_token[:1],condition=condition,records=[dict(instance_id=rid)]) for rid in ids]
    out=runtime().capture_fit_cache(object(),d,pr,output=tmp_path/'produced',batch_resolver=batches)
    actual,stored=p.artifacts.read_bundle(tmp_path/'produced',expected=metadata)
    assert actual==out==metadata
    assert all(np.array_equal(stored[k],v) for k,v in arrays.items())
    p.fit_from_cache(d,tmp_path/'produced',protocol=pr,output=tmp_path/'fitted')


def test_capture_adapter_rejects_duplicate_or_missing_membership(tmp_path,monkeypatch):
    from tests.test_a3_direction_fit import fixture
    from component_analysis import a3_direction_runner as runner
    p,d,pr,cache,metadata,arrays=fixture(tmp_path)
    monkeypatch.setattr(runner,'capture_readouts',lambda *a,**kw:None)
    with pytest.raises(ValueError,match='capture coverage'):
        runtime().capture_fit_cache(object(),d,pr,output=tmp_path/'bad',batch_resolver=lambda *a:[])
    assert not (tmp_path/'bad').exists()


def test_loaded_selected_axis_preserves_numeric_identity(tmp_path):
    from tests.test_a3_direction_selection import selection_fixture
    p,d,pr,root,fits=selection_fixture(tmp_path)
    protocol_file=tmp_path/'protocol.json'; p.artifacts.ladder.write_artifact(protocol_file,pr)
    selected=p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected',protocol_path=protocol_file)
    axes=runtime().load_selected_axes(tmp_path/'selected',selected)
    from component_analysis.a3_direction_runner import axis_identity
    assert len(axes)==3*(1+199+32+1)
    for name,axis in axes.items():
        assert axis_identity(axis)==selected['axes'][name]['sha256']
        assert 'pinv' in axis and 'id_weights' in axis


def test_completed_object_bytes_and_partial_rejection(tmp_path):
    r=runtime(); obj={'kind':'example','value':[1,2]}
    r.publish_object(tmp_path/'object',obj)
    assert r.read_object(tmp_path/'object')==obj
    (tmp_path/'object'/'payload.json').write_text('{"kind":"example","value":[1,2]} ')
    with pytest.raises(ValueError): r.read_object(tmp_path/'object')
    partial=tmp_path/'partial'; partial.mkdir(); (partial/'payload.json').write_text('{}')
    with pytest.raises(ValueError): r.read_object(partial)


def ledger_fixture(tmp_path,identity=None,inventory_sha=None):
    tmp_path.mkdir(parents=True,exist_ok=True)
    inventory_sha=inventory_sha or "c"*64
    r=runtime(); path=tmp_path/'ledger.json'
    ledger=dict(reservations=[dict(id='r-1',job_id='100',cluster='delta',account='a',partition='p',gpus=1,
        requested_minutes=12,reserved_gpu_hours=.2,actual_seconds=30,source_commit='a'*40,output_dir='/output',status='completed',manifest_hash='b'*64)])
    path.write_text(json.dumps(ledger))
    original=dict(kind='a3_root_fit_admission_v1',id='fit-admission',identity=identity or {'injected':True},upper_inventory_sha256=inventory_sha,
        max_gpu_hours=.4,reservation_ids=['r-1'])
    original['admission_sha256']=r.workload.digest(original)
    r.publish_object(tmp_path/'admission',original)
    import time
    start=time.time()-30
    r.publish_object(tmp_path/'allocation',dict(kind='a3_injected_slurm_allocation_v1',injected=True,job_id='100',cluster='delta',account='a',partition='p',gpus=1,
        state='RUNNING',start_time_unix=start,end_time_unix=start+720,time_limit_seconds=720))
    entry=dict(reservation_id='r-1',experiment='A3',phase='M2',subphase='directions',inventory_sha256=inventory_sha,
        original_reserved_gpu_hours=.2,actual_entry=copy.deepcopy(ledger['reservations'][0]),reservation_lineage=dict(
            admission_id=original['id'],admission_sha256=original['admission_sha256'],upper_inventory_sha256=inventory_sha,max_gpu_hours=.4,reserved_gpu_hours=.2))
    mapping=dict(kind='a3_root_ledger_mapping_v1',ledger_path=str(path),ledger_sha256=r.common.file_hash(path),
        expected_entry_ids=['r-1'],entries=[entry],original_admission_paths=[str(tmp_path/'admission')],
        storage_capacities={'host_ram':{'pool':'ram','available_bytes':100}},contingency_gpu_hours=6,max_age_seconds=900)
    r.publish_object(tmp_path/'mapping',mapping)
    return r,tmp_path/'mapping',path,ledger,mapping


def test_actual_ledger_schema_charges_original_reservation_even_when_completed(tmp_path):
    r,mapping,path,ledger,_=ledger_fixture(tmp_path)
    normalized=r.normalize_ledger(mapping,identity={'injected':True},injected=True)
    assert normalized['entries'][0]['reserved_gpu_hours']==.2
    assert normalized['entries'][0]['actual_gpu_hours']==pytest.approx(30/3600)
    assert normalized['entries'][0]['state']=='completed'
    assert normalized['original_admissions'][0]['max_gpu_hours']==.4


@pytest.mark.parametrize('damage',['bytes','missing','reserved','unrelated'])
def test_actual_ledger_mutations_fail_closed(tmp_path,damage):
    r,mapping,path,ledger,m=ledger_fixture(tmp_path)
    if damage=='bytes': path.write_text(path.read_text()+' ')
    else:
        if damage=='missing': m['expected_entry_ids']=[]
        if damage=='reserved': m['entries'][0]['original_reserved_gpu_hours']=.01
        if damage=='unrelated': m['entries'][0]['actual_entry']['output_dir']='other'
        r.publish_object(tmp_path/'changed',m); mapping=tmp_path/'changed'
    with pytest.raises(ValueError): r.normalize_ledger(mapping,identity={'injected':True},injected=True)


from tests.test_a3_direction_runner import fake


def test_measured_packing_target_reuse_keeps_inputs_distinct(tmp_path,fake):
    from dataclasses import replace
    from tests.test_a3_direction_runner import batch,identity,axis,cell,SITE
    from component_analysis import a3_directions
    from tests.test_a3_direction_runner import measured_setup
    r=runtime(); ident,index,axes,measured_cells=measured_setup(fake); b=batch()
    receipt=ident['packed_equivalence']; ident.pop('packed_equivalence')
    cells=[measured_cells[1]]
    evidence=r.packing_evidence(receipt,[b])
    measured=dict(profile=ident['numeric_profile'],timing_inputs=[],axis_scope=[])
    r.publish_object(tmp_path/'measured',dict(evidence=evidence,measurement=measured,injected=True))
    target=replace(b,ids=['target-a','target-b'])
    target_identity=copy.deepcopy(ident)
    r.freeze_profile_reuse(tmp_path/'reuse',measured_path=tmp_path/'measured',batch=target,
        cells=cells,axes=axes,capture_index={},policy=r.workload.PROFILE_REUSE_POLICY)
    target_identity['profile_reuse']=str(tmp_path/'reuse')
    captured=[]
    r.runner.capture_readouts(object(),[target],sites=[SITE],sink=captured.append,identity=target_identity)
    reuse=r.read_object(tmp_path/'reuse')
    assert reuse['target_rows_are_measured'] is False
    assert r.read_object(tmp_path/'measured')['evidence']['runner_receipt']==receipt
    assert [v['instance_id'] for v in captured[0]['rows']]==target.ids
    same=r.freeze_profile_reuse(tmp_path/'same-input-reuse',measured_path=tmp_path/'measured',batch=b,
        cells=cells,axes=axes,capture_index={},policy=r.workload.PROFILE_REUSE_POLICY)
    assert same['target_rows_are_measured'] is True and same['target_execution_is_pilot'] is False
    with pytest.raises(ValueError,match='target'):
        r.runner.capture_readouts(object(),[replace(target,ids=['other-a','other-b'])],sites=[SITE],sink=lambda x:None,identity=target_identity)
    with pytest.raises(ValueError):
        r.runner.capture_readouts(object(),[target],sites=[SITE],sink=lambda x:None,identity=ident)


def test_interrupted_restart_equals_uninterrupted_and_refreshes_before_skip(tmp_path):
    from tests.test_a3_direction_artifacts import scientific_metadata
    r=runtime(); identity=scientific_metadata()['identity']
    capture=scientific_metadata(); r.artifacts.write_bundle(tmp_path/'capture',capture,{})
    identity=copy.deepcopy(identity); identity['capture_lineage']=[r.artifacts.capture_reference(tmp_path/'capture',expected=capture)]
    def key(i): return ['assessment','far_v2','far_v2','assessment',42,['head',7,16],'learned',0,'zero',str(i),'D','clean']
    inv={'shards':[dict(shard_id=str(i),expected_keys=[key(i)]) for i in range(3)]}
    calls=[]
    def producer(shard):
        calls.append(shard['shard_id'])
        if shard['shard_id']=='1' and len(calls)==2: raise RuntimeError('interrupted')
        return [dict(zip(r.artifacts.KEY_FIELDS,shard['expected_keys'][0]))],{'injected':True}
    guard_calls=[]
    with pytest.raises(RuntimeError,match='interrupted'):
        r.execute_shards(inv,tmp_path/'partial',identity=identity,producer=producer,guard=lambda:guard_calls.append(1))
    assert (tmp_path/'partial'/'0'/'COMPLETE.json').is_file()
    r.execute_shards(inv,tmp_path/'partial',identity=identity,producer=producer,guard=lambda:guard_calls.append(1),resume=True)
    r.execute_shards(inv,tmp_path/'full',identity=identity,producer=producer,guard=lambda:None)
    a=r.artifacts.read_completed_shards(inv,tmp_path/'partial',identity=identity)
    b=r.artifacts.read_completed_shards(inv,tmp_path/'full',identity=identity)
    assert a==b and len(guard_calls)==8
    def collision(): raise ValueError('live protected collision')
    with pytest.raises(ValueError,match='protected'):
        r.execute_shards(inv,tmp_path/'partial',identity=identity,producer=lambda x:pytest.fail('no model'),guard=collision,resume=True)


def test_dummy_execution_aliases_preserve_source_bytes_and_scientific_ids():
    from tests.test_a3_direction_workload import fixture
    r=runtime();d,p,s=fixture()
    rows=d['access_rows']['far_v2']
    for row in rows:
        row['task']='far_v2'; row.update(expected_token=1,honest_token=2,opposite_token=1)
        for stream in row['streams'].values():
            stream.update(layout=None,expected_token=1,honest_token=2,opposite_token=1)
    ident=dict(padded_width=4,physical_batch_size=4,axis_tile_size=2)
    real=d['tasks']['far_v2']['assessment_ids'][0]
    batch=r.source_batches(d,'far_v2','assessment',[real,'a3-dummy:test'],'D','clean',ident,dummy_sources={'a3-dummy:test':real})[0]
    assert batch.ids==[real,'a3-dummy:test']
    assert torch.equal(batch.input_ids[0],batch.input_ids[1])
    assert batch.records[1]['execution_dummy']['duplicate_of']==real
    assert batch.records[1]['execution_dummy']['source_sha256']==r.workload.digest(next(x for x in rows if x['condition']=='D' and x['instance_id']==real))
    assert all(not x['instance_id'].startswith('a3-dummy:') for x in d['access_rows']['far_v2'])


def test_proposal_is_not_execution_authority(tmp_path):
    r=runtime(); r.publish_object(tmp_path/'proposal',{'kind':'a3_direction_cost_proposal','admitted':True,'execution_authorized':False})
    with pytest.raises(ValueError,match='root reservation'):
        r.validate_reservation(tmp_path/'proposal',ledger={},inventory={},work_dir=tmp_path,injected=True)


def test_actual_tiny_runtime_shard_runs_positive_replays_and_atomic_restart(tmp_path):
    import sys
    if sys.version_info[:2] < (3,12):
        pytest.skip('pinned NNsight real hooks require mgnp; base retains contract tests')
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    from tests.helpers import tiny_config
    from tests.test_a3_direction_artifacts import scientific_metadata
    from tests.test_a3_direction_workload import fixture
    from component_analysis import hooks,a3_directions
    r=runtime();torch.manual_seed(92)
    model=NNsight(LlamaForCausalLM(tiny_config(attn_implementation='sdpa')).eval())
    d,_,_=fixture(); task='far_v2'; site=['head',0,0]
    for row in d['access_rows'][task]:
        row.update(task=task,source_id=row['instance_id'],source_hash='d'*64)
        for stream,record in row['streams'].items():
            record.update(layout=None,expected_token=1,honest_token=2,opposite_token=1)
            if stream=='corrupt': record['tokens']=[3,2,1]
    source=scientific_metadata()['identity']; d.update(a1_identity=source['a1_identity'],parent_evidence=source['parent_evidence'])
    profile=dict(padded_width=4,physical_batch_size=1,axis_tile_size=1,dtype='torch.float32',backend='sdpa',
        model=source['model'],model_revision=source['model_revision'],source_sha256=r.ladder.design._hash(source['code_hashes']))
    pr=dict(commit=source['commit'],code_hashes=source['code_hashes'],fit_cache=dict(capture_identity={k:source[k] for k in r.pipeline.IDENTITY_SOURCE_FIELDS}))
    width=hooks.geometry(model)['head_dim']; projection=hooks.o_proj_weight(model,0)[:,:width].detach().float().cpu()
    ax=a3_directions.prepare_image_direction(projection,projection[:,0]/projection[:,0].norm(),torch.randn(3,width),id_weights=torch.ones(3)/3)
    rid=d['tasks'][task]['assessment_ids'][0]
    key=['assessment',task,task,'assessment',42,site,'learned',0,'zero',rid,'D','clean']
    shard=dict(shard_id='tiny',expected_keys=[key],profile=profile,instance_ids=[rid],execution_ids=[rid],dummy_sources={},
        cells=[dict(seed=42,site=site,family='learned',axis_index=0,operation='zero',axis='x')],split='assessment',panel='assessment')
    rows,evidence,ident=r.score_runtime_shard(model,d,pr,shard,axes={'x':ax},output=tmp_path/'runtime',guard=lambda:None)
    assert len(rows)==1 and rows[0]['gate_valid'] and rows[0]['positive_control']['valid']
    assert set(rows[0]['replay_errors'])=={'empty','head_self','zero_coefficient'}
    r.artifacts.publish_shard(tmp_path/'published'/'tiny',identity=ident,expected_keys=[key],rows=rows,execution=evidence)
    assert r.artifacts.read_completed_shards({'shards':[shard]},tmp_path/'published',identity=ident)==rows


def test_cpu_solve_dry_run_checks_cache_without_fit_or_writes(tmp_path,monkeypatch):
    from tests.test_a3_direction_fit import fixture
    p,d,pr,cache,_,_=fixture(tmp_path)
    r=runtime();d.update(direction_protocol=pr,direction_protocol_sha256=r.ladder.design._hash(pr))
    # Fit contract hashes the unattached core, preserving fixture cache identity.
    path=tmp_path/'design.json';r.ladder.write_artifact(path,d)
    monkeypatch.setattr(r.artifacts,'validate_live',lambda *a,**kw:{'injected':True})
    monkeypatch.setattr(p,'fit_from_cache',lambda *a,**kw:pytest.fail('dry run fit'))
    before=set(tmp_path.iterdir())
    assert r.main(['--experiment','directions','--stage','fit','--action','solve','--design',str(path),
        '--commit',pr['commit'],'--work-dir',str(tmp_path),'--fit-cache',str(cache),'--dry-run'],
        model_loader=lambda *a:pytest.fail('dry run loader'))==0
    assert set(tmp_path.iterdir())==before


def test_generic_authority_reader_keeps_mask_proposals_nonauthorizing(tmp_path):
    r=runtime();r.publish_object(tmp_path/'proposal',{'kind':'a3_mask_cost_proposal','execution_authorized':False})
    with pytest.raises(ValueError,match='root reservation'):
        r.validate_reservation(tmp_path/'proposal',ledger={},inventory={},work_dir=tmp_path,injected=True,
            subphase='masks',inventory_validator=lambda _:None,subphase_limits={'M4':11})


def test_capture_shards_restart_and_refuse_partial_assembly(tmp_path,monkeypatch):
    from tests.test_a3_direction_fit import fixture
    r=runtime();p,d,pr,cache,metadata,arrays=fixture(tmp_path)
    profile=pr['fit_cache']['capture_identity']['numeric_profile']
    caps=[]
    for c in p.CONDITIONS:
        for stream in p.STREAMS:
            for rid in d['tasks']['far_v2']['fit_ids']:
                caps.append(dict(capture_id=f'{c}_{stream}_{rid}',source_task='far_v2',split='train',condition=c,stream=stream,
                    instance_ids=[rid],sites=[['head',7,16]],profile=profile))
    inv=dict(capture_shards=[dict(shard_id=c['capture_id'],capture=c) for c in caps])
    # Pure fixture producer writes actual numeric runner rows; assembly exercises
    # byte readers and exact original source membership independently of runner.
    def piece(model,batches,sites,identity,path,*,guard):
        key=Path(path).parent.name
        cap=next(c for c in caps if c['capture_id']==key)
        j=d['tasks']['far_v2']['fit_ids'].index(cap['instance_ids'][0]);st=p.STREAMS.index(cap['stream'])
        row=dict(profile_id=r.runner.profile_identity(identity),task='far_v2',condition=cap['condition'],stream=cap['stream'],
            instance_id=cap['instance_ids'][0],record=p._selection_source_record(next(x for x in d['access_rows']['far_v2'] if x['condition']==cap['condition'] and x['instance_id']==cap['instance_ids'][0]),cap['stream'],'far_v2'),
            heads=[dict(site=sites[0],array='head')],clause_summary={'heads':[]})
        meta=dict(schema_version=1,kind='a3_readout_chunk',split='train',injected=True,identity=identity,runner_rows=[row],
            projection_arrays=[dict(site=sites[0],array='projection')])
        r.artifacts.write_bundle(path,meta,{'head':arrays['t0_s0_'+cap['condition']][j,st],'projection':np.eye(2,dtype='float32')})
        return {},r.artifacts.capture_reference(path,expected=meta)
    monkeypatch.setattr(r,'_capture_bundle',piece)
    monkeypatch.setattr(r,'source_batches',lambda *a,**kw:[])
    r.run_fit_capture(object(),d,pr,inv,root=tmp_path/'run',guard=lambda:None,shard_id=caps[0]['capture_id'])
    assert not (tmp_path/'run'/'cache'/'fit-selection').exists()
    with pytest.raises(ValueError,match='incomplete'):
        r.assemble_fit_pieces(d,pr,inv,root=tmp_path/'run')
    r.run_fit_capture(object(),d,pr,inv,root=tmp_path/'run',guard=lambda:None,resume=True)
    _,actual=r.artifacts.read_bundle(tmp_path/'run'/'cache'/'fit-selection',expected=metadata)
    assert all(np.array_equal(actual[k],v) for k,v in arrays.items())


def test_calibration_stage_dispatch_filters_shards_before_any_resolver(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from tests.test_a3_direction_artifacts import scientific_metadata
    r=runtime();source=scientific_metadata();r.artifacts.write_bundle(tmp_path/'capture',source,{})
    identity=copy.deepcopy(source['identity']);identity['capture_lineage']=[r.artifacts.capture_reference(tmp_path/'capture',expected=source)]
    def shard(panel):
        key=[panel,'far_v2','far_v2','validation' if panel=='calibration' else 'assessment',42,['head',7,16],'learned',0,'zero',panel,'D','clean']
        return dict(shard_id=panel,panel=panel,expected_keys=[key])
    inv=dict(shards=[shard('calibration'),shard('assessment')]);seen=[]
    monkeypatch.setattr(r,'load_selected_axes',lambda *a:{})
    monkeypatch.setattr(r,'_admitted_packing_paths',lambda *a:[],raising=False)
    def produce(model,d,pr,s,**kwargs):
        seen.append(s['panel']);return [dict(zip(r.artifacts.KEY_FIELDS,s['expected_keys'][0]))],{'actual_execution':True},identity
    monkeypatch.setattr(r,'score_runtime_shard',produce)
    args=SimpleNamespace(stage='assess',panel='calibration',selected='selected',fits=None,shard_id=None,resume=False)
    r.run_scoring(object(),{'injected':True},{},inv,root=tmp_path,args=args,guard=lambda:None,selected={})
    assert seen==['calibration']
    assert not (tmp_path/'runtime-shards'/'assessment').exists()


def test_shared_capture_and_control_paths_are_scope_based(tmp_path):
    r=runtime()
    a={'analysis_split':'validation','numeric_profile':{'batch':2},'ordered_ids':['a','b'],'capture_lineage':[]}
    b=copy.deepcopy(a)
    assert r.shared_execution_paths(tmp_path,a,'clean')==r.shared_execution_paths(tmp_path,b,'clean')
    b['numeric_profile']['batch']=1
    assert r.shared_execution_paths(tmp_path,a,'clean')!=r.shared_execution_paths(tmp_path,b,'clean')
    assert r.shared_execution_paths(tmp_path,a,'clean')[0]==r.shared_execution_paths(tmp_path,a,'corrupt')[0]
    assert r.shared_execution_paths(tmp_path,a,'clean')[1]!=r.shared_execution_paths(tmp_path,a,'corrupt')[1]


def test_live_rs_status_reconciliation_preserves_original_snapshot_and_no_refund(tmp_path):
    r,mapping,path,ledger,m=ledger_fixture(tmp_path)
    snapshot=tmp_path/'original-ledger.json';snapshot.write_bytes(path.read_bytes());m['ledger_snapshot_path']=str(snapshot)
    r.publish_object(tmp_path/'new-mapping',m)
    ledger['reservations'][0].update(status='failed',actual_seconds=1)
    path.write_text(json.dumps(ledger))
    normalized=r.normalize_ledger(tmp_path/'new-mapping',identity={'injected':True},injected=True)
    assert normalized['entries'][0]['state']=='failed'
    assert normalized['entries'][0]['reserved_gpu_hours']==.2
    assert normalized['snapshot_sha256']==r.common.file_hash(path)
    assert normalized['snapshot_sha256']!=m['ledger_sha256']


@pytest.mark.parametrize('damage',[None,'original_ceiling','empty_anchors','current_identity','finish_time'])
def test_root_reservation_requires_independent_original_admission(tmp_path,damage):
    import time
    r,mapping,path,ledger,m=ledger_fixture(tmp_path,identity={'injected':True,'commit':'a'*40})
    ledger['reservations'][0]['status']='running';path.write_text(json.dumps(ledger))
    m['ledger_sha256']=r.common.file_hash(path);m['entries'][0]['actual_entry']=copy.deepcopy(ledger['reservations'][0])
    r.publish_object(tmp_path/'current-mapping',m)
    identity={'injected':True,'commit':'a'*40}
    inv=dict(identity=identity,inventory_sha256='c'*64,phase='M2',expected_keys=[],finish_reserve_seconds=10)
    r.publish_object(tmp_path/'upper',inv)
    admission=r.read_object(tmp_path/'admission')
    reservation=dict(kind='a3_root_execution_reservation_v1',identity=identity,inventory_sha256='c'*64,reservation_id='r-1',
        actual_entry={k:ledger['reservations'][0].get(k) for k in r.RESERVATION_FIELDS},
        admission_path=str(tmp_path/'admission'),admission_reference=r.object_reference(tmp_path/'admission'),
        admission_sha256=admission['admission_sha256'],upper_inventory_path=str(tmp_path/'upper'),end_time_unix=time.time()+600,minimum_shard_seconds=1,injected_allocation_path=str(tmp_path/'allocation'))
    if damage in ('original_ceiling','empty_anchors'):
        changed=copy.deepcopy(admission)
        if damage=='original_ceiling':changed['max_gpu_hours']=4
        else:changed['reservation_ids']=[]
        changed['admission_sha256']=r.workload.digest({k:v for k,v in changed.items() if k!='admission_sha256'})
        r.publish_object(tmp_path/'changed-admission',changed)
        reservation.update(admission_path=str(tmp_path/'changed-admission'),admission_reference=r.object_reference(tmp_path/'changed-admission'),admission_sha256=changed['admission_sha256'])
    if damage=='current_identity':reservation['actual_entry']['gpus']=2
    if damage=='finish_time':
        allocation=r.read_object(tmp_path/'allocation');allocation.update(start_time_unix=time.time()-720,end_time_unix=time.time())
        r.publish_object(tmp_path/'ended-allocation',allocation);reservation['injected_allocation_path']=str(tmp_path/'ended-allocation')
    r.publish_object(tmp_path/'reservation',reservation)
    normalized=r.normalize_ledger(tmp_path/'current-mapping',identity=identity,injected=True)
    call=lambda:r.validate_reservation(tmp_path/'reservation',ledger=normalized,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    if damage is None:assert call()['original_reserved_gpu_hours']==.2
    else:
        with pytest.raises(ValueError):call()


def test_measured_runner_clocks_observe_actual_full_and_dummy_operations(fake):
    from tests.test_a3_direction_runner import measured_setup,batch
    r=runtime();ident,index,axes,cells=measured_setup(fake);ident.pop('packed_equivalence')
    result,samples=r.measure_runner_operations(object(),lambda:r.runner.measure_packing_equivalence(
        object(),[batch()],cells=cells,capture_index=index,axes=axes,identity=ident))
    assert result['dummy_lanes_tested'] and samples
    operations={entry['operation'] for entry in samples}
    assert {'patched','intact','empty','head_self','zero_coefficient'}<=operations
    assert any(x['dummy'] for x in samples)
    assert {x['profile']['axis_tile_size'] for x in samples}=={1,2}
    assert all(x['seconds']>0 and x['synchronized'] for x in samples)


def test_injected_runtime_cannot_finalize_before_any_probe_or_summary(tmp_path,monkeypatch):
    r=runtime()
    with pytest.raises(ValueError,match='injected'):
        r.summarize_runtime({'injected':True},{},{},[],[],[],[],root=tmp_path,inventory={},final=True,guard=lambda:None)
    assert list(tmp_path.iterdir())==[]


def test_prefit_pilot_emits_actual_complete_scope_and_non_authorizing_cost(tmp_path,fake):
    from types import SimpleNamespace
    from tests.test_a3_direction_workload import fixture,ledger
    from tests.test_a3_direction_artifacts import scientific_metadata
    from component_analysis import ladder_tasks
    r=runtime();d,_,_=fixture();source=scientific_metadata()['identity']
    d.update(a1_identity=source['a1_identity'],parent_evidence=source['parent_evidence'])
    for task,spec in d['tasks'].items():spec['direction_sites']=[['head',0,0]]
    groups=list(d['access_rows'].items())+[(task,d[task+'_validation']) for task in ('ioi','mmlu')]+[(task,d['utility'][task]) for task in ('ioi','mmlu')]
    for task,rows in groups:
        for j,row in enumerate(rows):
            row.update(task=task,source_id=row['instance_id'],source_hash='e'*64,question_hash=row['instance_id'],
                analysis_split='validation' if row['instance_id'] in {x['instance_id'] for x in d.get(task+'_validation',[])} else row['split'],
                expected_token=1,honest_token=2,opposite_token=1)
            if task=='mmlu':row.update(choice_tokens=[0,1,2,3],gold_letter='B')
            for stream,saved in row['streams'].items():
                saved.update(tokens=[1,2,3+(j%3)] if stream=='clean' else [2,3,5+(j%3)],readout=2,layout=None,
                    expected_token=1,honest_token=2,opposite_token=1)
    d['mmlu_validation_maps']=ladder_tasks.mmlu_calibration_maps(d['mmlu_validation'])
    d['utility']['mmlu_maps']=ladder_tasks.mmlu_calibration_maps(d['utility']['mmlu'])
    pr=dict(commit=source['commit'],code_hashes=source['code_hashes'],injected=True,numeric_profile={})
    settings=dict(microbatch_size=2,axis_tile_size=2,head_width=2,hidden_size=4,num_layers=1,vocabulary_size=4,dtype_bytes=4,
        hardware={'gpu':'injected-cpu','count':1},warmup_batches=1,serialization_batches=0,finish_reserve_seconds=1,
        probe_max_bytes=1048576,dtype='torch.float32',backend='fake',jobs=1)
    r.freeze_operational_contract(d,pr,settings)
    inv=r.workload.build_inventory(d,pr,stage='prefit')
    import time
    start=time.perf_counter();model=object();startup=time.perf_counter()-start
    result=r.run_pilot(model,d,pr,inv,root=tmp_path,args=SimpleNamespace(pilot_part='prefit',selected=None),guard=lambda:None,startup_seconds=startup)
    target=r.read_object(tmp_path/'pilot-target-inventory'/'prefit')
    assert result['complete'] and result['status']=='completed' and result['source_split']=='validation'
    assert result['packing_references'] and all(m['batch_seconds'] for m in result['measurements'])
    budget=ledger(target)
    budget['storage_capacities']['host_ram']['available_bytes']=max(budget['storage_capacities']['host_ram']['available_bytes'],result['host_peak_bytes']*2)
    proposal=r.workload.project_cost([result],target,budget)
    assert proposal['execution_authorized'] is False and proposal['projected_seconds']>0


def test_metadata_probe_features_use_original_requested_split(tmp_path):
    from tests.test_a3_direction_fit import fixture
    p,d,pr,cache,_,_=fixture(tmp_path)
    original=copy.deepcopy(d);ids=d['tasks']['far_v2']['fit_ids']
    expected=p._metadata_features(d,'far_v2',ids)
    assert all(torch.equal(a,b) for a,b in zip(expected,p._metadata_features(d,'far_v2',ids,split='train')))
    for row in list(d['access_rows']['far_v2']):
        if row.get('split')=='train':d['access_rows']['far_v2'].append(dict(copy.deepcopy(row),split='test',instance_id='assess-'+row['instance_id']))
    actual=p._metadata_features(d,'far_v2',['assess-'+i for i in ids],split='assessment')
    assert all(torch.equal(a,b) for a,b in zip(expected,actual))
    assert all(row==original['access_rows']['far_v2'][j] for j,row in enumerate(d['access_rows']['far_v2'][:len(original['access_rows']['far_v2'])]))


def test_calibration_only_cpu_summary_never_reads_assessment(tmp_path,monkeypatch):
    from tests.test_a3_direction_reporting import fixture as reporting_fixture
    from component_analysis import a3_statistics
    d,s,panels=reporting_fixture.__wrapped__();r=runtime();calls=[]
    r.publish_object(tmp_path/'selected',s)
    monkeypatch.setattr(a3_statistics,'simulate_conditional_power',lambda panel,**kw:calls.append((panel,kw)) or {'power':.8})
    rows=panels['validation'];inv=dict(inventory_sha256='a'*64,expected_keys=[r.artifacts.row_key(row) for row in rows])
    result=r.summarize_calibration(d,{'bootstrap':{'power':2000,'power_seed':19001}},s,rows,[],root=tmp_path,inventory=inv,guard=lambda:None)
    assert result['source_split']=='validation' and result['continuation_authorized'] is False
    assert calls[0][1]==dict(n_rep=2000,seed=19001)
    assert not (tmp_path/'summary').exists()
    assert (tmp_path/'calibration-summary'/'COMPLETE.json').is_file()


def test_fit_cache_layout_uses_frozen_task_order_across_json(tmp_path):
    from tests.test_a3_direction_fit import fixture
    p,d,pr,_,_,_=fixture(tmp_path)
    original=copy.deepcopy(d['tasks']['far_v2']);other=copy.deepcopy(original)
    other['fit_ids']=['ser-'+rid for rid in other['fit_ids']]
    rows=copy.deepcopy(d['access_rows']['far_v2'])
    for row in rows:
        if row['split']=='train':row['instance_id']='ser-'+row['instance_id']
    d['tasks']={'ser_v2':other,'far_v2':original};d['access_rows']['ser_v2']=rows
    pr['task_order']=['ser_v2','far_v2']
    expected,layout=p._fit_contract(d,pr)
    restored=json.loads(json.dumps(d,sort_keys=True))
    actual,loaded=p._fit_contract(restored,json.loads(json.dumps(pr,sort_keys=True)))
    assert expected==actual and layout==loaded
    assert loaded[0]['task']=='ser_v2' and loaded[0]['activations']['D']=='t0_s0_D'


def test_additive_milestone_caps_count_m1_once_without_refunds():
    r=runtime();entries=[dict(phase=phase,subphase=sub,reserved_gpu_hours=hours,state='completed',actual_gpu_hours=0)
        for phase,sub,hours in [('M1','directions',.5),('M1','edges',.75),('M1','masks',.75),
            ('M2','directions',9),('M3','neurons',4),('M4','edges',9),('M5','masks',10)]]
    assert r.validate_global_budgets(entries,contingency_remaining=6)['all']==34
    changed=copy.deepcopy(entries);changed[1]['reserved_gpu_hours']=.8;changed[2]['reserved_gpu_hours']=.7
    with pytest.raises(ValueError):r.validate_global_budgets(changed,contingency_remaining=6)
    changed=copy.deepcopy(entries);changed[5]['reserved_gpu_hours']=9.1;changed[6]['reserved_gpu_hours']=9.9
    with pytest.raises(ValueError):r.validate_global_budgets(changed,contingency_remaining=6)


def test_authority_context_is_process_local_and_detects_same_size_restored_mtime(tmp_path):
    r=runtime();r.publish_object(tmp_path/'immutable',{'value':'alpha'})
    context=r._make_file_witness([tmp_path/'immutable'])
    r._check_file_witness(context)
    path=tmp_path/'immutable'/'payload.json';old=path.stat()
    path.write_text(path.read_text().replace('alpha','omega'))
    import os
    os.utime(path,ns=(old.st_atime_ns,old.st_mtime_ns))
    with pytest.raises(ValueError):r._check_file_witness(context)


@pytest.mark.parametrize('damage',['replace','symlink','missing','extra'])
def test_authority_file_witness_rejects_changed_tree(tmp_path,damage):
    r=runtime();r.publish_object(tmp_path/'immutable',{'value':'alpha'})
    context=r._make_file_witness([tmp_path/'immutable']);path=tmp_path/'immutable'/'payload.json'
    if damage=='replace':
        copy=tmp_path/'copy';copy.write_bytes(path.read_bytes());copy.replace(path)
    elif damage=='symlink':
        copy=tmp_path/'copy';copy.write_bytes(path.read_bytes());path.unlink();path.symlink_to(copy)
    elif damage=='missing':path.unlink()
    else:(tmp_path/'immutable'/'extra').write_text('not original')
    with pytest.raises(ValueError):r._check_file_witness(context)


def _authority_case(tmp_path,inventory=None,work_dir="/output"):
    import time
    identity=inventory['identity'] if inventory is not None else {'injected':True,'commit':'a'*40}
    r,_,path,ledger,m=ledger_fixture(tmp_path,identity=identity,inventory_sha=None if inventory is None else inventory['inventory_sha256'])
    ledger['reservations'][0].update(status='running',output_dir=str(work_dir));path.write_text(json.dumps(ledger))
    snapshot=tmp_path/'original-ledger.json';snapshot.write_bytes(path.read_bytes())
    m.update(ledger_sha256=r.common.file_hash(path),ledger_snapshot_path=str(snapshot),
        storage_capacities={'host_ram':{'pool':'ram','available_bytes':10000000}})
    m['entries'][0]['actual_entry']=copy.deepcopy(ledger['reservations'][0]);r.publish_object(tmp_path/'current-map',m)
    inv=inventory if inventory is not None else dict(identity=identity,inventory_sha256='c'*64,phase='M2',expected_keys=[],finish_reserve_seconds=10)
    r.publish_object(tmp_path/'upper',inv);a=r.read_object(tmp_path/'admission')
    reservation=dict(kind='a3_root_execution_reservation_v1',identity=identity,inventory_sha256=inv['inventory_sha256'],reservation_id='r-1',
        actual_entry={k:ledger['reservations'][0].get(k) for k in r.RESERVATION_FIELDS},admission_path=str(tmp_path/'admission'),
        admission_reference=r.object_reference(tmp_path/'admission'),admission_sha256=a['admission_sha256'],
        upper_inventory_path=str(tmp_path/'upper'),end_time_unix=time.time()+600,minimum_shard_seconds=1,injected_allocation_path=str(tmp_path/'allocation'))
    r.publish_object(tmp_path/'reservation',reservation)
    normalized=r.normalize_ledger(tmp_path/'current-map',identity=identity,injected=True)
    return r,normalized,inv,tmp_path/'reservation',path,ledger


def test_full_authority_context_reuses_proof_but_refreshes_actual_ledger(tmp_path):
    r,ledger,inv,reservation,live_path,live=_authority_case(tmp_path);calls=[]
    context=r.make_authority_context(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,
        inventory_validator=lambda _:calls.append(1),requested_scope='unit-test')
    import pickle
    with pytest.raises(TypeError):pickle.dumps(context)
    fresh=lambda:r.validate_reservation(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,
        inventory_validator=lambda _:pytest.fail('reconstructed immutable proof'),authority_context=context,requested_scope='unit-test')
    assert fresh()['original_reserved_gpu_hours']==.2 and calls==[1]
    live['reservations'][0]['actual_seconds']=5;live_path.write_text(json.dumps(live))
    assert fresh()['actual_gpu_hours']==pytest.approx(5/3600)
    with pytest.raises(ValueError):r.validate_reservation(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,
        authority_context={},requested_scope='unit-test')
    with pytest.raises(ValueError):r.validate_reservation(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,
        authority_context=context,requested_scope='changed-scope')
    live['reservations'][0]['status']='completed';live_path.write_text(json.dumps(live))
    with pytest.raises(ValueError):fresh()


def _mapping_successor_case(tmp_path):
    r,ledger,inv,reservation,live_path,live=_authority_case(tmp_path)
    current=r.read_object(tmp_path/'current-map');directory=tmp_path/'successors';directory.mkdir()
    current.update(successor_directory=str(directory),generation=0,refresh_wait_seconds=2)
    original=tmp_path/'original-mapping';r.publish_object(original,current)
    normalized=r.normalize_ledger(original,identity=inv['identity'],injected=True)
    context=r.make_authority_context(reservation,ledger=normalized,inventory=inv,work_dir='/output',injected=True,
        inventory_validator=lambda _:None,requested_scope='successors')
    new=dict(copy.deepcopy(live['reservations'][0]),id='r-2',job_id='200',requested_minutes=30,reserved_gpu_hours=.5,
        source_commit='b'*40,output_dir='/edges',status='reserved',actual_seconds=None)
    live['reservations'].append(new);live_path.write_text(json.dumps(live))
    snapshot=tmp_path/'second-snapshot.json';snapshot.write_bytes(live_path.read_bytes())
    successor=copy.deepcopy(current);successor.update(generation=1,predecessor_reference=r.object_reference(original),
        ledger_snapshot_path=str(snapshot),ledger_sha256=r.common.file_hash(snapshot),expected_entry_ids=['r-1','r-2'])
    successor['entries'].append(dict(reservation_id='r-2',experiment='A3',phase='M4',subphase='edges',inventory_sha256='d'*64,
        original_reserved_gpu_hours=.5,actual_entry=new,reservation_lineage={}))
    return r,original,normalized,inv,reservation,context,successor,directory


def test_current_mapping_successor_counts_new_phase_without_invalidating_original_job(tmp_path):
    r,original,ledger,inv,reservation,context,successor,directory=_mapping_successor_case(tmp_path)
    import threading,time
    failures=[]
    def publish():
        try:time.sleep(.05);r.publish_object(directory/'mapping-000001',successor)
        except BaseException as error:failures.append(error)
    thread=threading.Thread(target=publish);thread.start()
    result=r.validate_reservation(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,
        authority_context=context,requested_scope='successors',inventory_validator=lambda _:pytest.fail('old proof reconstructed'))
    thread.join();assert not failures
    assert result['original_budget_totals']['M4']==.5
    assert result['original_budget_totals']['all']==pytest.approx(.7)
    assert result['current_mapping_reference']['path']==str((directory/'mapping-000001').resolve())
    assert r.read_object(original)['entries'][0]['original_reserved_gpu_hours']==.2


@pytest.mark.parametrize('damage',['omit_old','old_charge','old_phase','old_admission','predecessor'])
def test_mapping_successor_cannot_change_old_anchors(tmp_path,damage):
    r,original,ledger,inv,reservation,context,successor,directory=_mapping_successor_case(tmp_path)
    if damage=='omit_old':successor['expected_entry_ids']=['r-2'];successor['entries']=successor['entries'][1:]
    if damage=='old_charge':successor['entries'][0]['original_reserved_gpu_hours']=.1
    if damage=='old_phase':successor['entries'][0]['phase']='M1'
    if damage=='old_admission':successor['original_admission_paths']=[]
    if damage=='predecessor':successor['predecessor_reference']['files']['payload.json']['sha256']='f'*64
    r.publish_object(directory/'mapping-000001',successor)
    with pytest.raises(ValueError):r.validate_reservation(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,
        authority_context=context,requested_scope='successors')


def test_model_config_metadata_validates_geometry_before_model_access():
    r=runtime();cfg=dict(head_width=16,hidden_size=64,num_layers=2,vocabulary_size=101,
        widths={'far_v2':{'train':10,'validation':11,'assessment':11}})
    local=dict(model_type='llama',hidden_size=64,num_hidden_layers=2,num_attention_heads=4,vocab_size=101,max_position_embeddings=1024)
    assert r.validate_model_metadata(local,cfg)['head_width']==16
    for field in ('hidden_size','num_hidden_layers','num_attention_heads','vocab_size','max_position_embeddings'):
        bad=dict(local);bad[field]=1
        with pytest.raises(ValueError):r.validate_model_metadata(bad,cfg)


def _real_injected_design():
    from tests.test_a3_direction_artifacts import scientific_metadata
    from component_analysis import ladder_tasks,a3_pipeline
    r=runtime();parent=scientific_metadata()['identity'];tasks={};access={}
    for task in ('far_v2','sdr_v2','ser_v2'):
        ids={split:[task+':'+split+':'+str(j) for j in range(n)] for split,n in [('train',2),('validation',2),('test',1)]}
        tasks[task]=dict(fit_ids=ids['train'],selection_ids=ids['validation'],assessment_ids=ids['test'],direction_sites=[['head',0,0]])
        rows=[]
        for split,values in ids.items():
            for c,base in [('D',12),('H',3),('F',3),('I',8),('user_neutral',2)]:
                for j,rid in enumerate(values):
                    expected=2 if c in ('D','I') else 1
                    rows.append(dict(task=task,instance_id=rid,source_id=rid,source_hash='e'*64,split=split,condition=c,
                        pressure_text='word'+str(j),expected_token=expected,honest_token=1,opposite_token=2,
                        streams={s:dict(prompt=rid+c+s,tokens=[1,2,base+j] if s=='clean' else [2,3,base+j+2],
                            readout=2,layout=None,expected_token=expected,honest_token=1,opposite_token=2) for s in ('clean','corrupt')}))
        access[task]=rows
    design=dict(injected=True,seeds=[42,1,123],tasks=tasks,access_rows=access,utility={},selection_exclusion_ids=[],
        a1_identity=parent['a1_identity'],parent_evidence=parent['parent_evidence'])
    for task,n in [('ioi',2),('mmlu',32)]:
        for split in ('validation','assessment'):
            rows=[]
            for j in range(n):
                rid=task+':'+split+':'+str(j);streams=('clean','corrupt') if task=='ioi' else ('clean',)
                row=dict(task=task,instance_id=rid,source_id=rid,source_hash='d'*64,condition=task.upper(),
                    split='generated' if task=='ioi' else 'test',expected_token=2,honest_token=1,opposite_token=2,
                    streams={s:dict(prompt=rid+s,tokens=[1,2,5+j%3] if s=='clean' else [2,3,7+j%3],readout=2,layout=None,
                        expected_token=2,honest_token=1,opposite_token=2) for s in streams})
                if split=='validation':row['analysis_split']='validation'
                if task=='mmlu':row.update(question_hash=rid,gold_letter='C',choice_tokens=[0,1,2,3])
                rows.append(row)
            if split=='validation':design[task+'_validation']=rows
            else:design['utility'][task]=rows
    design['ioi_validation_maps']=ladder_tasks.ioi_item_swap_maps(design['ioi_validation'])
    design['mmlu_validation_maps']=ladder_tasks.mmlu_calibration_maps(design['mmlu_validation'])
    design['utility']['ioi_maps']=ladder_tasks.ioi_item_swap_maps(design['utility']['ioi'])
    design['utility']['mmlu_maps']=ladder_tasks.mmlu_calibration_maps(design['utility']['mmlu'])
    settings=dict(microbatch_size=2,axis_tile_size=2,axis_tile_sizes={'prefit':2,'fit-select':2,'selected-pilot':32,'remaining':32},
        jobs=2,head_width=16,hidden_size=64,num_layers=1,vocabulary_size=101,dtype_bytes=4,hardware={'gpu':'injected-cpu','count':1},
        warmup_batches=0,serialization_batches=0,finish_reserve_seconds=1,probe_max_bytes=1048576,dtype='torch.float32',backend='sdpa')
    protocol=a3_pipeline.direction_protocol(design,commit=parent['commit'],injected_code_hashes=parent['code_hashes'],execution_settings=settings)
    design.update(direction_protocol=protocol,direction_protocol_sha256=r.ladder.design._hash(protocol))
    return design,protocol


def test_complete_real_tiny_injected_pipeline_all_seeds_and_199_axes(tmp_path,monkeypatch):
    import sys,time
    if sys.version_info[:2]<(3,12):pytest.skip('real pinned NNsight integration runs on mgnp')
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    from tests.helpers import tiny_config
    from component_analysis import hooks
    from types import SimpleNamespace
    r=runtime();d,pr=_real_injected_design();root=tmp_path/'study';root.mkdir()
    original_assessment={t:list(v['assessment_ids']) for t,v in d['tasks'].items()};utility=copy.deepcopy(d['utility'])
    r.ladder.write_artifact(root/'design.json',d);r.ladder.write_artifact(root/'direction_protocol.json',pr)
    d=r.ladder.read_artifact(root/'design.json');pr=r.ladder.read_artifact(root/'direction_protocol.json')
    assert d['utility']==utility and {t:v['assessment_ids'] for t,v in d['tasks'].items()}==original_assessment
    torch.manual_seed(91);plain=LlamaForCausalLM(tiny_config(num_hidden_layers=1,attn_implementation='sdpa')).eval()
    with torch.no_grad():
        for p in plain.parameters():p.zero_()
        plain.model.embed_tokens.weight.normal_(mean=0,std=.2)
        plain.model.embed_tokens.weight[:,0]=1
        plain.model.embed_tokens.weight[:,1]=torch.arange(101)/5
        plain.model.norm.weight.fill_(1)
        for layer in plain.model.layers:
            layer.input_layernorm.weight.fill_(1);layer.post_attention_layernorm.weight.fill_(1)
            for j in range(layer.self_attn.v_proj.weight.shape[0]):layer.self_attn.v_proj.weight[j,j]=1
            layer.self_attn.o_proj.weight.copy_(torch.eye(64)*.1)
        plain.lm_head.weight[1,0]=1;plain.lm_head.weight[2,1]=1
    model=NNsight(plain);counter=[0];original_forward=hooks.capture_forward
    def count_forward(*a,**kw):counter[0]+=1;return original_forward(*a,**kw)
    monkeypatch.setattr(hooks,'capture_forward',count_forward)
    def checkpoint(label):print('JOINED_TINY',label,'native_forwards',counter[0],flush=True)
    start=time.perf_counter();pilot=r.workload.build_inventory(d,pr,stage='prefit')
    r.run_pilot(model,d,pr,pilot,root=root,args=SimpleNamespace(pilot_part='prefit',selected=None),guard=lambda:None,startup_seconds=time.perf_counter()-start)
    checkpoint('prefit-complete')
    upper=r.workload.build_inventory(d,pr,stage='fit-select');r.publish_object(root/'inventory'/'upper',upper)
    r.run_fit_capture(model,d,pr,upper,root=root,guard=lambda:None)
    fits=r.pipeline.fit_from_cache(d,root/'cache'/'fit-selection',protocol=pr,output=root/'fits')
    assert not fits['blocked_task_seeds'];checkpoint('fits-complete')
    inv=r.workload.build_inventory(d,pr,stage='fit-select',fits=fits);r.publish_object(root/'inventory'/'validation',inv)
    r.publish_object(root/'test-admission',{'pilot_receipt_paths':[str(root/'pilot'/'prefit')]})
    r.publish_object(root/'test-reservation',{'admission_path':str(root/'test-admission')})
    args=SimpleNamespace(stage='select',panel=None,selected=None,fits=str(root/'fits'),inventory=str(root/'inventory'/'validation'),
        reservation=str(root/'test-reservation'),shard_id=None,resume=False)
    r.run_scoring(model,d,pr,inv,root=root,args=args,guard=lambda:None,fits=fits)
    selected=r.pipeline.freeze_selection(d,root/'fits',root/'validation',protocol=pr,output=root/'selected',protocol_path=root/'direction_protocol.json')
    assert not selected['blocked_task_seeds'] and len(selected['selected_records'])==9
    assert all(len(x['assessment_axes'])==199 and len(x['calibration_axes'])==32 for x in selected['selected_records'])
    checkpoint('selection-complete')
    selected_pilot=r.workload.build_inventory(d,pr,stage='selected-pilot',selected=selected)
    r.run_pilot(model,d,pr,selected_pilot,root=root,args=SimpleNamespace(pilot_part='selected',selected=str(root/'selected')),guard=lambda:None,startup_seconds=0,selected=selected)
    checkpoint('selected-199-pilot-complete')
    remaining=r.workload.build_inventory(d,pr,stage='remaining',selected=selected)
    r.publish_object(root/'test-admission-remaining',{'pilot_receipt_paths':[str(root/'pilot'/'selected')]})
    r.publish_object(root/'test-reservation-remaining',{'admission_path':str(root/'test-admission-remaining')})
    args=SimpleNamespace(stage='assess',panel='calibration',selected=str(root/'selected'),fits=None,shard_id=None,resume=False,
        reservation=str(root/'test-reservation-remaining'))
    r.run_scoring(model,d,pr,remaining,root=root,args=args,guard=lambda:None,selected=selected)
    calibration,crefs=r.read_runtime_rows(d,pr,remaining,root/'runtime-shards',panel='calibration')
    r.summarize_calibration(d,pr,selected,calibration,crefs,root=root,inventory=remaining,guard=lambda:None)
    checkpoint('calibration-and-power-complete')
    args.panel='assessment';r.run_scoring(model,d,pr,remaining,root=root,args=args,guard=lambda:None,selected=selected)
    rows,refs=r.read_runtime_rows(d,pr,remaining,root/'runtime-shards',panel='assessment')
    result=r.summarize_runtime(d,pr,selected,rows,calibration,refs,crefs,root=root,inventory=remaining,final=False,guard=lambda:None)
    assert not result['finalized'] and result['diagnostic_readiness']
    assert len(rows)+len(calibration)==len(remaining['expected_keys'])
    assert result['runtime_identity']['injected'] is True
    with pytest.raises(ValueError,match='injected'):
        r.summarize_runtime(d,pr,selected,rows,calibration,refs,crefs,root=root,inventory=remaining,final=True,guard=lambda:None)
    checkpoint('full-summary-complete')
    r.publish_object(root/'test-receipt',dict(injected=True,complete=True,scientific_execution=False,native_forward_calls=counter[0],
        observed_rows=len(rows)+len(calibration),expected_rows=len(remaining['expected_keys']),
        baseline_margin=rows[0]['intact_margin'],empty_replay_error=rows[0]['replay_errors']['empty']))


@pytest.mark.parametrize('static_end_offset',[-36000,360000])
def test_live_allocation_replaces_submit_time_deadline_for_delayed_queue(tmp_path,static_end_offset):
    import time
    r,ledger,inv,path,_,_=_authority_case(tmp_path)
    reservation=r.read_object(path);reservation['end_time_unix']=time.time()+static_end_offset
    r.publish_object(tmp_path/'queued-reservation',reservation)
    result=r.validate_reservation(tmp_path/'queued-reservation',ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    assert result['allocation_verified'] is True
    assert result['allocation']['end_time_unix']<time.time()+1000


@pytest.mark.parametrize('damage',['duration','gpus','job','state','end'])
def test_live_allocation_conflicts_fail_before_model_access(tmp_path,damage):
    r,ledger,inv,path,_,_=_authority_case(tmp_path)
    reservation=r.read_object(path);allocation=r.read_object(tmp_path/'allocation')
    if damage=='duration':allocation.update(time_limit_seconds=900,end_time_unix=allocation['start_time_unix']+900)
    if damage=='gpus':allocation['gpus']=2
    if damage=='job':allocation['job_id']='other'
    if damage=='state':allocation['state']='PENDING'
    if damage=='end':allocation['end_time_unix']=allocation['start_time_unix']+9999
    r.publish_object(tmp_path/'conflicting-allocation',allocation);reservation['injected_allocation_path']=str(tmp_path/'conflicting-allocation')
    r.publish_object(tmp_path/'conflicting-reservation',reservation)
    with pytest.raises(ValueError):r.validate_reservation(tmp_path/'conflicting-reservation',ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)


def test_pending_binding_dry_run_never_requires_allocation_or_authorizes(tmp_path):
    r,ledger,inv,path,_,_=_authority_case(tmp_path);reservation=r.read_object(path)
    reservation.pop('injected_allocation_path');reservation.pop('end_time_unix')
    r.publish_object(tmp_path/'pending-reservation',reservation)
    result=r.validate_reservation(tmp_path/'pending-reservation',ledger=ledger,inventory=inv,work_dir='/output',injected=True,
        inventory_validator=lambda _:None,require_allocation=False)
    assert result['execution_authorized'] is False and result['allocation_verified'] is False
    assert result['live_allocation_admission']=='deferred/unverified'


def test_normalized_a1_parent_without_masks_uses_authenticated_length_not_token_id():
    from tests.test_a3_direction_workload import fixture
    r=runtime();d,_,_=fixture();task='far_v2';rid=d['tasks'][task]['assessment_ids'][0]
    for row in d['access_rows'][task]:
        row['task']=task
        for stream in row['streams'].values():
            stream.update(tokens=[1,0,3],readout=2,layout=None,expected_token=1,honest_token=2,opposite_token=1)
            assert 'attention_mask' not in stream
    original=copy.deepcopy(d)
    batch=r.source_batches(d,task,'assessment',[rid],'D','clean',dict(padded_width=5,physical_batch_size=1,axis_tile_size=1))[0]
    assert batch.input_ids.tolist()==[[1,0,3,0,0]]
    assert batch.attention_mask.tolist()==[[1,1,1,0,0]] and batch.readout.tolist()==[2]
    assert d==original


def test_tail_execution_aliases_share_capture_across_both_streams(tmp_path,fake):
    from tests.test_a3_direction_workload import fixture
    from tests.test_a3_direction_artifacts import scientific_metadata
    from tests.test_a3_direction_runner import axis
    r=runtime();d,_,_=fixture();task='far_v2';rid=d['tasks'][task]['assessment_ids'][0]
    d['tasks'][task]['assessment_ids']=[rid];d['tasks'][task]['direction_sites']=[['head',0,0]]
    for row in d['access_rows'][task]:
        row.update(task=task,source_hash='e'*64,source_id=row['instance_id'])
        for stream,saved in row['streams'].items():saved.update(tokens=[1,0,3] if stream=='clean' else [2,0,4],readout=2,layout=None,expected_token=1,honest_token=2,opposite_token=1)
    source=scientific_metadata()['identity'];d.update(a1_identity=source['a1_identity'],parent_evidence=source['parent_evidence'])
    profile=dict(padded_width=5,physical_batch_size=2,axis_tile_size=1,dtype='torch.float32',backend='fake',model=source['model'],model_revision=source['model_revision'],
        source_sha256=r.ladder.design._hash(source['code_hashes']),sites=[['head',0,0]])
    pr=dict(commit=source['commit'],code_hashes=source['code_hashes'],fit_cache=dict(capture_identity={k:source[k] for k in r.pipeline.IDENTITY_SOURCE_FIELDS}))
    ids,dummies=r.workload.execution_membership(task,'assessment','D',[rid],2)
    captures=[]
    for stream in ('clean','corrupt'):
        key=['assessment',task,task,'assessment',42,['head',0,0],'learned',0,'interchange',rid,'D',stream]
        shard=dict(shard_id=stream,expected_keys=[key],profile=profile,instance_ids=[rid],execution_ids=ids,dummy_sources=dummies,
            cells=[dict(seed=42,site=['head',0,0],family='learned',axis_index=0,operation='interchange',axis='x')])
        rows,evidence,_=r.score_runtime_shard(object(),d,pr,shard,axes={'x':axis()},output=tmp_path/'executions'/stream,
            shared_root=tmp_path,guard=lambda:None)
        assert len(rows)==1 and rows[0]['instance_id']==rid
        assert evidence['dummy_control_count']==1
        captures.append(evidence['capture_reference'])
    assert captures[0]==captures[1]


def test_packing_reuse_rejects_changed_actual_runtime_kernel_profile(tmp_path,fake):
    from tests.test_a3_direction_runner import measured_setup,batch
    r=runtime();identity,index,axes,cells=measured_setup(fake)
    signature=r.runtime_kernel_identity(object())
    evidence=r.packing_evidence(identity['packed_equivalence'],[batch()])
    r.publish_object(tmp_path/'measured-kernel',dict(evidence=evidence,measurement=dict(profile=identity['numeric_profile'],timing_inputs=[],axis_scope=[]),
        injected=True,runtime_profile=signature))
    changed=copy.deepcopy(signature);changed['backend']='different-kernel'
    with pytest.raises(ValueError,match='runtime'):
        r.freeze_profile_reuse(tmp_path/'reuse',measured_path=tmp_path/'measured-kernel',batch=batch(),cells=[cells[1]],axes=axes,
            capture_index={},policy=r.workload.PROFILE_REUSE_POLICY,runtime_profile=changed)
    assert not (tmp_path/'reuse').exists()


def test_train_capture_resolver_does_not_require_or_materialize_f_train():
    from tests.test_a3_direction_workload import fixture
    r=runtime();d,p,_=fixture();task='far_v2'
    d['access_rows'][task]=[row for row in d['access_rows'][task] if not (row['split']=='train' and row['condition']=='F')]
    for row in d['access_rows'][task]:
        row['task']=task
        for saved in row['streams'].values():saved.update(layout=None,expected_token=1,honest_token=2,opposite_token=1)
    rid=d['tasks'][task]['fit_ids'][0]
    result=r.source_batches(d,task,'train',[rid],'D','clean',dict(padded_width=4,physical_batch_size=1,axis_tile_size=1))
    assert result[0].ids==[rid] and result[0].condition=='D'


def test_cost_proposal_cannot_be_root_admission_even_with_lineage_fields(tmp_path):
    r,_,inv,path,_,_=_authority_case(tmp_path)
    reservation=r.read_object(path);original=r.read_object(tmp_path/'admission')
    proposal=dict(original,kind='a3_direction_cost_proposal',execution_authorized=False)
    proposal['admission_sha256']=r.workload.digest({k:v for k,v in proposal.items() if k!='admission_sha256'})
    r.publish_object(tmp_path/'proposal-as-admission',proposal)
    mapping=r.read_object(tmp_path/'current-map');mapping['original_admission_paths']=[str(tmp_path/'proposal-as-admission')]
    mapping['entries'][0]['reservation_lineage']['admission_sha256']=proposal['admission_sha256']
    r.publish_object(tmp_path/'proposal-mapping',mapping)
    reservation.update(admission_path=str(tmp_path/'proposal-as-admission'),admission_reference=r.object_reference(tmp_path/'proposal-as-admission'),admission_sha256=proposal['admission_sha256'])
    r.publish_object(tmp_path/'proposal-reservation',reservation)
    ledger=r.normalize_ledger(tmp_path/'proposal-mapping',identity=inv['identity'],injected=True)
    with pytest.raises(ValueError,match='admission kind'):
        r.validate_reservation(tmp_path/'proposal-reservation',ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)


def test_assessment_requires_root_reference_to_complete_validation_power(tmp_path):
    r=runtime();selected={};design={'injected':False};protocol={};inventory={'inventory_sha256':'i'}
    with pytest.raises((ValueError,FileNotFoundError)):
        r.assessment_preflight(design,protocol,selected,inventory,root=tmp_path,reservation_path=tmp_path/'missing')


def test_nonfinite_direction_denominators_block_runtime_finality():
    r=runtime()
    with pytest.raises(ValueError,match='denominator'):
        r.validate_primary_interpretability([{'panel':'assessment','analysis_task':'far_v2','seed':42,'site':['head',0,0],
            'family':'learned','axis_index':0,'source_task':'far_v2','operation':'interchange'}])


@pytest.mark.parametrize('bindings',[False,True])
def test_main_model_dry_run_missing_or_pending_bindings_never_loads(tmp_path,monkeypatch,capsys,bindings):
    r=runtime();d,p=_real_injected_design();root=tmp_path/'study';root.mkdir()
    r.ladder.write_artifact(root/'design.json',d);r.ladder.write_artifact(root/'direction_protocol.json',p)
    inv=r.workload.build_inventory(d,p,stage='fit-select');r.publish_object(root/'inventory',inv)
    monkeypatch.setattr(r.artifacts,'validate_live',lambda *a,**kw:{'injected':True})
    monkeypatch.setattr(r,'read_current_allocation',lambda *a,**kw:pytest.fail('dry-run queried allocation'))
    monkeypatch.setattr(torch.cuda,'is_available',lambda:pytest.fail('dry-run queried CUDA'))
    args=['--experiment','directions','--stage','fit','--action','capture','--design',str(root/'design.json'),
        '--commit',p['commit'],'--work-dir',str(root),'--inventory',str(root/'inventory'),'--dry-run']
    if bindings:
        _,_,_,reservation,live_path,live=_authority_case(tmp_path/'authority',inventory=inv,work_dir=root)
        live['reservations'][0]['status']='reserved';live_path.write_text(json.dumps(live))
        args+=['--ledger-snapshot',str(tmp_path/'authority'/'current-map'),'--reservation',str(reservation)]
    before={str(q) for q in tmp_path.rglob('*')}
    assert r.main(args,model_loader=lambda _:pytest.fail('dry-run loaded weights'))==0
    result=json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert result['execution_authorized'] is False and result['live_allocation_admission']=='deferred/unverified'
    assert {str(q) for q in tmp_path.rglob('*')}==before


@pytest.mark.parametrize('explicit',[False,True])
def test_spooled_wrapper_resolves_declared_checkout_and_runs_no_write_help(tmp_path,explicit):
    import os,shutil,subprocess,sys
    r=runtime();script=r.ladder.REPO/'scripts/jobs/specificity_a3.sh'
    spool=tmp_path/'spool'/'job';spool.mkdir(parents=True);copy=spool/'slurm_script';shutil.copy2(script,copy)
    env=dict(os.environ,DC_PYTHON=sys.executable,DC_CLUSTER='delta',PYTHONDONTWRITEBYTECODE='1')
    cwd=r.ladder.REPO
    if explicit:
        env['A3_REPO_ROOT']=str(r.ladder.REPO);cwd=tmp_path
    else:
        env.pop('A3_REPO_ROOT',None);env['SLURM_SUBMIT_DIR']=str(r.ladder.REPO)
    result=subprocess.run(['bash',str(copy),'--dry-run','--experiment','directions','--help'],cwd=cwd,env=env,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stderr
    assert 'A3 command:' in result.stdout and '--experiment' in result.stdout


def test_authority_context_cannot_cross_injected_production_boundary(tmp_path,monkeypatch):
    r,ledger,inv,path,_,_=_authority_case(tmp_path)
    context=r.make_authority_context(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    monkeypatch.setattr(r,'read_current_allocation',lambda *a,**kw:pytest.fail('changed injected scope reached lease reader'))
    with pytest.raises(ValueError):
        r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=False,authority_context=context)


def test_pilot_candidate_selection_preserves_condition_stream_and_source_ids():
    from types import SimpleNamespace
    r=runtime();profile={'padded_width':8}
    def invocation(condition,stream,ids):
        return dict(invocation={'profile':profile},batches=[SimpleNamespace(task='far_v2',condition=condition,stream=stream,ids=ids)])
    wrong_condition=invocation('D','clean',['v0','v1'])
    wrong_stream=invocation('H','corrupt',['v0','v1'])
    wrong_id=invocation('H','clean',['v2','v3'])
    correct=invocation('H','clean',['v0','v1'])
    requirement={'profile':profile,'timing_inputs':[dict(source_task='far_v2',condition='H',stream='clean',instance_id='v1')]}
    candidates=r._pilot_candidates([wrong_condition,wrong_stream,wrong_id,correct],requirement)
    assert candidates==[correct]
    assert r._pilot_candidates([wrong_condition,wrong_stream,wrong_id],requirement)==[]
