"""CPU contracts for the bounded selective-removal pilot; no pretrained weights."""
import copy
import importlib

import pytest
import torch

from evaluation import selective_diagnostics as sd
from l0 import HardConcreteGate
from tests.test_selective_diagnostics import POOL, Tokenizer, record
from tests.helpers import build_tiny_pair


@pytest.fixture
def api(monkeypatch):
    module = importlib.import_module('evaluation.selective_mask')
    monkeypatch.setattr(module, 'R1_MANIFEST_HASH', 'synthetic')
    monkeypatch.setattr(module, 'R1_EXPOSURE_HASH', 'synthetic')
    return module


def stage1(records=None, stream='corrupt'):
    c = sd._preflight((records or [record(90)])[0], POOL, Tokenizer(), 512, 96)
    c['cluster_id'] = sd.content_hash(c['scenario'])
    m = {'clusters': [c], 'rows': [{'recipient': sd._endpoint(c, 'D', stream, 'original'),
                                 'donor': None}], 'donor_reference_rows': []}
    m['manifest_hash'] = sd.manifest_hash(m)
    return m


def build(api, records=None, tokenizer=None, exposed=None):
    m = exposed or stage1()
    # Patch evidence pins only in tests: production accepts the frozen r1 or a
    # root-approved unchanged-input successor, never arbitrary synthetic data.
    scenarios, _ = api._exposure(m, tokenizer or Tokenizer())
    api.R1_MANIFEST_HASH = m['manifest_hash']
    api.R1_EXPOSURE_HASH = sd.content_hash(sorted(sd.content_hash(s) for s in scenarios))
    return api.build_pilot_manifest(records or {
        'train': [record(i) for i in range(6)],
        'validation': [record(i) for i in range(10, 16)], 'test': [record(90)]},
        POOL, tokenizer or Tokenizer(), stage1_manifest=m, candidate_heads=[(0, 0), (1, 1)],
        source_metadata={'stage1_lineage': {'original_manifest_hash': m['manifest_hash'],
                                          'approved_manifest_hash': m['manifest_hash'],
                                          'root_decision': 'synthetic CPU fixture'}})


def test_actual_corrupt_exposure_flips_truth_and_excludes_whole_cluster(api):
    exposed = stage1([record(0, item_polarity=2)])
    rs = {'train': [record(i) for i in range(6)] + [record(0, variant='lab')],
          'validation': [record(i) for i in range(10, 16)], 'test': []}
    m = build(api, rs, exposed=exposed)
    assert record(0)['entity'] not in {c['scenario']['entity'] for c in m['splits']['train']['clusters']}
    excluded = [x for x in m['exclusions'] if x['reason'] == 'stage1_exposure']
    assert len(excluded) == 2
    assert m['exposed_scenarios'][0]['honest_item'] == record(0)['distractor']


def test_original_precedence_reserves_all_raw_validation_and_test_clusters(api):
    rs = {'train': [record(i) for i in range(8)],
          'validation': [record(0, variant='lab')] + [record(i) for i in range(10, 16)],
          'test': [record(1)]}
    m = build(api, rs, exposed=stage1([record(0)], 'clean'))
    assert {record(0)['entity'], record(1)['entity']}.isdisjoint(
        {c['scenario']['entity'] for c in m['splits']['train']['clusters']})
    assert any(x['source_id'] == record(0)['instance_id'] and x['reason'] == 'raw_split_precedence'
               for x in m['exclusions'])


def test_no_wrapper_replacement_or_outcome_filter(api):
    rs = {'train': [record(i) for i in range(6)] + [record(1, variant='lab')],
          'validation': [record(i) for i in range(10, 16)], 'test': []}
    a = build(api, rs)
    other = copy.deepcopy(rs)
    for rows in other.values():
        for r in rows:
            r.update(survived=False, prediction='wrong', capable=False)
    b = build(api, other)
    for split in ('train', 'validation'):
        assert a['splits'][split]['clusters'] == b['splits'][split]['clusters']
        assert a['splits'][split]['donor_map'] == b['splits'][split]['donor_map']


def test_split_local_derangement_has_no_singletons(api):
    rs = {'train': [record(i) for i in range(6)] + [record(7, variant='lab')],
          'validation': [record(i) for i in range(10, 16)], 'test': []}
    m = build(api, rs)
    assert any(x['reason'] == 'singleton_signature' for x in m['exclusions'])
    for s in m['splits'].values():
        assert set(s['donor_map']) == set(s['donor_map'].values())
        assert all(k != v for k, v in s['donor_map'].items())


