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


def _fake_pilot_inputs(tile):
    from tests.test_a3_direction_workload import fixture
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
    settings=dict(microbatch_size=2,axis_tile_size=tile,head_width=2,hidden_size=4,num_layers=1,vocabulary_size=4,dtype_bytes=4,
        hardware={'gpu':'injected-cpu','count':1},warmup_batches=1,serialization_batches=0,finish_reserve_seconds=1,
        probe_max_bytes=1048576,dtype='torch.float32',backend='fake',jobs=1)
    r.freeze_operational_contract(d,pr,settings)
    return r,d,pr


@pytest.mark.parametrize('tile',[1,2])
def test_prefit_pilot_emits_actual_complete_scope_and_non_authorizing_cost(tmp_path,fake,tile):
    from types import SimpleNamespace
    from tests.test_a3_direction_workload import ledger
    r,d,pr=_fake_pilot_inputs(tile)
    inv=r.workload.build_inventory(d,pr,stage='prefit')
    import time
    start=time.perf_counter();model=object();startup=time.perf_counter()-start
    result=r.run_pilot(model,d,pr,inv,root=tmp_path,args=SimpleNamespace(pilot_part='prefit',selected=None),guard=lambda:None,startup_seconds=startup)
    target=r.read_object(tmp_path/'pilot-target-inventory'/'prefit')
    assert result['complete'] and result['status']=='completed' and result['source_split']=='validation'
    assert (result['packing_references'] if tile>1 else result['serial_numeric_references']) and all(m['batch_seconds'] for m in result['measurements'])
    if tile>1:
        overhead=result['packing_overhead_measurements']
        assert len(overhead)==len(inv['packing_invocations'])
        assert all(x['scope_checks']==2 and x['boundary_refreshes']==2 and x['context_seconds']>0 for x in overhead)
        assert all(x['batch_seconds'][0]>=max(y['context_seconds'] for y in overhead if y['profile']==x['profile'])
            for x in result['measurements'] if x['operation']=='packing_lookup')
    if tile==1:r._authenticate_serial_references(d,pr,inv,result)
    if tile==1:
        original_path=Path(next(iter(result['serial_numeric_references'].values()))['path'])
        original=r.read_object(original_path)
        for damage in ('replay','timer','positive','rows','selected_backing'):
            changed=copy.deepcopy(original);raw=changed['receipt']
            if damage=='replay':raw['rows'][0]['replay_errors']['empty']=1.
            if damage=='timer':raw['operation_samples'][0]['seconds']=0.
            if damage=='positive':changed['positive_controls']=[]
            if damage=='rows':raw['rows'].pop()
            if damage=='selected_backing':changed.update(injected=False,timing_only=False,numeric_backing_references={})
            raw['receipt_sha256']=r.workload.digest({k:v for k,v in raw.items() if k!='receipt_sha256'})
            damaged=tmp_path/'serial-damage'/damage;r.publish_object(damaged,changed)
            with pytest.raises(ValueError):r._SerialNumericProof(damaged)
    budget=ledger(target)
    budget['storage_capacities']['host_ram']['available_bytes']=max(budget['storage_capacities']['host_ram']['available_bytes'],result['host_peak_bytes']*2)
    proposal=r.workload.project_cost([result],target,budget,packing_proofs=r._cost_packing_proofs([result]))
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


@pytest.mark.parametrize('field',['keys','shards','hardware','storage'])
def test_validated_inventory_is_deeply_immutable_and_replacement_rejects(tmp_path,field):
    inv=dict(identity={'injected':True,'commit':'a'*40},inventory_sha256='c'*64,phase='M2',
        expected_keys=[{'id':'original'}],finish_reserve_seconds=10,shards=[{'ids':['original']}],
        hardware={'gpu':'injected-cpu','count':1},storage_requirements={'tiers':{'host_ram':0}})
    r,ledger,inv,path,_,_=_authority_case(tmp_path,inventory=inv)
    original=json.loads(json.dumps(inv))
    context=r.make_authority_context(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    assert json.loads(json.dumps(inv))==original and copy.deepcopy(inv)==inv
    with pytest.raises(TypeError):
        if field=='keys':inv['expected_keys'][0]['id']='outside'
        if field=='shards':inv['shards'][0]['ids'].append('outside')
        if field=='hardware':inv['hardware']['count']=2
        if field=='storage':inv['storage_requirements']['tiers']['host_ram']=1
    assert context.retained_bytes>0 and context.transient_bytes>=context.retained_bytes
    inv['expected_keys']=[{'id':'outside'}]
    with pytest.raises(ValueError):r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)


@pytest.mark.parametrize('nested',[False,True])
def test_directory_symlink_descendant_changes_reject_cached_witness(tmp_path,nested):
    import os
    r=runtime();target=tmp_path/'target';target.mkdir();child=target/'payload.json';child.write_text('old')
    root=tmp_path/'bundle';root.mkdir();link=root/'link' if nested else tmp_path/'link';link.symlink_to(target,target_is_directory=True)
    witness=r._make_file_witness([root if nested else link]);old=child.stat();child.write_text('new');os.utime(child,ns=(old.st_atime_ns,old.st_mtime_ns))
    with pytest.raises(ValueError):r._check_file_witness(witness)


def test_directory_symlink_cycle_rejects_and_ordinary_file_symlink_remains_supported(tmp_path):
    r=runtime();target=tmp_path/'target';target.mkdir();data=tmp_path/'weights';data.write_text('weights')
    (target/'file').symlink_to(data);r._check_file_witness(r._make_file_witness([target]))
    (target/'cycle').symlink_to(target,target_is_directory=True)
    with pytest.raises(ValueError,match='cycle'):r._make_file_witness([target])


def test_full_cached_upper_directory_symlink_checks_completion_descendants(tmp_path):
    import os
    r,ledger,inv,path,_,_=_authority_case(tmp_path);link=tmp_path/'upper-link';link.symlink_to(tmp_path/'upper',target_is_directory=True)
    reservation=r.read_object(path);reservation['upper_inventory_path']=str(link);path=tmp_path/'linked';r.publish_object(path,reservation)
    context=r.make_authority_context(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    child=tmp_path/'upper'/'payload.json';old=child.stat();child.write_text(child.read_text().replace('"phase": "M2"','"phase": "M4"'));os.utime(child,ns=(old.st_atime_ns,old.st_mtime_ns))
    with pytest.raises(ValueError):r.read_object(tmp_path/'upper')
    with pytest.raises(ValueError):r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)


def _production_allocation_fixture():
    import time
    r=runtime();start=time.time()-30;checkout=str(Path(r.__file__).resolve().parents[1])
    contract=dict(kind='a3_allocation_contract_v1',scheduler_work_dir=checkout,source_commit='a'*40,cpus=4,memory_bytes=32*1024**3,gpus=1,gpu_type='h200')
    lease=dict(job_id='100',job_ids=['100'],cluster='delta',account='a',partition='p',state='RUNNING',gpus=1,gpu_types=['h200'],
        cpus=8,memory_bytes=64*1024**3,scheduler_work_dir=checkout,start_time_unix=start,end_time_unix=start+720,time_limit_seconds=720)
    actual=dict(job_id='100',cluster='delta',account='a',partition='p',gpus=1,requested_minutes=12,output_dir='/output')
    inv=dict(kind='a3_direction_inventory',identity={'commit':'a'*40},hardware={'gpu':'h200','count':1},storage_requirements={'tiers':{'host_ram':32*1024**3}})
    return r,contract,lease,actual,inv


@pytest.mark.parametrize('damage',[None,'workdir','gpu','cpu','ram','missing','contract_source','contract_checkout','contract_capacity'])
def test_real_allocation_matches_original_frozen_resource_contract(damage):
    r,contract,lease,actual,inv=_production_allocation_fixture()
    if damage=='workdir':lease['scheduler_work_dir']='/wrong'
    if damage=='gpu':lease['gpu_types']=['a40']
    if damage=='cpu':lease['cpus']=1
    if damage=='ram':lease['memory_bytes']=1024**2
    if damage=='missing':lease.pop('memory_bytes')
    if damage=='contract_source':contract['source_commit']='b'*40
    if damage=='contract_checkout':contract['scheduler_work_dir']='/wrong'
    if damage=='contract_capacity':contract['memory_bytes']=1024**2
    if damage is None:assert r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract) is lease
    else:
        with pytest.raises(ValueError):r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract)


