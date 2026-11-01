#!/usr/bin/env python3
"""Readers for instructed-route B2 (plans/B2-plan.md sections 2, 3 and 7; spec.md ruling R3). CPU only, numpy only.

p3  The SER MLP replication. Reads `knockout/groups.json` of the D, H and F cells of each run and task named in a
    layout file, applies R-cls (`component_analysis/rcls.py`) per one-member group, and writes `p3_rcls.csv` and
    `p3_verdict.json`. An MLP replicates when R-cls calls it "deception-leaning" on SER in both seeded runs and each
    cell read for that verdict has a `run_manifest.json` with a 40-hex `git_commit`; a missing item reads
    "not yet verified" and is named. FAR and SDR rows are descriptive (R3). An optional baseline run (seed 0) is
    compared with `docs/research/mechanism-analysis/phase1/rcls.csv`: d within 0.01 and the same class.

    Layout file:
        {"replication_runs": ["seed1", "seed2"], "baseline_run": "seed0",
         "runs": {"seed1": {"cells": {"ser": {"D": DIR, "H": DIR, "F": DIR}, "far": {...}}}, ...}}
    DIR is a cell directory (`<root>/<circuit>/<task>`), its `knockout/` subdirectory or the groups.json itself.

p2  The SDR wish test. Reads `groups.json` and `groups_instances.json` of the wish cell. Per group,
    f_wish = (mean m_I - mean m_KO) / (mean m_I - mean m_tw), where m_I is the clean margin, m_KO the margin under
    the group's neutral-twin interchange and m_tw the twin's own margin. 95% CIs come from 2,000 resamples of whole
    clusters, once by `instructed_inversion_id` and once by `pressure_id`, seed 20261101. Rule: the wish runs
    through the route when the quartet's f_wish is at least 0.5. The largest f among the `null_d*` groups and among
    the `kvg_*` groups is reported beside it, and either reaching 0.5 adds the label "not quartet-specific" (R3).

Usage:
    python scripts/instructed_route_b2_read.py p3 --layout LAYOUT.json [--out-dir DIR]
    python scripts/instructed_route_b2_read.py p2 --cell DIR [--locate NAME=DIR ...] [--reference NAME=DIR ...]
        [--exclude-ids FILE] [--dataset-dir DIR | --clusters FILE] [--output FILE]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from component_analysis import rcls as R  # noqa: E402

DIRECTION_DIR = ROOT / "docs" / "research" / "instructed-route"
DEFAULT_OUT_DIR = DIRECTION_DIR / "results"
RCLS_CSV = ROOT / "docs" / "research" / "mechanism-analysis" / "phase1" / "rcls.csv"
DEFAULT_DATASET = ROOT / "data" / "datasets" / "sdr_v2_inversion_reported"

MANIFEST = "run_manifest.json"
HEX40 = re.compile(r"[0-9a-f]{40}")

# P3
ROLES = ("D", "H", "F")
REPLICATION_TASK = "ser"
UNDER_TEST = ("mlp.11.0", "mlp.13.0", "mlp.16.0")
BASELINE_TOL = 0.01
P3_RULE = ("An MLP replicates when R-cls calls it deception-leaning on SER in both seeded runs and each run's SER "
           "D, H and F cells have a run_manifest.json with a 40-hex git_commit (B2 plan section 3). FAR and SDR "
           "rows are descriptive (R3).")

# P2
N_BOOT = 2000
BOOT_SEED = 20261101
CLUSTER_KEYS = ("instructed_inversion_id", "pressure_id")
WISH_BAR = 0.5
NULL_KINDS = (("null_d", "null_d"), ("kvg", "kvg_"))
NOT_SPECIFIC = "not quartet-specific"
EXPECT_N = 618
EXPECT_CLEAN = 3.15
EXPECT_TWIN = -2.92
EXPECT_TOL = 0.05
P2_RULE = ("The wish runs through the route when the quartet's neutral-twin interchange at all positions gives "
           "f_wish = (mean m_I - mean m_KO) / (mean m_I - mean m_tw) >= 0.5 on the 618 ids; when any of the 20 "
           "layer-matched random quartets or the seven other layer-17 KV groups also reaches 0.5, the verdict is "
           "labelled 'not quartet-specific' (spec R3).")


# ============================================================================== shared

def load_json(path) -> dict:
    with open(path) as handle:
        return json.load(handle)


def _jsonable(value):
    """NaN and infinities become null; numpy scalars become Python numbers."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _write_json(path, payload) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as handle:
        json.dump(_jsonable(payload), handle, indent=1)
        handle.write("\n")


