"""The v2 coarse evaluation suite (ticket 06): cell plan, sbatch generator, login-node checker, operands.

Seams: `mv2_cells.plan_cells` (what the suite evaluates, spec 14.G14), `mv2_cells.jobs_for` / `job_args`
(how cells become evaluate_circuit.py invocations), the `gen_cells.py` CLI (sbatch lines from a cluster
profile), `check_cells.check_jobs` (argparse + path + mask resolution on the login node) and
`build_operands` (the all-MLP operand and the nopressure stand-ins). CPU only; nothing evaluates a circuit.
Expected head counts are the recon's literals (reports/06-recon-evals-and-bridges2.md, table A3).
"""

import importlib
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVALS = os.path.join(REPO, "outputs", "_launch_mechanism_v2", "evals")


def _mod(name):
    if EVALS not in sys.path:
        sys.path.insert(0, EVALS)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def cells():
    return _mod("mv2_cells").plan_cells()


def _stage(cells, stage):
    return _mod("mv2_cells").select(cells, stage)


# ---------------------------------------------------------------- the plan

def test_stage_sizes_follow_g14(cells):
    assert len(_stage(cells, "control")) == 2
    assert len(_stage(cells, "1")) == 24
    assert len(_stage(cells, "2")) == 33
    cond = [c for c in cells if c["conditional"]]
    assert len(cond) == 6 and {c["stage"] for c in cond} == {"2"}
    assert all(c["block"] == "conditional_D_minus_H_cross_task" for c in cond)


def test_stage1_per_task_cells(cells):
    far = [c for c in _stage(cells, "1") if c["home_task"] == "far_v2"]
    got = sorted((c["label"], c["kind"], c["condition"]) for c in far)
    assert got == sorted([
        ("D_far", "sufficiency", "deceptive"),
        ("D_far_hko", "knockout", "deceptive"),
        ("H_far", "sufficiency", "honest"),
        ("H_far_hko", "knockout", "honest"),
        ("D_far_and_H_far_suff", "sufficiency", "deceptive"),
        ("D_far_and_H_far_hko", "knockout", "deceptive"),
        ("D_far_minus_H_far_hko", "knockout", "deceptive"),
        ("H_far_minus_D_far_hko", "knockout", "deceptive"),
    ])


def test_two_cell_design_expressions(cells):
    by = {c["label"]: c for c in cells if c["stage"] in ("1", "2")}
    assert by["D_far"]["expr"] == "D_far"
    assert by["D_far_hko"]["expr"] == "(D_far) - m"
    assert by["D_far_and_H_far_suff"]["expr"] == "(D_far & H_far) | m"
    assert by["D_far_minus_H_far_hko"]["expr"] == "(D_far - H_far) - m"
    for c in by.values():
        if c["kind"] == "knockout":
            assert c["evals"] == ["knockout"] and c["expr"].endswith(" - m")
        else:
            assert c["evals"] == ["sanity", "null", "pressure"]
            assert c["expr"].endswith(" | m") or "(" not in c["expr"]


def test_expected_heads_match_the_recon(cells):
    heads = {(c["label"], c["dataset"]): c["expected_heads"] for c in cells}
    # recon A3: D / H heads, D&H / D-H / H-D, shared core 31, exclusives 8 / 14 / 10
    assert heads[("D_far", "far_v2")] == 58 and heads[("H_far", "far_v2_honest")] == 60
    assert heads[("D_ser", "ser_v2")] == 55 and heads[("H_ser", "ser_v2_honest")] == 69
    assert heads[("D_far_and_H_far_hko", "far_v2")] == 32
    assert heads[("D_sdr_minus_H_sdr_hko", "sdr_v2")] == 21
    assert heads[("H_ser_minus_D_ser_hko", "ser_v2")] == 33
    for t in ("far_v2", "sdr_v2", "ser_v2"):
        assert heads[("D_core_hko", t)] == 31 and heads[("D_core_suff", t)] == 31
    assert heads[("D_far_minus_D_sdr_minus_D_ser_hko", "far_v2")] == 8
    assert heads[("D_sdr_minus_D_far_minus_D_ser_hko", "sdr_v2")] == 14
    assert heads[("D_ser_minus_D_far_minus_D_sdr_hko", "ser_v2")] == 10
    assert heads[("D_hko", "sdr")] == heads[("headsko", "sdr")] == 69     # drift control (v1 coarse SDR D)


# ---------------------------------------------------------------- operands

def test_allmlp_operand_is_the_fc_mask_with_a_v2_config(tmp_path):
    bo = _mod("build_operands")
    out = bo.build_allmlp_v2(REPO, str(tmp_path))
    with open(os.path.join(out, "active_nodes.json")) as f:
        built = json.load(f)["masks"]
    with open(os.path.join(REPO, "outputs/_launch_format_control/allmlp_nomb/active_nodes.json")) as f:
        fc = json.load(f)["masks"]
    assert built == fc                     # no heads, no attention, every MLP unit open; v2 keys == v1 keys
    with open(os.path.join(out, "config.json")) as f:
        cfg = json.load(f)
    assert cfg["task"] == "far_v2" and cfg["deception_condition"] == "deceptive"
    assert "operand" in cfg


