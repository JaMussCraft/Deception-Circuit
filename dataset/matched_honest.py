"""
Matched Honest Instructions and the Honest-Instruction Counterfactual.

A **Matched Honest Instruction** is an honesty instruction written to occupy
exactly the same number of tokens as the **Pressure Clause** it replaces, so
that a prompt and its honest counterpart align token for token everywhere and
differ only inside the clause span. The pair (prompt, prompt with its clause
replaced) is the **Honest-Instruction Counterfactual**: the paired, causal
version of the Honest Twin contrast, which is unpaired.

This is NOT the fixed-length `honest_instruction` prompt variant that
`evaluation/pressure.py` and `evaluation/variants.py` use. That one is a single
sentence (`deception_common.HONEST_INSTRUCTION`) applied to every clause, so it
moves the Readout position and nothing downstream may assume alignment. It is
deliberately left untouched; CONTEXT.md calls it the "honest variant" and
reserves that term for it.

What lives here
---------------
    replace_clause / split_around_clause   string surgery on a built prompt
    clause_span                            the clause's token span in a prompt
    assert_clause_aligned_pair             the new alignment assertion
    select_matched_instruction / build_pool   the drafting script's engine
    load_candidates / load_matched_honest_pool   the pool files
    filter_matched_honest                  the two-sided margin filter
    pair_with_matched_instructions         one honest twin per record, asserted
    MatchedHonestDataset / load_matched_honest   the loader the analyses use

Why string surgery rather than `deception_common.rebuild_prompt`. The saved
SDR dataset was built from an older designating-sentence template ("The miles
result is the one that is damaging, and the other is harmless."), so rebuilding
a saved record from today's `SPECS` does not reproduce its `clean_prompt` and
would silently change every prompt in the pair. The clause is stored verbatim
on each record and occurs exactly once, immediately before the system turn's
`<|eot_id|>`, which makes substitution exact and checkable. `split_around_clause`
raises if that is ever untrue.

Why the span comes from common prefixes and suffixes rather than from the
`<|eot_id|>` token. Locating the clause by that token id works under the real
tokenizer and breaks under `tests.fakes.FakeWordTokenizer`, which fuses the
clause's last word with the header that follows it into one whitespace chunk.
Comparing the full prompt's ids against the ids of its prefix and of its suffix
is correct under both, and a merge across either boundary shows up as a span
whose width disagrees with the clause's own token count.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

import torch
from torch.utils.data import DataLoader, Dataset

from dataset import deception_common as dc

#: The chat shell's end-of-turn marker. The Pressure Clause is the last thing
#: in the system turn, so this is what always follows it.
EOT = "<|eot_id|>"

POOLS_DIR = dc.POOLS_DIR
CANDIDATES_FILE = "matched_honest_candidates.json"
POOL_FILE = "matched_honest_{task}.json"

#: Written next to the dataset by the build step.
SURVIVORS_FILE = "matched_honest_survivors.json"
REPORT_FILE = "matched_honest_report.json"


# ==============================================================================
# STRING SURGERY
# ==============================================================================

def split_around_clause(prompt: str, clause: str) -> Tuple[str, str, str]:
    """(prefix, ' ' + clause, suffix) for the one occurrence of the clause.

    The suffix begins at the system turn's `<|eot_id|>`. The leading space goes
    with the clause because that is where the tokenizer puts it: ' Your' is one
    token, so the space is part of the clause's first token, not of the prefix's
    last one.
    """
    marker = " " + clause + EOT
    count = prompt.count(marker)
    if count != 1:
        raise ValueError(
            f"the Pressure Clause must occur exactly once, immediately before "
            f"the system turn's {EOT}; found {count} occurrence(s) of "
            f"{marker!r}")
    start = prompt.index(marker)
    end = start + 1 + len(clause)
    return prompt[:start], prompt[start:end], prompt[end:]


def replace_clause(prompt: str, clause: str, instruction: str) -> str:
    """The prompt with its Pressure Clause replaced by `instruction`."""
    prefix, _, suffix = split_around_clause(prompt, clause)
    return prefix + " " + instruction + suffix


# ==============================================================================
# CLAUSE SPAN
# ==============================================================================

def _common_prefix_len(a: Sequence[int], b: Sequence[int]) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _common_suffix_len(a: Sequence[int], b: Sequence[int]) -> int:
    n = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        n += 1
    return n


def clause_span(tokenizer, prompt: str, clause: str) -> Tuple[int, int]:
    """[start, end) — the token positions the Pressure Clause occupies.

    `start` is where the prompt's ids stop agreeing with the ids of everything
    before the clause, and `end` is where they start agreeing with the ids of
    everything after it. A BPE merge that straddles either boundary therefore
    lands inside the span rather than being lost outside it.
    """
    ids = tokenizer.encode(prompt, add_special_tokens=False)
    prefix, _, suffix = split_around_clause(prompt, clause)
    start = _common_prefix_len(ids, tokenizer.encode(prefix,
                                                    add_special_tokens=False))
    end = len(ids) - _common_suffix_len(
        ids, tokenizer.encode(suffix, add_special_tokens=False))
    if not 0 <= start < end <= len(ids):
        raise ValueError(
            f"could not locate the Pressure Clause in the prompt: span "
            f"({start}, {end}) of {len(ids)} tokens")
    return start, end


# ==============================================================================
# THE ALIGNMENT ASSERTION
# ==============================================================================

def assert_clause_aligned_pair(tokenizer, pressure_prompt: str,
                               honest_prompt: str, clause: str,
                               max_seq_length: int
                               ) -> Tuple[List[int], List[int], Tuple[int, int]]:
    """Assert the Honest-Instruction Counterfactual pair is token-aligned.

    Three requirements, all read off the FULL tokenized prompt rather than the
    clause alone, because a BPE merge at the clause boundary can differ:

      1. equal token count,
      2. every differing position inside the clause span,
      3. the Readout position identical — same index, same token.

    The item-swap pair keeps its own single-position assertion
    (`deception_common.assert_aligned_pair`); this one allows many differing
    positions, as long as all of them are inside the clause.

    Returns (pressure ids, honest ids, clause span).
    """
    ids_p = tokenizer.encode(pressure_prompt, add_special_tokens=False)
    ids_h = tokenizer.encode(honest_prompt, add_special_tokens=False)
    assert len(ids_p) == len(ids_h), (
        f"pressure/honest token counts differ: {len(ids_p)} vs {len(ids_h)}. "
        f"The Matched Honest Instruction must occupy exactly the clause's "
        f"token count in the full prompt.")
    assert len(ids_p) <= max_seq_length, (
        f"prompt is {len(ids_p)} tokens > max_seq_length={max_seq_length}")

    start, end = clause_span(tokenizer, pressure_prompt, clause)
    n_clause = len(tokenizer.encode(" " + clause, add_special_tokens=False))
    assert end - start == n_clause, (
        f"the clause span is {end - start} tokens but the clause alone is "
        f"{n_clause}; a BPE merge straddles the clause boundary")

    diffs = [i for i, (a, b) in enumerate(zip(ids_p, ids_h)) if a != b]
    outside = [i for i in diffs if not start <= i < end]
    assert not outside, (
        f"{len(outside)} token(s) differ outside the Pressure Clause span "
        f"[{start}, {end}): positions {outside[:8]}")

    readout = len(ids_p) - 1
    assert end <= readout, (
        f"the clause span [{start}, {end}) reaches the Readout position "
        f"{readout}")
    assert ids_p[readout] == ids_h[readout], (
        "the Readout token differs between the pressure and honest prompts")
    return ids_p, ids_h, (start, end)


# ==============================================================================
# CANDIDATE SELECTION AND THE POOL FILES
# ==============================================================================

def select_matched_instruction(tokenizer, clause: str,
                               candidates: Sequence[str],
                               sample_prompts: Sequence[str]) -> Optional[str]:
    """The first candidate that leaves every sample prompt's token count alone.

    Length is measured on the FULL prompt, not on the instruction alone: BPE
    merges at the clause boundary can differ between a clause and an
    instruction of the same standalone length, and it is the full prompt that
    has to align. Several sample prompts are checked because the scaffold
    around the clause varies by template variant and item polarity.

    Returns None when no candidate matches — the caller reports the clause as
    unmatched rather than falling back to a near-miss.
    """
    if not sample_prompts:
        raise ValueError("select_matched_instruction needs at least one sample "
                         "prompt to measure against")
    targets = [len(tokenizer.encode(p, add_special_tokens=False))
               for p in sample_prompts]
    for candidate in candidates:
        if all(len(tokenizer.encode(replace_clause(p, clause, candidate),
                                    add_special_tokens=False)) == n
               for p, n in zip(sample_prompts, targets)):
            return candidate
    return None


def build_pool(tokenizer, pressures: Sequence[Dict],
               candidates: Sequence[str], sample_prompts_for
               ) -> Tuple[Dict[str, Dict], List[str]]:
    """({pressure id: entry}, [unmatched pressure id]).

    `sample_prompts_for(pressure)` returns the prompts that pressure's length is
    measured on. The caller supplies real test-set prompts where the clause has
    instances and template-built ones where it has none.
    """
    pool, unmatched = {}, []
    for pressure in pressures:
        clause = pressure["text"]
        chosen = select_matched_instruction(tokenizer, clause, candidates,
                                            sample_prompts_for(pressure))
        if chosen is None:
            unmatched.append(pressure["id"])
            continue
        pool[pressure["id"]] = {
            "slot": pressure["slot"],
            "shared": bool(pressure["shared"]),
            "pressure": clause,
            "instruction": chosen,
            "clause_tokens": len(tokenizer.encode(" " + clause,
                                                  add_special_tokens=False)),
        }
    return pool, unmatched


def _pool_path(task: str, pools_dir: Optional[str] = None) -> str:
    return os.path.join(pools_dir or POOLS_DIR, POOL_FILE.format(task=task))


def write_matched_honest_pool(task: str, pool: Dict[str, Dict], *,
                              pools_dir: Optional[str] = None,
                              meta: Optional[Dict] = None) -> str:
    path = _pool_path(task, pools_dir)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload = {"task": task, **(meta or {}), "instructions": pool}
    with open(path, "w") as f:
        json.dump(payload, f, indent=1)
        f.write("\n")
    return path


def load_matched_honest_pool(task: str, pools_dir: Optional[str] = None
                             ) -> Dict[str, Dict]:
    """{pressure id: entry} for one task. Raises if the pool was never built."""
    path = _pool_path(task, pools_dir)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found — draft the Matched Honest Instructions first "
            f"with dataset/build_matched_honest.py --task {task} --write-pool")
    with open(path) as f:
        return json.load(f)["instructions"]


def load_candidates(pools_dir: Optional[str] = None) -> List[str]:
    """The drafted candidate ladder, in the order the selection walks it."""
    path = os.path.join(pools_dir or POOLS_DIR, CANDIDATES_FILE)
    with open(path) as f:
        return json.load(f)["candidates"]


# ==============================================================================
# THE TWO-SIDED MARGIN FILTER
# ==============================================================================

HONEST_STREAM_CHOICES = ("both", "clean")


def pair_with_matched_instructions(
        records: Sequence[Dict], pool: Dict[str, Dict], tokenizer,
        max_seq_length: int = dc.MAX_SEQ_LENGTH
) -> Tuple[List[Dict], List[Dict], List[str]]:
    """(records that have an instruction, their honest twins, clause ids without one).

    Every returned pair has been through `assert_clause_aligned_pair`, so the
    "asserts it on every instance at build time" requirement is discharged here
    and not left to the caller. The honest twin carries the same target and
    distractor labels as its source record: under the instruction the model is
    expected to pick the DISTRACTOR, which is what makes the honest side of the
    filter the flipped reading of the same margin.
    """
    kept, honest, missing = [], [], []
    for record in records:
        entry = pool.get(record["pressure_id"])
        if entry is None:
            missing.append(record["pressure_id"])
            continue
        clause = record["pressure"]
        if entry["pressure"] != clause:
            raise ValueError(
                f"pool entry {record['pressure_id']} holds a different clause "
                f"than record {record['instance_id']}")
        clean = replace_clause(record["clean_prompt"], clause,
                               entry["instruction"])
        corrupt = replace_clause(record["corrupt_prompt"], clause,
                                 entry["instruction"])
        assert_clause_aligned_pair(tokenizer, record["clean_prompt"], clean,
                                   clause, max_seq_length)
        assert_clause_aligned_pair(tokenizer, record["corrupt_prompt"], corrupt,
                                   clause, max_seq_length)
        # The honest pair is itself an item-swap pair, so it keeps the existing
        # single-position assertion. Not cosmetic: `evaluate_behavior` takes
        # `prefix_length` from the clean prompt and reads position
        # `prefix_length - 1` in BOTH streams, so a merge that lengthened the
        # honest corrupt prompt would move the Readout under the honest
        # criterion without anything saying so.
        dc.assert_aligned_pair(tokenizer, clean, corrupt,
                               record["clean_item_d"], record["corrupt_item_d"],
                               max_seq_length)
        kept.append(record)
        honest.append({**record, "clean_prompt": clean,
                       "corrupt_prompt": corrupt,
                       "matched_honest_instruction": entry["instruction"]})
    return kept, honest, sorted(set(missing))


def filter_matched_honest(records: Sequence[Dict], pool: Dict[str, Dict],
                          model, tokenizer, device, *,
                          margin_thresh: float = 1.0,
                          honest_streams: str = "both",
                          max_length: int = dc.MAX_SEQ_LENGTH,
                          batch_size: int = 32,
                          min_survivors: int = 1) -> Tuple[List[Dict], Dict]:
    """Keep instances that deceive under pressure and answer honestly under the
    Matched Honest Instruction.

    Both sides are the existing margin filter. The pressure side is
    `deception_common.filter_by_model_behavior` unchanged; the honest side is
    the same filter read with the answer flipped, which is exactly what
    `deception_common.harvest_honest_twins` does, so that is what runs.

    FORWARD-CALL ORDER, which `tests.fakes.ScriptedModel` consumes in sequence:
    pressure clean, pressure corrupt, honest clean, honest corrupt. With a batch
    size covering the whole record list that is four calls.

    `honest_streams` picks the honest criterion: "both" (the default, and the
    strict reading of the existing filter) requires the honest answer at margin
    in the clean AND corrupt streams; "clean" requires it in the clean stream
    only, which is the stream the analyses actually read. Both rates are always
    reported, so the choice can be revisited without another GPU run.

    Returns (surviving records, report).
    """
    if honest_streams not in HONEST_STREAM_CHOICES:
        raise ValueError(f"honest_streams must be one of "
                         f"{list(HONEST_STREAM_CHOICES)}, got {honest_streams!r}")

    kept, honest, missing = pair_with_matched_instructions(
        records, pool, tokenizer, max_length)
    report = {
        "margin_thresh": margin_thresh,
        "honest_streams": honest_streams,
        "n_records": len(records),
        "n_with_instruction": len(kept),
        "clauses_without_an_instruction": missing,
        "by_clause": {},
        "overall": {},
        "usable_clauses": [],
    }
    if not kept:
        report["overall"] = {"n": 0, "n_pressure_pass": 0,
                             "n_honest_pass_clean": 0, "n_honest_pass_both": 0,
                             "n_survivors": 0, "survivor_rate": 0.0}
        report["min_survivors"] = min_survivors
        report["unexpected_argmax_tokens"] = {}
        report["survivor_ids"] = {"clean": [], "both": []}
        return [], report

    # --- pressure side: the existing filter, unchanged --------------------
    _, pressure_behaviors, unexpected = dc.filter_by_model_behavior(
        kept, model, tokenizer, device, margin_thresh=margin_thresh,
        max_length=max_length, batch_size=batch_size)

    # --- honest side: the same filter read with the answer flipped --------
    honest_behaviors = dc.evaluate_behavior(honest, model, tokenizer, device,
                                            max_length=max_length,
                                            batch_size=batch_size)
    # Sets b["honest"] for the both-streams reading.
    dc.harvest_honest_twins(honest, honest_behaviors,
                            margin_thresh=margin_thresh)
    for b in honest_behaviors:
        b["honest_clean"] = bool(
            b["clean_argmax_id"] == b["distractor_token"] and
            -b["clean_margin"] >= margin_thresh)

    honest_key = {"both": "honest", "clean": "honest_clean"}[honest_streams]
    survivors, by_clause = [], {}
    # Both criteria's survivor ids are recorded, not just the chosen one: the
    # forward passes have already been paid for, and the choice between them is
    # the researcher's. Writing both means revisiting it costs no GPU time.
    survivor_ids = {"clean": [], "both": []}
    for record, pb, hb in zip(kept, pressure_behaviors, honest_behaviors):
        row = by_clause.setdefault(record["pressure_id"], {
            "instruction": pool[record["pressure_id"]]["instruction"],
            "clause_tokens": pool[record["pressure_id"]]["clause_tokens"],
            "n": 0, "n_pressure_pass": 0, "n_honest_pass_clean": 0,
            "n_honest_pass_both": 0, "n_survivors": 0})
        row["n"] += 1
        row["n_pressure_pass"] += int(pb["passed"])
        row["n_honest_pass_clean"] += int(hb["honest_clean"])
        row["n_honest_pass_both"] += int(hb["honest"])
        for criterion, key in (("clean", "honest_clean"), ("both", "honest")):
            if pb["passed"] and hb[key]:
                survivor_ids[criterion].append(record["instance_id"])
        if pb["passed"] and hb[honest_key]:
            row["n_survivors"] += 1
            survivors.append(record)

    for row in by_clause.values():
        row["pressure_pass_rate"] = row["n_pressure_pass"] / row["n"]
        row["honest_pass_rate_clean"] = row["n_honest_pass_clean"] / row["n"]
        row["honest_pass_rate_both"] = row["n_honest_pass_both"] / row["n"]
        row["survivor_rate"] = row["n_survivors"] / row["n"]

    report["by_clause"] = dict(sorted(by_clause.items()))
    report["usable_clauses"] = sorted(
        pid for pid, row in by_clause.items()
        if row["n_survivors"] >= min_survivors)
    report["min_survivors"] = min_survivors
    report["overall"] = {
        "n": len(kept),
        "n_pressure_pass": sum(int(b["passed"]) for b in pressure_behaviors),
        "n_honest_pass_clean": sum(int(b["honest_clean"])
                                   for b in honest_behaviors),
        "n_honest_pass_both": sum(int(b["honest"]) for b in honest_behaviors),
        "n_survivors": len(survivors),
        "survivor_rate": len(survivors) / len(kept),
    }
    report["unexpected_argmax_tokens"] = dict(unexpected.most_common())
    report["survivor_ids"] = survivor_ids
    return survivors, report


# ==============================================================================
# SURVIVORS AND THE REPORT, WRITTEN BESIDE THE DATASET
# ==============================================================================

def write_survivors(dataset_dir: str, task: str, survivors: Sequence[Dict],
                    report: Dict, *, split: str = "test") -> Dict[str, str]:
    """Write the surviving instance ids and the per-clause report.

    Beside the dataset, not inside a new DatasetDict: the paired dataset is the
    base split plus the pool plus this id list, and materialising a second copy
    of the prompts would let the two drift apart.
    """
    os.makedirs(dataset_dir, exist_ok=True)
    ids_path = os.path.join(dataset_dir, SURVIVORS_FILE)
    payload = {"task": task, "split": split,
               "honest_streams": report.get("honest_streams"),
               "n": len(survivors),
               "instance_ids": [r["instance_id"] for r in survivors]}
    if "survivor_ids" in report:
        # Both honest criteria, so switching between them needs no GPU rerun.
        payload["instance_ids_by_criterion"] = report["survivor_ids"]
    with open(ids_path, "w") as f:
        json.dump(payload, f, indent=1)
        f.write("\n")
    report_path = os.path.join(dataset_dir, REPORT_FILE)
    with open(report_path, "w") as f:
        json.dump({"task": task, "split": split, **report}, f, indent=1)
        f.write("\n")
    return {"survivors": ids_path, "report": report_path}


def load_survivors(dataset_dir: str, honest_streams: Optional[str] = None
                   ) -> List[str]:
    """The surviving instance ids.

    `honest_streams` re-reads the file under the other honest criterion without
    a GPU rerun; the default is whichever criterion the build was run with.
    """
    path = os.path.join(dataset_dir, SURVIVORS_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found — run dataset/build_matched_honest.py to filter "
            f"the split before loading the Honest-Instruction Counterfactual.")
    with open(path) as f:
        payload = json.load(f)
    if honest_streams is None:
        return list(payload["instance_ids"])
    by_criterion = payload.get("instance_ids_by_criterion")
    if by_criterion is None or honest_streams not in by_criterion:
        raise KeyError(
            f"{path} does not record survivors for honest_streams="
            f"{honest_streams!r}; it was written by an older build. Rerun "
            f"dataset/build_matched_honest.py.")
    return list(by_criterion[honest_streams])


# ==============================================================================
# THE LOADER
# ==============================================================================

class MatchedHonestDataset(Dataset):
    """Honest-Instruction Counterfactual pairs.

    `item(i)` is the text view the ticket names — pressure prompt, honest
    prompt, Target, Distractor, clause span — and `self[i]` is the tensor view,
    which is everything `DeceptionDatasetLlama` yields (so the item-swap
    counterfactual and the Readout position come along unchanged) plus
    `honest_input_ids`, `honest_attention_mask` and `clause_span`.

    Every pair is asserted aligned at construction, so a pool that has drifted
    from the dataset fails at load time rather than in the middle of a patch.
    """

    def __init__(self, records: Sequence[Dict], pool: Dict[str, Dict], tokenizer,
                 max_length: int = dc.MAX_SEQ_LENGTH):
        self.base = dc.DeceptionDatasetLlama(records, tokenizer,
                                             max_length=max_length)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.items: List[Dict] = []
        for item in self.base.processed_data:
            entry = pool.get(item["pressure_id"])
            if entry is None:
                raise KeyError(
                    f"no Matched Honest Instruction for pressure "
                    f"{item['pressure_id']!r}; rebuild the pool")
            clause = item["pressure"]
            honest = replace_clause(item["clean_prompt"], clause,
                                    entry["instruction"])
            _, _, span = assert_clause_aligned_pair(
                tokenizer, item["clean_prompt"], honest, clause, max_length)
            self.items.append({**item, "honest_prompt": honest,
                               "matched_honest_instruction": entry["instruction"],
                               "clause_span": span})

    def __len__(self) -> int:
        return len(self.items)

    def item(self, idx: int) -> Dict:
        """The text view: prompts, answer words, clause span, record metadata."""
        return self.items[idx]

    def __getitem__(self, idx: int) -> Dict:
        item = self.items[idx]
        enc = self.tokenizer(item["honest_prompt"], padding="max_length",
                             max_length=self.max_length, truncation=True,
                             add_special_tokens=False, return_tensors="pt")
        return {
            **self.base[idx],
            "honest_input_ids": enc["input_ids"].squeeze(0),
            "honest_attention_mask": enc["attention_mask"].squeeze(0),
            "clause_span": torch.tensor(item["clause_span"], dtype=torch.long),
        }


def matched_honest_loader(dataset: MatchedHonestDataset, batch_size: int
                          ) -> DataLoader:
    return DataLoader(dataset, batch_size=batch_size, shuffle=False)


def load_matched_honest(dataset_dir: str, tokenizer, *, split: str = "test",
                        task: Optional[str] = None,
                        pools_dir: Optional[str] = None,
                        max_length: Optional[int] = None,
                        survivors_only: bool = True,
                        honest_streams: Optional[str] = None
                        ) -> MatchedHonestDataset:
    """The paired dataset: the base split, filtered to the survivors, plus the pool."""
    config = dc.load_dataset_config(dataset_dir) if os.path.exists(
        os.path.join(dataset_dir, "dataset_config.json")) else {}
    task = task or config.get("task")
    if task is None:
        raise ValueError(
            f"cannot tell which task {dataset_dir} holds; pass task=...")
    if max_length is None:
        max_length = int(config.get("max_seq_length", dc.MAX_SEQ_LENGTH))

    records = dc.load_or_generate_deception_data(dataset_dir, split=split)
    if survivors_only:
        keep = set(load_survivors(dataset_dir, honest_streams))
        records = [r for r in records if r["instance_id"] in keep]
    pool = load_matched_honest_pool(task, pools_dir)
    return MatchedHonestDataset(records, pool, tokenizer, max_length=max_length)