def resolve_cell(path) -> Tuple[str, str]:
    """(cell dir, knockout dir) from a cell dir, its `knockout/` dir or a file inside `knockout/`."""
    path = os.path.abspath(str(path))
    if os.path.isfile(path) or path.endswith(".json"):
        knockout = os.path.dirname(path)
        return os.path.dirname(knockout), knockout
    if os.path.basename(path.rstrip(os.sep)) == "knockout":
        return os.path.dirname(path.rstrip(os.sep)), path
    return path, os.path.join(path, "knockout")


def manifest_problem(cell_dir) -> Optional[str]:
    """None when `<cell>/run_manifest.json` exists with a 40-hex `git_commit`; otherwise what is missing."""
    path = os.path.join(str(cell_dir), MANIFEST)
    if not os.path.isfile(path):
        return f"{path} missing"
    try:
        commit = load_json(path).get("git_commit")
    except (OSError, ValueError) as error:
        return f"{path} unreadable ({error})"
    if not isinstance(commit, str) or not HEX40.fullmatch(commit):
        return f"{path} git_commit {commit!r} is not 40-hex"
    return None


def read_ids(path) -> List[str]:
    """Ids from a JSON list or a text file with one id per line (blank lines and # comments skipped)."""
    with open(path) as handle:
        text = handle.read()
    if text.lstrip().startswith("["):
        return [str(one) for one in json.loads(text)]
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


# ============================================================================== P3

def group_label(row: dict) -> str:
    """A one-member group is keyed by its member's label (`mlp.11.0`, as in rcls.csv); others by name."""
    members = row.get("members") or []
    if row.get("n_components") == 1 and len(members) == 1:
        return str(members[0])
    return str(row["name"])


def group_entries(payload: dict) -> Dict[str, dict]:
    """{label: {"drop", "se", "clean", "n", "group"}} from a groups.json payload, in file order."""
    clean = payload["clean_run"]["mean_logit_difference"]
    out = {}
    for row in payload["groups"]:
        out[group_label(row)] = {"drop": row["mean_drop"], "se": row["standard_error"], "clean": clean,
                                 "n": row.get("n"), "group": row["name"]}
    return out


def _read_task(run: str, task: str, cells: dict) -> Tuple[List[dict], Dict[str, dict], List[str]]:
    """R-cls rows, {label: rcls output} and the problems of one run's D, H and F cells of one task."""
    problems: List[str] = []
    entries: Dict[str, Dict[str, dict]] = {}
    instances: Dict[str, list] = {}
    sources: Dict[str, str] = {}
    for role in ROLES:
        if role not in cells:
            problems.append(f"{run} {task.upper()} {role}: no cell in the layout")
            continue
        cell, knockout = resolve_cell(cells[role])
        path = os.path.join(knockout, "groups.json")
        if not os.path.isfile(path):
            problems.append(f"{run} {task.upper()} {role}: {path} missing")
            continue
        payload = load_json(path)
        entries[role] = group_entries(payload)
        instances[role] = list(payload.get("instances") or [])
        sources[role] = path
        problem = manifest_problem(cell)
        if problem:
            problems.append(f"{run} {task.upper()} {role}: {problem}")
    same_order = None
    if len(instances) == len(ROLES):
        # Equal ids is a set property: H and F come from other dataset directories and may emit another order.
        if not (set(instances["D"]) == set(instances["H"]) == set(instances["F"])):
            problems.append(f"{run} {task.upper()}: the D, H and F cells do not hold the same instance ids")
        same_order = instances["D"] == instances["H"] == instances["F"]
    rows: List[dict] = []
    classes: Dict[str, dict] = {}
    if len(entries) == len(ROLES):
        for label in entries["D"]:
            if not all(label in entries[role] for role in ROLES):
                problems.append(f"{run} {task.upper()}: {label} is not in every cell")
                continue
            out = R.rcls(**{role: entries[role][label] for role in ROLES})
            classes[label] = out
            row = {"run": run, "task": task, "label": label, "group": entries["D"][label]["group"],
                   "class": out["class"], "reason": out["reason"],
                   **{f"d_{role}": out["d"][role] for role in ROLES},
                   **{f"sig_{role}": out["sig"][role] for role in ROLES},
                   "m_HF": out["m_HF"], "U_HF": out["U_HF"], "ids_same_order": same_order}
            for role in ROLES:
                e = entries[role][label]
                row.update({f"drop_{role}": e["drop"], f"se_{role}": e["se"], f"clean_{role}": e["clean"],
                            f"n_{role}": e["n"], f"source_{role}": sources[role]})
            rows.append(row)
    return rows, classes, problems


