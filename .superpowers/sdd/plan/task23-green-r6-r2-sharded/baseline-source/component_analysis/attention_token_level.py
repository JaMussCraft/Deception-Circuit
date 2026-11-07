"""
component_analysis/attention_token_level.py — each circuit head's attention,
token by token.

`--attention-token-level` asks the attention-pattern analysis
(`attention_patterns.py`) to also render, for every circuit head, the mean
attention from the query positions (the **Readout** by default) to every token
of the prompt, with no Segment summing. This module is that rendering; it is
not an analysis of its own and registers nothing. `attention_patterns.run`
feeds it the attention rows it already reads for the Segment masses, so it
costs no forward pass, and calls `write` at the end.

Lining tokens up
----------------
Prompts differ in length, so a mean over "position 37" would average different
words. Instances are therefore grouped by **Template Variant** and, within one,
by the order of the Segment runs their tokens fall into (on the saved SDR split
that is one order per variant). A token's place, its `Slot`, is its run and its
offset from whichever end of that run is nearer. A run that is the same width
everywhere — the chat shell, the Designation Positions, the question, the stem
— then lines up token for token; a run that varies (the intro around the
entity name, the Pressure Clause) lines up at both ends and is ragged only in
its middle. The Segments line tokens up; they are never summed.

Each slot's value is its summed attention divided by the group's instance
count, so an instance with no token at a slot contributes nothing there, which
is literally what it attended to. Every row then sums to one, and a Segment's
slots sum back to its mass in `patterns.json`.

A slot is labelled with the most common token there and, when that is not
every instance's token, the share that carries it.

What lands in the cell
----------------------
Under `attention/token_level/`: one `token_level_<head>.png` and JSON twin per
circuit head (a panel per group, a row per condition, a column per slot), and
one index, `token_level.json`, holding what every head shares — the groups,
their slot labels and Segments, the colour scale, and the instance ids behind
every row, once per cell rather than once per head. The per-head twins carry
their values only while together they stay under
`--attention-token-level-json-limit` bytes (default `JSON_LIMIT_BYTES`);
above it they are written meta-only and the PNGs are the record.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

import torch

from component_analysis import attention_patterns as ap

#: Where the files go, inside the attention analysis's own directory.
SUBDIR = "token_level"
#: The cell's one index: layout, labels, instance ids, colour scale.
INDEX = "token_level.json"
#: `<STEM>_<head label>.png` and its JSON twin, one per circuit head.
STEM = "token_level"

#: The default per-cell budget for the per-head twins' values, in bytes. On
#: SDR nls0.3 (17 heads, 1000 instances) the full twins are about 0.8 MB.
JSON_LIMIT_BYTES = 5_000_000

#: The colour scale: `attention_patterns.COLORMAP` through a square root on a
#: fixed 0..1. Most of a head's mass sits on a few tokens (on Llama, often the
#: `<|begin_of_text|>` sink) and the rest is spread thin over a hundred, so a
#: linear scale draws everything but the sink at the palest colour. One fixed
#: scale for every head and every cell keeps two PNGs comparable by eye, and a
#: mass of 0.01 is a tenth of the way up the map.
SCALE = {"norm": "power", "gamma": 0.5, "vmin": 0.0, "vmax": 1.0}
#: Colour-bar ticks, so a reader of the square-root scale can read a mass off it.
TICKS = (0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0)

#: How many of a row's largest tokens its twin names, largest first.
TOP = 8

#: The two families of prompts a group can hold. The three conditions on the
#: task's own prompts share groups and labels; the honest twin is a different
#: dataset and gets groups of its own. Not the condition names: the task-prompt
#: family holds the `pressure`, `pressure_paired` and `honest_instruction` rows.
TASK_PROMPTS = "task_prompts"
TWIN_PROMPTS = "honest_twin_prompts"

#: The conditions whose prompts label the slots. Not the honest instruction:
#: its prompt is its pressure prompt with the clause replaced, so it reads the
#: pressure prompt's labels, and inside the Pressure Clause its own tokens are
#: the Matched Honest Instruction's rather than the label shown.
LABEL_CONDITIONS = (ap.PRESSURE, ap.PRESSURE_PAIRED, ap.HONEST_TWIN,
                    ap.PRESSURE_NEUTRAL_TWIN_PAIRED)

#: Every condition, in the order rows are drawn. The two v2 twin rows (ticket
#: 02b) come last and exist only on a v2 cell; the twin is token-matched to
#: its pressure prompt, so it is a task-prompt row like the honest instruction.
ROW_ORDER = (ap.PRESSURE, ap.PRESSURE_PAIRED, ap.HONEST_INSTRUCTION,
             ap.HONEST_TWIN, ap.PRESSURE_NEUTRAL_TWIN_PAIRED, ap.NEUTRAL_TWIN)

#: What a record says when it carries no `template_variant`.
NO_VARIANT = "-"

#: The run name of tokens no Segment claims. The default Segments partition the
#: prompt, so only an override that leaves gaps produces one.
UNCLAIMED_RUN = "unclaimed"

#: What the index and `patterns.json` say the per-head twins hold.
FULL, META_ONLY, NOT_PROFILED = "full", "meta-only", "none"

#: Said in every per-head twin, where a reader looks for the ids first.
INSTANCE_IDS_NOTE = (
    f"The instance ids are recorded once per cell, in {INDEX} under "
    f"groups[].rows[].instance_ids, rather than in each head's twin: every "
    f"head of a cell is averaged over the same instances.")

# --- figure geometry, in inches unless named otherwise -----------------------
#: The token labels' font size, in points, and a character's width in ems.
LABEL_FONT_PT = 5.5
CHAR_WIDTH_EM = 0.6
#: Longest token label drawn on an axis; the twin keeps the whole string.
AXIS_LABEL_CHARS = 24
ROW_HEIGHT = 0.3
PANEL_PADDING = 0.9
SLOT_WIDTH = 0.12
SIDE_MARGINS = 3.0
MIN_WIDTH = 8.0


# ==============================================================================
# THE FLAGS
# ==============================================================================

def add_arguments(group) -> None:
    """Two flags, under the attention analysis's prefix and in its group."""
    group.add_argument("--attention-token-level", action="store_true",
                       help="Also render, per circuit head, the mean attention "
                            "from the query positions to every token of the "
                            "prompt (no Segment summing), one PNG per head "
                            f"under {ap.SUBDIR}/{SUBDIR}/, grouped by Template "
                            "Variant. Read from the same forward passes, so it "
                            "adds no GPU pass.")
    group.add_argument("--attention-token-level-json-limit", type=int,
                       default=JSON_LIMIT_BYTES, metavar="BYTES",
                       help="The per-head token-level JSON twins carry their "
                            "values only while together they stay under this "
                            "many bytes per cell, and are meta-only above it "
                            f"(default {JSON_LIMIT_BYTES}).")


