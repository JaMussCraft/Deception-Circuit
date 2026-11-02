"""B2 ticket T8: the P2 and P3 batch files, the P3 layout and the P1 capture wrapper (plans/B2-plan.md sections 2-4,
section 6 T8; spec.md R3). CPU only: the batch lines are parsed with the real CLI parser, nothing is resolved or run."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "docs" / "research" / "instructed-route" / "jobs"
GROUPS = ROOT / "docs" / "research" / "instructed-route" / "groups"
P2 = JOBS / "B2-p2.batch"
P3 = JOBS / "B2-p3.batch"
LAYOUT = JOBS / "B2-p3-layout.json"
CAPTURE = ROOT / "scripts" / "jobs" / "run_b2_capture.sbatch"

U_EXPR = "U=(Df|Hf|Ds|Hs|De|He)-m"
WISH_STANDIN = "outputs/_launch_instructed_route/standins/sdr_v2_inversion_reported"
SDR_D = "outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323"
D_RUNS = {
    "far": "outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717",
    "sdr": SDR_D,
    "ser": "outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101",
}
H_RUNS = {
    "far": "outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323",
    "sdr": "outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323",
    "ser": "outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323",
}
F_RUNS = {t: f"outputs/_launch_mechanism_v2/evals/standins/{t}_v2_nopressure" for t in ("far", "sdr", "ser")}
P2_POSITIONS = ("all", "readout", "after=pressure_clause,exclude=readout")


def _lines(path):
    from component_analysis.batch import read_batch
    return read_batch(str(path))


def _parse(argv):
    import analyze_components
    return analyze_components.build_parser().parse_args(argv)


def _flag(argv, name):
    """Every value of a repeatable flag, in order."""
    return [argv[i + 1] for i, a in enumerate(argv) if a == name]


def _one(argv, name):
    values = _flag(argv, name)
    assert len(values) == 1, f"{name} appears {len(values)} times in {argv}"
    return values[0]


def _binding(argv):
    """The U binding of a line: its --circuit, --expr, --compose-granularity and --reference values."""
    return (tuple(_flag(argv, "--circuit")), tuple(_flag(argv, "--expr")), tuple(_flag(argv, "--compose-granularity")),
            tuple(_flag(argv, "--reference")))


@pytest.fixture(scope="module")
def p2():
    return _lines(P2)


@pytest.fixture(scope="module")
def p3():
    return _lines(P3)


@pytest.fixture(scope="module")
def layout():
    with open(LAYOUT) as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------- both batch files


@pytest.mark.parametrize("path", [P2, P3], ids=["p2", "p3"])
def test_batch_lines_parse_with_the_cli_parser(path):
    lines = _lines(path)
    assert lines
    for argv in lines:
        cli = _parse(argv)
        assert cli.analyses == "knockout"
        assert cli.knockout_singles == "off"
        assert cli.knockout_scheme == "interchange"
        assert not cli.dry_run


@pytest.mark.parametrize("path", [P2, P3], ids=["p2", "p3"])
def test_every_include_ids_line_sets_n_causal_1000(path):
    for argv in _lines(path):
        assert _flag(argv, "--include-ids"), f"line without --include-ids: {argv}"
        assert _one(argv, "--n-causal") == "1000"
        assert _parse(argv).n_causal == 1000
        assert (ROOT / _one(argv, "--include-ids")).is_file()


@pytest.mark.parametrize("path", [P2, P3], ids=["p2", "p3"])
def test_every_line_has_the_same_u_binding(path):
    lines = _lines(path)
    bindings = {_binding(argv) for argv in lines}
    assert len(bindings) == 1
    circuits, exprs, granularity, references = bindings.pop()
    assert exprs == (U_EXPR,)
    assert granularity == ("leaf",)
    names = [c.split("=", 1)[0] for c in circuits]
    assert names == ["Df", "Hf", "Ds", "Hs", "De", "He", "m"]
    for spec in circuits + references:
        assert (ROOT / spec.split("=", 1)[1]).is_dir(), spec


@pytest.mark.parametrize("path", [P2, P3], ids=["p2", "p3"])
def test_groups_files_exist(path):
    for argv in _lines(path):
        assert (ROOT / _one(argv, "--knockout-groups")).is_file()


@pytest.mark.parametrize("path", [P2, P3], ids=["p2", "p3"])
def test_output_dirs_are_distinct_within_a_file(path):
    # One root per (condition, positions) in P2 and per (seed, role) in P3; tasks separate inside a root.
    keys = []
    for argv in _lines(path):
        task = _task_of(argv)
        keys.append((_one(argv, "--output-dir"), task))
    assert len(keys) == len(set(keys))


def test_p2_and_p3_output_roots_do_not_overlap(p2, p3):
    assert not {_one(a, "--output-dir") for a in p2} & {_one(a, "--output-dir") for a in p3}


def _task_of(argv):
    task_from = _one(argv, "--task-from")
    for task in ("far", "sdr", "ser"):
        if f"_{task}_v2" in task_from or f"/{task}_v2" in task_from:
            return task
    raise AssertionError(f"no task in {task_from}")


# ---------------------------------------------------------------------------- P2


def test_p2_has_two_conditions_by_three_position_sets(p2):
    assert len(p2) == 6
    seen = set()
    for argv in p2:
        task_from = _one(argv, "--task-from")
        assert task_from in (WISH_STANDIN, SDR_D)
        positions = _one(argv, "--knockout-positions")
        assert positions in P2_POSITIONS
        seen.add((task_from, positions))
    assert seen == {(t, p) for t in (WISH_STANDIN, SDR_D) for p in P2_POSITIONS}


def test_p2_lines_are_the_neutral_twin_interchange_on_the_618_ids(p2):
    ids = (GROUPS / "sdr_wish_ids.txt").read_text().split()
    assert len(ids) == len(set(ids)) == 618
    for argv in p2:
        assert _one(argv, "--include-ids") == "docs/research/instructed-route/groups/sdr_wish_ids.txt"
        assert _one(argv, "--knockout-counterfactual") == "neutral_twin"
        assert _one(argv, "--knockout-scheme") == "interchange"
        assert _one(argv, "--knockout-groups") == "docs/research/instructed-route/groups/p2_groups.json"
        assert _one(argv, "--seed") == "0"


def test_p2_wish_and_d_reference_cells_have_distinct_output_dirs(p2):
    wish = {_one(a, "--output-dir") for a in p2 if _one(a, "--task-from") == WISH_STANDIN}
    dref = {_one(a, "--output-dir") for a in p2 if _one(a, "--task-from") == SDR_D}
    assert len(wish) == 3 and len(dref) == 3
    assert not wish & dref
    # Neither may nest inside the other: both write the cell U__leaf/sdr_v2.
    for a in wish:
        for b in dref:
            assert not a.startswith(b.rstrip("/") + "/") and not b.startswith(a.rstrip("/") + "/")


def test_p2_groups_file_names_the_quartet_and_the_nulls():
    with open(GROUPS / "p2_groups.json") as handle:
        groups = json.load(handle)
    assert groups["quartet"] == [["head", 17, h] for h in range(24, 28)]
    assert sum(1 for name in groups if name.startswith("null_d")) == 20
    assert sum(1 for name in groups if name.startswith("kvg_")) == 7


# ---------------------------------------------------------------------------- P3


def _p3_index(p3):
    """{(seed, task, role): argv} with the role read from --task-from."""
    out = {}
    for argv in p3:
        task = _task_of(argv)
        task_from = _one(argv, "--task-from")
        role = {D_RUNS[task]: "D", H_RUNS[task]: "H", F_RUNS[task]: "F"}[task_from]
        seed = int(_one(argv, "--seed"))
        key = (seed, task, role)
        assert key not in out, f"duplicate P3 cell {key}"
        out[key] = argv
    return out


def test_p3_seeds_are_0_1_2_with_seed_0_on_ser_only(p3):
    index = _p3_index(p3)
    assert {k[0] for k in index} == {0, 1, 2}
    expected = {(0, "ser", r) for r in "DHF"} | {(s, t, r) for s in (1, 2) for t in ("far", "sdr", "ser")
                                                  for r in "DHF"}
    assert set(index) == expected
    assert len(p3) == 21


def test_p3_lines_are_item_swap_at_all_positions_with_the_seed_id_file(p3):
    for (seed, task, _role), argv in _p3_index(p3).items():
        assert _one(argv, "--include-ids") == f"docs/research/instructed-route/groups/{task}_seed{seed}_ids.txt"
        assert _one(argv, "--knockout-counterfactual") == "item_swap"
        assert _one(argv, "--knockout-positions") == "all"
        assert _one(argv, "--knockout-groups") == "docs/research/instructed-route/groups/p3_groups.json"


def test_p3_d_h_f_of_a_run_share_ids_and_use_distinct_roots(p3):
    index = _p3_index(p3)
    for seed in (0, 1, 2):
        for task in ("far", "sdr", "ser"):
            cells = {r: index.get((seed, task, r)) for r in "DHF"}
            if not any(cells.values()):
                continue
            assert all(cells.values())
            assert len({_one(a, "--include-ids") for a in cells.values()}) == 1
            assert len({_one(a, "--output-dir") for a in cells.values()}) == 3


def test_p3_seed_id_files_have_100_distinct_ids_and_seeds_do_not_overlap():
    for task in ("far", "sdr", "ser"):
        sets = []
        for seed in (0, 1, 2):
            ids = (GROUPS / f"{task}_seed{seed}_ids.txt").read_text().split()
            assert len(ids) == len(set(ids)) == 100
            sets.append(set(ids))
        assert not (sets[0] & sets[1]) and not (sets[0] & sets[2]) and not (sets[1] & sets[2])


def test_p3_groups_file_holds_the_six_one_member_mlps():
    with open(GROUPS / "p3_groups.json") as handle:
        groups = json.load(handle)
    assert groups == {f"mlp.{l}": [["mlp", l, 0]] for l in (11, 13, 16, 30, 31, 0)}


# ---------------------------------------------------------------------------- P3 layout


def test_layout_names_runs_seed0_to_seed2(layout):
    assert layout["baseline_run"] == "seed0"
    assert layout["replication_runs"] == ["seed1", "seed2"]
    assert set(layout["runs"]) == {"seed0", "seed1", "seed2"}
    assert set(layout["runs"]["seed0"]["cells"]) == {"ser"}
    for run in ("seed1", "seed2"):
        assert set(layout["runs"][run]["cells"]) == {"far", "sdr", "ser"}


def test_layout_cells_are_the_batch_output_cells(layout, p3):
    index = _p3_index(p3)
    for run, body in layout["runs"].items():
        seed = int(run[len("seed"):])
        for task, cells in body["cells"].items():
            assert set(cells) == {"D", "H", "F"}
            for role, cell in cells.items():
                argv = index[(seed, task, role)]
                assert cell == f"{_one(argv, '--output-dir')}/U__leaf/{task}_v2"


def test_layout_run_directories_are_distinct(layout):
    cells = [cell for body in layout["runs"].values() for c in body["cells"].values() for cell in c.values()]
    assert len(cells) == len(set(cells))
    roots = {}
    for run, body in layout["runs"].items():
        roots[run] = {cell.split("/U__leaf/")[0] for c in body["cells"].values() for cell in c.values()}
        assert len(roots[run]) == 3
    runs = list(roots)
    for i, a in enumerate(runs):
        for b in runs[i + 1:]:
            assert not roots[a] & roots[b]


def test_layout_names_existing_group_files(layout):
    assert layout["groups"] == "docs/research/instructed-route/groups/p3_groups.json"
    assert (ROOT / layout["groups"]).is_file()
    for run, body in layout["runs"].items():
        seed = int(run[len("seed"):])
        for task in body["cells"]:
            assert layout["ids"][run][task] == f"docs/research/instructed-route/groups/{task}_seed{seed}_ids.txt"
            assert (ROOT / layout["ids"][run][task]).is_file()


def test_layout_reads_as_not_yet_verified_before_any_run(layout, tmp_path):
    # The reader accepts the layout and, with no cell on disk, names every missing item instead of failing.
    import importlib.util
    spec = importlib.util.spec_from_file_location("b2read", ROOT / "scripts" / "instructed_route_b2_read.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)  # relative cells resolve against the working directory: none exist here
        result = module.read_p3(layout)
    finally:
        os.chdir(cwd)
    assert [v["status"] for v in result["verdicts"]] == ["not yet verified"] * 3


# ---------------------------------------------------------------------------- the P1 capture wrapper


def test_capture_wrapper_is_valid_bash():
    bash = shutil.which("bash")
    assert bash
    subprocess.run([bash, "-n", str(CAPTURE)], check=True)


def test_capture_wrapper_contents():
    text = CAPTURE.read_text()
    directives = [line for line in text.splitlines() if line.startswith("#SBATCH")]
    assert directives
    assert not any("--time" in line or line.startswith("#SBATCH -t") for line in directives)
    assert "set -euo pipefail" in text
    assert "scripts/falsity_probe_capture.py" in text
    assert "docs/research/instructed-route/jobs/B2-p1-plan.json" in text
    assert '"$(pwd -P)"' in text
    assert "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route" in text
    assert "HF_HUB_OFFLINE=1" in text and "TRANSFORMERS_OFFLINE=1" in text
    for var in ("OMP_NUM_THREADS=1", "MKL_NUM_THREADS=1", "OPENBLAS_NUM_THREADS=1"):
        assert var in text
    assert "mgnp" in text or "DC_ACTIVATE" in text


def test_capture_wrapper_refuses_another_cwd(tmp_path):
    bash = shutil.which("bash")
    env = dict(os.environ)
    env.pop("SLURM_SUBMIT_DIR", None)
    env.pop("SLURM_JOB_ID", None)
    done = subprocess.run([bash, str(CAPTURE), "--dry-run"], cwd=str(tmp_path), env=env,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode != 0
    assert "worktree" in done.stderr
