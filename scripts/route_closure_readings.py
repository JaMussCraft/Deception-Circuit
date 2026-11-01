#!/usr/bin/env python
"""B1 readings (plan `docs/research/instructed-route/plans/B1-plan.md`, ticket 6). CPU only.

Reads one `route_closure.json` per task (far and ser; `component_analysis/route_closure.py` writes
them, its module docstring holds the schema) and applies the frozen B1 rules of `spec.md` with
ruling R1:

- **T2** (plan 2.2). P = mean m(D) - mean m(T); r_a = (mean m(D) - mean m(D_a)) / P for a restore
  arm (base D) and (mean m(T_a) - mean m(T)) / P for a reverse arm (base T). r_Q is `q_readout`,
  r_K `k_options`, r_out `out_readout`. Key-side when r_K - r_Q >= 0.15, query-side when
  r_Q - r_K >= 0.15, otherwise indeterminate (the frozen rule, `frozen_rule_verdict`). The
  reading (`verdict`) says "indeterminate, ceiling below 0.15" whenever r_out < 0.15 (plan 2.2).
- **T1** (plan 1.2 to 1.4, R1). M_q = O_q / O = mean_i O_q,i / mean_i O_i (G cancels), from the
  rule-of-record estimator: the forward sweep, or the offline one when only it ran. The loop
  closes when M_q >= 0.50, otherwise bypass. R1's qualifier compares M_q with the controls on one
  estimator, the offline one (plan 1.2: "arms are compared on one estimator"): M_X = mean_i
  O_X,i / mean_i O_T,i for C1, C2, C3 and S_k. "closes, route-specific" when M_q is above every
  C1 and C2 draw and M_q - M_C3 >= 0.15; "closes, generic amplification" when M_q - M_C3 < 0.15;
  "closes, not specific" when some C1 or C2 draw reaches M_q; "bypass" when M_q < 0.50. When two
  qualifiers hold, the label is the first in R1's order and `qualifiers` lists both.

Verdicts use the point estimates (ratios of means), as the frozen rules are worded. Beside each
point: the per-instance median (instances whose denominator is below 1e-3 in absolute value are
left out and counted) and a 95% percentile interval from 2,000 bootstrap resamples clustered by
`pressure_id` (seed 20261101; whole pressure clusters are drawn with replacement by
`numpy.random.default_rng(seed)`, one stream for all statistics; an instance without a
pressure_id is its own cluster). A boundary comparison allows 1e-12 for float representation, so
0.35 - 0.20 counts as 0.15.

Writes `<out-dir>/b1_readings.json` and `<out-dir>/b1_readings.md`.

    python scripts/route_closure_readings.py \\
        outputs/_analyses/instructed-route-b1/far/<cell>/route_closure/route_closure.json \\
        outputs/_analyses/instructed-route-b1/ser/<cell>/route_closure/route_closure.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

SCHEMA = "b1_readings/1"
DEFAULT_OUT_DIR = "docs/research/instructed-route/results"
JSON_NAME = "b1_readings.json"
MD_NAME = "b1_readings.md"
SEED = 20261101
N_RESAMPLES = 2000

CLOSES_AT = 0.50          # frozen T1 rule
SIDE_MARGIN = 0.15        # frozen T2 rule
CEILING = 0.15            # plan 2.2: r_out below this makes T2 indeterminate
C3_MARGIN = 0.15          # R1
TOLERANCE = 1e-12         # float representation at a boundary
MIN_DENOMINATOR = 1e-3    # per-instance medians: |denominator| below this is left out

KEY, QUERY, INDETERMINATE = "key-side", "query-side", "indeterminate"
CEILING_LABEL = "indeterminate, ceiling below 0.15"
CLOSES, BYPASS = "closes", "bypass"


# ==============================================================================
# RULES
# ==============================================================================

def at_least(value: float, threshold: float) -> bool:
    return value >= threshold - TOLERANCE


def t2_verdict(r_q: float, r_k: float, *, r_out: float) -> Tuple[str, str]:
    """`(reading, frozen_rule_verdict)`. The frozen rule compares r_K and r_Q alone; the
    reading is "indeterminate, ceiling below 0.15" whenever r_out < 0.15 (plan 2.2)."""
    if at_least(r_k - r_q, SIDE_MARGIN):
        frozen = KEY
    elif at_least(r_q - r_k, SIDE_MARGIN):
        frozen = QUERY
    else:
        frozen = INDETERMINATE
    reading = frozen if at_least(r_out, CEILING) else CEILING_LABEL
    return reading, frozen


def t1_verdict(m_q: float) -> str:
    return CLOSES if at_least(m_q, CLOSES_AT) else BYPASS


def r1_label(m_q: float, *, m_c3: Optional[float], c1: Sequence[float], c2: Sequence[float],
             m_q_controls: Optional[float] = None) -> Tuple[str, List[str]]:
    """Ruling R1: `(label, qualifiers)`. `m_q` decides closes or bypass; `m_q_controls` (the
    same estimator as the controls; default `m_q`) is what the controls are compared with."""
    if t1_verdict(m_q) == BYPASS:
        return BYPASS, []
    if m_c3 is None:
        return "closes, controls not computed", []
    compare = m_q if m_q_controls is None else m_q_controls
    generic = not at_least(compare - m_c3, C3_MARGIN)
    reached = any(at_least(one, compare) for one in list(c1) + list(c2))
    qualifiers = (["generic amplification"] if generic else []) + \
        (["not specific"] if reached else [])
    if not qualifiers:
        return "closes, route-specific", ["route-specific"]
    return f"closes, {qualifiers[0]}", qualifiers


# ==============================================================================
# THE CLUSTERED BOOTSTRAP
# ==============================================================================

def cluster_labels(pressure_ids: Sequence) -> List[str]:
    """One label per instance; an instance without a pressure_id is its own cluster."""
    return [f"pid:{one}" if one is not None else f"none:{row}"
            for row, one in enumerate(pressure_ids)]


def cluster_resamples(pressure_ids: Sequence, *, n_resamples: int, seed: int
                      ) -> List[np.ndarray]:
    """Instance index arrays, one per resample: as many clusters as there are, drawn with
    replacement from the sorted cluster labels, each contributing all its instances."""
    labels = cluster_labels(pressure_ids)
    order = sorted(set(labels))
    members = {label: np.flatnonzero(np.array(labels) == label) for label in order}
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_resamples):
        picks = rng.integers(0, len(order), size=len(order))
        out.append(np.concatenate([members[order[p]] for p in picks]))
    return out


def interval(statistic: Callable[[np.ndarray], Optional[float]], resamples) -> Optional[list]:
    values = [statistic(index) for index in resamples]
    values = np.array([one for one in values if one is not None and np.isfinite(one)])
    if not len(values):
        return None
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def _ratio(numerator: np.ndarray, denominator: np.ndarray, index: np.ndarray
           ) -> Optional[float]:
    bottom = float(np.mean(denominator[index]))
    if bottom == 0.0:
        return None
    return float(np.mean(numerator[index])) / bottom


def _median_ratio(numerator: np.ndarray, denominator: np.ndarray) -> Tuple[Optional[float], int]:
    keep = np.abs(denominator) >= MIN_DENOMINATOR
    if not keep.any():
        return None, int((~keep).sum())
    return float(np.median(numerator[keep] / denominator[keep])), int((~keep).sum())


def statistic(numerator: np.ndarray, denominator: np.ndarray, resamples) -> dict:
    """A ratio of means: the point, the per-instance median and the clustered interval."""
    every = np.arange(len(numerator))
    median, excluded = _median_ratio(numerator, denominator)
    return {"point": _ratio(numerator, denominator, every), "median": median,
            "n_excluded_from_median": excluded,
            "ci95": interval(lambda index: _ratio(numerator, denominator, index), resamples)}


def difference(left: Tuple[np.ndarray, np.ndarray], right: Tuple[np.ndarray, np.ndarray],
               resamples) -> dict:
    """The difference of two ratios of means, with its clustered interval."""
    every = np.arange(len(left[0]))

    def value(index):
        a, b = _ratio(*left, index), _ratio(*right, index)
        return None if a is None or b is None else a - b

    return {"point": value(every), "ci95": interval(value, resamples)}


# ==============================================================================
# ONE TASK
# ==============================================================================

def _array(values) -> np.ndarray:
    return np.asarray(values, dtype=np.float64)


def arm_share(data: dict, name: str) -> float:
    """r_a of one arm, as the share of P it moves (restore: base D; reverse: base T)."""
    base = data["baseline"]
    arm = data["arms"][name]
    p = base["mean_m_D"] - base["mean_m_T"]
    if arm.get("base", "D") == "T":
        return (arm["mean"] - base["mean_m_T"]) / p
    return (base["mean_m_D"] - arm["mean"]) / p


def _arm_numerator(data: dict, name: str) -> np.ndarray:
    """Per instance, what the arm moves: m_D - m_a (restore) or m_a - m_T (reverse)."""
    base = data["baseline"]
    margins = _array(data["arms"][name]["margins"])
    if data["arms"][name].get("base", "D") == "T":
        return margins - _array(base["m_T"])
    return _array(base["m_D"]) - margins


def read_task(data: dict, *, n_resamples: int = N_RESAMPLES, seed: int = SEED) -> dict:
    base = data["baseline"]
    gap = _array(base["G"])
    pids = data["instances"]["pressure_ids"]
    resamples = cluster_resamples(pids, n_resamples=n_resamples, seed=seed)
    labels = cluster_labels(pids)
    out = {"task": data["task"], "n_instances": len(gap),
           "P": base["mean_m_D"] - base["mean_m_T"], "mean_G": float(np.mean(gap)),
           "bootstrap": {"n_resamples": n_resamples, "seed": seed, "cluster": "pressure_id",
                         "n_clusters": len(set(labels))}}

    arms = data.get("arms") or {}
    shares = {name: statistic(_arm_numerator(data, name), gap, resamples)
              for name in sorted(arms) if name not in ("g1_empty", "g2_all_components")}
    t2 = {"arms": shares}
    if all(name in arms for name in ("q_readout", "k_options", "out_readout")):
        r_q, r_k, r_out = (shares[name] for name in ("q_readout", "k_options", "out_readout"))
        reading, frozen = t2_verdict(r_q["point"], r_k["point"], r_out=r_out["point"])
        t2.update(r_Q=r_q, r_K=r_k, r_out=r_out,
                  r_K_minus_r_Q=difference((_arm_numerator(data, "k_options"), gap),
                                           (_arm_numerator(data, "q_readout"), gap), resamples),
                  verdict=reading, frozen_rule_verdict=frozen,
                  ceiling_below_0_15=not at_least(r_out["point"], CEILING))
    else:
        t2.update(verdict=None, note="the T2 rule arms were not run")
    out["t2"] = t2
    out["t1"] = _read_t1(data, gap, resamples)
    return out


def _read_t1(data: dict, gap: np.ndarray, resamples) -> dict:
    sweeps = ((data.get("t1") or {}).get("sweeps") or {})
    forward, offline = sweeps.get("forward") or {}, sweeps.get("offline") or {}
    rule, name = (forward, "forward") if forward else (offline, "offline")
    if "T" not in rule or "dq_all" not in rule:
        return {"verdict": None, "note": f"no T1 sweep in this file "
                                         f"({sweeps.get('status', 'no t1.sweeps')})"}

    def sums(table, arm):
        return _array(table[arm]["per_instance"]["outside_sum"])

    o, o_q = sums(rule, "T"), sums(rule, "dq_all")
    out = {"rule_estimator": name,
           "O": statistic(o, gap, resamples), "O_q": statistic(o_q, gap, resamples),
           "M_q": statistic(o_q, o, resamples)}
    if "dq_all" in (data.get("arms") or {}):
        out["r_q"] = statistic(_arm_numerator(data, "dq_all"), gap, resamples)
    m_q = out["M_q"]["point"]
    out["verdict"] = t1_verdict(m_q)

    controls = {"M_C1": {}, "M_C2": {}, "M_C3": None, "M_S": None, "descriptive": {}}
    m_q_controls = None
    if "T" in offline:
        o_off = sums(offline, "T")
        for arm in sorted(offline):
            if arm == "T":
                continue
            value = statistic(sums(offline, arm), o_off, resamples)
            if arm.startswith("c1_d"):
                controls["M_C1"][arm] = value
            elif arm.startswith("c2_d"):
                controls["M_C2"][arm] = value
            elif arm == "c3_push":
                controls["M_C3"] = value
            elif arm == "s_k":
                controls["M_S"] = value
            else:
                controls["descriptive"][arm] = value
        if "dq_all" in offline:
            m_q_controls = controls["descriptive"]["dq_all"]["point"]
        if controls["M_C3"] is not None and "dq_all" in offline:
            out["M_q_minus_M_C3"] = difference((sums(offline, "dq_all"), o_off),
                                               (sums(offline, "c3_push"), o_off), resamples)
    out["controls"] = controls
    label, qualifiers = r1_label(
        m_q, m_c3=controls["M_C3"]["point"] if controls["M_C3"] else None,
        c1=[one["point"] for one in controls["M_C1"].values()],
        c2=[one["point"] for one in controls["M_C2"].values()], m_q_controls=m_q_controls)
    out.update(label=label, qualifiers=qualifiers,
               label_compares=("the offline M_q against the offline controls"
                               if m_q_controls is not None else "M_q against the controls"),
               M_q_offline=m_q_controls,
               n_c1_draws=len(controls["M_C1"]), n_c2_draws=len(controls["M_C2"]))
    return out


# ==============================================================================
# OUTPUT
# ==============================================================================

def _fmt(stat) -> str:
    if stat is None:
        return "n/a"
    point = stat.get("point") if isinstance(stat, dict) else stat
    if point is None:
        return "n/a"
    text = f"{point:.3f}"
    ci = stat.get("ci95") if isinstance(stat, dict) else None
    return f"{text} [{ci[0]:.3f}, {ci[1]:.3f}]" if ci else text


def markdown(readings: dict) -> str:
    lines = ["# B1 readings", "",
             f"Point estimates are ratios of means; brackets are 95% intervals from "
             f"{readings['bootstrap']['n_resamples']} resamples clustered by pressure_id "
             f"(seed {readings['bootstrap']['seed']}).", "",
             "## T1: loop closure", "",
             "| task | n | O | O_q | M_q | r_q | M_C3 | max C1/C2 | M_S | verdict | label |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for task, one in readings["tasks"].items():
        t1 = one["t1"]
        if t1.get("verdict") is None:
            lines.append(f"| {task} | {one['n_instances']} | {t1.get('note', 'n/a')} "
                         f"| | | | | | | | |")
            continue
        controls = t1["controls"]
        draws = [s["point"] for s in list(controls["M_C1"].values())
                 + list(controls["M_C2"].values()) if s["point"] is not None]
        top_draw = f"{max(draws):.3f}" if draws else "n/a"
        lines.append(
            f"| {task} | {one['n_instances']} | {_fmt(t1['O'])} | {_fmt(t1['O_q'])} | "
            f"{_fmt(t1['M_q'])} | {_fmt(t1.get('r_q'))} | {_fmt(controls['M_C3'])} | "
            f"{top_draw} | {_fmt(controls['M_S'])} | {t1['verdict']} | {t1['label']} |")
    lines += ["", "## T2: key-side or query-side", "",
              "| task | n | P | r_Q | r_K | r_K - r_Q | r_out | verdict | frozen rule |",
              "|---|---|---|---|---|---|---|---|---|"]
    for task, one in readings["tasks"].items():
        t2 = one["t2"]
        if t2.get("verdict") is None:
            lines.append(f"| {task} | {one['n_instances']} | {one['P']:.3f} | "
                         f"{t2.get('note', 'n/a')} | | | | | |")
            continue
        lines.append(f"| {task} | {one['n_instances']} | {one['P']:.3f} | {_fmt(t2['r_Q'])} | "
                     f"{_fmt(t2['r_K'])} | {_fmt(t2['r_K_minus_r_Q'])} | {_fmt(t2['r_out'])} | "
                     f"{t2['verdict']} | {t2['frozen_rule_verdict']} |")
    return "\n".join(lines) + "\n"


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("files", nargs="+", help="route_closure.json files, one per task")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR,
                        help=f"Where {JSON_NAME} and {MD_NAME} go. Default {DEFAULT_OUT_DIR}.")
    parser.add_argument("--n-resamples", type=int, default=N_RESAMPLES)
    parser.add_argument("--seed", type=int, default=SEED)
    return parser


def main(argv=None) -> dict:
    cli = build_parser().parse_args(argv)
    tasks: Dict[str, dict] = {}
    inputs = []
    for path in cli.files:
        with open(path) as handle:
            data = json.load(handle)
        if data.get("skipped"):
            raise SystemExit(f"{path}: skipped cell ({data['skipped']}); nothing to read")
        if data["task"] in tasks:
            raise SystemExit(f"{path}: a second file for task {data['task']!r}")
        tasks[data["task"]] = read_task(data, n_resamples=cli.n_resamples, seed=cli.seed)
        inputs.append({"path": path, "task": data["task"], "sha256": _sha256(path),
                       "schema": data.get("schema")})
    readings = {"schema": SCHEMA, "inputs": inputs,
                "bootstrap": {"n_resamples": cli.n_resamples, "seed": cli.seed,
                              "cluster": "pressure_id"},
                "rules": {"t1_closes_at": CLOSES_AT, "t2_side_margin": SIDE_MARGIN,
                          "t2_ceiling": CEILING, "r1_c3_margin": C3_MARGIN,
                          "boundary_tolerance": TOLERANCE,
                          "median_min_denominator": MIN_DENOMINATOR},
                "tasks": tasks}
    os.makedirs(cli.out_dir, exist_ok=True)
    with open(os.path.join(cli.out_dir, JSON_NAME), "w") as handle:
        json.dump(readings, handle, indent=2)
    with open(os.path.join(cli.out_dir, MD_NAME), "w") as handle:
        handle.write(markdown(readings))
    print(f"wrote {os.path.join(cli.out_dir, JSON_NAME)} and "
          f"{os.path.join(cli.out_dir, MD_NAME)} ({', '.join(tasks)})")
    return readings


if __name__ == "__main__":
    main()
