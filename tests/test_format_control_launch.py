"""
The format-control evaluation suite launcher (`outputs/_launch_format_control/`).

Three suites, one per task family, over the deceptive circuit D, its Honest
Twin H and the Format Circuit F (pruned on the `nopressure` condition). The
launcher's job is to turn one configuration (the run directories) into the
exact `evaluate_circuit.py` argument lists, one Slurm job per shard, and to
merge the shards back into one suite directory.

Seams under test, as the spec's Testing Decisions name them:
  * the cell-command generator, a pure function of the configuration;
  * the merge of shards into `cells/` and the suite manifest;
  * the `--dry` sbatch lines;
  * a tiny-model end to end: one faithfulness cell and one delta cell, with a
    `nopressure` run as `--task-from` / operand.
"""

from __future__ import annotations

import importlib
import json
import os
import sys

import pytest

LAUNCH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "outputs", "_launch_format_control")


def _launch_module(name):
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def fc():
    return _launch_module("fc_cells")


FINE = {"family": "fine", "task": "far",
        "runs": {"D": "/r/far_D", "H": "/r/far_H", "F": "/r/far_F"}}
COARSE = {"family": "coarse", "task": "sdr",
          "runs": {"D": "/r/c_D", "H": "/r/c_H", "F": "/r/c_F"},
          "allmlp": "/r/_allmlp_nomb"}
COMMON = ["--ablation", "interchange", "--n-random", "20",
          "--knockout-null-count", "20"]


def by_id(jobs):
    return {j["job"]: j for j in jobs}


# ==============================================================================
# THE GRID
# ==============================================================================

def test_fine_suite_has_nine_atomic_cells_and_six_delta_jobs(fc):
    jobs = by_id(fc.plan_suite("format-control-far-nls0.3", FINE))
    atomic = {f"{c}__{d}" for c in "DHF" for d in ("far", "far_honest", "far_nopressure")}
    deltas = {"D_minus_F__far", "D_and_F__far", "F_minus_D__far",
              "D_minus_H_minus_F__far", "H_minus_D_minus_F__far",
              "F_minus_D_minus_H__far"}
    assert set(jobs) == atomic | deltas


def test_fine_atomic_cell_is_faithfulness_and_knockout_in_one_job(fc):
    jobs = by_id(fc.plan_suite("format-control-far-nls0.3", FINE))
    job = jobs["H__far_nopressure"]
    assert job["cells"] == [{"circuit": "H", "dataset": "far_nopressure",
                             "condition": "nopressure",
                             "roles": ["faithfulness", "knockout"]}]
    assert fc.job_args(job) == [
        "--circuit", "H=/r/far_H", "--task-from", "/r/far_F",
        "--evals", "sanity", "knockout", "null", "pressure", *COMMON,
        "--suite-name", "format-control-far-nls0.3",
        "--output-dir", "outputs/_suites/format-control-far-nls0.3/_shards/H__far_nopressure"]


@pytest.mark.parametrize("job_id, binds, expr", [
    ("D_minus_F__far", ["D", "F"], "D_minus_F=D - F"),
    ("D_and_F__far", ["D", "F"], "D_and_F=D & F"),
    ("F_minus_D__far", ["D", "F"], "F_minus_D=F - D"),
    ("D_minus_H_minus_F__far", ["D", "H", "F"], "D_minus_H_minus_F=D - H - F"),
    ("H_minus_D_minus_F__far", ["D", "H", "F"], "H_minus_D_minus_F=H - D - F"),
    ("F_minus_D_minus_H__far", ["D", "H", "F"], "F_minus_D_minus_H=F - D - H"),
])
def test_fine_delta_is_a_knockout_cell_on_the_d_test_set_at_both_granularities(
        fc, job_id, binds, expr):
    job = by_id(fc.plan_suite("format-control-far-nls0.3", FINE))[job_id]
    label = expr.split("=")[0]
    assert job["cells"] == [
        {"circuit": f"{label}__leaf", "dataset": "far", "condition": "deceptive",
         "roles": ["delta"]},
        {"circuit": f"{label}__head", "dataset": "far", "condition": "deceptive",
         "roles": ["delta"]}]
    runs = {"D": "/r/far_D", "H": "/r/far_H", "F": "/r/far_F"}
    bind_args = [a for n in binds for a in ("--circuit", f"{n}={runs[n]}")]
    assert fc.job_args(job) == [
        *bind_args, "--expr", expr, "--compose-granularity", "both",
        "--task-from", "/r/far_D", "--evals", "knockout", *COMMON,
        "--suite-name", "format-control-far-nls0.3",
        "--output-dir", f"outputs/_suites/format-control-far-nls0.3/_shards/{job_id}"]