def test_manifest_rejects_token_collision_truncation_or_mutation(api):
    m = build(api)
    for change in ('token', 'truncated', 'donor', 'candidate', 'scenario', 'provenance'):
        x = copy.deepcopy(m)
        c = x['splits']['train']['clusters'][0]
        if change == 'token':
            c['prompts']['original']['D']['clean']['input_ids'].pop()
        elif change == 'truncated':
            c['prompts']['original']['D']['clean']['truncated'] = True
        elif change == 'donor':
            x['splits']['train']['donor_map'][c['cluster_id']] = c['cluster_id']
        elif change == 'candidate':
            x['candidate_heads'].append([0, 1])
        elif change == 'scenario':
            c['scenario']['entity'] = 'changed'
        else:
            x['source_metadata']['new_outcome_screening'] = True
        x['manifest_hash'] = sd.manifest_hash(x)
        with pytest.raises(ValueError):
            api.validate_pilot_manifest(x)
    class CollidingTokenizer(Tokenizer):
        def encode(self, text, add_special_tokens=False):
            return super().encode(text.replace('Entity010', 'Entity000'), add_special_tokens)
    with pytest.raises(ValueError, match='intersection|collision'):
        build(api, tokenizer=CollidingTokenizer())


def loss(api, d=None, h=None, base=None, capable=None, a=None, **kwargs):
    d = torch.tensor([[1., 0., -1.]]) if d is None else d
    h = torch.tensor([[0., 1., -1.]]) if h is None else h
    base = h.detach().clone() if base is None else base
    return api.pilot_loss(d, torch.ones((len(d), 1), dtype=torch.long), h, base,
                          torch.ones(len(h), dtype=torch.long),
                          torch.ones(len(h), dtype=torch.bool) if capable is None else capable,
                          torch.tensor([2.]) if a is None else a, rho=kwargs.pop('rho', 0.), **kwargs)


def test_deceptive_mass_suppression_is_stable_and_gradient_has_correct_sign(api):
    d = torch.tensor([[1000., -1000., -1000.], [2., 1., 0.]], requires_grad=True)
    result = api.pilot_loss(d, torch.tensor([[0, 1], [0, 1]]), torch.zeros(1, 3),
                            torch.zeros(1, 3), torch.tensor([1]), torch.tensor([True]),
                            torch.tensor([2.]), rho=0.)
    assert torch.isfinite(result.total)
    result.total.backward()
    assert (d.grad[:, :2] >= 0).all() and (d.grad[:, 2] < 0).all()
    repeated = loss(api, d=d.detach().repeat(3, 1))
    assert repeated.suppression == loss(api, d=d.detach()).suppression


def test_capable_kl_ignores_initially_wrong_h_but_truth_non_degradation_does_not(api):
    base = torch.tensor([[0., 3., 0.], [3., 1., 0.]], requires_grad=True)
    h = torch.tensor([[0., 3., 0.], [4., 0., 0.]], requires_grad=True)
    result = loss(api, h=h, base=base, capable=torch.tensor([True, False]))
    assert result.capable_kl.abs() < 1e-6 and result.truth_nondegradation > 0
    result.total.backward()
    assert base.grad is None and h.grad[1, 1] < 0
    empty = loss(api, h=h, base=base, capable=torch.tensor([False, False]))
    assert empty.capable_kl == 0 and empty.n_capable == 0 and empty.n_h == 2
    repeat = loss(api, h=h.repeat(3, 1), base=base.repeat(3, 1),
                  capable=torch.tensor([True, False] * 3))
    assert torch.allclose(repeat.total, result.total)


def test_removal_penalty_is_positive_expected_count(api):
    a = torch.tensor([0., 2., -2.], requires_grad=True)
    result = loss(api, a=a, rho=.1)
    assert torch.allclose(result.expected_removed, torch.sigmoid(-a).sum())
    assert torch.allclose(result.total - loss(api, a=a).total, .1 * result.expected_removed)
    result.total.backward()
    assert (a.grad < 0).all()


def test_eligibility_is_exact_in_train_eval_and_zero_gradient():
    gate = HardConcreteGate(4)
    for bad in (torch.ones(4), torch.ones(3, dtype=torch.bool)):
        with pytest.raises(ValueError):
            gate.set_eligibility(bad)
    gate.set_eligibility(torch.tensor([True, False, False, True]))
    with torch.no_grad():
        gate.log_alpha[:] = torch.tensor([0., -1000., -1000., 0.])
    for training in (True, False):
        gate.train(training)
        assert torch.equal(gate()[1:3], torch.ones(2))
    gate.train()
    torch.manual_seed(9)
    gate().sum().backward()
    assert torch.equal(gate.log_alpha.grad[1:3], torch.zeros(2))
    assert gate.eligibility.dtype == torch.bool
    restored = HardConcreteGate(4)
    restored.set_eligibility(gate.eligibility)
    restored.load_state_dict(gate.state_dict())
    assert torch.equal(restored.eligibility, gate.eligibility)


def test_legacy_gate_without_eligibility_loads_unchanged():
    g = HardConcreteGate(4).eval()
    old = g.state_dict()
    assert 'eligibility' not in old
    g.set_eligibility(torch.zeros(4, dtype=torch.bool))
    g.set_eligibility(None)
    g.load_state_dict(old, strict=True)
    assert 'eligibility' not in g.state_dict()
    other = HardConcreteGate(4).eval()
    other.load_state_dict(old)
    assert torch.equal(g(), other())


