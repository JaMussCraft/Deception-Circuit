"""
Library-seam tests for `component_analysis/dataloaders.py`.

A real SDR split on disk, built by the repo's own `generate_task_data` from the
real pools and tokenized with `tests.fakes.FakeWordTokenizer`, the way
`tests/test_analyze_components_segmentation.py` does it — so the prompts are
real SDR prompts and the joins are the joins the cluster will do.

Nothing here loads a model or imports nnsight: the dataloaders are the part of
the causal analyses that has to resolve on the login node, under `--dry-run`,
before an hour of GPU is spent on a sample that turns out to be half unpaired.
"""

from __future__ import annotations

import json

import pytest
import torch

from component_analysis import dataloaders, sampling
from dataset import matched_honest as mh
from dataset import deception_common as dc
from tests.fakes import FakeWordTokenizer

N_RECORDS = 24
MAX_LENGTH = 128


# ==============================================================================
# FIXTURE
# ==============================================================================

@pytest.fixture
def sdr_split(tmp_path):
    """(dataset dir, pools dir, records, tokenizer, honest survivor ids).

    Two thirds of the split survive the Matched Honest filter, so every test
    here sees both a paired instance and an unpaired one.
    """
    datasets = pytest.importorskip("datasets")
    tokenizer = FakeWordTokenizer()

    records = dc.generate_task_data(
        tokenizer, dc.SPECS["sdr"], N_RECORDS, dc.load_entities()[:4],
        dc.load_item_pairs()[:6], dc.load_pressures("sdr")[:3], seed=0)

    dataset_dir = tmp_path / "sdr"
    datasets.DatasetDict({"test": datasets.Dataset.from_list(records)}) \
        .save_to_disk(str(dataset_dir))
    with open(dataset_dir / "dataset_config.json", "w") as handle:
        json.dump({"task": "sdr", "max_seq_length": MAX_LENGTH,
                   "margin_thresh": 1.0}, handle)

    # The real candidate ladder is matched in the Llama tokenizer, so the pool
    # is rebuilt here against the whitespace one: `build_pool` picks whichever
    # candidate has the clause's token count in the tokenizer it is given.
    pool, unmatched = mh.build_pool(
        tokenizer, dc.load_pressures("sdr")[:3], mh.load_candidates(),
        lambda pressure: [r["clean_prompt"] for r in records
                          if r["pressure"] == pressure["text"]][:1])
    assert not unmatched, unmatched
    pools_dir = tmp_path / "pools"
    mh.write_matched_honest_pool("sdr", pool, pools_dir=str(pools_dir),
                                 meta={"model": "fake"})

    survivors = records[:2 * N_RECORDS // 3]
    ids = [r["instance_id"] for r in survivors]
    mh.write_survivors(str(dataset_dir), "sdr", survivors,
                       {"overall": {"n_survivors": len(survivors)},
                        "honest_streams": "clean",
                        "survivor_ids": {"clean": ids, "both": ids[:1]}})
    return dataset_dir, pools_dir, records, tokenizer, set(ids)


def load(sdr_split, ids, **kwargs):
    dataset_dir, pools_dir, _records, tokenizer, _survivors = sdr_split
    return dataloaders.causal_batches(
        str(dataset_dir), tokenizer, ids=ids, task="sdr",
        pools_dir=str(pools_dir), max_length=MAX_LENGTH, **kwargs)


# ==============================================================================
# THE JOIN
# ==============================================================================

def test_batches_carry_the_sampled_instances_in_the_order_they_were_asked_for(
        sdr_split):
    _dir, _pools, records, _tok, _survivors = sdr_split
    wanted = [records[i]["instance_id"] for i in (7, 1, 4)]

    batches = load(sdr_split, wanted, batch_size=2)

    assert [i for batch in batches for i in batch.ids] == wanted
    assert [len(batch.ids) for batch in batches] == [2, 1]


def test_an_id_the_split_does_not_hold_is_reported_not_guessed(sdr_split):
    _dir, _pools, records, _tok, _survivors = sdr_split
    wanted = [records[0]["instance_id"], "not-an-instance"]

    batches = load(sdr_split, wanted)

    assert batches.report["missing_from_split"] == ["not-an-instance"]
    assert [i for batch in batches for i in batch.ids] == [wanted[0]]


def test_the_join_is_by_instance_id_not_by_position(sdr_split):
    """`sample.json`'s own `join_on` rule, asserted rather than trusted.

    The sample records split indices as well as ids, and they are positions in
    the split *before* the dataset class drops anything. Asking for one id and
    getting the record that id names — not the record at that id's index — is
    the property every causal analysis rests on.
    """
    _dir, _pools, records, _tok, _survivors = sdr_split
    wanted = [records[9]["instance_id"]]

    batch = next(iter(load(sdr_split, wanted)))

    assert batch.records[0]["clean_prompt"] == records[9]["clean_prompt"]
    assert batch.records[0]["target"] == records[9]["target"]


# ==============================================================================
# THE TWO COUNTERFACTUAL PAIRS
# ==============================================================================

def test_the_item_swap_pair_differs_at_exactly_the_designation_site(sdr_split):
    _dir, _pools, records, tokenizer, _survivors = sdr_split
    ids = [r["instance_id"] for r in records[:4]]

    for batch in load(sdr_split, ids, batch_size=4):
        for row in range(len(batch.ids)):
            differing = (batch.input_ids[row] != batch.corrupt_input_ids[row]) \
                .nonzero().flatten().tolist()
            assert len(differing) == 1
            position = differing[0]
            record = batch.records[row]
            assert batch.input_ids[row, position] == \
                tokenizer.encode(" " + record["clean_item_d"])[0]
            assert batch.corrupt_input_ids[row, position] == \
                tokenizer.encode(" " + record["corrupt_item_d"])[0]


def test_the_honest_pair_differs_only_inside_the_pressure_clause_span(sdr_split):
    _dir, _pools, records, _tok, survivors = sdr_split
    ids = [r["instance_id"] for r in records[:6]]

    for batch in load(sdr_split, ids, batch_size=6):
        honest = batch.honest
        assert honest is not None
        for index, row in enumerate(honest.rows):
            start, end = honest.clause_span[index].tolist()
            differing = (batch.input_ids[row] != honest.input_ids[index]) \
                .nonzero().flatten().tolist()
            assert differing, "the honest prompt is not the pressure prompt"
            assert all(start <= position < end for position in differing)
            assert batch.ids[row] in survivors


def test_an_instance_with_no_honest_counterpart_is_reported_not_dropped(sdr_split):
    _dir, _pools, records, _tok, survivors = sdr_split
    unpaired = [r["instance_id"] for r in records
                if r["instance_id"] not in survivors][:2]
    paired = [r["instance_id"] for r in records[:2]]

    batches = load(sdr_split, paired + unpaired, batch_size=4)
    batch = next(iter(batches))

    assert batch.ids == paired + unpaired
    assert [batch.ids[row] for row in batch.honest.rows] == paired
    assert batches.report["without_honest"] == unpaired
    assert batches.report["n_with_honest"] == len(paired)


def test_a_batch_where_no_instance_has_a_counterpart_carries_no_honest_pair(
        sdr_split):
    _dir, _pools, records, _tok, survivors = sdr_split
    unpaired = [r["instance_id"] for r in records
                if r["instance_id"] not in survivors][:2]

    batch = next(iter(load(sdr_split, unpaired, batch_size=2)))

    assert batch.honest is None


def test_without_a_survivors_file_the_item_swap_pairs_still_load(sdr_split,
                                                                 tmp_path):
    """Only SDR has been through the Matched Honest build; FAR and SER have not."""
    dataset_dir, _pools, records, _tok, _survivors = sdr_split
    (dataset_dir / mh.SURVIVORS_FILE).unlink()

    batches = load(sdr_split, [records[0]["instance_id"]])
    batch = next(iter(batches))

    assert batch.honest is None
    assert batches.report["honest_source"] == "absent"
    assert batch.corrupt_input_ids.shape == batch.input_ids.shape


# ==============================================================================
# THE READOUT
# ==============================================================================

def test_the_readout_is_the_last_unpadded_position(sdr_split):
    _dir, _pools, records, tokenizer, _survivors = sdr_split
    ids = [r["instance_id"] for r in records[:3]]

    batch = next(iter(load(sdr_split, ids, batch_size=3)))

    assert torch.equal(batch.readout, batch.attention_mask.sum(-1) - 1)
    for row, record in enumerate(batch.records):
        prefix = len(tokenizer.encode(record["clean_prompt"]))
        assert int(batch.readout[row]) == prefix - 1


def test_target_and_distractor_are_the_records_own_answer_tokens(sdr_split):
    _dir, _pools, records, tokenizer, _survivors = sdr_split
    ids = [r["instance_id"] for r in records[:3]]

    batch = next(iter(load(sdr_split, ids, batch_size=3)))

    for row, record in enumerate(batch.records):
        assert int(batch.target_token[row]) == \
            tokenizer.encode(" " + record["target"])[0]
        assert int(batch.distractor_token[row]) == \
            tokenizer.encode(" " + record["distractor"])[0]


# ==============================================================================
# THE DESCRIPTIVE LOADER
# ==============================================================================

def test_the_descriptive_loader_covers_the_whole_split(sdr_split):
    dataset_dir, _pools, records, tokenizer, _survivors = sdr_split

    batches = dataloaders.descriptive_batches(
        str(dataset_dir), tokenizer, task="sdr", max_length=MAX_LENGTH,
        batch_size=5)

    seen = [i for batch in batches for i in batch.ids]
    assert seen == sampling.record_ids(records)
    assert batches.report["n_with_honest"] == 0


# ==============================================================================
# WHAT THESE LOADERS DO NOT COVER
# ==============================================================================

def test_std_is_refused_by_name_rather_than_yielding_an_empty_loader(sdr_split):
    """STD segments and samples, but neither counterfactual pair is its own.

    Its Corruption swaps the Designating Stipulation, not an item, and
    "accurate" / "inaccurate" are several tokens each, so the mechanism dataset
    class drops every instance. Before this check the STD dry run reported "100
    id(s) dropped because an answer word is not a single token", which is true
    and points at the data rather than at the loader.
    """
    dataset_dir, _pools, _records, tokenizer, _survivors = sdr_split

    assert dataloaders.uncovered_reason("sdr") is None
    assert "mechanism tasks" in dataloaders.uncovered_reason("std")

    with pytest.raises(ValueError, match="not one of the mechanism tasks"):
        dataloaders.causal_batches(str(dataset_dir), tokenizer, ids=[],
                                   task="std")


def test_records_with_no_instance_id_still_join_on_their_positional_ids(
        sdr_split, tmp_path):
    """`sampling.record_id` falls back to the split position, and so must the join.

    Before this check the loader keyed the split by `record_ids` but keyed the
    kept records by `instance_id`, so a task whose records carry none — STD —
    matched nothing and every id was reported as "dropped because an answer
    word is not a single token". A false diagnosis is worse than a crash.
    """
    datasets = pytest.importorskip("datasets")
    _dir, _pools, records, tokenizer, _survivors = sdr_split

    stripped = [{k: v for k, v in r.items() if k != "instance_id"}
                for r in records[:6]]
    anonymous = tmp_path / "anonymous"
    datasets.DatasetDict({"test": datasets.Dataset.from_list(stripped)}) \
        .save_to_disk(str(anonymous))
    with open(anonymous / "dataset_config.json", "w") as handle:
        json.dump({"task": "sdr", "max_seq_length": MAX_LENGTH}, handle)

    wanted = sampling.record_ids(stripped)
    batches = dataloaders.causal_batches(str(anonymous), tokenizer, ids=wanted,
                                         task="sdr", max_length=MAX_LENGTH)

    assert wanted == [f"index{i:06d}" for i in range(len(stripped))]
    assert batches.report["dropped_by_tokenization"] == []
    assert [i for batch in batches for i in batch.ids] == wanted


def test_the_retention_rule_still_agrees_with_the_repos_dataset_class(sdr_split):
    """The rule is applied here now, so it has to stay the same rule."""
    dataset_dir, _pools, records, tokenizer, _survivors = sdr_split

    batches = dataloaders.descriptive_batches(str(dataset_dir), tokenizer,
                                              task="sdr", max_length=MAX_LENGTH)
    dataset = dc.DeceptionDatasetLlama(records, tokenizer, max_length=MAX_LENGTH)

    assert batches.ids == [item["instance_id"] for item in dataset.processed_data]
