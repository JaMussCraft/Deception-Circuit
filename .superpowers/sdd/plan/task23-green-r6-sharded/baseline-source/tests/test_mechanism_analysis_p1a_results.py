"""Ticket 03 of mechanism-analysis: the phase-1A results builder in outputs/_launch_mechanism_analysis/.

Seams: the pre-registered R-A1 reading (spec section 2.5, amended per R13), the per-cell numbers read from a
fetched knockout.json (task bank and, under mean, the variant-matched no-pressure bank of R19(2)/R21), and the
per-set rows (ser's set 6 = set 5 by R21; interchange values of sets 1-5 and 7 from ticket 06).
"""

import importlib
import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_mechanism_analysis")


def _mod(name):
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def p1a():
    return _mod("p1a_results")


# ---------------------------------------------------------------- R-A1 (spec 2.5): D-test KO acc (mean), no-pressure KO
# deceptive rate (zero). answer machinery 0.25-0.75 and >= 0.25; deception-specific <= 0.25 and <= 0.10; item carrier
# <= 0.25 and >= 0.75; partial or none otherwise.

@pytest.mark.parametrize("d_acc, np_rate, reading", [
    (0.50, 0.90, "answer machinery"),
    (0.25, 0.25, "answer machinery"),          # both band edges are inclusive
    (0.75, 0.30, "answer machinery"),
    (0.10, 0.05, "deception-specific"),
    (0.25, 0.10, "deception-specific"),
    (0.00, 0.99, "item carrier"),
    (0.20, 0.75, "item carrier"),
    (0.50, 0.10, "partial or none"),           # answer lost, but the no-pressure rows stay honest
    (0.10, 0.50, "partial or none"),           # between deception-specific and item carrier
    (0.90, 0.00, "partial or none"),           # the knockout barely moves deception
])
def test_ra1_reading_follows_the_preregistered_bands(p1a, d_acc, np_rate, reading):
    assert p1a.ra1_reading(d_acc, np_rate) == reading


def test_ra1_reading_needs_both_columns(p1a):
    assert p1a.ra1_reading(None, 0.5) is None
    assert p1a.ra1_reading(0.5, None) is None


# ---------------------------------------------------------------- one cell's numbers from its knockout.json

def _stat(mean, pct, z):
    return {"mean": mean, "percentile": pct, "z": z}


def _variant(full, ko, bank=None):
    out = {"headline": {"full_accuracy": full, "knockout_accuracy": ko, "full_minus_knockout": full - ko}}
    if bank is not None:
        out["mean_bank"] = bank
    return out


def _knockout_json(matched=True, ko_acc=0.42, np_task=0.31, np_matched=0.12):
    ko = {
        "ablation": "mean" if matched else "zero",
        "task": {
            "knockout": {"accuracy": ko_acc, "logit_diff": -0.3, "kl_div": 0.9, "exact_match": 0.43, "n": 1000},
            "flip_summary": {"n_flipped_honest": 577, "n_stayed_deceptive": 420, "n_other": 3},
            "null": {"n": 20, "stats": {
                "accuracy": _stat(0.80, 0.0, -3.1),       # separated
                "logit_diff": _stat(1.2, 5.0, -2.0),      # separated (both edges inclusive)
                "kl_div": _stat(0.3, 0.0, -1.5),          # z too small
                "exact_match": _stat(0.81, 10.0, -4.0),   # percentile too high
            }},
        },
        "wikitext": {"discovered": {"kl_per_token": 0.071, "ppl_ratio": 1.07},
                     "null": {"stats": {"kl_per_token": {"mean": 0.12, "percentile": 15.0}}}},
        "variants": {"no_pressure": _variant(0.0, np_task, {"bank": "task"} if matched else None),
                     "honest_instruction": _variant(0.006, 0.28, {"bank": "task"} if matched else None)},
    }
    if matched:
        ko["variants_matched_bank"] = {"no_pressure": _variant(
            0.0, np_matched, {"bank": "variant:no_pressure", "rows": 1000, "tokens": 123456})}
        ko["mean_banks"] = {"task": "task", "variants": {"no_pressure": "task"},
                            "variants_matched_bank": {"no_pressure": "variant:no_pressure"}}
    return ko


def test_cell_numbers_read_both_no_pressure_banks_under_mean(p1a):
    row = p1a.cell_numbers(_knockout_json(matched=True))
    assert row["ko_accuracy"] == 0.42
    assert row["n"] == 1000
    assert row["flipped_honest"] == 577
    assert row["null_mean_accuracy"] == 0.80
    assert row["separated"] == 2
    assert row["np_ko_rate_task_bank"] == 0.31
    assert row["np_ko_rate_matched_bank"] == 0.12
    assert row["np_full_rate"] == 0.0
    assert row["hi_ko_rate_task_bank"] == 0.28
    assert row["wikitext_kl_per_token"] == 0.071
    assert row["wikitext_null_mean_kl"] == 0.12
    assert row["matched_bank"] == {"bank": "variant:no_pressure", "rows": 1000, "tokens": 123456}


def _nums(p1a, **kw):
    matched = kw.pop("matched", True)
    return p1a.cell_numbers(_knockout_json(matched=matched, **kw))


