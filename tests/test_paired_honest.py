"""
The paired Honest-Instruction Counterfactual columns and figures (ticket 06),
at the seams that need no model.

The paired condition is the one contrast in the descriptive analyses that is
*causal*: the same instances, the same instance ids, the Pressure Clause
swapped for its Matched Honest Instruction. The Honest Twin beside it is a
different population and is only ever descriptive. Everything here asserts the
one property that keeps those two apart in a CSV a researcher reads by column
header, and the two figures that show the paired contrast on its own.

Nothing here loads a model or imports nnsight, so it runs in both
environments. The CLI seam over a synthetic paired dataset, which does need
one, is `tests/test_paired_honest_cli.py`.
"""

from __future__ import annotations

import json
import os

import pytest

from component_analysis import attention_patterns as ap
from component_analysis import dla


# ==============================================================================
# --attention-conditions
# ==============================================================================

class Cli:
    """A stand-in for the parsed CLI namespace, with only the flags in play."""

    def __init__(self, **flags):
        self.__dict__.update(flags)


def test_the_attention_conditions_default_to_all_three():
    assert ap.wanted_conditions(Cli()) == list(ap.CONDITIONS)


def test_the_attention_conditions_are_chosen_by_name():
    cli = Cli(attention_conditions="honest_instruction,pressure")

    assert ap.wanted_conditions(cli) == [ap.PRESSURE, ap.HONEST_INSTRUCTION]


def test_an_unknown_attention_condition_is_refused_by_name():
    cli = Cli(attention_conditions="pressure,honest")

    with pytest.raises(ValueError) as failure:
        ap.wanted_conditions(cli)

    assert "honest" in str(failure.value)
    assert ap.HONEST_INSTRUCTION in str(failure.value)


def test_the_derived_paired_pressure_condition_cannot_be_asked_for():
    """`pressure_paired` is computed beside the paired honest side, never alone.

    Asking for it would produce a "paired" column with nothing paired against
    it, which is exactly the reading spec user story 27 exists to prevent.
    """
    with pytest.raises(ValueError):
        ap.wanted_conditions(Cli(attention_conditions=ap.PRESSURE_PAIRED))


# ==============================================================================
# THE HEAD-TABLE COLUMNS
# ==============================================================================

SEGMENTS = ["designation_site", "item_1_question", "readout"]
HEADS = [("head", 5, 1), ("head", 9, 3)]


def profile(**masses):
    return {name: masses.get(name, 0.0) for name in SEGMENTS}


def condition(name, *, masses, n=4, paired=False):
    return {
        "name": name,
        "kind": name.replace("_", " "),
        "paired": paired,
        "descriptive": not paired,
        "dataset": None,
        "n_instances": n,
        "n_loaded": n,
        "batches": 1,
        "levels": [{"level": ap.ALL_LEVEL, "n": n,
                    "n_by_query_position": {"readout": n},
                    "n_absent_by_query_position": {"readout": 0},
                    "masses": masses}],
        "checks": {"max_abs_sum_minus_one": 0.0, "max_outside": 0.0,
                   "n_batches": 1, "n_nan": 0, "sums_to_one": True},
        "notes": [],
    }


def patterns_payload(*conditions):
    return {
        "analysis": ap.NAME,
        "schema_version": ap.SCHEMA_VERSION,
        "task": "sdr",
        "circuit": "delta",
        "model": "llama-tiny",
        "split": "none",
        "query_positions": ["readout"],
        "column_query_position": "readout",
        "segments": SEGMENTS,
        "sum_tolerance": ap.SUM_TOLERANCE,
        "components": [{"key": list(key), "name": ap.component_key_name(key),
                        "label": ap.head_label(key), "layer": key[1],
                        "index": key[2], "kv_group": 0} for key in HEADS],
        "conditions": list(conditions),
        "skipped": [],
    }


