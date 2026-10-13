"""
component_analysis/roles.py — the mechanical Component Role proposal.

The four analyses each say one thing about a Component: where it reads
(attention patterns), what it writes (DLA), and what it depends on (knockout
and path patching). `CONTEXT.md` says a Component Role is assigned only from
the **conjunction** of those views, and never from one of them. This module is
that conjunction, applied to a finished head table with no model, no GPU and no
nnsight, so it runs on the login node in a second.

The criteria are **pre-registered** in `docs/component-roles.md`, written and
committed before any role was assigned to any Component. This file implements
exactly those rules; where a threshold appears here it is the default the doc
states and the reason is in the doc, not in a comment here. The sign convention
the criteria read across analyses is ADR-0002: **positive supports the
deceptive answer**. Path patching has written that sign since 2026-10-13 and
is read natively; a cell written before holds the opposite sign under its old
names, and the derived `roles.direct_support` column negates it rather than
touching the original.

What comes out, per Component:

    roles.role_proposed    binder | selector | mover | suppressor | unknown
    roles.role_notes       one line: the flavour, the lean, and the numbers
    roles.direct_support   path_patching.direct_support, or on a cell
                           written before 2026-10-13 -path_patching.direct_effect
                           (ADR-0002)
    roles.direct_support_se
    roles.direct_support_honest_instruction_paired
    roles.reads_group      which group the top Segment falls in

and `roles/roles.json`, which records every threshold, every view's input and
every criterion's verdict, so a disputed label is settled by reading a file
rather than by rerunning the pass.

**`role_confirmed` is the researcher's column.** It is read if the table has
it, reported in the JSON beside the proposal, and never written — `merge_columns`
refuses to write it at all, which is the mechanism rather than the promise.

Usage:

    python analyze_components.py roles outputs/_analyses/<suite>/<circuit>/<task>
    python analyze_components.py roles <cell> --dry-run
    python analyze_components.py roles <cell> --roles-merge-from <other cell>

`--roles-merge-from` exists because the analyses of record were run one suite
per analysis: it copies another cell's analysis columns onto the matching rows
before the criteria run, so that one table carries all three views. Since
ticket 13 a cell is assembled by running every job into it, so new cells need
no merge.

A table written before the paired columns said `paired` in their names is read
under the current names (`head_table.modernize_columns`), both the cell's own
and every merged one, and the translation is recorded in `roles.json`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from component_analysis import path_patching
from component_analysis.head_table import BASE_COLUMNS, COVERAGE_KEY, \
    INSTANCE_SETS_KEY, JSON_NAME as TABLE_JSON, KEY_COLUMNS, PROTECTED_COLUMNS, \
    RENAMED_KEY, merge_columns, modernize_columns, modernize_meta, row_key, \
    write_head_table

NAME = "roles"
SUBDIR = "roles"
JSON_NAME = "roles.json"

#: Where the criteria live. Recorded in every file this pass writes, because a
#: role is only auditable against the criteria it was assigned under.
CRITERIA_DOC = os.path.join("docs", "component-roles.md")

#: The vocabulary. `unknown` is a role, not a failure.
ROLES = ("binder", "selector", "mover", "suppressor", "unknown")

#: Held so that nothing else takes the name. Finding pressure readers needs a
#: dataset variant this repo does not have yet (spec, Out of Scope), so the
#: pass notes the signature and assigns `unknown`.
RESERVED = ("pressure reader",)

#: The flavours of `unknown`, which the notes name apart. `knockout-only` is
#: the researcher's 2026-10-13 amendment: a Component whose only significant
#: view is knockout, held at `unknown` until there is reads evidence rather
#: than given a fifth role (docs/component-roles.md, "Changing these criteria").
DISAGREE = "disagree"
INSUFFICIENT = "insufficient"
KNOCKOUT_ONLY = "knockout-only"
FLAVOURS = (DISAGREE, KNOCKOUT_ONLY, INSUFFICIENT)

#: Segment name -> group, from CONTEXT.md's prompt anatomy. A name that is not
#: here is `unestablished`, which is also what an absent read is: a Segment the
#: vocabulary does not know about has not been shown to be anything, and a
#: `--segment` override (ticket 03's `bos`) arrives that way. `designation_site`
#: counts as designation rather than as an Item Mention, and `question` is a
#: frame because the Item Mentions inside it are carved into their own Segments.
SEGMENT_GROUPS: Dict[str, str] = {
    "designating_sentence": "designation",
    "designation_site": "designation",
    "predicate_token": "designation",
    "other_token": "designation",
    "inverse_predicate_token": "designation",
    "designation_suffix": "designation",
    "item_1_intro": "item_mention",
    "item_2_intro": "item_mention",
    "item_1_question_pair": "item_mention",
    "item_1_question_option": "item_mention",
    "item_2_question_pair": "item_mention",
    "item_2_question_option": "item_mention",
    "pressure_clause": "pressure",
    "intro": "frame",
    "question": "frame",
    "stem": "frame",
    "readout": "unestablished",
    "unsegmented": "unestablished",
}

#: The groups a read has to fall in to be established at all.
ESTABLISHED_GROUPS = ("designation", "item_mention", "pressure", "frame")

#: The columns the criteria read, by view. Named here, and checked against the
#: table by `require_columns`, so that a renamed column upstream fails loudly in
#: one place rather than turning every Component into an `unknown` that reads
#: like a finding.
TOP_SEGMENT = "attention_patterns.pressure_top_segment"
TOP_MASS = "attention_patterns.pressure_top_mass"
PAIRED_TOP_SEGMENT = "attention_patterns.pressure_paired_top_segment"
HONEST_TOP_SEGMENT = "attention_patterns.honest_instruction_paired_top_segment"
DLA = "dla.pressure"
DLA_SE = "dla.pressure_se"
DLA_DIFFERENTIAL = "dla.differential_paired"
DLA_DIFFERENTIAL_SE = "dla.differential_paired_se"
DLA_SUPPRESSION = "dla.suppression"
KNOCKOUT = "knockout.logit_diff_drop"
KNOCKOUT_SE = "knockout.standard_error"
#: The path-patching columns, in the sign every path-patching run writes since
#: 2026-10-13 (`path_patching.CONVENTION`: positive helps deception), read
#: natively. A cell written before carries the legacy columns below instead,
#: in the opposite sign, and those are negated (ADR-0002). The two generations
#: have different names, so a row says by its names which one it is.
DIRECT_SUPPORT = "path_patching.direct_support"
DIRECT_SUPPORT_SE = "path_patching.direct_support_se"
DIRECT_SUPPORT_HONEST = "path_patching.direct_support_honest_instruction_paired"
DIRECT_SUPPORT_HONEST_SE = \
    "path_patching.direct_support_honest_instruction_paired_se"
OUTGOING = "path_patching.strongest_outgoing"
OUTGOING_SUPPORT = "path_patching.strongest_outgoing_support"
INCOMING_HONEST = "path_patching.strongest_incoming_honest_instruction_paired"
INCOMING_HONEST_SUPPORT = \
    "path_patching.strongest_incoming_support_honest_instruction_paired"

#: The legacy-sign spellings (negative helps deception), under ticket 13's
#: paired names. Never translated into the columns above: a sign is meaning.
DIRECT_EFFECT = "path_patching.direct_effect"
DIRECT_EFFECT_SE = "path_patching.direct_effect_se"
DIRECT_EFFECT_HONEST = "path_patching.direct_effect_honest_instruction_paired"
DIRECT_EFFECT_HONEST_SE = \
    "path_patching.direct_effect_se_honest_instruction_paired"
OUTGOING_EFFECT = "path_patching.strongest_outgoing_effect"
INCOMING_HONEST_EFFECT = \
    "path_patching.strongest_incoming_effect_honest_instruction_paired"

#: Every number the criteria read from path patching, by the name the roles
#: pass gives it in the support convention: `(native column, legacy column)`.
#: The one table both generations are read through — `path_value` reads a row
#: through it, `derived_coverage` takes coverage through it, `conventions_of`
#: finds the generation through it. A legacy value is negated, except a
#: standard error (`_se`), which has no sign.
PATH_READS = {
    "direct_support": (DIRECT_SUPPORT, DIRECT_EFFECT),
    "direct_support_se": (DIRECT_SUPPORT_SE, DIRECT_EFFECT_SE),
    "direct_support_honest_instruction_paired": (DIRECT_SUPPORT_HONEST,
                                                 DIRECT_EFFECT_HONEST),
    "outgoing_support": (OUTGOING_SUPPORT, OUTGOING_EFFECT),
    "incoming_honest_instruction_support": (INCOMING_HONEST_SUPPORT,
                                            INCOMING_HONEST_EFFECT),
}

#: Which head-table column each counterfactual's path-patching JSON stands
#: behind, `(native, legacy)`: the file's convention marker must agree with
#: the generation of the column (`check_markers`).
MARKED_BY = {path_patching.ITEM_SWAP: PATH_READS["direct_support"],
             path_patching.HONEST_INSTRUCTION:
                 PATH_READS["direct_support_honest_instruction_paired"]}


class MixedConventions(ValueError):
    """Path-patching numbers of both sign conventions where one was expected:
    a row holding both generations' columns, or a column whose generation
    disagrees with its own JSON's convention marker."""


