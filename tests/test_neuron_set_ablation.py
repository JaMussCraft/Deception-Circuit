"""
neuron-partition W2: the `mlp_hidden` kind (one MLP hidden neuron, a column of
the `down_proj` input) in `component_analysis/hooks.py` and
`component_analysis/knockout.py`, and the pure parts of
`scripts/neuron_set_ablation.py`.

Every model-side expectation comes by an independent route: plain torch hooks
on the HuggingFace model, not the nnsight trace under test. The model tests are
nnsight 0.7.0 only and skip in the login node's base environment (nnsight
0.5.12), as `tests/test_component_analysis_v2_knockout_model.py` does; the
groups-file and metric tests run on both interpreters.
"""

from __future__ import annotations

import json

import pytest
import torch

from component_analysis import knockout as ko
from scripts import neuron_set_ablation as nsa
from tests.helpers import TINY, tiny_config


def _nnsight_pinned() -> bool:
    try:
        import nnsight
    except ImportError:
        return False
    return nnsight.__version__ == "0.7.0"


needs_nnsight = pytest.mark.skipif(not _nnsight_pinned(),
                                   reason="nnsight 0.7.0 behaviours (login base env "
                                          "has 0.5.12)")

SEQ = 12
BATCH = 3
CLAUSE = (5, 8)


# ==============================================================================
# FIXTURES: the tiny model and a v2-shaped batch with a twin
# ==============================================================================

@pytest.fixture(scope="module")
def model():
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())


def make_batch():
    """The same batch `test_component_analysis_v2_knockout_model.make_batch`
    builds: the twin differs from the clean prompt at CLAUSE, row 2 is padded."""
    from component_analysis import dataloaders

    torch.manual_seed(2)
    clean = torch.randint(2, TINY["vocab"], (BATCH, SEQ))
    corrupt = clean.clone()
    corrupt[:, 3] = (clean[:, 3] + 7) % TINY["vocab"]
    twin = clean.clone()
    twin[:, CLAUSE[0]:CLAUSE[1]] = (clean[:, CLAUSE[0]:CLAUSE[1]] + 11) % TINY["vocab"]
    mask = torch.ones_like(clean)
    mask[2, SEQ - 2:] = 0
    readout = mask.sum(-1) - 1
    pair = dataloaders.NeutralTwinPair(
        rows=[0, 1, 2], input_ids=twin, attention_mask=mask.clone(),
        corrupt_input_ids=twin.clone(), corrupt_attention_mask=mask.clone(),
        clause_span=torch.tensor([list(CLAUSE)] * BATCH))
    return dataloaders.Batch(
        ids=[f"tiny_{n}" for n in range(BATCH)], records=[{} for _ in range(BATCH)],
        input_ids=clean, attention_mask=mask, corrupt_input_ids=corrupt,
        corrupt_attention_mask=mask, target_token=torch.tensor([5, 6, 7]),
        distractor_token=torch.tensor([8, 9, 10]), readout=readout, honest=None,
        neutral_twin=pair)


@pytest.fixture(scope="module")
def batch():
    return make_batch()


def down_inputs(model, input_ids, attention_mask, *, replace=None):
    """`{layer: down_proj input}` and the Readout logits by plain torch hooks.

    `replace` is `{layer: fn(tensor) -> tensor}`: a forward pre-hook that
    rewrites that layer's down_proj input, the independent route for a patch.
    """
    hf = model._model
    seen, handles = {}, []
    for layer, block in enumerate(hf.model.layers):
        def hook(module, args, layer=layer):
            value = args[0]
            if replace and layer in replace:
                value = replace[layer](value.clone())
            seen[layer] = value.detach().clone()
            return (value,) + tuple(args[1:])
        handles.append(block.mlp.down_proj.register_forward_pre_hook(hook))
    try:
        with torch.no_grad():
            logits = hf(input_ids=input_ids, attention_mask=attention_mask).logits
    finally:
        for handle in handles:
            handle.remove()
    readout = attention_mask.sum(-1) - 1
    return seen, logits[torch.arange(input_ids.shape[0]), readout, :]