def wanted(cli) -> bool:
    """Whether this run renders the token level at all."""
    return bool(getattr(cli, "attention_token_level", False))


def json_limit(cli) -> int:
    return int(getattr(cli, "attention_token_level_json_limit", JSON_LIMIT_BYTES))


def payload_label(full: bool) -> str:
    return FULL if full else META_ONLY


# ==============================================================================
# SLOTS
# ==============================================================================

class Slot(NamedTuple):
    """A token's place in its group: its run, which end of the run it is
    counted from, and how far from that end."""

    run: int
    from_end: bool
    offset: int


class RowKey(NamedTuple):
    """One row of a panel: a condition read from one query Segment."""

    condition: str
    query: str


def segment_runs(segmentation, names: Sequence[str]) -> List[Tuple[str, int]]:
    """`[(Segment name, width)]`: the prompt as maximal runs of one Segment.

    Interleaved Segments (the intro around its two Item Mentions) are several
    runs, in prompt order. A token no Segment claims is a run named
    `UNCLAIMED_RUN`.
    """
    ids = ap.segment_ids(segmentation, names, segmentation.n_tokens).tolist()
    runs: List[List] = []
    for owner in ids:
        name = names[owner] if owner >= 0 else UNCLAIMED_RUN
        if runs and runs[-1][0] == name:
            runs[-1][1] += 1
        else:
            runs.append([name, 1])
    return [(name, width) for name, width in runs]