def test_coarse_suite_splits_sufficiency_from_heads_only_knockout(fc):
    jobs = by_id(fc.plan_suite("format-control-sdr-coarse-nls0.3", COARSE))
    datasets = ("sdr", "sdr_honest", "sdr_nopressure")
    faith = {f"{c}__{d}" for c in "DHF" for d in datasets}
    ko = {f"{c}_hko__{d}" for c in "DHF" for d in datasets}
    deltas = {f"{x}_hko__sdr" for x in ("D_minus_F", "D_and_F", "F_minus_D",
                                         "D_minus_H_minus_F", "H_minus_D_minus_F",
                                         "F_minus_D_minus_H")}
    assert set(jobs) == faith | ko | deltas

    # Sufficiency on the atomic (expanded) circuit, no knockout: knocking out
    # an expanded coarse mask removes every MLP.
    job = jobs["F__sdr_honest"]
    assert job["cells"] == [{"circuit": "F", "dataset": "sdr_honest", "condition": "honest",
                             "roles": ["faithfulness"]}]
    assert fc.job_args(job) == [
        "--circuit", "F=/r/c_F", "--task-from", "/r/c_H",
        "--evals", "sanity", "null", "pressure", *COMMON,
        "--suite-name", "format-control-sdr-coarse-nls0.3",
        "--output-dir", "outputs/_suites/format-control-sdr-coarse-nls0.3/_shards/F__sdr_honest"]


@pytest.mark.parametrize("job_id, binds, expr", [
    ("D_hko__sdr_nopressure", ["D"], "D_hko=(D) - m"),
    ("D_and_F_hko__sdr", ["D", "F"], "D_and_F_hko=(D & F) - m"),
    ("D_minus_F_hko__sdr", ["D", "F"], "D_minus_F_hko=(D - F) - m"),
    ("F_minus_D_minus_H_hko__sdr", ["D", "H", "F"], "F_minus_D_minus_H_hko=(F - D - H) - m"),
])
def test_every_coarse_knockout_is_rewritten_as_c_minus_m(fc, job_id, binds, expr):
    """The heads-only knockout: the expression minus the all-MLP, no-head
    operand, composed at leaf, where the head-uniform coarse masks make leaf
    membership head membership."""
    job = by_id(fc.plan_suite("format-control-sdr-coarse-nls0.3", COARSE))[job_id]
    label = expr.split("=")[0]
    dataset = job_id.split("__")[1]
    role = "knockout" if job_id.startswith("D_hko") else "delta"
    condition = {"sdr": "deceptive", "sdr_honest": "honest",
                 "sdr_nopressure": "nopressure"}[dataset]
    assert job["cells"] == [{"circuit": f"{label}__leaf", "dataset": dataset,
                             "condition": condition, "roles": [role]}]
    runs = {"D": "/r/c_D", "H": "/r/c_H", "F": "/r/c_F"}
    bind_args = [a for n in binds for a in ("--circuit", f"{n}={runs[n]}")]
    task_from = {"sdr": "/r/c_D", "sdr_honest": "/r/c_H", "sdr_nopressure": "/r/c_F"}[dataset]
    assert fc.job_args(job) == [
        *bind_args, "--circuit", "m=/r/_allmlp_nomb", "--expr", expr,
        "--compose-granularity", "leaf", "--task-from", task_from,
        "--evals", "knockout", *COMMON,
        "--suite-name", "format-control-sdr-coarse-nls0.3",
        "--output-dir", f"outputs/_suites/format-control-sdr-coarse-nls0.3/_shards/{job_id}"]


