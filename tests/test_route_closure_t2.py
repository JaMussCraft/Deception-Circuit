"""
route_closure, the core and the T2 arms (B1 plan, ticket 4).

The pure tests (flags, files, control draws, masks on hand-built Segments)
run in both environments. The model tests run the tiny 2-layer GQA Llama
under nnsight 0.7.0 and skip otherwise, as the path-patching tests do.

The tiny model has 4 heads in 2 KV groups, so its "quartet" is the 2 heads of
one group: layer 1, heads 2 and 3, KV group 1. On Llama-3.1-8B the same code
is run with layer 17, heads 24 to 27, KV group 6.
"""

from __future__ import annotations

import argparse
import json
import os

import pytest
import torch

from component_analysis import dataloaders
from component_analysis import route_closure as rc
from component_analysis.segmentation import Segment, Segmentation
from tests.helpers import TINY, tiny_config

SEQ = 24
BATCH = 3
CLAUSE = (7, 11)
LAYER = 1
QUARTET = (2, 3)
GROUP = 1
OPTION_TOKENS = [13, 15, 17, 18]
PRECLAUSE_MENTIONS = [2, 3, 5]
LENGTHS = (SEQ, SEQ, SEQ - 2)


# ==============================================================================
# A HAND-BUILT TWIN BATCH WITH mechanism_v2 SEGMENTS
# ==============================================================================

def segmentation_for(record_id: str, n: int, *, drop=()):
    spans = {
        "intro": ((0, 2),),
        "item_1_intro": ((2, 3),),
        "item_2_intro": ((3, 4),),
        "designating_sentence": ((4, 5), (6, 7)),
        "designation_site": ((5, 6),),
        "pressure_clause": (CLAUSE,),
        "question": ((11, 13), (14, 15)),
        "item_1_question_pair": ((13, 14),),
        "item_2_question_pair": ((15, 16),),
        "response_line": ((16, 17),),
        "item_1_question_option": ((17, 18),),
        "item_2_question_option": ((18, 19),),
        "stem": ((19, n - 1),),
        "readout": ((n - 1, n),),
    }
    return Segmentation(
        task="far_v2", record_id=record_id, n_tokens=n, readout=n - 1,
        scheme="mechanism_v2",
        segments={name: Segment(name, () if name in drop else span)
                  for name, span in spans.items()})


def twin_batch(*, with_twin=True, twin_rows=(0, 1, 2)):
    """D and its token-aligned twin, which differ inside `CLAUSE` only."""
    torch.manual_seed(2)
    clean = torch.randint(2, TINY["vocab"], (BATCH, SEQ))
    corrupt = clean.clone()
    corrupt[:, 3] = (clean[:, 3] + 7) % TINY["vocab"]
    twin = clean.clone()
    twin[:, CLAUSE[0]:CLAUSE[1]] = (clean[:, CLAUSE[0]:CLAUSE[1]] + 11) % TINY["vocab"]
    mask = torch.ones_like(clean)
    for row, n in enumerate(LENGTHS):
        mask[row, n:] = 0
    readout = mask.sum(-1) - 1
    pair = None
    if with_twin:
        rows = list(twin_rows)
        pair = dataloaders.NeutralTwinPair(
            rows=rows, input_ids=twin[rows], attention_mask=mask[rows].clone(),
            corrupt_input_ids=twin[rows].clone(),
            corrupt_attention_mask=mask[rows].clone(),
            clause_span=torch.tensor([list(CLAUSE)] * len(rows)))
    batch = dataloaders.Batch(
        ids=[f"tiny_{n}" for n in range(BATCH)],
        records=[{"pressure_id": f"p{n % 2}"} for n in range(BATCH)],
        input_ids=clean, attention_mask=mask, corrupt_input_ids=corrupt,
        corrupt_attention_mask=mask, target_token=torch.tensor([5, 6, 7]),
        distractor_token=torch.tensor([8, 9, 10]), readout=readout, honest=None,
        neutral_twin=pair)
    return batch, twin, mask


def segmentations_by_id(batch, **kwargs):
    return {one: segmentation_for(one, int(batch.attention_mask[row].sum()), **kwargs)
            for row, one in enumerate(batch.ids)}


# ==============================================================================
# FLAGS, REGISTRATION, FILES (no model)
# ==============================================================================

