"""
Library-seam tests for the component_analysis package.

The seams under test are the ones a caller sees: the Components a mask object
coarsens to, and the head table written to disk. Nothing here touches nnsight,
a GPU or a real model — the whole intake layer is pure Python over mask objects
so that it runs on the login node and in both environments.
"""

from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np
import pytest

from evaluation import algebra
from evaluation.masks import coarsen_masks, validate_hierarchy
from tests.helpers import TINY

HEADS = TINY["heads"]
HEAD_DIM = TINY["head_dim"]
KV_HEADS = TINY["kv_heads"]
LAYERS = TINY["layers"]


# ==============================================================================
# MASK FIXTURES
# ==============================================================================

def make_masks(live_heads, live_mlp, *, seed=0):
    """A hierarchy-valid tiny mask object.

    `live_heads` is {layer: [head, ...]} and `live_mlp` is the set of layers
    whose MLP block keeps live fine units. Every live head gets three live
    neurons, which is what makes `validate_hierarchy` pass (a live head with no
    live neuron is rejected there).
    """
    rng = np.random.default_rng(seed)
    heads, neurons, hidden, output = {}, {}, {}, {}
    attn_blocks = np.zeros(LAYERS, dtype=np.uint8)
    mlp_blocks = np.zeros(LAYERS, dtype=np.uint8)

    for layer in range(LAYERS):
        key = str(layer)
        h = np.zeros(HEADS, dtype=np.uint8)
        nrn = np.zeros(HEADS * HEAD_DIM, dtype=np.uint8)
        for head in live_heads.get(layer, ()):
            h[head] = 1
            dims = rng.choice(HEAD_DIM, size=3, replace=False)
            nrn[head * HEAD_DIM + dims] = 1
        attn_blocks[layer] = 1 if h.any() else 0
        heads[key], neurons[key] = h, nrn

        hid = np.zeros(TINY["intermediate"], dtype=np.uint8)
        out = np.zeros(TINY["hidden"], dtype=np.uint8)
        if layer in live_mlp:
            hid[rng.choice(TINY["intermediate"], size=5, replace=False)] = 1
            out[rng.choice(TINY["hidden"], size=3, replace=False)] = 1
            mlp_blocks[layer] = 1
        hidden[key], output[key] = hid, out

    masks = {"attention_blocks": attn_blocks, "mlp_blocks": mlp_blocks,
             "attention_heads": heads, "attention_neurons": neurons,
             "mlp_hidden": hidden, "mlp_output": output}
    validate_hierarchy(masks, num_heads=HEADS, head_dim=HEAD_DIM)
    return masks


def coarse_gates(masks):
    """{("head", layer, index)} | {("mlp", layer, 0)} per evaluation/masks.py.

    `coarsen_masks` is the evaluation package's own coarsening: it keeps the
    head and block gates exactly as discovered and opens everything beneath
    them. Reading its live coarse gates is therefore an independent statement
    of which Components a circuit contains.
    """
    coarse = coarsen_masks(masks, head_dim=HEAD_DIM)
    out = set()
    for key, vector in coarse.get("attention_heads", {}).items():
        for index, live in enumerate(np.asarray(vector)):
            if live:
                out.add(("head", int(key), index))
    for layer, live in enumerate(np.asarray(coarse.get("mlp_blocks", []))):
        if live:
            out.add(("mlp", layer, 0))
    return out


def component_keys(components):
    return {(c.kind, c.layer, c.index) for c in components}


# ==============================================================================
# COARSENING
# ==============================================================================

def test_coarsening_agrees_with_the_evaluation_packages_coarsening():
    from component_analysis.components import circuit_components

    masks = make_masks({0: [0, 3], 1: [2]}, {0, 1})
    components = circuit_components(masks, num_heads=HEADS, head_dim=HEAD_DIM,
                                    num_kv_heads=KV_HEADS)

    assert component_keys(components) == coarse_gates(masks)


def test_coarsening_of_a_leaf_only_delta_agrees_too():
    """The delta circuits evaluated on benchmarks are leaf-granularity.

    `compose(..., granularity="leaf")` re-derives every coarse gate from the
    fine ones, so the two coarsenings must agree on a composed circuit as well
    as on a saved one — this is the case the benchmark knockouts produced.
    """
    from component_analysis.components import circuit_components

    deceptive = make_masks({0: [0, 1, 3], 1: [2]}, {0, 1}, seed=1)
    honest = make_masks({0: [1], 1: [2]}, {1}, seed=2)
    tree = algebra.parse_expr("deceptive \\ honest")
    delta = algebra.compose(tree, {"deceptive": deceptive, "honest": honest},
                            granularity="leaf", num_heads=HEADS,
                            head_dim=HEAD_DIM)

    components = circuit_components(delta, num_heads=HEADS, head_dim=HEAD_DIM,
                                    num_kv_heads=KV_HEADS)

    assert component_keys(components) == coarse_gates(delta)
    assert component_keys(components), "the delta came out empty; nothing tested"


