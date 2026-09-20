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
deceptive answer**, with `path_patching`'s opposite sign carried by the derived
`roles.direct_support` column rather than by touching the original.

What comes out, per Component:

    roles.role_proposed    binder | selector | mover | suppressor | unknown
    roles.role_notes       one line: the flavour, the lean, and the numbers
    roles.direct_support   -path_patching.direct_effect  (ADR-0002)
    roles.direct_support_se
    roles.direct_support_honest_instruction
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
before the criteria run, so that one table carries all three views.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from component_analysis.head_table import BASE_COLUMNS, JSON_NAME as TABLE_JSON, \
    KEY_COLUMNS, PROTECTED_COLUMNS, load_head_table, merge_columns, row_key, \
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

#: The two flavours of `unknown`, which the notes name apart.
DISAGREE = "disagree"
INSUFFICIENT = "insufficient"

#: Segment name -> group, from CONTEXT.md's prompt anatomy. A name that is not
#: here falls in `other`, which is unestablished: `designation_site` counts as
#: designation rather than as an Item Mention, and `question` is a frame
#: because the Item Mentions inside it are carved out into their own Segments.
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

#: The columns the criteria read, by view. Named here so that a renamed column
#: upstream fails loudly in one place rather than silently reading nulls.
TOP_SEGMENT = "attention_patterns.pressure_top_segment"
TOP_MASS = "attention_patterns.pressure_top_mass"
PAIRED_TOP_SEGMENT = "attention_patterns.pressure_paired_top_segment"
HONEST_TOP_SEGMENT = "attention_patterns.honest_instruction_top_segment"
DLA = "dla.pressure"
DLA_SE = "dla.pressure_se"
DLA_DIFFERENTIAL = "dla.differential"
DLA_DIFFERENTIAL_SE = "dla.differential_se"
DLA_SUPPRESSION = "dla.suppression"
KNOCKOUT = "knockout.logit_diff_drop"
KNOCKOUT_SE = "knockout.standard_error"
DIRECT_EFFECT = "path_patching.direct_effect"
DIRECT_EFFECT_SE = "path_patching.direct_effect_se"
DIRECT_EFFECT_HONEST = "path_patching.direct_effect_honest_instruction"
OUTGOING = "path_patching.strongest_outgoing"
OUTGOING_EFFECT = "path_patching.strongest_outgoing_effect"
INCOMING_HONEST = "path_patching.strongest_incoming_honest_instruction"
INCOMING_HONEST_EFFECT = \
    "path_patching.strongest_incoming_effect_honest_instruction"

#: The human's column, read and never written.
CONFIRMED = PROTECTED_COLUMNS[0]

#: What the head table gains, before the CLI adds the `roles` namespace.
COLUMNS = ("role_proposed", "role_notes", "direct_support", "direct_support_se",
           "direct_support_honest_instruction", "reads_group")


@dataclass
class Thresholds:
    """Every number a criterion compares against. The doc says why each is what it is."""

    z: float = 2.0
    dla_floor: float = 0.01
    knockout_floor: float = 0.01
    path_floor: float = 0.005
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


def direction(value, se, floor, thresholds: Thresholds) -> int:
    """+1, -1 or 0: the sign of a number that clears both the z bar and its floor.

    Both bars, because they catch different things. Without the z test a large
    number measured over nothing counts; without the floor a path-patching cell
    four standard errors from zero at 0.0005 counts, which is noise measured
    precisely. A missing standard error is not a small one: it fails.
    """
    if value is None or abs(value) < floor:
        return 0
    if se is None:
        return 0
    if se > 0 and abs(value) / se < thresholds.z:
        return 0
    return 1 if value > 0 else -1


def segment_group(segment) -> str:
    """Which group a Segment name falls in; an unknown name is unestablished."""
    if not segment:
        return "unestablished"
    return SEGMENT_GROUPS.get(str(segment), "unestablished")


def derived_columns(row) -> dict:
    """ADR-0002's sign flip, as new columns rather than a rewrite.

    `path_patching` is negative where knockout and DLA are positive, so the
    criteria read a derived negation and the original column keeps its meaning
    in every file already written. A standard error has no sign and is copied.
    """
    direct = _number(row, DIRECT_EFFECT)
    honest = _number(row, DIRECT_EFFECT_HONEST)
    return {
        "direct_support": None if direct is None else -direct,
        "direct_support_se": _number(row, DIRECT_EFFECT_SE),
        "direct_support_honest_instruction": None if honest is None else -honest,
    }


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
    outgoing_effect = _number(row, OUTGOING_EFFECT)
    incoming_effect = _number(row, INCOMING_HONEST_EFFECT)

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
            "suppression": bool(row.get(DLA_SUPPRESSION)),
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
            "outgoing_effect": outgoing_effect,
            "outgoing_clears_floor": (outgoing_effect is not None
                                      and abs(outgoing_effect) >= thresholds.path_floor),
            "outgoing_is_readout": is_readout_receiver(row.get(OUTGOING)),
            "incoming_honest_instruction": row.get(INCOMING_HONEST),
            "incoming_honest_instruction_effect": incoming_effect,
            "honest_instruction_at_own_query": (
                is_query_receiver_on(row.get(INCOMING_HONEST), key)
                and incoming_effect is not None
                and abs(incoming_effect) >= thresholds.path_floor),
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

    lean = lean_of(criteria)
    missing = _missing(criteria, lean) if lean else None
    notes = "unknown/insufficient: "
    notes += f"{lean} lean, {missing} not met; " if lean else ""
    return decide("unknown", INSUFFICIENT, notes + _evidence(views))


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


