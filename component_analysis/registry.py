"""
component_analysis/registry.py — what an analysis is, and which ones exist.

An **analysis** is a module. It exposes five names and nothing else is required
of it:

    NAME                 what `--analyses` calls it, and the head-table namespace
    SUBDIR               the directory it writes under, inside the cell
    add_arguments(group) its own CLI flags, registered into an argument group
    estimate(ctx) -> str one line for `--dry-run`: how much work it would be
    run(ctx) -> dict     the analysis; returns head-table column updates

`run` returns `{component key: {column: value}}` and the CLI merges it with the
analysis's `NAME` as the namespace, so a column lands as `<NAME>.<column>` and
two analyses cannot collide. It writes its own JSON and PNG under
`ctx.subdir()`; the head table is written once, by the CLI, after every
analysis has run.

`ANALYSES` is the one place registration happens: a new analysis is one line
here and one new module. That is deliberate — tickets 03, 04, 07 and 08 are
implemented on sibling branches cut from the same commit, and one line each in
one list is the smallest thing the orchestrator has to rebase.

Nothing here imports `hooks.py` or nnsight at module level, and an analysis
module must not either: `--dry-run` is a login-node mode and the login node
has no nnsight 0.7.0.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from typing import List, Optional

#: The built-in analyses, in the order they run: descriptive ones first, so a
#: causal analysis can read a column an earlier one wrote.
#:
#: One line per analysis, and the four that block on this scaffold each have
#: their own placeholder line to replace. The blank lines between them are not
#: decoration: four sibling branches each adding a line to the same one-element
#: list conflict on every rebase after the first, and a line of their own,
#: separated, does not.
ANALYSES: List[str] = [
    # ticket 03, attention patterns:     "component_analysis.attention",

    # ticket 04, DLA and logit lens:     "component_analysis.dla",

    # ticket 07, per-Component knockout: "component_analysis.knockout",

    # ticket 08, path patching:          "component_analysis.path_patching",
]

#: The five names a module must expose to be an analysis.
REQUIRED = ("NAME", "SUBDIR", "add_arguments", "estimate", "run")


def _module(entry):
    """A registry entry as a module. A dotted path is imported; a module is itself."""
    module = importlib.import_module(entry) if isinstance(entry, str) else entry
    missing = [name for name in REQUIRED if not hasattr(module, name)]
    if missing:
        raise TypeError(
            f"{getattr(module, '__name__', module)} is registered as an "
            f"analysis but does not expose {', '.join(missing)}")
    return module


def registered() -> list:
    """Every registered analysis module, in registration order."""
    return [_module(entry) for entry in ANALYSES]


def names() -> List[str]:
    return [module.NAME for module in registered()]


def parse_names(value: Optional[str]) -> Optional[List[str]]:
    """`--analyses a,b` to `["a", "b"]`; not given stays None, meaning all."""
    if value is None:
        return None
    return [one.strip() for one in value.split(",") if one.strip()]


def select(wanted: Optional[List[str]]) -> list:
    """The modules `--analyses` asks for, in registration order.

    Unknown names are refused by name rather than ignored, because an analysis
    silently not running looks exactly like an analysis that found nothing.
    """
    modules = registered()
    if wanted is None:
        return modules
    by_name = {module.NAME: module for module in modules}
    unknown = [one for one in wanted if one not in by_name]
    if unknown:
        raise ValueError(
            f"--analyses names {', '.join(unknown)}, which "
            f"{'is' if len(unknown) == 1 else 'are'} not registered. "
            f"Registered: {', '.join(by_name) or '(none)'}")
    return [module for module in modules if module.NAME in wanted]


# ==============================================================================
# THE CONTEXT
# ==============================================================================

@dataclass
class AnalysisContext:
    """Everything an analysis is given, and the only way it reaches the model.

    The loaders are built on first use and memoized: a cell whose analyses are
    all descriptive never tokenizes the causal sample, and two analyses that
    both want the sample share one load.
    """

    cli: object
    intake: object
    circuit_spec: object
    task_spec: object
    components: list
    cell_dir: str
    model: object = None
    tokenizer: object = None
    segmentations: Optional[list] = None
    sample: object = None
    device: str = "cuda"
    _loaders: dict = field(default_factory=dict, repr=False)

    @property
    def keys(self) -> list:
        """The Component keys of this circuit, in head-table order."""
        return [component.key for component in self.components]

    def causal_batches(self):
        """The fixed-seed sample, joined by instance id, with both pairs."""
        from component_analysis import dataloaders

        if "causal" not in self._loaders:
            if self.sample is None:
                raise ValueError(
                    f"task {self.task_spec.name!r} has no causal sample, so a "
                    f"causal analysis cannot run on it")
            self._loaders["causal"] = dataloaders.batches_for_task(
                self.task_spec, self.tokenizer, ids=self.sample.ids,
                batch_size=getattr(self.cli, "batch_size",
                                   dataloaders.DEFAULT_BATCH_SIZE))
        return self._loaders["causal"]

    def descriptive_batches(self):
        """The whole test split, item-swap pair only."""
        from component_analysis import dataloaders

        if "descriptive" not in self._loaders:
            self._loaders["descriptive"] = dataloaders.batches_for_task(
                self.task_spec, self.tokenizer, ids=None,
                batch_size=getattr(self.cli, "batch_size",
                                   dataloaders.DEFAULT_BATCH_SIZE))
        return self._loaders["descriptive"]

    def subdir(self, analysis) -> str:
        """The analysis's own directory inside the cell, created on demand.

        `analysis` is the module or, equivalently, its `SUBDIR` string — a
        module that writes from a helper should not have to pass itself around.
        """
        name = analysis if isinstance(analysis, str) else analysis.SUBDIR
        path = os.path.join(self.cell_dir, name)
        os.makedirs(path, exist_ok=True)
        return path

    def write_json(self, analysis, filename: str, payload: dict) -> str:
        """Write one of the analysis's JSON files. Every figure gets one of these."""
        import json

        path = os.path.join(self.subdir(analysis), filename)
        with open(path, "w") as handle:
            json.dump(payload, handle, indent=2)
        return path
