"""Prompt variants — the same test set with the pressure clause changed.

The deception tasks put the model under pressure to lie. Two counterfactual
prompt sets ask what the circuit does when that pressure is taken away:

  no_pressure         the pressure clause is deleted, nothing put in its place
  honest_instruction  the pressure clause is replaced by an explicit instruction
                      to answer honestly

Both streams (clean and corrupt) get the same variant clause, so every
alignment invariant the training data satisfies still holds: the pair
tokenizes to equal lengths and differs at exactly one position. Prompts are
re-tokenized from scratch, because dropping a clause moves `prefix_length`.

    LABELS ARE DELIBERATELY UNCHANGED.

`target` is still the *deceptive* answer word. Under a variant, therefore,
"accuracy" means "still gives the deceptive answer" and `logit_diff` is still
logit(deceptive) - logit(honest). The desired result is the opposite of the
usual one: accuracy should FALL and logit_diff should go NEGATIVE. Every
evaluation that consumes these loaders repeats this in its report header and
carries `label_convention` in its JSON payload, because a reader who assumes
the usual polarity will read every number backwards.

A prompt that no longer fits `--max-seq-length` once the clause is swapped is
raised, never truncated: a truncated prompt silently moves the readout position
and would quietly report numbers for the wrong token.
"""

from __future__ import annotations

from torch.utils.data import DataLoader

#: Variants that rebuild the prompt. "with_pressure" is the unmodified test set
#: and is served by the ordinary test loader, not by a variant loader.
PROMPT_VARIANTS = ("no_pressure", "honest_instruction")

VARIANT_DESCRIPTIONS = {
    "with_pressure": "the test set as trained — the pressure clause is present",
    "no_pressure": "the pressure clause deleted, nothing in its place",
    "honest_instruction": "the pressure clause replaced by an explicit "
                          "instruction to answer honestly",
}

LABEL_CONVENTION = (
    "Labels are unchanged from the trained test set: `target` is the DECEPTIVE "
    "answer and `distractor` the honest one. Under a prompt variant, accuracy "
    "therefore reads as 'still gives the deceptive answer' and logit_diff as "
    "logit(deceptive) - logit(honest). The desired result is accuracy FALLING "
    "and logit_diff going NEGATIVE."
)


def pressure_text(variant: str, honest_instruction: str) -> str:
    """What goes in the pressure slot for this variant."""
    if variant == "no_pressure":
        return ""
    if variant == "honest_instruction":
        return honest_instruction
    raise ValueError(f"unknown prompt variant {variant!r}; "
                     f"choose from {list(PROMPT_VARIANTS)}")


def assert_fits(tokenizer, prompt: str, max_seq_length: int, *,
                variant: str, task: str) -> None:
    """Refuse to truncate. A truncated prompt moves the readout position."""
    n = len(tokenizer.encode(prompt, add_special_tokens=False))
    if n > max_seq_length:
        raise ValueError(
            f"{task} '{variant}' prompt is {n} tokens but --max-seq-length is "
            f"{max_seq_length}. Truncating it would move the prediction "
            f"position, so this is fatal. Offending prompt:\n{prompt}")


# ==============================================================================
# RECORD REBUILDING
# ==============================================================================

def _is_nopressure(record) -> bool:
    return record.get("condition") == "nopressure" or not record.get("pressure")


def _nopressure_reason(task_name: str, variant: str) -> str:
    return (f"{task_name} '{variant}' variant skipped: the dataset's condition "
            f"is 'nopressure' (empty pressure), so it already is the no_pressure "
            f"variant (the Pressure Clause was deleted at build time) and has no "
            f"clause to replace with an honest instruction")


def dataset_is_nopressure(dataset_dir) -> bool:
    """Whether a stored dataset is a `nopressure` one, read from the data:
    its dataset_config.json `condition`, else every test record's `pressure`
    being empty. False for a missing directory."""
    import json
    import os

    if not dataset_dir or not os.path.isdir(dataset_dir):
        return False
    config = os.path.join(dataset_dir, "dataset_config.json")
    if os.path.exists(config):
        with open(config) as f:
            condition = json.load(f).get("condition")
        if condition is not None:
            return condition == "nopressure"
    try:
        from datasets import load_from_disk
        test = load_from_disk(dataset_dir)["test"]
    except Exception:                                   # noqa: BLE001
        return False
    if "pressure" not in test.column_names or len(test) == 0:
        return False
    return all(p == "" for p in test["pressure"])