def margins(logits, batch):
    from component_analysis import hooks
    return hooks.target_minus_distractor(logits.float(), batch.target_token,
                                         batch.distractor_token).tolist()


ALL_LAYER0 = [("mlp_hidden", 0, n) for n in range(TINY["intermediate"])]


# ==============================================================================
# (1) CAPTURE
# ==============================================================================

@needs_nnsight
def test_capturing_mlp_hidden_returns_the_whole_down_proj_input_of_the_layer(model, batch):
    from component_analysis import hooks

    keys = [("mlp_hidden", 1, 3), ("mlp_hidden", 1, 40), ("mlp_hidden", 0, 7)]
    capture = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                    components=keys)
    truth, _logits = down_inputs(model, batch.input_ids, batch.attention_mask)
    for layer in (0, 1):
        whole = capture.layers[("mlp_hidden", layer)]
        assert tuple(whole.shape) == (BATCH, SEQ, TINY["intermediate"])
        assert torch.allclose(whole, truth[layer], atol=1e-6)
    for kind, layer, index in keys:
        view = capture.outputs[(kind, layer, index)]
        assert tuple(view.shape) == (BATCH, SEQ, 1)
        assert torch.allclose(view[..., 0], truth[layer][:, :, index], atol=1e-6)


@needs_nnsight
def test_a_pass_without_mlp_hidden_keys_has_no_layers(model, batch):
    from component_analysis import hooks

    capture = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                    components=[("head", 0, 1)])
    assert capture.layers == {}


@needs_nnsight
def test_geometry_reports_the_intermediate_size(model):
    from component_analysis import hooks

    assert hooks.geometry(model)["intermediate_size"] == TINY["intermediate"]


@needs_nnsight
def test_an_mlp_hidden_index_outside_the_layer_is_refused_by_the_pass(model, batch):
    from component_analysis import hooks

    with pytest.raises(ValueError, match="outside"):
        hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                              components=[("mlp_hidden", 0, TINY["intermediate"])])


# ==============================================================================
# (2) REPLACE ONE NEURON
# ==============================================================================

@needs_nnsight
def test_replacing_one_neuron_changes_exactly_that_column(model, batch):
    from component_analysis import hooks

    key = ("mlp_hidden", 1, 17)
    pair = batch.neutral_twin
    twin = hooks.capture_forward(model, pair.input_ids, pair.attention_mask,
                                 components=[key])
    probe = [("mlp_hidden", 1, n) for n in range(TINY["intermediate"])] + \
        [("mlp_hidden", 0, n) for n in range(TINY["intermediate"])]
    clean = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                  components=probe)
    patched = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                    components=probe,
                                    replacements={key: twin.outputs[key]})

    before, after = clean.layers[("mlp_hidden", 1)], patched.layers[("mlp_hidden", 1)]
    changed = (before != after).any(dim=(0, 1)).nonzero().flatten().tolist()
    assert changed == [17]
    assert torch.equal(after[:, :, 17], twin.layers[("mlp_hidden", 1)][:, :, 17])
    # The layer before is untouched.
    assert torch.equal(clean.layers[("mlp_hidden", 0)], patched.layers[("mlp_hidden", 0)])

    # Independent route: a torch pre-hook writes the same column.
    want = twin.layers[("mlp_hidden", 1)][:, :, 17]

    def write(value):
        value[:, :, 17] = want
        return value
    _seen, logits = down_inputs(model, batch.input_ids, batch.attention_mask,
                                replace={1: write})
    got = hooks.replace_forward(model, batch.input_ids, batch.attention_mask,
                                replacements={key: twin.outputs[key]})
    assert torch.allclose(got, logits, atol=1e-5)
    assert not torch.allclose(got, down_inputs(model, batch.input_ids,
                                               batch.attention_mask)[1], atol=1e-6)