def masses_where(top):
    """`{component name: {readout: profile}}` putting each head's mass on `top`."""
    return {ap.component_key_name(key): {"readout": profile(**{top[key]: 0.9})}
            for key in HEADS}


def test_the_paired_honest_instruction_gets_its_own_top_segment_column():
    payload = patterns_payload(
        condition(ap.PRESSURE, masses=masses_where(
            {HEADS[0]: "readout", HEADS[1]: "readout"})),
        condition(ap.PRESSURE_PAIRED, n=2, paired=True, masses=masses_where(
            {HEADS[0]: "designation_site", HEADS[1]: "readout"})),
        condition(ap.HONEST_INSTRUCTION, n=2, paired=True, masses=masses_where(
            {HEADS[0]: "item_1_question", HEADS[1]: "readout"})))

    updates = ap.columns(payload)

    assert updates[HEADS[0]]["honest_instruction_top_segment"] == "item_1_question"
    assert updates[HEADS[0]]["honest_instruction_top_mass"] == pytest.approx(0.9)
    assert updates[HEADS[1]]["honest_instruction_top_segment"] == "readout"


def test_the_paired_columns_have_a_left_term_read_over_the_same_instances():
    """The paired honest column is comparable to `pressure_paired`, not `pressure`.

    `pressure` is the whole test split and `pressure_paired` is the subset with
    an Honest-Instruction Counterfactual, so the two differ; the column that
    the paired honest column is meant to be read against is the one measured
    over its own instances.
    """
    payload = patterns_payload(
        condition(ap.PRESSURE, n=48, masses=masses_where(
            {HEADS[0]: "readout", HEADS[1]: "readout"})),
        condition(ap.PRESSURE_PAIRED, n=2, paired=True, masses=masses_where(
            {HEADS[0]: "designation_site", HEADS[1]: "readout"})),
        condition(ap.HONEST_INSTRUCTION, n=2, paired=True, masses=masses_where(
            {HEADS[0]: "item_1_question", HEADS[1]: "readout"})))

    updates = ap.columns(payload)

    assert updates[HEADS[0]]["pressure_top_segment"] == "readout"
    assert updates[HEADS[0]]["pressure_paired_top_segment"] == "designation_site"


def test_the_unpaired_twin_column_still_says_descriptive_in_its_own_name():
    """The one thing a CSV reader has to be able to tell from the header alone."""
    payload = patterns_payload(
        condition(ap.PRESSURE, masses=masses_where(
            {HEADS[0]: "readout", HEADS[1]: "readout"})),
        condition(ap.HONEST_TWIN, masses=masses_where(
            {HEADS[0]: "designation_site", HEADS[1]: "readout"})))

    updates = ap.columns(payload)

    assert updates[HEADS[0]]["honest_twin_descriptive_top_segment"] == \
        "designation_site"
    assert "honest_instruction_top_segment" in updates[HEADS[0]]
    assert updates[HEADS[0]]["honest_instruction_top_segment"] is None


def test_a_condition_that_did_not_run_leaves_its_columns_empty_not_missing():
    """An absent column and an empty one read the same in a CSV; make it empty.

    A head table whose columns differ from cell to cell cannot be concatenated,
    and a missing column is indistinguishable from a head that attends nowhere.
    """
    payload = patterns_payload(condition(ap.PRESSURE, masses=masses_where(
        {HEADS[0]: "readout", HEADS[1]: "readout"})))

    updates = ap.columns(payload)

    for key in HEADS:
        for name in ("honest_instruction", "pressure_paired",
                     "honest_twin_descriptive"):
            assert updates[key][f"{name}_top_segment"] is None
            assert updates[key][f"{name}_top_mass"] is None


