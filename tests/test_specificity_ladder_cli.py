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
    from component_analysis import specificity_ladder as runner,dla
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
    out=cli.select(SimpleNamespace(tasks=['far_v2'],batch_size=2,injected=True),prepared,object())
    assert captured==['clean','corrupt']
    assert out['groups']['far_v2']['minus']==[['mlp',0,0]]
    assert out['groups']['far_v2']['screen']['selection_ids']==['selection']


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


def test_tiny_native_select_to_score_pipeline():
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
    prepared=dict(tasks=['far_v2'],designs={'far_v2':frozen},rows={'far_v2':source},recorded_groups={'far':dict(members=[['head',0,0],['mlp',0,0]])},
                  utility=dict(ioi=[ioi],mmlu=mmlu,ioi_maps=ladder_tasks.ioi_item_swap_maps([ioi]),mmlu_maps=ladder_tasks.mmlu_calibration_maps(mmlu)))
    args=SimpleNamespace(tasks=['far_v2'],batch_size=1,injected=True,limit=1)
    selected=cli.select(args,prepared,model)
    scored=cli.score(args,prepared,selected,model)
    assert scored['pilot'] and scored['injected']
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