def test_nopressure_standins_are_config_only(tmp_path):
    bo = _mod("build_operands")
    dirs = bo.build_standins(REPO, str(tmp_path))
    assert sorted(dirs) == ["far", "sdr", "ser"]
    for t, d in dirs.items():
        assert os.listdir(d) == ["config.json"]
        with open(os.path.join(d, "config.json")) as f:
            cfg = json.load(f)
        assert cfg["task"] == f"{t}_v2" and cfg["deception_condition"] == "nopressure"
        assert os.path.isdir(os.path.join(REPO, "data/datasets", f"{t}_v2_nopressure", "test"))


MAIN = "/projects/beto/swong2/Alignment/Deception-Circuit"   # the main checkout (read-only reference)


@pytest.mark.skipif(not os.path.isdir(os.path.join(MAIN, "outputs/llama-8b-instruct_sdr_coarse")),
                    reason="main checkout with the v1 coarse SDR runs not available")
def test_drift_copy_is_byte_identical_to_the_main_checkout(tmp_path):
    bo = _mod("build_operands")
    out = bo.copy_drift_run(MAIN, str(tmp_path))
    with open(os.path.join(out, "provenance.json")) as f:
        prov = json.load(f)
    assert sorted(prov["files"]) == ["active_nodes.json", "config.json"]
    for name, rec in prov["files"].items():
        assert rec["sha256"] == bo.sha256(os.path.join(MAIN, prov["source"], name))
        assert rec["sha256"] == bo.sha256(os.path.join(out, name))


# ---------------------------------------------------------------- jobs

def test_packed_jobs_per_stage(cells):
    mc = _mod("mv2_cells")
    assert len(mc.jobs_for(mc.select(cells, "control"))) == 2
    s1 = mc.jobs_for(mc.select(cells, "1"))
    assert len(s1) == 12 and sum(len(j["cells"]) for j in s1) == 24
    s2 = mc.jobs_for(mc.select(cells, "2"))
    assert len(s2) == 12 and sum(len(j["cells"]) for j in s2) == 33
    s2c = mc.jobs_for(mc.select(cells, "2", include_conditional=True))
    assert [j["job"] for j in s2c] == [j["job"] for j in s2]       # conditional cells join the D-test KO jobs
    assert sum(len(j["cells"]) for j in s2c) == 39
    assert len(mc.jobs_for(mc.select(cells, "1"), pack=False)) == 24
    with pytest.raises(ValueError):
        mc.select(cells, "1", include_conditional=True)


def test_job_args_are_repo_relative_and_follow_the_coarse_recipe(cells):
    mc = _mod("mv2_cells")
    job = next(j for j in mc.jobs_for(mc.select(cells, "1")) if j["job"] == "s1_far__D_ko")
    args = mc.job_args(job)
    assert args[:6] == ["--circuit", "D_far=" + mc.RUNS["far"]["D"], "--circuit", "H_far=" + mc.RUNS["far"]["H"],
                        "--circuit", "m=" + mc.ALLMLP]
    assert "--expr" in args and "D_far_minus_H_far_hko=(D_far - H_far) - m" in args
    assert args[args.index("--compose-granularity") + 1] == "leaf"
    assert args[args.index("--task-from") + 1] == mc.RUNS["far"]["D"]
    assert args[args.index("--evals") + 1] == "knockout"
    assert args[args.index("--output-dir") + 1] == "outputs/_suites/mechanism-v2-coarse/stage1/s1_far__D_ko"
    for a in args:
        assert not a.startswith("/") and "=/" not in a
    nopress = next(j for j in mc.jobs_for(mc.select(cells, "2")) if j["job"] == "s2_sdr__np_ko")
    assert nopress["task_from"] == mc.STANDINS["sdr"] and "sdr_v2_nopressure" not in nopress["binds"].values()
    assert nopress["results"]["D_sdr_hko"] == (
        "outputs/_suites/mechanism-v2-coarse/stage2/s2_sdr__np_ko/cells/D_sdr_hko__leaf/sdr_v2/interchange")


REFERENCE_ARGV = {   # the suite.json of each Delta reference job, main checkout
    "drift_sdr_coarse_D_hko": "outputs/_suites/format-control-sdr-coarse-nls0.3/_shards/D_hko__sdr/suite.json",
    "drift_sdr_coarse_D_headsko": "outputs/llama-8b-instruct_sdr_coarse/"
                                  "nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/evaluations_headsko/suite.json",
}


