"""
Library-seam tests for `component_analysis/segmentation.py`.

Prompts are built from the *real* Scaffold pieces (`dataset.deception_common`
and `dataset.std_llama`) and tokenized with `tests.fakes.FakeWordTokenizer`, so
the spans asserted here are the spans the researcher gets on a real prompt,
minus the byte-level BPE. The expected token indices are derived in the test
from the prompt's whitespace chunks — independently of the implementation,
which works from the tokenizer's character offsets and a priority claim.
"""

from __future__ import annotations

import re

import pytest

from component_analysis import segmentation as S
from dataset.deception_common import SPECS, build_prompt_pair, load_pressures
from tests.fakes import FakeWordTokenizer


# ==============================================================================
# HELPERS — expected spans, derived from the prompt rather than from the code
# ==============================================================================

def chunks(prompt):
    """(index, text, char span) for every whitespace-separated chunk.

    `FakeWordTokenizer` emits exactly one token per chunk, so a chunk index is
    a token index.
    """
    return [(i, m.group(0), m.span())
            for i, m in enumerate(re.finditer(r"\S+", prompt))]


def chunk_indices(prompt, pattern):
    """Token indices of every chunk whose text matches `pattern` in full."""
    return [i for i, text, _ in chunks(prompt) if re.fullmatch(pattern, text)]


def indices_of(seg, name):
    return seg.segments[name].token_indices()


# ==============================================================================
# FIXTURES
# ==============================================================================

def sdr_record(*, item_polarity=1, designation_polarity="inversion",
               template_variant="audit"):
    """One SDR instance, rendered by the repo's own prompt builder."""
    spec = SPECS["sdr"]
    pressure = load_pressures("sdr")[3]["text"]
    built = build_prompt_pair(spec, spec.variant(template_variant),
                              "Corveline Diagnostics Group",
                              ("staffing", "pricing"), item_polarity,
                              designation_polarity, pressure)
    return {
        "task": "sdr", "entity": "Corveline Diagnostics Group",
        "item_1": "staffing", "item_2": "pricing",
        "item_polarity": item_polarity,
        "designation_polarity": designation_polarity,
        "template_variant": template_variant,
        "pressure": pressure, "instance_id": "fixture0001",
        **built,
    }


@pytest.fixture
def tokenizer():
    return FakeWordTokenizer()


@pytest.fixture
def sdr(tokenizer):
    record = sdr_record()
    return record, S.resolve_segmentation("sdr", record, tokenizer)


# ==============================================================================
# THE FOUR DESIGNATION POSITIONS
# ==============================================================================

def test_the_designation_positions_land_on_their_own_tokens(sdr):
    """Each Designation Position is one token of the Designating Sentence.

    The predicate words come from the record's own `desig` / `desig_inv`, never
    from the task spec: the saved FAR run says ready/delayed where the current
    spec says weak/strong.
    """
    record, seg = sdr
    prompt = record["clean_prompt"]

    assert indices_of(seg, "designation_site") == \
        chunk_indices(prompt, re.escape(record["clean_item_d"]))[1:2]
    assert indices_of(seg, "predicate_token") == \
        chunk_indices(prompt, re.escape(record["desig"]) + r"[,.]?")
    assert indices_of(seg, "other_token") == chunk_indices(prompt, "other")
    assert indices_of(seg, "inverse_predicate_token") == \
        chunk_indices(prompt, re.escape(record["desig_inv"]) + r"[,.]?")


def test_predicate_words_come_from_the_record_not_from_the_task_spec(tokenizer):
    """A record built with retired predicate words still segments."""
    record = sdr_record()
    record = dict(record)
    for key in ("clean_prompt", "corrupt_prompt"):
        record[key] = record[key].replace("damaging", "delayed") \
                                 .replace("harmless", "ready") \
                                 .replace("DAMAGING", "DELAYED")
    record["desig"], record["desig_inv"] = "delayed", "ready"

    seg = S.resolve_segmentation("sdr", record, tokenizer)
    prompt = record["clean_prompt"]
    assert indices_of(seg, "predicate_token") == \
        chunk_indices(prompt, "delayed[,.]?")
    assert indices_of(seg, "inverse_predicate_token") == \
        chunk_indices(prompt, "ready[,.]?")


