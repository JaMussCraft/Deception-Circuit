"""Ticket 01 of mechanism-analysis: dispatch and wrapper infrastructure.

Seams (the ones the ticket names):

  * scripts/evaluate_chain.sbatch at run time: one Slurm job, several evaluate_circuit.py processes in a row
    (one per ablation scheme), each through the tested scripts/evaluate_circuit.sbatch wrapper;
  * scripts/analyze_components.sbatch at run time: the cluster-profile block of evaluate_circuit.sbatch;
  * scripts/remote/b2.sh --dry output: the branch it syncs and what `fetch` brings back;
  * scripts/cluster/delta.env: the Delta repo root and its override.

Everything runs bash with stubs on the CPU, the way tests/test_cluster_profiles.py does; nothing touches Slurm,
SSH or a GPU.
"""

import os
import shlex
import subprocess

from tests.test_cluster_profiles import B2, FAKE_BASHRC, STUB_PYTHON, _b2, _b2_profile, _bash, _commands, _read

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sandbox(tmp_path, scripts, profiles, python=STUB_PYTHON):
    """A submit dir holding the named wrappers and profiles, a fake HOME and a stub python on PATH."""
    submit = tmp_path / "repo"
    (submit / "scripts" / "cluster").mkdir(parents=True)
    for rel in scripts:
        with open(os.path.join(REPO, rel)) as fh:
            (submit / rel).write_text(fh.read())
    for name, text in profiles.items():
        (submit / "scripts" / "cluster" / f"{name}.env").write_text(text)
    home = tmp_path / "home"
    home.mkdir()
    (home / ".bashrc").write_text(FAKE_BASHRC)
    stubs = tmp_path / "bin"
    stubs.mkdir()
    (stubs / "python").write_text(python)
    (stubs / "python").chmod(0o755)
    env = {"HOME": str(home), "PATH": f"{stubs}:/usr/bin:/bin", "SLURM_SUBMIT_DIR": str(submit)}
    return submit, env


def _job(submit, env, script, *args):
    return subprocess.run(["/bin/bash", str(submit / script), *args], cwd=str(submit), env=env,
                          capture_output=True, text=True)


# ---------------------------------------------------------------------------------------------------------
# scripts/evaluate_chain.sbatch

CHAIN = "scripts/evaluate_chain.sbatch"
EVAL = "scripts/evaluate_circuit.sbatch"


def test_chain_runs_one_evaluator_process_per_group_in_order(tmp_path):
    submit, env = _sandbox(tmp_path, [CHAIN, EVAL], {"delta": _read("delta")})
    out = _job(submit, env, CHAIN, "--expr", "a=(D) - m", "--ablation", "mean", ":::",
               "--ablation", "zero", ":::", "--ablation", "interchange")
    assert out.returncode == 0, out.stderr
    argvs = [line for line in out.stdout.splitlines() if line.startswith("argv=")]
    assert argvs == ["argv=evaluate_circuit.py --expr a=(D) - m --ablation mean",
                     "argv=evaluate_circuit.py --ablation zero",
                     "argv=evaluate_circuit.py --ablation interchange"]
    # each group goes through the evaluate wrapper, so it activates the profile's env every time
    assert out.stdout.count("ACTIVATED=conda:mgnp") == 3


def test_chain_without_a_separator_is_one_evaluator_run(tmp_path):
    submit, env = _sandbox(tmp_path, [CHAIN, EVAL], {"delta": _read("delta")})
    out = _job(submit, env, CHAIN, "outputs/run_a", "--evals", "knockout")
    assert out.returncode == 0, out.stderr
    assert [x for x in out.stdout.splitlines() if x.startswith("argv=")] == [
        "argv=evaluate_circuit.py outputs/run_a --evals knockout"]


def test_chain_runs_every_group_after_a_failure_and_exits_nonzero(tmp_path):
    failing = STUB_PYTHON + 'case "$*" in *--fail*) exit 3 ;; esac\n'
    submit, env = _sandbox(tmp_path, [CHAIN, EVAL], {"delta": _read("delta")}, python=failing)
    out = _job(submit, env, CHAIN, "--ablation", "mean", "--fail", ":::", "--ablation", "zero")
    assert out.returncode == 3
    assert [x for x in out.stdout.splitlines() if x.startswith("argv=")] == [
        "argv=evaluate_circuit.py --ablation mean --fail", "argv=evaluate_circuit.py --ablation zero"]
    assert "group 1 of 2 exited 3" in out.stdout


