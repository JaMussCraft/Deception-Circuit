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

**The retention rule is applied here, by id.** `DeceptionDatasetLlama` keeps
only records whose Target and Distractor are single tokens, and it keeps them
in a list with no key back to the ids the sample named. Joining a split's ids
against that list by `instance_id` loses every task whose records carry none
(the ids fall back to the split position), and the loss shows up as "dropped
because an answer word is not a single token" whether or not that is true. So
the same rule is applied here instead, against the ids `sampling.record_ids`
produced, and `dropped_by_tokenization` holds exactly the ids it really
dropped. A test asserts the rule still agrees with the dataset class.

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

class LoaderUnavailable(ValueError):
    """These loaders do not cover this task, or this cell has no causal sample.

    Its own class because `--dry-run` turns it into a printed "not applicable"
    line and keeps going, while any other failure is a bad configuration and
    must stop the run on the login node.
    """


#: The tasks these loaders cover. Both pairs they build are properties of the
#: mechanism tasks: the item-swap Corruption edits the Designation Site, and the
#: Matched Honest Instruction replaces a Pressure Clause. STD is segmentable and
#: samples fine, but its Corruption swaps the Designating Stipulation rather
#: than an item, and its answer words ("accurate" / "inaccurate") are several
#: tokens each, which `DeceptionDatasetLlama` drops on sight — all 1000 of them.
#: A causal loader for STD is its own piece of work, not a silent empty batch.
#:
#: The v2 ids (mechanism-datasets) are the same three mechanisms on the aligned
#: v2 Scaffold, with the same item-swap Corruption and single-token answers.
#: Their paired honest counterpart is the Neutral-Clause Twin (`neutral_twin`
#: below), not a Matched Honest Instruction: v2 has no matched pools.
V2_TASKS = ("far_v2", "sdr_v2", "ser_v2")
MECHANISM_TASKS = ("far", "sdr", "ser") + V2_TASKS

#: The record `condition`s whose prompts carry a Pressure Clause that the
#: Neutral-Clause Twin replaces: D, and the instructed-inversion control I.
TWINNED_CONDITIONS = ("deceptive", "inversion")
#: What the twin split must say it is.
NEUTRAL_TWIN_KIND = "neutral_clause"

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
class NeutralTwinPair:
    """The Neutral-Clause Twin of the rows of a v2 batch that have one.

    `rows` are positions within the batch. Both streams of the twin are kept
    (its clean prompt pairs with the batch's clean prompt, its corrupt prompt
    with the corrupt one), each clause-aligned with its partner: identical
    tokens outside `clause_span`, the same length, the same Readout. The
    batch's Target and Distractor are the pressure prompt's (D's labels), so a
    number read on the twin is in the same direction as one read on D.
    """

    rows: List[int]
    input_ids: torch.Tensor              # [k, max_length], the twin's clean prompt
    attention_mask: torch.Tensor
    corrupt_input_ids: torch.Tensor      # the twin's corrupt prompt
    corrupt_attention_mask: torch.Tensor
    clause_span: torch.Tensor            # [k, 2], half-open token range


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
    #: v2 only: the Neutral-Clause Twin (None on v1, and on H and F cells).
    neutral_twin: Optional[NeutralTwinPair] = None

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

def uncovered_reason(task: Optional[str]) -> Optional[str]:
    """Why these loaders do not cover `task`, or None when they do."""
    if task in MECHANISM_TASKS:
        return None
    return (f"task {task!r} is not one of the mechanism tasks "
            f"({', '.join(MECHANISM_TASKS)}), whose item-swap Corruption and "
            f"Pressure Clause these loaders pair on. Its answer words are not "
            f"single tokens either, so the mechanism dataset class would drop "
            f"every instance and hand back an empty loader")


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
    twin_rows = [row for row, item in enumerate(items) if item.get("neutral_twin")]
    twin = None
    if twin_rows:
        def stack(field):
            return torch.stack([items[row]["neutral_twin"][field] for row in twin_rows])
        twin = NeutralTwinPair(
            rows=twin_rows, input_ids=stack("input_ids"),
            attention_mask=stack("attention_mask"),
            corrupt_input_ids=stack("corrupt_input_ids"),
            corrupt_attention_mask=stack("corrupt_attention_mask"),
            clause_span=torch.tensor([items[row]["neutral_twin"]["clause_span"]
                                      for row in twin_rows], dtype=torch.long))
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
        honest=honest, neutral_twin=twin)


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


def neutral_twin_dir(dataset_dir: str, config: dict) -> str:
    """`<data_dir>/<task>_honest`, from the dataset's own task name.

    Not `dataset_dir + "_honest"`: the I condition lives at
    `<task>_inversion`, and its twin is the same `<task>_honest` D's is.
    """
    return os.path.join(os.path.dirname(os.path.abspath(dataset_dir)),
                        f"{config['task']}_honest")