# ==============================================================================
# THE TWO SIDES OF THE PAIR
#
# These three reach below the seam the repo's testing rule names: they assert
# on the tensors an internal generator yields, not on a written file. They are
# kept deliberately, and the standards review recorded the tension rather than
# waving it through.
#
# Two reasons. First, the file-seam form of the same property —
# `test_both_sides_of_the_pair_are_profiled_over_the_same_instances`, which
# compares the two conditions' recorded `instance_ids` in `patterns.json` —
# needs a model, so it is in the nnsight-0.7.0-gated CLI file and does not run
# on the login node at all. Without these, the property that makes "paired"
# mean anything has no coverage in the base environment.
#
# Second, the bug they catch is invisible at the file seam: yielding
# `batch.honest.input_ids` for both sides would produce a perfectly
# well-formed `patterns.json` with matching ids, matching counts and every
# paired difference exactly zero. That reads as a finding, not as a failure.
# Only the prompts themselves distinguish the two, so the assertion has to be
# on the prompts.
# ==============================================================================

def hand_segmentation(record_id, *, n_tokens=6, clause=(2, 4)):
    """A `Segmentation` with a Pressure Clause, built from spans, no prompt."""
    from component_analysis import segmentation as segs

    spans = {"intro": ((0, 2),), "pressure_clause": (tuple(clause),),
             "readout": ((n_tokens - 1, n_tokens),)}
    return segs.Segmentation(
        task="sdr", record_id=record_id, n_tokens=n_tokens,
        readout=n_tokens - 1,
        segments={name: segs.Segment(name=name, spans=span)
                  for name, span in spans.items()},
        scheme="mechanism")


def hand_batch(ids, honest_rows, *, n_tokens=6):
    """One `Batch` whose honest prompts differ from the pressure ones in the clause."""
    import torch

    from component_analysis import dataloaders as dl

    pressure = torch.arange(len(ids) * n_tokens).reshape(len(ids), n_tokens)
    honest = pressure[honest_rows].clone()
    honest[:, 2:4] += 1000                       # differs only inside the clause
    ones = torch.ones_like(pressure)
    return dl.Batch(
        ids=list(ids),
        records=[{"instance_id": one, "designation_polarity": "identity"}
                 for one in ids],
        input_ids=pressure, attention_mask=ones,
        corrupt_input_ids=pressure, corrupt_attention_mask=ones,
        target_token=torch.zeros(len(ids), dtype=torch.long),
        distractor_token=torch.ones(len(ids), dtype=torch.long),
        readout=torch.full((len(ids),), n_tokens - 1, dtype=torch.long),
        honest=dl.HonestPair(
            rows=list(honest_rows), input_ids=honest,
            attention_mask=torch.ones_like(honest),
            clause_span=torch.tensor([[2, 4]] * len(honest_rows)),
            instructions=["be honest"] * len(honest_rows)))


def empty_report():
    return {"n_pairs": 0, "n_identical_to_pressure": 0,
            "n_differing_outside_the_clause": 0,
            "examples_outside_the_clause": []}


def test_the_paired_pressure_side_reads_exactly_the_instances_that_have_a_pair():
    """"Paired" means the same instance ids on both sides, and this is where it
    is made true: the left term is the pressure prompt of the very rows the
    honest side has, not the whole split and not the whole sample."""
    batches = [hand_batch(["a", "b", "c"], honest_rows=[0, 2])]
    resolved = [hand_segmentation(one) for one in ("a", "b", "c")]

    honest = list(ap.honest_instruction_slices(batches, resolved, empty_report()))
    pressure = list(ap.pressure_paired_slices(batches, resolved))

    assert [one["instance_id"] for slice_ in honest for one in slice_.records] \
        == ["a", "c"]
    assert [one["instance_id"] for slice_ in pressure for one in slice_.records] \
        == ["a", "c"]