@needs_nnsight
def test_a_positions_mask_confines_the_neuron_write(model, batch):
    from component_analysis import hooks

    keys = [("mlp_hidden", 0, 2), ("mlp_hidden", 0, 9)]
    pair = batch.neutral_twin
    twin = hooks.capture_forward(model, pair.input_ids, pair.attention_mask,
                                 components=keys)
    where = torch.zeros(SEQ, dtype=torch.bool)
    where[CLAUSE[0]:] = True
    clean = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                  components=keys)
    patched = hooks.capture_forward(
        model, batch.input_ids, batch.attention_mask, components=keys,
        replacements={key: hooks.Replacement(twin.outputs[key], positions=where)
                      for key in keys})
    for key in keys:
        assert torch.equal(patched.outputs[key][:, :CLAUSE[0]],
                           clean.outputs[key][:, :CLAUSE[0]])
        assert torch.equal(patched.outputs[key][:, CLAUSE[0]:],
                           twin.outputs[key][:, CLAUSE[0]:])


@needs_nnsight
def test_one_layers_neurons_must_share_one_mask(model, batch):
    from component_analysis import hooks

    keys = [("mlp_hidden", 0, 2), ("mlp_hidden", 0, 9)]
    value = torch.zeros(BATCH, SEQ, 1)
    first = torch.zeros(SEQ, dtype=torch.bool)
    second = torch.ones(SEQ, dtype=torch.bool)
    with pytest.raises(ValueError, match="one mask"):
        hooks.replace_forward(model, batch.input_ids, batch.attention_mask,
                              replacements={keys[0]: hooks.Replacement(value, first),
                                            keys[1]: hooks.Replacement(value, second)})


# ==============================================================================
# (3) NEUTRAL-TWIN INTERCHANGE OF A WHOLE LAYER
# ==============================================================================

@needs_nnsight
def test_twin_interchange_of_every_neuron_of_a_layer_reproduces_the_twins_input(
        model, batch):
    from component_analysis import hooks

    pair = batch.neutral_twin
    twin_truth, _ = down_inputs(model, pair.input_ids, pair.attention_mask)
    twin = hooks.capture_forward(model, pair.input_ids, pair.attention_mask,
                                 components=ALL_LAYER0)
    patched = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                    components=ALL_LAYER0,
                                    replacements={k: twin.outputs[k] for k in ALL_LAYER0})
    # Every position is patched, so layer 0's down_proj input IS the twin's.
    assert torch.allclose(patched.layers[("mlp_hidden", 0)], twin_truth[0], atol=1e-6)

    effects = ko.knock_out_groups(model, [batch], [("layer0", ALL_LAYER0)],
                                  plan=ko.KnockoutPlan(counterfactual="neutral_twin"),
                                  record_argmax=True)

    def write(value):
        return twin_truth[0].clone()
    _seen, logits = down_inputs(model, batch.input_ids, batch.attention_mask,
                                replace={0: write})
    assert effects.knocked_logit_difference["layer0"] == pytest.approx(
        margins(logits, batch), abs=1e-4)
    assert effects.knocked_argmax["layer0"] == logits.argmax(-1).tolist()
    _clean_seen, clean_logits = down_inputs(model, batch.input_ids, batch.attention_mask)
    assert effects.clean_argmax == clean_logits.argmax(-1).tolist()
    assert effects.unpaired == []


@needs_nnsight
def test_a_twin_identical_to_the_row_leaves_a_neuron_set_without_effect(model, batch):
    keys = [("mlp_hidden", 0, n) for n in range(0, 128, 3)] + [("mlp_hidden", 1, 5)]
    own = nsa.self_twin(batch)
    effects = ko.knock_out_groups(model, [own], [("set", keys)],
                                  plan=ko.KnockoutPlan(counterfactual="neutral_twin"))
    assert effects.knocked_logit_difference["set"] == pytest.approx(
        effects.clean_logit_difference, abs=1e-5)


# ==============================================================================
# (4) ZERO AND MEAN
# ==============================================================================