def test_every_combination_of_circuit_dataset_and_granularity_is_planned(fc):
    """Each (circuit, dataset, granularity) the spec asks for is one cell, and
    no cell is planned twice."""
    for name, cfg, grans in (("format-control-far-nls0.3", FINE, ("leaf", "head")),
                             ("format-control-sdr-nls0.3", dict(FINE, task="sdr"), ("leaf", "head")),
                             ("format-control-sdr-coarse-nls0.3", COARSE, ("leaf",))):
        task = cfg["task"]
        cells = [(c["circuit"], c["dataset"])
                 for j in fc.plan_suite(name, cfg) for c in j["cells"]]
        assert len(cells) == len(set(cells))
        suffix = "_hko" if cfg["family"] == "coarse" else ""
        for x in ("D_minus_F", "D_and_F", "F_minus_D", "D_minus_H_minus_F",
                  "H_minus_D_minus_F", "F_minus_D_minus_H"):
            for g in grans:
                assert (f"{x}{suffix}__{g}", task) in cells
        for c in "DHF":
            for d in (task, f"{task}_honest", f"{task}_nopressure"):
                assert (c, d) in cells
                if cfg["family"] == "coarse":
                    assert (f"{c}_hko__leaf", d) in cells
        # 9 atomic (+ 9 heads-only knockouts for coarse) + 6 deltas x granularities
        expected = 9 + (9 if cfg["family"] == "coarse" else 0) + 6 * len(grans)
        assert len(cells) == expected


# ==============================================================================
# THE F RUNS ARE ONE CONFIGURATION POINT
# ==============================================================================

def test_jobs_that_need_a_missing_run_await_it_and_render_no_args(fc):
    cfg = dict(FINE, runs={"D": "/r/far_D", "H": "/r/far_H", "F": None})
    jobs = by_id(fc.plan_suite("format-control-far-nls0.3", cfg))
    ready = {j for j, v in jobs.items() if not v["awaits"]}
    assert ready == {"D__far", "D__far_honest", "H__far", "H__far_honest"}
    assert jobs["D__far_nopressure"]["awaits"] == ["F"]
    assert jobs["D_minus_H_minus_F__far"]["awaits"] == ["F"]
    with pytest.raises(ValueError, match="awaits F"):
        fc.job_args(jobs["F__far"])


def test_the_dataset_label_is_the_dataset_directory_of_the_condition(fc):
    assert fc.dataset_label("far", "deceptive") == "far"
    assert fc.dataset_label("far", None) == "far"
    assert fc.dataset_label("sdr", "honest") == "sdr_honest"
    assert fc.dataset_label("sdr", "nopressure") == "sdr_nopressure"


# ==============================================================================
# WALLTIME
# ==============================================================================

@pytest.mark.parametrize("estimate, expected", [
    (10.0, "01:00:00"),      # floor of one hour
    (40.0, "01:00:00"),      # 60.0 exactly
    (40.1, "01:15:00"),      # rounds up to the next quarter hour
    (76.6, "02:00:00"),      # 114.9 -> 120
    (300.0, "07:30:00"),     # no cap
])
def test_walltime_is_the_estimate_times_one_and_a_half_in_quarter_hours(fc, estimate, expected):
    assert fc.walltime(estimate) == expected


def test_a_dry_run_log_passes_only_when_it_finished(fc):
    good = ("  TOTAL     76.6 min (1 cell(s))\n\n  Nothing was written. Drop --dry-run to run it.\n")
    assert fc.parse_dryrun_log(good) == (True, 76.6)
    assert fc.parse_dryrun_log("Traceback (most recent call last):\n  boom\n") == (False, None)
    assert fc.parse_dryrun_log("") == (False, None)


