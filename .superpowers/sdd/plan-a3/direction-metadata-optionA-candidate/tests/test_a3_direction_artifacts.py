"""Immutable numeric artifact and refresh-before-access contracts."""
import copy
import json
import numpy as np
import pytest


def test_partial_bundle_never_reused(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    target=tmp_path/'partial'; target.mkdir(); (target/'manifest.json').write_text('{}')
    with pytest.raises(ValueError,match='complete'):
        a.read_bundle(target,expected={})
    with pytest.raises(ValueError,match='exists'):
        a.write_bundle(target,generic_metadata(), {'axis':np.ones(3)})


def test_bundle_numeric_bytes_and_identity(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    target=tmp_path/'bundle'; metadata=dict(generic_metadata(),commit='a'*40,fixture_kind='axis')
    a.write_bundle(target,metadata,{'axis':np.arange(3,dtype=np.float32)})
    meta,arrays=a.read_bundle(target,expected=metadata)
    assert meta==metadata and np.array_equal(arrays['axis'],np.arange(3))
    with pytest.raises(ValueError,match='identity'):
        a.read_bundle(target,expected={'commit':'b'*40})
    path=target/'arrays'/'axis.npy'; path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='hash|bytes'):
        a.read_bundle(target,expected=metadata)


@pytest.mark.parametrize('name,array',[('../escape',np.ones(1)),('object',np.array([{}],dtype=object))])
def test_unsafe_array_rejected(tmp_path,name,array):
    from component_analysis import a3_direction_artifacts as a
    with pytest.raises(ValueError): a.write_bundle(tmp_path/'bundle',generic_metadata(), {name:array})


def test_full_source_closure_required():
    from component_analysis import a3_direction_artifacts as a
    # Partial Unit A deliberately cannot claim a complete production runtime.
    missing=[path for path in a.RUNTIME_FILES if not (a.ladder.REPO/path).is_file()]
    if missing:
        with pytest.raises(ValueError,match='source closure'): a.code_hashes()
    else:
        assert set(a.RUNTIME_FILES)<=set(a.code_hashes())


def row(i):
    return dict(panel='assessment',analysis_task='far_v2',source_task='mmlu',split='assessment',seed=42,
                site=['head',7,16],family='learned',axis_index='learned',operation='zero',
                instance_id=str(i),condition='MMLU',stream='clean')


def test_shard_exact_keys_completion_and_resume(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    rows=[row(0),row(1)]; keys=[a.row_key(r) for r in rows]; identity={'commit':'a'*40,'injected':True,'fixture_schema':'a3_injected_fixture_v1','numeric_profile':numeric_profile()}
    inventory={'identity':identity,'shards':[{'shard_id':'one','expected_keys':keys}]}
    a.publish_shard(tmp_path/'one',identity=identity,expected_keys=keys,rows=rows,execution={'exit_code':0})
    assert a.read_completed_shards(inventory,tmp_path,identity=identity)==rows
    with pytest.raises(ValueError,match='coverage'):
        a.publish_shard(tmp_path/'bad',identity=identity,expected_keys=keys,rows=rows[:1],execution={})
    (tmp_path/'one'/'rows.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='hash|bytes'):
        a.read_completed_shards(inventory,tmp_path,identity=identity)


@pytest.fixture
def live_fixture(tmp_path,monkeypatch):
    from component_analysis import a3_direction_artifacts as a
    from component_analysis import a3_pipeline as pipeline
    from tests.test_a3_design import freeze
    design=freeze(); design['a1_identity']['grader_sha256']=a.ladder.GRADER
    design['mmlu_validation']=[dict(instance_id='validation',source_id='source-validation',
                                  streams={'clean':{'prompt':'validation'}},donor_id='validation-donor')]
    design['parent_evidence']={'prepared_path':'fixture','selected_path':'fixture'}
    design['a1_repo_root']=str(tmp_path)
    source=tmp_path/'source'; source.write_text('frozen')
    design['historical_source_hashes']={str(source):a.common.file_hash(source)}
    design['matched_build_path']=str(source); design['matched_build_file_sha256']=a.common.file_hash(source)
    parent=dict(design['a1_identity']); selected={}
    design['parent_digests'].update(prepared=a.ladder.design._hash(parent),selected=a.ladder.design._hash(selected))
    protocol={'commit':'b'*40,'code_hashes':{},'injected_source_closure':{},'injected':True,
              'design_sha256':a.ladder.design._hash(design)}
    design['direction_protocol']=protocol; design['direction_protocol_sha256']=a.ladder.design._hash(protocol)
    monkeypatch.setattr(a.ladder,'grader_registry',lambda:{'live':'grader'})
    monkeypatch.setattr(pipeline,'load_a1_parents',lambda *args:(parent,selected,copy.deepcopy(design['parent_evidence'])))
    monkeypatch.setattr(pipeline,'_validate_parent_files',lambda *args,**kwargs:None)
    monkeypatch.setattr(pipeline,'validate_assessment_membership',lambda *args:None)
    registry=tmp_path/'registry.json'; registry.write_text(json.dumps({'schema':1,'sets':[]}))
    return design,protocol,registry,source


@pytest.mark.parametrize('protected',['validation','source-validation','validation-donor'])
def test_live_actual_collision_blocks_loader(live_fixture,protected):
    from component_analysis import a3_direction_artifacts as a
    design,protocol,registry,_=live_fixture
    calls=[]
    def guarded_load():
        a.validate_live(design,protocol,registry_paths=[str(registry)])
        calls.append('MODEL LOADER')
    result=a.validate_live(design,protocol,registry_paths=[str(registry)])
    assert result['registry_hashes'] and result['grader_registry']=={'live':'grader'}
    registry.write_text(json.dumps({'schema':1,'sets':[{'task':'mmlu','instance_ids':[protected]}]}))
    with pytest.raises(ValueError,match='overlap'): guarded_load()
    assert calls==[]


def test_live_changed_parent_sidecar_blocks(live_fixture,monkeypatch):
    from component_analysis import a3_direction_artifacts as a
    from component_analysis import a3_pipeline as pipeline
    design,protocol,registry,_=live_fixture
    original=pipeline.load_a1_parents
    def changed(*args):
        parent,selection,evidence=original(*args)
        return parent,selection,dict(evidence,completion_file_sha256='changed')
    monkeypatch.setattr(pipeline,'load_a1_parents',changed)
    with pytest.raises(ValueError,match='parent file bytes'):
        a.validate_live(design,protocol,registry_paths=[str(registry)])


def test_live_grader_registry_refresh_blocks_loader(live_fixture,monkeypatch):
    from component_analysis import a3_direction_artifacts as a
    design,protocol,registry,_=live_fixture
    def changed(): raise ValueError('changed grader registry')
    monkeypatch.setattr(a.ladder,'grader_registry',changed)
    with pytest.raises(ValueError,match='grader'):
        a.validate_live(design,protocol,registry_paths=[str(registry)])


def test_live_cached_utility_source_changed_blocks(live_fixture):
    from component_analysis import a3_direction_artifacts as a
    design,protocol,registry,source=live_fixture
    design['mmlu_validation_candidates_manifest']={'snapshot':str(source.parent),'parquet_hashes':{source.name:a.common.file_hash(source)}}
    core={k:v for k,v in design.items() if k not in ('direction_protocol','direction_protocol_sha256')}
    protocol['design_sha256']=a.ladder.design._hash(core)
    design['direction_protocol_sha256']=a.ladder.design._hash(protocol)
    # Keep historical and matched fingerprints current so only new utility cache
    # provenance can catch this change.
    source.write_text('changed')
    design['historical_source_hashes']={}
    design['matched_build_file_sha256']=a.common.file_hash(source)
    core={k:v for k,v in design.items() if k not in ('direction_protocol','direction_protocol_sha256')}
    protocol['design_sha256']=a.ladder.design._hash(core)
    design['direction_protocol_sha256']=a.ladder.design._hash(protocol)
    with pytest.raises(ValueError,match='utility source'):
        a.validate_live(design,protocol,registry_paths=[str(registry)])


def test_shard_injected_never_production_final(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    with pytest.raises(ValueError,match='injected'):
        a.validate_final_identity({'injected':True},final=True)


def test_complete_bundle_symlink_and_extra_bytes_rejected(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    target=tmp_path/'bundle'; a.write_bundle(target,generic_metadata(), {'axis':np.ones(3)})
    (target/'extra').write_text('unknown')
    with pytest.raises(ValueError,match='hash'): a.read_bundle(target,expected={})
    (target/'extra').unlink(); original=target/'arrays'/'axis.npy'
    copied=tmp_path/'array.npy'; copied.write_bytes(original.read_bytes())
    original.unlink(); original.symlink_to(copied)
    with pytest.raises(ValueError,match='symlink'): a.read_bundle(target,expected={})


def numeric_profile():
    return dict(padded_width=32,physical_batch_size=2,axis_tile_size=1,dtype='bfloat16',backend='native',
                model='fixture',model_revision='a'*40,source_sha256='c'*64)


def test_capture_bundle_requires_exact_numeric_profile(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata()
    a.write_bundle(tmp_path/'chunk',metadata,{'head':np.ones((2,4),dtype=np.float32)})
    # Omitting expected padding geometry is not a valid cache read.
    with pytest.raises(ValueError,match='profile|scientific|schema'):
        a.read_bundle(tmp_path/'chunk',expected={'kind':'a3_readout_chunk'})
    changed=copy.deepcopy(metadata); changed['identity']['numeric_profile']['padded_width']=64
    with pytest.raises(ValueError,match='identity|profile'):
        a.read_bundle(tmp_path/'chunk',expected=changed)


def test_capture_bundle_missing_or_partial_profile_blocks(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    for index,profile in enumerate((None,{'padded_width':32},dict(numeric_profile(),axis_tile_size=0))):
        metadata=scientific_metadata()
        if profile is None: del metadata['identity']['numeric_profile']
        else: metadata['identity']['numeric_profile']=profile
        with pytest.raises(ValueError,match='profile|scientific identity'):
            a.write_bundle(tmp_path/str(index),metadata,{'head':np.ones(2)})


def test_shard_missing_profile_rejected_before_publication(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    with pytest.raises(ValueError,match='profile|scientific identity'):
        a.publish_shard(tmp_path/'shard',identity={'commit':'a'*40},expected_keys=[a.row_key(row(0))],
                        rows=[row(0)],execution={})
    assert not (tmp_path/'shard').exists()


def _bind_cache_manifest(live_fixture,snapshot,relative,digest):
    from component_analysis import a3_direction_artifacts as a
    design,protocol,registry,_=live_fixture
    design['mmlu_validation_candidates_manifest']={'snapshot':str(snapshot),'parquet_hashes':{relative:digest}}
    core={k:v for k,v in design.items() if k not in ('direction_protocol','direction_protocol_sha256')}
    protocol['design_sha256']=a.ladder.design._hash(core)
    design['direction_protocol_sha256']=a.ladder.design._hash(protocol)
    return a.validate_live(design,protocol,registry_paths=[str(registry)])


def test_actual_frozen_hf_mmlu_blob_symlink_passes(live_fixture):
    from pathlib import Path
    from component_analysis import a3_direction_artifacts as a
    snapshot=Path('/work/nvme/beto/swong2/hub/datasets--cais--mmlu/snapshots/c30699e8356da336a370243923dbaf21066bb9fe')
    relative='all/test-00000-of-00001.parquet'
    assert (snapshot/relative).is_symlink()
    assert _bind_cache_manifest(live_fixture,snapshot,relative,a.common.file_hash(snapshot/relative))['injected']


@pytest.mark.parametrize('damage',['valid','traversal','absolute','arbitrary','other_repo','bad_hash','blob_dir_symlink'])
def test_hf_cache_lexical_containment_and_trusted_blob(live_fixture,tmp_path,damage):
    from component_analysis import a3_direction_artifacts as a
    repo=tmp_path/'datasets--cais--mmlu'; snapshot=repo/'snapshots'/('a'*40)
    (snapshot/'all').mkdir(parents=True)
    blobs=repo/'blobs'; blobs.mkdir(); blob=blobs/('b'*64); blob.write_text('frozen parquet bytes')
    relative='all/test.parquet'; source=snapshot/relative; source.symlink_to(blob)
    digest=a.common.file_hash(blob)
    if damage=='traversal': relative='../../blobs/'+blob.name
    elif damage=='absolute': relative=str(blob)
    elif damage in ('arbitrary','other_repo'):
        target=tmp_path/('arbitrary' if damage=='arbitrary' else 'datasets--other--data/blobs/'+blob.name)
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(blob.read_bytes())
        source.unlink(); source.symlink_to(target)
    elif damage=='bad_hash': digest='0'*64
    elif damage=='blob_dir_symlink':
        target=tmp_path/'external'; blobs.rename(target); blobs.symlink_to(target,target_is_directory=True)
    if damage=='valid': assert _bind_cache_manifest(live_fixture,snapshot,relative,digest)['injected']
    else:
        with pytest.raises(ValueError,match='utility source'):
            _bind_cache_manifest(live_fixture,snapshot,relative,digest)


def test_review83_profile_only_lineage_reproduction_rejected(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    metadata={'kind':'a3_readout_chunk','commit':'a'*40,'design_sha256':'b'*64,'numeric_profile':numeric_profile()}
    with pytest.raises(ValueError,match='scientific|schema|identity'):
        a.write_bundle(tmp_path/'bundle',metadata,{'head':np.ones(2)})


def test_review83_profile_free_fit_reproduction_rejected(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    with pytest.raises(ValueError,match='scientific|schema|identity'):
        a.write_bundle(tmp_path/'fit',{'kind':'a3_direction_fit','commit':'a'*40,'injected':False},{'axis':np.ones(2)})


@pytest.mark.parametrize('kind',['axis','fit','a3_direction_fit_alias','a3_direction_probe','a3_direction_axes','unknown'])
def test_scientific_alias_cannot_bypass_lineage(tmp_path,kind):
    from component_analysis import a3_direction_artifacts as a
    with pytest.raises(ValueError,match='scientific|schema|identity'):
        a.write_bundle(tmp_path/kind,{'kind':kind,'injected':False},{'axis':np.ones(2)})


def scientific_metadata():
    from component_analysis import a3_direction_artifacts as a
    closure={p:'c'*64 for p in set(a.RUNTIME_FILES)|set(a.ladder.code_hashes())}
    profile=numeric_profile(); profile['source_sha256']=a.ladder.design._hash(closure)
    identity=dict(analysis_split='train',injected=True,commit='a'*40,code_hashes=closure,
        a1_identity=dict(commit='b'*40,model='fixture',model_revision='a'*40,tokenizer_revision='d'*40,
                         tokenizer_identity={'vocab_sha256':'e'*64},grader_sha256='f'*64,source_hashes={'parent':'1'*64}),
        parent_evidence=dict(prepared_path='/frozen/design.json',selected_path='/frozen/selected.json',completion_path='/frozen/selection_run_manifest.json',
                             prepared_file_sha256='2'*64,selected_file_sha256='3'*64,completion_file_sha256='4'*64,completion={'kind':'selection'}),
        design_sha256='5'*64,protocol_sha256='6'*64,matched_source_hashes={'matched':'7'*64},
        ordered_ids=['id0','id1'],streams=['clean'],conditions=['D'],sites=[['head',7,16]],
        row_identity_sha256='8'*64,grader_sha256='f'*64,model='fixture',model_revision='a'*40,
        tokenizer_revision='d'*40,tokenizer_identity={'vocab_sha256':'e'*64},numeric_profile=profile,capture_lineage=[])
    return dict(schema_version=1,kind='a3_readout_chunk',split='train',injected=True,identity=identity)


def test_scientific_bundle_complete_expected_identity_required(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata(); target=tmp_path/'capture'
    a.write_bundle(target,metadata,{'head':np.ones(2)})
    assert a.read_bundle(target,expected=metadata)[0]==metadata
    for expected in ({},{'numeric_profile':metadata['identity']['numeric_profile']},
                     {'identity':{'numeric_profile':metadata['identity']['numeric_profile']}},
                     {k:v for k,v in metadata.items() if k!='split'}):
        with pytest.raises(ValueError,match='identity|scientific|schema'):
            a.read_bundle(target,expected=expected)


@pytest.mark.parametrize('field',list(scientific_metadata()['identity']))
def test_scientific_identity_omission_rejected(tmp_path,field):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata(); del metadata['identity'][field]
    with pytest.raises(ValueError,match='identity|scientific|schema'):
        a.write_bundle(tmp_path/'capture',metadata,{'head':np.ones(2)})


@pytest.mark.parametrize('field',['prepared_file_sha256','selected_file_sha256','completion_file_sha256','completion'])
def test_parent_sidecar_identity_omission_rejected(tmp_path,field):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata(); del metadata['identity']['parent_evidence'][field]
    with pytest.raises(ValueError,match='identity|scientific|schema'):
        a.write_bundle(tmp_path/'capture',metadata,{'head':np.ones(2)})


@pytest.mark.parametrize('kind',['a3_direction_fit','a3_direction_probe','a3_direction_axes','a3_direction_selection'])
def test_derived_scientific_cache_inherits_capture_identity(tmp_path,kind):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata(); target=tmp_path/'capture'
    a.write_bundle(target,metadata,{'head':np.ones(2)})
    derived=copy.deepcopy(metadata); derived['kind']=kind
    with pytest.raises(ValueError,match='capture lineage'):
        a.write_bundle(tmp_path/'missing',derived,{'axis':np.ones(2)})
    reference=a.capture_reference(target,expected=metadata)
    derived['identity']['capture_lineage']=[reference]
    a.write_bundle(tmp_path/'fit',derived,{'axis':np.ones(2)})
    assert a.read_bundle(tmp_path/'fit',expected=derived)[0]==derived
    changed=copy.deepcopy(derived); changed['identity']['numeric_profile']['padded_width']=64
    with pytest.raises(ValueError,match='capture lineage'):
        a.write_bundle(tmp_path/'wrong-profile',changed,{'axis':np.ones(2)})


def test_scientific_closure_and_model_profile_consistency(tmp_path):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata(); metadata['identity']['code_hashes'].pop(a.RUNTIME_FILES[-1])
    with pytest.raises(ValueError,match='closure|scientific identity'):
        a.write_bundle(tmp_path/'incomplete',metadata,{'head':np.ones(2)})
    metadata=scientific_metadata(); metadata['identity']['numeric_profile']['model_revision']='9'*40
    with pytest.raises(ValueError,match='profile|scientific identity'):
        a.write_bundle(tmp_path/'model',metadata,{'head':np.ones(2)})


def generic_metadata():
    return dict(schema_version=1,kind='a3_injected_fixture',injected=True)


def test_production_shard_requires_complete_scientific_identity(tmp_path,monkeypatch):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata(); metadata.update(split='assessment',injected=False)
    metadata['identity']['injected']=False
    closure=copy.deepcopy(metadata['identity']['code_hashes'])
    monkeypatch.setattr(a,'code_hashes',lambda:closure)
    identity=metadata['identity']; identity.update(analysis_split='assessment',ordered_ids=['0','1'],conditions=['MMLU'])
    a.write_bundle(tmp_path/'capture',metadata,{'head':np.ones(2)})
    identity['capture_lineage']=[a.capture_reference(tmp_path/'capture',expected=metadata)]
    rows=[row(0),row(1)]; keys=[a.row_key(r) for r in rows]
    a.publish_shard(tmp_path/'one',identity=identity,expected_keys=keys,rows=rows,execution={'exit_code':0})
    assert a.read_completed_shards({'identity':identity,'shards':[{'shard_id':'one','expected_keys':keys}]},
                                    tmp_path,identity=identity)==rows
    for expected in ({},{'numeric_profile':identity['numeric_profile']}):
        with pytest.raises(ValueError,match='identity|scientific|schema'):
            a.read_completed_shards({'shards':[{'shard_id':'one','expected_keys':keys}]},tmp_path,identity=expected)


@pytest.mark.parametrize('field',['schema_version','kind','split','injected'])
def test_scientific_outer_schema_omission_rejected(tmp_path,field):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata(); del metadata[field]
    with pytest.raises(ValueError,match='identity|scientific|schema'):
        a.write_bundle(tmp_path/'capture',metadata,{'head':np.ones(2)})


def test_scientific_production_stale_source_closure_blocks(tmp_path,monkeypatch):
    from component_analysis import a3_direction_artifacts as a
    metadata=scientific_metadata(); metadata['injected']=False; metadata['identity']['injected']=False
    monkeypatch.setattr(a,'code_hashes',lambda:{'different_source':'0'*64})
    with pytest.raises(ValueError,match='closure'):
        a.write_bundle(tmp_path/'stale',metadata,{'head':np.ones(2)})
