"""Ticket 01 of mechanism-analysis: the evaluator-suite launcher in outputs/_launch_mechanism_analysis/.

Seams: the cell plan and its packing (`ma_cells`), the sbatch lines and submissions of `ma_gen_cells.py` (its
--dry / --test-only / --submit output against stub profiles, sbatch and dispatchers), and the login-node checker
`ma_check_cells` against the real masks and datasets of this checkout.

Phase 1A (spec section 4): per task, `(E) - m` knockout cells at leaf on D's test set; sets 1-7 under mean, 3-6
under zero, 6 under interchange; one job per task chaining the schemes. R21: on ser, D-H holds no core head, so set
6 equals set 5 and its three cells are dropped (33 cells; the interchange one is ticket 06's cell of record).
"""

import importlib
import json
import os
import shlex
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_mechanism_analysis")
TICKET = "03-phase1-ablation-replication-and-sweeps"


def _mod(name):
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def cells():
    return _mod("ma_cells").plan_cells()


def _by(cells, **kw):
    return [c for c in cells if all(c[k] == v for k, v in kw.items())]


# ---------------------------------------------------------------- the phase-1A plan

def test_phase1a_has_33_cells_in_the_spec_blocks_without_sers_set_6(cells):
    one_a = _by(cells, stage="1a")
    assert len(one_a) == 33
    for t in ("far", "sdr"):
        assert sorted(c["set"] for c in _by(one_a, home=t, scheme="mean")) == [1, 2, 3, 4, 5, 6, 7]
        assert sorted(c["set"] for c in _by(one_a, home=t, scheme="zero")) == [3, 4, 5, 6]
        assert sorted(c["set"] for c in _by(one_a, home=t, scheme="interchange")) == [6]
    assert sorted(c["set"] for c in _by(one_a, home="ser", scheme="mean")) == [1, 2, 3, 4, 5, 7]
    assert sorted(c["set"] for c in _by(one_a, home="ser", scheme="zero")) == [3, 4, 5]
    assert _by(one_a, home="ser", scheme="interchange") == []


def test_every_cell_is_a_heads_only_knockout_on_ds_own_test_set(cells):
    mc = _mod("ma_cells")
    for c in _by(cells, stage="1a"):
        t = c["home"]
        assert c["kind"] == "knockout" and c["evals"] == ["knockout"]      # never sanity, null or pressure
        assert c["expr"].endswith(") - m") and c["expr"].startswith("(")
        assert (c["test_task"], c["condition"], c["dataset"]) == (f"{t}_v2", "deceptive", f"{t}_v2")
        assert c["task_from"] == mc.RUNS[t]["D"]
        assert c["operands"]["m"] == mc.ALLMLP
        assert c["cell_dir"] == c["label"] + "__leaf"


SETS_FAR = {   # set -> (label, expression before "- m", heads); heads of sets 1-5 and 7 from ticket 06's suite_v2
    1: ("D_far_hko", "D_far", 58),
    2: ("H_far_hko", "H_far", 60),
    3: ("D_core_hko", "D_far & D_sdr & D_ser", 31),
    4: ("D_far_minus_D_sdr_minus_D_ser_hko", "D_far - D_sdr - D_ser", 8),
    5: ("D_far_minus_H_far_hko", "D_far - H_far", 26),
    6: ("D_far_minus_H_far_minus_D_core_hko", "(D_far - H_far) - (D_far & D_sdr & D_ser)", None),
    7: ("D_far_and_H_far_hko", "D_far & H_far", 32),
}


def test_sets_follow_rq_a_with_ticket_06_labels_and_head_counts(cells):
    for c in _by(cells, stage="1a", home="far", scheme="mean"):
        label, expr, heads = SETS_FAR[c["set"]]
        assert (c["label"], c["expr"]) == (label, f"({expr}) - m")
        if heads is not None:
            assert c["expected_heads"] == heads
    excl = {t: _by(cells, stage="1a", home=t, scheme="mean", set=4)[0]["expected_heads"] for t in ("sdr", "ser")}
    assert excl == {"sdr": 14, "ser": 10}


