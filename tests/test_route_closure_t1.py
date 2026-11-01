"""
route_closure, T1: the sweeps, the controls and the path patching (B1 plan, ticket 5).

The pure tests (flags, sender sets, draws, the summary arithmetic, the path-patching
receiver map) run in both environments. The model tests run the tiny 2-layer GQA Llama
under nnsight 0.7.0 and skip otherwise, as the ticket-4 tests do, whose batch, fixtures
and stub context are reused.

On the tiny model the "quartet" is layer 1, heads 2 and 3 (KV group 1).
"""

from __future__ import annotations

import json
import os

import pytest
import torch

from component_analysis import route_closure as rc
from tests.helpers import TINY
from tests.test_route_closure_t2 import (  # noqa: F401  (fixtures)
    CLAUSE, GROUP, LAYER, QUARTET, ListBatches, StubContext, model, nnsight_model, pair,
    parser, segmentations_by_id, twin_batch)

QUARTET_KEYS = [("head", LAYER, h) for h in QUARTET]


# ==============================================================================
# FLAGS AND SENDER SETS (no model)
# ==============================================================================

def test_the_ticket_5_flags_parse_with_their_defaults():
    cli = parser().parse_args([])
    assert cli.route_c2_layers == (8, 16)
    assert cli.route_path_patching == "on"
    assert rc.parse_keys(cli.route_pp_feeders) == [
        ("head", 14, 4), ("head", 15, 8), ("mlp", 13, 0), ("mlp", 14, 0), ("mlp", 15, 0)]
    cli = parser().parse_args(["--route-c2-layers", "0-0", "--route-path-patching", "off",
                               "--route-pp-feeders", "head.0.1,mlp.0.0"])
    assert cli.route_c2_layers == (0, 0)
    assert cli.route_path_patching == "off"
    assert rc.parse_keys(cli.route_pp_feeders) == [("head", 0, 1), ("mlp", 0, 0)]
    with pytest.raises(SystemExit):
        parser().parse_args(["--route-c2-layers", "16-8"])


def test_the_outside_senders_exclude_the_grid_the_quartet_and_the_embedding():
    grid = {("head", 17, 3), ("mlp", 4, 0)}
    quartet = {("head", 17, h) for h in (24, 25, 26, 27)}
    outside = rc.outside_senders(num_layers=32, num_heads=32, excluded=grid | quartet)
    assert len(outside) == 32 * 32 + 32 - len(grid) - len(quartet)
    assert not set(outside) & (grid | quartet)
    assert ("embed", 0, 0) not in outside
    assert outside[0] == ("head", 0, 0) and outside[-1] == ("mlp", 31, 0)
    assert ("mlp", 31, 0) in outside and ("head", 31, 0) in outside


def test_c2_draws_are_seeded_in_layer_range_and_disjoint_from_grid_deciding_set_and_quartet():
    grid = {("head", 9, h) for h in range(30)}
    deciding = [("head", 10, 22), ("head", 11, 0), ("mlp", 6, 0)]
    quartet = [("head", 17, h) for h in (24, 25, 26, 27)]
    first = rc.draw_c2_heads(num_heads=32, layers=(8, 16), excluded=grid | set(deciding)
                             | set(quartet), n_draws=5, size=4, seed=20261101)
    again = rc.draw_c2_heads(num_heads=32, layers=(8, 16), excluded=grid | set(deciding)
                             | set(quartet), n_draws=5, size=4, seed=20261101)
    other = rc.draw_c2_heads(num_heads=32, layers=(8, 16), excluded=grid, n_draws=5, size=4,
                             seed=1)
    assert first == again and first != other
    assert len(first) == 5
    for draw in first:
        assert len(draw) == 4 and len(set(draw)) == 4
        for kind, layer, head in draw:
            assert kind == "head" and 8 <= layer <= 16 and 0 <= head < 32
        assert not set(draw) & (grid | set(deciding) | set(quartet))
    # A range the model does not have gives no draw (the tiny model), not an error.
    assert rc.draw_c2_heads(num_heads=4, layers=(8, 16), excluded=set(), n_draws=5,
                            size=4, seed=1, num_layers=2) == []
    with pytest.raises(ValueError, match="layers 0-0"):
        rc.draw_c2_heads(num_heads=4, layers=(0, 0), excluded={("head", 0, 0)}, n_draws=1,
                         size=4, seed=1, num_layers=2)


