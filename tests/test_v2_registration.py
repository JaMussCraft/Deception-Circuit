"""Registration of the v2 mechanism tasks (far_v2 / sdr_v2 / ser_v2, ticket 02).

v2 is a side build: the three ids are new tasks, `DECEPTION_TASKS` and the
joint run's default subtasks stay the v1 three.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

import tasks
from config import default_hyperparams
from tasks import get_task, list_tasks

V2 = ["far_v2", "sdr_v2", "ser_v2"]


def test_v2_ids_are_listed_and_resolve():
    for name in V2:
        assert name in list_tasks()
        task = get_task(name)
        assert task.name == name
        assert task.supports_family("llama") and not task.supports_family("gpt2")


def test_v2_mechanisms_match_v1():
    for v1 in ("far", "sdr", "ser"):
        assert get_task(f"{v1}_v2").mechanism == get_task(v1).mechanism


def test_deception_tasks_v2_constant():
    assert tasks.DECEPTION_TASKS_V2 == V2


def test_v1_deception_tasks_unchanged():
    assert tasks.DECEPTION_TASKS == ["far", "sdr", "ser"]


@pytest.mark.parametrize("condition,dirname", [
    ("deceptive", "sdr_v2"), (None, "sdr_v2"), ("honest", "sdr_v2_honest"),
    ("nopressure", "sdr_v2_nopressure")])
def test_dataset_dir_per_condition(condition, dirname):
    args = SimpleNamespace(data_dir="/data", deception_condition=condition)
    assert get_task("sdr_v2").dataset_dir(args) == os.path.join("/data", dirname)


@pytest.mark.parametrize("name", V2)
def test_hyperparams_copy_sdr(name):
    assert default_hyperparams("llama", name) == default_hyperparams("llama", "sdr")


def test_joint_default_subtasks_unchanged():
    import train
    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "joint"])
    train.resolve_args(args)
    assert args.joint_tasks == ["far", "sdr", "ser"]


def test_joint_tasks_choices_exclude_v2():
    import train
    with pytest.raises(SystemExit):
        train.build_parser().parse_args(
            ["--model", "llama-8b-instruct", "--task", "joint",
             "--joint-tasks", "far_v2"])


def test_train_accepts_a_v2_task():
    import train
    args = train.build_parser().parse_args(
        ["--model", "llama-8b-instruct", "--task", "far_v2",
         "--deception-condition", "honest"])
    assert args.task == "far_v2"


def test_condition_of_covers_v2():
    from evaluation.circuits import condition_of
    assert condition_of({"task": "far_v2", "deception_condition": "honest"}) == "honest"
    assert condition_of({"task": "ser_v2"}) == "deceptive"
    assert condition_of({"task": "std"}) == "-"
