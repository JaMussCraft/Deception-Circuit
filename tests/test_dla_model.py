"""
Library- and CLI-seam tests for direct logit attribution and the logit lens on
a model.

The invariant that makes a DLA table trustworthy is that it adds up: every
Component's contribution plus the embedding's, read through the final norm at
the Readout, is the model's own logit difference there. A projection with a
transposed weight, a head slice off by one group or a scale taken from the
wrong vector all still produce a plausible-looking ranking, and the sum is what
catches them. So the sum is tested two ways — against the total, and for one
head against a contribution computed by hand from the raw HuggingFace modules,
which is an independent source of truth rather than the same arithmetic twice.

The tiny model is 2 layers of 4 heads in fp32 on the CPU, so "within tolerance"
here is tight; on the real bfloat16 model the same reconstruction is recorded
in `dla.json` rather than asserted (see `sum_check`).

nnsight 0.7.0 only, gated the way `tests/test_component_hooks.py` gates: the
login-node base environment carries an nnsight 0.5.12 for the parent Alignment
repo, so "nnsight imports" is not the question. The rules that need no model
are in `tests/test_dla.py` and run in both environments.
"""

from __future__ import annotations

import os

import pytest

from component_analysis import dla

# ==============================================================================
# THE NUMBERS, ON THE TINY MODEL
# ==============================================================================

nnsight = pytest.importorskip("nnsight")
PINNED = "0.7.0"
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}; these run a traced forward.",
                allow_module_level=True)

import torch                                               # noqa: E402

from component_analysis import hooks                       # noqa: E402
from tests.helpers import TINY, tiny_config                # noqa: E402

SEQ = 10
BATCH = 2