def parser():
    out = argparse.ArgumentParser()
    rc.add_arguments(out.add_argument_group("route_closure"))
    return out


def test_the_flags_parse_with_the_plan_defaults():
    cli = parser().parse_args([])
    assert cli.route_tests == "both"
    assert cli.route_direction == "both"
    assert cli.route_sweep == "both"
    assert cli.route_control_draws == 5
    assert cli.route_control_seed == 20261101
    assert cli.route_ct is None and cli.route_deciding_set is None
    assert cli.route_pp_top == 20
    assert rc.parse_quartet(cli.route_quartet) == (17, (24, 25, 26, 27))
    cli = parser().parse_args(["--route-tests", "t2", "--route-direction", "reverse",
                               "--route-deciding-set", "a/b.json:greedy_k20",
                               "--route-quartet", "1:2,3"])
    assert cli.route_tests == "t2" and cli.route_direction == "reverse"
    assert cli.route_deciding_set == ("a/b.json", "greedy_k20")
    assert rc.parse_quartet(cli.route_quartet) == (1, (2, 3))
    assert rc.parse_quartet("17:27,26,25,24") == (17, (24, 25, 26, 27))
    with pytest.raises(SystemExit):
        parser().parse_args(["--route-tests", "t3"])
    with pytest.raises(SystemExit):
        parser().parse_args(["--route-deciding-set", "no_name.json"])


def test_route_closure_is_registered_and_its_flags_are_in_the_cli_help():
    import analyze_components
    from component_analysis import registry

    assert "component_analysis.route_closure" in registry.ANALYSES
    assert "route_closure" in registry.names()
    text = analyze_components.build_parser().format_help()
    for flag in ("--route-tests", "--route-direction", "--route-sweep",
                 "--route-control-draws", "--route-control-seed", "--route-ct",
                 "--route-deciding-set", "--route-pp-top", "--route-quartet"):
        assert flag in text


def test_the_module_does_not_import_nnsight_at_module_level():
    source = open(rc.__file__).read()
    header = source.split("\ndef ", 1)[0]
    assert "import nnsight" not in header
    assert "from component_analysis import hooks" not in header


def test_the_ct_file_is_read_per_task_without_the_v2_suffix(tmp_path):
    path = tmp_path / "ct.json"
    path.write_text(json.dumps({"tasks": {
        "far": {"members": {"C_t": ["head.17.24", "head.17.3", "mlp.4.0"]}}}}))
    assert rc.load_ct(str(path), "far_v2") == {("head", 17, 24), ("head", 17, 3),
                                               ("mlp", 4, 0)}
    with pytest.raises(ValueError, match="ser"):
        rc.load_ct(str(path), "ser_v2")


def test_the_deciding_set_is_read_by_name(tmp_path):
    path = tmp_path / "groups.json"
    path.write_text(json.dumps({"greedy_k20": [["head", 9, 29], ["mlp", 6, 0]]}))
    assert rc.load_deciding_set((str(path), "greedy_k20")) == [("head", 9, 29),
                                                               ("mlp", 6, 0)]
    with pytest.raises(ValueError, match="nosuch"):
        rc.load_deciding_set((str(path), "nosuch"))


def test_the_estimate_counts_forwards_and_says_when_a_cell_has_no_twin(tmp_path):
    """`--dry-run` runs this on the login node: no model, no nnsight."""
    batch, _twin, _mask = twin_batch()
    loader = ListBatches([batch, batch])
    loader.report = {"batch_size": BATCH, "n_with_neutral_twin": 6}
    ctx = StubContext(None, tmp_path, loader, [])
    ctx.cli.route_quartet = rc.DEFAULT_QUARTET
    ctx.intake = type("I", (), {"geometry": {"num_heads": 32}})()
    line = rc.estimate(ctx)
    n_arms = len(rc.build_arms(layer=17, quartet=QUARTET_8B, kv_group=6, num_kv_heads=8,
                               tests=("t1", "t2"), directions=("restore", "reverse"),
                               head_draws=[[0, 1, 2, 3]] * 2, n_position_draws=2))
    assert f"{n_arms} arm(s)" in line
    assert f"{2 * (2 + n_arms)} forward(s)" in line
    loader.report = {"batch_size": BATCH, "n_with_neutral_twin": 0}
    assert rc.estimate(ctx).startswith("not applicable")


