"""
component_analysis/receiver_category.py — where the pressure arrives at a head.

Mechanism-analysis spec §2.3 (R11(g)), ticket 02b. From a cell's path patching
under the Neutral-Clause Twin, each circuit head's **strongest incoming path**
at or above the floor (`FLOOR`, the roles doc's path floor) is read as exactly
one of

    q               it arrives at the head's own query input: the head
                    itself is steered by the pressure (what rule 4b reads
                    beside the other columns; the category alone names
                    no Component Role)
    kv_clause       at the K or V input of the head's KV group, carried from
                    the clause span: the head reads the clause directly
    kv_post_clause  at K or V, carried from positions after the clause
                    (question, response line, the item mentions, stem,
                    Readout): the head reads items the pressure already changed
    kv_unresolved   at K or V, but the cell has no position-specific split
                    (its |mean| is below --path-position-threshold), or the
                    split's top Segment is `unsegmented`; and, flagged `!!`,
                    a top Segment before the clause, which is impossible by
                    construction (every pre-clause position is identical in D
                    and its twin) and is a bug
    none            no incoming cell at or above the floor

The incoming cells of a head are those into its own `q.` receiver and into
its KV group's `k.` and `v.` receivers (K and V are per group, as
`path_patching._receives` reads them), so a K/V category is a claim about the
group's circuit heads together. The strongest is by absolute mean; on an exact
tie the tied cells are listed and the first in receiver order (q, k, v), then
layer, index and sender, is the path of record. Two tied K/V cells that agree
on the span class keep it; two that disagree are `kv_unresolved`.

Inputs are the files `path_patching/agnostic_neutral_twin.json` (the cells)
and `path_patching/segments_neutral_twin.json` (the splits, optional). CPU
only: it runs inside a path-patching job as the twin pass finishes, and again
on the login node as `analyze_components.py receiver-category CELL_DIR`. It
writes `path_patching/receiver_category_neutral_twin.json` and five head-table
columns under the `path_patching.` namespace (`COLUMNS`), covered by the twin
pass's own instance set.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from component_analysis import path_patching as pp
from component_analysis.head_table import (CAUSAL_SAMPLE_NEUTRAL_TWIN, add_coverage,
                                           load_head_table, load_head_table_meta,
                                           merge_columns, row_key, write_head_table)
from component_analysis.segmentation import MECHANISM_V2_SEGMENTS

NAME = "receiver_category"
#: The path floor of `docs/component-roles.md`: twice the measured cross-card
#: noise on a path-patching cell.
FLOOR = 0.01
#: Written under the `path_patching.` namespace, beside the columns it reads.
NAMESPACE = pp.NAME
COLUMN = "receiver_category_neutral_twin"
COLUMNS = (COLUMN, f"{COLUMN}_path", f"{COLUMN}_support", f"{COLUMN}_se",
           f"{COLUMN}_segment")
JSON_NAME = "receiver_category_neutral_twin.json"
CATEGORIES = ("q", "kv_clause", "kv_post_clause", "kv_unresolved", "none")
RECEIVER_ORDER = ("q", "k", "v")
CLAUSE = "pressure_clause"
UNSEGMENTED = "unsegmented"


# ==============================================================================
# SEGMENT CLASSES
# ==============================================================================

def segment_class(name: Optional[str]) -> str:
    """`clause`, `pre_clause`, `post_clause` or `unresolved`, by the v2 Segment
    order (`segmentation.MECHANISM_V2_SEGMENTS`; the v1 list is a subset in
    the same order, so a v1 name reads the same way)."""
    if name is None or name == UNSEGMENTED or name not in MECHANISM_V2_SEGMENTS:
        return "unresolved"
    position = MECHANISM_V2_SEGMENTS.index(name)
    clause = MECHANISM_V2_SEGMENTS.index(CLAUSE)
    if position == clause:
        return "clause"
    return "pre_clause" if position < clause else "post_clause"


# ==============================================================================
# ONE HEAD
# ==============================================================================

def incoming_receivers(receivers: Sequence[dict], key: tuple) -> List[dict]:
    """The receivers a patch reaches this head at: its own query, and its KV
    group's K and V (every receiver whose `circuit_heads` holds the head)."""
    _kind, layer, index = key
    return [one for one in receivers
            if one.get("kind") in RECEIVER_ORDER and one.get("layer") == layer
            and index in (one.get("circuit_heads") or [])]


