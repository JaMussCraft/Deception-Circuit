"""
evaluation/context.py — the shared substrate every evaluation runs on.

`build_context` turns a run directory plus the eval CLI into an `EvalContext`:
the resolved training args, the task and its test loader, the full model, the
node model with the discovered circuit loaded, the knockout, the random circuit
set, the reference-logit cache and the mean banks. Evaluations compose on top of
it instead of each re-deriving the same objects.

Training args are rebuilt as `train.build_parser().parse_args([])` and then
overlaid with config.json and the eval CLI, so every task default (sample
counts, sequence length, --std-variant, …) is inherited rather than duplicated.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager

import torch
from torch.utils.data import DataLoader

from analysis import apply_node_masks, open_all_gates
from config import NodePruningConfig
from evaluation.ablation import ABLATION_SCHEMES, collect_mean_bank, make_hook
from evaluation.masks import (assert_complement, coarsen_masks, count_masks,
                              knockout_masks, load_circuit_masks,
                              sample_random_mask_set, validate_hierarchy)
from models import MODEL_REGISTRY, ModelAdapter
from tasks import get_task

SCHEMA_VERSION = 1

# Training-config keys copied verbatim from config.json onto the rebuilt args.
_RUN_CONFIG_KEYS = (
    "model", "task", "family", "edge_pruning", "skip_node_pruning", "seed",
    "node_epochs", "edge_epochs", "lr", "batch_size", "max_seq_length",
    "train_samples", "val_samples", "test_samples",
    "node_lambda_sparsity", "edge_lambda_sparsity", "data_dir",
    # Recorded only by runs trained after the std_variant fix; see below.
    "std_variant", "std_runtime_filter", "std_margin_loss",
    # far / sdr / ser: which of <task> and <task>_honest the run was trained on.
    "deception_condition", "deception_runtime_filter", "deception_margin_loss",
)


# ==============================================================================
# RUN DIRECTORY
# ==============================================================================

def load_run_config(run_dir: str) -> dict:
    path = os.path.join(run_dir, "config.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found — is {run_dir} a run directory?")
    with open(path) as f:
        return json.load(f)


def load_run_results(run_dir: str):
    """results.json, or None. Used only for the reference numbers in eval 1."""
    path = os.path.join(run_dir, "results.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def geometry_from_masks(masks: dict) -> dict:
    """Model geometry read off the saved circuit — no model required.

    Lets --dry-run validate everything (feasibility, hierarchy, the random set)
    on a login node without touching CUDA or downloading weights.
    """
    heads = masks.get("attention_heads")
    neurons = masks.get("attention_neurons")
    if not heads or not neurons:
        raise ValueError(
            "saved masks lack attention_heads / attention_neurons, so the "
            "model geometry cannot be recovered from them.")
    any_layer = next(iter(heads))
    num_heads = int(len(heads[any_layer]))
    n_neurons = int(len(neurons[any_layer]))
    if n_neurons % num_heads:
        raise ValueError(
            f"{n_neurons} attention neurons is not a multiple of {num_heads} heads")

    geom = {"num_heads": num_heads, "head_dim": n_neurons // num_heads}
    if "mlp_hidden" in masks:
        geom["intermediate_size"] = int(len(next(iter(masks["mlp_hidden"].values()))))
    if "mlp_output" in masks:
        geom["hidden_size"] = int(len(next(iter(masks["mlp_output"].values()))))
    for key in ("attention_blocks", "mlp_blocks", "layers"):
        if key in masks:
            geom["num_layers"] = int(len(masks[key]))
            break
    else:
        geom["num_layers"] = len(heads)
    return geom


def resolve_train_args(run_config: dict, cli):
    """train.py's args for this run: parser defaults <- config.json <- eval CLI."""
    import train  # imported here so --dry-run stays cheap and cycle-free

    args = train.build_parser().parse_args([])
    for key in _RUN_CONFIG_KEYS:
        if key in run_config:
            setattr(args, key, run_config[key])

    args.family = MODEL_REGISTRY[args.model][1]
    args.output_dir = run_config.get("output_dir")
    args.shuffle_train = False
    args.hf_token = getattr(cli, "hf_token", None)

    # Evaluation never re-filters the splits: the run was trained against the
    # prebuilt ones, and a runtime filter would change what "the test set" means.
    args.std_runtime_filter = False
    args.deception_runtime_filter = False

    if getattr(cli, "data_dir", None):
        args.data_dir = cli.data_dir
    if getattr(cli, "test_samples", None):
        args.test_samples = cli.test_samples

    if args.task == "std":
        if run_config.get("std_variant"):
            args.std_variant = run_config["std_variant"]
            if getattr(cli, "std_variant", None) and cli.std_variant != args.std_variant:
                print(f"  --std-variant {cli.std_variant} overrides the recorded "
                      f"{args.std_variant}")
                args.std_variant = cli.std_variant
        elif getattr(cli, "std_variant", None):
            args.std_variant = cli.std_variant
            print(f"  config.json does not record --std-variant; using "
                  f"--std-variant {args.std_variant} from the command line.")
        else:
            # Runs trained before run_io started recording std_variant. Getting
            # this wrong silently evaluates against the other dataset, so say so
            # every single time.
            print(f"\n  !! --std-variant is not recorded in this run's "
                  f"config.json; defaulting to '{args.std_variant}'.")
            print("     If the run was trained on std_neutral, every number "
                  "below is against the WRONG dataset.")
            print("     Pass --std-variant explicitly to be sure.\n")

    if args.task in ("far", "sdr", "ser") and not run_config.get("deception_condition"):
        # Same failure mode as std_variant: evaluating a deceptive-condition run
        # against <task>_honest silently reports the wrong numbers.
        print(f"\n  !! --deception-condition is not recorded in this run's "
              f"config.json; defaulting to '{args.deception_condition}'.")
        print("     If the run was trained on the honest twin, every number "
              "below is against the WRONG dataset.\n")

    node_cfg = NodePruningConfig(**run_config["node_config"])
    return args, node_cfg