def _baseline(classes: Dict[str, dict], problems: List[str], rcls_csv) -> dict:
    """Seed-0 SER reproduction of rcls.csv: d(D), d(H), d(F) within 0.01 and the same class."""
    with open(rcls_csv) as handle:
        reference = {(row["task"], row["label"]): row for row in csv.DictReader(handle)}
    labels = {}
    for label in UNDER_TEST:
        ref = reference.get((REPLICATION_TASK, label))
        got = classes.get(label)
        if ref is None or got is None:
            labels[label] = {"ok": False, "reason": "missing in " + ("rcls.csv" if ref is None else "the run")}
            continue
        diff = {role: got["d"][role] - float(ref["d_" + role]) for role in ROLES}
        ok = all(abs(v) <= BASELINE_TOL for v in diff.values()) and got["class"] == ref["class"]
        labels[label] = {"ok": ok, "class": got["class"], "reference_class": ref["class"], "d_diff": diff,
                         "d": dict(got["d"]), "reference_d": {role: float(ref["d_" + role]) for role in ROLES}}
    return {"ok": all(one["ok"] for one in labels.values()), "tolerance": BASELINE_TOL,
            "reference": str(rcls_csv), "labels": labels, "problems": problems}


def _summary(verdicts: List[dict]) -> str:
    by = {}
    for v in verdicts:
        by.setdefault(v["status"], []).append(v["label"])
    if "not yet verified" in by:
        parts = [f"not yet verified: {', '.join(by['not yet verified'])}"]
        parts += [f"{s}: {', '.join(by[s])}" for s in ("replicates", "fails") if s in by]
        return "; ".join(parts)
    return "; ".join(f"{s}: {', '.join(by[s])}" for s in ("replicates", "fails") if s in by)