def _rank_key(cell: dict):
    """Strongest first; an exact tie keeps the incoming list's order, which is
    the grid's (the head's query receiver, then its KV group's K and V, senders
    in run order) — the same stable sort `path_patching.strongest` applies for
    the `strongest_incoming` column, so the two name the same cell."""
    return -abs(cell["mean"])


def _class_of(cell: dict, splits: Dict[str, dict]) -> Tuple[str, Optional[str],
                                                           Optional[float], str]:
    """`(class, top Segment, its mean, note)` of one K or V cell's split."""
    split = splits.get(cell["cell"])
    if split is None:
        return ("unresolved", None, None,
                "no position-specific split for this cell (its |mean| is below "
                "--path-position-threshold, or the twin pass wrote no split)")
    top = split.get("top_segment") or {}
    segment, mean = top.get("segment"), top.get("mean")
    kind = segment_class(segment)
    if kind == "pre_clause":
        return ("unresolved", segment, mean,
                f"!! top Segment {segment} is before the clause, where D and "
                f"its twin are identical by construction: a bug in the split "
                f"or the pairing, not a reading")
    if kind == "unresolved":
        return ("unresolved", segment, mean,
                f"top Segment {segment!r} is not a position of the prompt")
    return (kind, segment, mean, "")


_CATEGORY_OF_CLASS = {"clause": "kv_clause", "post_clause": "kv_post_clause",
                      "unresolved": "kv_unresolved"}


class TwinPassSkipped(Exception):
    """The cell's neutral-twin pass ran but was skipped (no instance of the
    causal sample has a twin: an H or F cell, or a D cell the pairing missed),
    so its heads have no category. Nothing is written: the roles pass reads
    the absent columns as unmeasured, which is what they are, and a `none` here
    would say "measured, nothing above the floor" about a pass that measured
    nothing."""


def categorize_head(key: tuple, cells: Sequence[dict], splits: Dict[str, dict],
                    *, floor: float = FLOOR) -> dict:
    """One head's category from its incoming cells (already selected)."""
    empty = {"key": list(key), "category": "none", "path": None, "support": None,
             "se": None, "n": None, "segment": None, "segment_support": None,
             "tied": [], "note": ""}
    ranked = sorted((one for one in cells
                     if one.get("mean") is not None and abs(one["mean"]) >= floor),
                    key=_rank_key)
    if not ranked:
        return {**empty, "note": f"no incoming cell at or above the floor {floor}"}
    best = ranked[0]
    tied = [one for one in ranked if abs(one["mean"]) == abs(best["mean"])]
    tied_names = [one["cell"] for one in tied] if len(tied) > 1 else []
    out = {**empty, "path": best["cell"], "support": best["mean"], "se": best.get("se"),
           "n": best.get("n"), "tied": tied_names}
    kind = best["receiver"].split(".")[0]
    if kind == "q":
        out["category"] = "q"
        if tied_names:
            out["note"] = (f"tie at |mean| {abs(best['mean'])} with "
                           f"{', '.join(tied_names[1:])}; the grid's order decides, "
                           f"as for strongest_incoming")
        return out

    classes = [_class_of(one, splits) for one in tied]
    first_class, segment, segment_support, note = classes[0]
    if len({one[0] for one in classes}) > 1:
        out.update(category="kv_unresolved", segment=None, segment_support=None,
                   note=(f"tie at |mean| {abs(best['mean'])} between "
                         f"{', '.join(tied_names)} whose top Segments disagree: "
                         + "; ".join(f"{one['cell']}: {cls[1]}"
                                     for one, cls in zip(tied, classes))))
        return out
    out.update(category=_CATEGORY_OF_CLASS[first_class], segment=segment,
               segment_support=segment_support, note=note)
    if tied_names and not note:
        out["note"] = (f"tie at |mean| {abs(best['mean'])} between "
                       f"{', '.join(tied_names)}, agreeing on the span")
    return out


