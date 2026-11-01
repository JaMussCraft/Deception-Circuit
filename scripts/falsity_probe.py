"""
scripts/falsity_probe.py: the B2 P1 falsity probe, fit, score and per-token read (instructed-route ticket T7).

CPU only, numpy and torch only (mgnp has neither sklearn nor scipy). Reads a capture directory written by
`scripts/falsity_probe_capture.py` (T6; its module docstring fixes `rows.<cell>.jsonl`, `resid.<cell>.pt` and
`tokens.<cell>.pt`). The design is `docs/research/instructed-route/plans/B2-plan.md` section 1 and ruling R2 of
`docs/research/instructed-route/spec.md`.

    python scripts/falsity_probe.py fit   --capture DIR [--out DIR]
    python scripts/falsity_probe.py score --capture DIR [--out DIR] [--n-resamples 2000] [--n-permutations 200]
    python scripts/falsity_probe.py read  --capture DIR [--out DIR] [--n-resamples 2000]

Torch runs on one thread (`FALSITY_PROBE_THREADS` overrides); export `OMP_NUM_THREADS=1` as well on a login node.
`--out` defaults to `docs/research/instructed-route/results`. `--n-resamples` and `--n-permutations` exist for the
tests; the pre-registered values are the defaults. `score` needs `fit`'s `p1_fit.pt` in `--out`; `read` needs only
the capture.

ROWS AND LAYERS
---------------
The residual has rows 0 to 32: row 0 is the embedding output and row l + 1 the residual after decoder layer l (the
`fig9_lens.csv` convention, where E16's "layer 17" is row 18). Every output names both `row` and `layer`. Layers 4
to 31 (rows 5 to 32) are eligible for selection.

CELLS
-----
Cells are found by the `role`, `task` and `condition` fields of their rows (or `capture_plan.json` for an empty
cell), not by file name: fit = (fit, far_v2, D/H); select = (select, far_v2, D/H/HI); FAR gate = (far_gate, far_v2,
D/H/HI/F/I); SER = (ser_test, ser_v2, D/H/HI/F/I); SDR = (sdr, sdr_v2, D/H/I_reported), optional.
A cell is compared with "its own H twin": the H rows of the same role with the same `instance_id` (an inner join;
unjoined rows are counted). HI rows under `h_honest_instruction_clean` 0.3 (`keep_if_value`) are dropped if any
reached the capture. SDR I-reported rows flagged `in_seed0_sample` or `in_seed1_sample` are dropped, so the held-out
sample is never read. Clusters are the row's `pressure_id` (twins share it).

FIT (`fit`)
-----------
Standardise each row on the fit split (far train D and H); L2 logistic regression, D = 1, in float64 torch LBFGS
(`component_analysis/probe.py`, objective mean BCE + ||w||^2 / (2 C n), sklearn's C), C in {1e-3, 1e-2, 1e-1, 1}, at
every row; and the mass-mean direction (mean D minus mean H, raw residual; descriptive). Selection reads the select
split only (`check_selection_rows` raises on any other row): the AUROC of D against the pooled H and HI rows. Per
row the best C is taken (an exact tie goes to the smaller C); among eligible rows whose best is within 0.005 of the
overall best, the layer nearest 17 wins (then the higher AUROC, then the lower layer). Any non-finite residual in a
fit or select cell stops the fit.

`p1_fit.pt` (torch, `weights_only` loadable): schema, c_grid, mean [R, d] and std [R, d] float64 (the fit-split
standardisation), weights [R, nC, d] and bias [R, nC] float64 (standardised space), mass_mean [R, d] float64 (raw
space), selected (as in the JSON), n_rows R.

`p1_fit.json`: schema "falsity-probe-fit/1", capture, c_grid, eligible_layers [4, 31], centre_layer 17, tie 0.005,
n_fit {D, H}, n_select {D, H, HI}, select_auroc [R][nC] (D against H + HI), select_mass_mean_auroc [R],
converged [R][nC], grad_norm [R][nC], n_not_converged,
selected {row, layer, C, C_index, auroc, best_auroc, candidates: [{row, layer, auroc}] within the tie}.

SCORE (`score`) -> `p1_probe.json` and `p1_probe.md`
---------------------------------------------------
Every AUROC is Mann-Whitney with ties at half, cell rows (label 1) against their own H twins (label 0), with the
probe's decision value oriented D-positive (never flipped). Every CI is the percentile 95% interval of a bootstrap
that resamples `pressure_id` clusters of joined pairs, numpy `default_rng(20261101)`.

- schema "falsity-probe-score/1", capture, fit_file, fit_sha256, seed, n_resamples.
- selected: fit's selection (row, layer, C, C_index, auroc on the select split).
- far_gate: auroc, ci, n_pairs, n_unjoined, n_clusters, threshold 0.75, fallback (auroc < 0.75).
- rule: SER D against SER H. auroc, ci, n_pairs, n_unjoined, n_clusters, n_resamples, seed, band
  ("misleadingness" >= 0.75, "indeterminate", "literal_falsity" < 0.6), anti_aligned (auroc < 0.5),
  ci_edges_crossed (band edges inside the CI), ci_crosses_band_edge (bool).
- controls: {ser_D, far_I, far_HI, ser_HI, ser_I, far_F, ser_F} -> {cell, twin, auroc, ci, n_pairs, n_unjoined,
  n_clusters, n_nonfinite_dropped}.
- r2: label ("clean" / "instruction-confounded" / null when the band is not misleadingness), r2_cells
  {far_I, far_HI, ser_HI}, controls_at_or_over_0_6 (list), f_controls_off_half (F cells outside [0.4, 0.6], a
  descriptive broken-probe warning; the plan says "about 0.5").
- verdict: band, anti_aligned, r2_label, fallback, ci_crosses_band_edge, reading (text).
- hi_kept_share: {HI cell: kept share from `capture_plan.json` or null}; hi_below_bar_dropped {HI cell: n}.
- by_layer: [R] of {row, layer, eligible, select_auroc [nC], select_best_C, gate_auroc [nC], ser_auroc [nC],
  ser_auroc_at_select_best_C, mass_mean {select, gate, ser}} (descriptive; decides nothing).
- permutation_null: n_permutations, seed 20261102, row, C, n_pairs, aurocs [n], summary {n, mean, sd, q05, q95, min,
  max}, observed, p_one_sided ((1 + #null >= observed) / (n + 1)), p_two_sided (on |auroc - 0.5|). Each refit swaps
  the D and H labels of a random half of the fit-split instance pairs (`probe.permutation_swaps`), keeps the fit
  standardisation, and scores SER D against SER H.
- loco: row, C, by_clause {pressure_id: {auroc, n_D, n_H}} over FAR train and validation D and H pooled, each fold
  standardised and fitted on the other clauses; pooled_auroc over every held-out score; min_auroc.
- sdr (descriptive): {D: SDR D against SDR H, I_reported: the 618 reported rows against SDR H, with
  n_dropped_sample}; each {auroc, ci, n_pairs, n_unjoined, ...}. Empty when the capture has no SDR cells.
- nonfinite: {cell: number of residual elements that are not finite}.
- provenance: capture_manifest (path), git_commit, status ("ok" or "not yet verified: ...").

READ (`read`) -> `p1_tokens.json` and `p1_tokens.md`
---------------------------------------------------
Per joined D and H pair: D minus H of the centred logit (`logits_centred`, the sum of `dla` over every key) and of
each group's summed DLA, on column 0 (the honest item: suppression, negative means D lowers it) and column 1 (the
deceptive item: promotion, positive means D raises it). Groups: whole_model (`logits_centred`), whole_model_raw
(`logits_raw`), whole_model_logsoftmax (`logits_logsoftmax`), quartet (L17H24 to L17H27), late_honest_own (the
task's C6 late heads), late_honest_far_ser (the union of FAR's and SER's, the same set on both tasks), mlp.30,
mlp.31.

- schema "falsity-probe-tokens/1", capture, seed, n_resamples, sign (text), groups {name: [[kind, layer, index]]
  or the logits field}, late_honest_heads {far, ser, sdr}.
- tasks: {far (FAR gate D, H), ser (SER D, H), sdr (SDR D, H), sdr_I_reported (I-reported against SDR H, sample
  rows dropped)} -> {cells, n_pairs, n_unjoined, n_token_mismatch, n_dropped_sample, n_clusters,
  dla_sum_max_abs_error, groups {group: {suppression {mean, sd, ci}, promotion {mean, sd, ci}}}}.
- far_minus_ser: {group: {suppression {mean, ci}, promotion {mean, ci}}}, the FAR mean minus the SER mean, the CI
  from independent cluster bootstraps (FAR seed 20261101, SER seed 20261102).
- provenance: as in `score`.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from component_analysis import probe  # noqa: E402

FIT_SCHEMA = "falsity-probe-fit/1"
SCORE_SCHEMA = "falsity-probe-score/1"
TOKENS_SCHEMA = "falsity-probe-tokens/1"
DEFAULT_OUT = os.path.join(ROOT, "docs", "research", "instructed-route", "results")

SEED = 20261101
C_GRID = [1e-3, 1e-2, 1e-1, 1.0]
ELIGIBLE_LAYERS = (4, 31)
CENTRE_LAYER = 17
TIE = 0.005
N_RESAMPLES = 2000
N_PERMUTATIONS = 200
HI_BAR = 0.3
SAMPLE_FLAGS = ("in_seed0_sample", "in_seed1_sample")

QUARTET = [("head", 17, head) for head in range(24, 28)]
#: C6's late honest-leaning heads (synthesis C6, "C-honest"): every head listed under `<task>.c_honest.heads` of
#: `docs/research/mechanism-analysis/phase2/p2_readings.json`, in its order. A test checks the copy.
LATE_HONEST_HEADS = {
    "far": [(22, 8), (22, 11), (22, 16), (22, 19), (22, 27), (22, 28), (22, 29),
            (30, 12), (30, 15), (30, 24), (30, 26), (30, 30)],
    "ser": [(18, 16), (18, 20), (18, 23), (18, 28), (30, 12), (30, 15), (30, 24), (30, 26)],
    "sdr": [(18, 20), (18, 23), (18, 28), (30, 12), (30, 15), (30, 24), (30, 30)],
}

#: name -> (role, task, condition)
CELLS = {
    "fit_D": ("fit", "far_v2", "D"), "fit_H": ("fit", "far_v2", "H"),
    "select_D": ("select", "far_v2", "D"), "select_H": ("select", "far_v2", "H"),
    "select_HI": ("select", "far_v2", "HI"),
    "gate_D": ("far_gate", "far_v2", "D"), "gate_H": ("far_gate", "far_v2", "H"),
    "gate_HI": ("far_gate", "far_v2", "HI"), "gate_F": ("far_gate", "far_v2", "F"),
    "gate_I": ("far_gate", "far_v2", "I"),
    "ser_D": ("ser_test", "ser_v2", "D"), "ser_H": ("ser_test", "ser_v2", "H"),
    "ser_HI": ("ser_test", "ser_v2", "HI"), "ser_F": ("ser_test", "ser_v2", "F"),
    "ser_I": ("ser_test", "ser_v2", "I"),
    "sdr_D": ("sdr", "sdr_v2", "D"), "sdr_H": ("sdr", "sdr_v2", "H"),
    "sdr_I_reported": ("sdr", "sdr_v2", "I_reported"),
}
#: control name -> (cell, twin), plan section 1's control table.
CONTROLS = {
    "ser_D": ("ser_D", "ser_H"), "far_I": ("gate_I", "gate_H"), "far_HI": ("gate_HI", "gate_H"),
    "ser_HI": ("ser_HI", "ser_H"), "ser_I": ("ser_I", "ser_H"), "far_F": ("gate_F", "gate_H"),
    "ser_F": ("ser_F", "ser_H"),
}


def fail(message: str):
    raise SystemExit(f"falsity_probe: {message}")


def layer_of(row: int) -> int:
    return row - 1


def eligible(row: int) -> bool:
    return ELIGIBLE_LAYERS[0] <= layer_of(row) <= ELIGIBLE_LAYERS[1]


# ==============================================================================
# THE CAPTURE DIRECTORY
# ==============================================================================

def _load_pt(path: str):
    import torch

    return torch.load(path, map_location="cpu", weights_only=True)


class Capture:
    """Index of a T6 capture directory, by (role, task, condition)."""

    def __init__(self, directory: str):
        if not os.path.isdir(directory):
            fail(f"capture directory {directory} does not exist")
        self.directory = os.path.abspath(directory)
        plan_path = os.path.join(self.directory, "capture_plan.json")
        self.plan = json.load(open(plan_path)) if os.path.exists(plan_path) else {}
        self.meta: Dict[str, Tuple[str, str, str]] = {}
        self._rows: Dict[str, List[dict]] = {}
        for path in sorted(glob.glob(os.path.join(self.directory, "rows.*.jsonl"))):
            name = os.path.basename(path)[len("rows."):-len(".jsonl")]
            rows = self.rows(name)
            if rows:
                first = rows[0]
                key = (first["role"], first["task"], first["condition"])
            else:
                spec = self.plan.get("cells", {}).get(name, {}).get("spec", {})
                key = (spec.get("role"), spec.get("task"), spec.get("condition"))
            self.meta[name] = key

    def rows(self, name: str) -> List[dict]:
        if name not in self._rows:
            path = os.path.join(self.directory, f"rows.{name}.jsonl")
            if not os.path.exists(path):
                fail(f"{path} does not exist")
            with open(path) as handle:
                self._rows[name] = [json.loads(line) for line in handle if line.strip()]
        return self._rows[name]

    def find(self, cell: str, *, required: bool = True) -> Optional[str]:
        key = CELLS[cell]
        names = [name for name, meta in self.meta.items() if meta == key]
        if len(names) > 1:
            fail(f"more than one cell is {key}: {names}")
        if not names:
            if required:
                fail(f"no cell with role, task and condition {key} in {self.directory}")
            return None
        return names[0]

    def _ids_match(self, name: str, blob: dict, kind: str) -> None:
        ids = [row["instance_id"] for row in self.rows(name)]
        if list(blob["ids"]) != ids:
            fail(f"{kind}.{name}.pt ids do not match rows.{name}.jsonl")

    def resid(self, name: str):
        blob = _load_pt(os.path.join(self.directory, f"resid.{name}.pt"))
        self._ids_match(name, blob, "resid")
        return blob["resid"]

    def tokens(self, name: str) -> dict:
        blob = _load_pt(os.path.join(self.directory, f"tokens.{name}.pt"))
        self._ids_match(name, blob, "tokens")
        if list(blob.get("token_order", [])) != ["honest", "deceptive"]:
            fail(f"tokens.{name}.pt token_order is {blob.get('token_order')}")
        return blob

    def kept_share(self, name: str) -> Optional[float]:
        report = self.plan.get("cells", {}).get(name, {}).get("report") or {}
        return report.get("kept_share")

    def provenance(self) -> dict:
        path = os.path.join(self.directory, "run_manifest.json")
        if not os.path.exists(path):
            return {"capture_manifest": None, "git_commit": None,
                    "status": f"not yet verified: {path} is missing"}
        commit = json.load(open(path)).get("git_commit")
        ok = isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
        return {"capture_manifest": path, "git_commit": commit,
                "status": "ok" if ok else f"not yet verified: git_commit {commit!r} is not 40-hex"}


# ==============================================================================
# GUARDS AND SELECTION
# ==============================================================================

def check_fit_rows(rows: Sequence[dict]) -> None:
    """Raise unless every row is a FAR train D or H row of the fit role."""
    for row in rows:
        if not (row.get("role") == "fit" and row.get("task") == "far_v2" and row.get("split") == "train"
                and row.get("condition") in ("D", "H")):
            raise ValueError(f"the fit reads FAR train D and H rows only; got {row.get('role')}, "
                             f"{row.get('task')}, {row.get('split')}, {row.get('condition')} "
                             f"({row.get('instance_id')})")


def check_selection_rows(rows: Sequence[dict]) -> None:
    """Raise on any row that is not a FAR validation D, H or HI row of the select role (no SER, SDR or FAR test)."""
    for row in rows:
        if not (row.get("role") == "select" and row.get("task") == "far_v2"
                and row.get("split") == "validation" and row.get("condition") in ("D", "H", "HI")):
            raise ValueError(f"selection reads the FAR validation select rows only; got {row.get('role')}, "
                             f"{row.get('task')}, {row.get('split')}, {row.get('condition')} "
                             f"({row.get('instance_id')})")


def selection_table(rows: Sequence[dict], scores) -> np.ndarray:
    """[R, nC] AUROC of D against the pooled H and HI rows. `scores` is [n, R, nC], row-aligned with `rows`."""
    check_selection_rows(rows)
    scores = np.asarray(scores, dtype=np.float64)
    if scores.shape[0] != len(rows):
        raise ValueError(f"{scores.shape[0]} score rows for {len(rows)} rows")
    is_d = np.array([row["condition"] == "D" for row in rows])
    if not is_d.any() or is_d.all():
        raise ValueError("selection needs D rows and H or HI rows")
    table = np.empty(scores.shape[1:], dtype=np.float64)
    for r in range(scores.shape[1]):
        for k in range(scores.shape[2]):
            table[r, k] = probe.auroc(scores[is_d, r, k], scores[~is_d, r, k])
    return table


def select_from_table(table, c_grid: Sequence[float]) -> dict:
    """Best C per row (exact ties to the smaller C), then the eligible row nearest layer 17 within 0.005."""
    table = np.asarray(table, dtype=np.float64)
    rows = [r for r in range(table.shape[0]) if eligible(r)]
    if not rows:
        raise ValueError("no eligible row")
    best_k = {r: int(np.argmax(table[r])) for r in rows}  # argmax takes the first, the smaller C
    best = {r: float(table[r, best_k[r]]) for r in rows}
    top = max(best.values())
    candidates = [r for r in rows if best[r] >= top - TIE - 1e-12]
    row = min(candidates, key=lambda r: (abs(layer_of(r) - CENTRE_LAYER), -best[r], r))
    k = best_k[row]
    return {"row": row, "layer": layer_of(row), "C": float(c_grid[k]), "C_index": k, "auroc": best[row],
            "best_auroc": top,
            "candidates": [{"row": r, "layer": layer_of(r), "auroc": best[r]} for r in candidates]}


# ==============================================================================
# FIT
# ==============================================================================

def _features(resid, row: int) -> np.ndarray:
    return resid[:, row, :].double().numpy()


def _nonfinite(resid) -> int:
    import torch

    return int((~torch.isfinite(resid)).sum())


def run_fit(capture_dir: str, out_dir: str) -> dict:
    import torch

    cap = Capture(capture_dir)
    names = {cell: cap.find(cell) for cell in ("fit_D", "fit_H", "select_D", "select_H", "select_HI")}
    fit_rows = cap.rows(names["fit_D"]) + cap.rows(names["fit_H"])
    select_rows = cap.rows(names["select_D"]) + cap.rows(names["select_H"]) + cap.rows(names["select_HI"])
    try:
        check_fit_rows(fit_rows)
        check_selection_rows(select_rows)
    except ValueError as error:
        fail(str(error))
    resid = {cell: cap.resid(name) for cell, name in names.items()}
    for cell, tensor in resid.items():
        bad = _nonfinite(tensor)
        if bad:
            fail(f"{names[cell]} has {bad} non-finite residual element(s); the fit and the selection need finite "
                 f"rows (store the capture in bfloat16 or drop the rows and refit)")
    shapes = {tuple(tensor.shape[1:]) for tensor in resid.values()}
    if len(shapes) != 1:
        fail(f"cells disagree on the residual shape: {shapes}")
    n_rows, hidden = shapes.pop()

    y = np.concatenate([np.ones(len(cap.rows(names["fit_D"]))), np.zeros(len(cap.rows(names["fit_H"])))])
    n_c = len(C_GRID)
    mean = np.zeros((n_rows, hidden))
    std = np.ones((n_rows, hidden))
    weights = np.zeros((n_rows, n_c, hidden))
    bias = np.zeros((n_rows, n_c))
    mm = np.zeros((n_rows, hidden))
    converged = np.zeros((n_rows, n_c), dtype=bool)
    grad = np.zeros((n_rows, n_c))
    sel_scores = np.zeros((len(select_rows), n_rows, n_c))
    sel_mm = np.zeros((len(select_rows), n_rows))
    for r in range(n_rows):
        X = np.concatenate([_features(resid["fit_D"], r), _features(resid["fit_H"], r)])
        mean[r], std[r] = probe.standardise_fit(X)
        Z = probe.standardise_apply(X, mean[r], std[r])
        mm[r] = probe.mass_mean(X, y)
        Xs = np.concatenate([_features(resid[cell], r) for cell in ("select_D", "select_H", "select_HI")])
        Zs = probe.standardise_apply(Xs, mean[r], std[r])
        sel_mm[:, r] = Xs @ mm[r]
        for k, C in enumerate(C_GRID):
            fitted = probe.fit_logistic(Z, y, C)
            weights[r, k], bias[r, k] = fitted["w"], fitted["b"]
            converged[r, k], grad[r, k] = fitted["converged"], fitted["grad_norm"]
            sel_scores[:, r, k] = probe.decision(Zs, fitted["w"], fitted["b"])

    table = selection_table(select_rows, sel_scores)
    is_d = np.array([row["condition"] == "D" for row in select_rows])
    select_mm = [probe.auroc(sel_mm[is_d, r], sel_mm[~is_d, r]) for r in range(n_rows)]
    selected = select_from_table(table, C_GRID)
    summary = {
        "schema": FIT_SCHEMA, "capture": cap.directory, "c_grid": list(C_GRID),
        "eligible_layers": list(ELIGIBLE_LAYERS), "centre_layer": CENTRE_LAYER, "tie": TIE,
        "n_fit": {"D": int(y.sum()), "H": int((1 - y).sum())},
        "n_select": {c: len(cap.rows(names[f"select_{c}"])) for c in ("D", "H", "HI")},
        "select_auroc": table.tolist(), "select_mass_mean_auroc": select_mm,
        "converged": converged.tolist(), "grad_norm": grad.tolist(),
        "n_not_converged": int((~converged).sum()), "selected": selected,
    }
    os.makedirs(out_dir, exist_ok=True)
    torch.save({"schema": FIT_SCHEMA, "c_grid": list(C_GRID), "n_rows": int(n_rows),
                "mean": torch.from_numpy(mean), "std": torch.from_numpy(std),
                "weights": torch.from_numpy(weights), "bias": torch.from_numpy(bias),
                "mass_mean": torch.from_numpy(mm), "selected": selected},
               os.path.join(out_dir, "p1_fit.pt"))
    _write_json(os.path.join(out_dir, "p1_fit.json"), summary)
    print(f"fit: selected row {selected['row']} (layer {selected['layer']}), C {selected['C']}, "
          f"select AUROC {selected['auroc']:.4f}; {summary['n_not_converged']} fit(s) not converged")
    return summary


# ==============================================================================
# SCORE
# ==============================================================================

def _write_json(path: str, obj) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as handle:
        json.dump(obj, handle, indent=1, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, path)


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def usable_rows(rows: Sequence[dict]) -> Tuple[np.ndarray, dict]:
    """Boolean mask of rows to use, and the drop counts (HI under the bar; SDR I-reported sample rows)."""
    keep = np.ones(len(rows), dtype=bool)
    counts = {"n_below_hi_bar": 0, "n_dropped_sample": 0}
    for i, row in enumerate(rows):
        if row.get("condition") == "HI":
            value = row.get("keep_if_value")
            if value is None or float(value) < HI_BAR:
                keep[i] = False
                counts["n_below_hi_bar"] += 1
        if row.get("condition") == "I_reported" and any(row.get(flag) for flag in SAMPLE_FLAGS):
            keep[i] = False
            counts["n_dropped_sample"] += 1
    return keep, counts


def pair_rows(rows: Sequence[dict], twin_rows: Sequence[dict]) -> dict:
    """Join a cell's usable rows to its twin's rows on `instance_id`. -> indices, clusters and counts."""
    keep, counts = usable_rows(rows)
    twin_index = {row["instance_id"]: j for j, row in enumerate(twin_rows)}
    left, right, clusters, unjoined = [], [], [], 0
    for i, row in enumerate(rows):
        if not keep[i]:
            continue
        j = twin_index.get(row["instance_id"])
        if j is None:
            unjoined += 1
            continue
        left.append(i)
        right.append(j)
        clusters.append(str(row.get("pressure_id")))
    return {"left": np.array(left, dtype=int), "right": np.array(right, dtype=int),
            "clusters": np.array(clusters, dtype=object), "n_unjoined": unjoined, **counts}


def contrast_auroc(cell_scores, twin_scores, pairing: dict, *, n_resamples: int, seed: int = SEED) -> dict:
    """AUROC of the joined cell rows against their twins, with the clustered bootstrap CI."""
    a = np.asarray(cell_scores, dtype=np.float64)[pairing["left"]]
    b = np.asarray(twin_scores, dtype=np.float64)[pairing["right"]]
    finite = np.isfinite(a) & np.isfinite(b)
    a, b, clusters = a[finite], b[finite], pairing["clusters"][finite]
    out = {"n_pairs": int(a.size), "n_unjoined": pairing["n_unjoined"],
           "n_nonfinite_dropped": int((~finite).sum()), "n_clusters": int(len(set(clusters.tolist())))}
    for key in ("n_below_hi_bar", "n_dropped_sample"):
        if pairing.get(key):
            out[key] = pairing[key]
    if a.size == 0:
        out.update({"auroc": None, "ci": None})
        return out
    out["auroc"] = probe.auroc(a, b)
    if n_resamples > 0:
        draws = probe.cluster_bootstrap(lambda idx: probe.auroc(a[idx], b[idx]), clusters,
                                        n_resamples=n_resamples, seed=seed)
        out["ci"] = list(probe.percentile_ci(draws))
    else:
        out["ci"] = None
    return out


def load_fit(out_dir: str) -> Tuple[dict, str]:
    path = os.path.join(out_dir, "p1_fit.pt")
    if not os.path.exists(path):
        fail(f"{path} does not exist; run `fit` first")
    art = _load_pt(path)
    if art.get("schema") != FIT_SCHEMA:
        fail(f"{path} has schema {art.get('schema')!r}")
    return art, path


def cell_scores(resid, art: dict) -> dict:
    """Decision values [n, R, nC] and mass-mean projections [n, R]; NaN where a row's residual is not finite."""
    n, n_rows, _ = resid.shape
    n_c = len(art["c_grid"])
    logit = np.full((n, n_rows, n_c), np.nan)
    mm = np.full((n, n_rows), np.nan)
    for r in range(n_rows):
        X = _features(resid, r)
        ok = np.isfinite(X).all(axis=1)
        Z = probe.standardise_apply(X[ok], art["mean"][r].numpy(), art["std"][r].numpy())
        for k in range(n_c):
            logit[ok, r, k] = probe.decision(Z, art["weights"][r, k].numpy(), float(art["bias"][r, k]))
        mm[ok, r] = X[ok] @ art["mass_mean"][r].numpy()
    return {"logit": logit, "mm": mm}


