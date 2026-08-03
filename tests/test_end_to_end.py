"""
End-to-end CPU test for evaluate_circuit.py.

Builds a throwaway "run directory" for a 2-layer random Llama and a synthetic
task, then runs the real CLI over it — the real context builder, the real mask
loader, the real generic evaluator, the real null sampler, the real wikitext
harness, the real reporting and JSON writing. Only three things are faked: the
model loader (so no 16 GB download), the tokenizer, and the wikitext corpus (so
no network).

The synthetic task's `evaluate` calls the repo's own
`dataset.std_llama.run_evaluation`, so eval 1's generic-vs-repo cross-check is
comparing the generic evaluator against the actual production code path — which
is the assertion that makes the rest of the harness trustworthy.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest
import torch
from torch.utils.data import DataLoader, Dataset

import evaluate_circuit
from config import NodePruningConfig
from tasks import Task
from tests.helpers import TINY, build_tiny_pair

pytest_plugins = []

SEQ = 12
N_SAMPLES = 24
BATCH = 4


# ==============================================================================
# FAKES
# ==============================================================================

class FakeTokenizer:
    """Just enough tokenizer for run_evaluation and the wikitext harness."""

    bos_token_id = 1
    pad_token = "<pad>"
    pad_token_id = 0

    def decode(self, ids, **kwargs):
        if isinstance(ids, int):
            ids = [ids]
        if torch.is_tensor(ids):
            ids = ids.reshape(-1).tolist()
        return "".join(f"<{int(i)}>" for i in ids)

    def __call__(self, text, add_special_tokens=False, **kwargs):
        rng = np.random.default_rng(len(text))
        return {"input_ids": rng.integers(0, TINY["vocab"], size=4096).tolist()}


class TinyDataset(Dataset):
    """Two aligned streams differing at one position, like STD."""

    def __init__(self, n, seq, vocab, seed=0):
        rng = np.random.default_rng(seed)
        self.processed_data = []
        for i in range(n):
            ids = rng.integers(0, vocab, size=seq).tolist()
            corrupt = list(ids)
            flip = 2 + int(rng.integers(0, 3))
            corrupt[flip] = (corrupt[flip] + 7) % vocab
            prefix = seq - int(rng.integers(0, 3))     # some right padding
            self.processed_data.append({
                "input_ids": ids,
                "corrupted_input_ids": corrupt,
                "prefix_length": prefix,
                "target_token": int(rng.integers(0, vocab)),
                "distractor_token": int(rng.integers(0, vocab)),
                # run_evaluation reaches into processed_data for these.
                "statement": f"statement {i}",
                "clean_stip": "true",
                "pressure": "none",
            })

    def __len__(self):
        return len(self.processed_data)

    def __getitem__(self, i):
        item = self.processed_data[i]
        mask = torch.zeros(len(item["input_ids"]), dtype=torch.long)
        mask[: item["prefix_length"]] = 1
        return {
            "input_ids": torch.tensor(item["input_ids"], dtype=torch.long),
            "corrupted_input_ids": torch.tensor(item["corrupted_input_ids"],
                                                dtype=torch.long),
            "attention_mask": mask,
            "target_token": torch.tensor(item["target_token"], dtype=torch.long),
            "distractor_token": torch.tensor(item["distractor_token"], dtype=torch.long),
            "prefix_length": torch.tensor(item["prefix_length"], dtype=torch.long),
        }


class TinyTask(Task):
    name = "tinystd"
    display_name = "Tiny synthetic STD"

    def build_dataloaders(self, tokenizer, family, full_model, device, args, state):
        make = lambda n, seed: DataLoader(
            TinyDataset(n, args.max_seq_length, TINY["vocab"], seed),
            batch_size=args.batch_size, shuffle=False)
        return make(4, 1), make(4, 2), make(args.test_samples, 3)

    def pred_spec(self, batch):
        return {"pred_pos": batch["prefix_length"] - 1,
                "target": batch["target_token"],
                "distractor": batch["distractor_token"]}

    def evaluate(self, model, name, full_model, loader, device, tokenizer, state):
        # The repo's own evaluation code, so the cross-check is meaningful.
        from dataset.std_llama import run_evaluation
        return run_evaluation(model, name, full_model, loader, device,
                              verbose=False, tokenizer=tokenizer)


def tiny_circuit_masks():
    n_layers, n_heads, head_dim = TINY["layers"], TINY["heads"], TINY["head_dim"]
    rng = np.random.default_rng(0)

    heads, neurons, hidden, output = {}, {}, {}, {}
    attn_blocks = np.array([1, 0], dtype=np.uint8)
    mlp_blocks = np.array([1, 1], dtype=np.uint8)
    for l in range(n_layers):
        h = np.zeros(n_heads, dtype=np.uint8)
        nrn = np.zeros(n_heads * head_dim, dtype=np.uint8)
        if attn_blocks[l]:
            drawn = rng.choice(n_heads, size=2, replace=False)
            h[drawn] = 1
            for head in drawn:
                dims = rng.choice(head_dim, size=3, replace=False)
                nrn[head * head_dim + dims] = 1
        heads[str(l)] = h
        neurons[str(l)] = nrn

        hid = np.zeros(TINY["intermediate"], dtype=np.uint8)
        out = np.zeros(TINY["hidden"], dtype=np.uint8)
        if mlp_blocks[l]:
            hid[rng.choice(TINY["intermediate"], size=9, replace=False)] = 1
            out[rng.choice(TINY["hidden"], size=5, replace=False)] = 1
        hidden[str(l)] = hid
        output[str(l)] = out

    return {"attention_blocks": attn_blocks, "mlp_blocks": mlp_blocks,
            "attention_heads": heads, "attention_neurons": neurons,
            "mlp_hidden": hidden, "mlp_output": output}


# ==============================================================================
# FIXTURE
# ==============================================================================

@pytest.fixture
def tiny_run(tmp_path, monkeypatch):
    import tasks
    from evaluation import masks as M
    from models import MODEL_REGISTRY, ModelAdapter

    monkeypatch.setitem(MODEL_REGISTRY, "llama-tiny", ("llama-tiny", "llama"))
    monkeypatch.setitem(tasks._TASKS, "tinystd", TinyTask)

    # Same weights on both sides, eager attention so all-gates-open is exact.
    plain, pruned = build_tiny_pair(attn_implementation="eager")
    monkeypatch.setattr(ModelAdapter, "load_tokenizer", lambda self: FakeTokenizer())
    monkeypatch.setattr(ModelAdapter, "load_full_model", lambda self, device: plain)
    monkeypatch.setattr(ModelAdapter, "build_node_model",
                        lambda self, cfg, device: pruned)

    # No network: a deterministic stand-in corpus of the right shape.
    import evaluation.wikitext as W

    def fake_blocks(ctx):
        g = torch.Generator().manual_seed(7)
        blocks = torch.randint(0, TINY["vocab"],
                               (ctx.cli.wikitext_blocks, ctx.cli.wikitext_block_size),
                               generator=g)
        blocks[:, 0] = FakeTokenizer.bos_token_id
        return W._cache_blocks(ctx, blocks)

    monkeypatch.setattr(W, "load_wikitext_blocks", fake_blocks)

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "config.json").write_text(json.dumps({
        "model": "llama-tiny", "task": "tinystd", "family": "llama",
        "edge_pruning": False, "skip_node_pruning": False, "seed": 42,
        "batch_size": BATCH, "max_seq_length": SEQ,
        "train_samples": 4, "val_samples": 4, "test_samples": N_SAMPLES,
        "node_lambda_sparsity": 0.7, "data_dir": "./data/datasets",
        "node_config": NodePruningConfig().__dict__,
    }))

    circuit = tiny_circuit_masks()
    M.validate_hierarchy(circuit, num_heads=TINY["heads"], head_dim=TINY["head_dim"])
    (run_dir / "active_nodes.json").write_text(json.dumps({
        "active_heads": {}, "active_mlps": [], "masks": M.as_lists(circuit),
    }))
    (run_dir / "results.json").write_text(json.dumps({
        "baseline": {"accuracy": 1.0, "logit_diff": 1.0, "kl_div": 0.0,
                     "exact_match": 1.0},
        "node_eval": None,
    }))
    return run_dir


def run_cli(monkeypatch, run_dir, *extra):
    argv = ["evaluate_circuit.py", str(run_dir)] + list(extra)
    monkeypatch.setattr("sys.argv", argv)
    return evaluate_circuit.main()


def read_json(run_dir, *parts):
    with open(os.path.join(str(run_dir), "evaluations", *parts)) as f:
        return json.load(f)


# ==============================================================================
# TESTS
# ==============================================================================

def test_dry_run_writes_nothing(tiny_run, monkeypatch, capsys):
    assert run_cli(monkeypatch, tiny_run, "--dry-run", "--n-random", "5") == 0
    assert not os.path.exists(os.path.join(str(tiny_run), "evaluations"))
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "all 5 samples size-matched" in out


def test_full_run_interchange(tiny_run, monkeypatch):
    code = run_cli(monkeypatch, tiny_run, "--n-random", "5",
                   "--wikitext-blocks", "4", "--wikitext-block-size", "16",
                   "--wikitext-batch-size", "2", "--strict")
    assert code == 0, "a verification check failed"

    sanity = read_json(tiny_run, "interchange", "sanity.json")
    assert sanity["cross_check"]["ran"] and sanity["cross_check"]["ok"], \
        sanity["cross_check"]
    assert sanity["all_open"]["ok"], sanity["all_open"]
    assert sanity["rows"]["full_open"]["exact_match"] == 1.0
    assert sanity["rows"]["full_open"]["kl_div"] < 1e-6
    assert sanity["n"] == N_SAMPLES
    assert sanity["batch_size"] == BATCH

    null = read_json(tiny_run, "interchange", "null.json")
    assert null["n"] == 5 and not null["size_mismatches"]
    assert len(null["rows"]) == 5
    for key in ("accuracy", "logit_diff", "kl_div", "exact_match"):
        assert key in null["stats"]
        assert 0.0 <= null["stats"][key]["percentile"] <= 100.0

    knock = read_json(tiny_run, "interchange", "knockout.json")
    assert knock["wikitext"]["floor_ok"], knock["wikitext"]["floor"]
    assert knock["wikitext"]["floor"]["kl_per_token"] < 1e-6
    assert abs(knock["wikitext"]["floor"]["ppl_ratio"] - 1.0) < 1e-6
    assert len(knock["wikitext"]["null"]["rows"]) == 5
    assert knock["task"]["knockout"]["argmax"]["n_distinct"] >= 1

    summary = read_json(tiny_run, "interchange", "summary.json")
    assert summary["verification"]["all_open_equals_full"] is True
    assert summary["failures"] == []
    index = read_json(tiny_run, "index.json")
    assert set(index["interchange"]["evals"]) == {"sanity", "knockout", "null"}

    assert os.path.exists(os.path.join(
        str(tiny_run), "evaluations", "interchange", "plots",
        "null_distribution.pdf"))
    assert os.path.exists(os.path.join(
        str(tiny_run), "evaluations", "interchange", "random_circuits.json"))


def test_reproduction_delta_passes_against_its_own_numbers(tiny_run, monkeypatch):
    """Feed eval 1's own output back in as results.json:node_eval — the delta
    table must then come out clean, which is what it will do on a real run."""
    run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--n-random", "1")
    observed = read_json(tiny_run, "interchange", "sanity.json")["rows"]["discovered"]

    results = json.loads((tiny_run / "results.json").read_text())
    results["node_eval"] = {k: observed[k] for k in
                            ("accuracy", "logit_diff", "kl_div", "exact_match")}
    (tiny_run / "results.json").write_text(json.dumps(results))

    assert run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--n-random", "1",
                   "--strict") == 0
    sanity = read_json(tiny_run, "interchange", "sanity.json")
    assert sanity["delta"]["ok"], sanity["delta"]["rows"]
    assert sanity["delta"]["max_delta"] < 1e-9


def test_strict_flags_a_bad_reproduction(tiny_run, monkeypatch):
    results = json.loads((tiny_run / "results.json").read_text())
    results["node_eval"] = {"accuracy": 0.123, "logit_diff": 9.9,
                            "kl_div": 0.0, "exact_match": 0.1}
    (tiny_run / "results.json").write_text(json.dumps(results))

    assert run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--strict") == 1
    summary = read_json(tiny_run, "interchange", "summary.json")
    assert any("reproduce" in f for f in summary["failures"])


@pytest.mark.parametrize("scheme", ["zero", "mean"])
def test_other_ablation_schemes_run(tiny_run, monkeypatch, scheme):
    code = run_cli(monkeypatch, tiny_run, "--ablation", scheme,
                   "--evals", "sanity", "knockout", "--n-random", "2",
                   "--wikitext-blocks", "4", "--wikitext-block-size", "16",
                   "--wikitext-batch-size", "2")
    assert code == 0

    sanity = read_json(tiny_run, scheme, "sanity.json")
    # All gates open reaches no ablation site, so the anchor is the full model
    # under every scheme.
    assert sanity["all_open"]["ok"], sanity["all_open"]
    assert sanity["cross_check"]["ok"], sanity["cross_check"]

    knock = read_json(tiny_run, scheme, "knockout.json")
    assert knock["wikitext"]["floor_ok"], knock["wikitext"]["floor"]

    index = read_json(tiny_run, "index.json")
    assert scheme in index


def test_sanity_granularity_coarse(tiny_run, monkeypatch):
    """--sanity-granularity coarse evaluates a strictly larger circuit, keeps
    every self-check, and drops the reproduction comparison."""
    results = json.loads((tiny_run / "results.json").read_text())
    results["node_eval"] = {"accuracy": 0.123, "logit_diff": 9.9,
                            "kl_div": 0.0, "exact_match": 0.1}
    (tiny_run / "results.json").write_text(json.dumps(results))

    # The same bogus node_eval makes the default granularity exit 1 (above), so
    # a clean exit here is only possible because the check was dropped.
    assert run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--strict",
                   "--sanity-granularity", "coarse") == 0

    sanity = read_json(tiny_run, "interchange", "sanity.json")
    assert sanity["granularity"] == "coarse"
    assert sanity["delta"] is None
    assert sanity["all_open"]["ok"], sanity["all_open"]
    assert sanity["cross_check"]["ok"], sanity["cross_check"]

    counts, summary = sanity["counts"], read_json(tiny_run, "interchange", "summary.json")
    discovered = summary["circuit"]["counts"]
    assert summary["sanity_circuit"]["granularity"] == "coarse"
    for key in ("attention_blocks", "mlp_blocks", "attention_heads"):
        assert counts[key] == discovered[key], key
    for key in ("attention_neurons", "mlp_hidden", "mlp_output"):
        assert counts[key]["active"] > discovered[key]["active"], key


def test_sanity_granularity_defaults_to_all(tiny_run, monkeypatch):
    run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--n-random", "1")
    sanity = read_json(tiny_run, "interchange", "sanity.json")
    assert sanity["granularity"] == "all"
    assert sanity["counts"] == read_json(
        tiny_run, "interchange", "summary.json")["circuit"]["counts"]


def test_shared_reference_matches_separate(tiny_run, monkeypatch):
    run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--n-random", "1")
    separate = read_json(tiny_run, "interchange", "sanity.json")["rows"]["discovered"]

    run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--n-random", "1",
            "--reference", "shared")
    shared = read_json(tiny_run, "interchange", "sanity.json")["rows"]["discovered"]

    for key in ("accuracy", "logit_diff", "kl_div", "exact_match"):
        assert abs(separate[key] - shared[key]) < 1e-6, key


def test_log_appends_across_invocations(tiny_run, monkeypatch):
    run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--n-random", "1")
    run_cli(monkeypatch, tiny_run, "--evals", "sanity", "--n-random", "1")
    log = os.path.join(str(tiny_run), "evaluations", "interchange", "evaluation.log")
    with open(log) as f:
        text = f.read()
    assert text.count("EVAL 1 — SANITY CHECK") == 2


def test_null_shard_matches_the_contiguous_run(tiny_run, monkeypatch):
    run_cli(monkeypatch, tiny_run, "--evals", "null", "--n-random", "4",
            "--skip-wikitext")
    whole = read_json(tiny_run, "interchange", "null.json")["rows"]

    run_cli(monkeypatch, tiny_run, "--evals", "null", "--null-start", "2",
            "--null-count", "2", "--skip-wikitext")
    shard = read_json(tiny_run, "interchange", "null.json")["rows"]

    assert [r["index"] for r in shard] == [2, 3]
    for row in shard:
        match = next(r for r in whole if r["index"] == row["index"])
        assert abs(row["accuracy"] - match["accuracy"]) < 1e-9
        assert abs(row["logit_diff"] - match["logit_diff"]) < 1e-6