#: The circuit set to every head and every MLP block, plus the embedding. The
#: sum invariant holds for this set and for no subset of it, so the tests that
#: use it say so by construction.
ALL_KEYS = tuple(
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
def prompts():
    """(input ids, attention mask). One row is padded, so the Readout is not -1."""
    torch.manual_seed(1)
    ids = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    mask = torch.ones_like(ids)
    mask[1, SEQ - 2:] = 0
    return ids, mask


@pytest.fixture(scope="module")
def answers():
    """(Target ids, Distractor ids), two different tokens per row."""
    return torch.tensor([7, 11]), torch.tensor([13, 5])


@pytest.fixture(scope="module")
def capture(model, prompts):
    ids, mask = prompts
    return hooks.capture_forward(model, ids, mask, components=ALL_KEYS)


def total_logit_difference(model, capture, answers):
    """The model's own fp32 logit difference at the Readout — the thing to match."""
    target, distractor = answers
    return hooks.target_minus_distractor(
        hooks.readout_logits(model, capture.residual[:, -1, :]),
        target, distractor)


def test_dla_over_every_component_and_the_embedding_sums_to_the_logit_difference(
        model, capture, answers):
    """The invariant. It holds only for the whole model, never for a subset.

    With the scale held fixed at the one the final norm applied, the readout is
    linear in the residual, so the parts add up to the whole. A transposed
    `o_proj` slice, a head read from the wrong KV group or a per-Component
    scale would all still produce a plausible ranking and would all fail here.
    """
    target, distractor = answers

    per_component = dla.component_logit_difference(
        model, capture, ALL_KEYS, target=target, distractor=distractor)

    assert per_component.shape == (BATCH, len(ALL_KEYS))
    assert torch.allclose(per_component.sum(dim=1),
                          total_logit_difference(model, capture, answers),
                          atol=1e-4)


def test_one_heads_contribution_matches_the_same_thing_computed_by_hand(
        model, capture, answers):
    """An independent source of truth, so the sum cannot be right by symmetry.

    Computed straight off the HuggingFace modules — the head's `o_proj` input
    slice, the matching columns of `o_proj.weight`, the final norm's own weight
    and epsilon at the residual's scale, the unembedding — rather than through
    anything the module under test shares.
    """
    target, distractor = answers
    key = ("head", 1, 2)
    hf = model._model                      # tests may reach through the wrapper
    rows = torch.arange(BATCH)
    readout = capture.readout

    with torch.no_grad():
        z = capture.outputs[key][rows, readout, :].float()      # [batch, head_dim]
        weight = hf.model.layers[1].self_attn.o_proj.weight.float()
        head_dim = TINY["head_dim"]
        contribution = z @ weight[:, 2 * head_dim:3 * head_dim].float().T
        residual = capture.residual[:, -1, :].float()
        scale = torch.rsqrt(residual.pow(2).mean(-1, keepdim=True)
                            + hf.model.norm.variance_epsilon)
        normed = contribution * scale * hf.model.norm.weight.float()
        logits = normed @ hf.lm_head.weight.float().T
        expected = logits[rows, target] - logits[rows, distractor]

    got = dla.component_logit_difference(model, capture, [key], target=target,
                                         distractor=distractor)

    assert torch.allclose(got[:, 0], expected, atol=1e-4)


def test_the_logit_lens_has_one_row_per_layer_plus_the_embedding(model, capture,
                                                                 answers):
    target, distractor = answers

    lens = dla.lens_logit_difference(model, capture, target=target,
                                     distractor=distractor)

    assert lens.shape == (BATCH, TINY["layers"] + 1)


def test_the_last_lens_row_is_the_models_own_logit_difference(model, capture,
                                                              answers):
    """The last cumulative residual *is* the final one, so the lens ends on it."""
    target, distractor = answers

    lens = dla.lens_logit_difference(model, capture, target=target,
                                     distractor=distractor)

    assert torch.allclose(lens[:, -1],
                          total_logit_difference(model, capture, answers),
                          atol=1e-5)


# ==============================================================================
# THE CLI SEAM
# ==============================================================================

import json                                                # noqa: E402

import analyze_components                                  # noqa: E402
from component_analysis import registry                    # noqa: E402
from tests.fakes import FAKE_VOCAB_SIZE                    # noqa: E402
from tests.test_analyze_components_end_to_end import written_files  # noqa: E402,F401
from tests.test_analyze_components_segmentation import (   # noqa: E402,F401
    CELL, build_sdr_split, read_json, run_cli, sdr_run)

DLA_FILES = [dla.JSON_NAME, dla.LENS_JSON_NAME, dla.PNG_NAME, dla.LENS_PNG_NAME]


def cli_model():
    """The tiny model, widened to the fake tokenizer's vocabulary.

    `tests.helpers.tiny_config` pins 101 tokens and `FakeWordTokenizer` hands
    out up to 256 ids, so the CLI seam needs its own config rather than the
    shared one; every other dimension is the shared model's.
    """
    from nnsight import NNsight
    from transformers import LlamaConfig, LlamaForCausalLM

    torch.manual_seed(0)
    config = LlamaConfig(
        hidden_size=TINY["hidden"], num_hidden_layers=TINY["layers"],
        num_attention_heads=TINY["heads"], num_key_value_heads=TINY["kv_heads"],
        intermediate_size=TINY["intermediate"], vocab_size=FAKE_VOCAB_SIZE,
        max_position_embeddings=TINY["max_pos"], attn_implementation="sdpa")
    return NNsight(LlamaForCausalLM(config).eval())


@pytest.fixture
def dla_run(sdr_run, monkeypatch, tmp_path):
    """The SDR CLI fixture with an Honest Twin beside it and a model to run.

    The twin is the same split with `target` and `distractor` swapped, which is
    what `harvest_honest_twins` does to a real one. So the twin's DLA, once the
    module has negated it back into the deception direction, must come out
    *equal* to the pressure column — and would come out as its negative if the
    negation were missing.
    """
    run_dir, out, records = sdr_run
    monkeypatch.setattr(registry, "ANALYSES", ["component_analysis.dla"])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: cli_model())

    twin = [dict(record, target=record["distractor"],
                 distractor=record["target"], condition="honest")
            for record in records]
    twin_dir = tmp_path / "datasets" / "sdr_honest"
    from datasets import Dataset, DatasetDict

    DatasetDict({"test": Dataset.from_list(twin)}).save_to_disk(str(twin_dir))
    with open(os.path.join(str(twin_dir), "dataset_config.json"), "w") as handle:
        json.dump({"task": "sdr", "max_seq_length": 128, "margin_thresh": 1.0},
                  handle)
    return run_dir, out, records


