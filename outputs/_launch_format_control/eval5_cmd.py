#!/usr/bin/env python3
"""
eval5_cmd.py — EVAL 5 for the format-control suites (ticket 06): the command
generator, the worktree-local screen cache, the pre-flight gate, the refusals
and the record. NOTHING HERE SUBMITS A JOB; `submit_eval5.sh` is the only
caller that can, and only after every refusal below has been cleared.

One benchmark suite per task family and benchmark group binds the deceptive
circuit D, its Honest Twin H and the Format Circuit F in ONE
`evaluate_circuit.py` invocation, so the three knockouts run on the identical
screened items, against one judge cache, under identical settings. The random
rows stay size-matched per circuit.

    family      suite in suites.json                 circuits bound
    far         format-control-far-nls0.3            D, H, F
    sdr         format-control-sdr-nls0.3            D, H, F
    sdr_coarse  format-control-sdr-coarse-nls0.3     D, H, F, m; knockouts
                                                     X_hko = X - m (heads only)

    group  benchmarks                                                    output
    sm     sandbagging mask                                              outputs/eval5_format_<family>
    lb     lb:instructed-deception lb:harm-pressure-knowledge-report     outputs/eval5_format_<family>_lb
           lb:convincing-game

Settings are those of `outputs/_eval5_launch/eval5_args.sh` in the main
checkout (interchange, 50 items per dataset, 6 random circuits, screen budget
600). Added, none changing a number:

  --task-from <D run>
      Mandatory: with no task flag the evaluator defaults to every bound
      circuit's own test set, and D, H, F have three conditions, so it would
      run a 3 x 3 grid of benchmark cells instead of 3.
  --benchmark-screen-cache <worktree>/outputs/_eval5_format_cache/screens
      A worktree-local COPY of the main checkout's A40 screens (`seed-cache`
      copies files, never links). The existing eval5_* suites were judged on
      those screens, so a hit keeps the items identical; a miss writes under
      the worktree, never into the main checkout. The cache key includes the
      GPU, so the copy holds A40 screens only and the launcher refuses, after
      the dry-run, any suite whose screens are not all `[cached]`, any non-A40
      screen in the copy and any non-A40 partition, unless
      `--allow-rescreen "<reason>"` is given and recorded.
  --benchmark-repo-root /projects/beto/swong2/Alignment
      The MASK and Liars' Bench checkouts beside the main checkout (read-only);
      the default resolves them inside .claude/worktrees. Not in the cache key.

The pre-flight gate (spec: "eval 2 gate (wikitext KL <= 0.66) before eval 5")
reads the wikitext KL of the Format Circuit's knockout from ticket 04's suite:
the knockout cell of F on the D test set and on its own test set, found through
`suite_manifest.json`'s per-suite `cells` index. It refuses a missing cell, a
missing KL, a KL > 0.66 (naming the number), and a cell that was not produced
by the F that suites.json configures now (the manifest's planned F and the
cell's own `summary.json` operand must both equal it). Only the KL bar can be
overridden, by the researcher, with `--gate-override "<reason>"`, recorded.

Every dry run and submission is appended to `eval5_record.json` (arguments,
cost, gate KLs, overrides with their reasons, job id).

CLI (run from the worktree root):

    python outputs/_launch_format_control/eval5_cmd.py args        <family> <sm|lb> [--standin]
    python outputs/_launch_format_control/eval5_cmd.py check       <family> <sm|lb> [--dry] [--standin] [--gate-override R]
    python outputs/_launch_format_control/eval5_cmd.py gate        <family> [--gate-override R]
    python outputs/_launch_format_control/eval5_cmd.py seed-cache  <sm|lb>
    python outputs/_launch_format_control/eval5_cmd.py cache-check <dry-run log> <sm|lb> [--partition P] [--allow-rescreen R]
    python outputs/_launch_format_control/eval5_cmd.py sbatch      <family> <sm|lb> --log L --account A
    python outputs/_launch_format_control/eval5_cmd.py cost        <dry-run log> [--family F --group G]
    python outputs/_launch_format_control/eval5_cmd.py record      <family> <sm|lb> --event dry|submit --log L
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
#: The worktree root (this file is <root>/outputs/_launch_format_control/).
WORKTREE = os.path.dirname(os.path.dirname(HERE))

#: The main checkout, which holds D, H and the source screens. Read-only from
#: here: the only paths under its outputs/ that a command may name are circuit
#: run directories.
MAIN_CHECKOUT = "/projects/beto/swong2/Alignment/Deception-Circuit"
SCREEN_CACHE_SRC = MAIN_CHECKOUT + "/outputs/_screens"
BENCHMARK_REPO_ROOT = "/projects/beto/swong2/Alignment"

#: The worktree-local copy the evaluator reads and (on a miss) writes.
LOCAL_CACHE_ROOT = os.path.join(WORKTREE, "outputs", "_eval5_format_cache")
LOCAL_SCREEN_CACHE = os.path.join(LOCAL_CACHE_ROOT, "screens")

#: family -> ticket 04 suite name (its key in suites.json / suite_manifest.json)
FAMILIES = {
    "far": "format-control-far-nls0.3",
    "sdr": "format-control-sdr-nls0.3",
    "sdr_coarse": "format-control-sdr-coarse-nls0.3",
}
COARSE = ("sdr_coarse",)

GROUPS = {
    "sm": ("sandbagging", "mask"),
    "lb": ("lb:instructed-deception", "lb:harm-pressure-knowledge-report",
           "lb:convincing-game"),
}
#: What `--benchmarks <group>` expands to (checked against the dry-run logs).
GROUP_DATASETS = {
    "sm": ("sandbagging", "mask:continuations", "mask:disinformation",
           "mask:doubling_down_known_facts", "mask:known_facts", "mask:provided_facts",
           "mask:statistics"),
    "lb": GROUPS["lb"],
}
GROUP_SUFFIX = {"sm": "", "lb": "_lb"}

ROLES = ("D", "H", "F")
ALLMLP = "m"
HKO = "_hko"

#: outputs/_eval5_launch/eval5_args.sh, verbatim.
SETTINGS = ("--evals", "benchmarks", "--ablation", "interchange")
SIZES = ("--benchmark-n-per-dataset", "50", "--benchmark-n-random", "6",
         "--benchmark-screen-budget", "600")

#: The spec's eval 2 bar for the Format Circuit knockout.
KL_GATE = 0.66

#: The environment variable the researcher sets to give the go-ahead.
GO_ENV = "FORMAT_CONTROL_EVAL5_GO"

#: The GPU that made the cached screens, and the partitions that have it.
#: Other partitions re-screen, and the items stop matching the existing suites.
A40_DEVICE = "NVIDIA A40"
A40_PARTITIONS = ("gpuA40x4",)
DEFAULT_PARTITION = "gpuA40x4"

CONFIG_PATH = os.path.join(HERE, "suites.json")
MANIFEST_PATH = os.path.join(HERE, "suite_manifest.json")
RECORD_PATH = os.path.join(HERE, "eval5_record.json")


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _reason(text, name):
    if text is not None and not str(text).strip():
        raise ValueError(f"{name} needs a reason (who decided and why)")
    return None if text is None else str(text).strip()


def _same_path(a, b) -> bool:
    if not a or not b:
        return False
    norm = lambda p: os.path.normpath(os.path.abspath(p))       # noqa: E731
    return norm(a) == norm(b) or os.path.realpath(a) == os.path.realpath(b)


# ==============================================================================
# THE COMMAND GENERATOR (pure)
# ==============================================================================

def _check_family_group(family: str, group: str) -> None:
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r} (expected one of {', '.join(FAMILIES)})")
    if group not in GROUPS:
        raise ValueError(f"unknown group {group!r} (expected one of {', '.join(GROUPS)})")


def output_dir(family: str, group: str) -> str:
    _check_family_group(family, group)
    return f"outputs/eval5_format_{family}{GROUP_SUFFIX[group]}"


def cell_labels(family: str) -> dict:
    """{role: the cell's circuit label} as the evaluator files it."""
    if family in COARSE:
        return {r: f"{r}{HKO}__leaf" for r in ROLES}
    return {r: r for r in ROLES}


def eval5_args(family: str, group: str, runs: dict, allmlp: str = None,
               screen_cache: str = LOCAL_SCREEN_CACHE) -> list:
    """The exact `evaluate_circuit.py` arguments of one EVAL 5 suite."""
    _check_family_group(family, group)
    for role in ROLES:
        if not runs.get(role):
            raise ValueError(f"the {role} run directory is not configured "
                             f"(suites.json {FAMILIES[family]} runs.{role} is null)")
    args = []
    for role in ROLES:
        args += ["--circuit", f"{role}={runs[role]}"]
    if family in COARSE:
        if not allmlp:
            raise ValueError("the coarse family needs the all-MLP operand "
                             "(suites.json allmlp) for its heads-only knockouts")
        args += ["--circuit", f"{ALLMLP}={allmlp}"]
        for role in ROLES:
            args += ["--expr", f"{role}{HKO}={role} - {ALLMLP}"]
        args += ["--compose-granularity", "leaf"]
    args += ["--task-from", runs["D"], *SETTINGS, "--benchmarks", *GROUPS[group], *SIZES,
             "--benchmark-screen-cache", screen_cache,
             "--benchmark-repo-root", BENCHMARK_REPO_ROOT,
             "--output-dir", output_dir(family, group)]
    return args


# ==============================================================================
# THE WORKTREE-LOCAL SCREEN CACHE
# ==============================================================================

def _cache_dirname(dataset: str) -> str:
    """`evaluation/screen_cache.cache_dir_for`'s directory name."""
    return dataset.replace(":", "__").replace("/", "__")


def seed_screen_cache(datasets, src: str = SCREEN_CACHE_SRC,
                      dst: str = LOCAL_SCREEN_CACHE) -> dict:
    """Copy the A40 screens of `datasets` from `src` into `dst`.

    Real file copies (a symlinked source is followed), never links; an entry
    already in `dst` is never overwritten. Only screens whose key says
    NVIDIA A40 are copied, so a `[cached]` dry-run line on the copy means an
    A40 screen matched. -> {"copied": [...], "kept": [...], "skipped": [...]}.
    """
    out = {"copied": [], "kept": [], "skipped": []}
    root = os.path.dirname(os.path.normpath(dst))
    os.makedirs(dst, exist_ok=True)
    ignore = os.path.join(root, ".gitignore")
    if os.path.basename(root) == "_eval5_format_cache" and not os.path.exists(ignore):
        with open(ignore, "w") as f:
            f.write("# worktree-local copy of the A40 screen cache: never committed\n*\n")
    for dataset in datasets:
        name = _cache_dirname(dataset)
        sdir, ddir = os.path.join(src, name), os.path.join(dst, name)
        for sidecar in sorted(glob.glob(os.path.join(sdir, "*.json"))):
            stem = os.path.splitext(os.path.basename(sidecar))[0]
            tag = f"{name}/{stem}"
            pt = os.path.join(sdir, stem + ".pt")
            try:
                device = load_json(sidecar).get("device")
            except (OSError, ValueError):
                device = None
            if device != A40_DEVICE or not os.path.isfile(pt):
                out["skipped"].append(tag)
                continue
            dpt, djs = os.path.join(ddir, stem + ".pt"), os.path.join(ddir, stem + ".json")
            if os.path.exists(dpt) or os.path.exists(djs):
                out["kept"].append(tag)
                continue
            os.makedirs(ddir, exist_ok=True)
            # temp file + rename, the sidecar last: a concurrent launcher never
            # sees a sidecar whose pickle is half written
            for s, d in ((pt, dpt), (sidecar, djs)):
                tmp = f"{d}.{os.getpid()}.tmp"
                shutil.copyfile(s, tmp)
                os.replace(tmp, d)
            out["copied"].append(tag)
    return out


def cache_check(parsed: dict, group: str, *, cache_dir: str = LOCAL_SCREEN_CACHE,
                partition: str = DEFAULT_PARTITION, allow_rescreen: str = None) -> dict:
    """After the dry-run: is every screen of the group an A40 cache hit?

    Refuses (reasons) when a dataset is not `[cached]` in the dry-run log, when
    the copy holds a non-A40 screen for the group, or when the partition is not
    an A40 one. `allow_rescreen` (a reason) clears the refusal; the reasons are
    still returned so they are printed and recorded.
    """
    allowed = _reason(allow_rescreen, "--allow-rescreen")
    reasons = []
    cached = set(parsed.get("cached") or ())
    for dataset in GROUP_DATASETS[group]:
        if dataset not in cached:
            reasons.append(f"{dataset}: no cached screen matched in {cache_dir}; the job would "
                           f"re-screen it and its items would not match the existing eval5_* suites")
    for dataset in GROUP_DATASETS[group]:
        for sidecar in sorted(glob.glob(os.path.join(cache_dir, _cache_dirname(dataset), "*.json"))):
            try:
                device = load_json(sidecar).get("device")
            except (OSError, ValueError):
                device = "unreadable"
            if device != A40_DEVICE:
                reasons.append(f"{sidecar}: a {device} screen in the local copy (only {A40_DEVICE} "
                               f"screens keep the items comparable)")
    if partition not in A40_PARTITIONS:
        reasons.append(f"partition {partition} is not an A40 partition ({', '.join(A40_PARTITIONS)}): "
                       f"the cached screens are A40, so every screen would be repaid")
    return {"passed": not reasons or allowed is not None, "reasons": reasons, "allowed": allowed}


# ==============================================================================
# THE PRE-FLIGHT GATE
# ==============================================================================

#: The F knockout cells the gate reads: F on the D test set and on its own.
GATE_CONDITIONS = ("deceptive", "nopressure")


def _role_of_circuit(label: str):
    """'F' for the atomic cell `F` and for the coarse heads-only `F_hko__leaf`."""
    base = re.sub(r"__(leaf|head)$", "", str(label))
    base = re.sub(HKO + "$", "", base)
    return base if base in ROLES else None


def f_knockout_cells(manifest_suite: dict) -> dict:
    """{condition: cell} for F's knockout cells on the D and F test sets."""
    out = {}
    for cell in manifest_suite.get("cells") or ():
        if ("knockout" in (cell.get("roles") or ())
                and _role_of_circuit(cell.get("circuit")) == "F"
                and cell.get("condition") in GATE_CONDITIONS):
            out[cell["condition"]] = cell
    return out


def read_wikitext_kl(knockout: dict):
    """The knockout's wikitext KL per token, where eval 2 writes it."""
    head = (knockout.get("headline") or {}).get("wikitext_kl")
    if head is not None:
        return float(head)
    disc = ((knockout.get("wikitext") or {}).get("discovered") or {}).get("kl_per_token")
    return None if disc is None else float(disc)


def _cell_f_run(cell_dir: str):
    """The F run directory a cell was produced from (its summary.json operand)."""
    spec = load_json(os.path.join(cell_dir, "summary.json")).get("circuit_spec") or {}
    return (spec.get("operands") or {}).get("F")


def gate(suite_root: str, manifest_suite: dict, *, f_run: str, threshold: float = KL_GATE,
         override: str = None) -> dict:
    """Read each F knockout's wikitext KL from ticket 04's suite.

    -> {"passed", "reasons", "kl": {cell path: KL}, "overridden": [...]}.
    Passing means: the manifest planned the suite with the configured F, both
    cells exist, both were produced by that F, and both KLs are <= threshold.
    `override` (the researcher's reason, e.g. fluent generations) moves only
    the KL-bar failures to "overridden"; nothing else is overridable.
    """
    override = _reason(override, "--gate-override")
    reasons, overridden, kls = [], [], {}
    planned = (manifest_suite.get("runs") or {}).get("F")
    if not planned:
        reasons.append("suite_manifest.json records no F run for this suite (ticket 04's suite "
                       "was planned before F was configured: re-plan and re-run it)")
    elif not _same_path(planned, f_run):
        reasons.append(f"suite_manifest.json planned this suite with F = {planned}, but suites.json "
                       f"now names F = {f_run}: its cells are not this F's (re-plan and re-run "
                       f"ticket 04's suite)")
    cells = f_knockout_cells(manifest_suite)
    for cond in GATE_CONDITIONS:
        cell = cells.get(cond)
        if cell is None:
            reasons.append(f"no F knockout cell on the {cond} test set in the suite manifest")
            continue
        path = cell["path"]
        cell_dir = os.path.join(suite_root, path)
        if not os.path.isfile(os.path.join(cell_dir, "knockout.json")):
            reasons.append(f"F knockout cell missing: {path}/knockout.json not found under "
                           f"{suite_root} (has ticket 04's suite run and been merged?)")
            continue
        try:
            kl = read_wikitext_kl(load_json(os.path.join(cell_dir, "knockout.json")))
        except Exception as error:                                  # noqa: BLE001
            reasons.append(f"F knockout cell {path}: unreadable knockout.json "
                           f"({type(error).__name__}: {error})")
            continue
        if kl is None:
            reasons.append(f"F knockout cell {path}: no wikitext KL in knockout.json "
                           f"(was eval 2 run with --skip-wikitext?)")
            continue
        try:
            cell_f = _cell_f_run(cell_dir)
        except Exception as error:                                  # noqa: BLE001
            cell_f, why = None, f"{type(error).__name__}: {error}"
        else:
            why = "summary.json circuit_spec.operands has no F"
        if not cell_f:
            reasons.append(f"F knockout cell {path}: cannot verify which F produced it ({why})")
            continue
        if not _same_path(cell_f, f_run):
            reasons.append(f"F knockout cell {path} was produced by F = {cell_f}, not the configured "
                           f"F = {f_run} (a stale cell: re-run ticket 04's suite)")
            continue
        kls[path] = kl
        if not kl <= threshold:
            msg = (f"F knockout wikitext KL {kl:.3f} > {threshold:.2f} in {path} ({cond} test set): "
                   f"fails the eval 2 gate. The spec's alternative, fluent generations, is the "
                   f"researcher's call: read `generation.examples` in that knockout.json")
            (overridden if override else reasons).append(msg)
    return {"passed": not reasons, "reasons": reasons, "kl": kls, "overridden": overridden,
            "override": override}


# ==============================================================================
# CONFIGURATION, REFUSALS, THE SBATCH LINE
# ==============================================================================

def family_runs(config: dict, family: str, standin: bool = False) -> dict:
    """D, H, F and the coarse all-MLP operand of a family, from suites.json.

    With `standin`, a null F is replaced by H (ticket 04's `standin_config`
    default): plumbing only, never submitted. A stand-in with F configured is
    refused, so a log labelled stand-in never carries the real F.
    """
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r} (expected one of {', '.join(FAMILIES)})")
    cfg = config[FAMILIES[family]]
    runs = {r: (cfg.get("runs") or {}).get(r) for r in ROLES}
    if standin:
        if runs["F"]:
            raise ValueError(f"a stand-in (F := H) is only for a null F; suites.json already names "
                             f"F = {runs['F']}: drop --standin")
        runs["F"] = runs["H"]
    return {"suite": FAMILIES[family], "runs": runs, "allmlp": cfg.get("allmlp"),
            "standin": bool(standin)}


