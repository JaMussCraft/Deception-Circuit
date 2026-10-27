"""
p3_logic.py -- the pre-registered phase-3 readings as pure functions (ticket 05; spec section 2.3, 2.6 B-selector and
B4, R11(g), R14). No file IO: p3_results.py reads the cells and calls these; tests/test_mechanism_analysis_p3.py
holds them to the spec's wording.

Sign: every path number is the neutral-twin pass's normalized effect, (clean - patched) / (clean - twin) per instance,
then averaged: positive = the path helps the deceptive (pressured) answer against the twin (ADR-0002, native).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

#: The path floor of docs/component-roles.md (and receiver_category.FLOOR).
FLOOR = 0.01
#: R11(h) / R14: an A'-mover or A'-unresolved call is claimed only when routing share (c) is at most this.
ROUTING_MAX = 0.25
CATEGORIES = ("q", "kv_clause", "kv_post_clause", "kv_unresolved", "none")
#: Spec 2.3: the sub-reading named by the category holding > 50 % of the deciding set's head weight.
SUB_READING = {"q": "A'-selector", "kv_clause": "A'-clause-reader", "kv_post_clause": "A'-mover",
               "none": "A'-unresolved"}
MIXED = "A'-mixed"
ROUTE_OUTSIDE = "A', route outside C_t"
#: Sub-readings that rest on where or whether grid paths arrive (spec 2.3): gated by routing share (c).
ROUTING_GATED = ("A'-mover", "A'-unresolved")
L17_HEADS = ("head.17.24", "head.17.25", "head.17.26", "head.17.27")


def parse(label: str):
    kind, layer, index = label.split(".")
    return kind, int(layer), int(index)


# ------------------------------------------------------------------ A' adjudication

def weighted_call(heads: List[dict]) -> dict:
    """The weighted majority over the deciding set's heads (MLP members never reach here).

    `heads`: [{"label", "category", "weight"}], weight = the head's S2p single effect (mean drop, logits). A negative
    weight (the head opposes the pressured answer when knocked out) counts as 0, a convention recorded in the output.
    The call is the category holding > 50 % of the summed weight; otherwise A'-mixed."""
    weights = {h["label"]: max(float(h["weight"]), 0.0) for h in heads}
    total = sum(weights.values())
    shares = {c: (sum(weights[h["label"]] for h in heads if h["category"] == c) / total if total > 0 else 0.0)
              for c in CATEGORIES}
    counts = {c: sum(1 for h in heads if h["category"] == c) for c in CATEGORIES}
    top = max(CATEGORIES, key=lambda c: shares[c])
    call = top if shares[top] > 0.5 else None
    if total <= 0:
        sub, note = MIXED, "no positive head weight: every S2p single effect is <= 0, so no share is defined"
    elif call is None:
        sub, note = MIXED, "no category holds more than half of the head weight"
    elif call == "kv_unresolved":
        sub, note = None, ("kv_unresolved holds the majority: a K/V arrival whose span the split cannot place; the "
                           "spec's four sub-readings do not name it, so the call needs a researcher ruling")
    else:
        sub, note = SUB_READING[call], ""
    return {"shares": shares, "counts": counts, "total_weight": total, "call": call, "sub_reading": sub,
            "note": note, "negative_weights_floored": sorted(h["label"] for h in heads if float(h["weight"]) < 0)}


def routing_gate(sub_reading: Optional[str], share_c: float) -> dict:
    """R11(h) / R14: A'-mover and A'-unresolved stand only when share (c) <= 0.25, else 'A', route outside C_t'."""
    gated = sub_reading in ROUTING_GATED
    if gated and share_c > ROUTING_MAX:
        return {"final": ROUTE_OUTSIDE, "gated": True, "passes": False, "r14": True}
    return {"final": sub_reading, "gated": gated, "passes": True if gated else None, "r14": False}


