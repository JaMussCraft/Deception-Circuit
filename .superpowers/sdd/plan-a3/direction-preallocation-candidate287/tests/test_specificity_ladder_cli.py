"""Staging guards for the specificity ladder; no pretrained model required."""
import json
from pathlib import Path
import pytest
from component_analysis import ladder_pipeline as cli


def test_selection_requires_actual_provenance(tmp_path):
    with pytest.raises((ValueError, FileNotFoundError), match='selection|sample'):
        cli.selection_provenance(tmp_path)


def test_hash_join_refuses_stale_payload(tmp_path):
    p=tmp_path/'artifact.json'
    cli.write_artifact(p, {'bank': [1]})
    assert cli.read_artifact(p)['bank']==[1]
    raw=json.loads(p.read_text()); raw['payload']['bank']=[2]; p.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match='hash'):
        cli.read_artifact(p)


def test_artifacts_are_immutable(tmp_path):
    p=tmp_path/'artifact.json'; cli.write_artifact(p, {})
    with pytest.raises((ValueError,FileExistsError),match='exists'):
        cli.write_artifact(p,{})


def test_pilot_cannot_finalize():
    with pytest.raises(ValueError, match='pilot'):
        cli.validate_finalization({'pilot':True}, final=True)
    with pytest.raises(ValueError, match='injected'):
        cli.validate_finalization({'pilot':False,'injected':True}, final=True)


def test_incomplete_rows_refused():
    expected=[('far_v2','id','D','clean','far_full','zero',None)]
    with pytest.raises(ValueError,match='incomplete'):
        cli.validate_rows([],expected)


def test_role_layout_uses_exact_token_boundaries():
    class Tokens:
        def encode(self,text,add_special_tokens=False): return list(text.encode())
    prompt='<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\ns<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nu<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\na'
    result=cli.prompt_record(Tokens(),prompt)
    assert [x[0] for x in result['layout']['role_spans']]==['system','user','assistant']
    assert result['readout']==len(result['tokens'])-1


def test_prepare_dry_run_never_loads_model_or_writes(tmp_path,monkeypatch):
    called=[]
    monkeypatch.setattr(cli,'prepare',lambda args,tokenizer:called.append((args.dry_run,tokenizer)))
    tokenizer=object()
    args=['--stage','prepare','--tasks','far_v2','--commit','a'*40,'--dry-run']
    for name in ('artifact-root','data-root','user-control-root','work-dir','design','groups'):
        args+=['--'+name,str(tmp_path/name)]
    def forbidden(args): raise AssertionError('model loaded')
    assert cli.main(args,tokenizer=tokenizer,model_loader=forbidden)==0
    assert called==[(True,tokenizer)]
    assert list(tmp_path.iterdir())==[]


def test_utility_registry_refresh(tmp_path,monkeypatch):
    registry=tmp_path/'held_out.json'
    registry.write_text(json.dumps({'schema':1,'sets':[]}))
    monkeypatch.setattr(cli.common,'PRIMARY_REGISTRY',registry)
    monkeypatch.setattr(cli.common,'REPO',tmp_path)
    (tmp_path/'docs/research').mkdir(parents=True)
    local=tmp_path/'docs/research/held_out.json'
    local.write_text(registry.read_text())
    class Args: registry=[]
    rows={'ioi':[{'instance_id':'protected'}]}
    assert cli.utility_registries(Args(),rows)
    local.write_text(json.dumps({'schema':1,'sets':[{'task':'ioi','instance_ids':['protected']}]}))
    with pytest.raises(ValueError,match='protected registry id overlap'):
        cli.utility_registries(Args(),rows)


