import json
import pytest
import torch
from component_analysis import selective_v7 as v
from component_analysis import hooks


def test_mapping_mixed_padding_and_rows():
    dm=torch.tensor([[0,1,1,0],[1,1,1,1]])
    rm=torch.tensor([[1,1,1,0],[0,1,1,0]])
    bank={('head',0,0):torch.arange(8.).reshape(2,4,1)}
    rep=v.aligned_replacements(bank,dm,rm)[('head',0,0)]
    initial=torch.full((2,4,1),-1.)
    expected=initial.clone(); expected[0,1,0]=1;expected[0,2,0]=2;expected[1,1,0]=6;expected[1,2,0]=7
    assert torch.equal(hooks._write(initial,rep),expected)
    assert rep.positions.tolist()==[[False,True,True,False],[False,True,True,False]]
    final=v.replacements(bank,dm,rm,'final')[('head',0,0)]
    old=v.core.final_replacements(bank,dm,rm)[('head',0,0)]
    assert torch.equal(hooks._write(initial,final),hooks._write(initial,old))
    own={('head',0,0):torch.arange(8.).reshape(2,4,1)+100}
    replay=v.self_replacements(own,{('head',0,0):rep})[('head',0,0)]
    assert torch.equal(hooks._write(own[('head',0,0)],replay),own[('head',0,0)])


def test_receipt_and_one_use(tmp_path):
    p=dict(manifest_sha256='m',selection_sha256='s',runner_sha256='r',code_hashes={'x':'h'},batch_size=4)
    receipt=dict(p,review_status='approved',mode='smoke',output_dir=str(tmp_path),reservation_id='one',reserved_gpu_hours=1/6,remaining_gpu_hours_before=1.9,gpu_type='A40',gpu_count=1,max_wall_seconds=600,wrapper_path=str(tmp_path/'wrapper'),wrapper_sha256='bad',source_commit='c')
    (tmp_path/'wrapper').write_text('wrapper')
    receipt['wrapper_sha256']=v.core.sha256(tmp_path/'wrapper')
    v.validate_receipt(receipt,p,'smoke',tmp_path)
    for key,value in [('selection_sha256','bad'),('batch_size',8),('max_wall_seconds',601),('gpu_type','A100'),('remaining_gpu_hours_before',float('nan')),('wrapper_sha256','bad')]:
        with pytest.raises(ValueError):v.validate_receipt(dict(receipt,**{key:value}),p,'smoke',tmp_path)
    path=tmp_path/'receipt';path.write_text(json.dumps(receipt))
    v.core.claim_receipt(path,'hash')
    with pytest.raises(FileExistsError):v.core.claim_receipt(path,'hash')


def test_tiny_real_hook_write_self_and_full_logits():
    nnsight=pytest.importorskip('nnsight')
    if nnsight.__version__!='0.7.0':pytest.skip('pinned nnsight required')
    from nnsight import NNsight
    from scripts.smoke_nnsight import build_tiny
    model=NNsight(build_tiny().eval())
    ids=torch.tensor([[1,2,3],[3,4,0]]);mask=torch.tensor([[1,1,1],[1,1,0]])
    di=torch.tensor([[4,5,0,0],[1,3,4,5]]);dm=torch.tensor([[1,1,0,0],[1,1,1,1]])
    keys=[('head',0,0),('head',1,1)]
    clean,base,proof=v.core.identity_controls(model,ids,mask,keys)
    donor=hooks.capture_forward(model,di,dm,components=keys,positions=v.core.last_nonpad(dm))
    replacement=v.aligned_replacements(donor.outputs,dm,mask)
    proofs=v.control_proofs(model,ids,mask,clean,base,replacement,clean.outputs)
    assert all(value for name,value in proofs.items() if name.endswith('_exact'))
    assert proofs['write_isolation_exact']


def test_frozen_prepare_rejects_case_source_and_support_drift(tmp_path):
    from pathlib import Path
    source=Path('/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v7/selection.frozen-001.json')
    selection=json.loads(source.read_text())
    def check(changed,match):
        path=tmp_path/'selection.json';path.write_text(json.dumps(changed))
        with pytest.raises(ValueError,match=match):v.prepare(selection['manifest_path'],path)
    check(dict(selection,case_ids=selection['case_ids'][::-1]),'case coverage')
    check(dict(selection,manifest_sha256='bad'),'manifest binding')
    check(dict(selection,masks=dict(selection['masks'],release17=[])),'support mismatch')
    check(dict(selection,smoke_case_ids=selection['smoke_case_ids'][:-1]),'smoke coverage')
    check(dict(selection,design_sha256='bad'),'design binding')


def test_all_seven_states_and_original_donor_capability_tiny():
    nnsight=pytest.importorskip('nnsight')
    if nnsight.__version__!='0.7.0':pytest.skip('pinned nnsight required')
    from nnsight import NNsight
    from scripts.smoke_nnsight import build_tiny
    model=NNsight(build_tiny().eval())
    case=dict(case_id='r:H',source_id='r',scenario_key='s',variant='H',stratum={},recipient_token_ids=[1,2,3],donor_token_ids=[2,4],donor_source_id='d',requested_target_id=1,alternate_answer_id=2,truthful_id=1,donor_requested_target_id=4,donor_alternate_answer_id=3)
    selection=dict(masks={'new30':[[0,0],[1,1]],'single17':[[1,1]],'release17':[[0,0]]})
    rows,proof,donors=v.score_batch(model,dict(pad_token_id=0),selection,[case],device='cpu',smoke=True)
    assert [r['condition'] for r in rows]==list(v.STATES)
    assert set(proof['conditions'])==set(v.STATES[1:])
    assert donors[0]['truthful_id']==4
    assert all(r['metrics']['truth_oriented_margin']==r['metrics']['requested_margin'] for r in rows)
    assert all(r['native_truth_oriented_margin']==r['native_requested_margin'] for r in rows)
