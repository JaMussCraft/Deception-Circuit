"""Paper figures for the mechanism-analysis synthesis (ticket 06).

Two stages, so every PNG is drawn from a committed CSV and nothing else:

- extract: read the curated tables under docs/research/mechanism-analysis/{phase1,phase1a,phase2,phase3}/ and the
  named reports (the 20 null draws of 03-1c-results.json; the logit-lens summaries in the fetched phase-1 cells), and
  write one CSV per figure into this directory, with figures_meta.json naming each CSV's sources;
- render: read each CSV and draw its PNG.

    python figures.py            # extract + render (needs the sources)
    python figures.py --render   # render only, from the committed CSVs

Task names far / sdr / ser and condition names D / H / F / I follow spec section 2.2. Colours are Okabe-Ito picks
checked with the dataviz palette validator (colour-blind separation passes); grey is reserved for nulls and the
"none" category.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MA = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(MA)))
REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports"
LENS_ROOT = os.path.join(REPO, "outputs", "_analyses", "mechanism-analysis-p1", "lens", "U__leaf")

TASKS = ("far", "sdr", "ser")
K_GRID = {"single": (1, 2, 3, 5, 10, 20, 40, 80), "greedy": (1, 2, 3, 5, 10, 20)}


# ==============================================================================
# CSV helpers
# ==============================================================================

def read_csv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: _cell(r.get(k, "")) for k in fields})


def _cell(v):
    if isinstance(v, float):
        return repr(v)
    return v


def _truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes")


# ==============================================================================
# Figure 1: R-AB mediation curves
# ==============================================================================

MEDIATION_FIELDS = [
    "task", "selector", "k", "candidate", "f_D", "f_lo", "f_hi", "acc", "acc_lo", "acc_hi",
    "null_f_mean", "null_f_min", "null_f_max", "null_acc_mean", "n_null", "null_f_draws",
    "test_i", "test_ii", "reading", "deciding", "f_I", "f_D_paired",
    "n_per_instance", "f_pi_median", "f_pi_q1", "f_pi_q3",
]


def _quartiles(values):
    """Median and first / third quartiles (statistics.quantiles, exclusive method; the same in py3.9 and py3.12)."""
    import statistics
    v = sorted(values)
    q = statistics.quantiles(v, n=4)
    return statistics.median(v), q[0], q[2]


def extract_mediation(p1c_json, rinv_csv):
    """One row per (task, selector, k) of the pre-registered grid; the U-only arm (R24) is left out.

    Sources: reports/03-1c-results.json (rab.<task>.candidates, with the 20 null draws) and phase1/rinv.csv (option B
    row: f_I and the paired f_D of the deciding set)."""
    with open(p1c_json) as fh:
        rab = json.load(fh)["rab"]
    rinv = {r["task"]: r for r in read_csv(rinv_csv) if r["rows"] == "optionB"}
    rows = []
    for task in TASKS:
        t = rab[task]
        for name, c in t["candidates"].items():
            sel = c["selector"]
            if sel not in K_GRID or int(c["k"]) not in K_GRID[sel]:
                continue
            draws = [float(x) for x in c["null_f"]]
            per = [float(x) for x in c["per_instance_f"] if x is not None]
            med, q1, q3 = _quartiles(per)
            deciding = name == t["deciding"]
            rows.append({
                "task": task, "selector": sel, "k": int(c["k"]), "candidate": name,
                "f_D": c["f"], "f_lo": c["f_ci"][0], "f_hi": c["f_ci"][1],
                "acc": c["acc"], "acc_lo": c["acc_ci"][0], "acc_hi": c["acc_ci"][1],
                "null_f_mean": c["null_f_mean"], "null_f_min": min(draws), "null_f_max": c["null_f_max"],
                "null_acc_mean": c["null_acc_mean"], "n_null": c["n_null"],
                "null_f_draws": ";".join(repr(x) for x in draws),
                "test_i": bool(c["i"]), "test_ii": bool(c["ii"]), "reading": t["reading"],
                "deciding": deciding,
                "f_I": float(rinv[task]["f_I"]) if deciding and rinv[task]["candidate"] == name else "",
                "f_D_paired": float(rinv[task]["f_D"]) if deciding and rinv[task]["candidate"] == name else "",
                "n_per_instance": len(per), "f_pi_median": med, "f_pi_q1": q1, "f_pi_q3": q3,
            })
    rows.sort(key=lambda r: (TASKS.index(r["task"]), r["selector"], r["k"]))
    return rows


# ==============================================================================
# Figure 2: R-inv paired contrast
# ==============================================================================

RINV_FIELDS = ["task", "candidate", "rows", "row_name", "primary", "n", "n_clusters", "f_D", "f_I", "half_f_D",
               "diff", "diff_lo", "diff_hi", "label"]
RINV_ROW_NAMES = {
    "optionB": "option B (primary, R23)",
    "optionB_inversion_polarity": "option B, inversion polarity only",
    "r19_robustness": "R19(3) subset (robustness)",
}


def extract_rinv(rinv_csv):
    """phase1/rinv.csv as is, plus 0.5 f_D and which id set is primary (R23 option B)."""
    rows = []
    for r in read_csv(rinv_csv):
        rows.append({
            "task": r["task"], "candidate": r["candidate"], "rows": r["rows"],
            "row_name": RINV_ROW_NAMES[r["rows"]], "primary": r["rows"] == "optionB",
            "n": int(r["n"]), "n_clusters": int(r["n_clusters"]),
            "f_D": float(r["f_D"]), "f_I": float(r["f_I"]), "half_f_D": 0.5 * float(r["f_D"]),
            "diff": float(r["diff"]), "diff_lo": float(r["diff_lo"]), "diff_hi": float(r["diff_hi"]),
            "label": r["label"],
        })
    return rows


# ==============================================================================
# Figure 3: B2 pressure-reader signature by layer
# ==============================================================================

B2_FLOOR = 0.05   # docs/component-roles.md rule 4b / spec 2.6 B2: drop >= 0.05 and >= 2 SE
B2_Z = 2.0
B2_FIELDS = ["task", "label", "layer", "index", "drop", "se", "signature", "in_S_k", "in_core", "in_excl"]
B2_COL = "attention_patterns.clause_mass_drop_neutral_twin_paired"


def extract_b2(head_tables):
    """Every measured head of the phase-2 D cell (U'), with its paired clause-mass drop at the Readout query.

    head_tables: {task: path to phase2/<task>_d_head_table.csv}."""
    rows = []
    for task in TASKS:
        for r in read_csv(head_tables[task]):
            if r["kind"] != "head" or r[B2_COL] in ("", None):
                continue
            drop, se = float(r[B2_COL]), float(r[B2_COL + "_se"])
            rows.append({
                "task": task, "label": f"head.{r['layer']}.{r['index']}", "layer": int(r["layer"]),
                "index": int(r["index"]), "drop": drop, "se": se,
                "signature": drop >= B2_FLOOR and drop >= B2_Z * se,
                "in_S_k": _truthy(r["membership.S_k"]), "in_core": _truthy(r["membership.core"]),
                "in_excl": _truthy(r["membership.excl_t"]),
            })
    return rows


# ==============================================================================
# Figure 4: A' adjudication shares
# ==============================================================================

CATEGORIES = ("q", "kv_clause", "kv_post_clause", "kv_unresolved", "none")
A_PRIME_FIELDS = ["task", "status", "category", "n_heads", "weight", "share", "call", "call_share"]


def extract_a_prime(a_prime_csv):
    """Share of the deciding set's head weight (the S2p single effect) per receiver category, spec 2.3."""
    heads = read_csv(a_prime_csv)
    rows = []
    for task in TASKS:
        mine = [h for h in heads if h["task"] == task]
        total = math.fsum(float(h["weight"]) for h in mine)
        per = {c: [h for h in mine if h["category"] == c] for c in CATEGORIES}
        unknown = {h["category"] for h in mine} - set(CATEGORIES)
        if unknown:
            raise ValueError(f"{task}: unknown categories {sorted(unknown)}")
        shares = {c: math.fsum(float(h["weight"]) for h in per[c]) / total for c in CATEGORIES}
        call = max(CATEGORIES, key=lambda c: shares[c])
        call_name = call if shares[call] > 0.5 else "mixed"
        for c in CATEGORIES:
            rows.append({
                "task": task, "status": mine[0]["status"], "category": c, "n_heads": len(per[c]),
                "weight": math.fsum(float(h["weight"]) for h in per[c]), "share": shares[c],
                "call": call_name, "call_share": shares[call],
            })
    return rows


# ==============================================================================
# Figures 5 and 6: phase-3 entry paths (B4) and the strongest neutral-twin paths
# ==============================================================================

PLACEMENTS = ("kv_clause", "kv_post_clause_named", "kv_post_clause_template", "q", "mlp_in", "readout")
ENTRY_FIELDS = ["task", "placement", "n", "sum_abs", "post_clause_share_of_kv"]
ROUTE_FIELDS = ["task", "rank", "cell", "sender", "receiver", "receiver_kind", "receiver_node", "sender_layer",
                "receiver_layer", "mean", "se", "placement", "top_segment"]


def _placement(r):
    """Where a neutral-twin path arrives (05-phase3-reading.md section 3). An `unsegmented` K/V split lands on template
    tokens after the clause, because pre-clause positions are identical in D and its twin."""
    if r["where"] == "clause":
        return "kv_clause"
    if r["where"] == "post_clause":
        return "kv_post_clause_named"
    if r["where"] == "post_clause_unsegmented":
        return "kv_post_clause_template"
    if r["where"] == "query_positions":
        if r["receiver_kind"] not in ("q", "mlp_in", "readout"):
            raise ValueError(f"unexpected receiver kind at the query positions: {r['receiver_kind']}")
        return r["receiver_kind"]
    raise ValueError(f"unplaced path {r['cell']}: where={r['where']!r}")


def extract_entry(entry_csv):
    paths = read_csv(entry_csv)
    rows = []
    for task in TASKS:
        mine = [p for p in paths if p["task"] == task]
        agg = {p: [0, 0.0] for p in PLACEMENTS}
        for p in mine:
            a = agg[_placement(p)]
            a[0] += 1
            a[1] += abs(float(p["mean"]))
        kv = math.fsum(agg[p][1] for p in PLACEMENTS[:3])
        post = (agg["kv_post_clause_named"][1] + agg["kv_post_clause_template"][1]) / kv
        for p in PLACEMENTS:
            rows.append({"task": task, "placement": p, "n": agg[p][0], "sum_abs": agg[p][1],
                         "post_clause_share_of_kv": post})
    return rows


def _node(name):
    """A path end as a graph node: q.L.H -> head.L.H; k|v.L.G -> kv.L.G (a KV group); mlp_in.L.0 -> mlp.L.0."""
    kind, _, rest = name.partition(".")
    if kind == "q":
        return "head." + rest
    if kind in ("k", "v"):
        return "kv." + rest
    if kind == "mlp_in":
        return "mlp." + rest
    return name


def _layer(node):
    if node == "embed":
        return -1
    if node == "readout":
        return 32
    return int(node.split(".")[1])


def extract_route(entry_csv, top=25):
    """The `top` strongest neutral-twin paths per task by |mean| (selection sample, C_t grid; EXPLORATORY figure)."""
    paths = read_csv(entry_csv)
    rows = []
    for task in TASKS:
        mine = sorted((p for p in paths if p["task"] == task), key=lambda p: -abs(float(p["mean"])))[:top]
        for i, p in enumerate(mine, 1):
            node = _node(p["receiver"])
            rows.append({
                "task": task, "rank": i, "cell": p["cell"], "sender": p["sender"], "receiver": p["receiver"],
                "receiver_kind": p["receiver_kind"], "receiver_node": node,
                "sender_layer": _layer(p["sender"]), "receiver_layer": _layer(node),
                "mean": float(p["mean"]), "se": float(p["se"]), "placement": _placement(p),
                "top_segment": p["top_segment"],
            })
    return rows


# ==============================================================================
# Figure 7: C1 cross-task knockout matrix (mean d per composition group)
# ==============================================================================

C1_COLUMNS = ("far:s1", "far:s5", "far:s6", "sdr:s1", "sdr:s5", "sdr:s6", "ser:s1", "ser:s5", "ser:s6",
              "far:s2", "far:s4", "sdr:s2", "sdr:s4", "ser:s2", "ser:s4")
C1_GROUPS = ("core", "excl_far", "excl_sdr", "excl_ser", "other D", "H only", "MLP", "outside")
C1_FIELDS = ["group", "n", "column", "task", "test_set", "counterfactual", "mean_d"]
C1_CELL = {"s1": ("D", "item-swap"), "s5": ("H", "item-swap"), "s6": ("F", "item-swap"),
           "s2": ("D", "neutral twin"), "s4": ("D", "mean")}


def extract_c1(c1_csv):
    table = read_csv(c1_csv)
    rows = []
    for g in C1_GROUPS:
        mine = [r for r in table if r["group"] == g]
        for col in C1_COLUMNS:
            vals = [float(r[col]) for r in mine if r[col] not in ("", None)]
            task, cell = col.split(":")
            rows.append({"group": g, "n": len(mine), "column": col, "task": task, "test_set": C1_CELL[cell][0],
                         "counterfactual": C1_CELL[cell][1], "mean_d": math.fsum(vals) / len(vals)})
    return rows


# ==============================================================================
# Figure 8: the exclusives' layers and reads
# ==============================================================================

EXCL_FIELDS = ["task", "label", "layer", "index", "top_segment", "top_mass", "read_group", "b2_drop"]
SEGMENT_GROUP = {   # docs/component-roles.md read groups; `unsegmented` is the BOS attention sink
    "response_line": "frame", "stem": "frame", "question": "frame",
    "item_1_question_option": "item_mention", "item_2_question_option": "item_mention",
    "pressure_clause": "pressure_clause", "unsegmented": "sink",
}


def extract_exclusives(head_tables):
    rows = []
    for task in TASKS:
        for r in read_csv(head_tables[task]):
            if r["kind"] != "head" or not _truthy(r["membership.excl_t"]):
                continue
            seg = r["attention_patterns.pressure_top_segment"]
            group = r["roles.reads_group"]
            rows.append({
                "task": task, "label": f"head.{r['layer']}.{r['index']}", "layer": int(r["layer"]),
                "index": int(r["index"]), "top_segment": seg,
                "top_mass": float(r["attention_patterns.pressure_top_mass"]),
                "read_group": "sink" if seg == "unsegmented" else (group or SEGMENT_GROUP.get(seg, "other")),
                "b2_drop": float(r[B2_COL]) if r[B2_COL] else "",
            })
    return rows


# ==============================================================================
# Figure 9: logit-lens trajectories (EXPLORATORY, R12)
# ==============================================================================

LENS_FIELDS = ["task", "condition", "source_condition", "row", "layer", "n", "mean", "se", "sign_flip_layer"]
LENS_CONDITIONS = {"D": "pressure_neutral_twin_paired", "H": "neutral_twin", "D-H": "differential_neutral_twin"}


def extract_lens(lens_root):
    """Mean and per-instance SE of the raw lens margin logit(deceptive) - logit(honest) at the Readout, per row
    (row 0 = the embedding, row l+1 = after layer l), D paired with its Neutral-Clause Twin (H) over 1,000 rows.

    The cells hold no per-instance trajectory, so no CI clustered by pressure_id can be drawn here (R12)."""
    rows = []
    for task in TASKS:
        with open(os.path.join(lens_root, f"{task}_v2", "dla", "logit_lens.json")) as fh:
            lens = json.load(fh)
        for cond, src in LENS_CONDITIONS.items():
            c = lens["conditions"][src]
            lv = c["levels"]["all"]
            for i, (m, s) in enumerate(zip(lv["mean"], lv["se"])):
                rows.append({"task": task, "condition": cond, "source_condition": src, "row": i, "layer": i - 1,
                             "n": lv["n"], "mean": float(m), "se": float(s),
                             "sign_flip_layer": c["sign_flip_layer"]})
    return rows


# ==============================================================================
# The figure registry: CSV, sources, status, caption
# ==============================================================================

def default_sources():
    return {
        "p1c_json": os.path.join(REPORTS, "03-1c-results.json"),
        "rinv_csv": os.path.join(MA, "phase1", "rinv.csv"),
        "c1_csv": os.path.join(MA, "phase1", "c1_matrix.csv"),
        "head_tables": {t: os.path.join(MA, "phase2", f"{t}_d_head_table.csv") for t in TASKS},
        "a_prime_csv": os.path.join(MA, "phase3", "a_prime.csv"),
        "entry_csv": os.path.join(MA, "phase3", "entry_paths.csv"),
        "lens_root": LENS_ROOT,
    }


FIGURES = {
    "fig1_mediation": {
        "fields": MEDIATION_FIELDS, "status": "pre-registered (R-AB, spec 2.3; f_I from R-inv, spec 2.4)",
        "sources": ["reports/03-1c-results.json (rab.<task>.candidates, null_f draws)", "phase1/rinv.csv"],
        "extract": lambda s: extract_mediation(s["p1c_json"], s["rinv_csv"]),
        "caption": "R-AB mediation curves on the held-out sample (n = 100, seed 1): joint neutral-twin knockout of "
                   "S_k at post-clause positions on D. Top: mediated fraction f_D with per-instance bootstrap 95% "
                   "CIs, the 20-draw layer-matched null (band = min to max, dotted = mean) and test (i)'s 0.75 bar; "
                   "the diamond is f_I of the deciding set on I (paired R-inv sample, R23; on sdr, read B, the "
                   "descriptive S_20). Bottom: two-way deceptive accuracy after the knockout, with (i)'s 0.25 bar "
                   "and the null mean. The CSV also gives the median and quartiles of the 100 per-instance f "
                   "(spec 2.3, R11(i)).",
    },
    "fig2_rinv": {
        "fields": RINV_FIELDS, "status": "pre-registered (R-inv, spec 2.4 as amended by R19(3) and R23)",
        "sources": ["phase1/rinv.csv"],
        "extract": lambda s: extract_rinv(s["rinv_csv"]),
        "caption": "R-inv, paired: 0.5 f_D and f_I of the deciding set (far, ser; on sdr, read B, the descriptive "
                   "S_20) on the same ids (left) and f_I - 0.5 f_D "
                   "with its 95% CI from a bootstrap clustered by pressure_id (right). On far and ser a CI "
                   "above 0 reads 'instructed inversion machinery', which licenses only 'not called "
                   "deception-specific'; both are below the 300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees (R30). sdr's rows are descriptive and carry no "
                   "verdict. Option B (R23) is primary; the other two id sets are robustness rows.",
    },
    "fig3_b2_by_layer": {
        "fields": B2_FIELDS, "status": "pre-registered (B-reader, spec 2.6; B2 signature of R25 rule 4b)",
        "sources": [f"phase2/{t}_d_head_table.csv" for t in TASKS],
        "extract": lambda s: extract_b2(s["head_tables"]),
        "caption": "B2 pressure-reader signature by layer: the paired drop of each U' head's Readout-query "
                   "attention mass on the Pressure Clause from D to its Neutral-Clause Twin (1,000 paired rows). "
                   "Filled = signature (drop >= 0.05 and >= 2 SE); shaded = layers 8-17 of B-reader's binomial "
                   "test; ringed = member of the deciding S_k.",
    },
    "fig4_a_prime": {
        "fields": A_PRIME_FIELDS, "status": "pre-registered on far and ser (A' adjudication, spec 2.3); descriptive "
                                            "on sdr (R-AB reading B)",
        "sources": ["phase3/a_prime.csv"],
        "extract": lambda s: extract_a_prime(s["a_prime_csv"]),
        "caption": "A' adjudication: share of the deciding set's head weight (each head's S2p single effect) by "
                   "the category of its strongest neutral-twin incoming path above the 0.01 floor (selection "
                   "sample, path patching on C_t). The call needs > 50% (dashed line). sdr is read B, so its bar "
                   "describes the single selector's S_20 and carries no sub-reading.",
    },
    "fig5_entry_paths": {
        "fields": ENTRY_FIELDS, "status": "descriptive (B4, spec 2.6); template-token placement EXPLORATORY",
        "sources": ["phase3/entry_paths.csv"],
        "extract": lambda s: extract_entry(s["entry_csv"]),
        "caption": "Where the neutral-twin pressure arrives on C_t (paths >= 0.01, selection sample). Left: K/V "
                   "paths by the Segment that carries most of their split (the clause span, a named post-clause "
                   "Segment, or post-clause template tokens). Right: receivers that sit at the query positions by "
                   "construction (Q, MLP input, Readout).",
    },
    "fig6_route": {
        "fields": ROUTE_FIELDS, "status": "EXPLORATORY (route description, 05-phase3-reading.md section 3)",
        "sources": ["phase3/entry_paths.csv"],
        "extract": lambda s: extract_route(s["entry_csv"], top=25),
        "caption": "The 25 strongest neutral-twin paths per task on C_t (selection sample), placed by layer. Edge "
                   "width = |normalized effect|; colour = where the path arrives; dashed = the path opposes the "
                   "pressured answer. kv.L.G is the shared K/V of group G at layer L (four query heads). Paths "
                   "outside C_t are not measured (routing share (c): far 0.163, sdr 0.297, ser 0.006).",
    },
    "fig7_c1_matrix": {
        "fields": C1_FIELDS, "status": "descriptive (C1, spec 2.7)",
        "sources": ["phase1/c1_matrix.csv"],
        "extract": lambda s: extract_c1(s["c1_csv"]),
        "caption": "Cross-task knockout matrix (C1): mean normalized drop d of each composition group on the nine "
                   "item-swap test sets (D, H, F per task) and on D under the neutral twin and under mean ablation "
                   "(selection sample, n = 100). Positive = supports the test set's own target (deceptive on D, "
                   "honest on H and F).",
    },
    "fig8_exclusives": {
        "fields": EXCL_FIELDS, "status": "C-reads pre-registered (fails, p 0.58); layer bands descriptive",
        "sources": [f"phase2/{t}_d_head_table.csv" for t in TASKS],
        "extract": lambda s: extract_exclusives(s["head_tables"]),
        "caption": "The exclusive heads of each D circuit by layer, marked by the read group of their top Segment "
                   "at the Readout under pressure (sink = the BOS attention sink, no established read).",
    },
    "fig9_lens": {
        "fields": LENS_FIELDS, "status": "EXPLORATORY (R12: raw lens, uncalibrated)",
        "sources": [f"outputs/_analyses/mechanism-analysis-p1/lens/U__leaf/{t}_v2/dla/logit_lens.json"
                    for t in TASKS],
        "extract": lambda s: extract_lens(s["lens_root"]),
        "caption": "Raw logit lens at the Readout: mean margin logit(deceptive) - logit(honest) per layer on D and "
                   "its paired Neutral-Clause Twin (H), 1,000 paired rows; bands are +/- 1.96 per-instance SE. "
                   "The cells keep no per-instance trajectory, so the band is not clustered by pressure_id. "
                   "Dashed: R-lens's -0.5 line; dotted verticals: the layer from which each mean margin keeps its "
                   "final sign (sign_flip_layer of component_analysis/dla.py).",
    },
}


def extract_all(out_dir, sources=None):
    sources = sources or default_sources()
    meta = {}
    for name, spec in FIGURES.items():
        rows = spec["extract"](sources)
        write_csv(os.path.join(out_dir, name + ".csv"), rows, spec["fields"])
        meta[name] = {"csv": name + ".csv", "png": name + ".png", "rows": len(rows), "status": spec["status"],
                      "sources": spec["sources"], "caption": spec["caption"]}
    with open(os.path.join(out_dir, "figures_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return meta


# ==============================================================================
# Render: CSV in, PNG out
# ==============================================================================

TASK_COLOUR = {"far": "#0072B2", "sdr": "#E69F00", "ser": "#009E73"}
COND_COLOUR = {"D": "#D55E00", "H": "#0072B2", "F": "#009E73", "I": "#CC79A7"}
SELECTOR_STYLE = {"greedy": ("#D55E00", "-", "o"), "single": ("#0072B2", "--", "s")}
CATEGORY_COLOUR = {"q": "#CC79A7", "kv_clause": "#0072B2", "kv_unresolved": "#56B4E9",
                   "kv_post_clause": "#E69F00", "none": "#999999"}
CATEGORY_ORDER = ("q", "kv_clause", "kv_unresolved", "kv_post_clause", "none")
PLACEMENT_COLOUR = {"kv_clause": "#0072B2", "kv_post_clause_named": "#E69F00", "kv_post_clause_template": "#56B4E9",
                    "q": "#CC79A7", "mlp_in": "#009E73", "readout": "#000000"}
PLACEMENT_NAME = {"kv_clause": "K/V, clause span", "kv_post_clause_named": "K/V, post-clause Segment",
                  "kv_post_clause_template": "K/V, post-clause template tokens", "q": "Q",
                  "mlp_in": "MLP input", "readout": "Readout"}
READ_STYLE = {"frame": ("#0072B2", "o"), "item_mention": ("#E69F00", "s"), "pressure_clause": ("#CC79A7", "D"),
              "sink": ("#999999", "x"), "other": ("#000000", "^")}
NULL_GREY = "#999999"
INK = "#222222"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#555555",
        "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "savefig.dpi": 200,
        "figure.facecolor": "white", "axes.facecolor": "white", "text.color": INK, "axes.labelcolor": INK,
    })
    return plt


def _f(v):
    return float(v) if v not in ("", None) else None


def _save(fig, path):
    fig.savefig(path, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)


def render_mediation(rows, path):
    plt = _plt()
    fig, axes = plt.subplots(2, 3, figsize=(10, 5.6), sharex=True)
    for j, task in enumerate(TASKS):
        top, bot = axes[0, j], axes[1, j]
        reading = next(r["reading"] for r in rows if r["task"] == task)
        for sel in ("single", "greedy"):
            col, ls, mk = SELECTOR_STYLE[sel]
            pts = sorted((r for r in rows if r["task"] == task and r["selector"] == sel), key=lambda r: int(r["k"]))
            k = [int(r["k"]) for r in pts]
            f = [float(r["f_D"]) for r in pts]
            top.fill_between(k, [float(r["null_f_min"]) for r in pts], [float(r["null_f_max"]) for r in pts],
                             color=col, alpha=0.12, linewidth=0)
            top.plot(k, [float(r["null_f_mean"]) for r in pts], color=col, ls=":", lw=1)
            top.errorbar(k, f, yerr=[[a - float(r["f_lo"]) for a, r in zip(f, pts)],
                                     [float(r["f_hi"]) - a for a, r in zip(f, pts)]],
                         color=col, ls=ls, marker=mk, ms=4, lw=1.5, capsize=2, label=f"{sel} selector")
            acc = [float(r["acc"]) for r in pts]
            bot.errorbar(k, acc, yerr=[[a - float(r["acc_lo"]) for a, r in zip(acc, pts)],
                                       [float(r["acc_hi"]) - a for a, r in zip(acc, pts)]],
                         color=col, ls=ls, marker=mk, ms=4, lw=1.5, capsize=2, label=f"{sel} selector")
            bot.plot(k, [float(r["null_acc_mean"]) for r in pts], color=col, ls=":", lw=1)
        dec = next(r for r in rows if r["task"] == task and _truthy(r["deciding"]))
        top.plot([int(dec["k"])], [float(dec["f_I"])], marker="D", ms=7, color=COND_COLOUR["I"], ls="none",
                 markeredgecolor="white", label="f_I, deciding set (I)", zorder=5)
        top.axhline(0.75, color=INK, ls="--", lw=0.8)
        bot.axhline(0.25, color=INK, ls="--", lw=0.8)
        top.set_title(f"{task}: R-AB reading {reading} (deciding: {dec['selector']} k = {dec['k']})")
        top.set_ylim(-0.05, 1.0)
        bot.set_ylim(-0.03, 1.03)
        bot.set_xscale("log")
        bot.set_xticks([1, 2, 3, 5, 10, 20, 40, 80])
        bot.set_xticklabels(["1", "2", "3", "5", "10", "20", "40", "80"])
        bot.set_xlabel("k (Components knocked out jointly)")
        if j == 0:
            top.set_ylabel("mediated fraction f_D")
            bot.set_ylabel("deceptive accuracy after KO")
    axes[0, 0].legend(loc="upper left", frameon=False)
    fig.suptitle("Pressure mediation by small Component sets (held-out D, neutral twin, post-clause)", y=1.0)
    fig.tight_layout()
    _save(fig, path)


def render_rinv(rows, path):
    plt = _plt()
    fig, (a, b) = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True, gridspec_kw={"width_ratios": [1.2, 1]})
    order = [(t, r) for t in TASKS for r in RINV_ROW_NAMES]
    ys = {key: -i - (TASKS.index(key[0]) * 0.6) for i, key in enumerate(order)}
    for r in rows:
        y = ys[(r["task"], r["rows"])]
        hd, fi = float(r["half_f_D"]), float(r["f_I"])
        a.plot([hd, fi], [y, y], color="#bbbbbb", lw=1.5, zorder=1)
        a.plot(hd, y, "o", color=COND_COLOUR["D"], ms=6, zorder=2)
        a.plot(fi, y, "D", color=COND_COLOUR["I"], ms=6, zorder=2)
        primary = _truthy(r["primary"])
        b.errorbar(float(r["diff"]), y, xerr=[[float(r["diff"]) - float(r["diff_lo"])],
                                             [float(r["diff_hi"]) - float(r["diff"])]],
                   fmt="o", ms=6 if primary else 4,
                   color=TASK_COLOUR[r["task"]], mfc=TASK_COLOUR[r["task"]] if primary else "white", capsize=2)
        star = "*" if r["task"] == "far" and r["rows"] != "optionB_inversion_polarity" else ""
        text = "descriptive" if r["task"] == "sdr" else r["label"].replace(" machinery", "") + star
        b.text(0.52, y, text, va="center", fontsize=6.5)
    a.plot([], [], "o", color=COND_COLOUR["D"], label="0.5 f_D (D)")
    a.plot([], [], "D", color=COND_COLOUR["I"], label="f_I (I)")
    a.legend(loc="lower right", frameon=False)
    a.set_yticks([ys[k] for k in order])
    a.set_yticklabels([f"{t}: {RINV_ROW_NAMES[r]} (n = {next(x['n'] for x in rows if x['task'] == t and x['rows'] == r)})"
                       for t, r in order])
    a.set_xlabel("fraction of I's (or D's) clean-minus-twin gap")
    b.axvline(0, color=INK, lw=0.8)
    b.set_xlabel("f_I - 0.5 f_D (95% CI, clustered by pressure_id)")
    b.set_xlim(-0.05, 0.75)
    fig.suptitle("R-inv: the far and ser deciding sets are not called deception-specific; sdr's S_20 is descriptive\n"
                 "(far and ser I pools below the 300-id minimum, R30; * far: polarity-confounded id set, "
                 "its inversion-polarity subset agrees)", y=1.05)
    fig.tight_layout()
    _save(fig, path)