@pytest.mark.parametrize('domain',['source','bank','donors','assessment'])
def test_prepared_mutation_refused(tmp_path,monkeypatch,domain):
    from tests.test_ladder_design import pools
    from types import SimpleNamespace
    rows=pools(104)
    for c in rows:
        rows[c].append(dict(rows[c][0],instance_id='bank',split='train'))
    frozen=cli.design.freeze_design(rows,{'0','1'},mover_selection_ids=['1','0'])
    source=tmp_path/'source'; source.write_text('original')
    prepared=dict(kind='prepared',tasks=['far_v2'],rows={'far_v2':rows},designs={'far_v2':frozen},utility={},
                  model='model',model_revision='rev',tokenizer_revision='rev',commit='a'*40,
                  code_hashes={},source_hashes={str(source):cli.common.file_hash(source)},selection_hashes={})
    args=SimpleNamespace(tasks=['far_v2'],model='model',model_revision='rev',tokenizer_revision='rev',commit='a'*40)
    monkeypatch.setattr(cli,'code_hashes',lambda:{})
    monkeypatch.setattr(cli,'grader_registry',lambda:{})
    monkeypatch.setattr(cli,'registries',lambda *a:{})
    monkeypatch.setattr(cli,'utility_registries',lambda *a:{})
    cli.validate_prepared(args,prepared)
    if domain=='source': source.write_text('changed')
    elif domain=='bank': prepared['rows']['far_v2']['H'][-1]['streams']['clean']['tokens']=[9]
    elif domain=='donors': frozen['donors'][0]['covered_positions']=999
    else: frozen['assessment_ids'].pop()
    with pytest.raises(ValueError,match='stale'):
        cli.validate_prepared(args,prepared)


def test_expected_scope_does_not_trust_scored_row_counts():
    prepared=dict(tasks=['far_v2'],designs={'far_v2':{'assessment_ids':['a','b']}},
                  utility={'ioi':[dict(instance_id='i',condition='IOI')],'mmlu':[dict(instance_id='m',condition='MMLU')]})
    selected={'groups':{'far_v2':{'duplicate_group':False}}}
    keys=cli.expected_keys(prepared,selected)
    assert len(keys)==2*5*2*2*9+2*9
    assert len(keys)==len(set(keys))
    assert all(key[1]!='b' for key in cli.expected_keys(prepared,selected,limit=1))


def test_selection_ids_are_ordered_per_task_union_is_independent(tmp_path):
    for task,ids in zip(cli.TASKS,[['b','a'],['c'],['d']]):
        p=tmp_path/'outputs/_analyses/mechanism-analysis-p1/s1/U__leaf'/task/'sample.json'
        p.parent.mkdir(parents=True); p.write_text(json.dumps({'instance_ids':ids}))
    selected,hashes=cli.selection_provenance(tmp_path)
    assert selected['far_v2']==['b','a']
    assert set().union(*map(set,selected.values()))==set('abcd')
    assert len(hashes)==3


def test_select_uses_only_original_h_selection_and_bank(monkeypatch):
    import torch
    from types import SimpleNamespace
    from component_analysis import specificity_ladder as runner,dla,hooks
    monkeypatch.setattr(hooks,'device_and_dtype',lambda model:('cpu',torch.float32))
    rows=[]
    for rid,split in [('selection','test'),('assessment','test'),('bank','train')]:
        streams={s:dict(tokens=[1,2],readout=1,layout={'role_spans':[['text',0,2]],'content_spans':[['text',0,2]]},
                        expected_token=3,honest_token=3,opposite_token=4) for s in cli.design.STREAMS}
        rows.append(dict(instance_id=rid,condition='H',source_condition='H',split=split,source_hash='h',task='far_v2',streams=streams))
    prepared=dict(designs={'far_v2':dict(mover_selection_ids=['selection'],bank_ids=['bank'])},rows={'far_v2':{'H':rows}},
                  recorded_groups={'far':dict(members=[['head',0,0],['mlp',0,0]])})
    captured=[]
    def capture(model,batch,keys):
        assert batch.ids==['selection'] and batch.condition=='H'
        captured.append(batch.stream)
        return object(),None
    def bank(model,batches,keys):
        assert {(b.ids[0],b.stream) for b in batches}=={('bank','clean'),('bank','corrupt')}
        return dict(values={tuple(k):torch.zeros(2) for k in keys},provenance={'source_ids':['bank']})
    monkeypatch.setattr(runner,'_capture',capture)
    monkeypatch.setattr(runner,'collect_h_mean_bank',bank)
    monkeypatch.setattr(dla,'component_logit_difference',lambda *a,**k:torch.ones((1,1)))
    out=cli.select(SimpleNamespace(tasks=['far_v2'],batch_size=2,injected=True,commit='a'*40,model='fixture',model_revision='revision',tokenizer_revision='revision'),prepared,object())
    assert captured==['clean','corrupt']
    assert out['groups']['far_v2']['minus']==[['mlp',0,0]]
    assert out['groups']['far_v2']['screen']['selection_ids']==['selection']
    evidence=out['groups']['far_v2']['selection_evidence']
    assert evidence['head_keys']==[['head',0,0]]
    assert evidence['selection_ids']==['selection']
    assert evidence['clean_dla']==[[1.]] and evidence['corrupt_dla']==[[1.]]
    reconstructed=cli.design.choose_mover_candidates(
        [tuple(k) for k in out['groups']['far_v2']['full']],
        evidence['clean_dla'],evidence['corrupt_dla'],evidence['selection_ids'])
    assert reconstructed==out['groups']['far_v2']['screen']


