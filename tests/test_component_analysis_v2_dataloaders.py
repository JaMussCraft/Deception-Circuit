"""
The `neutral_twin` paired kind (ticket 02a, spec R1, R16): a v2 pressure prompt
(D, or the I condition) paired with its Neutral-Clause Twin from
`<data_dir>/<task>_honest`, joined by instance id, clause-aligned in both
streams, D's labels kept.

The column trap: D rows carry `neutral_prompt`, which is the Prior-Balance
prompt (Designating Sentence neutralized, clause KEPT). It is not the twin, and
a test here says so with the tokens.

Real tokenizer and real datasets; skip cleanly when absent.
"""

from __future__ import annotations

import json
import os

import pytest

from component_analysis import dataloaders, sampling

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "datasets")


@pytest.fixture(scope="module")
def tokenizer():
    try:
        from component_analysis import instances
        return instances.load_analysis_tokenizer("llama-8b-instruct")
    except Exception as exc:                                  # noqa: BLE001
        pytest.skip(f"the Llama tokenizer is not available here: {exc}")


def need(name):
    path = os.path.join(DATA, name)
    if not os.path.isdir(path):
        pytest.skip(f"{name} is not built under data/datasets")
    return path


def test_rows(name):
    from datasets import load_from_disk
    return [dict(row) for row in load_from_disk(need(name))["test"]]


test_rows.__test__ = False


@pytest.fixture(scope="module")
def sdr_sample_ids():
    return sampling.draw_sample(test_rows("sdr_v2"), n=100, seed=0).ids


def test_v2_ids_are_mechanism_tasks_and_v1_ids_still_are():
    for task in ("far", "sdr", "ser", "far_v2", "sdr_v2", "ser_v2"):
        assert dataloaders.uncovered_reason(task) is None
    assert dataloaders.uncovered_reason("std") is not None


def test_the_causal_sample_pairs_every_instance_with_its_neutral_twin(
        tokenizer, sdr_sample_ids):
    batches = dataloaders.causal_batches(need("sdr_v2"), tokenizer,
                                         ids=sdr_sample_ids, task="sdr_v2")
    report = batches.report
    assert report["n_with_neutral_twin"] == 100
    assert report["neutral_twin_source"].endswith(os.path.join("datasets", "sdr_v2_honest"))
    assert any("neutral-clause twin on 100 of 100" in line
               for line in dataloaders.summarize(batches))


def test_the_twin_is_the_honest_split_row_and_never_the_neutral_prompt_column(
        tokenizer, sdr_sample_ids):
    d_rows = {row["instance_id"]: row for row in test_rows("sdr_v2")}
    h_rows = {row["instance_id"]: row for row in test_rows("sdr_v2_honest")}
    batches = dataloaders.causal_batches(need("sdr_v2"), tokenizer,
                                         ids=sdr_sample_ids[:16], task="sdr_v2")
    checked = 0
    for batch in batches:
        twin = batch.neutral_twin
        assert twin is not None and twin.rows == list(range(len(batch)))
        for row, one in enumerate(batch.ids):
            ids = twin.input_ids[row][twin.attention_mask[row].bool()].tolist()
            h_ids = tokenizer.encode(h_rows[one]["clean_prompt"], add_special_tokens=False)
            trap = tokenizer.encode(d_rows[one]["neutral_prompt"], add_special_tokens=False)
            assert ids == h_ids
            assert ids != trap
            corrupt = twin.corrupt_input_ids[row][twin.corrupt_attention_mask[row].bool()]
            assert corrupt.tolist() == tokenizer.encode(
                h_rows[one]["corrupt_prompt"], add_special_tokens=False)
            # Aligned with D outside the clause span, D's labels kept.
            start, end = twin.clause_span[row].tolist()
            d_ids = batch.input_ids[row].tolist()
            twin_ids = twin.input_ids[row].tolist()
            assert d_ids[:start] == twin_ids[:start]
            assert d_ids[end:] == twin_ids[end:]
            assert d_ids[start:end] != twin_ids[start:end]
            assert tokenizer.decode(batch.target_token[row]).strip() == d_rows[one]["target"]
            checked += 1
    assert checked == 16


def test_the_whole_split_pairs_one_thousand_of_one_thousand(tokenizer):
    batches = dataloaders.neutral_twin_batches(need("far_v2"), tokenizer, task="far_v2")
    assert batches.n_instances == 1000
    assert batches.report["n_with_neutral_twin"] == 1000
    assert not batches.report["without_neutral_twin"]