#: The human's column, read and never written. Looked up by name rather than by
#: position, because `head_table` documents `PROTECTED_COLUMNS` as extensible.
CONFIRMED = "role_confirmed"
assert CONFIRMED in PROTECTED_COLUMNS, (
    "head_table stopped protecting role_confirmed, which the roles pass relies "
    "on to keep the researcher's column out of an analysis's reach")

#: One column per view whose absence means that view was never computed. A
#: table missing all of one view's columns cannot support a conjunction, and
#: saying so beats proposing `unknown` for every Component.
REQUIRED_COLUMNS = {
    "reads (attention_patterns)": (TOP_SEGMENT, TOP_MASS),
    "writes (dla)": (DLA, DLA_SE),
    "depends, whether (knockout)": (KNOCKOUT, KNOCKOUT_SE),
    "depends, how (path_patching)": (DIRECT_SUPPORT, DIRECT_SUPPORT_SE,
                                     DIRECT_EFFECT, DIRECT_EFFECT_SE, OUTGOING),
}

#: What the head table gains, before the CLI adds the `roles` namespace.
COLUMNS = ("role_proposed", "role_notes", "direct_support", "direct_support_se",
           "direct_support_honest_instruction_paired", "reads_group")

#: The `COLUMNS` read from path patching through `PATH_READS`; each covers
#: exactly the instances its source column does, so it takes its coverage.
DERIVED = ("direct_support", "direct_support_se",
           "direct_support_honest_instruction_paired")