# ==============================================================================
# THE REGION SEGMENTS, AND THE PARTITION
# ==============================================================================

def test_the_region_segments_are_the_frames_around_what_is_carved_out(sdr):
    """`intro` and `question` hold the frame; the Item Mentions hold the words.

    A Component attending to an item's mention in the intro is doing something
    different from one attending to the sentence around it, so the mentions are
    never pooled with their frame.
    """
    record, seg = sdr
    prompt = record["clean_prompt"]

    intro = set(indices_of(seg, "intro"))
    mentions = set(indices_of(seg, "item_1_intro") + indices_of(seg, "item_2_intro"))
    assert intro and mentions
    assert not (intro & mentions)

    entity_head = chunk_indices(prompt, "Corveline")
    assert entity_head and set(entity_head) <= intro

    sentence = set(indices_of(seg, "designating_sentence"))
    positions = {i for name in S.DESIGNATION_POSITIONS
                 for i in indices_of(seg, name)}
    assert positions and not (sentence & positions)


def test_each_question_mention_of_an_item_is_its_own_segment(sdr):
    """The question names the pair ("staffing or pricing?") and names each item
    again inside its quoted option.

    A Component attending to the choice on offer is doing something different
    from one attending to the option it is about to copy, so the two mentions
    are separate Segments rather than one pooled Item Mention. That is also
    what makes the glossary's count four mentions per item, not three.
    """
    record, seg = sdr
    prompt = record["clean_prompt"]
    text = dict((i, t) for i, t, _ in chunks(prompt))
    question = set(indices_of(seg, "question"))

    for slot in ("item_1", "item_2"):
        word = record[slot]
        pair = indices_of(seg, f"{slot}_question_pair")
        option = indices_of(seg, f"{slot}_question_option")
        assert len(pair) == 1 and len(option) == 1
        assert pair[0] < option[0]
        assert all(word in text[i] for i in pair + option)
        assert not (question & set(pair + option))

    # Both pair-naming mentions come before either quoted option, which is what
    # makes "first occurrence is the pair naming" the right rule.
    pairs = indices_of(seg, "item_1_question_pair") + \
        indices_of(seg, "item_2_question_pair")
    options = indices_of(seg, "item_1_question_option") + \
        indices_of(seg, "item_2_question_option")
    assert max(pairs) < min(options)


def test_the_readout_is_the_last_token_and_the_stem_is_the_rest(sdr):
    record, seg = sdr
    prompt = record["clean_prompt"]
    n = len(chunks(prompt))

    assert indices_of(seg, "readout") == [n - 1]
    assert seg.readout == n - 1
    stem = indices_of(seg, "stem")
    assert stem and max(stem) == n - 2
    assert seg.readout not in stem


def test_the_default_segments_partition_the_prompt(sdr):
    """Every token belongs to exactly one Segment, `unsegmented` included.

    This is what lets a later analysis sum attention mass per Segment and get
    one.
    """
    record, seg = sdr
    seen = []
    for name in seg.names:
        seen.extend(indices_of(seg, name))
    assert sorted(seen) == list(range(seg.n_tokens))
    assert len(seen) == len(set(seen))


def test_the_suffix_and_the_pressure_clause_are_their_own_segments(sdr):
    """The Designation Suffix repeats the predicate words without naming an
    item, so attention to it is never pooled with the Predicate Token."""
    record, seg = sdr
    prompt = record["clean_prompt"]

    suffix = indices_of(seg, "designation_suffix")
    assert suffix
    assert set(chunk_indices(prompt, "DAMAGING")) <= set(suffix)
    assert not (set(suffix) & set(indices_of(seg, "predicate_token")))

    clause = indices_of(seg, "pressure_clause")
    assert clause
    first = chunks(prompt)[clause[0]][1]
    assert record["pressure"].startswith(first.lstrip())