# ==============================================================================
# CONTEXT
# ==============================================================================

class EvalContext:
    """Everything the evaluations share. Built once per invocation."""

    def __init__(self, cli, run_dir, run_config, train_args, node_cfg, task,
                 circuit_masks, geometry):
        self.cli = cli
        self.run_dir = run_dir
        self.run_config = run_config
        self.run_results = load_run_results(run_dir)
        self.args = train_args
        self.node_cfg = node_cfg
        self.task = task
        self.geometry = geometry
        self.device = cli.device

        self.circuit_masks = circuit_masks
        self.counts = count_masks(circuit_masks)
        self.knockout_masks = knockout_masks(circuit_masks, cli.knockout_granularity)

        # What the sanity eval loads. Under --sanity-granularity coarse this is a
        # strictly larger circuit than the discovered one, so it does not — and
        # should not — reproduce results.json; sanity.py says so rather than
        # reporting a failed check.
        self.sanity_granularity = getattr(cli, "sanity_granularity", "all")
        self.sanity_masks = (
            coarsen_masks(circuit_masks, head_dim=geometry["head_dim"])
            if self.sanity_granularity == "coarse" else circuit_masks)
        self.sanity_counts = count_masks(self.sanity_masks)

        self.random_indices = []
        self.random_masks = []

        self.out_dir = os.path.join(cli.output_dir, cli.ablation)
        self.plots_dir = os.path.join(self.out_dir, "plots")

        # Verification checks that did not pass; --strict turns these into a
        # non-zero exit code.
        self.failures = []

        # Heavy state; absent under --dry-run.
        self.adapter = None
        self.tokenizer = None
        self.full_model = None
        self.node_model = None
        self.test_loader = None
        self.fast_loader = None
        self.state = None
        self.ref_cache = None
        self.mean_banks = {}
        self._current_masks = circuit_masks

    def check(self, ok: bool, message: str) -> bool:
        """Record a verification result; returns `ok` so callers can branch."""
        if not ok:
            self.failures.append(message)
        return bool(ok)

    # ---- capability ----------------------------------------------------
    @property
    def has_pred_spec(self) -> bool:
        return self.task.pred_spec(_ProbeBatch()) is not None

    def requires_ok(self, evaluation):
        """(ok, reason) for an Evaluation's `requires` tuple."""
        for need in evaluation.requires:
            if need == "pred_spec" and not self.has_pred_spec:
                return False, (f"{self.task.name} does not implement pred_spec, "
                               f"which {evaluation.name} needs")
            if need == "wikitext" and self.cli.skip_wikitext:
                return False, "--skip-wikitext was passed"
        return True, ""

    # ---- circuits ------------------------------------------------------
    def apply_circuit(self, masks, verify=False):
        """Load a mask object onto the node model."""
        counts = apply_node_masks(self.node_model, masks)
        self._current_masks = masks
        if verify:
            from analysis import assert_masks_equal, extract_node_masks
            from evaluation.masks import as_lists
            assert_masks_equal(as_lists(masks), extract_node_masks(self.node_model))
        return counts

    def gate_sums(self) -> dict:
        """Cheap per-granularity per-layer live-gate counts, straight off the GPU.

        The full round trip is ~722K comparisons; this is the invariant to check
        on every one of the ~100 circuits an evaluation run loads.
        """
        out = {}
        with torch.no_grad():
            for i, block in enumerate(self.node_model.model.layers):
                for key, gate in (("attention_heads", getattr(block.attn, "head_gates", None)),
                                  ("attention_neurons", getattr(block.attn, "neuron_gates", None)),
                                  ("mlp_hidden", getattr(block.mlp, "hidden_gates", None)),
                                  ("mlp_output", getattr(block.mlp, "output_gates", None)),
                                  ("attention_blocks", getattr(block, "attention_block_gate", None)),
                                  ("mlp_blocks", getattr(block, "mlp_block_gate", None))):
                    if gate is not None:
                        n = int(gate().sum().item())
                        if n:
                            out.setdefault(key, {})[str(i)] = n
        return out

    @contextmanager
    def circuit(self, masks, verify=False):
        """Run a block with `masks` loaded, then restore what was loaded before."""
        previous = self._current_masks
        self.apply_circuit(masks, verify=verify)
        try:
            yield self.node_model
        finally:
            self.apply_circuit(previous)

    @contextmanager
    def all_gates_open(self):
        """Run a block with every gate pinned open — the full-model anchor.

        Goes through `open_all_gates` rather than an all-ones mask so it also
        covers any gate the saved masks do not mention; with all gates open the
        dual-stream forward is the plain model, which is the harness's strongest
        self-test.
        """
        previous = self._current_masks
        open_all_gates(self.node_model)
        try:
            yield self.node_model
        finally:
            self.apply_circuit(previous)

    # ---- ablation ------------------------------------------------------
    def hook_for(self, bank_name="task"):
        """The ablation hook for this invocation's --ablation scheme."""
        if self.cli.ablation == "mean":
            return make_hook("mean", self.mean_bank(bank_name), self.node_model)
        return make_hook(self.cli.ablation)

    def mean_bank(self, name="task"):
        """The mean bank for a prompt distribution, collected on first use.

        Gate values never touch the corrupted stream, so a bank is
        circuit-independent: collected once, reused across every circuit.
        """
        if name in self.mean_banks:
            return self.mean_banks[name]
        if name == "task":
            batches = [self.task.model_inputs(b) for b in self.test_loader]
        elif name == "wikitext":
            from evaluation.wikitext import wikitext_stream_batches
            batches = wikitext_stream_batches(self)
        else:
            raise ValueError(f"unknown mean bank {name!r}")
        bank = collect_mean_bank(self.node_model, batches, device=self.device,
                                 source=self.cli.mean_source,
                                 desc=f"Mean bank ({name})")
        self.mean_banks[name] = bank
        return bank

    # ---- reference model ------------------------------------------------
    def reference_logits(self, input_ids, attention_mask):
        """Full-model logits [B, S, V] — the faithfulness reference."""
        with torch.no_grad():
            if self.cli.reference == "separate":
                return self.full_model(input_ids=input_ids,
                                       attention_mask=attention_mask,
                                       use_cache=False).logits
            # shared: no corrupted stream means no gate is applied anywhere, so
            # the prunable model *is* the ungated full model.
            return self.node_model(input_ids=input_ids,
                                   attention_mask=attention_mask,
                                   use_cache=False).logits

    @property
    def reference_model(self):
        """A model object usable as `full_model` in Task.evaluate, or None."""
        return self.full_model if self.cli.reference == "separate" else None

    def ensure_ref_cache(self):
        """Full-model logits at the prediction position, [N, V], cached.

        Eliminates one full-model forward per circuit — ~50 of them in eval 3.
        Only reachable through Task.pred_spec; Task.evaluate wants [B, S, V] and
        reaches into dataloader.dataset.processed_data, so it cannot use this.
        """
        if self.ref_cache is not None or not self.has_pred_spec:
            return self.ref_cache
        from evaluation.metrics import build_ref_cache
        self.ref_cache = build_ref_cache(self, self.test_loader)
        return self.ref_cache


