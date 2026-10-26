"""
analyze_components.py — component-level analysis of a discovered circuit.

`evaluate_circuit.py` asks whether a circuit is faithful and necessary. This
asks what is *in* it: which attention heads and MLP blocks the circuit contains
(its **Components**), and — in the tickets that follow — where each one reads,
what it writes, and what it depends on.

Circuits enter exactly as they do for the evaluator, through
`--circuit NAME=RUN_DIR` bindings and `--expr` set algebra, so a delta circuit
already evaluated on benchmarks needs no new plumbing. Reference circuits are
extra bindings that are never analysed on their own: each becomes a membership
column, which is how a Component shared with the honest twin is told apart from
a deception-specific one in one table.

Usage:

    # the SDR circuit's Components, annotated with honest-twin membership
    python analyze_components.py --dry-run \\
        --circuit sdr=outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414 \\
        --reference honest=outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525 \\
        --expr sdr

    # the deception-specific delta, leaf granularity, same reference column
    python analyze_components.py --dry-run \\
        --circuit sdr=<sdr_run> --circuit honest_c=<honest_run> \\
        --reference honest=<honest_run> \\
        --expr "delta=sdr \\ honest_c" --compose-granularity leaf \\
        --task-from <sdr_run>

Results land in `outputs/_analyses/<suite>/<circuit>/<task>/`, one cell per
(circuit, task) pair — a composed circuit has no home run directory, so
analyses never write inside one.

**A cell is assembled by running jobs into it.** Each run into a cell that
already has a head table replaces the columns of the analyses it runs and
carries every other column forward, with its coverage meta (`carry_forward`):

    sbatch scripts/analyze_components.sbatch <intake flags> --analyses attention_patterns,dla,knockout --suite-name S
    sbatch scripts/analyze_components.sbatch <intake flags> --analyses path_patching --suite-name S

leaves one table holding all four analyses' columns. A dry run replaces
nothing. The researcher's `role_confirmed` and the roles pass's `roles.*`
columns survive every run by the same rule.

Subcommands come before the flags:

    # propose a Component Role per Component from a finished head table
    python analyze_components.py roles outputs/_analyses/<suite>/<circuit>/<task>
    # the receiver category per head from a finished neutral-twin pass (v2)
    python analyze_components.py receiver-category outputs/_analyses/<suite>/<circuit>/<task>
    # several intakes from one job file, one cell each
    python analyze_components.py batch <job file> [shared flags]

It needs no model and no circuit binding — it reads the head table the analyses
left and applies the pre-registered criteria in `docs/component-roles.md` — so
it is a subcommand rather than a registered analysis. `--help` after the word
`roles` describes its own flags.

`--dry-run` resolves everything on the login node with no GPU and writes three
files per cell: the head table, the `segmentation.json` that says which tokens
each Segment covers on every test instance, and the `sample.json` that names
the instances the causal analyses will run over. Writing the last two is what
stops a plot from later being read against the wrong spans or the wrong
instances. The analyses that need a model are added by later tickets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from component_analysis import dataloaders, instances, intake, registry, sampling
from component_analysis import segmentation as segments
from component_analysis.components import circuit_components, count_components, \
    is_component_of
from component_analysis.head_table import BASE_COLUMNS, COVERAGE_KEY, \
    INSTANCE_SETS_KEY, JSON_NAME as TABLE_JSON, PROTECTED_COLUMNS, RENAMED_KEY, \
    add_declarations, is_appended_row, merge_columns, modernize_columns, \
    modernize_meta, row_key, rows_from_components, write_head_table
from evaluation import circuits as circuit_intake

#: Descriptive analyses run over this split; the causal sample is drawn from it.
ANALYSIS_SPLIT = "test"

#: Subcommands that do not analyse a circuit and so do not take the circuit
#: intake flags at all. `roles` reads a *finished* head table off disk and
#: needs no model, no circuit binding and no task: it is not a registered
#: analysis because a registered analysis runs inside one invocation, from the
#: intake's fresh rows, and never sees the columns a previous run wrote.
SUBCOMMANDS = {"roles": "component_analysis.roles",
               # The receiver category per head from a twin path-patching pass (02b).
               "receiver-category": "component_analysis.receiver_category",
               # Several invocations in one job, one model load (mechanism-analysis 02a).
               "batch": "component_analysis.batch"}


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(
        description="Component-level analysis of node-pruned circuits. "
                    "Subcommands, given before any flag: "
                    + ", ".join(SUBCOMMANDS)
                    + " (try `analyze_components.py roles --help`).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("run_dir", nargs="?", default=None,
                   help="Run directory holding config.json and active_nodes.json. "
                        "Equivalent to --circuit self=<run_dir>.")

    circuit_intake.add_circuit_args(p)
    circuit_intake.add_task_args(p)

    g = p.add_argument_group("reference circuits")
    g.add_argument("--reference", action="append", metavar="NAME=RUN_DIR",
                   help="Annotate every Component with its membership in this "
                        "circuit, as a 'reference.NAME' column. Repeatable. "
                        "Reference circuits are never analysed on their own, so "
                        "the name must not also be bound with --circuit.")

    g = p.add_argument_group("model & data")
    g.add_argument("--num-kv-heads", type=int, default=None,
                   help="Override the model's key/value head count, which sets "
                        "each head's KV group. Default: read from the model's "
                        "HuggingFace config (no weights are downloaded).")
    g.add_argument("--data-dir", default=None, help="Override the recorded --data-dir.")
    g.add_argument("--test-samples", type=int, default=None,
                   help="Shrink the task test set.")
    g.add_argument("--std-variant", default=None, choices=["azaria", "neutral"],
                   help="Which STD dataset the run was trained on.")
    g.add_argument("--hf-token", default=None)

    g = p.add_argument_group("segmentation & sample")
    g.add_argument("--segment", action="append", metavar="NAME=REGEX",
                   help="Add or replace a Segment by regular expression over "
                        "the decoded prompt. Repeatable. Merged with the "
                        "task's default segmentation, which is what a Segment "
                        "of the same name is replaced in. 'readout' and "
                        "'unsegmented' are reserved.")
    g.add_argument("--n-causal", type=int, default=sampling.DEFAULT_N_CAUSAL,
                   help="How many instances the causal analyses (knockout, "
                        "path patching) run over. Descriptive analyses use the "
                        "whole test split.")
    g.add_argument("--seed", type=int, default=sampling.DEFAULT_SEED,
                   help="Seed for the causal sample. Does not touch the run's "
                        "own training seed.")
    g.add_argument("--exclude-ids", default=None, metavar="FILE",
                   help="Draw the causal sample without these instances: a "
                        "sample.json (the selection cell's), a JSON list or one "
                        "id per line. The held-out sample is --seed 1 with the "
                        "seed-0 sample excluded. Recorded in sample.json.")
    g.add_argument("--include-ids", default=None, metavar="FILE",
                   help="Draw the causal sample only from these instances (same "
                        "file forms). With --n-causal at or above their number "
                        "the sample is exactly them, which is how a paired "
                        "comparison across test sets fixes its ids. Ids not in "
                        "the split are reported in sample.json.")

    g = p.add_argument_group("analyses")
    g.add_argument("--analyses", default=None, metavar="NAME[,NAME]",
                   help="Which registered analyses to run, in registration "
                        "order. Default: every registered one, which is "
                        f"currently {', '.join(registry.names()) or '(none)'}.")
    g.add_argument("--batch-size", type=int,
                   default=dataloaders.DEFAULT_BATCH_SIZE,
                   help="Instances per forward pass.")
    g.add_argument("--device", default="cuda",
                   help="Where the model is loaded. Ignored by --dry-run, "
                        "which loads no model.")

    for module in registry.registered():
        module.add_arguments(p.add_argument_group(f"{module.NAME} analysis"))

    g = p.add_argument_group("output")
    g.add_argument("--output-dir", default=None,
                   help="Default: outputs/_analyses/<suite-name>.")
    g.add_argument("--suite-name", default=None,
                   help="Name the analyses directory (default: a timestamp slug).")
    g.add_argument("--dry-run", action="store_true",
                   help="Resolve circuits, references and tasks, coarsen to "
                        "Components and write the head table. No GPU, no model.")
    return p


# ==============================================================================
# HEAD TABLE
# ==============================================================================

def head_table_for(circuit_spec, resolved, *, num_kv_heads: int):
    """The intake rows for one circuit: its Components plus reference columns."""
    geometry = resolved.geometry
    components = circuit_components(
        circuit_spec.masks, num_heads=geometry["num_heads"],
        head_dim=geometry["head_dim"], num_kv_heads=num_kv_heads)

    rows = rows_from_components(components)
    for name, masks in resolved.references.items():
        membership = {
            component.key: {name: is_component_of(
                component, masks, num_heads=geometry["num_heads"],
                head_dim=geometry["head_dim"])}
            for component in components}
        rows = merge_columns(rows, membership, namespace="reference")
    return components, rows


#: Namespaces the intake rebuilds on every run. Never carried from an old table:
#: the fresh intake's value is the right one, whatever an earlier run wrote.
INTAKE_NAMESPACES = ("reference",)

#: The meta keys `write_cell` rebuilds on every run. Every other key of an old
#: table's meta (the roles pass's `roles` block, say) is carried with the table.
INTAKE_META = ("circuit", "task", "intake", "components")


def _rebuilt(column: str, replaced) -> bool:
    """Does this run write `column` afresh, so the old value must not be kept?"""
    if column in BASE_COLUMNS:
        return True
    namespace = column.split(".", 1)[0] if "." in column else None
    return namespace in INTAKE_NAMESPACES or namespace in replaced


def carry_forward(cell_dir: str, rows, *, replaced=()) -> tuple:
    """`(rows, meta)`: a cell's existing columns, carried onto the fresh rows.

    Every run builds its rows from the circuit intake and writes the whole head
    table at the end. A cell is assembled from several jobs, so before the
    analyses run the existing table's columns are copied back onto those rows,
    matched by row key — **all of them except the intake's own and those under
    a namespace in `replaced`**, which is the namespaces of the analyses this
    invocation runs. A rerun of an analysis therefore replaces its whole
    namespace, stale columns included, and touches nothing else; a dry run
    replaces nothing. `role_confirmed` (the researcher's, bare) and `roles.*`
    (the roles pass's, which the CLI never runs) are carried by the same rule
    and need no case of their own.

    Rows:

    * an old row whose key the fresh intake has gets its carried columns;
    * an old row an analysis **appended** — a Component outside the circuit,
      as the completeness sweep writes, recognisable by its empty intake
      columns — is kept while it still holds a carried column, and goes with
      its namespace when that analysis reruns;
    * an old *intake* row the fresh intake no longer has belonged to a
      different circuit under the same label, and is dropped.

    Legacy column names are translated on the way (`head_table.LEGACY_COLUMNS`)
    and the translation is recorded in the meta's `renamed_columns`, so a cell
    of record touched by a later run reads under the current names. The meta
    returned carries the coverage of every carried column and every old meta
    key that is not the intake's. Returns new rows; nothing is mutated.
    """
    path = os.path.join(cell_dir, TABLE_JSON)
    if not os.path.exists(path):
        return rows, {}
    with open(path) as handle:
        table = json.load(handle)
    old_rows, renamed = modernize_columns(table.get("rows", []))
    old_meta = modernize_meta(table.get("meta"), renamed)
    replaced = set(replaced)

    fresh = {row_key(row) for row in rows}
    carried = {}
    for row in old_rows:
        key = row_key(row)
        values = {column: value for column, value in row.items()
                  if not _rebuilt(column, replaced)}
        if key not in fresh:
            if not is_appended_row(row):
                continue           # an intake row of a circuit this one is not
            if all(value is None for value in values.values()):
                continue           # appended by an analysis that is rerunning
        carried[key] = values

    out = [dict(row, **carried.get(row_key(row), {})) for row in rows]
    out += [{"kind": key[0], "layer": key[1], "index": key[2], **values}
            for key, values in carried.items() if key not in fresh]

    kept = {column for values in carried.values() for column in values}
    meta = {name: value for name, value in old_meta.items()
            if name not in INTAKE_META}
    meta[COVERAGE_KEY] = {column: entry for column, entry
                          in (old_meta.get(COVERAGE_KEY) or {}).items()
                          if column in kept}
    return out, meta


def print_carried(rows, meta) -> None:
    """One line saying what a run kept from the cell it ran into."""
    columns = sorted({column for row in rows for column in row
                      if column not in BASE_COLUMNS and "." in column
                      and not column.startswith(INTAKE_NAMESPACES)}
                     | {column for row in rows for column in row
                        if column in PROTECTED_COLUMNS})
    if not columns:
        return
    namespaces = sorted({column.split(".", 1)[0] if "." in column else column
                         for column in columns})
    print(f"    carried forward from the cell's head table: {len(columns)} "
          f"column(s) under {', '.join(namespaces)}")
    if meta.get(RENAMED_KEY):
        print("    !! legacy column names translated: "
              + ", ".join(f"{old} -> {new}" for old, new
                          in meta[RENAMED_KEY].items()))


def write_cell(cell_dir: str, circuit_spec, task_spec, rows, components,
               resolved, *, meta: dict = None) -> dict:
    """The head table, with the intake's meta rebuilt over whatever `meta`
    carries (the coverage, and the keys a previous run left)."""
    meta = dict(meta or {})
    meta.update({"circuit": circuit_spec.provenance(),
                 "task": task_spec.provenance(),
                 "intake": resolved.provenance(),
                 "components": count_components(components)})
    return write_head_table(cell_dir, rows, meta=meta)


# ==============================================================================
# SEGMENTATION AND SAMPLE
# ==============================================================================

class TaskInstances:
    """One task's resolved Segments and its causal sample, ready to write."""

    def __init__(self, task_spec, segmentations, report, sample, overrides,
                 tokenizer=None):
        self.task_spec = task_spec
        self.segmentations = segmentations
        self.report = report
        self.sample = sample
        self.overrides = overrides
        # Kept so the analyses tokenize their prompts with the tokenizer the
        # Segments were resolved against, rather than loading a second one.
        self.tokenizer = tokenizer

    def write(self, cell_dir: str, *, meta: dict) -> dict:
        return {
            "segmentation": instances.write_segmentation(
                cell_dir, self.segmentations, task=self.task_spec.name,
                overrides=self.overrides, report=self.report,
                split=ANALYSIS_SPLIT, meta=meta),
            "sample": instances.write_sample(
                cell_dir, self.sample, task=self.task_spec.name,
                split=ANALYSIS_SPLIT, meta=meta),
        }


def resolve_instances(cli, resolved, *, tokenizer=None) -> dict:
    """`{task label: TaskInstances}` for every task that has a segmenter.

    A task with no default segmentation (the synthetic ones, IOI, GT, GP) is
    skipped rather than failing the run: the head table still describes its
    Components. A task that *does* have one and whose dataset or prompts do not
    resolve fails here, which is what `--dry-run` is for.
    """
    overrides = segments.parse_segment_overrides(getattr(cli, "segment", None))
    # A mechanism task (v1 or v2) always has a segmentation; skipping one
    # would run its causal analyses on no sample and say nothing, so it is
    # refused by name instead (mechanism-analysis 02a).
    unsegmented = [spec.name for spec in resolved.tasks
                   if spec.name in dataloaders.MECHANISM_TASKS
                   and not segments.is_segmentable(spec.name)]
    if unsegmented:
        raise SystemExit(
            f"task(s) {', '.join(unsegmented)} are mechanism tasks with no default "
            f"segmentation; they would be skipped silently, so the run stops here")
    wanted = [spec for spec in resolved.tasks if segments.is_segmentable(spec.name)]
    if not wanted:
        return {}
    filters = {}
    for option, flag in (("exclude_ids", "--exclude-ids"),
                         ("include_ids", "--include-ids")):
        path = getattr(cli, option, None)
        if path:
            filters[option] = (path, sampling.read_id_file(path))

    if tokenizer is None:
        tokenizer = instances.load_analysis_tokenizer(
            resolved.model, hf_token=getattr(cli, "hf_token", None))

    out = {}
    for task_spec in wanted:
        records = instances.load_records(task_spec, ANALYSIS_SPLIT)
        ids = sampling.record_ids(records)
        segmentations, report = instances.resolve_split_segmentation(
            task_spec.name, records, tokenizer, overrides=overrides, ids=ids)
        sample = sampling.draw_sample(
            records, n=cli.n_causal, seed=cli.seed, ids=ids,
            **{option: listed for option, (_path, listed) in filters.items()})
        for option, (path, _listed) in filters.items():
            key = "id_exclusion" if option == "exclude_ids" else "id_inclusion"
            sample.id_filters[key]["source"] = path
        out[task_spec.label] = TaskInstances(task_spec, segmentations, report,
                                             sample, overrides, tokenizer)
    return out


def print_instances(task_instances: TaskInstances) -> None:
    sample = task_instances.sample
    segmentations = task_instances.segmentations
    names = list(segmentations[0].segments) if segmentations else []
    print(f"    segmentation: {len(segmentations)} instance(s), "
          f"{len(names)} Segment(s): {', '.join(names)}")
    absent = sorted({name for one in segmentations
                     for name, segment in one.segments.items()
                     if segment.status == "absent"})
    if absent:
        print(f"      absent on at least one instance: {', '.join(absent)}")
    overlapping = task_instances.report["instances_with_overlapping_segments"]
    if overlapping:
        print(f"      !! an override overlaps a default Segment on "
              f"{len(overlapping)} instance(s)")
    print(f"    sample: {sample.n_drawn} of {sample.n_requested} requested, "
          f"seed {sample.seed}")
    for name, value in sample.id_filters.items():
        detail = (f"{value['n_removed_from_pool']} removed from the pool"
                  if name == "id_exclusion" else
                  f"{value['n_kept_in_split']} in the split, "
                  f"{len(value['not_in_split'])} not")
        print(f"      {name.replace('_', ' ')}: {value['n_ids']} id(s) from "
              f"{value.get('source')}; {detail}")
    if sample.factors:
        print(f"      stratified over {', '.join(sample.factors)} "
              f"({len(sample.strata)} strata)")
        for factor in sample.factors:
            counts = sample.marginals[factor]
            print("        " + factor + ": " + ", ".join(
                f"{level}={count}" for level, count in counts.items()))
    else:
        print("      no factor has more than one level; drawn unstratified")
    if sample.inactive_factors:
        print("      not stratified over: " + ", ".join(
            f"{factor} (the records do not carry it)" if level is None
            else f"{factor} (one level: {level})"
            for factor, level in sample.inactive_factors.items()))


# ==============================================================================
# ANALYSES
# ==============================================================================

def analysis_context(cli, resolved, circuit_spec, task_spec, components, cell,
                     task_instances, *, model=None) -> registry.AnalysisContext:
    """What every analysis is handed for one (circuit, task) cell."""
    return registry.AnalysisContext(
        cli=cli, intake=resolved, circuit_spec=circuit_spec,
        task_spec=task_spec, components=components, cell_dir=cell, model=model,
        tokenizer=None if task_instances is None else task_instances.tokenizer,
        segmentations=None if task_instances is None else task_instances.segmentations,
        sample=None if task_instances is None else task_instances.sample,
        device=getattr(cli, "device", "cuda"))


def selected_analyses(cli) -> list:
    return registry.select(registry.parse_names(getattr(cli, "analyses", None)))


def print_estimates(ctx, selected) -> None:
    """`--dry-run`: one line per analysis, and no file created by any of them.

    An analysis whose loader this cell cannot supply — a causal analysis on a
    task with no sample, or on a task the loaders do not cover — prints "not
    applicable" and the dry run continues. Only that one failure is softened:
    every other exception is a bad configuration, which is what `--dry-run` is
    for catching on the login node.
    """
    if not selected:
        print("    analyses: none registered, so this run would only write the "
              "head table, the segmentation and the sample")
        return
    for module in selected:
        try:
            line = module.estimate(ctx)
        except dataloaders.LoaderUnavailable as unavailable:
            line = f"not applicable — {unavailable}"
        print(f"    {module.NAME}: {line}")


# ==============================================================================
# DRY RUN
# ==============================================================================

def dry_run(cli, resolved, *, tokenizer=None) -> int:
    selected = selected_analyses(cli)
    kv_heads = intake.num_key_value_heads(
        resolved.model, hf_token=cli.hf_token, override=cli.num_kv_heads)
    root = intake.analyses_root(cli, resolved.base_run_dir)
    resolved_instances = resolve_instances(cli, resolved, tokenizer=tokenizer)

    print("\nDRY RUN — no model loaded, no CUDA touched")
    print(f"  model        {resolved.model}")
    print(f"  geometry     {resolved.geometry}")
    print(f"  kv heads     {kv_heads} "
          f"({resolved.geometry['num_heads'] // kv_heads} query heads per group)")
    print("  references   " + (", ".join(
        f"{n}={d}" for n, d in resolved.reference_run_dirs.items()) or "(none)"))
    print(f"  output root  {root}\n")

    for circuit_spec in resolved.circuits:
        components, rows = head_table_for(circuit_spec, resolved,
                                          num_kv_heads=kv_heads)
        census = count_components(components)
        for task_spec in resolved.tasks:
            cell = intake.cell_dir(root, circuit_spec, task_spec)
            # A dry run runs no analysis, so it replaces no namespace: every
            # column the cell already holds is written back as it was.
            carried, meta = carry_forward(cell, rows)
            written = write_cell(cell, circuit_spec, task_spec, carried,
                                 components, resolved, meta=meta)
            print(f"  {circuit_spec.label} x {task_spec.label}")
            print_carried(carried, meta)
            print(f"    {census['heads']} head(s) and {census['mlps']} MLP "
                  f"block(s) over {census['layers']} layer(s); "
                  f"{census['heads_head_gate_active']} head(s) have their head "
                  f"gate open")
            for name in resolved.references:
                shared = sum(1 for r in rows if r.get(f"reference.{name}"))
                print(f"    shared with {name}: {shared} of {len(rows)} Components")
            print(f"    {written['csv']}")
            print(f"    {written['json']}")

            task_instances = resolved_instances.get(task_spec.label)
            if task_instances is None:
                print(f"    segmentation: task {task_spec.name!r} has no "
                      f"default segmentation, so no segmentation.json, no "
                      f"sample.json and no causal loader")
                print_estimates(analysis_context(cli, resolved, circuit_spec,
                                                 task_spec, components, cell,
                                                 None), selected)
                continue
            files = task_instances.write(cell, meta={
                "circuit": circuit_spec.provenance(),
                "task": task_spec.provenance()})
            print_instances(task_instances)
            print(f"    {files['segmentation']}")
            print(f"    {files['sample']}")

            ctx = analysis_context(cli, resolved, circuit_spec, task_spec,
                                   components, cell, task_instances)
            uncovered = dataloaders.uncovered_reason(task_spec.name)
            if uncovered:
                print(f"    causal loader: none — {uncovered}")
            else:
                for line in dataloaders.summarize(ctx.causal_batches()):
                    print(f"    causal loader: {line}")
            print_estimates(ctx, selected)

    if resolved_instances:
        print("\n  The head table, the segmentation and the sample were "
              "written.", end=" ")
    else:
        print("\n  Only the head table was written: no task in this run has a "
              "default segmentation.", end=" ")
    if selected:
        print(f"Without --dry-run this would run: "
              f"{', '.join(module.NAME for module in selected)}.")
    else:
        print("No analysis is registered yet, so the analyses that need a "
              "model come from the later tickets.")
    return 0


# ==============================================================================
# THE RUN
# ==============================================================================

def load_model(cli, resolved):
    """The model every analysis shares, loaded once for the whole run.

    Imported here rather than at module scope so that `--dry-run` never reaches
    nnsight: the login node carries 0.5.12 for the parent repo, not the 0.7.0
    ADR-0001 pins.
    """
    from component_analysis import hooks

    model = hooks.load_analysis_model(resolved.model, device=cli.device,
                                      hf_token=cli.hf_token)
    print(f"  model loaded: {hooks.describe(model)}")
    return model


def run(cli, resolved, *, model=None) -> int:
    """Every selected analysis over every cell, then one head table per cell."""
    selected = selected_analyses(cli)
    if not selected:
        raise SystemExit(
            "no analysis is registered, so a run without --dry-run would load "
            "a model and do nothing with it. Register one in "
            "component_analysis/registry.py, or pass --dry-run.")

    kv_heads = intake.num_key_value_heads(
        resolved.model, hf_token=cli.hf_token, override=cli.num_kv_heads)
    root = intake.analyses_root(cli, resolved.base_run_dir)
    resolved_instances = resolve_instances(cli, resolved)
    if model is None:
        model = load_model(cli, resolved)

    print(f"\n  running {', '.join(m.NAME for m in selected)} over "
          f"{len(resolved.circuits)} circuit(s) x {len(resolved.tasks)} task(s)")
    for circuit_spec in resolved.circuits:
        components, base_rows = head_table_for(circuit_spec, resolved,
                                               num_kv_heads=kv_heads)
        for task_spec in resolved.tasks:
            cell = intake.cell_dir(root, circuit_spec, task_spec)
            task_instances = resolved_instances.get(task_spec.label)
            ctx = analysis_context(cli, resolved, circuit_spec, task_spec,
                                   components, cell, task_instances, model=model)
            print(f"  {circuit_spec.label} x {task_spec.label}")

            # Before the analyses, so the table they leave holds every column
            # the cell already had except the namespaces about to be rewritten.
            rows, meta = carry_forward(
                cell, base_rows, replaced={module.NAME for module in selected})
            print_carried(rows, meta)
            for module in selected:
                updates = module.run(ctx) or {}
                rows = merge_columns(rows, updates, namespace=module.NAME)
                meta = add_declarations(meta, ctx.take_coverage(),
                                        namespace=module.NAME)
                print(f"    {module.NAME}: {len(updates)} Component(s) updated, "
                      f"output under {module.SUBDIR}/")

            if task_instances is not None:
                task_instances.write(cell, meta={
                    "circuit": circuit_spec.provenance(),
                    "task": task_spec.provenance()})
            written = write_cell(cell, circuit_spec, task_spec, rows, components,
                                 resolved, meta=meta)
            print(f"    {written['csv']}")
            print(f"    {written['json']}")
    return 0


# ==============================================================================
# MAIN
# ==============================================================================

def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] in SUBCOMMANDS:
        import importlib

        return importlib.import_module(SUBCOMMANDS[argv[0]]).main(argv[1:])

    cli = build_parser().parse_args(argv)
    resolved = intake.resolve_intake(cli)
    if cli.dry_run:
        return dry_run(cli, resolved)
    return run(cli, resolved)


if __name__ == "__main__":
    sys.exit(main())