def test_canonical_runner_preserves_injection_signature(monkeypatch):
    from component_analysis import specificity_ladder as runner
    marker=object(); loader=object(); calls=[]
    monkeypatch.setattr(cli,'main',lambda argv=None,tokenizer=None,model_loader=None:calls.append((argv,tokenizer,model_loader)) or 19)
    assert runner.main(['--stage','prepare'],tokenizer=marker,model_loader=loader)==19
    assert calls==[(['--stage','prepare'],marker,loader)]


def test_positive_control_coverage_is_exact():
    prepared=dict(tasks=['far_v2'],designs={'far_v2':{'assessment_ids':['a']}},utility={'ioi':[],'mmlu':[]})
    controls=[dict(zip(('mechanism_task','task','instance_id','condition','stream'),key),valid=True) for key in cli.positive_keys(prepared)]
    cli.validate_positive_controls(controls,prepared)
    with pytest.raises(ValueError,match='incomplete'):
        cli.validate_positive_controls(controls[:-1],prepared)


def test_tiny_native_select_to_score_pipeline(tmp_path):
    import copy
    import torch
    import nnsight
    if nnsight.__version__!='0.7.0': pytest.skip('pinned nnsight 0.7.0 required')
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    from tests.helpers import tiny_config
    from tests.test_ladder_design import row
    from types import SimpleNamespace
    from component_analysis import ladder_tasks
    torch.manual_seed(41)
    model=NNsight(LlamaForCausalLM(tiny_config(attn_implementation='sdpa')).eval())
    source={}
    for index,condition in enumerate(cli.design.CONDITIONS):
        source[condition]=[]
        for rid,split in [('selection','test'),('assessment','test'),('bank','train')]:
            r=row(rid,condition,split); r.update(task='far_v2',source_hash='fixture',source_condition=condition)
            for stream,s in r['streams'].items():
                s.update(tokens=[1,2+index,3,4] if stream=='clean' else [1,3+index,2,4],readout=3,
                         honest_token=13 if stream=='clean' else 11,opposite_token=11 if stream=='clean' else 13)
                s['expected_token']=s['opposite_token'] if condition in ('D','I') else s['honest_token']
            source[condition].append(r)
    frozen=cli.design.freeze_design(source,{'selection'},mover_selection_ids=['selection'],n=1)
    ioi=copy.deepcopy(source['H'][1]); ioi.update(instance_id='ioi',task='ioi',condition='IOI',source_condition='IOI',source_id='ioi',honest_token=13,opposite_token=11,expected_token=13)
    mmlu=[]
    for index in range(2):
        r=copy.deepcopy(ioi); r.update(instance_id='mmlu'+str(index),task='mmlu',condition='MMLU',source_id='mmlu'+str(index),question_hash='q'+str(index),gold_letter='AB'[index],choice_tokens=[11,12,13,14])
        r['streams']={'clean':r['streams']['clean']}; r['streams']['clean']['tokens'][1]+=index
        mmlu.append(r)
    prepared=dict(tasks=['far_v2'],source_hashes={},selection_hashes={},designs={'far_v2':frozen},rows={'far_v2':source},recorded_groups={'far':dict(members=[['head',0,0],['mlp',0,0]])},
                  utility=dict(ioi=[ioi],mmlu=mmlu,ioi_maps=ladder_tasks.ioi_item_swap_maps([ioi]),mmlu_maps=ladder_tasks.mmlu_calibration_maps(mmlu)))
    args=SimpleNamespace(tasks=['far_v2'],batch_size=1,injected=True,limit=1,commit='a'*40,model='fixture',model_revision='revision',tokenizer_revision='revision')
    prepared.update({field:getattr(args,field) for field in ('commit','model','model_revision','tokenizer_revision')},code_hashes=cli.code_hashes(),injected=True)
    selected=cli.select(args,prepared,model)
    group=selected['groups']['far_v2']; evidence=group['selection_evidence']
    reconstructed=cli.design.choose_mover_candidates([tuple(k) for k in group['full']],evidence['clean_dla'],evidence['corrupt_dla'],evidence['selection_ids'])
    assert reconstructed==group['screen']
    execution=selected['execution_provenance']
    assert execution['device']=='cpu' and execution['dtype']=='torch.float32'
    assert execution['selection_compute_seconds']>=0 and execution['peak_allocated_memory_bytes'] is None
    assert execution['gpu_name'] is None and execution['peak_reserved_memory_bytes'] is None
    assert execution['commit']==args.commit and execution['model_revision']==args.model_revision
    args.groups=str(tmp_path/'groups.json')
    cli.write_selection(args,prepared,selected)
    manifest=cli.common.read_json(tmp_path/'selection_run_manifest.json')
    assert manifest['selection_file_sha256']==cli.common.file_hash(args.groups)
    assert manifest['design_sha256']==cli.design._hash(prepared)
    assert cli.read_selection(args,prepared)==selected
    assert manifest['raw_dla_sha256']==cli.design._hash({'far_v2':evidence})
    scored=cli.score(args,prepared,selected,model)
    assert scored['pilot'] and scored['injected']
    execution=scored['execution_provenance']
    assert execution['device']=='cpu' and execution['dtype']=='torch.float32'
    assert execution['gpu_name'] is None and execution['peak_allocated_memory_bytes'] is None and execution['peak_reserved_memory_bytes'] is None
    assert execution['scoring_compute_seconds']>=0
    assert scored['counts']['rows']==scored['counts']['expected']==len(cli.expected_keys(prepared,selected,1))
    assert scored['counts']['positive_controls']==12
    assert any(r['operation']=='h_mean' and r['supported'] for r in scored['rows'])