# ==============================================================================
# MERGE: shards -> cells/<circuit>/<dataset>/<ablation>
# ==============================================================================

@pytest.fixture(scope="module")
def merge():
    return _launch_module("merge_shards")


def _shard(root, job, circuit, task, condition, accuracy, finished=True):
    """A shard as evaluate_circuit.py writes it with one --task-from: the task
    label is the bare task name whatever the condition of its test set."""
    sh = root / "_shards" / job
    cell = sh / "cells" / circuit / task / "interchange"
    cell.mkdir(parents=True)
    (cell / "knockout.json").write_text(json.dumps({"task": {"knockout": {"accuracy": accuracy}}}))
    (sh / "suite.json").write_text(json.dumps({
        "argv": ["evaluate_circuit.py", job],
        "circuits": [{"label": circuit, "kind": "atomic", "expr": None,
                      "operands": {circuit: f"/r/{circuit}"}}],
        "tasks": [{"label": task, "task": task, "home_run_dir": f"/r/{condition}",
                   "dataset": {"data_dir": "./data/datasets",
                               "deception_condition": condition}}]}))
    if finished:
        (sh / "matrix.json").write_text(json.dumps({"cells": [{
            "circuit": circuit, "circuit_kind": "atomic", "expr": None, "task": task,
            "ablation": "interchange", "out_dir": str(cell), "counts": {},
            "headlines": {"knockout": {"accuracy": accuracy}}, "skipped": {},
            "failures": []}]}))
    return sh


def test_merge_files_each_shard_under_its_test_set_not_its_task_name(tmp_path, merge):
    root = tmp_path / "suite"
    _shard(root, "D__far", "D", "far", "deceptive", 0.01)
    _shard(root, "D__far_honest", "D", "far", "honest", 0.42)
    _shard(root, "H__far_nopressure", "H", "far", "nopressure", 0.0, finished=False)

    report = merge.merge_suite(str(root))

    assert report["merged"] == ["D__far", "D__far_honest"]
    assert report["pending"] == ["H__far_nopressure"]
    k = json.loads((root / "cells" / "D" / "far_honest" / "interchange" / "knockout.json").read_text())
    assert k["task"]["knockout"]["accuracy"] == 0.42
    k = json.loads((root / "cells" / "D" / "far" / "interchange" / "knockout.json").read_text())
    assert k["task"]["knockout"]["accuracy"] == 0.01

    matrix = json.loads((root / "matrix.json").read_text())
    got = {(c["circuit"], c["task"], c["task_name"], c["dataset_condition"], c["shard"])
           for c in matrix["cells"]}
    assert got == {("D", "far", "far", "deceptive", "D__far"),
                   ("D", "far_honest", "far", "honest", "D__far_honest")}
    csv_tasks = {row.split(",")[3] for row in (root / "matrix.csv").read_text().splitlines()[1:]}
    assert csv_tasks == {"far", "far_honest"}

    suite = json.loads((root / "suite.json").read_text())
    assert sorted(t["label"] for t in suite["tasks"]) == ["far", "far_honest"]
    assert suite["shards_pending"] == ["H__far_nopressure"]


def test_merge_checks_each_shard_against_the_manifest(tmp_path, merge):
    root = tmp_path / "suite"
    _shard(root, "D__far_honest", "D", "far", "deceptive", 0.01)   # wrong test set
    expected = {"D__far_honest": [{"circuit": "D", "dataset": "far_honest"}],
                "D__far": [{"circuit": "D", "dataset": "far"}]}
    with pytest.raises(ValueError, match="D__far_honest"):
        merge.merge_suite(str(root), expected_cells=expected)


def test_merge_reports_manifest_jobs_with_no_shard_yet(tmp_path, merge):
    root = tmp_path / "suite"
    _shard(root, "D__far", "D", "far", "deceptive", 0.01)
    expected = {"D__far": [{"circuit": "D", "dataset": "far"}],
                "F__far": [{"circuit": "F", "dataset": "far"}]}
    report = merge.merge_suite(str(root), expected_cells=expected)
    assert report["missing"] == ["F__far"]
    assert json.loads((root / "suite.json").read_text())["shards_missing"] == ["F__far"]


