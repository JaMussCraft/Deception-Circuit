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
    if knockout_text is None:
        return {"skipped": "--skip-wikitext was passed, so there are no prompts to continue"}
    full = "the film was released in the summer and earned praise from critics for its score"
    return {"examples": [{"index": i, "continuations": {"full": full + f" {i}",
                                                        "knockout": knockout_text + f" {i}"}}
                         for i in range(3)]}


def _variant(full, ko):
    return {"rows": {"full": {"accuracy": full, "n": 1000}, "circuit": {"accuracy": 0.5},
                     "knockout": {"accuracy": ko, "n": 1000}},
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


#: The real FAR F run's size_check.json (e2a1b2b), trimmed to the fields the writer reads.
FAR_SIZE_CHECK = {
    "compared": ["heads", "fine_units"],
    "gaps": {"heads": 0.7083333333333334, "fine_units": 1.3888888888888888},
    "out_of_tolerance": ["heads", "fine_units"], "tol": 0.25, "step": 0.1,
    "paired_nls": 0.3, "format_nls": 0.3, "retuned": False, "verdict": "retune",
    "next_nls": 0.4,
    "in_run_gate": {"kl_div": 0.1333, "misses": [], "passes": True},
    "retune": {"nls": 0.4, "format_counts": {"heads": 72, "fine_units": 10729},
               "gaps": {"heads": 0.5, "fine_units": 0.9736938925680647},
               "out_of_tolerance": ["heads", "fine_units"], "verdict": "refused",
               "in_run_gate": {"kl_div": 0.2144364150762558, "misses": ["kl_div"],
                               "passes": False}},
    "carried": "nls0.3",
}
SDR_SIZE_CHECK = {"compared": ["heads", "fine_units"],
                  "gaps": {"heads": 0.0, "fine_units": -0.12}, "out_of_tolerance": [],
                  "paired_nls": 0.3, "format_nls": 0.3, "retuned": False,
                  "verdict": "within_tolerance", "next_nls": None,
                  "in_run_gate": {"kl_div": 0.1, "misses": [], "passes": True}}


def make_suite(tmp_path, family="fine", task="far", over=None, skip_cells=(),
               f_nls=0.3, overlap=True, flip=True, size_check=None, side_kl=None):
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
    if size_check is not None:
        _dump(os.path.join(runs["F"], "size_check.json"), size_check)
    elif f_nls != 0.3:
        _dump(os.path.join(runs["F"], "size_check.json"),
              {"paired_nls": 0.3, "format_nls": f_nls, "retuned": True})
    datasets = {suffix: task + suffix for suffix in ("", "_honest", "_nopressure")}
    # Fine atomic circuits hold partial heads and MLP units; coarse atomic circuits
    # hold full heads plus every MLP unit (expanded masks); a heads-only `(X) - m`
    # cell holds full heads and no MLP unit (the real coarse suite's counts).
    circuits = [{"label": r, "kind": "atomic", "expr": None, "operands": {r: runs[r]},
                 "home_run_dir": runs[r],
                 "counts": ({"attention_heads": 40 + i, "attention_neurons": 3000 + i,
                             "mlp_hidden": 1000, "mlp_output": 500} if family == "fine" else
                            {"attention_heads": 40 + i, "attention_neurons": (40 + i) * 128,
                             "mlp_hidden": 458752, "mlp_output": 131072})}
                for i, r in enumerate(ROLES)]
    if family == "coarse":
        circuits += [{"label": f"{r}_hko__leaf", "kind": "leaf", "expr": f"({r}) - m",
                      "counts": {"attention_heads": 40 + i,
                                 "attention_neurons": (40 + i) * 128,
                                 "mlp_hidden": 0, "mlp_output": 0}}
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
    if side_kl is not None:
        # The retuned F's side job (ticket 03/04): its knockout cell on the D test set.
        _dump(os.path.join(root, "_side_F04", "cells", "F04", task, "interchange",
                           "knockout.json"),
              _knockout_json(p["full"][""], 0.0, (0.2, 0.7, 0.9), side_kl, None, "x"))
    _dump(os.path.join(root, "suite.json"),
          {"circuits": circuits, "tasks": tasks,
           "geometry": {"num_heads": 32, "head_dim": 128},
           "cli": {"null_alloc": "uniform", "knockout_granularity": "finest",
                   "n_random": 20, "knockout_null_count": 20}})
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
    # Default mode `variants`: only the spec's eval 2 variant rows enter the rule.
    cond = decision["conditions"][1]
    assert [r["row"] for r in cond["rows"]] == ["honest_instruction (D data)",
                                                 "no_pressure (D data)"]
    assert [r["row"] for r in cond["informational_rows"]] == ["H test set", "F test set"]


def test_weaker_format_knockout_is_verdict_b(tmp_path):
    root, data = make_suite(tmp_path, over={"ko": {"F": {"": 0.60}}})   # F drop 0.37
    md, decision = run(root, data)
    assert decision["verdict"] == "b"
    cond = {c["name"]: c for c in decision["conditions"]}
    assert cond["deception drop"]["passed"] is False
    assert cond["deception drop"]["F"] == pytest.approx(0.37)
    assert "Deception-specific machinery exists" in md


RULING = "orchestrator ruling 2026-10-13: spec rows only; researcher may flip"


def test_honest_rows_modes_disagree_when_only_a_test_set_row_fails(tmp_path):
    # F's knockout hurts honest answering on the H test set more than D's (0.55 > 0.45),
    # while F <= D on both eval 2 variant rows. `variants` (default, the spec's rows)
    # gives (a); `all` adds the H and F test sets to the rule and gives (b).
    root, data = make_suite(tmp_path, over={"ko": {"F": {"_honest": 0.40}}})
    md, decision = run(root, data)
    assert decision["honest_rows_mode"] == "variants"
    assert decision["verdict"] == "a"
    cond = {c["name"]: c for c in decision["conditions"]}["honest-answer drop"]
    assert {r["row"]: r["passed"] for r in cond["rows"]} == {
        "honest_instruction (D data)": True, "no_pressure (D data)": True}
    assert {r["row"]: r["passed"] for r in cond["informational_rows"]} == {
        "H test set": False, "F test set": True}
    assert "honest-answer rows: `variants`" in md and RULING in md
    assert any("in-distribution for F; not in the rule" in c for c in decision["caveats"])
    informational = [ln for ln in md.splitlines() if "H test set" in ln and "F <= D" in ln]
    assert informational and "informational" in informational[0]

    md_all, decision_all = run(root, data, honest_rows="all")
    assert decision_all["honest_rows_mode"] == "all"
    assert decision_all["verdict"] == "b"
    cond = {c["name"]: c for c in decision_all["conditions"]}["honest-answer drop"]
    assert {r["row"]: r["passed"] for r in cond["rows"]} == {
        "honest_instruction (D data)": True, "no_pressure (D data)": True,
        "H test set": False, "F test set": True}
    assert cond["informational_rows"] == []
    assert "honest-answer rows: `all`" in md_all
    assert not any("not in the rule" in c for c in decision_all["caveats"])


def test_honest_rows_mode_is_rejected_when_unknown(tmp_path):
    root, data = make_suite(tmp_path)
    with pytest.raises(ValueError):
        run(root, data, honest_rows="some")


def test_format_knockout_inside_its_null_is_verdict_b(tmp_path):
    root, data = make_suite(tmp_path, over={"null": {"F": (0.05, 0.5, 0.9)}})
    _, decision = run(root, data)
    cond = {c["name"]: c for c in decision["conditions"]}
    assert cond["outside nulls"]["D"] is True and cond["outside nulls"]["F"] is False
    assert decision["verdict"] == "b"


def test_format_knockout_above_the_kl_gate_is_verdict_c_with_the_spec_remedy(tmp_path):
    # D's knockout passes the gate (0.50) and F's fails it (0.70): the spec sentence.
    root, data = make_suite(tmp_path, over={"kl": {"D": 0.50, "F": 0.70}})
    md, decision = run(root, data)
    assert decision["gate"]["kl_fails"] is True
    assert decision["gate"]["d_fails_kl_gate"] is False
    assert decision["verdict"] == "c"
    assert "retrain the Format Circuit at a lower NLS" in decision["sentence"]
    assert "retrain the Format Circuit at a lower NLS" in md
    assert decision["spec_sentence"] == decision["sentence"]


BOTH_FAIL = ("both D and F knockouts fail the gate at this NLS; the comparison is "
             "incoherent on both sides; researcher decides")


def test_verdict_c_with_d_also_failing_the_gate_replaces_the_remedy(tmp_path):
    # D is above the gate too, so "F's KL <= D's" passes and only the gate stops (a).
    # The spec's remedy (retrain F at a lower NLS) would enlarge F, so it is replaced.
    root, data = make_suite(tmp_path, over={"kl": {"D": 0.80, "H": 0.69, "F": 0.70}})
    md, decision = run(root, data)
    assert all(c["passed"] for c in decision["conditions"])
    assert decision["verdict"] == "c"
    assert decision["gate"]["d_fails_kl_gate"] is True
    s = decision["sentence"]
    assert BOTH_FAIL in s
    assert "D 0.800" in s and "H 0.690" in s and "F 0.700" in s
    assert "a lower NLS gives a larger circuit" in s
    assert "Nothing is launched" in s
    assert "retrain the Format Circuit at a lower NLS, never to reinterpret" not in s
    assert "retrain the Format Circuit at a lower NLS" in decision["spec_sentence"]
    assert BOTH_FAIL in md


UNREGISTERED = "not pre-registered; orchestrator choice 2026-10-13, researcher to confirm"


def test_rule_choices_that_were_not_pre_registered_are_labelled_as_such(tmp_path):
    root, data = make_suite(tmp_path)
    md, decision = run(root, data)
    for key in ("c_before_a", "distinct2"):
        assert UNREGISTERED in decision["decisions_taken"][key], key
    assert UNREGISTERED in decision["gate"]["distinct2_frac_status"]
    assert UNREGISTERED in decision["rule_order"][0]
    decided = md.split("## Decisions taken in applying the rule", 1)[1].split("##", 1)[0]
    assert decided.count(UNREGISTERED) == 2
    gate_line = next(ln for ln in md.splitlines() if ln.startswith("(c) gate on F's knockout"))
    assert UNREGISTERED in gate_line
    order_line = next(ln for ln in md.splitlines() if ln.startswith("Rule order:"))
    assert UNREGISTERED in order_line


OVERSIZED = ("F is already oversized (+71% heads); the spec's remedy (lower NLS) enlarges it "
             "further (higher NLS = smaller circuit); the one allowed retune toward smaller "
             "(NLS 0.4) also failed the in-run gate (KL 0.214)")


def test_verdict_c_with_an_oversized_format_circuit_replaces_the_remedy(tmp_path):
    # The real FAR case: F fails the gate (D passes), F is +71% heads, the NLS 0.4
    # retune failed its in-run gate, and the retuned F's side job knocks out at KL 2.317.
    root, data = make_suite(tmp_path, over={"kl": {"F": 0.9}}, size_check=FAR_SIZE_CHECK,
                            side_kl=2.317)
    md, decision = run(root, data)
    assert decision["verdict"] == "c"
    assert decision["gate"]["d_fails_kl_gate"] is False
    want = OVERSIZED + " and its side-job knockout KL is 2.317; researcher decides"
    assert want in decision["sentence"]
    assert "retrain the Format Circuit at a lower NLS, never to reinterpret" not in \
        decision["sentence"]
    assert "retrain the Format Circuit at a lower NLS" in decision["spec_sentence"]
    assert decision["gate"]["side_kl"] == pytest.approx(2.317)
    assert want in md


def test_oversized_remedy_omits_the_side_job_clause_without_its_cell(tmp_path):
    root, data = make_suite(tmp_path, over={"kl": {"F": 0.9}}, size_check=FAR_SIZE_CHECK)
    _, decision = run(root, data)
    assert OVERSIZED + "; researcher decides" in decision["sentence"]
    assert "side-job" not in decision["sentence"]


def test_size_within_tolerance_keeps_the_spec_remedy(tmp_path):
    root, data = make_suite(tmp_path, task="sdr", over={"kl": {"F": 0.9}},
                            size_check=SDR_SIZE_CHECK)
    _, decision = run(root, data)
    assert decision["verdict"] == "c"
    assert decision["sentence"] == decision["spec_sentence"]


def test_gate_line_prints_every_circuits_kl_when_c_fires(tmp_path):
    root, data = make_suite(tmp_path, over={"kl": {"D": 0.327, "H": 0.70, "F": 0.9}})
    md, decision = run(root, data)
    line = next(ln for ln in md.splitlines() if ln.startswith("(c) gate on F's knockout"))
    assert ("Wikitext KL/token of every knockout: D 0.327 (passes), H 0.700 (FAILS), "
            "F 0.900 (FAILS)") in line
    assert decision["gate"]["h_kl"] == pytest.approx(0.70)
    root2, data2 = make_suite(tmp_path / "a", over={"kl": {"H": 0.70}})     # verdict (a)
    md2, _ = run(root2, data2)
    line2 = next(ln for ln in md2.splitlines() if ln.startswith("(c) gate on F's knockout"))
    assert "of every knockout" not in line2


def test_leaf_positional_defaults_show_beside_primary_head_rows(tmp_path):
    root, data = make_suite(tmp_path)
    path = os.path.join(root, "flip_audit.json")
    with open(path) as f:
        audit = json.load(f)
    audit["cells"] = [c for c in audit["cells"] if not c["circuit"].startswith("D_minus_F")]
    audit["cells"] += [
        {"circuit": "D_minus_F__head", "task": "far", "headline": {"separable": True},
         "positional": {"verdict": "content-driven flip"}},
        {"circuit": "D_minus_F__leaf", "task": "far", "headline": {"separable": True},
         "positional": {"verdict": "positional default"}}]
    _dump(path, audit)
    md, _ = run(root, data)
    deltas = md.split("## Delta cells", 1)[1].split("##", 1)[0]
    head = next(ln for ln in deltas.splitlines() if "`D - F`" in ln and "head" in ln)
    leaf = next(ln for ln in deltas.splitlines() if "`D - F`" in ln and "| leaf |" in ln)
    assert "head (primary)" in head and "content-driven flip; separable" in head
    assert "positional default; separable" in leaf


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
    # Under `all`, the F x far_honest cell is a rule input (the H test set row).
    root, data = make_suite(tmp_path, skip_cells=("F/far_honest",))
    md, decision = run(root, data, honest_rows="all")
    assert decision["verdict"] is None
    assert "cell F x far_honest (knockout)" in decision["missing"]
    assert any("H test set" in m for m in decision["missing_inputs"])
    section = md.split("## Missing", 1)[1]
    assert "F x far_honest" in section
    assert "**Verdict: undecided.**" in md
    # Under the default `variants`, the same cell is informational only.
    _, decision_v = run(root, data)
    assert decision_v["verdict"] == "a"
    assert "cell F x far_honest (knockout)" in decision_v["missing"]


def test_missing_d_data_knockout_leaves_the_verdict_undecided(tmp_path):
    root, data = make_suite(tmp_path, skip_cells=("F/far",))
    _, decision = run(root, data)
    assert decision["verdict"] is None
    assert "F deception drop" in decision["missing_inputs"]


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
    _, decision = run(root, data, honest_rows="all")
    assert decision["verdict"] == "b"
    assert any("H test set" in m for m in decision["missing_inputs"])


def test_kl_gate_still_decides_c_when_other_inputs_are_missing(tmp_path):
    root, data = make_suite(tmp_path, over={"kl": {"F": 0.9}}, skip_cells=("D/far_honest",))
    _, decision = run(root, data, honest_rows="all")
    assert decision["verdict"] == "c"


def test_unassessed_kl_gate_leaves_the_verdict_undecided(tmp_path):
    # With eval 5 given, collateral is the ref-NLL rise, so F's missing wikitext KL used
    # to touch only the gate; an (a) must not be issued with the gate unassessed.
    root, data = make_suite(tmp_path, over={"kl": {"F": None}})
    _, decision = run(root, data, eval5_dirs=[make_eval5(tmp_path)])
    assert decision["gate"]["kl_fails"] is None
    assert decision["verdict"] is None
    assert "F wikitext KL" in decision["missing_inputs"]


def test_unassessed_distinct2_leaves_the_verdict_undecided(tmp_path):
    root, data = make_suite(tmp_path, over={"gen": {"F": None}})       # no generations
    md, decision = run(root, data)
    assert decision["gate"]["degenerate"] is None
    assert decision["verdict"] is None
    assert any(m.startswith("F distinct-2") for m in decision["missing_inputs"])
    assert "**Verdict: undecided.**" in md


def test_unassessed_gate_is_undecided_even_when_a_condition_fails(tmp_path):
    # (c) pre-empts (b) as well as (a), so an unassessed gate cannot give (b) either.
    root, data = make_suite(tmp_path, over={"gen": {"F": None}, "ko": {"F": {"": 0.60}}})
    _, decision = run(root, data)
    assert decision["verdict"] is None


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
    assert decision["pairing"]["train_honest_share"] == pytest.approx(149 / 150)
    assert ("F trained on 99% honest-split instances (train 149/150); validation 100% "
            "(150/150), test 98% (492/500)") in " ".join(decision["caveats"])
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
    # The share is the TRAIN split's (44/150 = 29%), not all splits pooled (98/820 = 12%).
    assert decision["pairing"]["train_honest_share"] == pytest.approx(44 / 150)
    assert ("F trained on 29% honest-split instances (train 44/150); validation 36% "
            "(54/150), test 0% (0/520)") in " ".join(decision["caveats"])
    assert not any("12%" in c for c in decision["caveats"])


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

def make_eval5(tmp_path, ref_nll_ko=None, distinct_ko=None, name="eval5_format_fine",
               datasets=("sandbagging", "mask:known_facts"), ko_rate=None):
    """An eval 5 suite (ticket 06 layout) with D, H, F on some benchmark datasets.

    ref_nll_ko[role] is a float for every dataset, or {dataset: float};
    datasets is a tuple for every role, or {role: tuple}; ko_rate[role] is the
    knockout's deception rate (the full model's is 1.0)."""
    ref_nll_ko = ref_nll_ko or {"D": 1.5, "H": 1.0, "F": 1.2}
    distinct_ko = distinct_ko or {"D": 0.5, "H": 0.6, "F": 0.6}
    ko_rate = ko_rate or {"D": 0.2, "H": 0.2, "F": 0.2}
    d = str(tmp_path / name)
    for r in ROLES:
        names = datasets[r] if isinstance(datasets, dict) else datasets
        out = {}
        for ds in names:
            ko = ref_nll_ko[r][ds] if isinstance(ref_nll_ko[r], dict) else ref_nll_ko[r]
            out[ds] = {
                "configs": {
                    "full": {"rates": {"deceptive": 1.0},
                             "coherence": {"ref_nll": 0.3, "distinct_n": 0.7}},
                    "knockout": {"rates": {"deceptive": ko_rate[r]},
                                 "coherence": {"ref_nll": ko, "distinct_n": distinct_ko[r]}}},
                "null": {"deceptive": {"p5": 0.05, "p50": 0.1}}}
        _dump(os.path.join(d, "cells", r, "far", "interchange", "benchmarks.json"),
              {"datasets": out})
    return d


def test_eval5_collateral_compares_only_datasets_both_circuits_have(tmp_path):
    # D has one more dataset than F, with a large ref-NLL rise (4.7). Pooled, D's mean
    # rise would be (1.2 + 1.2 + 4.7) / 3 = 2.37 and F's 1.4 would pass (a). Over the
    # two shared datasets D's rise is 1.2, so F's 1.4 fails: (b).
    root, data = make_suite(tmp_path)
    e5 = make_eval5(tmp_path,
                    ref_nll_ko={"D": {"sandbagging": 1.5, "mask:known_facts": 1.5,
                                      "lb:convincing-game": 5.0},
                                "H": 1.0, "F": 1.7},
                    datasets={"D": ("sandbagging", "mask:known_facts", "lb:convincing-game"),
                              "H": ("sandbagging",),
                              "F": ("sandbagging", "mask:known_facts")})
    md, decision = run(root, data, eval5_dirs=[e5])
    cond = {c["name"]: c for c in decision["conditions"]}["collateral"]
    assert cond["D"] == pytest.approx(1.2)
    assert cond["F"] == pytest.approx(1.4)
    assert cond["datasets"] == ["mask:known_facts", "sandbagging"]
    assert cond["excluded"] == {"D": ["lb:convincing-game"], "F": []}
    assert decision["verdict"] == "b"
    assert "lb:convincing-game" in md.split("## Eval 5 benchmarks", 1)[1].split("##", 1)[0]
    assert "excluded from the comparison (not shared by D and F): D lb:convincing-game" in md


def test_eval5_without_shared_datasets_leaves_collateral_missing(tmp_path):
    root, data = make_suite(tmp_path)
    e5 = make_eval5(tmp_path, datasets={"D": ("sandbagging",), "H": ("sandbagging",),
                                        "F": ("mask:known_facts",)})
    _, decision = run(root, data, eval5_dirs=[e5])
    assert decision["verdict"] is None
    assert any("reference-NLL rise" in m for m in decision["missing_inputs"])


def test_two_eval5_groups_are_merged(tmp_path):
    # ticket 06 writes the sm and lb benchmark groups as two suites; both are passed.
    root, data = make_suite(tmp_path)
    sm = make_eval5(tmp_path, name="eval5_format_fine",
                    datasets=("sandbagging", "mask:known_facts"))
    lb = make_eval5(tmp_path, name="eval5_format_fine_lb",
                    ref_nll_ko={"D": 2.3, "H": 1.0, "F": 0.3},
                    datasets=("lb:instructed-deception", "lb:convincing-game"))
    md, decision = run(root, data, eval5_dirs=[sm, lb])
    assert decision["eval5_dirs"] == [sm, lb]
    cond = {c["name"]: c for c in decision["conditions"]}["collateral"]
    assert cond["datasets"] == ["lb:convincing-game", "lb:instructed-deception",
                                "mask:known_facts", "sandbagging"]
    assert cond["D"] == pytest.approx((1.2 + 1.2 + 2.0 + 2.0) / 4)
    assert cond["F"] == pytest.approx((0.9 + 0.9 + 0.0 + 0.0) / 4)
    table = md.split("## Eval 5 benchmarks", 1)[1].split("##", 1)[0]
    for ds in ("sandbagging", "mask:known_facts", "lb:instructed-deception",
               "lb:convincing-game"):
        assert f"| F | {ds} |" in table


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
# DIAGNOSTIC CAVEATS (real-suite round; none changes the rule)
# ==============================================================================

SATURATED = ("atomic knockouts saturate, so the eval 2 deception-drop condition is "
             "trivially satisfied and cannot tell D from F; the rule still evaluates it on "
             "eval 2 (eval 5's deception drop, when given, is informational and not in the "
             "rule)")
EVAL2_CHOICE = "not pre-registered; orchestrator choice 2026-10-15, researcher to confirm"


def test_saturated_knockouts_on_d_data_are_caveated(tmp_path):
    # The real coarse SDR suite: D 0.002, F 0.000 on D data.
    root, data = make_suite(tmp_path, over={"ko": {"D": {"": 0.002}, "F": {"": 0.0}}})
    md, decision = run(root, data)
    assert decision["diagnostics"]["saturated"] is True
    assert any(SATURATED in c for c in decision["caveats"])
    assert SATURATED in md
    assert "eval 5 is the discriminating comparison" not in md
    assert decision["verdict"] == "a"                      # the rule is unchanged


def test_eval2_reading_of_deception_drop_and_nulls_is_recorded_as_a_choice(tmp_path):
    root, data = make_suite(tmp_path)
    md, decision = run(root, data, eval5_dirs=[make_eval5(tmp_path)])
    text = decision["decisions_taken"]["eval2_conditions"]
    assert "deception-drop and outside-null conditions are evaluated on eval 2" in text
    assert "even when --eval5-dir is given" in text
    assert EVAL2_CHOICE in text
    decided = md.split("## Decisions taken in applying the rule", 1)[1].split("##", 1)[0]
    assert EVAL2_CHOICE in decided


def test_eval5_deception_drop_is_an_informational_row_beside_the_rules_row(tmp_path):
    # Full-model deception rate 1.0; knockout rates D 0.10, F 0.40 on both shared
    # datasets -> eval 5 drops D 0.900, F 0.600 (F < 0.8 x D), yet the verdict stays
    # the eval 2 rule's (a): the row is informational.
    root, data = make_suite(tmp_path)
    e5 = make_eval5(tmp_path, ko_rate={"D": 0.10, "H": 0.2, "F": 0.40})
    md, decision = run(root, data, eval5_dirs=[e5])
    info = decision["eval5_deception_drop"]
    assert info["D"] == pytest.approx(0.9) and info["F"] == pytest.approx(0.6)
    assert info["datasets"] == ["mask:known_facts", "sandbagging"]
    assert info["in_rule"] is False
    assert decision["verdict"] == "a"
    rows = md.split("| condition | rule | D | F | result |", 1)[1].split("\n\n", 1)[0]
    lines = rows.splitlines()
    i = next(k for k, ln in enumerate(lines) if ln.startswith("| deception drop |"))
    assert "deception drop, eval 5 (informational: not in the rule)" in lines[i + 1]
    assert "| 0.900 | 0.600 |" in lines[i + 1]


def test_no_eval5_deception_row_without_an_eval5_directory(tmp_path):
    root, data = make_suite(tmp_path)
    md, decision = run(root, data)
    assert decision["eval5_deception_drop"] is None
    assert "deception drop, eval 5" not in md


def test_unsaturated_knockouts_are_not_caveated(tmp_path):
    root, data = make_suite(tmp_path)                      # F 0.10 on D data
    _, decision = run(root, data)
    assert decision["diagnostics"]["saturated"] is False
    assert not any(SATURATED in c for c in decision["caveats"])


#: The real coarse SDR rows: honest-answer drops 0.530 / 0.519 / 0.519 (honest_instruction)
#: and 0.560 / 0.535 / 0.534 (no_pressure) for D / H / F, full model 0.234 / 0.228, n=1000.
COARSE_ROWS = {"D": {"honest_instruction": (0.234, 0.764), "no_pressure": (0.228, 0.788)},
               "H": {"honest_instruction": (0.234, 0.753), "no_pressure": (0.228, 0.763)},
               "F": {"honest_instruction": (0.234, 0.753), "no_pressure": (0.228, 0.762)}}


def test_rule_rows_within_binomial_error_are_caveated_non_discriminating(tmp_path):
    root, data = make_suite(tmp_path, over={"variants": COARSE_ROWS})
    md, decision = run(root, data)
    rows = {r["row"]: r for r in decision["diagnostics"]["honest_rows"]}
    hi, nopress = rows["honest_instruction (D data)"], rows["no_pressure (D data)"]
    # honest_instruction: |F - D| = 0.011, SE of the knockout-accuracy difference
    # sqrt(.764*.236/1000 + .753*.247/1000) = 0.0191; D, H, F within 0.011 of each other.
    assert hi["abs_f_minus_d"] == pytest.approx(0.011)
    assert hi["se"] == pytest.approx(0.0191, abs=1e-4)
    assert hi["non_discriminating"] is True
    # no_pressure: |F - D| = 0.026 > SE 0.0187: the criterion does not flag it.
    assert nopress["abs_f_minus_d"] == pytest.approx(0.026)
    assert nopress["non_discriminating"] is False
    cav = next(c for c in decision["caveats"] if "non-discriminating" in c)
    assert cav.startswith("variant rows read the ablation source; condition "
                          "non-discriminating at n=1000")
    assert "honest_instruction (D data)" in cav and "no_pressure (D data)" not in cav
    assert decision["verdict"] == "a"                      # the rule is unchanged


def test_separated_rule_rows_are_not_caveated(tmp_path):
    root, data = make_suite(tmp_path)          # drops 0.755 / 0.194 / 0.394: far apart
    _, decision = run(root, data)
    assert not any(r["non_discriminating"] for r in decision["diagnostics"]["honest_rows"])
    assert not any("non-discriminating" in c for c in decision["caveats"])


def test_failed_retune_is_caveated_from_size_check(tmp_path):
    root, data = make_suite(tmp_path, size_check=FAR_SIZE_CHECK)
    md, decision = run(root, data)
    want = ("F oversized at NLS 0.3 (+71% heads, +139% fine units); retune to 0.4 failed "
            "the in-run gate (KL 0.214, misses kl_div; still +50% heads, +97% fine units); "
            "carried nls0.3")
    assert any(want in c for c in decision["caveats"])
    assert want in md
    assert decision["size_check"]["verdict"] == "retune"


def test_size_within_tolerance_has_no_retune_caveat(tmp_path):
    root, data = make_suite(tmp_path, task="sdr", size_check=SDR_SIZE_CHECK)
    _, decision = run(root, data)
    assert not any("oversized" in c or "retune to" in c for c in decision["caveats"])


def test_null_sampling_is_stated_for_fine_cells(tmp_path):
    root, data = make_suite(tmp_path)
    md, decision = run(root, data)
    ns = decision["null_sampling"]
    assert ns["unit"] == "fine units" and ns["alloc"] == "uniform" and ns["n"] == 20
    header = md.split("## Paired table", 1)[1].split("###", 1)[0]
    assert "Null:" in header and "fine units" in header and "layer by layer" in header


def test_null_sampling_is_whole_heads_for_heads_only_cells(tmp_path):
    root, data = make_suite(tmp_path, family="coarse", task="sdr")
    md, decision = run(root, data)
    assert decision["null_sampling"]["unit"] == "whole heads"
    header = md.split("## Paired table", 1)[1].split("###", 1)[0]
    assert "whole heads" in header and "no MLP units" in header


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
              "roles": ["knockout"]}]
    manifest = make_manifest(tmp_path, root, extra=extra)
    _, decision = run(root, data, manifest=manifest)
    assert "cell D_or_F__head x far (knockout)" in decision["missing"]
    assert decision["verdict"] == "a"