def test_export_roundtrip_replaces_only_removed_heads_and_no_mlps(api):
    from analysis import apply_node_masks
    from evaluation.selective_runner import safe_knockout
    _, model = build_tiny_pair()
    candidates = [(0, 0), (0, 1), (1, 1)]
    api.configure_candidate_gates(model, candidates)
    with torch.no_grad():
        model.model.layers[0].attn.head_gates.log_alpha[:] = torch.tensor([-1., 0., -999., 3.])
    exported = api.export_binary_masks(model, candidates, provenance={'data_hash': 'fixture'})
    assert exported['removed_heads'] == [[0, 0], [0, 1]]
    assert exported['effective_candidate_count'] == 3
    for l, values in exported['K'].items():
        assert [1 - k for k in values] == exported['R'][l]
    assert all(not any(v) for v in exported['removal_mask']['mlp_hidden'].values())
    model.eval()
    ids = torch.tensor([[1, 2, 3, 4]])
    donors = torch.tensor([[5, 6, 7, 8]])
    expected = model(input_ids=ids, corrupted_input_ids=donors, use_cache=False).logits
    for module in model.modules():
        if isinstance(module, HardConcreteGate):
            module.set_eligibility(None)
    apply_node_masks(model, safe_knockout(exported['removal_mask']))
    actual = model(input_ids=ids, corrupted_input_ids=donors, use_cache=False).logits
    torch.testing.assert_close(actual, expected, atol=0, rtol=0)


def test_tiny_joint_forward_identity_shared_draw_and_eligible_updates(api):
    from unittest.mock import patch
    from config import NodePruningConfig
    cfg = NodePruningConfig(prune_attention_neurons=False, prune_attention_blocks=False,
                            prune_mlp_hidden=False, prune_mlp_output=False, prune_mlp_blocks=False)
    plain, model = build_tiny_pair(node_cfg=cfg)
    params = api.configure_candidate_gates(model, [(0, 0), (1, 1)], expected_initial_removed=.5)
    assert len(params) == 2 and all(p.dtype == torch.float32 for p in params)
    ids = torch.tensor([[1, 2, 3, 4], [8, 9, 10, 11]])
    donors = ids.flip(0)
    model.eval()
    expected = plain(ids, use_cache=False).logits
    torch.testing.assert_close(model(input_ids=ids, corrupted_input_ids=donors, use_cache=False).logits,
                               expected, atol=1e-6, rtol=1e-6)
    with torch.no_grad():
        params[0][0] = -1.
    changed = model(input_ids=ids, corrupted_input_ids=donors, use_cache=False).logits
    assert not torch.equal(changed, expected)
    torch.testing.assert_close(model(input_ids=ids, corrupted_input_ids=ids, use_cache=False).logits,
                               expected, atol=1e-6, rtol=1e-6)
    before = {n: p.clone() for n, p in model.named_parameters()}
    model.train()
    with patch('torch.rand_like', side_effect=lambda a: torch.full_like(a, .5)) as draws:
        joined = model(input_ids=ids, corrupted_input_ids=donors, use_cache=False).logits[:, -1]
        assert draws.call_count == 2
        joint_loss = loss(api, d=joined[:1], h=joined[1:])
        joint_grad = torch.autograd.grad(joint_loss.total, params)
        separate = [model(input_ids=ids[i:i+1], corrupted_input_ids=donors[i:i+1],
                          use_cache=False).logits[:, -1] for i in range(2)]
        separate_loss = loss(api, d=separate[0], h=separate[1])
        separate_grad = torch.autograd.grad(separate_loss.total, params)
    for a, b in zip(joint_grad, separate_grad):
        torch.testing.assert_close(a, b, atol=1e-6, rtol=1e-5)
    optimizer = torch.optim.AdamW(params, lr=.03, weight_decay=0.)
    for p, g in zip(params, joint_grad):
        p.grad = g
    optimizer.step()
    changed_names = []
    for n, p in model.named_parameters():
        if not torch.equal(p, before[n]):
            changed_names.append(n)
            assert n.endswith('attn.head_gates.log_alpha')
            eligibility = model.get_submodule(n.rsplit('.', 1)[0]).eligibility
            assert torch.equal(p[~eligibility], before[n][~eligibility])
    assert changed_names


def test_manifest_rehashed_relational_mutation_is_rejected(api):
    m = build(api)
    api.validate_pilot_manifest(m)
    for change in ('prompt', 'rotation'):
        x = copy.deepcopy(m)
        d = x['splits']['train']
        if change == 'prompt':
            p = d['clusters'][0]['prompts']['original']['D']['clean']
            p['text'] = p['text'].replace('reviewed', 'observed')
            p['text_hash'] = sd._text_hash(p['text'])
        else:
            ids = [c['cluster_id'] for c in d['clusters']]
            d['donor_map'] = dict(zip(ids, ids[2:] + ids[:2]))
        d.update(api._split_hashes(d['clusters'], d['donor_map']))
        x['manifest_hash'] = sd.manifest_hash(x)
        with pytest.raises(ValueError):
            api.validate_pilot_manifest(x)
