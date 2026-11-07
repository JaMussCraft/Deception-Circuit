"""Synthetic CPU contracts; no empirical deception efficacy is tested."""
import pytest
import torch
from component_analysis import a3_directions as core


def cohort():
    d = torch.tensor([[[1., 0.], [3., 0.]], [[4., 2.], [6., 2.]], [[8., 1.], [10., 1.]]])
    return d, torch.zeros_like(d), torch.ones_like(d), torch.tensor([[2., 0.], [0., 1.], [0., 0.]])


def fit(seed=2):
    return core.fit_direction(*cohort(), seed=seed, cluster_ids=['a','b','b'], instance_ids=['0','1','2'])


def test_bootstrap_retains_every_member_and_weights_streams_and_ids():
    result = fit()
    # Seed 2 draws b,a: all three members retained with equal id weight.
    assert result['cluster_draws'] == ['b', 'a']
    assert torch.allclose(result['id_weights'], torch.full((3,), 1/3))
    assert result['expanded_n'] == 3 and result['unique_n'] == 3
    assert result['effective_n'] == pytest.approx(3)
    expected = torch.tensor([32/3, 1., 0.])
    assert torch.allclose(result['v'], expected / expected.norm())
    assert result['raw_norm'] == pytest.approx(expected.norm().item())
    twice = fit(seed=0)  # b,b: the two b members both repeat; never truncate to N.
    assert twice['cluster_draws'] == ['b','b']
    assert twice['expanded_n'] == 4 and twice['unique_n'] == 2
    assert torch.equal(twice['id_weights'], torch.tensor([0., .5, .5]))


def test_svd_cutoff_pseudoinverse_and_nulls_stay_in_attainable_image():
    w = torch.diag(torch.tensor([1., 2e-6, 1e-6, 5e-7]))
    geom = core.image_geometry(w)
    assert geom['rank'] == 2
    assert torch.allclose(geom['pinv'], torch.diag(torch.tensor([1., 5e5, 0., 0.])))
    axes = core.random_image_directions(w, n=199, seed=42)
    assert axes.shape == (199,4)
    assert torch.allclose(axes.norm(dim=-1), torch.ones(199), atol=2e-7)
    assert torch.equal(axes[:,2:], torch.zeros(199,2))
    assert torch.equal(axes, core.random_image_directions(w, n=199, seed=42))
    g = torch.Generator().manual_seed(10042)
    expected = torch.randn(199,2,generator=g)
    expected /= expected.norm(dim=-1,keepdim=True)
    assert torch.equal(axes[:,:2], expected)


def test_head_coordinate_rotation_preserves_residual_patch():
    d,i,h,w = cohort()
    q = torch.tensor([[.6,-.8],[.8,.6]])
    a = fit()
    b = core.fit_direction(d@q,i@q,h@q,w@q,seed=2,cluster_ids=['a','b','b'],instance_ids=['0','1','2'])
    assert torch.allclose(a['v'],b['v'],atol=2e-6)
    z, donor = d[:2], h[:2]
    x = core.direction_replacement(z,donor,a,mode='interchange',positions=torch.tensor([1,0]))
    y = core.direction_replacement(z@q,donor@q,b,mode='interchange',positions=torch.tensor([1,0]))
    assert torch.allclose(x@w.T,y@(w@q).T,atol=4e-6)


def test_exact_subspace_patch_center_removal_steering_and_padding():
    d = torch.tensor([[[1.,0.],[3.,0.]], [[1.,0.],[3.,0.]]])
    w = torch.tensor([[2.,0.],[0.,1.],[0.,0.]])
    axis = core.fit_direction(d,torch.zeros_like(d),torch.tensor([[[0.,4.],[2.,4.]],[[0.,4.],[2.,4.]]]),w,seed=1,cluster_ids=['a','a'],instance_ids=['0','1'])
    z = torch.tensor([[[9.,7.],[10.,8.],[99.,99.]],[[5.,6.],[88.,88.],[77.,77.]]])
    donor = torch.zeros_like(z)
    mask = torch.tensor([[False,True,False],[True,False,False]])
    patched = core.direction_replacement(z,donor,axis,mode='interchange',positions=mask)
    assert torch.equal(patched[...,1],z[...,1])
    assert torch.equal(patched[...,0],torch.tensor([[9.,0.,99.],[0.,88.,77.]]))
    centered = core.direction_replacement(z,donor,axis,mode='remove',positions=mask)
    assert centered[0,1,0] == 1
    assert centered[0,1,1] == 8
    plus = core.direction_replacement(z,donor,axis,mode='steer_positive',positions=mask)
    minus = core.direction_replacement(z,donor,axis,mode='steer_negative',positions=mask)
    assert plus[0,1,0] == 11 and minus[0,1,0] == 9
    assert torch.equal(core.direction_replacement(z,z,axis,mode='interchange',positions=mask),z)
    assert torch.equal(core.direction_replacement(z,donor,axis,mode='interchange',positions=torch.zeros_like(mask)),z)
    diag = core.perturbation_diagnostics(z,patched,axis,positions=mask)
    assert torch.allclose(diag['residual_norm'],torch.tensor([20.,10.]))
    assert axis['projected_variance'] == 4