def _normalized(argv):
    """(flag, values) pairs with run paths replaced by their role; output dir and suite name dropped."""
    def role(path):
        if path.rstrip("/").endswith("260922-092742"):
            return "<sdr coarse D>"
        return "<all-MLP>" if "allmlp" in path else path
    pairs, flag = [], None
    for tok in argv:
        if tok.startswith("--"):
            flag = tok
            pairs.append([tok])
        elif flag is not None:
            if flag == "--circuit":
                name, path = tok.split("=", 1)
                tok = f"{name}={role(path)}"
            elif flag == "--task-from":
                tok = role(tok)
            pairs[-1].append(tok)
    return sorted(tuple(p) for p in pairs if p[0] not in ("--output-dir", "--suite-name"))


@pytest.mark.skipif(not os.path.isdir(os.path.join(MAIN, "outputs/llama-8b-instruct_sdr_coarse")),
                    reason="main checkout with the reference cells not available")
def test_each_drift_job_reproduces_its_reference_argv(cells):
    mc = _mod("mv2_cells")
    jobs = mc.jobs_for(mc.select(cells, "control"))
    assert [j["job"] for j in jobs] == list(REFERENCE_ARGV)
    for job in jobs:
        with open(os.path.join(MAIN, REFERENCE_ARGV[job["job"]])) as f:
            ref = json.load(f)["argv"][1:]
        assert _normalized(mc.job_args(job)) == _normalized(ref), job["job"]


def test_walltime_rule():
    mc = _mod("mv2_cells")
    assert mc.walltime(5) == "01:00:00"                  # one-hour floor (orchestrator ruling)
    assert mc.walltime(41) == "01:15:00"                 # 61.5 -> 75
    assert mc.walltime(5, floor_min=30) == "00:30:00"    # tightened floor
    assert mc.walltime(29, floor_min=30) == "00:45:00"   # 43.5 -> 45
    assert mc.walltime_hours("01:15:00") == 1.25


# ---------------------------------------------------------------- suite file and drift control

def test_suite_file_is_current(cells):
    mc = _mod("mv2_cells")
    suite = mc.load_suite()
    assert suite["cells"] == cells, "suite_v2.json is stale: re-run build_suite.py"
    assert suite["common_args"] == mc.COMMON_ARGS


def test_drift_references_are_recorded_from_delta(cells):
    suite = _mod("mv2_cells").load_suite()
    drift = suite["drift_control"]
    assert [c["job"] for c in drift["cells"]] == ["drift_sdr_coarse_D_hko", "drift_sdr_coarse_D_headsko"]
    primary, secondary = drift["references"]
    assert primary["slurm_job"] == 22895982 and secondary["slurm_job"] == 22316469
    assert primary["cell_job"] == "drift_sdr_coarse_D_hko" and secondary["cell_job"] == "drift_sdr_coarse_D_headsko"
    assert secondary["result"].endswith("drift_sdr_coarse_D_headsko/cells/headsko__leaf/sdr/interchange/knockout.json")
    assert primary["gpu"] == secondary["gpu"] == "A40"
    # literals from the Delta knockout.json files (reports/06-recon A2)
    assert primary["metrics"]["task.knockout.accuracy"] == 0.002
    assert primary["metrics"]["wikitext.kl_per_token"] == pytest.approx(0.364369448099751)
    assert primary["metrics"]["task.null.accuracy.mean"] == pytest.approx(0.3897)
    assert secondary["metrics"]["variants.no_pressure.full_accuracy"] == 0.169
    assert primary["metrics"]["variants.no_pressure.full_accuracy"] == 0.228


def test_drift_compare_reports_per_metric_deltas():
    drift = _mod("drift")
    stats = {m: {"mean": 0.4, "percentile": 0.0, "z": z}
             for m, z in (("accuracy", -1.5), ("logit_diff", -2.2), ("kl_div", -2.8), ("exact_match", -2.1))}
    row = {"accuracy": 0.002, "logit_diff": -1.7, "kl_div": 1.2, "exact_match": 0.002}
    ref = {"task": {"knockout": dict(row), "circuit": dict(row),
                    "flip_summary": {"n_flipped_honest": 998}, "null": {"stats": stats}},
           "wikitext": {"discovered": {"kl_per_token": 0.36, "ppl_ratio": 1.43},
                        "null": {"stats": {"kl_per_token": {"mean": 0.4, "percentile": 45.0}}}},
           "variants": {"no_pressure": {"headline": {"full_accuracy": 0.2, "knockout_accuracy": 0.8}}}}
    m = drift.metrics_of(ref)
    assert m["task.null.separated"] == 3          # accuracy z -1.5 misses the z <= -2 rule
    new = json.loads(json.dumps(ref))
    new["task"]["knockout"]["accuracy"] = 0.005
    rows = drift.compare(m, drift.metrics_of(new))
    assert rows["task.knockout.accuracy"]["delta"] == pytest.approx(0.003)
    assert rows["wikitext.kl_per_token"]["delta"] == 0


# ---------------------------------------------------------------- gen_cells.py

GEN = os.path.join(EVALS, "gen_cells.py")
TICKET = "06-evaluate-coarse-v2-circuits"


