"""
Tests for the attention-pattern analysis (`component_analysis/attention_patterns.py`).

Three seams, in the order the spec's Testing Decisions name them:

  * the **pure** seam — how a row of attention becomes a mass per Segment, how
    `--query-positions` and `--split` are read, and what the head table's top
    Segment is. No model, so these run in both environments;
  * the **library** seam on the 2-layer random Llama — Segment masses sum to
    one per query position, and a head hand-built to attend to one known span
    reports that span's Segment as its top one. The invariant that makes every
    later profile readable: a bug here would look exactly like a finding;
  * the **CLI** seam — the real CLI over a throwaway run directory with real
    SDR prompts, asserting on the files the researcher gets.

The nnsight gate is on the `model` fixture rather than at module level, so the
pure tests keep running in the login-node base environment, which carries
nnsight 0.5.12 for the parent repo.
"""

from __future__ import annotations

import json
import os

import pytest
import torch

from component_analysis import attention_patterns as ap
from component_analysis import segmentation as segments

# ==============================================================================
# FIXTURES FOR THE PURE SEAM
# ==============================================================================

#: A three-Segment scheme, small enough to read an expected value off by hand.
NAMES = ("intro", "designation_site", "readout")


def hand_segmentation(spans, *, n_tokens, record_id="r0"):
    """A `Segmentation` built directly from token spans, no prompt involved."""
    return segments.Segmentation(
        task="sdr", record_id=record_id, n_tokens=n_tokens,
        readout=n_tokens - 1,
        segments={name: segments.Segment(name=name, spans=tuple(spans[name]))
                  for name in spans},
        scheme="mechanism")


# ==============================================================================
# MASS PER SEGMENT
# ==============================================================================

def test_a_row_that_attends_to_one_segment_puts_all_its_mass_there():
    # one instance, one head, one query position, four key tokens
    rows = torch.tensor([[[[0.0, 0.25, 0.75, 0.0]]]])
    ids = torch.tensor([[0, 1, 1, 2]])

    masses, outside = ap.masses_from_rows(rows, ids, n_segments=3)

    assert masses.shape == (1, 1, 1, 3)
    assert masses[0, 0, 0].tolist() == [0.0, 1.0, 0.0]
    assert float(outside.max()) == 0.0


def test_mass_on_a_token_no_segment_claims_is_reported_rather_than_pooled():
    """A token outside the segmentation is padding, and padding is not a Segment.

    If it were silently folded into a Segment the masses would still sum to
    one and the profile would be wrong, so it comes back as its own number.
    """
    rows = torch.tensor([[[[0.5, 0.5]]]])
    ids = torch.tensor([[0, -1]])

    masses, outside = ap.masses_from_rows(rows, ids, n_segments=3)

    assert masses[0, 0, 0].tolist() == [0.5, 0.0, 0.0]
    assert float(outside[0, 0, 0]) == 0.5


def test_segment_ids_name_every_token_once_and_padding_never():
    one = hand_segmentation({"intro": [(0, 2)], "designation_site": [(2, 3)],
                             "readout": [(3, 4)]}, n_tokens=4)

    ids = ap.segment_ids(one, NAMES, n_positions=6)

    assert ids.tolist() == [0, 0, 1, 2, -1, -1]


def test_a_segment_absent_from_an_instance_claims_no_token():
    one = hand_segmentation({"intro": [(0, 3)], "designation_site": [],
                             "readout": [(3, 4)]}, n_tokens=4)

    ids = ap.segment_ids(one, NAMES, n_positions=4)

    assert ids.tolist() == [0, 0, 0, 2]


# ==============================================================================
# QUERY POSITIONS
# ==============================================================================

def test_query_positions_default_to_the_readout():
    assert ap.parse_query_positions(None, NAMES) == ["readout"]


def test_query_positions_are_segment_names_and_a_typo_is_refused_by_name():
    assert ap.parse_query_positions("intro,readout", NAMES) == ["intro", "readout"]

    with pytest.raises(ValueError, match="readut"):
        ap.parse_query_positions("readut", NAMES)