def _standardised_at(resid, art: dict, row: int) -> np.ndarray:
    X = _features(resid, row)
    Z = probe.standardise_apply(X, art["mean"][row].numpy(), art["std"][row].numpy())
    Z[~np.isfinite(X).all(axis=1)] = np.nan
    return Z


def permutation_null(cap: Capture, art: dict, selected: dict, ser_pair: dict, ser_Z: Tuple[np.ndarray, np.ndarray],
                     observed: float, n_permutations: int) -> dict:
    """Refit at the selected row and C with D and H labels swapped in a random half of the fit instance pairs."""
    row, C = selected["row"], selected["C"]
    out = {"n_permutations": n_permutations, "seed": SEED + 1, "row": row, "layer": layer_of(row), "C": C,
           "observed": observed}
    if n_permutations <= 0:
        out.update({"aurocs": [], "summary": probe.summarise([]), "p_one_sided": None, "p_two_sided": None,
                    "n_pairs": 0})
        return out
    d_name, h_name = cap.find("fit_D"), cap.find("fit_H")
    d_rows, h_rows = cap.rows(d_name), cap.rows(h_name)
    Zd = _standardised_at(cap.resid(d_name), art, row)
    Zh = _standardised_at(cap.resid(h_name), art, row)
    h_index = {r["instance_id"]: j for j, r in enumerate(h_rows)}
    pairs = [(i, h_index[r["instance_id"]]) for i, r in enumerate(d_rows) if r["instance_id"] in h_index]
    paired_d = {i for i, _ in pairs}
    paired_h = {j for _, j in pairs}
    loose_d = [i for i in range(len(d_rows)) if i not in paired_d]
    loose_h = [j for j in range(len(h_rows)) if j not in paired_h]
    pi = np.array([i for i, _ in pairs], dtype=int)
    pj = np.array([j for _, j in pairs], dtype=int)
    X = np.concatenate([Zd[pi], Zh[pj], Zd[loose_d], Zh[loose_h]])
    Sd, Sh = ser_Z
    a_rows, b_rows = Sd[ser_pair["left"]], Sh[ser_pair["right"]]
    finite = np.isfinite(a_rows).all(axis=1) & np.isfinite(b_rows).all(axis=1)
    a_rows, b_rows = a_rows[finite], b_rows[finite]
    swaps = probe.permutation_swaps(len(pairs), n_permutations, seed=SEED + 1)
    aurocs = []
    for p in range(n_permutations):
        s = swaps[p].astype(np.float64)
        y = np.concatenate([1.0 - s, s, np.ones(len(loose_d)), np.zeros(len(loose_h))])
        fitted = probe.fit_logistic(X, y, C)
        aurocs.append(probe.auroc(probe.decision(a_rows, fitted["w"], fitted["b"]),
                                  probe.decision(b_rows, fitted["w"], fitted["b"])))
    null = np.array(aurocs)
    out.update({"n_pairs": len(pairs), "aurocs": aurocs, "summary": probe.summarise(aurocs),
                "p_one_sided": float((1 + (null >= observed).sum()) / (n_permutations + 1)),
                "p_two_sided": float((1 + (np.abs(null - 0.5) >= abs(observed - 0.5)).sum())
                                     / (n_permutations + 1))})
    return out


