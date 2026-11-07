"""B1 regressions: bank shape/provenance and linked-artifact intake only."""
import copy
import importlib.util
from pathlib import Path
import pytest
import torch

_spec=importlib.util.spec_from_file_location('edge_bank_fixtures',Path(__file__).with_name('test_a3_edge_pipeline.py'))
f=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(f)
p=f.p


def bank_case():
    design,model=f.complete_design_and_model()
    graph=p.prepare_graph(design,'far_v2',f.geometry())
    prepared={'graphs':{'far_v2':graph},'bank_sources':p.ancestral_bank_sources(design)}
    identity={'injected':True}
    sources=sorted({tuple(e['sender']) for e in graph['edges']})
    source=prepared['bank_sources']['far_v2']
    key=dict(identity=identity,task='far_v2',sources=[list(s) for s in sources],source_sha256=source['source_sha256'])
    good=p.h_mean_bank(model,design,'far_v2',graph['edges'],guard=lambda:None,bank_sources=source)
    body=dict(kind='a3_edge_H_bank',key=key,values=[dict(site=list(s),value=good['values'][s].tolist()) for s in sources],provenance=copy.deepcopy(good['provenance']))
    if 'contract' in good:body['contract']=copy.deepcopy(good['contract'])
    return design,model,prepared,identity,graph,good,body


@pytest.mark.parametrize('defect',[
    'scalar','matrix','duplicate','missing','extra','boolean_key','out_of_bounds',
    'nan','overflow','false_source','reordered_ids','wrong_task','streams',
    'weighting','representation','native_dtype','padded_width','base','profile',
])
def test_B1_cache_rejects_malformed_bank_before_native_intervention(tmp_path,defect):
    d,m,prepared,identity,g,good,body=bank_case()
    if defect=='scalar':body['values'][0]['value']=[.125]
    elif defect=='matrix':body['values'][0]['value']=[body['values'][0]['value']]
    elif defect=='duplicate':body['values'].append(copy.deepcopy(body['values'][0]))
    elif defect=='missing':body['values'].pop()
    elif defect=='extra':body['values'].append(dict(site=['mlp',0,0],value=[0.]*8))
    elif defect=='boolean_key':body['values'][0]['site'][1]=False
    elif defect=='out_of_bounds':body['values'][0]['site'][1]=m.config.num_hidden_layers
    elif defect=='nan':
        # In-memory validator must also reject NaN before JSON publication.
        bad=copy.deepcopy(good);bad['values'][tuple(body['values'][0]['site'])][0]=float('nan')
        batch=p._utility_batch(d['utility']['mmlu'][0],'clean',physical_width=p.source_width(d,'mmlu'))
        with pytest.raises(ValueError):p._utility_floor(m,batch,[e for e in g['edges'] if e['position']=='assistant_readout'][:1],'h_mean',bad)
        return
    elif defect=='overflow':body['values'][0]['value'][0]=1e100
    elif defect=='false_source':body['provenance']['source_sha256']='0'*64
    elif defect=='reordered_ids':body['provenance']['source_ids'].reverse()
    elif defect=='wrong_task':body['provenance']['task']='ser_v2'
    elif defect=='streams':body['provenance']['streams']=['clean']
    elif defect=='weighting':body['provenance']['weighting']='equal ID readout'
    elif defect=='representation':body['provenance']['representation']='pre-o_proj head coordinates'
    elif defect=='native_dtype':body['provenance']['native_dtype']='torch.float16'
    elif defect=='padded_width':body['provenance']['padded_width']+=1
    elif defect=='base':body.setdefault('contract',{})['base_design_sha256']='0'*64
    elif defect=='profile':body.setdefault('contract',{})['numeric_profile']={'backend':'fabricated'}
    p.authority.publish_object(tmp_path/p.digest(body['key']),body)
    with pytest.raises(ValueError):p.cached_h_bank(m,d,prepared,'far_v2',identity=identity,root=tmp_path,guard=lambda:None)


def test_B1_floor_requires_independent_contract_before_native_forward(monkeypatch):
    d,m,prepared,identity,g,good,body=bank_case()
    batch=p._utility_batch(d['utility']['mmlu'][0],'clean',physical_width=p.source_width(d,'mmlu'))
    from component_analysis import a3_native
    monkeypatch.setattr(a3_native,'native_forward',lambda *a,**k:pytest.fail('bank was not validated before forward'))
    with pytest.raises(ValueError):p._utility_floor(m,batch,[e for e in g['edges'] if e['position']=='assistant_readout'][:1],'h_mean',good)


