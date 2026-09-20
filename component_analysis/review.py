"""Reading a finished cell back for human review.

`analyze_components.py` writes a cell — `head_table.csv`/`.json` at the root,
`segmentation.json`, `sample.json`, and one subdirectory per analysis holding a
JSON twin beside every PNG. `review_components.ipynb` renders that cell. This
module is the seam between the two: it turns each file into one of four plain
shapes — `Table`, `Heatmap`, `Bars`, `Lines` — that the notebook hands
straight to plotly or circuitsvis, and it returns a falsy `Missing` for any
analysis the cell does not contain, because the ticket's rule is that *a
missing analysis renders a note, not an error*.

Everything the notebook decides lives here, and nothing else does. The project
rule is that agents never execute notebooks, so a notebook cell holding logic
would be logic nobody ran; `tests/test_review.py` runs all of it against
trimmed copies of real cells instead.

**This module stays pure.** No nnsight (a package-wide test asserts that), and
also no torch, no plotly and no circuitsvis: it is imported by the base-env
suite under Python 3.9, where none of those three is installed. Rendering is
the notebook's half of the seam.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

# ==============================================================================
# THE CELL'S LAYOUT
# ==============================================================================

HEAD_TABLE_JSON = "head_table.json"
HEAD_TABLE_CSV = "head_table.csv"
SEGMENTATION_JSON = "segmentation.json"
SAMPLE_JSON = "sample.json"

#: One subdirectory per analysis, named by that module's `SUBDIR`. Spelled out
#: rather than imported, because importing `attention_patterns` would pull
#: torch into a module the base env has to import without it.
ATTENTION_SUBDIR = "attention"
DLA_SUBDIR = "dla"
KNOCKOUT_SUBDIR = "knockout"
PATH_PATCHING_SUBDIR = "path_patching"

#: The role triple. Ticket 10 writes the proposal and the notes under the
#: `roles` namespace; `role_confirmed` is the human's column and `head_table.py`
#: protects it under its bare name. Both spellings are accepted for all three,
#: so that a namespace decision made after this module was written does not
#: silently blank the role columns in the notebook.
ROLE_NAMES = ("role_proposed", "role_confirmed", "role_notes")
ROLE_NAMESPACE = "roles"

#: Shown first in the head table, before the role triple and the analyses.
IDENTITY_COLUMNS = ("label", "kind", "layer", "index")


# ==============================================================================
# THE FOUR SHAPES, AND THE ABSENCE OF ONE
# ==============================================================================


@dataclass
class Missing:
    """An analysis this cell does not contain.

    Falsy, so a notebook cell is `view = review.x(d)` then
    `if view: render(view) else: print(view.note)` — never a try/except and
    never a traceback in the middle of a review.
    """

    what: str
    note: str
    paths: Sequence[str] = ()

    def __bool__(self) -> bool:
        return False


@dataclass
class Table:
    title: str
    subtitle: str
    columns: List[str]
    rows: List[dict]
    #: Sentences to print beside the table: which optional columns are absent,
    #: which convention a number follows.
    notes: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    #: `{bare role name: the column that holds it}` for the roles present.
    role_columns: Dict[str, str] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return True


@dataclass
class Heatmap:
    """A matrix with named axes, ready for `plotly.express.imshow`."""

    title: str
    subtitle: str
    rows: List[str]
    columns: List[str]
    #: `[len(rows)][len(columns)]`, None where the cell does not exist.
    values: List[List[Optional[float]]]
    #: Symmetric colour limit taken from the JSON when it records one, so the
    #: notebook and the PNG of record are on the same scale. None means "let
    #: plotly choose".
    extent: Optional[float] = None
    notes: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return True


@dataclass
class Bars:
    """One bar per label, with standard errors when the analysis records them."""

    title: str
    subtitle: str
    labels: List[str]
    values: List[Optional[float]]
    errors: Optional[List[Optional[float]]] = None
    #: Parallel to `labels`, for hover text.
    hover: Optional[List[str]] = None
    notes: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return True


@dataclass
class Scatter:
    """One point per Component, the same quantity under two conditions."""

    title: str
    subtitle: str
    labels: List[str]
    x: List[Optional[float]]
    y: List[Optional[float]]
    x_title: str
    y_title: str
    x_se: Optional[List[Optional[float]]] = None
    y_se: Optional[List[Optional[float]]] = None
    notes: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return True


@dataclass
class Group:
    """Several views the notebook renders one after another under one heading.

    Falsy when empty, so a section that found its files but had nothing to draw
    reads the same way as one whose files are absent.
    """

    title: str
    subtitle: str
    items: List[Any]
    notes: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.items)


@dataclass
class Series:
    name: str
    y: List[Optional[float]]
    se: Optional[List[Optional[float]]] = None


@dataclass
class Lines:
    """The logit lens: one series per condition over the layer rows."""

    title: str
    subtitle: str
    x: List[int]
    x_title: str
    series: List[Series]
    notes: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return True


# ==============================================================================
# READING FILES
# ==============================================================================


def read_json(path: str):
    """The payload, or None when the file is not there."""
    if not os.path.isfile(path):
        return None
    with open(path) as handle:
        return json.load(handle)


def _missing(what: str, *paths: str) -> Missing:
    names = ", ".join(os.path.basename(one) for one in paths)
    return Missing(what=what,
                   note=f"no {what} in this cell — looked for {names}. "
                        f"Rerun `analyze_components.py` with that analysis "
                        f"selected to fill this section.",
                   paths=paths)


def found(directory: str, subdir: str, pattern: str) -> List[str]:
    """Every file of a subdirectory matching a glob, in sorted order."""
    return sorted(glob.glob(os.path.join(directory, subdir, pattern)))


def component_label(row) -> str:
    """`L17H3` for a head, `L17 MLP` for an MLP block — `dla.label_of`'s spelling.

    Copied rather than imported for the same reason the subdirectory names are:
    `dla` carries torch.
    """
    if isinstance(row, dict):
        kind, layer, index = row.get("kind"), row.get("layer"), row.get("index")
    else:
        kind, layer, index = tuple(row)
    if kind == "head":
        return f"L{layer}H{index}"
    if kind == "mlp":
        return f"L{layer} MLP"
    return str(kind)


def cell_subtitle(meta: dict, extra: str = "") -> str:
    """`circuit <label> · task <label>`, the line every section is read under."""
    circuit = (meta or {}).get("circuit", {}).get("label", "?")
    task = (meta or {}).get("task", {}).get("label", "?")
    line = f"circuit {circuit} · task {task}"
    return f"{line} · {extra}" if extra else line


# ==============================================================================
# THE HEAD TABLE
# ==============================================================================


def role_columns(columns: Sequence[str]) -> Dict[str, str]:
    """`{bare role name: the column holding it}` for the roles this cell has."""
    present = {}
    for name in ROLE_NAMES:
        for candidate in (f"{ROLE_NAMESPACE}.{name}", name):
            if candidate in columns:
                present[name] = candidate
                break
    return present


def _ordered_columns(columns: Sequence[str], roles: Dict[str, str]) -> List[str]:
    ordered = [one for one in IDENTITY_COLUMNS if one in columns or one == "label"]
    ordered += [roles[name] for name in ROLE_NAMES if name in roles]
    ordered += [one for one in columns if one not in ordered]
    return ordered


def head_table_view(results_dir: str) -> Table:
    """The head table with a `label` column and the role triple brought forward.

    One row per Component, exactly as `head_table.write_head_table` wrote it;
    this adds the plot label and decides the column order, and says in a note
    when the role columns are not there yet.
    """
    path = os.path.join(results_dir, HEAD_TABLE_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("head table", path)

    rows = [dict(row) for row in payload.get("rows", [])]
    for row in rows:
        row["label"] = component_label(row)
    columns = list(payload.get("columns", []))
    roles = role_columns(columns)
    notes = []
    if not roles:
        notes.append(
            "no role columns yet — ticket 10's proposal step writes "
            "`roles.role_proposed` and `roles.role_notes`, and `role_confirmed` "
            "is the researcher's own column. Until then every Component is "
            "unlabelled.")
    meta = payload.get("meta", {})
    return Table(title="Head table",
                 subtitle=cell_subtitle(meta, f"{len(rows)} Component(s)"),
                 columns=_ordered_columns(columns, roles), rows=rows,
                 notes=notes, meta=meta, role_columns=roles)


# ==============================================================================
# ATTENTION PATTERNS
# ==============================================================================

#: `patterns_<level>.png` and its twin, one per level of the chosen split.
PATTERNS_TWIN_GLOB = "patterns_*.json"
PATTERNS_JSON = "patterns.json"
TOP_HEADS_JSON = "top_heads.json"


def _condition_subtitle(panel: dict, query_position: str) -> str:
    """Whose instances these are, and whether the contrast is causal.

    Spec user story 27: *"a paired honest-instruction column and an unpaired
    honest-twin column beside every descriptive analysis, clearly labelled
    paired versus descriptive, so that I never read a population contrast as a
    causal one."* The label is on the figure, not only in the column name.
    """
    stance = "paired" if panel.get("paired") else "descriptive (unpaired)"
    return (f"query position {query_position} · {panel.get('n')} instance(s) · "
            f"{stance}")


def attention_views(results_dir: str) -> "Group":
    """One Heatmap of Segment masses per (level, condition).

    Read from the figure twins rather than `patterns.json`, so that what the
    notebook draws is what the PNG of record drew. `patterns.json` is opened
    only for the sum-to-one check, which is the reason to trust either.
    """
    twins = [one for one in found(results_dir, ATTENTION_SUBDIR,
                                  PATTERNS_TWIN_GLOB)
             if os.path.basename(one) != PATTERNS_JSON]
    if not twins:
        return _missing("attention patterns",
                        os.path.join(results_dir, ATTENTION_SUBDIR,
                                     PATTERNS_TWIN_GLOB))

    items = []
    for path in twins:
        payload = read_json(path)
        level = payload.get("level", "?")
        query_position = payload.get("query_position", "?")
        for panel in payload.get("panels", []):
            items.append(Heatmap(
                title=f"attention mass per Segment — {panel.get('kind')} ({level})",
                subtitle=_condition_subtitle(panel, query_position),
                rows=list(payload.get("rows", [])),
                columns=list(payload.get("columns", [])),
                values=[list(row) for row in panel.get("matrix", [])]))

    notes = []
    checks = read_json(os.path.join(results_dir, ATTENTION_SUBDIR, PATTERNS_JSON))
    if checks:
        tolerance = checks.get("sum_tolerance")
        for condition in checks.get("conditions", []):
            report = condition.get("checks", {})
            verdict = ("sum to one" if report.get("sums_to_one")
                       else "DO NOT sum to one")
            notes.append(
                f"{condition.get('name')}: the rows {verdict} "
                f"(largest deviation {report.get('max_abs_sum_minus_one'):.2g}, "
                f"tolerance {tolerance}), {report.get('n_nan')} NaN row(s).")
    return Group(title="Attention patterns by Segment",
                 subtitle=cell_subtitle(_cell_meta(results_dir)),
                 items=items, notes=notes)


def top_heads_view(results_dir: str) -> Heatmap:
    """The same matrix cut to the heads the cell ranked highest."""
    path = os.path.join(results_dir, ATTENTION_SUBDIR, TOP_HEADS_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("top-head attention summary", path)
    return Heatmap(
        title=f"top heads — {payload.get('condition')} ({payload.get('level')})",
        subtitle=(f"query position {payload.get('query_position')} · "
                  f"ranked by {payload.get('ranked_by')}"),
        rows=list(payload.get("rows", [])),
        columns=list(payload.get("columns", [])),
        values=[list(row) for row in payload.get("matrix", [])])


def coloured_tokens(heatmap: Heatmap):
    """`(tokens, values, labels)` for `circuitsvis.tokens.colored_tokens_multi`.

    circuitsvis colours a run of tokens by one value each, and its `_multi`
    form takes `[n_tokens][n_series]`. The Segments are the tokens — this is a
    Segment-level view, not a token-level one — and each head is a series, so
    the matrix is the transpose of the one plotly draws.
    """
    values = [[row[column] for row in heatmap.values]
              for column in range(len(heatmap.columns))]
    return list(heatmap.columns), values, list(heatmap.rows)


# ==============================================================================
# DIRECT LOGIT ATTRIBUTION AND THE LOGIT LENS
# ==============================================================================

DLA_JSON = "dla.json"
PAIRED_SCATTER_JSON = "dla_paired_scatter.json"
LENS_JSON = "logit_lens.json"
PAIRED_LENS_JSON = "logit_lens_paired.json"

#: Every condition is reported at this level as well as at each split level;
#: the notebook's default view is the pooled one.
ALL_LEVEL = "all"


def _stat(levels: dict, level: str, field_name: str):
    return (levels or {}).get(level, {}).get(field_name)


def dla_view(results_dir: str, level: str = ALL_LEVEL) -> "Group":
    """One Bars per condition, in head-table order, the embedding last."""
    path = os.path.join(results_dir, DLA_SUBDIR, DLA_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("direct logit attribution", path)

    items = []
    for name, condition in payload.get("conditions", {}).items():
        components = condition.get("components", [])
        embedding = condition.get("embedding")
        labels = [one.get("label") for one in components]
        values = [_stat(one.get("levels"), level, "mean") for one in components]
        errors = [_stat(one.get("levels"), level, "se") for one in components]
        if embedding:
            labels.append(embedding.get("label", "embed"))
            values.append(_stat(embedding.get("levels"), level, "mean"))
            errors.append(_stat(embedding.get("levels"), level, "se"))
        totals = condition.get("totals", {}).get(level, {})
        model = totals.get("model_logit_difference", {})
        items.append(Bars(
            title=f"direct logit attribution — {name}",
            subtitle=(f"{condition.get('n_instances')} instance(s) · level "
                      f"{level} · the model's own logit difference is "
                      f"{_number(model.get('mean'))}"),
            labels=labels, values=values, errors=errors))

    notes = [payload.get("metric", ""),
             f"The suppression flag is set when a Component's attribution "
             f"favours the Distractor by more than "
             f"{payload.get('suppression_margin')}.",
             payload.get("fixed_scale", "")]
    return Group(title="Direct logit attribution at the Readout",
                 subtitle=cell_subtitle(_cell_meta(results_dir)),
                 items=items, notes=[one for one in notes if one])


def dla_scatter_view(results_dir: str) -> "Scatter":
    """Each Component under pressure against itself under the honest instruction."""
    path = os.path.join(results_dir, DLA_SUBDIR, PAIRED_SCATTER_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("paired DLA scatter", path)
    if payload.get("skipped"):
        return Missing(what="paired DLA scatter", note=payload["skipped"],
                       paths=(path,))
    points = payload.get("points", [])
    return Scatter(
        title="Paired DLA: pressure against the Matched Honest Instruction",
        subtitle=(f"{payload.get('n_instances')} paired instance(s) · "
                  f"{payload.get('diagonal')}"),
        labels=[one.get("label") for one in points],
        x=[one.get("x") for one in points], y=[one.get("y") for one in points],
        x_se=[one.get("x_se") for one in points],
        y_se=[one.get("y_se") for one in points],
        x_title=payload.get("x", ""), y_title=payload.get("y", ""),
        notes=[payload.get("metric", "")])


def _lens_notes(conditions: dict) -> List[str]:
    notes = []
    for name, condition in conditions.items():
        layer = condition.get("sign_flip_layer")
        if layer is None:
            notes.append(f"{name}: the lens never changes sign, so the "
                         f"deceptive answer never overtakes within the stack.")
        else:
            notes.append(f"{name}: the deceptive answer first overtakes the "
                         f"honest one after layer {layer} "
                         f"(row {condition.get('sign_flip_row')}).")
    return notes


def logit_lens_views(results_dir: str) -> "Group":
    """The cumulative-residual lens: every condition, then the paired overlay."""
    path = os.path.join(results_dir, DLA_SUBDIR, LENS_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("logit lens", path)

    conditions = payload.get("conditions", {})
    items = []
    series = []
    x = []
    for name, condition in conditions.items():
        level = condition.get("levels", {}).get(ALL_LEVEL, {})
        mean = level.get("mean", [])
        x = x or list(range(len(mean)))
        series.append(Series(name=name, y=list(mean), se=level.get("se")))
    items.append(Lines(title="Logit lens at the Readout",
                       subtitle=cell_subtitle(_cell_meta(results_dir),
                                              f"level {ALL_LEVEL}"),
                       x=x, x_title=payload.get("rows", "row"), series=series))

    overlay = read_json(os.path.join(results_dir, DLA_SUBDIR, PAIRED_LENS_JSON))
    if overlay and not overlay.get("skipped"):
        paired = overlay.get("conditions", {})
        items.append(Lines(
            title="Logit lens, paired conditions only",
            subtitle=overlay.get("shows", ""),
            x=list(range(len(next(iter(paired.values()), {}).get("mean", [])))),
            x_title=overlay.get("rows", "row"),
            series=[Series(name=name, y=list(one.get("mean", [])),
                           se=one.get("se"))
                    for name, one in paired.items()]))

    return Group(title="Logit lens", subtitle=payload.get("metric", ""),
                 items=items, notes=_lens_notes(conditions))


def _number(value) -> str:
    return "unavailable" if value is None else f"{value:.3f}"


def _cell_meta(results_dir: str) -> dict:
    payload = read_json(os.path.join(results_dir, HEAD_TABLE_JSON)) or {}
    return payload.get("meta", {})


# ==============================================================================
# KNOCKOUT
# ==============================================================================

KNOCKOUT_JSON = "knockout.json"
#: Ticket 10 writes the family-level knockout beside the per-Component one. Its
#: exact filename is that ticket's to choose, so the section globs for it and
#: renders a note until one appears.
FAMILY_KNOCKOUT_GLOB = "family*.json"


def knockout_view(results_dir: str) -> Bars:
    """Components ranked by how much removing one costs the deceptive answer."""
    path = os.path.join(results_dir, KNOCKOUT_SUBDIR, KNOCKOUT_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("per-Component knockout", path)
    return _knockout_bars(payload, title="Interchange knockout, one Component "
                                         "at a time")


def family_knockout_view(results_dir: str) -> Bars:
    """The same knockout grouped by Component Role, once roles exist."""
    matches = found(results_dir, KNOCKOUT_SUBDIR, FAMILY_KNOCKOUT_GLOB)
    if not matches:
        return Missing(
            what="family knockout",
            note="no family knockout in this cell — it is written by the "
                 "role-family pass (ticket 10), which needs a role column "
                 "first. Looked for knockout/family*.json.",
            paths=(os.path.join(results_dir, KNOCKOUT_SUBDIR,
                                FAMILY_KNOCKOUT_GLOB),))
    payload = read_json(matches[0])
    return _knockout_bars(payload, title="Interchange knockout by role family")


def _knockout_bars(payload: dict, *, title: str) -> Bars:
    rows = payload.get("components") or payload.get("families") or []
    clean = payload.get("clean_run", {})
    metric = payload.get("metric", {})
    labels = [row.get("label") or row.get("role") or component_label(row.get("key"))
              for row in rows]
    hover = [f"rank {row.get('rank')} · accuracy {row.get('accuracy')} "
             f"(clean run {clean.get('accuracy')}) · n={row.get('n')}"
             for row in rows]
    return Bars(
        title=title,
        subtitle=(f"{payload.get('scheme')} ablation · clean logit difference "
                  f"{_number(clean.get('mean_logit_difference'))} over "
                  f"{clean.get('n_instances')} instance(s)"),
        labels=labels,
        values=[row.get("mean_drop") for row in rows],
        errors=[row.get("standard_error") for row in rows],
        hover=hover,
        notes=[metric.get("sign", ""), metric.get("ablation", ""),
               metric.get("accuracy", "")])


# ==============================================================================
# PATH PATCHING
# ==============================================================================

AGNOSTIC_HEATMAP_GLOB = "heatmap*.json"
SEGMENTS_HEATMAP_GLOB = "segments_heatmap*.json"
DIRECT_EFFECT_GLOB = "direct_effect*.json"
SWEEP_BARS_JSON = "sweep_bars.json"


def _receiver_labels(columns: Sequence) -> List[str]:
    """Receiver columns are dicts carrying a `key`; rows are already strings."""
    return [one["key"] if isinstance(one, dict) else str(one) for one in columns]


def path_patching_views(results_dir: str) -> "Group":
    """Both passes of both counterfactuals: agnostic grid, direct effect, Segments.

    The sign convention differs from knockout's on purpose (block D decision,
    2026-09-16), so every view carries its own JSON's `metric.sign` sentence
    rather than a convention this module assumes.
    """
    agnostic = [one for one in found(results_dir, PATH_PATCHING_SUBDIR,
                                     AGNOSTIC_HEATMAP_GLOB)
                if "segments" not in os.path.basename(one)]
    segments = found(results_dir, PATH_PATCHING_SUBDIR, SEGMENTS_HEATMAP_GLOB)
    direct = found(results_dir, PATH_PATCHING_SUBDIR, DIRECT_EFFECT_GLOB)
    if not (agnostic or segments or direct):
        return _missing("path patching",
                        os.path.join(results_dir, PATH_PATCHING_SUBDIR,
                                     AGNOSTIC_HEATMAP_GLOB))

    items = []
    notes = []
    for path in agnostic:
        payload = read_json(path)
        counterfactual = payload.get("counterfactual", "?")
        scale = payload.get("colour_scale", {})
        items.append(Heatmap(
            title=f"position-agnostic path patching ({counterfactual})",
            subtitle=(f"sender rows into receiver columns · "
                      f"{scale.get('cells_beyond_the_scale')} cell(s) beyond "
                      f"the colour scale"),
            rows=[str(one) for one in payload.get("rows", [])],
            columns=_receiver_labels(payload.get("columns", [])),
            values=[list(row) for row in payload.get("values", [])],
            extent=scale.get("extent"),
            notes=[payload.get("missing", "")]))
        notes.append(payload.get("metric", {}).get("sign", ""))
    for path in direct:
        payload = read_json(path)
        senders = payload.get("senders", [])
        items.append(Bars(
            title=f"direct effect on the Readout "
                  f"({payload.get('counterfactual', '?')})",
            subtitle=f"receiver {payload.get('receiver')}",
            labels=[one.get("sender") for one in senders],
            values=[one.get("mean") for one in senders],
            errors=[one.get("se") for one in senders],
            hover=[f"n={one.get('n')} · {one.get('n_excluded')} excluded"
                   for one in senders]))
    for path in segments:
        payload = read_json(path)
        items.append(Heatmap(
            title=f"path patching by Segment "
                  f"({payload.get('counterfactual', '?')})",
            subtitle=(f"only the sender-receiver pairs clearing "
                      f"{payload.get('threshold')} of the clean-minus-"
                      f"counterfactual gap were swept by Segment"),
            rows=[str(one) for one in payload.get("rows", [])],
            columns=[str(one) for one in payload.get("columns", [])],
            values=[list(row) for row in payload.get("values", [])],
            notes=[payload.get("missing", "")]))

    seen = []
    for note in notes:
        if note and note not in seen:
            seen.append(note)
    return Group(title="Path patching", subtitle=cell_subtitle(_cell_meta(results_dir)),
                 items=items, notes=seen)


def sweep_view(results_dir: str) -> Bars:
    """Every head and MLP block as a sender into the Readout, ranked."""
    path = os.path.join(results_dir, PATH_PATCHING_SUBDIR, SWEEP_BARS_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("completeness sweep", path)
    senders = payload.get("senders", [])
    return Bars(
        title=f"Completeness sweep into the Readout "
              f"({payload.get('counterfactual', '?')})",
        subtitle=(f"top {payload.get('n_shown')} of {payload.get('n_senders')} "
                  f"senders swept"),
        labels=[one.get("sender") for one in senders],
        values=[one.get("mean") for one in senders],
        errors=[one.get("se") for one in senders],
        hover=[("in the circuit" if one.get("in_circuit")
                else "not in the circuit")
               + (" · flagged" if one.get("flagged") else "")
               + f" · rank {one.get('rank')}"
               for one in senders],
        notes=[f"A sender is flagged when its direct effect clears "
               f"{payload.get('threshold')} of the clean-minus-counterfactual "
               f"gap; a flagged sender outside the circuit is one the pruning "
               f"missed.",
               payload.get("metric", {}).get("sign", "")])


# ==============================================================================
# SEGMENTATION AND SAMPLE
# ==============================================================================


def segmentation_view(results_dir: str) -> Table:
    """Which Segments were resolved, from where, and how often they are present.

    Spec user story 10: the segmentation actually used is written to the
    output *"so that no plot is read against the wrong spans"* — so it is read
    back here beside the plots rather than trusted.
    """
    path = os.path.join(results_dir, SEGMENTATION_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("segmentation", path)

    instances = payload.get("instances", [])
    sources = payload.get("segment_sources", {})
    rows = []
    for name in payload.get("segment_names", []):
        spans = [one.get("segments", {}).get(name, []) for one in instances]
        present = [span for span in spans if span]
        rows.append({
            "segment": name,
            "source": sources.get(name, "?"),
            "present_on": f"{len(present)} of {len(instances)}",
            "mean_tokens": (round(sum(len(one) for one in present) / len(present), 1)
                            if present else 0.0)})

    overrides = payload.get("overrides", {})
    overlapping = payload.get("report", {}).get(
        "instances_with_overlapping_segments", [])
    notes = [
        ("no Segment was overridden on the command line; every one is the "
         "task's default" if not overrides
         else f"overridden by regex: {', '.join(sorted(overrides))}"),
        (f"!! an override overlaps a default Segment on {len(overlapping)} "
         f"instance(s)" if overlapping
         else "no Segment overlaps another on any instance"),
        payload.get("partition", ""), payload.get("empty_spans", "")]
    return Table(title="Segmentation actually used",
                 subtitle=cell_subtitle(payload.get("meta", {}),
                                        f"{payload.get('n_instances')} instance(s) "
                                        f"of split {payload.get('split')}"),
                 columns=["segment", "source", "present_on", "mean_tokens"],
                 rows=rows, notes=[one for one in notes if one],
                 meta=payload.get("meta", {}))


def sample_view(results_dir: str) -> Table:
    """The causal sample's strata: what was available, wanted and drawn."""
    path = os.path.join(results_dir, SAMPLE_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("causal sample", path)

    factors = list(payload.get("factors", []))
    rows = []
    for stratum in payload.get("strata", []):
        row = dict(stratum.get("key", {}))
        row.update({"available": stratum.get("available"),
                    "target": stratum.get("target"),
                    "achieved": stratum.get("achieved")})
        rows.append(row)
    notes = [f"{factor}: " + ", ".join(
        f"{level}={count}" for level, count
        in payload.get("marginals", {}).get(factor, {}).items())
        for factor in factors]
    if not factors:
        notes.append("no factor has more than one level, so the sample is "
                     "unstratified.")
    inactive = payload.get("inactive_factors", {})
    if inactive:
        notes.append("not stratified over: " + ", ".join(sorted(inactive)))
    notes.append(payload.get("allocation_rule", ""))
    return Table(title="Causal sample",
                 subtitle=cell_subtitle(payload.get("meta", {}),
                                        f"{payload.get('n_drawn')} of "
                                        f"{payload.get('n_requested')} requested, "
                                        f"seed {payload.get('seed')}"),
                 columns=factors + ["available", "target", "achieved"],
                 rows=rows, notes=[one for one in notes if one],
                 meta=payload.get("meta", {}))
