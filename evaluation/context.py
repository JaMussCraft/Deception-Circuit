"""
evaluation/context.py — the shared substrate every evaluation runs on.

Two objects, because a suite evaluates many circuits on many tasks but may only
load the model once:

  `Session`      the per-process singletons — device, tokenizer, node model,
                 optional full model, per-task dataloaders, per-task mean banks
                 and reference-logit caches, the wikitext block cache.

  `EvalContext`  one (circuit, task) cell. Holds that cell's masks, knockout,
                 random-circuit null and output directory, and delegates
                 everything heavy to its session. This is the object the
                 evaluations in `evaluation/` see, and its surface is unchanged
                 from when it was built by `build_context`.

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
    "joint_tasks", "joint_scale_epochs",
)

#: Prompt variants `Task.build_variant_dataloader` may be asked for.
PROMPT_VARIANTS = ("no_pressure", "honest_instruction")


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
    if not run_dir:
        return None
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
# SESSION
# ==============================================================================

class Session:
    """Per-process state shared by every cell of a suite.

    The model is loaded once. Dataloaders, mean banks and reference-logit caches
    are keyed by *task label*, because they describe a prompt distribution, not
    a circuit; the wikitext caches are global because the wikitext stream is the
    same for every cell.
    """

    def __init__(self, cli, base_run_dir, base_run_config, base_args, node_cfg,
                 geometry, circuits, tasks):
        self.cli = cli
        self.base_args = base_args
        self.device = cli.device
        self.base_run_dir = base_run_dir
        self.base_run_config = base_run_config
        self.node_cfg = node_cfg
        self.geometry = geometry
        self.circuits = circuits
        self.tasks = tasks

        self.adapter = None
        self.tokenizer = None
        self.full_model = None
        self.node_model = None

        self._loaders = {}          # task label -> (test, fast, state)
        self._tasks = {}            # task label -> Task after build_dataloaders
        self._mean_banks = {}       # (task label | "-", bank name) -> bank
        self._ref_caches = {}       # task label -> [N, vocab]
        self._variant_loaders = {}  # (task label, variant) -> (loader, reason)
        self._random_sets = {}      # circuit label -> (indices, masks)
        self._wikitext_blocks = None
        self._current_masks = None

    # ---- heavy build ----------------------------------------------------
    def build_heavy(self) -> None:
        import train

        model_name = self.base_args.model
        self.adapter = ModelAdapter(model_name,
                                    hf_token=train.resolve_hf_token(self.base_args))
        self.tokenizer = self.adapter.load_tokenizer()

        if self.cli.reference == "separate":
            self.full_model = self.adapter.load_full_model(self.device)
        self.node_model = self.adapter.build_node_model(self.node_cfg, self.device)
        self._check_geometry(model_name)

    def _check_geometry(self, model_name: str) -> None:
        cfg = self.node_model.config
        got = {"num_heads": cfg.num_attention_heads,
               "head_dim": cfg.hidden_size // cfg.num_attention_heads,
               "num_layers": cfg.num_hidden_layers,
               "intermediate_size": cfg.intermediate_size,
               "hidden_size": cfg.hidden_size}
        for key, value in self.geometry.items():
            if key in got and got[key] != value:
                raise ValueError(
                    f"saved masks describe {key}={value} but {model_name} has "
                    f"{key}={got[key]} — the masks are from a different model.")

    # ---- per-task data --------------------------------------------------
    def loader_for(self, task_spec):
        """(test_loader, fast_loader, state) for a task, built once."""
        if task_spec.label in self._loaders:
            return self._loaders[task_spec.label]

        args = task_spec.args
        task = task_spec.build()
        state = task.prepare(self.tokenizer, self.device)
        # full_model=None is safe: --std-runtime-filter is forced off in
        # resolve_train_args, and no task uses the reference model for anything
        # else at loader-build time.
        _, _, test_dl = task.build_dataloaders(
            self.tokenizer, args.family, None, self.device, args, state)

        bs = self.cli.eval_batch_size or args.batch_size
        fast_dl = (test_dl if bs == test_dl.batch_size else
                   DataLoader(test_dl.dataset, batch_size=bs, shuffle=False))
        if bs != test_dl.batch_size:
            print(f"  Sanity eval pinned to the run's batch size "
                  f"{test_dl.batch_size}; other evaluations use "
                  f"--eval-batch-size {bs}.")

        # Keep this Task: build_dataloaders binds side effects evaluate() needs
        # (e.g. STDTask._run_evaluation). EvalContext must reuse it.
        self._tasks[task_spec.label] = task
        self._loaders[task_spec.label] = (test_dl, fast_dl, state)
        return self._loaders[task_spec.label]

    def variant_loader(self, task_spec, variant: str):
        """(loader, reason) for a prompt variant. loader is None when unavailable.

        Building is lazy and failures are returned, not raised: a prompt that no
        longer fits `--max-seq-length` once the pressure clause is swapped is a
        reason to skip a section, not to lose the results of every evaluation
        that already ran.
        """
        key = (task_spec.label, variant)
        if key in self._variant_loaders:
            return self._variant_loaders[key]

        task = task_spec.build()
        builder = getattr(task, "build_variant_dataloader", None)
        if builder is None:
            result = (None, f"{task.name} has no build_variant_dataloader hook")
        else:
            _, _, state = self.loader_for(task_spec)
            try:
                loader = builder(variant, self.tokenizer, task_spec.args, state)
            except Exception as exc:                       # noqa: BLE001
                result = (None, f"{variant} prompts could not be built: {exc}")
            else:
                if loader is None:
                    result = (None, f"{task.name} does not implement the "
                                    f"'{variant}' prompt variant")
                else:
                    # Same rebatching as loader_for: variant sections are not
                    # reproducing an in-run number, so they get --eval-batch-size.
                    bs = self.cli.eval_batch_size or task_spec.args.batch_size
                    if loader.batch_size != bs:
                        loader = DataLoader(loader.dataset, batch_size=bs,
                                            shuffle=False)
                    result = (loader, "")
        self._variant_loaders[key] = result
        return result

    # ---- per-task caches -------------------------------------------------
    def mean_bank(self, ctx, name="task"):
        key = ("-", name) if name == "wikitext" else (ctx.task_spec.label, name)
        if key in self._mean_banks:
            return self._mean_banks[key]
        if name == "task":
            batches = [ctx.task.model_inputs(b) for b in ctx.test_loader]
            desc = f"Mean bank (task: {ctx.task_spec.label})"
        elif name == "wikitext":
            from evaluation.wikitext import wikitext_stream_batches
            batches = wikitext_stream_batches(ctx)
            desc = "Mean bank (wikitext)"
        else:
            raise ValueError(f"unknown mean bank {name!r}")
        bank = collect_mean_bank(self.node_model, batches, device=self.device,
                                 source=self.cli.mean_source, desc=desc)
        self._mean_banks[key] = bank
        return bank

    def ref_cache_for(self, ctx):
        label = ctx.task_spec.label
        if label in self._ref_caches:
            return self._ref_caches[label]
        from evaluation.metrics import build_ref_cache
        self._ref_caches[label] = build_ref_cache(ctx, ctx.test_loader)
        return self._ref_caches[label]

    def random_set_for(self, circuit_spec):
        """(indices, masks) size-matched to a circuit — shared across its tasks.

        The draw depends only on the circuit's per-layer counts, so the same
        circuit gets the same null on every task it is evaluated against.
        """
        if circuit_spec.label in self._random_sets:
            return self._random_sets[circuit_spec.label]
        cli = self.cli
        n = cli.null_count if cli.null_count is not None else cli.n_random
        indices = list(range(cli.null_start, cli.null_start + n))
        masks = sample_random_mask_set(
            circuit_spec.masks, num_heads=self.geometry["num_heads"],
            head_dim=self.geometry["head_dim"], seed=cli.null_seed, n=n,
            alloc=cli.null_alloc, start=cli.null_start)
        self._random_sets[circuit_spec.label] = (indices, masks)
        return self._random_sets[circuit_spec.label]

    # ---- cells -----------------------------------------------------------
    def context_for(self, circuit_spec, task_spec, out_dir):
        return EvalContext(self, circuit_spec, task_spec, out_dir)


# ==============================================================================
# CONTEXT
# ==============================================================================

class EvalContext:
    """One (circuit, task) cell. Everything the evaluations share."""

    def __init__(self, session: Session, circuit_spec, task_spec, out_dir: str):
        cli = session.cli
        self.session = session
        self.cli = cli
        self.circuit_spec = circuit_spec
        self.task_spec = task_spec

        self.args = task_spec.args
        # Prefer the Session-cached Task once loaders exist — that is the
        # instance build_dataloaders ran on. A fresh build() here is only a
        # stand-in for metadata (metric_columns, pred_spec) before then.
        self._task = task_spec.build()
        self.geometry = session.geometry
        self.device = session.device

        # `run_dir` names the circuit's home run where there is one; it is what
        # the sanity eval reproduces against and what the legacy layout writes
        # under. A composed circuit has neither.
        self.run_dir = circuit_spec.home_run_dir or session.base_run_dir
        self.run_config = (load_run_config(circuit_spec.home_run_dir)
                           if circuit_spec.home_run_dir else session.base_run_config)
        self.run_results = load_run_results(circuit_spec.home_run_dir)

        self.circuit_masks = circuit_spec.masks
        self.counts = circuit_spec.counts
        self.knockout_masks = knockout_masks(self.circuit_masks,
                                             cli.knockout_granularity)
        assert_complement(self.circuit_masks, self.knockout_masks)

        # What the sanity eval loads. Under --sanity-granularity coarse this is a
        # strictly larger circuit than the discovered one, so it does not — and
        # should not — reproduce results.json; sanity.py says so rather than
        # reporting a failed check.
        self.sanity_granularity = getattr(cli, "sanity_granularity", "all")
        self.sanity_masks = (
            coarsen_masks(self.circuit_masks, head_dim=self.geometry["head_dim"])
            if self.sanity_granularity == "coarse" else self.circuit_masks)
        self.sanity_counts = count_masks(self.sanity_masks)
        if self.sanity_granularity != "all":
            validate_hierarchy(self.sanity_masks,
                               num_heads=self.geometry["num_heads"],
                               head_dim=self.geometry["head_dim"],
                               label="coarse-only circuit")

        # Size-matched to *this* cell's circuit (drawn once per circuit).
        self.random_indices, self.random_masks = session.random_set_for(circuit_spec)

        self.out_dir = out_dir
        self.plots_dir = os.path.join(out_dir, "plots")

        # Verification checks that did not pass; --strict turns these into a
        # non-zero exit code.
        self.failures = []

    # ---- session delegation ---------------------------------------------
    @property
    def adapter(self):
        return self.session.adapter

    @property
    def tokenizer(self):
        return self.session.tokenizer

    @property
    def node_model(self):
        return self.session.node_model

    @property
    def full_model(self):
        return self.session.full_model

    @property
    def task(self):
        return self.session._tasks.get(self.task_spec.label, self._task)

    @property
    def test_loader(self):
        return self.session.loader_for(self.task_spec)[0]

    @property
    def fast_loader(self):
        return self.session.loader_for(self.task_spec)[1]

    @property
    def state(self):
        return self.session.loader_for(self.task_spec)[2]

    @property
    def ref_cache(self):
        return self.session._ref_caches.get(self.task_spec.label)

    @property
    def _wikitext_blocks(self):
        return self.session._wikitext_blocks

    @_wikitext_blocks.setter
    def _wikitext_blocks(self, value):
        self.session._wikitext_blocks = value

    def check(self, ok: bool, message: str) -> bool:
        """Record a verification result; returns `ok` so callers can branch."""
        if not ok:
            self.failures.append(message)
        return bool(ok)

    # ---- capability ------------------------------------------------------
    @property
    def has_pred_spec(self) -> bool:
        return self.task.pred_spec(_ProbeBatch()) is not None

    def variant_loader(self, variant: str):
        """(loader, reason) for one prompt variant of this cell's task."""
        return self.session.variant_loader(self.task_spec, variant)

    def prompt_variants_ok(self):
        """(ok, reason) — can this task build both pressure-clause variants?"""
        for variant in PROMPT_VARIANTS:
            loader, reason = self.session.variant_loader(self.task_spec, variant)
            if loader is None:
                return False, reason
        return True, ""

    def requires_ok(self, evaluation):
        """(ok, reason) for an Evaluation's `requires` tuple."""
        for need in evaluation.requires:
            if need == "pred_spec" and not self.has_pred_spec:
                return False, (f"{self.task.name} does not implement pred_spec, "
                               f"which {evaluation.name} needs")
            if need == "wikitext" and self.cli.skip_wikitext:
                return False, "--skip-wikitext was passed"
            if need == "home_run":
                home = self.circuit_spec.home_run_dir
                if not home:
                    return False, (f"circuit '{self.circuit_spec.label}' is "
                                   f"composed ({self.circuit_spec.expr}), so "
                                   f"there is no run whose results.json it "
                                   f"could reproduce")
                if self.task_spec.home_run_dir != home:
                    # Reproducing an in-run number needs the run's own task and
                    # its own dataset args; anything else is a different
                    # experiment wearing the sanity eval's name.
                    return False, (f"circuit '{self.circuit_spec.label}' was "
                                   f"trained in {home}, but this cell evaluates "
                                   f"task '{self.task_spec.label}', so there is "
                                   f"no in-run number to reproduce")
            if need == "prompt_variants":
                ok, reason = self.prompt_variants_ok()
                if not ok:
                    return False, reason
        return True, ""

    # ---- circuits --------------------------------------------------------
    def apply_circuit(self, masks, verify=False):
        """Load a mask object onto the node model."""
        counts = apply_node_masks(self.node_model, masks)
        self.session._current_masks = masks
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
        previous = self.session._current_masks
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
        previous = self.session._current_masks
        open_all_gates(self.node_model)
        try:
            yield self.node_model
        finally:
            self.apply_circuit(previous)

    # ---- ablation --------------------------------------------------------
    def hook_for(self, bank_name="task"):
        """The ablation hook for this invocation's --ablation scheme."""
        if self.cli.ablation == "mean":
            return make_hook("mean", self.mean_bank(bank_name), self.node_model)
        return make_hook(self.cli.ablation)

    def mean_bank(self, name="task"):
        """The mean bank for a prompt distribution, collected on first use.

        Gate values never touch the corrupted stream, so a bank is
        circuit-independent: collected once per task, reused across circuits.
        """
        return self.session.mean_bank(self, name)

    # ---- reference model --------------------------------------------------
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
        """Full-model logits at the prediction position, [N, V], cached per task.

        Eliminates one full-model forward per circuit — ~50 of them in eval 3.
        Only reachable through Task.pred_spec; Task.evaluate wants [B, S, V] and
        reaches into dataloader.dataset.processed_data, so it cannot use this.
        """
        if not self.has_pred_spec:
            return None
        return self.session.ref_cache_for(self)


class _ProbeBatch(dict):
    """Answers `batch[key] - 1` etc. so `pred_spec` can be probed without data."""

    def __missing__(self, key):
        return torch.zeros(1, dtype=torch.long)


# ==============================================================================
# BUILD
# ==============================================================================

def build_session(cli) -> Session:
    """Resolve every circuit and task, then load the model once.

    Under --dry-run nothing heavy is built: no tokenizer, no model, no
    dataloaders — so the whole resolution path is checkable on a login node.
    """
    from evaluation.circuits import resolve_circuits, resolve_tasks

    if cli.ablation not in ABLATION_SCHEMES:
        raise ValueError(f"--ablation must be one of {list(ABLATION_SCHEMES)}")

    circuits, bindings, _operands, configs, geometry = resolve_circuits(cli)
    tasks = resolve_tasks(cli, bindings, configs)

    base_name = next(iter(bindings))
    base_run_dir = bindings[base_name]
    base_config = configs[base_name]
    base_args, node_cfg = resolve_train_args(base_config, cli)

    session = Session(cli, base_run_dir, base_config, base_args, node_cfg,
                      geometry, circuits, tasks)
    if not cli.dry_run:
        session.build_heavy()
    return session


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
