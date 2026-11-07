"""Synthetic CPU-only validation freeze; no model, pilot, or assessment outcomes."""
import copy
import numpy as np
import pytest
import torch
from component_analysis import a3_direction_pipeline as pipeline
from component_analysis import a3_directions as directions
from component_analysis import a3_direction_artifacts as artifacts
from tests.test_a3_direction_fit import fixture as fit_fixture


def test_gate_first_and_fallback_match_reviewed_core():
    sites=[['head',2,1],['head',1,2]]
    records=[dict(task='far_v2',site=s,seed=42,valid=True) for s in sites]
    summaries=[dict(site=sites[0],seed=42,split='validation',D_fraction=.9,I_fraction=.4,point_pass=False),
               dict(site=sites[1],seed=42,split='validation',D_fraction=.6,I_fraction=.2,point_pass=True)]
    selected,failed=pipeline._select_candidates(records,summaries,task='far_v2',seed=42)
    assert selected==directions.select_direction(summaries,sites=sites,seed=42)
    assert failed==[] and selected['site']==sites[1]
    summaries[1]['point_pass']=False
    selected,_=pipeline._select_candidates(records,summaries,task='far_v2',seed=42)
    assert selected['validation_failure'] and selected['site']==sites[0]
    summaries[1].update(D_fraction=.8,I_fraction=.3)
    selected,_=pipeline._select_candidates(records,summaries,task='far_v2',seed=42)
    assert selected['site']==sites[1]  # lexical tie


def test_nonfinite_fraction_blocks_seed_if_no_valid_candidate():
    records=[dict(task='far_v2',site=['head',1,1],seed=42,valid=True)]
    summaries=[dict(site=['head',1,1],seed=42,split='validation',D_fraction=float('nan'),I_fraction=.1,point_pass=False)]
    selected,failed=pipeline._select_candidates(records,summaries,task='far_v2',seed=42)
    assert selected is None and len(failed)==1
    assert failed[0]['reason']=='nonfinite validation fraction'


def test_exact_null_rng_offsets_and_axis_specific_h_statistics():
    projection=torch.tensor([[2.,0.],[0.,1.],[0.,0.]])
    h=torch.tensor([[[1.,2.],[2.,1.]],[[3.,4.],[4.,5.]]])
    weights=torch.tensor([.25,.75])
    arrays={}
    assessment,calibration,axes=pipeline._freeze_null_axes(projection,h,weights,seed=42,prefix='selected0',arrays=arrays)
    for descriptors,n,rng_seed in ((assessment,199,42),(calibration,32,21042)):
        assert len(descriptors)==n
        expected=directions.random_image_directions(projection,n=n,seed=rng_seed)
        for j,descriptor in enumerate(descriptors):
            assert descriptor['axis_index']==j
            axis=axes[descriptor['reference']]
            assert torch.allclose(torch.from_numpy(arrays[axis['arrays']['v']]),expected[j])
            prepared=directions.prepare_image_direction(projection,expected[j],h,id_weights=weights)
            assert axis['projected_variance']==pytest.approx(prepared['projected_variance'])
            assert axis['rng_seed']==10000+rng_seed
            assert axis['geometry_rank']==2
    assert not torch.equal(torch.from_numpy(arrays[axes[assessment[0]['reference']]['arrays']['v']]),
                           torch.from_numpy(arrays[axes[calibration[0]['reference']]['arrays']['v']]))