def test_an_indexed_extra_delta_becomes_a_delta_row(tmp_path):
    """A suite's opt-in extra_deltas (fc_cells.py) reach the delta table through the
    manifest's cells index (role `delta`), without a hardcoded label."""
    root, data = make_suite(tmp_path)
    extra = [{"circuit": f"D_or_F__{g}", "dataset": "far", "condition": "deceptive",
              "roles": ["delta"]} for g in ("leaf", "head")]
    manifest = make_manifest(tmp_path, root, extra=extra)
    md, decision = run(root, data, manifest=manifest)
    assert "delta cell D_or_F__head x far" in decision["missing"]
    assert "delta cell D_or_F__leaf x far" in decision["missing"]
    deltas = md.split("## Delta cells", 1)[1].split("##", 1)[0]
    rows = [ln for ln in deltas.splitlines() if ln.startswith("| D_or_F |")]
    assert len(rows) == 2 and "`D | F`" in rows[0] and "head (primary)" in rows[0]
    assert "| leaf |" in rows[1]
    assert decision["verdict"] == "a"


def test_coarse_extra_delta_rows_read_their_cell_and_expression(tmp_path):
    root, data = make_suite(tmp_path, family="coarse", task="sdr")
    extra = [{"circuit": f"{b}_hko__leaf", "dataset": "sdr", "condition": "deceptive",
              "roles": ["delta"]} for b in ("D_and_H_minus_F", "D_and_H_and_F")]
    manifest = make_manifest(tmp_path, root, family="coarse", task="sdr", extra=extra)
    # The first extra cell ran; the second did not.
    _dump(os.path.join(root, "cells", "D_and_H_minus_F_hko__leaf", "sdr", "interchange",
                       "knockout.json"),
          _knockout_json(DEFAULTS["full"][""], 0.7, (0.6, 0.8, 0.9), 0.2, None, "x"))
    with open(os.path.join(root, "suite.json")) as f:
        suite = json.load(f)
    suite["circuits"].append({"label": "D_and_H_minus_F_hko__leaf", "kind": "composed",
                              "expr": "(((D & H) \\ F) \\ m)",
                              "counts": {"attention_heads": {"active": 17, "total": 1024}}})
    _dump(os.path.join(root, "suite.json"), suite)
    md, decision = run(root, data, manifest=manifest)
    assert decision["missing"] == ["delta cell D_and_H_and_F_hko__leaf x sdr"]
    deltas = md.split("## Delta cells", 1)[1].split("##", 1)[0]
    assert deltas.count("head (composed at leaf)") == 8
    line = next(ln for ln in deltas.splitlines() if ln.startswith("| D_and_H_minus_F |"))
    assert "`(D & H) - F`" in line and "| 17 |" in line and "0.700" in line
    line = next(ln for ln in deltas.splitlines() if ln.startswith("| D_and_H_and_F |"))
    assert "`D & H & F`" in line and "missing" in line


REAL_MANIFEST = os.path.join(REPO, "outputs", "_launch_format_control", "suite_manifest.json")


@pytest.mark.skipif(not os.path.exists(REAL_MANIFEST), reason="no launcher manifest")
def test_the_writers_grid_is_exactly_the_launchers_cell_index():
    with open(REAL_MANIFEST) as f:
        suites = json.load(f)["suites"]
    assert suites
    for name, s in suites.items():
        indexed = {(c["circuit"], c["dataset"]) for c in s["cells"]}
        index = {(c["circuit"], c["dataset"]): c for c in s["cells"]}
        assert fcs.expected_cells(s["family"], s["task"], index) == indexed, name


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
                          root, "--data-dir", data, "--eval5-dir", e5, "--manifest", manifest,
                          "--honest-rows", "all"],
                         cwd=REPO, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert "verdict (a)" in out.stdout
    with open(os.path.join(root, "decision.json")) as f:
        d = json.load(f)
    assert d["evaluated_on"] == "eval 2 + eval 5"
    assert d["manifest_indexed"] is True
    assert d["honest_rows_mode"] == "all"
    assert os.path.exists(os.path.join(root, "evaluation_summary.md"))
