"""
Segment-union positions for `--knockout-positions` (instructed-route B1 ticket
3, plan sections 2.1 and 7): `segments=a+b+c` writes at the union of several
Segments, so one knockout column can cover every option token of the
`mechanism_v2` scheme at once. No model; runs in both environments.

The positions fixtures of `test_component_analysis_v2_knockout.py` are
rebuilt here with the real `mechanism_v2` option Segment names rather than
imported, so the two test modules stay independent.
"""

from __future__ import annotations

import argparse

import pytest
import torch

from component_analysis import knockout as ko
from component_analysis.segmentation import (MECHANISM_SEGMENTS,
                                             MECHANISM_V2_SEGMENTS, STD_SEGMENTS,
                                             Segment, Segmentation)

OPTIONS = ("item_1_question_pair", "item_2_question_pair",
           "item_1_question_option", "item_2_question_option")
UNION = "segments=" + "+".join(OPTIONS)


def segmentation(rid, n_tokens, segments):
    return Segmentation(task="far_v2", record_id=rid, n_tokens=n_tokens,
                        readout=n_tokens - 1, scheme="mechanism_v2",
                        segments={name: Segment(name, tuple(spans))
                                  for name, spans in segments.items()})


#: Two prompts of 14 and 12 tokens, padded to 16. Each option Segment is one
#: token, as on the held-out ids; the clause sits before them.
SEGS = {
    "a": segmentation("a", 14, {"item_1_intro": [(1, 2)], "item_2_intro": [(2, 3)],
                                "pressure_clause": [(3, 6)], "question": [(6, 7)],
                                "item_1_question_pair": [(7, 8)],
                                "item_2_question_pair": [(9, 10)],
                                "response_line": [(10, 11)],
                                "item_1_question_option": [(11, 12)],
                                "item_2_question_option": [(12, 13)],
                                "stem": [(13, 14)], "readout": [(13, 14)]}),
    "b": segmentation("b", 12, {"item_1_intro": [(0, 1)], "item_2_intro": [(1, 2)],
                                "pressure_clause": [(2, 4)], "question": [(4, 5)],
                                "item_1_question_pair": [(5, 6)],
                                "item_2_question_pair": [(6, 7)],
                                "response_line": [(7, 8)],
                                "item_1_question_option": [(8, 9)],
                                "item_2_question_option": [(10, 11)],
                                "stem": [(11, 12)], "readout": [(11, 12)]}),
}
READOUT = torch.tensor([13, 11])
SEQ = 16


def mask(text, ids=("a", "b"), segs=SEGS, readout=READOUT):
    return ko.position_mask(ko.parse_positions(text), list(ids), segs, readout, SEQ)


# ==============================================================================
# PARSING
# ==============================================================================

def test_a_union_parses_to_its_segment_names_in_the_order_given():
    parsed = ko.parse_positions(UNION)
    assert parsed == {"form": "segments", "segments": list(OPTIONS), "text": UNION}


def test_a_union_of_one_segment_is_accepted():
    assert ko.parse_positions("segments=readout")["segments"] == ["readout"]


@pytest.mark.parametrize("bad", ["segments=", "segments=a++b", "segments=+a",
                                 "segments=a+", "segments=a+a", "segments=a+b c",
                                 "segments=a,b", "segments=1a+b"])
def test_a_malformed_union_is_refused_at_parse_time(bad):
    with pytest.raises(argparse.ArgumentTypeError):
        ko.parse_positions(bad)


@pytest.mark.parametrize("text, parsed", [
    ("all", {"form": "all"}),
    ("readout", {"form": "readout"}),
    ("pressure_clause", {"form": "segment", "segment": "pressure_clause"}),
    ("after=pressure_clause", {"form": "after", "segment": "pressure_clause",
                               "exclude_readout": False}),
    ("after=pressure_clause,exclude=readout",
     {"form": "after", "segment": "pressure_clause", "exclude_readout": True}),
])
def test_the_existing_forms_still_parse_to_the_same_result(text, parsed):
    assert ko.parse_positions(text) == {**parsed, "text": text}


def test_the_flag_accepts_a_union():
    parser = argparse.ArgumentParser()
    ko.add_arguments(parser.add_argument_group("knockout"))
    cli = parser.parse_args(["--knockout-positions", UNION])
    assert cli.knockout_positions["form"] == "segments"
    assert "segments=" in parser.format_help()


# ==============================================================================
# THE MASK
# ==============================================================================