def adjudicate(members: Iterable[str], categories: Dict[str, dict], weights: Dict[str, float],
               share_c: float) -> dict:
    """Spec 2.3's A' adjudication for one deciding set.

    `categories`: {head label: the receiver-category result (category, path, support, se, segment, ...)};
    `weights`: {label: S2p mean drop}. MLP members are listed and counted, never called."""
    members = list(members)
    mlps = [m for m in members if m.startswith("mlp.")]
    rows = []
    for m in members:
        if not m.startswith("head."):
            continue
        cat = categories.get(m) or {}
        rows.append({"label": m, "category": cat.get("category", "unmeasured"), "path": cat.get("path"),
                     "support": cat.get("support"), "se": cat.get("se"), "segment": cat.get("segment"),
                     "weight": weights.get(m), "note": cat.get("note", "")})
    missing = [r["label"] for r in rows if r["category"] not in CATEGORIES or r["weight"] is None]
    if missing:
        raise ValueError(f"deciding-set heads without a category or an S2p weight: {missing}")
    call = weighted_call(rows)
    gate = routing_gate(call["sub_reading"], share_c)
    return {"heads": rows, "mlp_members": mlps, "n_heads": len(rows), "n_mlps": len(mlps), "weighted": call,
            "routing_share_c": share_c, "routing": gate, "sub_reading": gate["final"]}


def _call(heads: List[dict], category_of, categories: Iterable[str]) -> dict:
    """The > 50 % weighted call over `categories`, each head placed by `category_of(head)`."""
    categories = tuple(categories)
    weights = {h["label"]: max(float(h["weight"] or 0.0), 0.0) for h in heads}
    total = sum(weights.values())
    shares = {c: (sum(weights[h["label"]] for h in heads if category_of(h) == c) / total if total > 0 else 0.0)
              for c in categories}
    top = max(categories, key=lambda c: shares[c])
    return {"shares": shares, "call": top if shares[top] > 0.5 else None}


def robustness(heads: List[dict], floor: float = FLOOR) -> dict:
    """EXPLORATORY, not pre-registered: does the weighted call survive three re-readings of the same cells?

    - positive_path_only: a head whose strongest path opposes the pressured answer (support < 0) counts as none;
    - floor_x2: a head whose strongest path is under twice the floor counts as none (the cross-card noise is ~0.005);
    - totals: each head placed by its larger summed |effect| over the floor, Q against K+V (the roles doc says the
      strongest single receiver is not dominance; this is the totals view of the same question).
    Also the number of distinct KV groups behind the kv_clause heads: heads of one group share their K/V cells, so
    the group, not the head, is the independent test (spec 7)."""
    def signed(h):
        return h["category"] if (h.get("support") or 0.0) > 0 or h["category"] in ("none",) else "none"

    def doubled(h):
        s = h.get("support")
        return h["category"] if s is not None and abs(s) >= 2 * floor else "none"

    def totals(h):
        q, kv = h.get("q_abs") or 0.0, h.get("kv_abs") or 0.0
        return "q" if q > kv else ("kv" if kv > q else "none")

    clause = [h for h in heads if h["category"] == "kv_clause"]
    groups = {h["path"].split("->")[1].split(".", 1)[1] for h in clause if h.get("path")}
    return {"positive_path_only": _call(heads, signed, CATEGORIES),
            "floor_x2": _call(heads, doubled, CATEGORIES),
            "totals": _call(heads, totals, ("q", "kv", "none")),
            "kv_clause_heads": len(clause), "kv_clause_groups": len(groups)}


# ------------------------------------------------------------------ receivers of one head

def incoming(agnostic: dict, label: str) -> Dict[str, List[dict]]:
    """{"q": cells into the head's own query, "kv": cells into its KV group's k and v receivers}."""
    _kind, layer, index = parse(label)
    receivers = agnostic.get("receivers") or []
    q_keys = {r["key"] for r in receivers if r.get("kind") == "q" and r.get("layer") == layer
              and index in (r.get("circuit_heads") or [])}
    kv_keys = {r["key"] for r in receivers if r.get("kind") in ("k", "v") and r.get("layer") == layer
               and index in (r.get("circuit_heads") or [])}
    cells = agnostic.get("cells") or []
    return {"q": [c for c in cells if c["receiver"] in q_keys],
            "kv": [c for c in cells if c["receiver"] in kv_keys]}