def test_set_6_is_d_minus_h_with_the_core_removed(cells):
    # far and sdr lose 11 and 6 core heads (the evaluator's own composition is checked in the checker test below)
    got = {t: (_by(cells, stage="1a", home=t, scheme="mean", set=5)[0]["expected_heads"],
               _by(cells, stage="1a", home=t, scheme="mean", set=6)[0]["expected_heads"]) for t in ("far", "sdr")}
    assert got == {"far": (26, 15), "sdr": (21, 15)}


def test_sers_set_6_is_dropped_because_it_equals_set_5_and_the_suite_records_why():
    mc = _mod("ma_cells")
    dropped = mc.dropped_cells()
    assert [(d["home"], d["scheme"], d["set"]) for d in dropped] == [
        ("ser", "mean", 6), ("ser", "zero", 6), ("ser", "interchange", 6)]
    for d in dropped:
        assert d["label"] == "D_ser_minus_H_ser_minus_D_core_hko"
        assert d["identity"] == {"set_5": "D_ser - H_ser", "set_6": "(D_ser - H_ser) - (D_far & D_sdr & D_ser)",
                                 "heads_set_5": 19, "heads_set_6": 19, "core_heads_in_set_5": 0}
    inter = [d for d in dropped if d["scheme"] == "interchange"][0]
    assert inter["cell_of_record"] == ("outputs/_suites/mechanism-v2-coarse/stage1/s1_ser__D_ko/cells/"
                                       "D_ser_minus_H_ser_hko__leaf/ser_v2/interchange")
    assert os.path.isfile(os.path.join(REPO, inter["cell_of_record"], "knockout.json"))
    assert all(d["cell_of_record"] is None for d in dropped if d["scheme"] != "interchange")
    with open(mc.SUITE_JSON) as f:
        saved = json.load(f)
    assert saved["dropped_cells"]["cells"] == dropped
    assert "R21" in saved["dropped_cells"]["ruling"]


def test_one_job_per_task_chains_mean_zero_interchange(cells):
    mc = _mod("ma_cells")
    jobs = mc.jobs_for(mc.select(cells, "1a"))
    assert [j["job"] for j in jobs] == ["p1a_far", "p1a_sdr", "p1a_ser"]
    for job in jobs[:2]:
        assert [g["scheme"] for g in job["groups"]] == ["mean", "zero", "interchange"]
        assert [len(g["cells"]) for g in job["groups"]] == [7, 4, 1]
    assert [g["scheme"] for g in jobs[2]["groups"]] == ["mean", "zero"]
    assert [len(g["cells"]) for g in jobs[2]["groups"]] == [6, 3]


def test_scheme_groups_have_distinct_output_dirs_suite_names_and_cell_ids(cells):
    mc = _mod("ma_cells")
    jobs = mc.jobs_for(mc.select(cells, "1a"))
    groups = [g for j in jobs for g in j["groups"]]
    outs = [g["output_dir"] for g in groups]
    assert len(set(outs)) == len(outs) == 8
    assert len({g["suite_name"] for g in groups}) == 8
    assert len({c["cell_id"] for c in _by(cells, stage="1a")}) == 33
    for g in groups:
        assert g["output_dir"].startswith("outputs/_suites/mechanism-analysis/phase1a/")
        assert "mechanism-v2-coarse" not in g["output_dir"]
        for label, path in g["results"].items():
            assert path.startswith(g["output_dir"] + "/cells/") and path.endswith("/" + g["scheme"])


