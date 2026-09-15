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

`--dry-run` resolves everything on the login node with no GPU and writes three
files per cell: the head table, the `segmentation.json` that says which tokens
each Segment covers on every test instance, and the `sample.json` that names
the instances the causal analyses will run over. Writing the last two is what
stops a plot from later being read against the wrong spans or the wrong
instances. The analyses that need a model are added by later tickets.
"""

from __future__ import annotations

import argparse
import sys

from component_analysis import instances, intake, sampling
from component_analysis import segmentation as segments
from component_analysis.components import circuit_components, count_components, \
    is_component_of
from component_analysis.head_table import merge_columns, rows_from_components, \
    write_head_table
from evaluation import circuits as circuit_intake

#: Descriptive analyses run over this split; the causal sample is drawn from it.
ANALYSIS_SPLIT = "test"


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(
        description="Component-level analysis of node-pruned circuits.",
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


def write_cell(cell_dir: str, circuit_spec, task_spec, rows, components,
               resolved) -> dict:
    meta = {"circuit": circuit_spec.provenance(),
            "task": task_spec.provenance(),
            "intake": resolved.provenance(),
            "components": count_components(components)}
    return write_head_table(cell_dir, rows, meta=meta)


# ==============================================================================
# SEGMENTATION AND SAMPLE
# ==============================================================================

class TaskInstances:
    """One task's resolved Segments and its causal sample, ready to write."""

    def __init__(self, task_spec, segmentations, report, sample, overrides):
        self.task_spec = task_spec
        self.segmentations = segmentations
        self.report = report
        self.sample = sample
        self.overrides = overrides

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
    wanted = [spec for spec in resolved.tasks if segments.is_segmentable(spec.name)]
    if not wanted:
        return {}

    if tokenizer is None:
        tokenizer = instances.load_analysis_tokenizer(
            resolved.model, hf_token=getattr(cli, "hf_token", None))

    out = {}
    for task_spec in wanted:
        records = instances.load_records(task_spec, ANALYSIS_SPLIT)
        ids = sampling.record_ids(records)
        segmentations, report = instances.resolve_split_segmentation(
            task_spec.name, records, tokenizer, overrides=overrides, ids=ids)
        sample = sampling.draw_sample(records, n=cli.n_causal, seed=cli.seed,
                                      ids=ids)
        out[task_spec.label] = TaskInstances(task_spec, segmentations, report,
                                             sample, overrides)
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
# DRY RUN
# ==============================================================================

def dry_run(cli, resolved, *, tokenizer=None) -> int:
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
            written = write_cell(cell, circuit_spec, task_spec, rows,
                                 components, resolved)
            print(f"  {circuit_spec.label} x {task_spec.label}")
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
                      f"default segmentation, so no segmentation.json or "
                      f"sample.json")
                continue
            files = task_instances.write(cell, meta={
                "circuit": circuit_spec.provenance(),
                "task": task_spec.provenance()})
            print_instances(task_instances)
            print(f"    {files['segmentation']}")
            print(f"    {files['sample']}")

    if resolved_instances:
        print("\n  The head table, the segmentation and the sample were "
              "written.", end=" ")
    else:
        print("\n  Only the head table was written: no task in this run has a "
              "default segmentation.", end=" ")
    print("The analyses that need a model come from the later tickets.")
    return 0


# ==============================================================================
# MAIN
# ==============================================================================

def main(argv=None) -> int:
    cli = build_parser().parse_args(argv)
    resolved = intake.resolve_intake(cli)
    if not cli.dry_run:
        raise SystemExit(
            "analyze_components.py currently implements --dry-run only: circuit "
            "intake and the head table. The analyses that load a model arrive "
            "with the tickets that add them.")
    return dry_run(cli, resolved)


if __name__ == "__main__":
    sys.exit(main())