def neutral_twin_reason(task: Optional[str], config: dict) -> Optional[str]:
    """Why this dataset has no Neutral-Clause Twin pairing, or None when it has."""
    if task not in V2_TASKS:
        return f"task {task!r} is not a v2 task; only v2 has a Neutral-Clause Twin"
    condition = config.get("condition") or "deceptive"
    if condition == "honest":
        return ("not applicable: this test set is the Neutral-Clause Twin "
                "itself (condition honest)")
    if condition == "nopressure":
        return ("not applicable: the nopressure condition has no Pressure "
                "Clause for a twin to replace")
    if condition not in TWINNED_CONDITIONS:
        return f"not applicable: condition {condition!r} has no twin"
    return None


def _neutral_twins_by_id(dataset_dir: str, tokenizer, kept: dict, *, config: dict,
                         split: str, max_length: int):
    """({instance id: twin item}, twin directory), for the kept pressure rows.

    Every pairing is checked rather than trusted: the split must say it is the
    Neutral-Clause Twin, each twin row must carry the pressure row's
    `pressure_id`, and both streams must be clause-aligned with their partner
    (`matched_honest.assert_clause_aligned_pair`, the pressure row's own clause
    locating the span). The twin is read from the `_honest` split's
    `clean_prompt` / `corrupt_prompt`; the pressure rows' `neutral_prompt`
    column is the Prior-Balance prompt and is never read here.
    """
    from dataset import deception_common as dc
    from dataset.matched_honest import assert_clause_aligned_pair

    directory = neutral_twin_dir(dataset_dir, config)
    twin_config = dc.load_dataset_config(directory)
    if twin_config.get("honest_twin_kind") != NEUTRAL_TWIN_KIND:
        raise ValueError(
            f"{directory} is not a Neutral-Clause Twin split: its "
            f"dataset_config.json says honest_twin_kind "
            f"{twin_config.get('honest_twin_kind')!r}, not {NEUTRAL_TWIN_KIND!r}")
    twins = {}
    for index, row in enumerate(dc.load_or_generate_deception_data(directory, split=split)):
        twins[sampling.record_id(row, index)] = row

    out = {}
    for one, record in kept.items():
        twin = twins.get(one)
        if twin is None:
            continue
        if twin.get("honest_twin_kind") != NEUTRAL_TWIN_KIND or \
                twin.get("condition") != "honest":
            raise ValueError(
                f"instance {one}: the row in {directory} is condition "
                f"{twin.get('condition')!r}, kind {twin.get('honest_twin_kind')!r}, "
                f"not an honest {NEUTRAL_TWIN_KIND} twin")
        if twin.get("pressure_id") != record.get("pressure_id"):
            raise ValueError(
                f"instance {one}: the twin's pressure_id {twin.get('pressure_id')!r} "
                f"is not the pressure row's {record.get('pressure_id')!r}")
        spans = []
        for stream in ("clean_prompt", "corrupt_prompt"):
            try:
                _p, _h, span = assert_clause_aligned_pair(
                    tokenizer, record[stream], twin[stream], record["pressure"],
                    max_length)
            except (AssertionError, ValueError) as exc:
                raise ValueError(
                    f"instance {one}: its Neutral-Clause Twin is not clause-aligned "
                    f"on the {stream.split('_')[0]} stream: {exc}") from exc
            spans.append(tuple(span))
        if spans[0] != spans[1]:
            raise ValueError(f"instance {one}: the clause spans of the two streams "
                             f"differ ({spans[0]} vs {spans[1]})")
        input_ids, attention_mask = _encode(tokenizer, twin["clean_prompt"], max_length)
        corrupt_ids, corrupt_mask = _encode(tokenizer, twin["corrupt_prompt"], max_length)
        out[one] = {"input_ids": input_ids, "attention_mask": attention_mask,
                    "corrupt_input_ids": corrupt_ids,
                    "corrupt_attention_mask": corrupt_mask,
                    "clause_span": list(spans[0])}
    return out, directory


