"""Process-local source proof boundaries, using actual file/protection validators."""
import copy
import json
import os
from pathlib import Path
import pickle
import shutil
from types import SimpleNamespace

import pytest


def setup_case(tmp_path, monkeypatch, *, extra_registry=()):
    from component_analysis import a3_source_validation as s
    from component_analysis import a3_direction_runtime as authority, ladder_pipeline as ladder
    from dataset import user_inversion_pipeline as common
    runtime=tmp_path/'runtime';primary=tmp_path/'primary'
    original=Path(__file__).resolve().parents[1]
    for root in (runtime,primary):
        (root/'docs/research').mkdir(parents=True)
        (root/'docs/research/held_out.json').write_text(json.dumps({'schema':1,'sets':[]}))
        (root/'docs/research/directions.json').write_text(json.dumps({'directions':[{'id':'specificity-ladder','frozen_grader_sha256':ladder.GRADER}]}))
    for rel in ['evaluation/benchmark_eval.py']+[str(p.relative_to(original)) for p in (original/'evaluation/benchmarks').glob('*.py')]:
        target=runtime/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original/rel,target)
    monkeypatch.setattr(common,'PRIMARY_REGISTRY',str(primary/'docs/research/held_out.json'))
    monkeypatch.setattr(common,'REPO',runtime);monkeypatch.setattr(ladder,'REPO',runtime);monkeypatch.setattr(ladder,'PRIMARY',primary)
    design=dict(access_rows={'far_v2':[{'instance_id':'recipient','source_reference':{'instance_id':'nested-donor'}}]},
        donor_ids={'far_v2':['declared-donor']},utility={'ioi':[{'instance_id':'utility','donor':{'source_id':'utility-donor'}}], 'mmlu_maps':[{'donor_id':'map-donor'}]},
        ioi_validation=[{'source_id':'validation-source'}],mmlu_validation=[])
    prepared={'kind':'fixture','identity':{'commit':'a'*40},'empty':[]}
    design_path=tmp_path/'design.json';ladder.write_artifact(design_path,design)
    prepared_path=tmp_path/'prepared';authority.publish_object(prepared_path,prepared)
    static=tmp_path/'static';static.write_bytes(b'original')
    calls=[]
    def validate(owned):
        calls.append('semantic')
        assert owned['design']==design and owned['prepared']==prepared
        return {'commit':'a'*40,'protocol_sha256':'b'*64,'injected':False}, {'far_v2':[{'instance_id':'bank','source_recipient':{'donor_id':'bank-nested'}}]}
    def build(**kwargs):
        return s.build_state(owner=kwargs.pop('owner','fixture'),originals={'design':design,'prepared':prepared},
            artifacts={'design':('artifact',design_path),'prepared':('object',prepared_path)},
            dependencies=lambda owned:([static],[],[]),semantic=kwargs.pop('semantic',validate),
            registry_paths=list(extra_registry),scope={'commit':'a'*40},**kwargs)
    return SimpleNamespace(s=s,runtime=runtime,primary=primary,design=design,prepared=prepared,design_path=design_path,
        prepared_path=prepared_path,static=static,calls=calls,build=build,extra=list(extra_registry))


def refresh(case,state):
    return state.refresh(owner='fixture',bound_inputs={'design':case.design,'prepared':case.prepared},
        registry_paths=case.extra,scope={'commit':'a'*40})


@pytest.mark.parametrize('raw',[{},[],{'nested':[{'empty':[]}]}])
def test_source_views_seal_empty_and_nested_values_and_deepcopy_thaws(raw):
    from component_analysis import a3_source_validation as s
    view=s.freeze(raw)
    for action in (lambda:view.__init__(),lambda:setattr(view,'_seal',None),lambda:delattr(view,'_seal')):
        with pytest.raises((TypeError,ValueError)):action()
    assert not hasattr(view,'__dict__')
    if isinstance(view,dict):
        for action in (lambda:view.update(x=1),lambda:view.clear(),lambda:view.__setitem__('x',1),lambda:view.__ior__({'x':1})):
            with pytest.raises(TypeError):action()
    else:
        for action in (lambda:view.append(1),lambda:view.extend([]),lambda:view.__setitem__(slice(None),[]),lambda:view.__iadd__([]),lambda:view.__imul__(0)):
            with pytest.raises(TypeError):action()
    mutable=copy.deepcopy(view);assert type(mutable) is type(raw) and mutable==raw
    if isinstance(mutable,dict):mutable['new']=[]
    else:mutable.append({})
    assert mutable!=view
    if raw=={'nested':[{'empty':[]}]}:
        mutable['nested'][0]['empty'].append('copy only')
        assert view['nested'][0]['empty']==[]
        assert type(mutable['nested']) is list and type(mutable['nested'][0]) is dict