def receiver_totals(agnostic: dict, label: str, floor: float = FLOOR) -> dict:
    """Descriptive per-receiver totals (B-selector): over the incoming cells at or above the floor, the signed sum
    and the sum of |mean|, into Q vs into K + V. Not dominance (the roles doc): a description beside the category."""
    out = {}
    for side, cells in incoming(agnostic, label).items():
        kept = [c for c in cells if c.get("mean") is not None and abs(c["mean"]) >= floor]
        out[f"{side}_n"] = len(kept)
        out[f"{side}_signed"] = sum(c["mean"] for c in kept)
        out[f"{side}_abs"] = sum(abs(c["mean"]) for c in kept)
    return out


def strongest_kv(agnostic: dict, label: str) -> Optional[dict]:
    """The strongest K/V cell into the head's KV group (by |mean|), whatever the head's own category."""
    cells = [c for c in incoming(agnostic, label)["kv"] if c.get("mean") is not None]
    return max(cells, key=lambda c: abs(c["mean"])) if cells else None


# ------------------------------------------------------------------ B-selector

def b_selector(by_task: Dict[str, Dict[str, str]], core_l24: Dict[str, List[str]]) -> dict:
    """Spec 2.6 B-selector, two clauses.

    `by_task`: {task: {head label: category}} (L17H24-27 must be present); `core_l24`: {task: [the core's L24 heads]}.
    (1) "At least one of L17H24-27 has category Q on >= 2 tasks": decided on the literal reading, one head with q on
        two or more tasks; the looser reading (q on some L17 head, on >= 2 tasks) is reported beside it.
    (2) "the core's L24 heads fall in K/V from post-clause positions": per task, every core L24 head kv_post_clause."""
    tasks = list(by_task)
    missing = [f"{t}:{h}" for t in tasks for h in list(L17_HEADS) + list(core_l24.get(t, []))
               if by_task[t].get(h) not in CATEGORIES]
    if missing:
        raise ValueError(f"B-selector heads without a receiver category: {missing}")
    per_head = {h: [t for t in tasks if by_task[t].get(h) == "q"] for h in L17_HEADS}
    literal = any(len(v) >= 2 for v in per_head.values())
    loose_tasks = [t for t in tasks if any(by_task[t].get(h) == "q" for h in L17_HEADS)]
    l24 = {}
    for t in tasks:
        cats = {h: by_task[t].get(h) for h in core_l24.get(t, [])}
        l24[t] = {"categories": cats, "n": len(cats),
                  "n_kv_post_clause": sum(1 for c in cats.values() if c == "kv_post_clause"),
                  "all_kv_post_clause": bool(cats) and all(c == "kv_post_clause" for c in cats.values())}
    return {"l17_q_tasks_per_head": per_head, "clause1_literal": literal,
            "clause1_loose_tasks": loose_tasks, "clause1_loose": len(loose_tasks) >= 2,
            "l24": l24, "clause2_all_tasks": all(v["all_kv_post_clause"] for v in l24.values()),
            "clause2_tasks": [t for t, v in l24.items() if v["all_kv_post_clause"]]}


# ------------------------------------------------------------------ where the pressure enters (B4)

UNSEGMENTED = "unsegmented"
POST_CLAUSE_UNSEGMENTED = "post_clause_unsegmented"


def span_class(segment: Optional[str]) -> str:
    from component_analysis.receiver_category import segment_class
    return segment_class(segment)


