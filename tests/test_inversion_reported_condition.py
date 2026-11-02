"""
The `inversion_reported` condition (instructed-route B2 plan, ticket T2): the 618
reported-wish SDR rows of F-mech-012 at `<data_dir>/sdr_v2_inversion_reported`,
paired by instance id with the Neutral-Clause Twin in `<data_dir>/sdr_v2_honest`.

It is bound exactly as the directive I condition (`inversion`) is: through a
config-only stand-in whose `deception_condition` names it, resolved by
`instances.dataset_dir`, and twinned by `dataloaders` because its rows carry a
Pressure Clause (the reported wish) that the twin replaces. Nothing trains on
it, so the trainable `DECEPTION_CONDITIONS` stay as they were.

Real tokenizer and real datasets; skip cleanly when absent.
"""

from __future__ import annotations

import importlib.util
import json
import os
from types import SimpleNamespace

import pytest
import torch

from component_analysis import dataloaders, instances, sampling

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "datasets")
REPORTED = "sdr_v2_inversion_reported"
N_REPORTED = 618


def need(name):
    path = os.path.join(DATA, name)
    if not os.path.isdir(path):
        pytest.skip(f"{name} is not built under data/datasets")
    return path


def rows_of(name):
    from datasets import load_from_disk
    return [dict(row) for row in load_from_disk(need(name))["test"]]


def config_of(name):
    with open(os.path.join(need(name), "dataset_config.json")) as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def tokenizer():
    try:
        return instances.load_analysis_tokenizer("llama-8b-instruct")
    except Exception as exc:                                  # noqa: BLE001
        pytest.skip(f"the Llama tokenizer is not available here: {exc}")