def test_raw_unsealed_and_subclass_source_views_cannot_be_trusted():
    from component_analysis import a3_source_validation as s
    good=s.freeze({});raw=dict.__new__(type(good))
    with pytest.raises((ValueError,TypeError)):s.freeze(raw)
    with pytest.raises((ValueError,TypeError)):type(good)({})
    class Untrusted(dict):pass
    with pytest.raises((ValueError,TypeError)):s.freeze(Untrusted())
    raw_list=list.__new__(type(s.freeze([])))
    with pytest.raises((ValueError,TypeError)):s.freeze(raw_list)


def test_context_retains_validated_owned_snapshot_and_fresh_evidence(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);state=c.build();first=refresh(c,state);second=refresh(c,state)
    assert c.calls==['semantic']
    assert first==second and first is not second
    first['registry_hashes'].clear();assert refresh(c,state)['registry_hashes']
    stats=state.stats();stats['roots']=[];assert type(state.stats()['roots']) is int
    assert state.stats()['retained_bytes']>0 and state.stats()['refreshes']==3
    with pytest.raises(TypeError):pickle.dumps(state)
    with pytest.raises((TypeError,ValueError)):type(state)()
    unsealed=object.__new__(type(state))
    with pytest.raises((TypeError,ValueError)):
        refresh(c,unsealed)
    monkeypatch.setattr(os,'getpid',lambda:-1)
    with pytest.raises(ValueError,match='process'):refresh(c,state)


@pytest.mark.parametrize('mutation',['outer','nested','owned'])
def test_mutation_during_semantic_validation_cannot_enter_minted_source(tmp_path,monkeypatch,mutation):
    c=setup_case(tmp_path,monkeypatch)
    def mutate(owned):
        if mutation=='outer':c.prepared['empty']=[]
        elif mutation=='nested':c.design['access_rows']['far_v2'][0]['instance_id']='unvalidated'
        else:owned['design']['access_rows']['far_v2'][0]['instance_id']='unvalidated'
        return {},{}
    with pytest.raises((ValueError,TypeError)):c.build(semantic=mutate)


@pytest.mark.parametrize('damage',['bytes','marker','child','outer','scope','owner'])
def test_static_artifact_and_input_scope_changes_fail_closed(tmp_path,monkeypatch,damage):
    c=setup_case(tmp_path,monkeypatch);state=c.build()
    if damage=='bytes':
        stamp=c.static.stat().st_mtime_ns;c.static.write_bytes(b'modified');os.utime(c.static,ns=(stamp,stamp))
    elif damage=='marker':(c.prepared_path/'COMPLETE.json').unlink()
    elif damage=='child':(c.prepared_path/'unexpected').write_text('x')
    elif damage=='outer':c.prepared['empty']=[]
    elif damage=='scope':
        with pytest.raises(ValueError):state.refresh(owner='fixture',bound_inputs={'prepared':c.prepared},registry_paths=[],scope={'commit':'x'})
        return
    else:
        with pytest.raises(ValueError):state.refresh(owner='wrong',bound_inputs={'prepared':c.prepared},registry_paths=[],scope={'commit':'a'*40})
        return
    with pytest.raises(ValueError):refresh(c,state)


@pytest.mark.parametrize('kind',['leaf','ancestor'])
def test_static_same_bytes_link_retargets_reject(tmp_path,monkeypatch,kind):
    c=setup_case(tmp_path,monkeypatch)
    a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir();(a/'file').write_text('same');(b/'file').write_text('same')
    link=tmp_path/'link';link.symlink_to(a if kind=='ancestor' else a/'file')
    path=link/'file' if kind=='ancestor' else link
    state=c.s.build_state(owner='fixture',originals={'design':c.design,'prepared':c.prepared},
        artifacts={'design':('artifact',c.design_path),'prepared':('object',c.prepared_path)},
        dependencies=lambda owned:([path],[],[]),semantic=lambda owned:({},{}),registry_paths=[],scope={'commit':'a'*40})
    link.unlink();link.symlink_to(b if kind=='ancestor' else b/'file')
    with pytest.raises(ValueError):refresh(c,state)