@pytest.mark.parametrize('unit,value',[('64G',64*1024**3),('65536M',64*1024**3),('1T',1024**4),('64000',64000*1024**2)])
def test_scheduler_resource_units_and_generic_gpu_independent_node_lookup(monkeypatch,unit,value):
    import time,subprocess
    from datetime import datetime,timezone
    from types import SimpleNamespace
    r,contract,_,_,_=_production_allocation_fixture();start=int(time.time())-30
    stamp=lambda n:datetime.fromtimestamp(n,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    text=f'JobId=100 JobState=RUNNING Account=a Partition=p TimeLimit=00:12:00 StartTime={stamp(start)} EndTime={stamp(start+720)} AllocTRES=cpu=8,mem={unit},gres/gpu=1 NumCPUs=8 WorkDir={contract["scheduler_work_dir"]} NodeList=gpue03'
    calls=[]
    def transport(argv,**kw):
        calls.append(argv)
        if argv==['scontrol','-o','show','job','100']:return SimpleNamespace(stdout=text)
        assert argv==['scontrol','-o','show','node','gpue03']
        return SimpleNamespace(stdout='NodeName=gpue03 Gres=gpu:h200:8(S:0,2) CfgTRES=cpu=128,mem=1000G,gres/gpu=8,gres/gpu:h200=8')
    monkeypatch.setattr(subprocess,'run',transport);monkeypatch.setenv('SLURM_JOB_ID','100');monkeypatch.setenv('DC_CLUSTER','delta')
    lease=r.read_current_allocation({'actual_entry':{'job_id':'100'}},injected=False)
    assert lease['gpu_types']==['h200'] and lease['cpus']==8 and lease['memory_bytes']==value
    assert lease['scheduler_work_dir']==contract['scheduler_work_dir'] and len(calls)==2


@pytest.mark.parametrize('nodes',['NodeName=n1 Gres=gpu:h200:8\nNodeName=n2 Gres=gpu:a40:4','NodeName=n1 Gres=gpu:8','NodeName=n1 Gres=gpu:h200:4,gpu:a40:4'])
def test_ambiguous_or_untyped_node_gpu_facts_reject(nodes):
    with pytest.raises(ValueError):runtime()._node_gpu_types(nodes)


@pytest.mark.parametrize('mutation',['payload','backing'])
def test_completed_packing_proof_reuses_bounded_index_and_checks_each_target(tmp_path,fake,monkeypatch,mutation):
    from tests.test_a3_direction_runner import measured_setup,batch
    r=runtime();ident,index,axes,cells=measured_setup(fake);ident.pop('packed_equivalence')
    from dataclasses import replace
    from tests.test_a3_direction_runner import donor_maps,SITE
    records=[]
    for i,record in enumerate(batch().records):
        records.append(dict(record,streams={stream:dict(tokens=batch(stream).input_ids[i,:int(batch(stream).attention_mask[i].sum())].tolist(),
            readout=int(batch(stream).readout[i])) for stream in ('clean','corrupt')}))
    b=replace(batch(),records=records);donor=replace(batch('corrupt'),records=records);index={}
    for lanes in (1,2):
        capture_ident=copy.deepcopy(ident);capture_ident['numeric_profile'].update(axis_tile_size=lanes,physical_batch_size=2*lanes)
        chunks=[];r.runner._capture_readouts(object(),[b,donor],sites=[SITE],sink=chunks.append,identity=capture_ident,measuring=True)
        for chunk in chunks:
            for row in chunk['rows']:index[(chunk['profile_id'],row['task'],row['condition'],row['stream'],row['instance_id'])]=row
    serial=copy.deepcopy(ident);serial['numeric_profile'].update(axis_tile_size=1,physical_batch_size=2)
    cells[0]['donor_maps']=donor_maps(b,donor,r.runner.profile_identity(serial))
    receipt=r.runner.measure_packing_equivalence(object(),[b],cells=cells,capture_index=index,axes=axes,identity=ident)
    profile=receipt['scope']['profile'];evidence=r.packing_evidence(receipt,[b])
    measurement=dict(profile=profile,timing_inputs=r._timing_inputs_from_batches([b],profile),
        axis_scope=[{k:v for k,v in s.items() if k!='donors'} for s in next(iter(receipt['scope']['batches'].values()))])
    backing=tmp_path/'numeric-backing';backing.mkdir();np.save(backing/'projection.npy',np.eye(2,dtype=np.float32),allow_pickle=False);r.artifacts._finish(backing)
    path=tmp_path/'packing';r.publish_object(path,dict(evidence=evidence,measurement=measurement,injected=True,
        numeric_backing_references={str(backing):r.pipeline._bundle_byte_reference(backing)}))
    original=r.workload._packing_evidence;calls=[]
    def counted(*a,**kw):calls.append(1);return original(*a,**kw)
    monkeypatch.setattr(r.workload,'_packing_evidence',counted)
    proof=r._CompletedPackingProof(path)
    target=dict(requirements=[copy.deepcopy(measurement)],finish_reserve_seconds=1)
    with r._PilotReconciliationPass([proof],target,guard=lambda:None,injected=True) as reconciliation:
        target['requirements'][0]['profile']['padded_width']+=1
        with pytest.raises(TypeError):reconciliation.inventory['requirements'][0]['profile']['padded_width']=99
        for _ in range(100):reconciliation.check(proof,reconciliation.inventory['requirements'][0])
    reconciliation.before_publication()

    assert calls==[1] and proof.retained_bytes>0
    assert 'comparisons' not in proof.metadata['evidence']['runner_receipt']
    production=tmp_path/'production-packing';r.publish_object(production,dict(evidence=evidence,measurement=measurement,injected=False,timing_only=False,
        numeric_backing_references={str(backing):r.pipeline._bundle_byte_reference(backing)}))
    with pytest.raises(ValueError):r._CompletedPackingProof(production)

    with pytest.raises(TypeError):proof.proof=None
    with pytest.raises(TypeError):proof.proof._rows[next(iter(proof.proof._rows))]['tokens'][0]=99
    with pytest.raises(TypeError):proof.proof._specs[next(iter(proof.proof._specs))]['axis_sha256']='f'*64
    with pytest.raises(TypeError):proof.witness.identities=()

    for damage in ('input','profile','axis','donor'):
        changed=copy.deepcopy(measurement)
        if damage=='input':changed['timing_inputs'][0]['record']['streams']['clean']['tokens'][0]+=1
        if damage=='profile':changed['profile']['padded_width']+=1
        if damage=='axis':changed['axis_scope'][0]['axis_sha256']='f'*64
        if damage=='donor':changed['donor_convention']='wrong'
        with pytest.raises(ValueError):proof.check(changed)
    if mutation=='payload':
        payload=path/'payload.json';payload.write_bytes(payload.read_bytes()+b' ')
        with pytest.raises(ValueError):
            with r._PilotReconciliationPass([proof],dict(requirements=[measurement],finish_reserve_seconds=1),guard=lambda:None,injected=True):pass
    else:
        import os
        changed_pass=r._PilotReconciliationPass([proof],dict(requirements=[measurement],finish_reserve_seconds=1),guard=lambda:None,injected=True)
        with pytest.raises(ValueError):
            with changed_pass:
                numeric=next(backing.glob('*.npy'));old=numeric.stat();raw=bytearray(numeric.read_bytes());raw[-1]^=1;numeric.write_bytes(raw)
                os.utime(numeric,ns=(old.st_atime_ns,old.st_mtime_ns))
                changed_pass.check(proof,changed_pass.inventory['requirements'][0])
        with pytest.raises(ValueError):changed_pass.before_publication()
    with pytest.raises(ValueError):proof.check(measurement)


def test_allocation_contract_is_anchored_in_original_admission_for_live_and_pending(tmp_path):
    r,contract,lease,actual,base=_production_allocation_fixture()
    inv=dict(kind='a3_direction_inventory',identity={'injected':True,'commit':'a'*40},inventory_sha256='c'*64,phase='M2',expected_keys=[],finish_reserve_seconds=10,
        hardware=base['hardware'],storage_requirements=base['storage_requirements'])
    r,ledger,inv,path,_,_=_authority_case(tmp_path,inventory=inv)
    admission=r.read_object(tmp_path/'admission');admission.pop('admission_sha256');admission['allocation_contract']=contract
    admission['admission_sha256']=r.workload.digest(admission);admission_path=tmp_path/'contract-admission';r.publish_object(admission_path,admission)
    mapping=r.read_object(tmp_path/'current-map');mapping['original_admission_paths']=[str(admission_path)]
    mapping['entries'][0]['reservation_lineage']['admission_sha256']=admission['admission_sha256']
    mapping_path=tmp_path/'contract-mapping';r.publish_object(mapping_path,mapping)
    ledger=r.normalize_ledger(mapping_path,identity=inv['identity'],injected=True)
    allocation=dict(lease,kind='a3_injected_slurm_allocation_v1',injected=True);allocation_path=tmp_path/'contract-allocation';r.publish_object(allocation_path,allocation)
    reservation=r.read_object(path);reservation.update(admission_path=str(admission_path),admission_reference=r.object_reference(admission_path),
        admission_sha256=admission['admission_sha256'],allocation_contract=contract,injected_allocation_path=str(allocation_path))
    path=tmp_path/'contract-reservation';r.publish_object(path,reservation)
    assert r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)['allocation_verified']
    assert not r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None,require_allocation=False)['execution_authorized']
    changed=copy.deepcopy(reservation);changed['allocation_contract']['cpus']=1;changed_path=tmp_path/'lowered-cpu';r.publish_object(changed_path,changed)
    with pytest.raises(ValueError,match='original root admission'):
        r.validate_reservation(changed_path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None,require_allocation=False)


@pytest.mark.parametrize('experiment',['mask','edge'])
def test_allocation_contract_uses_own_validated_consumer_resource_shape(experiment):
    r,contract,lease,actual,_=_production_allocation_fixture()
    if experiment=='mask':
        from tests.test_a3_mask_pipeline import cost_fixture
        from component_analysis import a3_mask_workload as own
        inv,_,_=cost_fixture()
    else:
        from tests.test_a3_edge_pipeline import source_design,geometry,p
        from component_analysis import a3_edge_workload as own
        design=source_design();inv=own.freeze_inventory(design,{'far_v2':p.prepare_graph(design,'far_v2',geometry())},stage='fit',identity={'commit':'a'*40})
    own.validate_inventory(inv)
    assert 'hardware' not in inv
    floor=inv['storage_requirements']['tiers']['host_ram'];contract['memory_bytes']=max(32*1024**3,floor);lease['memory_bytes']=contract['memory_bytes']
    assert r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract) is lease
    contract['gpu_type']='a40';lease['gpu_types']=['a40']
    with pytest.raises(ValueError):r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract)
    contract['gpu_type']='h200';contract['memory_bytes']=floor-1;lease['gpu_types']=['h200']
    with pytest.raises(ValueError):r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract)


@pytest.mark.parametrize('damage',['kind','device'])
def test_unsupported_allocation_inventory_or_device_rejects(damage):
    r,contract,lease,actual,inv=_production_allocation_fixture()
    if damage=='kind':inv['kind']='unknown'
    else:inv['hardware']['gpu']='mystery'
    with pytest.raises(ValueError):r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract)