def default_suite_root(family: str) -> str:
    return os.path.join(WORKTREE, "outputs", "_suites", FAMILIES[family])


def _mask_signature(run: str) -> str:
    masks = load_json(os.path.join(run, "active_nodes.json")).get("masks") or {}
    return "mb" if "mlp_blocks" in masks else "nomb"


def coarse_signature_reasons(runs: dict, allmlp: str) -> list:
    """The heads-only operand must match each coarse run's mask signature (as
    llama-8b-instruct_sdr_coarse/_launch/submit_eval5.sh derives it)."""
    m = re.search(r"_allmlp_(mb|nomb)$", os.path.basename(os.path.normpath(allmlp or "")))
    if not m:
        return [f"cannot tell the all-MLP operand's signature from its name: {allmlp}"]
    want, out = m.group(1), []
    for role in ROLES:
        try:
            sig = _mask_signature(runs[role])
        except Exception as error:                                  # noqa: BLE001
            out.append(f"cannot read {runs[role]}/active_nodes.json to check its mask signature "
                       f"({type(error).__name__}: {error})")
            continue
        if sig != want:
            has = "has an" if sig == "mb" else "has no"
            out.append(f"{role} run {runs[role]} {has} mlp_blocks gate (signature {sig}) but the "
                       f"all-MLP operand is {allmlp} ({want})")
    return out


