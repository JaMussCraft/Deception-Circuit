"""Where results land: the legacy single-cell path vs. the suite grid.

Reuses the tiny end-to-end machinery (a 2-layer Llama, a fake tokenizer, a
synthetic aligned dataset) from `tests/test_end_to_end.py`, so these tests go
through the real CLI, the real session builder and the real cell loop — only
the model, tokenizer and corpus are stand-ins.

Only `--evals sanity` is run: the question here is layout and provenance, not
numbers, and sanity is also the eval whose `requires` the grid is supposed to
enforce.
"""

from __future__ import annotations

import csv
import json
import os

import numpy as np
import pytest
import torch

import evaluate_circuit
from config import NodePruningConfig
from tests.helpers import TINY, build_tiny_pair
from tests.test_end_to_end import (BATCH, N_SAMPLES, SEQ, FakeTokenizer,
                                   TinyTask, tiny_circuit_masks)


class TinyTaskB(TinyTask):
    """A second task, so a cell grid has something to cross."""

    name = "tinystd2"
    display_name = "Tiny synthetic STD (second dataset)"


def write_run(path, task_name, seed):
    """A run directory of the shape build_session expects."""
    from evaluation import masks as M

    path.mkdir(parents=True, exist_ok=True)
    (path / "config.json").write_text(json.dumps({
        "model": "llama-tiny", "task": task_name, "family": "llama",
        "edge_pruning": False, "skip_node_pruning": False, "seed": seed,
        "batch_size": BATCH, "max_seq_length": SEQ,
        "train_samples": 4, "val_samples": 4, "test_samples": N_SAMPLES,
        "node_lambda_sparsity": 0.7, "data_dir": "./data/datasets",
        "node_config": NodePruningConfig().__dict__,
    }))
    circuit = tiny_circuit_masks()
    (path / "active_nodes.json").write_text(json.dumps({
        "active_heads": {}, "active_mlps": [], "masks": M.as_lists(circuit),
    }))
    (path / "results.json").write_text(json.dumps({
        "baseline": {"accuracy": 1.0, "logit_diff": 1.0, "kl_div": 0.0,
                     "exact_match": 1.0},
        "node_eval": None,
    }))
    return path


@pytest.fixture
def two_runs(tmp_path, monkeypatch):
    """(run_a, run_b): the same circuit geometry, two different tasks."""
    import tasks
    from models import MODEL_REGISTRY, ModelAdapter

    monkeypatch.setitem(MODEL_REGISTRY, "llama-tiny", ("llama-tiny", "llama"))
    monkeypatch.setitem(tasks._TASKS, "tinystd", TinyTask)
    monkeypatch.setitem(tasks._TASKS, "tinystd2", TinyTaskB)

    plain, pruned = build_tiny_pair(attn_implementation="eager")
    monkeypatch.setattr(ModelAdapter, "load_tokenizer", lambda self: FakeTokenizer())
    monkeypatch.setattr(ModelAdapter, "load_full_model", lambda self, device: plain)
    monkeypatch.setattr(ModelAdapter, "build_node_model",
                        lambda self, cfg, device: pruned)

    import evaluation.wikitext as W

    def fake_blocks(ctx):
        g = torch.Generator().manual_seed(7)
        blocks = torch.randint(0, TINY["vocab"],
                               (ctx.cli.wikitext_blocks, ctx.cli.wikitext_block_size),
                               generator=g)
        blocks[:, 0] = FakeTokenizer.bos_token_id
        return W._cache_blocks(ctx, blocks)

    monkeypatch.setattr(W, "load_wikitext_blocks", fake_blocks)

    outputs = tmp_path / "outputs" / "llama-tiny"
    return (write_run(outputs / "run_a", "tinystd", 1),
            write_run(outputs / "run_b", "tinystd2", 2))


def run_cli(monkeypatch, *argv):
    monkeypatch.setattr("sys.argv", ["evaluate_circuit.py"] + [str(a) for a in argv])
    return evaluate_circuit.main()


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


# ==============================================================================
# LEGACY — one circuit, its own task, today's layout untouched
# ==============================================================================

def test_a_bare_run_dir_still_writes_the_legacy_layout(two_runs, monkeypatch):
    run_a, _ = two_runs
    assert run_cli(monkeypatch, run_a, "--evals", "sanity", "--n-random", "1",
                   "--skip-wikitext") == 0

    assert os.path.isfile(run_a / "evaluations" / "interchange" / "sanity.json")
    assert os.path.isfile(run_a / "evaluations" / "interchange" / "evaluation.log")
    assert os.path.isfile(run_a / "evaluations" / "index.json")
    # No suite artefacts anywhere.
    assert not os.path.exists(run_a / "evaluations" / "cells")
    assert not os.path.exists(run_a / "evaluations" / "suite.json")


def test_naming_the_runs_own_task_is_still_a_suite(two_runs, monkeypatch, tmp_path):
    """--task-from is a suite flag even when it points at the circuit's own run.

    Writing it into the run's own evaluations/ would overwrite results that
    have different provenance, so the flag alone decides.
    """
    run_a, _ = two_runs
    root = tmp_path / "suite_self"
    assert run_cli(monkeypatch, run_a, "--task-from", run_a,
                   "--evals", "sanity", "--n-random", "1", "--skip-wikitext",
                   "--output-dir", root) == 0
    assert os.path.isfile(root / "suite.json")
    assert os.path.isfile(root / "cells" / "self" / "tinystd" / "interchange"
                          / "sanity.json")