def leave_one_clause_out(cap: Capture, selected: dict) -> dict:
    """Pool FAR train and validation D and H; per clause, fit on the others and score D against H on it."""
    row, C = selected["row"], selected["C"]
    X, y, clauses = [], [], []
    for cell, label in (("fit_D", 1.0), ("fit_H", 0.0), ("select_D", 1.0), ("select_H", 0.0)):
        name = cap.find(cell)
        rows = cap.rows(name)
        X.append(_features(cap.resid(name), row))
        y.extend([label] * len(rows))
        clauses.extend(str(r.get("pressure_id")) for r in rows)
    X = np.concatenate(X)
    y = np.array(y)
    clauses = np.array(clauses, dtype=object)
    finite = np.isfinite(X).all(axis=1)
    X, y, clauses = X[finite], y[finite], clauses[finite]
    by_clause, held_scores, held_labels = {}, [], []
    for clause in sorted(set(clauses.tolist())):
        test = clauses == clause
        train = ~test
        entry = {"n_D": int(y[test].sum()), "n_H": int((1 - y[test]).sum())}
        if entry["n_D"] == 0 or entry["n_H"] == 0 or len(set(y[train].tolist())) < 2:
            entry["auroc"] = None
            by_clause[clause] = entry
            continue
        mean, std = probe.standardise_fit(X[train])
        fitted = probe.fit_logistic(probe.standardise_apply(X[train], mean, std), y[train], C)
        scores = probe.decision(probe.standardise_apply(X[test], mean, std), fitted["w"], fitted["b"])
        entry["auroc"] = probe.auroc(scores[y[test] == 1], scores[y[test] == 0])
        by_clause[clause] = entry
        held_scores.append(scores)
        held_labels.append(y[test])
    pooled = None
    if held_scores:
        s, lab = np.concatenate(held_scores), np.concatenate(held_labels)
        pooled = probe.auroc(s[lab == 1], s[lab == 0])
    values = [e["auroc"] for e in by_clause.values() if e["auroc"] is not None]
    return {"row": row, "layer": layer_of(row), "C": C, "by_clause": by_clause, "pooled_auroc": pooled,
            "min_auroc": min(values) if values else None, "n_dropped_nonfinite": int((~finite).sum())}