def test_atomic_reconciliation_rechecks_deadline_without_caching_live_authority(monkeypatch):
    import time
    r=runtime();end=time.time()+100
    def guard():return {'reservation':{'allocation_verified':True,'execution_authorized':True,'allocation':{'end_time_unix':end},'reservation':{'minimum_shard_seconds':1}}}
    with r._PilotReconciliationPass([],dict(requirements=[],finish_reserve_seconds=1),guard=guard,injected=True) as reconciliation:
        with monkeypatch.context() as scoped:
            scoped.setattr(r.time,'time',lambda:end)
            with pytest.raises(ValueError,match='finish'):reconciliation.check_deadline()


@pytest.mark.parametrize('target',['dict','list','empty_dict','empty_list'])
def test_cached_authority_rejects_public_reinitialization_including_empty_containers(tmp_path,target):
    key={} if target=='empty_dict' else {'ids':[]} if target=='empty_list' else {'id':'original'}
    inv=dict(identity={'injected':True,'commit':'a'*40},inventory_sha256='c'*64,phase='M2',expected_keys=[key],finish_reserve_seconds=10)
    r,ledger,inv,path,_,_=_authority_case(tmp_path,inventory=inv);original=json.loads(json.dumps(inv));calls=[]
    context=r.make_authority_context(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:calls.append(1))
    container=inv['expected_keys'] if target=='list' else inv['expected_keys'][0]['ids'] if target=='empty_list' else inv['expected_keys'][0]
    with pytest.raises(TypeError):
        if target in ('dict','empty_dict'):container.__init__(id='outside')
        elif target=='list':container.__init__([{'id':'outside'}])
        else:container.__init__(['outside'])
    with pytest.raises(TypeError):container._initialized=False
    with pytest.raises(TypeError):del container._initialized
    assert not hasattr(container,'__dict__')
    assert json.loads(json.dumps(inv))==original and copy.deepcopy(inv)==inv
    assert r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context,
        inventory_validator=lambda _:pytest.fail('reconstructed proof'))['execution_authorized'] is True
    assert calls==[1]


@pytest.mark.parametrize('constructor',['dict','list','dict_subclass','list_subclass'])
def test_frozen_construction_recursively_owns_mutable_children_and_preserves_json(constructor):
    r=runtime();mutable={'id':'original'}
    if constructor=='dict':value=r._FrozenJSONDict(child=mutable)
    elif constructor=='list':value=r._FrozenJSONList([mutable])
    elif constructor=='dict_subclass':
        class Mapping(dict):pass
        value=r._freeze_json(Mapping(child=mutable))
    else:
        class Sequence(list):pass
        value=r._freeze_json(Sequence([mutable]))
    mutable['id']='outside';child=value['child'] if isinstance(value,dict) else value[0]
    assert child['id']=='original'
    with pytest.raises(TypeError):child.__init__(id='outside')
    with pytest.raises(TypeError):child['id']='outside'
    assert copy.copy(value) is value and copy.deepcopy(value) is value
    assert json.loads(json.dumps(value))==({'child':{'id':'original'}} if isinstance(value,dict) else [{'id':'original'}])


@pytest.mark.parametrize('container_kind',['dict','list'])
def test_context_mint_reconstructs_uninitialized_frozen_instances(tmp_path,container_kind):
    r=runtime();cls=r._FrozenJSONDict if container_kind=='dict' else r._FrozenJSONList
    unsealed=cls.__new__(cls)
    key=unsealed if container_kind=='dict' else {'ids':unsealed}
    inv=dict(identity={'injected':True,'commit':'a'*40},inventory_sha256='c'*64,phase='M2',expected_keys=[key],finish_reserve_seconds=10)
    r,ledger,inv,path,_,_=_authority_case(tmp_path,inventory=inv);original=json.loads(json.dumps(inv))
    context=r.make_authority_context(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    consumed=inv['expected_keys'][0] if container_kind=='dict' else inv['expected_keys'][0]['ids']
    assert consumed is not unsealed and consumed._initialized is True
    unsealed.__init__({'outside':1} if container_kind=='dict' else ['outside'])
    with pytest.raises(TypeError):consumed.__init__({'outside':1} if container_kind=='dict' else ['outside'])
    assert json.loads(json.dumps(inv))==original
    assert r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context,
        inventory_validator=lambda _:pytest.fail('reconstructed proof'))['execution_authorized'] is True


def _indexed_proof_case(tmp_path):
    from tests.test_a3_direction_workload import inventory,receipts,packing_evidence
    r=runtime();inv=inventory();receipt=receipts(inv)[0]
    m=next(x for x in receipt['measurements'] if x.get('packing_id') and x.get('axis_scope'));e=receipt['packing_evidence'][m['packing_id']]
    paths=[]
    for i in range(3):
        measurement=copy.deepcopy(m)
        if i<2:measurement['profile']=dict(measurement['profile'],padded_width=measurement['profile']['padded_width']+i+1)
        evidence=e if i==2 else packing_evidence(measurement)
        path=tmp_path/str(i);r.publish_object(path,dict(injected=True,timing_only=True,evidence=evidence,measurement=measurement))
        paths.append(path)
    return r,paths,m


def test_candidate_index_filters_without_io_but_refreshes_every_dependency(tmp_path,monkeypatch):
    r,paths,m=_indexed_proof_case(tmp_path)
    proofs=[r._CompletedPackingProof(path) for path in paths]
    index=r._PackingCandidateIndex(proofs)
    calls=[];original=r._file_tree_identity
    monkeypatch.setattr(r,'_file_tree_identity',lambda p:calls.append(str(p)) or original(p))
    selected=index.candidates(m['profile'],m['axis_scope'])
    assert selected==[proofs[-1]] and calls==[]
    index.refresh_dependencies()
    assert len(calls)==len(paths) and len(set(calls))==len(paths)
    with pytest.raises(TypeError):index.proofs=()
    # A rejected candidate is still an immutable referenced dependency.
    bad=paths[0]/'payload.json';bad.write_bytes(bad.read_bytes()+b' ')
    assert index.candidates(m['profile'],m['axis_scope'])==selected
    with pytest.raises(ValueError):index.refresh_dependencies()


def test_candidate_index_preserves_exact_axis_selection_and_rejects_unminted_values(tmp_path):
    r,paths,m=_indexed_proof_case(tmp_path);proof=r._CompletedPackingProof(paths[-1]);index=r._PackingCandidateIndex([proof])
    wrong=copy.deepcopy(m['axis_scope']);wrong[0]['axis_sha256']='f'*64
    assert index.candidates(m['profile'],wrong)==[]
    with pytest.raises(ValueError):r._PackingCandidateIndex([{'profile':m['profile']}])
    with pytest.raises(TypeError):index.__init__([proof])


def test_candidate_index_rejects_ordinary_proof_child_seal_deletion(tmp_path):
    r,paths,m=_indexed_proof_case(tmp_path);proof=r._CompletedPackingProof(paths[-1]);index=r._PackingCandidateIndex([proof])
    assert index.candidates(m['profile'],m['axis_scope'])==[proof]
    with pytest.raises(TypeError):del proof._sealed
    with pytest.raises(TypeError):proof.metadata={}


def test_sealed_reuse_context_removes_duplicate_runner_file_validation(tmp_path,fake,monkeypatch):
    from dataclasses import replace
    from tests.test_a3_direction_runner import measured_setup,batch,SITE
    r=runtime();ident,index,axes,cells=measured_setup(fake);b=replace(batch(),ids=['target-a','target-b']);receipt=ident.pop('packed_equivalence')
    path=tmp_path/'measured';r.publish_object(path,dict(injected=True,evidence=r.packing_evidence(receipt,[batch()]),measurement=dict(profile=ident['numeric_profile'],timing_inputs=[],axis_scope=[])))
    proof=r._CompletedPackingProof(path);lookup=r._PackingCandidateIndex([proof])
    reuse=tmp_path/'reuse';r.freeze_profile_reuse(reuse,measured_path=path,batch=b,cells=[cells[1]],axes=axes,capture_index=index,
        policy=r.workload.PROFILE_REUSE_POLICY,validated_proof=proof)
    identity=dict(ident,profile_reuse=str(reuse));context=r._validated_reuse_context(identity,b,proof=proof)
    with pytest.raises(ValueError):r.validate_profile_reuse(identity,b,context=context)
    calls=[]
    def old_reader(*a,**kw):pytest.fail('repeated completed proof lookup inside runner')
    monkeypatch.setattr(r,'_validated_measurement',old_reader)
    with context.operation():
        assert r.validate_profile_reuse(identity,b,context=context)
        assert r.runner._geometry(b,identity,reuse_context=context)==2
        assert r.runner._packing_receipt(identity,b,reuse_context=context)
        with pytest.raises(ValueError):r.validate_profile_reuse(identity,replace(b,ids=['wrong','ids']),context=context)
    with pytest.raises(ValueError):r.validate_profile_reuse(identity,b,context=context)
    with pytest.raises(ValueError):r.validate_profile_reuse(identity,b,context={})


def test_reuse_overhead_records_observed_scope_calls_without_model_forwards(tmp_path,fake,monkeypatch):
    from tests.test_a3_direction_runner import measured_setup,batch
    r=runtime();ident,index,axes,cells=measured_setup(fake)
    evidence=r.packing_evidence(ident['packed_equivalence'],[batch()]);scope_calls=[]
    original_scope=r._ValidatedReuseContext.scope
    def observed(context,*args,**kwargs):
        scope_calls.append(1);return original_scope(context,*args,**kwargs)
    original_receipt=r.runner._packing_receipt
    def extra_valid_lookup(*args,**kwargs):
        original_receipt(*args,**kwargs);return original_receipt(*args,**kwargs)
    monkeypatch.setattr(r._ValidatedReuseContext,'scope',observed)
    monkeypatch.setattr(r.runner,'_packing_receipt',extra_valid_lookup)
    before=len(fake)
    overhead=r._measure_reuse_overhead(tmp_path,ident['numeric_profile'],evidence,[batch()],cells,axes,index,None)
    assert len(fake)==before
    assert overhead['scope_checks']==len(scope_calls)==4
    assert overhead['boundary_refreshes']==2 and overhead['context_seconds']>0
    print(json.dumps(dict(observed_scope_calls=len(scope_calls),recorded_scope_calls=overhead['scope_checks'],
        overhead_model_forwards=len(fake)-before,boundary_refreshes=overhead['boundary_refreshes'])))