def read_p3(layout: dict, *, rcls_csv=RCLS_CSV) -> dict:
    runs = layout["runs"]
    baseline = layout.get("baseline_run")
    replication = list(layout.get("replication_runs") or [r for r in runs if r != baseline])
    rows: List[dict] = []
    classes: Dict[Tuple[str, str], Dict[str, dict]] = {}
    problems: Dict[Tuple[str, str], List[str]] = {}
    order = ([baseline] if baseline in runs else []) + [r for r in runs if r != baseline]
    for run in order:
        for task, cells in (runs[run].get("cells") or {}).items():
            task_rows, task_classes, task_problems = _read_task(run, task, cells)
            role = "baseline" if run == baseline else ("replication" if run in replication else "other")
            provenance = "ok" if not task_problems else " | ".join(task_problems)
            for row in task_rows:
                row["run_role"] = role
                row["provenance"] = provenance
            rows.extend(task_rows)
            classes[(run, task)] = task_classes
            problems[(run, task)] = task_problems

    verdicts = []
    for label in UNDER_TEST:
        missing: List[str] = []
        if len(replication) < 2:
            missing.append(f"two seeded replication runs are needed and the layout names {len(replication)}")
        got = {}
        for run in replication:
            if (run, REPLICATION_TASK) not in classes:
                missing.append(f"{run}: no SER cells in the layout")
                continue
            missing.extend(problems[(run, REPLICATION_TASK)])
            out = classes[(run, REPLICATION_TASK)].get(label)
            if out is None:
                missing.append(f"{run}: no SER row for {label}")
            else:
                got[run] = out["class"]
        failing = {run: cls for run, cls in got.items() if cls != "deception-leaning"}
        missing = list(dict.fromkeys(missing))
        if failing:
            miss = "; ".join(f"{run} class {cls}" for run, cls in failing.items())
            if missing:
                status = "not yet verified"
                text = (f"not yet verified: {label} misses the rule ({miss}) and the evidence is incomplete: "
                        + "; ".join(missing))
            else:
                status = "fails"
                text = f"{label} does not meet the rule on SER: {miss}"
        elif missing:
            status = "not yet verified"
            text = f"not yet verified: {label}: " + "; ".join(missing)
        else:
            status = "replicates"
            text = f"{label} is deception-leaning on SER in {' and '.join(replication)}, each with provenance"
        verdicts.append({"label": label, "status": status, "classes": got, "missing": missing, "text": text})

    out = {"rule": P3_RULE, "replication_runs": replication, "baseline_run": baseline, "rows": rows,
           "verdicts": verdicts, "summary": _summary(verdicts),
           "problems": {f"{run}/{task}": p for (run, task), p in problems.items()}}
    if baseline:
        out["baseline"] = _baseline(classes.get((baseline, REPLICATION_TASK), {}),
                                    problems.get((baseline, REPLICATION_TASK), [f"{baseline}: no SER cells"]),
                                    rcls_csv)
    return out


P3_COLUMNS = (["run", "run_role", "task", "label", "group", "class", "reason"]
              + [f"d_{r}" for r in ROLES] + [f"sig_{r}" for r in ROLES] + ["m_HF", "U_HF"]
              + [f"{k}_{r}" for r in ROLES for k in ("drop", "se", "clean", "n")]
              + ["ids_same_order", "provenance"] + [f"source_{r}" for r in ROLES])


def write_p3(result: dict, out_dir, layout_path=None) -> Tuple[str, str]:
    os.makedirs(str(out_dir), exist_ok=True)
    csv_path = os.path.join(str(out_dir), "p3_rcls.csv")
    with open(csv_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=P3_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in P3_COLUMNS})
    verdict_path = os.path.join(str(out_dir), "p3_verdict.json")
    payload = {k: v for k, v in result.items() if k != "rows"}
    payload["layout"] = None if layout_path is None else os.path.abspath(str(layout_path))
    payload["rows_file"] = csv_path
    _write_json(verdict_path, payload)
    return csv_path, verdict_path


# ============================================================================== P2

def f_wish(clean, knocked, twin) -> float:
    """(mean m_I - mean m_KO) / (mean m_I - mean m_tw); NaN when the gap is zero."""
    clean, knocked, twin = (np.asarray(x, dtype=np.float64) for x in (clean, knocked, twin))
    gap = clean.mean() - twin.mean()
    if gap == 0:
        return float("nan")
    return float((clean.mean() - knocked.mean()) / gap)


def wish_passes(f) -> bool:
    """The pre-registered 0.5 rule, no tolerance; NaN fails."""
    return bool(f is not None and math.isfinite(f) and f >= WISH_BAR)


def cluster_bootstrap(clean, knocked, twin, clusters: Sequence, *, n_boot: int = N_BOOT,
                      seed: int = BOOT_SEED) -> np.ndarray:
    """f_wish over `n_boot` resamples of whole clusters, drawn with replacement, as many as there are clusters.

    The ratio of means equals sum(m_I - m_KO) / sum(m_I - m_tw) over the resampled instances, so each resample is a
    count-weighted sum of per-cluster totals. Clusters are taken in sorted label order, so the draws do not depend
    on the instance order. A resample with a zero gap is NaN.
    """
    clean, knocked, twin = (np.asarray(x, dtype=np.float64) for x in (clean, knocked, twin))
    labels = sorted(set(clusters))
    index = {label: i for i, label in enumerate(labels)}
    codes = np.array([index[c] for c in clusters], dtype=np.int64)
    k = len(labels)
    num = np.bincount(codes, weights=clean - knocked, minlength=k)
    den = np.bincount(codes, weights=clean - twin, minlength=k)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, k, size=(n_boot, k))
    counts = np.zeros((n_boot, k), dtype=np.float64)
    np.add.at(counts, (np.repeat(np.arange(n_boot), k), draws.ravel()), 1.0)
    top, bottom = counts @ num, counts @ den
    out = np.full(n_boot, np.nan)
    ok = bottom != 0
    out[ok] = top[ok] / bottom[ok]
    return out


