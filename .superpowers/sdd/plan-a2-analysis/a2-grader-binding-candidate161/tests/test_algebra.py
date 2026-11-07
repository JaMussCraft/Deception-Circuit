"""Set algebra over saved node circuits — parser, compose, hierarchy validity.

Pure CPU: no model, no tokenizer, no CUDA.
"""

import numpy as np
import pytest

from evaluation import algebra as A
from evaluation.masks import FINEST_KEYS, count_masks, validate_hierarchy

N_LAYERS = 3
NUM_HEADS = 4
HEAD_DIM = 8
INTERMEDIATE = 16
HIDDEN = NUM_HEADS * HEAD_DIM


def make_circuit(seed=0, density=0.4):
    """A hierarchy-valid mask object: fine gates drawn, coarse gates derived."""
    rng = np.random.default_rng(seed)
    masks = {}
    for key, size in (("attention_neurons", NUM_HEADS * HEAD_DIM),
                      ("mlp_hidden", INTERMEDIATE),
                      ("mlp_output", HIDDEN)):
        masks[key] = {str(l): (rng.random(size) < density).astype(np.uint8)
                      for l in range(N_LAYERS)}
    heads, attn_blocks, mlp_blocks = {}, [], []
    for l in range(N_LAYERS):
        key = str(l)
        by_head = masks["attention_neurons"][key].reshape(NUM_HEADS, HEAD_DIM).any(axis=1)
        heads[key] = by_head.astype(np.uint8)
        attn_blocks.append(int(by_head.any()))
        mlp_blocks.append(int(masks["mlp_hidden"][key].any()
                              or masks["mlp_output"][key].any()))
    masks["attention_heads"] = heads
    masks["attention_blocks"] = np.asarray(attn_blocks, dtype=np.uint8)
    masks["mlp_blocks"] = np.asarray(mlp_blocks, dtype=np.uint8)
    masks["embedding"] = 1
    return masks


def compose(expr, operands, granularity):
    return A.compose(A.parse_expr(expr), operands, granularity=granularity,
                     num_heads=NUM_HEADS, head_dim=HEAD_DIM)


@pytest.fixture
def ops():
    return {"far": make_circuit(seed=1), "sdr": make_circuit(seed=2),
            "ser": make_circuit(seed=3)}


# ==============================================================================
# PARSER
# ==============================================================================

def test_parses_a_bare_name():
    assert A.parse_expr("far") == ("name", "far")
    assert A.is_atomic(A.parse_expr("far"))


def test_union_binds_looser_than_difference():
    # far | (sdr \ ser), not (far | sdr) \ ser
    assert A.parse_expr("far|sdr\\ser") == (
        "|", ("name", "far"), ("\\", ("name", "sdr"), ("name", "ser")))


def test_difference_is_left_associative():
    assert A.parse_expr("far\\sdr\\ser") == (
        "\\", ("\\", ("name", "far"), ("name", "sdr")), ("name", "ser"))


def test_minus_is_an_alias_for_backslash():
    assert A.parse_expr("far-sdr") == A.parse_expr("far\\sdr")


def test_parentheses_override_precedence():
    assert A.parse_expr("(far|sdr)\\ser") == (
        "\\", ("|", ("name", "far"), ("name", "sdr")), ("name", "ser"))


def test_whitespace_is_ignored():
    assert A.parse_expr("  far &  sdr ") == A.parse_expr("far&sdr")


@pytest.mark.parametrize("expr,message", [
    ("far &", "expected a circuit name"),
    ("(far", "unbalanced '('"),
    ("far)", "unbalanced ')'"),
    ("far $ sdr", "unexpected character"),
    ("", "empty circuit expression"),
])
def test_parse_errors_say_what_is_wrong(expr, message):
    with pytest.raises(A.ExprError, match=message.replace("(", r"\(").replace(")", r"\)")):
        A.parse_expr(expr)


def test_unknown_name_names_the_bound_circuits():
    with pytest.raises(A.ExprError, match="unknown circuit 'nope'"):
        A.validate_names(A.parse_expr("far\\nope"), ["far", "sdr"])