def test_B1_complete_panel_requires_linked_bank_at_resume_and_summary(tmp_path,monkeypatch):
    # The existing genuine numerical positive flow is retained; no injected
    # outcome/header substitutes for actual native bank and floor computation.
    f.test_complete_tiny_native_staged_path_reports_scientific_failure_not_missing_assay(tmp_path,monkeypatch)
    d,m=f.complete_design_and_model();prepared=p.authority.read_object(tmp_path/'prepared')
    identity=p._stage_identity(d,prepared);run=tmp_path/'run'
    panel_path=next((run/'panels').iterdir());panel=p.authority.read_object(panel_path)
    args=p.parser().parse_args(['--stage','summarize','--design','fixture','--commit','a'*40,'--work-dir',str(run),'--resume'])
    original=run/'banks';absent=run/'banks-B1-unavailable';original.rename(absent)
    try:
        with pytest.raises((ValueError,OSError)):
            p.cached_assessment_panel(m,d,prepared,'far_v2',panel['edges'],identity=identity,root=run,guard=lambda:None)
        with pytest.raises((ValueError,OSError)):p._run_summary(d,prepared,args,identity)
    finally:absent.rename(original)
    # Every link is resolved even on an otherwise complete cached report.
    result=p._run_summary(d,prepared,args,identity)
    assert result['runtime_identity']['complete'] and not result['finalized']
    missing=copy.deepcopy(panel);missing.pop('bank_reference')
    with pytest.raises(ValueError):p.validate_panel_bank(missing,d,prepared,identity)
    changed=copy.deepcopy(panel);changed['bank_reference']['files']['payload.json']['sha256']='0'*64
    with pytest.raises(ValueError):p.validate_panel_bank(changed,d,prepared,identity)
    # A freshly self-hashed foreign profile is not a valid linked bank either.
    foreign=p.authority.read_object(panel['bank_reference']['path'])
    foreign['provenance']['source_sha256']='0'*64
    p.authority.publish_object(tmp_path/'foreign-bank',foreign)
    changed['bank_reference']=p.authority.object_reference(tmp_path/'foreign-bank')
    with pytest.raises(ValueError):p.validate_panel_bank(changed,d,prepared,identity)


def test_B1_bfloat16_conversion_is_finite_before_any_native_forward(monkeypatch):
    d,m,prepared,identity,g,_,_=bank_case()
    m=m.to(torch.bfloat16);d['direction_protocol']['numeric_profile']['dtype']='torch.bfloat16'
    source=prepared['bank_sources']['far_v2']
    bank=p.h_mean_bank(m,d,'far_v2',g['edges'],guard=lambda:None,bank_sources=source)
    expected=p.h_bank_contract(d,'far_v2',model=m,prepared=prepared,bank_sources=source)
    # Finite float32, but not representable in the native BF16 clamp dtype.
    bad=copy.deepcopy(bank);site=next(iter(bad['values']))
    bad['values'][site]=torch.full((m.config.hidden_size,),3.4e38,dtype=torch.float32)
    assert torch.isfinite(bad['values'][site]).all()
    assert not torch.isfinite(bad['values'][site].to(torch.bfloat16)).all()
    from component_analysis import a3_native
    monkeypatch.setattr(a3_native,'native_forward',lambda *a,**k:pytest.fail('nonfinite native donor reached forward'))
    batch=p._utility_batch(d['utility']['mmlu'][0],'clean',physical_width=p.source_width(d,'mmlu'))
    with pytest.raises(ValueError,match='native dtype'):
        p._utility_floor(m,batch,[e for e in g['edges'] if e['position']=='assistant_readout'][:1],'h_mean',bad,bank_contract=expected)


def test_B1_projected_heads_and_MLP_use_residual_not_head_or_neuron_width():
    d,m=f.complete_design_and_model();d['tasks']['far_v2']['edge_nodes'].append(['mlp',0,0])
    graph=p.prepare_graph(d,'far_v2',f.geometry());source=p.ancestral_bank_sources(d)['far_v2']
    bank=p.h_mean_bank(m,d,'far_v2',graph['edges'],guard=lambda:None,bank_sources=source)
    expected=p.h_bank_contract(d,'far_v2',model=m,bank_sources=source)
    assert all(v.shape==(8,) for v in bank['values'].values())
    for site,width in [(('head',0,0),4),(('mlp',0,0),12)]:
        bad=copy.deepcopy(bank);bad['values'][site]=torch.zeros(width)
        with pytest.raises(ValueError,match='residual vector'):p.validate_h_bank(bad,expected)
