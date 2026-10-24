"""Cluster profiles (scripts/cluster/*.env), the evaluate_circuit.sbatch wrapper and scripts/remote/b2.sh.

Ticket 07. The seams are the three things other code relies on: the DC_* variables a profile exports, what the
sbatch wrapper does at run time once Slurm has started it, and the commands b2.sh would run (its --dry output).
Everything runs bash with stubs on the CPU; nothing touches Slurm, SSH or a GPU.
"""

import os
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_VARS = (
    "DC_ACCOUNT",
    "DC_PARTITION",
    "DC_GPU_SPEC",
    "DC_ACTIVATE",
    "DC_HF_HOME",
    "DC_HF_OFFLINE",
    "DC_REPO_ROOT",
    "DC_TIME_DEFAULT",
)


def _bash(script, env=None, cwd=REPO):
    base = {"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp")}
    base.update(env or {})
    return subprocess.run(["/bin/bash", "-c", script], cwd=cwd, env=base, capture_output=True, text=True)


def _profile(name):
    """Source a profile in a clean shell and return the DC_* variables it exported."""
    path = os.path.join(REPO, "scripts", "cluster", f"{name}.env")
    out = _bash(f"set -euo pipefail; source {path}; env")
    assert out.returncode == 0, out.stderr
    return {k: v for k, v in (line.split("=", 1) for line in out.stdout.splitlines() if "=" in line)
            if k.startswith("DC_")}


@pytest.mark.parametrize("name", ["delta", "bridges2"])
def test_profile_exports_every_variable(name):
    got = _profile(name)
    missing = [v for v in PROFILE_VARS if v not in got]
    assert not missing, f"{name}.env does not export {missing}"
    assert got["DC_HF_OFFLINE"] in {"0", "1"}


def test_delta_profile_reproduces_the_sbatch_header_defaults():
    got = _profile("delta")
    assert got["DC_ACCOUNT"] == "beto-delta-gpu"
    assert got["DC_PARTITION"] == "gpuA40x4"
    assert got["DC_GPU_SPEC"] == "--gpus-per-node=1"
    assert got["DC_TIME_DEFAULT"] == "12:00:00"
    assert got["DC_ACTIVATE"] == "source ~/.bashrc && conda activate mgnp"
    assert got["DC_HF_HOME"] == "/work/nvme/beto/swong2"
    assert got["DC_HF_OFFLINE"] == "0"


def test_bridges2_profile_is_offline_h100_and_never_sources_bashrc():
    got = _profile("bridges2")
    assert got["DC_PARTITION"] == "GPU-shared"
    assert got["DC_GPU_SPEC"] == "--gpus=h100-80:1"
    assert got["DC_HF_OFFLINE"] == "1"
    assert ".bashrc" not in got["DC_ACTIVATE"]
    assert got["DC_REPO_ROOT"].startswith("/ocean/projects/")
    assert got["DC_HF_HOME"].startswith("/ocean/projects/")


# ---------------------------------------------------------------------------------------------------------
# scripts/evaluate_circuit.sbatch at run time. The job body runs under bash with a fake HOME whose .bashrc
# defines a `conda` stub, and a stub `python` that prints what the real one would receive.

STUB_PYTHON = """#!/bin/bash
echo "cwd=$(pwd)"
echo "argv=$*"
echo "HF_HOME=${HF_HOME-<unset>}"
echo "HF_HUB_OFFLINE=${HF_HUB_OFFLINE-<unset>}"
echo "HF_DATASETS_OFFLINE=${HF_DATASETS_OFFLINE-<unset>}"
echo "TRANSFORMERS_OFFLINE=${TRANSFORMERS_OFFLINE-<unset>}"
echo "ACTIVATED=${ACTIVATED-<unset>}"
"""

FAKE_BASHRC = """export HF_HOME=/work/nvme/beto/swong2
conda() { echo "conda $*" >&2; export ACTIVATED="conda:$2"; }
"""


def _job_sandbox(tmp_path, profiles):
    """A submit dir holding the wrapper and the named profiles, a fake HOME, and a stub python on PATH."""
    submit = tmp_path / "repo"
    (submit / "scripts" / "cluster").mkdir(parents=True)
    with open(os.path.join(REPO, "scripts", "evaluate_circuit.sbatch")) as fh:
        (submit / "scripts" / "evaluate_circuit.sbatch").write_text(fh.read())
    for name, text in profiles.items():
        (submit / "scripts" / "cluster" / f"{name}.env").write_text(text)
    home = tmp_path / "home"
    home.mkdir()
    (home / ".bashrc").write_text(FAKE_BASHRC)
    stubs = tmp_path / "bin"
    stubs.mkdir()
    (stubs / "python").write_text(STUB_PYTHON)
    (stubs / "python").chmod(0o755)
    env = {"HOME": str(home), "PATH": f"{stubs}:/usr/bin:/bin", "SLURM_SUBMIT_DIR": str(submit)}
    return submit, env