@needs_nnsight
def test_zero_ablation_zeroes_the_sets_columns(model, batch):
    from component_analysis import hooks

    keys = [("mlp_hidden", 1, 4), ("mlp_hidden", 1, 99)]
    shape = hooks.geometry(model)
    values = {key: ko._fill(key, scheme="zero", mean_bank=None, n=BATCH, seq=SEQ,
                            shape=shape, dtype=torch.float32, device="cpu") for key in keys}
    probe = [("mlp_hidden", 1, n) for n in range(TINY["intermediate"])]
    patched = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                    components=probe, replacements=values)
    clean = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                  components=probe)
    after = patched.layers[("mlp_hidden", 1)]
    assert torch.equal(after[:, :, [4, 99]], torch.zeros(BATCH, SEQ, 2))
    keep = [n for n in range(TINY["intermediate"]) if n not in (4, 99)]
    assert torch.equal(after[:, :, keep], clean.layers[("mlp_hidden", 1)][:, :, keep])

    effects = ko.knock_out_groups(model, [batch], [("set", keys)],
                                  plan=ko.KnockoutPlan(scheme="zero"))

    def write(value):
        value[:, :, [4, 99]] = 0
        return value
    _seen, logits = down_inputs(model, batch.input_ids, batch.attention_mask,
                                replace={1: write})
    assert effects.knocked_logit_difference["set"] == pytest.approx(
        margins(logits, batch), abs=1e-4)


@needs_nnsight
def test_the_mlp_hidden_mean_bank_is_the_mean_over_unpadded_positions_of_both_streams(
        model, batch):
    keys = [("mlp_hidden", 0, 3), ("mlp_hidden", 1, 64), ("mlp_hidden", 1, 0)]
    bank, info = ko.collect_mean_bank(model, [batch], keys)

    total, tokens = {0: 0.0, 1: 0.0}, 0.0
    for ids, mask in ((batch.input_ids, batch.attention_mask),
                      (batch.corrupt_input_ids, batch.corrupt_attention_mask)):
        seen, _ = down_inputs(model, ids, mask)
        weight = mask.float().unsqueeze(-1)
        for layer in (0, 1):
            total[layer] = total[layer] + (seen[layer].float() * weight).sum(dim=(0, 1))
        tokens += float(mask.sum())
    for kind, layer, index in keys:
        assert tuple(bank[(kind, layer, index)].shape) == (1,)
        assert bank[(kind, layer, index)].item() == pytest.approx(
            (total[layer][index] / tokens).item(), abs=1e-5)
    assert info["n_tokens"] == tokens


@needs_nnsight
def test_mean_ablation_writes_the_banks_values(model, batch):
    keys = [("mlp_hidden", 0, 3), ("mlp_hidden", 0, 50)]
    bank, _info = ko.collect_mean_bank(model, [batch], keys)
    effects = ko.knock_out_groups(model, [batch], [("set", keys)],
                                  plan=ko.KnockoutPlan(scheme="mean"), mean_bank=bank)

    def write(value):
        value[:, :, 3] = bank[("mlp_hidden", 0, 3)].item()
        value[:, :, 50] = bank[("mlp_hidden", 0, 50)].item()
        return value
    _seen, logits = down_inputs(model, batch.input_ids, batch.attention_mask,
                                replace={0: write})
    assert effects.knocked_logit_difference["set"] == pytest.approx(
        margins(logits, batch), abs=1e-4)


# ==============================================================================
# (5) THE GROUPS FILE
# ==============================================================================

def _write(tmp_path, groups):
    path = tmp_path / "sets.json"
    path.write_text(json.dumps(groups))
    return str(path)


def test_an_mlp_hidden_index_of_14336_is_refused_and_14335_accepted(tmp_path):
    with pytest.raises(ValueError, match="0..14335"):
        ko.load_groups(_write(tmp_path, {"s": [["mlp_hidden", 3, 14336]]}))
    assert ko.load_groups(_write(tmp_path, {"s": [["mlp_hidden", 3, 14335]]})) == [
        ("s", [("mlp_hidden", 3, 14335)])]


def test_a_negative_mlp_hidden_index_is_refused(tmp_path):
    with pytest.raises(ValueError, match="mlp_hidden index"):
        ko.load_groups(_write(tmp_path, {"s": [["mlp_hidden", 3, -1]]}))


