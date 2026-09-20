"""The review notebook's data seam: `component_analysis.review`.

The notebook itself is never executed by an agent (project rule), so every
decision it makes about a results directory lives in `review.py` and is
asserted here. The fixtures under `tests/fixtures/review/` are trimmed copies
of real cells written by tickets 03, 06, 07 and 09 — trimmed only by dropping
instances and per-head masses, never by reshaping — so a schema drift in an
analysis breaks these tests rather than the researcher's notebook.

Cells, and which sections each one exercises:

  attention_dla/  head table with role-less columns, attention, DLA, logit lens
  knockout/       knockout ranking, segmentation, sample
  path_patching/  both counterfactuals of the agnostic and Segment passes
  sweep/          the completeness sweep
  empty/          every section's "missing analysis" note
"""

import json
import os

import pytest

from component_analysis import review

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "review")


def cell(name):
    return os.path.join(FIXTURES, name)


# ==============================================================================
# THE MISSING NOTE
# ==============================================================================
#
# The ticket's rule: "a missing analysis renders a note, not an error". Every
# section returns a falsy `Missing` rather than raising, so a notebook cell
# reads `view = review.x(dir)` and renders `view.note` when it is falsy.


def test_a_missing_analysis_is_a_falsy_note_rather_than_an_exception():
    for view in (review.head_table_view(cell("empty")),
                 review.attention_views(cell("empty")),
                 review.dla_view(cell("empty")),
                 review.logit_lens_views(cell("empty")),
                 review.path_patching_views(cell("empty")),
                 review.sweep_view(cell("empty")),
                 review.knockout_view(cell("empty")),
                 review.family_knockout_view(cell("empty")),
                 review.segmentation_view(cell("empty")),
                 review.sample_view(cell("empty"))):
        assert not view
        assert isinstance(view, review.Missing)
        assert view.note


def test_a_missing_note_names_the_file_it_looked_for():
    missing = review.knockout_view(cell("empty"))
    assert "knockout.json" in missing.note


# ==============================================================================
# THE HEAD TABLE
# ==============================================================================


def test_the_head_table_view_carries_every_component_and_its_columns():
    view = review.head_table_view(cell("attention_dla"))
    assert view
    assert len(view.rows) == 18          # 17 heads and one MLP block
    assert view.columns[:4] == ["label", "kind", "layer", "index"]
    assert "dla.pressure" in view.columns
    assert view.rows[0]["label"] == "L5H5"
    assert view.rows[-1]["label"] == "L31 MLP"


def test_the_head_table_view_reports_the_circuit_it_describes():
    view = review.head_table_view(cell("attention_dla"))
    assert view.meta["circuit"]["label"] == "delta__head"
    assert view.meta["task"]["label"] == "sdr"
    assert "delta__head" in view.subtitle and "sdr" in view.subtitle


def test_role_columns_are_rendered_right_after_the_identity_columns(tmp_path):
    # Ticket 10 writes these; until it lands no cell has them, which is why
    # this fixture is hand-built rather than copied.
    _write_head_table(tmp_path, [
        {"kind": "head", "layer": 5, "index": 5, "dla.pressure": 0.1,
         "roles.role_proposed": "mover", "roles.role_notes": "top DLA",
         "role_confirmed": None},
    ])
    view = review.head_table_view(str(tmp_path))
    assert view.columns[:7] == ["label", "kind", "layer", "index",
                                "roles.role_proposed", "role_confirmed",
                                "roles.role_notes"]
    assert view.role_columns["role_proposed"] == "roles.role_proposed"
    assert view.role_columns["role_confirmed"] == "role_confirmed"
    assert view.notes == []


def test_an_unnamespaced_role_column_is_found_too(tmp_path):
    _write_head_table(tmp_path, [
        {"kind": "mlp", "layer": 31, "index": 0, "role_proposed": "unknown"},
    ])
    view = review.head_table_view(str(tmp_path))
    assert view.role_columns == {"role_proposed": "role_proposed"}


def test_a_head_table_without_role_columns_carries_a_note_not_an_error():
    view = review.head_table_view(cell("attention_dla"))
    assert view.role_columns == {}
    assert any("role" in note for note in view.notes)


def _write_head_table(directory, rows):
    payload = {"schema_version": 1, "columns": sorted({k for r in rows for k in r}),
               "meta": {"circuit": {"label": "c"}, "task": {"label": "t"}},
               "rows": rows}
    with open(os.path.join(str(directory), "head_table.json"), "w") as handle:
        json.dump(payload, handle)


# ==============================================================================
# ATTENTION PATTERNS
# ==============================================================================


def test_attention_views_give_one_heatmap_per_level_and_condition():
    group = review.attention_views(cell("attention_dla"))
    assert group
    # Three levels (all, identity, inversion) times four conditions.
    assert len(group.items) == 12
    first = group.items[0]
    assert first.rows[:2] == ["L5H5", "L5H6"]
    assert first.columns[0] == "intro"
    assert len(first.values) == 17 and len(first.values[0]) == 18
    titles = [one.title for one in group.items]
    assert "attention mass per Segment — pressure (all)" in titles
    assert "attention mass per Segment — honest instruction (identity)" in titles