# ==============================================================================
# CONTROL DRAWS (no model)
# ==============================================================================

QUARTET_8B = (24, 25, 26, 27)
CT_8B = {("head", 17, 0), ("head", 17, 5), ("head", 17, 31), ("head", 16, 1),
         ("mlp", 17, 0)}


def test_head_draws_are_seeded_reproducible_and_disjoint_from_the_quartet_and_ct():
    first = rc.draw_control_heads(num_heads=32, layer=17, quartet=QUARTET_8B,
                                  excluded=CT_8B, n_draws=5, size=4, seed=20261101)
    again = rc.draw_control_heads(num_heads=32, layer=17, quartet=QUARTET_8B,
                                  excluded=CT_8B, n_draws=5, size=4, seed=20261101)
    other = rc.draw_control_heads(num_heads=32, layer=17, quartet=QUARTET_8B,
                                  excluded=CT_8B, n_draws=5, size=4, seed=7)
    assert first == again
    assert first != other
    assert len(first) == 5
    forbidden = set(QUARTET_8B) | {0, 5, 31}
    for draw in first:
        assert len(draw) == 4 and len(set(draw)) == 4
        assert not set(draw) & forbidden
        assert all(0 <= one < 32 for one in draw)


def test_a_head_pool_smaller_than_a_draw_is_refused():
    with pytest.raises(ValueError, match="layer 17"):
        rc.draw_control_heads(num_heads=6, layer=17, quartet=(2, 3, 4, 5),
                              excluded=set(), n_draws=5, size=4, seed=1)


def test_position_draws_are_per_instance_reproducible_and_avoid_options_and_readout():
    batch, _twin, _mask = twin_batch()
    by_id = segmentations_by_id(batch)
    ids = list(batch.ids)
    masks = rc.position_masks(ids, [by_id[one] for one in ids], batch.readout, SEQ)
    drawn = rc.draw_control_positions(ids, masks, n_draws=5, size=4, seed=20261101)
    # The same instances in the other order give each instance the same tokens.
    order = [2, 0, 1]
    swapped = rc.position_masks([ids[r] for r in order],
                                [by_id[ids[r]] for r in order],
                                batch.readout[order], SEQ)
    drawn_swapped = rc.draw_control_positions([ids[r] for r in order], swapped,
                                              n_draws=5, size=4, seed=20261101)
    for draw in range(5):
        for row, one in enumerate(ids):
            tokens = drawn["tokens"][draw][row]
            assert tokens == drawn_swapped["tokens"][draw][order.index(row)]
            assert len(tokens) == 4 and len(set(tokens)) == 4
            readout = int(batch.readout[row])
            assert all(CLAUSE[1] <= t < readout for t in tokens)
            assert not set(tokens) & set(OPTION_TOKENS)
            assert torch.equal(drawn["masks"][draw][row].nonzero().flatten(),
                               torch.tensor(sorted(tokens)))
    assert drawn["tokens"][0] != drawn["tokens"][1] or drawn["tokens"][1] != drawn["tokens"][2]


# ==============================================================================
# POSITION MASKS (no model)
# ==============================================================================

def test_the_option_mask_is_exactly_the_four_option_segments():
    batch, _twin, _mask = twin_batch()
    by_id = segmentations_by_id(batch)
    ids = list(batch.ids)
    masks = rc.position_masks(ids, [by_id[one] for one in ids], batch.readout, SEQ)
    for row in range(BATCH):
        options = masks["options"][row].nonzero().flatten().tolist()
        assert options == OPTION_TOKENS
        assert not set(options) & set(PRECLAUSE_MENTIONS)
        assert masks["preclause_mentions"][row].nonzero().flatten().tolist() == \
            PRECLAUSE_MENTIONS
        assert masks["readout"][row].nonzero().flatten().tolist() == \
            [int(batch.readout[row])]
        assert masks["clause"][row].nonzero().flatten().tolist() == list(range(*CLAUSE))
        post = masks["post_clause"][row].nonzero().flatten().tolist()
        assert post == list(range(CLAUSE[1], int(batch.readout[row]) + 1))
        assert masks["post_clause_no_readout"][row].nonzero().flatten().tolist() == post[:-1]


