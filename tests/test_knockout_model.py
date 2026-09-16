"""
The per-Component knockout against a model: the two invariants on the 2-layer
random Llama, and the CLI seam that turns them into files.

The invariants are the ones that make a ranking trustworthy. A knockout must be
*exactly* the interchange the ADR describes — the Component's output replaced by
what it carried on the corrupt stream, and nothing else touched — and a run that
knocks nothing out must be the clean run. A bug in either would show up as a
plausible ranking rather than as an error.

nnsight 0.7.0 only, gated the way `tests/test_component_hooks.py` gates: the
login-node base environment carries nnsight 0.5.12 for the parent Alignment
repo, so importability is not the question. The arithmetic over the numbers a
forward produced is tested in `tests/test_knockout.py`, which runs everywhere.
"""

from __future__ import annotations

import json
import os

import pytest

nnsight = pytest.importorskip("nnsight")
PINNED = "0.7.0"
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}; these are 0.7.0 behaviours.",
                allow_module_level=True)

import torch                                                       # noqa: E402

import analyze_components                                          # noqa: E402
from component_analysis import dataloaders, hooks, knockout, registry  # noqa: E402
from tests.helpers import TINY, tiny_config                        # noqa: E402
from tests.test_analyze_components_end_to_end import written_files  # noqa: E402, F401
from tests.test_analyze_components_segmentation import (           # noqa: E402, F401
    CELL, read_json, run_cli, sdr_run)
from tests.test_component_hooks import plain_readout_logits        # noqa: E402

SEQ = 12
BATCH = 3

#: The circuit set to every head and every MLP block of the tiny model, which
#: is what the "knocking out nothing reproduces the clean logits" invariant is
#: stated over: it must hold with nothing left outside the circuit.
ALL_COMPONENTS = tuple(
    [("head", layer, head)
     for layer in range(TINY["layers"]) for head in range(TINY["heads"])]
    + [("mlp", layer, 0) for layer in range(TINY["layers"])])


@pytest.fixture(scope="module")
def model():
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())


@pytest.fixture(scope="module")
def batch():
    """One `Batch` of an item-swap pair, as the causal loader would yield it."""
    torch.manual_seed(2)
    clean = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    corrupt = clean.clone()
    corrupt[:, 3] = (clean[:, 3] + 7) % TINY["vocab"]     # the Designation Site
    mask = torch.ones_like(clean)
    mask[2, SEQ - 2:] = 0          # one padded row, so the Readout is not -1
    readout = mask.sum(-1) - 1
    return dataloaders.Batch(
        ids=[f"tiny_{n}" for n in range(BATCH)],
        records=[{} for _ in range(BATCH)],
        input_ids=clean, attention_mask=mask,
        corrupt_input_ids=corrupt, corrupt_attention_mask=mask,
        target_token=torch.tensor([5, 6, 7]),
        distractor_token=torch.tensor([8, 9, 10]),
        readout=readout, honest=None)


def logit_difference_of(logits, batch):
    return hooks.target_minus_distractor(logits.float(), batch.target_token,
                                         batch.distractor_token).tolist()


# ==============================================================================
# THE TWO INVARIANTS
# ==============================================================================

def test_knocking_out_a_component_is_replacing_its_output_with_the_corrupt_one(
        model, batch):
    """The definition of the knockout, checked against the primitive itself.

    The independent value goes through `replace_forward`, whose logits come
    from the model's own head inside the trace; the analysis reads its own from
    the residual through the fp32 readout. Two different routes to the same
    number, so agreement is evidence rather than arithmetic repeated twice.
    """
    keys = [("head", 1, 2), ("mlp", 0, 0)]

    effects = knockout.knockout_effects(model, [batch], keys)

    corrupt = hooks.capture_forward(model, batch.corrupt_input_ids,
                                    batch.corrupt_attention_mask,
                                    components=keys, positions=batch.readout)
    for key in keys:
        expected = logit_difference_of(
            hooks.replace_forward(model, batch.input_ids, batch.attention_mask,
                                  replacements={key: corrupt.outputs[key]},
                                  positions=batch.readout),
            batch)
        assert effects.knocked_logit_diff[key] == pytest.approx(expected,
                                                                abs=1e-4)


def test_at_least_one_knockout_actually_moves_the_metric(model, batch):
    """Guards the test above against passing because nothing ever changed."""
    keys = list(ALL_COMPONENTS)

    effects = knockout.knockout_effects(model, [batch], keys)

    assert any(abs(drop) > 1e-3 for key in keys for drop in effects.drops(key))


def test_knocking_nothing_out_reproduces_the_clean_logits(model, batch):
    """The baseline is the untouched model, with the circuit the whole model.

    Stated over every head and every MLP block on purpose: an invariant that
    only held for a subset would not tell us the knockout loop leaves the rest
    of the forward alone.
    """
    effects = knockout.knockout_effects(model, [batch], ALL_COMPONENTS)

    clean = logit_difference_of(
        plain_readout_logits(model, batch.input_ids, batch.attention_mask),
        batch)
    assert effects.clean_logit_diff == pytest.approx(clean, abs=1e-4)
    assert effects.ids == batch.ids