def test_the_paired_pressure_side_carries_the_pressure_prompt_not_the_honest_one():
    """The obvious bug this guards: yielding `batch.honest.input_ids` twice,
    which would make the differential identically zero and look like a finding."""
    batches = [hand_batch(["a", "b"], honest_rows=[1])]
    resolved = [hand_segmentation(one) for one in ("a", "b")]

    honest = next(iter(ap.honest_instruction_slices(batches, resolved,
                                                   empty_report())))
    pressure = next(iter(ap.pressure_paired_slices(batches, resolved)))

    assert pressure.input_ids.tolist() == batches[0].input_ids[[1]].tolist()
    assert honest.input_ids.tolist() != pressure.input_ids.tolist()


def test_a_batch_with_no_pair_at_all_contributes_to_neither_side():
    batches = [hand_batch(["a", "b"], honest_rows=[])]
    batches[0].honest = None
    resolved = [hand_segmentation(one) for one in ("a", "b")]

    assert list(ap.pressure_paired_slices(batches, resolved)) == []
    assert list(ap.honest_instruction_slices(batches, resolved,
                                             empty_report())) == []


# ==============================================================================
# THE TWO PAIRED FIGURES' JSON TWINS
# ==============================================================================

COMPONENTS = [("head", 24, 18), ("mlp", 31, 0)]


def dla_component(key, mean, se=0.01):
    return {"key": list(key), "kind": key[0], "layer": key[1], "index": key[2],
            "label": dla.label_of(key),
            "levels": {dla.ALL: {"n": 7, "mean": mean, "se": se}}}


def dla_condition(means, *, n=7, ids=("a", "b")):
    return {"n_instances": n, "instance_ids": list(ids), "direction_sign": 1,
            "levels": [dla.ALL], "totals": {},
            "components": [dla_component(key, means[key]) for key in COMPONENTS],
            "embedding": {"label": "embed", "levels": {}}}


def dla_payload(**conditions):
    return {"schema_version": dla.SCHEMA_VERSION, "analysis": dla.NAME,
            "circuit": "delta", "task": "sdr", "metric": dla.METRIC,
            "fixed_scale": dla.FIXED_SCALE, "suppression_margin": 0.05,
            "split": "none", "split_factors": [],
            "n_components": len(COMPONENTS), "conditions": dict(conditions),
            "sources": {}, "skipped": {}, "unpaired_instance_ids": [],
            "sum_check": None}


def lens_condition(means, *, n=7):
    return {"n_instances": n, "n_rows": len(means), "sign_flip_row": 1,
            "sign_flip_layer": 0, "sign_change_rows": [1],
            "levels": {dla.ALL: {"mean": list(means),
                                 "se": [0.0] * len(means)}}}


def lens_payload(**conditions):
    return {"schema_version": dla.SCHEMA_VERSION, "analysis": dla.NAME,
            "circuit": "delta", "task": "sdr", "metric": dla.METRIC,
            "rows": "row 0 is the embedding's output; layer = row - 1",
            "conditions": dict(conditions)}


def paired_dla():
    return dla_payload(**{
        dla.PRESSURE: dla_condition({COMPONENTS[0]: 0.04, COMPONENTS[1]: 0.18},
                                    n=48),
        dla.PRESSURE_PAIRED: dla_condition({COMPONENTS[0]: 0.02,
                                            COMPONENTS[1]: -0.24}),
        dla.HONEST_INSTRUCTION: dla_condition({COMPONENTS[0]: -0.05,
                                               COMPONENTS[1]: -0.57}),
        dla.DIFFERENTIAL: dla_condition({COMPONENTS[0]: 0.07,
                                         COMPONENTS[1]: 0.33})})


def test_the_scatter_axes_are_the_two_paired_conditions_not_the_full_split():
    """The axis choice *is* the correctness claim: `pressure` is 48 instances
    and `pressure_paired` is the 7 that have a counterpart."""
    twin = dla.paired_scatter_payload(paired_dla())

    assert twin["x"] == dla.PRESSURE_PAIRED
    assert twin["y"] == dla.HONEST_INSTRUCTION
    assert twin["n_instances"] == 7
    by_label = {one["label"]: one for one in twin["points"]}
    assert by_label["L31 MLP"]["x"] == pytest.approx(-0.24)
    assert by_label["L31 MLP"]["y"] == pytest.approx(-0.57)


