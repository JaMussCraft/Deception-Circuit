"""component_analysis/review.py — reading a finished cell back for review.

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

from component_analysis import dla, head_table, knockout, path_patching

# ==============================================================================
# THE CELL'S LAYOUT
# ==============================================================================

HEAD_TABLE_JSON = head_table.JSON_NAME
SEGMENTATION_JSON = "segmentation.json"
SAMPLE_JSON = "sample.json"

#: Asked of the modules that own them, so a renamed output file breaks the
#: import rather than silently rendering "absent" over a file that is there.
#: `attention_patterns` is the one exception: it imports torch at module scope
#: (for its mass arithmetic), and this module has to import where torch is not
#: wanted, so its two names are spelled out and a test pins them.
ATTENTION_SUBDIR = "attention"
DLA_SUBDIR = dla.SUBDIR
KNOCKOUT_SUBDIR = knockout.SUBDIR
PATH_PATCHING_SUBDIR = path_patching.SUBDIR

#: The role triple. Ticket 10 writes the proposal and the notes under the
#: `roles` namespace; `role_confirmed` is the human's column and `head_table.py`
#: protects it under its bare name. Both spellings are accepted for all three,
#: so that a namespace decision made after this module was written does not
#: silently blank the role columns in the notebook.
ROLE_NAMES = ("role_proposed", "role_confirmed", "role_notes")
ROLE_NAMESPACE = "roles"

#: Why each one might not be there, said one column at a time. An
#: all-or-nothing note would say "no role columns" over a table that has two of
#: the three, which is exactly the table a researcher is reading when they want
#: to know where the third goes.
ROLE_ABSENCE = {
    "role_proposed": "the mechanical role pass has not run on this cell.",
    "role_confirmed": ("no tool writes it. It is the researcher's own column, "
                       "added by hand to the head table to own the final "
                       "label."),
    "role_notes": "the mechanical role pass has not run on this cell.",
}

#: The logit lens's x axis. The JSON's `rows` field is a paragraph saying
#: what a row is; it belongs in a note, not in an axis label.
ROW_AXIS = "residual row (0 = the embedding, l + 1 = after layer l)"

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

    @property
    def note(self) -> str:
        """What to print when this Group is falsy, spelled like `Missing.note`.

        A renderer reaches for `.note` on anything falsy, so an empty Group has
        to answer that question rather than raise in the middle of a review.
        """
        if self.notes:
            return " ".join(self.notes)
        return (f"{self.title}: the files are there but there is nothing to "
                f"draw in them.")


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
    """`L17H3` for a head, `L17 MLP` for an MLP block, via `dla.label_of`.

    Takes a head-table row, a key tuple or a key list, because the analyses
    write all three spellings. The label itself is `dla`'s to define: two
    spellings of the same head would read as two heads.
    """
    if isinstance(row, dict):
        key = (row.get("kind"), row.get("layer"), row.get("index"))
    else:
        key = tuple(row)
    return dla.label_of(key)


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
    for name in ROLE_NAMES:
        if name not in roles:
            notes.append(f"no {name} column: {ROLE_ABSENCE[name]}")
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
    # `patterns_*.json` does not match `patterns.json`, which is the data of
    # record rather than a figure twin.
    twins = found(results_dir, ATTENTION_SUBDIR, PATTERNS_TWIN_GLOB)
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
    record = read_json(os.path.join(results_dir, ATTENTION_SUBDIR, PATTERNS_JSON))
    if record:
        tolerance = record.get("sum_tolerance")
        for condition in record.get("conditions", []):
            report = condition.get("checks") or {}
            verdict = ("sum to one" if report.get("sums_to_one")
                       else "DO NOT sum to one")
            notes.append(
                f"{condition.get('name')}: the rows {verdict} (largest "
                f"deviation {_number(report.get('max_abs_sum_minus_one'), 2)}, "
                f"tolerance {_number(tolerance, 2)}), "
                f"{report.get('n_nan', 'an unrecorded number of')} NaN row(s).")
        notes += skipped_notes(record.get("skipped"))
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

DLA_JSON = dla.JSON_NAME
PAIRED_SCATTER_JSON = dla.PAIRED_SCATTER_JSON_NAME
LENS_JSON = dla.LENS_JSON_NAME
PAIRED_LENS_JSON = dla.PAIRED_LENS_JSON_NAME

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

    check = payload.get("sum_check") or {}
    notes = [payload.get("metric", ""),
             f"The suppression flag is set when a Component's attribution "
             f"favours the Distractor by more than "
             f"{payload.get('suppression_margin')}.",
             payload.get("fixed_scale", "")]
    if check:
        notes.append(
            f"Sum check: over {check.get('n_senders')} sender(s) on "
            f"{check.get('n_instances')} instance(s), the parts miss the "
            f"model's own logit difference by at most "
            f"{_number(check.get('max_abs_error'), 4)} against a mean "
            f"magnitude of "
            f"{_number(check.get('mean_abs_logit_difference'), 3)}.")
    notes += skipped_notes(payload.get("skipped"))
    return Group(title="Direct logit attribution at the Readout",
                 subtitle=cell_subtitle(_cell_meta(results_dir)),
                 items=items, notes=[one for one in notes if one])


def dla_heatmap(results_dir: str, level: str = ALL_LEVEL) -> Heatmap:
    """Every Component against every condition in one matrix.

    The bars answer "who writes the deceptive answer under pressure"; this
    answers "which Components write something different under the honest
    instruction", which is the differential column read as a picture. The
    colour scale is symmetric about zero and clipped to the largest magnitude
    in the matrix, so a suppressor reads as the opposite colour of a mover.
    """
    path = os.path.join(results_dir, DLA_SUBDIR, DLA_JSON)
    payload = read_json(path)
    if payload is None:
        return _missing("direct logit attribution", path)

    conditions = payload.get("conditions", {})
    names = list(conditions)
    first = conditions.get(names[0], {}) if names else {}
    rows = [one.get("label") for one in first.get("components", [])]
    if first.get("embedding"):
        rows.append(first["embedding"].get("label", "embed"))

    # Joined on the Component's label, not on its row number: the conditions
    # are separate passes over different instance sets, and one of them may
    # have dropped a Component. Reading by position would then put one
    # Component's attribution under another's name.
    by_label = {}
    for name, condition in conditions.items():
        entries = list(condition.get("components", []))
        if condition.get("embedding"):
            entries.append(condition["embedding"])
        by_label[name] = {one.get("label"): one for one in entries}

    values = [[_stat(by_label[name].get(label, {}).get("levels"), level, "mean")
               for name in names]
              for label in rows]

    magnitudes = [abs(one) for row in values for one in row if one is not None]
    return Heatmap(
        title="Direct logit attribution, every Component by condition",
        subtitle=cell_subtitle(_cell_meta(results_dir), f"level {level}"),
        rows=rows, columns=names, values=values,
        extent=max(magnitudes) if magnitudes else None,
        notes=[payload.get("metric", "")])


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
                       x=x, x_title=ROW_AXIS, series=series,
                       notes=[payload.get("rows", "")]))

    overlay = read_json(os.path.join(results_dir, DLA_SUBDIR, PAIRED_LENS_JSON))
    if overlay and not overlay.get("skipped"):
        paired = overlay.get("conditions", {})
        items.append(Lines(
            title="Logit lens, paired conditions only",
            subtitle=overlay.get("shows", ""),
            x=list(range(len(next(iter(paired.values()), {}).get("mean", [])))),
            x_title=ROW_AXIS,
            series=[Series(name=name, y=list(one.get("mean", [])),
                           se=one.get("se"))
                    for name, one in paired.items()]))

    return Group(title="Logit lens",
                 subtitle=cell_subtitle(_cell_meta(results_dir)),
                 items=items,
                 notes=[payload.get("metric", "")] + _lens_notes(conditions))


def _number(value, precision: int = 3) -> str:
    """A number for prose, or the word for its absence.

    Formatting a missing value raises rather than printing `None`, which is how
    an absent check key used to take a whole section down with it.
    """
    if value is None:
        return "unrecorded"
    try:
        return f"{value:.{precision}g}" if precision < 3 else f"{value:.{precision}f}"
    except (TypeError, ValueError):
        return str(value)


def skipped_notes(skipped) -> List[str]:
    """One sentence per condition an analysis could not compute.

    Spec user story 26 makes a Matched Honest Instruction that fails *"a data
    finding rather than a circuit finding"*, and the ticket's rule is that an
    absent analysis renders a note. A condition that was asked for and failed
    leaves no figure behind, so without this it reads exactly like one that was
    never asked for. The analyses write `skipped` as a list of entries or as a
    `{condition: reason}` mapping; both are read.
    """
    if not skipped:
        return []
    if isinstance(skipped, dict):
        return [f"not computed — {name}: {reason}"
                for name, reason in skipped.items()]
    notes = []
    for entry in skipped:
        if isinstance(entry, dict):
            name = entry.get("condition") or entry.get("name") or "a condition"
            notes.append(f"not computed — {name}: "
                         f"{entry.get('reason', 'no reason recorded')}")
        else:
            notes.append(f"not computed — {entry}")
    return notes


def _cell_meta(results_dir: str) -> dict:
    payload = read_json(os.path.join(results_dir, HEAD_TABLE_JSON)) or {}
    return payload.get("meta", {})


# ==============================================================================
# KNOCKOUT
# ==============================================================================

KNOCKOUT_JSON = knockout.JSON_NAME
#: The family-level knockout, written beside the per-Component one by the role
#: pass. `knockout_families.json` is the name that pass settled on; the second
#: pattern is kept so a cell written before it was settled still renders.
FAMILY_KNOCKOUT_GLOBS = ("knockout_families.json", "family*.json")


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
    matches = [one for pattern in FAMILY_KNOCKOUT_GLOBS
               for one in found(results_dir, KNOCKOUT_SUBDIR, pattern)]
    if not matches:
        return Missing(
            what="family knockout",
            note="no family knockout in this cell — it is written by the "
                 "role-family pass, which needs a role column first. Looked "
                 "for knockout/knockout_families.json.",
            paths=tuple(os.path.join(results_dir, KNOCKOUT_SUBDIR, pattern)
                        for pattern in FAMILY_KNOCKOUT_GLOBS))
    payload = read_json(matches[0])
    view = _knockout_bars(payload, title="Interchange knockout by role family")
    grouping = payload.get("grouping") or {}
    if grouping.get("column"):
        view.notes.append(f"Grouped by {grouping['column']}, read from "
                          f"{grouping.get('read_from')}, against the criteria "
                          f"in {grouping.get('criteria_doc')}.")
    if len(matches) > 1:
        view.notes.append(
            "more than one family file in this cell; showing "
            f"{os.path.basename(matches[0])} and ignoring "
            + ", ".join(os.path.basename(one) for one in matches[1:]))
    return view


def _knockout_bars(payload: dict, *, title: str) -> Bars:
    rows = payload.get("components") or payload.get("families") or []
    clean = payload.get("clean_run", {})
    metric = payload.get("metric", {})
    labels = [row.get("label") or row.get("role")
              or component_label(row.get("key") or ("?", 0, 0))
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
    # `heatmap*.json` anchors at the start of the basename, so the Segment
    # pass's `segments_heatmap*.json` is not caught here.
    agnostic = found(results_dir, PATH_PATCHING_SUBDIR, AGNOSTIC_HEATMAP_GLOB)
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
        # A Segment is a list of half-open [start, end) ranges, so its width is
        # the ranges summed, not the number of ranges. Counting the ranges made
        # a three-range, eight-token Segment read as three tokens wide.
        widths = [sum(end - start for start, end in span) for span in present]
        rows.append({
            "segment": name,
            "source": sources.get(name, "?"),
            "present_on": f"{len(present)} of {len(instances)}",
            "mean_tokens": (round(sum(widths) / len(widths), 1)
                            if widths else 0.0)})

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


# ==============================================================================
# WHAT THE LIVE SECTION NEEDS FROM THE CELL
# ==============================================================================
#
# The live section of the notebook calls `hooks`, `dla` and `path_patching`
# with the same signatures the CLI uses; the only thing it cannot take
# straight from those modules is a way to reach one instance's prompts without
# re-resolving the circuit expression. Every cell of record names run
# directories inside worktrees that have since been removed, so re-resolving
# would fail on a cell that is otherwise perfectly readable. The head table
# already records what the loaders need, and these two functions read it.


def model_name_of(meta: dict) -> str:
    """The model this cell was computed on, for `hooks.load_analysis_model`."""
    name = (meta or {}).get("intake", {}).get("model")
    if not name:
        raise ValueError(
            "this head table records no intake provenance, so the model it was "
            "computed on is unknown; set MODEL_NAME in the live section by hand")
    return name


def task_spec_from_meta(meta: dict):
    """An `evaluation.circuits.TaskSpec` rebuilt from a written cell.

    Imported inside the function: `evaluation.circuits` reaches the task
    registry, which the pure read-back path has no reason to load.
    """
    import argparse

    from evaluation.circuits import TaskSpec

    task = (meta or {}).get("task")
    if not task or not task.get("task"):
        raise ValueError(
            "this head table has no task provenance, so its instances cannot "
            "be reloaded; build the TaskSpec by hand in the live section")
    args = argparse.Namespace(task=task["task"], **task.get("dataset", {}))
    return TaskSpec(name=task["task"], label=task.get("label", task["task"]),
                    args=args, home_run_dir=task.get("home_run_dir"))