@pytest.mark.parametrize('bad', ['zero','nan','shape','counts','duplicate','clusters'])
def test_fit_rejects_unstable_or_unpaired_inputs(bad):
    d,i,h,w=cohort(); ids=['0','1','2']; clusters=['a','b','b']
    if bad=='zero': d=i.clone()
    if bad=='nan': d[0,0,0]=float('nan')
    if bad=='shape': w=w.T
    if bad=='counts': i=i[:2]
    if bad=='duplicate': ids=['0','0','2']
    if bad=='clusters': clusters=['a','b']
    with pytest.raises(ValueError): core.fit_direction(d,i,h,w,seed=2,cluster_ids=clusters,instance_ids=ids)


def test_invalid_geometry_and_intervention_inputs_rejected():
    for w in [torch.zeros(3,2),torch.ones(2),torch.tensor([[float('inf')]])]:
        with pytest.raises(ValueError): core.random_image_directions(w,n=3,seed=1)
    d,i,_,_=cohort()
    for positions in [torch.tensor([20,0,0]), torch.ones(3,2), torch.tensor([-1,0,0])]:
        with pytest.raises(ValueError): core.direction_replacement(d,i,fit(),mode='interchange',positions=positions)
    with pytest.raises(ValueError): core.direction_replacement(d,i,fit(),mode='unknown',positions=torch.ones(3,2,dtype=torch.bool))


def test_validation_only_gate_first_site_selection_and_lexical_ties():
    rows=[dict(split='validation',site=s,seed=42,D_fraction=d,I_fraction=i,point_pass=p) for s,d,i,p in [('b',.8,.1,True),('a',.8,.15,True),('c',1.,0.,False)]]
    selected=core.select_direction(rows,sites=['a','b','c'],seed=42)
    assert selected['site']=='a' and not selected['validation_failure']
    for r in rows: r['point_pass']=False
    assert core.select_direction(rows,sites=['a','b','c'],seed=42)['site']=='c'
    rows[0]['split']='test'
    with pytest.raises(ValueError): core.select_direction(rows,sites=['a','b','c'],seed=42)
    with pytest.raises(ValueError): core.select_direction(rows[1:],sites=['a','b','c'],seed=42)


def test_nuisance_cosine_and_ridge_probe_train_only_standardization():
    nuisance=core.fit_nuisance_direction(*cohort(),seed=2,cluster_ids=['a','b','b'],instance_ids=['0','1','2'])
    assert nuisance['kind']=='neutral_frame'
    assert core.direction_cosine(nuisance,fit())==pytest.approx(1.)
    x=torch.tensor([[1.,50.],[2.,50.],[-1.,50.],[-2.,50.]])
    labels=torch.tensor([1.,1.,-1.,-1.])
    probe=core.fit_ridge_probe(x,labels)
    assert core.probe_balanced_accuracy(probe,x,labels)==1
    assert probe['scale'][1]==1 and torch.equal(probe['center'],torch.tensor([0.,50.]))
    assert core.probe_balanced_accuracy(probe,torch.tensor([[100.,50.],[-100.,50.]]),torch.tensor([1.,-1.]))==1
    with pytest.raises(ValueError): core.fit_ridge_probe(x,torch.ones(4))
    with pytest.raises(ValueError): core.direction_cosine({'v':torch.zeros(3)},fit())


def test_null_axis_receives_own_h_variance_and_pullback():
    _,_,h,w=cohort()
    null=core.prepare_image_direction(w,torch.tensor([0.,1.,0.]),h,id_weights=torch.tensor([.2,.3,.5]))
    assert torch.equal(null['pullback'],torch.tensor([0.,1.]))
    assert null['projected_variance']==0
    with pytest.raises(ValueError): core.prepare_image_direction(w,torch.tensor([0.,0.,1.]),h,id_weights=torch.tensor([.2,.3,.5]))
    with pytest.raises(ValueError): core.prepare_image_direction(w,torch.tensor([0.,1.,0.]),h,id_weights=torch.tensor([1.,1.,1.]))