def test_merge_refuses_two_shards_for_one_cell(tmp_path, merge):
    root = tmp_path / "suite"
    _shard(root, "a", "D", "far", "honest", 0.1)
    _shard(root, "b", "D", "far", "honest", 0.2)
    with pytest.raises(ValueError, match="D/far_honest"):
        merge.merge_suite(str(root))


# ==============================================================================
# MANIFEST AND SUBMISSION
# ==============================================================================

@pytest.fixture(scope="module")
def launch():
    return _launch_module("fc_launch")


CONFIG = {
    "format-control-far-nls0.3": {"family": "fine", "task": "far",
                                  "runs": {"D": "/r/far_D", "H": "/r/far_H", "F": None}},
    "format-control-sdr-nls0.3": {"family": "fine", "task": "sdr",
                                  "runs": {"D": "/r/sdr_D", "H": "/r/sdr_H", "F": None}},
    "format-control-sdr-coarse-nls0.3": {"family": "coarse", "task": "sdr",
                                         "runs": {"D": "/r/c_D", "H": "/r/c_H", "F": None},
                                         "allmlp": "/r/_allmlp_nomb"},
}


def test_the_manifest_maps_every_cell_to_its_circuit_and_test_set_condition(launch):
    """Ticket 05's writer finds cells by (circuit, dataset condition): the
    manifest says where each lands under cells/ and which condition that is."""
    manifest = launch.build_manifest(CONFIG)
    index = manifest["suites"]["format-control-far-nls0.3"]["cells"]
    rows = {(r["circuit"], r["condition"]): r for r in index}
    assert rows[("D", "honest")]["path"] == "cells/D/far_honest/interchange"
    assert rows[("F", "nopressure")]["job"] == "F__far_nopressure"
    assert rows[("D_and_F__head", "deceptive")]["path"] == "cells/D_and_F__head/far/interchange"
    assert len(rows) == len(index) == 21
    coarse = {(r["circuit"], r["condition"]): r
              for r in manifest["suites"]["format-control-sdr-coarse-nls0.3"]["cells"]}
    assert coarse[("H_hko__leaf", "nopressure")]["path"] == "cells/H_hko__leaf/sdr_nopressure/interchange"
    assert coarse[("H_hko__leaf", "nopressure")]["roles"] == ["knockout"]


def test_the_manifest_lists_every_cell_and_keeps_recorded_job_ids(launch):
    manifest = launch.build_manifest(CONFIG)
    suites = manifest["suites"]
    assert set(suites) == set(CONFIG)
    n_cells = {s: sum(len(j["cells"]) for j in v["jobs"]) for s, v in suites.items()}
    assert n_cells == {"format-control-far-nls0.3": 21, "format-control-sdr-nls0.3": 21,
                       "format-control-sdr-coarse-nls0.3": 24}
    jobs = {j["job"]: j for j in suites["format-control-far-nls0.3"]["jobs"]}
    assert jobs["D__far"]["args"][:2] == ["--circuit", "D=/r/far_D"]
    assert jobs["F__far"]["args"] is None and jobs["F__far"]["awaits"] == ["F"]
    assert jobs["D__far"]["slurm"] == {"job_id": None}

    jobs["D__far"]["slurm"] = {"job_id": "123", "account": "bgrb-delta-gpu"}
    again = launch.build_manifest(CONFIG, previous=manifest)
    jobs = {j["job"]: j for j in again["suites"]["format-control-far-nls0.3"]["jobs"]}
    assert jobs["D__far"]["slurm"] == {"job_id": "123", "account": "bgrb-delta-gpu"}


def _ready_manifest(launch, estimate=76.6):
    manifest = launch.build_manifest(CONFIG)
    for suite in manifest["suites"].values():
        for job in suite["jobs"]:
            if job["args"] is not None:
                job["dryrun"] = {"log": "x.log", "passed": True, "estimate_min": estimate}
    return manifest