def test_chain_refuses_an_empty_group_before_running_anything(tmp_path):
    submit, env = _sandbox(tmp_path, [CHAIN, EVAL], {"delta": _read("delta")})
    for args in ([":::", "--ablation", "zero"], ["--ablation", "zero", ":::"], ["a", ":::", ":::", "b"], []):
        out = _job(submit, env, CHAIN, *args)
        assert out.returncode == 2, args
        assert "argv=" not in out.stdout


def test_chain_honours_the_cluster_profile_of_each_group(tmp_path):
    activate = tmp_path / "activate"
    activate.write_text("export ACTIVATED=packed-env\n")
    profile = (f'export DC_ACTIVATE="source {activate}"\nexport DC_HF_HOME="{tmp_path}/hf"\n'
               'export DC_HF_OFFLINE="1"\n')
    submit, env = _sandbox(tmp_path, [CHAIN, EVAL], {"delta": _read("delta"), "remote": profile})
    env["DC_CLUSTER"] = "remote"
    out = _job(submit, env, CHAIN, "--ablation", "mean", ":::", "--ablation", "zero")
    assert out.returncode == 0, out.stderr
    assert out.stdout.count("HF_HUB_OFFLINE=1") == 2
    assert out.stdout.count("ACTIVATED=packed-env") == 2


def test_chain_parses_as_bash_and_keeps_the_evaluator_header():
    out = _bash(f"/bin/bash -n {os.path.join(REPO, CHAIN)}")
    assert out.returncode == 0, out.stderr
    with open(os.path.join(REPO, CHAIN)) as fh:
        header = [x for x in fh.read().splitlines() if x.startswith("#SBATCH")]
    assert "#SBATCH --account=beto-delta-gpu" in header
    assert "#SBATCH --gpus-per-node=1" in header
    assert "#SBATCH --output=logs/evaluate_chain_%j.out" in header


# ---------------------------------------------------------------------------------------------------------
# scripts/analyze_components.sbatch: the evaluate wrapper's profile block

ANALYZE = "scripts/analyze_components.sbatch"


def test_analyze_without_dc_cluster_runs_as_the_pre_profile_wrapper(tmp_path):
    submit, env = _sandbox(tmp_path, [ANALYZE], {"delta": _read("delta")})
    out = _job(submit, env, ANALYZE, "--circuit", "c=outputs/run_a", "--analyses", "knockout")
    assert out.returncode == 0, out.stderr
    # Before: cd to the submit dir, activate mgnp through ~/.bashrc (which sets HF_HOME), no offline flag, the
    # arguments untouched. Added, as in the evaluate wrapper (orchestrator, 2026-10-24): BLAS threads pinned to 1.
    assert out.stdout.splitlines() == [
        f"cwd={submit}",
        "argv=analyze_components.py --circuit c=outputs/run_a --analyses knockout",
        "HF_HOME=/work/nvme/beto/swong2",
        "HF_HUB_OFFLINE=<unset>",
        "HF_DATASETS_OFFLINE=<unset>",
        "TRANSFORMERS_OFFLINE=<unset>",
        "ACTIVATED=conda:mgnp",
        "OMP_NUM_THREADS=1",
    ]
    assert out.stderr.strip() == "conda activate mgnp"


def test_analyze_with_an_offline_profile_never_touches_bashrc(tmp_path):
    activate = tmp_path / "activate"
    activate.write_text("export ACTIVATED=packed-env\n")
    profile = (f'export DC_ACTIVATE="source {activate}"\nexport DC_HF_HOME="{tmp_path}/hf"\n'
               'export DC_HF_OFFLINE="1"\n')
    submit, env = _sandbox(tmp_path, [ANALYZE], {"delta": _read("delta"), "remote": profile})
    env["DC_CLUSTER"] = "remote"
    out = _job(submit, env, ANALYZE, "--circuit", "c=outputs/x")
    assert out.returncode == 0, out.stderr
    lines = out.stdout.splitlines()
    for want in (f"HF_HOME={tmp_path}/hf", "HF_HUB_OFFLINE=1", "HF_DATASETS_OFFLINE=1", "TRANSFORMERS_OFFLINE=1",
                 "ACTIVATED=packed-env", "argv=analyze_components.py --circuit c=outputs/x"):
        assert want in lines
    assert "conda" not in out.stderr


def test_analyze_refuses_an_unknown_cluster_before_running_anything(tmp_path):
    submit, env = _sandbox(tmp_path, [ANALYZE], {"delta": _read("delta")})
    env["DC_CLUSTER"] = "nowhere"
    out = _job(submit, env, ANALYZE, "outputs/run_a")
    assert out.returncode != 0 and "nowhere" in out.stderr and "argv=" not in out.stdout