@dataclass
class Thresholds:
    """Every number a criterion compares against. The doc says why each is what it is."""

    z: float = 2.0
    dla_floor: float = 0.01
    knockout_floor: float = 0.01
    path_floor: float = 0.01
    attention_floor: float = 0.20

    def as_dict(self) -> dict:
        return {"z": self.z, "dla_floor": self.dla_floor,
                "knockout_floor": self.knockout_floor,
                "path_floor": self.path_floor,
                "attention_floor": self.attention_floor}


# ==============================================================================
# READING ONE ROW
# ==============================================================================

def _number(row, column) -> Optional[float]:
    """A column as a float, or None. CSV-read rows carry strings; JSON rows do not."""
    value = row.get(column)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _flag(value) -> bool:
    """A boolean column, however it was written.

    The JSON twin keeps booleans as booleans, but the CSV view writes them as
    0 and 1 and a hand-edited table may hold "false". `bool("0")` is True, and
    the suppressor clause is checked first, so an unnormalized read of
    `dla.suppression` would make every Component a suppressor candidate.
    """
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes")
    return bool(value)


def direction(value, se, floor, thresholds: Thresholds) -> int:
    """+1, -1 or 0: the sign of a number that clears both the z bar and its floor.

    Both bars, because they catch different things. Without the z test a large
    number measured over nothing counts; without the floor a path-patching cell
    four standard errors from zero at 0.0005 counts, which is noise measured
    precisely. A missing standard error is not a small one: it fails, and so
    does a standard error of exactly zero — a spread of zero over a sample is
    a spread that was not measured (one instance, or a column written by
    something that does not compute one), not a measurement of perfect
    agreement.
    """
    if value is None or abs(value) < floor:
        return 0
    if not se or se <= 0:
        return 0
    if abs(value) / se < thresholds.z:
        return 0
    return 1 if value > 0 else -1


def segment_group(segment) -> str:
    """Which group a Segment name falls in; an unknown name is unestablished."""
    if not segment:
        return "unestablished"
    return SEGMENT_GROUPS.get(str(segment), "unestablished")


def path_value(row, name: str) -> Optional[float]:
    """One path-patching number of `PATH_READS`, in the support convention.

    The native column is read as it is; the legacy column is negated
    (ADR-0002), except a standard error, which is copied. Absent rather than
    zero when neither is there. A row holding both generations is refused:
    that is two path-patching runs of opposite sign merged into one table
    (`--roles-merge-from` a legacy cell into a new one), which the merge's own
    conflict check cannot see because the names differ, and reading either
    would silently drop the other measurement.
    """
    native, legacy = PATH_READS[name]
    new, old = _number(row, native), _number(row, legacy)
    if new is not None and old is not None:
        raise MixedConventions(
            f"{row_key(row)} carries both {legacy} (written before path "
            f"patching's sign flipped on 2026-10-13, negative helps deception) "
            f"and {native} (positive helps deception). They are two runs, not "
            f"one; drop one of the cells this table was merged from.")
    if new is not None:
        return new
    if old is None or name.endswith("_se"):
        return old
    return -old


def generations_of(rows) -> List[str]:
    """The path-patching sign conventions a table's rows hold, as
    `path_patching`'s own markers, current first: `[CONVENTION]`,
    `[LEGACY_CONVENTION]`, both (across rows), or none."""
    present = {column for one in rows for column, value in one.items()
               if value is not None and value != ""}
    found = []
    for marker, side in ((path_patching.CONVENTION, 0),
                         (path_patching.LEGACY_CONVENTION, 1)):
        if any(pair[side] in present for pair in PATH_READS.values()):
            found.append(marker)
    return found


def check_markers(rows, cell_dir: str) -> None:
    """The cell's path-patching JSONs must say the sign its columns are in.

    The roles pass tells the generations apart by column name, because a
    name travels with its values through every merge and a CSV has no meta.
    Where the JSON a column came from is in the cell, its `metric.convention`
    marker is the second witness: a disagreement means the table or the file
    was edited, or the cell was assembled from two runs, and neither reading
    is safe.
    """
    for counterfactual, (native, legacy) in MARKED_BY.items():
        path = os.path.join(cell_dir, path_patching.SUBDIR,
                            path_patching.output_name(
                                path_patching.AGNOSTIC_STEM, counterfactual,
                                "json"))
        if not os.path.isfile(path):
            continue
        has_native = any(_number(one, native) is not None for one in rows)
        has_legacy = any(_number(one, legacy) is not None for one in rows)
        if not (has_native or has_legacy):
            continue
        with open(path) as handle:
            marker = path_patching.convention_of(json.load(handle).get("metric"))
        columns = (path_patching.CONVENTION if has_native
                   else path_patching.LEGACY_CONVENTION)
        if marker != columns or (has_native and has_legacy):
            raise MixedConventions(
                f"{path} says {marker}, but the head table's "
                f"{native if has_native else legacy} column is in "
                f"{columns}. The column and the file it came from disagree "
                f"about the sign; rerun path patching into this cell, or "
                f"restore the file the table was written with.")


