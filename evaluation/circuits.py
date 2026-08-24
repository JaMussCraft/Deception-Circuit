"""
evaluation/circuits.py — what to evaluate, and on what.

`evaluate_circuit.py` used to answer both questions from one run directory: the
circuit was that run's `active_nodes.json` and the task was that run's
`config.json`. The cross-task matrices in
`project_context/prompts/deception_circuit_evaluation.md` need the two
decoupled, so they become two small specs:

    CircuitSpec   a resolved mask object + how it was derived
    TaskSpec      a registered task + the dataset args to build it with

A suite is the cartesian product, one cell per (circuit, task).

Circuits come from `--circuit NAME=RUN_DIR` bindings plus `--expr`
expressions (see evaluation/algebra.py); tasks come from `--task-from RUN_DIR`
(inheriting that run's dataset args) or `--task NAME`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from config import default_hyperparams
from evaluation import algebra
from evaluation.context import geometry_from_masks, load_run_config, resolve_train_args
from evaluation.masks import count_masks, load_circuit_masks, validate_hierarchy
from tasks import get_task, list_tasks

#: Hyperparameters that belong to the *task*, not to the run, and so must be
#: re-derived when `--task NAME` borrows another run's config as a template.
_TASK_HYPERPARAM_KEYS = ("node_epochs", "edge_epochs", "lr", "batch_size",
                         "max_seq_length", "train_samples", "val_samples",
                         "test_samples")

#: config.json keys that identify which dataset a task reads.
_DATASET_KEYS = ("data_dir", "std_variant", "deception_condition", "test_samples")


@dataclass
class CircuitSpec:
    """One circuit to evaluate: resolved masks plus where they came from."""

    label: str                      # cell directory name
    masks: dict                     # resolved mask object (uint8 arrays)
    counts: dict                    # count_masks(masks)
    kind: str                       # "atomic" | "leaf" | "head"
    expr: str = None                # source expression, None when atomic
    operands: dict = field(default_factory=dict)   # name -> run_dir
    home_run_dir: str = None        # set only for atomic circuits

    @property
    def is_atomic(self) -> bool:
        return self.kind == "atomic"

    def provenance(self) -> dict:
        return {"label": self.label, "kind": self.kind, "expr": self.expr,
                "operands": dict(self.operands),
                "home_run_dir": self.home_run_dir,
                "counts": {k: v["active"] for k, v in self.counts.items()}}


@dataclass
class TaskSpec:
    """One task to evaluate on: the registered task plus its dataset args."""

    name: str                       # registered task name
    label: str                      # cell directory name
    args: object                    # argparse.Namespace of train.py args
    home_run_dir: str = None        # the run the dataset args came from

    def build(self):
        return get_task(self.name)

    def provenance(self) -> dict:
        return {"label": self.label, "task": self.name,
                "home_run_dir": self.home_run_dir,
                "dataset": {k: getattr(self.args, k, None) for k in _DATASET_KEYS}}


# ==============================================================================
# BINDINGS
# ==============================================================================

def norm_run_dir(run_dir: str) -> str:
    """The canonical spelling of a run directory.

    Run directories are compared as strings in several places — the same run
    bound twice, a circuit's home run against a task's — and shell completion
    happily hands us a trailing slash, so a raw string compare would silently
    treat `out/far` and `out/far/` as two different runs (skipping sanity,
    double-labelling tasks). Normalise once, at every entry point.
    """
    return os.path.normpath(os.path.abspath(os.path.expanduser(run_dir.strip())))


def parse_binding(text: str):
    """`NAME=RUN_DIR` -> (name, run_dir)."""
    if "=" not in text:
        raise ValueError(
            f"--circuit expects NAME=RUN_DIR, got {text!r}. Names are "
            f"[A-Za-z0-9_]+ and are what circuit expressions refer to.")
    name, run_dir = text.split("=", 1)
    name = name.strip()
    if not algebra._NAME_RE.fullmatch(name):
        raise ValueError(
            f"circuit name {name!r} is not [A-Za-z0-9_]+ — expressions could "
            f"not refer to it.")
    return name, norm_run_dir(run_dir)


def bindings_from_cli(cli) -> dict:
    """Ordered `name -> run_dir`, from the positional run_dir and --circuit."""
    out = {}
    if getattr(cli, "run_dir", None):
        out["self"] = norm_run_dir(cli.run_dir)
    for text in getattr(cli, "circuit", None) or []:
        name, run_dir = parse_binding(text)
        if name in out and out[name] != run_dir:
            raise ValueError(f"circuit {name!r} is bound twice, to different runs")
        out[name] = run_dir
    if not out:
        raise ValueError("no circuits given — pass a run directory or --circuit NAME=RUN_DIR")
    return out


def load_operands(bindings: dict):
    """Load every bound circuit and assert they describe the same model.

    Set algebra across two geometries is meaningless, and so is evaluating a
    Gemma circuit on a Llama forward, so this is checked before any algebra
    runs rather than surfacing as a shape error deep inside a hook.
    """
    operands, configs, geometry = {}, {}, None
    reference_name = None
    for name, run_dir in bindings.items():
        masks = load_circuit_masks(run_dir)
        geom = geometry_from_masks(masks)
        validate_hierarchy(masks, num_heads=geom["num_heads"],
                           head_dim=geom["head_dim"], label=f"circuit '{name}'")
        config = load_run_config(run_dir)
        if geometry is None:
            geometry, reference_name = geom, name
        elif geom != geometry:
            raise ValueError(
                f"circuit '{name}' ({run_dir}) has geometry {geom}, but circuit "
                f"'{reference_name}' has {geometry} — they are from different "
                f"models and cannot be combined or compared.")
        first_model = configs[reference_name]["model"] if configs else config.get("model")
        if config.get("model") != first_model:
            raise ValueError(
                f"circuit '{name}' was trained on {config.get('model')!r} but "
                f"circuit '{reference_name}' on {first_model!r}.")
        operands[name] = masks
        configs[name] = config
    return operands, configs, geometry


# ==============================================================================
# CIRCUIT SPECS
# ==============================================================================

def _expression_list(cli, bindings: dict):
    """[(label_or_None, expr_text), ...] from --expr / --xor / --all-pairs-delta.

    With none of those given, every bound circuit is evaluated on its own.
    """
    out = []
    for text in getattr(cli, "expr", None) or []:
        label, _, expr = text.partition("=")
        if expr and algebra._NAME_RE.fullmatch(label.strip()):
            out.append((label.strip(), expr.strip()))
        else:
            out.append((None, text.strip()))
    if getattr(cli, "xor", None):
        names = [n.strip() for n in cli.xor.split(",") if n.strip()]
        out.extend((label, expr) for label, expr in algebra.expand_xor(names))
    if getattr(cli, "all_pairs_delta", False):
        out.extend((label, expr)
                   for label, expr in algebra.expand_all_pairs_delta(bindings))
    if not out:
        out = [(None, name) for name in bindings]
    return out


def _granularities(cli):
    choice = getattr(cli, "compose_granularity", "both") or "both"
    return list(algebra.GRANULARITIES) if choice == "both" else [choice]


def resolve_circuits(cli):
    """(specs, bindings, operands, configs, geometry) for this invocation."""
    bindings = bindings_from_cli(cli)
    operands, configs, geometry = load_operands(bindings)
    granularities = _granularities(cli)

    specs, used_labels = [], {}

    def unique(label):
        if label not in used_labels:
            used_labels[label] = 1
            return label
        used_labels[label] += 1
        return f"{label}_{used_labels[label]}"

    for explicit_label, text in _expression_list(cli, bindings):
        tree = algebra.parse_expr(text)
        algebra.validate_names(tree, operands)
        base = explicit_label or algebra.slug_for(tree)

        if algebra.is_atomic(tree):
            # Passed through untouched — no re-derivation — so the sanity eval
            # stays bit-reproducible against the run's results.json.
            name = tree[1]
            specs.append(CircuitSpec(
                label=unique(base), masks=operands[name],
                counts=count_masks(operands[name]), kind="atomic", expr=None,
                operands={name: bindings[name]}, home_run_dir=bindings[name]))
            continue

        for granularity in granularities:
            masks = algebra.compose(tree, operands, granularity=granularity,
                                    num_heads=geometry["num_heads"],
                                    head_dim=geometry["head_dim"])
            label = unique(f"{base}__{granularity}")
            validate_hierarchy(masks, num_heads=geometry["num_heads"],
                               head_dim=geometry["head_dim"], label=label)
            specs.append(CircuitSpec(
                label=label, masks=masks, counts=count_masks(masks),
                kind=granularity, expr=text,
                operands={n: bindings[n] for n in algebra.expr_names(tree)}))

    return specs, bindings, operands, configs, geometry


# ==============================================================================
# TASK SPECS
# ==============================================================================

def _args_from_run(run_dir: str, cli):
    config = load_run_config(run_dir)
    args, _ = resolve_train_args(config, cli)
    return args


def _args_for_task(name: str, template_config: dict, cli):
    """Dataset args for `--task NAME`, borrowing a bound run's config.

    Deviation from the plan, which said to start from
    `train.build_parser().parse_args([])`: that yields `model=gpt2` and
    `max_seq_length=None`, so nothing would load. Since every bound circuit is
    already forced onto one model by `load_operands`, the model / family /
    data_dir are inherited from the template run and only the per-task
    hyperparameters are re-derived from `config.default_hyperparams`.
    """
    if name not in list_tasks():
        raise ValueError(f"unknown task {name!r}. Choose from {list_tasks()}.")
    config = {k: v for k, v in template_config.items()
              if k not in _TASK_HYPERPARAM_KEYS}
    config["task"] = name
    args, _ = resolve_train_args(config, cli)
    for key, value in default_hyperparams(args.family, name).items():
        if getattr(args, key, None) is None:
            setattr(args, key, value)
    return args


def _dataset_key(args):
    return (args.task,) + tuple(str(getattr(args, k, None)) for k in _DATASET_KEYS)


def _run_slug(run_dir: str) -> str:
    return os.path.basename(os.path.normpath(run_dir)) or "run"


def resolve_tasks(cli, bindings: dict, configs: dict):
    """[TaskSpec] from --task / --task-from, defaulting to the circuits' own tasks."""
    template = configs[next(iter(configs))]
    requested = []          # (args, home_run_dir)

    for run_dir in getattr(cli, "task_from", None) or []:
        run_dir = norm_run_dir(run_dir)
        requested.append((_args_from_run(run_dir, cli), run_dir))
    for name in getattr(cli, "task", None) or []:
        requested.append((_args_for_task(name, template, cli), None))

    if not requested:
        # Default: every bound circuit's own task, deduped.
        for name, run_dir in bindings.items():
            requested.append((_args_from_run(run_dir, cli), run_dir))

    specs, seen = [], {}
    for args, run_dir in requested:
        key = _dataset_key(args)
        if key in seen:
            continue
        seen[key] = True
        specs.append(TaskSpec(name=args.task, label=args.task, args=args,
                              home_run_dir=run_dir))

    # Two specs for the same task must not land in the same cell directory.
    by_name = {}
    for spec in specs:
        by_name.setdefault(spec.name, []).append(spec)
    for name, group in by_name.items():
        if len(group) < 2:
            continue
        for i, spec in enumerate(group):
            suffix = _run_slug(spec.home_run_dir) if spec.home_run_dir else f"cli{i}"
            spec.label = f"{name}@{suffix}"
    return specs