def slots_of(runs: Sequence[Tuple[str, int]]) -> List[Slot]:
    """One `Slot` per token, counted from the nearer end of its run.

    The first half of a run of width w (rounded up) is counted from its start
    and the rest from its end, so two runs of different width agree on their
    first and last tokens and differ only in the middle.
    """
    slots = []
    for run, (_name, width) in enumerate(runs):
        left = (width + 1) // 2
        for k in range(width):
            slots.append(Slot(run, False, k) if k < left
                         else Slot(run, True, width - 1 - k))
    return slots


def display_token(text: str) -> str:
    """A token as a label: control characters visible, nothing else changed."""
    return text.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


def axis_label(label: str) -> str:
    """A slot label cut to `AXIS_LABEL_CHARS`, so one long token cannot take
    the figure's height."""
    if len(label) <= AXIS_LABEL_CHARS:
        return label
    return label[:AXIS_LABEL_CHARS - 1] + "\u2026"


# ==============================================================================
# ACCUMULATING
# ==============================================================================

class TokenGroup:
    """Running sums for one group of prompts that share a token layout."""

    def __init__(self, family: str, variant: str, run_names: tuple):
        self.family = family
        self.variant = variant
        self.run_names = run_names
        #: `[left, right]` per run: the most slots seen from each end.
        self.widths = [[0, 0] for _ in run_names]
        self.sums: Dict[RowKey, Dict[Slot, "object"]] = {}
        self.present: Dict[RowKey, Dict[Slot, int]] = {}
        self.ids: Dict[RowKey, List[str]] = {}
        #: `{slot: {token id: how many labelling instances have it there}}`.
        self.token_counts: Dict[Slot, Dict[int, int]] = {}
        #: The record ids already counted into `token_counts`, so an instance
        #: read under two conditions labels its slots once.
        self.labelled_ids: set = set()

    def add(self, row: RowKey, record_id: str, slots: Sequence[Slot], values,
            token_ids, *, label: bool) -> None:
        """One instance: `values` is `[heads, n_tokens]` of its mean attention
        from the query Segment, `token_ids` its prompt."""
        sums = self.sums.setdefault(row, {})
        present = self.present.setdefault(row, {})
        self.ids.setdefault(row, []).append(record_id)
        for position, slot in enumerate(slots):
            width = self.widths[slot.run]
            side = 1 if slot.from_end else 0
            width[side] = max(width[side], slot.offset + 1)
            if slot in sums:
                sums[slot] = sums[slot] + values[:, position]
            else:
                sums[slot] = values[:, position].copy()
            present[slot] = present.get(slot, 0) + 1
        if label and record_id not in self.labelled_ids:
            self.labelled_ids.add(record_id)
            for position, slot in enumerate(slots):
                counts = self.token_counts.setdefault(slot, {})
                token = int(token_ids[position])
                counts[token] = counts.get(token, 0) + 1

    def slots(self) -> List[Slot]:
        """Every slot in prompt order: a run's left half, then its right."""
        out = []
        for run, (left, right) in enumerate(self.widths):
            out += [Slot(run, False, k) for k in range(left)]
            out += [Slot(run, True, k) for k in reversed(range(right))]
        return out

    def row_keys(self, query_names: Sequence[str]) -> List[RowKey]:
        """The rows this group holds, in `ROW_ORDER` and query order."""
        return [RowKey(condition, query) for condition in ROW_ORDER
                for query in query_names if RowKey(condition, query) in self.sums]

    def most_common_tokens(self, slots: Sequence[Slot]
                           ) -> List[Tuple[Optional[int], float]]:
        """`[(token id, share of labelling instances carrying it)]` per slot,
        `(None, 0.0)` where no labelling instance has a token."""
        out = []
        for slot in slots:
            counts = self.token_counts.get(slot, {})
            if not counts:
                out.append((None, 0.0))
                continue
            token, count = max(counts.items(),
                               key=lambda item: (item[1], -item[0]))
            out.append((token, count / sum(counts.values())))
        return out

    def means(self, row: RowKey, head: int, slots: Sequence[Slot]) -> List[float]:
        """One head's row: each slot's summed attention over the row's n."""
        n = len(self.ids[row])
        sums = self.sums[row]
        return [float(sums[slot][head]) / n if slot in sums else 0.0
                for slot in slots]

    def size(self) -> int:
        return max((len(ids) for ids in self.ids.values()), default=0)