def test_the_t1_control_arms_restore_from_t_at_every_position_except_s_k_and_c3():
    arms = rc.build_t1_arms(layer=17, c1_draws=[[0, 1, 2, 3], [4, 5, 6, 7]],
                            c2_draws=[[("head", 9, 1), ("head", 12, 4), ("head", 14, 0),
                                       ("head", 16, 31)]],
                            deciding=[("head", 9, 29), ("mlp", 6, 0)])
    by_name = {arm.name: arm for arm in arms}
    assert list(by_name) == ["c1_d0", "c1_d1", "c2_d0", "c3_push", "s_k"]
    assert by_name["c1_d1"].writes == tuple((("head", 17, h), "all") for h in (4, 5, 6, 7))
    assert by_name["c2_d0"].writes[1] == (("head", 12, 4), "all")
    assert by_name["s_k"].writes == ((("head", 9, 29), "post_clause"),
                                     (("mlp", 6, 0), "post_clause"))
    assert by_name["c3_push"].writes == ((("mlp", 17, 0), "readout"),)
    for arm in arms:
        assert arm.test == "t1" and arm.base == "D" and arm.source == "T"
    assert by_name["c3_push"].meta["push"] is True
    assert rc.build_t1_arms(layer=17, c1_draws=[], c2_draws=[], deciding=[]) == [
        arm for arm in rc.build_t1_arms(layer=17, c1_draws=[], c2_draws=[], deciding=[])
        if arm.name == "c3_push"]


# ==============================================================================
# THE SUMMARY ARITHMETIC (no model)
# ==============================================================================

def test_the_summary_normalizes_every_sender_by_the_mean_twin_gap_as_a_ratio_of_means():
    keys = [("head", 1, 0), ("mlp", 1, 0), ("head", 0, 1)]
    drops = torch.tensor([[1.0, -0.5, 0.25],
                          [2.0, -1.5, 0.75]])
    gap = torch.tensor([1.0, 3.0])                      # mean 2.0; per-row ratios differ
    include = [True, True, False]
    m_d = torch.tensor([4.0, 6.0])
    margins = torch.tensor([3.0, 4.0])                  # the arm's own margins
    joint = torch.tensor([0.5, 1.5])
    out = rc.summarize_sweep(drops, keys, gap=gap, include=include, joint=joint,
                             margins=margins, m_d=m_d, rows=[("mlp", 1, 0)])
    assert out["senders"]["head.1.0"]["e"] == pytest.approx(1.5 / 2.0)
    assert out["senders"]["mlp.1.0"]["e"] == pytest.approx(-1.0 / 2.0)
    assert out["O"] == pytest.approx(0.25)
    assert out["O_pos"] == pytest.approx(0.75) and out["O_neg"] == pytest.approx(-0.5)
    assert out["O_joint"] == pytest.approx(1.0 / 2.0)
    assert out["r_total"] == pytest.approx((5.0 - 3.5) / 2.0)
    assert out["per_instance"]["outside_sum"] == pytest.approx([0.5, 0.5])
    assert out["per_instance"]["pos_sum"] == pytest.approx([1.0, 2.0])
    assert out["per_instance"]["neg_sum"] == pytest.approx([-0.5, -1.5])
    assert out["rows"]["mlp.1.0"] == pytest.approx(-0.5)
    assert out["per_instance"]["rows"]["mlp.1.0"] == pytest.approx([-0.5, -1.5])
    assert out["senders"]["head.0.1"]["in_sum"] is False
    assert out["n_in_sum"] == 2
    # Not the mean of per-instance ratios, and not the arm's own gap.
    assert out["O"] != pytest.approx(float(((drops[:, :2].sum(1)) / gap).mean()))
    assert out["O"] != pytest.approx(float(drops[:, :2].sum(1).mean() / (m_d - margins).mean()))