def test_the_v1_causal_loader_report_is_unchanged(tokenizer):
    ids = sampling.draw_sample(test_rows("sdr"), n=8, seed=0).ids
    report = dataloaders.causal_batches(need("sdr"), tokenizer, ids=ids,
                                        task="sdr").report
    assert not [key for key in report if "neutral" in key]


@pytest.mark.parametrize("condition, why", [("honest", "is the Neutral-Clause Twin"),
                                             ("nopressure", "no Pressure Clause")])
def test_on_h_and_f_the_pairing_is_reported_not_applicable(tokenizer, condition, why):
    ids = [row["instance_id"] for row in test_rows(f"sdr_v2_{condition}")[:8]]
    batches = dataloaders.causal_batches(need(f"sdr_v2_{condition}"), tokenizer,
                                         ids=ids, task="sdr_v2")
    assert batches.report["n_with_neutral_twin"] == 0
    assert why in batches.report["neutral_twin_source"]
    assert all(batch.neutral_twin is None for batch in batches)


# ==============================================================================
# FIXTURE DATASETS: the I condition, and what is refused
# ==============================================================================

def make_fixture(tmp_path, *, pressure_name="sdr_v2_inversion", condition="inversion",
                 twin_kind="neutral_clause", mutate_twin=None, n=4):
    """A data dir with a 4-row pressure split and its twin split."""
    from datasets import Dataset, DatasetDict

    d_rows = test_rows("sdr_v2")[:n]
    h_rows = test_rows("sdr_v2_honest")[:n]
    pressure = [dict(row, condition=condition) for row in d_rows]
    twins = [dict(row) for row in h_rows]
    if mutate_twin:
        mutate_twin(twins)
    root = tmp_path / "datasets"
    for name, rows, source in ((pressure_name, pressure, "sdr_v2"),
                               ("sdr_v2_honest", twins, "sdr_v2_honest")):
        DatasetDict({"test": Dataset.from_list(rows)}).save_to_disk(str(root / name))
        with open(os.path.join(DATA, source, "dataset_config.json")) as handle:
            config = json.load(handle)
        if name == pressure_name:
            config["condition"] = condition
        else:
            config["honest_twin_kind"] = twin_kind
        with open(root / name / "dataset_config.json", "w") as handle:
            json.dump(config, handle)
    return str(root / pressure_name), [row["instance_id"] for row in d_rows]


def test_the_inversion_condition_pairs_with_the_same_twin_split(tokenizer, tmp_path):
    directory, ids = make_fixture(tmp_path)
    batches = dataloaders.causal_batches(directory, tokenizer, ids=ids, task="sdr_v2")
    assert batches.report["n_with_neutral_twin"] == 4
    assert batches.report["neutral_twin_source"] == str(tmp_path / "datasets" / "sdr_v2_honest")


def test_a_twin_split_that_is_not_the_neutral_clause_twin_is_refused(tokenizer, tmp_path):
    directory, ids = make_fixture(tmp_path, twin_kind="matched_honest")
    with pytest.raises(ValueError, match="neutral_clause"):
        dataloaders.causal_batches(directory, tokenizer, ids=ids, task="sdr_v2")


def test_a_twin_with_another_pressure_id_is_refused(tokenizer, tmp_path):
    def swap(rows):
        rows[1]["pressure_id"] = "somewhere_else"
    directory, ids = make_fixture(tmp_path, mutate_twin=swap)
    with pytest.raises(ValueError, match="pressure_id"):
        dataloaders.causal_batches(directory, tokenizer, ids=ids, task="sdr_v2")


def test_a_twin_that_is_not_clause_aligned_is_refused(tokenizer, tmp_path):
    def lengthen(rows):
        row = rows[2]
        longer = row["pressure"][:-1] + " and nothing else happened."
        for key in ("clean_prompt", "corrupt_prompt"):
            row[key] = row[key].replace(row["pressure"], longer)
        row["pressure"] = longer
    directory, ids = make_fixture(tmp_path, mutate_twin=lengthen)
    with pytest.raises(ValueError, match="not clause-aligned"):
        dataloaders.causal_batches(directory, tokenizer, ids=ids, task="sdr_v2")


def test_an_instance_with_no_twin_row_is_reported_not_dropped(tokenizer, tmp_path):
    def drop(rows):
        del rows[3]
    directory, ids = make_fixture(tmp_path, mutate_twin=drop)
    batches = dataloaders.causal_batches(directory, tokenizer, ids=ids, task="sdr_v2")
    assert batches.n_instances == 4
    assert batches.report["n_with_neutral_twin"] == 3
    assert batches.report["without_neutral_twin"] == [ids[3]]
