#!/usr/bin/env python3
"""Size check and retune rule for a Format Circuit against its paired circuit.

Spec (format-control, "Pairing targets and the size rule"): a gap above 25
percent in head count, or in fine-unit count for fine circuits, triggers one
retrain at NLS 0.3 +/- 0.1 in the direction that closes the gap; both sizes are
recorded either way; at most one retune.

usage (from the repo root):
    python outputs/_launch_format_control/size_check.py <paired_run> <format_run>
    python outputs/_launch_format_control/size_check.py record-retune <first_run> <retune_run> --carried nls0.3

The first form prints both sizes per gate kind and the verdict, and writes
size_check.json beside the format run. The second records the retune's outcome
and the carried run in the first run's size_check.json (and `carried` in the
retune's), since that is the file read beside the Format Circuit.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, Mapping, Optional

# Gate kinds the rule compares, in priority order: heads first (the primary
# granularity), so heads set the direction whenever they are out of tolerance.
RULE_KINDS = ("heads", "fine_units")


def out_of_tolerance(paired_counts, format_counts, *, tol=0.25):
    """Rule kinds (in priority order) whose gap is strictly above `tol`.

    A kind is compared only when the paired circuit carries it, so a coarse
    pairing compares heads only."""
    return [k for k in RULE_KINDS
            if k in paired_counts
            and abs(format_counts[k] - paired_counts[k]) > tol * paired_counts[k]]


class RetuneRefused(RuntimeError):
    """The size gap still exceeds tolerance after the one permitted retune."""


def retune_step(paired_counts: Mapping[str, int], format_counts: Mapping[str, int],
                nls: float, *, tol: float = 0.25, step: float = 0.1,
                retuned: bool = False) -> Optional[float]:
    """NLS for the one retrain the size rule allows, or None when no retrain is due.

    Fires when the head gap, or the fine-unit gap for fine pairings, is strictly
    above `tol` of the paired size. A larger Format Circuit steps NLS up (more
    sparsity, fewer units), a smaller one steps it down; on disagreement the
    head gap sets the direction. `retuned=True` marks a run that already is the
    retrain: a remaining gap then raises RetuneRefused instead of stepping again.
    """
    fired = out_of_tolerance(paired_counts, format_counts, tol=tol)
    if not fired:
        return None
    if retuned:
        raise RetuneRefused(
            f"size gap in {', '.join(fired)} still above {tol:.0%} at NLS {nls}; "
            "the rule allows at most one retune, so both sizes are recorded and "
            "the gap is left for the researcher")
    k = fired[0]
    larger = format_counts[k] > paired_counts[k]
    return round(nls + step if larger else nls - step, 10)


# --------------------------------------------------------------------- run dirs

FINE_KINDS = ("attention_neurons", "mlp_hidden", "mlp_output")


def mask_source(run_dir: str) -> str:
    """The mask file that holds the circuit as trained.

    A coarse run's post-processing keeps the trained masks in
    active_nodes.coarse.json and expands active_nodes.json with every fine unit
    of a live head or block open, so the expanded file would misstate its size."""
    coarse = os.path.join(run_dir, "active_nodes.coarse.json")
    return coarse if os.path.exists(coarse) else os.path.join(run_dir, "active_nodes.json")


def circuit_counts(run_dir: str) -> Dict[str, int]:
    """Active units per gate kind; `fine_units` only when the circuit is fine.

    `heads` is the attention-head count; `fine_units` is attention neurons plus
    MLP hidden plus MLP output units, present only when all three were pruned
    (absent from a coarse circuit's trained masks)."""
    with open(mask_source(run_dir)) as f:
        masks = json.load(f)["masks"]

    def active(m):
        if isinstance(m, dict):
            return int(sum(sum(v) for v in m.values()))
        return int(sum(m))

    counts = {}
    for kind in ("attention_blocks", "mlp_blocks"):
        if kind in masks:
            counts[kind] = active(masks[kind])
    counts["heads"] = active(masks["attention_heads"])
    if all(k in masks for k in FINE_KINDS):
        for k in FINE_KINDS:
            counts[k] = active(masks[k])
        counts["fine_units"] = sum(counts[k] for k in FINE_KINDS)
    return counts


# In-run sufficiency gate of the coarse SDR wave (_launch/postprocess.sh):
# metric -> (comparison, threshold). A miss is flagged, never retuned for.
SUFFICIENCY_GATE = {"accuracy": (">=", 0.90), "exact_match": (">=", 0.90), "kl_div": ("<=", 0.20)}


def in_run_gate(run_dir: str) -> dict:
    """The run's own node eval (results.json, its test set) against the gate."""
    with open(os.path.join(run_dir, "results.json")) as f:
        node_eval = json.load(f)["node_eval"]
    gate = {k: node_eval[k] for k in SUFFICIENCY_GATE}
    gate["misses"] = [k for k, (op, t) in SUFFICIENCY_GATE.items()
                      if not (gate[k] >= t if op == ">=" else gate[k] <= t)]
    gate["passes"] = not gate["misses"]
    gate["thresholds"] = {k: f"{op} {t}" for k, (op, t) in SUFFICIENCY_GATE.items()}
    return gate


def _nls(run_dir: str) -> float:
    with open(os.path.join(run_dir, "config.json")) as f:
        return float(json.load(f)["node_lambda_sparsity"])


def check(paired_run: str, format_run: str, *, tol: float = 0.25, step: float = 0.1) -> dict:
    """Compare a Format Circuit run with its paired run and decide the retune.

    The format run counts as already retuned when its NLS differs from the
    paired run's (the Format Circuit is first trained at the paired NLS)."""
    paired, fmt = circuit_counts(paired_run), circuit_counts(format_run)
    paired_nls, format_nls = _nls(paired_run), _nls(format_run)
    retuned = abs(format_nls - paired_nls) > 1e-9
    compared = [k for k in RULE_KINDS if k in paired]
    try:
        next_nls = retune_step(paired, fmt, format_nls, tol=tol, step=step, retuned=retuned)
        verdict = "within_tolerance" if next_nls is None else "retune"
        note = None
    except RetuneRefused as exc:
        next_nls, verdict, note = None, "refused", str(exc)
    return {
        "paired_run": os.path.abspath(paired_run),
        "format_run": os.path.abspath(format_run),
        "paired_source": os.path.basename(mask_source(paired_run)),
        "format_source": os.path.basename(mask_source(format_run)),
        "paired_counts": paired,
        "format_counts": fmt,
        "compared": compared,
        "gaps": {k: (fmt[k] - paired[k]) / paired[k] for k in compared},
        "out_of_tolerance": out_of_tolerance(paired, fmt, tol=tol),
        "tol": tol,
        "step": step,
        "paired_nls": paired_nls,
        "format_nls": format_nls,
        "retuned": retuned,
        "verdict": verdict,
        "next_nls": next_nls,
        "note": note,
        "in_run_gate": in_run_gate(format_run),
    }


def _nls_label(nls: float) -> str:
    return f"nls{nls:g}"


def _load_report(run_dir: str) -> dict:
    with open(os.path.join(run_dir, "size_check.json")) as f:
        return json.load(f)


def _write_report(run_dir: str, report: dict) -> None:
    with open(os.path.join(run_dir, "size_check.json"), "w") as f:
        json.dump(report, f, indent=2)


def record_retune(first_run: str, retune_run: str, carried: str) -> dict:
    """Record the retune's outcome beside the first Format Circuit run.

    Both runs must already have size_check.json. The first run's file gains a
    `retune` block (the retune run's path, NLS, both sizes, gaps, verdict and
    in-run gate) and `carried`, the label (`nls<NLS>`) of the run carried into
    evaluation; the retune run's file gains the same `carried`. A label naming
    neither run is refused before anything is written."""
    first, retune = _load_report(first_run), _load_report(retune_run)
    labels = {_nls_label(first["format_nls"]), _nls_label(retune["format_nls"])}
    if carried not in labels:
        raise SystemExit(f"--carried {carried!r} names neither run ({', '.join(sorted(labels))})")
    first["retune"] = {
        "run": os.path.abspath(retune_run),
        "nls": retune["format_nls"],
        **{k: retune[k] for k in ("paired_counts", "format_counts", "gaps",
                                  "out_of_tolerance", "verdict", "note", "in_run_gate")},
    }
    first["carried"] = retune["carried"] = carried
    _write_report(first_run, first)
    _write_report(retune_run, retune)
    return first


def _record_retune_main(argv) -> dict:
    ap = argparse.ArgumentParser(prog="size_check.py record-retune",
                                 description=record_retune.__doc__)
    ap.add_argument("first_run", help="the Format Circuit run trained at the paired NLS")
    ap.add_argument("retune_run", help="its one retune")
    ap.add_argument("--carried", required=True,
                    help="label of the run carried into evaluation, e.g. nls0.3")
    args = ap.parse_args(argv)
    report = record_retune(args.first_run, args.retune_run, args.carried)
    rt = report["retune"]
    print(f"retune {rt['run']} (NLS {rt['nls']}): verdict {rt['verdict']}, heads "
          f"{rt['format_counts']['heads']} vs {rt['paired_counts']['heads']}, gate "
          + ("PASS" if rt["in_run_gate"]["passes"] else "MISS on " + ", ".join(rt["in_run_gate"]["misses"])))
    print(f"carried: {report['carried']} (recorded in both size_check.json files)")
    return report


def main(argv=None) -> dict:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "record-retune":
        return _record_retune_main(argv[1:])
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paired_run", help="the paired mechanism (D) run directory")
    ap.add_argument("format_run", help="the Format Circuit (F) run directory")
    ap.add_argument("--tol", type=float, default=0.25)
    ap.add_argument("--step", type=float, default=0.1)
    args = ap.parse_args(argv)

    report = check(args.paired_run, args.format_run, tol=args.tol, step=args.step)
    out = os.path.join(args.format_run, "size_check.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)

    p, fm = report["paired_counts"], report["format_counts"]
    print(f"paired  {report['paired_run']}  ({report['paired_source']}, NLS {report['paired_nls']})")
    print(f"format  {report['format_run']}  ({report['format_source']}, NLS {report['format_nls']})")
    print(f"{'gate kind':<18} {'paired':>9} {'format':>9} {'gap':>8}")
    for k in sorted(set(p) | set(fm), key=lambda k: list(p).index(k) if k in p else 99):
        gap = report["gaps"].get(k)
        gap_s = f"{gap:+.1%}" if gap is not None else ""
        print(f"{k:<18} {p.get(k, '-'):>9} {fm.get(k, '-'):>9} {gap_s:>8}")
    print(f"verdict: {report['verdict']}"
          + (f" -> retrain at NLS {report['next_nls']}" if report["next_nls"] is not None else "")
          + (f" ({report['note']})" if report["note"] else ""))
    g = report["in_run_gate"]
    print(f"in-run node eval: acc={g['accuracy']} em={g['exact_match']} kl={g['kl_div']} | gate "
          + ("PASS" if g["passes"] else f"MISS on {', '.join(g['misses'])} (flag to the researcher)"))
    print(f"wrote {out}")
    return report


if __name__ == "__main__":
    main()