def derived_columns(row) -> dict:
    """ADR-0002's support convention, read from either generation.

    A path-patching run since 2026-10-13 writes `path_patching.direct_support`
    with positive helping deception, and it is copied as it is. A cell written
    before holds `path_patching.direct_effect` in the opposite sign, and it is
    negated, as it always was; the original column keeps its meaning in every
    file already written. A standard error has no sign and is copied.
    """
    return {name: path_value(row, name) for name in DERIVED}


def receiver_of(path) -> Optional[str]:
    """`head.14.22->q.17.25` to `q.17.25`; a path with no arrow has no receiver."""
    if not path or "->" not in str(path):
        return None
    return str(path).split("->", 1)[1].strip()


def is_query_receiver_on(path, key) -> bool:
    """Does this path land on *this* Component's query input?

    Q is per head, so `q.<layer>.<index>` names one Component. K and V are per
    KV group and reach every query head of that group, so they are never read
    as a claim about one head (ticket 08's coverage note, and the reason the
    selector criterion names Q alone).
    """
    receiver = receiver_of(path)
    if not receiver or not receiver.startswith("q."):
        return False
    parts = receiver.split(".")
    if len(parts) != 3:
        return False
    try:
        return (key[0] == "head" and int(parts[1]) == key[1]
                and int(parts[2]) == key[2])
    except ValueError:
        return False


def is_readout_receiver(path) -> bool:
    return receiver_of(path) == "readout"


def views_of(row, thresholds: Thresholds) -> dict:
    """The three views, as the criteria see them: value, error, verdict."""
    key = row_key(row)
    is_head = key[0] == "head"
    segment = row.get(TOP_SEGMENT)
    mass = _number(row, TOP_MASS)
    group = segment_group(segment) if is_head else "not_applicable"
    if is_head and group in ESTABLISHED_GROUPS and (
            mass is None or mass < thresholds.attention_floor):
        group = "unestablished"

    dla = _number(row, DLA)
    differential = _number(row, DLA_DIFFERENTIAL)
    knockout = _number(row, KNOCKOUT)
    derived = derived_columns(row)
    support = derived["direct_support"]
    outgoing_support = path_value(row, "outgoing_support")
    incoming_support = path_value(row, "incoming_honest_instruction_support")

    return {
        "reads": {
            "segment": segment, "mass": mass, "group": group,
            "established": group in ESTABLISHED_GROUPS,
            "not_applicable": not is_head,
            "paired_segment": row.get(PAIRED_TOP_SEGMENT),
            "honest_instruction_segment": row.get(HONEST_TOP_SEGMENT),
        },
        "writes": {
            "value": dla, "se": _number(row, DLA_SE),
            "sign": direction(dla, _number(row, DLA_SE), thresholds.dla_floor,
                              thresholds),
            "differential": differential,
            "differential_se": _number(row, DLA_DIFFERENTIAL_SE),
            "differential_sign": direction(
                differential, _number(row, DLA_DIFFERENTIAL_SE),
                thresholds.dla_floor, thresholds),
            "suppression": _flag(row.get(DLA_SUPPRESSION)),
        },
        "depends": {
            "knockout": knockout, "knockout_se": _number(row, KNOCKOUT_SE),
            "knockout_sign": direction(knockout, _number(row, KNOCKOUT_SE),
                                       thresholds.knockout_floor, thresholds),
            "direct_support": support,
            "direct_support_se": derived["direct_support_se"],
            "direct_support_sign": direction(support, derived["direct_support_se"],
                                             thresholds.path_floor, thresholds),
            "outgoing": row.get(OUTGOING),
            "outgoing_support": outgoing_support,
            "outgoing_clears_floor": (outgoing_support is not None
                                      and abs(outgoing_support) >= thresholds.path_floor),
            "outgoing_is_readout": is_readout_receiver(row.get(OUTGOING)),
            "incoming_honest_instruction": row.get(INCOMING_HONEST),
            "incoming_honest_instruction_support": incoming_support,
            "honest_instruction_at_own_query": (
                is_query_receiver_on(row.get(INCOMING_HONEST), key)
                and incoming_support is not None
                and abs(incoming_support) >= thresholds.path_floor),
        },
    }


def scored(views: dict) -> bool:
    """Did any analysis score this Component at all?"""
    reads, writes, depends = views["reads"], views["writes"], views["depends"]
    return any([reads["segment"] is not None, writes["value"] is not None,
                depends["knockout"] is not None,
                depends["direct_support"] is not None,
                depends["outgoing"] is not None])


# ==============================================================================
# THE CRITERIA
# ==============================================================================

def support_signs(views: dict) -> List[int]:
    """The three numbers that speak to "does this Component support deception"."""
    return [views["writes"]["sign"], views["depends"]["knockout_sign"],
            views["depends"]["direct_support_sign"]]