def test_check_groups_bounds_neurons_by_the_models_intermediate_size(tmp_path):
    groups = ko.load_groups(_write(tmp_path, {"s": [["mlp_hidden", 1, 200]]}))
    with pytest.raises(ValueError, match="mlp_hidden index 200"):
        ko.check_groups(groups, {"num_layers": 2, "num_heads": 4,
                                 "intermediate_size": TINY["intermediate"]})
    ko.check_groups(groups, {"num_layers": 32, "num_heads": 32})   # 8B default bound


def test_other_kinds_are_still_refused_and_heads_still_load(tmp_path):
    with pytest.raises(ValueError, match="head or mlp"):
        ko.load_groups(_write(tmp_path, {"s": [["q", 1, 2]]}))
    assert ko.load_groups(_write(tmp_path, {"s": [["head", 1, 2], ["mlp", 0, 0],
                                                  ["mlp_hidden", 0, 0]]})) == [
        ("s", [("head", 1, 2), ("mlp", 0, 0), ("mlp_hidden", 0, 0)])]


def test_a_neuron_named_twice_is_refused(tmp_path):
    with pytest.raises(ValueError, match="twice"):
        ko.load_groups(_write(tmp_path, {"s": [["mlp_hidden", 1, 2], ["mlp_hidden", 1, 2]]}))


# ==============================================================================
# (6) EXISTING KINDS UNCHANGED
# ==============================================================================

#: `knock_out_groups` on head 1.2 + MLP 0 of the tiny model, measured on the
#: code before the mlp_hidden change (branch neuron-partition at 618efdd) and
#: pinned here: the change must not move them.
GOLDEN = {
    "item_swap": [0.21871556341648102, -0.012111328542232513, -0.2548017203807831],
    "twin": [0.24555842578411102, 0.014691049233078957, -0.234916090965271],
    "zero": [0.14703369140625, -0.015606045722961426, -0.23438462615013123],
    "mean": [0.15637654066085815, -0.03458159416913986, -0.3051384687423706],
}
GOLDEN_CLEAN = [0.23387692868709564, 0.02027326449751854, -0.26442795991897583]


@needs_nnsight
@pytest.mark.parametrize("name", list(GOLDEN))
def test_head_and_mlp_knockouts_are_unchanged(model, batch, name):
    keys = [("head", 1, 2), ("mlp", 0, 0)]
    plan = {"item_swap": ko.KnockoutPlan(),
            "twin": ko.KnockoutPlan(counterfactual="neutral_twin"),
            "zero": ko.KnockoutPlan(scheme="zero"),
            "mean": ko.KnockoutPlan(scheme="mean")}[name]
    bank = ko.collect_mean_bank(model, [batch], keys)[0] if name == "mean" else None
    effects = ko.knock_out_groups(model, [batch], [("pair", keys)], plan=plan,
                                  mean_bank=bank)
    assert effects.clean_logit_difference == pytest.approx(GOLDEN_CLEAN, abs=1e-6)
    assert effects.knocked_logit_difference["pair"] == pytest.approx(GOLDEN[name], abs=1e-6)
    assert effects.clean_argmax == [] and effects.knocked_argmax == {}


# ==============================================================================
# THE SCRIPT: STREAMS, PAIRING AND METRICS
# ==============================================================================

def test_the_corrupt_stream_swaps_the_words_and_takes_the_twins_corrupt_prompt():
    batch = make_batch()
    flipped = nsa.corrupt_stream(batch)
    assert torch.equal(flipped.input_ids, batch.corrupt_input_ids)
    assert torch.equal(flipped.target_token, batch.distractor_token)
    assert torch.equal(flipped.distractor_token, batch.target_token)
    assert torch.equal(flipped.neutral_twin.input_ids, batch.neutral_twin.corrupt_input_ids)
    assert torch.equal(flipped.readout, batch.corrupt_attention_mask.sum(-1) - 1)


def test_the_reverse_twin_makes_the_twin_the_recipient_with_its_own_labels():
    batch = make_batch()
    reverse = nsa.reverse_twin(batch)
    assert torch.equal(reverse.input_ids, batch.neutral_twin.input_ids)
    assert torch.equal(reverse.neutral_twin.input_ids, batch.input_ids)
    assert torch.equal(reverse.target_token, batch.distractor_token)