def test_serial_donor_cache_maps_and_observed_rows_match_rebuilt_source(tmp_path,fake):
    r,d,p=_fake_pilot_inputs(1);inv=r.workload.build_inventory(d,p,stage='prefit')
    invocation=next(x for x in r._serial_invocations(inv) if x['source_task']=='far_v2')
    result=r._pilot_invocation(object(),d,p,invocation,axes=None,root=tmp_path,guard=lambda:None)
    original=dict(kind='a3_serial_numeric_invocation_v1',actual_execution=True,injected=True,timing_only=True,
        source_commit=p['commit'],runtime_profile=r.runtime_kernel_identity(object()),receipt=result['receipt'],
        positive_controls=result['positive_controls'],numeric_backing_references={})
    measurement=r._pilot_scope_measurement(d,invocation)
    for damage in (None,'id','condition','stream','readout','cache_hash','cache_missing','cache_source','observation','source_id','split'):
        value=copy.deepcopy(original);raw=value['receipt']
        descriptor=next(s['donors'][0] for ss in raw['batches'].values() for s in ss if s['operation']=='interchange')
        if damage=='id':descriptor['mapping']['donor_id']='other'
        if damage=='condition':descriptor['mapping']['donor_condition']='other'
        if damage=='stream':descriptor['mapping']['donor_stream']='not-a-real-stream'
        if damage=='readout':descriptor['mapping']['donor_positions']=[0]
        if damage=='cache_hash':descriptor['cached_donor_sha256']='0'*64
        if damage=='cache_missing':raw['donor_cache']=[]
        if damage=='cache_source':
            changed=raw['donor_cache'][0];changed['row']['tokens'][0]+=1
            cache_value=r._serial_cache_wire(changed['row'],decode=True);new_hash=r.runner._digest(cache_value)
            for ss in raw['batches'].values():
                for spec in ss:
                    for item in spec.get('donors',[]):
                        m=item['mapping'];key=[m['donor_profile_id'],cache_value['task'],m['donor_condition'],m['donor_stream'],m['donor_id']]
                        if key==changed['key']:item['cached_donor_sha256']=new_hash
        if damage=='observation':next(x for x in raw['rows'] if x['operation']=='interchange')['donor_mapping']['donor_positions']=[0]
        if damage in ('source_id','split'):
            for ss in raw['batches'].values():
                for spec in ss:
                    for item in spec.get('donors',[]):item['mapping']['donor_'+damage]='foreign'
            for row in raw['rows']:
                if row['operation']=='interchange':row['donor_mapping']['donor_'+damage]='foreign'
        raw['receipt_sha256']=r.workload.digest({k:v for k,v in raw.items() if k!='receipt_sha256'})
        path=tmp_path/('baseline' if damage is None else damage);r.publish_object(path,value)
        if damage is None:r._SerialNumericProof(path).check_scope(measurement)
        else:
            with pytest.raises(ValueError):r._SerialNumericProof(path).check_scope(measurement)


@pytest.mark.parametrize('tile',[1,2])
def test_guard_benchmark_covers_final_receipt_and_all_numeric_roots(tmp_path,fake,tile):
    from types import SimpleNamespace
    r,d,p=_fake_pilot_inputs(tile);inv=r.workload.build_inventory(d,p,stage='prefit')
    receipt=r.run_pilot(object(),d,p,inv,root=tmp_path,args=SimpleNamespace(pilot_part='prefit',selected=None),guard=lambda:None,startup_seconds=0)
    r.publish_object(tmp_path/'admission',{'pilot_receipt_paths':[str(tmp_path/'pilot'/'prefit')]})
    r.publish_object(tmp_path/'reservation',{'admission_path':str(tmp_path/'admission')})
    index=r._admitted_candidate_index(SimpleNamespace(reservation=str(tmp_path/'reservation')),d,p)
    actual=index.refresh_dependencies();measured=receipt['guard_dependency_measurement']
    assert measured['measured_bytes_per_refresh']>=actual['verified_bytes'] and measured['measured_roots']>=actual['roots']
    assert set(index.forest.paths)-{str((tmp_path/'pilot'/'prefit').absolute()),index.startup_reference['path']}==set(measured['dependency_roots'])
    bad=copy.deepcopy(receipt);bad['guard_dependency_measurement']['final_receipt_file_upper_bytes']['payload.json']=1
    with pytest.raises(ValueError):r._publish_measured_pilot_receipt(tmp_path/'underflow',bad)
    assert not (tmp_path/'underflow').exists()
    envelope=tmp_path/'inert';r.publish_object(envelope,dict(inert_final_receipt_byte_envelope='x'*100,execution_authorized=False))
    with pytest.raises(ValueError):r._authenticated_pilot_receipts(d,p,r.read_object(tmp_path/'pilot-target-inventory'/'prefit'),[envelope],ledger_path=None)
    print(json.dumps(dict(tile=tile,actual_bytes=actual['verified_bytes'],measured_bytes=measured['measured_bytes_per_refresh'],roots=actual['roots'])))


def test_completed_index_startup_is_measured_conditionally_and_charged_per_job(tmp_path,fake,monkeypatch):
    from types import SimpleNamespace
    from tests.test_a3_direction_workload import ledger
    r,d,p=_fake_pilot_inputs(1);inv=r.workload.build_inventory(d,p,stage='prefit')
    receipt=r.run_pilot(object(),d,p,inv,root=tmp_path,args=SimpleNamespace(pilot_part='prefit',selected=None),guard=lambda:None,startup_seconds=0)
    target=r.read_object(tmp_path/'pilot-target-inventory'/'prefit');path=tmp_path/'pilot'/'prefit'
    index,receipts,sources=r._completed_pilot_index(d,p,target,[path],ledger_path=None,host_capacity_bytes=10**12)
    cost=index.startup_evidence
    assert cost['seconds']==index.startup_seconds>0 and cost['process_local_cold'] and not cost['os_cache_cold_claimed']
    assert cost['conditional'] and cost['execution_authorized'] is False and cost['host_profile']['threads']['OMP_NUM_THREADS']=='1'
    assert cost['dependency_roots']==11 and cost['dependency_bytes_per_refresh']>0 and cost['retained_bytes']>0
    reference=cost['startup_record_reference'];record=r.read_object(reference['path'])
    assert record['execution_authorized'] is False and record['process']['pid']>0
    assert record['source_identity']==target['identity'] and record['target_inventory_sha256']==target['inventory_sha256']
    assert 'publication_seconds' not in record and cost['publication_seconds']>0
    assert cost['seconds']>=record['construction']['seconds']+cost['publication_seconds']
    assert r._object_payload_size(reference)<=r.workload.STARTUP_REFERENCE_BYTES
    assert r._validate_startup_record(reference,d,p,expected_job_id='injected-cpu')==record
    with pytest.raises(ValueError):r._validate_startup_record(reference,d,p,expected_job_id='injected-cpu',expected_pid=record['process']['pid']+1)
    budget=ledger(target);budget['storage_capacities']['host_ram']['available_bytes']=10**12
    plain=r.workload.project_cost(receipts,target,budget)
    proposal=r.workload.project_cost(receipts,target,budget,runtime_cost=cost)
    assert proposal['startup_seconds']==pytest.approx(plain['startup_seconds']+cost['seconds'])
    assert proposal['conditional_proposal'] and 'bounded allocated-host authentication/index startup' in proposal['missing_execution_prerequisites']
    for actual,old in zip(proposal['jobs'],plain['jobs']):assert actual['projected_seconds']>=old['projected_seconds']+cost['seconds']-1e-8
    with pytest.raises(ValueError):r._completed_pilot_index(d,p,target,[path],ledger_path=None,host_capacity_bytes=1)
    bad=dict(cost,target_inventory_sha256='0'*64)
    with pytest.raises(ValueError):r.workload.project_cost(receipts,target,budget,runtime_cost=bad)
    for damage in ('conditional','capacity'):
        bad=dict(cost)
        if damage=='conditional':bad['conditional']=False
        else:bad['frozen_host_capacity_bytes']=1
        with pytest.raises(ValueError):r.workload.project_cost(receipts,target,budget,runtime_cost=bad)
    r.publish_object(tmp_path/'admission',dict(pilot_receipt_paths=[str(path)],completed_host_startup_cost=cost))
    r.publish_object(tmp_path/'reservation',dict(admission_path=str(tmp_path/'admission'),upper_inventory_path=str(tmp_path/'pilot-target-inventory'/'prefit')))
    actual=r._admitted_candidate_index(SimpleNamespace(reservation=str(tmp_path/'reservation')),d,p)
    assert actual.startup_reconciliation['forecast_seconds']==cost['seconds'] and actual.startup_reconciliation['retroactive_authorization'] is False
    shards=copy.deepcopy(target['shards'][:2]);expected=[]
    for shard in shards:
        axes,shard['cells']=r._pilot_axes(object(),shard['cells'],None)
        rows,execution,identity=r.score_runtime_shard(object(),d,p,shard,axes=axes,output=tmp_path/'execution'/shard['shard_id'],
            guard=lambda:None,measured_index=index,shared_root=tmp_path)
        assert execution['candidate_index_startup_reference']==reference and execution['candidate_index_startup_seconds']==cost['seconds']
        assert r._object_payload_size({k:v for k,v in execution.items() if k.startswith('candidate_index_startup_')})<=r.workload.STARTUP_REFERENCE_BYTES
        assert execution['candidate_index_startup_dependency_roots']==cost['dependency_roots']
        r.artifacts.publish_shard(tmp_path/'runtime-shards'/shard['shard_id'],identity=identity,expected_keys=shard['expected_keys'],rows=rows,execution=execution)
        expected.extend(shard['expected_keys'])
    one=dict(shards=shards,expected_keys=expected);validations=[];original_validator=r._validate_startup_record
    def counted(*args,**kwargs):validations.append(1);return original_validator(*args,**kwargs)
    with monkeypatch.context() as scoped:
        scoped.setattr(r,'_validate_startup_record',counted)
        rows,_=r.read_runtime_rows(d,p,one,tmp_path/'runtime-shards')
    assert len(rows)==len(expected) and validations==[1]
    manifest_path=tmp_path/'runtime-shards'/shards[1]['shard_id']/'run_manifest.json';saved=manifest_path.read_bytes()
    changed=json.loads(saved);changed['execution']['producer_pid']+=1
    r.common.write_json(manifest_path,changed);r.artifacts._finish(manifest_path.parent)
    with pytest.raises(ValueError):r.read_runtime_rows(d,p,one,tmp_path/'runtime-shards')
    manifest_path.write_bytes(saved);r.artifacts._finish(manifest_path.parent)
    print(json.dumps(dict(host_startup_seconds=cost['seconds'],guard_seconds=cost['guard_seconds'],dependency_roots=cost['dependency_roots'],
        dependency_bytes=cost['dependency_bytes_per_refresh'],retained_bytes=cost['retained_bytes'],peak_host_bytes=cost['peak_host_bytes'],
        conditional=cost['conditional'],source_reference_count=len(cost['pilot_references']),cpu_model=cost['host_profile']['cpu_model'])))
    marker=Path(reference['path'])/'COMPLETE.json';original_marker=marker.read_bytes();marker.unlink()
    with pytest.raises((ValueError,FileNotFoundError)):r._validate_startup_record(reference,d,p,expected_job_id='injected-cpu')
    with pytest.raises((ValueError,FileNotFoundError)):r.read_runtime_rows(d,p,one,tmp_path/'runtime-shards')
    marker.write_bytes(original_marker)
    payload=Path(reference['path'])/'payload.json';payload.write_bytes(payload.read_bytes()+b' ')
    with pytest.raises(ValueError):index.refresh_dependencies()
    with pytest.raises(ValueError):r._validate_startup_record(reference,d,p,expected_job_id='injected-cpu')
    with pytest.raises(ValueError):r.read_runtime_rows(d,p,one,tmp_path/'runtime-shards')