def test_an_attention_heatmap_says_how_many_instances_and_whether_it_is_paired():
    group = review.attention_views(cell("attention_dla"))
    paired = [one for one in group.items if "honest instruction (all)" in one.title][0]
    assert "71 instance(s)" in paired.subtitle
    assert "paired" in paired.subtitle
    unpaired = [one for one in group.items if "honest twin (all)" in one.title][0]
    assert "descriptive" in unpaired.subtitle


def test_attention_views_carry_the_sum_to_one_check_as_a_note():
    group = review.attention_views(cell("attention_dla"))
    assert any("sum to one" in note for note in group.notes)


def test_top_heads_is_a_view_of_its_own_and_says_what_ranked_it():
    view = review.top_heads_view(cell("attention_dla"))
    assert view
    assert len(view.rows) == 8
    assert "layer order" in view.subtitle


def test_a_heatmap_converts_to_circuitsvis_coloured_tokens():
    group = review.attention_views(cell("attention_dla"))
    heatmap = group.items[0]
    tokens, values, labels = review.coloured_tokens(heatmap)
    # circuitsvis wants [n_tokens][n_series]; the Segments are the tokens and
    # the heads the series, which is the transpose of the plotly matrix.
    assert tokens == heatmap.columns
    assert labels == heatmap.rows
    assert len(values) == 18 and len(values[0]) == 17
    assert values[0][0] == heatmap.values[0][0]


# ==============================================================================
# DLA AND THE LOGIT LENS
# ==============================================================================


def test_dla_view_gives_one_bar_chart_per_condition_in_head_table_order():
    group = review.dla_view(cell("attention_dla"))
    assert group
    assert [one.title for one in group.items] == [
        "direct logit attribution — pressure",
        "direct logit attribution — honest_instruction",
        "direct logit attribution — pressure_paired",
        "direct logit attribution — differential",
        "direct logit attribution — honest_twin"]
    bars = group.items[0]
    assert bars.labels[0] == "L5H5" and bars.labels[-1] == "embed"
    assert len(bars.values) == len(bars.labels) == 19   # 18 Components + embed
    assert bars.errors is not None
    assert "1000 instance(s)" in bars.subtitle


def test_dla_is_also_a_component_by_condition_heatmap():
    """The ticket asks for a DLA heatmap; the bars are one condition at a time."""
    view = review.dla_heatmap(cell("attention_dla"))
    assert view
    assert view.rows[0] == "L5H5" and view.rows[-1] == "embed"
    assert view.columns == ["pressure", "honest_instruction", "pressure_paired",
                            "differential", "honest_twin"]
    assert len(view.values) == 19 and len(view.values[0]) == 5
    assert view.extent is not None and view.extent > 0


def test_a_dla_heatmap_is_missing_when_the_cell_has_no_dla():
    assert not review.dla_heatmap(cell("knockout"))


def test_dla_view_states_the_metric_and_the_suppression_margin():
    group = review.dla_view(cell("attention_dla"))
    assert any("logit(deceptive answer)" in note for note in group.notes)
    assert any("suppression" in note for note in group.notes)


def test_the_paired_dla_scatter_pairs_each_component_across_the_two_conditions():
    view = review.dla_scatter_view(cell("attention_dla"))
    assert view
    assert view.x_title == "pressure_paired" and view.y_title == "honest_instruction"
    assert len(view.labels) == 18
    assert view.labels[0] == "L5H5"
    assert len(view.x) == len(view.y) == len(view.labels)


def test_logit_lens_views_are_one_series_per_condition_over_the_layer_rows():
    views = review.logit_lens_views(cell("attention_dla"))
    assert views
    lens = views.items[0]
    assert lens.x == list(range(33))
    assert [one.name for one in lens.series] == [
        "pressure", "honest_instruction", "pressure_paired", "differential",
        "honest_twin"]
    assert len(lens.series[0].y) == 33


def test_the_logit_lens_reports_where_the_deceptive_answer_overtakes():
    views = review.logit_lens_views(cell("attention_dla"))
    assert any("layer 14" in note for note in views.notes)


# ==============================================================================
# KNOCKOUT
# ==============================================================================


def test_knockout_view_is_the_ranking_the_analysis_wrote():
    view = review.knockout_view(cell("knockout"))
    assert view
    assert view.labels[:2] == ["L17H25", "L31 MLP"]
    assert len(view.labels) == 18
    assert view.values[0] == pytest.approx(0.4465214729309082)
    assert view.errors[0] == pytest.approx(0.02785063613438062)


def test_knockout_view_states_its_sign_convention_and_its_clean_run():
    view = review.knockout_view(cell("knockout"))
    assert any("positive drop" in note or "positive means" in note
               for note in view.notes)
    assert "1.613" in view.subtitle          # the clean logit difference
    assert "interchange" in view.subtitle