def selection_fixture(tmp_path, *, zero=False, nuisance_zero=False, damage=None, protocol_change=None):
    p,d,pr,cache,_,arrays=fit_fixture(tmp_path,zero=zero)
    ids=d['tasks']['far_v2']['selection_ids']
    template=copy.deepcopy(d['access_rows']['far_v2'][0])
    d['access_rows']['far_v2']=[r for r in d['access_rows']['far_v2'] if r['split']=='train']
    for c in ('D','H','F','I','user_neutral'):
        r=copy.deepcopy(template); r.update(instance_id=ids[0],condition=c,split='validation')
        d['access_rows']['far_v2'].append(r)
    for task,n in (('ioi',2),('mmlu',32)):
        d[task+'_validation']=[]
        for j in range(n):
            r=copy.deepcopy(template); r.update(instance_id=task+str(j),condition=task.upper(),task=task,split='test' if task=='mmlu' else 'validation',analysis_split='validation')
            d[task+'_validation'].append(r)
    groups=[]
    for j,task in enumerate(('far_v2','ioi','mmlu')):
        profile=copy.deepcopy(pr['fit_cache']['capture_identity']['numeric_profile'])
        profile['padded_width']+=j
        groups.append(dict(group_id='group'+str(j),analysis_task='far_v2',source_task=task,
            site=['head',7,16],numeric_profile=profile,rows_per_shard=1000))
    pr['selection_cache']=dict(groups=groups)
    if protocol_change: pr.update(protocol_change)
    meta,_=p._fit_contract(d,pr)
    if nuisance_zero: arrays['t0_s0_user_neutral']=arrays['t0_s0_H'].copy()
    artifacts.write_bundle(tmp_path/'train',meta,arrays)
    fits=p.fit_from_cache(d,tmp_path/'train',protocol=pr,output=tmp_path/'fits')
    _,fit_arrays=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    # Fixture adapter for deferred F: strict per-profile captures and raw shards.
    fit_ref=p._bundle_byte_reference(tmp_path/'fits')
    layout=p._selection_layout(d,pr,fits)
    root=tmp_path/'validation'
    for group in layout:
        path=root/group['group_id']
        artifacts.write_bundle(path/'capture',group['capture_metadata'],{})
        identity=copy.deepcopy(group['capture_metadata']['identity'])
        identity['capture_lineage']=[artifacts.capture_reference(path/'capture',expected=group['capture_metadata'])]
        for shard in group['shards']:
            rows=[]
            for key in shard['expected_keys']:
                row=dict(zip(artifacts.KEY_FIELDS,key))
                row['site']=list(row['site'])
                source=group['sources'][(row['condition'],row['instance_id'])]
                fit=next(r for r in fits['fit_records'] if r['seed']==row['seed'])
                axis=p._loaded_fit_axis(fits,fit_arrays,fit,'dom')
                from component_analysis.a3_direction_runner import axis_identity
                c=row['condition']
                row.update(intact_margin=2. if c in ('D','I') else 0.,
                    patched_margin=.6 if c=='D' else (1.8 if c=='I' else 0.),
                    intact_correct=True,patched_correct=True,epsilon=1e-6,
                    source_provenance=p._selection_source_record(source,row['stream'],row['source_task']),
                    numeric_profile=group['numeric_profile'],axis_hash=axis_identity(axis),
                    replay_valid=True,supported=True,positive_control={'valid':True},gate_valid=True)
                if damage: damage(row)
                rows.append(row)
            artifacts.publish_shard(path/'shards'/shard['shard_id'],identity=identity,
                expected_keys=shard['expected_keys'],rows=rows,execution={'fit_reference':fit_ref})
    return p,d,pr,root,fits


def test_selected_axes_are_frozen_before_assessment(tmp_path):
    p,d,pr,root,fits=selection_fixture(tmp_path)
    protocol_file=tmp_path/'direction_protocol.json'
    artifacts.ladder.write_artifact(protocol_file,pr)
    out=p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected',protocol_path=protocol_file)
    meta,arrays=artifacts.read_bundle(tmp_path/'selected',expected=out)
    assert meta['selection_split']=='validation' and meta['split']=='train'
    assert meta['protocol_file_reference']['file_sha256']==artifacts.common.file_hash(protocol_file)
    with pytest.raises(ValueError): artifacts.validate_final_identity(meta['identity'],final=True)
    assert meta['status']=='selected' and len(meta['selected_records'])==3
    assert meta['validation_references'] and meta['fit_reference']
    for geometry in meta['geometries'].values():
        if geometry['status']=='fitted':
            assert all(ref in arrays for ref in geometry['arrays'].values())
    assert len(meta['validation_table'])==3
    for record in meta['selected_records']:
        assert record['site']==['head',7,16]
        assert len(record['assessment_axes'])==199 and len(record['calibration_axes'])==32
        assert record['steering']['random']==record['assessment_axes'][0]
        assert record['steering']['signs']==[-1,1]
        assert record['nuisance']['status']=='fitted'
    with pytest.raises(ValueError): p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected')