def criteria_of(views: dict) -> Dict[str, Dict[str, bool]]:
    """Every role's clauses, evaluated. The doc's rules 2 to 5, one dict each."""
    reads, writes, depends = views["reads"], views["writes"], views["depends"]
    established = reads["established"] or reads["not_applicable"]

    return {
        "suppressor": {
            "writes": writes["sign"] < 0 or writes["suppression"],
            "depends": depends["knockout_sign"] < 0
            or depends["direct_support_sign"] < 0,
        },
        "binder": {
            "reads": reads["group"] == "designation",
            "writes": writes["sign"] == 0,
            "depends": (depends["direct_support_sign"] == 0
                        and depends["outgoing_clears_floor"]
                        and not depends["outgoing_is_readout"]),
        },
        "selector": {
            "reads": established,
            "writes": writes["sign"] != 0 and writes["differential_sign"] != 0,
            "depends": (depends["knockout_sign"] > 0
                        or depends["direct_support_sign"] > 0),
            "query": depends["honest_instruction_at_own_query"],
        },
        "mover": {
            "reads": reads["group"] == "item_mention" or reads["not_applicable"],
            "writes": writes["sign"] > 0,
            "depends": (depends["direct_support_sign"] > 0
                        and depends["outgoing_is_readout"]),
        },
    }


#: The order the doc checks the roles in; the first whose clauses all hold wins.
CHECK_ORDER = ("suppressor", "binder", "selector", "mover")


def lean_of(criteria: Dict[str, Dict[str, bool]]) -> Optional[str]:
    """Which role the established views point at, when none is assignable.

    The share of clauses satisfied, not their count, so that `selector`'s four
    clauses do not beat `mover`'s three on arithmetic alone. Ties, and anything
    under half, lean nowhere.
    """
    best, score = None, 0.5
    for role in CHECK_ORDER:
        clauses = criteria[role]
        share = sum(1 for one in clauses.values() if one) / len(clauses)
        if share > score:
            best, score = role, share
        elif share == score and best is not None:
            best = None
    return best


def knockout_only(views: dict) -> bool:
    """Is knockout the only view that speaks? The `unknown/knockout-only` test.

    Knockout significant and above its floor, in either direction; no
    established read (an MLP block has none to establish); nothing written at
    the Readout, pressure-dependent or not; no direct path, no onward path and
    no honest-instruction path at its own query above the path floor.

    "Nothing written" and "no path" are claims about views that were
    measured: a table missing DLA or path patching (allowed with
    `--roles-allow-missing-views`) leaves those views unmeasured, not silent,
    and the Component is `unknown/insufficient`. An unmeasured read is no
    reads evidence, which is the flavour's premise, so it does not block.
    """
    reads, writes, depends = views["reads"], views["writes"], views["depends"]
    return (not unmeasured_views(views) and depends["knockout_sign"] != 0
            and not reads["established"]
            and writes["sign"] == 0 and writes["differential_sign"] == 0
            and not writes["suppression"]
            and depends["direct_support_sign"] == 0
            and not depends["outgoing_clears_floor"]
            and not depends["honest_instruction_at_own_query"])


def pressure_reader_signature(views: dict) -> bool:
    """Reads the Pressure Clause under pressure, and stops under the instruction.

    Noted, never assigned: the reserved role needs a dataset variant with an
    honest-instruction Corruption, which is out of scope (spec, Out of Scope).
    """
    reads = views["reads"]
    honest = reads["honest_instruction_segment"]
    return (reads["paired_segment"] == "pressure_clause"
            and honest is not None and honest != "pressure_clause")


@dataclass
class Decision:
    """One Component's proposal, and everything it was made from."""

    key: tuple
    role: str
    flavour: Optional[str]
    notes: str
    reads_group: str
    views: dict
    criteria: Dict[str, Dict[str, bool]]
    confirmed: Optional[str] = None
    derived: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"key": list(self.key), "role": self.role,
                "flavour": self.flavour, "notes": self.notes,
                "reads_group": self.reads_group,
                CONFIRMED: self.confirmed,
                "views": self.views, "criteria": self.criteria}

    def columns(self) -> dict:
        return {"role_proposed": self.role, "role_notes": self.notes,
                "reads_group": self.reads_group, **self.derived}


def propose(row, thresholds: Thresholds = None) -> Decision:
    """The role `docs/component-roles.md` assigns this row, and why."""
    thresholds = thresholds or Thresholds()
    key = row_key(row)
    views = views_of(row, thresholds)
    criteria = criteria_of(views)
    derived = derived_columns(row)
    confirmed = row.get(CONFIRMED)

    def decide(role, flavour, notes):
        if pressure_reader_signature(views):
            notes += ("; pressure-reader signature (reads the Pressure Clause "
                      "under pressure and leaves it under the instruction), "
                      "which is a reserved role and is never assigned")
        return Decision(key=key, role=role, flavour=flavour, notes=notes,
                        reads_group=views["reads"]["group"], views=views,
                        criteria=criteria, confirmed=confirmed, derived=derived)

    if not scored(views):
        return decide("unknown", INSUFFICIENT,
                      "unknown/insufficient: no analysis scored this Component")

    signs = [one for one in support_signs(views) if one != 0]
    if 1 in signs and -1 in signs:
        return decide("unknown", DISAGREE,
                      f"unknown/disagree: {_evidence(views)}")

    for role in CHECK_ORDER:
        if all(criteria[role].values()):
            return decide(role, None, f"{role}: {_evidence(views)}")

    if knockout_only(views):
        way = ("supports deception" if views["depends"]["knockout_sign"] > 0
               else "opposes deception")
        return decide("unknown", KNOCKOUT_ONLY,
                      f"unknown/knockout-only: knockout {way} and no other view "
                      f"speaks, held until there is reads evidence; "
                      + _evidence(views))

    lean = lean_of(criteria)
    missing = _missing(criteria, lean) if lean else None
    notes = "unknown/insufficient: "
    notes += f"{lean} lean, {missing} not met; " if lean else ""
    unmeasured = unmeasured_views(views)
    if unmeasured:
        notes += f"not measured: {', '.join(unmeasured)}; "
    return decide("unknown", INSUFFICIENT, notes + _evidence(views))