def test_query_slots_carry_one_column_per_token_of_the_widest_instance():
    """A query Segment is a span, so instances contribute different numbers of
    query positions; the short ones are padded and marked invalid."""
    wide = hand_segmentation({"intro": [(0, 3)], "designation_site": [(3, 4)],
                              "readout": [(4, 5)]}, n_tokens=5, record_id="w")
    narrow = hand_segmentation({"intro": [(0, 1)], "designation_site": [(1, 2)],
                                "readout": [(2, 3)]}, n_tokens=3, record_id="n")

    positions, valid, slots = ap.query_slots([wide, narrow], ["intro", "readout"])

    assert slots == [("intro", 0), ("intro", 1), ("intro", 2), ("readout", 0)]
    assert positions.tolist() == [[0, 1, 2, 4], [0, 0, 0, 2]]
    assert valid.tolist() == [[True, True, True, True],
                              [True, False, False, True]]


# ==============================================================================
# SPLITS
# ==============================================================================

def test_split_none_puts_every_instance_in_one_level():
    record = {"designation_polarity": "inversion", "item_polarity": 1}

    assert ap.level_of(record, "none") == ap.ALL_LEVEL


def test_split_by_designation_item_or_both():
    record = {"designation_polarity": "inversion", "item_polarity": 1}

    assert ap.level_of(record, "designation") == "inversion"
    assert ap.level_of(record, "item") == "1"
    assert ap.level_of(record, "both") == "inversion|1"


def test_an_instance_missing_the_factor_is_named_unknown_rather_than_dropped():
    assert ap.level_of({}, "designation") == "unknown"


# ==============================================================================
# THE HEAD TABLE'S TOP SEGMENT
# ==============================================================================

def test_the_top_segment_is_the_one_holding_the_most_mass():
    profile = {"intro": 0.2, "designation_site": 0.5, "readout": 0.3}

    assert ap.top_segment(profile) == ("designation_site", 0.5)


def test_a_profile_with_no_instances_behind_it_has_no_top_segment():
    assert ap.top_segment({}) == (None, None)


# ==============================================================================
# THE LIBRARY SEAM: REAL ATTENTION ON THE TINY MODEL
# ==============================================================================

#: The Segments of the hand-built prompts below, in claim order.
TOY_NAMES = ("intro", "designation_site", "question", "readout")
TOY_SPANS = {"intro": [(0, 3)], "designation_site": [(3, 4)],
             "question": [(4, 7)], "readout": [(7, 8)]}
TOY_TOKENS = 8

#: Where the marker token sits, and therefore which Segment the forced head
#: must report: `designation_site`.
MARKER_POSITION = 3


def nnsight_model(build):
    """`build()` wrapped for nnsight, or a skip when 0.7.0 is not installed.

    The gate is here rather than at module level so the pure tests above keep
    running in the login-node base environment, which carries nnsight 0.5.12
    for the parent Alignment repo.
    """
    nnsight = pytest.importorskip("nnsight")
    if nnsight.__version__ != "0.7.0":
        pytest.skip(f"nnsight {nnsight.__version__} is installed, not the "
                    f"pinned 0.7.0; attention weights are a 0.7.0 behaviour.")
    from nnsight import NNsight

    return NNsight(build())


@pytest.fixture(scope="module")
def tiny_model():
    from transformers import LlamaForCausalLM

    from tests.helpers import tiny_config

    def build():
        torch.manual_seed(0)
        return LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval()

    return nnsight_model(build)


@pytest.fixture(scope="module")
def forced_model():
    """A tiny model whose layer-0 head 0 attends to the marker token, whatever
    else is in the prompt.

    Hand-built rather than trained: the embedding gives the marker token its
    own hidden dimension, `k_proj` reads only that dimension into one component
    of head 0's key, and `q_proj` reads the dimension every other token has
    into the same component of its query. So the marker's key is enormous along
    the one direction every query points in and every other key is zero there.
    The component is index 7 of the 16-wide head, whose rotary frequency is
    ~3e-4 radians per position, so rotary embedding moves the dot product by
    less than a part in ten thousand over a prompt this short.
    """
    from transformers import LlamaForCausalLM

    from tests.helpers import TINY, tiny_config

    def build():
        torch.manual_seed(0)
        model = LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval()
        component = TINY["head_dim"] // 2 - 1        # the slowest rotary pair
        with torch.no_grad():
            embed = model.model.embed_tokens.weight
            embed.zero_()
            embed[:, 1] = 1.0                        # every ordinary token
            embed[MARKER_TOKEN, 1] = 0.0
            embed[MARKER_TOKEN, 0] = 1.0             # the marker, and only it
            attention = model.model.layers[0].self_attn
            model.model.layers[0].input_layernorm.weight.fill_(1.0)
            attention.q_proj.weight.zero_()
            attention.k_proj.weight.zero_()
            attention.q_proj.weight[component, 1] = 1.0
            attention.k_proj.weight[component, 0] = 10.0
        return model

    return nnsight_model(build)