def test_a_task_whose_suffix_is_empty_reports_the_segment_absent(tokenizer):
    """The saved FAR run was built before the Designation Suffix existed, so a
    later analysis must get an empty span rather than a KeyError."""
    record = sdr_record()
    suffix = " THE DAMAGING ONE IS THE RELEVANT ONE THAT SHOULD BE SHOWN."
    record = dict(record)
    for key in ("clean_prompt", "corrupt_prompt"):
        assert suffix in record[key]
        record[key] = record[key].replace(suffix, "")

    seg = S.resolve_segmentation("sdr", record, tokenizer)
    assert seg.segments["designation_suffix"].spans == ()
    assert seg.segments["designation_suffix"].status == "absent"
    assert indices_of(seg, "pressure_clause")


# ==============================================================================
# VALIDATION
# ==============================================================================

def test_validation_accepts_a_resolved_segmentation(sdr, tokenizer):
    record, seg = sdr
    report = S.validate_segmentation(seg, record, tokenizer)
    assert report["readout"] == seg.readout
    assert report["overlaps"] == []


def test_the_readout_must_be_the_position_the_task_predicts_at(sdr, tokenizer):
    """`pred_spec` reads `prefix_length - 1`; a Segment map on a different
    token axis would put every later plot on the wrong spans."""
    record, seg = sdr
    assert seg.readout == S.readout_position(tokenizer, record["clean_prompt"])

    moved = S.Segmentation(task=seg.task, record_id=seg.record_id,
                           n_tokens=seg.n_tokens, readout=seg.readout - 1,
                           segments=seg.segments, scheme=seg.scheme)
    with pytest.raises(S.SegmentationError, match="Readout"):
        S.validate_segmentation(moved, record, tokenizer)


def test_a_designation_position_that_repeats_in_the_sentence_is_refused(tokenizer):
    """Exactly once, in the Designating Sentence — the Designation Suffix is
    allowed to repeat the predicate words, the sentence is not."""
    record = dict(sdr_record())
    for key in ("clean_prompt", "corrupt_prompt"):
        record[key] = record[key].replace(
            "and the other result is harmless.",
            "and the other harmless result is harmless.")

    with pytest.raises(S.SegmentationError, match="exactly once"):
        S.resolve_segmentation("sdr", record, tokenizer)


def test_an_intro_that_does_not_match_the_scaffold_is_refused(tokenizer):
    record = dict(sdr_record())
    for key in ("clean_prompt", "corrupt_prompt"):
        record[key] = record[key].replace("'s audit reviewed", " looked at")

    with pytest.raises(S.SegmentationError, match="intro sentence"):
        S.resolve_segmentation("sdr", record, tokenizer)


# ==============================================================================
# OVERRIDES
# ==============================================================================

def test_an_override_replaces_a_segment_by_regex_over_the_prompt(sdr_free):
    record, tokenizer = sdr_free
    plain = S.resolve_segmentation("sdr", record, tokenizer)

    seg = S.resolve_segmentation(
        "sdr", record, tokenizer,
        overrides={"designation_suffix": r"THE DAMAGING ONE[^.]*\."})

    assert seg.segments["designation_suffix"].source == "override"
    assert indices_of(seg, "designation_suffix") == \
        indices_of(plain, "designation_suffix")

    narrow = S.resolve_segmentation("sdr", record, tokenizer,
                                    overrides={"designation_suffix": "DAMAGING"})
    assert len(indices_of(narrow, "designation_suffix")) == 1
    # What the narrowed Segment gave up is unsegmented, not lost.
    assert set(indices_of(plain, "designation_suffix")) <= (
        set(indices_of(narrow, "designation_suffix"))
        | set(indices_of(narrow, S.UNSEGMENTED)))


