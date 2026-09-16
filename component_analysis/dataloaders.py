"""
component_analysis/dataloaders.py — the prompts a component analysis runs over.

Two counterfactual pairs per instance, both aligned token for token:

  * the **item-swap pair** (clean prompt, corrupt prompt) the dataset was built
    with, differing at exactly one position — the Designation Site;
  * the **Honest-Instruction Counterfactual** (clean prompt, clean prompt with
    its Pressure Clause replaced by the Matched Honest Instruction), differing
    only inside the clause span, and only for the instances that survived the
    clean-stream honest filter.

Descriptive analyses (attention patterns, DLA, logit lens) run over the whole
test split; causal ones (knockout, path patching) over the fixed-seed sample.
`descriptive_batches` and `causal_batches` are the same machinery with and
without an id list.

**The join is by instance id, never by split index.** `sample.json` says so in
its own `join_on` field: the indices it records are positions in the split as
the task's loader returns it, *before* `DeceptionDatasetLlama` drops any record
whose target or distractor is not a single token. The ids survive that; the
indices do not.

**An instance with no honest counterpart is reported, not dropped.** Most of a
split has no Matched Honest survivor — 629 of 1000 on SDR, and none at all on a
task whose build has not been run — and the item-swap analyses do not care.
Dropping them would silently shrink the causal sample the researcher fixed the
seed for. Each batch carries the honest pair for the rows that have one and
`None` where no row does, so there is no filler row to mistake for data.

Nothing here imports nnsight, or `hooks.py`, at module level: `--dry-run`
resolves the sample and reports how many of it are paired on the login node,
before an hour of GPU is spent.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Sequence

import torch

from component_analysis import sampling

#: Instances per forward. Sized for a 128-token prompt on a 40 GB card under
#: bfloat16; the analyses that need eager attention pay a
#: [batch, heads, seq, seq] buffer per layer and pass a smaller one.
DEFAULT_BATCH_SIZE = 8


@dataclass
class HonestPair:
    """The Honest-Instruction Counterfactual for the rows of a batch that have one.

    `rows` are positions *within the batch*, so `input_ids[i]` is the honest
    prompt of `batch.input_ids[rows[i]]`. There is no row for an instance
    without a counterpart, which is what keeps a missing pair from being read
    as a null effect.
    """

    rows: List[int]
    input_ids: torch.Tensor          # [k, max_length]
    attention_mask: torch.Tensor     # [k, max_length]
    clause_span: torch.Tensor        # [k, 2], half-open token range
    instructions: List[str]


@dataclass
class Batch:
    """One forward's worth of instances, with both counterfactual pairs."""

    ids: List[str]
    records: List[dict]
    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    corrupt_input_ids: torch.Tensor
    corrupt_attention_mask: torch.Tensor
    target_token: torch.Tensor       # [batch]; the corrupt stream's are swapped
    distractor_token: torch.Tensor
    readout: torch.Tensor            # [batch], prefix_length - 1
    honest: Optional[HonestPair]

    def __len__(self) -> int:
        return len(self.ids)


class Batches:
    """An iterable of `Batch`, plus the report of what did and did not join."""

    def __init__(self, items: Sequence[dict], *, batch_size: int, report: dict):
        self._items = list(items)
        self._batch_size = batch_size
        self.report = report

    @property
    def ids(self) -> List[str]:
        return [item["instance_id"] for item in self._items]

    def __len__(self) -> int:
        """The number of *batches*, so that `len(loader)` sizes a progress bar."""
        if not self._items:
            return 0
        return (len(self._items) + self._batch_size - 1) // self._batch_size

    @property
    def n_instances(self) -> int:
        return len(self._items)

    def __iter__(self):
        for start in range(0, len(self._items), self._batch_size):
            yield _collate(self._items[start:start + self._batch_size])


# ==============================================================================
# BUILDING
# ==============================================================================

def _encode(tokenizer, prompt: str, max_length: int):
    encoded = tokenizer(prompt, padding="max_length", max_length=max_length,
                        truncation=True, add_special_tokens=False,
                        return_tensors="pt")
    return (encoded["input_ids"].squeeze(0).long(),
            encoded["attention_mask"].squeeze(0).long())