def render_b2(rows, path):
    plt = _plt()
    fig, axes = plt.subplots(3, 1, figsize=(8, 6.4), sharex=True, sharey=True)
    for ax, task in zip(axes, TASKS):
        mine = [r for r in rows if r["task"] == task]
        ax.axvspan(7.5, 17.5, color="#f2f2f2", zorder=0, lw=0)
        no = [r for r in mine if not _truthy(r["signature"])]
        yes = [r for r in mine if _truthy(r["signature"])]
        ax.scatter([int(r["layer"]) for r in no], [float(r["drop"]) for r in no], s=10, color=NULL_GREY,
                   alpha=0.6, lw=0, label="no signature")
        ax.scatter([int(r["layer"]) for r in yes], [float(r["drop"]) for r in yes], s=18,
                   color=TASK_COLOUR[task], lw=0, label="B2 signature")
        sk = [r for r in mine if _truthy(r["in_S_k"])]
        ax.scatter([int(r["layer"]) for r in sk], [float(r["drop"]) for r in sk], s=46, facecolors="none",
                   edgecolors=INK, lw=0.8, label="in deciding S_k")
        ax.axhline(B2_FLOOR, color=INK, ls="--", lw=0.8)
        for r in sorted(yes, key=lambda r: -float(r["drop"]))[:3]:
            ax.annotate(r["label"].replace("head.", "L").replace(".", "H", 1), (int(r["layer"]), float(r["drop"])),
                        xytext=(4, 0), textcoords="offset points", fontsize=6.5, va="center")
        n_band = sum(1 for r in yes if 8 <= int(r["layer"]) <= 17)
        ax.set_title(f"{task}: {len(yes)} of {len(mine)} measured heads carry the signature, {n_band} in L8-17",
                     loc="left")
        ax.set_ylabel("clause-mass drop\n(D - twin, paired)")
    axes[0].legend(loc="upper right", frameon=False, ncol=3)
    axes[-1].set_xlabel("layer")
    axes[-1].set_xticks(range(0, 32, 2))
    fig.tight_layout()
    _save(fig, path)


