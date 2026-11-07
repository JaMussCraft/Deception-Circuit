import copy,json,shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
from component_analysis import a2_pipeline as a2
from component_analysis import ladder_pipeline as a1

@pytest.fixture
def context(tmp_path,monkeypatch):
    from evaluation.grader_hash import grader_files,grader_sha256
    source=a1.REPO;repo=tmp_path/'repo';primary=tmp_path/'primary';runtime_files=a2.runtime_hashes()
    for rel in sorted(set(grader_files(str(source))) | set(runtime_files)):
        dest=repo/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/rel,dest)
    assert grader_sha256(str(repo))==a1.GRADER
    row=dict(id='specificity-ladder',frozen_grader_sha256=a1.GRADER,typed=True,nested=[1,None,1.0])
    foreign=dict(id='foreign',do_not_touch=['a','a','b'],archive=['old'],frozen_grader_sha256=a1.GRADER)
    paths=[]
    for root in (primary,repo):
        p=root/'docs/research/directions.json';p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(dict(schema=1,updated='2026-11-03',global_config={'x':[1,True]},directions=[row,foreign,copy.deepcopy(foreign),dict(id='empty',do_not_touch=[])])));paths.append(p)
    monkeypatch.setattr(a1,'REPO',repo);monkeypatch.setattr(a1,'PRIMARY',primary)
    assert a2.runtime_hashes()==runtime_files
    original=a1.grader_registry;calls=[]
    def grader():calls.append(1);return original()
    monkeypatch.setattr(a1,'grader_registry',grader)
    provenance,binding=a2._observe_grader_catalogue()
    receipt=dict(grader_registry=provenance,grader_binding=binding,a1_ancestor_commit='a'*40,a2_training_execution_commit='b'*40,receipt_sha256='c'*64,comparison_sha256='d'*64,file_references={},registry_hashes={},utility_registry_hashes={},model_identity={},operations=[])
    args=SimpleNamespace(stage='bank',commit='e'*40)
    def forbidden(*args,**kwargs):raise AssertionError('model/tokenizer access')
    monkeypatch.setattr(a1.common,'load_tokenizer',forbidden)
    return SimpleNamespace(paths=paths,receipt=receipt,args=args,calls=calls,repo=repo,tmp=tmp_path)

def edit(path,fn):
    value=json.loads(path.read_text());fn(value);path.write_text(json.dumps(value))

@pytest.mark.parametrize('route',[0,1])
@pytest.mark.parametrize('mutation',['own_bool_int','own_int_float','top_int_float','global_nested','duplicate_row_remove','duplicate_path_remove','path_order','foreign_pin_remove','foreign_archive_remove','new_protected','unknown_foreign'])
def test_manifest_direct_enforces_semantics(context,route,mutation):
    c=context
    def change(v):
        if mutation=='own_bool_int':v['directions'][0]['typed']=1
        elif mutation=='own_int_float':v['directions'][0]['nested'][0]=1.0
        elif mutation=='top_int_float':v['schema']=1.0
        elif mutation=='global_nested':v['global_config']['x'][1]=1
        elif mutation=='duplicate_row_remove':v['directions'].pop(2)
        elif mutation=='duplicate_path_remove':v['directions'][1]['do_not_touch'].pop(0)
        elif mutation=='path_order':v['directions'][1]['do_not_touch'].reverse()
        elif mutation=='foreign_pin_remove':del v['directions'][1]['frozen_grader_sha256']
        elif mutation=='foreign_archive_remove':del v['directions'][1]['archive']
        elif mutation=='new_protected':v['directions'].append(dict(id='new',legacy_scratch=['new']))
        else:v['directions'][3]['unknown']=False
    edit(c.paths[route],change)
    before=len(c.calls)
    with pytest.raises(ValueError):a2._manifest(c.args,c.receipt,dict(counts={}))
    assert len(c.calls)>before

@pytest.mark.parametrize('route',[0,1])
def test_stage_read_allowed_metadata_keeps_all_bytes(context,route):
    c=context;payload=dict(kind='independent-software',counts={})
    stage=c.tmp/'stage';a2._publish_stage(stage,'payload.json',payload,a2._manifest(c.args,c.receipt,payload))
    before={p.name:p.read_bytes() for p in stage.iterdir()};historical=copy.deepcopy(c.receipt)
    def change(v):
        v['directions'].reverse()
        for row in v['directions']:
            if row['id']!='specificity-ladder':row.update(title='new',status='done',updated='metadata')
        v['directions'].append(dict(id='newempty',do_not_touch=[],archive=[],legacy_scratch=[],frozen_grader_sha256=None))
        v['updated']='2026-11-04'
    edit(c.paths[route],change)
    assert a2.read_stage(stage,'payload.json','bank',c.args,c.receipt)==payload
    assert before=={p.name:p.read_bytes() for p in stage.iterdir()}
    assert c.receipt==historical
    assert c.receipt['grader_registry'][str(c.paths[route])]!=a1.common.file_hash(c.paths[route])
    edit(c.paths[route],lambda v:v['global_config'].update(new_authority=[]))
    with pytest.raises(ValueError):a2.read_stage(stage,'payload.json','bank',c.args,c.receipt)

@pytest.mark.parametrize('mutation',['binding_missing','route_missing','route_alias','digest_malformed','source_byte','new_glob'])
def test_manifest_provenance_and_real_grader(context,mutation):
    c=context;r=copy.deepcopy(c.receipt)
    if mutation=='binding_missing':del r['grader_binding']
    elif mutation=='route_missing':r['grader_registry'].pop(next(iter(r['grader_registry'])))
    elif mutation=='route_alias':r['grader_registry'][str(c.paths[0].parent/'alias.json')]=r['grader_registry'].pop(str(c.paths[0]))
    elif mutation=='digest_malformed':r['grader_registry'][str(c.paths[0])]='not-a-digest'
    elif mutation=='source_byte':
        p=c.repo/'evaluation/benchmark_eval.py';p.write_text(p.read_text()+'\n# independent mutation\n')
    else:(c.repo/'evaluation/benchmarks/independent_added.py').write_text('# added grader member\n')
    with pytest.raises(ValueError):a2._manifest(c.args,r,dict(counts={}))

def test_returns_independent_copies(context):
    c=context;baseline=copy.deepcopy(c.receipt)
    provenance,binding=a2._validate_grader_catalogue(c.receipt)
    provenance.clear();next(iter(binding['routes'].values()))['own_entry']['typed']=False
    assert c.receipt==baseline
    a2._manifest(c.args,c.receipt,dict(counts={}))