def _collate(items: Sequence[dict]) -> Batch:
    honest_rows = [row for row, item in enumerate(items) if item["honest"]]
    honest = None
    if honest_rows:
        honest = HonestPair(
            rows=honest_rows,
            input_ids=torch.stack([items[row]["honest"]["input_ids"]
                                   for row in honest_rows]),
            attention_mask=torch.stack([items[row]["honest"]["attention_mask"]
                                        for row in honest_rows]),
            clause_span=torch.tensor([items[row]["honest"]["clause_span"]
                                      for row in honest_rows], dtype=torch.long),
            instructions=[items[row]["honest"]["instruction"]
                          for row in honest_rows])
    return Batch(
        ids=[item["instance_id"] for item in items],
        records=[item["record"] for item in items],
        input_ids=torch.stack([item["input_ids"] for item in items]),
        attention_mask=torch.stack([item["attention_mask"] for item in items]),
        corrupt_input_ids=torch.stack([item["corrupt_input_ids"] for item in items]),
        corrupt_attention_mask=torch.stack([item["corrupt_attention_mask"]
                                            for item in items]),
        target_token=torch.tensor([item["target_token"] for item in items],
                                  dtype=torch.long),
        distractor_token=torch.tensor([item["distractor_token"] for item in items],
                                      dtype=torch.long),
        readout=torch.tensor([item["readout"] for item in items], dtype=torch.long),
        honest=honest)


def _honest_by_id(dataset_dir: str, tokenizer, *, split: str, task: Optional[str],
                  pools_dir: Optional[str], max_length: int,
                  honest_streams: Optional[str]):
    """({instance id: honest item}, how the pairs were found).

    The pairs come from `dataset.matched_honest.load_matched_honest`, which
    re-derives each honest prompt from the pool and re-asserts the clause-span
    alignment as it loads, so a pool that has drifted from the dataset fails
    here rather than in the middle of a patch.
    """
    from dataset import matched_honest as mh

    if not os.path.exists(os.path.join(dataset_dir, mh.SURVIVORS_FILE)):
        return {}, "absent"

    paired = mh.load_matched_honest(
        dataset_dir, tokenizer, split=split, task=task, pools_dir=pools_dir,
        max_length=max_length, survivors_only=True,
        honest_streams=honest_streams)

    out = {}
    for index in range(len(paired)):
        item = paired.item(index)
        input_ids, attention_mask = _encode(tokenizer, item["honest_prompt"],
                                            max_length)
        out[item["instance_id"]] = {
            "input_ids": input_ids, "attention_mask": attention_mask,
            "clause_span": list(item["clause_span"]),
            "instruction": item["matched_honest_instruction"]}
    return out, mh.SURVIVORS_FILE


def _batches(dataset_dir: str, tokenizer, *, ids: Optional[Sequence[str]],
             task: Optional[str], split: str, batch_size: int,
             max_length: Optional[int], pools_dir: Optional[str],
             honest_streams: Optional[str], with_honest: bool) -> Batches:
    from dataset import deception_common as dc

    config = dc.load_dataset_config(dataset_dir)
    task = task or config.get("task")
    if max_length is None:
        max_length = int(config.get("max_seq_length", dc.MAX_SEQ_LENGTH))

    records = dc.load_or_generate_deception_data(dataset_dir, split=split)
    record_ids = sampling.record_ids(records)
    by_id = dict(zip(record_ids, records))

    wanted = list(ids) if ids is not None else record_ids
    missing = [one for one in wanted if one not in by_id]
    selected = [by_id[one] for one in wanted if one in by_id]

    dataset = dc.DeceptionDatasetLlama(selected, tokenizer, max_length=max_length)
    kept = {item["instance_id"]: item for item in dataset.processed_data
            if "instance_id" in item}
    dropped = [one for one in wanted if one in by_id and one not in kept]

    honest, source = ({}, "not requested")
    if with_honest:
        honest, source = _honest_by_id(
            dataset_dir, tokenizer, split=split, task=task, pools_dir=pools_dir,
            max_length=max_length, honest_streams=honest_streams)

    items, without_honest = [], []
    for one in wanted:
        item = kept.get(one)
        if item is None:
            continue
        input_ids, attention_mask = _encode(tokenizer, item["clean_prompt"],
                                            max_length)
        corrupt_ids, corrupt_mask = _encode(tokenizer, item["corrupt_prompt"],
                                            max_length)
        readout = int(item["prefix_length"]) - 1
        if readout != int(attention_mask.sum()) - 1:
            raise ValueError(
                f"instance {one}: the Readout is prefix_length - 1 = {readout} "
                f"but the last unpadded position is "
                f"{int(attention_mask.sum()) - 1}. Every analysis reads the "
                f"Readout off the attention mask, so this tokenizer must pad "
                f"on the right.")
        pair = honest.get(one)
        if with_honest and pair is None:
            without_honest.append(one)
        items.append({
            "instance_id": one, "record": item,
            "input_ids": input_ids, "attention_mask": attention_mask,
            "corrupt_input_ids": corrupt_ids,
            "corrupt_attention_mask": corrupt_mask,
            "target_token": int(item["target_token"]),
            "distractor_token": int(item["distractor_token"]),
            "readout": readout, "honest": pair})

    report = {
        "task": task, "split": split, "batch_size": batch_size,
        "max_length": max_length,
        "n_requested": len(wanted), "n_instances": len(items),
        "missing_from_split": missing,
        "dropped_by_tokenization": dropped,
        "honest_source": source,
        "honest_streams": honest_streams if with_honest else None,
        "n_with_honest": len(items) - len(without_honest) if with_honest else 0,
        "without_honest": without_honest,
    }
    return Batches(items, batch_size=batch_size, report=report)