def test_a_head_is_a_component_when_any_leaf_gate_is_active():
    """The rule from the glossary, asserted one head at a time."""
    from component_analysis.components import circuit_components

    masks = make_masks({0: [2]}, set())
    # Open a second head's gate but leave every neuron under it dead. Gates AND
    # together, so that head contributes nothing and is not a Component.
    masks["attention_heads"]["0"][1] = 1

    keys = component_keys(circuit_components(masks, num_heads=HEADS,
                                            head_dim=HEAD_DIM,
                                            num_kv_heads=KV_HEADS))
    assert ("head", 0, 2) in keys
    assert ("head", 0, 1) not in keys


def test_an_mlp_block_with_no_live_fine_units_is_not_a_component():
    """`validate_hierarchy` permits an open block over dead fine gates.

    `coarsen_masks` would call that block live because it keeps the block gate
    verbatim; the Component rule does not, because an MLP whose hidden and
    output gates are all closed writes nothing.
    """
    from component_analysis.components import circuit_components

    masks = make_masks({0: [0]}, set())
    masks["mlp_blocks"][1] = 1

    keys = component_keys(circuit_components(masks, num_heads=HEADS,
                                            head_dim=HEAD_DIM,
                                            num_kv_heads=KV_HEADS))
    assert ("mlp", 1, 0) not in keys


def test_head_gates_stand_in_when_a_circuit_has_no_neuron_gates():
    """Runs with attention-neuron pruning off save no `attention_neurons`."""
    from component_analysis.components import circuit_components

    masks = make_masks({0: [0, 2]}, {0})
    del masks["attention_neurons"]

    keys = component_keys(circuit_components(masks, num_heads=HEADS,
                                            head_dim=HEAD_DIM,
                                            num_kv_heads=KV_HEADS))
    assert {k for k in keys if k[0] == "head"} == {("head", 0, 0), ("head", 0, 2)}


def test_components_record_kv_group_gate_state_and_neuron_count():
    from component_analysis.components import circuit_components

    masks = make_masks({0: [0, 3]}, {0})
    by_key = {(c.kind, c.layer, c.index): c
              for c in circuit_components(masks, num_heads=HEADS,
                                          head_dim=HEAD_DIM,
                                          num_kv_heads=KV_HEADS)}

    # 4 query heads over 2 KV heads: heads 0-1 are group 0, heads 2-3 group 1.
    assert by_key[("head", 0, 0)].kv_group == 0
    assert by_key[("head", 0, 3)].kv_group == 1
    assert by_key[("head", 0, 0)].head_gate_active is True
    assert by_key[("head", 0, 0)].active_neuron_count == 3

    mlp = by_key[("mlp", 0, 0)]
    assert mlp.kv_group is None
    assert mlp.head_gate_active is True
    # 5 hidden + 3 output gates, collapsed onto the block.
    assert mlp.active_neuron_count == 8


def test_membership_reports_whether_a_component_is_in_another_circuit():
    from component_analysis.components import circuit_components, is_component_of

    deceptive = make_masks({0: [0, 1, 3], 1: [2]}, {0, 1}, seed=1)
    honest = make_masks({0: [1], 1: [2]}, {1}, seed=2)
    components = circuit_components(deceptive, num_heads=HEADS,
                                    head_dim=HEAD_DIM, num_kv_heads=KV_HEADS)

    member = {(c.kind, c.layer, c.index): is_component_of(
        c, honest, num_heads=HEADS, head_dim=HEAD_DIM) for c in components}

    assert member[("head", 0, 1)] is True
    assert member[("head", 0, 0)] is False
    assert member[("mlp", 1, 0)] is True
    assert member[("mlp", 0, 0)] is False