def test_finite_inputs_with_overflowed_fit_statistics_are_rejected():
    x=torch.full((2,2),1e30)
    with pytest.raises(ValueError):
        core.fit_direction(x,torch.zeros_like(x),torch.zeros_like(x),torch.eye(2),seed=0,cluster_ids=['a','a'],instance_ids=['0','1'])


def test_predictive_role_axis_can_be_causally_inert_on_biased_toy_readout():
    # Coordinate 0 drives the readout; coordinate 1 is correlated role metadata.
    d=torch.tensor([[1.,10.],[2.,20.]])
    i=-d; h=torch.zeros_like(d)
    role=core.prepare_image_direction(torch.eye(2),torch.tensor([0.,1.]),h,id_weights=torch.tensor([.5,.5]))
    probe=core.fit_ridge_probe(d[:,1:].repeat(2,1)*torch.tensor([[1.],[1.],[-1.],[-1.]]),torch.tensor([1.,1.,-1.,-1.]))
    assert core.probe_balanced_accuracy(probe,torch.tensor([[5.],[-5.]]),torch.tensor([1.,-1.]))==1
    patched=core.direction_replacement(d[:,None,:],i[:,None,:],role,mode='interchange',positions=torch.tensor([0,0]))
    assert torch.equal(patched[:,0,0],d[:,0])
    assert torch.equal(patched[:,0,1],i[:,1])


def test_tiny_llama_native_replay_and_adjacent_head_isolation():
    from transformers import LlamaConfig, LlamaForCausalLM
    config=LlamaConfig(hidden_size=16,intermediate_size=32,num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=1,vocab_size=31,max_position_embeddings=32,attn_implementation='eager')
    with torch.random.fork_rng():
        torch.manual_seed(9)
        model=LlamaForCausalLM(config).eval()
    ids=torch.tensor([[1,2,3,0],[4,5,0,0]])
    attention_mask=torch.tensor([[1,1,1,0],[1,1,0,0]])
    projection=model.model.layers[0].self_attn.o_proj
    captures=[]
    def capture(module,args): captures.append(args[0].detach().clone())
    handle=projection.register_forward_pre_hook(capture)
    try:
        with torch.no_grad(): base=model(input_ids=ids,attention_mask=attention_mask).logits
    finally: handle.remove()
    z=captures[0][...,:8]; donor=z+1
    w=projection.weight[:,:8].detach()
    direction=core.fit_direction(z[:,0],torch.zeros_like(z[:,0]),z[:,1],w,seed=0,cluster_ids=['a','a'],instance_ids=['0','1'])
    positions=torch.tensor([2,1])
    self_replay=core.direction_replacement(z,z,direction,mode='interchange',positions=positions)
    replacement=core.direction_replacement(z,donor,direction,mode='interchange',positions=positions)
    seen=[]
    def replay(value):
        def patch(module,args):
            intact=args[0]; edited=intact.clone(); edited[...,:8]=value
            seen.append((intact.detach().clone(),edited.detach().clone()))
            return (edited,)
        handle=projection.register_forward_pre_hook(patch)
        try:
            with torch.no_grad(): return model(input_ids=ids,attention_mask=attention_mask).logits
        finally: handle.remove()
    logits=replay(self_replay)
    error=float((logits-base).abs().max())
    print('tiny_native_replay_max_abs_error=',error)
    assert error <= 1e-5
    changed=replay(replacement)
    assert not torch.equal(changed,base)
    before,after=seen[-1]
    assert torch.equal(before[...,8:],after[...,8:])
    mask=torch.tensor([[False,False,True,False],[False,True,False,False]])
    assert torch.equal(before[~mask],after[~mask])
    assert not projection._forward_pre_hooks