class TokenProfiles:
    """Token-level means for every condition, grouped by token layout."""

    def __init__(self, head_keys, names, query_names):
        self.head_keys = list(head_keys)
        self.names = list(names)
        self.query_names = list(query_names)
        self.groups: Dict[tuple, TokenGroup] = {}

    def add(self, condition: str, one, rows: dict, positions_valid,
            slots) -> None:
        """One batch of one condition. `one` is an `attention_patterns.Slice`,
        `rows` is `{(layer, head): [batch, query slots, keys]}`, the raw
        attention rows of this batch, and `slots` names its query columns."""
        stacked = torch.stack([rows[(key[1], key[2])] for key in self.head_keys],
                              dim=1).float()          # [batch, heads, slots, keys]
        family = TWIN_PROMPTS if condition == ap.HONEST_TWIN else TASK_PROMPTS
        label = condition in LABEL_CONDITIONS
        for row, (record, segmentation) in enumerate(
                zip(one.records, one.segmentations)):
            n_tokens = segmentation.n_tokens
            runs = segment_runs(segmentation, self.names)
            variant = str(record.get("template_variant") or NO_VARIANT)
            names = tuple(name for name, _width in runs)
            group = self.groups.get((family, variant, names))
            if group is None:
                group = self.groups[(family, variant, names)] = TokenGroup(
                    family, variant, names)
            token_slots = slots_of(runs)
            token_ids = one.input_ids[row, :n_tokens].tolist()
            for query in self.query_names:
                columns = [i for i, (name, _k) in enumerate(slots)
                           if name == query and bool(positions_valid[row, i])]
                if not columns:
                    continue
                values = stacked[row][:, columns, :n_tokens].mean(1).numpy()
                group.add(RowKey(condition, query), segmentation.record_id,
                          token_slots, values, token_ids, label=label)

    def ordered_groups(self) -> List[Tuple[str, TokenGroup]]:
        """`[(group id, group)]`: the task's prompts first, larger groups first.

        A group id is `<family>/<Template Variant>`, with `#2`, `#3` after it
        when one variant holds more than one token layout.
        """
        out, seen = [], {}
        for family in (TASK_PROMPTS, TWIN_PROMPTS):
            members = sorted((group for group in self.groups.values()
                              if group.family == family),
                             key=lambda group: (-group.size(), group.variant))
            for group in members:
                base = f"{family}/{group.variant}"
                seen[base] = seen.get(base, 0) + 1
                out.append((base if seen[base] == 1 else f"{base}#{seen[base]}",
                            group))
        return out


# ==============================================================================
# PAYLOADS
# ==============================================================================

def _row_label(row: RowKey, n: int, query_names) -> str:
    where = f" @ {row.query}" if len(query_names) > 1 else ""
    return f"{row.condition}{where} (n={n})"