def test_analyze_wrapper_parses_as_bash():
    out = _bash(f"/bin/bash -n {os.path.join(REPO, ANALYZE)}")
    assert out.returncode == 0, out.stderr


# ---------------------------------------------------------------------------------------------------------
# scripts/cluster/delta.env: the Delta repo root


def _delta_root(env=None):
    out = _bash(f"set -euo pipefail; source {os.path.join(REPO, 'scripts', 'cluster', 'delta.env')}; "
                'echo "$DC_REPO_ROOT"', env=env)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def test_delta_repo_root_follows_dc_delta_repo_root():
    assert _delta_root({"DC_DELTA_REPO_ROOT": "/some/other/checkout"}) == "/some/other/checkout"


def test_b2_syncs_and_fetches_into_the_overridden_delta_root(tmp_path):
    out = _b2(tmp_path, "fetch", "--dry", "outputs/_suites/x")
    assert out.returncode == 0, out.stderr
    [cmd] = _commands(out)
    assert cmd.split()[-1] == str(tmp_path / "delta_repo" / "outputs" / "_suites" / "x") + "/"


# ---------------------------------------------------------------------------------------------------------
# scripts/remote/b2.sh: the branch, and the analysis cells in `fetch`


def _sync(tmp_path, *args, env=None):
    out = _b2(tmp_path, "sync-code", "--dry", *args, extra_env=env)
    assert out.returncode == 0, out.stderr
    return "\n".join(_commands(out))


def test_b2_sync_code_defaults_to_the_mechanism_datasets_branch(tmp_path):
    cmd = _sync(tmp_path)
    assert "fetch origin +mechanism-datasets:refs/remotes/origin/mechanism-datasets" in cmd
    assert "merge --ff-only origin/mechanism-datasets" in cmd
    assert "clone --branch mechanism-datasets" in cmd


def test_b2_sync_code_takes_the_branch_from_dc_b2_branch(tmp_path):
    cmd = _sync(tmp_path, env={"DC_B2_BRANCH": "mechanism-analysis"})
    assert "mechanism-datasets" not in cmd
    # forced refspec: a force-pushed branch still updates the remote-tracking ref
    assert "fetch origin +mechanism-analysis:refs/remotes/origin/mechanism-analysis" in cmd
    assert "merge --ff-only origin/mechanism-analysis" in cmd
    assert "clone --branch mechanism-analysis" in cmd
    # a clone that has never seen the branch makes a tracking branch from the fetched remote one; whether the
    # branch exists is asked, so a checkout that fails for a real reason is not retried as a branch creation
    assert "show-ref --verify --quiet refs/heads/mechanism-analysis" in cmd
    assert "checkout -b mechanism-analysis --track origin/mechanism-analysis" in cmd
    assert "2>/dev/null" not in cmd


def test_b2_branch_flag_overrides_the_environment(tmp_path):
    cmd = _sync(tmp_path, "--branch", "feature-x", env={"DC_B2_BRANCH": "mechanism-analysis"})
    assert "fetch origin +feature-x:refs/remotes/origin/feature-x" in cmd and "mechanism-analysis" not in cmd


def test_b2_usage_is_literal_text(tmp_path):
    for args in ((), ("--help",)):
        out = _b2(tmp_path, *args)
        assert out.returncode == 2
        lines = out.stderr.splitlines()
        assert lines[0].startswith("usage: scripts/remote/b2.sh sync-code")
        assert any("DC_B2_BRANCH" in x for x in lines)
        assert not any(x.startswith("#") for x in lines)


# ---- sync-code's remote command, run for real against local git repositories (no SSH, no network)

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


def _git(cwd, *args):
    out = _bash("git " + " ".join(shlex.quote(a) for a in args), env=GIT_ENV, cwd=str(cwd))
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def _commit(work, name, text):
    (work / name).write_text(text)
    _git(work, "add", name)
    _git(work, "commit", "-q", "-m", name)
    return _git(work, "rev-parse", "HEAD")


def _remote_sync(tmp_path, clone, branch):
    """b2.sh sync-code --dry's remote command, with the clone path, run here in bash."""
    profile = tmp_path / "b2_local.env"
    profile.write_text(open(_b2_profile(tmp_path)).read() + f'export DC_REPO_ROOT="{clone}"\n')
    env = {"DC_B2_PROFILE": str(profile), "DC_DELTA_REPO_ROOT": str(tmp_path / "delta_repo")}
    out = _bash(f"/bin/bash {B2} sync-code --dry --branch {branch}", env=env)
    assert out.returncode == 0, out.stderr
    [line] = _commands(out)
    remote = shlex.split(line)[-1]
    return _bash(remote, env=GIT_ENV, cwd=str(tmp_path))