class _ProbeBatch(dict):
    """Answers `batch[key] - 1` etc. so `pred_spec` can be probed without data."""

    def __missing__(self, key):
        return torch.zeros(1, dtype=torch.long)


# ==============================================================================
# BUILD
# ==============================================================================

def build_context(cli) -> EvalContext:
    run_dir = cli.run_dir
    if cli.ablation not in ABLATION_SCHEMES:
        raise ValueError(f"--ablation must be one of {list(ABLATION_SCHEMES)}")

    run_config = load_run_config(run_dir)
    train_args, node_cfg = resolve_train_args(run_config, cli)
    task = get_task(train_args.task)

    circuit = load_circuit_masks(run_dir)
    geometry = geometry_from_masks(circuit)
    validate_hierarchy(circuit, num_heads=geometry["num_heads"],
                       head_dim=geometry["head_dim"], label="discovered circuit")

    ctx = EvalContext(cli, run_dir, run_config, train_args, node_cfg, task,
                      circuit, geometry)
    assert_complement(circuit, ctx.knockout_masks)
    if ctx.sanity_granularity != "all":
        validate_hierarchy(ctx.sanity_masks, num_heads=geometry["num_heads"],
                           head_dim=geometry["head_dim"],
                           label="coarse-only circuit")

    n = cli.null_count if cli.null_count is not None else cli.n_random
    ctx.random_indices = list(range(cli.null_start, cli.null_start + n))
    ctx.random_masks = sample_random_mask_set(
        circuit, num_heads=geometry["num_heads"], head_dim=geometry["head_dim"],
        seed=cli.null_seed, n=n, alloc=cli.null_alloc, start=cli.null_start)

    if cli.dry_run:
        return ctx

    _build_heavy(ctx)
    return ctx


