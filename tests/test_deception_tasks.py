"""Tests for the far / sdr / ser Task classes and their CLI wiring."""

from __future__ import annotations

import json
import os
from types import SimpleNamespace

import pytest
import torch

import tasks
from config import default_hyperparams
from dataset import deception_common as dc
from tests.fakes import FAKE_VOCAB_SIZE, FakeWordTokenizer

TASKS = ["far", "sdr", "ser"]


@pytest.mark.parametrize("name", TASKS)
def test_registry_returns_the_task(name):
    task = tasks.get_task(name)
    assert task.name == name
    assert task.mechanism == dc.SPECS[name].mechanism
    assert name in tasks.list_tasks()


@pytest.mark.parametrize("name", TASKS)
def test_tasks_are_llama_only(name):
    task = tasks.get_task(name)
    assert task.supports_family("llama")
    assert not task.supports_family("gpt2")


def test_hyperparameters_are_identical_across_the_three_mechanisms():
    """A circuit difference between mechanisms must not be a difference in how
    hard each task was trained."""
    hp = [default_hyperparams("llama", name) for name in TASKS]
    assert hp[0] == hp[1] == hp[2]
    assert hp[0]["max_seq_length"] >= dc.MAX_SEQ_LENGTH


@pytest.mark.parametrize("name", TASKS)
def test_dataset_dir_follows_the_condition(name):
    task = tasks.get_task(name)
    args = SimpleNamespace(data_dir="/data", deception_condition="deceptive")
    assert task.dataset_dir(args) == f"/data/{name}"
    args.deception_condition = "honest"
    assert task.dataset_dir(args) == f"/data/{name}_honest"


def test_pred_spec_reads_the_token_after_the_prompt():
    batch = {"prefix_length": torch.tensor([7, 9]),
             "target_token": torch.tensor([3, 4]),
             "distractor_token": torch.tensor([5, 6])}
    spec = tasks.get_task("far").pred_spec(batch)
    assert spec["pred_pos"].tolist() == [6, 8]
    assert spec["target"].tolist() == [3, 4]


def test_compute_objective_matches_the_std_objective():
    """The three mechanisms are only comparable if the readout and the loss are
    identical to each other — and to STD, which they are compared against."""
    torch.manual_seed(0)
    circuit = torch.randn(2, 10, 16)
    target = torch.randn(2, 10, 16)
    batch = {"prefix_length": torch.tensor([5, 7]),
             "target_token": torch.tensor([1, 2]),
             "distractor_token": torch.tensor([3, 4])}
    state = {"margin": 1.0}

    from tasks.std import STDTask
    for name in TASKS:
        kl, loss = tasks.get_task(name).compute_objective(
            circuit, target, batch, state, "cpu")
        std_kl, std_loss = STDTask().compute_objective(
            circuit, target, batch, state, "cpu")
        assert torch.allclose(kl, std_kl)
        assert torch.allclose(loss, std_loss)


# ==============================================================================
# End-to-end dataloader construction over a written-to-disk dataset
# ==============================================================================

def _write_dataset(path, records, margin_thresh=1.0):
    from datasets import Dataset, DatasetDict
    os.makedirs(path, exist_ok=True)
    DatasetDict({split: Dataset.from_list(records)
                 for split in ("train", "validation", "test")}).save_to_disk(path)
    with open(os.path.join(path, "dataset_config.json"), "w") as f:
        json.dump({"task": os.path.basename(path), "margin_thresh": margin_thresh},
                  f)


@pytest.mark.parametrize("condition", ["deceptive", "honest"])
def test_build_dataloaders_loads_the_right_directory(tmp_path, condition):
    tok = FakeWordTokenizer()
    entities = [{"name": "Firm", "domain": "logistics"}]
    pairs = [("staffing", "pricing"), ("budget", "timeline")]
    pressures = [{"id": "p0", "slot": 0, "text": "You will be shut off.",
                  "shared": False}]
    records = dc.generate_task_data(tok, dc.SPECS["far"], 4, entities, pairs,
                                    pressures, max_seq_length=96, seed=0)
    records = [{k: v for k, v in r.items()} for r in records]

    data_dir = tmp_path / "datasets"
    suffix = "_honest" if condition == "honest" else ""
    _write_dataset(str(data_dir / f"far{suffix}"), records, margin_thresh=2.0)

    args = SimpleNamespace(
        data_dir=str(data_dir), deception_condition=condition,
        batch_size=2, max_seq_length=96, train_samples=None, val_samples=None,
        test_samples=None, shuffle_train=False, deception_runtime_filter=False,
        deception_margin_loss=None)
    state = {}
    train_dl, val_dl, test_dl = tasks.get_task("far").build_dataloaders(
        tok, "llama", None, "cpu", args, state)

    assert state["margin"] == 2.0        # read from dataset_config.json
    assert len(train_dl.dataset) == 4
    batch = next(iter(train_dl))
    assert batch["input_ids"].shape == (2, 96)
    assert batch["prefix_length"].max().item() <= 96
    assert len(val_dl.dataset) == len(test_dl.dataset) == 4