def test_changed_grader_source_refused_even_with_unchanged_registry(tmp_path,monkeypatch):
    from evaluation import grader_hash
    path=tmp_path/'docs/research/directions.json'; path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'directions':[{'id':'specificity-ladder','frozen_grader_sha256':cli.GRADER}]}))
    monkeypatch.setattr(cli,'REPO',tmp_path); monkeypatch.setattr(cli,'PRIMARY',tmp_path)
    monkeypatch.setattr(grader_hash,'grader_sha256',lambda root:cli.GRADER)
    cli.grader_registry()
    monkeypatch.setattr(grader_hash,'grader_sha256',lambda root:'changed')
    with pytest.raises(ValueError,match='changed grader source'):
        cli.grader_registry()


def test_summary_preserves_sdr_descriptive_qualification():
    source=dict(full=[['mlp',0,0]],minus=[['mlp',0,0]],duplicate_group=True)
    selected={'groups':{task:dict(source,descriptive=task=='sdr_v2') for task in cli.TASKS}}
    summary={'cells':[dict(task=task,status='strong',strong=True,point_pass=True) for task in cli.TASKS]}
    qualified=cli.qualify_summary(summary,selected)
    sdr=qualified['cells'][1]
    assert sdr['descriptive'] and sdr['status']=='descriptive_only' and not sdr['strong']
    assert sdr['numerical_status']=='strong' and sdr['numerical_strong'] and sdr['point_pass']
    assert qualified['cells'][0]['strong'] and not qualified['cells'][0]['descriptive']
    assert summary['cells'][1]['strong']  # Pure qualification preserves input.