def payloads(tokens: TokenProfiles, tokenizer, *, labels) -> Tuple[dict, dict]:
    """`(index groups, {head label: panels})` — what the figures are drawn from.

    The index groups hold what every head shares: each group's slots, their
    labels and Segments, and which instances stand behind each row. A head's
    panels hold its values and its largest tokens per row.
    """
    decoded: Dict[int, str] = {}

    def decode(token: int) -> str:
        if token not in decoded:
            decoded[token] = display_token(tokenizer.decode([token]))
        return decoded[token]

    index_groups, panels_by_head = [], {label: [] for label in labels}
    for group_id, group in tokens.ordered_groups():
        slots = group.slots()
        rows = group.row_keys(tokens.query_names)
        slot_segments = [group.run_names[slot.run] for slot in slots]
        slot_tokens, slot_share, slot_labels = [], [], []
        for token, share in group.most_common_tokens(slots):
            text = None if token is None else decode(token)
            slot_tokens.append(text)
            slot_share.append(share)
            slot_labels.append("?" if text is None else
                               text if share == 1.0 else f"{text} ({share:.0%})")
        rows_meta = [{
            "condition": row.condition, "query_position": row.query,
            "label": _row_label(row, len(group.ids[row]), tokens.query_names),
            "n_instances": len(group.ids[row]),
            "instance_ids": list(group.ids[row]),
            "n_present": [group.present[row].get(slot, 0) for slot in slots]}
            for row in rows]
        title = (f"{group_id} (Template Variant {group.variant}): averaged over "
                 + ", ".join(f"{meta['n_instances']} ({meta['condition']})"
                             for meta in rows_meta) + " instance(s)")
        index_groups.append({
            "group": group_id, "family": group.family,
            "template_variant": group.variant, "title": title,
            "n_slots": len(slots), "slot_labels": slot_labels,
            "slot_tokens": slot_tokens, "slot_token_share": slot_share,
            "slot_segments": slot_segments, "rows": rows_meta})
        for head, label in enumerate(labels):
            head_rows = []
            for row, meta in zip(rows, rows_meta):
                values = group.means(row, head, slots)
                top = sorted(range(len(values)), key=lambda i: -values[i])[:TOP]
                head_rows.append({
                    "condition": row.condition, "query_position": row.query,
                    "label": meta["label"], "n_instances": meta["n_instances"],
                    "values": values,
                    "top_tokens": [{"slot": i, "token": slot_labels[i],
                                    "segment": slot_segments[i],
                                    "mass": values[i]} for i in top]})
            panels_by_head[label].append({"group": group_id, "title": title,
                                          "rows": head_rows})
    return index_groups, panels_by_head


def regenerate(ctx, query_names: Sequence[str], full_bytes: int) -> str:
    """The exact flags that rewrite this cell's token level with full twins:
    the conditions the run profiled (the twin included on a v2 cell)."""
    conditions = ",".join(ap.wanted_conditions_for(ctx))
    return (f"Rerun analyze_components.py into this cell with the circuit "
            f"bindings recorded in head_table.json's meta (and the same --split "
            f"and --segment, if any), adding: --analyses attention_patterns "
            f"--attention-token-level --query-positions {','.join(query_names)} "
            f"--attention-conditions {conditions} "
            f"--attention-token-level-json-limit {full_bytes}. "
            f"The PNGs are complete either way.")


# ==============================================================================
# FIGURES AND FILES
# ==============================================================================