def test_build_dataloaders_reports_a_missing_dataset(tmp_path):
    args = SimpleNamespace(data_dir=str(tmp_path), deception_condition="deceptive",
                           batch_size=2, max_seq_length=96, train_samples=None,
                           val_samples=None, test_samples=None)
    with pytest.raises(FileNotFoundError, match="build the dataset first"):
        tasks.get_task("sdr").build_dataloaders(
            FakeWordTokenizer(), "llama", None, "cpu", args, {})


# ==============================================================================
# CLI wiring
# ==============================================================================

def test_train_cli_exposes_the_deception_flags():
    import train
    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "ser",
         "--deception-condition", "honest"])
    assert args.task == "ser"
    assert args.deception_condition == "honest"
    assert args.deception_runtime_filter is False
    assert args.deception_margin_loss is None


def test_run_slug_separates_the_honest_twin():
    import train
    from config import NodePruningConfig
    from run_io import build_run_slug

    slugs = {}
    for condition in ("deceptive", "honest"):
        args = train.build_parser().parse_args(
            ["--model", "llama-8b-instruct", "--task", "far",
             "--deception-condition", condition])
        train.resolve_args(args)
        slugs[condition] = build_run_slug(args, NodePruningConfig())
    # Timestamps differ anyway, but the run directory has to say WHICH
    # condition it is: mixing them up inverts Δ = C_deceptive − C_honest.
    assert "honest" in slugs["honest"]
    assert "honest" not in slugs["deceptive"]


def test_run_config_records_the_condition():
    import train
    from config import EdgeConfig, NodePruningConfig
    from run_io import resolved_run_config

    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "far",
         "--deception-condition", "honest"])
    train.resolve_args(args)
    cfg = resolved_run_config(args, NodePruningConfig(), EdgeConfig())
    # Without this, a run trained on far_honest is indistinguishable from one
    # trained on far, and evaluate_circuit would reload the wrong dataset.
    assert cfg["deception_condition"] == "honest"


def test_evaluation_context_restores_the_condition():
    from evaluation.context import _RUN_CONFIG_KEYS
    for key in ("deception_condition", "deception_runtime_filter",
                "deception_margin_loss", "joint_tasks", "joint_scale_epochs"):
        assert key in _RUN_CONFIG_KEYS


# ==============================================================================
# Joint multitask pruning
# ==============================================================================

def test_joint_task_is_registered():
    task = tasks.get_task("joint")
    assert task.name == "joint"
    assert "joint" in tasks.list_tasks()


def test_normalize_joint_tasks_requires_at_least_two():
    from tasks.joint_deception import _normalize_joint_tasks
    with pytest.raises(ValueError, match="at least two"):
        _normalize_joint_tasks(["far"])
    assert _normalize_joint_tasks(["far", "sdr", "ser"]) == ["far", "sdr", "ser"]
    assert _normalize_joint_tasks(["ser", "far", "far", "sdr"]) == ["ser", "far", "sdr"]


