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

`--dry-run` resolves everything and writes the head table on the login node
with no GPU; it is the mode ticket 01 delivers. The analyses that need a model
are added by later tickets.
"""

from __future__ import annotations

import argparse
import sys

from component_analysis import intake
from component_analysis.components import circuit_components, count_components, \
    is_component_of
from component_analysis.head_table import merge_columns, rows_from_components, \
    write_head_table
from evaluation import circuits as circuit_intake


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

def head_table_for(circuit_spec, cells_intake, *, num_kv_heads: int):
    """The intake rows for one circuit: its Components plus reference columns."""
    geometry = cells_intake.geometry
    components = circuit_components(
        circuit_spec.masks, num_heads=geometry["num_heads"],
        head_dim=geometry["head_dim"], num_kv_heads=num_kv_heads)

    rows = rows_from_components(components)
    for name, masks in cells_intake.references.items():
        membership = {
            component.key: {name: is_component_of(
                component, masks, num_heads=geometry["num_heads"],
                head_dim=geometry["head_dim"])}
            for component in components}
        rows = merge_columns(rows, membership, namespace="reference")
    return components, rows


def write_cell(cell_dir: str, circuit_spec, task_spec, rows, components,
               cells_intake) -> dict:
    meta = {"circuit": circuit_spec.provenance(),
            "task": task_spec.provenance(),
            "intake": cells_intake.provenance(),
            "components": count_components(components)}
    return write_head_table(cell_dir, rows, meta=meta)


# ==============================================================================
# DRY RUN
# ==============================================================================

def dry_run(cli, cells_intake) -> int:
    kv_heads = intake.num_key_value_heads(
        cells_intake.model, hf_token=cli.hf_token, override=cli.num_kv_heads)
    root = intake.analyses_root(cli, cells_intake.base_run_dir)

    print("\nDRY RUN — no model loaded, no CUDA touched")
    print(f"  model        {cells_intake.model}")
    print(f"  geometry     {cells_intake.geometry}")
    print(f"  kv heads     {kv_heads} "
          f"({cells_intake.geometry['num_heads'] // kv_heads} query heads per group)")
    print("  references   " + (", ".join(
        f"{n}={d}" for n, d in cells_intake.reference_run_dirs.items()) or "(none)"))
    print(f"  output root  {root}\n")

    for circuit_spec in cells_intake.circuits:
        components, rows = head_table_for(circuit_spec, cells_intake,
                                          num_kv_heads=kv_heads)
        census = count_components(components)
        for task_spec in cells_intake.tasks:
            cell = intake.cell_dir(root, circuit_spec, task_spec)
            written = write_cell(cell, circuit_spec, task_spec, rows,
                                 components, cells_intake)
            print(f"  {circuit_spec.label} x {task_spec.label}")
            print(f"    {census['heads']} head(s) and {census['mlps']} MLP "
                  f"block(s) over {census['layers']} layer(s); "
                  f"{census['heads_head_gate_active']} head(s) have their head "
                  f"gate open")
            for name in cells_intake.references:
                shared = sum(1 for r in rows if r.get(f"reference.{name}"))
                print(f"    shared with {name}: {shared} of {len(rows)} Components")
            print(f"    {written['csv']}")
            print(f"    {written['json']}")

    print("\n  Only the head table was written. The analyses that need a model "
          "come from the later tickets.")
    return 0


# ==============================================================================
# MAIN
# ==============================================================================

def main(argv=None) -> int:
    cli = build_parser().parse_args(argv)
    cells_intake = intake.resolve_intake(cli)
    if not cli.dry_run:
        raise SystemExit(
            "analyze_components.py currently implements --dry-run only: circuit "
            "intake and the head table. The analyses that load a model arrive "
            "with the tickets that add them.")
    return dry_run(cli, cells_intake)


if __name__ == "__main__":
    sys.exit(main())