# ==============================================================================
# PATH PATCHING: WHERE SENDERS AND RECEIVERS ARE WRITTEN (no model)
# ==============================================================================

def test_the_writer_receivers_are_the_plan_sites_at_the_plan_positions():
    kv_of = {h: h // 4 for h in range(32)}.__getitem__
    assert rc.writer_receivers(("mlp", 30, 0), kv_of) == [(("mlp_in", 30, 0), "readout")]
    assert rc.writer_receivers(("head", 31, 0), kv_of) == [
        (("q", 31, 0), "readout"), (("k", 31, 0), "post_clause"),
        (("v", 31, 0), "post_clause")]
    assert rc.writer_receivers(("head", 24, 27), kv_of)[1] == (("k", 24, 6), "post_clause")
    assert rc.PP_SENDER_MASKS == ("readout", "post_clause_no_readout", "post_clause")


def test_the_sender_and_receiver_masks_start_and_end_where_the_plan_says():
    batch, _twin, _mask = twin_batch()
    by_id = segmentations_by_id(batch)
    ids = list(batch.ids)
    masks = rc.position_masks(ids, [by_id[one] for one in ids], batch.readout,
                              batch.input_ids.shape[1])
    for row in range(len(ids)):
        readout = int(batch.readout[row])
        assert masks["readout"][row].nonzero().flatten().tolist() == [readout]
        post = masks["post_clause_no_readout"][row].nonzero().flatten().tolist()
        assert post[0] == CLAUSE[1] and post[-1] == readout - 1
        both = masks["post_clause"][row].nonzero().flatten().tolist()
        assert both[0] == CLAUSE[1] and both[-1] == readout
        assert not (masks["readout"][row] & masks["post_clause_no_readout"][row]).any()


# ==============================================================================
# THROUGH THE MODEL (nnsight 0.7.0)
# ==============================================================================

@pytest.fixture(scope="module")
def dq(model, pair):
    """The primary T1 arm, D with the quartet's outputs from T, every sender captured."""
    from component_analysis import hooks

    bank = rc.restore_bank(pair.t, QUARTET_KEYS, None)
    return rc.run_arm(model, pair, bank, capture_keys=hooks.all_component_keys(model))


def outside(model, grid=()):
    shape = rc.hooks_geometry(model)
    return rc.outside_senders(num_layers=shape["num_layers"], num_heads=shape["num_heads"],
                              excluded=set(grid) | set(QUARTET_KEYS))


def test_the_pair_and_the_arm_keep_the_residual_for_the_lens(model, pair, dq):
    assert pair.d.residual.shape == (3, TINY["layers"] + 1, TINY["hidden"])
    assert pair.t.residual.shape == pair.d.residual.shape
    assert dq.residual.shape == pair.d.residual.shape


def test_the_forward_sweep_is_normalized_by_g_and_not_by_the_arms_own_gap(model, pair, dq):
    from component_analysis import hooks
    from component_analysis import path_patching as pp

    arm_gap = pair.d.margin - dq.margins
    # The case is built so the two normalisers differ (by a third, on this model).
    assert abs(float(arm_gap.mean()) - float(pair.gap.mean())) > \
        0.2 * abs(float(pair.gap.mean()))
    streams = rc.sweep_streams(model, pair, dq.outputs)
    assert torch.equal(streams.gap, pair.gap)
    assert set(streams.clean_outputs) == set(hooks.all_component_keys(model))
    senders = outside(model)
    drops = rc.forward_sweep(model, pair, dq.outputs, senders)
    for sender in senders:
        patched = pp.sweep_readout(model, streams, sender)
        assert torch.allclose(pp.normalized_effect(streams, patched),
                              drops[sender] / pair.gap, atol=1e-6)
    stacked = torch.stack([drops[one] for one in senders], dim=1)
    out = rc.summarize_sweep(stacked, senders, gap=pair.gap, include=[True] * len(senders),
                             joint=rc.forward_joint(model, pair, dq.outputs, senders),
                             margins=dq.margins, m_d=pair.d.margin)
    for column, sender in enumerate(senders):
        want = float(stacked[:, column].mean() / pair.gap.mean())
        assert out["senders"][rc.key_name(sender)]["e"] == pytest.approx(want, abs=1e-6)
    assert out["O"] == pytest.approx(float(stacked.sum(1).mean() / pair.gap.mean()), abs=1e-6)
    assert out["O"] != pytest.approx(float(stacked.sum(1).mean() / arm_gap.mean()), rel=0.1)


@pytest.mark.parametrize("source", ["T", "Dq"])
def test_offline_and_forward_direct_effects_agree_within_1e_3(model, pair, dq, source):
    from component_analysis import hooks

    x_outputs = pair.t.outputs if source == "T" else dq.outputs
    senders = outside(model)
    forward = rc.forward_sweep(model, pair, x_outputs, senders)
    every = [one for one in hooks.all_component_keys(model) if one != hooks.EMBED_KEY]
    offline = rc.offline_direct_effects(model, pair, x_outputs, every, joint=senders)
    for sender in senders:
        column = every.index(sender)
        assert torch.allclose(offline.drops[:, column], forward[sender], atol=1e-3), sender
    joint = rc.forward_joint(model, pair, x_outputs, senders)
    assert torch.allclose(offline.joint, joint, atol=1e-3)
    # Some sender actually moves, so the agreement is not 0 == 0.
    assert max(float(one.abs().max()) for one in forward.values()) > 1e-3


@pytest.mark.parametrize("source", ["T", "Dq"])
def test_the_joint_swap_equals_a_forward_with_every_outside_sender_replaced(model, pair, dq,
                                                                             source):
    from component_analysis import hooks

    x_outputs = pair.t.outputs if source == "T" else dq.outputs
    grid = [("head", 0, 0), ("mlp", 0, 0)]
    senders = outside(model, grid)
    # Every sender written: the outside ones from X, the grid, quartet and embedding
    # frozen at D.
    replacements = {key: pair.d.outputs[key] for key in hooks.all_component_keys(model)}
    replacements.update({key: x_outputs[key] for key in senders})
    capture = hooks.capture_forward(model, pair.d.input_ids, pair.d.attention_mask,
                                    components=[hooks.READOUT_KEY], positions=pair.readout,
                                    replacements=replacements)
    direct = pair.d.margin - rc._margin(model, capture, pair.target, pair.distractor)
    assert float(direct.abs().max()) > 1e-3
    joint = rc.forward_joint(model, pair, x_outputs, senders)
    assert torch.allclose(joint, direct, atol=1e-6)
    offline = rc.offline_direct_effects(model, pair, x_outputs, senders, joint=senders)
    assert torch.allclose(offline.joint, direct, atol=1e-3)
    if source == "T":
        # The joint swap is not the sum of the single swaps (the final norm). Under D_q
        # only mlp.1 moves on this 2-layer model, so only the twin shows it.
        single = rc.forward_sweep(model, pair, x_outputs, senders)
        assert not torch.allclose(sum(single.values()), joint, atol=1e-6)


def test_c3_delta_moves_the_fixed_scale_lens_exactly_as_the_quartet_restoration(model, pair,
                                                                                   dq):
    push = rc.solve_push(model, pair, dq.residual, layer=LAYER)
    scale = pair.d.residual[:, LAYER + 1]
    before = rc.lens_margin(model, scale, scale, pair.target, pair.distractor)
    after_dq = rc.lens_margin(model, dq.residual[:, LAYER + 1], scale, pair.target,
                              pair.distractor)
    assert torch.allclose(push.target_change, after_dq - before, atol=1e-6)
    assert float(push.target_change.abs().min()) > 1e-3
    assert torch.allclose(push.direction.norm(dim=-1), torch.ones(3), atol=1e-6)
    bank = rc.direction_push_bank(pair, push, layer=LAYER)
    result = rc.run_arm(model, pair, bank, capture_keys=[("mlp", LAYER, 0)])
    achieved = rc.lens_margin(model, result.residual[:, LAYER + 1], scale, pair.target,
                              pair.distractor) - before
    assert torch.allclose(achieved, push.target_change, atol=1e-4)
    # The push is written at the Readout and nowhere else.
    written = result.outputs[("mlp", LAYER, 0)] - pair.d.outputs[("mlp", LAYER, 0)]
    moved = written.abs().amax(-1) > 0
    assert torch.equal(moved, pair.masks["readout"].cpu())


def test_the_quartet_path_patching_writes_the_sender_only_at_its_mask(model, pair):
    from component_analysis import path_patching as pp

    writers = [("mlp", LAYER, 0)]
    out = rc.quartet_path_patching(model, pair, QUARTET_KEYS, writers,
                                   kv_group_of=lambda h: h // 2)
    assert set(out) == set(rc.PP_SENDER_MASKS)
    # The Readout-only sender reaches the MLP input at the Readout exactly as a
    # two-pass patch with the quartet written there and nowhere else.
    streams = rc.sweep_streams(model, pair, pair.t.outputs)
    captured = pp.receiver_inputs(model, streams, senders=QUARTET_KEYS,
                                  receivers=[("mlp_in", LAYER, 0)],
                                  sender_positions=pair.masks["readout"])
    from component_analysis import hooks
    replacement = hooks.Replacement(captured.outputs[("mlp_in", LAYER, 0)],
                                    pair.masks["readout"])
    logits = pp.readout_from_receivers(model, streams, {("mlp_in", LAYER, 0): replacement})
    want = pair.d.margin - hooks.target_minus_distractor(logits, pair.target, pair.distractor)
    assert torch.allclose(out["readout"]["writers"]["mlp.1.0"], want, atol=1e-6)
    # Restricted to the pre-Readout positions, the quartet cannot reach the Readout's
    # MLP input directly: attention at layer 1 mixes positions, but the quartet's own
    # output at the Readout is clean there, and the MLP is position-wise.
    assert torch.allclose(out["post_clause_no_readout"]["writers"]["mlp.1.0"],
                          torch.zeros(3), atol=1e-6)


# ==============================================================================
# run() ON THE STUB CONTEXT
# ==============================================================================

def run_t1(model, tmp_path, *argv):
    batch, _twin, _mask = twin_batch()
    segmentations = list(segmentations_by_id(batch).values())
    ctx = StubContext(model, tmp_path, ListBatches([batch]), segmentations,
                      argv=["--route-c2-layers", "0-0", "--route-pp-top", "4",
                            "--route-pp-feeders", "head.0.1,mlp.0.0,head.14.4", *argv])
    ctx.components = [type("C", (), {"key": ("head", 0, 0)})(),
                      type("C", (), {"key": ("head", 1, 2)})(),
                      type("C", (), {"key": ("head", 1, 3)})()]
    assert rc.run(ctx) == {}
    return json.load(open(os.path.join(tmp_path, rc.SUBDIR, rc.JSON_FILE))), ctx


def test_run_writes_the_sweeps_controls_and_path_patching(model, tmp_path):
    payload, _ctx = run_t1(model, tmp_path)
    sweeps = payload["t1"]["sweeps"]
    assert sweeps["status"] == "computed"
    assert sweeps["normalized_by"].startswith("mean G")
    names = sweeps["outside"]["keys"]
    assert "head.0.0" not in names and "embed.0.0" not in names
    assert "head.1.2" not in names and "head.1.3" not in names
    assert len(names) == 2 * 4 + 2 - 3
    assert set(sweeps["forward"]) == {"T", "dq_all"}
    assert {"T", "dq_all", "dq_readout", "dq_post_clause_no_readout", "c1_d0", "c1_d1",
            "c2_d0", "c2_d1", "c3_push"} <= set(sweeps["offline"])
    forward_t = sweeps["forward"]["T"]
    assert forward_t["O"] == pytest.approx(
        sum(one["e"] for one in forward_t["senders"].values() if one["in_sum"]), abs=1e-6)
    gate = payload["gates"]["g3"]
    assert gate["passed"] is True
    assert gate["max_sender_diff"] < 1e-3 and gate["max_sum_diff"] < 1e-3
    summary = payload["t1"]["summary"]
    assert summary["M_q"] == pytest.approx(
        sweeps["forward"]["dq_all"]["O"] / sweeps["forward"]["T"]["O"])
    assert summary["rule_estimator"] == "forward"
    assert set(summary["M_C1"]) == {"c1_d0", "c1_d1"}
    c3 = sweeps["c3"]
    assert c3["max_abs_miss"] < 1e-4
    assert len(c3["delta"]) == 3
    assert payload["arms"]["c3_push"]["test"] == "t1"
    assert len(payload["arms"]["c1_d0"]["margins"]) == 3
    # The ticket-4 fields are still there, unchanged.
    for name in ("g1_empty", "dq_all", "q_readout", "k_options"):
        assert name in payload["arms"]
    assert payload["gates"]["g1_bit_identical"] is True

    pp_out = payload["t1"]["path_patching"]
    assert pp_out["status"] == "computed"
    writers = pp_out["plan_1_5"]["writers"]
    assert len(writers) == 4
    assert set(pp_out["plan_1_5"]["effects"]) == set(rc.PP_SENDER_MASKS)
    feeders = pp_out["plan_2_3"]
    assert feeders["skipped_senders"] == ["head.14.4"]
    assert [one["name"] for one in feeders["senders"]] == ["head.0.1", "mlp.0.0", "layer.0"]
    first = payload["positions"]["first_batch"]["masks"]
    assert first["post_clause_no_readout"]["tokens"][0][0] == CLAUSE[1]


def test_run_with_the_forward_sweep_alone_says_the_controls_need_the_offline_estimator(
        model, tmp_path):
    payload, _ctx = run_t1(model, tmp_path, "--route-sweep", "forward",
                           "--route-path-patching", "off")
    sweeps = payload["t1"]["sweeps"]
    assert set(sweeps["forward"]) == {"T", "dq_all"}
    assert sweeps["offline"] == {}
    assert "offline" in sweeps["controls_status"]
    assert "c1_d0" not in payload["arms"]
    assert payload["t1"]["path_patching"]["status"].startswith("off")
    assert payload["gates"]["g3"]["passed"] is None


def test_run_without_t1_writes_no_sweep(model, tmp_path):
    payload, _ctx = run_t1(model, tmp_path, "--route-tests", "t2")
    assert payload["t1"]["sweeps"]["status"].startswith("not selected")
    assert "dq_all" not in payload["arms"]


def test_run_restores_the_deciding_set_post_clause_and_keeps_intervened_sites_out_of_o(
        model, tmp_path):
    groups = tmp_path / "groups.json"
    groups.write_text(json.dumps({"greedy_k20": [["head", 0, 1], ["mlp", 0, 0]]}))
    payload, _ctx = run_t1(model, tmp_path, "--route-deciding-set",
                           f"{groups}:greedy_k20", "--route-path-patching", "off")
    sweeps = payload["t1"]["sweeps"]
    assert payload["arms"]["s_k"]["writes"] == [
        {"site": "head.0.1", "positions": "post_clause"},
        {"site": "mlp.0.0", "positions": "post_clause"}]
    s_k = sweeps["offline"]["s_k"]
    assert s_k["intervened"] == ["head.0.1", "mlp.0.0"]
    assert s_k["senders"]["head.0.1"]["in_sum"] is False
    assert s_k["senders"]["mlp.1.0"]["in_sum"] is True
    assert payload["t1"]["summary"]["M_S"] == pytest.approx(
        s_k["O"] / sweeps["offline"]["T"]["O"])
    # C2 draws avoid the deciding set; the C3 push site is not summed into O_C3.
    for draw in sweeps["c2_draws"]:
        assert "head.0.1" not in draw and "head.0.0" not in draw
    assert sweeps["offline"]["c3_push"]["senders"]["mlp.1.0"]["in_sum"] is False
    assert sweeps["offline"]["dq_all"]["senders"]["mlp.1.0"]["in_sum"] is True
    # The twin's own O: every outside sender is summed.
    assert sweeps["offline"]["T"]["n_in_sum"] == sweeps["outside"]["n"]


def test_run_with_the_offline_sweep_alone_ranks_and_reads_on_the_offline_estimator(
        model, tmp_path):
    payload, _ctx = run_t1(model, tmp_path, "--route-sweep", "offline")
    sweeps = payload["t1"]["sweeps"]
    assert sweeps["forward"] == {}
    assert "c3_push" in sweeps["offline"] and "c1_d0" in payload["arms"]
    assert payload["t1"]["summary"]["rule_estimator"] == "offline"
    assert payload["t1"]["summary"]["M_q"] == pytest.approx(
        sweeps["offline"]["dq_all"]["O"] / sweeps["offline"]["T"]["O"])
    assert payload["gates"]["g3"]["passed"] is None
    plan = payload["t1"]["path_patching"]["plan_1_5"]
    assert plan["ranked_by"] == "|e_s(T)|, offline estimator"
    ranked = sorted(sweeps["outside"]["keys"],
                    key=lambda name: -abs(sweeps["offline"]["T"]["senders"][name]["e"]))
    assert [row["sender"] for row in plan["writers"]] == ranked[:4]


def test_the_readings_script_reads_what_run_writes(model, tmp_path):
    from tests.test_route_closure_readings import load_script

    rr = load_script()
    payload, _ctx = run_t1(model, tmp_path, "--route-path-patching", "off")
    readings = rr.read_task(payload, n_resamples=20, seed=1)
    summary = payload["t1"]["summary"]
    assert readings["t1"]["rule_estimator"] == "forward"
    assert readings["t1"]["M_q"]["point"] == pytest.approx(summary["M_q"], rel=1e-9)
    assert readings["t1"]["O"]["point"] == pytest.approx(summary["O"], rel=1e-9)
    assert readings["t1"]["r_q"]["point"] == pytest.approx(summary["r_q"], rel=1e-6)
    assert readings["t1"]["controls"]["M_C3"]["point"] == pytest.approx(summary["M_C3"],
                                                                         rel=1e-9)
    assert set(readings["t1"]["controls"]["M_C1"]) == set(summary["M_C1"])
    assert readings["t1"]["M_q_offline"] == pytest.approx(summary["M_q_offline"], rel=1e-9)
    assert readings["t2"]["r_Q"]["point"] == pytest.approx(rr.arm_share(payload, "q_readout"))
    assert readings["t2"]["verdict"] is not None


def test_the_estimate_counts_the_sweep_and_path_patching_forwards(tmp_path):
    batch, _twin, _mask = twin_batch()
    loader = ListBatches([batch, batch])
    loader.report = {"batch_size": 3, "n_with_neutral_twin": 6}
    ctx = StubContext(None, tmp_path, loader, [])
    ctx.cli.route_quartet = rc.DEFAULT_QUARTET
    ctx.intake = type("I", (), {"geometry": {"num_heads": 32, "num_layers": 32}})()
    line = rc.estimate(ctx)
    n_outside = 32 * 33 - 4
    assert f"{n_outside} outside sender(s)" in line
    sweep, paths = rc._t1_forwards(ctx, n_outside=n_outside, n_kv=8, num_layers=32,
                                   num_heads=32, draws=2)
    # forward: 2 sweeps + 2 joint swaps; offline: 2 C1 + 2 C2 draws + C3 (no deciding set)
    assert sweep == 2 * n_outside + 2 + 2 + 2 + 1
    # 2 recaptures, 3 sender masks x (pass 1 + 20 writers + joint), 3 x (5 feeders + 17 layers)
    assert paths == 2 + 3 * 22 + 3 * 22
    assert f"plus {2 * sweep} T1 sweep and control forward(s)" in line
    assert f"{2 * paths} path-patching forward(s)" in line
    ctx.cli.route_path_patching = "off"
    ctx.cli.route_sweep = "forward"
    assert rc._t1_forwards(ctx, n_outside=n_outside, n_kv=8, num_layers=32, num_heads=32,
                           draws=2) == (2 * n_outside + 2, 0)