def test_family_knockout_is_absent_until_ticket_ten_writes_it():
    missing = review.family_knockout_view(cell("knockout"))
    assert not missing
    assert "family" in missing.note


# ==============================================================================
# PATH PATCHING
# ==============================================================================


def test_path_patching_views_cover_both_counterfactuals():
    group = review.path_patching_views(cell("path_patching"))
    assert group
    titles = [one.title for one in group.items]
    assert "position-agnostic path patching (item_swap)" in titles
    assert "position-agnostic path patching (honest_instruction)" in titles
    assert "direct effect on the Readout (item_swap)" in titles
    assert "path patching by Segment (item_swap)" in titles


def test_the_agnostic_heatmap_names_its_receivers_and_keeps_the_png_scale():
    group = review.path_patching_views(cell("path_patching"))
    heatmap = [one for one in group.items
               if one.title == "position-agnostic path patching (item_swap)"][0]
    assert heatmap.rows[0] == "embed"
    assert heatmap.columns[0] == "q.5.5"     # the dict column normalized to its key
    assert len(heatmap.columns) == 41
    assert heatmap.extent == pytest.approx(0.004294038876032571)
    assert heatmap.values[0][0] is not None


def test_path_patching_says_negative_carries_the_counterfactual():
    group = review.path_patching_views(cell("path_patching"))
    assert any("negative" in note for note in group.notes)


def test_the_segment_pass_records_the_threshold_that_selected_its_cells():
    group = review.path_patching_views(cell("path_patching"))
    segments = [one for one in group.items
                if one.title == "path patching by Segment (item_swap)"][0]
    assert "0.0035" in segments.subtitle
    assert segments.rows[0] == "mlp.31.0->readout"


def test_the_completeness_sweep_ranks_every_sender_and_flags_non_circuit_ones():
    view = review.sweep_view(cell("sweep"))
    assert view
    assert view.labels[0] == "mlp.30.0"
    assert view.values[0] == pytest.approx(0.12747240484895883)
    assert "not in the circuit" in view.hover[0]
    assert "1057" in view.subtitle           # senders swept
    assert any("0.05" in note for note in view.notes)


# ==============================================================================
# SEGMENTATION AND SAMPLE
# ==============================================================================


def test_segmentation_view_lists_every_segment_and_where_it_came_from():
    view = review.segmentation_view(cell("knockout"))
    assert view
    assert view.columns == ["segment", "source", "present_on", "mean_tokens"]
    assert len(view.rows) == 18
    names = [row["segment"] for row in view.rows]
    assert "designation_site" in names and "designation_suffix" in names
    assert view.rows[0]["source"] == "default"


def test_segmentation_view_reports_overrides_and_overlaps():
    view = review.segmentation_view(cell("knockout"))
    assert any("no Segment was overridden" in note for note in view.notes)
    assert any("overlap" in note for note in view.notes)


def test_sample_view_shows_the_achieved_counts_per_stratum():
    view = review.sample_view(cell("knockout"))
    assert view
    assert len(view.rows) == 8
    assert view.rows[0]["available"] == 189
    assert view.rows[0]["achieved"] == 13
    assert view.rows[0]["designation_polarity"] == "identity"
    assert "100 of 100" in view.subtitle
    assert any("designation_polarity" in note for note in view.notes)


# ==============================================================================
# PURITY
# ==============================================================================


def test_review_imports_without_torch_nnsight_plotly_or_circuitsvis():
    """The base env has none of the four, and it still imports this module.

    A fresh interpreter, because `sys.modules` is process-wide and some earlier
    test in this session has certainly imported torch.
    """
    import subprocess
    import sys

    probe = ("import component_analysis.review, sys; "
             "banned = {'torch', 'nnsight', 'plotly', 'circuitsvis'} & "
             "set(sys.modules); "
             "assert not banned, sorted(banned)")
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


# ==============================================================================
# THE LIVE SECTION'S ONE NON-RENDERING DECISION
# ==============================================================================


def test_the_task_spec_is_rebuilt_from_the_cells_own_provenance():
    """The live section reloads instances without re-resolving the circuits.

    `analyze_components.py` resolves a TaskSpec from run directories that may
    no longer be mounted where the cell was written (every cell of record names
    a worktree that has since been removed). The head table already records
    what the loaders need, so the notebook rebuilds the spec from that instead.
    """
    view = review.head_table_view(cell("attention_dla"))
    spec = review.task_spec_from_meta(view.meta)
    assert spec.name == "sdr"
    assert spec.label == "sdr"
    assert spec.args.data_dir == "./data/datasets"
    assert spec.args.test_samples == 1000
    assert spec.args.deception_condition == "deceptive"
    assert spec.args.std_variant == "azaria"


def test_rebuilding_a_task_spec_without_provenance_says_so():
    with pytest.raises(ValueError, match="no task provenance"):
        review.task_spec_from_meta({})


def test_the_model_name_comes_from_the_cells_intake():
    view = review.head_table_view(cell("attention_dla"))
    assert review.model_name_of(view.meta) == "llama-8b-instruct"
