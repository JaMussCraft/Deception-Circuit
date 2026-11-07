"""Native bank replay: real tiny Llama, CPU only, without downloads."""
from dataclasses import replace

import pytest
import torch
from transformers.cache_utils import DynamicCache

from evaluation import native_interchange as ni
from tests.helpers import TINY, build_tiny_pair


@pytest.fixture(params=['eager', 'sdpa'])
def model(request):
    _, model = build_tiny_pair(seed=17, attn_implementation=request.param)
    return model


def prompt(n=5, offset=3):
    return torch.arange(offset, offset + n).unsqueeze(0)


def capture(model, ids=None, spec=None):
    return ni.capture_donor(model, prompt() if ids is None else ids,
                            spec or ni.DecodeSpec(4, ()),
                            model_identity='weights-sha:test', tokenizer_identity='tokenizer-sha:test')


def replay(model, ids, bank, keep=None, spec=None):
    return ni.generate_with_replay(model, ids,
                                  torch.ones(TINY['layers'], TINY['heads']) if keep is None else keep,
                                  bank, spec or ni.DecodeSpec(4, ()),
                                  model_identity='weights-sha:test', tokenizer_identity='tokenizer-sha:test')


def test_actual_donor_tokens_capture_and_off_by_one(model):
    seen = []
    handle = model.register_forward_pre_hook(lambda m, a, kw: seen.append(
        (kw['input_ids'].clone(), kw['corrupted_input_ids'].clone(), kw['position_ids'].clone())),
        with_kwargs=True)
    bank = capture(model)
    handle.remove()
    assert len(seen) == 4
    for t, (clean, shadow, positions) in enumerate(seen):
        assert torch.equal(clean, shadow)
        expected = prompt() if t == 0 else torch.tensor([[bank.generated_tokens[t - 1]]])
        assert torch.equal(clean, expected)
        assert positions.tolist() == ([list(range(5))] if t == 0 else [[5 + t - 1]])
    assert bank.query_count == 8  # five prompt + three forwarded continuation queries
    assert bank.termination == 'cap'
    assert ni.make_position_map(prompt(7), bank) == (-1, -1, 0, 1, 2, 3, 4)
    assert ni.make_position_map(prompt(3), bank) == (2, 3, 4)

    # Separate cached intact execution under the actual complete token sequence.
    captures = {i: [] for i in range(TINY['layers'])}
    with ni._execution(model, torch.ones(2, 4),
                       lambda module, value, site: (
                           captures[module.layer_idx].append(value.detach().cpu().clone())
                           if site == 'attn_head' else None) or value):
        cache, shadow_cache = DynamicCache(), DynamicCache()
        for t, (ids, _, pos) in enumerate(seen):
            model(input_ids=ids, corrupted_input_ids=ids, position_ids=pos,
                  attention_mask=torch.ones(1, 5 + t, dtype=torch.long),
                  past_key_values=cache, corrupted_past_key_values=shadow_cache, use_cache=True)
    for layer in captures:
        torch.testing.assert_close(bank.activations[layer], torch.cat(captures[layer], dim=1)[0], rtol=0, atol=0)


def test_all_open_identity_and_closed_content_load_bearing(model):
    a, b = capture(model), capture(model, prompt(8, 20))
    ids = prompt(7, 35)
    one = replay(model, ids, a)
    two = replay(model, ids, b)
    assert one.generated_tokens == two.generated_tokens
    torch.testing.assert_close(one.last_logits, two.last_logits, rtol=0, atol=0)
    zeros = torch.zeros(2, 4)
    closed_a, closed_b = replay(model, ids, a, zeros), replay(model, ids, b, zeros)
    assert not torch.allclose(closed_a.last_logits, closed_b.last_logits, atol=1e-6)


def test_equal_shape_fixed_continuation_matches_dual_stream(model):
    bank = capture(model)
    ids = prompt(5, 31)
    keep = torch.tensor([[1, 0, 1, 0], [0, 1, 0, 1]])
    hook = ni._ReplayHook(model, bank)
    cache, shadow_cache, direct_cache, donor_cache = [DynamicCache() for _ in range(4)]
    for t in range(4):
        clean = ids if t == 0 else torch.tensor([[40 + t]])
        donor = prompt() if t == 0 else torch.tensor([[bank.generated_tokens[t - 1]]])
        hook.set_indices(tuple(range(5)) if t == 0 else (5 + t - 1,))
        kwargs = dict(attention_mask=torch.ones(1, 5 + t, dtype=torch.long),
                      position_ids=torch.arange(5).unsqueeze(0) if t == 0 else torch.tensor([[4 + t]]),
                      use_cache=True)
        with ni._execution(model, keep, hook):
            actual = model(input_ids=clean, corrupted_input_ids=clean,
                           past_key_values=cache, corrupted_past_key_values=shadow_cache, **kwargs).logits
        with ni._execution(model, keep, None):
            expected = model(input_ids=clean, corrupted_input_ids=donor,
                             past_key_values=direct_cache, corrupted_past_key_values=donor_cache, **kwargs).logits
        torch.testing.assert_close(actual, expected, rtol=0, atol=0)