def test_a_knockout_does_not_leak_into_the_other_components(model, batch):
    """One Component is replaced; its neighbours carry what they always did."""
    victim, neighbour = ("head", 1, 2), ("head", 1, 3)
    corrupt = hooks.capture_forward(model, batch.corrupt_input_ids,
                                    batch.corrupt_attention_mask,
                                    components=[victim],
                                    positions=batch.readout)
    clean = hooks.capture_forward(model, batch.input_ids, batch.attention_mask,
                                  components=[neighbour],
                                  positions=batch.readout)

    under_knockout = hooks.capture_forward(
        model, batch.input_ids, batch.attention_mask, components=[neighbour],
        positions=batch.readout,
        replacements={victim: corrupt.outputs[victim]})

    assert torch.allclose(under_knockout.outputs[neighbour],
                          clean.outputs[neighbour], atol=1e-6)


def test_the_effects_are_per_instance_over_every_batch(model, batch):
    effects = knockout.knockout_effects(model, [batch, batch],
                                        [("head", 0, 0)])

    assert len(effects.ids) == 2 * BATCH
    assert len(effects.clean_logit_diff) == 2 * BATCH
    assert len(effects.knocked_logit_diff[("head", 0, 0)]) == 2 * BATCH
    assert knockout.summarize(effects)[0]["n"] == 2 * BATCH


def test_an_unbuilt_scheme_is_refused_before_any_forward_runs(model, batch):
    with pytest.raises(ValueError, match="future work"):
        knockout.knockout_effects(model, [batch], [("head", 0, 0)],
                                  scheme="zero")


# ==============================================================================
# THE CLI SEAM
# ==============================================================================

@pytest.fixture
def cli_model(monkeypatch):
    """The real CLI, with the tiny model standing in for Llama-3.1-8B.

    The vocabulary is widened to the fake tokenizer's, because the SDR fixture
    tokenizes real SDR prompts word by word and `tests.helpers` sizes its
    vocabulary for random ids.
    """
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    from tests.fakes import FAKE_VOCAB_SIZE

    config = tiny_config(attn_implementation="sdpa")
    config.vocab_size = FAKE_VOCAB_SIZE
    torch.manual_seed(0)
    wrapped = NNsight(LlamaForCausalLM(config).eval())
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: wrapped)
    # Only this analysis: the siblings land in the same list on rebase, and
    # this test is about what the knockout writes.
    monkeypatch.setattr(registry, "ANALYSES", [knockout])
    return wrapped


def test_a_cli_run_writes_the_json_the_png_and_the_head_table_columns(
        sdr_run, cli_model):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(out)) == 0

    written = written_files(out)
    assert os.path.join(*CELL, knockout.SUBDIR, knockout.JSON_NAME) in written
    assert os.path.join(*CELL, knockout.SUBDIR, knockout.PNG_NAME) in written

    table = read_json(out, *CELL, "head_table.json")
    assert "knockout.knockout_logit_diff_drop" in table["columns"]
    assert "knockout.knockout_rank" in table["columns"]
    ranks = sorted(row["knockout.knockout_rank"] for row in table["rows"])
    assert ranks == list(range(1, len(table["rows"]) + 1))


def test_the_written_json_holds_the_numbers_the_chart_draws(sdr_run, cli_model):
    run_dir, out, _records = sdr_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
            "--device", "cpu", "--output-dir", str(out))

    written = read_json(out, *CELL, knockout.SUBDIR, knockout.JSON_NAME)

    assert written["scheme"] == "interchange"
    assert written["baseline"]["n_instances"] > 0, \
        "an empty causal sample would make every assertion here vacuous"
    assert len(written["instances"]) == written["baseline"]["n_instances"]
    assert written["n_components"] == len(written["components"])
    for row in written["components"]:
        assert row["n"] == written["baseline"]["n_instances"]
        assert row["mean_drop"] is not None
        assert 0.0 <= row["accuracy"] <= 1.0


def test_the_head_table_agrees_with_the_json(sdr_run, cli_model):
    """One ranking, two files: a researcher reads the table, an agent the JSON."""
    run_dir, out, _records = sdr_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
            "--device", "cpu", "--output-dir", str(out))

    written = read_json(out, *CELL, knockout.SUBDIR, knockout.JSON_NAME)
    table = read_json(out, *CELL, "head_table.json")

    by_key = {(row["kind"], row["layer"], row["index"]): row
              for row in table["rows"]}
    for one in written["components"]:
        row = by_key[tuple(one["key"])]
        assert row["knockout.knockout_rank"] == one["rank"]
        assert row["knockout.knockout_logit_diff_drop"] == \
            pytest.approx(one["mean_drop"])


def test_the_dry_run_estimates_the_passes_and_writes_no_knockout_output(
        sdr_run, cli_model, capsys):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    printed = capsys.readouterr().out
    assert "knockout:" in printed and "forward pass(es)" in printed
    assert not os.path.exists(os.path.join(str(out), *CELL, knockout.SUBDIR))


def test_the_json_is_valid_json_and_the_png_is_a_png(sdr_run, cli_model):
    run_dir, out, _records = sdr_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
            "--device", "cpu", "--output-dir", str(out))

    with open(os.path.join(str(out), *CELL, knockout.SUBDIR,
                           knockout.JSON_NAME)) as handle:
        json.load(handle)
    with open(os.path.join(str(out), *CELL, knockout.SUBDIR,
                           knockout.PNG_NAME), "rb") as handle:
        assert handle.read(8) == b"\x89PNG\r\n\x1a\n"