def test_the_cli_run_writes_both_json_files_and_both_figures(dla_run):
    run_dir, out, _records = dla_run

    assert run_cli(str(run_dir), "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    written = written_files(out)
    for name in DLA_FILES:
        assert os.path.join(*CELL, dla.SUBDIR, name) in written
    assert all(os.path.getsize(os.path.join(str(out), *CELL, dla.SUBDIR, name))
               > 0 for name in DLA_FILES)


def test_the_dla_json_has_the_documented_schema(dla_run):
    run_dir, out, records = dla_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    payload = read_json(out, *CELL, dla.SUBDIR, dla.JSON_NAME)

    assert payload["schema_version"] == dla.SCHEMA_VERSION
    assert payload["analysis"] == "dla" and payload["task"] == "sdr"
    assert "deceptive answer" in payload["metric"]
    assert payload["suppression_margin"] == dla.DEFAULT_SUPPRESSION_MARGIN
    pressure = payload["conditions"]["pressure"]
    assert pressure["n_instances"] == len(records)
    assert pressure["direction_sign"] == 1
    for row in pressure["components"]:
        stats = row["levels"]["all"]
        assert set(row) == {"key", "kind", "layer", "index", "label", "levels"}
        assert stats["n"] == len(records)
        assert stats["mean"] is not None and stats["se"] is not None
    assert pressure["embedding"]["levels"]["all"]["n"] == len(records)


def test_the_head_table_gains_the_dla_columns_under_its_own_name(dla_run):
    run_dir, out, _records = dla_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    table = read_json(out, *CELL, "head_table.json")

    for column in ("dla.pressure", "dla.pressure_se",
                   "dla.honest_twin_descriptive",
                   "dla.honest_twin_descriptive_se",
                   "dla.suppression", "dla.differential"):
        assert column in table["columns"]
    assert all(row["dla.pressure"] is not None for row in table["rows"])
    assert all(row["dla.suppression"] in (True, False) for row in table["rows"])
    assert not any(row["kind"] == "embed" for row in table["rows"]), \
        "the embedding is a sender, not a Component, and has no row"


def test_the_honest_twin_column_is_read_in_the_deception_direction(dla_run):
    """The fixture's twin is the split with the two answers swapped.

    So a column that respected the twin's own labels would be the negative of
    the pressure column. Equality is what says the negation happened.
    """
    run_dir, out, _records = dla_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    table = read_json(out, *CELL, "head_table.json")

    assert table["rows"], "no Components to compare"
    for row in table["rows"]:
        assert row["dla.honest_twin_descriptive"] == pytest.approx(
            row["dla.pressure"], abs=1e-5)


def test_the_logit_lens_json_has_one_row_per_layer_and_names_the_flip(dla_run):
    run_dir, out, _records = dla_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    payload = read_json(out, *CELL, dla.SUBDIR, dla.LENS_JSON_NAME)

    pressure = payload["conditions"]["pressure"]
    assert pressure["n_rows"] == TINY["layers"] + 1
    level = pressure["levels"]["all"]
    assert len(level["mean"]) == TINY["layers"] + 1
    assert len(level["se"]) == TINY["layers"] + 1
    assert pressure["sign_flip_row"] == dla.sign_flip_row(level["mean"])
    assert pressure["sign_flip_layer"] == dla.layer_of_row(
        pressure["sign_flip_row"]), "a row is not a layer, and both are given"


def test_the_run_records_whether_the_sum_invariant_held_on_this_model(dla_run):
    """The invariant the library test asserts, measured where the run happened."""
    run_dir, out, _records = dla_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    check = read_json(out, *CELL, dla.SUBDIR, dla.JSON_NAME)["sum_check"]

    assert check["n_senders"] == 1 + TINY["layers"] * (TINY["heads"] + 1)
    assert check["max_abs_error"] < 1e-3


def test_a_condition_with_no_data_is_named_and_skipped_rather_than_failing(dla_run):
    """No Matched Honest survivors here, so the paired condition cannot run."""
    run_dir, out, _records = dla_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    payload = read_json(out, *CELL, dla.SUBDIR, dla.JSON_NAME)

    assert "honest_instruction" in payload["skipped"]
    assert "honest_instruction" not in payload["conditions"]
    table = read_json(out, *CELL, "head_table.json")
    assert all(row["dla.honest_instruction"] is None for row in table["rows"])


def test_conditions_can_be_chosen_on_the_command_line(dla_run):
    run_dir, out, _records = dla_run

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--dla-conditions",
                   "pressure", "--output-dir", str(out)) == 0

    payload = read_json(out, *CELL, dla.SUBDIR, dla.JSON_NAME)
    assert set(payload["conditions"]) == {"pressure"}


def test_a_split_writes_a_level_per_stratum_beside_the_ungrouped_mean(dla_run):
    run_dir, out, _records = dla_run

    run_cli(str(run_dir), "--num-kv-heads", "2", "--dla-split", "designation",
            "--dla-conditions", "pressure", "--output-dir", str(out))

    payload = read_json(out, *CELL, dla.SUBDIR, dla.JSON_NAME)
    levels = payload["conditions"]["pressure"]["components"][0]["levels"]
    assert "all" in levels
    assert any(name.startswith("designation_polarity=") for name in levels)
    assert sum(levels[name]["n"] for name in levels if name != "all") == \
        levels["all"]["n"], "every instance belongs to exactly one stratum"


def test_the_dry_run_estimates_every_condition_and_writes_no_dla_files(dla_run,
                                                                       capsys):
    run_dir, out, records = dla_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    printed = capsys.readouterr().out
    assert f"pressure {len(records)} instance(s)" in printed
    assert "honest_twin" in printed
    assert not os.path.exists(os.path.join(str(out), *CELL, dla.SUBDIR))