def test_nuisance_uses_dom_site_and_unfitted_is_conditional(tmp_path):
    p,d,pr,root,_=selection_fixture(tmp_path,nuisance_zero=True)
    out=p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected')
    assert out['blocked_task_seeds']==[]
    assert all(r['nuisance']['status']=='unfitted' and r['nuisance']['fit_receipt'] for r in out['selected_records'])
    _,arrays=artifacts.read_bundle(tmp_path/'selected',expected=out)
    layout=p._fit_contract(d,pr)[1][0]
    for record in out['selected_records']:
        weights,_=p._bootstrap(layout['cluster_ids'],layout['instance_ids'],record['seed'])
        for descriptor in record['assessment_axes']+record['calibration_axes']:
            receipt=out['axes'][descriptor['reference']]
            geometry=out['geometries'][receipt['geometry']]
            pinv=np.array(arrays[geometry['arrays']['pinv']])
            v=np.array(arrays[receipt['arrays']['v']])
            assert np.allclose(pinv@v,arrays[receipt['arrays']['pullback']],atol=2e-6,rtol=2e-6)
            assert np.array_equal(arrays[receipt['arrays']['id_weights']],weights.numpy())


@pytest.mark.parametrize('damage',['membership','profile','axis','source','assessment','pilot','partial'])
def test_selection_cannot_read_pilot_or_assessment_or_changed_validation(tmp_path,damage):
    def mutate(row):
        if damage=='profile': row['numeric_profile']['padded_width']+=10
        elif damage=='axis': row['axis_hash']='0'*64
        elif damage=='source': row['source_provenance']['streams']['clean']['tokens']=[999]
    p,d,pr,root,_=selection_fixture(tmp_path,damage=mutate)
    if damage in ('assessment','pilot'):
        # Protocol layout is validation-only; no caller can redirect its split.
        pr['selection_cache']['groups'][0]['split']=damage
    elif damage=='membership': d['tasks']['far_v2']['selection_ids']=['different']
    elif damage=='partial': next(root.glob('*/shards/*/COMPLETE.json')).unlink()
    with pytest.raises((ValueError,KeyError)):
        p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected')
    assert not (tmp_path/'selected').exists()


def test_validation_all_gates_include_disjoint_mmlu(tmp_path):
    def damage(row):
        if row['source_task']=='mmlu' and row['operation']=='h_mean' and row['instance_id'] in ('mmlu0','mmlu1'):
            row['patched_correct']=False
    p,d,pr,root,_=selection_fixture(tmp_path,damage=damage)
    out=p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected')
    assert all(r['selection']['validation_failure'] for r in out['selected_records'])
    assert out['status']=='validation-failed'


def test_missing_seed_fit_is_rejected_before_selection(tmp_path):
    p,d,pr,root,fits=selection_fixture(tmp_path)
    _,arrays=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    fits['fit_records'].pop()
    artifacts.write_bundle(tmp_path/'short-fits',fits,{k:np.array(v) for k,v in arrays.items()})
    with pytest.raises(ValueError,match='fit candidate coverage'):
        p.freeze_selection(d,tmp_path/'short-fits',root,protocol=pr,output=tmp_path/'selected')


def test_no_fitted_dom_blocks_all_seeds_without_nuisance_rescue(tmp_path):
    p,d,pr,root,_=selection_fixture(tmp_path,zero=True)
    out=p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected')
    assert out['selected_records']==[] and len(out['blocked_task_seeds'])==3
    assert len(out['candidate_failures'])==3 and out['status']=='blocked'


def test_validation_floor_membership_is_disjoint_by_prompt_and_source_id():
    row=dict(instance_id='v',source_id='source',streams={'clean':dict(prompt='same bytes')})
    row.update(condition='MMLU',split='test',analysis_split='validation')
    rows=[dict(copy.deepcopy(row),instance_id='v'+str(j)) for j in range(32)]
    d=dict(injected=True,mmlu_validation=rows,utility={'mmlu':[dict(copy.deepcopy(row),instance_id='a')]})
    with pytest.raises(ValueError,match='utility collision'):
        pipeline._selection_sources(d,'mmlu')