def test_set_rows_read_ra1_from_mean_d_test_and_zero_no_pressure(p1a):
    numbers = {
        ("far", 3, "mean"): _nums(p1a, ko_acc=0.50, np_task=0.02, np_matched=0.04),
        ("far", 3, "zero"): _nums(p1a, matched=False, ko_acc=0.05, np_task=0.60),
    }
    ic = {("far", 3): {"ko_accuracy": 0.0, "np_ko_rate_task_bank": 0.995, "source": "ticket 06"}}
    (row,) = p1a.set_rows(numbers, ic, aliases={})
    assert (row["task"], row["set"]) == ("far", 3)
    assert row["d_test_ko_acc"] == {"mean": 0.50, "zero": 0.05, "interchange": 0.0}
    assert row["np_ko_rate"] == {"mean_task_bank": 0.02, "mean_matched_bank": 0.04, "zero": 0.60,
                                 "interchange": 0.995}
    assert row["ra1"] == "answer machinery"            # mean 0.50 with zero 0.60, not mean's own 0.02
    assert row["ra1_robustness"] == {"mean_task_bank": "partial or none", "mean_matched_bank": "partial or none"}
    assert row["interchange_source"] == "ticket 06"


def test_calibration_sets_get_no_ra1_reading(p1a):
    numbers = {("sdr", 1, "mean"): _nums(p1a, ko_acc=0.10, np_task=0.02)}
    (row,) = p1a.set_rows(numbers, {}, aliases={})
    assert row["calibration"] is True
    assert row["ra1"] is None
    assert row["d_test_ko_acc"]["zero"] is None


def test_an_aliased_set_repeats_its_twin_and_says_so(p1a):
    numbers = {("ser", 5, "mean"): _nums(p1a, ko_acc=0.20, np_task=0.5, np_matched=0.3),
               ("ser", 5, "zero"): _nums(p1a, matched=False, ko_acc=0.15, np_task=0.05)}
    ic = {("ser", 5): {"ko_accuracy": 0.228, "np_ko_rate_task_bank": 0.756, "source": "ticket 06"}}
    rows = p1a.set_rows(numbers, ic, aliases={("ser", 6): 5})
    six = next(r for r in rows if r["set"] == 6)
    assert six["same_as_set"] == 5
    assert six["d_test_ko_acc"] == {"mean": 0.20, "zero": 0.15, "interchange": 0.228}
    assert six["ra1"] == "deception-specific"
    assert [r["set"] for r in rows] == [5, 6]


CHAIN_LOG = """\
=== evaluate_chain: group 1 of 3 starts 2026-10-25 15:10:02
noise
=== evaluate_chain: group 1 of 3 exited 0 2026-10-25 16:05:32
=== evaluate_chain: group 2 of 3 starts 2026-10-25 16:05:32
=== evaluate_chain: group 2 of 3 exited 0 2026-10-25 16:30:02
=== evaluate_chain: group 3 of 3 starts 2026-10-25 16:30:02
"""


def test_chain_log_gives_minutes_and_exit_per_group(p1a):
    groups = p1a.chain_timings(CHAIN_LOG)
    assert groups == [
        {"group": 1, "of": 3, "minutes": 55.5, "exit": 0},
        {"group": 2, "of": 3, "minutes": 24.5, "exit": 0},
        {"group": 3, "of": 3, "minutes": None, "exit": None},      # started, never exited (walltime or still on)
    ]


# ---------------------------------------------------------------- phase-1B job files (spec 4, R11)

@pytest.fixture(scope="module")
def p1b():
    return _mod("p1b_jobs")


def _flag(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


@pytest.mark.parametrize("task", ["far", "sdr", "ser"])
def test_p1b_job_runs_the_seven_sweeps_and_the_lens_in_spec_order(p1b, task):
    cells = dict(p1b.cells(task))
    assert list(cells) == ["s1", "s2", "s2p", "s3", "s4", "s5", "s6", "lens", "lens_f"]
    d, h = p1b.RUNS[task]
    f = f"outputs/_launch_mechanism_v2/evals/standins/{task}_v2_nopressure"
    assert [_flag(cells[c], "--task-from") for c in cells] == [d, d, d, d, d, h, f, d, f]
    sweeps = [c for c in cells if c.startswith("s")]
    assert all("--knockout-completeness-sweep" in cells[c] for c in sweeps)
    assert [_flag(cells[c], "--knockout-counterfactual") for c in sweeps] == [
        None, "neutral_twin", "neutral_twin", "neutral_twin", None, None, None]
    assert _flag(cells["s2p"], "--knockout-positions") == "after=pressure_clause,exclude=readout"
    assert _flag(cells["s2p"], "--knockout-sweep-exclude") == "mlp.0.0"
    assert _flag(cells["s3"], "--knockout-positions") == "readout"
    assert _flag(cells["s4"], "--knockout-scheme") == "mean"
    assert _flag(cells["lens"], "--dla-conditions") == "pressure,neutral_twin"
    assert _flag(cells["lens_f"], "--dla-conditions") == "pressure"
    outs = [_flag(cells[c], "--output-dir") for c in cells]
    assert len(set(outs)) == len(outs) and all(o.startswith("outputs/_analyses/mechanism-analysis-p1/") for o in outs)
    # the selection sample: no seed or id filter on any 1B line (seed 0, n = 100 are the CLI defaults)
    assert not any(x in argv for argv in cells.values() for x in ("--seed", "--exclude-ids", "--include-ids"))


def test_p1b_lines_bind_u_at_leaf_with_the_six_runs(p1b):
    b = p1b.binding()
    assert _flag(b, "--expr") == "U=(Df|Hf|Ds|Hs|De|He)-m"
    assert _flag(b, "--compose-granularity") == "leaf"
    assert b.count("--circuit") == 7 and b.count("--reference") == 6
    text = p1b.batch_text("sdr")
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    assert len(lines) == 9 and all("U=(Df|Hf|Ds|Hs|De|He)-m" in ln for ln in lines)


def test_cell_numbers_without_a_matched_bank_leave_it_empty(p1a):
    row = p1a.cell_numbers(_knockout_json(matched=False))
    assert row["np_ko_rate_task_bank"] == 0.31
    assert row["np_ko_rate_matched_bank"] is None
    assert row["matched_bank"] is None