def _pool_batch(request_tokens, *, target, distractor, span=(5, 8)):
    from component_analysis import dataloaders

    ids = torch.arange(10, 10 + SEQ).repeat(2, 1)
    ids[:, span[0]:span[1]] = torch.tensor(request_tokens)
    mask = torch.ones_like(ids)
    records = [{"request_spans": {"clean": list(span), "corrupt": list(span)}}] * 2
    return dataloaders.Batch(
        ids=["a", "b"], records=records, input_ids=ids, attention_mask=mask,
        corrupt_input_ids=ids.clone(), corrupt_attention_mask=mask.clone(),
        target_token=torch.tensor([target] * 2), distractor_token=torch.tensor([distractor] * 2),
        readout=mask.sum(-1) - 1, honest=None)


def test_attach_twin_pairs_a_user_turn_pool_with_its_neutral_twin():
    inversion = _pool_batch([1, 2, 3], target=7, distractor=8)
    neutral = _pool_batch([4, 5, 6], target=8, distractor=7)
    paired = nsa.attach_twin(inversion, neutral)
    assert paired.neutral_twin.rows == [0, 1]
    assert torch.equal(paired.neutral_twin.input_ids, neutral.input_ids)
    assert paired.neutral_twin.clause_span.tolist() == [[5, 8], [5, 8]]


def test_attach_twin_refuses_a_twin_that_differs_outside_the_request_span():
    inversion = _pool_batch([1, 2, 3], target=7, distractor=8)
    neutral = _pool_batch([4, 5, 6], target=8, distractor=7)
    neutral.input_ids[0, 1] = 99
    with pytest.raises(ValueError, match="outside the request span"):
        nsa.attach_twin(inversion, neutral)


def test_attach_twin_refuses_a_twin_whose_words_are_not_swapped():
    inversion = _pool_batch([1, 2, 3], target=7, distractor=8)
    neutral = _pool_batch([4, 5, 6], target=7, distractor=8)
    with pytest.raises(ValueError, match="swapped"):
        nsa.attach_twin(inversion, neutral)


def test_the_ladder_ratio_averages_streams_within_an_id_then_ids():
    m_int = {"clean": {"a": 4.0, "b": 2.0}, "corrupt": {"a": 6.0, "b": 2.0}}
    m_abl = {"clean": {"a": 2.0, "b": 2.0}, "corrupt": {"a": 4.0, "b": 0.0}}
    m_twin = {"clean": {"a": 0.0, "b": 0.0}, "corrupt": {"a": 0.0, "b": -2.0}}
    out = nsa.ladder_ratio(m_int, m_abl, m_twin, ["a", "b"], 1e-6)
    # gaps: a = (4 + 6) / 2 = 5, b = (2 + 4) / 2 = 3 -> G 4; drops: a 2, b 1 -> 1.5
    assert out["G"] == pytest.approx(4.0)
    assert out["mean_drop"] == pytest.approx(1.5)
    assert out["fraction_removed"] == pytest.approx(0.375)
    assert nsa.ladder_ratio(m_int, m_abl, m_int, ["a", "b"], 1e-6)["fraction_removed"] is None


def test_the_rate_share_uses_the_ge_margin_rule():
    values = {"clean": {"a": 0.7, "b": 0.69}, "corrupt": {"a": 1.0, "b": 0.8}}
    # a: (1 + 1) / 2, b: (0 + 1) / 2 -> 0.75
    assert nsa.share(values, ["a", "b"], lambda v: v >= 0.7) == pytest.approx(0.75)
    assert nsa.removed_fraction(0.8, 0.2) == pytest.approx(0.75)
    assert nsa.removed_fraction(0.0, 0.2) is None