def _ci(draws: np.ndarray) -> List[float]:
    finite = draws[np.isfinite(draws)]
    if not finite.size:
        return [float("nan"), float("nan")]
    lo, hi = np.percentile(finite, [2.5, 97.5])
    return [float(lo), float(hi)]


def read_p2_cell(path, clusters: Dict[str, dict], *, n_boot: int = N_BOOT, seed: int = BOOT_SEED,
                 exclude_ids: Optional[Iterable[str]] = None) -> dict:
    """f_wish and its clustered CIs for every group of one cell's groups knockout."""
    cell, knockout = resolve_cell(path)
    groups = load_json(os.path.join(knockout, "groups.json"))
    instances = load_json(os.path.join(knockout, groups.get("instances_file") or "groups_instances.json"))
    ids = [str(one) for one in instances["instance_ids"]]
    twin = instances.get("neutral_twin_logit_difference") or instances.get("counterfactual_logit_difference")
    if not twin or len(twin) != len(ids) or any(one is None for one in twin):
        raise ValueError(f"{knockout}: no twin margin for every instance; the cell must run the neutral-twin "
                         f"interchange (--knockout-counterfactual neutral_twin)")
    excluded = set(exclude_ids or ())
    keep = [i for i, one in enumerate(ids) if one not in excluded]
    for i in keep:
        if ids[i] not in clusters:
            raise ValueError(f"no cluster ids for instance {ids[i]}")
    clean_all = np.asarray(instances["clean_logit_difference"], dtype=np.float64)
    twin_all = np.asarray(twin, dtype=np.float64)
    clean, tw = clean_all[keep], twin_all[keep]
    labels = {key: [clusters[ids[i]][key] for i in keep] for key in CLUSTER_KEYS}
    consistent = True
    out_groups = {}
    for row in groups["groups"]:
        name = row["name"]
        knocked_all = np.asarray(instances["knocked_logit_difference"][name], dtype=np.float64)
        if len(knocked_all) != len(ids):
            raise ValueError(f"{knockout}: group {name} has {len(knocked_all)} margins for {len(ids)} instances")
        if row.get("mean_drop") is not None and abs(
                (clean_all.mean() - knocked_all.mean()) - row["mean_drop"]) > 1e-6:
            consistent = False
        knocked = knocked_all[keep]
        f = f_wish(clean, knocked, tw)
        ci = {key: _ci(cluster_bootstrap(clean, knocked, tw, labels[key], n_boot=n_boot, seed=seed))
              for key in CLUSTER_KEYS}
        out_groups[name] = {"f": f, "passes": wish_passes(f), "ci": ci, "mean_knocked": float(knocked.mean()),
                            "members": row.get("members"), "n_components": row.get("n_components")}
    return {"cell": cell, "groups_file": os.path.join(knockout, "groups.json"), "plan": groups.get("plan"),
            "n": len(keep), "n_excluded": len(ids) - len(keep),
            "n_unpaired": len(groups.get("unpaired_instance_ids") or []),
            "n_clusters": {key: len(set(labels[key])) for key in CLUSTER_KEYS},
            "mean_clean": float(clean.mean()) if len(keep) else float("nan"),
            "mean_twin": float(tw.mean()) if len(keep) else float("nan"),
            "consistent_with_groups_json": consistent, "manifest_problem": manifest_problem(cell),
            "groups": out_groups}


