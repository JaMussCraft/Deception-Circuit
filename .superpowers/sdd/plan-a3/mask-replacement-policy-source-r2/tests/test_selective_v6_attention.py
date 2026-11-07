"""CPU tests: no pretrained loading, CUDA, API calls, or notebooks."""
import copy
from types import SimpleNamespace

import pytest
import torch

from component_analysis import selective_v6_attention as attention


def cases():
    rows = []
    for designation in ("identity", "inverted"):
        for polarity in (0, 1):
            for index in range(4):
                scenario = f"{designation}-{polarity}-{index}"
                for variant in ("D", "H", "F", "I"):
                    rows.append(dict(case_id=f"{scenario}:{variant}", scenario_key=scenario,
                                     family="sdr", split="discovery", variant=variant,
                                     stratum=dict(designation_polarity=designation, item_polarity=polarity)))
    return rows


def test_fixed_two_per_cell_dhi_only_without_outcomes():
    rows = cases()
    selected = attention.select_cases(list(reversed(rows)))
    assert len(selected) == 24
    assert {c["variant"] for c in selected} == {"D", "H", "I"}
    assert len({c["scenario_key"] for c in selected}) == 8
    assert all(c["scenario_key"].endswith(("-0", "-1")) for c in selected)
    assert selected == attention.select_cases(rows)
    assert attention.select_cases(rows + [dict(rows[0], family="far", split="validation")]) == selected


def test_missing_variant_or_duplicate_rejected():
    rows = cases()
    with pytest.raises(ValueError, match="D/H/I"):
        attention.select_cases([c for c in rows if c["case_id"] != "identity-0-0:I"])
    with pytest.raises(ValueError, match="duplicate"):
        attention.select_cases(rows + [rows[0]])


def test_rows_keep_actual_query_and_exact_tokens_with_padding():
    weights = torch.tensor([[[[0., .25, .75, 0.]]]])
    ids = torch.tensor([[99, 10, 11, 99]])
    mask = torch.tensor([[0, 1, 1, 0]])
    tokenizer = SimpleNamespace(convert_ids_to_tokens=lambda ids: [f"tok-{i}" for i in ids])
    result = attention.token_rows(weights, ids, mask, [dict(case_id="x", scenario_key="s", variant="D")],
                                  layer=3, heads=[7], tokenizer=tokenizer,
                                  geometry=dict(num_heads=8, num_kv_heads=2, heads_per_group=4))
    row, = result
    assert row["query_position"] == 2
    assert row["key_positions"] == [1, 2]
    assert row["token_ids"] == [10, 11]
    assert row["token_strings"] == ["tok-10", "tok-11"]
    assert row["weights"] == [.25, .75]
    assert row["kv_group"] == 1
    assert row["segments"]["status"] == "unavailable"
    assert row["backend"] == "eager"


@pytest.mark.parametrize("weights", [torch.tensor([[[[.5, .5, .1]]]]),
                                    torch.tensor([[[[float("nan"), 1., 0.]]]]),
                                    torch.tensor([[[[.3, .3, 0.]]]]),
                                    torch.tensor([[[[-.1, 1.1, 0.]]]])])
def test_bad_mass_mask_or_values_rejected(weights):
    with pytest.raises(ValueError):
        attention.token_rows(weights, torch.tensor([[10, 11, 99]]), torch.tensor([[1, 1, 0]]),
                             [dict(case_id="x", scenario_key="s", variant="H")], layer=0, heads=[0],
                             tokenizer=SimpleNamespace(convert_ids_to_tokens=lambda x: list(map(str, x))),
                             geometry=dict(num_heads=2, num_kv_heads=1, heads_per_group=2))


def test_receipt_binds_mode_output_model_sources_and_budget(tmp_path):
    plan = dict(mode="attention", manifest_sha256="m", runner_sha256="r", code_hashes={"c": "h"},
                source_hashes={"s": "hash"}, model_identity={"revision": "rev"})
    receipt = dict(plan, review_status="approved", output_dir=str(tmp_path), reserved_gpu_hours=.25,
                   remaining_gpu_hours_before=.4, reservation_id="reservation")
    attention.validate_receipt(receipt, plan, tmp_path)
    for key in ("mode", "manifest_sha256", "runner_sha256", "source_hashes", "model_identity", "code_hashes", "output_dir"):
        bad = copy.deepcopy(receipt)
        bad[key] = "wrong"
        with pytest.raises(ValueError):
            attention.validate_receipt(bad, plan, tmp_path)
    with pytest.raises(ValueError):
        attention.validate_receipt(dict(receipt, reserved_gpu_hours=.251), plan, tmp_path)


def test_eager_backend_recovers_after_failure(monkeypatch):
    model = SimpleNamespace(config=SimpleNamespace(_attn_implementation="sdpa"))
    model.set_attn_implementation = lambda value: setattr(model.config, "_attn_implementation", value)
    monkeypatch.setattr(attention.hooks, "_hf", lambda _: model)
    with pytest.raises(RuntimeError, match="test failure"):
        with attention.eager_backend(model):
            assert model.config._attn_implementation == "eager"
            raise RuntimeError("test failure")
    assert model.config._attn_implementation == "sdpa"


def test_drift_covers_full_vocab_and_margin_argmax():
    result = attention.backend_drift(torch.tensor([[1., 2., 3.]]), torch.tensor([[1., 4., 3.]]),
                                     dict(requested_target_id=1, alternate_answer_id=0, truthful_id=0))
    assert result["full_vocab_max_abs"] == 2.
    assert result["argmax_changed"]
    assert result["sdpa_requested_margin"] == 1.
    assert result["eager_requested_margin"] == 3.
    assert result["kl_sdpa_to_eager"] > 0


def test_actual_random_toy_attention_has_padding_checks_and_backend_proofs():
    import importlib.metadata
    if importlib.metadata.version('nnsight') != '0.7.0':
        pytest.skip('actual hook integration requires pinned nnsight 0.7.0')
    from nnsight import NNsight
    from scripts.smoke_nnsight import build_tiny
    from component_analysis import selective_v6 as core
    model = NNsight(build_tiny().eval())
    ids = torch.tensor([[1, 2, 3, 0]])
    mask = torch.tensor([[1, 1, 1, 0]])
    keys = [('head', 0, 0)]
    sdpa_capture, sdpa, sdpa_proof = core.identity_controls(model, ids, mask, keys)
    with attention.eager_backend(model):
        eager_capture, eager, eager_proof = core.identity_controls(model, ids, mask, keys)
    assert sdpa_proof['plain_native_exact'] and eager_proof['plain_native_exact']
    assert sdpa_proof['fp32_self_exact'] and eager_proof['fp32_self_exact']
    weights = attention.hooks.attention_weights(model, ids, mask, layer=0, heads=[0], query_positions=[[2]])
    row, = attention.token_rows(weights, ids, mask, [dict(case_id='toy', scenario_key='toy', variant='I')],
                                layer=0, heads=[0], tokenizer=SimpleNamespace(convert_ids_to_tokens=lambda x: list(map(str,x))),
                                geometry=attention.hooks.geometry(model))
    assert row['query_position'] == 2 and row['key_positions'] == [0, 1, 2]
    assert attention.hooks.attention_implementation(model) == 'sdpa'
    drift = attention.backend_drift(sdpa, eager, dict(requested_target_id=1, alternate_answer_id=2))
    assert drift['full_vocab_max_abs'] >= 0