def standins_module():
    path = os.path.join(REPO, "scripts", "instructed_route_standins.py")
    spec = importlib.util.spec_from_file_location("instructed_route_standins", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def spec_for(task, condition, data_dir="/data"):
    def build():
        from tasks import get_task
        return get_task(task)
    return SimpleNamespace(name=task, build=build, args=SimpleNamespace(
        data_dir=data_dir, deception_condition=condition, std_variant="azaria"))


# ==============================================================================
# THE DIRECTORY
# ==============================================================================

@pytest.mark.parametrize("task", ["far_v2", "sdr_v2", "ser_v2"])
def test_inversion_reported_resolves_to_its_own_directory(task):
    assert instances.dataset_dir(spec_for(task, "inversion_reported")) == \
        os.path.join("/data", f"{task}_inversion_reported")


@pytest.mark.parametrize("task", ["far_v2", "sdr_v2", "ser_v2"])
def test_inversion_resolves_exactly_as_before(task):
    assert instances.INVERSION_CONDITION == "inversion"
    assert instances.dataset_dir(spec_for(task, "inversion")) == \
        os.path.join("/data", f"{task}_inversion")


def test_the_trainable_conditions_are_unchanged():
    """The I conditions are analysis-only: training still refuses both."""
    from tasks import DECEPTION_CONDITIONS
    from tasks.deception import DeceptionTask

    assert DECEPTION_CONDITIONS == ["deceptive", "honest", "nopressure"]
    task = DeceptionTask()
    task.name = "sdr_v2"
    for condition in ("inversion", "inversion_reported"):
        with pytest.raises(ValueError, match="unknown deception condition"):
            task.dataset_dir(SimpleNamespace(data_dir="/data",
                                             deception_condition=condition))
    assert task.dataset_dir(SimpleNamespace(data_dir="/data",
                                            deception_condition="honest")) == \
        os.path.join("/data", "sdr_v2_honest")


def test_the_real_directory_is_the_reported_wish_split():
    spec = spec_for("sdr_v2", "inversion_reported", data_dir=DATA)
    assert instances.dataset_dir(spec) == need(REPORTED)
    assert config_of(REPORTED)["condition"] == "inversion_reported"
    assert len(instances.load_records(spec)) == N_REPORTED


# ==============================================================================
# THE TWIN
# ==============================================================================

def test_the_reported_condition_is_twinned_and_inversion_still_is():
    assert dataloaders.TWINNED_CONDITIONS[:2] == ("deceptive", "inversion")
    assert "inversion_reported" in dataloaders.TWINNED_CONDITIONS
    for condition in ("deceptive", "inversion", "inversion_reported"):
        assert dataloaders.neutral_twin_reason(
            "sdr_v2", {"task": "sdr_v2", "condition": condition}) is None
    for condition in ("honest", "nopressure"):
        assert dataloaders.neutral_twin_reason(
            "sdr_v2", {"task": "sdr_v2", "condition": condition}) is not None


def test_the_real_reported_config_has_a_twin_in_the_honest_split():
    config = config_of(REPORTED)
    assert dataloaders.neutral_twin_reason("sdr_v2", config) is None
    assert dataloaders.neutral_twin_dir(need(REPORTED), config) == \
        os.path.join(DATA, "sdr_v2_honest")


def make_reported_fixture(tmp_path, n=2):
    """A data dir with `n` real reported-wish rows and their twins, by id.

    The reported split keeps 618 of D's 1,000 ids, so the twins are looked
    up by instance id, never by position.
    """
    from datasets import Dataset, DatasetDict

    pressure = rows_of(REPORTED)[:n]
    honest = {row["instance_id"]: row for row in rows_of("sdr_v2_honest")}
    twins = [honest[row["instance_id"]] for row in pressure]
    root = tmp_path / "datasets"
    for name, rows in ((REPORTED, pressure), ("sdr_v2_honest", twins)):
        DatasetDict({"test": Dataset.from_list(rows)}).save_to_disk(str(root / name))
        with open(root / name / "dataset_config.json", "w") as handle:
            json.dump(config_of(name), handle)
    return str(root / REPORTED), pressure, twins


def test_a_two_row_fixture_builds_aligned_neutral_twin_pairs(tokenizer, tmp_path):
    directory, pressure, twins = make_reported_fixture(tmp_path)
    ids = [row["instance_id"] for row in pressure]
    # The rows really are the reported wish, not D's clause relabelled.
    assert all(row["condition"] == "inversion_reported" for row in pressure)
    assert all(row["pressure"] != row["i_source_pressure"] for row in pressure)

    batches = dataloaders.causal_batches(directory, tokenizer, ids=ids, task="sdr_v2")
    assert batches.report["n_instances"] == 2
    assert batches.report["n_with_neutral_twin"] == 2
    assert batches.report["without_neutral_twin"] == []
    assert batches.report["neutral_twin_source"] == str(tmp_path / "datasets" / "sdr_v2_honest")

    (batch,) = list(batches)
    pair = batch.neutral_twin
    assert isinstance(pair, dataloaders.NeutralTwinPair)
    assert pair.rows == [0, 1]
    for i in range(2):
        start, end = (int(v) for v in pair.clause_span[i])
        assert 0 < start < end
        for mine, theirs, mask in (
                (batch.input_ids[i], pair.input_ids[i], batch.attention_mask[i]),
                (batch.corrupt_input_ids[i], pair.corrupt_input_ids[i],
                 batch.corrupt_attention_mask[i])):
            assert torch.equal(mask, pair.attention_mask[i])
            outside = torch.ones_like(mine, dtype=torch.bool)
            outside[start:end] = False
            assert torch.equal(mine[outside], theirs[outside])
            assert not torch.equal(mine[start:end], theirs[start:end])
        # D's labels are kept: the twin's answer tokens are swapped, the batch's are not.
        assert batch.records[i]["target"] == pressure[i]["target"]
        assert twins[i]["target"] == pressure[i]["distractor"]


def test_every_reported_row_pairs_with_its_twin(tokenizer):
    batches = dataloaders.neutral_twin_batches(need(REPORTED), tokenizer, task="sdr_v2")
    assert batches.report["n_instances"] == N_REPORTED
    assert batches.report["n_with_neutral_twin"] == N_REPORTED
    assert batches.report["without_neutral_twin"] == []
    assert batches.report["dropped_by_tokenization"] == []


# ==============================================================================
# THE STAND-IN AND THE ID FILE
# ==============================================================================

def test_the_standin_is_the_inversion_standin_with_only_the_condition_changed(tmp_path):
    module = standins_module()
    source = os.path.join(REPO, module.SOURCE_STANDIN, "config.json")
    if not os.path.exists(source):
        pytest.skip("the sdr_v2_inversion stand-in is not here")
    path = module.write_standin(REPO, out_repo=str(tmp_path))
    assert path == os.path.join(str(tmp_path), module.STANDIN, "config.json")
    assert module.STANDIN == \
        "outputs/_launch_instructed_route/standins/sdr_v2_inversion_reported"

    with open(source) as handle:
        before = json.load(handle)
    with open(path) as handle:
        after = json.load(handle)
    assert after["deception_condition"] == "inversion_reported"
    assert before["deception_condition"] == "inversion"
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    assert changed <= {"deception_condition", "standin", "standin_source"}
    assert after["standin_of"] == before["standin_of"]
    assert after["task"] == "sdr_v2" and after["data_dir"] == "./data/datasets"

    spec = spec_for(after["task"], after["deception_condition"], data_dir=DATA)
    assert instances.dataset_dir(spec) == os.path.join(DATA, REPORTED)


def test_the_id_file_lists_the_split_ids_and_is_never_overwritten(tmp_path):
    module = standins_module()
    need(REPORTED)
    path, written = module.write_wish_ids(REPO, out_repo=str(tmp_path))
    assert written is True
    with open(path) as handle:
        ids = [line.strip() for line in handle if line.strip()]
    assert ids == sampling.record_ids(rows_of(REPORTED))
    assert len(ids) == len(set(ids)) == N_REPORTED

    with open(path, "w") as handle:
        handle.write("someone_else\n")
    again, written = module.write_wish_ids(REPO, out_repo=str(tmp_path))
    assert again == path and written is False
    with open(path) as handle:
        assert handle.read() == "someone_else\n"
