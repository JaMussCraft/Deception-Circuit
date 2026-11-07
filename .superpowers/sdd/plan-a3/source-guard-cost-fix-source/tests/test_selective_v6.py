import json
import pytest
import torch
from component_analysis import selective_v6 as v6
from component_analysis.hooks import _write


def masks():
    heads = [[l, h] for l in range(3) for h in range(10)]
    return {'new30': heads, 'new23': heads[:23], 'oldD69': heads, 'random30': heads}


def test_condition_counts_and_true_conditional_release():
    panel = v6.conditions(masks(), 'discovery')
    assert len(panel) == 42
    assert len(v6.conditions(masks(), 'validation')) == 5
    assert len(v6.conditions(masks(), 'supplementary')) == 5
    for name, heads in panel.items():
        if name.startswith('release_'):
            assert len(heads) == 29
            assert set(heads) < set(panel['new30'])
    assert all(k[0] == 'head' for heads in panel.values() for k in heads)


def test_final_nonpad_mapping_independent_rows_and_write_isolation():
    donor_mask = torch.tensor([[0, 1, 1, 0], [1, 1, 1, 1]])
    recipient_mask = torch.tensor([[1, 1, 0], [0, 1, 1]])
    donor = torch.arange(16.).reshape(2, 4, 2)
    current = torch.full((2, 3, 2), -1.)
    repl = v6.final_replacements({('head', 0, 1): donor}, donor_mask, recipient_mask)[('head', 0, 1)]
    got = _write(current, repl)
    assert torch.equal(got[0, 1], donor[0, 2])
    assert torch.equal(got[1, 2], donor[1, 3])
    assert torch.equal(got[~repl.positions], current[~repl.positions])
    assert torch.equal(current, torch.full_like(current, -1))
    with pytest.raises(ValueError):
        v6.last_nonpad(torch.zeros(1, 3))


def test_full_vocab_metrics_signs_probability_and_kl():
    clean = torch.tensor([[1., 3., 0.]])
    changed = torch.tensor([[1., 1., 2.]])
    row = v6.metrics(changed, clean, [1], [0], [0])[0]
    assert row['requested_margin'] == 0
    assert row['margin_drop'] == 2
    assert row['target_probability'] == pytest.approx(float(changed.softmax(-1)[0, 1]))
    assert row['argmax_id'] == 2
    assert not row['requested_correct']
    assert row['kl_intact_to_condition'] > 0
    assert v6.metrics(clean, clean, [1], [0], [0])[0]['kl_intact_to_condition'] == pytest.approx(0)


def test_smoke_four_balanced_discovery_scenarios_only():
    cases = []
    for split in ['discovery', 'validation']:
        for cell in range(4):
            for i in range(2):
                for variant in 'DHFI':
                    cases.append(dict(case_id=f'{split}{cell}{i}{variant}', scenario_key=f'{split}{cell}{i}', family='sdr', split=split, variant=variant, stratum={'designation_polarity':cell//2,'item_polarity':cell%2, 'pressure_id':f'p{i}'}))
    selected = v6.select_cases(cases, 'smoke')
    assert len(selected) == 16
    assert {c['split'] for c in selected} == {'discovery'}
    assert len({c['scenario_key'] for c in selected}) == 4


def test_receipt_requires_exact_source_mode_budget_and_review(tmp_path):
    receipt = {'manifest_sha256':'abc', 'runner_sha256':'def', 'mode':'smoke', 'review_status':'approved', 'reserved_gpu_hours':.25, 'remaining_gpu_hours_before':2.9, 'reservation_id':'r1', 'code_hashes':{'hooks':'ghi'}, 'output_dir':str(tmp_path/'out')}
    v6.validate_receipt(receipt, 'abc', 'def', 'smoke', {'hooks':'ghi'}, tmp_path/'out')
    for key, value in [('manifest_sha256','bad'), ('review_status','pending'), ('reserved_gpu_hours',3), ('mode','discovery'), ('code_hashes',{'hooks':'changed'}), ('remaining_gpu_hours_before',float('nan')), ('output_dir',str(tmp_path/'other'))]:
        with pytest.raises(ValueError):
            v6.validate_receipt(dict(receipt, **{key:value}), 'abc', 'def', 'smoke', {'hooks':'ghi'}, tmp_path/'out')


def test_actual_tiny_backend_identity_and_replacement():
    nnsight = pytest.importorskip('nnsight')
    if nnsight.__version__ != '0.7.0':
        pytest.skip('requires pinned nnsight 0.7.0')
    from nnsight import NNsight
    from scripts.smoke_nnsight import build_tiny
    from component_analysis import hooks
    model = NNsight(build_tiny().eval())
    ids = torch.tensor([[1, 2, 3], [3, 4, 0]])
    mask = torch.tensor([[1, 1, 1], [1, 1, 0]])
    keys = [('head', 0, 0), ('head', 0, 1)]
    clean, logits, proof = v6.identity_controls(model, ids, mask, keys)
    assert proof['native_noop_exact'] and proof['fp32_self_exact']
    assert proof['plain_native_exact']
    donor = hooks.capture_forward(model, ids.flip(0), mask.flip(0), components=keys, positions=v6.last_nonpad(mask.flip(0)))
    replacements = v6.final_replacements(donor.outputs, mask.flip(0), mask)
    result = hooks.capture_forward(model, ids, mask, components=keys, replacements={keys[0]:replacements[keys[0]]}, positions=v6.last_nonpad(mask))
    pos = v6.last_nonpad(mask)
    rows = torch.arange(2)
    assert torch.equal(result.outputs[keys[0]][rows, pos], donor.outputs[keys[0]][rows, v6.last_nonpad(mask.flip(0))])
    assert torch.equal(result.outputs[keys[1]], clean.outputs[keys[1]])


def test_one_use_receipt_claim_is_exclusive(tmp_path):
    receipt = tmp_path/'receipt.json'
    receipt.write_text('{}')
    v6.claim_receipt(receipt, 'hash')
    with pytest.raises(FileExistsError):
        v6.claim_receipt(receipt, 'hash')


def test_dry_run_never_constructs_model_and_never_overwrites(tmp_path, monkeypatch):
    import argparse
    from component_analysis import selective_v6_manifest
    manifest_path = tmp_path/'manifest.json'
    manifest_path.write_text('{}')
    panel = dict(cases=[], masks=masks(), sources={}, model_identity={'snapshot':'frozen'}, model_name='model', tokenizer_id='tokenizer')
    monkeypatch.setattr(selective_v6_manifest, 'load_manifest', lambda *a, **k:panel)
    def forbidden(*a, **k):
        raise AssertionError('dry run constructed pretrained model')
    monkeypatch.setattr(v6.hooks, 'load_analysis_model', forbidden)
    args = argparse.Namespace(manifest=str(manifest_path), output_dir=str(tmp_path/'out'), mode='dry-run', execution_receipt=None, batch_size=4)
    v6.run(args)
    assert json.loads((tmp_path/'out'/'plan.json').read_text())['condition_rows'] == 0
    with pytest.raises(FileExistsError):
        v6.run(args)