def counts(decisions: List[Decision]) -> dict:
    out = {role: 0 for role in ROLES}
    for one in decisions:
        out[one.role] = out.get(one.role, 0) + 1
    return out


def payload(decisions: List[Decision], *, cell_dir: str, thresholds: Thresholds,
            merged_from: List[str], meta: dict = None) -> dict:
    return {
        "analysis": NAME,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "criteria_doc": CRITERIA_DOC,
        "sign_convention": (
            "positive supports the deceptive answer (ADR-0002); "
            "knockout and dla are read natively and roles.direct_support is "
            "-path_patching.direct_effect"),
        "vocabulary": list(ROLES),
        "reserved": list(RESERVED),
        "thresholds": thresholds.as_dict(),
        "cell": cell_dir,
        "merged_from": list(merged_from),
        "circuit": (meta or {}).get("circuit"),
        "task": (meta or {}).get("task"),
        "counts": counts(decisions),
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
    p.add_argument("--dry-run", action="store_true",
                   help="Propose and print; write nothing.")
    return p


def thresholds_from(cli) -> Thresholds:
    return Thresholds(z=cli.roles_z, dla_floor=cli.roles_dla_floor,
                      knockout_floor=cli.roles_knockout_floor,
                      path_floor=cli.roles_path_floor,
                      attention_floor=cli.roles_attention_floor)


def read_table(cell_dir: str) -> tuple:
    """`(rows, meta)` of a written head table, or a refusal naming the file."""
    path = os.path.join(cell_dir, TABLE_JSON)
    if not os.path.exists(path):
        raise SystemExit(f"no {TABLE_JSON} in {cell_dir!r}: the roles pass "
                         f"reads a finished head table, so run the analyses "
                         f"into this cell first (or point --roles-merge-from "
                         f"at the cells that have them).")
    with open(path) as handle:
        table = json.load(handle)
    return table["rows"], table.get("meta", {})


#: Never copied by `--roles-merge-from`: the key identifies the row, the intake
#: columns are the same on both sides, and `role_confirmed` is the human's.
NOT_MERGED = set(KEY_COLUMNS) | set(BASE_COLUMNS) | set(PROTECTED_COLUMNS)


def merge_cells(rows, cell_dirs) -> list:
    """Another cell's analysis columns, onto the rows that are already here."""
    for cell_dir in cell_dirs:
        other, _meta = read_table(cell_dir)
        updates = {row_key(one): {column: value
                                  for column, value in one.items()
                                  if column not in NOT_MERGED and value is not None}
                   for one in other}
        rows = merge_columns(rows, {key: values for key, values
                                    in updates.items() if values})
    return rows


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
    rows, meta = read_table(cli.cell_dir)
    rows = merge_cells(rows, cli.roles_merge_from)

    decisions = decide_rows(rows, thresholds)
    print(f"\nROLES — {cli.cell_dir}")
    print(f"  criteria: {CRITERIA_DOC} (pre-registered)")
    print(f"  thresholds: {thresholds.as_dict()}\n")
    print_decisions(decisions)

    if cli.dry_run:
        print("\n  --dry-run: nothing written.")
        return 0

    rows = merge_columns(rows, columns(decisions), namespace=NAME)
    meta = dict(meta)
    meta["roles"] = {"criteria_doc": CRITERIA_DOC,
                     "thresholds": thresholds.as_dict(),
                     "merged_from": list(cli.roles_merge_from),
                     "counts": counts(decisions)}
    written = write_head_table(cli.cell_dir, rows, meta=meta)

    out = os.path.join(cli.cell_dir, SUBDIR)
    os.makedirs(out, exist_ok=True)
    json_path = os.path.join(out, JSON_NAME)
    with open(json_path, "w") as handle:
        json.dump(payload(decisions, cell_dir=cli.cell_dir,
                          thresholds=thresholds,
                          merged_from=cli.roles_merge_from, meta=meta),
                  handle, indent=2, default=str)

    print(f"\n  {written['csv']}\n  {written['json']}\n  {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