def test_bank_provenance_reference_roundtrip_and_mutation_refusal(tmp_path):
    import copy
    bank=dict(values=[dict(key=['mlp',0,0],value=[1.,2.])],
              provenance=dict(source_condition='H',source_ids=['bank1'],splits=['train'],n_tokens=8,provenance=[{'full':'source row'}]))
    selected=dict(groups={'far_v2':{}},banks={'far_v2':bank})
    path=tmp_path/'groups.json'; cli.write_artifact(path,selected)
    rows=[dict(group='far_v2_full',mean_bank_provenance=copy.deepcopy(bank['provenance']))]
    cli.compact_bank_provenance(rows,selected,path)
    reference=rows[0]['mean_bank_provenance']
    restored=cli.resolve_bank_reference(json.loads(json.dumps(reference)))
    assert cli.design._hash(restored)==cli.design._hash(bank['provenance'])
    assert 'provenance' not in reference and reference['n_instances']==1 and reference['n_tokens']==8
    raw=json.loads(path.read_text()); raw['payload']['banks']['far_v2']['provenance']['n_tokens']=99
    raw['sha256']=cli.design._hash(raw['payload']); path.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='bank artifact reference hash'):
        cli.resolve_bank_reference(reference)


def test_selection_manifest_links_exact_artifact_and_raw_evidence(tmp_path):
    from types import SimpleNamespace
    group=dict(full=[['head',0,0]],minus=[],selection_evidence=dict(head_keys=[['head',0,0]],selection_ids=['ordered'],clean_dla=[[1.]],corrupt_dla=[[2.]]))
    selected=dict(kind='selected',design_sha256='design',groups={'far_v2':group},banks={},
                  group_sha256='group',bank_sha256='bank',execution_provenance=dict(device='cpu',dtype='torch.float32',selection_compute_seconds=.1),injected=True)
    args=SimpleNamespace(groups=str(tmp_path/'groups.json'),commit='a'*40,model='fixture',model_revision='revision',tokenizer_revision='revision')
    prepared=dict(source_hashes={'input':'sha'},selection_hashes={'selection':'sha'})
    cli.write_selection(args,prepared,selected)
    manifest=cli.common.read_json(tmp_path/'selection_run_manifest.json')
    assert manifest['selection_artifact_sha256']==cli.design._hash(cli.read_artifact(args.groups))
    assert manifest['selection_file_sha256']==cli.common.file_hash(args.groups)
    assert manifest['selection_artifact']==str(Path(args.groups).resolve())
    assert manifest['raw_dla_sha256']==cli.design._hash({'far_v2':group['selection_evidence']})
    assert manifest['execution']==selected['execution_provenance']
    assert manifest['commit']==args.commit and manifest['tokenizer_revision']=='revision'
    with pytest.raises(ValueError,match='exists'):
        cli.write_selection(args,prepared,selected)


def test_selection_runtime_records_only_safe_allowlisted_labels(monkeypatch):
    for name in ('SLURM_JOB_ID','SLURM_CLUSTER_NAME','DC_CLUSTER_NAME','DC_CLUSTER'):
        monkeypatch.delenv(name,raising=False)
    monkeypatch.setenv('SLURM_JOB_ID','12345_2'); monkeypatch.setenv('DC_CLUSTER','delta')
    monkeypatch.setenv('UNRELATED_SECRET','never-record-this')
    assert cli.selection_runtime_identity()==dict(slurm_job_id='12345_2',cluster='delta',cluster_source='DC_CLUSTER')
    monkeypatch.setenv('SLURM_JOB_ID','bad\nvalue'); monkeypatch.setenv('DC_CLUSTER','bad value')
    assert cli.selection_runtime_identity()==dict(slurm_job_id=None,cluster=None,cluster_source=None)


def test_existing_selection_manifest_refused_before_model_load(tmp_path):
    (tmp_path/'selection_run_manifest.json').write_text('{}')
    args=['--stage','select','--tasks','far_v2','--commit','a'*40]
    for name in ('artifact-root','data-root','user-control-root','work-dir','design'):
        args+=['--'+name,str(tmp_path/name)]
    args+=['--groups',str(tmp_path/'groups.json')]
    def forbidden(args): raise AssertionError('model must not load')
    with pytest.raises(ValueError,match='selection_run_manifest.json'):
        cli.main(args,model_loader=forbidden)