def _profile(tmp_path, name="fakeb2", **over):
    vals = {"DC_ACCOUNT": "acct123", "DC_PARTITION": "PART-shared", "DC_GPU_SPEC": "--gpus=h100-80:1",
            "DC_ACTIVATE": "source /env/bin/activate", "DC_HF_HOME": "/hf", "DC_HF_OFFLINE": "1",
            "DC_REPO_ROOT": REPO, "DC_TIME_DEFAULT": "01:00:00"}
    vals.update(over)
    path = tmp_path / f"{name}.env"
    path.write_text("".join(f'export {k}="{v}"\n' for k, v in vals.items() if v is not None))
    return str(path)


def _gen(*args, env=None):
    full = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, GEN, *args], capture_output=True, text=True, env=full, cwd=REPO)


def _sbatch_lines(text):
    import shlex
    return [shlex.split(line) for line in text.splitlines() if line.startswith("sbatch ")]


def test_missing_profile_is_a_clear_error(tmp_path):
    r = _gen("--profile-file", str(tmp_path / "nope.env"), "--stage", "control", "--dry")
    assert r.returncode == 2
    assert "nope.env" in r.stderr and "ticket 07" in r.stderr
    r = _gen("--profile", "no_such_cluster", "--stage", "control", "--dry")
    assert r.returncode == 2 and os.path.join("scripts", "cluster", "no_such_cluster.env") in r.stderr


def test_profile_missing_a_variable_is_refused(tmp_path):
    r = _gen("--profile-file", _profile(tmp_path, DC_GPU_SPEC=None), "--stage", "1", "--dry")
    assert r.returncode == 2 and "DC_GPU_SPEC" in r.stderr


def test_dry_prints_sbatch_lines_built_from_profile_variables_only(tmp_path, cells):
    mc = _mod("mv2_cells")
    r = _gen("--profile-file", _profile(tmp_path), "--stage", "1", "--dry")
    assert r.returncode == 0, r.stderr
    assert f"cd {REPO}\n" in r.stdout
    lines = _sbatch_lines(r.stdout)
    jobs = mc.jobs_for(mc.select(cells, "1"))
    assert len(lines) == len(jobs) == 12
    for argv, job in zip(lines, jobs):
        script = argv.index("scripts/evaluate_circuit.sbatch")
        head, tail = argv[:script], argv[script + 1:]
        assert head[:5] == ["sbatch", "--export=ALL,DC_CLUSTER=fakeb2", "--account=acct123",
                            "--partition=PART-shared", "--gpus=h100-80:1"]
        assert head[5] == "--time=01:00:00"        # every stage-1 job estimates under 40 min on an H100
        assert head[6] == f"--job-name=mv2-1-{job['job']}" and len(head) == 7
        assert tail == mc.job_args(job)
    assert "GPU class H100" in r.stdout


def test_walltime_floor_tightens_estimated_times(tmp_path):
    r = _gen("--profile-file", _profile(tmp_path), "--stage", "1", "--walltime-floor", "30", "--dry")
    assert r.returncode == 0, r.stderr
    lines = _sbatch_lines(r.stdout)
    by_job = {a[a.index("scripts/evaluate_circuit.sbatch") - 1].split("mv2-1-")[1]: a[5] for a in lines}
    assert by_job["s1_far__D_ko"] == "--time=01:00:00"      # 10.5 + 4 x 26 / 4.0 = 36.5 min, x 1.5 -> 60
    assert by_job["s1_far__H_ko"] == "--time=00:30:00"


def test_unknown_gpu_class_falls_back_to_the_profile_default_time(tmp_path):
    r = _gen("--profile-file", _profile(tmp_path, DC_GPU_SPEC="--gres=gpu:1", DC_PARTITION="mystery",
                                        DC_TIME_DEFAULT="02:00:00"), "--stage", "control",
             "--only", "drift_sdr_coarse_D_hko", "--dry")
    assert r.returncode == 0, r.stderr
    (argv,) = _sbatch_lines(r.stdout)
    assert "--time=02:00:00" in argv and "--gres=gpu:1" in argv


def test_generator_hard_codes_no_cluster_setting():
    with open(GEN) as f:
        src = f.read()
    for forbidden in ("delta-gpu", "gpuA40", "gpuA100", "gpuH200", "GPU-shared", "h100-80", "/projects/",
                      "/ocean/", "/u/swong2", "conda activate", "DC_DELTA"):
        assert forbidden not in src


@pytest.mark.parametrize("spec, n", [("--gpus=h100-80:1", 1),
                                     ("--gpus-per-node=h100-80:2 --cpus-per-task=1 --mem=64G", 2),
                                     ("--gpus-per-node=1", 1), ("--gres=gpu:a40:4", 4), ("--gpus=3", 3),
                                     ("--mem=64G", 1)])
def test_gpu_count_reads_every_spec_form(spec, n):
    assert _mod("gen_cells").gpu_count({"DC_GPU_SPEC": spec}) == n