SUB_READING = {"kv_clause": "A'-clause-reader", "q": "A'-selector", "kv_post_clause": "A'-mover",
               "kv_unresolved": "A'-unresolved", "none": "A'-unresolved", "mixed": "A'-mixed"}


def render_a_prime(rows, path):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8, 2.6))
    for i, task in enumerate(TASKS):
        y = len(TASKS) - 1 - i
        mine = {r["category"]: r for r in rows if r["task"] == task}
        left = 0.0
        for c in CATEGORY_ORDER:
            s = float(mine[c]["share"])
            ax.barh(y, s, left=left, color=CATEGORY_COLOUR[c], edgecolor="white", lw=1.5, height=0.6,
                    label=c if i == 0 else None)
            if s >= 0.06:
                ax.text(left + s / 2, y, f"{s:.2f}\n({mine[c]['n_heads']})", ha="center", va="center",
                        fontsize=6.5, color="white" if c in ("kv_clause", "q") else INK)
            left += s
        r0 = mine["q"]
        if r0["status"].startswith("pre-registered"):
            verdict = SUB_READING[r0["call"]]
        else:
            verdict = f"reading B: descriptive, {r0['call'].upper() if r0['call'] == 'q' else r0['call']}-dominated"
        ax.text(1.02, y, verdict, va="center", fontsize=7)
    ax.axvline(0.5, color=INK, ls="--", lw=0.8)
    ax.set_yticks(range(len(TASKS)))
    ax.set_yticklabels(list(reversed(TASKS)))
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of the deciding set's head weight (S2p single effect); (n) = heads")
    ax.grid(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=5, frameon=False)
    ax.set_title("A' adjudication: where the strongest neutral-twin input reaches each deciding-set head")
    _save(fig, path)