def test_execution_resources_cuda_branch_is_mocked_and_scoped(monkeypatch):
    import torch
    from component_analysis import hooks
    calls=[]; device=torch.device('cuda:3')
    monkeypatch.setattr(hooks,'device_and_dtype',lambda model:(device,torch.bfloat16))
    monkeypatch.setattr(torch.cuda,'synchronize',lambda value:calls.append(('sync',value)))
    monkeypatch.setattr(torch.cuda,'reset_peak_memory_stats',lambda value:calls.append(('reset',value)))
    monkeypatch.setattr(torch.cuda,'get_device_name',lambda value:'mock H200')
    monkeypatch.setattr(torch.cuda,'max_memory_allocated',lambda value:8192)
    monkeypatch.setattr(torch.cuda,'max_memory_reserved',lambda value:16384)
    clock=iter([10.,12.5]); monkeypatch.setattr(cli.time,'perf_counter',lambda:next(clock))
    state=cli.start_execution(object())
    result=cli.finish_execution(state,'scoring')
    assert calls==[('sync',device),('reset',device),('sync',device)]
    assert result['gpu_name']=='mock H200' and result['device']=='cuda:3'
    assert result['peak_allocated_memory_bytes']==8192 and result['peak_reserved_memory_bytes']==16384
    assert result['scoring_compute_seconds']==2.5
    assert result['memory_scope']=='scoring compute after model load; includes resident model'


def test_execution_resources_cpu_never_reads_cuda(monkeypatch):
    import torch
    from component_analysis import hooks
    monkeypatch.setattr(hooks,'device_and_dtype',lambda model:(torch.device('cpu'),torch.float32))
    def forbidden(*args): raise AssertionError('CPU instrumentation touched CUDA')
    for name in ('synchronize','reset_peak_memory_stats','get_device_name','max_memory_allocated','max_memory_reserved'):
        monkeypatch.setattr(torch.cuda,name,forbidden)
    result=cli.finish_execution(cli.start_execution(object()),'selection')
    assert result['gpu_name'] is None
    assert result['peak_allocated_memory_bytes'] is None and result['peak_reserved_memory_bytes'] is None
    assert result['selection_compute_seconds']>=0


@pytest.mark.parametrize('stage',['selection','scoring'])
def test_model_load_and_stage_timing_is_recorded(stage,monkeypatch):
    from types import SimpleNamespace
    args=SimpleNamespace(); model=object(); calls=[]
    def loader(received):
        assert received is args; calls.append('load'); return model
    def compute(received):
        assert received is model; calls.append('compute')
        return dict(execution_provenance={stage+'_compute_seconds':3.})
    clock=iter([10.,12.,17.]); monkeypatch.setattr(cli.time,'perf_counter',lambda:next(clock))
    result=cli.timed_model_stage(args,loader,compute,stage)
    assert calls==['load','compute']
    assert result['execution_provenance']=={stage+'_compute_seconds':3.,'model_load_seconds':2.,stage+'_stage_seconds':7.,'stage_time_scope':'model load plus '+stage+' compute; excludes artifact publication'}