def unmeasured_views(views: dict) -> List[str]:
    """The DLA and path-patching views with no value on this row.

    Named in the notes so a Component held at `unknown/insufficient` because a
    view was never measured (a table proposed with `--roles-allow-missing-views`)
    is not read as one whose views were measured and silent.
    """
    out = []
    if views["writes"]["value"] is None:
        out.append("writes (dla)")
    if views["depends"]["direct_support"] is None \
            or views["depends"]["outgoing_support"] is None:
        out.append("depends, how (path_patching)")
    return out


def _missing(criteria, role) -> str:
    return ", ".join(name for name, held in criteria[role].items() if not held)


def _number_note(value, se) -> str:
    if value is None:
        return "none"
    if se:
        return f"{value:+.4f} (z={abs(value) / se:.1f})"
    return f"{value:+.4f}"


def _evidence(views: dict) -> str:
    """The one line a researcher reads instead of four columns."""
    reads, writes, depends = views["reads"], views["writes"], views["depends"]
    if reads["not_applicable"]:
        read = "reads n/a (MLP block)"
    elif reads["segment"] is None:
        read = "reads unmeasured"
    else:
        read = ("reads " + str(reads["segment"])
                + ("" if reads["mass"] is None else f" ({reads['mass']:.2f})")
                + ("" if reads["established"] else ", unestablished"))
    return "; ".join([
        read,
        f"writes {_number_note(writes['value'], writes['se'])}",
        f"differential {_number_note(writes['differential'], writes['differential_se'])}",
        f"knockout {_number_note(depends['knockout'], depends['knockout_se'])}",
        f"direct support {_number_note(depends['direct_support'], depends['direct_support_se'])}",
        f"strongest outgoing {depends['outgoing'] or 'none'}",
        f"honest instruction in {depends['incoming_honest_instruction'] or 'none'}",
    ])


def decide_rows(rows, thresholds: Thresholds = None) -> List[Decision]:
    thresholds = thresholds or Thresholds()
    return [propose(row, thresholds) for row in rows]


def columns(decisions: List[Decision]) -> dict:
    """The head-table update; the CLI namespaces it under `roles`."""
    return {one.key: one.columns() for one in decisions}


def _label(provenance) -> Optional[str]:
    """A circuit's or task's label out of the head table's provenance block."""
    if isinstance(provenance, dict):
        return provenance.get("label") or provenance.get("name")
    return None if provenance is None else str(provenance)


def counts(decisions: List[Decision]) -> dict:
    out = {role: 0 for role in ROLES}
    for one in decisions:
        out[one.role] = out.get(one.role, 0) + 1
    return out


def flavour_counts(decisions: List[Decision]) -> dict:
    """How many `unknown`s of each flavour, the ones that occurred only."""
    out: Dict[str, int] = {}
    for one in decisions:
        if one.flavour:
            out[one.flavour] = out.get(one.flavour, 0) + 1
    return out


def sign_convention(markers) -> str:
    """The roles JSON's sentence on how path patching was read in this table.

    For a human; a reader tests `path_conventions`, the markers themselves.
    """
    ways = []
    if path_patching.CONVENTION in markers:
        ways.append("roles.direct_support is path_patching.direct_support "
                    "read natively (a path-patching run since 2026-10-13, "
                    "positive helps deception)")
    if path_patching.LEGACY_CONVENTION in markers:
        ways.append("roles.direct_support is -path_patching.direct_effect, "
                    "negating a legacy cell written before 2026-10-13")
    if not ways:
        ways.append("no path-patching column was present")
    return ("positive supports the deceptive answer (ADR-0002); knockout and "
            "dla are read natively; " + "; ".join(ways))


def payload(decisions: List[Decision], *, cell_dir: str, thresholds: Thresholds,
            merged_from: List[str], meta: dict = None,
            missing_views: List[str] = None, renamed: dict = None,
            conventions: List[str] = ()) -> dict:
    return {
        "analysis": NAME,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "criteria_doc": CRITERIA_DOC,
        "sign_convention": sign_convention(conventions),
        #: `path_patching.CONVENTION` and/or `LEGACY_CONVENTION`: the sign
        #: conventions of the path-patching columns this table was read from.
        "path_conventions": list(conventions),
        "vocabulary": list(ROLES),
        "reserved": list(RESERVED),
        "thresholds": thresholds.as_dict(),
        "cell": cell_dir,
        "merged_from": list(merged_from),
        #: Views whose columns were absent from the table. Non-empty only with
        #: --roles-allow-missing-views, and every role here is worth less.
        "missing_views": list(missing_views or []),
        # Label strings, as every sibling analysis JSON writes them: the head
        # table's meta holds the full provenance dicts, and a notebook reading
        # "circuit" across the analyses must not meet two types.
        "circuit": _label((meta or {}).get("circuit")),
        "task": _label((meta or {}).get("task")),
        "counts": counts(decisions),
        "flavour_counts": flavour_counts(decisions),
        #: Legacy column names translated on the way in, old -> current.
        RENAMED_KEY: dict(renamed or {}),
        "n_components": len(decisions),
        "components": [one.as_dict() for one in decisions],
    }