def refusals(family: str, group: str, *, config: dict, manifest: dict, env: dict,
             suite_root: str = None, dry: bool = False, standin: bool = False,
             gate_override: str = None) -> list:
    """Every reason, known before the dry-run, not to print (dry) or not to run
    (submit) the sbatch line. Empty list = cleared. A dry run needs no
    go-ahead but still obeys the F and gate refusals. (The screen-cache
    refusals need the dry-run log: `cache_check`.)"""
    _check_family_group(family, group)
    out = []
    if standin:
        out.append("a stand-in suite (F := H) is plumbing only and is never submitted")
    fam = family_runs(config, family)
    if not fam["runs"]["F"]:
        out.append(f"the F run directory is not configured (suites.json {fam['suite']} "
                   f"runs.F is null: the Format Circuit has not landed)")
    else:
        root = suite_root or default_suite_root(family)
        g = gate(root, (manifest.get("suites") or {}).get(fam["suite"]) or {},
                 f_run=fam["runs"]["F"], override=gate_override)
        out += g["reasons"]
        if family in COARSE:
            out += coarse_signature_reasons(fam["runs"], fam["allmlp"])
    if not dry and env.get(GO_ENV) != "1":
        out.append(f"no go-ahead: EVAL 5 is launched only on the researcher's explicit "
                   f"go-ahead; set {GO_ENV}=1 in the session that submits")
    return out