def test_an_absent_option_segment_is_refused_by_name():
    batch, _twin, _mask = twin_batch()
    by_id = segmentations_by_id(batch, drop=("item_2_question_option",))
    ids = list(batch.ids)
    with pytest.raises(ValueError, match="item_2_question_option"):
        rc.position_masks(ids, [by_id[one] for one in ids], batch.readout, SEQ)


def test_the_arm_lists_name_the_rule_arms_and_the_controls():
    arms = rc.build_arms(layer=17, quartet=QUARTET_8B, kv_group=6, num_kv_heads=8,
                         tests=("t1", "t2"), directions=("restore", "reverse"),
                         head_draws=[[0, 1, 2, 3]] * 5, n_position_draws=5)
    names = [arm.name for arm in arms]
    assert len(names) == len(set(names))
    by_name = {arm.name: arm for arm in arms}
    assert by_name["q_readout"].writes == tuple((("q", 17, h), "readout") for h in QUARTET_8B)
    assert by_name["k_options"].writes == ((("k", 17, 6), "options"),)
    assert by_name["q_readout"].role == by_name["k_options"].role == "rule"
    assert by_name["out_readout"].writes == tuple((("head", 17, h), "readout")
                                                  for h in QUARTET_8B)
    assert by_name["dq_all"].writes == tuple((("head", 17, h), "all") for h in QUARTET_8B)
    assert by_name["rev_k_options"].base == "T"
    assert by_name["tq_all"].base == "T"
    groups = sorted(arm.meta["kv_group"] for arm in arms
                    if arm.name.startswith("ctrl_k_options_g"))
    assert groups == [0, 1, 2, 3, 4, 5, 7]
    assert len([one for one in names if one.startswith("ctrl_q_readout_d")]) == 5
    assert len([one for one in names if one.startswith("ctrl_k_random_post_d")]) == 5
    assert names[:2] == ["g1_empty", "g2_all_components"]
    only_t2 = [arm.name for arm in rc.build_arms(
        layer=17, quartet=QUARTET_8B, kv_group=6, num_kv_heads=8, tests=("t2",),
        directions=("restore",), head_draws=[[0, 1, 2, 3]] * 5, n_position_draws=5)]
    assert "dq_all" not in only_t2 and "rev_q_readout" not in only_t2


# ==============================================================================
# THROUGH THE MODEL (nnsight 0.7.0)
# ==============================================================================

def nnsight_model():
    nnsight = pytest.importorskip("nnsight")
    if nnsight.__version__ != "0.7.0":
        pytest.skip("patched forwards are a nnsight 0.7.0 behaviour")
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())


@pytest.fixture(scope="module")
def model():
    return nnsight_model()


@pytest.fixture(scope="module")
def pair(model):
    batch, _twin, _mask = twin_batch()
    return rc.capture_pair(model, batch, segmentations_by_id(batch))


def test_the_pair_holds_both_streams_and_the_twin_gap(model, pair):
    from component_analysis import hooks

    assert pair.ids == ["tiny_0", "tiny_1", "tiny_2"]
    assert pair.pressure_ids == ["p0", "p1", "p0"]
    for key in hooks.all_component_keys(model) + hooks.all_receiver_keys(model):
        assert key in pair.d.outputs and key in pair.t.outputs
    assert torch.equal(pair.gap, pair.d.margin - pair.t.margin)
    assert pair.d.margin.dtype == torch.float32
    assert not torch.allclose(pair.d.margin, pair.t.margin, atol=1e-4)


def test_g1_an_empty_bank_reproduces_the_pressure_margin_bit_identically(model, pair):
    result = rc.run_arm(model, pair, {})
    assert torch.equal(result.margins, pair.d.margin)


def test_g2_restoring_every_component_reproduces_the_twin_margin(model, pair):
    from component_analysis import hooks

    keys = hooks.all_component_keys(model)
    assert hooks.EMBED_KEY in keys
    bank = rc.restore_bank(pair.t, keys, None)
    result = rc.run_arm(model, pair, bank)
    assert torch.allclose(result.margins, pair.t.margin, atol=1e-5, rtol=0)
    # And the reverse direction: the twin prompt with everything from D is D.
    back = rc.run_arm(model, pair, rc.restore_bank(pair.d, keys, None), base="T")
    assert torch.allclose(back.margins, pair.d.margin, atol=1e-5, rtol=0)