def _origin_and_clone(tmp_path):
    origin, work, clone = tmp_path / "origin.git", tmp_path / "work", tmp_path / "clone"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(work))
    _git(work, "checkout", "-q", "-b", "main")
    _commit(work, "a.txt", "a")
    _git(work, "push", "-q", "origin", "main")
    _git(tmp_path, "clone", "-q", str(origin), str(clone))      # the Bridges-2 clone, made before the branch
    _git(work, "checkout", "-q", "-b", "feat")
    return origin, work, clone


def test_sync_code_tracks_a_new_branch_then_fast_forwards_it(tmp_path):
    _, work, clone = _origin_and_clone(tmp_path)
    first = _commit(work, "b.txt", "b")
    _git(work, "push", "-q", "origin", "feat")
    out = _remote_sync(tmp_path, clone, "feat")
    assert out.returncode == 0, out.stderr
    assert f"remote_head={first}" in out.stdout
    assert _git(clone, "rev-parse", "--abbrev-ref", "HEAD") == "feat"
    second = _commit(work, "c.txt", "c")
    _git(work, "push", "-q", "origin", "feat")
    out = _remote_sync(tmp_path, clone, "feat")
    assert out.returncode == 0 and f"remote_head={second}" in out.stdout, out.stderr


def test_sync_code_follows_a_force_pushed_branch_and_says_so(tmp_path):
    _, work, clone = _origin_and_clone(tmp_path)
    old = _commit(work, "b.txt", "b")
    _git(work, "push", "-q", "origin", "feat")
    assert _remote_sync(tmp_path, clone, "feat").returncode == 0
    _git(work, "reset", "-q", "--hard", "HEAD~1")
    new = _commit(work, "b2.txt", "rewritten")
    _git(work, "push", "-q", "--force", "origin", "feat")
    out = _remote_sync(tmp_path, clone, "feat")
    assert out.returncode == 0, out.stderr
    assert f"remote_head={new}" in out.stdout
    assert "force-pushed" in out.stderr and old in out.stderr          # the old head is printed for recovery


def test_sync_code_stops_on_a_real_checkout_error_with_gits_message(tmp_path):
    _, work, clone = _origin_and_clone(tmp_path)
    _commit(work, "a.txt", "changed on feat")
    _git(work, "push", "-q", "origin", "feat")
    assert _remote_sync(tmp_path, clone, "feat").returncode == 0  # the clone now has a local feat branch
    _git(clone, "checkout", "-q", "main")
    (clone / "a.txt").write_text("a local edit on Bridges-2")      # in the way of checking feat out again
    out = _remote_sync(tmp_path, clone, "feat")
    assert out.returncode != 0
    assert "already exists" not in out.stderr
    assert "a.txt" in out.stderr                                      # git's own reason
    assert _git(clone, "rev-parse", "--abbrev-ref", "HEAD") == "main"


def test_b2_refuses_a_branch_name_that_is_not_a_plain_ref(tmp_path):
    out = _b2(tmp_path, "sync-code", "--dry", "--branch", "'x;rm -rf y'")   # _b2 joins words for bash -c
    assert out.returncode != 0 and "branch" in out.stderr and not _commands(out)


def test_b2_fetch_brings_back_the_mechanism_analysis_cells(tmp_path):
    out = _b2(tmp_path, "fetch", "--dry")
    assert out.returncode == 0, out.stderr
    cmds = _commands(out)
    [ana] = [c for c in cmds if "outputs/_analyses/" in c]
    words = ana.split()
    assert "--include=/mechanism-analysis-*/***" in words and "--exclude=*" in words
    assert "--prune-empty-dirs" in words
    assert words[-2] == "b2dtn:/ocean/projects/abc123p/swong2/Deception-Circuit/outputs/_analyses/"
    assert words[-1] == str(tmp_path / "delta_repo" / "outputs" / "_analyses") + "/"
    # same safety rule as every other fetch: never delete, keep newer Delta files, back up what is replaced
    assert "--update" in words and "--backup" in words and "--delete" not in ana and "-rl" in words
    # nothing else under outputs/_analyses (the v1 cells of record) is pulled
    assert sum("outputs/_analyses" in c for c in cmds) == 1


def test_b2_fetch_ignore_existing_applies_to_the_analysis_cells_too(tmp_path):
    out = _b2(tmp_path, "fetch", "--dry", "--ignore-existing")
    [ana] = [c for c in _commands(out) if "outputs/_analyses/" in c]
    assert "--ignore-existing" in ana.split()