def test_exact_id_union_matches_original_base_and_bank_expansions(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch)
    from component_analysis import a3_design, a3_mask_pipeline as mask
    from dataset import user_inversion_pipeline as common
    collected=[];actual=common.check_registry
    def inspect(args,contexts):
        collected.append({t:{r['instance_id'] for split in args.splits for r in v['rows']['D'][split]} for t,v in contexts.items()})
        return actual(args,contexts)
    monkeypatch.setattr(common,'check_registry',inspect)
    a3_design.validate_access(c.design,[])
    parent={'rows':{'far_v2':{'H':[{'instance_id':'bank','source_recipient':{'donor_id':'bank-nested'}}]}}}
    mask._protect_bank_sources(c.design,parent,{'far_v2':{'ids':['bank']}},[])
    state=c.build();refresh(c,state)
    assert collected[0]['far_v2']=={'recipient','nested-donor','declared-donor'}
    assert collected[1]['far_v2']==collected[-1]['far_v2']==collected[0]['far_v2']|{'bank','bank-nested'}
    assert collected[0]['ioi']==collected[-1]['ioi']=={'utility','utility-donor','validation-source'}
    assert collected[0]['mmlu']==collected[-1]['mmlu']=={'map-donor'}


def test_current_registry_atomic_updates_new_sets_and_new_link_attacks(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);state=c.build();registry=c.primary/'docs/research/held_out.json'
    replacement=registry.with_suffix('.new');replacement.write_text(json.dumps({'schema':1,'sets':[{'ids':['unrelated']}]}));replacement.replace(registry)
    refresh(c,state)
    data=c.primary/'new-ids.json';data.write_text(json.dumps(['unrelated']))
    import hashlib
    def use_file():
        registry.write_text(json.dumps({'schema':1,'sets':[{'path':'new-ids.json','sha256':hashlib.sha256(data.read_bytes()).hexdigest(),'n':1}]}))
    use_file();refresh(c,state)
    moved=c.primary/'same-ids.json';moved.write_bytes(data.read_bytes());data.unlink();data.symlink_to(moved)
    with pytest.raises(ValueError,match='provenance'):refresh(c,state)


def test_new_file_protected_overlap_and_grader_changes_still_fail(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);state=c.build();registry=c.primary/'docs/research/held_out.json'
    registry.write_text(json.dumps({'schema':1,'sets':[{'ids':['bank-nested']}]}))
    with pytest.raises(ValueError,match='overlap'):refresh(c,state)
    registry.write_text(json.dumps({'schema':1,'sets':[]}))
    grader=c.primary/'docs/research/directions.json';grader.write_text(json.dumps({'directions':[{'id':'specificity-ladder','frozen_grader_sha256':'wrong'}]}))
    with pytest.raises(ValueError,match='grader'):refresh(c,state)


@pytest.mark.parametrize('pathkind',['default','explicit'])
def test_mutable_registry_lexical_provenance_and_relative_cwd(tmp_path,monkeypatch,pathkind):
    c=setup_case(tmp_path,monkeypatch)
    if pathkind=='default':
        registry=c.runtime/'docs/research/held_out.json';target=tmp_path/'target.json';target.write_bytes(registry.read_bytes());registry.unlink();registry.symlink_to(target)
        state=c.build();other=tmp_path/'other.json';other.write_bytes(target.read_bytes());registry.unlink();registry.symlink_to(other)
        with pytest.raises(ValueError,match='provenance'):refresh(c,state)
    else:
        relative=tmp_path/'relative.json';relative.write_text(json.dumps({'schema':1,'sets':[]}));monkeypatch.chdir(tmp_path);c.extra.append('relative.json')
        state=c.s.build_state(owner='fixture',originals={'design':c.design,'prepared':c.prepared},artifacts={'design':('artifact',c.design_path),'prepared':('object',c.prepared_path)},dependencies=lambda owned:([c.static],[],[]),semantic=lambda owned:({},{}),registry_paths=c.extra,scope={'commit':'a'*40})
        monkeypatch.chdir(c.runtime)
        with pytest.raises(ValueError,match='registry scope'):refresh(c,state)