def causal_batches(dataset_dir: str, tokenizer, *, ids: Sequence[str],
                   task: Optional[str] = None, split: str = "test",
                   batch_size: int = DEFAULT_BATCH_SIZE,
                   max_length: Optional[int] = None,
                   pools_dir: Optional[str] = None,
                   honest_streams: Optional[str] = None) -> Batches:
    """The sampled instances, with both counterfactual pairs.

    `ids` are `sample.json`'s instance ids and the batches come back in that
    order. `honest_streams` defaults to the clean-stream criterion the
    researcher chose for the Honest-Instruction Counterfactual; it is the only
    stream the pair contains.
    """
    from dataset.matched_honest import DEFAULT_HONEST_STREAMS

    return _batches(
        dataset_dir, tokenizer, ids=ids, task=task, split=split,
        batch_size=batch_size, max_length=max_length, pools_dir=pools_dir,
        honest_streams=honest_streams or DEFAULT_HONEST_STREAMS,
        with_honest=True)


def descriptive_batches(dataset_dir: str, tokenizer, *, task: Optional[str] = None,
                        split: str = "test",
                        batch_size: int = DEFAULT_BATCH_SIZE,
                        max_length: Optional[int] = None) -> Batches:
    """The whole split, item-swap pair only.

    The descriptive analyses read the pressure prompts over the full test set
    and take their honest column from a bound reference task, not from the
    paired counterfactual, so this loader does not build one.
    """
    return _batches(dataset_dir, tokenizer, ids=None, task=task, split=split,
                    batch_size=batch_size, max_length=max_length,
                    pools_dir=None, honest_streams=None, with_honest=False)


def batches_for_task(task_spec, tokenizer, *, ids: Optional[Sequence[str]] = None,
                     split: str = "test",
                     batch_size: int = DEFAULT_BATCH_SIZE,
                     max_length: Optional[int] = None,
                     pools_dir: Optional[str] = None,
                     honest_streams: Optional[str] = None) -> Batches:
    """The CLI's entry point: ask the task where its dataset is, then load it.

    `ids=None` gives the descriptive loader over the whole split; an id list
    gives the causal one with both counterfactual pairs.
    """
    from component_analysis import instances

    directory = instances.dataset_dir(task_spec)
    if ids is None:
        return descriptive_batches(directory, tokenizer, task=task_spec.name,
                                   split=split, batch_size=batch_size,
                                   max_length=max_length)
    return causal_batches(directory, tokenizer, ids=ids, task=task_spec.name,
                          split=split, batch_size=batch_size,
                          max_length=max_length, pools_dir=pools_dir,
                          honest_streams=honest_streams)


def summarize(batches: Batches) -> List[str]:
    """The lines `--dry-run` prints about a loader, one fact each."""
    report = batches.report
    lines = [f"{report['n_instances']} instance(s) of {report['n_requested']} "
             f"requested, {len(batches)} batch(es) of {report['batch_size']}"]
    if report["missing_from_split"]:
        lines.append(f"!! {len(report['missing_from_split'])} id(s) are not in "
                     f"the {report['split']} split: "
                     f"{', '.join(report['missing_from_split'][:3])}")
    if report["dropped_by_tokenization"]:
        lines.append(f"!! {len(report['dropped_by_tokenization'])} id(s) dropped "
                     f"because an answer word is not a single token")
    if report["honest_source"] == "absent":
        lines.append("no Matched Honest survivors file for this task, so no "
                     "Honest-Instruction Counterfactual")
    elif report["honest_source"] != "not requested":
        lines.append(f"honest-instruction pair on {report['n_with_honest']} of "
                     f"{report['n_instances']} ({report['honest_streams']} "
                     f"criterion); {len(report['without_honest'])} without")
    return lines