def test_generated_argv_carries_no_value_the_profile_did_not_give(tmp_path, monkeypatch):
    """No real-profile value, no /projects/beto path and no caller environment leaks into the sbatch argv."""
    gc = _mod("gen_cells")
    real = {}
    for name in ("delta", "bridges2"):
        path = gc.profile_path(name)
        if os.path.isfile(path):
            real.update({f"{name}:{k}": v for k, v in gc.load_profile(path).items()})
    prof = _profile(tmp_path, "fakeiso", DC_ACCOUNT="${DC_LEAKY:-acct123}")
    fixture = set(gc.load_profile(prof).values())
    r = _gen("--profile-file", prof, "--stage", "2", "--include-conditional", "--dry",
             env={"DC_LEAKY": "SENTINELX", "DC_DELTA_REPO_ROOT": "/projects/beto/SENTINELX"})
    assert r.returncode == 0, r.stderr
    lines = _sbatch_lines(r.stdout)
    assert len(lines) == 12
    for argv in lines:
        assert "--account=acct123" in argv              # the caller's DC_LEAKY never reaches the profile
        for tok in argv:
            assert "/projects/beto" not in tok and "SENTINELX" not in tok, tok
            for key, value in real.items():
                if value and value not in fixture and len(value) > 3:
                    assert value not in tok, (key, tok)


B2SH = os.path.join(REPO, "scripts", "remote", "b2.sh")