def sbatch_cmd(family: str, group: str, args: list, *, account: str, ceiling_min,
               time_: str = None, partition: str = DEFAULT_PARTITION) -> list:
    """The sbatch argv. --time is the dry-run ceiling x 1.5 in quarter hours
    (ticket 04's rule) unless given."""
    if time_ is None:
        if ceiling_min is None:
            raise ValueError("no --time and no dry-run ceiling to size it from")
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        from fc_cells import walltime
        time_ = walltime(ceiling_min)
    return ["sbatch", f"--account={account}", f"--partition={partition}",
            f"--time={time_}", f"--job-name=e5fc-{family}-{group}",
            "scripts/evaluate_circuit.sbatch", *args]


# ==============================================================================
# THE COST ESTIMATE
# ==============================================================================

_TOTAL_RE = re.compile(r"^\s*TOTAL\s+([0-9.]+)(?:\s*-\s*([0-9.]+))?\s+min", re.M)
_DATASET_HEADER_RE = re.compile(r"^\s*dataset\s+condition\s+tokens\s+pool\s+judge\s*$")
_DATASET_ROW_RE = re.compile(r"^\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(.+?)\s*$")
_CACHED_RE = re.compile(r"eval 5 (\S+): screen \([^)]*\) \[cached\]")
_CELL_RE = re.compile(r"^\s+(\S*/cells/\S+)\s*$")