def render_entry(rows, path):
    plt = _plt()
    fig, (a, b) = plt.subplots(1, 2, figsize=(9, 3.0), gridspec_kw={"width_ratios": [1.2, 1]})
    for ax, group in ((a, PLACEMENTS[:3]), (b, PLACEMENTS[3:])):
        for i, task in enumerate(TASKS):
            y = len(TASKS) - 1 - i
            mine = {r["placement"]: r for r in rows if r["task"] == task}
            left = 0.0
            for p in group:
                s = float(mine[p]["sum_abs"])
                ax.barh(y, s, left=left, color=PLACEMENT_COLOUR[p], edgecolor="white", lw=1.5, height=0.6,
                        label=PLACEMENT_NAME[p] if i == 0 else None)
                if s >= 0.35:
                    ax.text(left + s / 2, y, f"{s:.2f}\n({mine[p]['n']})", ha="center", va="center", fontsize=6,
                            color="white" if p in ("kv_clause", "readout", "q", "mlp_in") else INK)
                left += s
            if ax is a:
                ax.text(left + 0.05, y, f"post-clause {float(mine[group[0]]['post_clause_share_of_kv']):.2f}",
                        va="center", fontsize=6.5)
        ax.set_yticks(range(len(TASKS)))
        ax.set_yticklabels(list(reversed(TASKS)))
        ax.grid(False)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False)
        ax.set_xlabel("summed |normalized path effect|; (n) = paths")
    a.set_title("K/V arrivals by Segment")
    b.set_title("receivers at the query positions")
    a.set_xlim(0, 6.0)
    _save(fig, path)


