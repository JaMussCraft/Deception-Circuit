"""
Knockout extensions for phase 1 (ticket 02a, spec R11, R16, R19), the parts
that need no model: the positions flag and the masks it builds from the
Segments, the groups file, greedy selection on a scripted effect table, the
sweep's exclusion from ranking, and the column names a non-default plan
writes under. Runs in both environments.
"""

from __future__ import annotations

import argparse
import json

import pytest
import torch

from component_analysis import knockout as ko
from component_analysis.segmentation import Segment, Segmentation


# ==============================================================================
# THE POSITIONS FLAG
# ==============================================================================

@pytest.mark.parametrize("text, parsed", [
    ("all", {"form": "all"}),
    ("readout", {"form": "readout"}),
    ("pressure_clause", {"form": "segment", "segment": "pressure_clause"}),
    ("after=pressure_clause", {"form": "after", "segment": "pressure_clause",
                               "exclude_readout": False}),
    ("after=pressure_clause,exclude=readout",
     {"form": "after", "segment": "pressure_clause", "exclude_readout": True}),
])
def test_the_positions_flag_parses_every_form(text, parsed):
    assert {k: v for k, v in ko.parse_positions(text).items() if k != "text"} == parsed


@pytest.mark.parametrize("bad", ["after=", "after=x,exclude=stem", "two words",
                                 "after=x,include=readout"])
def test_a_malformed_positions_value_is_refused_at_parse_time(bad):
    with pytest.raises(argparse.ArgumentTypeError):
        ko.parse_positions(bad)


def segmentation(rid, n_tokens, segments):
    return Segmentation(task="sdr_v2", record_id=rid, n_tokens=n_tokens,
                        readout=n_tokens - 1,
                        segments={name: Segment(name, tuple(spans))
                                  for name, spans in segments.items()})


#: Two prompts of 10 and 8 tokens, padded to 12. The clause ends at 6 and at 5.
SEGS = {
    "a": segmentation("a", 10, {"intro": [(0, 3)], "pressure_clause": [(3, 6)],
                                "question": [(6, 8)], "stem": [(8, 10)],
                                "readout": [(9, 10)]}),
    "b": segmentation("b", 8, {"intro": [(0, 2)], "pressure_clause": [(2, 5)],
                               "question": [(5, 6)], "stem": [(6, 8)],
                               "readout": [(7, 8)]}),
}
READOUT = torch.tensor([9, 7])


def mask_rows(text, ids=("a", "b")):
    mask = ko.position_mask(ko.parse_positions(text), list(ids), SEGS, READOUT, 12)
    return None if mask is None else [torch.nonzero(row).flatten().tolist()
                                      for row in mask]


def test_all_positions_is_no_mask_so_the_v1_path_is_unchanged():
    assert mask_rows("all") is None


def test_the_readout_form_is_the_readout_alone():
    assert mask_rows("readout") == [[9], [7]]


def test_a_segment_form_is_exactly_that_segments_tokens():
    assert mask_rows("pressure_clause") == [[3, 4, 5], [2, 3, 4]]


def test_the_post_clause_range_is_every_token_after_the_clause_but_the_readout():
    assert mask_rows("after=pressure_clause,exclude=readout") == [
        [6, 7, 8], [5, 6]]
    assert mask_rows("after=pressure_clause") == [[6, 7, 8, 9], [5, 6, 7]]


def test_a_segment_absent_on_a_row_is_refused_by_name():
    no_clause = {**SEGS, "c": segmentation("c", 8, {"intro": [(0, 2)],
                                                    "pressure_clause": [],
                                                    "readout": [(7, 8)]})}
    with pytest.raises(ValueError, match="pressure_clause.*absent.*c"):
        ko.position_mask(ko.parse_positions("after=pressure_clause"), ["c"],
                         no_clause, torch.tensor([7]), 12)


def test_an_unknown_segment_is_refused_by_name():
    with pytest.raises(ValueError, match="no Segment 'clause'"):
        mask_rows("after=clause")


# ==============================================================================
# THE PLAN, AND THE COLUMN NAMES IT WRITES UNDER
# ==============================================================================

def test_the_default_plan_writes_the_v1_column_names():
    assert ko.KnockoutPlan().column_suffix == ""


def test_a_non_default_plan_writes_columns_whose_names_say_so():
    plan = ko.KnockoutPlan(counterfactual="neutral_twin",
                           positions="after=pressure_clause,exclude=readout")
    assert plan.column_suffix == "_neutral_twin_paired_after_pressure_clause_excl_readout"
    assert ko.KnockoutPlan(scheme="mean").column_suffix == "_mean"
    assert ko.KnockoutPlan(positions="readout").column_suffix == "_at_readout"


