"""Bounded synthetic CPU fits; no model or evaluation split access."""
import copy
import numpy as np
import pytest
import torch
from component_analysis import a3_direction_artifacts as artifacts
from tests.test_a3_direction_artifacts import scientific_metadata


def fixture(tmp_path, *, zero=False):
    from component_analysis import a3_direction_pipeline as p
    identity=scientific_metadata()['identity']
    ids=['id0','id1','id2','id3']; site=['head',7,16]
    rows=[]
    for c in ('D','I','H','user_neutral'):
        for j,rid in enumerate(ids):
            rows.append(dict(instance_id=rid,condition=c,split='train',pressure_text='wording'+str(j//2),
                streams={s:dict(prompt=c+rid+s,tokens=[1,2,3+j],readout=2,
                               layout={'content_spans':[['user',0,2]]},user_request_span=[1,2]) for s in ('clean','corrupt')}))
    rows.append(dict(instance_id='validation',split='validation',condition='D',streams={'clean':{'tokens':[999]*1000}}))
    design=dict(injected=True,seeds=[42,1,123],tasks={'far_v2':dict(fit_ids=ids,direction_sites=[site],selection_ids=['validation'],assessment_ids=['assessment'])},
                access_rows={'far_v2':rows},a1_identity=identity['a1_identity'],parent_evidence=identity['parent_evidence'])
    protocol=dict(injected=True,commit=identity['commit'],code_hashes=identity['code_hashes'],
        fit_cache=dict(capture_identity={k:identity[k] for k in ('commit','code_hashes','a1_identity','parent_evidence','matched_source_hashes','grader_sha256','model','model_revision','tokenizer_revision','tokenizer_identity','numeric_profile')},probe_max_bytes=1024*1024))
    metadata,layout=p._fit_contract(design,protocol)
    rng=np.random.default_rng(21); h=rng.normal(size=(4,2,2)).astype('float32')
    arrays={'geometry0_projection':np.eye(2,dtype='float32')}
    for condition in ('D','I','H','user_neutral'):
        arrays['t0_s0_'+condition]=h.copy()
    arrays['t0_s0_D']+=0 if zero else np.array([2.,-1.],dtype='float32')
    arrays['t0_s0_user_neutral']-=np.array([.2,1.],dtype='float32')
    cache=tmp_path/'capture'; artifacts.write_bundle(cache,metadata,arrays)
    return p,design,protocol,cache,metadata,arrays


def run_fixture(tmp_path,**kwargs):
    p,d,pr,c,_,_=fixture(tmp_path,**kwargs)
    result=p.fit_from_cache(d,c,protocol=pr,output=tmp_path/'fits')
    metadata,arrays=artifacts.read_bundle(tmp_path/'fits',expected=result)
    return metadata,arrays


def test_fit_consumes_train_only_complete_cache(tmp_path):
    meta,arrays=run_fixture(tmp_path)
    assert meta['kind']=='a3_direction_fit' and meta['injected'] is True
    assert meta['identity']['analysis_split']=='train'
    assert len(meta['fit_records'])==3 and all(r['valid'] for r in meta['fit_records'])
    assert meta['identity']['capture_lineage'] and meta['blocked_task_seeds']==[]
    assert all(np.isfinite(v).all() for v in arrays.values())


@pytest.mark.parametrize('damage',['validation','assessment','ids','streams','sites','source','profile','incomplete'])
def test_cache_mutations_rejected_against_independent_freeze(tmp_path,damage):
    p,d,pr,c,meta,arrays=fixture(tmp_path)
    changed=copy.deepcopy(meta)
    if damage in ('validation','assessment'):
        changed['split']=damage; changed['identity']['analysis_split']=damage
    elif damage=='ids': changed['identity']['ordered_ids'][0]='intruder'
    elif damage=='streams': changed['identity']['streams'].reverse()
    elif damage=='sites': changed['identity']['sites']=[['head',1,1]]
    elif damage=='source': changed['identity']['matched_source_hashes']={'other':'9'*64}
    elif damage=='profile': changed['identity']['numeric_profile']['padded_width']+=1
    elif damage=='incomplete': arrays.pop('t0_s0_H')
    other=tmp_path/'changed'; artifacts.write_bundle(other,changed,arrays)
    with pytest.raises(ValueError): p.fit_from_cache(d,other,protocol=pr,output=tmp_path/'fits')
    assert not (tmp_path/'fits').exists()


def test_cluster_weights_shared_dom_nuisance_probe(tmp_path):
    meta,arrays=run_fixture(tmp_path)
    for row in meta['fit_records']:
        assert row['dom']['bootstrap']==row['nuisance']['bootstrap']==row['image_probe']['bootstrap']==row['metadata_probe']['bootstrap']
        weights=arrays[row['dom']['arrays']['id_weights']]
        assert float(weights.sum())==pytest.approx(1)
        assert row['image_probe']['expanded_examples']==row['dom']['bootstrap']['expanded_n']*4


def test_zero_dom_receipt_is_not_replaced(tmp_path):
    meta,arrays=run_fixture(tmp_path,zero=True)
    assert len(meta['blocked_task_seeds'])==3
    assert all(not r['valid'] and r['dom']['status']=='unfitted' for r in meta['fit_records'])
    assert all('v' not in r['dom'].get('arrays',{}) for r in meta['fit_records'])
    assert all(r['nuisance']['status']=='fitted' for r in meta['fit_records'])


def test_probe_standardization_never_uses_validation(tmp_path):
    p,d,pr,c,_,_=fixture(tmp_path)
    a=p.fit_from_cache(d,c,protocol=pr,output=tmp_path/'fits')
    assert all(r['image_probe']['status']=='fitted' for r in a['fit_records'])
    assert 'validation' not in a['identity']['ordered_ids']
    _,out_arrays=artifacts.read_bundle(tmp_path/'fits',expected=a)
    _,cache_arrays=artifacts.read_bundle(c,expected=p._fit_contract(d,pr)[0])
    for row in a['fit_records']:
        weights=out_arrays[row['dom']['arrays']['id_weights']]
        expected=sum((cache_arrays['t0_s0_D'].mean(1)+cache_arrays['t0_s0_I'].mean(1))*weights[:,None])/2
        assert np.allclose(out_arrays[row['image_probe']['arrays']['center']],expected)


def test_nuisance_never_changes_sites(tmp_path):
    meta,_=run_fixture(tmp_path)
    assert {tuple(r['site']) for r in meta['fit_records']}=={('head',7,16)}
    assert all(r['nuisance_cosine'] is not None for r in meta['fit_records'])


def test_fit_bundle_deduplicates_geometry(tmp_path):
    meta,arrays=run_fixture(tmp_path)
    assert len(meta['geometries'])==1
    assert sum(name.endswith('_projection') for name in arrays)==1
    assert len({r['geometry'] for r in meta['fit_records']})==1


def test_probe_preflight_retains_failed_diagnostic(tmp_path):
    p,d,pr,c,_,_=fixture(tmp_path)
    # Rebuild capture with the amended frozen byte limit and protocol digest.
    pr['fit_cache']['probe_max_bytes']=1
    meta,_=p._fit_contract(d,pr); _,arrays=artifacts.read_bundle(c,expected=p._fit_contract(d,{**pr,'fit_cache':{**pr['fit_cache'],'probe_max_bytes':1024*1024}})[0])
    artifacts.write_bundle(tmp_path/'tiny',meta,arrays)
    out=p.fit_from_cache(d,tmp_path/'tiny',protocol=pr,output=tmp_path/'fits')
    assert all(r['valid'] and r['image_probe']['status']=='failed' and r['metadata_probe']['status']=='failed' for r in out['fit_records'])


def test_failed_nuisance_and_nonfinite_probe_remain_diagnostics(tmp_path):
    p,d,pr,c,meta,arrays=fixture(tmp_path)
    arrays['t0_s0_user_neutral']=arrays['t0_s0_H'].copy()
    artifacts.write_bundle(tmp_path/'neutralzero',meta,arrays)
    out=p.fit_from_cache(d,tmp_path/'neutralzero',protocol=pr,output=tmp_path/'fits')
    assert all(r['valid'] and r['nuisance']['status']=='unfitted' and r['nuisance_cosine'] is None for r in out['fit_records'])
    assert out['blocked_task_seeds']==[]


def test_zero_projection_retains_every_failed_seed(tmp_path):
    p,d,pr,c,meta,arrays=fixture(tmp_path)
    arrays['geometry0_projection'][:]=0
    artifacts.write_bundle(tmp_path/'zero_geometry',meta,arrays)
    out=p.fit_from_cache(d,tmp_path/'zero_geometry',protocol=pr,output=tmp_path/'fits')
    assert len(out['fit_records'])==3 and len(out['blocked_task_seeds'])==3
    assert all(r['image_probe']['status']=='failed' and r['metadata_probe']['status']=='fitted' for r in out['fit_records'])
    assert all(g['status']=='unfitted' for g in out['geometries'].values())


@pytest.mark.parametrize('damage',['nonfinite','overflow'])
def test_nonfinite_activation_preserves_failed_receipts(tmp_path,damage):
    p,d,pr,c,meta,arrays=fixture(tmp_path)
    arrays['t0_s0_D']=arrays['t0_s0_D'].astype('float64')
    arrays['t0_s0_D'][:]=np.inf if damage=='nonfinite' else 1e100
    artifacts.write_bundle(tmp_path/'badnumeric',meta,arrays)
    with np.errstate(over='ignore'):
        out=p.fit_from_cache(d,tmp_path/'badnumeric',protocol=pr,output=tmp_path/'fits')
    assert all(not r['valid'] and r['image_probe']['status']=='failed' for r in out['fit_records'])
    assert len(out['blocked_task_seeds'])==3


def test_probe_preflight_accounts_for_head_to_image_transform():
    from component_analysis import a3_direction_pipeline as p
    base=p._probe_preflight(4,2,1,4,head_width=1)
    wide=p._probe_preflight(4,2,1,4,head_width=128)
    assert wide['estimated_peak_bytes']-base['estimated_peak_bytes'] >= 4*127


@pytest.mark.parametrize('field,value',[('task_order',['ser_v2']),('stream_order',['corrupt','clean']),('seeds',[42]),('candidate_sites',{'far_v2':[['head',1,1]]}),('design_sha256','0'*64)])
def test_frozen_operational_contract_cannot_disagree_with_design(tmp_path,field,value):
    p,d,pr,c,_,_=fixture(tmp_path)
    pr[field]=value
    with pytest.raises(ValueError,match='frozen'):
        p._fit_contract(d,pr)