def test_missing_static_source_appearance_and_glob_change_invalidate(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);missing=tmp_path/'missing/receipt.json';watch=tmp_path/'watch';watch.mkdir();(watch/'source.py').write_text('a')
    state=c.s.build_state(owner='fixture',originals={'design':c.design,'prepared':c.prepared},artifacts={'design':('artifact',c.design_path),'prepared':('object',c.prepared_path)},dependencies=lambda owned:([c.static],[missing],[(watch,'*.py')]),semantic=lambda owned:({},{}),registry_paths=[],scope={'commit':'a'*40})
    refresh(c,state);missing.parent.mkdir();missing.write_text('{}')
    with pytest.raises(ValueError):refresh(c,state)


def test_static_absence_and_glob_are_rechecked_across_mint(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);missing=tmp_path/'absent.json'
    def mutation(owned):missing.write_text('{}');return {},{}
    with pytest.raises(ValueError):
        c.s.build_state(owner='fixture',originals={'design':c.design,'prepared':c.prepared},artifacts={'design':('artifact',c.design_path),'prepared':('object',c.prepared_path)},
            dependencies=lambda owned:([c.static],[missing],[]),semantic=mutation,registry_paths=[],scope={'commit':'a'*40})


@pytest.mark.parametrize('damage',['overlap','count','hash','escape'])
def test_actual_new_file_set_checks_remain_authoritative(tmp_path,monkeypatch,damage):
    c=setup_case(tmp_path,monkeypatch);state=c.build();registry=c.primary/'docs/research/held_out.json'
    import hashlib
    path=c.primary/'set.json';path.write_text(json.dumps(['bank-nested' if damage=='overlap' else 'unrelated']))
    entry={'path':'set.json','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'n':1}
    if damage=='count':entry['n']=2
    if damage=='hash':entry['sha256']='0'*64
    if damage=='escape':entry['path']='../outside.json'
    registry.write_text(json.dumps({'schema':1,'sets':[entry]}))
    with pytest.raises(ValueError):refresh(c,state)


def test_owned_snapshot_is_matched_to_actual_artifact_before_semantics(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);c.design['access_rows']['far_v2'][0]['instance_id']='not-authenticated'
    with pytest.raises(ValueError,match='actual artifact'):c.build()
    assert c.calls==[]


def test_proof_retains_no_initializer_callback_closure(tmp_path,monkeypatch):
    import gc,weakref
    c=setup_case(tmp_path,monkeypatch)
    class ParentPayload:pass
    payload=ParentPayload();reference=weakref.ref(payload)
    def make_callback(value):
        def callback(owned):assert value is not None;return {},{}
        return callback
    callback=make_callback(payload);state=c.build(semantic=callback)
    del payload,callback;gc.collect();assert reference() is None
    assert state.stats()['retained_bytes']>0


@pytest.mark.parametrize('owner',['mask','edge'])
def test_generic_proof_cannot_impersonate_an_owner_validator(tmp_path,monkeypatch,owner):
    c=setup_case(tmp_path,monkeypatch);state=c.build(owner=owner)
    from component_analysis import a3_mask_pipeline as mask,a3_edge_pipeline as edge
    module=mask if owner=='mask' else edge
    with pytest.raises(ValueError):module._source_startup_seconds(0.,SimpleNamespace(**{'_'+owner+'_source_context':state}))


def test_registry_discovery_binds_the_same_bytes_as_current_checker(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);state=c.build()
    from dataset import user_inversion_pipeline as common
    import hashlib
    registry=c.primary/'docs/research/held_out.json';data=c.primary/'new-set.json';data.write_text(json.dumps(['unrelated']))
    added={'schema':1,'sets':[{'path':'new-set.json','sha256':hashlib.sha256(data.read_bytes()).hexdigest(),'n':1}]}
    read=common.read_json;once=[True]
    def changing(path):
        value=read(path)
        if Path(path)==registry and once[0]:
            once[0]=False;registry.write_text(json.dumps(added))
        return value
    monkeypatch.setattr(common,'read_json',changing)
    with pytest.raises(ValueError,match='changed during refresh'):refresh(c,state)
    refresh(c,state)
    other=c.primary/'other.json';other.write_bytes(data.read_bytes());data.unlink();data.symlink_to(other)
    with pytest.raises(ValueError,match='provenance'):refresh(c,state)


def test_source_code_closures_include_the_new_helper():
    from component_analysis import a3_mask_pipeline as mask,a3_edge_pipeline as edge
    helper=Path(__file__).resolve().parents[1]/'component_analysis/a3_source_validation.py'
    assert str(helper) in mask.mask_code_hashes()
    assert 'component_analysis/a3_source_validation.py' in edge.code_hashes()


def test_protection_metadata_cannot_be_reinitialized_or_rerouted(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);state=c.build();protection=state._protection
    with pytest.raises(TypeError):protection.__init__(protection.contexts,[])
    with pytest.raises(TypeError):protection.contexts={}
    from dataset import user_inversion_pipeline as common
    other=tmp_path/'other.json';other.write_text(json.dumps({'schema':1,'sets':[]}));monkeypatch.setattr(common,'PRIMARY_REGISTRY',str(other))
    with pytest.raises(ValueError,match='default'):refresh(c,state)


@pytest.mark.parametrize('body',['[]','null','{"schema":1,"sets":null}'])
def test_malformed_current_registry_fails_with_validation_error(tmp_path,monkeypatch,body):
    c=setup_case(tmp_path,monkeypatch);state=c.build();(c.primary/'docs/research/held_out.json').write_text(body)
    with pytest.raises(ValueError):refresh(c,state)


def test_mutable_diagnostic_counters_cannot_change_charged_initialization(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);state=c.build();before=c.s.startup_seconds(0.,state)
    state._stats['initialization_seconds']=0.
    assert c.s.startup_seconds(0.,state)==before and before>0


def test_new30_closure_covers_missing_receipt_first_missing_link_and_escape(tmp_path,monkeypatch):
    from component_analysis import a3_source_validation as s
    actual=Path;study=tmp_path/'study';study.mkdir()
    marker='/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_studies/selective-deception/study'
    monkeypatch.setattr(s,'Path',lambda value:study if str(value)==marker else actual(value))
    receipt=study/'sparse-optimization-v4/comparison/selection-receipt.json'
    assert s.new30_dependencies()==([],[receipt])
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({'masks':[{'label':'new-allW30','head_list':{'path':'selective-deception/heads.json'},'source_proposal':{k+'_path':'selective-deception/'+k+'.json' for k in ('export','manifest','run_identity')}}]}))
    paths,missing=s.new30_dependencies();assert paths==[receipt] and missing==[study/'heads.json']
    (study/'heads.json').write_text('{}');paths,missing=s.new30_dependencies();assert missing==[study/'export.json']
    for name in ('export','manifest','run_identity'):(study/(name+'.json')).write_text('{}')
    paths,missing=s.new30_dependencies();assert len(paths)==5 and not missing
    (study/'heads.json').unlink();outside=tmp_path/'outside.json';outside.write_text('{}');(study/'heads.json').symlink_to(outside)
    with pytest.raises(ValueError,match='escaped'):s.new30_dependencies()