def test_a_k_group_write_touches_only_that_groups_heads(model, pair):
    from component_analysis import hooks

    heads = hooks.heads_of_kv_group(model, GROUP)
    assert tuple(heads) == QUARTET
    masks = pair.masks
    for mask in (None, masks["options"]):
        bank = rc.restore_bank(pair.t, [("k", LAYER, GROUP)], mask)
        capture_keys = [("head", layer, h) for layer in range(TINY["layers"])
                        for h in range(TINY["heads"])]
        result = rc.run_arm(model, pair, bank, capture_keys=capture_keys)
        for layer in range(TINY["layers"]):
            for h in range(TINY["heads"]):
                got = result.outputs[("head", layer, h)]
                want = pair.d.outputs[("head", layer, h)]
                if layer == LAYER and h in heads:
                    assert not torch.equal(got, want), (layer, h)
                else:
                    assert torch.equal(got, want), (layer, h)
        if mask is not None:
            # Keys at the options reach no query before the first option.
            first = min(OPTION_TOKENS)
            for h in heads:
                assert torch.equal(result.outputs[("head", LAYER, h)][:, :first],
                                   pair.d.outputs[("head", LAYER, h)][:, :first])


def test_the_preclause_mentions_are_an_exact_zero(model, pair):
    bank = rc.restore_bank(pair.t, [("k", LAYER, GROUP), ("v", LAYER, GROUP)],
                           pair.masks["preclause_mentions"])
    assert torch.equal(rc.run_arm(model, pair, bank).margins, pair.d.margin)


def test_the_rule_arms_move_the_margin(model, pair):
    q = rc.run_arm(model, pair, rc.restore_bank(
        pair.t, [("q", LAYER, h) for h in QUARTET], pair.masks["readout"]))
    k = rc.run_arm(model, pair, rc.restore_bank(
        pair.t, [("k", LAYER, GROUP)], pair.masks["options"]))
    assert not torch.equal(q.margins, pair.d.margin)
    assert not torch.equal(k.margins, pair.d.margin)


def test_a_misaligned_twin_is_refused(model):
    batch, _twin, _mask = twin_batch()
    batch.neutral_twin.input_ids[0, 1] = (batch.neutral_twin.input_ids[0, 1] + 1) % 50
    with pytest.raises(ValueError, match="outside the Pressure Clause"):
        rc.capture_pair(model, batch, segmentations_by_id(batch))


def test_a_batch_without_a_twin_gives_no_pair(model):
    batch, _twin, _mask = twin_batch(with_twin=False)
    assert rc.capture_pair(model, batch, segmentations_by_id(batch)) is None


# ==============================================================================
# run() ON A STUB CONTEXT
# ==============================================================================

class StubContext:
    def __init__(self, model, cell_dir, batches, segmentations, argv=()):
        self.model = model
        self.cell_dir = str(cell_dir)
        cli = parser().parse_args(["--route-quartet", f"{LAYER}:2,3",
                                   "--route-control-draws", "2", *argv])
        self.cli = cli
        self.circuit_spec = type("S", (), {"label": "tiny"})()
        self.task_spec = type("T", (), {"name": "far_v2"})()
        self.components = []
        self._batches = batches
        self.segmentations = segmentations
        self.declared = []

    def causal_batches(self):
        return self._batches

    def subdir(self, analysis):
        name = analysis if isinstance(analysis, str) else analysis.SUBDIR
        path = os.path.join(self.cell_dir, name)
        os.makedirs(path, exist_ok=True)
        return path

    def write_json(self, analysis, filename, payload):
        path = os.path.join(self.subdir(analysis), filename)
        with open(path, "w") as handle:
            json.dump(payload, handle, indent=2)
        return path

    def declare_coverage(self, columns, *, instance_ids, instance_set, **extra):
        self.declared.append((list(columns), list(instance_ids), instance_set))


class ListBatches(list):
    """A list of batches with the two attributes `run` reads off a loader."""

    report = {"batch_size": BATCH}

    @property
    def n_instances(self):
        return sum(len(one) for one in self)


