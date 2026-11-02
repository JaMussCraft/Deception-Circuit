"""A3 consumes A1's execution identity and full task scope."""
import pytest
from component_analysis import a3_pipeline as p
from component_analysis import ladder_pipeline as ladder


def test_missing_parent_is_closed(tmp_path):
    with pytest.raises((ValueError,FileNotFoundError)):
        p.load_a1_parents(tmp_path/'design.json',tmp_path/'selected.json')


def test_read_selection_uses_original_identity_and_retains_sidecar(tmp_path,monkeypatch):
    parent=dict(kind='prepared',tasks=['far_v2','sdr_v2','ser_v2'],commit='a'*40,model='m',model_revision='r',tokenizer_revision='t')
    selected=tmp_path/'selected.json'; sidecar=ladder.selection_manifest_path(selected)
    sidecar.write_text('{"completion":"fixture"}')
    (tmp_path/'design.json').write_text('{}'); selected.write_text('{}')
    monkeypatch.setattr(ladder,'read_artifact',lambda path:parent)
    calls=[]
    def read(args,prepared):
        calls.append(args); assert prepared is parent
        return {'kind':'selected'}
    monkeypatch.setattr(ladder,'read_selection',read)
    prepared,result,evidence=p.load_a1_parents(tmp_path/'design.json',selected)
    assert prepared is parent and result['kind']=='selected'
    assert calls[0].commit=='a'*40 and calls[0].tasks==parent['tasks']
    assert calls[0].groups==str(selected)
    assert evidence['completion']['completion']=='fixture' and evidence['completion_file_sha256']


@pytest.fixture
def completed_a1(tmp_path,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(ladder,'code_hashes',lambda:{})
    identity=dict(commit='a'*40,model='fixture',model_revision='revision',tokenizer_revision='revision')
    args=SimpleNamespace(**identity,tasks=['far_v2'],groups=str(tmp_path/'selected.json'),design=str(tmp_path/'design.json'))
    group=dict(full=[['head',0,0]],selection_evidence=dict(head_keys=[['head',0,0]],selection_ids=['selection'],clean_dla=[[1.]],corrupt_dla=[[2.]]))
    parent=dict(kind='prepared',tasks=args.tasks,injected=True,**identity,code_hashes={},source_hashes={},selection_hashes={},
                designs={'far_v2':dict(mover_selection_ids=['selection'],bank_ids=['bank'])},recorded_groups={'far':dict(members=[['head',0,0]])})
    banks={'far_v2':dict(provenance=dict(source_ids=['bank']))}
    selected=dict(kind='selected',design_sha256=ladder.design._hash(parent),groups={'far_v2':group},banks=banks,
                  group_sha256=ladder.design._hash({'far_v2':group}),bank_sha256=ladder.design._hash(banks),
                  execution_provenance=dict(**identity,device='cpu',dtype='torch.float32'),injected=True)
    ladder.write_artifact(args.design,parent); ladder.write_selection(args,parent,selected)
    return args,parent,selected


@pytest.mark.parametrize('damage',['missing','partial','stale','bytes','scope'])
def test_parent_completion_evidence_rejected_before_prepare(completed_a1,damage):
    import json
    from pathlib import Path
    args,parent,selected=completed_a1
    marker=ladder.selection_manifest_path(args.groups)
    if damage=='missing': marker.unlink()
    elif damage=='partial': marker.write_text('{"schema_version":1,"kind":"specificity_ladder_selection"}')
    elif damage=='stale':
        raw=json.loads(marker.read_text()); raw['commit']='b'*40; marker.write_text(json.dumps(raw))
    elif damage=='bytes': Path(args.groups).write_text(Path(args.groups).read_text()+' ')
    else:
        raw=json.loads(Path(args.design).read_text()); raw['payload']['tasks']=['ser_v2']; raw['sha256']=ladder.design._hash(raw['payload']); Path(args.design).write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='selection'): p.load_a1_parents(args.design,args.groups)