def test_max_batches_stops_a_condition_early(dla_run):
    """The smoke-run flag: a GPU run should be shortenable without editing code."""
    run_dir, out, records = dla_run

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--dla-conditions",
                   "pressure", "--dla-max-batches", "1", "--dla-sum-check",
                   "off", "--output-dir", str(out)) == 0

    payload = read_json(out, *CELL, dla.SUBDIR, dla.JSON_NAME)
    pressure = payload["conditions"]["pressure"]
    assert pressure["n_instances"] == payload["sources"]["pressure"]["batch_size"]
    assert pressure["n_instances"] < len(records), "one batch, not the split"
    assert payload["sum_check"] is None, "--dla-sum-check off spends no pass"


def test_an_unknown_condition_is_refused_by_name(dla_run, capsys):
    run_dir, out, _records = dla_run

    # Refused by argparse at parse time, before any model is loaded — the
    # same moment `--attention-conditions` refuses one (ticket 06's open
    # question 4). SystemExit is what argparse raises after printing the
    # message, and the message has to name the condition it refused: a bare
    # SystemExit is satisfied by any argparse error at all, including one that
    # never mentions the typo.
    with pytest.raises(SystemExit):
        run_cli(str(run_dir), "--num-kv-heads", "2", "--dla-conditions",
                "nosuch", "--output-dir", str(out))
    assert "nosuch" in capsys.readouterr().err


def test_a_twin_directory_that_is_not_the_honest_condition_is_refused(
        dla_run, tmp_path, monkeypatch):
    """The twin column is negated, so pointing the flag elsewhere would invert it.

    `--dla-honest-twin-dir` takes any directory. A deceptive split behind it
    would be read as an Honest Twin and every Component reported with its sign
    flipped, which is a silent wrong answer rather than a failure.
    """
    run_dir, out, records = dla_run
    from datasets import Dataset, DatasetDict

    impostor = tmp_path / "datasets" / "sdr_not_honest"
    DatasetDict({"test": Dataset.from_list(
        [dict(r, condition="deceptive") for r in records])}).save_to_disk(
            str(impostor))
    with open(os.path.join(str(impostor), "dataset_config.json"), "w") as handle:
        json.dump({"task": "sdr", "max_seq_length": 128, "margin_thresh": 1.0},
                  handle)

    run_cli(str(run_dir), "--num-kv-heads", "2", "--dla-honest-twin-dir",
            str(impostor), "--output-dir", str(out))

    payload = read_json(out, *CELL, dla.SUBDIR, dla.JSON_NAME)
    assert "honest_twin" in payload["skipped"]
    assert "not an Honest Twin split" in payload["skipped"]["honest_twin"]


def test_the_differential_is_the_paired_difference_over_the_same_ids(model,
                                                                     prompts,
                                                                     answers):
    """`paired` means the same instance ids on both sides, not two populations.

    The Honest-Instruction Counterfactual here is the pressure prompt itself,
    so every Component's differential must be exactly zero and both sides must
    name the same instances. A differential taken between a full-split pressure
    mean and a paired honest mean would satisfy neither.
    """
    from component_analysis.dataloaders import Batch, HonestPair

    ids, mask = prompts
    target, distractor = answers
    rows = list(range(BATCH))
    batch = Batch(
        ids=[f"i{row}" for row in rows],
        records=[{"designation_polarity": "identity"} for _ in rows],
        input_ids=ids, attention_mask=mask,
        corrupt_input_ids=ids, corrupt_attention_mask=mask,
        target_token=target, distractor_token=distractor,
        readout=hooks.readout_positions(mask),
        honest=HonestPair(rows=rows, input_ids=ids.clone(),
                          attention_mask=mask.clone(),
                          clause_span=torch.zeros(BATCH, 2, dtype=torch.long),
                          instructions=["itself"] * BATCH))

    paired, honest, differential, unpaired = dla.measure_paired(
        model, [batch], ALL_KEYS)

    assert unpaired == []
    assert paired.ids == honest.ids == differential.ids == batch.ids
    for key in ALL_KEYS:
        assert differential.component_stats(key)["all"]["mean"] == \
            pytest.approx(0.0, abs=1e-5)


def test_a_differential_over_different_instances_is_refused(model, prompts,
                                                            answers):
    """The guard that makes the column paired rather than merely subtracted."""
    left = dla.Tally(ALL_KEYS)
    left.ids = ["a", "b"]
    right = dla.Tally(ALL_KEYS)
    right.ids = ["a", "c"]

    with pytest.raises(ValueError, match="same instances"):
        dla.paired_difference(left, right)