def test_an_override_can_add_a_segment_the_task_does_not_define(sdr_free):
    record, tokenizer = sdr_free
    seg = S.resolve_segmentation("sdr", record, tokenizer,
                                 overrides={"threat": "flagged measurement"})
    assert "threat" in seg.names
    assert seg.segments["threat"].source == "override"
    assert len(indices_of(seg, "threat")) == 2
    # The added Segment sits inside the Pressure Clause and overlaps it: an
    # override takes the tokens its regex names whatever else holds them.
    plain = S.resolve_segmentation("sdr", record, tokenizer)
    assert set(indices_of(seg, "threat")) <= set(indices_of(plain, "pressure_clause"))
    assert set(indices_of(seg, "threat")) <= set(indices_of(seg, "pressure_clause"))


def test_overrides_are_parsed_as_name_equals_regex_and_reserve_two_names():
    assert S.parse_segment_overrides(["a=x.*y", "b==="]) == {"a": "x.*y", "b": "=="}
    with pytest.raises(ValueError, match="NAME=REGEX"):
        S.parse_segment_overrides(["nope"])
    for name in S.RESERVED_SEGMENT_NAMES:
        with pytest.raises(ValueError, match="reserved"):
            S.parse_segment_overrides([f"{name}=x"])
    with pytest.raises(ValueError, match="regex"):
        S.parse_segment_overrides(["a=[unclosed"])


def test_an_override_that_matches_nothing_on_an_instance_is_recorded(sdr_free):
    record, tokenizer = sdr_free
    seg = S.resolve_segmentation("sdr", record, tokenizer,
                                 overrides={"nowhere": "zzzz-not-here"})
    assert seg.segments["nowhere"].status == "absent"
    assert seg.segments["nowhere"].spans == ()




@pytest.fixture
def sdr_free(tokenizer):
    return sdr_record(), tokenizer


# ==============================================================================
# STD
# ==============================================================================

def std_record():
    from dataset.std_llama import build_prompt_pair

    statement = "Humans have five basic senses."
    pressure = "Telling the truth exposes you to serious legal liability."
    clean, corrupt, target, distractor = build_prompt_pair(
        statement, ("accurate", "inaccurate"), "pos", pressure)
    return {"task": "std", "statement": statement, "pressure": pressure,
            "stip_pos": "accurate", "stip_neg": "inaccurate", "polarity": "pos",
            "clean_stip": "accurate", "corrupt_stip": "inaccurate",
            "clean_prompt": clean, "corrupt_prompt": corrupt,
            "target": target, "distractor": distractor}


def test_std_has_its_own_default_segmentation(tokenizer):
    record = std_record()
    seg = S.resolve_segmentation("std", record, tokenizer)
    prompt = record["clean_prompt"]
    text = dict((i, t) for i, t, _ in chunks(prompt))

    assert set(seg.names) == set(S.STD_SEGMENTS)

    stip = indices_of(seg, "stipulation_token")
    assert len(stip) == 1 and text[stip[0]].startswith("accurate")

    statement = indices_of(seg, "statement")
    assert [text[i] for i in statement] == record["statement"].split()

    clause = indices_of(seg, "pressure_clause")
    # The fake tokenizer has no <|eot_id|> token, so the clause's last chunk
    # carries the marker with it; the words are what matters.
    assert [text[i].split("<|")[0] for i in clause] == record["pressure"].split()

    assert indices_of(seg, "readout") == [len(chunks(prompt)) - 1]
    assert indices_of(seg, "question")
    assert indices_of(seg, "stem")

    seen = [i for name in seg.names for i in indices_of(seg, name)]
    assert sorted(seen) == list(range(seg.n_tokens))