def test_group_args_name_the_scheme_and_the_variant_matched_bank(cells):
    mc = _mod("ma_cells")
    far = mc.jobs_for(mc.select(cells, "1a"))[0]
    mean, zero, inter = (mc.group_args(g) for g in far["groups"])
    assert mean[mean.index("--ablation") + 1] == "mean"
    assert mean[mean.index("--variant-mean-bank") + 1] == "no_pressure"
    assert zero[zero.index("--ablation") + 1] == "zero" and "--variant-mean-bank" not in zero
    assert inter[inter.index("--ablation") + 1] == "interchange" and "--variant-mean-bank" not in inter
    for args in (mean, zero, inter):
        assert args[args.index("--evals") + 1:args.index("--evals") + 2] == ["knockout"]
        assert "sanity" not in args and "null" not in args
        assert args.count("--task-from") == 1
        assert args[args.index("--compose-granularity") + 1] == "leaf"
        assert args[args.index("--n-random") + 1] == "20"
        assert args[args.index("--knockout-null-count") + 1] == "20"
        assert not any(os.path.isabs(a) for a in args)
    chain = mc.chain_args(far)
    assert chain == mean + [":::"] + zero + [":::"] + inter


def test_cost_model_puts_phase_1a_near_seven_h100_hours(cells):
    mc = _mod("ma_cells")
    jobs = mc.jobs_for(mc.select(cells, "1a"))
    est = [mc.job_minutes(j, "H100") for j in jobs]
    # far/sdr: 12 KO cells (26 A40-min each) + three banks + the 7 mean cells' matched no_pressure run (4 A40-min
    # each), at 4x on an H100, + one cold load (10.5) + two warm (0.4): 97.8 min. ser: 9 cells, 6 matched runs,
    # one warm load: 76.9 min.
    assert [round(m, 1) for m in est] == [97.8, 97.8, 76.9]
    walls = [mc.walltime(m) for m in est]
    assert walls == ["02:30:00", "02:30:00", "02:00:00"]
    assert sum(mc.walltime_hours(w) for w in walls) == 7.0


def test_a_mean_group_pays_for_its_matched_no_pressure_runs(cells):
    mc = _mod("ma_cells")
    far = mc.jobs_for(mc.select(cells, "1a"))[0]
    mean, zero = far["groups"][0], far["groups"][1]
    assert mc.group_minutes(mean, "A40", True) == mc.LOAD_MIN["A40"] + 7 * (26.0 + mc.A40_MATCHED_RUN_MIN) + 3 * 2.0
    assert mc.group_minutes(zero, "A40", True) == mc.LOAD_MIN["A40"] + 4 * 26.0


def test_suite_file_is_current(cells):
    mc = _mod("ma_cells")
    with open(mc.SUITE_JSON) as f:
        saved = json.load(f)
    assert saved == json.loads(json.dumps(_mod("ma_build_suite").build()))


# ---------------------------------------------------------------- ma_gen_cells.py

GEN = os.path.join(LAUNCH, "ma_gen_cells.py")
CHAIN = "scripts/evaluate_chain.sbatch"


def _profile(tmp_path, name="fakeb2", **over):
    vals = {"DC_ACCOUNT": "acct123", "DC_PARTITION": "PART-shared", "DC_GPU_SPEC": "--gpus-per-node=h100-80:1",
            "DC_ACTIVATE": "source /env/bin/activate", "DC_HF_HOME": "/hf", "DC_HF_OFFLINE": "1",
            "DC_REPO_ROOT": REPO, "DC_TIME_DEFAULT": "01:00:00"}
    vals.update(over)
    path = tmp_path / f"{name}.env"
    path.write_text("".join(f'export {k}="{v}"\n' for k, v in vals.items() if v is not None))
    return str(path)


def _gen(*args, env=None):
    full = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, GEN, *args], capture_output=True, text=True, env=full, cwd=REPO)


def _lines(text, first):
    return [shlex.split(line) for line in text.splitlines() if line.startswith(first)]


def test_dry_prints_one_chained_sbatch_per_task_from_profile_values(tmp_path, cells):
    mc = _mod("ma_cells")
    r = _gen("--profile-file", _profile(tmp_path), "--stage", "1a", "--dry")
    assert r.returncode == 0, r.stderr
    assert f"cd {REPO}\n" in r.stdout
    lines = _lines(r.stdout, "sbatch ")
    jobs = mc.jobs_for(mc.select(cells, "1a"))
    assert len(lines) == len(jobs) == 3
    for argv, job, t in zip(lines, jobs, ("02:30:00", "02:30:00", "02:00:00")):
        script = argv.index(CHAIN)
        assert argv[:script] == ["sbatch", "--export=ALL,DC_CLUSTER=fakeb2", "--account=acct123",
                                 "--partition=PART-shared", "--gpus-per-node=h100-80:1", f"--time={t}",
                                 f"--job-name=ma-1a-{job['job']}"]
        assert argv[script + 1:] == mc.chain_args(job)
    assert "GPU class H100" in r.stdout
    assert "reservation 7.00 GPU-h" in r.stdout