def render_route(rows, path):
    plt = _plt()
    fig, axes = plt.subplots(3, 1, figsize=(10, 9.5), sharex=True)
    for ax, task in zip(axes, TASKS):
        mine = [r for r in rows if r["task"] == task]
        nodes = {}
        for r in mine:
            nodes.setdefault(r["sender"], int(r["sender_layer"]))
            nodes.setdefault(r["receiver_node"], int(r["receiver_layer"]))
        by_layer = {}
        for n, layer in sorted(nodes.items(), key=lambda kv: (kv[1], kv[0])):
            by_layer.setdefault(layer, []).append(n)
        pos = {}
        for layer, ns in by_layer.items():
            for i, n in enumerate(ns):
                pos[n] = (layer, i - (len(ns) - 1) / 2.0)
        top = max(abs(float(r["mean"])) for r in mine)
        for r in mine:
            (x0, y0), (x1, y1) = pos[r["sender"]], pos[r["receiver_node"]]
            m = float(r["mean"])
            ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                        arrowprops=dict(arrowstyle="-|>", color=PLACEMENT_COLOUR[r["placement"]],
                                        lw=0.6 + 3.4 * abs(m) / top, ls="-" if m >= 0 else "--",
                                        shrinkA=6, shrinkB=6, connectionstyle="arc3,rad=0.08"))
        for n, (x, y) in pos.items():
            ax.plot(x, y, "o", ms=5, color="white", markeredgecolor=INK, zorder=3)
            short = n.replace("head.", "L").replace("mlp.", "MLP").replace("kv.", "KV")
            short = short.replace(".0", "") if short.startswith("MLP") else short.replace(".", "H" if
                                                                                          short.startswith("L") else "g", 1)
            above = int(x) % 2 == 0   # alternate label sides by layer so neighbouring layers do not collide
            ax.text(x, y + (0.28 if above else -0.28), short, ha="center", va="bottom" if above else "top",
                    fontsize=6, zorder=4)
        ax.set_title(f"{task}: 25 strongest neutral-twin paths into C_t", loc="left")
        ax.set_yticks([])
        ax.grid(axis="y", visible=False)
        ax.set_ylim(min(p[1] for p in pos.values()) - 0.8, max(p[1] for p in pos.values()) + 1.0)
    for p in PLACEMENTS:
        axes[0].plot([], [], color=PLACEMENT_COLOUR[p], lw=2, label=PLACEMENT_NAME[p])
    axes[0].legend(loc="upper left", ncol=3, frameon=False, bbox_to_anchor=(0, 1.35))
    axes[-1].set_xlabel("layer")
    axes[-1].set_xticks(range(0, 33, 2))
    fig.tight_layout()
    _save(fig, path)