def test_submit_dry_prints_the_exact_sbatch_lines_and_submits_nothing(launch):
    calls = []
    lines = launch.submit(_ready_manifest(launch), dry=True,
                          accounts=["bgrb-delta-gpu", "bimc-delta-gpu"],
                          partition="gpuA100x4,gpuA40x4", suites=["format-control-far-nls0.3"],
                          run=calls.append)
    assert calls == []
    sb = [ln for ln in lines if ln.startswith("sbatch ")]
    assert len(sb) == 4                          # D/H on D/H data; everything else awaits F
    assert sb[0] == (
        "sbatch --account=bgrb-delta-gpu --partition=gpuA100x4,gpuA40x4 --time=02:00:00 "
        "--job-name=fc-far-D__far "
        "--output=outputs/_launch_format_control/logs/format-control-far-nls0.3/D__far_%j.out "
        "scripts/evaluate_circuit.sbatch --circuit D=/r/far_D --task-from /r/far_D "
        "--evals sanity knockout null pressure --ablation interchange --n-random 20 "
        "--knockout-null-count 20 --suite-name format-control-far-nls0.3 "
        "--output-dir outputs/_suites/format-control-far-nls0.3/_shards/D__far")
    assert "--account=bimc-delta-gpu" in sb[1]   # accounts alternate
    assert "# skip F__far: awaits F" in lines


def test_submit_never_sends_a_job_without_a_passing_dry_run(launch):
    manifest = launch.build_manifest(CONFIG)          # no dry-run recorded
    lines = launch.submit(manifest, dry=True, accounts=["beto-delta-gpu"], partition="gpuA40x4",
                          suites=["format-control-far-nls0.3"], run=None)
    assert not [ln for ln in lines if ln.startswith("sbatch ")]
    assert "# skip D__far: no passing dry-run" in lines


def test_submit_records_the_slurm_job_id_and_skips_submitted_jobs(launch, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)                 # submit creates the Slurm log directory
    manifest = _ready_manifest(launch)
    sent = []

    def run(cmd):
        sent.append(cmd)
        return f"Submitted batch job {1000 + len(sent)}"
    launch.submit(manifest, dry=False, accounts=["bgrb-delta-gpu"], partition="gpuA40x4",
                  suites=["format-control-far-nls0.3"], run=run, time="03:00:00")
    assert len(sent) == 4
    assert sent[0][:4] == ["sbatch", "--account=bgrb-delta-gpu", "--partition=gpuA40x4",
                           "--time=03:00:00"]
    assert "D_and_F=D & F" not in sent[0]       # a list, never a shell string
    assert (tmp_path / "outputs" / "_launch_format_control" / "logs"
            / "format-control-far-nls0.3").is_dir()
    jobs = {j["job"]: j for j in manifest["suites"]["format-control-far-nls0.3"]["jobs"]}
    assert jobs["D__far"]["slurm"]["job_id"] == "1001"
    assert jobs["D__far"]["slurm"]["account"] == "bgrb-delta-gpu"

    lines = launch.submit(manifest, dry=True, accounts=["bgrb-delta-gpu"], partition="gpuA40x4",
                          suites=["format-control-far-nls0.3"], run=None)
    assert "# skip D__far: submitted as 1001" in lines


# ==============================================================================
# OVERLAP
# ==============================================================================

def _masks_run(path, heads, neurons, hidden, filename="active_nodes.json"):
    path.mkdir(parents=True, exist_ok=True)
    masks = {"attention_heads": {"0": heads}, "attention_neurons": {"0": neurons},
             "mlp_hidden": {"0": hidden}, "mlp_output": {"0": [0]}}
    (path / filename).write_text(json.dumps({"masks": masks}))
    return str(path)