def test_production_shaped_completed_startup_preserves_lifecycle_and_footprint_refusals(tmp_path,monkeypatch,fake):
    import shutil
    r,d,p,target,path,mapping,live_path,live=_production_cost_source_case(tmp_path,monkeypatch,capture_model=object())
    receipt=r.read_object(path);proofs=[r._CompletedPackingProof(v['measured_path']) for v in receipt['packing_evidence'].values()]
    reconciliation=r._PilotReconciliationPass(proofs,target,guard=lambda:None,injected=True)
    with reconciliation:pass
    receipt.update(proof_validation_seconds=sum(x.validation_seconds for x in proofs),
        proof_verified_bytes=reconciliation.verified_bytes,proof_verification_seconds=reconciliation.verification_seconds)
    r._measure_complete_guard_union(receipt,reconciliation,tmp_path,lambda:None)
    shutil.rmtree(path);r._publish_measured_pilot_receipt(path,receipt)
    capacity=r.read_object(receipt['origin']['reservation_reference']['path'])['allocation_contract']['memory_bytes']
    index,_,sources=r._completed_pilot_index(d,p,target,[path],ledger_path=mapping,host_capacity_bytes=capacity)
    assert len(sources)==1 and index.startup_evidence['conditional'] and index.startup_evidence['frozen_host_capacity_bytes']==capacity
    import os
    assert r.read_object(index.startup_reference['path'])['process']['job_id']==os.environ.get('SLURM_JOB_ID','host-cpu')
    original=copy.deepcopy(receipt)
    for damage in ('bytes','roots','incomplete','running'):
        changed=copy.deepcopy(original)
        if damage=='bytes':changed['guard_dependency_measurement']['measured_bytes_per_refresh']=1
        if damage=='roots':changed['guard_dependency_measurement']['dependency_roots']=[]
        if damage=='incomplete':changed['complete']=False
        if damage=='running':
            live['reservations'][0]['status']='running';live_path.write_text(json.dumps(live))
        shutil.rmtree(path);r.publish_object(path,changed)
        with pytest.raises(ValueError):r._completed_pilot_index(d,p,target,[path],ledger_path=mapping,host_capacity_bytes=capacity)


def test_production_cost_intake_rejects_synthetic_completed_receipts_before_projector(tmp_path):
    from tests.test_a3_direction_workload import fixture,receipts
    r=runtime();d,p,_=fixture();d['injected']=False;p['task_order']=list(d['tasks']);p['numeric_profile']={'dtype':'bfloat16','backend':'native'};p['workload']['vocabulary_size']=8
    for task,spec in d['tasks'].items():spec['assessment_ids']=[task+'a'+str(i) for i in range(100)]
    for task,n in [('ioi',100),('mmlu',32)]:
        old=d['utility'][task][0];d['utility'][task]=[dict(copy.deepcopy(old),instance_id=task+'a'+str(i)) for i in range(n)]
        old=d[task+'_validation'][0];d[task+'_validation']=[dict(copy.deepcopy(old),instance_id=task+'v'+str(i)) for i in range(n)]
    inv=r.workload.build_inventory(d,p,stage='fit-select');receipt=receipts(inv)[0]
    receipt.update(injected=True,actual_execution=False,job_id='injected-cpu',part='wrong',source_split='assessment',runtime={'device':'cpu'},pilot_inventory_sha256='0'*64)
    path=tmp_path/'receipt';r.publish_object(path,receipt)
    with pytest.raises(ValueError):r._authenticated_pilot_receipts(d,p,inv,[path],ledger_path=tmp_path/'missing')