def test_account_and_partition_overrides_change_the_line_and_the_gpu_class(tmp_path):
    prof = _profile(tmp_path, "fakedelta", DC_GPU_SPEC="--gpus-per-node=1", DC_PARTITION="gpuA40x4")
    r = _gen("--profile-file", prof, "--stage", "1a", "--account", "other-acct", "--partition", "gpuH200x8",
             "--first", "1", "--dry")
    assert r.returncode == 0, r.stderr
    (argv,) = _lines(r.stdout, "sbatch ")
    assert "--account=other-acct" in argv and "--partition=gpuH200x8" in argv
    assert "GPU class H200" in r.stdout


def test_via_dispatcher_lines_name_the_chain_script(tmp_path, cells):
    mc = _mod("ma_cells")
    r = _gen("--profile-file", _profile(tmp_path, DC_REPO_ROOT="/remote/repo"), "--stage", "1a",
             "--via", "scripts/remote/b2.sh", "--dry")
    assert r.returncode == 0, r.stderr
    lines = _lines(r.stdout, "scripts/remote/b2.sh ")
    job = mc.jobs_for(mc.select(cells, "1a"))[0]
    assert lines[0] == ["scripts/remote/b2.sh", "submit", "--script", CHAIN, "--time", "02:30:00",
                        "--job-name", "ma-1a-p1a_far", "--", *mc.chain_args(job)]


B2SH = os.path.join(REPO, "scripts", "remote", "b2.sh")