def test_complete_parent_real_reader(completed_a1):
    args,parent,selected=completed_a1
    actual,chosen,evidence=p.load_a1_parents(args.design,args.groups)
    assert actual==parent and chosen==selected
    assert evidence['completion']['commit']==parent['commit']


def test_semantic_twin_maps_are_builder_verified():
    class Bytes:
        def encode(self,text,add_special_tokens=False): return list(text.encode())
    def row(condition,clause):
        return dict(instance_id='same',condition=condition,split='train',pressure=clause,request_text=clause,request_id='r',
            streams={stream:dict(prompt='prefix '+clause+'<|eot_id|>tail',tokens=list(('prefix '+clause+'<|eot_id|>tail').encode()),
                layout={'role_spans':[['text',0,24]],'content_spans':[['text',0,24]]},user_request_span=[6,10]) for stream in ('clean','corrupt')})
    rows=[row('D','yes'),row('H','non'),row('I','yes'),row('user_neutral','non')]
    design={'access_rows':{'far_v2':rows}}
    maps=p.freeze_semantic_maps(design,Bytes())['far_v2']
    assert len(maps)==4 and all(m['supported'] for m in maps)
    assert all(m['recipient_condition']!='D' or m['donor_condition']=='H' for m in maps)
    rows[1]['streams']['clean']['prompt']='shifted prefix non<|eot_id|>tail'
    assert not p.freeze_semantic_maps(design,Bytes())['far_v2'][0]['supported']


def test_twin_map_validation_survives_python_optimized():
    import os
    import subprocess
    import sys
    code='''
from component_analysis.a3_pipeline import freeze_semantic_maps
class Bytes:
    def encode(self,text,add_special_tokens=False): return list(text.encode())
def row(c,p,clause):
    n=len(p)
    return dict(instance_id='id',condition=c,split='train',pressure=clause,streams={
        'clean':dict(prompt=p,tokens=list(p.encode()),layout=dict(role_spans=[['text',0,n]],content_spans=[['text',0,n]]))})
a=row('D','prefix yes<|eot_id|>tail','yes')
b=row('H','badfix non<|eot_id|>tail','non')
result=freeze_semantic_maps({'access_rows':{'far_v2':[a,b]}},Bytes())
if result['far_v2'][0]['supported']: raise RuntimeError('optimized Python accepted outside-clause changes')
'''
    result=subprocess.run([sys.executable,'-O','-c',code],capture_output=True,text=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),timeout=60)
    assert result.returncode==0,result.stderr