def test_noninterpretable_validation_keeps_failure_table_and_blocks_seed(tmp_path):
    def damage(row):
        if row['condition']=='D': row['intact_margin']=0.
    p,d,pr,root,_=selection_fixture(tmp_path,damage=damage)
    out=p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected')
    assert len(out['blocked_task_seeds'])==3 and out['selected_records']==[]
    assert len(out['validation_table'])==3 and out['validation_references']
    assert all(r['D_fraction'] is None for r in out['validation_table'])
    assert all(r['reason']=='nonfinite validation fraction' for r in out['candidate_failures'])


def test_selection_children_are_immutable_and_axis_geometry_is_self_contained(tmp_path):
    from component_analysis.a3_direction_runner import axis_identity
    p,d,pr,root,_=selection_fixture(tmp_path)
    out=p.freeze_selection(d,tmp_path/'fits',root,protocol=pr,output=tmp_path/'selected')
    _,arrays=artifacts.read_bundle(tmp_path/'selected',expected=out)
    for record in out['selected_records']:
        for descriptor in [record['learned_axis'],record['assessment_axes'][0],record['calibration_axes'][0]]:
            receipt=out['axes'][descriptor['reference']]
            geometry=out['geometries'][receipt['geometry']]
            axis={k:torch.from_numpy(np.array(arrays[v])) for k,v in geometry['arrays'].items()}
            axis.update({k:torch.from_numpy(np.array(arrays[v])) for k,v in receipt['arrays'].items()})
            axis.update({k:receipt[k] for k in ('sigma_fit','projected_variance')})
            assert axis_identity(axis)==descriptor['sha256']
    array_file=next((tmp_path/'selected'/'arrays').glob('*.npy'))
    array_file.write_bytes(array_file.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='hash|bytes'):
        artifacts.read_bundle(tmp_path/'selected',expected=out)


def test_fit_geometry_must_equal_its_source_site_projection(tmp_path):
    p,d,pr,root,fits=selection_fixture(tmp_path)
    _,loaded=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    arrays={k:np.array(v) for k,v in loaded.items()}
    geometry=next(iter(fits['geometries'].values()))
    arrays[geometry['arrays']['projection']]*=2
    artifacts.write_bundle(tmp_path/'other-geometry',fits,arrays)
    with pytest.raises(ValueError,match='source site projection'):
        p._read_selection_fits(d,pr,tmp_path/'other-geometry')


@pytest.mark.parametrize('field,value',[('assessment_orientations',198),('calibration_orientations',31)])
def test_frozen_protocol_cannot_claim_different_null_counts(tmp_path,field,value):
    with pytest.raises(ValueError,match='frozen null'):
        selection_fixture(tmp_path,protocol_change={field:value})


def test_production_selection_requires_canonical_protocol_path(tmp_path):
    with pytest.raises(ValueError,match='protocol_path'):
        pipeline.freeze_selection({'injected':False},tmp_path/'unused-fits',tmp_path/'unused-validation',
            protocol={},output=tmp_path/'selected')


def test_protocol_file_rejects_mismatched_payload_and_reencoded_recorded_bytes(tmp_path):
    from component_analysis import ladder_pipeline
    protocol={'injected':True,'frozen':'fixture'}
    wrong=tmp_path/'wrong.json'; ladder_pipeline.write_artifact(wrong,dict(protocol,frozen='other'))
    with pytest.raises(ValueError,match='protocol'):
        pipeline._selection_protocol_reference(protocol,wrong,injected=True)
    path=tmp_path/'protocol.json'; ladder_pipeline.write_artifact(path,protocol)
    reference=pipeline._selection_protocol_reference(protocol,path,injected=True)
    path.write_text(path.read_text()+'\n')
    with pytest.raises(ValueError,match='protocol.*bytes'):
        pipeline._selection_protocol_reference(protocol,path,injected=True,expected=reference)