def reading_text(fallback: bool, rule_band: str, anti: bool, label: Optional[str]) -> str:
    if fallback:
        return "per-token DLA only"
    if rule_band == "misleadingness":
        if label == "instruction-confounded":
            return "misleadingness, instruction-confounded: the per-token DLA carries the reading"
        return "misleadingness, clean"
    if rule_band == "literal_falsity":
        return "literal falsity, anti-aligned" if anti else "literal falsity"
    return "indeterminate"


def run_score(capture_dir: str, out_dir: str, *, n_resamples: int = N_RESAMPLES,
              n_permutations: int = N_PERMUTATIONS) -> dict:
    cap = Capture(capture_dir)
    art, fit_path = load_fit(out_dir)
    if not os.path.exists(os.path.join(out_dir, "p1_fit.json")):
        fail(f"{os.path.join(out_dir, 'p1_fit.json')} does not exist; run `fit` first")
    with open(os.path.join(out_dir, "p1_fit.json")) as handle:
        fit_summary = json.load(handle)
    selected = dict(art["selected"])
    row, k = int(selected["row"]), int(selected["C_index"])

    needed = ["gate_D", "gate_H", "gate_HI", "gate_F", "gate_I", "ser_D", "ser_H", "ser_HI", "ser_F", "ser_I"]
    optional = ["sdr_D", "sdr_H", "sdr_I_reported"]
    names = {cell: cap.find(cell) for cell in needed}
    names.update({cell: cap.find(cell, required=False) for cell in optional})
    names = {cell: name for cell, name in names.items() if name is not None}
    for cell, name in names.items():
        role = CELLS[cell][0]
        bad = [r for r in cap.rows(name) if r.get("role") != role]
        if bad:
            fail(f"{name} mixes roles")

    scores, nonfinite, ser_Z = {}, {}, {}
    for cell, name in names.items():
        resid = cap.resid(name)
        if resid.shape[1] != art["n_rows"]:
            fail(f"{name} has {resid.shape[1]} residual rows, the fit {art['n_rows']}")
        nonfinite[name] = _nonfinite(resid)
        scores[cell] = cell_scores(resid, art)
        if cell in ("ser_D", "ser_H"):
            ser_Z[cell] = _standardised_at(resid, art, row)
        del resid

    pairs = {}

    def pairing(cell: str, twin: str) -> dict:
        if (cell, twin) not in pairs:
            pairs[(cell, twin)] = pair_rows(cap.rows(names[cell]), cap.rows(names[twin]))
        return pairs[(cell, twin)]

    def at(cell: str, twin: str, rr: int, kk: Optional[int], resamples: int) -> dict:
        if kk is None:
            a, b = scores[cell]["mm"][:, rr], scores[twin]["mm"][:, rr]
        else:
            a, b = scores[cell]["logit"][:, rr, kk], scores[twin]["logit"][:, rr, kk]
        return contrast_auroc(a, b, pairing(cell, twin), n_resamples=resamples)

    gate = at("gate_D", "gate_H", row, k, n_resamples)
    if gate["auroc"] is None or at("ser_D", "ser_H", row, k, 0)["auroc"] is None:
        fail("the FAR gate or the SER rule cell has no joined, finite D and H pair")
    gate.update({"threshold": probe.GATE_AT, "fallback": probe.gate_fallback(gate["auroc"])})

    rule = at("ser_D", "ser_H", row, k, n_resamples)
    rule_band = probe.band(rule["auroc"])
    edges = probe.ci_band_edges_crossed(*rule["ci"]) if rule["ci"] else []
    rule.update({"band": rule_band, "anti_aligned": probe.anti_aligned(rule["auroc"]),
                 "n_resamples": n_resamples, "seed": SEED, "ci_edges_crossed": edges,
                 "ci_crosses_band_edge": bool(edges)})

    controls = {}
    for control, (cell, twin) in CONTROLS.items():
        controls[control] = {"cell": names[cell], "twin": names[twin], **at(cell, twin, row, k, n_resamples)}
    r2_values = {cell: controls[cell]["auroc"] for cell in probe.R2_CELLS}
    label = probe.r2_label(rule_band, r2_values)
    r2 = {"label": label, "r2_cells": r2_values,
          "controls_at_or_over_0_6": sorted(c for c, v in controls.items()
                                            if c != "ser_D" and v["auroc"] is not None and v["auroc"] >= 0.6),
          "f_controls_off_half": sorted(c for c in ("far_F", "ser_F")
                                        if controls[c]["auroc"] is not None
                                        and not 0.4 <= controls[c]["auroc"] <= 0.6)}

    by_layer = []
    select_table = fit_summary["select_auroc"]
    for rr in range(art["n_rows"]):
        best_k = int(np.argmax(select_table[rr]))
        ser_aucs = [at("ser_D", "ser_H", rr, kk, 0)["auroc"] for kk in range(len(C_GRID))]
        by_layer.append({
            "row": rr, "layer": layer_of(rr), "eligible": eligible(rr), "select_auroc": select_table[rr],
            "select_best_C": C_GRID[best_k],
            "gate_auroc": [at("gate_D", "gate_H", rr, kk, 0)["auroc"] for kk in range(len(C_GRID))],
            "ser_auroc": ser_aucs, "ser_auroc_at_select_best_C": ser_aucs[best_k],
            "mass_mean": {"select": fit_summary["select_mass_mean_auroc"][rr],
                          "gate": at("gate_D", "gate_H", rr, None, 0)["auroc"],
                          "ser": at("ser_D", "ser_H", rr, None, 0)["auroc"]},
        })

    null = permutation_null(cap, art, selected, pairing("ser_D", "ser_H"), (ser_Z["ser_D"], ser_Z["ser_H"]),
                            rule["auroc"], n_permutations)
    loco = leave_one_clause_out(cap, selected)

    sdr = {}
    if "sdr_D" in names and "sdr_H" in names:
        sdr["D"] = at("sdr_D", "sdr_H", row, k, n_resamples)
        if "sdr_I_reported" in names:
            sdr["I_reported"] = at("sdr_I_reported", "sdr_H", row, k, n_resamples)
            sdr["I_reported"].setdefault("n_dropped_sample", 0)

    hi_cells = [names[c] for c in ("gate_HI", "ser_HI")]
    hi_dropped = {names[c]: pairing(c, t)["n_below_hi_bar"] for c, t in (("gate_HI", "gate_H"),
                                                                      ("ser_HI", "ser_H"))}
    verdict = {"band": rule_band, "anti_aligned": rule["anti_aligned"], "r2_label": label,
               "fallback": gate["fallback"], "ci_crosses_band_edge": rule["ci_crosses_band_edge"],
               "reading": reading_text(gate["fallback"], rule_band, rule["anti_aligned"], label)}
    result = {
        "schema": SCORE_SCHEMA, "capture": cap.directory, "fit_file": fit_path, "fit_sha256": _sha256(fit_path),
        "seed": SEED, "n_resamples": n_resamples, "c_grid": list(C_GRID),
        "selected": {key: selected[key] for key in ("row", "layer", "C", "C_index", "auroc", "best_auroc")},
        "far_gate": gate, "rule": rule, "controls": controls, "r2": r2, "verdict": verdict,
        "hi_kept_share": {name: cap.kept_share(name) for name in hi_cells}, "hi_below_bar_dropped": hi_dropped,
        "by_layer": by_layer, "permutation_null": null, "loco": loco, "sdr": sdr, "nonfinite": nonfinite,
        "provenance": cap.provenance(),
    }
    os.makedirs(out_dir, exist_ok=True)
    _write_json(os.path.join(out_dir, "p1_probe.json"), result)
    with open(os.path.join(out_dir, "p1_probe.md"), "w") as handle:
        handle.write(probe_markdown(result))
    print(f"score: FAR gate {gate['auroc']:.4f}, rule (SER D vs H) {rule['auroc']:.4f} {rule['ci']}, "
          f"band {rule_band}, R2 {label}; reading: {verdict['reading']}")
    return result