def test_every_component_is_a_labelled_point_with_its_differential():
    twin = dla.paired_scatter_payload(paired_dla())

    assert sorted(one["label"] for one in twin["points"]) == ["L24H18", "L31 MLP"]
    by_label = {one["label"]: one for one in twin["points"]}
    assert by_label["L31 MLP"]["differential"] == pytest.approx(0.33)
    assert by_label["L24H18"]["x_se"] == pytest.approx(0.01)


def test_the_scatter_says_why_it_is_empty_when_no_condition_was_paired():
    payload = dla_payload(**{dla.PRESSURE: dla_condition(
        {COMPONENTS[0]: 0.04, COMPONENTS[1]: 0.18})})

    twin = dla.paired_scatter_payload(payload)

    assert twin["points"] == []
    assert dla.HONEST_INSTRUCTION in twin["skipped"]
    assert twin["figure"] == dla.PAIRED_SCATTER_PNG_NAME


def test_the_paired_lens_twin_keeps_only_the_two_paired_curves():
    lens = lens_payload(**{
        dla.PRESSURE: lens_condition([0.0, 0.5, 1.7], n=48),
        dla.PRESSURE_PAIRED: lens_condition([0.0, -0.2, 0.9]),
        dla.HONEST_INSTRUCTION: lens_condition([0.0, -0.4, -2.3]),
        dla.HONEST_TWIN: lens_condition([0.0, -0.3, -2.1], n=48)})

    twin = dla.paired_lens_payload(lens)

    assert set(twin["conditions"]) == {dla.PRESSURE_PAIRED,
                                       dla.HONEST_INSTRUCTION}
    assert twin["conditions"][dla.HONEST_INSTRUCTION]["mean"] == [0.0, -0.4, -2.3]
    assert twin["conditions"][dla.PRESSURE_PAIRED]["n_instances"] == 7


def test_the_paired_lens_figure_is_drawn_from_its_own_json_twin():
    """Not from `logit_lens.json`. Deriving the picture and the file separately
    from one source lets the two drift; deriving the picture from the file
    cannot, which is the rule the scatter's docstring already states."""
    lens = lens_payload(**{
        dla.PRESSURE: lens_condition([0.0, 0.5, 1.7], n=48),
        dla.PRESSURE_PAIRED: lens_condition([0.0, -0.2, 0.9]),
        dla.HONEST_INSTRUCTION: lens_condition([0.0, -0.4, -2.3])})
    twin = dla.paired_lens_payload(lens)
    twin["conditions"][dla.HONEST_INSTRUCTION]["mean"] = [9.0, 9.0, 9.0]

    figure_payload = dla.paired_lens_figure_payload(twin)

    assert set(figure_payload["conditions"]) == {dla.PRESSURE_PAIRED,
                                                 dla.HONEST_INSTRUCTION}
    assert figure_payload["circuit"] == lens["circuit"]
    # What the twin says is what gets drawn, even when the twin is edited.
    assert figure_payload["conditions"][dla.HONEST_INSTRUCTION]["levels"][
        dla.ALL]["mean"] == [9.0, 9.0, 9.0]


def test_the_paired_lens_twin_says_why_it_is_empty():
    lens = lens_payload(**{dla.PRESSURE: lens_condition([0.0, 0.5, 1.7])})

    twin = dla.paired_lens_payload(lens)

    assert twin["conditions"] == {}
    assert dla.HONEST_INSTRUCTION in twin["skipped"]