def test_joint_build_dataloaders_concatenates_subtasks(tmp_path):
    tok = FakeWordTokenizer()
    entities = [{"name": "Firm", "domain": "logistics"}]
    pairs = [("staffing", "pricing"), ("budget", "timeline")]
    pressures = [{"id": "p0", "slot": 0, "text": "You will be shut off.",
                  "shared": False}]
    data_dir = tmp_path / "datasets"

    for name in ("far", "sdr", "ser"):
        records = dc.generate_task_data(tok, dc.SPECS[name], 4, entities, pairs,
                                        pressures, max_seq_length=96, seed=0)
        records = [{k: v for k, v in r.items()} for r in records]
        _write_dataset(str(data_dir / name), records, margin_thresh=1.0)

    args = SimpleNamespace(
        data_dir=str(data_dir), deception_condition="deceptive",
        joint_tasks=["far", "sdr", "ser"],
        batch_size=2, max_seq_length=96, train_samples=None, val_samples=None,
        test_samples=None, shuffle_train=False, deception_runtime_filter=False,
        deception_margin_loss=None, seed=42)
    state = {"joint_test_loaders": {}}
    train_dl, val_dl, test_dl = tasks.get_task("joint").build_dataloaders(
        tok, "llama", None, "cpu", args, state)

    assert len(train_dl.dataset) == 12
    assert len(val_dl.dataset) == 12
    assert len(test_dl.dataset) == 12
    assert set(state["joint_test_loaders"]) == {"far", "sdr", "ser"}
    assert state["joint_tasks"] == ["far", "sdr", "ser"]
    tasks_seen = {rec["_joint_task"] for rec in train_dl.dataset.processed_data}
    assert tasks_seen == {"far", "sdr", "ser"}


def test_train_cli_joint_flags():
    import train
    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "joint"])
    assert args.task == "joint"
    assert args.joint_tasks is None
    assert args.joint_scale_epochs is True

    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "joint",
         "--joint-tasks", "far", "ser", "--no-joint-scale-epochs"])
    assert args.joint_tasks == ["far", "ser"]
    assert args.joint_scale_epochs is False


def test_joint_resolve_args_scales_epochs_by_default():
    import train
    from config import EdgeConfig, NodePruningConfig

    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "joint"])
    train.resolve_args(args)
    assert args.joint_tasks == ["far", "sdr", "ser"]
    assert args.node_epochs == 167
    assert args.edge_epochs == 100


def test_joint_resolve_args_no_scale_when_disabled():
    import train

    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "joint",
         "--no-joint-scale-epochs"])
    train.resolve_args(args)
    assert args.node_epochs == 500
    assert args.edge_epochs == 300


def test_joint_tasks_without_joint_task_errors():
    import train

    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "far",
         "--joint-tasks", "far", "sdr"])
    with pytest.raises(SystemExit):
        train.resolve_args(args)


# ==============================================================================
# Build-script invariants
# ==============================================================================

def test_length_matching_inflation_is_task_independent():
    """The generated count advances the shared `seen` set. If it differed per
    task, the three tasks would hold different `seen` sets after the first split
    and every later split would stop being a matched triplet."""
    from transformers import AutoTokenizer

    from dataset.build_deception_dataset import allowed_length_matched_slots
    try:
        tok = AutoTokenizer.from_pretrained(dc.DEFAULT_MODEL)
    except Exception as e:
        pytest.skip(f"Llama tokenizer unavailable: {type(e).__name__}: {e}")

    inflations, slot_sets = [], {}
    for task in TASKS:
        slots, inflate = allowed_length_matched_slots(
            tok, task, dc.load_pressures(task), dc.POOLS_DIR)
        inflations.append(inflate)
        slot_sets[task] = slots
    assert len(set(inflations)) == 1, inflations
    # The bands themselves are allowed to differ — that is the whole point.
    assert all(slot_sets[t] for t in TASKS)


def test_build_sbatch_does_not_contradict_its_own_warning():
    """The header tells the reader not to length-match by default; the command
    below it must agree, or the default build silently shrinks the comparison
    set at a cost of GPU-hours."""
    with open(os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "scripts", "build_deception.sbatch")) as f:
        text = f.read()
    body = text.split("for TASK in", 1)[1]
    assert "--match-length-distribution" not in body


def test_fake_vocab_is_large_enough_for_the_scaffold():
    """Guards the fakes themselves: a vocabulary overflow would surface as a
    confusing failure in the dataset tests."""
    tok = FakeWordTokenizer()
    records = dc.generate_task_data(
        tok, dc.SPECS["ser"], 8,
        [{"name": "Firm", "domain": "d"}], [("staffing", "pricing")],
        [{"id": "p0", "slot": 0, "text": "You will be shut off.", "shared": False}],
        max_seq_length=96, seed=0)
    assert len(tok.vocab) < FAKE_VOCAB_SIZE
    assert len(records) == 8