def _fmt(value, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_fmt(v, digits) for v in value) + "]"
    return f"{value:.{digits}f}"


def probe_markdown(result: dict) -> str:
    sel, rule, gate = result["selected"], result["rule"], result["far_gate"]
    lines = [
        "# P1 falsity probe",
        "",
        f"Selected layer {sel['layer']} (row {sel['row']}), C {sel['C']}, select AUROC {_fmt(sel['auroc'])}. "
        f"Reading: {result['verdict']['reading']}. Provenance: {result['provenance']['status']}.",
        "",
        "| cell against its H twin | AUROC | 95% CI (clustered) | pairs |",
        "| --- | --- | --- | --- |",
        f"| FAR gate D | {_fmt(gate['auroc'])} | {_fmt(gate['ci'])} | {gate['n_pairs']} |",
    ]
    names = {"ser_D": "SER D (rule)", "far_I": "FAR I", "far_HI": "FAR HI", "ser_HI": "SER HI",
             "ser_I": "SER I", "far_F": "FAR F", "ser_F": "SER F"}
    for key, label in names.items():
        c = result["controls"][key]
        lines.append(f"| {label} | {_fmt(c['auroc'])} | {_fmt(c['ci'])} | {c['n_pairs']} |")
    for key, label in (("D", "SDR D"), ("I_reported", "SDR I-reported")):
        if key in result["sdr"]:
            c = result["sdr"][key]
            lines.append(f"| {label} (descriptive) | {_fmt(c['auroc'])} | {_fmt(c['ci'])} | {c['n_pairs']} |")
    null, loco = result["permutation_null"], result["loco"]
    lines += [
        "",
        f"Rule number {_fmt(rule['auroc'])}, band {rule['band']}"
        f"{', anti-aligned' if rule['anti_aligned'] else ''}"
        f"{', CI crosses ' + _fmt(rule['ci_edges_crossed']) if rule['ci_crosses_band_edge'] else ''}. "
        f"R2 label: {result['r2']['label']}. FAR gate fallback: {gate['fallback']}.",
        f"Permutation null ({null['n_permutations']} refits): q95 {_fmt(null['summary'].get('q95'))}, "
        f"one-sided p {_fmt(null['p_one_sided'])}. Leave-one-clause-out: pooled {_fmt(loco['pooled_auroc'])}, "
        f"min {_fmt(loco['min_auroc'])}.",
        "",
    ]
    return "\n".join(lines)