def parse_dryrun(text: str) -> dict:
    """What an `evaluate_circuit.py --dry-run` log says about an EVAL 5 suite."""
    passed = "Traceback" not in text and "Nothing was written" in text
    totals = _TOTAL_RE.findall(text)
    floor = ceiling = None
    if totals:
        lo, hi = totals[-1]
        floor, ceiling = float(lo), float(hi or lo)
    datasets, in_table = [], False
    for line in text.splitlines():
        if _DATASET_HEADER_RE.match(line):
            in_table = True
            continue
        if in_table:
            if not line.strip():
                if datasets:
                    break
                continue
            if set(line.strip()) <= {"-"}:
                continue
            m = _DATASET_ROW_RE.match(line)
            if m:
                judge = m.group(5)
                datasets.append({"name": m.group(1), "tokens": int(m.group(3)),
                                 "pool": int(m.group(4)), "judge": judge,
                                 "judged": "no API call" not in judge})
    cached = []
    for name in _CACHED_RE.findall(text):
        if name not in cached:
            cached.append(name)
    cells = [m.group(1) for m in map(_CELL_RE.match, text.splitlines()) if m]
    return {"passed": passed, "floor_min": floor, "ceiling_min": ceiling,
            "cells": cells, "datasets": datasets, "cached": cached}


