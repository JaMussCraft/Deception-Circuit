"""
component_analysis/instances.py — the test instances an analysis runs over, and
the two files that say which spans and which instances were used.

`segmentation.json` and `sample.json` sit in the cell directory beside the head
table, and `--dry-run` writes both. That is the point of writing them: a plot
rendered later is read against the spans and the instance ids recorded here, so
a segmentation that has drifted, or a sample drawn with a different seed, is
visible as a file difference rather than as a quietly wrong figure.

Nothing here loads a model. The tokenizer is needed — Segments are spans of
tokens — but a Llama tokenizer is a few megabytes of JSON out of the local
HuggingFace cache, not weights, so `--dry-run` stays a login-node mode.
"""

from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Optional, Sequence

from component_analysis import sampling, segmentation as seg

SEGMENTATION_FILENAME = "segmentation.json"
SAMPLE_FILENAME = "sample.json"

#: Bumped when the shape of either file changes, as `head_table.py` does for
#: the head table, so a reader can tell an old cell from a new one.
SCHEMA_VERSION = 1


def _header() -> dict:
    return {"schema_version": SCHEMA_VERSION,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S")}


# ==============================================================================
# RECORDS
# ==============================================================================

def dataset_dir(task_spec) -> str:
    """Where this task's built dataset lives, asked of the task itself."""
    task = task_spec.build()
    if hasattr(task, "dataset_dir"):
        return task.dataset_dir(task_spec.args)
    if task_spec.name == "std":
        return os.path.join(task_spec.args.data_dir,
                            f"std_{task_spec.args.std_variant}")
    raise ValueError(
        f"task {task_spec.name!r} does not say where its dataset is, so its "
        f"instances cannot be loaded")


def load_records(task_spec, split: str = "test") -> List[dict]:
    """The split's records, exactly as the task's own loader returns them."""
    path = dataset_dir(task_spec)
    limit = getattr(task_spec.args, "test_samples", None) if split == "test" else None
    if task_spec.name == "std":
        from dataset.std_llama import load_or_generate_std_data
        return load_or_generate_std_data(path, split, limit)
    from dataset.deception_common import load_or_generate_deception_data
    return load_or_generate_deception_data(path, split, limit)


def load_analysis_tokenizer(model_name: str, *, hf_token: Optional[str] = None):
    """The model's tokenizer, through the repo's own adapter.

    A separate function so that the CLI-seam test can hand the dry run the
    whitespace-level fake without reaching into `models`, and so that nothing
    on this path can accidentally pull in weights.
    """
    from models import ModelAdapter
    return ModelAdapter(model_name, hf_token=hf_token).load_tokenizer()


# ==============================================================================
# SEGMENTATION, OVER A SPLIT
# ==============================================================================

def resolve_split_segmentation(task: str, records: Sequence[dict], tokenizer, *,
                               overrides: Optional[Dict[str, str]] = None,
                               ids: Optional[Sequence[str]] = None):
    """(segmentations, report) for every record of a split.

    Every instance is validated, so a prompt whose Designating Sentence has
    drifted fails here — on the login node, in `--dry-run` — rather than in the
    middle of a GPU job. An override that matched nothing anywhere is a typo
    and is raised for the same reason; one that matched on some instances and
    not others is a property of the data and is only counted.
    """
    overrides = dict(overrides or {})
    ids = list(ids) if ids is not None else sampling.record_ids(records)

    resolved, overlaps = [], []
    matched = {name: 0 for name in overrides}
    for record, record_id in zip(records, ids):
        one = seg.resolve_segmentation(task, record, tokenizer,
                                       overrides=overrides, record_id=record_id)
        report = seg.validate_segmentation(one, record, tokenizer)
        if report["overlaps"]:
            overlaps.append({"record_id": record_id,
                             "overlaps": report["overlaps"]})
        for name in overrides:
            matched[name] += int(one.segments[name].status == "present")
        resolved.append(one)

    empty = sorted(name for name, count in matched.items() if count == 0)
    if empty:
        raise seg.SegmentationError(
            f"--segment {', '.join(empty)} matched nothing on any of the "
            f"{len(records)} instances; a Segment that is never found would "
            f"leave every plot of it empty")

    return resolved, {"override_match_counts": matched,
                      "instances_with_overlapping_segments": overlaps}


def write_segmentation(cell_dir: str, segmentations: Sequence, *, task: str,
                       overrides: Dict[str, str], report: dict,
                       split: str = "test", meta: Optional[dict] = None) -> str:
    """Write `segmentation.json` for one cell."""
    os.makedirs(cell_dir, exist_ok=True)
    path = os.path.join(cell_dir, SEGMENTATION_FILENAME)
    names = list(segmentations[0].segments) if segmentations else []
    sources = ({name: segmentations[0].segments[name].source for name in names}
               if segmentations else {})
    payload = {
        **_header(),
        "task": task,
        "scheme": segmentations[0].scheme if segmentations else None,
        "split": split,
        "n_instances": len(segmentations),
        "segment_names": names,
        "segment_sources": sources,
        "overrides": dict(overrides),
        "spans": ("half-open [start, end) ranges of token indices over the "
                  "CLEAN prompt, tokenized with add_special_tokens=False. The "
                  "corrupt stream shares them: the item-swap Corruption is a "
                  "single-token edit, so the two streams align position for "
                  "position."),
        "empty_spans": ("A Segment with an empty span list is absent from "
                        "that instance — the saved FAR run predates the "
                        "Designation Suffix, and the pilot condition has no "
                        "Pressure Clause."),
        "partition": ("The default Segments are pairwise disjoint and cover "
                      "every token, 'unsegmented' holding what the named ones "
                      "do not claim. 'intro', 'question' and "
                      "'designating_sentence' are the frames around the Item "
                      "Mentions and Designation Positions carved out of them, "
                      "not spans that contain them. An override may overlap "
                      "the defaults; any instance where it does is listed "
                      "under report.instances_with_overlapping_segments."),
        "report": report,
        "meta": meta or {},
        "instances": [one.as_json() for one in segmentations],
    }
    with open(path, "w") as handle:
        json.dump(payload, handle, indent=2)
    return path


# ==============================================================================
# SAMPLE
# ==============================================================================

def write_sample(cell_dir: str, sample, *, task: str, split: str = "test",
                 meta: Optional[dict] = None) -> str:
    """Write `sample.json` for one cell."""
    os.makedirs(cell_dir, exist_ok=True)
    path = os.path.join(cell_dir, SAMPLE_FILENAME)
    payload = {**_header(), "task": task, "split": split, **sample.as_json(),
               "meta": meta or {}}
    with open(path, "w") as handle:
        json.dump(payload, handle, indent=2)
    return path