# ==============================================================================
# READ
# ==============================================================================

def token_groups() -> Dict[str, object]:
    union = sorted(set(LATE_HONEST_HEADS["far"]) | set(LATE_HONEST_HEADS["ser"]))
    return {
        "whole_model": "logits_centred", "whole_model_raw": "logits_raw",
        "whole_model_logsoftmax": "logits_logsoftmax",
        "quartet": [list(key) for key in QUARTET],
        "late_honest_own": "the task's own C6 late heads (late_honest_heads)",
        "late_honest_far_ser": [["head", layer, head] for layer, head in union],
        "mlp.30": [["mlp", 30, 0]], "mlp.31": [["mlp", 31, 0]],
    }


def _group_values(blob: dict, task: str) -> Dict[str, np.ndarray]:
    """Group name -> [n, 2] (honest, deceptive) values for one tokens file."""
    keys = [tuple(key) for key in blob["keys"]]
    index = {key: i for i, key in enumerate(keys)}
    dla = blob["dla"].double().numpy()

    def summed(members) -> np.ndarray:
        missing = [m for m in members if tuple(m) not in index]
        if missing:
            fail(f"keys {missing} are not in the tokens file")
        return dla[:, [index[tuple(m)] for m in members], :].sum(axis=1)

    groups = token_groups()
    own = [["head", layer, head] for layer, head in LATE_HONEST_HEADS[task]]
    return {
        "whole_model": blob["logits_centred"].double().numpy(),
        "whole_model_raw": blob["logits_raw"].double().numpy(),
        "whole_model_logsoftmax": blob["logits_logsoftmax"].double().numpy(),
        "quartet": summed(groups["quartet"]), "late_honest_own": summed(own),
        "late_honest_far_ser": summed(groups["late_honest_far_ser"]),
        "mlp.30": summed(groups["mlp.30"]), "mlp.31": summed(groups["mlp.31"]),
    }


