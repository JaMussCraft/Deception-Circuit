import copy
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from component_analysis import a3_direction_workload as w, a3_direction_runtime as r, a3_directions as d
from tests.test_a3_direction_workload import inventory, receipts, packing_evidence, ledger

@pytest.fixture(scope='module')
def proof_case():
    inv=inventory()
    m=next(x for x in receipts(inv)[0]['measurements'] if x.get('packing_id') and x['axis_scope'])
    evidence=packing_evidence(m)
    m=copy.deepcopy(m)
    for axis,spec in zip(m['axis_scope'],next(iter(evidence['runner_receipt']['scope']['batches'].values()))):
        axis['axis_sha256']=spec['axis_sha256']
    return m,evidence,w._validate_packing_proof(evidence,m)

@pytest.mark.parametrize('field',['model','source_sha256','physical_batch_size','axis_tile_size','padded_width','dtype','backend'])
def test_index_matches_full_validator_profile_rejection(proof_case,field):
    m,evidence,proof=proof_case; changed=copy.deepcopy(m)
    old=changed['profile'].get(field)
    changed['profile'][field]=(old+1 if type(old) is int else str(old)+'-changed')
    with pytest.raises((ValueError,KeyError)):w._packing_evidence(evidence,changed)
    with pytest.raises((ValueError,KeyError)):proof.check(changed)

@pytest.mark.parametrize('field',['tokens','readout','condition','stream','instance_id','record','mask_length','donor'])
def test_index_matches_full_validator_input_rejection(proof_case,field):
    m,evidence,proof=proof_case;changed=copy.deepcopy(m);row=changed['timing_inputs'][0]
    if field=='tokens':row['record']['streams'][row['stream']]['tokens'][0]+=1
    elif field=='readout':row['readout']+=1
    elif field=='record':row['record']['unexpected_source_field']='changed'
    elif field=='mask_length':row['unpadded_length']-=1
    elif field=='donor':changed['donor_convention']='unknown'
    else:row[field]+='-changed'
    if field!='donor':
        with pytest.raises((ValueError,KeyError)):w._packing_evidence(evidence,changed)
    with pytest.raises((ValueError,KeyError)):proof.check(changed)

@pytest.mark.parametrize('field',['site','seed','family','axis_index','operation','axis_sha256'])
def test_index_matches_full_validator_axis_rejection(proof_case,field):
    m,evidence,proof=proof_case;changed=copy.deepcopy(m);a=changed['axis_scope'][0]
    old=a[field];a[field]=['head',999,999] if field=='site' else (old+1 if type(old) is int else old+'-changed')
    with pytest.raises((ValueError,KeyError)):w._packing_evidence(evidence,changed)
    with pytest.raises((ValueError,KeyError)):proof.check(changed)
    assert not proof.covers_axes(changed['axis_scope'])

@pytest.mark.parametrize('seed',[1,42,123])
def test_probe_prediction_scalar_oracle_with_unbalanced_labels_and_ties(seed):
    gen=torch.Generator().manual_seed(seed);x=torch.randn(17,4,generator=gen)
    probe=dict(center=torch.randn(4,generator=gen),scale=torch.rand(4,generator=gen)+.1,
        coefficient=torch.randn(4,generator=gen),intercept=.25,regularization=1.)
    labels=torch.tensor([1.]*5+[-1.]*12)
    oracle=torch.where(((x.double()-probe['center'].double())/probe['scale'].double())@probe['coefficient'].double()+.25>=0,1.,-1.)
    assert torch.equal(d.probe_predictions(probe,x),oracle)
    expected=np.mean([(oracle.numpy()[labels.numpy()==c]==c).mean() for c in [-1.,1.]])
    assert abs(d.probe_balanced_accuracy(probe,x,labels)-expected)<1e-7
    probe['coefficient']=torch.zeros(4);probe['intercept']=0.
    assert torch.equal(d.probe_predictions(probe,x),torch.ones(17))

@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-float('inf')])
def test_probe_nonfinite_rejects(bad):
    probe=dict(center=torch.zeros(1),scale=torch.ones(1),coefficient=torch.ones(1),intercept=0.,regularization=1.)
    with pytest.raises(ValueError):d.probe_predictions(probe,[[bad]])

def test_cost_full_and_reference_proof_equivalence_and_not_authority():
    inv=inventory();rr=receipts(inv);full=w.project_cost(rr,inv,ledger(inv))
    proofs={}
    for pid,evidence in rr[0]['packing_evidence'].items():
        m=next(x for x in rr[0]['measurements'] if x.get('packing_id')==pid)
        proofs[pid]=w._validate_packing_proof(evidence,m)
    rr[0]['packing_evidence']={pid:dict(kind='a3_packing_proof_reference_v1',evidence_sha256=p.source_digest) for pid,p in proofs.items()}
    typed=w.project_cost(rr,inv,ledger(inv),packing_proofs={(w.digest(rr[0]),pid):p for pid,p in proofs.items()})
    for key in ('projected_seconds','projected_gpu_hours','execution_authorized','jobs','requirements'):
        if key in full:assert typed[key]==full[key]
    assert full['execution_authorized'] is typed['execution_authorized'] is False
    with pytest.raises(ValueError):w.project_cost(rr,inv,ledger(inv),packing_proofs={})

def test_candidate_selector_rejects_other_condition_and_stream():
    profile={'p':1};a=SimpleNamespace(task='far',condition='D',stream='clean',ids=['v'])
    b=SimpleNamespace(task='far',condition='I',stream='clean',ids=['v'])
    results=[dict(invocation=dict(profile=profile),batches=[a]),dict(invocation=dict(profile=profile),batches=[b])]
    req=dict(profile=profile,timing_inputs=[dict(source_task='far',condition='I',stream='clean',instance_id='v')])
    assert r._pilot_candidates(results,req)==results[1:]
    req['timing_inputs'][0]['stream']='corrupt';assert r._pilot_candidates(results,req)==[]