def test_slugs_are_directory_safe():
    assert A.slug_for(A.parse_expr("far")) == "far"
    assert A.slug_for(A.parse_expr("far\\sdr")) == "far_minus_sdr"
    assert A.slug_for(A.parse_expr("far&sdr")) == "far_and_sdr"
    assert A.slug_for(A.parse_expr("far|sdr")) == "far_or_sdr"


def test_xor_expands_to_the_exclusive_family():
    assert A.expand_xor(["far", "sdr", "ser"]) == [
        ("far_minus_sdr_minus_ser", "far\\sdr\\ser"),
        ("sdr_minus_far_minus_ser", "sdr\\far\\ser"),
        ("ser_minus_far_minus_sdr", "ser\\far\\sdr"),
    ]


def test_all_pairs_delta_covers_every_ordered_pair():
    pairs = A.expand_all_pairs_delta(["far", "sdr", "ser"])
    assert len(pairs) == 6
    assert ("far_minus_sdr", "far\\sdr") in pairs
    assert ("sdr_minus_far", "sdr\\far") in pairs


# ==============================================================================
# COMPOSE — algebraic identities
# ==============================================================================

@pytest.mark.parametrize("granularity", ["leaf", "head"])
def test_self_difference_has_no_live_fine_nodes(ops, granularity):
    result = compose("far\\far", ops, granularity)
    assert A.live_fine_units(result) == 0
    assert "empty" in A.emptiness_warning("far_minus_far", result)


@pytest.mark.parametrize("granularity", ["leaf", "head"])
def test_self_union_is_the_original(ops, granularity):
    result = compose("far|far", ops, granularity)
    for key in FINEST_KEYS:
        for layer, vector in ops["far"][key].items():
            assert np.array_equal(np.asarray(result[key][layer]), np.asarray(vector))


def test_leaf_intersection_is_a_subset_of_each_operand(ops):
    result = compose("far&sdr", ops, "leaf")
    for key in FINEST_KEYS:
        for layer, vector in result[key].items():
            vector = np.asarray(vector).astype(bool)
            for name in ("far", "sdr"):
                assert not (vector & ~np.asarray(ops[name][key][layer]).astype(bool)).any()


def test_leaf_difference_removes_exactly_the_shared_units(ops):
    result = compose("far\\sdr", ops, "leaf")
    for key in FINEST_KEYS:
        for layer in result[key]:
            a = np.asarray(ops["far"][key][layer]).astype(bool)
            b = np.asarray(ops["sdr"][key][layer]).astype(bool)
            assert np.array_equal(np.asarray(result[key][layer]).astype(bool), a & ~b)


def test_head_mode_intersection_takes_the_and_of_head_gates(ops):
    result = compose("far&sdr", ops, "head")
    for layer in result["attention_heads"]:
        a = np.asarray(ops["far"]["attention_heads"][layer]).astype(bool)
        b = np.asarray(ops["sdr"]["attention_heads"][layer]).astype(bool)
        got = np.asarray(result["attention_heads"][layer]).astype(bool)
        # A surviving head is exactly an AND-head; heads with no surviving
        # neuron are closed, but here the union of two live heads is non-empty.
        assert np.array_equal(got, a & b)


def test_head_mode_union_keeps_fine_gates_from_both_parents(ops):
    result = compose("far|sdr", ops, "head")
    layer = "0"
    a_heads = np.asarray(ops["far"]["attention_heads"][layer]).astype(bool)
    b_heads = np.asarray(ops["sdr"]["attention_heads"][layer]).astype(bool)
    expected_heads = a_heads | b_heads
    assert np.array_equal(
        np.asarray(result["attention_heads"][layer]).astype(bool), expected_heads)
    gate = np.repeat(expected_heads, HEAD_DIM)
    expected = gate & (
        (np.repeat(a_heads, HEAD_DIM) & np.asarray(ops["far"]["attention_neurons"][layer]).astype(bool))
        | (np.repeat(b_heads, HEAD_DIM) & np.asarray(ops["sdr"]["attention_neurons"][layer]).astype(bool)))
    assert np.array_equal(
        np.asarray(result["attention_neurons"][layer]).astype(bool), expected)