def _resign_selection_fit(tmp_path, fits, arrays):
    """Attack fixture: update all byte links; rejection must be semantic."""
    target=tmp_path/'resigned-fits'
    artifacts.write_bundle(target,fits,arrays)
    reference=pipeline._bundle_byte_reference(target)
    for root in (tmp_path/'validation').glob('*/shards/*'):
        manifest=artifacts._strict_json(root/'run_manifest.json')
        manifest['execution']['fit_reference']=reference
        artifacts.common.write_json(root/'run_manifest.json',manifest)
        artifacts.common.write_json(root/'COMPLETE.json',dict(schema_version=1,kind='a3_complete',files=artifacts._children(root)))
    return target


def test_resigned_perpendicular_pseudoinverse_rejected_with_unfitted_nuisance(tmp_path):
    p,d,pr,root,fits=selection_fixture(tmp_path,nuisance_zero=True)
    _,loaded=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    arrays={k:np.array(v) for k,v in loaded.items()}
    geometry=next(iter(fits['geometries'].values()))
    v=arrays[fits['fit_records'][0]['dom']['arrays']['v']]
    perpendicular=np.array([-v[1],v[0]],dtype=np.float32)
    arrays[geometry['arrays']['pinv']]+=2*np.outer(perpendicular,perpendicular)
    path=_resign_selection_fit(tmp_path,fits,arrays)
    with pytest.raises(ValueError,match='shared geometry'):
        p.freeze_selection(d,path,root,protocol=pr,output=tmp_path/'selected')
    assert not (tmp_path/'selected').exists()


@pytest.mark.parametrize('nuisance_unfitted',[False,True])
def test_resigned_bootstrap_weights_rejected_from_trusted_draw(tmp_path,nuisance_unfitted):
    p,d,pr,root,fits=selection_fixture(tmp_path,nuisance_zero=nuisance_unfitted)
    _,loaded=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    arrays={k:np.array(v) for k,v in loaded.items()}
    record=fits['fit_records'][0]
    arrays[record['dom']['arrays']['id_weights']][:]=[.5,.5,0.,0.]
    path=_resign_selection_fit(tmp_path,fits,arrays)
    with pytest.raises(ValueError,match='bootstrap weights'):
        p.freeze_selection(d,path,root,protocol=pr,output=tmp_path/'selected')
    assert not (tmp_path/'selected').exists()


@pytest.mark.parametrize('family',['dom','nuisance','image_probe','metadata_probe'])
def test_resigned_bootstrap_receipts_checked_even_if_nuisance_unfitted(tmp_path,family):
    p,d,pr,root,fits=selection_fixture(tmp_path,nuisance_zero=True)
    _,loaded=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    fits['fit_records'][0][family]['bootstrap']['cluster_draws'].append('forged-cluster')
    path=_resign_selection_fit(tmp_path,fits,{k:np.array(v) for k,v in loaded.items()})
    with pytest.raises(ValueError,match='bootstrap receipt'):
        p.freeze_selection(d,path,root,protocol=pr,output=tmp_path/'selected')


@pytest.mark.parametrize('damage',['rank','rank_rtol','spectrum','basis'])
def test_full_shared_geometry_is_bound_to_source_projection(tmp_path,damage):
    p,d,pr,root,fits=selection_fixture(tmp_path,nuisance_zero=True)
    _,loaded=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    arrays={k:np.array(v) for k,v in loaded.items()}
    geometry=next(iter(fits['geometries'].values()))
    if damage=='rank': geometry['rank']=1
    elif damage=='rank_rtol': geometry['rank_rtol']=.1
    elif damage=='spectrum': arrays[geometry['arrays']['spectrum']]*=2
    else: arrays[geometry['arrays']['U']]*=2
    path=_resign_selection_fit(tmp_path,fits,arrays)
    with pytest.raises(ValueError,match='shared geometry'):
        p.freeze_selection(d,path,root,protocol=pr,output=tmp_path/'selected')


