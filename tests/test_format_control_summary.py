"""
The format-control suite summary writer (`evaluation/format_control_summary.py`,
CLI `write_format_control_summary.py`).

Seams under test, as the spec's Testing Decisions name them: the summary
written for a fixture suite directory (`evaluation_summary.md` and
`decision.json`), and for an incomplete one (missing cells are reported, never
crashed on); plus the pure decision rule `decide` at its 80 percent boundary.

The fixture suite is tiny JSON cells in the merged layout ticket 04's
`merge_shards.py` writes: `cells/<circuit>/<dataset dir>/interchange/`. The
numbers are literals chosen by hand (the D-data honest-instruction row is the
real FAR nls0.3 cell of the 2026-09-22 rerun: full 0.106, knockout 0.861),
so every expected drop below is an independent worked example.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from evaluation import format_control_summary as fcs

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLES = ("D", "H", "F")
DELTAS = ("D_minus_F", "D_and_F", "F_minus_D",
          "D_minus_H_minus_F", "H_minus_D_minus_F", "F_minus_D_minus_H")
NOPRESSURE_REASON = ("far 'honest_instruction' variant skipped: the dataset's condition is "
                     "'nopressure' (empty pressure), so it already is the no_pressure variant")


# ==============================================================================
# FIXTURE SUITE
# ==============================================================================

def _dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f)


def _ko_block(full, ko, null):
    p5, p50, p95 = null
    return {"circuit": {"accuracy": 0.9, "n": 100},
            "knockout": {"accuracy": ko, "n": 100},
            "null": {"n": 20, "stats": {"accuracy": {
                "n": 20, "p5": p5, "p50": p50, "p95": p95, "discovered": ko,
                "percentile": 0.0 if ko < p5 else 50.0, "z": -4.0 if ko < p5 else 0.0}}}}


def _gens(knockout_text):
    full = "the film was released in the summer and earned praise from critics for its score"
    return {"examples": [{"index": i, "continuations": {"full": full + f" {i}",
                                                        "knockout": knockout_text + f" {i}"}}
                         for i in range(3)]}


def _variant(full, ko):
    return {"rows": {"full": {"accuracy": full}, "circuit": {"accuracy": 0.5},
                     "knockout": {"accuracy": ko}},
            "headline": {"full_accuracy": full, "knockout_accuracy": ko,
                         "full_minus_knockout": full - ko}}


def _knockout_json(full, ko, null, kl, variants, gen_text):
    out = {"granularity": "finest", "ablation": "interchange",
           "counts": {"ablated_fine_units": 5000},
           "task": _ko_block(full, ko, null),
           "wikitext": {"discovered": {"kl_per_token": kl}},
           "generation": _gens(gen_text)}
    if variants == "skip":
        out["variants"] = {v: {"variant": v, "skipped": NOPRESSURE_REASON.replace(
            "honest_instruction", v)} for v in ("honest_instruction", "no_pressure")}
    elif variants:
        out["variants"] = {v: _variant(*fk) for v, fk in variants.items()}
    return out


#: Defaults give verdict (a): F's knockout matches D's on deception at lower
#: collateral. Tests override single numbers to move the verdict.
DEFAULTS = {
    "full": {"": 0.97, "_honest": 0.95, "_nopressure": 0.96},
    "ko": {"D": {"": 0.00, "_honest": 0.50, "_nopressure": 0.60},
           "H": {"": 0.30, "_honest": 0.10, "_nopressure": 0.50},
           "F": {"": 0.10, "_honest": 0.60, "_nopressure": 0.70}},
    "null": {"D": (0.44, 0.87, 0.99), "H": (0.40, 0.80, 0.95), "F": (0.50, 0.85, 0.97)},
    "kl": {"D": 0.327, "H": 0.20, "F": 0.30},
    # (full, knockout) accuracy under the deceptive-label convention on D data
    "variants": {"D": {"honest_instruction": (0.106, 0.861), "no_pressure": (0.058, 0.934)},
                 "H": {"honest_instruction": (0.106, 0.300), "no_pressure": (0.058, 0.200)},
                 "F": {"honest_instruction": (0.106, 0.500), "no_pressure": (0.058, 0.400)}},
    "gen": {"D": "he was born in a small town and later moved to the city to study law",
            "H": "she wrote several novels about the sea and the people who lived near it",
            "F": "the band toured across europe before returning home to record a new album"},
    "source_counts": {"train": {"deceptive_split": 1, "honest_split": 149},
                      "validation": {"deceptive_split": 0, "honest_split": 150},
                      "test": {"deceptive_split": 8, "honest_split": 492}},
}


def _merge(base, over):
    out = json.loads(json.dumps(base))
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def make_suite(tmp_path, family="fine", task="far", over=None, skip_cells=(),
               f_nls=0.3, overlap=True, flip=True):
    """A merged format-control suite under tmp_path; returns (suite_root, data_dir)."""
    p = _merge(DEFAULTS, over)
    name = f"format-control-{task}{'-coarse' if family == 'coarse' else ''}-nls0.3"
    root = str(tmp_path / "outputs" / "_suites" / name)
    data_dir = str(tmp_path / "data" / "datasets")
    _dump(os.path.join(data_dir, f"{task}_nopressure", "dataset_config.json"),
          {"task": task, "condition": "nopressure", "margin_thresh": 0.3,
           "source_counts": p["source_counts"]})
    runs = {}
    conds = {"D": "deceptive", "H": "honest", "F": "nopressure"}
    for r in ROLES:
        runs[r] = str(tmp_path / "runs" / r)
        _dump(os.path.join(runs[r], "config.json"),
              {"task": task, "deception_condition": conds[r],
               "node_lambda_sparsity": f_nls if r == "F" else 0.3,
               "deception_margin_loss": 0.7})
    if f_nls != 0.3:
        _dump(os.path.join(runs["F"], "size_check.json"),
              {"paired_nls": 0.3, "format_nls": f_nls, "retuned": True})
    datasets = {suffix: task + suffix for suffix in ("", "_honest", "_nopressure")}
    circuits = [{"label": r, "kind": "atomic", "expr": None, "operands": {r: runs[r]},
                 "home_run_dir": runs[r], "counts": {"attention_heads": 40 + i}}
                for i, r in enumerate(ROLES)]
    tasks = [{"label": d, "task": task, "dataset": {"deception_condition":
              {"": "deceptive", "_honest": "honest", "_nopressure": "nopressure"}[s]}}
             for s, d in datasets.items()]

    def write_cell(label, dataset, knock=None, faith=None):
        if f"{label}/{dataset}" in skip_cells:
            return
        d = os.path.join(root, "cells", label, dataset, "interchange")
        if knock is not None:
            _dump(os.path.join(d, "knockout.json"), knock)
        if faith is not None:
            _dump(os.path.join(d, "null.json"), faith)

    for r in ROLES:
        for s, d in datasets.items():
            full, ko = p["full"][s], p["ko"][r][s]
            variants = ("skip" if s == "_nopressure" else
                        p["variants"][r] if s == "" else
                        {"honest_instruction": (0.90, 0.80), "no_pressure": (0.92, 0.85)})
            knock = _knockout_json(full, ko, p["null"][r], p["kl"][r], variants, p["gen"][r])
            faith = {"anchors": {"full": {"accuracy": full}}, "discovered": {"accuracy": 0.9}}
            if family == "fine":
                write_cell(r, d, knock, faith)
            else:
                write_cell(r, d, None, faith)
                write_cell(f"{r}_hko__leaf", d, knock, None)
    grans = ("head", "leaf") if family == "fine" else ("leaf",)
    for i, lab in enumerate(DELTAS):
        for g in grans:
            label = f"{lab}__{g}" if family == "fine" else f"{lab}_hko__leaf"
            knock = _knockout_json(p["full"][""], 0.5 + i / 100, (0.6, 0.8, 0.9), 0.2, None, "x")
            write_cell(label, task, knock, None)
            heads = 10 + i if g == "head" else {"active": 10 + i, "total": 1024}
            circuits.append({"label": label, "kind": "composed", "expr": lab,
                             "counts": {"attention_heads": heads}})
    _dump(os.path.join(root, "suite.json"), {"circuits": circuits, "tasks": tasks})
    if overlap:
        def pair(a, b, j, inter):
            return {"pair": f"{a}/{b}", "awaits": [],
                    "heads": {"jaccard": j, "intersection": inter, "active_a": 48,
                              "active_b": 60, "union": 70},
                    "fine_units": None if family == "coarse" else
                    {"jaccard": j / 2, "intersection": 1000, "active_a": 5436,
                     "active_b": 9000, "union": 13436}}
        _dump(os.path.join(root, "overlap.json"),
              {"family": family, "task": task,
               "pairs": [pair("D", "H", 0.43, 34), pair("D", "F", 0.31, 25),
                         pair("H", "F", 0.52, 40)]})
    if flip:
        cells = []
        for r in ROLES:
            lab = r if family == "fine" else f"{r}_hko__leaf"
            for d in datasets.values():
                cells.append({"circuit": lab, "task": d, "headline": {"separable": True},
                              "positional": {"verdict": "content-driven flip"}})
        cells.append({"circuit": "D_minus_F__head" if family == "fine" else "D_minus_F_hko__leaf",
                      "task": task, "headline": {"separable": False},
                      "positional": {"verdict": "positional default"}})
        _dump(os.path.join(root, "flip_audit.json"), {"cells": cells})
    return root, data_dir


def run(root, data_dir, **kw):
    md_path, json_path = fcs.write_summary(root, data_dir=data_dir, **kw)
    with open(md_path) as f:
        md = f.read()
    with open(json_path) as f:
        decision = json.load(f)
    return md, decision


# ==============================================================================
# VERDICTS
# ==============================================================================

def test_format_circuit_as_effective_at_lower_collateral_is_verdict_a(tmp_path):
    root, data = make_suite(tmp_path)
    md, decision = run(root, data)
    assert decision["verdict"] == "a"
    assert all(c["passed"] for c in decision["conditions"])
    assert "Format explains it" in decision["sentence"]
    assert "(a)" in md and decision["sentence"] in md
    assert os.path.exists(os.path.join(root, "evaluation_summary.md"))
    assert os.path.exists(os.path.join(root, "decision.json"))


def test_honest_answer_drop_on_d_data_follows_the_deceptive_label_convention(tmp_path):
    # Real FAR nls0.3 D x far honest_instruction row: full 0.106, knockout 0.861 under
    # deceptive labels -> honest-answer accuracy 0.894 -> 0.139, a drop of 0.755.
    root, data = make_suite(tmp_path)
    _, decision = run(root, data)
    rows = decision["inputs"]["D"]["honest_rows"]
    assert rows["honest_instruction (D data)"] == pytest.approx(0.755)
    assert rows["no_pressure (D data)"] == pytest.approx(0.876)
    assert rows["H test set"] == pytest.approx(0.95 - 0.50)       # honest labels
    assert list(rows) == ["honest_instruction (D data)", "no_pressure (D data)",
                          "H test set", "F test set"]
    rule_rows = [r["row"] for r in decision["conditions"][1]["rows"]]
    assert rule_rows == list(rows)


def test_weaker_format_knockout_is_verdict_b(tmp_path):
    root, data = make_suite(tmp_path, over={"ko": {"F": {"": 0.60}}})   # F drop 0.37
    md, decision = run(root, data)
    assert decision["verdict"] == "b"
    cond = {c["name"]: c for c in decision["conditions"]}
    assert cond["deception drop"]["passed"] is False
    assert cond["deception drop"]["F"] == pytest.approx(0.37)
    assert "Deception-specific machinery exists" in md


def test_larger_honest_answer_drop_on_one_row_is_verdict_b(tmp_path):
    # F's knockout hurts honest answering on the H test set more than D's (0.55 > 0.45).
    root, data = make_suite(tmp_path, over={"ko": {"F": {"_honest": 0.40}}})
    _, decision = run(root, data)
    cond = {c["name"]: c for c in decision["conditions"]}
    rows = {r["row"]: r["passed"] for r in cond["honest-answer drop"]["rows"]}
    assert rows == {"honest_instruction (D data)": True, "no_pressure (D data)": True,
                    "H test set": False, "F test set": True}
    assert decision["verdict"] == "b"


def test_format_knockout_inside_its_null_is_verdict_b(tmp_path):
    root, data = make_suite(tmp_path, over={"null": {"F": (0.05, 0.5, 0.9)}})
    _, decision = run(root, data)
    cond = {c["name"]: c for c in decision["conditions"]}
    assert cond["outside nulls"]["D"] is True and cond["outside nulls"]["F"] is False
    assert decision["verdict"] == "b"


def test_format_knockout_above_the_kl_gate_is_verdict_c_even_when_otherwise_a(tmp_path):
    # D is above the gate too, so "F's KL <= D's" passes: only the gate stops (a).
    root, data = make_suite(tmp_path, over={"kl": {"D": 0.80, "F": 0.70}})
    md, decision = run(root, data)
    assert all(c["passed"] for c in decision["conditions"])
    assert decision["gate"]["kl_fails"] is True
    assert decision["verdict"] == "c"
    assert "retrain the Format Circuit at a lower NLS" in decision["sentence"]
    assert "retrain the Format Circuit at a lower NLS" in md


def test_degenerate_format_generations_are_verdict_c(tmp_path):
    root, data = make_suite(tmp_path, over={"gen": {"F": "the the the the the the the the"}})
    _, decision = run(root, data)
    assert decision["gate"]["kl_fails"] is False
    assert decision["gate"]["degenerate"] is True
    assert decision["verdict"] == "c"


# ==============================================================================
# THE 80 PERCENT BOUNDARY
# ==============================================================================

def _sides(d_drop, f_drop):
    side = {"knockout_acc": 0.1, "null_p5": 0.5, "outside_null": True,
            "honest_rows": {"r": 0.2}, "wikitext_kl": 0.3, "distinct2_ratio": 1.0}
    return {"D": dict(side, deception_drop=d_drop), "F": dict(side, deception_drop=f_drop),
            "eval5": False}


def test_deception_drop_exactly_80_percent_of_d_passes():
    # Full 1.0, D knockout 0.7: D drop is 0.30000000000000004 in floats, so 0.8 x D is
    # 0.24000000000000005 > 0.24. An F drop of exactly 0.24 must still pass.
    assert 0.8 * (1.0 - 0.7) > 0.24
    assert fcs.decide(_sides(1.0 - 0.7, 0.24))["verdict"] == "a"
    assert fcs.decide(_sides(1.0, 0.8))["verdict"] == "a"


def test_deception_drop_just_below_80_percent_of_d_fails():
    got = fcs.decide(_sides(1.0, 0.799))
    assert got["verdict"] == "b"
    assert got["conditions"][0]["passed"] is False


def test_80_percent_boundary_through_the_suite(tmp_path):
    # full 0.97, D knockout 0.00 -> D drop 0.97; F knockout 0.194 -> F drop 0.776 = 0.8 x 0.97.
    root, data = make_suite(tmp_path, over={"ko": {"F": {"": 0.194}}})
    _, decision = run(root, data)
    assert decision["conditions"][0]["passed"] is True
    root2, data2 = make_suite(tmp_path / "below", over={"ko": {"F": {"": 0.20}}})
    _, decision2 = run(root2, data2)
    assert decision2["conditions"][0]["passed"] is False


# ==============================================================================
# INCOMPLETE SUITES
# ==============================================================================

def test_missing_rule_cell_is_reported_and_leaves_the_verdict_undecided(tmp_path):
    root, data = make_suite(tmp_path, skip_cells=("F/far_honest",))
    md, decision = run(root, data)
    assert decision["verdict"] is None
    assert "cell F x far_honest (knockout)" in decision["missing"]
    assert any("H test set" in m for m in decision["missing_inputs"])
    section = md.split("## Missing", 1)[1]
    assert "F x far_honest" in section
    assert "**Verdict: undecided.**" in md


def test_missing_delta_cell_is_reported_but_the_verdict_still_stands(tmp_path):
    root, data = make_suite(tmp_path, skip_cells=("D_and_F__leaf/far",))
    md, decision = run(root, data)
    assert decision["verdict"] == "a"
    assert "delta cell D_and_F__leaf x far" in decision["missing"]
    assert "D_and_F__leaf x far" in md.split("## Missing", 1)[1]


def test_empty_suite_directory_is_reported_not_crashed_on(tmp_path):
    root = tmp_path / "outputs" / "_suites" / "format-control-sdr-nls0.3"
    root.mkdir(parents=True)
    md, decision = run(str(root), str(tmp_path / "no_data"))
    assert decision["verdict"] is None
    assert "overlap.json" in decision["missing"]
    assert "cell D x sdr (knockout)" in decision["missing"]
    assert "## Missing" in md


def test_failed_condition_decides_b_even_when_another_input_is_missing(tmp_path):
    # Deception drop fails (F drop 0.37) and the F x far_honest cell is missing: (a) is
    # already impossible, so the verdict is (b) with the missing input still listed.
    root, data = make_suite(tmp_path, over={"ko": {"F": {"": 0.60}}},
                            skip_cells=("F/far_honest",))
    _, decision = run(root, data)
    assert decision["verdict"] == "b"
    assert any("H test set" in m for m in decision["missing_inputs"])


def test_kl_gate_still_decides_c_when_other_inputs_are_missing(tmp_path):
    root, data = make_suite(tmp_path, over={"kl": {"F": 0.9}}, skip_cells=("D/far_honest",))
    _, decision = run(root, data)
    assert decision["verdict"] == "c"


# ==============================================================================
# THE PAIRED TABLE: VARIANT ROWS, PAIRING, CONDITIONS
# ==============================================================================

def test_variant_cells_on_format_data_read_na_not_missing(tmp_path):
    root, data = make_suite(tmp_path)
    md, _ = run(root, data)
    table = md.split("### Honest-answer drop on the eval 2 variant rows", 1)[1].split("##", 1)[0]
    rows = [ln for ln in table.splitlines() if ln.startswith("| F |")]
    assert rows and rows[0].count("n/a (condition is nopressure)") == 2
    assert "missing" not in table


def test_unpaired_far_format_data_is_flagged_from_source_counts(tmp_path):
    root, data = make_suite(tmp_path)          # FAR: test 8 deceptive / 492 honest split
    md, decision = run(root, data)
    assert decision["pairing"]["paired"] is False
    assert decision["pairing"]["test_honest_share"] == pytest.approx(492 / 500)
    assert any(c.startswith("F trained on 99% honest-split instances") for c in decision["caveats"])
    assert "NOT paired: 98% honest-split instances" in md
    assert "unpaired (disjoint instances)" in md


def test_paired_sdr_format_data_is_flagged_from_source_counts(tmp_path):
    counts = {"train": {"deceptive_split": 106, "honest_split": 44},
              "validation": {"deceptive_split": 96, "honest_split": 54},
              "test": {"deceptive_split": 520, "honest_split": 0}}
    root, data = make_suite(tmp_path, task="sdr", over={"source_counts": counts})
    md, decision = run(root, data)
    assert decision["pairing"]["paired"] is True
    assert "paired with D data by instance" in md
    assert not any("NOT instance-paired" in c for c in decision["caveats"])
    assert any(c.startswith("F trained on 12% honest-split") for c in decision["caveats"])


def test_conditions_are_read_from_each_run(tmp_path):
    root, data = make_suite(tmp_path)
    md, decision = run(root, data)
    assert decision["conditions_of_runs"] == {"D": "deceptive", "H": "honest",
                                              "F": "nopressure"}
    assert "condition `nopressure`" in md


def test_standing_caveats_are_emitted(tmp_path):
    root, data = make_suite(tmp_path)
    _, decision = run(root, data)
    text = " ".join(decision["caveats"])
    assert "drift fix" in text
    assert "H column unpaired" in text
    assert "EVAL 5 absent" in text
    assert "heads-only" not in text
    assert "--deception-margin-loss 0.7" in text


def test_retuned_format_nls_is_caveated(tmp_path):
    root, data = make_suite(tmp_path, f_nls=0.4)
    _, decision = run(root, data)
    assert any(c.startswith("F at NLS 0.4") for c in decision["caveats"])


# ==============================================================================
# OVERLAP, DELTAS, FLIP AUDIT
# ==============================================================================

def test_overlap_and_delta_rows_with_head_primary(tmp_path):
    root, data = make_suite(tmp_path)
    md, _ = run(root, data)
    ov = md.split("## Overlap", 1)[1].split("##", 1)[0]
    assert "| D/F | 0.310 | 25 | 48 / 60 | 0.155 |" in ov
    deltas = md.split("## Delta cells", 1)[1].split("##", 1)[0]
    assert deltas.count("head (primary)") == 6 and deltas.count("| leaf |") == 6
    line = next(ln for ln in deltas.splitlines() if "`D - F`" in ln and "primary" in ln)
    assert "positional default; not separable" in line
    leaf = next(ln for ln in deltas.splitlines() if "`D - F`" in ln and "| leaf |" in ln)
    assert "| leaf | 10 |" in leaf        # {"active", "total"} counts read as active


def test_missing_overlap_and_flip_audit_are_reported(tmp_path):
    root, data = make_suite(tmp_path, overlap=False, flip=False)
    _, decision = run(root, data)
    assert {"overlap.json", "flip_audit.json"} <= set(decision["missing"])
    assert decision["verdict"] == "a"


# ==============================================================================
# COARSE SUITE
# ==============================================================================

def test_coarse_suite_reads_heads_only_knockouts_and_reports_them_at_head_level(tmp_path):
    root, data = make_suite(tmp_path, family="coarse", task="sdr",
                            over={"ko": {"F": {"": 0.60}}})
    md, decision = run(root, data)
    assert decision["family"] == "coarse"
    assert decision["inputs"]["F"]["knockout_acc"] == pytest.approx(0.60)  # from F_hko__leaf
    assert decision["verdict"] == "b"
    assert decision["missing"] == []
    assert any("heads-only" in c and "(expr) - m" in c for c in decision["caveats"])
    deltas = md.split("## Delta cells", 1)[1].split("##", 1)[0]
    assert deltas.count("head (composed at leaf)") == 6
    assert "primary" not in deltas
    line = next(ln for ln in deltas.splitlines() if "`D - F`" in ln)
    assert "positional default" in line
    ov = md.split("## Overlap", 1)[1].split("##", 1)[0]
    assert "n/a (heads only)" in ov


def test_coarse_missing_heads_only_cell_is_named(tmp_path):
    root, data = make_suite(tmp_path, family="coarse", task="sdr",
                            skip_cells=("D_hko__leaf/sdr",))
    _, decision = run(root, data)
    assert "cell D_hko__leaf x sdr (knockout)" in decision["missing"]
    assert decision["verdict"] is None


# ==============================================================================
# EVAL 5
# ==============================================================================

def make_eval5(tmp_path, ref_nll_ko=None, distinct_ko=None):
    """An eval 5 suite with D, H, F on two benchmark datasets."""
    ref_nll_ko = ref_nll_ko or {"D": 1.5, "H": 1.0, "F": 1.2}
    distinct_ko = distinct_ko or {"D": 0.5, "H": 0.6, "F": 0.6}
    d = str(tmp_path / "eval5_format-control-far")
    for r in ROLES:
        datasets = {}
        for name in ("sandbagging", "mask:known_facts"):
            datasets[name] = {
                "configs": {
                    "full": {"rates": {"deceptive": 1.0},
                             "coherence": {"ref_nll": 0.3, "distinct_n": 0.7}},
                    "knockout": {"rates": {"deceptive": 0.2},
                                 "coherence": {"ref_nll": ref_nll_ko[r],
                                               "distinct_n": distinct_ko[r]}}},
                "null": {"deceptive": {"p5": 0.05, "p50": 0.1}}}
        _dump(os.path.join(d, "cells", r, "far", "interchange", "benchmarks.json"),
              {"datasets": datasets})
    return d


def test_eval5_columns_appear_only_when_a_directory_is_given(tmp_path):
    root, data = make_suite(tmp_path)
    md, decision = run(root, data)
    assert "## Eval 5" not in md and "ref_nll" not in md
    assert decision["evaluated_on"] == "eval 2 alone"
    assert "evaluated on eval 2 alone until an eval 5 directory is given" in md

    e5 = make_eval5(tmp_path)
    md5, decision5 = run(root, data, eval5_dirs=[e5])
    assert "## Eval 5 benchmarks" in md5 and "ref_nll" in md5
    assert decision5["evaluated_on"] == "eval 2 + eval 5"
    cond = {c["name"]: c for c in decision5["conditions"]}
    assert cond["collateral"]["measure"] == "reference-NLL rise (eval 5)"
    assert cond["collateral"]["D"] == pytest.approx(1.2)      # 1.5 - 0.3
    assert cond["collateral"]["F"] == pytest.approx(0.9)
    assert decision5["verdict"] == "a"
    assert any(c.startswith("EVAL 5 present") for c in decision5["caveats"])


def test_eval5_reference_nll_rise_above_d_is_verdict_b(tmp_path):
    root, data = make_suite(tmp_path)
    e5 = make_eval5(tmp_path, ref_nll_ko={"D": 1.0, "H": 1.0, "F": 1.4})
    _, decision = run(root, data, eval5_dirs=[e5])
    assert decision["verdict"] == "b"


def test_eval5_distinct2_collapse_is_verdict_c(tmp_path):
    root, data = make_suite(tmp_path)
    e5 = make_eval5(tmp_path, distinct_ko={"D": 0.5, "H": 0.6, "F": 0.2})   # 0.2/0.7 < 0.5
    _, decision = run(root, data, eval5_dirs=[e5])
    assert decision["gate"]["distinct2_source"] == "eval 5 distinct_n"
    assert decision["verdict"] == "c"


# ==============================================================================
# THE SUITE MANIFEST'S CELL INDEX (ticket 04, 4e12a1d)
# ==============================================================================

def make_manifest(tmp_path, root, family="fine", task="far", moved=None, extra=()):
    """A suite_manifest.json whose per-suite `cells` index lists every planned cell,
    as fc_cells.py writes it; `moved` maps (circuit, dataset) -> a different path."""
    conds = {"": "deceptive", "_honest": "honest", "_nopressure": "nopressure"}
    cells = []
    for r in ROLES:
        for s, c in conds.items():
            d = task + s
            if family == "fine":
                cells.append({"circuit": r, "dataset": d, "condition": c,
                              "roles": ["faithfulness", "knockout"]})
            else:
                cells.append({"circuit": r, "dataset": d, "condition": c,
                              "roles": ["faithfulness"]})
                cells.append({"circuit": f"{r}_hko__leaf", "dataset": d, "condition": c,
                              "roles": ["knockout"]})
    for lab in DELTAS:
        for g in (("leaf", "head") if family == "fine" else ("leaf",)):
            label = f"{lab}__{g}" if family == "fine" else f"{lab}_hko__leaf"
            cells.append({"circuit": label, "dataset": task, "condition": "deceptive",
                          "roles": ["delta"]})
    cells += list(extra)
    for c in cells:
        c["path"] = (moved or {}).get((c["circuit"], c["dataset"]),
                                      f"cells/{c['circuit']}/{c['dataset']}/interchange")
    path = str(tmp_path / "suite_manifest.json")
    _dump(path, {"suites": {os.path.basename(root): {"family": family, "task": task,
                                                      "cells": cells}}})
    return path


def test_cells_are_read_from_the_manifest_index_path(tmp_path):
    root, data = make_suite(tmp_path, over={"ko": {"F": {"": 0.60}}})      # verdict (b)
    src = os.path.join(root, "cells", "F", "far", "interchange")
    dst = os.path.join(root, "cells", "F", "far", "interchange_moved")
    os.rename(src, dst)
    manifest = make_manifest(tmp_path, root,
                             moved={("F", "far"): "cells/F/far/interchange_moved"})
    _, guessed = run(root, data)
    assert "cell F x far (knockout)" in guessed["missing"]
    _, decision = run(root, data, manifest=manifest)
    assert "cell F x far (knockout)" not in decision["missing"]
    assert decision["inputs"]["F"]["knockout_acc"] == pytest.approx(0.60)
    assert decision["verdict"] == "b"


def test_dataset_conditions_come_from_the_manifest_index(tmp_path):
    root, data = make_suite(tmp_path)
    manifest = make_manifest(tmp_path, root)
    md, decision = run(root, data, manifest=manifest)
    assert decision["datasets"]["F"] == {"dir": "far_nopressure", "condition": "nopressure",
                                         "condition_source": "manifest",
                                         "full_acc": pytest.approx(0.96)}
    assert "`far_honest` (condition `honest`, from the manifest)" in md


def test_an_indexed_cell_outside_the_grid_is_still_reported_missing(tmp_path):
    root, data = make_suite(tmp_path)
    extra = [{"circuit": "D_or_F__head", "dataset": "far", "condition": "deceptive",
              "roles": ["delta"]}]
    manifest = make_manifest(tmp_path, root, extra=extra)
    _, decision = run(root, data, manifest=manifest)
    assert "cell D_or_F__head x far (delta)" in decision["missing"]
    assert decision["verdict"] == "a"


REAL_MANIFEST = os.path.join(REPO, "outputs", "_launch_format_control", "suite_manifest.json")


@pytest.mark.skipif(not os.path.exists(REAL_MANIFEST), reason="no launcher manifest")
def test_the_writers_grid_is_exactly_the_launchers_cell_index():
    with open(REAL_MANIFEST) as f:
        suites = json.load(f)["suites"]
    assert suites
    for name, s in suites.items():
        indexed = {(c["circuit"], c["dataset"]) for c in s["cells"]}
        assert fcs.expected_cells(s["family"], s["task"]) == indexed, name


def test_a_manifest_without_this_suite_falls_back_to_the_grid(tmp_path):
    root, data = make_suite(tmp_path)
    manifest = str(tmp_path / "other_manifest.json")
    _dump(manifest, {"suites": {"format-control-sdr-nls0.3": {"cells": []}}})
    _, decision = run(root, data, manifest=manifest)
    assert decision["verdict"] == "a"
    assert any("not in the manifest" in m for m in decision["missing"])


# ==============================================================================
# CLI
# ==============================================================================

def test_cli_writes_both_files(tmp_path):
    root, data = make_suite(tmp_path)
    e5 = make_eval5(tmp_path)
    manifest = make_manifest(tmp_path, root)
    out = subprocess.run([sys.executable, os.path.join(REPO, "write_format_control_summary.py"),
                          root, "--data-dir", data, "--eval5-dir", e5, "--manifest", manifest],
                         cwd=REPO, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert "verdict (a)" in out.stdout
    with open(os.path.join(root, "decision.json")) as f:
        d = json.load(f)
    assert d["evaluated_on"] == "eval 2 + eval 5"
    assert d["manifest_indexed"] is True
    assert os.path.exists(os.path.join(root, "evaluation_summary.md"))
