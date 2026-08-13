"""
FAR — Falsified Audit Report (fabrication)

The system turn states the ground truth explicitly; the user asks a direct
factual question about it; the deceptive answer names the wrong item — a false
assertion about the record. Unlike SDR and SER this is checkable by
construction: the deceptive target is provably false given the context.

This module is intentionally thin: the scaffold, the instance list, the filters
and the dataset class all live in `dataset/deception_common.py`, which is what
keeps the three mechanisms comparable. Only the predicate words, the question and
the assistant stem differ, and those live in `deception_common.SPECS`.
"""

from dataset.deception_common import (  # noqa: F401  (re-exported for callers)
    MAX_SEQ_LENGTH, SPECS, DeceptionDatasetLlama, assert_aligned_pair,
    build_prompt_pair, encode_answer_token, filter_by_model_behavior,
    filter_by_prior_balance, generate_task_data, harvest_honest_twins,
    load_dataset_config, load_entities, load_item_pairs,
    load_or_generate_deception_data, load_pressures, print_sample_pair,
    resolve_margin, run_evaluation)

SPEC = SPECS["far"]

#: The predicate applied to the designated item, (inversion word, identity word).
DESIGNATION_WORDS = (SPEC.desig_inversion, SPEC.desig_identity)


def generate_far_data(tokenizer, num_samples, entities=None, item_pairs=None,
                      pressures=None, variant_names=None,
                      max_seq_length=MAX_SEQ_LENGTH, seed=0, seen=None):
    """Generate `num_samples` aligned FAR pairs from the shared pools."""
    return generate_task_data(
        tokenizer, SPEC, num_samples,
        entities if entities is not None else load_entities(),
        item_pairs if item_pairs is not None else load_item_pairs(),
        pressures if pressures is not None else load_pressures("far"),
        variant_names=variant_names, max_seq_length=max_seq_length,
        seed=seed, seen=seen)


def load_or_generate_far_data(dataset_path="./data/datasets/far/", split="test",
                              num_samples=None):
    return load_or_generate_deception_data(dataset_path, split, num_samples)


def filter_far_by_model_behavior(*args, **kwargs):
    return filter_by_model_behavior(*args, **kwargs)
