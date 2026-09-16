"""
Library-seam tests for the three shared forward passes in
`component_analysis/hooks.py`, on the 2-layer random Llama.

These are the passes every component analysis is built from, so the assertions
are the invariants that make a later finding trustworthy: a replacement of
nothing changes nothing, a replacement of everything reproduces the other
stream exactly, a replacement of one head leaves its neighbours alone, and an
attention row is a distribution. A patching bug that survived these would be
indistinguishable from a result.

nnsight 0.7.0 only, and for the same reason `tests/test_nnsight_hooks.py`
gates the same way: the login-node base environment carries an nnsight 0.5.12
for the parent Alignment repo, so "nnsight imports" is not the question.
"""

from __future__ import annotations

import pytest

nnsight = pytest.importorskip("nnsight")
PINNED = "0.7.0"
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}; these are 0.7.0 behaviours.",
                allow_module_level=True)

import torch                                               # noqa: E402

from component_analysis import hooks                       # noqa: E402
from tests.helpers import TINY, tiny_config                # noqa: E402

SEQ = 10
BATCH = 2

#: Every head and every MLP block of the tiny model. The two "reproduces the
#: other stream" invariants only hold for the whole model, never for a subset,
#: so the tests that use them say so by construction.
ALL_COMPONENTS = tuple(
    [hooks.EMBED_KEY]
    + [("head", layer, head)
       for layer in range(TINY["layers"]) for head in range(TINY["heads"])]
    + [("mlp", layer, 0) for layer in range(TINY["layers"])])


@pytest.fixture(scope="module")
def model():
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())


@pytest.fixture(scope="module")
def streams():
    """(clean ids, corrupt ids, attention mask).

    The two streams differ at many positions including the last one, unlike a
    real item-swap pair. That is deliberate: when the two streams agree at the
    Readout token, replacing every head and MLP block reproduces the other
    stream's Readout logits even without the embedding, and the invariant that
    the embedding is a sender too would go untested.
    """
    torch.manual_seed(1)
    clean = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    corrupt = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    mask = torch.ones_like(clean)
    mask[1, SEQ - 2:] = 0          # one padded row, so the Readout is not just -1
    return clean, corrupt, mask


def plain_readout_logits(model, input_ids, attention_mask):
    """The Readout logits of an untraced forward, as the independent truth."""
    with torch.no_grad():
        logits = model._model(input_ids=input_ids,
                              attention_mask=attention_mask).logits
    readout = attention_mask.sum(-1) - 1
    return logits[torch.arange(input_ids.shape[0]), readout, :]


# ==============================================================================
# REPLACE
# ==============================================================================

def test_replacing_nothing_reproduces_the_clean_readout_logits(model, streams):
    clean, _corrupt, mask = streams

    got = hooks.replace_forward(model, clean, mask, replacements={})

    assert torch.allclose(got, plain_readout_logits(model, clean, mask),
                          atol=1e-6)


def test_replacing_every_component_with_the_corrupt_capture_gives_corrupt_logits(
        model, streams):
    """The invariant that makes an interchange number meaningful.

    It holds only when the replaced set is every head, every MLP block *and*
    the embedding — a subset leaves part of the residual stream reading the
    clean prompt — so this test says so by using `ALL_COMPONENTS`.
    """
    clean, corrupt, mask = streams

    corrupt_run = hooks.capture_forward(model, corrupt, mask,
                                        components=ALL_COMPONENTS)
    got = hooks.replace_forward(model, clean, mask,
                                replacements=corrupt_run.outputs)

    assert torch.allclose(got, plain_readout_logits(model, corrupt, mask),
                          atol=1e-5)
    # ... and the clean run is genuinely different, so the test cannot pass by
    # the two streams agreeing.
    assert not torch.allclose(got, plain_readout_logits(model, clean, mask),
                              atol=1e-3)


