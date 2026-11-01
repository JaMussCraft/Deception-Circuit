"""B1 ticket 7: the loop-closure batch files B1-{smoke,far,ser}.batch and the Bridges-2 fetch glob
(plans/B1-plan.md sections 0, 3, 4 and 5 ticket 7). CPU only: the lines are parsed with the real CLI parser and
the circuit composition is resolved with the intake `--dry-run` uses (no model, no tokenizer, no dataset)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "docs" / "research" / "instructed-route" / "jobs"
P3_JOBS = ROOT / "docs" / "research" / "mechanism-analysis" / "jobs"
GROUPS = "docs/research/mechanism-analysis/phase1/groups"
CT = "docs/research/mechanism-analysis/phase3/ct.json"
OUT_ROOT = "outputs/_analyses/instructed-route-b1"
B2 = ROOT / "scripts" / "remote" / "b2.sh"
FILES = {name: JOBS / f"B1-{name}.batch" for name in ("smoke", "far", "ser")}
#: The tasks each file runs, in line order.
TASKS = {"smoke": ["far", "ser"], "far": ["far"], "ser": ["ser"]}
#: C_t sizes recorded in ct.json (plan section 0).
CT_SIZE = {"far": 72, "ser": 78}


def _lines(path):
    from component_analysis.batch import read_batch
    return read_batch(str(path))


def _parse(argv):
    import analyze_components
    return analyze_components.build_parser().parse_args(argv)


def _flag(argv, name):
    return [argv[i + 1] for i, a in enumerate(argv) if a == name]


def _one(argv, name):
    values = _flag(argv, name)
    assert len(values) == 1, f"{name} appears {len(values)} times"
    return values[0]


def _task_of(argv):
    task_from = _one(argv, "--task-from")
    for task in ("far", "sdr", "ser"):
        if f"_{task}_v2_coarse/" in task_from:
            return task
    raise AssertionError(f"no task in {task_from}")


def _binding(argv):
    """The composition part of a line: everything up to and including --task-from VALUE."""
    return argv[:argv.index("--task-from") + 2]


def _all_lines():
    return [(name, argv) for name, path in FILES.items() for argv in _lines(path)]


# ---------------------------------------------------------------------------- parsing


@pytest.mark.parametrize("name", list(FILES))
def test_each_batch_file_parses_with_the_cli_parser(name):
    lines = _lines(FILES[name])
    assert [_task_of(argv) for argv in lines] == TASKS[name]
    for argv in lines:
        cli = _parse(argv)
        assert cli.analyses == "route_closure"
        assert not cli.dry_run
        assert cli.route_tests == "both"
        assert cli.route_direction == "both"
        assert cli.route_sweep == "both"
        assert cli.route_path_patching == "on"   # plan 1.5 and 2.3: path patching on by default
        # --timings belongs to the batch subcommand, never to a line
        assert "--timings" not in argv


@pytest.mark.parametrize("name", list(FILES))
def test_the_header_run_command_names_its_timings_file(name):
    text = FILES[name].read_text()
    assert (f"python analyze_components.py batch docs/research/instructed-route/jobs/B1-{name}.batch "
            f"--timings {OUT_ROOT}/timings/{name}.json") in text


# ---------------------------------------------------------------------------- the grid C_t


@pytest.mark.parametrize("name", list(FILES))
def test_each_line_copies_the_05_p3_composition_verbatim(name):
    for argv in _lines(FILES[name]):
        task = _task_of(argv)
        p3 = _lines(P3_JOBS / f"05-p3-{task}.batch")[0]
        assert _binding(argv) == _binding(p3)


@pytest.mark.parametrize("name", list(FILES))
def test_each_cells_component_set_equals_ct_json_c_t(name, monkeypatch):
    import analyze_components
    from component_analysis import route_closure

    monkeypatch.chdir(ROOT)
    for argv in _lines(FILES[name]):
        dirs = [spec.split("=", 1)[1] for spec in _flag(argv, "--circuit") + _flag(argv, "--reference")]
        missing = [d for d in dirs if not (ROOT / d).is_dir()]
        if missing:
            pytest.skip(f"circuit run dirs not in this checkout: {missing[0]}")
        cli = _parse(argv)
        resolved = analyze_components.intake.resolve_intake(cli)
        assert len(resolved.circuits) == 1 and len(resolved.tasks) == 1
        task = _task_of(argv)
        assert resolved.tasks[0].name == f"{task}_v2"
        components, _rows = analyze_components.head_table_for(resolved.circuits[0], resolved, num_kv_heads=8)
        cell = {tuple(component.key) for component in components}
        ct = route_closure.load_ct(cli.route_ct, resolved.tasks[0].name)
        assert len(ct) == CT_SIZE[task]
        assert cell == ct


# ---------------------------------------------------------------------------- sample, grid file, deciding set


@pytest.mark.parametrize("name", list(FILES))
def test_every_line_names_ct_json_the_held_out_ids_and_n_causal_100(name):
    from component_analysis import sampling

    for argv in _lines(FILES[name]):
        task = _task_of(argv)
        assert _one(argv, "--route-ct") == CT
        include = _one(argv, "--include-ids")
        assert include == f"{GROUPS}/{task}_heldout_D_sample.json"
        ids = sampling.read_id_file(str(ROOT / include))
        assert len(ids) == len(set(ids)) == 100
        assert _one(argv, "--n-causal") == "100"
        assert _parse(argv).n_causal == 100
        # the default seed, as 05-p3; with all 100 ids included it only orders the draw
        assert "--seed" not in argv


@pytest.mark.parametrize("name", list(FILES))
def test_every_line_names_the_greedy_k20_deciding_set_of_its_task(name):
    from component_analysis import route_closure

    for argv in _lines(FILES[name]):
        task = _task_of(argv)
        spec = _parse(argv).route_deciding_set
        assert spec == (f"{GROUPS}/{task}_heldout_D.json", "greedy_k20")
        keys = route_closure.load_deciding_set((str(ROOT / spec[0]), spec[1]))
        assert len(keys) == len(set(keys)) == 20


# ---------------------------------------------------------------------------- output dirs and the smoke


def test_output_dirs_are_distinct_across_all_three_files_and_under_the_b1_root():
    dirs = [_one(argv, "--output-dir") for _name, argv in _all_lines()]
    assert len(dirs) == len(set(dirs)) == 4
    for one in dirs:
        assert one.startswith(OUT_ROOT + "/")
    # no output dir nests inside another
    for a in dirs:
        for b in dirs:
            assert a == b or not a.startswith(b.rstrip("/") + "/")
    expected = {("smoke", "far"): f"{OUT_ROOT}/smoke/far", ("smoke", "ser"): f"{OUT_ROOT}/smoke/ser",
                ("far", "far"): f"{OUT_ROOT}/far", ("ser", "ser"): f"{OUT_ROOT}/ser"}
    assert {(name, _task_of(argv)): _one(argv, "--output-dir") for name, argv in _all_lines()} == expected


def test_the_smoke_lines_carry_route_max_batches_1_and_the_task_lines_do_not():
    for name, argv in _all_lines():
        if name == "smoke":
            assert _one(argv, "--route-max-batches") == "1"
            assert _parse(argv).route_max_batches == 1
        else:
            assert "--route-max-batches" not in argv
            assert _parse(argv).route_max_batches == 0


def test_smoke_and_task_lines_differ_only_in_max_batches_and_output_dir():
    smoke = {_task_of(argv): argv for argv in _lines(FILES["smoke"])}
    for task in ("far", "ser"):
        (full,) = _lines(FILES[task])
        strip = {"--route-max-batches", "--output-dir"}

        def rest(argv):
            out, skip = [], False
            for a in argv:
                if skip:
                    skip = False
                    continue
                if a in strip:
                    skip = True
                    continue
                out.append(a)
            return out

        assert rest(smoke[task]) == rest(full)


# ---------------------------------------------------------------------------- the fetch glob


def _fetch_globs():
    match = re.search(r"^FETCH_ANALYSIS_GLOBS=\((.*)\)\s*$", B2.read_text(), flags=re.M)
    assert match, "FETCH_ANALYSIS_GLOBS not found in b2.sh"
    return re.findall(r'"([^"]+)"', match.group(1))


def test_b2_fetch_globs_include_the_b1_root_and_keep_mechanism_analysis():
    import fnmatch

    globs = _fetch_globs()
    assert "instructed-route-b1*" in globs
    assert "mechanism-analysis-*" in globs
    top = OUT_ROOT.split("/")[-1]
    assert any(fnmatch.fnmatch(top, glob) for glob in globs)


def test_b2_fetch_dry_print_includes_the_b1_glob(tmp_path):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("no bash")
    env = dict(os.environ, DC_DELTA_REPO_ROOT=str(tmp_path))
    done = subprocess.run([bash, str(B2), "fetch", "--dry"], cwd=str(ROOT), env=env,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    analyses = [line for line in done.stdout.splitlines() if "outputs/_analyses/" in line]
    assert len(analyses) == 1
    assert "--include=/instructed-route-b1*/***" in analyses[0]
    assert analyses[0].rstrip().endswith(f"{tmp_path}/outputs/_analyses/")
    assert not (tmp_path / "outputs").exists()   # --dry creates nothing


def test_the_ct_json_task_names_are_the_ones_the_lines_use():
    with open(ROOT / CT) as handle:
        tasks = json.load(handle)["tasks"]
    for task in ("far", "ser"):
        assert len(tasks[task]["members"]["C_t"]) == CT_SIZE[task]