def _production_cost_source_case(tmp_path,monkeypatch,*,capture_model=None):
    from tests.test_a3_direction_workload import fixture,receipts,packing_evidence
    r=runtime();d,p,_=fixture();d['injected']=False;p['task_order']=list(d['tasks']);p['numeric_profile']={'dtype':'torch.bfloat16','backend':'native'}
    p['workload'].update(vocabulary_size=8,hardware={'gpu':'h200','count':1})
    for task,spec in d['tasks'].items():spec['assessment_ids']=[task+'a'+str(i) for i in range(100)]
    for task,n in [('ioi',100),('mmlu',32)]:
        for name in ('utility','validation'):
            original=d['utility'][task][0] if name=='utility' else d[task+'_validation'][0]
            values=[dict(copy.deepcopy(original),instance_id=task+name+str(i)) for i in range(n)]
            if name=='utility':d['utility'][task]=values
            else:d[task+'_validation']=values
    for task,values in list(d['access_rows'].items())+[(t,d[t+'_validation']) for t in ('ioi','mmlu')]:
        for row in values:
            row.update(task=task,source_id=row['instance_id'],source_hash='e'*64,expected_token=1,honest_token=2,opposite_token=1,choice_tokens=[0,1,2,3],gold_letter='B',question_hash=row['instance_id'])
            for value in row['streams'].values():value.update(layout=None,expected_token=1,honest_token=2,opposite_token=1)
    target=r.workload.build_inventory(d,p,stage='fit-select');pilot=r.workload.build_inventory(d,p,stage='prefit')
    r,_,_,reservation_path,live_path,live=_authority_case(tmp_path/'authority',inventory=pilot)
    output=tmp_path/'output';output.mkdir();actual=live['reservations'][0];actual.update(status='completed',output_dir=str(output));live_path.write_text(json.dumps(live))
    # Authentic completed CPU preparation data, rooted in the original admission.
    target_path=output/'pilot-target-inventory'/'prefit';emitted=r._publish_prepared_target_object(target_path,target)
    source=r._prepared_source_identity(p)
    preparation_path=output/'pilot-target-preparation'/'prefit'
    descriptor=dict(kind='a3_pilot_target_preparation_v1',part='prefit',target_stage='fit-select',injected=False,
        source_identity=source,pilot_inventory_reference=r.object_reference(tmp_path/'authority'/'upper'),
        pilot_inventory_sha256=pilot['inventory_sha256'],target_reference=emitted['reference'],
        emitted_payload_sha256=emitted['emitted_payload_sha256'],emitted_payload_bytes=emitted['emitted_payload_bytes'],
        inventory_sha256=target['inventory_sha256'],summary={key:target[key] for key in ('operation_counts','forward_counts','bytes','jobs','blockers',
            'conditional_unavailable','fit_failures','finish_reserve_seconds','hardware','reuse_policy')},storage_requirements=target['storage_requirements'],
        execution_settings=p['workload'],numeric_profile=p['numeric_profile'],finish_reserve_seconds=target['finish_reserve_seconds'],
        selected_reference=None,provenance=dict(normal_completion=True,exit_code=0,pid=__import__('os').getpid(),
            source_before=source['code_hashes'],source_after=source['code_hashes']),model_loaded=False,execution_authorized=False)
    r.publish_object(preparation_path,descriptor)
    target_ref=r.object_reference(target_path);prep_ref=r.object_reference(preparation_path)
    namespace=dict(work_dir=str(output),target_root=str(target_path),preparation_root=str(preparation_path),allowed_aliases=(),
        expected_resolved=dict(work_dir=str(output.resolve()),target_root=str(target_path.resolve()),preparation_root=str(preparation_path.resolve())))
    resource_path=output/'receiver-resources'
    # Measure the lower data-only reader on this explicit synthetic CPU fixture;
    # this is neither an operational resource upper bound nor model admission.
    _,_,_,_,observed_io,observed=r._read_prepared_target_object(target_ref,prep_ref,namespace)
    r.publish_object(resource_path,dict(kind='a3_prepared_target_receiver_resources_v1',references=dict(target=target_ref,preparation=prep_ref),
        source_identity=source,reader_sha256=r.common.file_hash(Path(r.__file__)),freeze_sha256=r.common.file_hash(Path(r.workload.__file__)),
        environment=r._prepared_environment(False),recipe=observed['recipe'],scope=observed['scope'],observed_io=observed_io,
        retained_metadata_bytes_bound=observed['retained_metadata_bytes']+1048576,extra_transient_bytes_bound=observed['extra_transient_bytes']+1048576,
        process_peak_rss_bytes_bound=2**44,cgroup_peak_bytes_bound=2**44,
        model_loaded=False,execution_authorized=False,provenance=dict(normal_completion=True,exit_code=0,
            injected=True,pid=__import__('os').getpid(),source_before=source['code_hashes'],source_after=source['code_hashes'])))
    prepared_binding=dict(part='prefit',pilot_inventory_sha256=pilot['inventory_sha256'],target_reference=target_ref,
        preparation_reference=prep_ref,receiver_resources_reference=r.object_reference(resource_path),namespace_policy=namespace)
    _,contract,_,_,_=_production_allocation_fixture();admission=r.read_object(tmp_path/'authority'/'admission');admission.pop('admission_sha256')
    admission.update(kind='a3_root_pilot_admission_v1',allocation_contract=contract,pilot_target_preparation=prepared_binding);admission['admission_sha256']=r.workload.digest(admission)
    ap=tmp_path/'original-admission';r.publish_object(ap,admission)
    mapping=r.read_object(tmp_path/'authority'/'current-map');snapshot=tmp_path/'completed-ledger.json';snapshot.write_bytes(live_path.read_bytes())
    mapping.update(ledger_snapshot_path=str(snapshot),ledger_sha256=r.common.file_hash(snapshot),original_admission_paths=[str(ap)],
        storage_capacities={'host_ram':{'pool':'ram','available_bytes':contract['memory_bytes']}})
    entry=mapping['entries'][0];entry.update(phase='M1',actual_entry=copy.deepcopy(actual));entry['reservation_lineage']['admission_sha256']=admission['admission_sha256']
    mp=tmp_path/'original-mapping';r.publish_object(mp,mapping)
    reservation=r.read_object(reservation_path);reservation.update(actual_entry={k:actual.get(k) for k in r.RESERVATION_FIELDS},admission_path=str(ap),admission_reference=r.object_reference(ap),admission_sha256=admission['admission_sha256'],allocation_contract=contract)
    rp=tmp_path/'original-reservation';r.publish_object(rp,reservation)
    origin=dict(target_preparation_reference=prep_ref,receiver_resources_reference=r.object_reference(resource_path),kind='a3_direction_pilot_origin_v1',work_dir=str(output),reservation_reference=r.object_reference(rp),admission_reference=r.object_reference(ap),
        original_mapping_reference=r.object_reference(mp),pilot_inventory_reference=r.object_reference(tmp_path/'authority'/'upper'),target_inventory_reference=r.object_reference(target_path))
    kernel=dict(device_type='cuda',hardware={'name':'NVIDIA H200'},dtype='bfloat16',backend='native')
    receipt=receipts(target)[0];receipt.update(injected=False,actual_execution=True,job_id='100',part='prefit',source_split='validation',pilot_inventory_sha256=pilot['inventory_sha256'],
        runtime={'device':'cuda:0','runtime_profile':kernel},runtime_profile=kernel,origin=origin)
    refs={};evidence={};built=[]
    for invocation in pilot['packing_invocations']:
        batches=r._expected_pilot_batches(d,invocation);inputs=r._timing_inputs_from_batches(batches,invocation['profile']);wanted=r._pilot_scope_measurement(d,invocation)['axis_scope']
        pieces=[]
        for b in batches:
            scope=[x for x in inputs if (x['condition'],x['stream'])==(b.condition,b.stream) and x['instance_id'] in b.ids]
            pieces.append(packing_evidence(dict(profile=invocation['profile'],timing_inputs=scope,axis_scope=wanted)))
        first=copy.deepcopy(pieces[0]);raw=first['runner_receipt']
        for piece in pieces[1:]:
            for name in ('batches','recipients','dummy_cells'):raw['scope'][name].update(piece['runner_receipt']['scope'][name])
            raw['comparisons'].extend(piece['runner_receipt']['comparisons']);first['snapshots'].update(piece['snapshots'])
        raw['nonzero_patches']=len(raw['comparisons']);raw['scope_sha256']=r.workload.digest(raw['scope']);raw['receipt_sha256']=r.workload.digest({k:v for k,v in raw.items() if k!='receipt_sha256'})
        path=output/'pilot-evidence'/'prefit'/invocation['invocation_id']
        r.publish_object(path,dict(injected=False,timing_only=True,source_commit=p['identity']['commit'],runtime_profile=kernel,evidence=first,
            measurement=dict(profile=invocation['profile'],timing_inputs=inputs,axis_scope=wanted)))
        proof=r._CompletedPackingProof(path);built.append(proof);ref=r.object_reference(path);refs[str(path.resolve())]=ref
        evidence[invocation['invocation_id']]=dict(kind='a3_packing_proof_reference_v1',evidence_sha256=proof.proof.source_digest,measured_path=str(path),measured_reference=ref)
    receipt['packing_evidence']=evidence;receipt['packing_references']=refs
    # Associate each genuine-shaped requirement with its complete invocation proof.
    for m in receipt['measurements']:
        if capture_model is not None and m['operation'].startswith('capture_') and m['profile']['axis_tile_size']>1:
            # Production-shaped provenance fixture only: numeric capture comes
            # from the explicitly injected CPU runner, never from an H200 job.
            from dataclasses import replace
            batches=[r._batch_for_timing(d,m['profile'],m['timing_inputs'])]
            chunks=[]
            # The CPU fixture hook has one site; preserve the frozen site label
            # while translating only the injected hook's component dictionary.
            from component_analysis import hooks
            original=hooks.capture_forward
            site=tuple(m['profile']['sites'][0])
            def capture(*args,**kwargs):
                result=original(*args,**dict(kwargs,components=[('head',0,0)],replacements=None))
                return replace(result,outputs={site:result.outputs[('head',0,0)]})
            with monkeypatch.context() as scoped:
                scoped.setattr(hooks,'capture_forward',capture)
                scoped.setattr(hooks,'device_and_dtype',lambda _: (torch.device('cpu'),torch.bfloat16))
                scoped.setattr(hooks,'attention_implementation',lambda _: 'native')
                run=r.runner._capture_readouts(capture_model,batches,sites=m['profile']['sites'],sink=chunks.append,
                    identity={'numeric_profile':m['profile']},measuring=True)
            m['capture_lane_equivalence']=r.capture_lane_evidence(run,chunks,batches,m['timing_inputs'])
            m.pop('packing_id',None);continue
        if not m.get('packing_id'):continue
        candidates=[i for i,proof in enumerate(built) if proof.proof._profile==m['profile'] and proof.proof.covers_axes(m['axis_scope'])]
        covered=[i for i in candidates if all((x['source_task'],x['condition'],x['stream'],x['instance_id']) in built[i].proof._rows for x in m['timing_inputs'])]
        if not covered and m['operation'].startswith('capture_'):
            m.pop('packing_id');continue  # donor-only capture is not a patched IOI invocation
        assert covered,(m['operation'],m['profile'])
        m['packing_id']=pilot['packing_invocations'][covered[0]]['invocation_id']
    receipt_path=output/'pilot'/'prefit';r.publish_object(receipt_path,receipt)
    real_normalize=r.normalize_ledger
    monkeypatch.setattr(r,'normalize_ledger',lambda path,**kw:real_normalize(path,**dict(kw,injected=True)))
    return r,d,p,target,receipt_path,mp,live_path,live


@pytest.mark.parametrize('damage',[None,'injected','execution','part','split','job','runtime','legacy','missing_numeric','status','output','source','completion','hardware','pilot_scope','target_scope','origin'])
def test_production_shaped_completed_pilot_intake_authenticates_original_sources(tmp_path,monkeypatch,damage):
    r,d,p,target,path,mapping,live_path,live=_production_cost_source_case(tmp_path,monkeypatch)
    if damage in ('status','output','source'):
        if damage=='status':live['reservations'][0]['status']='failed'
        if damage=='output':live['reservations'][0]['output_dir']='/other'
        if damage=='source':live['reservations'][0]['source_commit']='f'*40
        live_path.write_text(json.dumps(live))
    elif damage is not None:
        value=r.read_object(path)
        if damage=='injected':value['injected']=True
        if damage=='execution':value['actual_execution']=False
        if damage=='part':value['part']='selected'
        if damage=='split':value['source_split']='assessment'
        if damage=='job':value['job_id']='injected-cpu'
        if damage=='runtime':value['runtime']['device']='cpu'
        if damage=='completion':value['complete']=False
        if damage=='hardware':value['hardware']['gpu']='other'
        if damage=='pilot_scope':value['pilot_inventory_sha256']='0'*64
        if damage=='target_scope':value['inventory_sha256']='0'*64
        if damage=='origin':value['origin'].pop('reservation_reference')
        if damage=='legacy':next(iter(value['packing_evidence'].values()))['kind']='synthetic-inline'
        if damage=='missing_numeric':value['packing_evidence'].pop(next(iter(value['packing_evidence'])))
        # New completed bytes at the canonical output are a test fixture, not an old-source rewrite.
        import shutil
        shutil.rmtree(path);r.publish_object(path,value)
    if damage is None:
        receipts,sources=r._authenticated_pilot_receipts(d,p,target,[path],ledger_path=mapping)
        assert len(receipts)==len(sources)==1 and sources[0].value['execution_authorized'] is False
    else:
        with pytest.raises((ValueError,FileNotFoundError,KeyError)):r._authenticated_pilot_receipts(d,p,target,[path],ledger_path=mapping)