def _batches(dataset_dir: str, tokenizer, *, ids: Optional[Sequence[str]],
             task: Optional[str], split: str, batch_size: int,
             max_length: Optional[int], pools_dir: Optional[str],
             honest_streams: Optional[str], with_honest: bool,
             with_neutral_twin: Optional[bool] = None) -> Batches:
    """`with_neutral_twin`: None pairs v2 tasks and leaves v1 untouched (its
    report gains no key), True asks for the pairing, False never pairs."""
    from dataset import deception_common as dc

    config = dc.load_dataset_config(dataset_dir)
    task = task or config.get("task")
    reason = uncovered_reason(task)
    if reason:
        raise LoaderUnavailable(reason)
    if max_length is None:
        max_length = int(config.get("max_seq_length", dc.MAX_SEQ_LENGTH))

    records = dc.load_or_generate_deception_data(dataset_dir, split=split)
    split_ids = sampling.record_ids(records)
    by_id = dict(zip(split_ids, records))

    wanted = list(ids) if ids is not None else split_ids
    missing = [one for one in wanted if one not in by_id]

    kept, dropped = {}, []
    for one in wanted:
        record = by_id.get(one)
        if record is None:
            continue
        target = dc.encode_answer_token(tokenizer, record["target"])
        distractor = dc.encode_answer_token(tokenizer, record["distractor"])
        if len(target) != 1 or len(distractor) != 1:
            dropped.append(one)
            continue
        kept[one] = {**record, "target_token": target[0],
                     "distractor_token": distractor[0],
                     "prefix_length": len(tokenizer.encode(
                         record["clean_prompt"], add_special_tokens=False))}

    honest, source = ({}, "not requested")
    if with_honest:
        honest, source = _honest_by_id(
            dataset_dir, tokenizer, split=split, task=task, pools_dir=pools_dir,
            max_length=max_length, honest_streams=honest_streams)

    if with_neutral_twin is None:
        with_neutral_twin = task in V2_TASKS
    twins, twin_source, pairing = {}, None, False
    if with_neutral_twin:
        twin_source = neutral_twin_reason(task, config)
        pairing = twin_source is None
        if pairing:
            twins, twin_source = _neutral_twins_by_id(
                dataset_dir, tokenizer, kept, config=config, split=split,
                max_length=max_length)

    items, without_honest, without_twin = [], [], []
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
        twin = twins.get(one)
        if pairing and twin is None:
            without_twin.append(one)
        if twin is not None and not torch.equal(twin["attention_mask"], attention_mask):
            raise ValueError(f"instance {one}: the Neutral-Clause Twin's attention "
                             f"mask is not the pressure prompt's")
        items.append({
            "instance_id": one, "record": item,
            "input_ids": input_ids, "attention_mask": attention_mask,
            "corrupt_input_ids": corrupt_ids,
            "corrupt_attention_mask": corrupt_mask,
            "target_token": int(item["target_token"]),
            "distractor_token": int(item["distractor_token"]),
            "readout": readout, "honest": pair, "neutral_twin": twin})

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
    if with_neutral_twin:
        # Only when asked for (every v2 loader), so a v1 report, which
        # `dla.json` copies whole, keeps exactly the keys it always had.
        report.update({
            "neutral_twin_source": twin_source,
            "n_with_neutral_twin": sum(1 for item in items if item["neutral_twin"]),
            "without_neutral_twin": without_twin,
        })
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
                    pools_dir=None, honest_streams=None, with_honest=False,
                    with_neutral_twin=False)


def neutral_twin_batches(dataset_dir: str, tokenizer, *, task: Optional[str] = None,
                         split: str = "test",
                         batch_size: int = DEFAULT_BATCH_SIZE,
                         max_length: Optional[int] = None) -> Batches:
    """The whole split, each row with its Neutral-Clause Twin (v2 D or I).

    The descriptive half of the `neutral_twin` paired kind: DLA's paired
    neutral-twin condition reads every row of the split, not the causal sample.
    On an H or F test set the report says why there is no pairing.
    """
    return _batches(dataset_dir, tokenizer, ids=None, task=task, split=split,
                    batch_size=batch_size, max_length=max_length,
                    pools_dir=None, honest_streams=None, with_honest=False,
                    with_neutral_twin=True)


def batches_for_task(task_spec, tokenizer, *, ids: Optional[Sequence[str]] = None,
                     split: str = "test",
                     batch_size: int = DEFAULT_BATCH_SIZE,
                     max_length: Optional[int] = None,
                     pools_dir: Optional[str] = None,
                     honest_streams: Optional[str] = None,
                     neutral_twin: bool = False) -> Batches:
    """The CLI's entry point: ask the task where its dataset is, then load it.

    `ids=None` gives the descriptive loader over the whole split; an id list
    gives the causal one with both counterfactual pairs. `neutral_twin=True`
    with `ids=None` gives the whole split paired with its Neutral-Clause Twin.
    """
    from component_analysis import instances

    directory = instances.dataset_dir(task_spec)
    if ids is None and neutral_twin:
        return neutral_twin_batches(directory, tokenizer, task=task_spec.name,
                                    split=split, batch_size=batch_size,
                                    max_length=max_length)
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
                     f"because the Target or the Distractor is not a single "
                     f"token: {', '.join(report['dropped_by_tokenization'][:3])}")
    if report["honest_source"] == "absent":
        lines.append("no Matched Honest survivors file for this task, so no "
                     "Honest-Instruction Counterfactual")
    elif report["honest_source"] != "not requested":
        lines.append(f"honest-instruction pair on {report['n_with_honest']} of "
                     f"{report['n_instances']} ({report['honest_streams']} "
                     f"criterion); {len(report['without_honest'])} without")
    if "neutral_twin_source" in report:
        if report["n_with_neutral_twin"] or report["without_neutral_twin"]:
            lines.append(f"neutral-clause twin on {report['n_with_neutral_twin']} "
                         f"of {report['n_instances']}, from "
                         f"{report['neutral_twin_source']}; "
                         f"{len(report['without_neutral_twin'])} without")
        else:
            lines.append(f"neutral-clause twin: {report['neutral_twin_source']}")
    return lines

