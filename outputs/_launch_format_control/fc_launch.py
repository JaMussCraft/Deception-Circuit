#!/usr/bin/env python3
"""
fc_launch.py — plan, dry-run, submit, merge and post-process the three
format-control evaluation suites.

    suites.json            the ONE configuration point: D, H, F run directories
                           per suite (F is null until ticket 03's runs exist)
    suite_manifest.json    every job and cell, its arguments, its dry-run
                           verdict and estimate, and its Slurm job id

Run every subcommand from the repo (worktree) root:

    python outputs/_launch_format_control/fc_launch.py plan
    python outputs/_launch_format_control/fc_launch.py args <suite> <job>
    python outputs/_launch_format_control/fc_launch.py dryrun [--suite S] [--job J] [--parallel N]
    python outputs/_launch_format_control/fc_launch.py submit --dry --accounts A [B ...] --partition P
    python outputs/_launch_format_control/fc_launch.py merge <suite>
    python outputs/_launch_format_control/fc_launch.py overlap <suite>
    python outputs/_launch_format_control/fc_launch.py standin-dryrun [--suite S]

`cell_cmd.sh` and `submit.sh` are thin wrappers over `args` and `submit`.
A job is submitted only after its login-node `--dry-run` passed (log under
dryrun/<suite>/<job>.log); --time is the dry-run estimate x 1.5 in quarter
hours (at least one hour) unless --time is given.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.getcwd())

from fc_cells import job_args, parse_dryrun_log, plan_suite, walltime  # noqa: E402

LAUNCH_REL = "outputs/_launch_format_control"
CONFIG_PATH = os.path.join(HERE, "suites.json")
MANIFEST_PATH = os.path.join(HERE, "suite_manifest.json")
DRYRUN_DIR = os.path.join(HERE, "dryrun")
STANDIN_DIR = os.path.join(HERE, "dryrun_standin")


# ==============================================================================
# CONFIG AND MANIFEST
# ==============================================================================

def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path) as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def build_manifest(config: dict, previous: dict = None, dryruns: dict = None) -> dict:
    """Every suite's jobs and cells. `previous` carries Slurm records forward;
    `dryruns` maps (suite, job) -> {"log", "passed", "estimate_min"}."""
    prev = {}
    for sname, s in ((previous or {}).get("suites") or {}).items():
        for j in s.get("jobs", []):
            prev[(sname, j["job"])] = j
    suites = {}
    for sname, cfg in config.items():
        jobs = []
        for job in plan_suite(sname, cfg):
            old = prev.get((sname, job["job"]), {})
            args = None if job["awaits"] else job_args(job)
            dr = (dryruns or {}).get((sname, job["job"]))
            if dr is None and old.get("args") == args:
                dr = old.get("dryrun")
            jobs.append({
                "job": job["job"], "cells": job["cells"], "evals": job["evals"],
                "compose_granularity": job["compose_granularity"],
                "task_from_role": job["task_from_role"], "awaits": job["awaits"],
                "args": args,
                "dryrun": dr or {"log": None, "passed": None, "estimate_min": None},
                "slurm": old.get("slurm") or {"job_id": None},
            })
        # Flat index for readers (ticket 05's summary writer): find a cell by
        # (circuit label, test-set condition) and read it at `path` under the
        # suite root, which is where merge_shards.py files it.
        cells = [dict(c, job=j["job"], path=f"cells/{c['circuit']}/{c['dataset']}/interchange")
                 for j in jobs for c in j["cells"]]
        suites[sname] = {"family": cfg["family"], "task": cfg["task"], "runs": cfg["runs"],
                         "allmlp": cfg.get("allmlp"), "cells": cells, "jobs": jobs}
    return {"created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "config": os.path.join(LAUNCH_REL, "suites.json"), "suites": suites}


def read_dryruns(config: dict, dryrun_dir: str = DRYRUN_DIR) -> dict:
    out = {}
    for sname, cfg in config.items():
        for job in plan_suite(sname, cfg):
            path = os.path.join(dryrun_dir, sname, f"{job['job']}.log")
            if os.path.exists(path):
                with open(path, errors="replace") as f:
                    passed, est = parse_dryrun_log(f.read())
                out[(sname, job["job"])] = {"log": os.path.relpath(path, HERE),
                                            "passed": passed, "estimate_min": est}
    return out


def load_manifest(path: str = MANIFEST_PATH):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_manifest(manifest: dict, path: str = MANIFEST_PATH) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=1)
    os.replace(tmp, path)


def refresh_manifest() -> dict:
    config = load_config()
    manifest = build_manifest(config, previous=load_manifest(), dryruns=read_dryruns(config))
    save_manifest(manifest)
    return manifest


# ==============================================================================
# SUBMISSION
# ==============================================================================

def short_name(suite: str) -> str:
    return re.sub(r"-nls[0-9.]+$", "", suite.replace("format-control-", ""))


def sbatch_cmd(suite: str, job: dict, *, account: str, partition: str, time_: str) -> list:
    return ["sbatch", f"--account={account}", f"--partition={partition}", f"--time={time_}",
            f"--job-name=fc-{short_name(suite)}-{job['job']}",
            f"--output={LAUNCH_REL}/logs/{suite}/{job['job']}_%j.out",
            "scripts/evaluate_circuit.sbatch", *job["args"]]


def _default_run(cmd: list) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def submit(manifest: dict, *, dry: bool, accounts, partition: str, suites=None, jobs=None,
           time: str = None, resubmit: bool = False, run=_default_run) -> list:
    """Submit (or with dry=True print) one sbatch per ready job. Returns the
    printed lines; records job ids in `manifest` in place."""
    lines, i = [], 0
    for sname, suite in manifest["suites"].items():
        if suites and sname not in suites:
            continue
        lines.append(f"# {sname}")
        for job in suite["jobs"]:
            if jobs and job["job"] not in jobs:
                continue
            jid = (job.get("slurm") or {}).get("job_id")
            if job["awaits"]:
                lines.append(f"# skip {job['job']}: awaits {', '.join(job['awaits'])}")
                continue
            if jid and not resubmit:
                lines.append(f"# skip {job['job']}: submitted as {jid}")
                continue
            dr = job.get("dryrun") or {}
            if not dr.get("passed"):
                lines.append(f"# skip {job['job']}: no passing dry-run")
                continue
            t = time or walltime(dr.get("estimate_min") or 60.0)
            account = accounts[i % len(accounts)]
            i += 1
            cmd = sbatch_cmd(sname, job, account=account, partition=partition, time_=t)
            lines.append(" ".join(shlex.quote(c) for c in cmd))
            if dry:
                continue
            os.makedirs(os.path.join(LAUNCH_REL, "logs", sname), exist_ok=True)
            out = run(cmd)
            new_id = out.strip().split()[-1]
            job["slurm"] = {"job_id": new_id, "account": account, "partition": partition,
                            "time": t, "submitted": time_stamp()}
            lines.append(f"#   -> {new_id}")
    return lines


def time_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ==============================================================================
# DRY RUNS
# ==============================================================================

def _dryrun_one(args: list, log_path: str, timeout: int) -> tuple:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    with open(log_path, "w") as f:
        f.write(f"# {time_stamp()}  python evaluate_circuit.py {shlex.join(args)} --dry-run\n")
        f.flush()
        try:
            subprocess.run([sys.executable, "evaluate_circuit.py", *args, "--dry-run"],
                           stdout=f, stderr=subprocess.STDOUT, env=env, timeout=timeout)
        except subprocess.TimeoutExpired:
            f.write(f"\nDRY-RUN TIMED OUT after {timeout} s\n")
    with open(log_path, errors="replace") as f:
        return parse_dryrun_log(f.read())


def dryrun(config: dict, out_dir: str, *, suites=None, jobs=None, parallel: int = 2,
           timeout: int = 1800, log=print) -> dict:
    todo = []
    for sname, cfg in config.items():
        if suites and sname not in suites:
            continue
        for job in plan_suite(sname, cfg):
            if jobs and job["job"] not in jobs:
                continue
            if job["awaits"]:
                log(f"  {sname} {job['job']}: awaits {', '.join(job['awaits'])}")
                continue
            todo.append((sname, job["job"], job_args(job),
                         os.path.join(out_dir, sname, f"{job['job']}.log")))
    results = {}
    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        futs = {pool.submit(_dryrun_one, a, p, timeout): (s, j, p) for s, j, a, p in todo}
        for fut, (s, j, p) in futs.items():
            passed, est = fut.result()
            results[(s, j)] = (passed, est)
            log(f"  {s} {j}: {'PASS' if passed else 'FAIL'}"
                f"{f'  est {est} min' if est else ''}  ({os.path.relpath(p, HERE)})")
    return results


def standin_config(config: dict, f_runs: dict = None) -> dict:
    """A plumbing-only dry-run of the F-dependent jobs before the Format
    Circuits exist. F is `f_runs[suite]` when given (e.g. a copy of the H run
    with `deception_condition: nopressure`, so the F test set really is
    `<task>_nopressure`), else the H run itself (then the "F test set" is the
    H test set)."""
    out = {}
    for sname, cfg in config.items():
        runs = dict(cfg["runs"])
        runs["F"] = runs["F"] or (f_runs or {}).get(sname) or runs["H"]
        out[sname] = dict(cfg, runs=runs)
    return out


# ==============================================================================
# CLI
# ==============================================================================

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="(re)write suite_manifest.json")
    p = sub.add_parser("args", help="print one job's evaluate_circuit.py arguments")
    p.add_argument("suite")
    p.add_argument("job")
    for name in ("dryrun", "standin-dryrun"):
        p = sub.add_parser(name)
        p.add_argument("--suite", action="append")
        p.add_argument("--job", action="append")
        p.add_argument("--parallel", type=int, default=2)
        p.add_argument("--timeout", type=int, default=1800)
        if name == "standin-dryrun":
            p.add_argument("--f-run", action="append", default=[], metavar="SUITE=RUN_DIR",
                           help="stand-in F run per suite (default: the suite's H run)")
    p = sub.add_parser("submit")
    p.add_argument("--dry", action="store_true", help="print the sbatch lines, submit nothing")
    p.add_argument("--accounts", nargs="+", default=["bgrb-delta-gpu"])
    p.add_argument("--partition", default="gpuA40x4,gpuA100x4,gpuA100x8")
    p.add_argument("--time", default=None, help="override the per-job estimate")
    p.add_argument("--suite", action="append")
    p.add_argument("--job", action="append")
    p.add_argument("--resubmit", action="store_true")
    p = sub.add_parser("merge")
    p.add_argument("suite")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("overlap")
    p.add_argument("suite")
    a = ap.parse_args(argv)

    if a.cmd == "plan":
        m = refresh_manifest()
        for s, v in m["suites"].items():
            n_ready = sum(1 for j in v["jobs"] if not j["awaits"])
            print(f"  {s}: {len(v['jobs'])} jobs ({n_ready} ready), "
                  f"{sum(len(j['cells']) for j in v['jobs'])} cells")
        print(f"  wrote {MANIFEST_PATH}")
    elif a.cmd == "args":
        cfg = load_config()[a.suite]
        job = {j["job"]: j for j in plan_suite(a.suite, cfg)}[a.job]
        print(shlex.join(job_args(job)))
    elif a.cmd == "dryrun":
        dryrun(load_config(), DRYRUN_DIR, suites=a.suite, jobs=a.job, parallel=a.parallel,
               timeout=a.timeout)
        refresh_manifest()
    elif a.cmd == "standin-dryrun":
        # Only the jobs the real configuration cannot dry-run yet.
        config = load_config()
        waiting = {j["job"] for s, c in config.items() for j in plan_suite(s, c) if j["awaits"]}
        jobs = [j for j in (a.job or sorted(waiting)) if j in waiting]
        f_runs = dict(x.split("=", 1) for x in a.f_run)
        dryrun(standin_config(config, f_runs), STANDIN_DIR, suites=a.suite, jobs=jobs,
               parallel=a.parallel, timeout=a.timeout)
    elif a.cmd == "submit":
        m = refresh_manifest()
        lines = submit(m, dry=a.dry, accounts=a.accounts, partition=a.partition,
                       suites=a.suite, jobs=a.job, time=a.time, resubmit=a.resubmit)
        print("\n".join(lines))
        if not a.dry:
            save_manifest(m)
    elif a.cmd == "merge":
        from merge_shards import expected_from_manifest, merge_suite
        refresh_manifest()
        merge_suite(os.path.join("outputs", "_suites", a.suite),
                    expected_from_manifest(MANIFEST_PATH, a.suite), force=a.force)
    elif a.cmd == "overlap":
        from overlap import write_overlap
        cfg = load_config()[a.suite]
        for p in write_overlap(os.path.join("outputs", "_suites", a.suite), cfg):
            print(f"  wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
