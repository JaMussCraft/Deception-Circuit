import copy
import numpy as np
import pytest
from evaluation.frozen_head_masks import heads_to_leaf_masks, validate_effective_removal, layer_matched_random
from evaluation.masks import knockout_masks, ones_like

G = dict(num_layers=2, num_heads=4, head_dim=16, hidden_size=64, intermediate_size=128)


def test_finest_complement_removes_exact_query_heads_and_no_mlp():
    masks = heads_to_leaf_masks([[0, 1], [1, 3]], G)
    keep = knockout_masks(masks, 'finest')
    for l, h in [(0, 1), (1, 3)]:
        assert (keep['attention_neurons'][str(l)].reshape(4, 16).sum(1) == np.array([0 if x == h else 16 for x in range(4)])).all()
    assert all(v.all() for k in ['mlp_hidden', 'mlp_output'] for v in keep[k].values())
    assert all(v.all() for v in keep['attention_heads'].values())


@pytest.mark.parametrize('mutation', ['partial', 'mlp', 'shape', 'missing_layer', 'head'])
def test_invalid_support_rejected(mutation):
    masks = heads_to_leaf_masks([[0, 1]], G)
    if mutation == 'partial': masks['attention_neurons']['0'][16] = 0
    if mutation == 'mlp': masks['mlp_hidden']['1'][0] = 1
    if mutation == 'shape': masks['mlp_output']['0'] = [0]
    if mutation == 'missing_layer': del masks['attention_heads']['1']
    if mutation == 'head': masks['attention_heads']['0'][2] = 1
    with pytest.raises(ValueError): validate_effective_removal(masks, [[0, 1]], G)


@pytest.mark.parametrize('heads', [[[0, 1], [0, 1]], [[True, 0]], [[0, 4]], [[2, 0]]])
def test_invalid_query_heads_rejected(heads):
    with pytest.raises(ValueError): heads_to_leaf_masks(heads, G)


def test_random_full_layer_includes_target_heads_without_rejection_sampling():
    heads = [[0, h] for h in range(4)] + [[1, 0]]
    assert layer_matched_random(heads, G) == layer_matched_random(heads[::-1], G)
    assert layer_matched_random(heads, G)[:4] == heads[:4]
    assert sum(l == 1 for l, _ in layer_matched_random(heads, G)) == 1


def test_full_consumer_and_allopen_logits_identity():
    import torch
    from analysis import apply_node_masks, open_all_gates
    from config import NodePruningConfig
    from tests.helpers import build_tiny_pair
    node = NodePruningConfig(prune_attention_blocks=True, prune_attention_heads=True,
        prune_attention_neurons=True, prune_mlp_hidden=True, prune_mlp_output=True,
        prune_mlp_blocks=False, prune_full_layers=False, prune_embedding=False)
    plain, model = build_tiny_pair(node_cfg=node)
    ids = torch.tensor([[1, 4, 7]])
    open_all_gates(model)
    with torch.no_grad(): before = model(ids).logits
    circuit = heads_to_leaf_masks([[0, 1]], G)
    apply_node_masks(model, ones_like(circuit))
    with torch.no_grad(): after = model(ids).logits
    assert torch.equal(before, after)
    apply_node_masks(model, knockout_masks(circuit, 'finest'))
    from analysis import extract_node_masks
    actual = extract_node_masks(model)
    for k, entry in knockout_masks(circuit, 'finest').items():
        if isinstance(entry, dict):
            for l, v in entry.items(): assert np.array_equal(actual[k][l], v)
        else: assert np.array_equal(actual[k], entry)


def _frozen_sources(tmp_path, monkeypatch):
    import json
    import evaluation.frozen_head_masks as f
    root = tmp_path
    study = root/'.scratch/selective-deception/sparse-optimization-v4'
    (study/'comparison').mkdir(parents=True)
    oldpath = root/'Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/active_nodes.coarse.json'
    oldpath.parent.mkdir(parents=True)
    old = [[l,h] for l in range(32) for h in range(32)][:69]
    oldpath.write_text(json.dumps(dict(active_heads={str(l):[h for x,h in old if x==l] for l in range(32)},active_mlps=list(range(32)))))
    monkeypatch.setattr(f,'OLD_D_SHA256',f.file_hash(oldpath))
    receipt=dict(finalists_frozen=True,no_test_based_selection=True,masks=[])
    for count in [23,30]:
        heads=[[l,h] for l in range(32) for h in range(32)][:count]
        hp=study/f'heads-{count}.json';hp.write_text(json.dumps(dict(removed_heads=heads)))
        r={str(l):[int([l,h] in heads) for h in range(32)] for l in range(32)}
        export=dict(removed_heads=heads,R=r,K={k:[1-v for v in values] for k,values in r.items()})
        export['export_hash']=f.digest(export)
        ep=study/f'export-{count}.json';ep.write_text(json.dumps(export))
        proposal={}
        for name in ['checkpoint','export','manifest','run_identity']:
            p=ep if name=='export' else study/f'{name}-{count}.json'
            if name!='export':p.write_text('{}')
            proposal[name+'_path']=str(p);proposal[name+'_sha256']=f.file_hash(p)
        receipt['masks'].append(dict(label=f'new-allW{count}',head_list=f.binding(hp),source_proposal=proposal))
    rp=study/'comparison/selection-receipt.json';rp.write_text(json.dumps(receipt))
    monkeypatch.setattr(f,'SELECTION_SHA256',f.file_hash(rp))
    return f,root


def test_full_frozen_binding_loader_and_ungated_old_mlp_safeguard(tmp_path,monkeypatch):
    f,root=_frozen_sources(tmp_path,monkeypatch)
    path=tmp_path/'masks.json'
    data=f.prepare_frozen_masks(root,path)
    masks=f.load_frozen_masks(path)
    assert {k:len(v['removed_heads']) for k,v in data['conditions'].items()}==dict(oldD69=69,**{'new-allW23':23,'new-allW30':30,'random30':30})
    assert all(not v.any() for m in masks.values() for k in ['mlp_hidden','mlp_output'] for v in m[k].values())


@pytest.mark.parametrize('kind',['support','binding_omission','checkpoint_bytes','random_seed','geometry'])
def test_frozen_manifest_tamper_rejected(tmp_path,monkeypatch,kind):
    import json
    f,root=_frozen_sources(tmp_path,monkeypatch)
    path=tmp_path/'masks.json';data=f.prepare_frozen_masks(root,path)
    if kind=='support':data['conditions']['new-allW30']['removed_heads'].pop()
    if kind=='binding_omission':data['source_bindings'].pop()
    if kind=='checkpoint_bytes':
        b=next(b for b in data['source_bindings'] if 'checkpoint' in b['path'])
        with open(b['path'],'a') as stream:stream.write('changed')
    if kind=='random_seed':data['conditions']['random30']['seed']=1
    if kind=='geometry':data['geometry']['num_heads']=8
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):f.load_frozen_masks(path)