def test_overlap_is_jaccard_over_heads_and_pooled_fine_units(tmp_path):
    ov = _launch_module("overlap")
    runs = {"D": _masks_run(tmp_path / "D", [1, 1, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0], [1, 0]),
            "H": _masks_run(tmp_path / "H", [1, 0, 1, 0], [1, 1, 0, 0, 1, 1, 0, 0], [1, 1]),
            "F": None}
    paths = ov.write_overlap(str(tmp_path / "suite"),
                             {"family": "fine", "task": "far", "runs": runs})
    table = json.loads((tmp_path / "suite" / "overlap.json").read_text())
    dh = {r["pair"]: r for r in table["pairs"]}["D/H"]
    assert dh["heads"]["jaccard"] == pytest.approx(1 / 3)
    assert dh["fine_units"]["jaccard"] == pytest.approx(3 / 8)   # (2 + 1 + 0) / (6 + 2 + 0)
    assert {r["pair"]: r for r in table["pairs"]}["D/F"]["awaits"] == ["F"]
    md = (tmp_path / "suite" / "overlap.md").read_text()
    assert "| D/H | 0.333 |" in md and "0.375" in md
    assert len(paths) == 2


def test_coarse_overlap_reads_the_unexpanded_heads(tmp_path):
    """The expanded coarse masks put every MLP unit in every circuit; the
    overlap of coarse circuits is read from active_nodes.coarse.json, heads only."""
    ov = _launch_module("overlap")
    runs = {}
    for name, heads in (("D", [1, 1, 0, 0]), ("H", [0, 1, 1, 0]), ("F", [0, 1, 0, 0])):
        _masks_run(tmp_path / name, [1, 1, 1, 1], [1] * 8, [1, 1])      # expanded
        runs[name] = _masks_run(tmp_path / name, heads, [0] * 8, [0, 0],
                                filename="active_nodes.coarse.json")
    ov.write_overlap(str(tmp_path / "suite"), {"family": "coarse", "task": "sdr", "runs": runs})
    pairs = {r["pair"]: r for r in json.loads((tmp_path / "suite" / "overlap.json").read_text())["pairs"]}
    assert pairs["D/H"]["heads"]["jaccard"] == pytest.approx(1 / 3)
    assert pairs["H/F"]["heads"]["jaccard"] == pytest.approx(1 / 2)
    assert pairs["D/F"]["fine_units"] is None


# ==============================================================================
# END TO END: tiny Llama, a deceptive run D and a Format Circuit run F
# ==============================================================================

from tests.test_nopressure_condition import SEQ, tiny_far_data  # noqa: E402,F401

#: Shrink the suite's settings to the tiny model; everything else is the
#: generator's own argument list.
TINY_OVERRIDES = ["--n-random", "2", "--knockout-null-count", "2",
                  "--wikitext-blocks", "2", "--wikitext-block-size", "16",
                  "--wikitext-batch-size", "2", "--gen-examples", "1",
                  "--gen-new-tokens", "2", "--eval-batch-size", "2"]


def _train_tiny(monkeypatch, data_dir, condition):
    import train
    before = set(os.listdir(os.path.join("outputs", "llama-tiny_far"))) \
        if os.path.isdir(os.path.join("outputs", "llama-tiny_far")) else set()
    monkeypatch.setattr(sys, "argv", [
        "train.py", "--model", "llama-tiny", "--task", "far",
        "--deception-condition", condition, "--data-dir", str(data_dir),
        "--no-edge-pruning", "--node-lambda-sparsity", "0.3", "--node-epochs", "1",
        "--batch-size", "2", "--max-seq-length", str(SEQ)])
    train.main()
    (new,) = set(os.listdir(os.path.join("outputs", "llama-tiny_far"))) - before
    return os.path.abspath(os.path.join("outputs", "llama-tiny_far", new))


@pytest.fixture
def fake_wikitext(monkeypatch):
    import torch

    import evaluation.wikitext as W
    from tests.fakes import FAKE_VOCAB_SIZE

    def fake_blocks(ctx):
        g = torch.Generator().manual_seed(7)
        return W._cache_blocks(ctx, torch.randint(
            2, FAKE_VOCAB_SIZE, (ctx.cli.wikitext_blocks, ctx.cli.wikitext_block_size),
            generator=g))
    monkeypatch.setattr(W, "load_wikitext_blocks", fake_blocks)