def known_item_counts(suite_dir: str) -> dict:
    """{dataset: n_items} from an existing EVAL 5 suite on the same screens."""
    out = {}
    for path in sorted(glob.glob(os.path.join(suite_dir, "cells", "*", "*", "*",
                                              "benchmarks.json"))):
        for name, entry in (load_json(path).get("datasets") or {}).items():
            if isinstance(entry, dict) and entry.get("n_items") is not None:
                out.setdefault(name, int(entry["n_items"]))
    return out


def cost_estimate(parsed: dict, *, n_per_dataset: int = 50, n_random: int = 6,
                  screen_budget: int = 600, known_n: dict = None) -> dict:
    """Judge calls and GPU hours of one suite.

    Ablated judge calls: per cell and judged dataset, (knockout, circuit_only,
    empty, n_random randoms) x items; `full` reuses the screen's labels. An
    upper bound: the judge cache dedups identical (item, response) pairs, and
    `empty` is the same configuration in every cell. Items are the known
    post-screen counts when given, else min(n, pool). Screen judge calls are
    counted only for datasets whose screen is not cached (belief probes extra).
    GPU hours are the dry-run's floor and ceiling on one GPU.
    """
    known_n = known_n or {}
    n_cells = max(1, len(parsed.get("cells") or ()))
    configs = 3 + n_random
    per_dataset, ablated, screen = {}, 0, 0
    for d in parsed.get("datasets") or ():
        if not d["judged"]:
            per_dataset[d["name"]] = 0
            continue
        items = known_n.get(d["name"], min(n_per_dataset, d["pool"]))
        calls = n_cells * configs * items
        per_dataset[d["name"]] = calls
        ablated += calls
        if d["name"] not in (parsed.get("cached") or ()):
            screen += min(screen_budget, d["pool"])
    fl, ce = parsed.get("floor_min"), parsed.get("ceiling_min")
    hours = (None if fl is None else round(fl / 60, 1), None if ce is None else round(ce / 60, 1))
    return {"cells": n_cells, "configs_judged_per_cell": configs,
            "judge_calls_ablated": ablated, "judge_calls_per_dataset": per_dataset,
            "judge_calls_screen_max": screen, "gpu_hours": hours,
            "items_from": "known post-screen counts" if known_n else "min(n, pool)"}


#: The existing one-circuit suites on the same screens: their post-screen item
#: counts anchor the judge-call estimate (the dry-run only knows pool sizes).
ANCHOR_SUITES = {
    ("far", "sm"): "eval5_far", ("far", "lb"): "eval5_far_lb",
    ("sdr", "sm"): "eval5_sdr", ("sdr", "lb"): "eval5_sdr_lb",
    ("sdr_coarse", "sm"): "eval5_sdr_coarse_nls0.3_nomb",
    ("sdr_coarse", "lb"): "eval5_sdr_coarse_nls0.3_nomb_lb",
}


def suite_cost(log_path: str, family: str = None, group: str = None, anchor: str = None):
    """(cost, parsed, anchor used) for a dry-run log."""
    with open(log_path, errors="replace") as f:
        parsed = parse_dryrun(f.read())
    if anchor is None and (family, group) in ANCHOR_SUITES:
        anchor = os.path.join(MAIN_CHECKOUT, "outputs", ANCHOR_SUITES[(family, group)])
    known = known_item_counts(anchor) if anchor and os.path.isdir(anchor) else None
    return cost_estimate(parsed, known_n=known), parsed, (anchor if known else None)