def test_the_union_mask_is_the_or_of_the_single_segment_masks():
    expected = torch.zeros((2, SEQ), dtype=torch.bool)
    for name in OPTIONS:
        expected |= mask(name)
    union = mask(UNION)
    assert union.dtype == torch.bool and union.shape == (2, SEQ)
    assert torch.equal(union, expected)
    assert [torch.nonzero(row).flatten().tolist() for row in union] == [
        [7, 9, 11, 12], [5, 6, 8, 10]]


def test_a_union_of_one_segment_equals_the_segment_form():
    assert torch.equal(mask("segments=pressure_clause"), mask("pressure_clause"))


def test_overlapping_segments_are_counted_once():
    union = mask("segments=stem+readout")
    assert torch.equal(union, mask("stem") | mask("readout"))
    assert [torch.nonzero(row).flatten().tolist() for row in union] == [[13], [11]]


def test_the_union_excludes_the_pre_clause_mentions():
    union = mask(UNION)
    intros = mask("segments=item_1_intro+item_2_intro")
    assert not (union & intros).any()


def test_a_segment_the_scheme_does_not_define_is_refused_by_name():
    with pytest.raises(ValueError, match="no Segment 'item_3_question_option'"):
        mask("segments=item_1_question_pair+item_3_question_option")


def test_a_defined_segment_absent_on_a_row_is_refused_by_name():
    no_option = dict(SEGS)
    spans = {name: list(seg.spans) for name, seg in SEGS["b"].segments.items()}
    spans["item_2_question_option"] = []
    no_option["b"] = segmentation("b", 12, spans)
    with pytest.raises(ValueError, match="item_2_question_option.*absent.*b"):
        mask(UNION, segs=no_option)


def test_a_row_without_a_segmentation_is_refused():
    with pytest.raises(ValueError, match="no segmentation"):
        mask(UNION, ids=("a", "z"))


def test_every_declared_v2_option_segment_is_a_scheme_name():
    for name in OPTIONS:
        assert name in MECHANISM_V2_SEGMENTS


# ==============================================================================
# THE COLUMN SUFFIX
# ==============================================================================

def suffix(text, **plan):
    return ko.KnockoutPlan(positions=text, **plan).column_suffix


def test_the_union_suffix_is_stable_across_two_parses():
    assert suffix(UNION) == suffix(UNION)
    assert ko.positions_slug(ko.parse_positions(UNION)) == \
        ko.positions_slug(ko.parse_positions(UNION))


def test_the_union_suffix_is_documented_form():
    assert suffix(UNION) == ("_at_item_1_question_option+item_1_question_pair"
                             "+item_2_question_option+item_2_question_pair")
    assert suffix(UNION, counterfactual="neutral_twin") == (
        "_neutral_twin_paired_at_item_1_question_option+item_1_question_pair"
        "+item_2_question_option+item_2_question_pair")


def test_the_union_suffix_ignores_the_order_the_segments_are_given_in():
    assert suffix("segments=stem+question") == suffix("segments=question+stem")


def test_different_unions_have_different_suffixes():
    texts = [UNION, "segments=item_1_question_pair+item_2_question_pair",
             "segments=item_1_question_option+item_2_question_option",
             "segments=pressure_clause+readout", "readout", "all"]
    suffixes = [suffix(text) for text in texts]
    assert len(set(suffixes)) == len(suffixes)


def test_a_union_of_one_segment_writes_the_segment_forms_columns():
    assert suffix("segments=pressure_clause") == suffix("pressure_clause")


def test_no_union_of_declared_names_collides_with_a_single_segment_suffix():
    for names in (MECHANISM_SEGMENTS, MECHANISM_V2_SEGMENTS, STD_SEGMENTS):
        singles = {suffix(name) for name in names}
        pairs = {suffix(f"segments={a}+{b}") for a in names for b in names if a != b}
        assert not singles & pairs


def test_the_existing_suffixes_are_unchanged():
    assert suffix("all") == ""
    assert suffix("readout") == "_at_readout"
    assert suffix("pressure_clause") == "_at_pressure_clause"
    assert suffix("after=pressure_clause,exclude=readout") == \
        "_after_pressure_clause_excl_readout"


def test_a_union_plan_has_an_ablation_sentence_naming_its_segments():
    sentence = ko.ablation_sentence(ko.KnockoutPlan(
        counterfactual="neutral_twin", positions=UNION))
    for name in OPTIONS:
        assert name in sentence
    assert "Neutral-Clause Twin" in sentence