def _run_job(submit, env, *args):
    cmd = ["/bin/bash", str(submit / "scripts" / "evaluate_circuit.sbatch"), *args]
    return subprocess.run(cmd, cwd=str(submit), env=env, capture_output=True, text=True)


def _read(name):
    with open(os.path.join(REPO, "scripts", "cluster", f"{name}.env")) as fh:
        return fh.read()


def test_sbatch_without_dc_cluster_runs_exactly_as_the_pre_profile_wrapper(tmp_path):
    submit, env = _job_sandbox(tmp_path, {"delta": _read("delta")})
    out = _run_job(submit, env, "outputs/run_a", "--evals", "sanity")
    assert out.returncode == 0, out.stderr
    # What the wrapper did before profiles existed: cd to the submit dir, activate mgnp through ~/.bashrc
    # (which sets HF_HOME), set no offline flag, pass the arguments through untouched.
    assert out.stdout.splitlines() == [
        f"cwd={submit}",
        "argv=evaluate_circuit.py outputs/run_a --evals sanity",
        "HF_HOME=/work/nvme/beto/swong2",
        "HF_HUB_OFFLINE=<unset>",
        "HF_DATASETS_OFFLINE=<unset>",
        "TRANSFORMERS_OFFLINE=<unset>",
        "ACTIVATED=conda:mgnp",
    ]
    assert out.stderr.strip() == "conda activate mgnp"


def test_sbatch_with_an_offline_profile_activates_it_and_switches_the_hub_off(tmp_path):
    activate = tmp_path / "activate"
    activate.write_text("export ACTIVATED=packed-env\n")
    profile = (f'export DC_ACTIVATE="source {activate}"\nexport DC_HF_HOME="{tmp_path}/hf"\n'
               'export DC_HF_OFFLINE="1"\n')
    submit, env = _job_sandbox(tmp_path, {"delta": _read("delta"), "remote": profile})
    env["DC_CLUSTER"] = "remote"
    out = _run_job(submit, env, "--circuit", "a=outputs/x")
    assert out.returncode == 0, out.stderr
    lines = out.stdout.splitlines()
    assert f"HF_HOME={tmp_path}/hf" in lines
    assert "HF_HUB_OFFLINE=1" in lines
    assert "HF_DATASETS_OFFLINE=1" in lines
    assert "TRANSFORMERS_OFFLINE=1" in lines
    assert "ACTIVATED=packed-env" in lines
    assert "conda" not in out.stderr


def test_sbatch_and_b2_parse_as_bash():
    for rel in ("scripts/evaluate_circuit.sbatch", "scripts/remote/b2.sh", "scripts/cluster/bridges2_smoke.sbatch"):
        out = _bash(f"/bin/bash -n {os.path.join(REPO, rel)}")
        assert out.returncode == 0, (rel, out.stderr)


def test_sbatch_refuses_an_unknown_cluster_before_running_anything(tmp_path):
    submit, env = _job_sandbox(tmp_path, {"delta": _read("delta")})
    env["DC_CLUSTER"] = "nowhere"
    out = _run_job(submit, env, "outputs/run_a")
    assert out.returncode != 0
    assert "nowhere" in out.stderr
    assert "argv=" not in out.stdout


# ---------------------------------------------------------------------------------------------------------
# scripts/remote/b2.sh. --dry prints every command it would run and touches nothing; a stub ssh on PATH
# shows what a real run does when the SSH masters are not open.

B2 = os.path.join(REPO, "scripts", "remote", "b2.sh")


def _b2_profile(tmp_path, alloc="abc123p"):
    path = tmp_path / "b2.env"
    path.write_text(_read("bridges2").replace('DC_B2_ALLOC="${DC_B2_ALLOC:-__ALLOC__}"', f'DC_B2_ALLOC="{alloc}"'))
    return str(path)


def _b2(tmp_path, *args, alloc="abc123p", extra_env=None):
    env = {"DC_B2_PROFILE": _b2_profile(tmp_path, alloc), "DC_DELTA_REPO_ROOT": str(tmp_path / "delta_repo")}
    env.update(extra_env or {})
    return _bash(" ".join(["/bin/bash", B2, *args]), env=env)


def _commands(out):
    """The commands a --dry run printed, one per '+ ' line."""
    return [line[2:] for line in out.stdout.splitlines() if line.startswith("+ ")]


def test_b2_without_a_known_subcommand_prints_usage(tmp_path):
    out = _b2(tmp_path, "frobnicate")
    assert out.returncode == 2
    for sub in ("sync-code", "sync-data", "submit", "status", "fetch"):
        assert sub in out.stderr


