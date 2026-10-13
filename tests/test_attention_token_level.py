"""
Tests for ticket 16: the attention colormap, and the token-by-token rendering.

Two seams:

  * the **pure** seam — the colormap constant is warm and stays ordered under a
    strong blue-light filter. No model, so it runs in both environments;
  * the **CLI** seam on the tiny random Llama — every attention JSON twin
    records the colormap; `--attention-token-level` writes one PNG per circuit
    head, its rows are distributions over the prompt's tokens and agree with
    the Segment masses of `patterns.json`; above the size limit the per-head
    twins are written meta-only.

The CLI fixtures are ticket 03's (`tests/test_attention_patterns.py`), which
gate on nnsight 0.7.0 themselves.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from component_analysis import attention_patterns as ap

# ==============================================================================
# THE COLORMAP UNDER A BLUE-LIGHT FILTER
# ==============================================================================

#: A strong blue-light filter, as channel gains: blue nearly gone, green dimmed.
FILTER_GAINS = (1.0, 0.8, 0.1)


def filtered_luminance(name: str) -> np.ndarray:
    """Relative luminance of 256 samples of a colormap seen through the filter."""
    import matplotlib

    rgb = matplotlib.colormaps[name](np.linspace(0.0, 1.0, 256))[:, :3]
    seen = rgb * np.array(FILTER_GAINS)
    linear = np.where(seen <= 0.04045, seen / 12.92,
                      ((seen + 0.055) / 1.055) ** 2.4)
    return linear @ np.array([0.2126, 0.7152, 0.0722])


def readable_under_the_filter(name: str) -> bool:
    """Ordered by luminance through the filter, and the low third still spans.

    A map whose low end is dark purple or blue collapses its bottom third to
    near-black once the blue is filtered out: measured, magma keeps 7% of its
    luminance range in its bottom third and viridis 10%. A quarter is the bar.
    """
    luminance = filtered_luminance(name)
    steps = np.diff(luminance)
    ordered = bool((steps <= 1e-9).all() or (steps >= -1e-9).all())
    whole = abs(luminance[-1] - luminance[0])
    bottom_third = abs(luminance[255 // 3] - luminance[0])
    return ordered and whole > 0.3 and bottom_third / whole >= 0.25


def test_the_filter_check_refuses_the_maps_that_lose_their_low_end():
    # The check has to be able to fail, or passing it says nothing.
    for name in ("magma", "viridis", "plasma"):
        assert not readable_under_the_filter(name), name


def test_the_attention_colormap_stays_ordered_under_a_blue_light_filter():
    assert readable_under_the_filter(ap.COLORMAP)


def test_the_attention_colormap_is_one_plotly_also_knows_by_name():
    """The notebook hands the same name to plotly, so it must mean the same
    map there: same ends, light to dark."""
    plotly_colors = pytest.importorskip("plotly.colors")
    import matplotlib

    scale = plotly_colors.get_colorscale(ap.COLORMAP)
    ends = [matplotlib.colormaps[ap.COLORMAP](v)[:3] for v in (0.0, 1.0)]
    for (_position, colour), expected in zip((scale[0], scale[-1]), ends):
        rgb = [int(part) / 255.0 for part in
               colour.strip("rgb()").split(",")]
        assert np.allclose(rgb, expected, atol=2 / 255.0)


# ==============================================================================
# THE CLI SEAM
# ==============================================================================

from tests.test_analyze_components_segmentation import (  # noqa: E402,F401
    CELL, read_json, run_cli, sdr_run)
from tests.test_attention_patterns import (  # noqa: E402,F401
    analysis_model, sdr_cell)


def attention_dir(out) -> str:
    return os.path.join(str(out), *CELL, ap.SUBDIR)


def token_level_dir(out) -> str:
    return os.path.join(attention_dir(out), ap.TOKEN_LEVEL_SUBDIR)


def run_token_level(sdr_cell, *extra):
    run_dir, out, records, _twin = sdr_cell
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir",
                   str(out), "--attention-token-level", *extra) == 0
    return out, records


def test_every_attention_twin_records_the_colormap_it_was_drawn_with(sdr_cell):
    out, _records = run_token_level(sdr_cell)

    twins = []
    for root, _dirs, files in os.walk(attention_dir(out)):
        for name in files:
            if name.endswith(".png"):
                twins.append(os.path.join(root, name[:-4] + ".json"))
    assert len(twins) >= 4      # patterns_*, top_heads, one per head
    for path in twins:
        with open(path) as handle:
            assert json.load(handle)["colormap"] == ap.COLORMAP, path


def token_level_index(out) -> dict:
    with open(os.path.join(token_level_dir(out), ap.TOKEN_LEVEL_INDEX)) as handle:
        return json.load(handle)


def head_twin(out, label) -> dict:
    with open(os.path.join(token_level_dir(out),
                           f"{ap.TOKEN_LEVEL_STEM}_{label}.json")) as handle:
        return json.load(handle)


def test_token_level_writes_one_png_and_twin_per_circuit_head(sdr_cell):
    out, _records = run_token_level(sdr_cell)

    written = set(os.listdir(token_level_dir(out)))
    # The fixture circuit's heads are L0H0 and L0H2 (ticket 03's fixture).
    for label in ("L0H0", "L0H2"):
        assert f"{ap.TOKEN_LEVEL_STEM}_{label}.png" in written
        assert f"{ap.TOKEN_LEVEL_STEM}_{label}.json" in written
    assert ap.TOKEN_LEVEL_INDEX in written
    assert sorted(one["label"] for one in token_level_index(out)["heads"]) == \
        ["L0H0", "L0H2"]


def test_without_the_flag_no_token_level_rendering_is_written(sdr_cell):
    run_dir, out, _records, _twin = sdr_cell
    assert run_cli(str(run_dir), "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    assert not os.path.exists(token_level_dir(out))
    with open(os.path.join(attention_dir(out), ap.PATTERNS_FILE)) as handle:
        assert json.load(handle)["token_level"] is None


def test_each_template_variant_is_its_own_group_and_says_how_many_it_averaged(
        sdr_cell):
    out, records = run_token_level(sdr_cell)

    index = token_level_index(out)
    pressure_groups = [group for group in index["groups"]
                       if group["family"] == "pressure"]
    variants = sorted({record["template_variant"] for record in records})
    assert sorted(group["template_variant"] for group in pressure_groups) == \
        variants
    # Every pressure instance is averaged into exactly one group.
    pressure_rows = [row for group in pressure_groups for row in group["rows"]
                     if row["condition"] == "pressure"]
    assert sum(row["n_instances"] for row in pressure_rows) == len(records)
    ids = [one for row in pressure_rows for one in row["instance_ids"]]
    assert sorted(ids) == sorted(record["instance_id"] for record in records)
    for group in index["groups"]:
        assert len(group["slot_labels"]) == group["n_slots"]
        assert len(group["slot_segments"]) == group["n_slots"]


def test_every_token_level_row_is_a_distribution_over_the_prompt(sdr_cell):
    out, _records = run_token_level(sdr_cell)

    for label in ("L0H0", "L0H2"):
        twin = head_twin(out, label)
        assert twin["payload"] == "full"
        for panel in twin["panels"]:
            for row in panel["rows"]:
                assert abs(sum(row["values"]) - 1.0) < 1e-4, (label, row)


def test_token_level_sums_back_to_the_segment_masses_of_patterns_json(sdr_cell):
    """The two views of one head cannot disagree: a Segment's mass is the sum
    of its tokens, weighted over the template groups by their instances."""
    out, _records = run_token_level(sdr_cell)

    with open(os.path.join(attention_dir(out), ap.PATTERNS_FILE)) as handle:
        patterns = json.load(handle)
    pressure = next(one for one in patterns["conditions"]
                    if one["name"] == "pressure")
    level = next(one for one in pressure["levels"] if one["level"] == "all")
    index = token_level_index(out)
    groups = {group["group"]: group for group in index["groups"]}

    for component in patterns["components"]:
        expected = level["masses"][component["name"]]["readout"]
        twin = head_twin(out, component["label"])
        totals = {name: 0.0 for name in expected}
        n_total = 0
        for panel in twin["panels"]:
            group = groups[panel["group"]]
            row = next((one for one in panel["rows"]
                        if one["condition"] == "pressure"), None)
            if row is None:
                continue
            meta = next(one for one in group["rows"]
                        if one["condition"] == "pressure")
            n_total += meta["n_instances"]
            for segment, value in zip(group["slot_segments"], row["values"]):
                totals[segment] += value * meta["n_instances"]
        for name, mass in expected.items():
            assert abs(totals[name] / n_total - mass) < 1e-4, \
                (component["label"], name)


def test_every_panel_title_says_how_many_instances_each_row_averaged(sdr_cell):
    out, _records = run_token_level(sdr_cell)

    twin = head_twin(out, "L0H0")
    for panel in twin["panels"]:
        assert panel["rows"]
        for row in panel["rows"]:
            assert f"{row['n_instances']} ({row['condition']})" in panel["title"]
            assert f"n={row['n_instances']}" in row["label"]


def test_above_the_size_limit_the_head_twins_are_meta_only(sdr_cell, monkeypatch):
    monkeypatch.setattr(ap, "TOKEN_LEVEL_JSON_LIMIT_BYTES", 1000)
    out, records = run_token_level(sdr_cell)

    index = token_level_index(out)
    assert index["payload"] == "meta-only"
    assert index["json_limit_bytes"] == 1000
    assert index["full_twins_bytes"] > 1000
    assert index["colormap"] == ap.COLORMAP
    # The instance ids stay recorded, once, in the index.
    ids = [one for group in index["groups"] if group["family"] == "pressure"
           for row in group["rows"] if row["condition"] == "pressure"
           for one in row["instance_ids"]]
    assert len(ids) == len(records)

    written = set(os.listdir(token_level_dir(out)))
    for label in ("L0H0", "L0H2"):
        assert f"{ap.TOKEN_LEVEL_STEM}_{label}.png" in written
        twin = head_twin(out, label)
        assert twin["payload"] == "meta-only"
        assert "panels" not in twin
        assert twin["colormap"] == ap.COLORMAP
        assert twin["regenerate"]
        assert [one["slots"] for one in twin["shape"]] == \
            [group["n_slots"] for group in index["groups"]]

    with open(os.path.join(attention_dir(out), ap.PATTERNS_FILE)) as handle:
        assert json.load(handle)["token_level"]["payload"] == "meta-only"


def test_under_the_size_limit_the_head_twins_carry_their_values(sdr_cell):
    out, _records = run_token_level(sdr_cell)

    index = token_level_index(out)
    assert index["payload"] == "full"
    assert index["full_twins_bytes"] <= ap.TOKEN_LEVEL_JSON_LIMIT_BYTES


# ==============================================================================
# THE NOTEBOOK'S SEAM (component_analysis/review.py)
# ==============================================================================

from component_analysis import review  # noqa: E402

REVIEW_FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "review")


def test_review_spells_the_attention_colormap_the_module_draws_with():
    # review.py cannot import attention_patterns (torch at module scope), so
    # it spells the two out; this pins them.
    import matplotlib
    from matplotlib.colors import to_hex

    assert review.ATTENTION_COLORMAP == ap.COLORMAP
    assert review.ATTENTION_TOP_COLOUR == to_hex(
        matplotlib.colormaps[ap.COLORMAP](1.0))
    assert review.TOKEN_LEVEL_SUBDIR == f"{ap.SUBDIR}/{ap.TOKEN_LEVEL_SUBDIR}"
    assert review.TOKEN_LEVEL_INDEX == ap.TOKEN_LEVEL_INDEX


def test_a_cell_written_before_the_colormap_was_recorded_is_drawn_in_it_anyway():
    view = review.attention_views(os.path.join(REVIEW_FIXTURES, "attention_dla"))

    assert view.items
    for heatmap in view.items:
        assert heatmap.colorscale == ap.COLORMAP
        assert heatmap.value_range == [0.0, 1.0]
    assert any("colormap" in note for note in view.notes)


def test_a_cell_without_token_level_output_renders_a_note():
    view = review.token_level_views(os.path.join(REVIEW_FIXTURES, "attention_dla"))

    assert not view
    assert "--attention-token-level" in view.note


def test_the_notebook_views_carry_the_recorded_colormap_and_the_token_pngs(
        sdr_cell):
    out, _records = run_token_level(sdr_cell)
    results_dir = os.path.join(str(out), *CELL)

    attention = review.attention_views(results_dir)
    assert attention.items
    assert {one.colorscale for one in attention.items} == {ap.COLORMAP}
    assert not any("colormap" in note for note in attention.notes)
    assert review.top_heads_view(results_dir).colorscale == ap.COLORMAP

    pictures = review.token_level_views(results_dir)
    assert [one.title.split(" ")[0] for one in pictures.items] == ["L0H0", "L0H2"]
    for picture in pictures.items:
        assert os.path.isfile(picture.path) and picture.path.endswith(".png")
        # A full twin lets the view name each row's largest tokens.
        assert any("largest" in note for note in picture.notes)


def test_a_meta_only_cell_still_gives_the_notebook_its_pngs(sdr_cell, monkeypatch):
    monkeypatch.setattr(ap, "TOKEN_LEVEL_JSON_LIMIT_BYTES", 1000)
    out, _records = run_token_level(sdr_cell)

    pictures = review.token_level_views(os.path.join(str(out), *CELL))

    assert len(pictures.items) == 2
    assert all(os.path.isfile(one.path) for one in pictures.items)
    assert any("meta-only" in note for note in pictures.notes)