@pytest.mark.parametrize('recipient_length', [3, 8])
def test_exact_indices_and_unmatched_prefix_causality(model, recipient_length):
    a, b = capture(model), capture(model, prompt(5, 20))
    ids = prompt(recipient_length, 40)
    mapping = ni.make_position_map(ids, a)
    refs = []
    outputs = []
    for bank in [a, b]:
        hook = ni._ReplayHook(model, bank)
        hook.set_indices(mapping)
        def record(module, value, site):
            answer = hook(module, value, site)
            if site == 'attn_head':
                refs.append((bank, module.layer_idx, value.clone(), answer.clone()))
            return answer
        with ni._execution(model, torch.zeros(2, 4), record):
            out = model(input_ids=ids, corrupted_input_ids=ids,
                        attention_mask=torch.ones_like(ids), use_cache=True, output_hidden_states=True)
            outputs.append(out)
    for bank, layer, shadow, value in refs:
        for p, q in enumerate(mapping):
            torch.testing.assert_close(value[0, p], shadow[0, p] if q == -1 else bank.activations[layer][q], rtol=0, atol=0)
    prefix = max(0, recipient_length - 5)
    with ni._execution(model, torch.ones(2, 4), None):
        intact = model(input_ids=ids, corrupted_input_ids=ids, attention_mask=torch.ones_like(ids),
                       use_cache=True, output_hidden_states=True)
    for output in outputs:
        for layer, clean_layer in zip(output.hidden_states, intact.hidden_states):
            torch.testing.assert_close(layer[:, :prefix], clean_layer[:, :prefix], rtol=0, atol=0)
    result = replay(model, ids, a, torch.zeros(2, 4))
    assert result.prompt_map == mapping
    assert result.unmapped_prefix == prefix
    assert result.query_indices == (4, 5, 6, 7)


def test_eos_first_early_and_cap_no_extra_queries(model):
    ordinary = capture(model)
    for stop_step in [0, 1]:
        token = ordinary.generated_tokens[stop_step]
        # Tiny deterministic seed's early token differs from its first token.
        assert stop_step == 0 or token != ordinary.generated_tokens[0]
        forwarded = []
        handle = model.register_forward_pre_hook(
            lambda m, a, kw: forwarded.append(kw['input_ids'].clone()), with_kwargs=True)
        bank = capture(model, spec=ni.DecodeSpec(4, (token,)))
        handle.remove()
        assert bank.termination == 'eos'
        assert bank.query_count == 5 + stop_step
        assert len(bank.generated_tokens) == stop_step + 1
        assert len(forwarded) == len(bank.generated_tokens)
        assert all(value.shape[0] == bank.query_count for value in bank.activations)
        for t in range(1, len(forwarded)):
            assert forwarded[t].tolist() == [[bank.generated_tokens[t - 1]]]
        result = replay(model, prompt(7, 33), bank, spec=ni.DecodeSpec(6, (token,)))
        terminal = bank.query_count - 1
        expected = tuple(min(4 + t, terminal) for t in range(len(result.generated_tokens)))
        assert result.query_indices == expected
        assert result.terminal_held_steps == sum(4 + t > terminal for t in range(len(expected)))
        assert result.terminal_held_steps > 0  # target really outlives donor; holding is exercised
    with pytest.raises(ValueError, match='cap'):
        replay(model, prompt(), ordinary, spec=ni.DecodeSpec(5, ()))