def test_b2_submit_dry_puts_the_bridges2_profile_on_the_sbatch_command_line(tmp_path):
    out = _b2(tmp_path, "submit", "--dry", "--", "outputs/run_a", "--evals", "sanity")
    assert out.returncode == 0, out.stderr
    [cmd] = _commands(out)
    assert "ssh -o BatchMode=yes bridges2" in cmd
    assert "cd /ocean/projects/abc123p/swong2/Deception-Circuit" in cmd
    assert ("DC_CLUSTER=bridges2 DC_B2_ALLOC=abc123p sbatch -A abc123p -p GPU-shared --gpus=h100-80:1 -t 01:00:00 "
            "scripts/evaluate_circuit.sbatch outputs/run_a --evals sanity") in cmd


def test_b2_submit_refuses_while_the_allocation_is_a_placeholder(tmp_path):
    out = _b2(tmp_path, "submit", "--", "outputs/run_a", alloc="__ALLOC__")
    assert out.returncode != 0
    assert "__ALLOC__" in out.stderr
    assert not _commands(out)


def test_b2_fetch_dry_never_overwrites_newer_delta_files_and_never_deletes(tmp_path):
    out = _b2(tmp_path, "fetch", "--dry")
    assert out.returncode == 0, out.stderr
    cmds = _commands(out)
    assert cmds and all(c.startswith("rsync ") for c in cmds)
    for c in cmds:
        assert "--update" in c
        assert "--delete" not in c
        assert "--backup" in c, "a Delta file that is replaced anyway must be kept"
        assert "--checksum" in c, "identical bytes with a fresh Bridges-2 mtime must not be re-copied"
        assert "b2dtn:/ocean/projects/abc123p/swong2/Deception-Circuit/" in c
        assert str(tmp_path / "delta_repo") in c
    assert any("evaluations*/***" in c for c in cmds)


def test_b2_fetch_ignore_existing_keeps_every_delta_file(tmp_path):
    out = _b2(tmp_path, "fetch", "--dry", "--ignore-existing", "outputs/_suites/x")
    assert out.returncode == 0, out.stderr
    [cmd] = _commands(out)
    assert "--ignore-existing" in cmd
    assert cmd.split()[-1] == str(tmp_path / "delta_repo" / "outputs" / "_suites" / "x") + "/"


def test_b2_sync_data_dry_copies_only_named_cache_dirs_and_no_secret(tmp_path):
    out = _b2(tmp_path, "sync-data", "--dry", "--what", "all")
    assert out.returncode == 0, out.stderr
    cmds = _commands(out)
    rsyncs = [c for c in cmds if c.startswith("rsync ")]
    assert any("hub/models--meta-llama--Llama-3.1-8B-Instruct/" in c for c in rsyncs)
    assert any("hub/datasets--Salesforce--wikitext/" in c for c in rsyncs)
    assert any("datasets/Salesforce___wikitext/" in c for c in rsyncs)
    for c in rsyncs:
        assert "b2dtn:" in c
        assert ".bashrc" not in c.replace("--exclude=.bashrc", "")
        assert " /work/nvme/beto/swong2/ " not in c, "the HF_HOME root holds the token"
        assert "--exclude=token" in c
        assert "--delete" not in c


def test_b2_sync_data_refuses_a_secret_in_the_run_manifest(tmp_path):
    manifest = tmp_path / "manifest.txt"
    manifest.write_text("outputs/some_run\n~/.bashrc\n")
    out = _b2(tmp_path, "sync-data", "--dry", "--what", "runs", extra_env={"DC_B2_MANIFEST": str(manifest)})
    assert out.returncode != 0
    assert ".bashrc" in out.stderr
    assert not [c for c in _commands(out) if c.startswith("rsync ")]


def test_b2_sync_code_dry_fast_forwards_the_branch_on_bridges2(tmp_path):
    out = _b2(tmp_path, "sync-code", "--dry")
    assert out.returncode == 0, out.stderr
    joined = "\n".join(_commands(out))
    assert "ssh -o BatchMode=yes bridges2" in joined
    assert "mechanism-datasets" in joined
    assert "--ff-only" in joined
    assert "https://github.com/JaMussCraft/Deception-Circuit.git" in joined


def test_b2_status_dry_reads_sacct(tmp_path):
    out = _b2(tmp_path, "status", "--dry", "12345")
    assert out.returncode == 0, out.stderr
    [cmd] = _commands(out)
    assert "sacct" in cmd and "12345" in cmd


def test_b2_stops_without_prompting_when_the_ssh_master_is_closed(tmp_path):
    stubs = tmp_path / "bin"
    stubs.mkdir()
    calls = tmp_path / "ssh_calls"
    (stubs / "ssh").write_text(f'#!/bin/bash\necho "$*" >> {calls}\n[ "$1" = "-O" ] && exit 255\nexit 0\n')
    (stubs / "ssh").chmod(0o755)
    out = _b2(tmp_path, "status", extra_env={"PATH": f"{stubs}:/usr/bin:/bin"})
    assert out.returncode != 0
    assert "master" in out.stderr.lower()
    assert calls.read_text().splitlines() == ["-O check bridges2"]