def test_mean_and_zero_take_no_counterfactual_stream():
    with pytest.raises(ValueError, match="interchange"):
        ko.KnockoutPlan(scheme="zero", counterfactual="neutral_twin")


@pytest.mark.parametrize("scheme", ["interchange", "mean", "zero"])
def test_every_scheme_is_built(scheme):
    assert ko.resolve_scheme(scheme) == scheme


# ==============================================================================
# THE GROUPS FILE
# ==============================================================================

def test_a_groups_file_is_name_to_component_keys(tmp_path):
    path = tmp_path / "groups.json"
    path.write_text(json.dumps({"core": [["head", 17, 24], ["mlp", 30, 0]],
                                "single": [["head", 5, 8]]}))
    assert ko.load_groups(str(path)) == [
        ("core", [("head", 17, 24), ("mlp", 30, 0)]), ("single", [("head", 5, 8)])]


@pytest.mark.parametrize("groups, why", [
    ({"empty": []}, "no Component"),
    ({"bad": [["head", 1]]}, r"\[kind, layer, index\]"),
    ({"bad": [["q", 1, 2]]}, "head or mlp"),
    ({"twice": [["head", 1, 2], ["head", 1, 2]]}, "twice"),
    (["not", "a", "dict"], "object"),
])
def test_a_malformed_groups_file_is_refused(tmp_path, groups, why):
    path = tmp_path / "groups.json"
    path.write_text(json.dumps(groups))
    with pytest.raises(ValueError, match=why):
        ko.load_groups(str(path))


def test_a_group_outside_the_model_is_refused_against_its_geometry(tmp_path):
    path = tmp_path / "groups.json"
    path.write_text(json.dumps({"far": [["head", 40, 0]]}))
    groups = ko.load_groups(str(path))
    with pytest.raises(ValueError, match="layer 40"):
        ko.check_groups(groups, {"num_layers": 32, "num_heads": 32})


# ==============================================================================
# GREEDY SELECTION
# ==============================================================================

A, B, C, D = ("head", 1, 0), ("head", 2, 0), ("head", 3, 0), ("mlp", 4, 0)

#: Joint drops of every set the greedy search can ask for, worked by hand:
#: A is the best single, but B and C are redundant with A's partner choices,
#: so the order is A, then C (A+C = 1.9 beats A+B = 1.2 and A+D = 1.4), then D.
TABLE = {
    frozenset(): 0.0,
    frozenset([A]): 1.0, frozenset([B]): 0.9, frozenset([C]): 0.5, frozenset([D]): 0.2,
    frozenset([A, B]): 1.2, frozenset([A, C]): 1.9, frozenset([A, D]): 1.4,
    frozenset([A, C, B]): 2.0, frozenset([A, C, D]): 2.3,
    frozenset([A, C, D, B]): 2.35,
}


def scripted(groups):
    return [(TABLE[frozenset(group)], None) for group in groups]


def test_greedy_adds_the_component_with_the_largest_joint_drop_each_step():
    steps = ko.greedy_select([A, B, C, D], scripted, k_max=3)
    assert [step["added"] for step in steps] == [A, C, D]
    assert [step["joint_drop"] for step in steps] == [1.0, 1.9, 2.3]
    assert steps[2]["members"] == [A, C, D]
    assert [one["key"] for one in steps[1]["candidates"]] == [B, C, D]


def test_greedy_breaks_a_tie_by_pool_order():
    def flat(groups):
        return [(1.0, None) for _ in groups]
    steps = ko.greedy_select([C, A, B], flat, k_max=2)
    assert [step["added"] for step in steps] == [C, A]


def test_greedy_stops_at_the_pool_size():
    steps = ko.greedy_select([A, B], scripted, k_max=5)
    assert len(steps) == 2


def sweep_file(tmp_path, rows, **extra):
    path = tmp_path / "sweep.json"
    path.write_text(json.dumps({"components": rows, **extra}))
    return str(path)


def row(key, drop):
    return {"key": list(key), "kind": key[0], "layer": key[1], "index": key[2],
            "mean_drop": drop}


def test_the_greedy_pool_is_the_top_of_a_sweep_by_signed_drop_less_layer_zero_mlp(tmp_path):
    rows = [row(("mlp", 0, 0), 3.0), row(A, -2.0), row(B, 0.4), row(C, 0.9),
            row(D, 0.4), {**row(("head", 9, 9), 5.0), "excluded_from_ranking": True}]
    pool = ko.greedy_pool(sweep_file(tmp_path, rows), size=3)
    # Signed, so the large negative A is last; ties (B, D) by model order;
    # the layer-0 MLP and a row excluded from ranking never enter.
    assert pool == [C, B, D]


