"""D4 batch files of direction deception-divergence. D4(c): the SDR route-closure batch file
`docs/research/deception-divergence/jobs/D4c-sdr.batch`, cloned from instructed-route B1-far.batch with the
composition of mechanism-analysis 05-p3-sdr.batch (the pattern of `tests/test_instructed_route_b1_jobs.py`). D4(a):
`D4a.batch`, the quartet's attention under D and the twin on the B1 held-out ids. CPU only: the lines are parsed with
the real CLI parser and the circuit composition is resolved with the intake `--dry-run` uses (no model, no
tokenizer, no dataset)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "docs" / "research" / "deception-divergence" / "jobs" / "D4c-sdr.batch"
B1_FAR = ROOT / "docs" / "research" / "instructed-route" / "jobs" / "B1-far.batch"
P3_SDR = ROOT / "docs" / "research" / "mechanism-analysis" / "jobs" / "05-p3-sdr.batch"
GROUPS = "docs/research/mechanism-analysis/phase1/groups"
CT = "docs/research/mechanism-analysis/phase3/ct.json"
OUT = "outputs/_analyses/deception-divergence/d4c/sdr"
#: C_t size recorded in ct.json for sdr.
CT_SIZE_SDR = 66


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


def _binding(argv):
    return argv[:argv.index("--task-from") + 2]


def _line():
    lines = _lines(FILE)
    assert len(lines) == 1
    return lines[0]


def test_the_line_parses_with_the_b1_route_closure_settings():
    cli = _parse(_line())
    assert cli.analyses == "route_closure"
    assert not cli.dry_run
    assert cli.route_tests == "both" and cli.route_direction == "both" and cli.route_sweep == "both"
    assert cli.route_path_patching == "on"
    assert cli.route_max_batches == 0
    assert "--timings" not in _line()


def test_the_composition_is_05_p3_sdr_verbatim_and_the_rest_is_b1_far_with_sdr():
    argv = _line()
    assert _binding(argv) == _binding(_lines(P3_SDR)[0])
    far = _lines(B1_FAR)[0]
    rest = argv[argv.index("--task-from") + 2:]
    far_rest = far[far.index("--task-from") + 2:]
    expected = [a.replace("far_heldout", "sdr_heldout") for a in far_rest]
    expected[expected.index("--output-dir") + 1] = OUT
    assert rest == expected


def test_held_out_ids_ct_json_and_the_greedy_k20_deciding_set():
    from component_analysis import route_closure, sampling

    argv = _line()
    assert _one(argv, "--route-ct") == CT
    include = _one(argv, "--include-ids")
    assert include == f"{GROUPS}/sdr_heldout_D_sample.json"
    ids = sampling.read_id_file(str(ROOT / include))
    assert len(ids) == len(set(ids)) == 100
    assert _parse(argv).n_causal == 100 and "--seed" not in argv
    spec = _parse(argv).route_deciding_set
    assert spec == (f"{GROUPS}/sdr_heldout_D.json", "greedy_k20")
    keys = route_closure.load_deciding_set((str(ROOT / spec[0]), spec[1]))
    assert len(keys) == len(set(keys)) == 20


def test_the_output_dir_is_under_this_directions_d4c_root():
    assert _one(_line(), "--output-dir") == OUT


def test_the_header_names_the_timings_file_and_the_readings_out_dir():
    text = FILE.read_text()
    assert ("python analyze_components.py batch docs/research/deception-divergence/jobs/D4c-sdr.batch "
            "--timings outputs/_analyses/deception-divergence/d4c/timings/sdr.json") in text
    assert "--out-dir docs/research/deception-divergence/results/d4c" in text


def test_the_cells_component_set_equals_ct_json_c_t_for_sdr(monkeypatch):
    import analyze_components
    from component_analysis import route_closure

    monkeypatch.chdir(ROOT)
    argv = _line()
    dirs = [spec.split("=", 1)[1] for spec in _flag(argv, "--circuit") + _flag(argv, "--reference")]
    missing = [d for d in dirs if not (ROOT / d).is_dir()]
    if missing:
        pytest.skip(f"circuit run dirs not in this checkout: {missing[0]}")
    cli = _parse(argv)
    resolved = analyze_components.intake.resolve_intake(cli)
    assert len(resolved.circuits) == 1 and len(resolved.tasks) == 1
    assert resolved.tasks[0].name == "sdr_v2"
    components, _rows = analyze_components.head_table_for(resolved.circuits[0], resolved, num_kv_heads=8)
    cell = {tuple(component.key) for component in components}
    ct = route_closure.load_ct(cli.route_ct, "sdr_v2")
    assert len(ct) == CT_SIZE_SDR
    assert cell == ct
    assert {("head", 17, h) for h in (24, 25, 26, 27)} <= cell


def test_ct_json_records_66_components_for_sdr():
    with open(ROOT / CT) as handle:
        assert len(json.load(handle)["tasks"]["sdr"]["members"]["C_t"]) == CT_SIZE_SDR


# ---------------------------------------------------------------------------- D4(a): D4a.batch

D4A = ROOT / "docs" / "research" / "deception-divergence" / "jobs" / "D4a.batch"
D4A_OUT = "outputs/_analyses/deception-divergence/d4a"


def _d4a_lines():
    lines = _lines(D4A)
    assert len(lines) == 2
    return dict(zip(("far", "ser"), lines))


def test_d4a_lines_copy_the_b1_composition_and_read_the_twin_on_the_held_out_ids():
    from component_analysis import sampling

    for task, argv in _d4a_lines().items():
        b1 = _lines(ROOT / "docs" / "research" / "instructed-route" / "jobs" / f"B1-{task}.batch")[0]
        assert _binding(argv) == _binding(b1)
        cli = _parse(argv)
        assert cli.analyses == "attention_patterns" and not cli.dry_run
        assert cli.attention_conditions == ["neutral_twin"]
        assert cli.attention_instances == "causal_sample"
        assert cli.n_causal == 100 and "--seed" not in argv
        include = _one(argv, "--include-ids")
        assert include == f"{GROUPS}/{task}_heldout_D_sample.json"
        assert len(sampling.read_id_file(str(ROOT / include))) == 100
        assert _one(argv, "--output-dir") == f"{D4A_OUT}/{task}"
        assert "--query-positions" not in argv          # the Readout, the default


def test_d4a_header_states_the_question_and_the_run_command():
    text = " ".join(D4A.read_text().split())
    assert "does the query-side signal of F-rte-006 change which positions the quartet attends to" in text
    assert ("python analyze_components.py batch docs/research/deception-divergence/jobs/D4a.batch "
            "--timings outputs/_analyses/deception-divergence/d4a/timings/d4a.json") in text


# ---------------------------------------------------------------------------- Bridges-2 fetch of this direction


def test_b2_fetch_brings_back_the_deception_divergence_root_and_keeps_the_old_globs(tmp_path):
    import os
    import shutil
    import subprocess

    import re
    b2 = ROOT / "scripts" / "remote" / "b2.sh"
    match = re.search(r"^FETCH_ANALYSIS_GLOBS=\((.*)\)\s*$", b2.read_text(), flags=re.M)
    globs = re.findall(r'"([^"]+)"', match.group(1))
    # The old globs stay first and in order; later directions append theirs (neuron-partition*).
    assert globs[:3] == ["mechanism-analysis-*", "instructed-route-b1*", "deception-divergence*"]
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("no bash")
    env = dict(os.environ, DC_DELTA_REPO_ROOT=str(tmp_path))
    done = subprocess.run([bash, str(b2), "fetch", "--dry"], cwd=str(ROOT), env=env,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    (line,) = [one for one in done.stdout.splitlines() if "outputs/_analyses/" in one]
    assert "--include=/deception-divergence*/***" in line
    assert "--include=/instructed-route-b1*/***" in line and "--include=/mechanism-analysis-*/***" in line
