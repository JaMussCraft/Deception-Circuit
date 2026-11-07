import copy
import hashlib
import pytest
import torch
from component_analysis import selective_v6_followup as f
from component_analysis import hooks


def test_unique_assignment_exact_hash_order_and_scenario_exclusion():
    recipients = [dict(source_id='r', truth_label=1, donor_source_id='orig')]
    donors = [dict(source_id=str(i), truth_label=i % 2 + 1, scenario_key=str(i)) for i in range(12)]
    got = f.assign_donors(recipients, donors, {'0'})
    for arm, label in [('agree', 1), ('disagree', 2)]:
        eligible = [d for d in donors if d['truth_label'] == label and d['scenario_key'] != '0']
        expected = min(eligible, key=lambda d:(hashlib.sha256(f"v6-followup-donor|20261026|{arm}|r|{d['source_id']}".encode()).hexdigest(),d['source_id']))
        assert got['r'][arm] == expected
    assert len({d['source_id'] for d in got['r'].values()}) == 2
    with pytest.raises(ValueError, match='insufficient'):
        f.assign_donors(recipients, donors[:1], set())


def test_truth_label_is_construction_ordinal_not_requested_false():
    row = dict(item_1='a', item_2='b', target='b')
    assert f.truth_label(row) == 2
    with pytest.raises(ValueError):
        f.truth_label(dict(row, target='c'))


def test_synthetic_sender_changes_only_recipient_final_and_never_mutates():
    key=('head',0,0)
    clean={key:torch.arange(12.).reshape(2,3,2)}
    donor=torch.arange(20.,40.).reshape(2,5,2)
    cm=torch.tensor([[0,1,1],[1,1,0]])
    dm=torch.tensor([[1,1,0,0,0],[0,1,1,1,1]])
    before=clean[key].clone()
    got=f.synthetic_sender(clean, {key:donor}, dm, cm, key)
    assert set(got)=={key}
    expected=before.clone(); expected[0,2]=donor[0,1];expected[1,1]=donor[1,4]
    assert torch.equal(got[key],expected)
    assert torch.equal(clean[key],before)


def test_tiny_actual_composition_and_shams():
    nnsight=pytest.importorskip('nnsight')
    if nnsight.__version__ != '0.7.0': pytest.skip('pinned nnsight required')
    from nnsight import NNsight
    from scripts.smoke_nnsight import build_tiny
    model=NNsight(build_tiny().eval())
    ids=torch.tensor([[1,2,3],[3,4,0]]);mask=torch.tensor([[1,1,1],[1,1,0]])
    dids=torch.tensor([[4,5,0,0],[1,3,4,5]]);dm=torch.tensor([[1,1,0,0],[1,1,1,1]])
    sender=('head',0,0);receivers=(('q',1,0),('q',1,1))
    clean=hooks.capture_forward(model,ids,mask,components=hooks.all_component_keys(model)+[f.pp.READOUT_KEY],positions=f.core.last_nonpad(mask))
    donor=hooks.capture_forward(model,dids,dm,components=[sender],positions=f.core.last_nonpad(dm))
    streams=f.make_streams(model,ids,mask,clean,donor,dm,sender,[1,1],[2,2])
    assert set(streams.clean_outputs)==set(hooks.all_component_keys(model))
    results,controls=f.path_states(model,streams,clean,receivers,sender)
    assert set(results)=={'total_sender_13','path_Q27','path_Q26'}
    assert all(v for k,v in controls.items() if k.endswith('_exact'))
    assert all(torch.isfinite(pair[0]).all() for pair in results.values())


def test_fixed_modes_and_receipt_binding(tmp_path):
    cases=[dict(case_id=str(i)) for i in range(64)]
    pack=dict(cases=cases,smoke={'case_ids':[str(i) for i in range(16)]})
    assert len(f.selected_cases(pack,'smoke'))==16
    assert len(f.selected_cases(pack,'followup'))==64
    with pytest.raises(ValueError):f.selected_cases(pack,'other')
    receipt=dict(review_status='approved',mode='smoke',pack_sha256='p',selection_sha256='s',
                 runner_sha256='r',code_hashes={'h':'x'},output_dir=str(tmp_path),
                 reserved_gpu_hours=.25,remaining_gpu_hours_before=2.4,reservation_id='once')
    f.validate_receipt(receipt,'p','s','r',{'h':'x'},'smoke',tmp_path)
    for key,val in [('selection_sha256','wrong'),('reserved_gpu_hours',.26),('remaining_gpu_hours_before',float('nan')),('review_status','pending')]:
        with pytest.raises(ValueError):f.validate_receipt(dict(receipt,**{key:val}),'p','s','r',{'h':'x'},'smoke',tmp_path)


def test_all_ten_states_tiny_model_truth_metrics_and_rescue(monkeypatch):
    nnsight=pytest.importorskip('nnsight')
    if nnsight.__version__ != '0.7.0': pytest.skip('pinned nnsight required')
    from nnsight import NNsight
    from scripts.smoke_nnsight import build_tiny
    model=NNsight(build_tiny().eval())
    monkeypatch.setattr(f,'SENDER',('head',0,0));monkeypatch.setattr(f,'RESCUE',('head',1,1))
    monkeypatch.setattr(f,'RECEIVERS',(('q',1,1),('q',1,0)))
    donor=dict(source_id='d',token_ids=[1,4],truthful_id=1,alternate_answer_id=2)
    case=dict(case_id='r:H',source_id='r',scenario_key='s',variant='H',stratum={},recipient_token_ids=[1,2,3],
              donor_token_ids=[2,4],construction={},donor_source_id='orig',requested_target_id=1,alternate_answer_id=2,truthful_id=1)
    pack=dict(original_donors={'orig':donor},pad_token_id=0,masks={'new30':[[0,0],[1,1]]},pairs={'r':{'agree':donor,'disagree':dict(donor,source_id='d2')}})
    rows,controls,capability=f.score_batch(model,pack,[case],device='cpu')
    assert [r['condition'] for r in rows]==list(f.STATES)
    by={r['condition']:r for r in rows}
    assert by['self_rescue_17']['metrics']==by['original_New30']['metrics']
    assert len(capability)==3
    assert all(r['metrics']['truth_oriented_margin']==r['metrics']['requested_margin'] for r in rows)


def test_pack_reconstruction_allows_only_frozen_status(tmp_path,monkeypatch):
    pack=dict(status='candidate_not_frozen',sources={},prepare_inputs={'x':'y'},payload=[1])
    monkeypatch.setattr(f,'prepare',lambda **kwargs:dict(status='candidate_not_frozen',sources={},payload=[1]))
    path=tmp_path/'pack.json';import json
    path.write_text(json.dumps(pack))
    assert f.load_pack(path)['payload']==[1]
    path.write_text(json.dumps(dict(pack,status='frozen')))
    assert f.load_pack(path)['status']=='frozen'
    path.write_text(json.dumps(dict(pack,payload=[2])))
    with pytest.raises(ValueError):f.load_pack(path)