@pytest.fixture
def actual_matched(tmp_path,monkeypatch):
    import copy
    import json
    import datasets
    from dataset import build_twin_training as build
    task='far_v2'; splits=('train','validation','test'); conditions={'D':'D','H':'H','I':'I','I_neutral':'user_neutral'}
    loaded={}; sources={}; hashes={}; normalized={}
    for condition,canonical in conditions.items():
        directory=tmp_path/'source'/condition; directory.mkdir(parents=True)
        path=directory/'frozen.json'; path.write_text(condition)
        digest=p.common.file_hash(path); hashes[str(path)]=digest
        raw={split:[dict(instance_id=split,pressure='pressure',clean_prompt='a',corrupt_prompt='b',target='yes',distractor='no',condition=canonical)] for split in splits}
        meta=dict(path=str(directory),file_hashes={'frozen.json':digest},content_hash=build._hash({'frozen.json':digest}),row_hash=build._hash(raw))
        loaded[str(directory)]=(raw,meta); sources[condition]=meta
        normalized[canonical]=[dict(instance_id=split,split=split,condition=canonical,streams={'clean':{'prompt':'a'},'corrupt':{'prompt':'b'}}) for split in splits]
    normalized['F']=copy.deepcopy(normalized['H'])
    for row in normalized['F']: row['condition']='F'
    ids={s:[s] for s in splits}; materialized={}
    for arm,reference in [('D','H'),('I','I_neutral')]:
        directory=tmp_path/arm/task; directory.mkdir(parents=True)
        proofs={split:{split:dict(recipient_prompt_hash=build._hash('a'),reference_prompt_hash=build._hash('a'))} for split in splits}
        (directory/'dataset_config.json').write_text(json.dumps(dict(cohort='matched',fleet_ready=True,split_ids=ids,token_proofs=proofs,source_provenance={k:sources[k] for k in (arm,reference)})))
        materialized[str(directory)]={}
        for split in splits:
            source=copy.deepcopy(loaded[sources[arm]['path']][0][split][0]); neutral=copy.deepcopy(loaded[sources[reference]['path']][0][split][0])
            materialized[str(directory)][split]=[dict(source,corrupt_prompt=neutral['clean_prompt'],source_recipient=source,source_reference=neutral,
                orientation='clean',corruption_kind='neutral_twin_same_item',recipient_condition=source['condition'],
                donor_identity=dict(instance_id=split,condition=neutral['condition'],stream='clean'),token_proof=copy.deepcopy(proofs[split][split]))]
    materialized.update({path:raw for path,(raw,meta) in loaded.items()})
    monkeypatch.setattr(datasets,'load_from_disk',lambda path:materialized[path])
    monkeypatch.setattr(build,'_load',lambda path:loaded[path])
    manifest={'fleet_ready':True,'tasks':{task:dict(sources=sources,split_ids=ids,counts={s:1 for s in splits})}}
    prepared=dict(rows={task:normalized},source_hashes=hashes,tokenizer_identity={'revision':'t'},grader_sha256='g')
    return tmp_path,manifest,prepared,materialized


def test_matched_adapter_reads_actual_memberships(actual_matched):
    root,manifest,parent,materialized=actual_matched
    actual,enriched=p._matched_rows(root,manifest,parent)
    assert actual['tasks']['far_v2']['actual_split_ids']['D']==manifest['tasks']['far_v2']['split_ids']
    assert enriched['far_v2']['F'][0]['pressure_text']=='pressure'


@pytest.mark.parametrize('damage',['source_hash','prompt'])
def test_matched_adapter_rejects_stale_actual_sources(actual_matched,damage):
    root,manifest,parent,materialized=actual_matched
    if damage=='source_hash': parent['source_hashes']={}
    else: materialized[str(root/'D'/'far_v2')]['train'][0]['source_recipient']['clean_prompt']='changed'
    with pytest.raises(ValueError,match='source'): p._matched_rows(root,manifest,parent)


def test_canonical_hashes_resolve_against_explicit_parent_root(tmp_path,monkeypatch):
    parent_root=tmp_path/'repo'; parent_root.mkdir(); other=tmp_path/'elsewhere'; other.mkdir()
    monkeypatch.chdir(other)
    values={'data/source.json':'same',str(parent_root/'data/source.json'):'same'}
    assert p.canonical_source_hashes(values,a1_repo_root=parent_root)=={str(parent_root/'data/source.json'):'same'}
    assert len(values)==2
    values[str(parent_root/'data/source.json')]='conflict'
    with pytest.raises(ValueError,match='conflicting'): p.canonical_source_hashes(values,a1_repo_root=parent_root)


@pytest.mark.parametrize('field,value',[('clean_prompt','tampered'),('corrupt_prompt','tampered'),('target','tampered'),('distractor','tampered'),('orientation','corrupt'),('token_proof',{'invalid':True})])
def test_top_level_materialized_tampering_refused(actual_matched,field,value):
    root,manifest,parent,materialized=actual_matched
    materialized[str(root/'D'/'far_v2')]['train'][0][field]=value
    with pytest.raises(ValueError,match='stored|proof|metadata|recipient|prompt'): p._matched_rows(root,manifest,parent)