def render_c1(rows, path):
    plt = _plt()
    import numpy as np
    groups = [g for g in C1_GROUPS if any(r["group"] == g for r in rows)]
    m = np.array([[float(next(r["mean_d"] for r in rows if r["group"] == g and r["column"] == c))
                   for c in C1_COLUMNS] for g in groups])
    lim = float(np.max(np.abs(m)))
    fig, ax = plt.subplots(figsize=(9, 3.4))
    im = ax.imshow(m, cmap="RdBu_r", vmin=-lim, vmax=lim, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center", fontsize=6,
                    color="white" if abs(m[i, j]) > 0.6 * lim else INK)
    labels = []
    for c in C1_COLUMNS:
        task, cell = c.split(":")
        ts, cf = C1_CELL[cell]
        labels.append(f"{task} {ts}\n{ {'item-swap': 'swap', 'neutral twin': 'twin', 'mean': 'mean'}[cf] }")
    ax.set_xticks(range(len(C1_COLUMNS)))
    ax.set_xticklabels(labels)
    n = {r["group"]: r["n"] for r in rows}
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([f"{g} ({n[g]})" for g in groups])
    ax.axvline(8.5, color=INK, lw=1)
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01)
    cb.set_label("mean d")
    ax.set_title("C1: mean normalized knockout drop by composition group "
                 "(item-swap on D / H / F; neutral twin and mean on D)")
    _save(fig, path)