# ==============================================================================
# THE SUBCOMMAND
# ==============================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="analyze_components.py roles",
        description="Apply the pre-registered Component Role criteria "
                    f"({CRITERIA_DOC}) to a finished head table.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("cell_dir", help="The cell directory holding head_table.json.")
    p.add_argument("--roles-merge-from", action="append", default=[],
                   metavar="CELL_DIR",
                   help="Merge another cell's analysis columns onto the "
                        "matching rows before the criteria run. Repeatable. "
                        "The analyses of record were run one suite per "
                        "analysis, so this is how one table gets all three "
                        "views. Key columns and role_confirmed are never "
                        "copied.")
    p.add_argument("--roles-z", type=float, default=Thresholds.z,
                   help="How many standard errors a number needs to count.")
    p.add_argument("--roles-dla-floor", type=float, default=Thresholds.dla_floor,
                   help="Smallest |DLA| in logits that counts as writing.")
    p.add_argument("--roles-knockout-floor", type=float,
                   default=Thresholds.knockout_floor,
                   help="Smallest |knockout drop| in logits that counts.")
    p.add_argument("--roles-path-floor", type=float, default=Thresholds.path_floor,
                   help="Smallest |path-patching effect| that counts, as a "
                        "fraction of the clean-minus-corrupt gap.")
    p.add_argument("--roles-attention-floor", type=float,
                   default=Thresholds.attention_floor,
                   help="Smallest top-Segment mass that establishes a read.")
    p.add_argument("--roles-allow-missing-views", action="store_true",
                   help="Propose even when a whole view's columns are absent "
                        "from the table. Off by default, because a table with "
                        "no DLA columns proposes `unknown` for every Component "
                        "and that reads like a finding. The views that were "
                        "missing are recorded in roles.json.")
    p.add_argument("--dry-run", action="store_true",
                   help="Propose and print; write nothing.")
    return p


def thresholds_from(cli) -> Thresholds:
    return Thresholds(z=cli.roles_z, dla_floor=cli.roles_dla_floor,
                      knockout_floor=cli.roles_knockout_floor,
                      path_floor=cli.roles_path_floor,
                      attention_floor=cli.roles_attention_floor)


def require_columns(rows, *, cell_dir: str, merged_from=(), allow=False) -> list:
    """Refuse a table that is missing a whole view, naming the columns.

    Not a refusal of *null cells* — an MLP block legitimately has no attention
    columns, and a Component an analysis skipped legitimately has nulls. This
    refuses a table where the column does not exist at all, which is what a
    renamed column upstream and a forgotten `--roles-merge-from` both look
    like, and which would otherwise come out as a full table of `unknown`.
    """
    present = {column for row in rows for column in row}
    missing = {view: [c for c in columns if c not in present]
               for view, columns in REQUIRED_COLUMNS.items()}
    absent = {view: columns for view, columns in missing.items()
              if len(columns) == len(REQUIRED_COLUMNS[view])}
    if not absent:
        return []
    merged = (f" (merged from {', '.join(merged_from)})" if merged_from
              else " (nothing was merged in)")
    complaint = (
        f"{cell_dir!r}{merged} has no column at all for: "
        + "; ".join(f"{view} — {', '.join(columns)}"
                    for view, columns in absent.items())
        + ". A Component Role is a conjunction of all three views, so a table "
          "missing one of them can only propose `unknown`.")
    if not allow:
        raise SystemExit(complaint + " Run the missing analyses, or merge the "
                         "cell that has them with --roles-merge-from, or pass "
                         "--roles-allow-missing-views to propose anyway.")
    print(f"  !! {complaint} Proposing anyway, because "
          f"--roles-allow-missing-views was given.")
    return sorted(absent)


def read_table(cell_dir: str) -> tuple:
    """`(rows, meta, renamed)` of a written head table, under the current names.

    `renamed` is the legacy translation applied, old -> current, so a cell of
    record written before the paired names reads like any other. A missing
    table is refused by name.
    """
    path = os.path.join(cell_dir, TABLE_JSON)
    if not os.path.exists(path):
        raise SystemExit(f"no {TABLE_JSON} in {cell_dir!r}: the roles pass "
                         f"reads a finished head table, so run the analyses "
                         f"into this cell first (or point --roles-merge-from "
                         f"at the cells that have them).")
    with open(path) as handle:
        table = json.load(handle)
    rows, renamed = modernize_columns(table["rows"])
    return rows, modernize_meta(table.get("meta")), renamed


#: Never copied by `--roles-merge-from`: the key identifies the row, the intake
#: columns are the same on both sides, and `role_confirmed` is the human's.
NOT_MERGED = set(KEY_COLUMNS) | set(BASE_COLUMNS) | set(PROTECTED_COLUMNS)


