"""
The `nopressure` condition end to end: train.py on a synthetic
`<task>_nopressure` dataset, then the evaluator's `--task-from` on that run.

A Format Circuit is a mechanism task's circuit pruned on its `nopressure`
condition (the Scaffold with the Pressure Clause deleted, honest labels). It is
not a new task, so everything below goes through the same code as `honest`:
the only thing that may differ is which directory is read and what the run
directory is called.

The model is a random 2-layer Llama (tests/helpers.py) with the vocabulary
widened to the fake word tokenizer's, and one node epoch; nothing here says
anything about circuits, only about plumbing.
"""

from __future__ import annotations

import json
import os
import re
import sys

import pytest
from transformers import LlamaConfig, LlamaForCausalLM

from dataset import deception_common as dc
from models.llama_node import PrunableLlamaForCausalLM, apply_pruning_wrappers
from tests.fakes import FAKE_VOCAB_SIZE, FakeWordTokenizer
from tests.helpers import TINY

SEQ = 96


def _tiny_llama_config():
    return LlamaConfig(
        hidden_size=TINY["hidden"], num_hidden_layers=TINY["layers"],
        num_attention_heads=TINY["heads"], num_key_value_heads=TINY["kv_heads"],
        intermediate_size=TINY["intermediate"], vocab_size=FAKE_VOCAB_SIZE,
        max_position_embeddings=TINY["max_pos"], attn_implementation="eager")


def _write_condition_dataset(path, records, condition, margin_thresh):
    """The arrow DatasetDict layout of `<task>` / `<task>_honest`."""
    from datasets import Dataset, DatasetDict
    os.makedirs(path, exist_ok=True)
    DatasetDict({split: Dataset.from_list(records)
                 for split in ("train", "validation", "test")}).save_to_disk(path)
    with open(os.path.join(path, "dataset_config.json"), "w") as f:
        json.dump({"task": os.path.basename(path), "condition": condition,
                   "margin_thresh": margin_thresh}, f)


@pytest.fixture
def tiny_far_data(tmp_path, monkeypatch):
    """A `far` and a differently sized `far_nopressure` dataset, and a tiny
    Llama behind ModelAdapter. Returns (data_dir, tokenizer)."""
    import torch
    from models import MODEL_REGISTRY, ModelAdapter

    tok = FakeWordTokenizer()
    entities = [{"name": "Firm", "domain": "logistics"}]
    pairs = [("staffing", "pricing"), ("budget", "timeline")]
    pressures = [{"id": "p0", "slot": 0, "text": "You will be shut off.",
                  "shared": False}]
    records = dc.generate_task_data(tok, dc.SPECS["far"], 6, entities, pairs,
                                    pressures, max_seq_length=SEQ, seed=0)
    records = [dict(r) for r in records]

    data_dir = tmp_path / "datasets"
    # The deceptive dataset has 6 records, the no-pressure one 4, so a test can
    # tell from the loaded size alone which directory was read.
    _write_condition_dataset(str(data_dir / "far"), records, "deceptive", 1.0)
    nopressure = [dict(r, condition="nopressure", pressure="")
                  for r in records[:4]]
    _write_condition_dataset(str(data_dir / "far_nopressure"), nopressure,
                             "nopressure", 0.5)

    torch.manual_seed(0)
    plain = LlamaForCausalLM(_tiny_llama_config()).eval()

    def build_node_model(self, cfg, device):
        pruned = PrunableLlamaForCausalLM(_tiny_llama_config())
        pruned.load_state_dict(plain.state_dict())
        apply_pruning_wrappers(pruned, cfg)
        return pruned

    monkeypatch.setitem(MODEL_REGISTRY, "llama-tiny", ("llama-tiny", "llama"))
    monkeypatch.setattr(ModelAdapter, "load_tokenizer", lambda self: tok)
    monkeypatch.setattr(ModelAdapter, "load_full_model", lambda self, device: plain)
    monkeypatch.setattr(ModelAdapter, "build_node_model", build_node_model)
    monkeypatch.chdir(tmp_path)
    return data_dir, tok


