"""
component_analysis/intake.py — circuits, reference circuits, tasks, and where
their results land.

Circuits enter exactly as they do for the evaluator: `--circuit NAME=RUN_DIR`
bindings plus `--expr` set algebra, resolved by `evaluation/circuits.py` with
no Session in sight. On top of that this adds two things the evaluator has no
use for:

  * **reference circuits** — further `--reference NAME=RUN_DIR` bindings that
    are never evaluated on their own. Each one becomes a membership column on
    the head table, so that a Component shared with the honest twin and a
    deception-specific one are distinguishable in one table rather than by
    diffing two.
  * **the analysis cell layout** — `outputs/_analyses/<suite>/<circuit>/<task>/`.
    A composed circuit has no home run directory to write into, which is why
    analyses get their own root rather than the evaluator's
    `<run_dir>/evaluations`.

Nothing here loads a model. `num_key_value_heads` is the one piece of geometry
no mask object records, and it is read from the HuggingFace *config* (a small
JSON, already in the local cache), never from weights.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from evaluation import circuits as circuit_intake
from evaluation.context import geometry_from_masks, load_run_config
from evaluation.masks import load_circuit_masks, validate_hierarchy

ANALYSES_DIRNAME = "_analyses"


@dataclass
class Intake:
    """Everything the analyses need before a model is loaded."""

    circuits: list                      # [CircuitSpec]
    tasks: list                         # [TaskSpec]
    references: dict = field(default_factory=dict)   # name -> mask object
    reference_run_dirs: dict = field(default_factory=dict)   # name -> run_dir
    geometry: dict = field(default_factory=dict)
    model: str = None
    base_run_dir: str = None

    def provenance(self) -> dict:
        return {"model": self.model, "geometry": dict(self.geometry),
                "references": dict(self.reference_run_dirs)}


# ==============================================================================
# GEOMETRY
# ==============================================================================

def num_key_value_heads(model_name: str, *, hf_token=None, override=None) -> int:
    """How many KV heads the model has, for the head table's `kv_group`.

    Under grouped-query attention a K or V receiver is shared by
    `num_heads // num_kv_heads` query heads, so patching one head's K without
    knowing its group silently patches its neighbours too (ADR-0001). The mask
    object cannot say — it has no KV gates — so this reads the HF config, which
    is a few kilobytes of JSON and is already in the local cache for every
    model this repo trains on. `override` is the escape hatch for a model whose
    config is not reachable, and for the tiny test models.
    """
    if override is not None:
        return int(override)
    from models import MODEL_REGISTRY
    if model_name not in MODEL_REGISTRY:
        raise ValueError(
            f"unknown model {model_name!r}; pass --num-kv-heads to say how many "
            f"key/value heads it has.")
    from transformers import AutoConfig
    config = AutoConfig.from_pretrained(MODEL_REGISTRY[model_name][0],
                                        token=hf_token)
    return int(getattr(config, "num_key_value_heads", None)
               or config.num_attention_heads)


# ==============================================================================
# RESOLUTION
# ==============================================================================

def reference_bindings(cli) -> dict:
    """Ordered `name -> run_dir` from --reference."""
    out = {}
    for text in getattr(cli, "reference", None) or []:
        name, run_dir = circuit_intake.parse_binding(text)
        if name in out and out[name] != run_dir:
            raise ValueError(
                f"reference {name!r} is bound twice, to different runs")
        out[name] = run_dir
    return out


def resolve_intake(cli) -> Intake:
    """Circuits, references and tasks for one invocation.

    References are resolved through the same `load_operands` the circuits use,
    so a reference from a different model or a different geometry fails here
    rather than as a shape error inside an analysis.
    """
    specs, bindings, _operands, configs, geometry = \
        circuit_intake.resolve_circuits(cli)
    tasks = circuit_intake.resolve_tasks(cli, bindings, configs)

    refs = reference_bindings(cli)
    clash = sorted(set(refs) & set(bindings))
    if clash:
        raise ValueError(
            f"{', '.join(clash)} is bound both as a circuit and as a reference. "
            f"Reference names label membership columns, so they must be "
            f"distinct from the names expressions refer to.")

    base_name = next(iter(bindings))
    model = configs[base_name].get("model")
    references = {}
    for name, run_dir in refs.items():
        masks = load_circuit_masks(run_dir)
        geom = geometry_from_masks(masks)
        if geom != geometry:
            raise ValueError(
                f"reference '{name}' ({run_dir}) has geometry {geom}, but the "
                f"circuits have {geometry} — they are from different models.")
        ref_model = load_run_config(run_dir).get("model")
        if ref_model != model:
            raise ValueError(
                f"reference '{name}' was trained on {ref_model!r} but the "
                f"circuits on {model!r}.")
        validate_hierarchy(masks, num_heads=geometry["num_heads"],
                           head_dim=geometry["head_dim"],
                           label=f"reference '{name}'")
        references[name] = masks

    return Intake(circuits=specs, tasks=tasks, references=references,
                  reference_run_dirs=refs, geometry=geometry, model=model,
                  base_run_dir=bindings[base_name])


# ==============================================================================
# LAYOUT
# ==============================================================================

def default_suite_name() -> str:
    return time.strftime("analysis_%y%m%d-%H%M%S")


def analyses_root(cli, base_run_dir: str) -> str:
    """`outputs/_analyses/<suite>` — sibling of `_suites`, or --output-dir.

    Composed circuits have no home run directory, and a cell is a (circuit,
    task) pair rather than a run, so analyses never write inside a run
    directory even when the circuit happens to be atomic.
    """
    if getattr(cli, "output_dir", None):
        return cli.output_dir
    outputs = os.path.dirname(os.path.dirname(os.path.abspath(base_run_dir)))
    suite = getattr(cli, "suite_name", None) or default_suite_name()
    return os.path.join(outputs, ANALYSES_DIRNAME, suite)


def cell_dir(root: str, circuit_spec, task_spec) -> str:
    """`<root>/<circuit>/<task>` — one directory per analysed cell."""
    return os.path.join(root, circuit_spec.label, task_spec.label)