def merge_cells(rows, cell_dirs, *, meta: dict = None) -> tuple:
    """`(rows, meta, renamed)`: other cells' analysis columns, onto these rows.

    A column that already holds a different value is refused by name rather
    than overwritten: two cells that both ran path patching would otherwise
    have the last one on the command line win silently, and a role assigned
    from columns whose provenance is "whichever cell came last" is not
    auditable. Merging a cell that agrees, or that only fills blanks, is fine.
    Each merged cell is read under the current column names first, so the same
    column under its legacy spelling is compared as itself. Its coverage
    comes with its columns, without replacing coverage already held.
    """
    meta = dict(meta or {})
    renamed_all: Dict[str, str] = {}
    seen = {row_key(one): dict(one) for one in rows}
    for cell_dir in cell_dirs:
        other, other_meta, renamed = read_table(cell_dir)
        renamed_all.update(renamed)
        coverage = dict(meta.get(COVERAGE_KEY) or {})
        for column, entry in (other_meta.get(COVERAGE_KEY) or {}).items():
            coverage.setdefault(column, entry)
        meta[COVERAGE_KEY] = coverage
        meta[INSTANCE_SETS_KEY] = {**(other_meta.get(INSTANCE_SETS_KEY) or {}),
                                   **(meta.get(INSTANCE_SETS_KEY) or {})}
        updates = {}
        for one in other:
            key = row_key(one)
            values = {column: value for column, value in one.items()
                      if column not in NOT_MERGED and value is not None}
            for column, value in values.items():
                held = seen.get(key, {}).get(column)
                if held is not None and held != value:
                    raise SystemExit(
                        f"--roles-merge-from {cell_dir!r} would overwrite "
                        f"{column!r} on {key}: it already holds {held!r} and "
                        f"the merged cell says {value!r}. Merge cells that ran "
                        f"different analyses, or drop one of them.")
            if values:
                updates[key] = values
                seen.setdefault(key, {}).update(values)
        rows = merge_columns(rows, updates)
    return rows, meta, renamed_all


def derived_coverage(meta: dict) -> dict:
    """The meta with each derived column given its source column's coverage."""
    meta = dict(meta or {})
    coverage = dict(meta.get(COVERAGE_KEY) or {})
    for column in DERIVED:
        for source in PATH_READS[column]:
            if source in coverage:
                coverage[f"{NAME}.{column}"] = dict(coverage[source])
                break
    if coverage:
        meta[COVERAGE_KEY] = coverage
    return meta


def print_decisions(decisions: List[Decision]) -> None:
    for one in decisions:
        kind, layer, index = one.key
        label = f"L{layer} MLP" if kind == "mlp" else f"L{layer} H{index}"
        confirmed = f" [confirmed: {one.confirmed}]" if one.confirmed else ""
        print(f"  {label:>10}  {one.role:<11}{confirmed}")
        print(f"              {one.notes}")
    tally = counts(decisions)
    print("\n  " + ", ".join(f"{role}: {tally[role]}" for role in ROLES))


def main(argv=None) -> int:
    cli = build_parser().parse_args(argv)
    thresholds = thresholds_from(cli)
    rows, meta, renamed = read_table(cli.cell_dir)
    try:
        # Each cell's columns against its own JSONs, before the merge mixes
        # the cells' rows together.
        check_markers(rows, cli.cell_dir)
        for other in cli.roles_merge_from:
            check_markers(read_table(other)[0], other)
    except MixedConventions as error:
        raise SystemExit(str(error))
    rows, meta, merged_renamed = merge_cells(rows, cli.roles_merge_from,
                                             meta=meta)
    renamed = {**renamed, **merged_renamed}
    print(f"\nROLES — {cli.cell_dir}")
    print(f"  criteria: {CRITERIA_DOC} (pre-registered)")
    print(f"  thresholds: {thresholds.as_dict()}")
    if renamed:
        print("  legacy column names read under their current names: "
              + ", ".join(f"{old} -> {new}" for old, new in renamed.items()))
    print()
    missing_views = require_columns(
        rows, cell_dir=cli.cell_dir, merged_from=cli.roles_merge_from,
        allow=cli.roles_allow_missing_views)

    try:
        decisions = decide_rows(rows, thresholds)
    except MixedConventions as error:
        raise SystemExit(f"{cli.cell_dir!r}: {error}")
    conventions = generations_of(rows)
    print_decisions(decisions)

    if cli.dry_run:
        print("\n  --dry-run: nothing written.")
        return 0

    rows = merge_columns(rows, columns(decisions), namespace=NAME)
    meta = modernize_meta(derived_coverage(meta), renamed)
    meta["roles"] = {"criteria_doc": CRITERIA_DOC,
                     "thresholds": thresholds.as_dict(),
                     "merged_from": list(cli.roles_merge_from),
                     "counts": counts(decisions),
                     "flavour_counts": flavour_counts(decisions)}
    written = write_head_table(cli.cell_dir, rows, meta=meta)

    out = os.path.join(cli.cell_dir, SUBDIR)
    os.makedirs(out, exist_ok=True)
    json_path = os.path.join(out, JSON_NAME)
    with open(json_path, "w") as handle:
        json.dump(payload(decisions, cell_dir=cli.cell_dir,
                          thresholds=thresholds,
                          merged_from=cli.roles_merge_from, meta=meta,
                          missing_views=missing_views, renamed=renamed,
                          conventions=conventions),
                  handle, indent=2, default=str)

    print(f"\n  {written['csv']}\n  {written['json']}\n  {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