# ==============================================================================
# THE SWEEP'S EXCLUSION FROM RANKING
# ==============================================================================

def effects(drops):
    keys = list(drops)
    return ko.Effects(ids=["x", "y"], keys=keys,
                      clean_logit_difference=[1.0, 1.0],
                      knocked_logit_difference={k: [1.0 - d, 1.0 - d]
                                                for k, d in drops.items()})


def test_an_excluded_component_keeps_its_numbers_and_loses_its_rank():
    swept = effects({("mlp", 0, 0): 3.0, A: 0.5, B: -0.7})
    rows = ko.summarize_sweep(swept, [A], threshold=0.4,
                              exclude_from_ranking=[("mlp", 0, 0)])
    by_key = {r["key"]: r for r in rows}
    assert by_key[("mlp", 0, 0)]["rank"] is None
    assert by_key[("mlp", 0, 0)]["mean_drop"] == pytest.approx(3.0)
    assert by_key[("mlp", 0, 0)]["excluded_from_ranking"] is True
    assert by_key[("mlp", 0, 0)]["flagged"] is False
    assert (by_key[B]["rank"], by_key[A]["rank"]) == (1, 2)


def test_without_exclusions_the_sweep_rows_are_the_v1_rows():
    swept = effects({("mlp", 0, 0): 3.0, A: 0.5, B: -0.7})
    rows = ko.summarize_sweep(swept, [A], threshold=0.4)
    assert all("excluded_from_ranking" not in r for r in rows)
    assert [r["rank"] for r in rows] == [1, 2, 3]


# ==============================================================================
# v1's JSON IS v1's JSON
# ==============================================================================

#: The keys `knockout.json` had before ticket 02a, written out by hand.
V1_PAYLOAD_KEYS = {"analysis", "circuit", "task", "scheme", "metric",
                   "n_components", "instances", "sample", "clean_run",
                   "components"}
V1_SIGN = ("drop = clean logit difference - knocked-out logit difference, so a "
           "positive drop means the Component helps deception and a negative "
           "one means it opposes it")
V1_ABLATION = ("the Component's output at every position is replaced by the "
               "value it carried on the item-swap corrupt stream")
PLAN_KEYS = {"plan", "target_direction", "counterfactual_run",
             "unpaired_instance_ids"}


def test_the_default_plan_writes_v1s_keys_sign_and_ablation_sentence():
    made = effects({A: 0.5, B: -0.2})
    single = ko.payload(made, circuit="delta", task="sdr")
    assert set(single) == V1_PAYLOAD_KEYS
    assert single["metric"]["sign"] == V1_SIGN
    assert single["metric"]["ablation"] == V1_ABLATION
    rows = ko.summarize_sweep(made, [A], threshold=0.4)
    swept = ko.sweep_payload(made, rows, circuit="delta", task="sdr", threshold=0.4)
    families = ko.family_payload(effects({"mover": 0.3}), {"mover": [A]},
                                 circuit="delta", task="sdr")
    assert not PLAN_KEYS & set(swept)
    assert not PLAN_KEYS & set(families)


def test_a_recorded_plan_adds_its_keys_and_says_the_target_direction():
    made = effects({A: 0.5})
    single = ko.payload(made, circuit="u", task="sdr_v2", target_direction="honest",
                        extra={"instances_file": "knockout_instances.json"},
                        record_plan=True)
    assert set(single) == V1_PAYLOAD_KEYS | PLAN_KEYS | {"instances_file"}
    assert single["target_direction"] == "honest"
    assert "target direction" in single["metric"]["sign"]
    assert single["plan"]["counterfactual"] == "item_swap"
    # `extra` never leaks into a payload that records no plan.
    assert "instances_file" not in ko.payload(made, circuit="u", task="sdr",
                                              extra={"instances_file": "x"})


def test_the_sidecar_names_every_margin_list():
    made = effects({A: 0.5})
    made.counterfactual_logit_difference = [-0.4, -0.3]
    made.neutral_twin_logit_difference = [-0.4, None]
    sidecar = ko.instances_payload(made, what="groups", label=str)
    assert sidecar["instance_ids"] == ["x", "y"]
    assert sidecar["clean_logit_difference"] == [1.0, 1.0]
    assert sidecar["counterfactual_logit_difference"] == [-0.4, -0.3]
    assert sidecar["neutral_twin_logit_difference"] == [-0.4, None]
    assert sidecar["knocked_logit_difference"][str(A)] == [0.5, 0.5]
