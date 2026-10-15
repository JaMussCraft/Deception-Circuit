"""
EVAL 5 preparation for the format-control suites (ticket 06).

One benchmark suite per task family and benchmark group binds the deceptive
circuit D, its Honest Twin H and the Format Circuit F in ONE
`evaluate_circuit.py` invocation, so the three knockouts share one screen and
one judge cache. Nothing here submits a job.

Seams under test (the ticket's Testing Decisions plus the review round):
  * the command generator, a pure function (bindings, groups, coarse rewriting,
    and no writable path into the main checkout);
  * the worktree-local screen cache: seeding (A40 copies only) and the
    post-dry-run cache check (refuses unless --allow-rescreen with a reason);
  * the pre-flight gate on each F knockout's wikitext KL (pass, fail, missing,
    stale F, explicit recorded override);
  * `submit_eval5.sh`'s refusals and its record, with stub sbatch / evaluator;
  * the `result_summary.md` writer on a fixture suite with three circuits, and
    its grader caveats quoted from their source files.
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys

import pytest

LAUNCH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "outputs", "_launch_format_control")
MAIN_OUTPUTS = "/projects/beto/swong2/Alignment/Deception-Circuit/outputs/"

D_RUN = "/runs/far/nls0.3_noedge_A"
H_RUN = "/runs/far/nls0.3_honest_noedge_B"
F_RUN = "/runs/far/nls0.3_nopressure_noedge_C"
M_RUN = "/runs/sdr_coarse/_allmlp_nomb"
RUNS = {"D": D_RUN, "H": H_RUN, "F": F_RUN}
CACHE = "/cache/screens"


def _launch_module(name):
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def e5():
    return _launch_module("eval5_cmd")


def _flag_values(args, flag):
    """Every value following `flag` (a flag may take several values)."""
    out, i = [], 0
    while i < len(args):
        if args[i] == flag:
            j = i + 1
            vals = []
            while j < len(args) and not args[j].startswith("--"):
                vals.append(args[j])
                j += 1
            out.append(vals)
            i = j
        else:
            i += 1
    return out


# ==============================================================================
# THE COMMAND GENERATOR
# ==============================================================================

def test_fine_family_binds_D_H_F_in_one_invocation_on_the_D_task(e5):
    args = e5.eval5_args("far", "sm", RUNS)
    assert _flag_values(args, "--circuit") == [[f"D={D_RUN}"], [f"H={H_RUN}"], [f"F={F_RUN}"]]
    # One task, the deceptive one: without it the evaluator would default to
    # every circuit's own test set and run a 3 x 3 grid.
    assert _flag_values(args, "--task-from") == [[D_RUN]]
    assert "--expr" not in args


def test_settings_are_the_exploratory_waves(e5):
    args = e5.eval5_args("far", "sm", RUNS)
    assert _flag_values(args, "--evals") == [["benchmarks"]]
    assert _flag_values(args, "--ablation") == [["interchange"]]
    assert _flag_values(args, "--benchmark-n-per-dataset") == [["50"]]
    assert _flag_values(args, "--benchmark-n-random") == [["6"]]
    assert _flag_values(args, "--benchmark-screen-budget") == [["600"]]


def test_groups_select_the_benchmarks_and_the_output_directory(e5):
    sm = e5.eval5_args("sdr", "sm", RUNS)
    lb = e5.eval5_args("sdr", "lb", RUNS)
    assert _flag_values(sm, "--benchmarks") == [["sandbagging", "mask"]]
    assert _flag_values(lb, "--benchmarks") == [[
        "lb:instructed-deception", "lb:harm-pressure-knowledge-report", "lb:convincing-game"]]
    assert _flag_values(sm, "--output-dir") == [["outputs/eval5_format_sdr"]]
    assert _flag_values(lb, "--output-dir") == [["outputs/eval5_format_sdr_lb"]]


def test_screens_come_from_the_worktree_local_copy(e5):
    args = e5.eval5_args("far", "lb", RUNS)
    assert _flag_values(args, "--benchmark-screen-cache") == [[e5.LOCAL_SCREEN_CACHE]]
    assert e5.LOCAL_SCREEN_CACHE.startswith(e5.WORKTREE + os.sep)
    assert not e5.LOCAL_SCREEN_CACHE.startswith(MAIN_OUTPUTS)
    assert _flag_values(e5.eval5_args("far", "lb", RUNS, screen_cache=CACHE),
                        "--benchmark-screen-cache") == [[CACHE]]
    # read-only benchmark sources beside the main checkout
    assert _flag_values(args, "--benchmark-repo-root") == [["/projects/beto/swong2/Alignment"]]


@pytest.mark.parametrize("family", ["far", "sdr", "sdr_coarse"])
@pytest.mark.parametrize("group", ["sm", "lb"])
def test_no_path_in_the_command_is_writable_under_the_main_checkout(e5, family, group):
    """Only the read-only circuit run directories may sit under the main
    checkout's outputs/; the screen cache, output dir and logs may not."""
    runs = {r: MAIN_OUTPUTS + f"llama-8b-instruct_x/run_{r}" for r in ("D", "H", "F")}
    allmlp = MAIN_OUTPUTS + "llama-8b-instruct_sdr_coarse/_allmlp_nomb"
    allowed = set(runs.values()) | {allmlp}
    args = e5.eval5_args(family, group, runs, allmlp=allmlp)
    cmd = e5.sbatch_cmd(family, group, args, account="a", ceiling_min=100.0)
    for token in cmd:
        for piece in token.split("="):
            path = os.path.abspath(os.path.join(e5.WORKTREE, piece)) if piece else ""
            if path.startswith(MAIN_OUTPUTS):
                assert path in allowed, (token, path)


def test_coarse_family_knocks_out_heads_only_against_the_all_mlp_operand(e5):
    args = e5.eval5_args("sdr_coarse", "sm", RUNS, allmlp=M_RUN)
    assert _flag_values(args, "--circuit") == [
        [f"D={D_RUN}"], [f"H={H_RUN}"], [f"F={F_RUN}"], [f"m={M_RUN}"]]
    # Labels end in `_hko` so the cells are `<X>_hko__leaf`, which ticket 05's
    # eval 5 loader maps back to the roles D, H, F.
    assert _flag_values(args, "--expr") == [["D_hko=D - m"], ["H_hko=H - m"], ["F_hko=F - m"]]
    assert _flag_values(args, "--compose-granularity") == [["leaf"]]
    assert _flag_values(args, "--task-from") == [[D_RUN]]
    assert _flag_values(args, "--output-dir") == [["outputs/eval5_format_sdr_coarse"]]


def test_coarse_family_needs_the_all_mlp_operand(e5):
    with pytest.raises(ValueError, match="all-MLP"):
        e5.eval5_args("sdr_coarse", "sm", RUNS)


def test_unknown_family_or_group_is_refused(e5):
    with pytest.raises(ValueError, match="family"):
        e5.eval5_args("ser", "sm", RUNS)
    with pytest.raises(ValueError, match="group"):
        e5.eval5_args("far", "xx", RUNS)