def render_cost(cost: dict, parsed: dict) -> str:
    lo, hi = cost["gpu_hours"]
    lines = [f"  cost: {cost['cells']} cell(s); judge calls (ablated configs, upper bound, "
             f"items from {cost['items_from']}): {cost['judge_calls_ablated']:,}",
             f"        judge calls for uncached screens (at most): {cost['judge_calls_screen_max']:,}"
             f"  (cached screens: {len(parsed['cached'])} of {len(parsed['datasets'])})",
             f"        GPU hours (dry-run estimate, 1 GPU, very rough): {lo} - {hi}"]
    for name, n in cost["judge_calls_per_dataset"].items():
        lines.append(f"          {name:<34} {n:>6,}")
    return "\n".join(lines)


# ==============================================================================
# THE RECORD
# ==============================================================================

def record_event(path: str, family: str, group: str, entry: dict) -> dict:
    """Append one event to the EVAL 5 record, keyed by the suite's output dir."""
    try:
        data = load_json(path)
    except (OSError, ValueError):
        data = {"schema": "eval5_record/1", "suites": {}}
    key = os.path.basename(output_dir(family, group))
    event = dict(entry, time=time.strftime("%Y-%m-%dT%H:%M:%S"), family=family, group=group)
    data.setdefault("suites", {}).setdefault(key, {"events": []})["events"].append(event)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)
    return event


# ==============================================================================
# CLI
# ==============================================================================

def _positionals(p, *names):
    for name in names:
        p.add_argument(name)


def _common(p, *, paths=True):
    p.add_argument("--config", default=CONFIG_PATH)
    p.add_argument("--standin", action="store_true")
    p.add_argument("--cache-dir", default=LOCAL_SCREEN_CACHE)
    if paths:
        p.add_argument("--manifest", default=MANIFEST_PATH)
        p.add_argument("--suite-root", default=None)
        p.add_argument("--gate-override", default=None)