def test_head_mode_difference_keeps_only_the_left_operands_neurons(ops):
    result = compose("far\\sdr", ops, "head")
    for layer in result["attention_neurons"]:
        a_heads = np.asarray(ops["far"]["attention_heads"][layer]).astype(bool)
        b_heads = np.asarray(ops["sdr"]["attention_heads"][layer]).astype(bool)
        keep = np.repeat(a_heads & ~b_heads, HEAD_DIM)
        expected = keep & np.asarray(ops["far"]["attention_neurons"][layer]).astype(bool)
        assert np.array_equal(
            np.asarray(result["attention_neurons"][layer]).astype(bool), expected)


# ==============================================================================
# COMPOSE — structural invariants
# ==============================================================================

@pytest.mark.parametrize("granularity", ["leaf", "head"])
@pytest.mark.parametrize("expr", ["far", "far\\sdr", "far&sdr", "far|sdr",
                                  "far\\sdr\\ser", "(far|sdr)&ser", "far\\far"])
def test_every_composed_circuit_passes_validate_hierarchy(ops, granularity, expr):
    result = compose(expr, ops, granularity)
    validate_hierarchy(result, num_heads=NUM_HEADS, head_dim=HEAD_DIM, label=expr)


@pytest.mark.parametrize("granularity", ["leaf", "head"])
def test_coarse_gates_are_rederived_from_the_fine_ones(ops, granularity):
    result = compose("far\\sdr", ops, granularity)
    for l in range(N_LAYERS):
        key = str(l)
        heads = np.asarray(result["attention_heads"][key]).astype(bool)
        neurons = np.asarray(result["attention_neurons"][key]).astype(bool)
        assert bool(result["attention_blocks"][l]) == bool(heads.any())
        assert bool(result["mlp_blocks"][l]) == bool(
            np.asarray(result["mlp_hidden"][key]).any()
            or np.asarray(result["mlp_output"][key]).any())
        assert neurons.reshape(NUM_HEADS, HEAD_DIM).any(axis=1).tolist() <= heads.tolist() \
            or np.array_equal(neurons.reshape(NUM_HEADS, HEAD_DIM).any(axis=1), heads)


@pytest.mark.parametrize("granularity", ["leaf", "head"])
def test_embedding_is_the_or_of_the_operands_not_a_set_member(ops, granularity):
    ops["sdr"]["embedding"] = 0
    result = compose("far\\sdr", ops, granularity)
    # Were embedding a member, far\sdr would close it (1 and not 0 -> 1 here,
    # so use the opposite polarity to make the distinction visible).
    assert result["embedding"] == 1
    ops["far"]["embedding"] = 0
    assert compose("far\\sdr", ops, granularity)["embedding"] == 0


def test_circuits_without_embedding_or_layers_compose_fine(ops):
    for masks in ops.values():
        masks.pop("embedding")
    result = compose("far&sdr", ops, "leaf")
    assert "embedding" not in result
    assert "layers" not in result
    validate_hierarchy(result, num_heads=NUM_HEADS, head_dim=HEAD_DIM)


def test_layers_gate_is_derived_when_present(ops):
    for masks in ops.values():
        masks["layers"] = np.ones(N_LAYERS, dtype=np.uint8)
    result = compose("far\\far", ops, "leaf")
    assert not np.asarray(result["layers"]).any()


def test_operands_with_different_granularities_are_rejected(ops):
    ops["sdr"].pop("mlp_output")
    with pytest.raises(A.ExprError, match="different mask granularities"):
        compose("far&sdr", ops, "leaf")


def test_only_the_named_operands_participate(ops):
    ops["ser"] = {"attention_neurons": {}}  # would fail the key check if used
    result = compose("far&sdr", ops, "leaf")
    assert count_masks(result)["attention_neurons"]["active"] >= 0