def plot(path: str, twin: dict, groups: Dict[str, dict]) -> None:
    """One head: a panel per group, a row per condition, a column per slot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import PowerNorm

    panels = twin["panels"]
    widest = max((groups[panel["group"]]["n_slots"] for panel in panels),
                 default=1)
    labels_of = {panel["group"]: [axis_label(one) for one in
                                  groups[panel["group"]]["slot_labels"]]
                 for panel in panels}
    # Room under each panel for its rotated token labels, from the longest one.
    label_inches = CHAR_WIDTH_EM * LABEL_FONT_PT / 72.0
    heights = [ROW_HEIGHT * max(1, len(panel["rows"])) + PANEL_PADDING
               + max((len(one) for one in labels_of[panel["group"]]), default=1)
               * label_inches for panel in panels]
    figure, axes = plt.subplots(
        max(1, len(panels)), 1, squeeze=False, constrained_layout=True,
        figsize=(max(MIN_WIDTH, SLOT_WIDTH * widest + SIDE_MARGINS),
                 sum(heights) + PANEL_PADDING),
        gridspec_kw={"height_ratios": heights or [1.0]})
    norm = PowerNorm(gamma=SCALE["gamma"], vmin=SCALE["vmin"], vmax=SCALE["vmax"])
    for axis, panel in zip(axes[:, 0], panels):
        group = groups[panel["group"]]
        image = axis.imshow([row["values"] for row in panel["rows"]],
                            aspect="auto", cmap=ap.colormap(), norm=norm,
                            interpolation="nearest")
        ap.show_missing_as_hatching(axis)
        axis.set_xticks(range(group["n_slots"]))
        axis.set_xticklabels(labels_of[panel["group"]], rotation=90,
                             fontsize=LABEL_FONT_PT)
        axis.set_yticks(range(len(panel["rows"])))
        axis.set_yticklabels([row["label"] for row in panel["rows"]], fontsize=7)
        axis.set_title(panel["title"], fontsize=8)
        figure.colorbar(image, ax=axis, fraction=0.02, pad=0.01, ticks=TICKS)
    figure.suptitle(twin["title"], fontsize=9)
    figure.savefig(path, dpi=150)
    plt.close(figure)


def write(ctx, tokens: TokenProfiles, payload: dict) -> dict:
    """Every head's PNG and twin, and the index; returns what `patterns.json`
    records about them. With nothing profiled, writes nothing and says so."""
    if not tokens.groups:
        return {"payload": NOT_PROFILED,
                "reason": "no condition was profiled, so there are no tokens "
                          "to render; see 'skipped'"}
    subdir = os.path.join(ap.SUBDIR, SUBDIR)
    directory = ctx.subdir(subdir)
    components = payload["components"]
    labels = [one["label"] for one in components]
    index_groups, panels_by_head = payloads(tokens, ctx.tokenizer, labels=labels)
    groups = {group["group"]: group for group in index_groups}
    queries = ", ".join(tokens.query_names)

    twins = {}
    for component in components:
        label = component["label"]
        twins[label] = {
            "figure": f"{STEM}_{label}.png",
            "shows": (f"{label}'s mean attention from {queries} to every "
                      f"token of the prompt, no Segment summing"),
            "title": (f"{label}: attention from {queries} to every token, "
                      f"mean over instances (n per row); colour "
                      f"{ap.COLORMAP}, square-root scale 0 to 1"),
            "head": component["key"], "label": label,
            "colormap": ap.COLORMAP, "colour_scale": SCALE,
            "index": INDEX, "instance_ids": INSTANCE_IDS_NOTE,
            "payload": FULL, "panels": panels_by_head[label]}
    full_bytes = sum(len(json.dumps(twin, indent=2)) for twin in twins.values())
    limit = json_limit(ctx.cli)
    full = full_bytes <= limit
    how = regenerate(ctx, tokens.query_names, full_bytes)

    heads = []
    for component in components:
        label = component["label"]
        twin = twins[label]
        plot(os.path.join(directory, twin["figure"]), twin, groups)
        if not full:
            twin = {key: value for key, value in twin.items() if key != "panels"}
            twin.update(
                payload=META_ONLY,
                shape=[{"group": panel["group"], "rows": len(panel["rows"]),
                        "slots": groups[panel["group"]]["n_slots"]}
                       for panel in panels_by_head[label]],
                json_limit_bytes=limit, full_twins_bytes=full_bytes,
                regenerate=how)
        name = f"{STEM}_{label}.json"
        ctx.write_json(subdir, name, twin)
        heads.append({"key": component["key"], "label": label,
                      "figure": twin["figure"], "twin": name})

    ctx.write_json(subdir, INDEX, {
        "analysis": ap.NAME, "schema_version": ap.SCHEMA_VERSION,
        "task": payload["task"], "circuit": payload["circuit"],
        "shows": (f"mean attention from {queries} to every token of the "
                  f"prompt, per circuit head; one PNG per head"),
        "colormap": ap.COLORMAP, "colour_scale": SCALE,
        "query_positions": list(tokens.query_names),
        "level": ap.ALL_LEVEL,
        "alignment": ("instances grouped by Template Variant and Segment-run "
                      "order; a token's slot is its run and its offset from "
                      "the nearer end of that run, so runs of varying width "
                      "are ragged only in the middle"),
        "values": ("summed attention over the group's instances divided by "
                   "the group's instance count, so every row sums to one and a "
                   "Segment's slots sum to its mass in patterns.json; "
                   "n_present says how many instances have a token at a slot"),
        "labels": ("the most common token at the slot among the group's "
                   "task-prompt (or honest-twin) instances, with the share "
                   "carrying it when it is not all of them; the "
                   "honest_instruction row reads the pressure labels, and "
                   "inside the Pressure Clause its own tokens are the Matched "
                   "Honest Instruction's"),
        "payload": payload_label(full),
        "json_limit_bytes": limit,
        "full_twins_bytes": full_bytes,
        "regenerate": how,
        "heads": heads, "groups": index_groups})
    return {"index": f"{SUBDIR}/{INDEX}", "payload": payload_label(full),
            "full_twins_bytes": full_bytes, "json_limit_bytes": limit,
            "n_heads": len(heads)}