def _mean_ci(values: np.ndarray, clusters: np.ndarray, n_resamples: int, seed: int) -> Tuple[dict, np.ndarray]:
    entry = {"mean": float(values.mean()) if values.size else None,
             "sd": float(values.std()) if values.size else None, "ci": None}
    draws = np.array([])
    if values.size and n_resamples > 0:
        draws = probe.cluster_bootstrap(lambda idx: float(values[idx].mean()), clusters,
                                        n_resamples=n_resamples, seed=seed)
        entry["ci"] = list(probe.percentile_ci(draws))
    return entry, draws


def read_task(cap: Capture, cell: str, twin: str, task: str, n_resamples: int, seeds: Sequence[int]) -> dict:
    """D minus H per group and column for one (cell, twin). Returns the entry and the bootstrap draws per seed."""
    name, twin_name = cap.find(cell), cap.find(twin)
    pairing = pair_rows(cap.rows(name), cap.rows(twin_name))
    blob, twin_blob = cap.tokens(name), cap.tokens(twin_name)
    left, right, clusters = pairing["left"], pairing["right"], pairing["clusters"]
    same = (blob["token_ids"][left] == twin_blob["token_ids"][right]).all(dim=1).numpy() if left.size else \
        np.zeros(0, dtype=bool)
    left, right, clusters = left[same], right[same], clusters[same]
    error = max(float((b["dla"].double().sum(1) - b["logits_centred"].double()).abs().max())
                if b["dla"].shape[0] else 0.0 for b in (blob, twin_blob))
    values, twin_values = _group_values(blob, task), _group_values(twin_blob, task)
    entry = {"cells": [name, twin_name], "n_pairs": int(left.size), "n_unjoined": pairing["n_unjoined"],
             "n_token_mismatch": int((~same).sum()), "n_dropped_sample": pairing["n_dropped_sample"],
             "n_clusters": int(len(set(clusters.tolist()))), "dla_sum_max_abs_error": error, "groups": {}}
    draws: Dict[int, Dict[str, Dict[str, np.ndarray]]] = {seed: {} for seed in seeds}
    for group in values:
        diff = values[group][left] - twin_values[group][right]
        entry["groups"][group] = {}
        for column, label in ((0, "suppression"), (1, "promotion")):
            for s_i, seed in enumerate(seeds):
                one, d = _mean_ci(diff[:, column], clusters, n_resamples, seed)
                if s_i == 0:
                    entry["groups"][group][label] = one
                draws[seed].setdefault(group, {})[label] = d
    return entry, draws