def entry_points(agnostic: dict, segments: Optional[dict], floor: float = FLOOR) -> dict:
    """Per sender, its neutral-twin paths into the grid's receivers at or above the floor, with the positions:
    K/V cells by the split's top Segment class (clause / post_clause / unresolved; pre_clause would be a bug),
    Q / MLP-in / Readout cells at the query positions (the Readout), where the split patches them.

    Returns {"senders": [...] strongest first by summed |mean|, "by_class": totals, "cells": the cells}."""
    kinds = {r["key"]: r["kind"] for r in agnostic.get("receivers") or []}
    splits = {c["cell"]: c for c in (segments or {}).get("cells") or []}
    cells, senders = [], {}
    for c in agnostic.get("cells") or []:
        if c.get("mean") is None or abs(c["mean"]) < floor:
            continue
        kind = kinds.get(c["receiver"], c["receiver"].split(".")[0])
        split = splits.get(c["cell"])
        if kind in ("k", "v"):
            seg = ((split or {}).get("top_segment") or {}).get("segment")
            where = span_class(seg) if split else "no_split"
            if seg == UNSEGMENTED:
                # The unsegmented positions are the template tokens before the clause and after it. Pre-clause
                # positions are identical in D and its twin, so they carry nothing: the arrival is post-clause
                # (05 spec review 2). The pre-registered category (receiver_category, R25) is unchanged.
                where = POST_CLAUSE_UNSEGMENTED
        else:
            seg, where = None, "query_positions"
        one = {"cell": c["cell"], "sender": c["sender"], "receiver": c["receiver"], "receiver_kind": kind,
               "mean": c["mean"], "se": c.get("se"), "top_segment": seg, "where": where}
        cells.append(one)
        s = senders.setdefault(c["sender"], {"sender": c["sender"], "n": 0, "abs": 0.0, "signed": 0.0,
                                             "abs_by_where": {}, "n_by_where": {}, "receivers": []})
        s["n"] += 1
        s["abs"] += abs(c["mean"])
        s["signed"] += c["mean"]
        s["abs_by_where"][where] = s["abs_by_where"].get(where, 0.0) + abs(c["mean"])
        s["n_by_where"][where] = s["n_by_where"].get(where, 0) + 1
        s["receivers"].append(c["receiver"])
    ranked = sorted(senders.values(), key=lambda s: -s["abs"])
    by_class = {}
    for one in cells:
        b = by_class.setdefault(one["where"], {"n": 0, "abs": 0.0})
        b["n"] += 1
        b["abs"] += abs(one["mean"])
    return {"senders": ranked, "by_class": by_class, "cells": cells, "n_cells": len(cells),
            "pre_clause_bug": [one["cell"] for one in cells if one["where"] == "pre_clause"]}


# ------------------------------------------------------------------ completeness (twin sweep)

def completeness(sweep: dict, ct_labels: Iterable[str]) -> dict:
    """The neutral-twin completeness sweep's direct paths into the Readout, as shares of the clean-minus-twin gap
    (each sender's mean is already normalized by the gap): summed over the candidates (C_t), over every Component
    outside C_t, and the embedding apart (a sender, not a Component). Signed sums decide nothing; |sums| beside."""
    ct = set(ct_labels)
    inside = [s for s in sweep["senders"] if s["sender"] in ct and s.get("mean") is not None]
    outside = [s for s in sweep["senders"] if s["sender"] not in ct and s["sender"] != "embed"
               and s.get("mean") is not None]
    embed = [s for s in sweep["senders"] if s["sender"] == "embed"]
    disagree = [s["sender"] for s in sweep["senders"] if s["sender"] != "embed"
                and bool(s.get("in_circuit")) != (s["sender"] in ct)]
    tot = sum(s["mean"] for s in inside + outside) + sum(s["mean"] or 0 for s in embed)
    unmeasured = [s["sender"] for s in sweep["senders"] if s["sender"] != "embed" and s.get("mean") is None]
    return {"n_inside": len(inside), "n_outside": len(outside),
            "unmeasured_inside": [x for x in unmeasured if x in ct],
            "unmeasured_outside": [x for x in unmeasured if x not in ct],
            "inside_signed": sum(s["mean"] for s in inside), "outside_signed": sum(s["mean"] for s in outside),
            "inside_abs": sum(abs(s["mean"]) for s in inside), "outside_abs": sum(abs(s["mean"]) for s in outside),
            "embed": embed[0]["mean"] if embed else None, "all_signed": tot,
            "flagged": list(sweep.get("flagged") or []),
            "top_outside": sorted(({"sender": s["sender"], "mean": s["mean"], "se": s.get("se")} for s in outside),
                                  key=lambda s: -abs(s["mean"]))[:10],
            "membership_disagrees": disagree}