MARKER_TOKEN = 42


def toy_batch(n_instances=2, marker_at=MARKER_POSITION):
    """(input_ids, attention_mask, segmentations) for the hand-built prompts."""
    ids = torch.full((n_instances, TOY_TOKENS), 7, dtype=torch.long)
    ids[:, marker_at] = MARKER_TOKEN
    mask = torch.ones_like(ids)
    segmentations = [hand_segmentation(TOY_SPANS, n_tokens=TOY_TOKENS,
                                       record_id=f"r{i}")
                     for i in range(n_instances)]
    return ids, mask, segmentations


def test_segment_masses_sum_to_one_at_every_query_position(tiny_model):
    """The invariant every profile is read through: a Segment scheme partitions
    the prompt, so a head's mass over it is a distribution."""
    ids, mask, segmentations = toy_batch()
    positions, _valid, _slots = ap.query_slots(segmentations,
                                               ["question", "readout"])
    seg_ids = ap.segment_id_batch(segmentations, TOY_NAMES, TOY_TOKENS)

    masses, checks = ap.batch_masses(
        tiny_model, ids, mask, heads_by_layer={0: [0, 1], 1: [3]},
        positions=positions, ids=seg_ids, n_segments=len(TOY_NAMES))

    assert sorted(masses) == [(0, 0), (0, 1), (1, 3)]
    for key, value in masses.items():
        assert value.shape == (2, positions.shape[1], len(TOY_NAMES)), key
        assert torch.allclose(value.sum(-1), torch.ones(2, positions.shape[1]),
                              atol=1e-4), key
    assert checks["max_abs_sum_minus_one"] < 1e-4
    assert checks["max_outside"] < 1e-6


def test_mass_landing_on_padding_is_counted_outside_the_segments(tiny_model):
    """A padded row's Segments stop at its prompt, and nothing may attend past
    it. If the report ever says otherwise the profile is being read against the
    wrong spans."""
    ids, mask, segmentations = toy_batch()
    mask[1, TOY_TOKENS - 2:] = 0
    positions = torch.tensor([[TOY_TOKENS - 1], [TOY_TOKENS - 3]])
    seg_ids = ap.segment_id_batch(segmentations, TOY_NAMES, TOY_TOKENS)

    _masses, checks = ap.batch_masses(
        tiny_model, ids, mask, heads_by_layer={0: [0]}, positions=positions,
        ids=seg_ids, n_segments=len(TOY_NAMES))

    assert checks["max_outside"] < 1e-6


def test_a_head_forced_to_attend_to_one_span_reports_that_segment_as_its_top(
        forced_model):
    """The end-to-end check that the aggregation points at the right Segment.

    Head 0 of layer 0 is built to attend to the marker token, which sits in
    `designation_site`. Head 1 shares its KV group but not its query
    projection, so it is the unforced comparison: if the masses were being
    read off the wrong head or the wrong query row, both would say the same
    thing. (CONTEXT.md reserves "control" for something else, so the name
    here says what it is.)
    """
    ids, mask, segmentations = toy_batch()
    positions, _valid, _slots = ap.query_slots(segmentations, ["readout"])
    seg_ids = ap.segment_id_batch(segmentations, TOY_NAMES, TOY_TOKENS)

    masses, _checks = ap.batch_masses(
        forced_model, ids, mask, heads_by_layer={0: [0, 1]},
        positions=positions, ids=seg_ids, n_segments=len(TOY_NAMES))

    profile = dict(zip(TOY_NAMES, masses[(0, 0)][0, 0].tolist()))
    assert ap.top_segment(profile)[0] == "designation_site"
    assert profile["designation_site"] > 0.99
    unforced = dict(zip(TOY_NAMES, masses[(0, 1)][0, 0].tolist()))
    assert unforced["designation_site"] < 0.5


def test_the_forced_head_follows_the_marker_when_the_prompt_moves_it(
        forced_model):
    """Moving the marker into another Segment moves the top Segment with it, so
    the previous test cannot be passing on a fixed span."""
    ids, mask, segmentations = toy_batch(marker_at=5)     # inside "question"
    positions, _valid, _slots = ap.query_slots(segmentations, ["readout"])
    seg_ids = ap.segment_id_batch(segmentations, TOY_NAMES, TOY_TOKENS)

    masses, _checks = ap.batch_masses(
        forced_model, ids, mask, heads_by_layer={0: [0]}, positions=positions,
        ids=seg_ids, n_segments=len(TOY_NAMES))

    profile = dict(zip(TOY_NAMES, masses[(0, 0)][0, 0].tolist()))
    assert ap.top_segment(profile)[0] == "question"