def test_both_paired_figures_write_a_png_even_with_nothing_to_draw(tmp_path):
    """A JSON beside no PNG reads as a crashed run, so the empties are drawn."""
    scatter = os.path.join(str(tmp_path), dla.PAIRED_SCATTER_PNG_NAME)
    lens_path = os.path.join(str(tmp_path), dla.PAIRED_LENS_PNG_NAME)
    empty = dla_payload(**{dla.PRESSURE: dla_condition(
        {COMPONENTS[0]: 0.04, COMPONENTS[1]: 0.18})})

    dla.plot_paired_scatter(scatter, dla.paired_scatter_payload(empty))
    dla.plot_lens(lens_path, dla.paired_lens_figure_payload(
        dla.paired_lens_payload(
            lens_payload(**{dla.PRESSURE: lens_condition([0.0, 0.5])}))),
        empty_message=dla.NOT_PAIRED)

    assert os.path.getsize(scatter) > 0 and os.path.getsize(lens_path) > 0


def test_the_scatter_png_is_drawn_from_its_own_json_twin(tmp_path):
    path = os.path.join(str(tmp_path), dla.PAIRED_SCATTER_PNG_NAME)

    dla.plot_paired_scatter(path, dla.paired_scatter_payload(paired_dla()))

    assert os.path.getsize(path) > 0


def test_the_paired_figures_carry_the_sign_convention_in_their_own_meta():
    """Block C's rule: every JSON states its sign convention in its meta."""
    scatter = dla.paired_scatter_payload(paired_dla())
    lens = dla.paired_lens_payload(lens_payload(**{
        dla.PRESSURE_PAIRED: lens_condition([0.0, 0.9]),
        dla.HONEST_INSTRUCTION: lens_condition([0.0, -2.3])}))

    for twin in (scatter, lens):
        assert "deceptive answer" in twin["metric"]
        assert twin["paired"] is True


def test_this_module_pair_does_not_import_nnsight():
    """`--dry-run` is a login-node mode, and the login node has no 0.7.0."""
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, "-c",
         "import sys; "
         "import component_analysis.attention_patterns, component_analysis.dla; "
         "assert 'nnsight' not in sys.modules, sorted(sys.modules)"],
        check=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==============================================================================
# THE SCATTER'S SECOND PANEL
# ==============================================================================

def spread(*pairs):
    return [{"label": f"C{i}", "x": x, "y": y, "x_se": 0.0, "y_se": 0.0,
             "differential": x - y} for i, (x, y) in enumerate(pairs)]


def test_a_cluster_under_one_outlier_earns_a_zoom_panel():
    """The real SDR run put one MLP at -0.24/-0.57 and thirteen heads inside
    0.01 of the origin, and every label in the clump landed on top of the
    others. The zoom limit is what makes the clump readable."""
    points = spread((-0.24, -0.57), (0.13, 0.05), (0.06, -0.01),
                    (0.003, 0.001), (0.001, 0.0), (0.0005, -0.0002),
                    (0.0004, 0.0001), (0.0002, 0.0))

    limit = dla.zoom_limit(points)

    assert limit is not None
    assert limit < 0.06, "the three big Components must fall outside the zoom"
    assert limit > 0.003, "the cluster's own largest member must fall inside it"


def test_points_spread_evenly_earn_no_zoom_panel():
    """A second panel showing the same thing as the first is worse than none."""
    points = spread((0.5, 0.4), (0.3, 0.25), (0.2, 0.1), (-0.4, -0.45),
                    (-0.25, -0.2))

    assert dla.zoom_limit(points) is None


def test_a_single_point_earns_no_zoom_panel():
    assert dla.zoom_limit(spread((0.2, 0.1))) is None



