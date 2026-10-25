"""
Knockout extensions against a model (ticket 02a): the mean bank against a
hand-computed mean, zero and mean against the replace primitive, the
Neutral-Clause Twin counterfactual (identical streams give zero, pre-clause
positions give exactly zero), position restrictions against hand-built masks,
the counterfactual margin per instance, and the CLI seam on a real v2 cell.

Every expected number comes by an independent route: torch forward hooks on
the plain HF model, or `hooks.replace_forward`, whose logits come from the
model's own head inside the trace, while the analysis reads its own through
the fp32 readout.

nnsight 0.7.0 only, gated as `tests/test_knockout_model.py` gates.
"""

from __future__ import annotations


import pytest

nnsight = pytest.importorskip("nnsight")
PINNED = "0.7.0"
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}; these are 0.7.0 behaviours.",
                allow_module_level=True)

import torch                                                       # noqa: E402

from component_analysis import dataloaders, hooks, knockout as ko  # noqa: E402
from component_analysis.segmentation import Segment, Segmentation  # noqa: E402
from tests.helpers import TINY, tiny_config                        # noqa: E402

SEQ = 12
BATCH = 3
CLAUSE = (5, 8)          # the twin differs from the clean prompt here


@pytest.fixture(scope="module")
def model():
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())


def make_batch(*, twin_equals_clean=False):
    torch.manual_seed(2)
    clean = torch.randint(2, TINY["vocab"], (BATCH, SEQ))
    corrupt = clean.clone()
    corrupt[:, 3] = (clean[:, 3] + 7) % TINY["vocab"]
    twin = clean.clone()
    if not twin_equals_clean:
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


def segmentations(batch):
    out = {}
    for row, one in enumerate(batch.ids):
        n = int(batch.attention_mask[row].sum())
        out[one] = Segmentation(
            task="sdr_v2", record_id=one, n_tokens=n, readout=n - 1, segments={
                "intro": Segment("intro", ((0, CLAUSE[0]),)),
                "pressure_clause": Segment("pressure_clause", (CLAUSE,)),
                "question": Segment("question", ((CLAUSE[1], n - 1),)),
                "readout": Segment("readout", ((n - 1, n),))})
    return out


def logit_difference_of(logits, batch):
    return hooks.target_minus_distractor(logits.float(), batch.target_token,
                                         batch.distractor_token).tolist()


def replaced(model, batch, key, value, mask=None):
    """The independent route: `replace_forward` with an explicit value."""
    replacement = hooks.Replacement(value, positions=mask) if mask is not None else value
    return logit_difference_of(
        hooks.replace_forward(model, batch.input_ids, batch.attention_mask,
                              replacements={key: replacement},
                              positions=batch.readout), batch)


KEYS = [("head", 1, 2), ("mlp", 0, 0)]


# ==============================================================================
# THE MEAN BANK, MEAN AND ZERO
# ==============================================================================

def hooked_outputs(model, input_ids, attention_mask):
    """Head 1.2's o_proj input slice and MLP 0's output, by plain torch hooks."""
    hf = model._model
    seen = {}
    handles = [
        hf.model.layers[1].self_attn.o_proj.register_forward_pre_hook(
            lambda module, args: seen.__setitem__("head", args[0].detach().clone())),
        hf.model.layers[0].mlp.register_forward_hook(
            lambda module, args, output: seen.__setitem__("mlp", output.detach().clone())),
    ]
    try:
        with torch.no_grad():
            hf(input_ids=input_ids, attention_mask=attention_mask)
    finally:
        for handle in handles:
            handle.remove()
    dim = TINY["head_dim"]
    return {("head", 1, 2): seen["head"][:, :, 2 * dim:3 * dim], ("mlp", 0, 0): seen["mlp"]}


def test_the_mean_bank_is_the_mean_over_every_unpadded_position_of_both_streams(
        model, batch):
    bank, info = ko.collect_mean_bank(model, [batch], KEYS)

    for key in KEYS:
        total, count = 0.0, 0
        for ids in (batch.input_ids, batch.corrupt_input_ids):
            values = hooked_outputs(model, ids, batch.attention_mask)[key]
            for row in range(BATCH):
                for position in range(SEQ):
                    if batch.attention_mask[row, position]:
                        total = total + values[row, position].double()
                        count += 1
        assert bank[key].dtype == torch.float32
        assert torch.allclose(bank[key].double(), total / count, atol=1e-5)
    assert info["n_tokens"] == 2 * int(batch.attention_mask.sum())


@pytest.mark.parametrize("key", KEYS)
def test_zero_writes_zeros(model, batch, key):
    effects = ko.knockout_effects(model, [batch], [key],
                                  plan=ko.KnockoutPlan(scheme="zero"))
    dim = TINY["head_dim"] if key[0] == "head" else TINY["hidden"]
    expected = replaced(model, batch, key, torch.zeros(BATCH, SEQ, dim))
    assert effects.knocked_logit_difference[key] == pytest.approx(expected, abs=1e-4)
    assert effects.counterfactual_logit_difference == []


