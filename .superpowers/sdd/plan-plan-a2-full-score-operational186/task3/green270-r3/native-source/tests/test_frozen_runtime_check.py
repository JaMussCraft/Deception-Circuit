import json
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from analysis import apply_node_masks, extract_node_masks
from config import NodePruningConfig
from models.llama_node import PrunableLlamaForCausalLM, apply_pruning_wrappers
from tests.helpers import tiny_config


def fixture(tmp_path, monkeypatch):
    import evaluation.frozen_runtime_check as check
    model=PrunableLlamaForCausalLM(tiny_config(attn_implementation='eager'))
    apply_pruning_wrappers(model,NodePruningConfig(prune_mlp_blocks=False))
    model.eval()
    shape=dict(num_layers=2,num_heads=4,head_dim=16,hidden_size=64,intermediate_size=128)
    def removal(head):
        masks=dict(attention_blocks=np.ones(2,dtype=np.uint8),attention_heads={},attention_neurons={},mlp_hidden={},mlp_output={})
        for layer in range(2):
            heads=np.zeros(4,dtype=np.uint8)
            if layer==0:heads[head]=1
            masks['attention_heads'][str(layer)]=heads
            masks['attention_neurons'][str(layer)]=np.repeat(heads,16)
            masks['mlp_hidden'][str(layer)]=np.zeros(128,dtype=np.uint8)
            masks['mlp_output'][str(layer)]=np.zeros(64,dtype=np.uint8)
        return masks
    masks={name:removal(i) for i,name in enumerate(['new-allW23','new-allW30','oldD69','random30'])}
    path=tmp_path/'frozen.json'
    path.write_text(json.dumps({'geometry':shape}))
    monkeypatch.setattr(check,'load_frozen_masks',lambda path:masks)
    apply_node_masks(model,masks['oldD69'])
    ctx=SimpleNamespace(node_model=model,device='cpu',out_dir=str(tmp_path),
          cli=SimpleNamespace(benchmark_frozen_masks=str(path),no_kv_cache=False,device='cpu'))
    return check,ctx,masks


def test_real_gate_support_and_same_path_full_vocab_identity_restore_state(tmp_path,monkeypatch):
    check,ctx,masks=fixture(tmp_path,monkeypatch)
    before=extract_node_masks(ctx.node_model)
    gate_parameters={name:p.detach().clone() for name,p in ctx.node_model.named_parameters() if 'log_alpha' in name}
    modes={name:module.final_mode for name,module in ctx.node_model.named_modules() if hasattr(module,'final_mode')}
    proof=check.check_frozen_runtime(ctx)
    assert proof['passed'] is True
    assert proof['logit_identity']['exact'] is True
    assert proof['logit_identity']['vocab_size']==101
    assert set(proof['states'])=={'full',*masks}
    assert proof['states']['full']['removed_query_heads']==0
    assert all(proof['states'][name]['removed_query_heads']==1 for name in masks)
    assert extract_node_masks(ctx.node_model)==before
    assert all(torch.equal(dict(ctx.node_model.named_parameters())[name],value) for name,value in gate_parameters.items())
    assert {name:module.final_mode for name,module in ctx.node_model.named_modules() if hasattr(module,'final_mode')}==modes
    assert json.loads((tmp_path/'frozen_runtime_check.json').read_text())['passed']


def test_missing_real_gate_family_fails_before_forward_and_restores(tmp_path,monkeypatch):
    check,ctx,masks=fixture(tmp_path,monkeypatch)
    ctx.node_model.model.layers[0].mlp.output_gates=None
    before=extract_node_masks(ctx.node_model)
    monkeypatch.setattr(ctx.node_model,'forward',lambda **kw:pytest.fail('must reject support before forward'))
    with pytest.raises((AssertionError,ValueError)):
        check.check_frozen_runtime(ctx)
    assert extract_node_masks(ctx.node_model)==before
    assert json.loads((tmp_path/'frozen_runtime_check.json').read_text())['passed'] is False


def test_logit_mismatch_fails_closed_and_restores(tmp_path,monkeypatch):
    check,ctx,masks=fixture(tmp_path,monkeypatch)
    before=extract_node_masks(ctx.node_model)
    original=ctx.node_model.forward
    calls=[]
    def forward(**kwargs):
        value=original(**kwargs)
        calls.append(1)
        if len(calls)==2:value.logits[:,-1,0]+=1
        return value
    monkeypatch.setattr(ctx.node_model,'forward',forward)
    with pytest.raises(AssertionError,match='logits'):
        check.check_frozen_runtime(ctx)
    assert len(calls)==2
    assert extract_node_masks(ctx.node_model)==before
    assert json.loads((tmp_path/'frozen_runtime_check.json').read_text())['passed'] is False


def test_frozen_consumer_runs_proof_before_any_judge_or_generation(tmp_path,monkeypatch):
    import evaluation.frozen_runtime_check as check
    import evaluation.benchmark_eval as benchmark
    ctx=SimpleNamespace(cli=SimpleNamespace(benchmark_frozen_masks='fixed.json',
        benchmark_fixed_cohort=None,judge_budget_ledger=None,judge_concurrency=1),
        out_dir=str(tmp_path))
    monkeypatch.setattr(benchmark,'JudgeClient',lambda **kw:pytest.fail('judge initialized before required proof'))
    def fail(ctx):
        raise AssertionError('technical proof failed')
    monkeypatch.setattr(check,'check_frozen_runtime',fail)
    with pytest.raises(AssertionError,match='technical proof failed'):
        benchmark.BenchmarkEvaluation().run(ctx)