def p2_checks(cell: dict, *, expect_n: int = EXPECT_N, expect_clean: float = EXPECT_CLEAN,
              expect_twin: float = EXPECT_TWIN, tol: float = EXPECT_TOL) -> dict:
    """B2 plan section 7: n = 618, mean clean I margin 3.15 and mean twin margin -2.92, each within 0.05."""
    items = {"n": {"observed": cell["n"], "expected": expect_n, "ok": cell["n"] == expect_n},
             "mean_clean": {"observed": cell["mean_clean"], "expected": expect_clean,
                            "ok": abs(cell["mean_clean"] - expect_clean) <= tol},
             "mean_twin": {"observed": cell["mean_twin"], "expected": expect_twin,
                           "ok": abs(cell["mean_twin"] - expect_twin) <= tol},
             "unpaired": {"observed": cell["n_unpaired"], "expected": 0, "ok": cell["n_unpaired"] == 0},
             "groups_json": {"observed": cell["consistent_with_groups_json"], "expected": True,
                             "ok": bool(cell["consistent_with_groups_json"])}}
    failed = [name for name, item in items.items() if not item["ok"]]
    return {"ok": not failed, "failed": failed, "tolerance": tol, "items": items}


def p2_verdict(cell: dict, *, quartet: str = "quartet", checks: Optional[dict] = None) -> dict:
    groups = cell["groups"]
    if quartet not in groups:
        raise ValueError(f"{cell['groups_file']}: no group named {quartet!r} (groups: {', '.join(groups)})")
    q = groups[quartet]
    null_max, null_argmax, missing = {}, {}, []
    for kind, prefix in NULL_KINDS:
        named = {name: g["f"] for name, g in groups.items() if name.startswith(prefix)}
        finite = {name: f for name, f in named.items() if f is not None and math.isfinite(f)}
        if not finite:
            null_max[kind], null_argmax[kind] = None, None
            missing.append(f"no {prefix}* groups with a finite f")
            continue
        best = max(finite, key=lambda name: (finite[name], name))
        null_max[kind], null_argmax[kind] = finite[best], best
    reaching = [null_argmax[k] for k, _ in NULL_KINDS if null_max[k] is not None and null_max[k] >= WISH_BAR]
    labels = [NOT_SPECIFIC] if reaching else []
    passes = wish_passes(q["f"])
    text = (f"f_wish(quartet) = {q['f']:.3f} {'>=' if passes else '<'} 0.5: "
            + ("the wish runs through the route" if passes else "the wish takes another path"))
    if reaching:
        text += "; " + NOT_SPECIFIC + " (" + ", ".join(
            f"{name} reaches {groups[name]['f']:.3f}" for name in reaching) + ")"
    problems = list(missing)
    if cell.get("manifest_problem"):
        problems.append(cell["manifest_problem"])
    if checks is not None and not checks["ok"]:
        problems.extend(f"execution check {name} failed (observed {checks['items'][name]['observed']}, "
                        f"expected {checks['items'][name]['expected']})" for name in checks["failed"])
    status = "complete" if not problems else "not yet verified: " + "; ".join(problems)
    return {"rule": P2_RULE, "quartet": quartet, "quartet_f": q["f"], "quartet_ci": q["ci"], "passes": passes,
            "null_max": null_max, "null_argmax": null_argmax, "labels": labels, "text": text, "status": status}


def load_clusters(dataset_dir=None, clusters_file=None) -> Dict[str, dict]:
    """{instance_id: {instructed_inversion_id, pressure_id}} from a JSON file or the dataset's rows."""
    if clusters_file:
        raw = load_json(clusters_file)
        return {str(k): {key: v[key] for key in CLUSTER_KEYS} for k, v in raw.items()}
    import datasets  # lazy: only the CLI path reads the arrow files

    data = datasets.load_from_disk(str(dataset_dir or DEFAULT_DATASET))
    if hasattr(data, "keys"):
        split = "test" if "test" in data else list(data.keys())[0]
        data = data[split]
    out = {}
    for row in data.select_columns(["instance_id", *CLUSTER_KEYS]):
        out[str(row["instance_id"])] = {key: row[key] for key in CLUSTER_KEYS}
    return out


def _named(values: Optional[List[str]]) -> List[Tuple[str, str]]:
    out = []
    for one in values or []:
        if "=" not in one:
            raise SystemExit(f"expected NAME=DIR, got {one!r}")
        name, path = one.split("=", 1)
        out.append((name, path))
    return out