@pytest.mark.parametrize("key", KEYS)
def test_mean_writes_the_bank_at_every_position(model, batch, key):
    bank, _info = ko.collect_mean_bank(model, [batch], KEYS)
    effects = ko.knockout_effects(model, [batch], [key], mean_bank=bank,
                                  plan=ko.KnockoutPlan(scheme="mean"))
    value = bank[key].reshape(1, 1, -1).expand(BATCH, SEQ, -1).clone()
    assert effects.knocked_logit_difference[key] == pytest.approx(
        replaced(model, batch, key, value), abs=1e-4)


def test_a_mean_knockout_without_a_bank_is_refused(model, batch):
    with pytest.raises(ValueError, match="mean bank"):
        ko.knockout_effects(model, [batch], KEYS, plan=ko.KnockoutPlan(scheme="mean"))


# ==============================================================================
# THE NEUTRAL-CLAUSE TWIN
# ==============================================================================

TWIN = {"counterfactual": "neutral_twin"}
ALL_KEYS = ([("head", layer, head) for layer in range(TINY["layers"])
             for head in range(TINY["heads"])]
            + [("mlp", layer, 0) for layer in range(TINY["layers"])])


def test_a_twin_identical_to_the_clean_prompt_gives_zero_drop(model):
    same = make_batch(twin_equals_clean=True)
    effects = ko.knockout_effects(model, [same], ALL_KEYS, plan=ko.KnockoutPlan(**TWIN))
    assert all(drop == 0.0 for key in ALL_KEYS for drop in effects.drops(key))


def test_the_twin_at_pre_clause_positions_gives_exactly_zero(model, batch):
    effects = ko.knockout_effects(
        model, [batch], ALL_KEYS, segmentations=segmentations(batch),
        plan=ko.KnockoutPlan(positions="intro", **TWIN))
    assert all(drop == 0.0 for key in ALL_KEYS for drop in effects.drops(key))


def test_the_twin_at_the_clause_moves_the_metric(model, batch):
    """Guards the two tests above against passing because nothing moves."""
    effects = ko.knockout_effects(
        model, [batch], ALL_KEYS, segmentations=segmentations(batch),
        plan=ko.KnockoutPlan(positions="pressure_clause", **TWIN))
    assert any(abs(drop) > 1e-3 for key in ALL_KEYS for drop in effects.drops(key))


def test_the_twin_knockout_copies_the_twins_value(model, batch):
    key = ("head", 1, 2)
    effects = ko.knockout_effects(model, [batch], [key], plan=ko.KnockoutPlan(**TWIN))
    twin = hooks.capture_forward(model, batch.neutral_twin.input_ids,
                                 batch.neutral_twin.attention_mask, components=[key],
                                 positions=batch.readout)
    assert effects.knocked_logit_difference[key] == pytest.approx(
        replaced(model, batch, key, twin.outputs[key]), abs=1e-4)


def test_the_twins_own_margin_is_recorded_per_instance_with_d_labels(model, batch):
    effects = ko.knockout_effects(model, [batch], KEYS, plan=ko.KnockoutPlan(**TWIN))
    from tests.test_component_hooks import plain_readout_logits
    expected = logit_difference_of(
        plain_readout_logits(model, batch.neutral_twin.input_ids,
                             batch.neutral_twin.attention_mask), batch)
    assert effects.counterfactual_logit_difference == pytest.approx(expected, abs=1e-4)


@pytest.mark.parametrize("plan", [{}, TWIN], ids=["item_swap", "neutral_twin"])
def test_every_plan_records_the_twins_own_margin_beside_its_numbers(model, batch, plan):
    """R19(1): the twin's margin is in the per-instance record whatever the plan."""
    from tests.test_component_hooks import plain_readout_logits
    effects = ko.knockout_effects(model, [batch], KEYS, plan=ko.KnockoutPlan(**plan))
    expected = logit_difference_of(
        plain_readout_logits(model, batch.neutral_twin.input_ids,
                             batch.neutral_twin.attention_mask), batch)
    assert effects.neutral_twin_logit_difference == pytest.approx(expected, abs=1e-4)


def test_a_row_without_a_twin_reads_none_and_a_cell_without_any_reads_empty(model):
    partial = make_batch()
    pair = partial.neutral_twin
    partial.neutral_twin = dataloaders.NeutralTwinPair(
        rows=[0, 2], input_ids=pair.input_ids[[0, 2]],
        attention_mask=pair.attention_mask[[0, 2]],
        corrupt_input_ids=pair.corrupt_input_ids[[0, 2]],
        corrupt_attention_mask=pair.corrupt_attention_mask[[0, 2]],
        clause_span=pair.clause_span[[0, 2]])
    effects = ko.knockout_effects(model, [partial], KEYS)
    assert effects.ids == ["tiny_0", "tiny_1", "tiny_2"]
    margins = effects.neutral_twin_logit_difference
    assert margins[1] is None and None not in (margins[0], margins[2])

    bare = make_batch()
    bare.neutral_twin = None
    assert ko.knockout_effects(model, [bare], KEYS).neutral_twin_logit_difference == []