def test_b2sh_hands_the_chain_and_its_separators_to_sbatch_unchanged(cells):
    mc, gc = _mod("ma_cells"), _mod("ma_gen_cells")
    prof = gc.load_profile(gc.profile_path("bridges2"))
    job = mc.jobs_for(mc.select(cells, "1a"))[0]
    argv = gc.via_argv(job, B2SH, "02:30:00", test_only=True)
    dry = argv[:2] + ["--dry"] + argv[2:]
    r = subprocess.run(["/bin/bash", *dry], capture_output=True, text=True, cwd=REPO,
                       env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/")})
    assert r.returncode == 0, r.stderr
    (line,) = [x for x in r.stdout.splitlines() if x.startswith("+ ssh ")]
    remote = shlex.split(line[2:])[-1]
    cd, mk, rest = remote.split(" && ", 2)
    assert cd == f"cd {prof['DC_REPO_ROOT']}" and mk == "mkdir -p logs"
    toks = shlex.split(rest)
    alloc = prof["DC_ACCOUNT"]
    assert toks[:2] == ["sbatch", f"--export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC={alloc}"]
    assert "--test-only" in toks and "--gpus-per-node=h100-80:1" in toks
    script = toks.index(CHAIN)
    assert toks[script + 1:] == mc.chain_args(job)
    assert toks[script + 1:].count(":::") == 2


def _fake_sbatch(tmp_path, reply="Submitted batch job 4242"):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    log = tmp_path / "sbatch_calls.txt"
    stub = bindir / "sbatch"
    stub.write_text(f'#!/bin/bash\necho "$PWD $*" >> {log}\necho "{reply}"\n')
    stub.chmod(0o755)
    return {"PATH": f"{bindir}:{os.environ.get('PATH', '/usr/bin:/bin')}"}, log


def _ledger(tmp_path, reserved=(), section="fakeb2", cap=None, alloc=19.5):
    sec = {"allocations_gpu_hours": {TICKET: alloc, "02a-other": 1.0},
           "reservations": [{"reservation_id": f"r{i}", "ticket": t, "reserved_gpu_hours": h, "status": st}
                            for i, (t, h, st) in enumerate(reserved)],
           "totals": {"reserved_gpu_hours_in_flight": 0, "reconciled_gpu_hours": 0, "committed_gpu_hours": 0,
                      "committed_su": 0},
           "su_rate_per_h100_gpu_hour": 2}
    if cap is not None:
        sec["reserved_gpu_hour_cap"] = cap
    path = tmp_path / "compute-ledger.json"
    path.write_text(json.dumps({"feature": "x", section: sec}))
    return path


def test_test_only_asks_sbatch_and_writes_no_ledger(tmp_path):
    env, log = _fake_sbatch(tmp_path, reply="sbatch: Job 1 to start at 2026-10-26T00:00:00 using 1 processors")
    jobs = tmp_path / "eval_jobs.txt"
    r = _gen("--profile-file", _profile(tmp_path), "--stage", "1a", "--first", "1", "--test-only",
             "--jobs-file", str(jobs), "--ledger", str(tmp_path / "no-ledger.json"), env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    (call,) = log.read_text().splitlines()
    assert call.startswith(f"{REPO} --test-only --export=ALL,DC_CLUSTER=fakeb2 ")
    assert "to start at" in r.stdout
    assert not jobs.exists() and not (tmp_path / "no-ledger.json").exists()


def test_test_only_through_the_dispatcher_passes_its_flag(tmp_path):
    via_log = tmp_path / "via_calls.txt"
    via = tmp_path / "dispatch.sh"
    via.write_text(f'#!/bin/bash\necho "$*" >> {via_log}\necho "sbatch: Job 9 to start at soon"\n')
    via.chmod(0o755)
    r = _gen("--profile-file", _profile(tmp_path, DC_REPO_ROOT="/remote/repo"), "--stage", "1a", "--first", "1",
             "--via", str(via), "--test-only")
    assert r.returncode == 0, r.stdout + r.stderr
    (call,) = via_log.read_text().splitlines()
    assert call.startswith(f"submit --test-only --script {CHAIN} --time 02:30:00 --job-name ma-1a-p1a_far -- ")


def test_submit_reserves_under_the_ledger_lock_and_records_job_ids(tmp_path):
    env, log = _fake_sbatch(tmp_path)
    jobs = tmp_path / "eval_jobs.txt"
    led = _ledger(tmp_path, reserved=[(TICKET, 0.5, "completed")])
    r = _gen("--profile-file", _profile(tmp_path), "--stage", "1a", "--submit", "--ledger", str(led),
             "--jobs-file", str(jobs), env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "check: 3 job(s), 0 problem(s)" in r.stdout
    assert len(log.read_text().splitlines()) == 3
    assert not os.path.exists(str(led).replace(".json", ".lock"))          # released after every write
    sec = json.loads(led.read_text())["fakeb2"]
    new = sec["reservations"][1:]
    assert [(x["ticket"], x["job_id"], x["status"], x["time_limit"], x["reserved_gpu_hours"]) for x in new] == \
        [(TICKET, "4242", "submitted", "02:30:00", 2.5)] * 2 + [(TICKET, "4242", "submitted", "02:00:00", 2.0)]
    assert new[0]["gpu_spec"] == "--gpus-per-node=h100-80:1"
    assert "outputs/_launch_mechanism_analysis/ma_gen_cells.py" in new[0]["source_sha256"]
    assert "scripts/evaluate_chain.sbatch" in new[0]["source_sha256"]
    assert sec["totals"]["committed_gpu_hours"] == 7.5 and sec["totals"]["committed_su"] == 15.0
    assert [row.split("\t")[3] for row in jobs.read_text().splitlines()] == ["p1a_far", "p1a_sdr", "p1a_ser"]


def test_submit_refuses_while_another_writer_holds_the_ledger_lock(tmp_path):
    env, log = _fake_sbatch(tmp_path)
    led = _ledger(tmp_path)
    lock = tmp_path / "compute-ledger.lock"
    lock.mkdir()
    (lock / "owner").write_text("02a 2026-10-25T11:00")
    before = led.read_text()
    r = _gen("--profile-file", _profile(tmp_path), "--stage", "1a", "--submit", "--ledger", str(led),
             "--jobs-file", str(tmp_path / "j.txt"), env=env)
    assert r.returncode != 0 and "lock" in r.stderr and "02a" in r.stderr
    assert led.read_text() == before and not log.exists() and lock.is_dir()      # never broken


def test_submit_refuses_beyond_the_ticket_allocation(tmp_path):
    env, log = _fake_sbatch(tmp_path)
    led = _ledger(tmp_path, reserved=[(TICKET, 15.0, "completed")])
    r = _gen("--profile-file", _profile(tmp_path), "--stage", "1a", "--submit", "--ledger", str(led),
             "--jobs-file", str(tmp_path / "j.txt"), env=env)
    assert r.returncode == 2 and "--first 1" in r.stderr and not log.exists()


def test_a_failing_owner_write_surfaces_its_own_error_and_releases_the_lock(tmp_path, monkeypatch):
    gc = _mod("ma_gen_cells")
    led = _ledger(tmp_path)
    before = led.read_text()
    real_open = open

    def failing_open(path, *a, **kw):
        if str(path).endswith("owner"):
            raise PermissionError("owner file not writable")
        return real_open(path, *a, **kw)

    monkeypatch.setattr("builtins.open", failing_open)
    with pytest.raises(PermissionError, match="owner file not writable"):
        gc.edit_ledger(str(led), "fakeb2", lambda sec: None, "test")
    monkeypatch.undo()
    assert not os.path.exists(gc.lock_path(str(led)))
    assert led.read_text() == before


def test_only_ma_cells_loads_modules_by_path():
    for name in ("ma_gen_cells.py", "ma_check_cells.py", "ma_build_suite.py"):
        with open(os.path.join(LAUNCH, name)) as f:
            assert "importlib" not in f.read(), name
    mc = _mod("ma_cells")
    assert _mod("ma_gen_cells").v2 is sys.modules["mv2_gen_cells"]
    assert _mod("ma_check_cells").v2check is sys.modules["mv2_check_cells"]
    assert mc.mv2 is sys.modules["mv2_cells"]


def test_generator_hard_codes_no_cluster_setting():
    with open(GEN) as f:
        src = f.read()
    for forbidden in ("delta-gpu", "gpuA40", "gpuA100", "gpuH200", "GPU-shared", "h100-80", "/projects/",
                      "/ocean/", "/u/swong2", "conda activate", "DC_DELTA"):
        assert forbidden not in src


# ---------------------------------------------------------------- ma_check_cells.py

def test_every_generated_group_checks_clean_on_this_checkout(cells):
    mc, cc = _mod("ma_cells"), _mod("ma_check_cells")
    jobs = mc.jobs_for(mc.select(cells, "1a"))
    assert cc.check_jobs(jobs, REPO) == {j["job"]: [] for j in jobs}


def test_checker_reports_broken_groups(cells):
    mc, cc = _mod("ma_cells"), _mod("ma_check_cells")
    jobs = json.loads(json.dumps(mc.jobs_for(mc.select(cells, "1a"))))
    far = jobs[0]
    mean, zero, inter = far["groups"]
    mean["common_args"] = [a for a in mean["common_args"] if a not in ("--variant-mean-bank", "no_pressure")]
    zero["evals"] = ["sanity", "knockout"]
    inter["output_dir"] = zero["output_dir"]
    jobs[1]["groups"][0]["cells"][0]["expected_heads"] += 1
    jobs[2]["groups"][1]["output_dir"] = "outputs/_suites/mechanism-v2-coarse/stage1/x"
    problems = cc.check_jobs(jobs, REPO)
    text = "\n".join(problems["p1a_far"])
    assert "variant-matched" in text
    assert "sanity" in text
    assert "shared" in text
    assert any("heads composed" in p for p in problems["p1a_sdr"])
    assert any("outputs/_suites/mechanism-analysis/phase1a/" in p for p in problems["p1a_ser"])
