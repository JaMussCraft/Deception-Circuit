"""
v2 segmentation (ticket 02a): the v2 ids resolve through the mechanism
segmenter with the v2 Scaffold's intro, and a v2 scheme carves a
`response_line` Segment out of `question` (R7). The v1 segmentation of the
saved v1 test splits is byte-identical to what the package produced before the
v2 extension: the golden digests were written by the unmodified code on
2026-10-25 (`tests/fixtures/component_analysis_v2/v1_segmentation_snapshot.json`).

Real Llama tokenizer and real datasets; both skip cleanly when absent.
"""

from __future__ import annotations

import hashlib
import json
import os

import pytest

from component_analysis import sampling, segmentation as seg

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "datasets")
SNAPSHOT = os.path.join(REPO, "tests", "fixtures", "component_analysis_v2",
                        "v1_segmentation_snapshot.json")

#: v1's Segment list as it stood before the v2 extension, written out by hand.
V1_SEGMENTS = (
    "intro", "item_1_intro", "item_2_intro",
    "designating_sentence", "designation_site", "predicate_token",
    "other_token", "inverse_predicate_token", "designation_suffix",
    "pressure_clause", "question",
    "item_1_question_pair", "item_1_question_option",
    "item_2_question_pair", "item_2_question_option",
    "stem", "readout", "unsegmented",
)


@pytest.fixture(scope="module")
def tokenizer():
    try:
        import transformers
        from dataset import deception_common as dc
        return transformers.AutoTokenizer.from_pretrained(dc.DEFAULT_MODEL)
    except Exception as exc:                                  # noqa: BLE001
        pytest.skip(f"the Llama tokenizer is not available here: {exc}")


def rows_of(name, limit=None):
    path = os.path.join(DATA, name)
    if not os.path.isdir(path):
        pytest.skip(f"{name} is not built under data/datasets")
    from datasets import load_from_disk
    split = load_from_disk(path)["test"]
    n = len(split) if limit is None else min(limit, len(split))
    return [dict(split[i]) for i in range(n)]


def decode(tokenizer, record, segment):
    ids = tokenizer.encode(record["clean_prompt"], add_special_tokens=False)
    return tokenizer.decode([ids[i] for i in segment.token_indices()])


# ==============================================================================
# v1 IS UNCHANGED
# ==============================================================================

def test_the_v1_segment_list_is_unchanged():
    assert seg.MECHANISM_SEGMENTS == V1_SEGMENTS
    for task in ("far", "sdr", "ser"):
        assert seg.segment_names(task) == V1_SEGMENTS


@pytest.mark.parametrize("task", ["far", "sdr", "ser"])
def test_v1_segmentation_of_every_saved_test_row_is_byte_identical(tokenizer, task):
    with open(SNAPSHOT) as handle:
        golden = json.load(handle)["tasks"][task]
    rows = rows_of(task)
    entries = []
    for record, rid in zip(rows, sampling.record_ids(rows)):
        one = seg.resolve_segmentation(task, record, tokenizer, record_id=rid)
        entries.append({"scheme": one.scheme, "segmentation": one.as_json(),
                        "report": seg.validate_segmentation(one, record, tokenizer)})
    assert entries[:3] == golden["first_three"]
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    assert (len(entries), digest) == (golden["n"], golden["sha256"])


# ==============================================================================
# v2
# ==============================================================================

V2_SEGMENTS = V1_SEGMENTS[:11] + ("response_line",) + V1_SEGMENTS[11:]


@pytest.mark.parametrize("task", ["far_v2", "sdr_v2", "ser_v2"])
def test_the_v2_ids_are_segmentable_with_a_response_line(task):
    assert seg.is_segmentable(task)
    assert seg.segment_names(task) == V2_SEGMENTS


@pytest.mark.parametrize("task", ["far_v2", "sdr_v2", "ser_v2"])
@pytest.mark.parametrize("condition", ["", "_honest", "_nopressure"])
def test_v2_rows_of_every_condition_resolve_and_validate(tokenizer, task, condition):
    rows = rows_of(task + condition, limit=60)
    for record, rid in zip(rows, sampling.record_ids(rows)):
        one = seg.resolve_segmentation(task, record, tokenizer, record_id=rid)
        seg.validate_segmentation(one, record, tokenizer)
        assert one.scheme == "mechanism_v2"
        assert one.segments["response_line"].status == "present"
        clause = one.segments["pressure_clause"]
        if condition == "_nopressure":
            assert clause.status == "absent"
        else:
            assert decode(tokenizer, record, clause).strip() == record["pressure"]


def test_the_response_line_is_carved_out_of_the_question(tokenizer):
    record = rows_of("sdr_v2", limit=1)[0]
    one = seg.resolve_segmentation("sdr_v2", record, tokenizer)

    response = decode(tokenizer, record, one.segments["response_line"])
    question = decode(tokenizer, record, one.segments["question"])

    # Row 0 of sdr_v2 names inbound / outbound; the two response-line mentions
    # are Item Mentions of their own, so neither item word is in the line.
    assert response == ' Only respond with "The result I will show you is X", where X is or.'
    assert question == "Which result will you show me, or?"
    assert not set(one.segments["response_line"].token_indices()) & \
        set(one.segments["question"].token_indices())
    for slot in ("item_1", "item_2"):
        mention = one.segments[f"{slot}_question_option"].token_indices()
        assert decode(tokenizer, record, one.segments[f"{slot}_question_option"]) \
            .strip() == record[slot]
        # The option mention sits inside the response line's character range.
        line = one.segments["response_line"].token_indices()
        assert min(line) < mention[0] < max(line)


def test_the_neutral_twin_clause_is_the_neutral_sentence(tokenizer):
    twin = rows_of("sdr_v2_honest", limit=1)[0]
    one = seg.resolve_segmentation("sdr_v2", twin, tokenizer)
    assert decode(tokenizer, twin, one.segments["pressure_clause"]).strip() == \
        twin["neutral_text"] == twin["pressure"]


def test_an_inversion_row_on_a_fixture_resolves_like_its_d_row(tokenizer):
    """The I condition (ticket 08) may not exist yet: a D row with its clause
    replaced by a transparent one, condition 'inversion', stands in for it."""
    record = rows_of("sdr_v2", limit=1)[0]
    transparent = "The reviewer asked you to name the result that is not critical."
    fixture = dict(record, condition="inversion", pressure=transparent,
                   clean_prompt=record["clean_prompt"].replace(record["pressure"],
                                                               transparent),
                   corrupt_prompt=record["corrupt_prompt"].replace(
                       record["pressure"], transparent))
    one = seg.resolve_segmentation("sdr_v2", fixture, tokenizer)
    seg.validate_segmentation(one, fixture, tokenizer)
    assert decode(tokenizer, fixture, one.segments["pressure_clause"]).strip() == \
        transparent


def test_a_v2_row_whose_intro_drifted_is_refused_by_name(tokenizer):
    record = rows_of("far_v2", limit=1)[0]
    broken = dict(record, entity="Somebody Else Entirely")
    with pytest.raises(seg.SegmentationError, match="intro sentence"):
        seg.resolve_segmentation("far_v2", broken, tokenizer)
