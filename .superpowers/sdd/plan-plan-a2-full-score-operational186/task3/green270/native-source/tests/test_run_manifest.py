"""run_manifest.json: the provenance file of training runs and evaluation cells.

Spec §4.6 and §6.1 (docs/research/autoresearch-workflow/spec.md). Git is
always mocked: `conftest.py` sets DC_RUN_MANIFEST_GIT=0 for the suite, and the
tests here that exercise git unset it and patch `subprocess.check_output`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from types import SimpleNamespace
from unittest import mock

import pytest

import run_manifest as RM
from tests.test_suite_layout import run_cli, two_runs  # noqa: F401 -- two_runs is a fixture

SPEC_FIELDS = {
    "schema", "created", "script", "argv", "cwd", "git_commit", "git_dirty",
    "dirty_diff_hash", "code_sha256", "config_sha256", "dataset_files", "model",
    "model_revision", "seed", "software", "host", "slurm_job_id", "direction",
    "grader", "manifest_hash",
}
COMMIT = "0123456789abcdef0123456789abcdef01234567"
FIXED = "2026-11-01T09:00:00-05:00"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fake_git(diff: bytes = b""):
    """A `subprocess.check_output` stand-in answering rev-parse and diff."""
    calls = []

    def run(cmd, **kwargs):
        calls.append(list(cmd))
        assert cmd[0] == "git"
        assert kwargs.get("timeout") == RM.GIT_TIMEOUT_SECONDS
        if cmd[1] == "rev-parse":
            return (COMMIT + "\n").encode()
        if cmd[1] == "diff":
            return diff
        raise AssertionError("unexpected git call %r" % (cmd,))

    run.calls = calls
    return run


@pytest.fixture
def git_on(monkeypatch):
    monkeypatch.delenv(RM.GIT_ENV_FLAG, raising=False)


def read(path):
    with open(path) as f:
        return json.load(f)


# ==============================================================================
# FIELDS AND HASH
# ==============================================================================

def test_every_spec_field_is_present_and_the_hash_verifies(tmp_path, git_on, monkeypatch):
    script = tmp_path / "train.py"
    script.write_text("print('hi')\n")
    config = tmp_path / "config.json"
    config.write_text('{"seed": 7}\n')
    data = tmp_path / "train.json"
    data.write_text("[1, 2, 3]\n")
    monkeypatch.setenv("SLURM_JOB_ID", "12345")

    run = fake_git()
    with mock.patch.object(RM.subprocess, "check_output", run):
        path = RM.write_run_manifest(
            str(tmp_path / "out"), script=str(script), argv=["train.py", "--seed", "7"],
            config_path=str(config), dataset_files=[str(data)], model="llama-8b-instruct",
            model_revision_value="abc123", seed=7, created=FIXED, repo_root=str(tmp_path))

    assert os.path.basename(path) == "run_manifest.json"
    m = read(path)
    assert SPEC_FIELDS <= set(m)
    assert m["schema"] == "run-manifest/1"
    assert m["script"] == "train.py"
    assert m["argv"] == ["train.py", "--seed", "7"]
    assert m["code_sha256"] == {"train.py": sha(script.read_bytes())}
    assert m["config_sha256"] == sha(config.read_bytes())
    assert list(m["dataset_files"].values()) == [sha(data.read_bytes())]
    assert m["model"] == "llama-8b-instruct" and m["model_revision"] == "abc123"
    assert m["seed"] == 7 and m["slurm_job_id"] == "12345"
    assert m["grader"] is None
    assert set(m["software"]) >= {"python", "torch", "transformers", "nnsight"}
    # The hash is over the file as written, not over an in-memory dict.
    assert RM.verify_manifest_hash(m)
    body = {k: v for k, v in m.items() if k != "manifest_hash"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    assert m["manifest_hash"] == sha(canonical)
    m["seed"] = 8
    assert not RM.verify_manifest_hash(m)


def test_git_clean(tmp_path, git_on):
    run = fake_git(diff=b"")
    with mock.patch.object(RM.subprocess, "check_output", run):
        m = RM.build_run_manifest(script="", created=FIXED, repo_root=str(tmp_path))
    assert m["git_commit"] == COMMIT
    assert m["git_dirty"] is False
    assert m["dirty_diff_hash"] is None
    assert "git_fingerprint_error" not in m
    assert [c[1] for c in run.calls] == ["rev-parse", "diff"]
    assert all(c[0] == "git" for c in run.calls)


def test_git_dirty(tmp_path, git_on):
    diff = b"diff --git a/x.py b/x.py\n+changed\n"
    with mock.patch.object(RM.subprocess, "check_output", fake_git(diff=diff)):
        m = RM.build_run_manifest(script="", created=FIXED, repo_root=str(tmp_path))
    assert m["git_commit"] == COMMIT
    assert m["git_dirty"] is True
    assert m["dirty_diff_hash"] == sha(diff)


@pytest.mark.parametrize("error", [
    FileNotFoundError("git"),
    subprocess.TimeoutExpired(["git"], 10),
    subprocess.CalledProcessError(128, ["git"]),
])
def test_git_unavailable_is_recorded_not_raised(tmp_path, git_on, error):
    with mock.patch.object(RM.subprocess, "check_output", side_effect=error):
        m = RM.build_run_manifest(script="", created=FIXED, repo_root=str(tmp_path))
    assert m["git_commit"] is None and m["git_dirty"] is None
    assert m["dirty_diff_hash"] is None
    assert m["git_fingerprint_error"].startswith("unavailable")
    assert SPEC_FIELDS <= set(m)


def test_git_disabled_by_environment_never_shells_out(tmp_path, monkeypatch):
    monkeypatch.setenv(RM.GIT_ENV_FLAG, "0")
    with mock.patch.object(RM.subprocess, "check_output",
                           side_effect=AssertionError("git was called")):
        m = RM.build_run_manifest(script="", created=FIXED, repo_root=str(tmp_path))
    assert m["git_fingerprint_error"] == "disabled"
    assert m["git_commit"] is None


def test_the_suite_disables_git_by_default():
    # conftest.py sets it for every test; the tests above unset it explicitly.
    assert os.environ.get(RM.GIT_ENV_FLAG) == "0"


def test_direction_comes_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.delenv(RM.DIRECTION_ENV, raising=False)
    assert RM.build_run_manifest(script="", created=FIXED)["direction"] is None
    monkeypatch.setenv(RM.DIRECTION_ENV, "sdr-mechanism")
    assert RM.build_run_manifest(script="", created=FIXED)["direction"] == "sdr-mechanism"


def test_model_revision_is_read_from_the_hub_cache_without_a_model_load(tmp_path):
    refs = tmp_path / "models--meta-llama--Llama-3.1-8B-Instruct" / "refs"
    refs.mkdir(parents=True)
    (refs / "main").write_text("0e9e39f249a16976918f6564b8830bc894c89659\n")
    assert RM.model_revision("llama-8b-instruct", str(tmp_path)) == \
        "0e9e39f249a16976918f6564b8830bc894c89659"
    assert RM.model_revision("llama-1b", str(tmp_path)) is None
    assert RM.model_revision(None, str(tmp_path)) is None


def test_model_revision_tries_each_cache_location_from_the_environment(tmp_path, monkeypatch):
    for name in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HF_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("TRANSFORMERS_CACHE", str(tmp_path / "empty"))
    refs = tmp_path / "home" / "hub" / "models--meta-llama--Llama-3.2-1B" / "refs"
    refs.mkdir(parents=True)
    (refs / "main").write_text("feedface\n")
    assert RM.hf_hub_caches() == [str(tmp_path / "empty"), str(tmp_path / "home" / "hub")]
    assert RM.model_revision("llama-1b") == "feedface"


# ==============================================================================
# NEVER OVERWRITE
# ==============================================================================

def test_identical_content_is_kept_and_different_content_gets_a_new_file(tmp_path, capsys):
    out = str(tmp_path / "run")
    kw = dict(script="", argv=["train.py"], cwd=str(tmp_path), created=FIXED, seed=1,
              model_revision_value="r")
    first = RM.write_run_manifest(out, **kw)
    original = open(first).read()

    assert RM.write_run_manifest(out, **kw) == first
    assert sorted(os.listdir(out)) == ["run_manifest.json"]

    kw["seed"] = 2
    second = RM.write_run_manifest(out, **kw)
    assert os.path.basename(second) == "run_manifest.1.json"
    assert open(first).read() == original
    assert read(second)["seed"] == 2
    assert "run_manifest.1.json" in capsys.readouterr().out

    kw["seed"] = 3
    third = RM.write_run_manifest(out, **kw)
    assert os.path.basename(third) == "run_manifest.2.json"
    assert open(first).read() == original
    assert read(second)["seed"] == 2


# ==============================================================================
# THE TRAINING SEAM: run_io.make_run_dir
# ==============================================================================

def minimal_args(tmp_path, data_dir):
    return argparse.Namespace(
        model="llama-8b-instruct", task="sdr", family="llama", seed=11,
        std_variant=None, deception_condition=None, edge_pruning=False,
        skip_node_pruning=False, node_epochs=1, edge_epochs=1, lr=0.1, batch_size=2,
        max_seq_length=8, train_samples=2, val_samples=2, test_samples=2,
        node_lambda_sparsity=0.3, edge_lambda_sparsity=0.3, data_dir=str(data_dir),
        output_dir=str(tmp_path / "run"), node_checkpoint=None)


def test_make_run_dir_keeps_config_json_and_adds_run_manifest(tmp_path):
    from config import EdgeConfig, NodePruningConfig
    from run_io import make_run_dir, resolved_run_config

    data = tmp_path / "data"
    (data / "sdr").mkdir(parents=True)
    (data / "sdr" / "train.json").write_text("[]\n")
    (data / "sdr" / "notes.bin").write_text("ignored\n")
    node_cfg, edge_cfg = NodePruningConfig(), EdgeConfig()
    args = minimal_args(tmp_path, data)

    out = make_run_dir(args, node_cfg, edge_cfg)

    with open(os.path.join(out, "config.json")) as f:
        written = f.read()
    # config.json is byte-identical to what make_run_dir always wrote.
    assert written == json.dumps(resolved_run_config(args, node_cfg, edge_cfg),
                                 indent=2, default=str)
    m = read(os.path.join(out, "run_manifest.json"))
    assert SPEC_FIELDS <= set(m)
    assert m["config_sha256"] == sha(written.encode())
    assert m["seed"] == 11 and m["model"] == "llama-8b-instruct"
    assert list(m["dataset_files"]) == [os.path.join(str(data), "sdr", "train.json")]
    assert m["git_fingerprint_error"] == "disabled"
    assert RM.verify_manifest_hash(m)
    assert args.node_checkpoint == os.path.join(out, "active_nodes.json")


def test_make_run_dir_survives_a_failing_manifest_writer(tmp_path, capsys):
    from config import EdgeConfig, NodePruningConfig
    from run_io import make_run_dir

    args = minimal_args(tmp_path, tmp_path / "nodata")
    with mock.patch.object(RM, "build_run_manifest", side_effect=RuntimeError("boom")):
        out = make_run_dir(args, NodePruningConfig(), EdgeConfig())
    assert os.path.isfile(os.path.join(out, "config.json"))
    assert not os.path.exists(os.path.join(out, "run_manifest.json"))
    assert "run_manifest.json not written" in capsys.readouterr().out


# ==============================================================================
# THE EVALUATION SEAM: evaluation.suite.write_cell_manifest
# ==============================================================================

def fake_ctx(tmp_path, evals, benchmarks=("sandbagging",)):
    run_dir = tmp_path / "circuit_run"
    run_dir.mkdir(exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps({"seed": 123, "model": "llama-8b-instruct"}))
    data = tmp_path / "data"
    (data / "far").mkdir(parents=True, exist_ok=True)
    (data / "far" / "test.json").write_text("[]\n")
    out_dir = tmp_path / "cell" / "interchange"
    out_dir.mkdir(parents=True, exist_ok=True)
    cli = SimpleNamespace(evals=list(evals), benchmarks=list(benchmarks))
    args = SimpleNamespace(model="llama-8b-instruct", task="far", data_dir=str(data),
                           deception_condition=None, seed=999)
    return SimpleNamespace(cli=cli, args=args, run_dir=str(run_dir), out_dir=str(out_dir))


def test_cell_manifest_without_benchmarks_has_no_grader(tmp_path):
    from evaluation.suite import write_cell_manifest

    ctx = fake_ctx(tmp_path, ["sanity", "knockout"])
    path = write_cell_manifest(ctx)
    assert path == os.path.join(ctx.out_dir, "run_manifest.json")
    m = read(path)
    assert SPEC_FIELDS <= set(m)
    assert m["grader"] is None
    # The circuit's own training config and seed, not the task's.
    assert m["config_sha256"] == sha(open(os.path.join(ctx.run_dir, "config.json"), "rb").read())
    assert m["seed"] == 123
    assert m["model"] == "llama-8b-instruct"
    assert list(m["dataset_files"]) == [os.path.join(ctx.args.data_dir, "far", "test.json")]
    assert RM.verify_manifest_hash(m)


def test_cell_manifest_with_benchmarks_carries_the_grader(tmp_path):
    from evaluation.grader_hash import grader_sha256
    from evaluation.suite import write_cell_manifest

    ctx = fake_ctx(tmp_path, ["sanity", "benchmarks"], benchmarks=["sandbagging"])
    m = read(write_cell_manifest(ctx))
    grader = m["grader"]
    assert set(grader) == {"grader_sha256", "files", "judge_spec"}
    assert grader["grader_sha256"] == grader_sha256()
    assert "evaluation/benchmark_eval.py" in grader["files"]
    assert grader["judge_spec"] == {"sandbagging": None}


def test_the_real_cell_loop_writes_a_run_manifest(two_runs, monkeypatch):
    """Through the CLI, the session builder and run_cell, with a tiny model."""
    run_a, _ = two_runs
    assert run_cli(monkeypatch, run_a, "--evals", "sanity", "--n-random", "1",
                   "--skip-wikitext") == 0
    cell = run_a / "evaluations" / "interchange"
    m = read(cell / "run_manifest.json")
    assert SPEC_FIELDS <= set(m)
    assert m["script"] == "evaluate_circuit.py"
    assert m["grader"] is None
    assert m["seed"] == 1 and m["model"] == "llama-tiny"
    assert m["config_sha256"] == sha((run_a / "config.json").read_bytes())
    assert m["git_fingerprint_error"] == "disabled"
    assert RM.verify_manifest_hash(m)
    assert os.path.isfile(cell / "summary.json")


def test_cell_manifest_failure_never_stops_the_cell(tmp_path, capsys):
    from evaluation.suite import write_cell_manifest

    ctx = fake_ctx(tmp_path, ["sanity"])
    with mock.patch.object(RM, "build_run_manifest", side_effect=RuntimeError("boom")):
        assert write_cell_manifest(ctx) is None
    assert "run_manifest.json not written" in capsys.readouterr().out