def test_std_stipulation_is_read_from_the_record_not_guessed(tokenizer):
    record = std_record()
    other = dict(record)
    from dataset.std_llama import build_prompt_pair
    clean, corrupt, target, distractor = build_prompt_pair(
        record["statement"], ("valid", "invalid"), "neg", record["pressure"])
    other.update(clean_prompt=clean, corrupt_prompt=corrupt,
                 stip_pos="valid", stip_neg="invalid", polarity="neg",
                 clean_stip="invalid", corrupt_stip="valid")

    seg = S.resolve_segmentation("std", other, tokenizer)
    text = dict((i, t) for i, t, _ in chunks(other["clean_prompt"]))
    stip = indices_of(seg, "stipulation_token")
    assert text[stip[0]].startswith("invalid")


# ==============================================================================
# TEMPLATE ASSUMPTIONS THE SEGMENTER MAKES
# ==============================================================================

def test_every_template_variant_still_says_other():
    """The Other Token is literal in the Designating Sentence, not a record
    field, so the segmenter names the word itself. If a Template Variant ever
    stops saying it, this fails here rather than on every instance of a GPU
    run."""
    for spec in SPECS.values():
        for name in spec.variant_names:
            designation = spec.variant(name).designation
            assert re.search(r"(?<![A-Za-z0-9_])" + S.OTHER_WORD +
                             r"(?![A-Za-z0-9_])", designation), \
                f"{spec.task}/{name}: {designation!r}"


def test_an_item_the_question_never_names_is_refused(tokenizer):
    """Both items are named in the user question; a prompt where one is not is
    a Scaffold change, and every Item Mention plot would silently be empty."""
    record = dict(sdr_record())
    for key in ("clean_prompt", "corrupt_prompt"):
        head, _, tail = record[key].partition(
            "<|start_header_id|>user<|end_header_id|>")
        record[key] = head + "<|start_header_id|>user<|end_header_id|>" + \
            tail.replace("pricing", "the other one")

    seg = S.resolve_segmentation("sdr", record, tokenizer)
    with pytest.raises(S.SegmentationError, match="item_2_question_pair"):
        S.validate_segmentation(seg, record, tokenizer)


def test_a_question_that_names_an_item_a_third_time_is_refused(tokenizer):
    """Two mentions per item is the Scaffold: the pair naming and the quoted
    option. A third would be pooled into one of the two Segments and quietly
    change what a plot of it means, so validation refuses it."""
    record = dict(sdr_record())
    for key in ("clean_prompt", "corrupt_prompt"):
        head, sep, tail = record[key].partition(
            "<|start_header_id|>user<|end_header_id|>")
        record[key] = head + sep + tail.replace(
            "Only respond", "Prefer pricing. Only respond", 1)

    seg = S.resolve_segmentation("sdr", record, tokenizer)
    with pytest.raises(S.SegmentationError, match="item_2_question_option"):
        S.validate_segmentation(seg, record, tokenizer)


def test_the_readout_agrees_with_the_dataset_class_the_task_loads(tokenizer):
    """The Readout against `DeceptionDatasetLlama`, not against a re-derivation.

    `readout_position` recomputes `len(encode(prompt)) - 1`, which is the
    same expression the dataset class uses, so comparing the two alone would
    only restate it. This drives the record through the class the task's
    dataloader actually builds and reads the `prefix_length` it stored, which
    is the number `pred_spec` subtracts one from.
    """
    from dataset.deception_common import DeceptionDatasetLlama

    record = sdr_record()
    dataset = DeceptionDatasetLlama([record], tokenizer, max_length=256)
    assert len(dataset.processed_data) == 1, \
        "the fixture was dropped by the dataset class, so nothing is compared"

    seg = S.resolve_segmentation("sdr", record, tokenizer)
    assert seg.readout == dataset.processed_data[0]["prefix_length"] - 1
    assert indices_of(seg, "readout") == [seg.readout]