def _build_args(a):
    fam = family_runs(load_json(a.config), a.family, standin=a.standin)
    return eval5_args(a.family, a.group, fam["runs"], fam["allmlp"], screen_cache=a.cache_dir)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("args", help="the evaluate_circuit.py arguments, one per line")
    _positionals(p, "family", "group")
    _common(p, paths=False)
    p = sub.add_parser("check", help="every refusal known before the dry-run; exit 3 if any")
    _positionals(p, "family", "group")
    p.add_argument("--dry", action="store_true")
    _common(p)
    p = sub.add_parser("gate", help="the F knockout wikitext KL gate of one family")
    _positionals(p, "family")
    _common(p)
    p = sub.add_parser("seed-cache", help="copy the group's A40 screens into the local cache")
    _positionals(p, "group")
    p.add_argument("--cache-src", default=SCREEN_CACHE_SRC)
    p.add_argument("--cache-dir", default=LOCAL_SCREEN_CACHE)
    p = sub.add_parser("cache-check", help="refuse unless every screen is an A40 cache hit")
    _positionals(p, "log", "group")
    p.add_argument("--cache-dir", default=LOCAL_SCREEN_CACHE)
    p.add_argument("--partition", default=DEFAULT_PARTITION)
    p.add_argument("--allow-rescreen", default=None)
    p = sub.add_parser("sbatch", help="the sbatch argv, one per line")
    _positionals(p, "family", "group")
    p.add_argument("--log", required=True)
    p.add_argument("--account", required=True)
    p.add_argument("--partition", default=DEFAULT_PARTITION)
    p.add_argument("--time", default=None)
    _common(p, paths=False)
    p = sub.add_parser("cost", help="judge calls and GPU hours from a --dry-run log")
    _positionals(p, "log")
    p.add_argument("--family")
    p.add_argument("--group")
    p.add_argument("--known-n-from", default=None,
                   help="an existing suite whose post-screen item counts to use "
                        "(default: the family's existing eval5_* suite)")
    p = sub.add_parser("record", help="append a dry or submit event to the EVAL 5 record")
    _positionals(p, "family", "group")
    p.add_argument("--event", choices=("dry", "submit"), required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--record", default=RECORD_PATH)
    p.add_argument("--account", default=None)
    p.add_argument("--partition", default=DEFAULT_PARTITION)
    p.add_argument("--job-id", default=None)
    p.add_argument("--allow-rescreen", default=None)
    _common(p)
    a = ap.parse_args(argv)

    try:
        if a.cmd == "args":
            print("\n".join(_build_args(a)))
            return 0
        if a.cmd == "check":
            reasons = refusals(a.family, a.group, config=load_json(a.config),
                               manifest=load_json(a.manifest), env=dict(os.environ),
                               suite_root=a.suite_root, dry=a.dry, standin=a.standin,
                               gate_override=a.gate_override)
            fam = family_runs(load_json(a.config), a.family)
            if fam["runs"]["F"] and a.gate_override:
                g = gate(a.suite_root or default_suite_root(a.family),
                         (load_json(a.manifest).get("suites") or {}).get(fam["suite"]) or {},
                         f_run=fam["runs"]["F"], override=a.gate_override)
                for msg in g["overridden"]:
                    print(f"gate overridden ({a.gate_override}): {msg}")
            for r in reasons:
                print(f"REFUSED: {r}")
            if not reasons:
                print("cleared: F configured, gate passed" + ("" if a.dry else f", {GO_ENV}=1"))
            return 3 if reasons else 0
        if a.cmd == "gate":
            fam = family_runs(load_json(a.config), a.family)
            root = a.suite_root or default_suite_root(a.family)
            if not fam["runs"]["F"]:
                print(f"REFUSED: suites.json {fam['suite']} runs.F is null")
                return 3
            g = gate(root, (load_json(a.manifest).get("suites") or {}).get(fam["suite"]) or {},
                     f_run=fam["runs"]["F"], override=a.gate_override)
            for path, kl in g["kl"].items():
                print(f"  {path}: wikitext KL {kl:.3f}")
            for msg in g["overridden"]:
                print(f"OVERRIDDEN ({a.gate_override}): {msg}")
            for r in g["reasons"]:
                print(f"REFUSED: {r}")
            print(f"gate {'PASSED' if g['passed'] else 'FAILED'} ({root})")
            return 0 if g["passed"] else 3
        if a.cmd == "seed-cache":
            out = seed_screen_cache(GROUP_DATASETS[a.group], src=a.cache_src, dst=a.cache_dir)
            print(f"screen cache {a.cache_dir}: copied {len(out['copied'])}, kept {len(out['kept'])}, "
                  f"skipped (not A40 or no .pt) {len(out['skipped'])} from {a.cache_src}")
            return 0
        if a.cmd == "cache-check":
            with open(a.log, errors="replace") as f:
                parsed = parse_dryrun(f.read())
            r = cache_check(parsed, a.group, cache_dir=a.cache_dir, partition=a.partition,
                            allow_rescreen=a.allow_rescreen)
            for reason in r["reasons"]:
                print(f"{'ALLOWED' if r['allowed'] else 'REFUSED'}: {reason}")
            if r["allowed"] and r["reasons"]:
                print(f"re-screen allowed ({r['allowed']}): the items will not match the existing suites")
            if not r["reasons"]:
                print(f"cleared: every screen is an {A40_DEVICE} cache hit on {a.partition}")
            return 0 if r["passed"] else 3
        if a.cmd == "sbatch":
            with open(a.log, errors="replace") as f:
                parsed = parse_dryrun(f.read())
            if not parsed["passed"]:
                print(f"the dry-run in {a.log} did not pass", file=sys.stderr)
                return 5
            print("\n".join(sbatch_cmd(a.family, a.group, _build_args(a), account=a.account,
                                       ceiling_min=parsed["ceiling_min"], time_=a.time,
                                       partition=a.partition)))
            return 0
        if a.cmd == "cost":
            cost, parsed, anchor = suite_cost(a.log, a.family, a.group, a.known_n_from)
            print(render_cost(cost, parsed))
            if anchor:
                print(f"        (item counts from {anchor})")
            return 0
        if a.cmd == "record":
            cost, parsed, anchor = suite_cost(a.log, a.family, a.group)
            fam = family_runs(load_json(a.config), a.family, standin=a.standin)
            g = None
            if not a.standin and fam["runs"]["F"]:
                g = gate(a.suite_root or default_suite_root(a.family),
                         (load_json(a.manifest).get("suites") or {}).get(fam["suite"]) or {},
                         f_run=fam["runs"]["F"], override=a.gate_override)
            r = cache_check(parsed, a.group, cache_dir=a.cache_dir, partition=a.partition,
                            allow_rescreen=a.allow_rescreen)
            record_event(a.record, a.family, a.group, {
                "event": a.event, "standin": a.standin, "runs": fam["runs"],
                "args": eval5_args(a.family, a.group, fam["runs"], fam["allmlp"],
                                   screen_cache=a.cache_dir),
                "log": a.log, "dry_run_passed": parsed["passed"], "cost": cost,
                "cost_items_from": anchor, "account": a.account, "partition": a.partition,
                "job_id": a.job_id,
                "gate_kl": g["kl"] if g else None, "gate_reasons": g["reasons"] if g else None,
                "gate_override": a.gate_override, "gate_overridden": g["overridden"] if g else [],
                "cache_reasons": r["reasons"], "allow_rescreen": r["allowed"]})
            print(f"recorded {a.event} in {a.record}")
            return 0
    except (ValueError, KeyError, OSError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 3
    return 2


if __name__ == "__main__":
    sys.exit(main())