def test_dependency_discovery_keeps_parent_sidecar_and_lexical_input_aliases(tmp_path,monkeypatch):
    from component_analysis import a3_source_validation as s,a3_pipeline
    import hashlib
    root=tmp_path/'runtime';root.mkdir();a1=tmp_path/'a1';a1.mkdir();target=tmp_path/'data';target.mkdir();(target/'file.json').write_text('{}');(a1/'data').symlink_to(target)
    snapshot=tmp_path/'snapshot';snapshot.mkdir();parquet=snapshot/'test.parquet';parquet.write_bytes(b'fixture parquet')
    evidence=dict(prepared_path=str(tmp_path/'parent.json'),selected_path=str(tmp_path/'selection.json'),completion_path=str(tmp_path/'completion.json'))
    parent={'source_hashes':{'data/file.json':'h'},'selection_hashes':{'selection-source.json':'h'},'code_hashes':{'code.py':'h'}}
    monkeypatch.setattr(a3_pipeline,'load_a1_parents',lambda *a:(parent,{},evidence))
    d=dict(parent_evidence=evidence,a1_repo_root=str(a1),direction_protocol={'code_hashes':{'direction.py':'h'}},historical_source_hashes={str(tmp_path/'history.csv'):'h'},matched_build_path=str(tmp_path/'build.json'),
        utility={},mmlu_validation_candidates_manifest={'snapshot':str(snapshot),'parquet_hashes':{'test.parquet':hashlib.sha256(parquet.read_bytes()).hexdigest()}})
    paths,missing,watch=s.source_dependencies(d,root=root,owner_paths=[tmp_path/'bundle'])
    assert set(map(str,paths))==set(evidence.values())|{str(a1/'data/file.json'),str(a1/'selection-source.json'),str(root/'code.py'),str(root/'direction.py'),str(tmp_path/'history.csv'),str(tmp_path/'build.json'),str(parquet),str(tmp_path/'bundle')}
    assert not missing and watch==[(root/'component_analysis','a3_direction_*.py')]