def test_a_faithfulness_cell_and_a_delta_cell_run_merge_and_audit(
        tiny_far_data, fake_wikitext, monkeypatch, tmp_path, capsys):
    """D on the F test set (`--task-from` the nopressure run) and D-F on the D
    test set, run from the generator's arguments, merged into one suite, then
    flip-audited with the positional-default check."""
    import evaluate_circuit
    fc_cells = _launch_module("fc_cells")
    merge = _launch_module("merge_shards")
    flip = _launch_module("flip_audit_analysis")

    data_dir, _ = tiny_far_data
    run_d = _train_tiny(monkeypatch, data_dir, "deceptive")
    run_f = _train_tiny(monkeypatch, data_dir, "nopressure")
    suite = "format-control-far-nls0.3"
    cfg = {"family": "fine", "task": "far", "runs": {"D": run_d, "H": None, "F": run_f}}
    jobs = {j["job"]: j for j in fc_cells.plan_suite(suite, cfg)}
    picked = ["D__far_nopressure", "D_minus_F__far"]
    for job_id in picked:
        args = fc_cells.job_args(jobs[job_id])
        monkeypatch.setattr(sys, "argv", ["evaluate_circuit.py", *args, *TINY_OVERRIDES])
        assert evaluate_circuit.main() == 0, job_id

    root = os.path.join("outputs", "_suites", suite)
    report = merge.merge_suite(root, {j: jobs[j]["cells"] for j in picked})
    assert report["merged"] == picked and report["cells"] == 3

    cell = os.path.join(root, "cells", "D", "far_nopressure", "interchange")
    for name in ("knockout", "null", "summary"):
        assert os.path.exists(os.path.join(cell, f"{name}.json")), name
    with open(os.path.join(cell, "summary.json")) as f:
        summary = json.load(f)
    assert summary["task_spec"]["dataset"]["deception_condition"] == "nopressure"
    # The F test set already is the no-pressure condition: eval 4 and the
    # eval 2 variant rows are skipped with a recorded reason, not run.
    assert not os.path.exists(os.path.join(cell, "pressure.json"))
    assert summary["skipped"]["pressure"]
    with open(os.path.join(cell, "knockout.json")) as f:
        ko = json.load(f)
    assert ko["task"]["knockout"]["n"] == 4           # the 4-record far_nopressure test set
    assert ko["task"]["null"]["stats"]["accuracy"]["n"] == 2
    assert ko["variants"] and all(v.get("skipped") for v in ko["variants"].values())

    for gran in ("leaf", "head"):
        delta = os.path.join(root, "cells", f"D_minus_F__{gran}", "far", "interchange")
        with open(os.path.join(delta, "knockout.json")) as f:
            ko = json.load(f)
        assert ko["task"]["knockout"]["n"] == 6       # the 6-record far test set
        assert "null" in ko["task"]

    with open(os.path.join(root, "matrix.json")) as f:
        tasks = {(c["circuit"], c["task"]) for c in json.load(f)["cells"]}
    assert tasks == {("D", "far_nopressure"), ("D_minus_F__leaf", "far"),
                     ("D_minus_F__head", "far")}

    flip.main([root, "--data-dir", str(data_dir)])
    with open(os.path.join(root, "flip_audit.json")) as f:
        audit = json.load(f)
    cells = {(c["circuit"], c["task"]): c for c in audit["cells"]}
    assert set(cells) == tasks
    for c in cells.values():
        assert c["rows_aligned"], c["notes"]          # read the right test set
        assert "positional" in c and c["positional"]["verdict"] in (
            "positional default", "content-driven flip")
    exprs = flip.suite_exprs(root)
    assert flip.is_delta("D_minus_F__head", exprs) and not flip.is_delta("D", exprs)