def test_sdpa_is_left_in_place_after_the_masses_are_read(tiny_model):
    """Eager attention is this analysis's alone (ADR-0001), so the model it
    hands back to the next analysis must still be on SDPA."""
    from component_analysis import hooks

    ids, mask, segmentations = toy_batch()
    positions, _valid, _slots = ap.query_slots(segmentations, ["readout"])
    seg_ids = ap.segment_id_batch(segmentations, TOY_NAMES, TOY_TOKENS)

    ap.batch_masses(tiny_model, ids, mask, heads_by_layer={0: [0]},
                    positions=positions, ids=seg_ids,
                    n_segments=len(TOY_NAMES))

    assert hooks.attention_implementation(tiny_model) == hooks.SDPA


# ==============================================================================
# THE CLI SEAM
# ==============================================================================

from tests.test_analyze_components_segmentation import (  # noqa: E402,F401
    CELL, build_sdr_split, read_json, run_cli, sdr_run)


@pytest.fixture
def analysis_model():
    """The tiny Llama the CLI run reads attention from.

    Its vocabulary is widened past `FakeWordTokenizer`'s 256 words, because the
    fixture's prompts are tokenized with the fake and a real embedding table
    has to hold every id it emits.
    """
    from transformers import LlamaForCausalLM

    from tests.helpers import tiny_config

    def build():
        config = tiny_config(attn_implementation="sdpa")
        config.vocab_size = 300
        torch.manual_seed(0)
        return LlamaForCausalLM(config).eval()

    return nnsight_model(build)


@pytest.fixture
def sdr_cell(sdr_run, analysis_model, monkeypatch):
    """The SDR fixture, plus an honest-twin dataset beside it and a model.

    (run dir, output dir, the pressure records, the twin records).
    """
    import analyze_components
    from component_analysis import instances as ca_instances

    run_dir, out, records = sdr_run
    data_dir = json.loads((run_dir / "config.json").read_text())["data_dir"]
    tokenizer = ca_instances.load_analysis_tokenizer("llama-tiny")
    twin = build_sdr_split(os.path.join(data_dir, "sdr_honest"), tokenizer)
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: analysis_model)
    return run_dir, out, records, twin


def patterns_of(out):
    return read_json(out, *CELL, "attention", ap.PATTERNS_FILE)