@pytest.fixture
def completed_selection(tmp_path,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(cli,'code_hashes',lambda:{})
    identity=dict(commit='a'*40,model='fixture',model_revision='revision',tokenizer_revision='revision')
    args=SimpleNamespace(**identity,tasks=['far_v2'],groups=str(tmp_path/'groups.json'),design=str(tmp_path/'design.json'))
    evidence=dict(head_keys=[['head',0,0]],selection_ids=['selection'],clean_dla=[[1.]],corrupt_dla=[[2.]])
    prepared=dict(kind='prepared',tasks=args.tasks,injected=True,**identity,code_hashes={},source_hashes={'source':'sha'},selection_hashes={'selection':'sha'},
                  designs={'far_v2':dict(mover_selection_ids=['selection'],bank_ids=['bank'])},
                  recorded_groups={'far':dict(members=[['head',0,0]])},rows={},utility={})
    group=dict(full=[['head',0,0]],minus=[],selection_evidence=evidence,descriptive=False,duplicate_group=False)
    banks={'far_v2':dict(values=[dict(key=['head',0,0],value=[0.])],provenance=dict(source_ids=['bank'],source_condition='H',splits=['train'],n_tokens=2))}
    selected=dict(kind='selected',design_sha256=cli.design._hash(prepared),groups={'far_v2':group},banks=banks,
                  group_sha256=cli.design._hash({'far_v2':group}),bank_sha256=cli.design._hash(banks),
                  execution_provenance=dict(**identity,device='cpu',dtype='torch.float32',selection_compute_seconds=.1),injected=True)
    cli.write_artifact(args.design,prepared); cli.write_selection(args,prepared,selected)
    monkeypatch.setattr(cli,'validate_prepared',lambda *a:None)
    monkeypatch.setattr(cli,'registries',lambda *a:{})
    monkeypatch.setattr(cli,'utility_registries',lambda *a:{})
    monkeypatch.setattr(cli,'grader_registry',lambda:{})
    original_read=cli.read_artifact
    def guarded_read(path):
        if Path(path).name=='score.json': raise AssertionError('SUMMARY_REACHED')
        return original_read(path)
    monkeypatch.setattr(cli,'read_artifact',guarded_read)
    argv=['--tasks','far_v2','--commit',args.commit,'--model',args.model,'--model-revision',args.model_revision,'--tokenizer-revision',args.tokenizer_revision]
    for name in ('artifact-root','data-root','user-control-root','work-dir'):
        argv+=['--'+name,str(tmp_path/name)]
    argv+=['--design',args.design,'--groups',args.groups]
    return args,prepared,selected,argv


@pytest.mark.parametrize('stage',['score','summarize'])
@pytest.mark.parametrize('damage',['missing','malformed','empty','partial','schema','selection_artifact','selection_artifact_sha256','selection_file_sha256',
                                   'selected_bytes','selected_payload','design_sha256','raw_dla_sha256','group_sha256','bank_sha256','counts',
                                   'commit','model','model_revision','tokenizer_revision','source_hashes','selection_source_hashes','code_hashes','execution','injected'])
def test_main_refuses_incomplete_selection_before_any_consumer(completed_selection,stage,damage):
    args,prepared,selected,argv=completed_selection
    path=cli.selection_manifest_path(args.groups)
    raw=json.loads(path.read_text())
    if damage=='missing': path.unlink()
    elif damage=='malformed': path.write_text('{partial')
    elif damage=='empty': path.write_text('{}')
    elif damage=='partial': path.write_text(json.dumps({'schema_version':1,'kind':'specificity_ladder_selection'}))
    elif damage=='selected_bytes': Path(args.groups).write_text(Path(args.groups).read_text()+' ')
    elif damage=='selected_payload':
        envelope=json.loads(Path(args.groups).read_text()); envelope['payload']['execution_provenance']['dtype']='changed'
        envelope['sha256']=cli.design._hash(envelope['payload']); Path(args.groups).write_text(json.dumps(envelope))
    else:
        if damage=='schema': raw['schema_version']=True
        elif damage=='counts': raw['counts']['far_v2']['bank_instances']=999
        elif damage=='execution': raw['execution']['dtype']='changed'
        elif damage=='injected': raw['injected']=False
        else: raw[damage]={'changed':'sha'} if isinstance(raw[damage],dict) else 'changed'
        path.write_text(json.dumps(raw))
    def forbidden(args): raise AssertionError('MODEL_LOADER_REACHED')
    with pytest.raises(ValueError,match='selection'):
        cli.main(['--stage',stage]+argv,model_loader=forbidden)


@pytest.mark.parametrize('stage',['score','summarize'])
def test_main_accepts_completed_selection_before_consumer(completed_selection,stage):
    args,prepared,selected,argv=completed_selection
    assert cli.read_selection(args,prepared)==selected
    def reached(args): raise AssertionError('MODEL_LOADER_REACHED')
    with pytest.raises(AssertionError,match='MODEL_LOADER_REACHED' if stage=='score' else 'SUMMARY_REACHED'):
        cli.main(['--stage',stage]+argv,model_loader=reached)


@pytest.mark.parametrize('stage',['score','summarize'])
def test_dry_run_rejects_incomplete_selection_before_tokenization(completed_selection,stage,monkeypatch):
    args,prepared,selected,argv=completed_selection
    cli.selection_manifest_path(args.groups).unlink()
    def forbidden(*args): raise AssertionError('TOKENIZER_OR_MODEL_REACHED')
    monkeypatch.setattr(cli.common,'load_tokenizer',forbidden)
    with pytest.raises(ValueError,match='missing selection completion manifest'):
        cli.main(['--stage',stage,'--dry-run']+argv,model_loader=forbidden)