# ==============================================================================
# EVERY HEAD OF A CELL
# ==============================================================================

def categorize(agnostic: dict, segments: Optional[dict], heads: Sequence[tuple],
               *, floor: float = FLOOR) -> Dict[tuple, dict]:
    """`{head key: result}` from the two neutral-twin path-patching payloads."""
    receivers = agnostic.get("receivers") or []
    by_receiver: Dict[str, List[dict]] = {}
    for cell in agnostic.get("cells") or []:
        by_receiver.setdefault(cell["receiver"], []).append(cell)
    splits = {one["cell"]: one for one in (segments or {}).get("cells") or []}
    out = {}
    for key in heads:
        key = tuple(key)
        incoming = [cell for receiver in incoming_receivers(receivers, key)
                    for cell in by_receiver.get(receiver["key"], [])]
        out[key] = categorize_head(key, incoming, splits, floor=floor)
    return out


def columns(results: Dict[tuple, dict]) -> Dict[tuple, dict]:
    """The five head-table columns per head, bare (the CLI namespaces them)."""
    return {key: {COLUMN: one["category"], f"{COLUMN}_path": one["path"],
                  f"{COLUMN}_support": one["support"], f"{COLUMN}_se": one["se"],
                  f"{COLUMN}_segment": one["segment"]}
            for key, one in results.items()}


def counts(results: Dict[tuple, dict]) -> Dict[str, int]:
    return {category: sum(1 for one in results.values() if one["category"] == category)
            for category in CATEGORIES}


def payload(results: Dict[tuple, dict], *, floor: float, agnostic_file: str,
            segments_file: Optional[str], instance_ids: Sequence[str]) -> dict:
    return {
        "analysis": NAME,
        "counterfactual": pp.NEUTRAL_TWIN,
        "floor": floor,
        "categories": list(CATEGORIES),
        "rule": ("the strongest incoming cell by |mean| at or above the floor, among "
                 "the cells into the head's own q receiver and its KV group's k and "
                 "v receivers; q -> q; k or v by the split's top Segment: "
                 "pressure_clause -> kv_clause, after the clause -> kv_post_clause, "
                 "no split or unsegmented (or, a bug, before the clause) -> "
                 "kv_unresolved; ties listed, broken in receiver order q, k, v, "
                 "and kv_unresolved when tied K/V spans disagree"),
        "agnostic_file": agnostic_file,
        "segments_file": segments_file,
        "sample": {"n_instances": len(instance_ids), "instance_ids": list(instance_ids)},
        "counts": counts(results),
        "heads": [results[key] for key in results],
    }


def categorize_cell(subdir: str, heads: Sequence[tuple], *, floor: float = FLOOR):
    """`(results, payload)` read off the twin pass's files in `subdir`."""
    agnostic_file = os.path.join(subdir, pp.output_name(pp.AGNOSTIC_STEM, pp.NEUTRAL_TWIN, "json"))
    if not os.path.isfile(agnostic_file):
        raise FileNotFoundError(
            f"{agnostic_file}: this cell has no path-patching pass under the "
            f"Neutral-Clause Twin (--path-counterfactual neutral_twin or both on a "
            f"v2 cell), so there is nothing to categorize")
    segments_file = os.path.join(subdir, pp.output_name(pp.SEGMENTS_STEM, pp.NEUTRAL_TWIN, "json"))
    with open(agnostic_file) as handle:
        agnostic = json.load(handle)
    if agnostic.get("skipped"):
        raise TwinPassSkipped(
            f"{agnostic_file}: the neutral-twin pass was skipped "
            f"({agnostic['skipped']}), so this cell's heads have no receiver "
            f"category; the columns stay absent (unmeasured), not `none`")
    segments = None
    if os.path.isfile(segments_file):
        with open(segments_file) as handle:
            segments = json.load(handle)
    else:
        segments_file = None
    results = categorize(agnostic, segments, heads, floor=floor)
    ids = (agnostic.get("sample") or {}).get("instance_ids") or []
    return results, payload(results, floor=floor, agnostic_file=agnostic_file,
                            segments_file=segments_file, instance_ids=ids)