def test_replacing_one_head_leaves_the_other_heads_of_its_layer_alone(model, streams):
    clean, corrupt, mask = streams
    victim = ("head", 1, 2)
    neighbours = [("head", 1, index) for index in range(TINY["heads"])
                  if index != victim[2]]

    corrupt_run = hooks.capture_forward(model, corrupt, mask, components=[victim])
    clean_run = hooks.capture_forward(model, clean, mask, components=neighbours)
    under = hooks.capture_forward(model, clean, mask, components=neighbours,
                                  replacements={victim: corrupt_run.outputs[victim]})

    assert not torch.allclose(under.logits, clean_run.logits, atol=1e-4)
    for key in neighbours:
        assert torch.equal(under.outputs[key], clean_run.outputs[key])


def test_a_replacement_can_be_confined_to_chosen_positions(model, streams):
    """A Segment is a span, so a replacement has to be writable at one."""
    clean, corrupt, mask = streams
    victim = ("head", 0, 1)

    corrupt_run = hooks.capture_forward(model, corrupt, mask, components=[victim])
    nowhere = torch.zeros(SEQ, dtype=torch.bool)
    confined = hooks.replace_forward(
        model, clean, mask,
        replacements={victim: hooks.Replacement(corrupt_run.outputs[victim],
                                                positions=nowhere)})
    everywhere = hooks.replace_forward(
        model, clean, mask, replacements={victim: corrupt_run.outputs[victim]})

    # An empty mask writes nothing, so the clean logits come back exactly.
    assert torch.allclose(confined, hooks.replace_forward(model, clean, mask,
                                                          replacements={}),
                          atol=1e-6)
    assert not torch.allclose(confined, everywhere, atol=1e-4)


def test_a_per_instance_position_mask_writes_only_on_the_rows_it_names(model,
                                                                       streams):
    """A Segment is a per-instance span, so the mask has to be per row.

    Ticket 08's position-specific pass patches K and V receivers at the key
    positions of one Segment, which differ instance by instance.
    """
    clean, corrupt, mask = streams
    victim = ("head", 0, 2)

    corrupt_run = hooks.capture_forward(model, corrupt, mask, components=[victim])
    per_row = torch.zeros(BATCH, SEQ, dtype=torch.bool)
    per_row[0, 4] = True                      # row 0 only, one position only
    confined = hooks.replace_forward(
        model, clean, mask,
        replacements={victim: hooks.Replacement(corrupt_run.outputs[victim],
                                                positions=per_row)})
    untouched = hooks.replace_forward(model, clean, mask, replacements={})

    assert not torch.allclose(confined[0], untouched[0], atol=1e-4)
    assert torch.allclose(confined[1], untouched[1], atol=1e-6)


def test_replacing_an_mlp_block_moves_the_logits_on_its_own(model, streams):
    clean, corrupt, mask = streams
    victim = ("mlp", 0, 0)

    corrupt_run = hooks.capture_forward(model, corrupt, mask, components=[victim])
    clean_run = hooks.capture_forward(model, clean, mask, components=[victim])
    replaced = hooks.replace_forward(model, clean, mask,
                                     replacements={victim: corrupt_run.outputs[victim]})

    assert tuple(clean_run.outputs[victim].shape) == (BATCH, SEQ, TINY["hidden"])
    assert not torch.allclose(replaced, clean_run.logits, atol=1e-4)
    # Replacing it with its own clean capture is a no-op, which is what says
    # the write lands on the MLP output rather than somewhere near it.
    assert torch.allclose(
        hooks.replace_forward(model, clean, mask,
                              replacements={victim: clean_run.outputs[victim]}),
        clean_run.logits, atol=1e-6)


def test_the_readout_defaults_to_the_last_unpadded_position(model, streams):
    clean, _corrupt, mask = streams

    capture = hooks.capture_forward(model, clean, mask, components=[])

    assert capture.readout.tolist() == [SEQ - 1, SEQ - 3]
    assert torch.equal(capture.readout,
                       hooks.readout_positions(mask, [SEQ - 1, SEQ - 3]))


def test_the_residual_stream_is_one_row_per_layer_plus_the_embedding(model, streams):
    clean, _corrupt, mask = streams

    capture = hooks.capture_forward(model, clean, mask,
                                    components=[hooks.EMBED_KEY])

    assert tuple(capture.residual.shape) == (BATCH, TINY["layers"] + 1,
                                             TINY["hidden"])
    rows = torch.arange(BATCH)
    assert torch.allclose(capture.residual[:, 0, :],
                          capture.outputs[hooks.EMBED_KEY][rows,
                                                           capture.readout, :])