def test_rows_without_a_twin_are_left_out_and_named(model):
    partial = make_batch()
    pair = partial.neutral_twin
    partial.neutral_twin = dataloaders.NeutralTwinPair(
        rows=[0, 2], input_ids=pair.input_ids[[0, 2]],
        attention_mask=pair.attention_mask[[0, 2]],
        corrupt_input_ids=pair.corrupt_input_ids[[0, 2]],
        corrupt_attention_mask=pair.corrupt_attention_mask[[0, 2]],
        clause_span=pair.clause_span[[0, 2]])
    effects = ko.knockout_effects(model, [partial], KEYS, plan=ko.KnockoutPlan(**TWIN))
    assert effects.ids == ["tiny_0", "tiny_2"]
    assert effects.unpaired == ["tiny_1"]


# ==============================================================================
# POSITIONS
# ==============================================================================

def hand_mask(batch, rows_positions):
    mask = torch.zeros(BATCH, SEQ, dtype=torch.bool)
    for row, positions in enumerate(rows_positions):
        mask[row, positions] = True
    return mask


def test_a_segment_restriction_writes_only_that_segments_tokens(model, batch):
    key = ("mlp", 0, 0)
    effects = ko.knockout_effects(model, [batch], [key],
                                  segmentations=segmentations(batch),
                                  plan=ko.KnockoutPlan(positions="question"))
    corrupt = hooks.capture_forward(model, batch.corrupt_input_ids,
                                    batch.corrupt_attention_mask, components=[key])
    # Rows 0 and 1 have 12 tokens, row 2 has 10: question is [8, n - 1).
    mask = hand_mask(batch, [[8, 9, 10], [8, 9, 10], [8]])
    assert effects.knocked_logit_difference[key] == pytest.approx(
        replaced(model, batch, key, corrupt.outputs[key], mask), abs=1e-4)


def test_the_post_clause_range_writes_after_the_clause_and_before_the_readout(
        model, batch):
    key = ("head", 1, 2)
    effects = ko.knockout_effects(
        model, [batch], [key], segmentations=segmentations(batch),
        plan=ko.KnockoutPlan(positions="after=pressure_clause,exclude=readout", **TWIN))
    twin = hooks.capture_forward(model, batch.neutral_twin.input_ids,
                                 batch.neutral_twin.attention_mask, components=[key])
    mask = hand_mask(batch, [list(range(8, 11)), list(range(8, 11)), [8]])
    assert effects.knocked_logit_difference[key] == pytest.approx(
        replaced(model, batch, key, twin.outputs[key], mask), abs=1e-4)


def test_the_default_plan_is_the_v1_knockout(model, batch):
    """Bit for bit: the default plan runs the forwards v1 ran."""
    v1 = ko.knockout_effects(model, [batch], ALL_KEYS)
    explicit = ko.knockout_effects(model, [batch], ALL_KEYS, plan=ko.KnockoutPlan())
    assert v1.knocked_logit_difference == explicit.knocked_logit_difference
    assert v1.clean_logit_difference == explicit.clean_logit_difference
    corrupt = hooks.capture_forward(model, batch.corrupt_input_ids,
                                    batch.corrupt_attention_mask, components=[])
    for key in ("head", 0, 1), ("mlp", 1, 0):
        capture = hooks.capture_forward(model, batch.corrupt_input_ids,
                                        batch.corrupt_attention_mask,
                                        components=[key])
        assert v1.knocked_logit_difference[key] == pytest.approx(
            replaced(model, batch, key, capture.outputs[key]), abs=1e-4)
    assert corrupt is not None


# ==============================================================================
# GROUPS AND GREEDY, ON THE MODEL
# ==============================================================================

def test_a_group_is_knocked_out_jointly(model, batch):
    group = [("head", 0, 1), ("mlp", 1, 0)]
    effects = ko.knock_out_groups(model, [batch], [("pair", group)])
    corrupt = hooks.capture_forward(model, batch.corrupt_input_ids,
                                    batch.corrupt_attention_mask, components=group)
    expected = logit_difference_of(
        hooks.replace_forward(model, batch.input_ids, batch.attention_mask,
                              replacements={key: corrupt.outputs[key] for key in group},
                              positions=batch.readout), batch)
    assert effects.knocked_logit_difference["pair"] == pytest.approx(expected, abs=1e-4)