def test_production_shaped_completed_pilot_full_projector_and_numeric_tamper(tmp_path,monkeypatch,fake):
    """Production-shaped files and fake CPU numbers, never production admission."""
    from tests.test_a3_direction_workload import ledger
    import shutil
    r,d,p,target,path,mapping,_,_=_production_cost_source_case(tmp_path,monkeypatch,capture_model=object())
    receipts,sources=r._authenticated_pilot_receipts(d,p,target,[path],ledger_path=mapping)
    result=r.workload.project_cost(receipts,target,ledger(target),packing_proofs=r._cost_packing_proofs(receipts))
    assert len(sources)==1 and result['execution_authorized'] is False and result['projected_seconds']>0
    # Capture-only corrupt IOI has its own typed lane evidence, with no patch claim.
    capture=next(m for m in receipts[0]['measurements'] if m['operation'].startswith('capture_')
        and m['profile'].get('source_task')=='ioi' and any(x['stream']=='corrupt' for x in m['timing_inputs'])
        and m['profile']['axis_tile_size']>1)
    assert capture['capture_lane_equivalence']['kind']=='a3_intact_lane_equivalence_v1' and 'packing_id' not in capture
    entry=next(iter(receipts[0]['packing_evidence'].values()));numeric=Path(entry['measured_path']);original=r.read_object(numeric)
    original_receipt=copy.deepcopy(receipts[0]);cache_key=str(numeric.absolute())
    for damage in ('source','stage','extra_input','missing_reference','reference_bytes','missing_marker'):
        payload=copy.deepcopy(original);value=copy.deepcopy(original_receipt)
        if damage=='source':payload['source_commit']='f'*40
        if damage=='stage':payload['timing_only']=False
        if damage=='extra_input':
            # A valid proof over an extra batch cannot impersonate the exact invocation.
            evidence=payload['evidence'];bid=next(iter(evidence['snapshots']));rows=copy.deepcopy(evidence['snapshots'][bid])
            rows[0]['instance_id']='outside';newbid=r.workload.digest([r.workload.digest(x) for x in rows])
            evidence['snapshots'][newbid]=rows;raw=evidence['runner_receipt']
            for name in ('batches','recipients','dummy_cells'):raw['scope'][name][newbid]=copy.deepcopy(raw['scope'][name][bid])
            for row in raw['scope']['recipients'][newbid]:
                if row['instance_id']==evidence['snapshots'][bid][0]['instance_id']:row['instance_id']='outside'
            raw['scope_sha256']=r.workload.digest(raw['scope']);raw['receipt_sha256']=r.workload.digest({k:v for k,v in raw.items() if k!='receipt_sha256'})
        shutil.rmtree(numeric);r.publish_object(numeric,payload);r._MEASURED_PACKING_CACHE.pop(cache_key,None)
        ref=r.object_reference(numeric);proof_value=value['packing_evidence'][Path(numeric).name]
        proof_value.update(measured_reference=ref,evidence_sha256=r.workload.digest(payload['evidence']))
        value['packing_references'][str(numeric.resolve())]=ref
        if damage=='missing_reference':value['packing_references'].pop(str(numeric.resolve()))
        if damage=='reference_bytes':proof_value['measured_reference']=dict(ref,payload_sha256='0'*64)
        if damage=='missing_marker':(numeric/'COMPLETE.json').unlink()
        shutil.rmtree(path);r.publish_object(path,value)
        with pytest.raises((ValueError,FileNotFoundError)):
            r._authenticated_pilot_receipts(d,p,target,[path],ledger_path=mapping)
    print('full_projector_positive=1 numeric_tamper_rejections=6')


def test_existing_production_model_loader_guard_rejects_before_any_weight_call(tmp_path):
    r=runtime();design,protocol=_real_injected_design();design['injected']=False
    r.ladder.write_artifact(tmp_path/'design.json',design)
    calls=[]
    with pytest.raises(ValueError,match='injected loader'):
        r.main(['--experiment','directions','--stage','pilot','--pilot-part','prefit','--design',str(tmp_path/'design.json'),
            '--commit',protocol['commit'],'--work-dir',str(tmp_path)],model_loader=lambda _:calls.append(1))
    assert calls==[]


def test_dependency_guard_deduplicates_shared_backing_and_counts_actual_live_checks(tmp_path,monkeypatch):
    r,paths,m=_indexed_proof_case(tmp_path)
    backing=tmp_path/'shared';backing.mkdir();np.save(backing/'axis.npy',np.eye(2,dtype=np.float32),allow_pickle=False);r.artifacts._finish(backing)
    proofs=[]
    for i,path in enumerate(paths):
        payload=r.read_object(path);payload['numeric_backing_references']={str(backing):r.pipeline._bundle_byte_reference(backing)}
        target=tmp_path/f'backed-{i}';r.publish_object(target,payload);proofs.append(r._CompletedPackingProof(target))
    index=r._PackingCandidateIndex(proofs);io=[];live=[];original=r._file_tree_identity
    monkeypatch.setattr(r,'_file_tree_identity',lambda p:io.append(str(p)) or original(p))
    guard=r._DependencyGuard(lambda:live.append(1),index)
    guard();guard()
    assert guard.calls==len(live)==2 and index.forest.refreshes==2
    assert len(io)==8 and all(io.count(path)==2 for path in set(io))
    assert guard.elapsed_seconds>0 and index.forest.verified_bytes>0


@pytest.mark.parametrize('tile',[1,2])
def test_runtime_shard_evidence_counts_its_final_live_guard(tmp_path,fake,tile):
    r,d,p=_fake_pilot_inputs(tile);inv=r.workload.build_inventory(d,p,stage='fit-select')
    shard=copy.deepcopy(inv['shards'][0]);axes,shard['cells']=r._pilot_axes(object(),shard['cells'],None)
    proofs=[]
    if tile>1:
        pilot=r.workload.build_inventory(d,p,stage='prefit')
        invocation=next(x for x in pilot['packing_invocations'] if x['profile']==shard['profile']
            and x['analysis_task']==shard['expected_keys'][0][1])
        measured=r._pilot_invocation(object(),d,p,invocation,axes=None,root=tmp_path,guard=lambda:None)
        path=tmp_path/'measured';r.publish_object(path,dict(injected=True,timing_only=True,source_commit=p['commit'],
            runtime_profile=r.runtime_kernel_identity(object()),evidence=measured['evidence'],measurement=r._pilot_scope_measurement(d,invocation)))
        proofs.append(r._CompletedPackingProof(path))
    index=r._PackingCandidateIndex(proofs);live=[];guard=r._DependencyGuard(lambda:live.append(1),index)
    before=len(fake)
    rows,evidence,_=r.score_runtime_shard(object(),d,p,shard,axes=axes,output=tmp_path/'shard',guard=guard,measured_index=index,axis_class=True)
    assert len(rows)==len(shard['expected_keys'])
    assert evidence['dependency_guard_calls']==len(live)==guard.calls
    assert evidence['dependency_refreshes']==index.forest.refreshes
    assert guard.calls<=10
    print(json.dumps(dict(tile=tile,rows=len(rows),actual_model_forwards=len(fake)-before,
        live_guard_calls=len(live),recorded_guard_calls=evidence['dependency_guard_calls'],recorded_refreshes=evidence['dependency_refreshes'])))


@pytest.mark.parametrize('damage',['production','duplicate','unknown','mixed','wrong_stage'])
def test_bounded_verification_shards_reject_invalid_selectors_before_model(tmp_path,damage):
    from tests.test_a3_direction_workload import inventory
    from types import SimpleNamespace
    r=runtime();inv=inventory('remaining');design={'injected':damage!='production'}
    calibration=next(s['shard_id'] for s in inv['shards'] if s['panel']=='calibration')
    assessment=next(s['shard_id'] for s in inv['shards'] if s['panel']=='assessment')
    ids=[calibration]
    if damage=='duplicate':ids*=2
    if damage=='unknown':ids=['missing']
    if damage=='wrong_stage':ids=[assessment]
    args=SimpleNamespace(stage='assess',panel='calibration',shard_id=calibration if damage=='mixed' else None)
    with pytest.raises(ValueError):r.run_scoring(object(),design,{},inv,root=tmp_path,args=args,guard=lambda:pytest.fail('model boundary reached'),shard_ids=ids)


def test_bounded_scenario_verifies_full_model_config_state_source_and_tamper(tmp_path,monkeypatch):
    import sys,os
    if sys.version_info[:2]<(3,12):pytest.skip('pinned NNsight scenario runs on mgnp')
    from tests import a3_direction_native_scenario as scenario
    scenario.scenario_init(tmp_path)
    _,_,model,plain=scenario.verify_scenario(tmp_path)
    identity=scenario.model_identity(plain)
    _,_,model2,plain2=scenario.verify_scenario(tmp_path)
    assert scenario.model_identity(plain2)==identity
    with torch.no_grad():plain2(torch.tensor([[1,2,3]]))
    assert scenario.model_identity(plain2)==identity
    real_sources=scenario.source_identity
    with monkeypatch.context() as scoped:
        scoped.setattr(scenario,'source_identity',lambda:dict(real_sources(),changed='0'*64))
        with pytest.raises(ValueError,match='source changed'):scenario.verify_scenario(tmp_path,load_model=False)
    original_model=scenario.tiny_model
    def changed_config():
        wrapped,plain=original_model();plain.config.num_hidden_layers+=1;return wrapped,plain
    with monkeypatch.context() as scoped:
        scoped.setattr(scenario,'tiny_model',changed_config)
        with pytest.raises(ValueError,match='state/config'):scenario.verify_scenario(tmp_path)
    with torch.no_grad():next(plain2.parameters()).view(-1)[0]+=1
    assert scenario.model_identity(plain2)!=identity
    backing=tmp_path/'tiny-model'/'state.npz';old=backing.stat();data=bytearray(backing.read_bytes());data[-1]^=1;backing.write_bytes(data)
    os.utime(backing,ns=(old.st_atime_ns,old.st_mtime_ns))
    with pytest.raises(ValueError):scenario.verify_scenario(tmp_path,load_model=False)