def write(cell_dir: str, *, floor: float = FLOOR) -> dict:
    """Categorize every head of the cell's head table and write it back.

    Returns `{"json": the category file, "head_table": what the table writer
    returned}`.
    """
    rows = load_head_table(cell_dir)
    meta = load_head_table_meta(cell_dir)
    heads = [row_key(row) for row in rows if row.get("kind") == "head"]
    subdir = os.path.join(cell_dir, pp.SUBDIR)
    results, out = categorize_cell(subdir, heads, floor=floor)
    rows = merge_columns(rows, columns(results), namespace=NAMESPACE)
    # Coverage over the measured instances (the pass's, less those the gap excluded), as the in-job hook declares
    # it through `path_patching.measured_ids` (02b review S4).
    with open(out["agnostic_file"]) as handle:
        excluded = set((json.load(handle).get("sample") or {}).get("excluded_by_gap") or [])
    measured = [one for one in out["sample"]["instance_ids"] if one not in excluded]
    meta = add_coverage(meta, COLUMNS, measured,
                        instance_set=CAUSAL_SAMPLE_NEUTRAL_TWIN, namespace=NAMESPACE)
    written = write_head_table(cell_dir, rows, meta=meta)
    path = os.path.join(subdir, JSON_NAME)
    with open(path, "w") as handle:
        json.dump(out, handle, indent=2)
    return {"json": path, "head_table": written}


# ==============================================================================
# CLI
# ==============================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="analyze_components.py receiver-category",
        description="The receiver category per head (spec 2.3) from a cell's "
                    "path patching under the Neutral-Clause Twin.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("cell_dir", help="The cell directory holding head_table.json "
                                    "and path_patching/agnostic_neutral_twin.json.")
    p.add_argument("--path-category-floor", type=float, default=FLOOR,
                   help="The smallest |mean| an incoming cell must have (the "
                        "job's flag of the same name).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the categories and write nothing.")
    return p


def main(argv=None) -> int:
    cli = build_parser().parse_args(argv)
    rows = load_head_table(cli.cell_dir)
    heads = [row_key(row) for row in rows if row.get("kind") == "head"]
    try:
        results, out = categorize_cell(os.path.join(cli.cell_dir, pp.SUBDIR), heads,
                                       floor=cli.path_category_floor)
    except (FileNotFoundError, TwinPassSkipped) as why:
        raise SystemExit(str(why))
    print(f"\nRECEIVER CATEGORY — {cli.cell_dir}")
    print(f"  floor: {cli.path_category_floor}; counts: {out['counts']}")
    for one in out["heads"]:
        _kind, layer, index = one["key"]
        support = "" if one["support"] is None else f"{one['support']:+.4f}"
        print(f"  L{layer}H{index}: {one['category']:<15} {one['path'] or '-':<28} "
              f"{support:>8} {one['segment'] or ''} {one['note']}")
    if cli.dry_run:
        print("\n  --dry-run: nothing written.")
        return 0
    written = write(cli.cell_dir, floor=cli.path_category_floor)
    print(f"\n  {written['head_table']['csv']}\n  {written['head_table']['json']}\n  "
          f"{written['json']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