# ==============================================================================
# SUITE — 2 circuits x 2 tasks
# ==============================================================================

@pytest.fixture
def suite_root(tmp_path, two_runs, monkeypatch):
    run_a, run_b = two_runs
    root = tmp_path / "suite"
    code = run_cli(monkeypatch,
                   "--circuit", f"a={run_a}", "--circuit", f"b={run_b}",
                   "--task-from", run_a, "--task-from", run_b,
                   "--evals", "sanity", "--n-random", "1", "--skip-wikitext",
                   "--output-dir", root)
    assert code == 0
    return root


def test_the_cell_tree_has_one_directory_per_circuit_task_pair(suite_root):
    for circuit in ("a", "b"):
        for task in ("tinystd", "tinystd2"):
            assert os.path.isdir(suite_root / "cells" / circuit / task
                                 / "interchange"), f"{circuit}/{task}"
    assert sorted(os.listdir(suite_root / "cells")) == ["a", "b"]
    assert os.path.isfile(suite_root / "suite.log")


def test_suite_json_records_the_provenance_of_every_circuit_and_task(suite_root):
    with open(suite_root / "suite.json") as f:
        record = json.load(f)
    assert [c["label"] for c in record["circuits"]] == ["a", "b"]
    assert [t["label"] for t in record["tasks"]] == ["tinystd", "tinystd2"]
    assert all(c["kind"] == "atomic" for c in record["circuits"])
    assert record["ablation"] == "interchange"
    assert record["evals"] == ["sanity"]
    assert record["membership_convention"]["leaf"]
    assert record["geometry"]


def test_the_matrix_covers_all_four_cells(suite_root):
    with open(suite_root / "matrix.json") as f:
        matrix = json.load(f)
    assert {(c["circuit"], c["task"]) for c in matrix["cells"]} == {
        ("a", "tinystd"), ("a", "tinystd2"),
        ("b", "tinystd"), ("b", "tinystd2")}

    # matrix.csv is unpivoted — one row per (cell, eval, metric) — so the four
    # cells show up as four distinct circuit/task pairs, not four rows.
    rows = read_csv(suite_root / "matrix.csv")
    assert rows
    assert {(r["circuit"], r["task"]) for r in rows} == {
        ("a", "tinystd"), ("b", "tinystd2")}   # only the cells sanity ran in
    assert {r["eval"] for r in rows} == {"sanity"}


def test_sanity_is_skipped_on_cross_task_cells_with_a_reason(suite_root):
    for circuit, task in (("a", "tinystd2"), ("b", "tinystd")):
        with open(suite_root / "cells" / circuit / task / "interchange"
                  / "summary.json") as f:
            summary = json.load(f)
        reason = summary["skipped"]["sanity"]
        assert "no in-run number to reproduce" in reason
        assert not os.path.exists(suite_root / "cells" / circuit / task
                                  / "interchange" / "sanity.json")

    for circuit, task in (("a", "tinystd"), ("b", "tinystd2")):
        assert os.path.isfile(suite_root / "cells" / circuit / task
                              / "interchange" / "sanity.json")


# ==============================================================================
# COMPOSED CIRCUITS
# ==============================================================================

def test_sanity_is_skipped_for_a_composed_circuit(two_runs, monkeypatch, tmp_path):
    run_a, run_b = two_runs
    root = tmp_path / "suite_expr"
    assert run_cli(monkeypatch,
                   "--circuit", f"a={run_a}", "--circuit", f"b={run_b}",
                   "--expr", "shared=a&b", "--compose-granularity", "leaf",
                   "--task-from", run_a,
                   "--evals", "sanity", "--n-random", "1", "--skip-wikitext",
                   "--output-dir", root) == 0

    # Composed circuits carry the granularity in their slug; atomic ones do not.
    cell = root / "cells" / "shared__leaf" / "tinystd" / "interchange"
    assert os.path.isdir(cell)
    with open(cell / "summary.json") as f:
        summary = json.load(f)
    assert "composed" in summary["skipped"]["sanity"]
    assert not os.path.exists(cell / "sanity.json")

    with open(root / "suite.json") as f:
        record = json.load(f)
    composed = [c for c in record["circuits"] if c["label"] == "shared__leaf"]
    assert composed and composed[0]["expr"] == "a&b"
    assert composed[0]["kind"] == "leaf"


def test_compose_granularity_both_makes_two_separate_cells(two_runs, monkeypatch,
                                                           tmp_path):
    """Leaf and head membership are different circuits, so they get their own cells."""
    run_a, run_b = two_runs
    root = tmp_path / "suite_both"
    assert run_cli(monkeypatch,
                   "--circuit", f"a={run_a}", "--circuit", f"b={run_b}",
                   "--expr", "shared=a&b", "--compose-granularity", "both",
                   "--task-from", run_a,
                   "--evals", "sanity", "--n-random", "1", "--skip-wikitext",
                   "--output-dir", root) == 0
    assert sorted(os.listdir(root / "cells")) == ["shared__head", "shared__leaf"]