def test_the_intake_layer_does_not_import_nnsight():
    """The pure-Python parts must import where nnsight 0.7.0 is not installed.

    Run in a fresh interpreter on purpose: `sys.modules` is process-wide, so
    checking it in-process would pass or fail on whether some earlier test in
    the session happened to import nnsight first.
    """
    import subprocess

    probe = ("import component_analysis.components, component_analysis.head_table, "
             "component_analysis.intake, component_analysis.segmentation, "
             "component_analysis.sampling, component_analysis.instances, sys; "
             "assert 'nnsight' not in sys.modules, sorted(sys.modules)")
    result = subprocess.run([sys.executable, "-c", probe],
                            cwd=os.path.dirname(os.path.dirname(
                                os.path.abspath(__file__))),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


# ==============================================================================
# HEAD TABLE
# ==============================================================================

def sample_rows():
    from component_analysis.components import circuit_components
    from component_analysis.head_table import rows_from_components

    masks = make_masks({0: [0, 3], 1: [2]}, {0, 1})
    return rows_from_components(
        circuit_components(masks, num_heads=HEADS, head_dim=HEAD_DIM,
                           num_kv_heads=KV_HEADS))


def test_head_table_round_trips_through_csv_and_json(tmp_path):
    from component_analysis.head_table import load_head_table, write_head_table

    rows = sample_rows()
    written = write_head_table(str(tmp_path), rows)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["head_table.csv",
                                                          "head_table.json"]
    assert load_head_table(str(tmp_path)) == rows

    with open(written["csv"]) as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == len(rows)
    assert csv_rows[0]["kind"] == rows[0]["kind"]
    assert int(csv_rows[0]["layer"]) == rows[0]["layer"]

    payload = json.loads(open(written["json"]).read())
    assert payload["columns"][:3] == ["kind", "layer", "index"]


def test_merge_columns_namespaces_new_columns_and_keys_by_component():
    from component_analysis.head_table import merge_columns

    rows = sample_rows()
    updates = {("head", 0, 3): {"logit_diff": 0.5}, ("mlp", 1, 0): {"logit_diff": -0.25}}

    merged = merge_columns(rows, updates, namespace="dla")

    by_key = {(r["kind"], r["layer"], r["index"]): r for r in merged}
    assert by_key[("head", 0, 3)]["dla.logit_diff"] == 0.5
    assert by_key[("mlp", 1, 0)]["dla.logit_diff"] == -0.25
    # Components the analysis said nothing about keep the column, empty.
    assert by_key[("head", 0, 0)]["dla.logit_diff"] is None


def test_merge_columns_adds_rows_for_components_not_already_in_the_table():
    """A completeness sweep scores Components outside the circuit."""
    from component_analysis.head_table import merge_columns

    rows = sample_rows()
    merged = merge_columns(rows, {("head", 1, 3): {"logit_diff": 1.0}},
                           namespace="sweep")

    by_key = {(r["kind"], r["layer"], r["index"]): r for r in merged}
    assert len(merged) == len(rows) + 1
    assert by_key[("head", 1, 3)]["sweep.logit_diff"] == 1.0
    assert by_key[("head", 1, 3)]["head_gate_active"] is None


def test_merge_columns_treats_a_string_typed_key_as_the_same_component():
    """A key read back from a CSV is (kind, "layer", "index"), all strings.

    The completeness sweep is the caller that builds keys from a prior table
    rather than from Component objects. Without coercion the same Component
    gets a second row, the analysis value lands on it, and "one row per
    Component" breaks silently while the CSV still looks well formed.
    """
    from component_analysis.head_table import merge_columns

    rows = sample_rows()
    merged = merge_columns(rows, {("head", "0", "3"): {"logit_diff": 1.0}},
                           namespace="sweep")

    assert len(merged) == len(rows)
    by_key = {(r["kind"], r["layer"], r["index"]): r for r in merged}
    assert by_key[("head", 0, 3)]["sweep.logit_diff"] == 1.0


def test_merge_columns_refuses_to_overwrite_a_confirmed_role():
    from component_analysis.head_table import merge_columns

    rows = sample_rows()
    rows[0]["role_confirmed"] = "mover"

    with pytest.raises(ValueError, match="role_confirmed"):
        merge_columns(rows, {(rows[0]["kind"], rows[0]["layer"], rows[0]["index"]):
                             {"role_confirmed": "binder"}})


def test_the_hook_module_is_the_only_place_that_imports_nnsight():
    """ADR-0001: one module holds the hook surface, so a 0.8 migration is local.

    Pure source parsing, so it runs in both environments rather than only
    where nnsight 0.7.0 is installed.
    """
    import ast
    import component_analysis

    package = os.path.dirname(component_analysis.__file__)
    offenders = []
    for name in sorted(os.listdir(package)):
        if not name.endswith(".py") or name == "hooks.py":
            continue
        tree = ast.parse(open(os.path.join(package, name)).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(n.split(".")[0] == "nnsight" for n in names):
                offenders.append(f"{name}:{node.lineno}")

    assert offenders == [], \
        f"nnsight is imported outside hooks.py: {', '.join(offenders)}"