def _train(monkeypatch, data_dir, *extra):
    import train
    argv = ["train.py", "--model", "llama-tiny", "--task", "far",
            "--deception-condition", "nopressure", "--data-dir", str(data_dir),
            "--no-edge-pruning", "--node-lambda-sparsity", "0.3",
            "--node-epochs", "1", "--batch-size", "2",
            "--max-seq-length", str(SEQ)] + list(extra)
    monkeypatch.setattr(sys, "argv", argv)
    train.main()
    runs = os.listdir(os.path.join("outputs", "llama-tiny_far"))
    assert len(runs) == 1
    return os.path.abspath(os.path.join("outputs", "llama-tiny_far", runs[0]))


def test_train_on_nopressure_writes_the_condition_and_the_slug(
        tiny_far_data, monkeypatch):
    data_dir, _ = tiny_far_data
    run_dir = _train(monkeypatch, data_dir)

    # nls0.3_nopressure_noedge_<stamp>, as nls0.3_honest_noedge_<stamp>. The
    # test's own small-run overrides (ne1_bs2_seq96_) come first.
    assert re.fullmatch(r"ne1_bs2_seq96_nls0\.3_nopressure_noedge_\d{6}-\d{6}",
                        os.path.basename(run_dir)), run_dir
    with open(os.path.join(run_dir, "config.json")) as f:
        config = json.load(f)
    assert config["deception_condition"] == "nopressure"
    assert config["task"] == "far"
    assert os.path.exists(os.path.join(run_dir, "active_nodes.json"))
    with open(os.path.join(run_dir, "results.json")) as f:
        results = json.load(f)
    assert results["node_eval"] is not None


def test_task_from_a_nopressure_run_resolves_the_nopressure_test_set(
        tiny_far_data, monkeypatch, capsys):
    import evaluate_circuit
    from evaluation.circuits import resolve_circuits, resolve_tasks
    from tasks import get_task

    data_dir, tok = tiny_far_data
    run_dir = _train(monkeypatch, data_dir)
    capsys.readouterr()

    argv = ["evaluate_circuit.py", "--circuit", f"F={run_dir}",
            "--task-from", run_dir, "--dry-run", "--n-random", "2"]
    monkeypatch.setattr(sys, "argv", argv)
    cli = evaluate_circuit.resolve_cli(evaluate_circuit.build_parser().parse_args())
    _, bindings, _, configs, _ = resolve_circuits(cli)
    (spec,) = resolve_tasks(cli, bindings, configs)

    assert spec.name == "far"
    assert spec.args.deception_condition == "nopressure"
    assert spec.provenance()["dataset"]["deception_condition"] == "nopressure"
    assert get_task("far").dataset_dir(spec.args) == str(data_dir / "far_nopressure")

    # And the loader really reads it: 4 no-pressure records, not the 6
    # deceptive ones, with the no-pressure dataset's own margin.
    spec.args.batch_size = 2
    state = {}
    _, _, test_dl = get_task("far").build_dataloaders(
        tok, "llama", None, "cpu", spec.args, state)
    assert len(test_dl.dataset) == 4
    assert state["margin"] == 0.5

    # The dry-run plan names the condition of the bound circuit and the task.
    assert evaluate_circuit.main() == 0
    out = capsys.readouterr().out
    circuits = out.split("CIRCUITS", 1)[1].split("TASKS", 1)[0]
    tasks_block = out.split("TASKS", 1)[1].split("CELL GRID", 1)[0]
    assert "condition=nopressure" in circuits
    assert "condition=nopressure" in tasks_block


