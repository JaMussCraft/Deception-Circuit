"""
component_analysis/sweep_drift.py — is a knockout sweep rerun on another GPU the same measurement?

The component-analysis drift control of mechanism-analysis ticket 02a. A sweep is rerun (same argv, same
sample) on Bridges-2 H100 and compared, Component by Component, with its cell of record (Delta H200 job
22899543). Pre-registered tolerance, over every Component of both `sweep.json`s:

  - max |delta mean_drop| <= 0.05 logits;
  - 99th percentile of |delta| <= 0.02;
  - Spearman correlation of mean_drop >= 0.99;
  - the same `flagged` set at the sweep's threshold, except Components within 0.02 of the threshold on
    either side.

    python -m component_analysis.sweep_drift REFERENCE_SWEEP_JSON RERUN_SWEEP_JSON --out drift.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Dict, List, Sequence

MAX_ABS = 0.05
P99 = 0.02
SPEARMAN = 0.99
BOUNDARY = 0.02


def _ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(a: Sequence[float], b: Sequence[float]) -> float:
    """Pearson correlation of average ranks."""
    ra, rb = _ranks(list(a)), _ranks(list(b))
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra)
    vb = sum((y - mb) ** 2 for y in rb)
    return cov / math.sqrt(va * vb) if va and vb else float("nan")


def _percentile(values: Sequence[float], q: float) -> float:
    """Linear interpolation between closest ranks (numpy's default)."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * q / 100.0
    low = math.floor(position)
    high = math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def compare(reference: Dict, rerun: Dict) -> Dict:
    ref = {row["label"]: row for row in reference["components"]}
    new = {row["label"]: row for row in rerun["components"]}
    missing = sorted(set(ref) ^ set(new))
    shared = [label for label in ref if label in new
              and ref[label]["mean_drop"] is not None and new[label]["mean_drop"] is not None]
    deltas = {label: new[label]["mean_drop"] - ref[label]["mean_drop"] for label in shared}
    magnitudes = [abs(one) for one in deltas.values()]
    threshold = float(reference.get("threshold", 0.4))

    def near(label):
        return any(abs(abs(side[label]["mean_drop"]) - threshold) <= BOUNDARY
                   for side in (ref, new) if side[label]["mean_drop"] is not None)

    ref_flagged, new_flagged = set(reference.get("flagged", [])), set(rerun.get("flagged", []))
    differ = sorted(ref_flagged ^ new_flagged)
    unforgiven = [label for label in differ if label not in ref or label not in new
                  or not near(label)]
    rho = spearman([ref[l]["mean_drop"] for l in shared], [new[l]["mean_drop"] for l in shared])
    worst = max(deltas, key=lambda label: abs(deltas[label])) if deltas else None
    result = {
        "n_components": len(shared), "missing": missing,
        "max_abs_delta": max(magnitudes) if magnitudes else None,
        "max_abs_delta_component": worst,
        "p99_abs_delta": _percentile(magnitudes, 99) if magnitudes else None,
        "mean_abs_delta": sum(magnitudes) / len(magnitudes) if magnitudes else None,
        "spearman": rho, "threshold": threshold,
        "flagged_reference": sorted(ref_flagged), "flagged_rerun": sorted(new_flagged),
        "flagged_differences": differ, "flagged_differences_not_near_threshold": unforgiven,
        "tolerance": {"max_abs_delta": MAX_ABS, "p99_abs_delta": P99, "spearman": SPEARMAN,
                      "flagged_boundary": BOUNDARY},
    }
    result["checks"] = {
        "complete": not missing,
        "max_abs_delta": result["max_abs_delta"] is not None and result["max_abs_delta"] <= MAX_ABS,
        "p99_abs_delta": result["p99_abs_delta"] is not None and result["p99_abs_delta"] <= P99,
        "spearman": rho >= SPEARMAN,
        "flagged_set": not unforgiven,
    }
    result["passed"] = all(result["checks"].values())
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("reference")
    parser.add_argument("rerun")
    parser.add_argument("--out", default=None)
    options = parser.parse_args(argv)
    with open(options.reference) as handle:
        reference = json.load(handle)
    with open(options.rerun) as handle:
        rerun = json.load(handle)
    result = compare(reference, rerun)
    result.update(reference_file=options.reference, rerun_file=options.rerun)
    text = json.dumps(result, indent=2)
    if options.out:
        with open(options.out, "w") as handle:
            handle.write(text)
    print(json.dumps({key: result[key] for key in ("passed", "checks", "max_abs_delta",
                                                   "p99_abs_delta", "spearman",
                                                   "flagged_differences")}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