def test_the_cli_run_writes_the_patterns_json_and_its_figures(sdr_cell):
    run_dir, out, records, _twin = sdr_cell

    assert run_cli(str(run_dir), "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    directory = os.path.join(str(out), *CELL, "attention")
    written = sorted(os.listdir(directory))
    assert ap.PATTERNS_FILE in written
    assert "patterns_all.png" in written and "patterns_all.json" in written
    assert "top_heads.png" in written and "top_heads.json" in written
    assert ap.TWIN_SEGMENTATION_FILE in written
    # Every PNG has the JSON twin an agent with no browser reads instead.
    for name in written:
        if name.endswith(".png"):
            assert name[:-4] + ".json" in written


def test_the_patterns_json_has_the_documented_schema(sdr_cell):
    run_dir, out, records, _twin = sdr_cell
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    payload = patterns_of(out)

    assert payload["analysis"] == ap.NAME
    assert payload["task"] == "sdr"
    assert payload["query_positions"] == ["readout"]
    assert payload["column_query_position"] == "readout"
    assert payload["segments"] == list(segments.MECHANISM_SEGMENTS)
    assert [one["label"] for one in payload["components"]] == ["L0H0", "L0H2"]
    assert [one["name"] for one in payload["conditions"]] == ["pressure",
                                                              "honest_twin"]
    pressure = payload["conditions"][0]
    assert pressure["paired"] is False and pressure["descriptive"] is True
    assert pressure["n_instances"] == len(records)
    assert pressure["checks"]["n_nan"] == 0
    assert pressure["checks"]["sums_to_one"] is True
    # The fixture has no Matched Honest survivors file, so the paired condition
    # says why it did not run rather than going missing.
    assert [one["condition"] for one in payload["skipped"]] == \
        ["honest_instruction"]


def test_every_head_profile_is_a_distribution_over_the_segments(sdr_cell):
    run_dir, out, _records, _twin = sdr_cell
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    payload = patterns_of(out)

    for condition in payload["conditions"]:
        for level in condition["levels"]:
            assert level["n"] > 0, (condition["name"], level["level"])
            for name, per_query in level["masses"].items():
                total = sum(per_query["readout"].values())
                assert abs(total - 1.0) < 1e-4, (condition["name"], name)


def test_the_split_gives_one_level_per_designation_polarity(sdr_cell):
    run_dir, out, records, _twin = sdr_cell
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    levels = {level["level"]: level["n"]
              for level in patterns_of(out)["conditions"][0]["levels"]}

    assert levels["all"] == len(records)
    assert set(levels) == {"all", "identity", "inversion"}
    assert levels["identity"] + levels["inversion"] == levels["all"]


def test_split_none_leaves_only_the_pooled_level(sdr_cell):
    run_dir, out, _records, _twin = sdr_cell
    run_cli(str(run_dir), "--num-kv-heads", "2", "--split", "none",
            "--output-dir", str(out))

    payload = patterns_of(out)

    assert [level["level"] for level in payload["conditions"][0]["levels"]] == \
        ["all"]
    assert os.path.exists(os.path.join(str(out), *CELL, "attention",
                                       "patterns_all.png"))


def test_the_head_table_carries_the_top_segment_under_both_conditions(sdr_cell):
    run_dir, out, _records, _twin = sdr_cell
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    table = read_json(out, *CELL, "head_table.json")
    heads = [row for row in table["rows"] if row["kind"] == "head"]

    for column in ("query_position", "pressure_top_segment",
                   "pressure_top_mass",
                   "honest_twin_descriptive_top_segment",
                   "honest_twin_descriptive_top_mass"):
        assert f"{ap.NAME}.{column}" in table["columns"]
    for row in heads:
        assert row[f"{ap.NAME}.query_position"] == "readout"
        assert row[f"{ap.NAME}.pressure_top_segment"] in \
            segments.MECHANISM_SEGMENTS
        assert 0.0 <= row[f"{ap.NAME}.pressure_top_mass"] <= 1.0
        assert row[f"{ap.NAME}.honest_twin_descriptive_top_segment"] in \
            segments.MECHANISM_SEGMENTS
    # The MLP block in this circuit has no attention pattern and says so by
    # holding no value, rather than by holding a zero.
    mlp = [row for row in table["rows"] if row["kind"] == "mlp"]
    assert mlp and mlp[0][f"{ap.NAME}.pressure_top_segment"] is None


def test_the_honest_twin_gets_its_own_segmentation_beside_its_numbers(sdr_cell):
    """Different prompts, so borrowing the pressure split's spans would read
    every twin profile against the wrong tokens."""
    run_dir, out, _records, twin = sdr_cell
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    written = read_json(out, *CELL, "attention", ap.TWIN_SEGMENTATION_FILE)

    assert written["condition"] == "honest_twin"
    assert written["n_instances"] == len(twin)
    assert written["segment_names"] == list(segments.MECHANISM_SEGMENTS)
    assert written["dataset"].endswith("sdr_honest")


def test_the_honest_twin_condition_says_why_it_did_not_run(sdr_cell):
    run_dir, out, _records, _twin = sdr_cell

    run_cli(str(run_dir), "--num-kv-heads", "2",
            "--attention-honest-twin", "off", "--output-dir", str(out))

    payload = patterns_of(out)
    assert [one["name"] for one in payload["conditions"]] == ["pressure"]
    assert {one["condition"] for one in payload["skipped"]} == \
        {"honest_instruction", "honest_twin"}


def test_a_query_position_that_is_not_a_segment_fails_before_the_model_loads(
        sdr_run):
    run_dir, out, _records = sdr_run

    with pytest.raises(ValueError, match="pressure_clase"):
        run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                "--query-positions", "pressure_clase", "--output-dir", str(out))


def test_dry_run_prints_the_cost_and_writes_nothing_of_the_analysis(sdr_run,
                                                                    capsys):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    printed = capsys.readouterr().out
    assert f"{ap.NAME}: " in printed
    assert "eager forward(s)" in printed
    assert not os.path.exists(os.path.join(str(out), *CELL, "attention"))