@pytest.mark.parametrize('damage',['code','new_glob'])
def test_current_grader_code_and_glob_membership_are_not_cached(tmp_path,monkeypatch,damage):
    c=setup_case(tmp_path,monkeypatch);state=c.build()
    path=c.runtime/('evaluation/benchmark_eval.py' if damage=='code' else 'evaluation/benchmarks/new_grader.py')
    with path.open('a') as handle:handle.write('\n# changed grader\n')
    with pytest.raises(ValueError,match='grader|immutable referenced|source closure'):refresh(c,state)


def test_charged_initialization_includes_context_construction(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);ticks=[0.];constructor=c.s._SourceState.__init__
    monkeypatch.setattr(c.s,'_clock',lambda:ticks[0])
    def constructing(self,**kwargs):constructor(self,**kwargs);ticks[0]+=7.
    monkeypatch.setattr(c.s._SourceState,'__init__',constructing)
    state=c.build();assert c.s.startup_seconds(0.,state)==7.


def test_validation_only_payload_is_released_before_returned_rss_sample(tmp_path,monkeypatch):
    import weakref
    c=setup_case(tmp_path,monkeypatch);reference=[None]
    class Payload:pass
    class ExtraRows(dict):pass
    def semantic(owned):
        rows=ExtraRows();rows.payload=Payload();reference[0]=weakref.ref(rows.payload)
        return {},rows
    monkeypatch.setattr(c.s,'_rss_bytes',lambda:100 if reference[0] is not None and reference[0]() is not None else 10)
    state=c.build(semantic=semantic)
    assert state.stats()['rss_after_bytes']==10


def test_static_link_target_ancestor_replacement_is_not_hidden_by_same_resolution(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);target=tmp_path/'target';target.mkdir();(target/'file').write_text('same')
    middle=tmp_path/'middle';middle.symlink_to(target);leaf=tmp_path/'leaf';leaf.symlink_to(middle/'file')
    state=c.s.build_state(owner='fixture',originals={'design':c.design,'prepared':c.prepared},artifacts={'design':('artifact',c.design_path),'prepared':('object',c.prepared_path)},
        dependencies=lambda owned:([leaf],[],[]),semantic=lambda owned:({},{}),registry_paths=[],scope={'commit':'a'*40})
    middle.unlink();middle.symlink_to(target)
    with pytest.raises(ValueError):refresh(c,state)


def test_review_b1_dependency_discovery_cannot_rebind_a_validated_envelope(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch)
    from component_analysis import a3_direction_artifacts as artifacts
    def replace_envelope(owned):
        changed=copy.deepcopy(c.prepared);changed['empty']=['not the retained source']
        (c.prepared_path/'payload.json').write_text(json.dumps(changed))
        (c.prepared_path/'COMPLETE.json').unlink();artifacts._finish(c.prepared_path)
        return [c.static],[],[]
    with pytest.raises(ValueError):
        c.s.build_state(owner='fixture',originals={'design':c.design,'prepared':c.prepared},artifacts={'design':('artifact',c.design_path),'prepared':('object',c.prepared_path)},
            dependencies=replace_envelope,semantic=lambda owned:({},{}),registry_paths=[],scope={'commit':'a'*40})


def test_review_b2_actual_grader_same_byte_external_link_is_not_a_cache_hit(tmp_path,monkeypatch):
    c=setup_case(tmp_path,monkeypatch);state=c.build()
    grader=c.runtime/'evaluation/benchmark_eval.py';outside=tmp_path/'outside-grader.py';outside.write_bytes(grader.read_bytes());grader.unlink();grader.symlink_to(outside)
    with pytest.raises(ValueError):refresh(c,state)
