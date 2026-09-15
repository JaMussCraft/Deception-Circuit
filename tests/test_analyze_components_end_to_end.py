"""
CLI-seam test for analyze_components.py.

Mirrors `tests/test_end_to_end.py`: a throwaway run directory for the 2-layer
random Llama, a synthetic task, and the real CLI over it — the real circuit
resolution, the real set algebra, the real coarsening, the real head-table
writer. Nothing is faked but the task registration and the KV-head count, and
nothing loads a model, because `--dry-run` is a login-node mode.

The assertions are on what the researcher gets: the files written under the
cell directory, the columns in them, and the fact that nothing else appeared.
"""

from __future__ import annotations

import csv
import json
import os

import pytest

import analyze_components
from config import NodePruningConfig
from tests.helpers import TINY
from tests.test_component_analysis import make_masks

CELL = ("self", "tinystd")


# ==============================================================================
# FIXTURE
# ==============================================================================

def write_run(path, masks, *, task="tinystd", model="llama-tiny"):
    from evaluation import masks as M

    path.mkdir(parents=True, exist_ok=True)
    (path / "config.json").write_text(json.dumps({
        "model": model, "task": task, "family": "llama",
        "edge_pruning": False, "skip_node_pruning": False, "seed": 42,
        "batch_size": 4, "max_seq_length": 12,
        "train_samples": 4, "val_samples": 4, "test_samples": 24,
        "node_lambda_sparsity": 0.7, "data_dir": "./data/datasets",
        "node_config": NodePruningConfig().__dict__,
    }))
    (path / "active_nodes.json").write_text(json.dumps({
        "active_heads": {}, "active_mlps": [], "masks": M.as_lists(masks),
    }))
    (path / "results.json").write_text(json.dumps({"node_eval": None}))
    return path


@pytest.fixture
def tiny_runs(tmp_path, monkeypatch):
    """(deceptive run dir, honest run dir, output dir)."""
    import tasks
    from models import MODEL_REGISTRY
    from tests.test_end_to_end import TinyTask

    monkeypatch.setitem(MODEL_REGISTRY, "llama-tiny", ("llama-tiny", "llama"))
    monkeypatch.setitem(tasks._TASKS, "tinystd", TinyTask)

    deceptive = write_run(tmp_path / "run", make_masks({0: [0, 1, 3], 1: [2]},
                                                       {0, 1}, seed=1))
    honest = write_run(tmp_path / "honest", make_masks({0: [1], 1: [2]},
                                                       {1}, seed=2))
    return deceptive, honest, tmp_path / "analyses"


def run_cli(*argv):
    return analyze_components.main(list(argv))


def written_files(root):
    return sorted(os.path.relpath(os.path.join(dirpath, name), str(root))
                  for dirpath, _dirs, names in os.walk(str(root))
                  for name in names)


def read_table(root, *cell):
    with open(os.path.join(str(root), *cell, "head_table.json")) as f:
        return json.load(f)


# ==============================================================================
# TESTS
# ==============================================================================

def test_dry_run_writes_the_head_table_and_nothing_else(tiny_runs):
    run_dir, _honest, out = tiny_runs

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    assert written_files(out) == [os.path.join(*CELL, "head_table.csv"),
                                  os.path.join(*CELL, "head_table.json")]
    # The run directory it read is untouched: analyses never write into one.
    assert sorted(p.name for p in run_dir.iterdir()) == [
        "active_nodes.json", "config.json", "results.json"]


def test_head_table_lists_every_component_with_its_intake_columns(tiny_runs):
    run_dir, _honest, out = tiny_runs
    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
            "--output-dir", str(out))

    table = read_table(out, *CELL)
    assert table["columns"] == ["kind", "layer", "index", "kv_group",
                                "head_gate_active", "active_neuron_count"]

    keys = {(r["kind"], r["layer"], r["index"]) for r in table["rows"]}
    assert keys == {("head", 0, 0), ("head", 0, 1), ("head", 0, 3),
                    ("head", 1, 2), ("mlp", 0, 0), ("mlp", 1, 0)}

    by_key = {(r["kind"], r["layer"], r["index"]): r for r in table["rows"]}
    # 4 query heads over 2 KV heads: heads 0-1 in group 0, heads 2-3 in group 1.
    assert by_key[("head", 0, 1)]["kv_group"] == 0
    assert by_key[("head", 0, 3)]["kv_group"] == 1
    assert by_key[("mlp", 0, 0)]["kv_group"] is None
    assert by_key[("head", 1, 2)]["head_gate_active"] is True
    assert by_key[("head", 1, 2)]["active_neuron_count"] == 3


def test_reference_binding_adds_a_membership_column(tiny_runs):
    run_dir, honest, out = tiny_runs

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--reference", f"honest={honest}",
                   "--output-dir", str(out)) == 0

    table = read_table(out, *CELL)
    assert "reference.honest" in table["columns"]
    by_key = {(r["kind"], r["layer"], r["index"]): r for r in table["rows"]}
    # The honest twin has head 1 of layer 0, head 2 of layer 1 and MLP 1.
    assert by_key[("head", 0, 1)]["reference.honest"] is True
    assert by_key[("head", 0, 0)]["reference.honest"] is False
    assert by_key[("mlp", 1, 0)]["reference.honest"] is True
    assert by_key[("mlp", 0, 0)]["reference.honest"] is False

    assert table["meta"]["intake"]["references"]["honest"] == str(honest)