def test_tiny_llama_direction_replays_through_existing_inference_hooks():
    import nnsight
    if nnsight.__version__ != '0.7.0':
        pytest.skip('existing inference hooks require pinned nnsight 0.7.0')
    from transformers import LlamaConfig, LlamaForCausalLM
    from component_analysis import hooks
    with torch.random.fork_rng():
        torch.manual_seed(19)
        model=nnsight.NNsight(LlamaForCausalLM(LlamaConfig(hidden_size=16,intermediate_size=32,num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=1,vocab_size=31,max_position_embeddings=32,attn_implementation='eager')).eval())
    ids=torch.tensor([[1,2,3,0],[4,5,0,0]])
    mask=torch.tensor([[1,1,1,0],[1,1,0,0]])
    key=('head',0,0); neighbor=('head',0,1)
    intact=hooks.capture_forward(model,ids,mask,components=[key,neighbor])
    z=intact.outputs[key]
    w=hooks.o_proj_weight(model,0)[:,:8].detach().cpu()
    axis=core.fit_direction(z[:,0],torch.zeros_like(z[:,0]),z[:,1],w,seed=0,cluster_ids=['a','a'],instance_ids=['0','1'])
    positions=mask.sum(-1)-1
    replacement=core.direction_replacement(z,z,axis,mode='interchange',positions=positions)
    replay=hooks.replace_forward(model,ids,mask,replacements={key:replacement})
    error=float((replay-intact.logits).abs().max())
    print('existing_inference_replay_max_abs_error=',error)
    assert error<=1e-5
    changed=core.direction_replacement(z,z+1,axis,mode='interchange',positions=positions)
    under=hooks.capture_forward(model,ids,mask,components=[key,neighbor],replacements={key:changed})
    assert torch.equal(under.outputs[neighbor],intact.outputs[neighbor])
    assert not torch.equal(under.logits,intact.logits)
    assert torch.allclose(under.outputs[key],changed,atol=1e-6)


def test_probe_rejects_finite_train_data_with_overflowed_statistics():
    x=torch.tensor([[3e38],[3e38],[1e38],[1e38]])
    assert torch.isfinite(x).all()
    with pytest.raises(ValueError,match='finite|overflow'):
        core.fit_ridge_probe(x,torch.tensor([1.,1.,-1.,-1.]))


def test_probe_rejects_overflowed_scores_from_finite_inputs_and_fields():
    x=torch.tensor([[1.],[-1.]])
    labels=torch.tensor([1.,-1.])
    probe=core.fit_ridge_probe(x,labels)
    probe['coefficient']=torch.tensor([3e38])
    with pytest.raises(ValueError,match='finite|overflow'):
        core.probe_balanced_accuracy(probe,x*2,labels)


def test_probe_rejects_overflowed_evaluation_standardization():
    x=torch.tensor([[1.],[-1.]])
    labels=torch.tensor([1.,-1.])
    probe=core.fit_ridge_probe(x,labels)
    probe['center']=torch.tensor([-3e38])
    with pytest.raises(ValueError,match='finite|overflow'):
        core.probe_balanced_accuracy(probe,torch.tensor([[3e38],[1e38]]),labels)


@pytest.mark.parametrize('field,value', [
    ('center',torch.tensor([float('nan')])),
    ('scale',torch.tensor([float('inf')])),
    ('scale',torch.tensor([0.])),
    ('scale',torch.tensor([-1.])),
    ('coefficient',torch.tensor([float('nan')])),
    ('coefficient',torch.tensor([[1.]])),
    ('center',torch.tensor([1.,2.])),
    ('intercept',float('nan')),
    ('intercept',float('inf')),
    ('regularization',float('nan')),
])
def test_probe_rejects_invalid_fitted_fields(field,value):
    x=torch.tensor([[1.],[-1.]])
    labels=torch.tensor([1.,-1.])
    probe=core.fit_ridge_probe(x,labels)
    probe[field]=value
    with pytest.raises(ValueError): core.probe_balanced_accuracy(probe,x,labels)


def test_probe_predictions_preserve_balanced_accuracy_ties_and_guards():
    from component_analysis import a3_directions as d
    import torch
    probe=dict(center=torch.zeros(2),scale=torch.ones(2),coefficient=torch.tensor([1.,0.]),intercept=0.,regularization=1.)
    x=torch.tensor([[0.,0.],[-1.,2.],[1.,3.],[-2.,0.]])
    y=torch.tensor([1.,-1.,-1.,1.])
    assert d.probe_predictions(probe,x).tolist()==[1.,-1.,1.,-1.]
    assert d.probe_balanced_accuracy(probe,x,y)==.5
    for changed in (dict(probe,scale=torch.zeros(2)),dict(probe,coefficient=torch.tensor([float('inf'),0.])),dict(probe,regularization=2.)):
        with pytest.raises(ValueError):d.probe_predictions(changed,x)
    with pytest.raises(ValueError):d.probe_predictions(probe,torch.full((2,2),float('inf')))
    with pytest.raises(ValueError):d.probe_predictions(dict(probe,coefficient=torch.full((2,),1e38)),torch.full((2,2),1e38))