def test_fail_closed_and_reuse_immutable(model, tmp_path):
    bank = capture(model)
    digest = bank.content_digest
    for length in [3, 5, 8]:
        replay(model, prompt(length, 30), bank, torch.zeros(2, 4))
    assert bank.compute_digest() == digest
    path = tmp_path / 'bank.pt'
    torch.save(bank, path)
    loaded = torch.load(path, weights_only=False)
    replay(model, prompt(), loaded)
    # Persisted banks also work with a fresh identically initialized model;
    # object IDs are only an additional same-process stale-weight guard.
    _, fresh = build_tiny_pair(seed=17, attn_implementation=model.config._attn_implementation)
    replay(fresh, prompt(), loaded)
    with pytest.raises(ValueError, match='identity'):
        ni.generate_with_replay(model, prompt(), torch.ones(2, 4), bank, ni.DecodeSpec(4, ()),
                                model_identity='wrong', tokenizer_identity='tokenizer-sha:test')
    with pytest.raises(ValueError, match='binary'):
        replay(model, prompt(), bank, torch.full((2, 4), .5))
    with pytest.raises(ValueError, match='shape'):
        replay(model, prompt(), bank, torch.ones(2, 3))
    with pytest.raises(ValueError, match='unpadded'):
        capture(model, torch.ones(2, 3, dtype=torch.long))
    hook = ni._ReplayHook(model, bank)
    with pytest.raises(ValueError, match='index'):
        hook.set_indices((bank.query_count,))
    broken = replace(bank, activations=bank.activations[:1])
    with pytest.raises(ValueError, match='site|layer'):
        replay(model, prompt(), broken)
    with torch.no_grad():
        model.lm_head.weight.add_(.01)
    with pytest.raises(ValueError, match='stale'):
        replay(model, prompt(), bank)


def test_nonhead_gates_open_and_restored_on_error(model):
    original = [g.log_alpha.clone() for g in model.modules() if hasattr(g, 'log_alpha')]
    with pytest.raises(RuntimeError, match='deliberate'):
        with ni._execution(model, torch.zeros(2, 4), None):
            heads = {id(b.attn.head_gates) for b in model.model.layers}
            for gate in model.modules():
                if hasattr(gate, 'log_alpha') and id(gate) not in heads:
                    assert torch.equal(gate(), torch.ones_like(gate()))
            raise RuntimeError('deliberate')
    after = [g.log_alpha for g in model.modules() if hasattr(g, 'log_alpha')]
    assert all(torch.equal(a, b) for a, b in zip(original, after))


def test_all_open_matches_existing_cached_engine(model):
    from types import SimpleNamespace
    from evaluation.gen_engine import generate
    bank = capture(model)
    ids = prompt(7, 23)
    actual = replay(model, ids, bank)
    ctx = SimpleNamespace(node_model=model, device='cpu', tokenizer=SimpleNamespace(pad_token_id=0))
    # Different arbitrary corrupted continuation is harmless with exactly open gates.
    corrupt = torch.cat([prompt(7, 11), prompt(4, 50)], dim=1)
    with ni._execution(model, torch.ones(2, 4), None):
        expected = generate(ctx, clean_ids=ids, corrupt_ids=corrupt, attention_mask=torch.ones_like(ids),
                            new_tokens=4, use_cache=True)
    assert actual.generated_tokens == tuple(expected[0, 7:].tolist())


def test_bank_mutation_missing_shape_and_source_binding_rejected(model):
    bank = capture(model)
    assert 'source_hashes' in bank.provenance
    bad_shape = replace(bank, activations=(bank.activations[0][:, :, :-1], bank.activations[1]))
    with pytest.raises(ValueError, match='shape'):
        replay(model, prompt(), bad_shape)
    bank.activations[0][0, 0, 0] += 1
    with pytest.raises(ValueError, match='digest'):
        replay(model, prompt(), bank)


def test_inconsistent_bank_termination_rejected_even_with_new_digest(model):
    bank = capture(model)
    broken = replace(bank, termination='eos')  # decode EOS set is empty
    object.__setattr__(broken, 'content_digest', broken.compute_digest())
    with pytest.raises(ValueError, match='termination'):
        replay(model, prompt(), broken)


def test_hook_state_restored_and_missing_forward_site_fails(model):
    sentinel = lambda module, value, site: value
    from models.llama_node import install_ablation_hook
    install_ablation_hook(model, sentinel)
    bank = capture(model)
    assert all(m._ablation_hook is sentinel for m in ni._gated_modules(model))
    replay(model, prompt(7), bank)
    assert all(m._ablation_hook is sentinel for m in ni._gated_modules(model))
    hook = ni._ReplayHook(model, bank)
    hook.set_indices((0,))
    with pytest.raises(ValueError, match='shape'):
        hook(model.model.layers[0].attn, torch.zeros(1, 2, 4, 16), 'attn_head')