def run_p2(args) -> dict:
    clusters = load_clusters(args.dataset_dir, args.clusters)
    common = {"n_boot": args.n_boot, "seed": args.seed}
    primary = read_p2_cell(args.cell, clusters, **common)
    checks = p2_checks(primary, expect_n=args.expect_n)
    verdict = p2_verdict(primary, quartet=args.quartet_name, checks=checks)
    out = {"rule": P2_RULE, "verdict": verdict, "checks": checks, "primary": primary,
           "bootstrap": {"n_boot": args.n_boot, "seed": args.seed, "cluster_keys": list(CLUSTER_KEYS)},
           "locate": {}, "reference": {}, "sensitivity": None}
    for name, path in _named(args.locate):
        cell = read_p2_cell(path, clusters, **common)
        out["locate"][name] = {"cell": cell, "verdict": p2_verdict(cell, quartet=args.quartet_name),
                               "note": "locates the effect; decides nothing"}
    for name, path in _named(args.reference):
        cell = read_p2_cell(path, clusters, **common)
        out["reference"][name] = {"cell": cell, "quartet_f": cell["groups"].get(args.quartet_name, {}).get("f"),
                                  "note": ("f of the same groups on the reference cell (f_D on SDR D), "
                                           "clustered by the wish rows' ids; descriptive")}
    if args.exclude_ids:
        excluded = set(read_ids(args.exclude_ids))
        cell = read_p2_cell(args.cell, clusters, exclude_ids=excluded, **common)
        out["sensitivity"] = {"exclude_ids": os.path.abspath(args.exclude_ids), "cell": cell,
                              "verdict": p2_verdict(cell, quartet=args.quartet_name),
                              "note": "sensitivity row; the primary verdict stands"}
    _write_json(args.output, out)
    return out


# ============================================================================== CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p3 = sub.add_parser("p3", help="SER MLP replication: R-cls per run and the verdict")
    p3.add_argument("--layout", required=True, help="JSON layout of runs, tasks and D/H/F cell directories")
    p3.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    p3.add_argument("--rcls-csv", default=str(RCLS_CSV), help="seed-0 reference for the baseline check")
    p2 = sub.add_parser("p2", help="SDR wish test: f_wish, clustered CIs, nulls and the verdict")
    p2.add_argument("--cell", required=True, help="the primary wish cell (all positions)")
    p2.add_argument("--locate", action="append", metavar="NAME=DIR", help="descriptive position-set cells")
    p2.add_argument("--reference", action="append", metavar="NAME=DIR", help="descriptive cells, e.g. SDR D")
    p2.add_argument("--exclude-ids", help="ids dropped in a sensitivity row (the 57 held-out-sample ids)")
    p2.add_argument("--dataset-dir", default=str(DEFAULT_DATASET), help="source of the cluster ids")
    p2.add_argument("--clusters", help="JSON {instance_id: {instructed_inversion_id, pressure_id}}; overrides")
    p2.add_argument("--quartet-name", default="quartet")
    p2.add_argument("--n-boot", type=int, default=N_BOOT)
    p2.add_argument("--seed", type=int, default=BOOT_SEED)
    p2.add_argument("--expect-n", type=int, default=EXPECT_N)
    p2.add_argument("--output", default=str(DEFAULT_OUT_DIR / "p2_wish.json"))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "p3":
        result = read_p3(load_json(args.layout), rcls_csv=args.rcls_csv)
        csv_path, verdict_path = write_p3(result, args.out_dir, layout_path=args.layout)
        for v in result["verdicts"]:
            print(f"  {v['status']:<17} {v['text']}")
        if "baseline" in result:
            print(f"  baseline seed-0 reproduction: {'ok' if result['baseline']['ok'] else 'MISS'}")
        print(f"P3: {result['summary']}\n  wrote {csv_path}\n  wrote {verdict_path}")
        return 0
    out = run_p2(args)
    v = out["verdict"]
    print(f"P2: {v['text']}\n  null max: null_d {v['null_max']['null_d']}, kvg {v['null_max']['kvg']}"
          f"\n  status: {v['status']}\n  wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