def run_read(capture_dir: str, out_dir: str, *, n_resamples: int = N_RESAMPLES) -> dict:
    cap = Capture(capture_dir)
    tasks: Dict[str, dict] = {}
    far, far_draws = read_task(cap, "gate_D", "gate_H", "far", n_resamples, [SEED])
    ser, ser_draws = read_task(cap, "ser_D", "ser_H", "ser", n_resamples, [SEED, SEED + 1])
    tasks["far"], tasks["ser"] = far, ser
    if cap.find("sdr_D", required=False) and cap.find("sdr_H", required=False):
        tasks["sdr"], _ = read_task(cap, "sdr_D", "sdr_H", "sdr", n_resamples, [SEED])
        if cap.find("sdr_I_reported", required=False):
            tasks["sdr_I_reported"], _ = read_task(cap, "sdr_I_reported", "sdr_H", "sdr", n_resamples, [SEED])

    far_minus_ser = {}
    for group in far["groups"]:
        far_minus_ser[group] = {}
        for label in ("suppression", "promotion"):
            fm, sm = far["groups"][group][label]["mean"], ser["groups"][group][label]["mean"]
            entry = {"mean": None if fm is None or sm is None else fm - sm, "ci": None}
            a, b = far_draws[SEED][group][label], ser_draws[SEED + 1][group][label]
            if a.size and b.size:
                entry["ci"] = list(probe.percentile_ci(a - b))
            far_minus_ser[group][label] = entry

    result = {
        "schema": TOKENS_SCHEMA, "capture": cap.directory, "seed": SEED, "n_resamples": n_resamples,
        "sign": ("D minus H per joined pair. suppression: column 0, the honest item; negative means D lowers it. "
                 "promotion: column 1, the deceptive item; positive means D raises it. Centred logits and "
                 "centred DLA; whole_model_raw and whole_model_logsoftmax use the other two logit forms."),
        "groups": token_groups(), "late_honest_heads": {t: [list(h) for h in v] for t, v in LATE_HONEST_HEADS.items()},
        "tasks": tasks, "far_minus_ser": far_minus_ser, "provenance": cap.provenance(),
    }
    os.makedirs(out_dir, exist_ok=True)
    _write_json(os.path.join(out_dir, "p1_tokens.json"), result)
    with open(os.path.join(out_dir, "p1_tokens.md"), "w") as handle:
        handle.write(tokens_markdown(result))
    q = far_minus_ser["quartet"]
    print(f"read: FAR {far['n_pairs']} pairs, SER {ser['n_pairs']} pairs; quartet FAR - SER promotion "
          f"{_fmt(q['promotion']['mean'])} {_fmt(q['promotion']['ci'])}")
    return result


def tokens_markdown(result: dict) -> str:
    far, ser = result["tasks"]["far"]["groups"], result["tasks"]["ser"]["groups"]
    diff = result["far_minus_ser"]
    lines = [
        "# P1 per-token readout (D minus H)",
        "",
        "Suppression is the honest item (negative: D lowers it). Promotion is the deceptive item (positive: D "
        f"raises it). 95% CIs resample pressure_id clusters. Provenance: {result['provenance']['status']}.",
        "",
        "| group | FAR suppression | FAR promotion | SER suppression | SER promotion | FAR - SER suppression "
        "| FAR - SER promotion |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for group in far:
        cells = []
        for source in (far, ser, diff):
            for label in ("suppression", "promotion"):
                one = source[group][label]
                cells.append(f"{_fmt(one['mean'])} {_fmt(one['ci'])}")
        lines.append(f"| {group} | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


# ==============================================================================
# CLI
# ==============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="B2 P1 falsity probe: fit, score, read (CPU).")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("fit", "score", "read"):
        one = sub.add_parser(command)
        one.add_argument("--capture", required=True, help="T6 capture directory")
        one.add_argument("--out", default=DEFAULT_OUT, help="results directory")
        if command in ("score", "read"):
            one.add_argument("--n-resamples", type=int, default=N_RESAMPLES)
        if command == "score":
            one.add_argument("--n-permutations", type=int, default=N_PERMUTATIONS)
    args = parser.parse_args(argv)
    import torch

    # A 128-core login node oversubscribes torch's default thread pool: one LBFGS fit on 400 x 4096 took 4.7 s
    # with the default threads and 0.05 s with one (2026-11-01). FALSITY_PROBE_THREADS overrides.
    torch.set_num_threads(int(os.environ.get("FALSITY_PROBE_THREADS", "1")))
    if args.command == "fit":
        run_fit(args.capture, args.out)
    elif args.command == "score":
        run_score(args.capture, args.out, n_resamples=args.n_resamples, n_permutations=args.n_permutations)
    else:
        run_read(args.capture, args.out, n_resamples=args.n_resamples)
    return 0


if __name__ == "__main__":
    sys.exit(main())