@pytest.mark.parametrize('family',['dom','nuisance'])
@pytest.mark.parametrize('damage',['center','variance'])
def test_fitted_h_statistics_are_recomputed_from_trusted_train_h(tmp_path,family,damage):
    p,d,pr,root,fits=selection_fixture(tmp_path)
    _,loaded=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    arrays={k:np.array(v) for k,v in loaded.items()}
    receipt=fits['fit_records'][0][family]
    if damage=='center': arrays[receipt['arrays']['h_center']]+=.2
    else:
        receipt['projected_variance']+=.5
        receipt['sigma_fit']=float(np.sqrt(receipt['projected_variance']))
    path=_resign_selection_fit(tmp_path,fits,arrays)
    with pytest.raises(ValueError,match='train H statistics'):
        p.freeze_selection(d,path,root,protocol=pr,output=tmp_path/'selected')


def test_equivalent_orthonormal_basis_preserves_legitimate_geometry(tmp_path):
    p,d,pr,root,fits=selection_fixture(tmp_path,nuisance_zero=True)
    _,loaded=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    arrays={k:np.array(v) for k,v in loaded.items()}
    geometry=next(iter(fits['geometries'].values()))
    key=geometry['arrays']['U']
    arrays[key]=arrays[key]@np.array([[0.,-1.],[1.,0.]],dtype=np.float32)
    path=_resign_selection_fit(tmp_path,fits,arrays)
    out=p.freeze_selection(d,path,root,protocol=pr,output=tmp_path/'selected')
    assert out['status']=='selected' and len(out['selected_records'])==3


@pytest.mark.parametrize('family',['dom','nuisance'])
def test_resigned_fit_axis_arrays_cannot_shadow_shared_geometry(tmp_path,family):
    from component_analysis.a3_direction_runner import axis_identity
    p,d,pr,root,fits=selection_fixture(tmp_path,nuisance_zero=family=='dom')
    _,loaded=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    arrays={k:np.array(v) for k,v in loaded.items()}
    geometry=next(iter(fits['geometries'].values()))
    arrays['override_projection']=2*arrays[geometry['arrays']['projection']]
    arrays['override_pinv']=arrays[geometry['arrays']['pinv']]/2
    for record in fits['fit_records']:
        receipt=record[family]
        receipt['arrays'].update(projection='override_projection',pinv='override_pinv')
        arrays[receipt['arrays']['pullback']]/=2
    path=_resign_selection_fit(tmp_path,fits,arrays)
    # Preserve every validation axis-byte link as well. Deliberately reconstruct
    # the old unsafe merge here, since the production loader must reject it.
    for shard in root.glob('*/shards/*'):
        rows=[artifacts._strict_json_line(line) for line in (shard/'rows.jsonl').read_text().splitlines()]
        for row in rows:
            record=next(r for r in fits['fit_records'] if r['seed']==row['seed'])
            receipt=record['dom']
            axis={k:torch.from_numpy(arrays[v]) for k,v in geometry['arrays'].items()}
            axis.update({k:torch.from_numpy(arrays[v]) for k,v in receipt['arrays'].items()})
            axis.update({k:receipt[k] for k in ('sigma_fit','projected_variance')})
            row['axis_hash']=axis_identity(axis)
        artifacts.common.write_jsonl(shard/'rows.jsonl',rows)
        artifacts.common.write_json(shard/'COMPLETE.json',dict(schema_version=1,kind='a3_complete',files=artifacts._children(shard)))
    with pytest.raises(ValueError,match='fit-axis arrays'):
        p.freeze_selection(d,path,root,protocol=pr,output=tmp_path/'selected')
    assert not (tmp_path/'selected').exists()


@pytest.mark.parametrize('family',['dom','nuisance'])
def test_fitted_axis_array_schema_requires_all_four_fields(tmp_path,family):
    p,d,pr,root,fits=selection_fixture(tmp_path)
    _,arrays=artifacts.read_bundle(tmp_path/'fits',expected=fits)
    record=copy.deepcopy(fits['fit_records'][0])
    del record[family]['arrays']['id_weights']
    with pytest.raises(ValueError,match='fit-axis arrays'):
        p._loaded_fit_axis(fits,arrays,record,family)