def test_a_multi_token_query_segment_is_averaged_over_its_tokens(sdr_cell):
    """The Pressure Clause is many tokens wide, so every instance contributes
    the mean of its own tokens and not one row per token."""
    run_dir, out, records, _twin = sdr_cell

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--query-positions",
                   "pressure_clause,readout", "--output-dir", str(out)) == 0

    payload = patterns_of(out)
    level = payload["conditions"][0]["levels"][0]
    assert payload["query_positions"] == ["pressure_clause", "readout"]
    assert level["n_by_query_position"] == {"pressure_clause": len(records),
                                            "readout": len(records)}
    for per_query in level["masses"].values():
        assert abs(sum(per_query["pressure_clause"].values()) - 1.0) < 1e-4


def test_this_analysis_module_does_not_import_nnsight():
    """`build_parser` imports every registered analysis on the login node, so
    an nnsight import at module scope here would break `--dry-run` where
    nnsight 0.7.0 is not installed.

    A fresh interpreter on purpose, as `tests/test_component_analysis.py` does
    for the intake layer: `sys.modules` is process-wide, so an in-process check
    would pass or fail on what an earlier test happened to import.
    """
    import subprocess
    import sys

    probe = ("import component_analysis.attention_patterns, sys; "
             "assert 'nnsight' not in sys.modules, sorted(sys.modules)")
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


# ==============================================================================
# WHICH HEADS THE BAR CHART SHOWS
# ==============================================================================

def inject_column(out, column, values):
    """Put a column into the cell's written head table, as a later analysis would.

    Ticket 07 writes `knockout.rank` on a second pass over the same cell, so
    this is what this analysis finds there when it is rerun.
    """
    path = os.path.join(str(out), *CELL, "head_table.json")
    with open(path) as handle:
        table = json.load(handle)
    table["columns"].append(column)
    for row in table["rows"]:
        row[column] = values.get((row["kind"], row["layer"], row["index"]))
    with open(path, "w") as handle:
        json.dump(table, handle)


def test_the_bar_chart_falls_back_to_layer_order_with_no_knockout_column(sdr_cell):
    run_dir, out, _records, _twin = sdr_cell

    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    chart = read_json(out, *CELL, "attention", "top_heads.json")
    assert "layer order" in chart["ranked_by"]
    assert chart["rows"] == ["L0H0", "L0H2"]


def test_the_bar_chart_ranks_by_knockout_once_that_column_exists(sdr_cell):
    """Rank 1 is ticket 07's largest signed drop, so it is shown first.

    The MLP block is in the same ranked list and has no attention pattern, so
    a chart of heads must skip it rather than plotting an empty row.
    """
    run_dir, out, _records, _twin = sdr_cell
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))
    inject_column(out, "knockout.rank",
                  {("head", 0, 0): 3, ("head", 0, 2): 1, ("mlp", 1, 0): 2})

    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    chart = read_json(out, *CELL, "attention", "top_heads.json")
    assert chart["ranked_by"].startswith("knockout.rank")
    assert "ascending" in chart["ranked_by"]
    assert chart["rows"] == ["L0H2", "L0H0"]


def test_the_bar_chart_shows_at_most_the_requested_number_of_heads(sdr_cell):
    run_dir, out, _records, _twin = sdr_cell

    run_cli(str(run_dir), "--num-kv-heads", "2", "--attention-top-k", "1",
            "--output-dir", str(out))

    chart = read_json(out, *CELL, "attention", "top_heads.json")
    assert chart["rows"] == ["L0H0"]
    assert len(chart["matrix"]) == 1


def test_a_query_segment_absent_from_the_whole_batch_counts_per_level():
    """Each level counts its own rows as absent, not the whole batch.

    `designation_suffix` is absent from every instance of the saved FAR run, so
    a query position on it takes this path. Adding the batch size to every
    level would tell a reader that identity and inversion each lost as many
    instances as the two of them together.
    """
    profiles = ap.Profiles(head_keys=[("head", 0, 0)], names=list(NAMES),
                           query_names=["intro"])

    profiles.add({(0, 0): torch.zeros(3, 0, len(NAMES))},
                 [[ap.ALL_LEVEL, "identity"], [ap.ALL_LEVEL, "inversion"],
                  [ap.ALL_LEVEL, "identity"]],
                 torch.zeros(3, 0, dtype=torch.bool), [])

    written = profiles.as_json()
    absent = {one["level"]: one["n_absent_by_query_position"]["intro"]
              for one in written}
    assert absent == {ap.ALL_LEVEL: 3, "identity": 2, "inversion": 1}