def _build_heavy(ctx: EvalContext) -> None:
    import train

    args = ctx.args
    adapter = ModelAdapter(args.model, hf_token=train.resolve_hf_token(args))
    ctx.adapter = adapter
    ctx.tokenizer = adapter.load_tokenizer()

    ctx.state = ctx.task.prepare(ctx.tokenizer, ctx.device)
    # full_model=None is safe: --std-runtime-filter is forced off above, and no
    # task uses the reference model for anything else at loader-build time.
    _, _, test_dl = ctx.task.build_dataloaders(
        ctx.tokenizer, args.family, None, ctx.device, args, ctx.state)
    ctx.test_loader = test_dl

    bs = ctx.cli.eval_batch_size or args.batch_size
    ctx.fast_loader = (test_dl if bs == test_dl.batch_size else
                       DataLoader(test_dl.dataset, batch_size=bs, shuffle=False))
    if bs != test_dl.batch_size:
        print(f"  Sanity eval pinned to the run's batch size {test_dl.batch_size}; "
              f"other evaluations use --eval-batch-size {bs}.")

    if ctx.cli.reference == "separate":
        ctx.full_model = adapter.load_full_model(ctx.device)
    ctx.node_model = adapter.build_node_model(ctx.node_cfg, ctx.device)

    _check_geometry(ctx)
    ctx.apply_circuit(ctx.circuit_masks, verify=ctx.cli.verify)


def _check_geometry(ctx: EvalContext) -> None:
    cfg = ctx.node_model.config
    got = {"num_heads": cfg.num_attention_heads,
           "head_dim": cfg.hidden_size // cfg.num_attention_heads,
           "num_layers": cfg.num_hidden_layers,
           "intermediate_size": cfg.intermediate_size,
           "hidden_size": cfg.hidden_size}
    for key, value in ctx.geometry.items():
        if key in got and got[key] != value:
            raise ValueError(
                f"saved masks describe {key}={value} but {ctx.args.model} has "
                f"{key}={got[key]} — the masks are from a different model.")


def reference_numbers(ctx: EvalContext):
    """The in-run node evaluation from results.json, if it is there."""
    if not ctx.run_results:
        return None
    node_eval = ctx.run_results.get("node_eval")
    if not node_eval:
        return None
    return {k: v for k, v in node_eval.items() if isinstance(v, (int, float))}


def baseline_numbers(ctx: EvalContext):
    if not ctx.run_results:
        return None
    baseline = ctx.run_results.get("baseline")
    if not baseline:
        return None
    return {k: v for k, v in baseline.items() if isinstance(v, (int, float))}