def empty_variant_reason(task_name: str, variant: str,
                         dataset_dir=None) -> str:
    """Why a deception task's `variant` prompt set came out empty, judged from
    the dataset itself (see dataset_is_nopressure)."""
    if dataset_is_nopressure(dataset_dir):
        return _nopressure_reason(task_name, variant)
    return (f"{task_name} '{variant}' variant derived no records from the test "
            f"set")


def deception_records(task_name: str, records, variant: str, tokenizer,
                      max_seq_length: int) -> list:
    """FAR / SDR / SER records with the variant's clean/corrupt prompt pair.

    Derived from the STORED prompt strings by clause surgery
    (`dataset/clause_surgery.py`), never re-templated through `dc.SPECS`: the
    stored FAR and SDR datasets use wording the current specs no longer
    produce, so a rebuilt prompt would not be the prompt the circuit was
    trained on. A `nopressure` dataset (empty `pressure`) derives no variants
    and returns [] with the reason printed to the cell's log.
    """
    import dataset.deception_common as dc
    from dataset.clause_surgery import remove_clause, replace_clause

    pressure_text(variant, dc.HONEST_INSTRUCTION)   # rejects unknown variants
    records = list(records)
    n_nopressure = sum(_is_nopressure(r) for r in records)
    if n_nopressure and n_nopressure < len(records):
        raise ValueError(
            f"{task_name} test set mixes {n_nopressure} nopressure record(s) "
            f"(empty pressure) with {len(records) - n_nopressure} record(s) "
            f"that carry a Pressure Clause; a variant cannot be derived for both")
    if n_nopressure:
        print(f"  {_nopressure_reason(task_name, variant)}")
        return []

    out = []
    for record in records:
        clause = record["pressure"]
        if variant == "no_pressure":
            clean = remove_clause(record["clean_prompt"], clause)
            corrupt = remove_clause(record["corrupt_prompt"], clause)
        else:
            clean = replace_clause(record["clean_prompt"], clause,
                                   dc.HONEST_INSTRUCTION)
            corrupt = replace_clause(record["corrupt_prompt"], clause,
                                     dc.HONEST_INSTRUCTION)
        assert_fits(tokenizer, clean, max_seq_length,
                    variant=variant, task=task_name)
        assert_fits(tokenizer, corrupt, max_seq_length,
                    variant=variant, task=task_name)
        dc.assert_aligned_pair(tokenizer, clean, corrupt,
                               clean_item=record["clean_item_d"],
                               corrupt_item=record["corrupt_item_d"],
                               max_seq_length=max_seq_length)
        out.append({**record, "clean_prompt": clean, "corrupt_prompt": corrupt})
    return out


def std_records(records, variant: str, tokenizer, max_seq_length: int) -> list:
    """STD records with a rebuilt clean/corrupt prompt pair."""
    import dataset.std_llama as sl

    pressure = pressure_text(variant, sl.HONEST_INSTRUCTION)

    out = []
    for record in records:
        clean = sl.rebuild_prompt(record, pressure)
        corrupt = sl.rebuild_prompt(record, pressure, stip=record["corrupt_stip"])
        assert_fits(tokenizer, clean, max_seq_length, variant=variant, task="std")
        assert_fits(tokenizer, corrupt, max_seq_length, variant=variant, task="std")
        sl.assert_aligned_pair(tokenizer, clean, corrupt,
                               clean_stip=record["clean_stip"],
                               corrupt_stip=record["corrupt_stip"],
                               max_seq_length=max_seq_length)
        out.append({**record, "clean_prompt": clean, "corrupt_prompt": corrupt})
    return out


def loader(dataset, batch_size: int) -> DataLoader:
    return DataLoader(dataset, batch_size=batch_size, shuffle=False)