@pytest.mark.skipif(not os.path.isfile(B2SH), reason="ticket 07's scripts/remote/b2.sh not present")
def test_bridges2_submission_through_b2sh_sets_the_jobs_submit_environment(cells):
    """`--via scripts/remote/b2.sh` hands b2.sh exactly its `submit --time T --job-name N -- ARGS` form; b2.sh
    (dry) then runs sbatch on Bridges-2 exporting DC_CLUSTER=bridges2 and DC_B2_ALLOC, the variables the wrapper
    needs to source the Bridges-2 profile instead of Delta's."""
    mc, gc = _mod("mv2_cells"), _mod("gen_cells")
    prof = gc.load_profile(gc.profile_path("bridges2"))
    job = mc.jobs_for(mc.select(cells, "control"))[0]
    argv = gc.via_argv(job, B2SH, "01:00:00")
    assert argv[:7] == [B2SH, "submit", "--time", "01:00:00", "--job-name", "mv2-control-drift_sdr_coarse_D_hko",
                        "--"]
    dry = argv[:2] + ["--dry"] + argv[2:]
    r = subprocess.run(["/bin/bash", *dry], capture_output=True, text=True, cwd=REPO,
                       env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/")})
    assert r.returncode == 0, r.stderr
    import shlex
    (line,) = [x for x in r.stdout.splitlines() if x.startswith("+ ssh ")]
    remote = shlex.split(line[2:])[-1]                     # the command string run on the Bridges-2 login node
    cd, mk, rest = remote.split(" && ", 2)
    assert cd == f"cd {prof['DC_REPO_ROOT']}" and mk == "mkdir -p logs"
    toks = shlex.split(rest)
    alloc = prof["DC_ACCOUNT"]
    # Bridges-2 login nodes set SBATCH_EXPORT=NONE, so the job's environment travels in --export (ticket 07)
    assert toks[0] == "sbatch"
    assert toks[1] == f"--export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC={alloc}"
    sb = 1
    script = toks.index("scripts/evaluate_circuit.sbatch")
    assert toks[sb + 1:script] == (["-A", alloc, "-p", prof["DC_PARTITION"], *shlex.split(prof["DC_GPU_SPEC"]),
                                    "-t", "01:00:00", "--job-name=mv2-control-drift_sdr_coarse_D_hko"])
    assert toks[script + 1:] == mc.job_args(job)          # the evaluate_circuit.py arguments arrive unchanged


def test_conditional_cells_join_stage2_only_when_asked(tmp_path):
    prof = _profile(tmp_path)
    base = _gen("--profile-file", prof, "--stage", "2", "--dry")
    cond = _gen("--profile-file", prof, "--stage", "2", "--include-conditional", "--dry")
    assert base.returncode == cond.returncode == 0
    assert "D_sdr_minus_H_sdr_hko=" not in base.stdout and "D_sdr_minus_H_sdr_hko=" in cond.stdout
    assert _gen("--profile-file", prof, "--stage", "1", "--include-conditional", "--dry").returncode == 2


def _fake_sbatch(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "sbatch_calls.txt"
    stub = bindir / "sbatch"
    stub.write_text(f'#!/bin/bash\necho "$PWD $*" >> {log}\necho "Submitted batch job 4242"\n')
    stub.chmod(0o755)
    return {"PATH": f"{bindir}:{os.environ.get('PATH', '/usr/bin:/bin')}"}, log


def _ledger(tmp_path, reserved=(), section="fakeb2", cap=None):
    sec = {"allocations_gpu_hours": {TICKET: 12.0, "07-other": 1.0},
           "reservations": [{"reservation_id": f"r{i}", "ticket": t, "reserved_gpu_hours": h, "status": st}
                            for i, (t, h, st) in enumerate(reserved)],
           "totals": {"reserved_gpu_hours_in_flight": 0.0, "reconciled_gpu_hours": 0.0,
                      "committed_gpu_hours": 0.0, "by_ticket_committed": {TICKET: 0.0, "07-other": 0.0}}}
    if cap is not None:
        sec["reserved_gpu_hour_cap"] = cap
    data = {"feature": "x", "reservations": [], section: sec}
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(data))
    return path


def test_submit_gates_placeholders_and_routing(tmp_path):
    env, log = _fake_sbatch(tmp_path)
    jobs = str(tmp_path / "eval_jobs.txt")
    led = str(_ledger(tmp_path))
    prof = _profile(tmp_path)
    r = _gen("--profile-file", prof, "--stage", "1", "--submit", "--ledger", led, "--jobs-file", jobs, env=env)
    assert r.returncode == 2 and "--drift-ok" in r.stderr
    r = _gen("--profile-file", prof, "--stage", "2", "--drift-ok", "--submit", "--ledger", led, "--jobs-file", jobs,
             env=env)
    assert r.returncode == 2 and "--user-go" in r.stderr
    r = _gen("--profile-file", _profile(tmp_path, "fakeph", DC_ACCOUNT="__ALLOC__"), "--stage", "control", "--submit",
             "--ledger", led, "--jobs-file", jobs, env=env)
    assert r.returncode == 2 and "placeholder" in r.stderr
    r = _gen("--profile-file", prof, "--stage", "control", "--submit", "--jobs-file", jobs, env=env)
    assert r.returncode == 2 and "--ledger" in r.stderr
    r = _gen("--profile-file", _profile(tmp_path, "fakeremote", DC_REPO_ROOT=str(tmp_path)), "--stage", "control",
             "--submit",
             "--ledger", led, "--jobs-file", jobs, env=env)
    assert r.returncode == 2 and "DC_REPO_ROOT" in r.stderr and "--via" in r.stderr
    assert not log.exists() and not os.path.exists(jobs)


def test_submit_refuses_beyond_the_ticket_allocation(tmp_path):
    env, log = _fake_sbatch(tmp_path)
    prof = _profile(tmp_path)
    led = _ledger(tmp_path, reserved=[(TICKET, 10.5, "completed"), ("07-other", 5.0, "submitted")])
    before = led.read_text()
    r = _gen("--profile-file", str(prof), "--stage", "control", "--submit", "--ledger", str(led),
             "--jobs-file", str(tmp_path / "j.txt"), env=env)
    # 10.5 reserved + 2 x 1 h > 12: only the first job fits; the other ticket's 5 h does not count
    assert r.returncode == 2 and "10.50 GPU-h reserved" in r.stderr and "--first 1" in r.stderr
    assert led.read_text() == before and not log.exists()
    led = _ledger(tmp_path, reserved=[(TICKET, 1.0, "completed")], cap=2.5)
    r = _gen("--profile-file", str(prof), "--stage", "control", "--submit", "--ledger", str(led),
             "--jobs-file", str(tmp_path / "j.txt"), env=env)
    assert r.returncode == 2 and "cap 2.50" in r.stderr and "--first 1" in r.stderr


def test_submit_checks_reserves_and_records_job_ids(tmp_path):
    env, log = _fake_sbatch(tmp_path)
    jobs = tmp_path / "eval_jobs.txt"
    led = _ledger(tmp_path, reserved=[(TICKET, 0.25, "completed")])
    r = _gen("--profile-file", _profile(tmp_path), "--stage", "control", "--submit", "--ledger", str(led),
             "--jobs-file", str(jobs), env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "check: 2 job(s), 0 problem(s)" in r.stdout
    calls = log.read_text().splitlines()
    assert len(calls) == 2 and all(c.startswith(REPO + " --export=ALL,DC_CLUSTER=fakeb2 ") for c in calls)
    rows = [row.split("\t") for row in jobs.read_text().splitlines()]
    assert [r_[1:5] for r_ in rows] == [["fakeb2", "control", "drift_sdr_coarse_D_hko", "4242"],
                                        ["fakeb2", "control", "drift_sdr_coarse_D_headsko", "4242"]]
    sec = json.loads(led.read_text())["fakeb2"]
    new = sec["reservations"][1:]
    assert [(x["ticket"], x["job_id"], x["status"], x["time_limit"], x["reserved_gpu_hours"], x["gpus"])
            for x in new] == [(TICKET, "4242", "submitted", "01:00:00", 1.0, 1)] * 2
    assert new[0]["account"] == "acct123" and new[0]["partition"] == "PART-shared"
    assert "outputs/_launch_mechanism_v2/evals/gen_cells.py" in new[0]["source_sha256"]
    assert sec["totals"]["reserved_gpu_hours_in_flight"] == 2.0
    assert sec["totals"]["reconciled_gpu_hours"] == 0.25
    assert sec["totals"]["by_ticket_committed"] == {TICKET: 2.25, "07-other": 0.0}


def test_submit_to_another_cluster_goes_through_the_dispatcher(tmp_path):
    env, log = _fake_sbatch(tmp_path)
    via_log = tmp_path / "via_calls.txt"
    via = tmp_path / "dispatch.sh"
    via.write_text(f'#!/bin/bash\necho "$*" >> {via_log}\necho "Submitted batch job 77"\n')
    via.chmod(0o755)
    led = _ledger(tmp_path)
    r = _gen("--profile-file", _profile(tmp_path, DC_REPO_ROOT="/remote/repo"), "--stage", "control",
             "--only", "drift_sdr_coarse_D_hko", "--submit", "--ledger", str(led), "--via", str(via),
             "--jobs-file", str(tmp_path / "j.txt"), env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    (call,) = via_log.read_text().splitlines()
    assert call.startswith("submit --time 01:00:00 --job-name mv2-control-drift_sdr_coarse_D_hko -- --circuit D=")
    assert not log.exists()                                   # local sbatch never ran
    (res,) = json.loads(led.read_text())["fakeb2"]["reservations"]
    assert res["job_id"] == "77" and "via" in res["notes"]


def test_dispatcher_without_execute_bit_runs_through_bash_and_a_failed_launch_frees_its_reservation(tmp_path):
    env, _ = _fake_sbatch(tmp_path)
    via = tmp_path / "noexec.sh"                                   # mode 0644, like a checkout without +x
    via.write_text('echo "Submitted batch job 78"\n')
    via.chmod(0o644)
    led = _ledger(tmp_path)
    prof = _profile(tmp_path, DC_REPO_ROOT="/remote/repo")
    common = ["--profile-file", prof, "--stage", "control", "--only", "drift_sdr_coarse_D_hko", "--submit",
              "--ledger", str(led), "--jobs-file", str(tmp_path / "j.txt")]
    r = _gen(*common, "--via", str(via), env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    r = _gen(*common, "--via", str(tmp_path / "missing.sh"), env=env)
    assert r.returncode == 1 and "missing.sh" in r.stderr
    ok, failed = json.loads(led.read_text())["fakeb2"]["reservations"]
    assert (ok["job_id"], ok["status"], ok["reserved_gpu_hours"]) == ("78", "submitted", 1.0)
    assert (failed["job_id"], failed["status"], failed["reserved_gpu_hours"]) == (None, "submit-failed", 0.0)
    assert json.loads(led.read_text())["fakeb2"]["totals"]["reserved_gpu_hours_in_flight"] == 1.0


# ---------------------------------------------------------------- check_cells.py

def test_every_generated_command_checks_clean_on_this_checkout(cells):
    mc, cc = _mod("mv2_cells"), _mod("check_cells")
    jobs = (mc.jobs_for(mc.select(cells, "control")) + mc.jobs_for(mc.select(cells, "1"))
            + mc.jobs_for(mc.select(cells, "2", include_conditional=True)))
    problems = cc.check_jobs(jobs, REPO)
    assert problems == {j["job"]: [] for j in jobs}


def test_checker_reports_broken_jobs(cells):
    mc, cc = _mod("mv2_cells"), _mod("check_cells")
    job = next(j for j in mc.jobs_for(mc.select(cells, "1")) if j["job"] == "s1_sdr__D_ko")
    bad_path = json.loads(json.dumps(job))
    bad_path["binds"]["H_sdr"] = "outputs/no_such_run"
    bad_heads = json.loads(json.dumps(job))
    bad_heads["cells"][1]["expected_heads"] += 1
    bad_cond = json.loads(json.dumps(job))
    bad_cond["task_from"] = mc.STANDINS["sdr"]
    bad_abs = json.loads(json.dumps(job))
    bad_abs["output_dir"] = "/abs/out"
    bad_flag = json.loads(json.dumps(job))
    bad_flag["evals"] = ["knockout", "--bogus-flag"]
    got = cc.check_jobs([dict(bad_path, job="p"), dict(bad_heads, job="h"), dict(bad_cond, job="c"),
                         dict(bad_abs, job="a"), dict(bad_flag, job="f")], REPO)
    assert any("outputs/no_such_run" in p for p in got["p"])
    assert any("D_sdr_and_H_sdr_hko" in p and "heads" in p for p in got["h"])
    assert any("test-set condition nopressure" in p for p in got["c"])
    assert any("relative" in p for p in got["a"])
    assert any("argparse" in p for p in got["f"])


def test_test_set_comes_from_task_from_never_from_the_operand_config(cells, monkeypatch):
    """m's config names far_v2 / deceptive; an H job on sdr_v2_honest must still bind sdr_v2 / honest."""
    mc = _mod("mv2_cells")
    monkeypatch.chdir(REPO)
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    import evaluate_circuit
    from evaluation import circuits
    with open(os.path.join(REPO, mc.ALLMLP, "config.json")) as f:
        assert json.load(f)["task"] == "far_v2"
    parser = evaluate_circuit.build_parser()
    all_jobs = (mc.jobs_for(mc.select(cells, "control")) + mc.jobs_for(mc.select(cells, "1"))
                + mc.jobs_for(mc.select(cells, "2", include_conditional=True)))
    for job in all_jobs:
        assert mc.job_args(job).count("--task-from") == 1, job["job"]
    job = next(j for j in all_jobs if j["job"] == "s1_sdr__H_ko")
    cli = parser.parse_args(mc.job_args(job))
    _, bindings, _, configs, _ = circuits.resolve_circuits(cli)
    (spec,) = circuits.resolve_tasks(cli, bindings, configs)
    assert (spec.args.task, circuits.condition_of(spec.args)) == ("sdr_v2", "honest")


# ---------------------------------------------------------------- stage1_results.py

FC_SUFF = os.path.join(MAIN, "outputs/_suites/format-control-sdr-coarse-nls0.3/cells/D/sdr/interchange")
DRIFT_KO = os.path.join(REPO, "outputs/_suites/mechanism-v2-coarse/control/drift_sdr_coarse_D_hko/cells/D_hko__leaf/"
                        "sdr/interchange")


@pytest.mark.skipif(not os.path.isdir(FC_SUFF), reason="main-checkout format-control cell not available")
def test_sufficiency_metrics_read_a_real_coarse_cell():
    s = _mod("stage1_results").suff_metrics(FC_SUFF)
    # literals from that cell's null.json / pressure.json / sanity.json (v1 coarse SDR D, format-control suite)
    assert s["circuit"]["accuracy"] == 0.967 and s["circuit"]["exact_match"] == 0.974
    assert s["full"]["accuracy"] == 1.0 and s["empty"]["accuracy"] == 0.0
    assert s["null_mean"]["accuracy"] == 0.0 and s["null_beats_all"] == 4
    assert s["pressure"]["no_pressure"]["circuit_accuracy"] == 0.357
    assert s["sanity"]["ok"] is True


@pytest.mark.skipif(not os.path.isdir(DRIFT_KO), reason="drift-control result not fetched")
def test_knockout_metrics_read_the_drift_cell():
    k = _mod("stage1_results").ko_metrics(DRIFT_KO)
    assert k["knockout"]["accuracy"] == 0.003 and k["separated"] == 2 and k["flipped_honest"] == 997
    assert k["wikitext"]["null_percentile"] == 45.0
    assert k["variants"]["no_pressure.full_accuracy"] == 0.224


def test_dh_call_is_strong_only_on_4_of_4_separation():
    sr = _mod("stage1_results")
    base = [{"label": "D_far", "present": True, "full": {"accuracy": 1.0}},
            {"label": "D_far_hko", "present": True, "knockout": {"accuracy": 0.0}, "separated": 4}]

    def dmh(acc, sep):
        return {"label": "D_far_minus_H_far_hko", "present": True, "heads": 26, "knockout": {"accuracy": acc},
                "null_mean": {"accuracy": 0.6}, "separated": sep, "flipped_honest": 700}
    strong = sr.dh_call(base + [dmh(0.25, 4)], "far")
    assert strong["strong"] and strong["recommend_conditional"] and strong["share_of_D_effect"] == 0.75
    weak = sr.dh_call(base + [dmh(0.25, 3)], "far")
    assert not weak["strong"] and not weak["recommend_conditional"]
    assert sr.dh_call(base, "far")["status"] == "missing"


STAGE2_DIR = os.path.join(REPO, "outputs/_suites/mechanism-v2-coarse/stage2")


@pytest.mark.skipif(not os.path.isdir(STAGE2_DIR), reason="stage-2 results not fetched")
def test_stage2_collect_and_transfer_matrix_read_the_fetched_cells(cells):
    s2 = _mod("stage2_results")
    rows = s2.collect(cells, "2", include_conditional=True)
    assert len(rows) == 39 and all(r["present"] for r in rows)
    s1rows = s2.collect(cells, "1")
    ko = dict(s2.transfer_matrix(s1rows + rows, "knockout"))
    # literals from the fetched knockout.json files (D_far heads removed on sdr_v2; home cell from stage 1)
    assert ko["D_far_hko"]["sdr_v2"]["accuracy"] == 0.003 and ko["D_far_hko"]["sdr_v2"]["separated"] == 2
    assert ko["D_far_hko"]["far_v2"]["accuracy"] == 0.0
    core = [r for r in rows if r["label"] == "D_core_hko"]
    assert len(core) == 3 and all(r["heads"] == 31 and r["separated"] == 4 for r in core)
    np_rows = [r for r in rows if r["block"] == "D_on_nopressure"]
    assert {r["dataset"] for r in np_rows} == {"far_v2_nopressure", "sdr_v2_nopressure", "ser_v2_nopressure"}