# ==============================================================================
# ATTENTION
# ==============================================================================

def test_attention_rows_sum_to_one_and_sdpa_comes_back(model, streams):
    clean, _corrupt, mask = streams
    before = hooks._hf(model).config._attn_implementation
    queries = [3, SEQ - 1]

    rows = hooks.attention_weights(model, clean, mask, layer=1,
                                   heads=[0, 2], query_positions=queries)

    assert tuple(rows.shape) == (BATCH, 2, len(queries), SEQ)
    assert torch.allclose(rows.sum(-1), torch.ones(BATCH, 2, len(queries)),
                          atol=1e-4)
    assert hooks._hf(model).config._attn_implementation == before == hooks.SDPA


def test_attention_query_positions_may_differ_per_instance(model, streams):
    clean, _corrupt, mask = streams

    per_row = hooks.attention_weights(model, clean, mask, layer=0, heads=[1],
                                      query_positions=torch.tensor([[2], [5]]))
    shared_2 = hooks.attention_weights(model, clean, mask, layer=0, heads=[1],
                                       query_positions=[2])
    shared_5 = hooks.attention_weights(model, clean, mask, layer=0, heads=[1],
                                       query_positions=[5])

    assert torch.equal(per_row[0], shared_2[0])
    assert torch.equal(per_row[1], shared_5[1])


def test_sdpa_is_restored_even_when_the_trace_raises(model, streams):
    clean, _corrupt, mask = streams

    with pytest.raises(Exception):
        hooks.attention_weights(model, clean, mask, layer=99, heads=[0],
                                query_positions=[0])

    assert hooks._hf(model).config._attn_implementation == hooks.SDPA


def test_a_key_that_is_not_a_component_is_refused(model, streams):
    clean, _corrupt, mask = streams

    with pytest.raises(ValueError, match="not a Component kind"):
        hooks.capture_forward(model, clean, mask,
                              components=[("neuron", 0, 3)])
    with pytest.raises(ValueError, match="outside the model"):
        hooks.capture_forward(model, clean, mask, components=[("head", 7, 0)])


# ==============================================================================
# THE SCAFFOLD CHECK
# ==============================================================================

def tiny_batches(clean, corrupt, mask):
    """The causal loader's output, hand-built for the tiny model.

    `stub_analysis.measure` is the code the GPU verification job runs, so it is
    exercised here rather than only on the cluster. What it needs from a loader
    is one batch with both streams, the answer tokens and the Readout.
    """
    from component_analysis import dataloaders

    readout = mask.sum(-1) - 1
    items = [{
        "instance_id": f"tiny{row}", "record": {},
        "input_ids": clean[row], "attention_mask": mask[row],
        "corrupt_input_ids": corrupt[row], "corrupt_attention_mask": mask[row],
        "target_token": 3 + row, "distractor_token": 11 + row,
        "readout": int(readout[row]), "honest": None,
    } for row in range(clean.shape[0])]
    return dataloaders.Batches(items, batch_size=clean.shape[0],
                               report={"batch_size": clean.shape[0]})


def test_the_gpu_scaffold_check_runs_end_to_end_on_the_tiny_model(model, streams):
    from types import SimpleNamespace

    from component_analysis import registry
    from tests import stub_analysis

    clean, corrupt, mask = streams
    ctx = registry.AnalysisContext(
        cli=SimpleNamespace(stub_batches=1), intake=None, circuit_spec=None,
        task_spec=None, components=[], cell_dir="", model=model,
        _loaders={"causal": tiny_batches(clean, corrupt, mask)})

    measured = stub_analysis.measure(ctx)

    assert measured["n_instances"] == BATCH
    assert measured["n_keys_replaced"] == len(ALL_COMPONENTS)
    # The same invariant as the hook test, through the code the job runs.
    assert measured["replace_all_with_corrupt_max_abs_logit_error"] < 1e-4
    assert measured["timings"]["batch_size"] == BATCH
    assert measured["timings"]["attention_weights_eager_s"] > 0
    assert hooks._hf(model).config._attn_implementation == hooks.SDPA