def test_a_leaf_delta_expression_gets_its_own_cell(tiny_runs):
    """The circuits the benchmark knockouts produced are leaf-level deltas."""
    run_dir, honest, out = tiny_runs

    assert run_cli("--dry-run", "--num-kv-heads", "2",
                   "--circuit", f"sdr={run_dir}",
                   "--circuit", f"twin={honest}",
                   "--expr", "delta=sdr \\ twin",
                   "--compose-granularity", "leaf",
                   "--task-from", str(run_dir),
                   "--output-dir", str(out)) == 0

    cell = ("delta__leaf", "tinystd")
    assert written_files(out) == [os.path.join(*cell, "head_table.csv"),
                                  os.path.join(*cell, "head_table.json")]

    table = read_table(out, *cell)
    keys = {(r["kind"], r["layer"], r["index"]) for r in table["rows"]}
    assert ("head", 0, 0) in keys and ("head", 0, 3) in keys
    assert table["meta"]["circuit"]["expr"] == "sdr \\ twin"


def test_the_head_delta_is_the_leaf_delta_minus_what_the_reference_shares(tiny_runs):
    """The 46-versus-14 reading of a delta circuit, in one table.

    A head survives the *leaf* delta when it keeps any neuron the reference
    does not have, which includes heads both circuits use with different
    neurons. It survives the *head* delta only when the reference does not use
    the head at all — which is exactly the leaf-delta heads whose reference
    membership column is false. Asserting the two agree is what lets the
    researcher read the head-gate-level subset out of the leaf-level table.
    """
    run_dir, honest, out = tiny_runs

    assert run_cli("--dry-run", "--num-kv-heads", "2",
                   "--circuit", f"sdr={run_dir}",
                   "--circuit", f"twin={honest}",
                   "--reference", f"honest={honest}",
                   "--expr", "delta=sdr \\ twin",
                   "--compose-granularity", "both",
                   "--task-from", str(run_dir),
                   "--output-dir", str(out)) == 0

    leaf = read_table(out, "delta__leaf", "tinystd")["rows"]
    head = read_table(out, "delta__head", "tinystd")["rows"]

    def keys(rows, kind="head"):
        return {(r["layer"], r["index"]) for r in rows if r["kind"] == kind}

    # Head 0/1 is in both circuits with different neurons: leaf keeps it,
    # head granularity does not.
    assert (0, 1) in keys(leaf) and (0, 1) not in keys(head)
    assert keys(head) == {(r["layer"], r["index"]) for r in leaf
                          if r["kind"] == "head" and not r["reference.honest"]}


def test_csv_and_json_carry_the_same_rows(tiny_runs):
    run_dir, honest, out = tiny_runs
    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
            "--reference", f"honest={honest}", "--output-dir", str(out))

    table = read_table(out, *CELL)
    with open(os.path.join(str(out), *CELL, "head_table.csv")) as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == len(table["rows"])
    assert list(rows[0]) == table["columns"]
    for csv_row, json_row in zip(rows, table["rows"]):
        assert csv_row["kind"] == json_row["kind"]
        assert int(csv_row["layer"]) == json_row["layer"]
        # CSV has no null and no boolean: blank for None, 0/1 for a flag.
        assert csv_row["kv_group"] == ("" if json_row["kv_group"] is None
                                       else str(json_row["kv_group"]))
        assert csv_row["reference.honest"] == str(int(json_row["reference.honest"]))


def test_a_reference_name_may_not_also_be_a_circuit_name(tiny_runs):
    run_dir, honest, out = tiny_runs

    with pytest.raises(ValueError, match="both as a circuit and as a reference"):
        run_cli("--dry-run", "--num-kv-heads", "2",
                "--circuit", f"sdr={run_dir}", "--reference", f"sdr={honest}",
                "--task-from", str(run_dir), "--output-dir", str(out))


def test_without_dry_run_it_says_what_is_not_built_yet(tiny_runs):
    run_dir, _honest, out = tiny_runs

    with pytest.raises(SystemExit, match="--dry-run"):
        run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))
    assert not os.path.exists(str(out))


def test_a_reference_from_another_model_is_refused(tiny_runs, tmp_path, monkeypatch):
    run_dir, _honest, out = tiny_runs
    from models import MODEL_REGISTRY

    monkeypatch.setitem(MODEL_REGISTRY, "llama-other", ("llama-other", "llama"))
    other = write_run(tmp_path / "other", make_masks({0: [0]}, {0}),
                      model="llama-other")

    with pytest.raises(ValueError, match="trained on"):
        run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                "--reference", f"other={other}", "--output-dir", str(out))
    assert not os.path.exists(str(out))


def test_geometry_is_read_from_the_masks_not_from_a_model(tiny_runs):
    """`--dry-run` is a login-node mode: no weights, no CUDA, no tokenizer."""
    run_dir, _honest, out = tiny_runs
    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
            "--output-dir", str(out))

    geometry = read_table(out, *CELL)["meta"]["intake"]["geometry"]
    assert geometry["num_heads"] == TINY["heads"]
    assert geometry["head_dim"] == TINY["head_dim"]
    assert geometry["num_layers"] == TINY["layers"]