def render_exclusives(rows, path):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8, 2.6))
    for i, task in enumerate(TASKS):
        y0 = len(TASKS) - 1 - i
        mine = sorted((r for r in rows if r["task"] == task), key=lambda r: (int(r["layer"]), int(r["index"])))
        seen = {}
        for r in mine:
            layer = int(r["layer"])
            k = seen.get(layer, 0)
            seen[layer] = k + 1
            col, mk = READ_STYLE.get(r["read_group"], READ_STYLE["other"])
            ax.plot(layer, y0 + (k - 0.0) * 0.12 - 0.2, mk, color=col, ms=6,
                    mfc=col if mk != "x" else "none")
        layers = [int(r["layer"]) for r in mine]
        ax.text(32.2, y0, f"n = {len(mine)}, median L{sorted(layers)[len(layers) // 2]}", va="center", fontsize=7)
    for g, (col, mk) in READ_STYLE.items():
        if any(r["read_group"] == g for r in rows):
            ax.plot([], [], mk, color=col, label="sink (BOS)" if g == "sink" else g.replace("_", " "))
    ax.set_yticks(range(len(TASKS)))
    ax.set_yticklabels([f"excl_{t}" for t in reversed(TASKS)])
    ax.set_xlim(-0.5, 31.5)
    ax.set_xticks(range(0, 32, 2))
    ax.set_xlabel("layer")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=4, frameon=False)
    ax.set_title("Exclusive heads by layer and read (top Segment at the Readout under pressure)")
    _save(fig, path)