def test_run_writes_the_schema_with_per_instance_margins_for_every_arm(model, tmp_path):
    batch, _twin, _mask = twin_batch(twin_rows=(0, 1))
    segmentations = list(segmentations_by_id(batch).values())
    ctx = StubContext(model, tmp_path, ListBatches([batch]), segmentations)
    updates = rc.run(ctx)
    assert updates == {}

    payload = json.load(open(os.path.join(tmp_path, rc.SUBDIR, rc.JSON_FILE)))
    assert payload["schema"] == rc.SCHEMA
    assert payload["task"] == "far_v2"
    assert payload["quartet"] == {"layer": LAYER, "heads": list(QUARTET),
                                  "kv_group": GROUP}
    assert payload["instances"]["ids"] == ["tiny_0", "tiny_1"]
    assert payload["instances"]["pressure_ids"] == ["p0", "p1"]
    assert payload["instances"]["without_twin"] == ["tiny_2"]
    baseline = payload["baseline"]
    for name in ("m_D", "m_T", "G"):
        assert len(baseline[name]) == 2
    assert baseline["mean_m_D"] == pytest.approx(sum(baseline["m_D"]) / 2)
    assert baseline["P"] == pytest.approx(baseline["mean_m_D"] - baseline["mean_m_T"])

    arms = payload["arms"]
    for name in ("g1_empty", "g2_all_components", "q_readout", "k_options",
                 "v_options", "kv_options", "qk", "k_post_clause", "k_clause",
                 "q_post_clause", "out_readout", "kv_preclause_mentions",
                 "rev_q_readout", "rev_k_options", "dq_all", "dq_readout",
                 "dq_post_clause_no_readout", "tq_all",
                 "ctrl_q_readout_d0", "ctrl_q_readout_d1", "ctrl_k_options_g0",
                 "ctrl_k_random_post_d0", "ctrl_k_random_post_d1"):
        assert name in arms, name
        assert len(arms[name]["margins"]) == 2
        assert arms[name]["mean"] == pytest.approx(sum(arms[name]["margins"]) / 2)
    assert arms["g1_empty"]["margins"] == baseline["m_D"]
    assert payload["gates"]["g1_bit_identical"] is True
    assert payload["gates"]["g2_max_abs_diff"] < 1e-5
    assert arms["kv_preclause_mentions"]["margins"] == baseline["m_D"]
    assert arms["k_options"]["writes"] == [{"site": "k.1.1", "positions": "options"}]
    assert arms["ctrl_q_readout_d0"]["meta"]["heads"] == [0, 1]
    assert payload["controls"]["q_heads"] == [[0, 1], [0, 1]]

    first = payload["positions"]["first_batch"]
    assert first["ids"] == ["tiny_0", "tiny_1"]
    assert first["masks"]["options"]["segments"] == list(rc.OPTION_SEGMENTS)
    assert first["masks"]["options"]["tokens"] == [OPTION_TOKENS, OPTION_TOKENS]
    assert len(first["masks"]["random_post_d0"]["tokens"][0]) == 4
    assert payload["t1"]["sweeps"]["status"] == "computed"      # ticket 5
    assert ctx.declared and ctx.declared[0][1] == ["tiny_0", "tiny_1"]


def test_run_on_a_cell_without_a_twin_writes_the_skipped_file(model, tmp_path):
    batch, _twin, _mask = twin_batch(with_twin=False)
    segmentations = list(segmentations_by_id(batch).values())
    ctx = StubContext(model, tmp_path, ListBatches([batch]), segmentations)
    assert rc.run(ctx) == {}
    payload = json.load(open(os.path.join(tmp_path, rc.SUBDIR, rc.JSON_FILE)))
    assert "skipped" in payload
    assert payload["instances"]["without_twin"] == ["tiny_0", "tiny_1", "tiny_2"]
    assert payload["arms"] == {}


def test_a_v1_cell_is_skipped_before_the_quartet_is_checked(model, tmp_path):
    """A default run (no --analyses) reaches route_closure on every cell; a v1 cell has no
    twin, so it must write the skipped file rather than refuse the 8B quartet on this model."""
    batch, _twin, _mask = twin_batch(with_twin=False)
    segmentations = list(segmentations_by_id(batch).values())
    ctx = StubContext(model, tmp_path, ListBatches([batch]), segmentations)
    ctx.cli.route_quartet = rc.DEFAULT_QUARTET
    ctx.task_spec = type("T", (), {"name": "far"})()
    assert rc.run(ctx) == {}
    payload = json.load(open(os.path.join(tmp_path, rc.SUBDIR, rc.JSON_FILE)))
    assert "skipped" in payload and payload["arms"] == {}