def _cell(sign, intact, ablated, twin=None, argmax=None, target=None, distractor=None):
    cell = nsa.Cell(sign)
    cell.ids = list(intact)
    cell.intact = dict(intact)
    cell.ablated = {"s": dict(ablated)}
    cell.twin = dict(twin or {})
    cell.intact_argmax = dict(argmax or {one: 0 for one in intact})
    cell.ablated_argmax = {"s": dict(argmax or {one: 0 for one in intact})}
    cell.target = dict(target or {one: 0 for one in intact})
    cell.distractor = dict(distractor or {one: 1 for one in intact})
    return cell


def test_the_d_effect_under_mean_compares_d_ablated_with_h_ablated():
    d = {"clean": _cell(1, {"a": 3.0, "b": 3.0}, {"a": 0.0, "b": 3.0},
                        twin={"a": -3.0, "b": -3.0})}
    # H's own margins (honest target): D orientation is the negative.
    h = {"clean": _cell(-1, {"a": 3.0, "b": 3.0}, {"a": -1.0, "b": 3.0})}
    out = nsa.effect_metrics(d, h, "s", reference="mean", margin=0.7, epsilon=1e-6)
    rate = out["rate"]
    assert rate["effect_intact"] == pytest.approx(1.0)
    # D ablated: a falls below the margin; H ablated: a rises to m = 1.0 >= 0.7.
    assert rate["effect_ablated"] == pytest.approx(0.5 - 0.5)
    assert rate["fraction_removed"] == pytest.approx(1.0)
    assert rate["effect_ablated_vs_twin_intact"] == pytest.approx(0.5)
    assert out["ladder_margin_ratio"]["fraction_removed"] == pytest.approx(1.5 / 6.0)
    twin = nsa.effect_metrics(d, None, "s", reference="twin", margin=0.7, epsilon=1e-6)
    assert twin["rate"]["fraction_removed"] == pytest.approx(0.5)


def test_the_cells_cover_twin_reverse_and_fill_with_ioi_only_off_twin():
    args = nsa.build_parser().parse_args(["--sets", "x", "--output-dir", "y"])
    cells = nsa.cells(args, has_ioi=True)
    kinds = {(r, c, k) for r, c, _s, k in cells}
    assert ("twin", "D", "twin") in kinds and ("twin", "I", "twin") in kinds
    assert ("twin", "H", "reverse") in kinds and ("twin", "N", "reverse") in kinds
    assert not any(c == "F" and r == "twin" for r, c, _k in kinds)
    assert ("mean", "IOI", "fill") in kinds and ("zero", "IOI", "fill") in kinds
    assert not any(c == "IOI" and r == "twin" for r, c, _k in kinds)
    off = nsa.build_parser().parse_args(["--sets", "x", "--output-dir", "y",
                                         "--no-twin-reverse"])
    assert not any(k == "reverse" for _r, _c, _s, k in nsa.cells(off, has_ioi=False))


def test_the_estimate_counts_one_clean_and_one_twin_pass_per_chunk(tmp_path):
    args = nsa.build_parser().parse_args(
        ["--sets", "x", "--output-dir", "y", "--conditions", "D", "--references", "twin",
         "--streams", "clean", "--sets-per-call", "2", "--no-ioi", "--no-self-replay"])
    groups = [(f"s{n}", [("mlp_hidden", 0, n)]) for n in range(5)]
    plan = nsa.estimate(args, groups, {"D": 4}, {"D": 128}, bank_batches=0)
    # 3 chunks x 2 base passes + 5 sets, per batch.
    assert plan["forwards"] == 4 * (3 * 2 + 5)
    assert plan["cells"][0]["kind"] == "twin"


def test_ids_files_accept_a_list_a_wrapped_list_or_a_per_condition_map(tmp_path):
    path = tmp_path / "ids.json"
    path.write_text(json.dumps(["x", "y"]))
    assert nsa.load_ids(str(path))["I"] == ["x", "y"]
    path.write_text(json.dumps({"instance_ids": ["x"]}))
    assert nsa.load_ids(str(path))["D"] == ["x"]
    path.write_text(json.dumps({"D": ["x"], "I": ["z"]}))
    loaded = nsa.load_ids(str(path))
    assert loaded["D"] == ["x"] and loaded["I"] == ["z"] and loaded["H"] is None