def render_lens(rows, path):
    plt = _plt()
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.0), sharey=True)
    for ax, task in zip(axes, TASKS):
        for cond, label in (("D", "D (pressure)"), ("H", "H (Neutral-Clause Twin)")):
            pts = sorted((r for r in rows if r["task"] == task and r["condition"] == cond),
                         key=lambda r: int(r["row"]))
            x = [int(r["layer"]) for r in pts]
            m = [float(r["mean"]) for r in pts]
            s = [1.96 * float(r["se"]) for r in pts]
            ax.fill_between(x, [a - b for a, b in zip(m, s)], [a + b for a, b in zip(m, s)],
                            color=COND_COLOUR[cond], alpha=0.2, lw=0)
            ax.plot(x, m, color=COND_COLOUR[cond], lw=1.5, label=label)
            flip = int(pts[0]["sign_flip_layer"])
            ax.axvline(flip, color=COND_COLOUR[cond], ls=":", lw=1)
        ax.axhline(0, color=INK, lw=0.8)
        ax.axhline(-0.5, color=INK, ls="--", lw=0.6)
        ax.set_title(task)
        ax.set_xlabel("layer (-1 = embedding)")
    axes[0].set_ylabel("lens margin\nlogit(deceptive) - logit(honest)")
    axes[0].legend(loc="upper left", frameon=False)
    fig.suptitle("EXPLORATORY (R12): raw logit lens at the Readout, D vs its paired twin", y=1.03)
    fig.tight_layout()
    _save(fig, path)


RENDER = {
    "fig1_mediation": render_mediation, "fig2_rinv": render_rinv, "fig3_b2_by_layer": render_b2,
    "fig4_a_prime": render_a_prime, "fig5_entry_paths": render_entry, "fig6_route": render_route,
    "fig7_c1_matrix": render_c1, "fig8_exclusives": render_exclusives, "fig9_lens": render_lens,
}


def render_all(out_dir):
    written = []
    for name, fn in RENDER.items():
        rows = read_csv(os.path.join(out_dir, name + ".csv"))
        png = os.path.join(out_dir, name + ".png")
        fn(rows, png)
        written.append(png)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=HERE, help="directory for the CSVs, PNGs and figures_meta.json")
    ap.add_argument("--render", action="store_true", help="render from the CSVs already in --out; no extraction")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    if not args.render:
        extract_all(args.out)
    for p in render_all(args.out):
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