@pytest.mark.parametrize("flags", [
    [],
    ["--deception-margin-loss", "0.25"],
])
def test_margin_for_nopressure_defaults_to_the_dataset(tiny_far_data, flags):
    """--deception-margin-loss overrides; otherwise the dataset's margin_thresh."""
    import train
    from tasks import get_task

    data_dir, tok = tiny_far_data
    args = train.build_parser().parse_args(
        ["--model", "llama-tiny", "--task", "far", "--deception-condition",
         "nopressure", "--data-dir", str(data_dir), "--batch-size", "2",
         "--max-seq-length", str(SEQ)] + flags)
    train.resolve_args(args)
    args.shuffle_train = False
    state = {}
    get_task("far").build_dataloaders(tok, "llama", None, "cpu", args, state)
    assert state["margin"] == (0.25 if flags else 0.5)


def test_suite_banner_names_the_condition_of_each_circuit_and_task(
        tiny_far_data, monkeypatch, tmp_path):
    """A real (sanity-only) suite on the Format Circuit's run: the suite log
    says which condition the bound circuit was pruned on and which condition
    the task's test set is."""
    import evaluate_circuit

    data_dir, _ = tiny_far_data
    run_dir = _train(monkeypatch, data_dir)
    root = tmp_path / "suite"
    monkeypatch.setattr(sys, "argv", [
        "evaluate_circuit.py", "--circuit", f"F={run_dir}", "--task-from", run_dir,
        "--evals", "sanity", "--n-random", "1", "--skip-wikitext",
        "--output-dir", str(root)])
    assert evaluate_circuit.main() == 0

    with open(root / "suite.log") as f:
        banner = f.read().split("SUITE", 1)[1].split("CIRCUIT EVALUATION", 1)[0]
    assert re.search(r"circuits\s+F \[condition=nopressure\]", banner), banner
    assert re.search(r"tasks\s+far \[condition=nopressure\]", banner), banner


@pytest.mark.parametrize("runtime_filter, expected_test", [(False, 4), (True, 0)])
def test_runtime_filter_applies_to_nopressure_as_to_honest(
        tiny_far_data, runtime_filter, expected_test):
    """--deception-runtime-filter re-checks val/test against the full model at
    the margin in force (here --deception-margin-loss, which no logit gap of
    the random model reaches); without the flag the stored splits load as is."""
    import train
    from models import ModelAdapter
    from tasks import get_task

    data_dir, tok = tiny_far_data
    full_model = ModelAdapter("llama-tiny").load_full_model("cpu")
    argv = ["--model", "llama-tiny", "--task", "far", "--deception-condition",
            "nopressure", "--data-dir", str(data_dir), "--batch-size", "2",
            "--max-seq-length", str(SEQ), "--deception-margin-loss", "1000"]
    if runtime_filter:
        argv.append("--deception-runtime-filter")
    args = train.build_parser().parse_args(argv)
    train.resolve_args(args)
    args.shuffle_train = False
    state = {}
    train_dl, val_dl, test_dl = get_task("far").build_dataloaders(
        tok, "llama", full_model, "cpu", args, state)
    assert state["margin"] == 1000.0
    assert len(train_dl.dataset) == 4        # train is never re-filtered
    assert len(val_dl.dataset) == len(test_dl.dataset) == expected_test


def test_a_composed_circuit_names_each_operands_condition(tmp_path):
    """A delta such as D-F mixes conditions; the plan names each operand's."""
    from types import SimpleNamespace

    from evaluation.circuits import circuit_condition, condition_of

    runs = {}
    for name, condition in (("D", "deceptive"), ("F", "nopressure")):
        run = tmp_path / name
        run.mkdir()
        (run / "config.json").write_text(json.dumps(
            {"task": "sdr", "deception_condition": condition}))
        runs[name] = str(run)

    atomic = SimpleNamespace(is_atomic=True, operands={"F": runs["F"]})
    delta = SimpleNamespace(is_atomic=False, operands=runs)
    assert circuit_condition(atomic) == "nopressure"
    assert circuit_condition(delta) == "D:deceptive,F:nopressure"
    # A task without conditions never shows one.
    assert condition_of({"task": "std", "deception_condition": "deceptive"}) == "-"