def test_bounded_scenario_rejects_changed_frozen_inventory_before_resume(tmp_path):
    from tests import a3_direction_native_scenario as scenario
    r=runtime();d,p=_real_injected_design();inv=scenario.inventory(tmp_path,d,p,'prefit')
    changed=copy.deepcopy(p);changed['workload']['microbatch_size']=1
    with pytest.raises(ValueError):scenario.inventory(tmp_path,d,changed,'prefit')


def test_bounded_pilot_cases_resume_authenticates_original_numbers_and_full_coverage(tmp_path,fake,monkeypatch):
    from tests import a3_direction_native_scenario as scenario
    r,d,p=_fake_pilot_inputs(2);inv=r.workload.build_inventory(d,p,stage='prefit')
    binding={'kind':'explicit_fake_cpu_case_binding','source':scenario.source_identity()}
    ids=[x['invocation_id'] for x in inv['packing_invocations']]
    for selected_ids in (['missing'],[ids[0],ids[0]]):
        with pytest.raises(ValueError):scenario.pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',case_ids=selected_ids,binding=binding)
    prod=copy.deepcopy(d);prod['injected']=False
    with pytest.raises(ValueError):scenario.pilot_cases(object(),prod,p,inv,root=tmp_path,part='prefit',case_ids=[ids[0]],binding=binding)
    scenario.pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',case_ids=ids[:1],binding=binding)
    assert not (tmp_path/'pilot'/'prefit').exists()
    with pytest.raises(ValueError,match='coverage'):scenario.aggregate_pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',binding=binding)
    first=tmp_path/'pilot-verification-cases'/'prefit'/ids[0]
    before=r.object_reference(first);calls=len(fake)
    scenario.pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',case_ids=ids[:1],binding=binding,resume=True)
    assert len(fake)==calls and r.object_reference(first)==before
    with pytest.raises(ValueError):scenario.pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',case_ids=ids[:1],binding=dict(binding,source={}),resume=True)
    # A marker alone cannot upgrade a partial or modified actual numeric object.
    payload=first/'numeric'/'payload.json';original=payload.read_bytes();payload.write_bytes(original+b' ')
    with pytest.raises(ValueError):scenario.pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',case_ids=ids[:1],binding=binding,resume=True)
    payload.write_bytes(original)
    marker=first/'numeric'/'COMPLETE.json';data=marker.read_bytes();marker.unlink()
    with pytest.raises((ValueError,FileNotFoundError)):scenario.pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',case_ids=ids[:1],binding=binding,resume=True)
    marker.write_bytes(data)
    scenario.pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',case_ids=ids[1:],binding=binding)
    original_invocation=r._pilot_invocation
    result=scenario.aggregate_pilot_cases(object(),d,p,inv,root=tmp_path,part='prefit',binding=binding)
    assert result['complete'] and len(result['packing_evidence'])==len(ids)
    assert r._pilot_invocation is original_invocation
    aggregate=r.read_object(tmp_path/'pilot-verification-aggregate'/'prefit')
    assert aggregate['case_order']==ids and aggregate['original_case_forward_calls']>0 and aggregate['case_forwards_reexecuted'] is False
    assert r.object_reference(first)==before


@pytest.mark.parametrize('fault',[None,'directions','edges','M2','M3','M4','M5','contingency_low','total','other_M1'])
def test_n5_exact_additive_boundary_preserves_other_caps(fault):
    from tests.test_a3_direction_workload import _n5_fixture,_n5_actual
    w,policy,old,a=_n5_fixture();new,a=_n5_actual(w,policy,a)
    entries=[old,new]+[dict(id=phase+sub,phase=phase,subphase=sub,reserved_gpu_hours=h,state='completed',actual_gpu_hours=0)
        for phase,sub,h in [('M1','directions',.5),('M1','edges',.75),('M2','directions',9),('M3','neurons',4),('M4','edges',9),('M5','masks',10)]]
    contingency=5.25
    if fault in ('directions','edges'):
        next(x for x in entries if x['phase']=='M1' and x['subphase']==fault)['reserved_gpu_hours']+=.01
    elif fault in ('M2','M3','M4','M5'):next(x for x in entries if x['phase']==fault)['reserved_gpu_hours']+=.01
    elif fault=='contingency_low':contingency=5.24
    elif fault=='total':contingency=5.26
    elif fault=='other_M1':entries.append(dict(phase='M1',subphase='other',reserved_gpu_hours=.01))
    if fault is None:assert runtime().validate_global_budgets(entries,contingency_remaining=contingency)['all']==34.75
    else:
        with pytest.raises(ValueError):runtime().validate_global_budgets(entries,contingency_remaining=contingency)


def test_n5_prospective_actual_successor_live_order(tmp_path):
    from tests.test_a3_direction_workload import _n5_fixture,_n5_actual
    import time
    r=runtime();w,policy,old,admission=_n5_fixture();identity=admission['identity']
    from pathlib import Path
    original_admission_path=Path(policy['original_reservation']['output_dir']).parent/'root-mask-m1'/'admission'
    original=r.read_object(original_admission_path)
    r.publish_object(tmp_path/'old-admission',original)
    live=dict(reservations=[copy.deepcopy(old['actual_entry'])]);live_path=tmp_path/'live.json';live_path.write_text(json.dumps(live))
    snapshot=tmp_path/'original.json';snapshot.write_bytes(live_path.read_bytes());directory=tmp_path/'successors';directory.mkdir()
    old_map=dict(reservation_id='r-031',experiment='A3',phase='M1',subphase='masks',inventory_sha256=policy['original_upper_inventory_sha256'],
        original_reserved_gpu_hours=.75,actual_entry=copy.deepcopy(old['actual_entry']),reservation_lineage=old['reservation_lineage'])
    mapping=dict(kind='a3_root_ledger_mapping_v1',ledger_path=str(live_path),ledger_snapshot_path=str(snapshot),ledger_sha256=r.common.file_hash(snapshot),
        expected_entry_ids=['r-031'],entries=[old_map],original_admission_paths=[str(tmp_path/'old-admission')],
        original_admission_references={str(tmp_path/'old-admission'):r.object_reference(tmp_path/'old-admission')},
        storage_capacities={'host_ram':dict(pool='ram',available_bytes=10**9)},contingency_gpu_hours=5.25,max_age_seconds=900,
        generation=0,successor_directory=str(directory),refresh_wait_seconds=0)
    r.publish_object(tmp_path/'mapping',mapping)
    before=r.normalize_ledger(tmp_path/'mapping',identity=identity,injected=True)
    assert w._ledger(before,identity)['mask_retry_gpu_hours']==0
    assert w.validate_mask_replacement_admission(admission,before['entries'])['execution_authorized'] is False
    assert before['expected_entry_ids']==['r-031']  # No invented new actual entry to construct admission.
    new,admission=_n5_actual(w,policy,admission);new['actual_entry'].update(status='RUNNING',actual_seconds=None)
    live['reservations'].append(new['actual_entry']);live_path.write_text(json.dumps(live))
    r.publish_object(tmp_path/'new-admission',admission)
    second=tmp_path/'second.json';second.write_bytes(live_path.read_bytes())
    successor=copy.deepcopy(mapping);successor.update(generation=1,predecessor_reference=r.object_reference(tmp_path/'mapping'),
        ledger_snapshot_path=str(second),ledger_sha256=r.common.file_hash(second),expected_entry_ids=['r-031','r-new'])
    successor['entries'].append(dict(reservation_id='r-new',experiment='A3',phase='M1',subphase='masks',inventory_sha256='c'*64,
        original_reserved_gpu_hours=.75,actual_entry=new['actual_entry'],reservation_lineage=new['reservation_lineage']))
    successor['original_admission_paths'].append(str(tmp_path/'new-admission'))
    successor['original_admission_references'][str(tmp_path/'new-admission')]=r.object_reference(tmp_path/'new-admission')
    r.publish_object(directory/'mapping-000001',successor)
    ledger=r.normalize_ledger(tmp_path/'mapping',identity=identity,injected=True)
    assert w._ledger(ledger,identity)['mask_retry_gpu_hours']==.75
    inv=dict(identity=identity,inventory_sha256='c'*64,phase='M1',expected_keys=[],finish_reserve_seconds=1)
    r.publish_object(tmp_path/'upper',inv)
    lease_start=time.time()-1
    r.publish_object(tmp_path/'allocation',dict(kind='a3_injected_slurm_allocation_v1',injected=True,job_id='999999',cluster='delta',
        account='new-account',partition='gpuH200x8',gpus=1,state='RUNNING',start_time_unix=lease_start,
        end_time_unix=lease_start+2700,time_limit_seconds=2700))
    reservation=dict(kind='a3_root_execution_reservation_v1',identity=identity,inventory_sha256='c'*64,reservation_id='r-new',
        actual_entry={k:new['actual_entry'].get(k) for k in r.RESERVATION_FIELDS},admission_path=str(tmp_path/'new-admission'),
        admission_reference=r.object_reference(tmp_path/'new-admission'),admission_sha256=admission['admission_sha256'],
        upper_inventory_path=str(tmp_path/'upper'),minimum_shard_seconds=1,injected_allocation_path=str(tmp_path/'allocation'))
    r.publish_object(tmp_path/'reservation',reservation)
    call=lambda:r.validate_reservation(tmp_path/'reservation',ledger=ledger,inventory=inv,work_dir='/tmp/n5-replacement',injected=True,
        subphase='masks',subphase_limits={'M1':1.5,'M5':10},inventory_validator=lambda _:None)
    assert call()['execution_authorized'] is True  # Explicit software allocation fixture only.
    with pytest.raises(ValueError):r.validate_reservation(tmp_path/'reservation',ledger=ledger,inventory=inv,work_dir='/tmp/n5-replacement',
        injected=False,subphase='masks',subphase_limits={'M1':1.5,'M5':10},inventory_validator=lambda _:None)
