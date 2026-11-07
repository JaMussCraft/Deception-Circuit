import importlib.util, json, copy, os
from pathlib import Path
import pytest
R=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-runtime-caae47195503/runtime')
spec=importlib.util.spec_from_file_location('owner_source_fixtures',R/'tests/test_a3_source_validation.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def test_prepared_envelope_replaced_after_first_read_before_witness(tmp_path,monkeypatch):
    c=f.setup_case(tmp_path,monkeypatch)
    from component_analysis import a3_direction_runtime as a,a3_direction_artifacts as artifacts
    def dependencies(owned):
        changed=copy.deepcopy(c.prepared);changed['empty']=['never semantically validated']
        (c.prepared_path/'payload.json').write_text(json.dumps(changed))
        (c.prepared_path/'COMPLETE.json').unlink();artifacts._finish(c.prepared_path)
        return [c.static],[],[]
    with pytest.raises(ValueError):
        state=c.s.build_state(owner='fixture',originals={'design':c.design,'prepared':c.prepared},artifacts={'design':('artifact',c.design_path),'prepared':('object',c.prepared_path)},dependencies=dependencies,semantic=lambda owned:({},{}),registry_paths=[],scope={'commit':'a'*40})
        assert state.view('prepared')!=a.read_object(c.prepared_path)
        f.refresh(c,state)

def test_current_grader_same_bytes_symlink_redirect_rejected(tmp_path,monkeypatch):
    c=f.setup_case(tmp_path,monkeypatch);state=c.build()
    path=c.runtime/'evaluation/benchmark_eval.py';target=tmp_path/'same-grader.py';target.write_bytes(path.read_bytes());path.unlink();path.symlink_to(target)
    with pytest.raises(ValueError):f.refresh(c,state)

@pytest.mark.parametrize('raw',[{},[],{'x':[{'y':[]}]}])
def test_mutation_and_copy_controls(raw):
    from component_analysis import a3_source_validation as s
    v=s.freeze(raw)
    with pytest.raises(TypeError):v.__init__()
    with pytest.raises(TypeError):v._seal=None
    with pytest.raises(TypeError):del v._seal
    w=copy.deepcopy(v);assert w==v and w is not v
    if isinstance(w,dict):w['new']=[]
    else:w.append({})
    assert w!=v
    assert json.loads(json.dumps(v))==raw

def test_real_registry_updates_and_static_mutation_controls(tmp_path,monkeypatch):
    c=f.setup_case(tmp_path,monkeypatch);state=c.build()
    registry=c.primary/'docs/research/held_out.json';temp=registry.with_suffix('.new');temp.write_text(json.dumps({'schema':1,'sets':[{'ids':['unrelated']}]}));temp.replace(registry)
    evidence=f.refresh(c,state);evidence['registry_hashes'].clear();assert f.refresh(c,state)['registry_hashes']
    stamp=c.static.stat().st_mtime_ns;c.static.write_bytes(b'modified');os.utime(c.static,ns=(stamp,stamp))
    with pytest.raises(ValueError):f.refresh(c,state)