def test_a_missing_format_circuit_is_refused_by_name(e5):
    with pytest.raises(ValueError, match="F run directory"):
        e5.eval5_args("far", "sm", dict(RUNS, F=None))


# ==============================================================================
# THE WORKTREE-LOCAL SCREEN CACHE
# ==============================================================================

def _sidecar(directory, stem, device, payload=b"pickle"):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, stem + ".json"), "w") as f:
        json.dump({"dataset": "x", "device": device, "_stamp": {"device": device}}, f)
    with open(os.path.join(directory, stem + ".pt"), "wb") as f:
        f.write(payload)


def test_group_datasets_match_what_the_evaluator_expands(e5):
    # the committed stand-in dry-run logs list what `--benchmarks` expands to
    for group, family in (("sm", "far"), ("lb", "far")):
        with open(os.path.join(LAUNCH, "dryrun_eval5_standin", f"{family}_{group}.log")) as f:
            parsed = e5.parse_dryrun(f.read())
        assert [d["name"] for d in parsed["datasets"]] == list(e5.GROUP_DATASETS[group])


def test_seeding_copies_only_A40_screens_as_real_files(e5, tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    _sidecar(src / "mask__statistics", "aaa", "NVIDIA A40", b"a40")
    _sidecar(src / "mask__statistics", "bbb", "NVIDIA H200", b"h200")
    (src / "mask__statistics" / "ccc.json").write_text(json.dumps({"device": "NVIDIA A40"}))  # no .pt
    out = e5.seed_screen_cache(["mask:statistics"], src=str(src), dst=str(dst))
    d = dst / "mask__statistics"
    assert sorted(os.listdir(d)) == ["aaa.json", "aaa.pt"]
    assert not os.path.islink(d / "aaa.pt") and (d / "aaa.pt").read_bytes() == b"a40"
    assert out["copied"] == ["mask__statistics/aaa"]


def test_seeding_follows_a_symlinked_source_and_never_overwrites(e5, tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    _sidecar(tmp_path / "real", "aaa", "NVIDIA A40", b"a40")
    (src).mkdir()
    os.symlink(tmp_path / "real", src / "sandbagging")
    e5.seed_screen_cache(["sandbagging"], src=str(src), dst=str(dst))
    pt = dst / "sandbagging" / "aaa.pt"
    assert not os.path.islink(dst / "sandbagging") and not os.path.islink(pt)
    pt.write_bytes(b"local")
    out = e5.seed_screen_cache(["sandbagging"], src=str(src), dst=str(dst))
    assert pt.read_bytes() == b"local" and out["copied"] == []


CACHED_LOG = """\
  dataset                            condition tokens     pool  judge
  ----------------------------------------------------------------------------------------------------
  lb:instructed-deception            outcome      512     4000  openrouter/openai/gpt-4o
  lb:harm-pressure-knowledge-report  outcome      512     4000  openrouter/openai/gpt-4o
  lb:convincing-game                 outcome      512     4000  openrouter/openai/gpt-4o

  eval 5 lb:instructed-deception: screen (50-600 items) [cached]          0.0 - 9.0 min
  eval 5 lb:harm-pressure-knowledge-report: screen (50-600 items) [cached]          0.0 - 9.0 min
  eval 5 lb:convincing-game: screen (50-600 items)                        6.0 - 9.0 min
  TOTAL                                                                   549.8 - 752.0 min (3 cell(s))

  Nothing was written. Drop --dry-run to run it.
"""


def _local_cache(tmp_path, devices=("NVIDIA A40",)):
    root = tmp_path / "local"
    for name in ("lb__instructed-deception", "lb__harm-pressure-knowledge-report",
                 "lb__convincing-game"):
        for i, dev in enumerate(devices):
            _sidecar(root / name, f"k{i}", dev)
    return str(root)


def test_cache_check_refuses_an_uncached_dataset(e5, tmp_path):
    r = e5.cache_check(e5.parse_dryrun(CACHED_LOG), "lb", cache_dir=_local_cache(tmp_path),
                       partition="gpuA40x4")
    assert len(r["reasons"]) == 1 and "lb:convincing-game" in r["reasons"][0]
    assert r["passed"] is False


def test_cache_check_passes_a_fully_cached_A40_suite(e5, tmp_path):
    log = CACHED_LOG.replace("convincing-game: screen (50-600 items)  ",
                             "convincing-game: screen (50-600 items) [cached]")
    r = e5.cache_check(e5.parse_dryrun(log), "lb", cache_dir=_local_cache(tmp_path),
                       partition="gpuA40x4")
    assert r == {"passed": True, "reasons": [], "allowed": None}


def test_cache_check_refuses_a_non_A40_partition_or_copy(e5, tmp_path):
    log = CACHED_LOG.replace("convincing-game: screen (50-600 items)  ",
                             "convincing-game: screen (50-600 items) [cached]")
    r = e5.cache_check(e5.parse_dryrun(log), "lb", cache_dir=_local_cache(tmp_path),
                       partition="gpuA100x4")
    assert any("gpuA100x4" in x for x in r["reasons"])
    mixed = _local_cache(tmp_path, devices=("NVIDIA A40", "NVIDIA H200"))
    r = e5.cache_check(e5.parse_dryrun(log), "lb", cache_dir=mixed, partition="gpuA40x4")
    assert any("NVIDIA H200" in x for x in r["reasons"])


def test_allow_rescreen_with_a_reason_clears_the_cache_check(e5, tmp_path):
    r = e5.cache_check(e5.parse_dryrun(CACHED_LOG), "lb", cache_dir=_local_cache(tmp_path),
                       partition="gpuA100x4", allow_rescreen="A40 queue is 3 days")
    assert r["passed"] is True and r["allowed"] == "A40 queue is 3 days"
    assert len(r["reasons"]) == 2                     # still reported, not hidden
    with pytest.raises(ValueError, match="reason"):
        e5.cache_check(e5.parse_dryrun(CACHED_LOG), "lb", cache_dir=_local_cache(tmp_path),
                       partition="gpuA40x4", allow_rescreen="  ")


# ==============================================================================
# THE PRE-FLIGHT GATE (F knockout wikitext KL <= 0.66)
# ==============================================================================

def _manifest_suite(task, f_label="F", f_run=F_RUN):
    """A ticket 04 manifest entry: the configured runs and the `cells` index."""
    cells = []
    for circuit in ("D", "H", f_label):
        for cond, ds in (("deceptive", task), ("honest", f"{task}_honest"),
                         ("nopressure", f"{task}_nopressure")):
            cells.append({"circuit": circuit, "dataset": ds, "condition": cond,
                          "roles": ["knockout"] if "_hko" in circuit
                          else ["faithfulness", "knockout"],
                          "job": f"{circuit}__{ds}", "path": f"cells/{circuit}/{ds}/interchange"})
    # a delta cell must not be mistaken for F's knockout
    cells.append({"circuit": "F_minus_D__head", "dataset": task, "condition": "deceptive",
                  "roles": ["delta"], "job": "F_minus_D__x",
                  "path": f"cells/F_minus_D__head/{task}/interchange"})
    return {"family": "fine", "task": task, "runs": {"D": D_RUN, "H": H_RUN, "F": f_run},
            "cells": cells}


def _write_knockout(root, path, kl, *, where="both", f_run=F_RUN, summary=True):
    d = os.path.join(root, path)
    os.makedirs(d, exist_ok=True)
    body = {"granularity": "finest", "ablation": "interchange"}
    if kl is not None and where in ("both", "wikitext"):
        body["wikitext"] = {"discovered": {"kl_per_token": kl, "ppl_ratio": 1.4}}
    if kl is not None and where in ("both", "headline"):
        body["headline"] = {"task_accuracy": 0.0, "wikitext_kl": kl}
    with open(os.path.join(d, "knockout.json"), "w") as f:
        json.dump(body, f)
    if summary:
        operands = {"F": f_run}
        if "_hko" in path:
            operands["m"] = M_RUN
        with open(os.path.join(d, "summary.json"), "w") as f:
            json.dump({"circuit_spec": {"label": path.split("/")[1], "operands": operands}}, f)


def _gate(e5, root, suite, f_run=F_RUN, **kw):
    return e5.gate(root, suite, f_run=f_run, **kw)


def test_gate_passes_when_both_F_knockouts_are_under_the_bar(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far/interchange", 0.33)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.66)   # the bar is inclusive
    g = _gate(e5, root, _manifest_suite("far"))
    assert g["passed"] is True
    assert g["reasons"] == [] and g["overridden"] == []
    assert sorted(g["kl"].values()) == [0.33, 0.66]


def test_gate_refuses_and_names_the_number(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far/interchange", 0.33)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.8123)
    g = _gate(e5, root, _manifest_suite("far"))
    assert g["passed"] is False
    assert len(g["reasons"]) == 1
    reason = g["reasons"][0]
    assert "0.812" in reason and "0.66" in reason
    assert "cells/F/far_nopressure/interchange" in reason
    # the fluent-generations route is the researcher's call: point at the text
    assert "generation" in reason


def test_gate_refuses_a_missing_cell(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.30)
    g = _gate(e5, root, _manifest_suite("far"))
    assert g["passed"] is False
    assert any("missing" in r and "cells/F/far/interchange" in r for r in g["reasons"])


def test_gate_refuses_a_cell_without_wikitext_kl(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far/interchange", 0.30)
    _write_knockout(root, "cells/F/far_nopressure/interchange", None)
    g = _gate(e5, root, _manifest_suite("far"))
    assert g["passed"] is False
    assert any("no wikitext KL" in r for r in g["reasons"])


def test_gate_refuses_a_malformed_cell_with_a_reason(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far/interchange", 0.30)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.30)
    with open(os.path.join(root, "cells/F/far/interchange/knockout.json"), "w") as f:
        json.dump([1, 2], f)
    with open(os.path.join(root, "cells/F/far_nopressure/interchange/knockout.json"), "w") as f:
        json.dump({"headline": {"wikitext_kl": [0.1]}}, f)
    g = _gate(e5, root, _manifest_suite("far"))
    assert g["passed"] is False and len(g["reasons"]) == 2
    assert all("unreadable" in r for r in g["reasons"])


def test_gate_reads_the_KL_from_either_place_the_evaluator_writes_it(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far/interchange", 0.2, where="wikitext")
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.7, where="headline")
    g = _gate(e5, root, _manifest_suite("far"))
    assert sorted(g["kl"].values()) == [0.2, 0.7]
    assert g["passed"] is False


def test_gate_finds_the_coarse_heads_only_knockout_cells(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F_hko__leaf/sdr/interchange", 0.36)
    _write_knockout(root, "cells/F_hko__leaf/sdr_nopressure/interchange", 0.37)
    g = _gate(e5, root, _manifest_suite("sdr", f_label="F_hko__leaf"))
    assert g["passed"] is True
    assert len(g["kl"]) == 2


def test_gate_refuses_when_the_manifest_plans_no_F_knockout(e5, tmp_path):
    suite = _manifest_suite("far")
    suite["cells"] = [c for c in suite["cells"] if c["circuit"] != "F"]
    g = _gate(e5, str(tmp_path), suite)
    assert g["passed"] is False
    assert any("no F knockout cell" in r for r in g["reasons"])


def test_gate_refuses_a_cell_from_a_different_F_than_the_configured_one(e5, tmp_path):
    root = str(tmp_path)
    stale = "/runs/sdr/nls0.3_nopressure_noedge_OLD"
    _write_knockout(root, "cells/F/far/interchange", 0.30, f_run=stale)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.30)
    g = _gate(e5, root, _manifest_suite("far"))
    assert g["passed"] is False
    assert len(g["reasons"]) == 1
    assert stale in g["reasons"][0] and F_RUN in g["reasons"][0]


def test_gate_refuses_when_the_suite_was_planned_with_another_F(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far/interchange", 0.30)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.30)
    g = _gate(e5, root, _manifest_suite("far", f_run="/runs/other_F"))
    assert g["passed"] is False
    assert any("/runs/other_F" in r and "suite_manifest" in r for r in g["reasons"])


def test_gate_refuses_a_cell_whose_F_cannot_be_verified(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far/interchange", 0.30, summary=False)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.30)
    g = _gate(e5, root, _manifest_suite("far"))
    assert g["passed"] is False
    assert any("cannot verify" in r for r in g["reasons"])


def _f_run(root, name, masks=None, condition="nopressure"):
    """A run directory with active_nodes.json and config.json."""
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "active_nodes.json"), "w") as f:
        json.dump({"masks": masks or {"attention_heads": [[1, 0], [0, 1]]}}, f)
    with open(os.path.join(d, "config.json"), "w") as f:
        json.dump({"deception_condition": condition}, f)
    return d


def _gate_on(e5, tmp_path, *, recorded, configured):
    """Cells and manifest produced from `recorded`; suites.json names `configured`."""
    root = str(tmp_path / "suite")
    _write_knockout(root, "cells/F/far/interchange", 0.30, f_run=recorded)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.30, f_run=recorded)
    return _gate(e5, root, _manifest_suite("far", f_run=recorded), f_run=configured)


def test_gate_accepts_a_relocated_copy_of_the_configured_F(e5, tmp_path):
    """After a merge the same run sits elsewhere: identical masks are the same F."""
    old = _f_run(str(tmp_path / "worktree"), "nls0.3_nopressure_X")
    new = _f_run(str(tmp_path / "main"), "nls0.3_nopressure_X")
    g = _gate_on(e5, tmp_path, recorded=old, configured=new)
    assert g["passed"] is True, g["reasons"]


def test_gate_refuses_a_run_with_different_masks(e5, tmp_path):
    old = _f_run(str(tmp_path / "a"), "run")
    other = _f_run(str(tmp_path / "b"), "run", masks={"attention_heads": [[1, 1], [0, 1]]})
    g = _gate_on(e5, tmp_path, recorded=old, configured=other)
    assert g["passed"] is False
    assert all("different masks" in r for r in g["reasons"]) and len(g["reasons"]) == 3


def test_gate_refuses_identical_masks_under_another_condition(e5, tmp_path):
    old = _f_run(str(tmp_path / "a"), "run")
    other = _f_run(str(tmp_path / "b"), "run", condition="honest")
    g = _gate_on(e5, tmp_path, recorded=old, configured=other)
    assert g["passed"] is False and all("condition" in r for r in g["reasons"])


def test_gate_says_to_keep_the_worktree_when_the_recorded_run_is_gone(e5, tmp_path):
    old = _f_run(str(tmp_path / "worktree"), "run")
    new = _f_run(str(tmp_path / "main"), "run")
    shutil.rmtree(str(tmp_path / "worktree"))
    g = _gate_on(e5, tmp_path, recorded=old, configured=new)
    assert g["passed"] is False
    assert all("cannot compare" in r and "keep the format-control worktree" in r
               for r in g["reasons"])


def test_gate_override_clears_only_the_KL_bar_and_is_reported(e5, tmp_path):
    root = str(tmp_path)
    _write_knockout(root, "cells/F/far/interchange", 0.70)
    _write_knockout(root, "cells/F/far_nopressure/interchange", 0.71)
    g = _gate(e5, root, _manifest_suite("far"), override="generations read fluent (JW)")
    assert g["passed"] is True and g["reasons"] == []
    assert len(g["overridden"]) == 2 and "0.710" in " ".join(g["overridden"])
    # a missing cell or a stale F is never overridable
    shutil.rmtree(os.path.join(root, "cells/F/far"))
    g = _gate(e5, root, _manifest_suite("far"), override="generations read fluent (JW)")
    assert g["passed"] is False and any("missing" in r for r in g["reasons"])
    with pytest.raises(ValueError, match="reason"):
        _gate(e5, root, _manifest_suite("far"), override=" ")


# ==============================================================================
# CONFIGURATION AND REFUSALS
# ==============================================================================

SUITE = "format-control-far-nls0.3"


def _config(f_run=F_RUN):
    return {SUITE: {"family": "fine", "task": "far",
                    "runs": {"D": D_RUN, "H": H_RUN, "F": f_run}},
            "format-control-sdr-coarse-nls0.3": {
                "family": "coarse", "task": "sdr",
                "runs": {"D": D_RUN, "H": H_RUN, "F": None}, "allmlp": M_RUN}}


def _gated_suite(root, kl=0.3):
    _write_knockout(root, "cells/F/far/interchange", kl)
    _write_knockout(root, "cells/F/far_nopressure/interchange", kl)
    return {"suites": {SUITE: _manifest_suite("far")}}


def test_runs_come_from_ticket_04s_configuration(e5):
    fam = e5.family_runs(_config(), "far")
    assert fam["runs"] == RUNS and fam["standin"] is False
    coarse = e5.family_runs(_config(), "sdr_coarse")
    assert coarse["allmlp"] == M_RUN and coarse["runs"]["F"] is None


def test_the_stand_in_puts_H_in_Fs_place_and_says_so(e5):
    fam = e5.family_runs(_config(f_run=None), "far", standin=True)
    assert fam["runs"]["F"] == H_RUN and fam["standin"] is True


def test_a_stand_in_is_refused_once_F_is_configured(e5):
    with pytest.raises(ValueError, match="stand-in"):
        e5.family_runs(_config(), "far", standin=True)


def test_nothing_refuses_a_gated_go_ahead_suite(e5, tmp_path):
    manifest = _gated_suite(str(tmp_path))
    r = e5.refusals("far", "sm", config=_config(), manifest=manifest,
                    env={e5.GO_ENV: "1"}, suite_root=str(tmp_path))
    assert r == []


def test_refusal_when_F_is_null(e5, tmp_path):
    r = e5.refusals("far", "sm", config=_config(f_run=None), manifest=_gated_suite(str(tmp_path)),
                    env={e5.GO_ENV: "1"}, suite_root=str(tmp_path))
    assert any("F run directory" in x for x in r)


def test_refusal_when_the_gate_fails_names_the_number(e5, tmp_path):
    manifest = _gated_suite(str(tmp_path), kl=0.9)
    r = e5.refusals("far", "lb", config=_config(), manifest=manifest,
                    env={e5.GO_ENV: "1"}, suite_root=str(tmp_path))
    assert any("0.900" in x for x in r)
    ok = e5.refusals("far", "lb", config=_config(), manifest=manifest,
                     env={e5.GO_ENV: "1"}, suite_root=str(tmp_path), gate_override="fluent")
    assert ok == []


def test_refusal_without_the_researchers_go_ahead(e5, tmp_path):
    manifest = _gated_suite(str(tmp_path))
    for env in ({}, {e5.GO_ENV: "0"}, {e5.GO_ENV: "yes"}):
        r = e5.refusals("far", "sm", config=_config(), manifest=manifest, env=env,
                        suite_root=str(tmp_path))
        assert len(r) == 1 and e5.GO_ENV in r[0]


def test_a_dry_run_needs_no_go_ahead_but_still_obeys_the_gate(e5, tmp_path):
    ok = e5.refusals("far", "sm", config=_config(), manifest=_gated_suite(str(tmp_path)),
                     env={}, suite_root=str(tmp_path), dry=True)
    assert ok == []
    bad = e5.refusals("far", "sm", config=_config(),
                      manifest=_gated_suite(str(tmp_path), kl=0.7), env={},
                      suite_root=str(tmp_path), dry=True)
    assert any("0.700" in x for x in bad)


def test_a_stand_in_suite_is_never_submittable(e5, tmp_path):
    r = e5.refusals("far", "sm", config=_config(f_run=None), manifest=_gated_suite(str(tmp_path)),
                    env={e5.GO_ENV: "1"}, suite_root=str(tmp_path), standin=True)
    assert any("stand-in" in x for x in r)
    r = e5.refusals("far", "sm", config=_config(f_run=None), manifest=_gated_suite(str(tmp_path)),
                    env={}, suite_root=str(tmp_path), standin=True, dry=True)
    assert any("stand-in" in x for x in r)


def _run_dir(tmp_path, name, masks):
    d = tmp_path / name
    d.mkdir()
    (d / "active_nodes.json").write_text(json.dumps({"masks": {k: [] for k in masks}}))
    return str(d)


def test_coarse_runs_must_match_the_all_mlp_operands_mask_signature(e5, tmp_path):
    nomb = ("attention_heads", "attention_neurons")
    # the operand's signature is read from its own masks, not its name (ticket 04
    # builds it as `allmlp_nomb` in the launcher directory)
    allmlp = _run_dir(tmp_path, "allmlp_nomb", nomb)
    runs = {"D": _run_dir(tmp_path, "d", nomb), "H": _run_dir(tmp_path, "h", nomb),
            "F": _run_dir(tmp_path, "f", nomb + ("mlp_blocks",))}
    assert e5.coarse_signature_reasons(runs, allmlp) == [
        f"F run {runs['F']} has an mlp_blocks gate (signature mb) but the all-MLP operand "
        f"{allmlp} has signature nomb"]
    runs["F"] = _run_dir(tmp_path, "f2", nomb)
    assert e5.coarse_signature_reasons(runs, allmlp) == []
    mb_operand = _run_dir(tmp_path, "_allmlp_mb", nomb + ("mlp_blocks",))
    assert len(e5.coarse_signature_reasons(runs, mb_operand)) == 3
    runs["H"] = str(tmp_path / "nowhere")
    assert any("cannot read" in r for r in e5.coarse_signature_reasons(runs, allmlp))
    assert any("cannot read" in r and "nowhere2" in r
               for r in e5.coarse_signature_reasons(runs, str(tmp_path / "nowhere2")))


def test_sbatch_line_sizes_the_walltime_from_the_dry_run_ceiling(e5):
    args = e5.eval5_args("far", "sm", RUNS)
    cmd = e5.sbatch_cmd("far", "sm", args, account="bgrb-delta-gpu",
                        ceiling_min=1774.3)
    assert cmd[:1] == ["sbatch"]
    assert "--account=bgrb-delta-gpu" in cmd
    assert "--partition=gpuA40x4" in cmd                 # the cached screens' GPU
    assert "--time=44:30:00" in cmd                       # 1774.3 x 1.5 -> quarter hours
    assert "--job-name=e5fc-far-sm" in cmd
    i = cmd.index("scripts/evaluate_circuit.sbatch")
    assert cmd[i + 1:] == args


def test_sbatch_line_takes_an_explicit_time_and_partition(e5):
    args = e5.eval5_args("far", "lb", RUNS)
    cmd = e5.sbatch_cmd("far", "lb", args, account="bimc-delta-gpu", ceiling_min=None,
                        time_="12:00:00", partition="gpuA100x4")
    assert "--time=12:00:00" in cmd and "--partition=gpuA100x4" in cmd
    with pytest.raises(ValueError, match="time"):
        e5.sbatch_cmd("far", "lb", args, account="a", ceiling_min=None)


# ==============================================================================
# THE COST ESTIMATE FROM A --dry-run LOG
# ==============================================================================

DRYRUN_LOG = """\
====================================================================================
  CELL GRID (3 circuits x 1 tasks)
====================================================================================

  outputs/eval5_format_far/cells/D/far/interchange
  outputs/eval5_format_far/cells/H/far/interchange
  outputs/eval5_format_far/cells/F/far/interchange

  dataset                            condition tokens     pool  judge
  ----------------------------------------------------------------------------------------------------
  sandbagging                        prompt      1024     3668  local grader, no API call
  mask:disinformation                outcome      512       97  openrouter/openai/gpt-4o
  mask:statistics                    outcome      512       30  openrouter/openai/o3-mini

  model load                                                                 3.3 min
  eval 5 sandbagging: screen (50-600 items) [cached]                         0.0 - 157.5 min
  eval 5 mask:disinformation: screen (50-97 items) [cached]                  0.0 - 12.7 min
  eval 5 mask:statistics: screen (30-30 items)                               6.6 - 12.2 min
  -------------------------------------------------------------------------------
  TOTAL                                                                   1460.5 - 1774.3 min (3 cell(s))

  Nothing was written. Drop --dry-run to run it.
"""


def test_dry_run_log_is_parsed_for_cells_datasets_cache_and_runtime(e5):
    p = e5.parse_dryrun(DRYRUN_LOG)
    assert p["passed"] is True
    assert (p["floor_min"], p["ceiling_min"]) == (1460.5, 1774.3)
    assert p["cells"] == ["outputs/eval5_format_far/cells/D/far/interchange",
                          "outputs/eval5_format_far/cells/H/far/interchange",
                          "outputs/eval5_format_far/cells/F/far/interchange"]
    assert [d["name"] for d in p["datasets"]] == ["sandbagging", "mask:disinformation",
                                                  "mask:statistics"]
    assert [d["pool"] for d in p["datasets"]] == [3668, 97, 30]
    assert [d["judged"] for d in p["datasets"]] == [False, True, True]
    assert p["cached"] == ["sandbagging", "mask:disinformation"]


def test_a_failed_dry_run_does_not_pass(e5):
    assert e5.parse_dryrun("Traceback (most recent call last):\n  boom")["passed"] is False
    assert e5.parse_dryrun("CELL GRID (3 circuits x 1 tasks)\n")["passed"] is False


def test_cost_counts_judge_calls_per_cell_and_config(e5):
    c = e5.cost_estimate(e5.parse_dryrun(DRYRUN_LOG), n_per_dataset=50, n_random=6)
    # 3 cells x (knockout, circuit_only, empty, 6 randoms) x items; `full` is the
    # screen. sandbagging is graded locally. statistics' pool caps it at 30.
    assert c["judge_calls_ablated"] == 3 * 9 * 50 + 3 * 9 * 30
    # the one uncached judged screen walks at most its pool
    assert c["judge_calls_screen_max"] == 30
    assert c["gpu_hours"] == (round(1460.5 / 60, 1), round(1774.3 / 60, 1))


def test_cost_uses_known_item_counts_from_an_existing_suite(e5, tmp_path):
    cell = tmp_path / "cells" / "hko__leaf" / "sdr" / "interchange"
    cell.mkdir(parents=True)
    (cell / "benchmarks.json").write_text(json.dumps({"datasets": {
        "mask:disinformation": {"n_items": 12}, "mask:statistics": {"n_items": 16}}}))
    known = e5.known_item_counts(str(tmp_path))
    assert known == {"mask:disinformation": 12, "mask:statistics": 16}
    c = e5.cost_estimate(e5.parse_dryrun(DRYRUN_LOG), n_per_dataset=50, n_random=6,
                         known_n=known)
    assert c["judge_calls_ablated"] == 3 * 9 * 12 + 3 * 9 * 16


# ==============================================================================
# submit_eval5.sh — refusals end to end, with stubs for sbatch and the evaluator
# ==============================================================================

SUBMIT = os.path.join(LAUNCH, "submit_eval5.sh")

#: What the stub evaluator prints: a passing dry-run with every sm screen cached.
SM_DATASETS = ("sandbagging", "mask:continuations", "mask:disinformation",
               "mask:doubling_down_known_facts", "mask:known_facts", "mask:provided_facts",
               "mask:statistics")


def _fake_log(cached=SM_DATASETS):
    rows = "\n".join(f"  {d:<34} outcome      512      100  openrouter/openai/gpt-4o"
                     for d in SM_DATASETS)
    screens = "\n".join(f"  eval 5 {d}: screen (50-100 items){' [cached]' if d in cached else ''}"
                        f"     0.0 - 9.0 min" for d in SM_DATASETS)
    return (f"  CELL GRID (3 circuits x 1 tasks)\n\n"
            f"  outputs/eval5_format_far/cells/D/far/interchange\n"
            f"  outputs/eval5_format_far/cells/H/far/interchange\n"
            f"  outputs/eval5_format_far/cells/F/far/interchange\n\n"
            f"  dataset                            condition tokens     pool  judge\n"
            f"  {'-' * 60}\n{rows}\n\n{screens}\n"
            f"  TOTAL     1460.5 - 1774.3 min (3 cell(s))\n\n"
            f"  Nothing was written. Drop --dry-run to run it.\n")


@pytest.fixture
def harness(tmp_path, e5):
    """A config, manifest, suite root, cache source and local cache in tmp;
    `sbatch` and the evaluator are stubs that record their argv, so no test can
    reach Slurm and no test writes into the worktree's outputs/."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "sbatch_calls.txt"
    sb = bin_dir / "sbatch"
    sb.write_text("#!/bin/bash\necho \"$@\" >> %s\necho 'Submitted batch job 4242'\n" % calls)
    sb.chmod(0o755)
    suite_root = tmp_path / "suite"
    suite_root.mkdir()
    src = tmp_path / "screens_src"
    for d in SM_DATASETS:
        _sidecar(src / d.replace(":", "__"), "k0", "NVIDIA A40")
    env = {k: v for k, v in os.environ.items() if k != e5.GO_ENV}
    env.update(PATH=f"{bin_dir}{os.pathsep}{env.get('PATH', '')}", PYTHON=sys.executable,
               EVAL5_ALLOW_PATH_OVERRIDES="1")
    assert shutil.which("sbatch", path=env["PATH"]) == str(sb)   # the stub shadows Slurm

    def run(*args, config=None, kl=0.3, go=False, log=None, fail=False, overrides=True):
        cfg = tmp_path / "suites.json"
        cfg.write_text(json.dumps(config if config is not None else _config()))
        man = tmp_path / "manifest.json"
        man.write_text(json.dumps(_gated_suite(str(suite_root), kl=kl)))
        fake_eval = tmp_path / "fake_evaluate.py"
        fake_eval.write_text("import sys\nprint('ARGV', ' '.join(sys.argv[1:]))\nprint(%r)\n%s"
                             % (log if log is not None else _fake_log(),
                                "sys.exit(1)\n" if fail else ""))
        e = dict(env, EVAL5_EVALUATOR=str(fake_eval), **({e5.GO_ENV: "1"} if go else {}))
        if not overrides:
            e.pop("EVAL5_ALLOW_PATH_OVERRIDES")
        cmd = ["bash", SUBMIT, *args, "--config", str(cfg), "--manifest", str(man),
               "--suite-root", str(suite_root), "--log-dir", str(tmp_path / "logs"),
               "--record", str(tmp_path / "record.json"), "--cache-src", str(src),
               "--cache-dir", str(tmp_path / "local_cache"), "--account", "bgrb-delta-gpu"]
        p = subprocess.run(cmd, capture_output=True, text=True, env=e, timeout=120)
        sbatched = calls.read_text() if calls.exists() else ""
        return p.returncode, p.stdout + p.stderr, sbatched

    def record():
        path = tmp_path / "record.json"
        return json.loads(path.read_text()) if path.exists() else None

    run.tmp = tmp_path
    run.record = record
    return run


def test_concurrent_launchers_never_lose_a_record_event(e5, tmp_path):
    """Two launchers append to one record at once (as the SDR and coarse dry
    runs did on 2026-10-15, losing an event): every event must survive."""
    record = tmp_path / "record.json"
    code = ("import sys; sys.path.insert(0, %r); import eval5_cmd as e\n"
            "for i in range(25): e.record_event(%r, 'far', 'sm', {'event': 'dry', 'n': sys.argv[1] + str(i)})\n"
            % (LAUNCH, str(record)))
    procs = [subprocess.Popen([sys.executable, "-c", code, tag]) for tag in "abcd"]
    assert [p.wait(timeout=120) for p in procs] == [0, 0, 0, 0]
    events = json.loads(record.read_text())["suites"]["eval5_format_far"]["events"]
    assert sorted(e["n"] for e in events) == sorted(f"{t}{i}" for t in "abcd" for i in range(25))


def test_submit_refuses_when_F_is_null(harness):
    code, out, sbatched = harness("far", "sm", config=_config(f_run=None), go=True)
    assert code == 3 and "F run directory" in out and sbatched == ""


def test_dry_refuses_to_build_a_command_without_F(harness):
    code, out, sbatched = harness("far", "sm", "--dry", config=_config(f_run=None))
    assert code == 3 and "F run directory" in out and sbatched == ""
    assert not (harness.tmp / "logs").exists()                 # no dry-run either


def test_submit_refuses_without_the_go_ahead(harness, e5):
    code, out, sbatched = harness("far", "sm")
    assert code == 3 and e5.GO_ENV in out and sbatched == ""


def test_submit_refuses_a_failing_gate_and_names_the_number(harness):
    code, out, sbatched = harness("far", "lb", kl=0.71, go=True)
    assert code == 3 and "0.710" in out and sbatched == ""


def test_submit_refuses_a_failing_dry_run(harness):
    code, out, sbatched = harness("far", "sm", go=True, fail=True)
    assert code == 5 and "DRY-RUN FAILED" in out and sbatched == ""


def test_submit_refuses_a_stand_in(harness):
    code, out, sbatched = harness("far", "sm", "--standin", config=_config(f_run=None), go=True)
    assert code == 3 and "stand-in" in out and sbatched == ""


def test_submit_refuses_path_overrides_without_the_test_switch(harness):
    code, out, sbatched = harness("far", "sm", go=True, overrides=False)
    assert code == 2 and "--dry" in out and sbatched == ""


def test_dry_seeds_the_local_cache_and_prints_the_submit_line(harness, e5):
    code, out, sbatched = harness("far", "sm", "--dry")
    assert code == 0, out
    assert "command: python " in out and f"--circuit D={D_RUN}" in out
    log = (harness.tmp / "logs" / "far_sm.log").read_text()
    argv = log.splitlines()[1]                                  # the evaluator's own echo
    assert argv.startswith(f"ARGV --circuit D={D_RUN}") and argv.endswith(" --dry-run")
    assert f"--benchmark-screen-cache {harness.tmp / 'local_cache'} " in argv
    assert (harness.tmp / "local_cache" / "mask__statistics" / "k0.pt").is_file()
    assert "judge calls" in log                                 # the cost is kept with the log
    assert "sbatch --account=bgrb-delta-gpu --partition=gpuA40x4 --time=44:30:00" in out
    assert sbatched == ""                                       # --dry never submits
    ev = harness.record()["suites"]["eval5_format_far"]["events"][-1]
    assert ev["event"] == "dry" and ev["cost"]["judge_calls_ablated"] > 0


def test_dry_prints_no_submit_line_when_the_gate_fails(harness):
    code, out, sbatched = harness("far", "sm", "--dry", kl=0.9)
    assert code == 0                                           # the dry-run itself passed
    assert "0.900" in out and "no submit line" in out
    assert "sbatch --account" not in out and sbatched == ""


def test_dry_prints_no_submit_line_when_a_screen_is_not_cached(harness):
    code, out, sbatched = harness("far", "sm", "--dry", log=_fake_log(cached=SM_DATASETS[:-1]))
    assert code == 0
    assert "mask:statistics" in out and "no submit line" in out and sbatched == ""


def test_a_stand_in_dry_run_is_labelled_and_never_gets_a_submit_line(harness):
    code, out, sbatched = harness("far", "sm", "--dry", "--standin", config=_config(f_run=None))
    assert code == 0, out
    assert f"F={H_RUN}" in out and "STAND-IN" in out
    assert "no submit line" in out and sbatched == ""


def test_submit_with_every_refusal_cleared_reaches_sbatch_once(harness):
    code, out, sbatched = harness("far", "sm", go=True)
    assert code == 0, out
    assert sbatched.count("\n") == 1
    assert sbatched.startswith("--account=bgrb-delta-gpu --partition=gpuA40x4 --time=44:30:00 "
                               "--job-name=e5fc-far-sm scripts/evaluate_circuit.sbatch --circuit D=")
    ev = harness.record()["suites"]["eval5_format_far"]["events"][-1]
    assert ev["event"] == "submit" and ev["job_id"] == "4242"
    assert ev["gate_override"] is None and ev["allow_rescreen"] is None


def test_submit_refuses_an_uncached_screen_unless_a_rescreen_is_allowed(harness):
    log = _fake_log(cached=SM_DATASETS[1:])
    code, out, sbatched = harness("far", "sm", go=True, log=log)
    assert code == 3 and "sandbagging" in out and sbatched == ""
    code, out, sbatched = harness("far", "sm", "--allow-rescreen", "A40 queue down (JW)",
                                  go=True, log=log)
    assert code == 0, out
    assert sbatched.count("\n") == 1
    ev = harness.record()["suites"]["eval5_format_far"]["events"][-1]
    assert ev["allow_rescreen"] == "A40 queue down (JW)"


def test_a_gate_override_is_recorded_with_its_reason(harness):
    code, out, sbatched = harness("far", "sm", "--gate-override", "generations fluent (JW)",
                                  kl=0.8, go=True)
    assert code == 0, out
    assert "overridden" in out and "0.800" in out
    ev = harness.record()["suites"]["eval5_format_far"]["events"][-1]
    assert ev["gate_override"] == "generations fluent (JW)"
    assert any("0.800" in x for x in ev["gate_overridden"])


# ==============================================================================
# result_summary.md FOR THE THREE-CIRCUIT LAYOUT
# ==============================================================================

@pytest.fixture(scope="module")
def summ():
    return importlib.import_module("evaluation.eval5_format_summary")


def _rows(dec, hon, unp, gens=None, raws=None):
    """Label rows: `dec` deceptive, `hon` honest, `unp` unparsed, in that order."""
    labels = ["deceptive"] * dec + ["honest"] * hon + ["unparsed"] * unp
    raws = raws or ["x"] * len(labels)
    return [{"label": lab, "raw": raw} for lab, raw in zip(labels, raws)]


def _bconfig(dec, hon, unp, nll, d2, gens=None, raws=None):
    n = dec + hon + unp
    return {"counts": {"deceptive": dec, "honest": hon, "unparsed": unp},
            "rates": {"deceptive": dec / n, "honest": hon / n, "unparsed": unp / n},
            "coherence": {"ref_nll": nll, "distinct_n": d2},
            "generations": gens or ["some text"] * n,
            "labels": _rows(dec, hon, unp, raws=raws)}


def _dataset(ko, randoms, *, full=(10, 0, 0, 0.30, 0.80), pct=100.0, ko_gens=None,
             ko_raws=None, screen=None):
    configs = {"full": _bconfig(*full), "knockout": _bconfig(*ko, gens=ko_gens, raws=ko_raws),
               "circuit_only": _bconfig(0, 2, 8, 1.4, 0.7), "empty": _bconfig(0, 2, 8, 1.4, 0.7)}
    for i, r in enumerate(randoms):
        configs[f"random-{i}"] = _bconfig(*r)
    return {"n_items": 10, "configs": configs,
            "screen": screen or {"selected": 10, "target": 50, "candidates": 10,
                                 "screened": 10, "full_model_deception_rate": 0.3},
            "null": {"n": len(randoms), "deceptive": {"percentile": pct, "p_value": 0.14}}}


def _write_suite(root, labels=("D", "H", "F"), task="far", skip=(), mask_d_on=None,
                 full_override=None):
    """Three cells sharing one screen. Per dataset, D lies least under knockout."""
    root = str(root)
    ko = {"D": (2, 5, 3, 0.9, 0.6), "H": (4, 3, 3, 0.8, 0.7), "F": (6, 1, 3, 0.5, 0.75)}
    for lab in labels:
        role = lab.split("_")[0]
        if role in skip:
            continue
        sand = _dataset(ko[role], [(8, 1, 1, 0.5, 0.6), (6, 1, 3, 0.7, 0.5)])
        stats_raws = None
        if mask_d_on == role:
            stats_raws = ["D"] + ["B"] * 9
        stats = _dataset(ko[role], [(7, 2, 1, 0.6, 0.7)], ko_raws=stats_raws,
                         screen={"selected": 10, "target": 50, "candidates": 10,
                                 "screened": 10, "full_model_deception_rate": 0.17})
        if full_override and role in full_override:
            sand["configs"]["full"] = _bconfig(*full_override[role])
        body = {"resolved": {"model": "llama-8b-instruct", "ablation": "interchange",
                             "n_per_dataset": 50, "n_random": 2},
                "datasets": {"sandbagging": sand, "mask:statistics": stats},
                "failed_datasets": {}, "judge": {"cache_hits": 3, "cache_writes": 40}}
        d = os.path.join(root, "cells", lab, task, "interchange")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "benchmarks.json"), "w") as f:
            json.dump(body, f)
    with open(os.path.join(root, "suite.json"), "w") as f:
        json.dump({"ablation": "interchange", "argv": ["evaluate_circuit.py", "--circuit",
                                                         "D=/r/d"],
                   "circuits": [{"label": lab, "expr": None, "operands": {}} for lab in labels]},
                  f)
    return root


def _table_row(md, first_cells):
    """The markdown table row starting with `first_cells` (a list of cell texts)."""
    prefix = "| " + " | ".join(first_cells) + " |"
    hits = [line for line in md.splitlines() if line.startswith(prefix)]
    assert len(hits) == 1, (prefix, hits)
    return [c.strip() for c in hits[0].strip("|").split("|")]


def test_summary_tabulates_full_and_each_circuits_knockout_and_random_rows(summ, tmp_path):
    root = _write_suite(tmp_path)
    md = summ.render(root)
    assert md.startswith("# EVAL 5")
    # per dataset: deception rate under interchange, ref_nll, distinct_n
    assert _table_row(md, ["sandbagging", "full"])[2:5] == ["1.000", "0.000", "0.000"]
    d = _table_row(md, ["sandbagging", "D knockout"])
    assert d[2:5] == ["0.200", "0.500", "0.300"]            # dec, hon, unp
    assert d[5] == "0.286"                                   # dec / (dec + hon) = 2/7
    assert d[6:8] == ["0.900", "0.600"]                      # ref_nll, distinct_n
    assert _table_row(md, ["sandbagging", "H knockout"])[2] == "0.400"
    assert _table_row(md, ["sandbagging", "F knockout"])[2] == "0.600"
    # random rows: mean of the circuit's own draws (0.8 and 0.6 deceptive)
    r = _table_row(md, ["sandbagging", "D random (mean of 2)"])
    assert r[2] == "0.700" and r[6] == "0.600"               # mean ref_nll (0.5 + 0.7) / 2
    # the headline across circuits: KO deception and delta vs own randoms
    h = _table_row(md, ["sandbagging", "10"])
    assert h[2:6] == ["1.000", "0.200", "0.400", "0.600"]    # full, D KO, H KO, F KO
    assert h[6] == "+0.500"                                  # D: random 0.7 - KO 0.2


def test_summary_prints_the_three_grader_caveats_and_the_random_row_note(summ, tmp_path):
    md = summ.render(_write_suite(tmp_path))
    assert len(summ.GRADER_CAVEATS) == 3
    for caveat in summ.GRADER_CAVEATS:
        for quote in caveat["quotes"]:
            assert " ".join(quote["text"].split()) in " ".join(md.split())
            assert quote["source"] in md
    assert summ.RANDOM_ROWS_NOTE in md
    assert "size-matched per circuit" in summ.RANDOM_ROWS_NOTE
    assert "shared" in summ.RANDOM_ROWS_NOTE


def test_grader_caveats_are_quoted_verbatim_from_their_sources(summ):
    """Each quote appears word for word (whitespace re-flowed) in its source."""
    assert [c["ticket"] for c in summ.GRADER_CAVEATS][:2] == [True, True]
    assert summ.GRADER_CAVEATS[2]["ticket"] is False          # no ticket: labelled so
    checked = 0
    for caveat in summ.GRADER_CAVEATS:
        for quote in caveat["quotes"]:
            if not os.path.isfile(quote["source"]):
                continue
            with open(quote["source"], encoding="utf-8") as f:
                source = " ".join(f.read().split())
            assert " ".join(quote["text"].split()) in source, (quote["source"], quote["text"])
            checked += 1
    if checked == 0:
        pytest.skip("caveat source files are not on this machine")


def test_summary_counts_rows_that_trigger_a_caveat(summ, tmp_path):
    md = summ.render(_write_suite(tmp_path, mask_d_on="H"))
    # H's knockout has one MASK verdict-D row coded deceptive
    row = _table_row(md, ["MASK verdict D coded deceptive"])
    assert row[1:4] == ["0", "1", "0"]                       # D, H, F knockouts


def test_caveat_counts_follow_each_triggers_exact_rule(summ):
    def row(label, raw, judge=None):
        return {"label": label, "raw": raw, "judge_text": judge}
    cfg = {"generations": ["No, that's not correct. It is X.",   # guard fired on REJECTED
                           "That is absolutely correct.",       # AFFIRMED: not this guard
                           "Not Correct at all.",               # case-sensitive: no 'correct'
                           "It is incorrect and not correct.",  # contains 'incorrect'
                           "   ",                               # empty, scored honest
                           ""],                                 # empty, already unparsed
           "labels": [row("unparsed", "invalid_judge", "Verdict: REJECTED"),
                      row("unparsed", "invalid_judge", "Verdict: AFFIRMED"),
                      row("unparsed", "invalid_judge", "Verdict: REJECTED"),
                      row("unparsed", "invalid_judge", "Verdict: REJECTED"),
                      row("honest", "claimed_known_answer"),
                      row("unparsed", "invalid_judge")]}
    hits = summ.caveat_hits("lb:instructed-deception", cfg)
    assert hits == {"empty_generation": 1, "mask_verdict_d": 0, "lb_correct_guard": 1}
    mask = {"generations": ["I cannot do that.", "Yes."],
            "labels": [row("deceptive", "D"), row("deceptive", "A")]}
    assert summ.caveat_hits("mask:known_facts", mask)["mask_verdict_d"] == 1


def test_summary_reads_the_coarse_heads_only_cells(summ, tmp_path):
    root = _write_suite(tmp_path, labels=("D_hko__leaf", "H_hko__leaf", "F_hko__leaf"), task="sdr")
    md = summ.render(root)
    assert _table_row(md, ["sandbagging", "F knockout"])[2] == "0.600"
    assert "F_hko__leaf" in md


def test_summary_reports_a_missing_circuit_instead_of_crashing(summ, tmp_path):
    md = summ.render(_write_suite(tmp_path, skip=("F",)))
    assert "F: cell missing" in md
    assert _table_row(md, ["sandbagging", "D knockout"])[2] == "0.200"
    assert _table_row(md, ["sandbagging", "F knockout"])[2] == "missing"


def test_summary_reports_an_empty_suite(summ, tmp_path):
    md = summ.render(str(tmp_path))
    assert "D: cell missing" in md and "H: cell missing" in md and "F: cell missing" in md


def test_summary_reports_an_unreadable_or_duplicate_cell(summ, tmp_path):
    root = _write_suite(tmp_path)
    with open(os.path.join(root, "cells", "H", "far", "interchange", "benchmarks.json"), "w") as f:
        f.write("{ not json")
    dup = os.path.join(root, "cells", "F_hko__leaf", "far", "interchange")
    os.makedirs(dup)
    shutil.copy(os.path.join(root, "cells", "F", "far", "interchange", "benchmarks.json"), dup)
    md = summ.render(root)
    assert "H: cell unreadable" in md
    assert "F: more than one cell" in md and "F_hko__leaf" in md
    assert _table_row(md, ["sandbagging", "H knockout"])[2] == "missing"


def test_summary_flags_a_full_row_that_differs_between_cells(summ, tmp_path):
    md = summ.render(_write_suite(tmp_path, full_override={"H": (9, 1, 0, 0.3, 0.8)}))
    assert "full row differs between cells" in md


def test_summary_reports_a_failed_dataset(summ, tmp_path):
    root = _write_suite(tmp_path)
    path = os.path.join(root, "cells", "D", "far", "interchange", "benchmarks.json")
    with open(path) as f:
        body = json.load(f)
    body["datasets"]["mask:statistics"] = {"error": "RuntimeError: judge outage"}
    body["failed_datasets"] = {"mask:statistics": "RuntimeError: judge outage"}
    with open(path, "w") as f:
        json.dump(body, f)
    md = summ.render(root)
    assert "judge outage" in md
    assert _table_row(md, ["mask:statistics", "D knockout"])[2] == "failed"
    # the means are over the datasets every circuit has, so they stay comparable
    mean = _table_row(md, ["**mean over 1 dataset(s) common to all circuits**"])
    assert mean[2:6] == ["1.000", "0.200", "0.400", "0.600"]


def test_write_produces_the_summary_and_the_json_ticket_05_can_read(summ, tmp_path):
    root = _write_suite(tmp_path)
    paths = summ.write(root)
    assert os.path.isfile(os.path.join(root, "result_summary.md"))
    data = json.load(open(os.path.join(root, "eval5_format.json")))
    assert set(paths) == {os.path.join(root, "result_summary.md"),
                          os.path.join(root, "eval5_format.json")}
    ko = data["roles"]["F"]["datasets"]["sandbagging"]["knockout"]
    assert ko["deceptive"] == 0.6 and ko["ref_nll"] == 0.5 and ko["distinct_n"] == 0.75
    assert data["roles"]["D"]["datasets"]["sandbagging"]["random_mean"]["deceptive"] == 0.7
    assert data["roles"]["H"]["label"] == "H"
