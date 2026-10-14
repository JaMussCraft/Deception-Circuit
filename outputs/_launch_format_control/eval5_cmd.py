#!/usr/bin/env python3
"""
eval5_cmd.py — EVAL 5 for the format-control suites (ticket 06): the command
generator, the pre-flight gate and the refusals. NOTHING HERE SUBMITS A JOB;
`submit_eval5.sh` is the only caller that can, and only after every refusal
below has been cleared.

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
600). Two flags are added because this runs from a worktree, and neither
changes a number:

  --benchmark-screen-cache <main checkout>/outputs/_screens
      The existing eval5_* suites read their screens from the main checkout's
      cache (made on NVIDIA A40). The worktree has no cache, so without this
      every screen would be repaid and the screened items would no longer be
      the items the existing suites were judged on. The cache key includes the
      GPU: submit on an A40 partition to hit it.
  --benchmark-repo-root /projects/beto/swong2/Alignment
      The MASK and Liars' Bench checkouts sit beside the main checkout; the
      default resolves them relative to the code, i.e. inside .claude/worktrees.
      Not part of the screen-cache key (the evaluator hashes content, not path).

`--task-from <D run>` is mandatory: with no task flag the evaluator defaults to
every bound circuit's own test set, and D, H, F have three different
conditions, so it would run a 3 x 3 grid of benchmark cells instead of 3.

The pre-flight gate (spec: "eval 2 gate (wikitext KL <= 0.66) before eval 5")
reads the wikitext KL of the Format Circuit's knockout from ticket 04's suite:
the knockout cell of F on the F test set and on the D test set, found through
`suite_manifest.json`'s per-suite `cells` index. A suite is refused when either
cell is missing, has no KL, or has KL > 0.66; the refusal names the number.

CLI (run from the worktree root; every subcommand is read-only):

    python outputs/_launch_format_control/eval5_cmd.py args  <family> <sm|lb> [--standin]
    python outputs/_launch_format_control/eval5_cmd.py gate  <family>
    python outputs/_launch_format_control/eval5_cmd.py check <family> <sm|lb> [--dry] [--standin]
    python outputs/_launch_format_control/eval5_cmd.py cost  <dry-run log>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: The main checkout, which holds D, H, the screen cache and (beside it) the
#: benchmark repos. Read-only from this worktree.
MAIN_CHECKOUT = "/projects/beto/swong2/Alignment/Deception-Circuit"
SCREEN_CACHE = MAIN_CHECKOUT + "/outputs/_screens"
BENCHMARK_REPO_ROOT = "/projects/beto/swong2/Alignment"

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

#: The partition whose GPU (NVIDIA A40) made the cached screens.
DEFAULT_PARTITION = "gpuA40x4"


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


def eval5_args(family: str, group: str, runs: dict, allmlp: str = None) -> list:
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
             "--benchmark-screen-cache", SCREEN_CACHE,
             "--benchmark-repo-root", BENCHMARK_REPO_ROOT,
             "--output-dir", output_dir(family, group)]
    return args


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


def gate(suite_root: str, manifest_suite: dict, threshold: float = KL_GATE) -> dict:
    """Read each F knockout's wikitext KL from ticket 04's suite.

    -> {"passed": bool, "reasons": [str], "kl": {cell path: KL}}. Passing means
    both cells exist and both KLs are <= threshold. The spec's alternative
    ("or fluent generations") is the researcher's ruling, not this function's:
    a failure points at the knockout's generation examples to read.
    """
    reasons, kls = [], {}
    cells = f_knockout_cells(manifest_suite)
    for cond in GATE_CONDITIONS:
        cell = cells.get(cond)
        if cell is None:
            reasons.append(f"no F knockout cell on the {cond} test set in the suite manifest")
            continue
        path = cell["path"]
        ko_path = os.path.join(suite_root, path, "knockout.json")
        if not os.path.isfile(ko_path):
            reasons.append(f"F knockout cell missing: {path}/knockout.json not found under "
                           f"{suite_root} (has ticket 04's suite run and been merged?)")
            continue
        try:
            with open(ko_path) as f:
                kl = read_wikitext_kl(json.load(f))
        except (OSError, ValueError) as error:
            reasons.append(f"F knockout cell {path}: unreadable knockout.json ({error})")
            continue
        if kl is None:
            reasons.append(f"F knockout cell {path}: no wikitext KL in knockout.json "
                           f"(was eval 2 run with --skip-wikitext?)")
            continue
        kls[path] = kl
        if not kl <= threshold:
            reasons.append(f"F knockout wikitext KL {kl:.3f} > {threshold:.2f} in {path} "
                           f"({cond} test set): fails the eval 2 gate. The spec's "
                           f"alternative, fluent generations, is the researcher's call: "
                           f"read `generation.examples` in that knockout.json")
    return {"passed": not reasons, "reasons": reasons, "kl": kls}


# ==============================================================================
# CONFIGURATION, REFUSALS, THE SBATCH LINE
# ==============================================================================

#: The worktree root (this file is <root>/outputs/_launch_format_control/).
WORKTREE = os.path.dirname(os.path.dirname(HERE))
CONFIG_PATH = os.path.join(HERE, "suites.json")
MANIFEST_PATH = os.path.join(HERE, "suite_manifest.json")


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def family_runs(config: dict, family: str, standin: bool = False) -> dict:
    """D, H, F and the coarse all-MLP operand of a family, from suites.json.

    With `standin`, a null F is replaced by H (ticket 04's `standin_config`
    default): plumbing only, never submitted.
    """
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r} (expected one of {', '.join(FAMILIES)})")
    cfg = config[FAMILIES[family]]
    runs = {r: (cfg.get("runs") or {}).get(r) for r in ROLES}
    if standin:
        runs["F"] = runs["F"] or runs["H"]
    return {"suite": FAMILIES[family], "runs": runs, "allmlp": cfg.get("allmlp"),
            "standin": bool(standin)}


def default_suite_root(family: str) -> str:
    return os.path.join(WORKTREE, "outputs", "_suites", FAMILIES[family])


def refusals(family: str, group: str, *, config: dict, manifest: dict, env: dict,
             suite_root: str = None, dry: bool = False, standin: bool = False) -> list:
    """Every reason not to print (dry) or not to run (submit) the sbatch line.

    Empty list = cleared. A dry run needs no go-ahead but still obeys the F
    and gate refusals, so a suite that fails the gate never gets a submit line.
    """
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
        g = gate(root, (manifest.get("suites") or {}).get(fam["suite"]) or {})
        out += g["reasons"]
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
    import glob
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
# CLI
# ==============================================================================

def _positionals(p, *names):
    for name in names:
        p.add_argument(name)


def _common(p, *, paths=True):
    p.add_argument("--config", default=CONFIG_PATH)
    p.add_argument("--standin", action="store_true")
    if paths:
        p.add_argument("--manifest", default=MANIFEST_PATH)
        p.add_argument("--suite-root", default=None)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("args", help="the evaluate_circuit.py arguments, one per line")
    _positionals(p, "family", "group")
    _common(p, paths=False)
    p = sub.add_parser("check", help="every refusal; exit 3 if any")
    _positionals(p, "family", "group")
    p.add_argument("--dry", action="store_true")
    _common(p)
    p = sub.add_parser("gate", help="the F knockout wikitext KL gate of one family")
    _positionals(p, "family")
    _common(p)
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
    a = ap.parse_args(argv)

    try:
        if a.cmd == "args":
            fam = family_runs(load_json(a.config), a.family, standin=a.standin)
            print("\n".join(eval5_args(a.family, a.group, fam["runs"], fam["allmlp"])))
            return 0
        if a.cmd == "check":
            reasons = refusals(a.family, a.group, config=load_json(a.config),
                               manifest=load_json(a.manifest), env=dict(os.environ),
                               suite_root=a.suite_root, dry=a.dry, standin=a.standin)
            for r in reasons:
                print(f"REFUSED: {r}")
            if not reasons:
                print("cleared: F configured, gate passed"
                      + ("" if a.dry else f", {GO_ENV}=1"))
            return 3 if reasons else 0
        if a.cmd == "gate":
            fam = family_runs(load_json(a.config), a.family)
            root = a.suite_root or default_suite_root(a.family)
            g = gate(root, (load_json(a.manifest).get("suites") or {}).get(fam["suite"]) or {})
            for path, kl in g["kl"].items():
                print(f"  {path}: wikitext KL {kl:.3f}")
            for r in g["reasons"]:
                print(f"REFUSED: {r}")
            print(f"gate {'PASSED' if g['passed'] else 'FAILED'} ({root})")
            return 0 if g["passed"] else 3
        if a.cmd == "sbatch":
            with open(a.log, errors="replace") as f:
                parsed = parse_dryrun(f.read())
            if not parsed["passed"]:
                print(f"the dry-run in {a.log} did not pass", file=sys.stderr)
                return 5
            fam = family_runs(load_json(a.config), a.family, standin=a.standin)
            args = eval5_args(a.family, a.group, fam["runs"], fam["allmlp"])
            print("\n".join(sbatch_cmd(a.family, a.group, args, account=a.account,
                                       ceiling_min=parsed["ceiling_min"], time_=a.time,
                                       partition=a.partition)))
            return 0
        if a.cmd == "cost":
            with open(a.log, errors="replace") as f:
                parsed = parse_dryrun(f.read())
            anchor = a.known_n_from
            if anchor is None and (a.family, a.group) in ANCHOR_SUITES:
                anchor = os.path.join(MAIN_CHECKOUT, "outputs", ANCHOR_SUITES[(a.family, a.group)])
            known = known_item_counts(anchor) if anchor and os.path.isdir(anchor) else None
            print(render_cost(cost_estimate(parsed, known_n=known), parsed))
            if known:
                print(f"        (item counts from {anchor})")
            return 0
    except (ValueError, KeyError, OSError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 3
    return 2


if __name__ == "__main__":
    sys.exit(main())