def test_the_scatter_twin_records_the_zoom_and_which_panel_names_each_point():
    """The twin must describe the figure, or it is not a twin of it. A reader
    of the file has to be able to tell that the picture has two panels and
    where it cuts, without opening the PNG."""
    points = spread((-0.24, -0.57), (0.13, 0.05), (0.06, -0.01),
                    (0.003, 0.001), (0.001, 0.0), (0.0005, -0.0002),
                    (0.0004, 0.0001), (0.0002, 0.0))
    payload = dla_payload(**{
        dla.PRESSURE_PAIRED: dla_condition({COMPONENTS[0]: 0.02,
                                            COMPONENTS[1]: -0.24}),
        dla.HONEST_INSTRUCTION: dla_condition({COMPONENTS[0]: -0.05,
                                               COMPONENTS[1]: -0.57})})

    twin = dla.paired_scatter_payload(payload)

    assert "zoom" in twin and "panels" in twin
    assert all("panel" in one for one in twin["points"])
    assert dla.zoom_limit(points) is not None     # the fixture earns a zoom


def test_a_component_exactly_on_the_cut_is_named_in_one_panel_only():
    """Inclusive on both ends would name it twice and make the panel counts
    sum to more than the number of Components, which the titles deny."""
    on_the_cut = {"label": "C", "x": 0.05, "y": 0.0, "x_se": 0.0, "y_se": 0.0}

    assert dla.panel_of(on_the_cut, 0.05) == dla.FULL_PANEL
    assert dla.panel_of(on_the_cut, 0.06) == dla.ZOOM_PANEL
    assert dla.panel_of(on_the_cut, None) == dla.SINGLE_PANEL


def test_the_two_panels_between_them_name_every_component_exactly_once():
    points = spread((-0.24, -0.57), (0.13, 0.05), (0.06, -0.01),
                    (0.003, 0.001), (0.001, 0.0), (0.0005, -0.0002),
                    (0.0004, 0.0001), (0.0002, 0.0))
    zoom = dla.zoom_limit(points)

    panels = [dla.panel_of(one, zoom) for one in points]

    assert len(panels) == len(points)
    assert set(panels) == {dla.FULL_PANEL, dla.ZOOM_PANEL}


def test_the_paired_conditions_are_named_once_for_both_figures():
    """The scatter's axes and the lens's curves must agree about which pair is
    the pair, so the pair is spelled in one place."""
    assert dla.PAIRED_CONDITIONS == (dla.PRESSURE_PAIRED,
                                     dla.HONEST_INSTRUCTION)

    lens = lens_payload(**{
        dla.PRESSURE: lens_condition([0.0, 1.7], n=48),
        dla.PRESSURE_PAIRED: lens_condition([0.0, 0.9]),
        dla.HONEST_INSTRUCTION: lens_condition([0.0, -2.3])})
    scatter = dla.paired_scatter_payload(paired_dla())

    assert set(dla.paired_lens_payload(lens)["conditions"]) == \
        set(dla.PAIRED_CONDITIONS)
    assert (scatter["x"], scatter["y"]) == dla.PAIRED_CONDITIONS


def test_the_refusal_names_the_bad_condition_and_the_good_ones():
    """Through argparse as well as directly. `argparse` keeps the message of an
    `ArgumentTypeError` and throws away the message of a plain `ValueError`,
    replacing it with "invalid parse_conditions value: 'honest'" — which names
    the function rather than the flag and lists nothing. The error is both."""
    import argparse

    assert issubclass(ap.UnknownCondition, ValueError)
    assert issubclass(ap.UnknownCondition, argparse.ArgumentTypeError)

    parser = argparse.ArgumentParser(prog="analyze_components.py")
    ap.add_arguments(parser)

    with pytest.raises(SystemExit):
        parser.parse_args(["--attention-conditions", "honest"])


def test_the_flag_parses_its_value_at_parse_time_not_at_run_time():
    import argparse

    parser = argparse.ArgumentParser()
    ap.add_arguments(parser)

    assert parser.parse_args([]).attention_conditions == list(ap.CONDITIONS)
    assert parser.parse_args(
        ["--attention-conditions", "honest_twin,pressure"]
    ).attention_conditions == [ap.PRESSURE, ap.HONEST_TWIN]
