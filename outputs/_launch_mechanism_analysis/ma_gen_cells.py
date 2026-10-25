#!/usr/bin/env python3
"""
ma_gen_cells.py -- sbatch lines for the mechanism-analysis evaluator suite on any cluster profile (ticket 01).

    python outputs/_launch_mechanism_analysis/ma_gen_cells.py --profile {delta,bridges2} --stage 1a \\
        [--only JOB ...] [--first N] [--account A] [--partition P] [--time HH:MM:SS | --walltime-floor MIN] \\
        [--via SCRIPT] --dry | --test-only | --submit --ledger PATH [--ledger-section NAME] [--ledger-ticket KEY]

Cells come from suite_ma.json (ma_build_suite.py). One job per task runs scripts/evaluate_chain.sbatch, which
runs one evaluate_circuit.py process per ablation scheme (groups separated by ':::'). A cluster profile is
`scripts/cluster/<name>.env` or any file given with --profile-file, sourced in a clean bash; it must export
DC_ACCOUNT, DC_PARTITION, DC_GPU_SPEC, DC_ACTIVATE, DC_HF_HOME, DC_HF_OFFLINE, DC_REPO_ROOT and DC_TIME_DEFAULT
(profile handling and the ledger arithmetic are ticket 06's gen_cells.py, reused). --account and --partition
override the profile's values (e.g. the bjhz account, or an H200 partition for the Delta fallback); the GPU class
for the walltime is read after the override.

    sbatch --export=ALL,DC_CLUSTER=<profile> --account=$DC_ACCOUNT --partition=$DC_PARTITION $DC_GPU_SPEC
           --time=<T> --job-name=ma-<stage>-<job> scripts/evaluate_chain.sbatch <group> ::: <group> ::: <group>

<T> is the cost model's estimate (ma_cells.job_minutes) x 1.5, rounded up to 15 min, at least --walltime-floor
(default 30); DC_TIME_DEFAULT when the GPU class is unknown; --time overrides both.

--dry prints a bash script and the GPU-hour estimate; nothing runs.
--test-only runs `sbatch --test-only` for every planned job (or `SCRIPT submit --test-only ...` with --via):
  Slurm validates account, partition, GPU spec and time and says when the job would start. No ledger write.
--submit runs on the canonical checkout, where the compute ledger lives:
  * it refuses profile values that are still placeholders (__NAME__)
  * it enforces the ticket's allocation in the ledger section (default section: the profile's name; default
    ticket: 03-phase1-ablation-replication-and-sweeps, --ledger-ticket for another key, e.g. the Delta fallback):
    reconciled + in flight + new must stay within the allocation and the section's cap; if not, nothing is
    submitted and the message says how many leading jobs fit (--first N)
  * it runs ma_check_cells.py on this checkout; any problem aborts
  * every ledger read-modify-write holds the ledger lock (agent-brief, R16): `<ledger stem>.lock/` made with
    mkdir, the writer in `owner`; a held lock is an error, never broken
  * per job: reserve (status submitting), submit, record the job id (or zero a failed reservation), append the
    row to eval_jobs.txt
  * it submits with sbatch when DC_REPO_ROOT is this checkout, else through --via SCRIPT (scripts/remote/b2.sh),
    called as `SCRIPT submit --script scripts/evaluate_chain.sbatch --time T --job-name N -- <chain args>`
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ma_cells as mc  # noqa: E402


#: Ticket 06's generator: profile loading, GPU class, ledger arithmetic.
v2 = mc._load_module("mv2_gen_cells", f"{mc.V2_LAUNCH}/gen_cells.py")
UsageError = v2.UsageError
PROFILE_VARS = v2.PROFILE_VARS
PLACEHOLDER = v2.PLACEHOLDER
load_profile = v2.load_profile
gpu_class = v2.gpu_class
gpu_count = v2.gpu_count
ledger_section = v2.ledger_section
default_section = v2.default_section
budget_check = v2.budget_check
update_totals = v2.update_totals

SBATCH_SCRIPT = mc.CHAIN_SCRIPT
TICKET = "03-phase1-ablation-replication-and-sweeps"
JOBS_FILE = os.path.join(HERE, "eval_jobs.txt")
#: Files whose sha256 each reservation records (repo-relative), plus the profile file.
SOURCES = (f"{mc.LAUNCH_DIR}/ma_gen_cells.py", f"{mc.LAUNCH_DIR}/ma_cells.py", f"{mc.LAUNCH_DIR}/suite_ma.json",
           "evaluate_circuit.py", "evaluation/ablation.py", "evaluation/context.py", "evaluation/knockout.py",
           SBATCH_SCRIPT, "scripts/evaluate_circuit.sbatch")


def profile_path(name: str, repo: str = mc.REPO) -> str:
    return os.path.join(repo, "scripts", "cluster", f"{name}.env")


def job_name(job) -> str:
    return f"ma-{job['stage']}-{job['job']}"


def job_time(job, profile: dict, a) -> str:
    if a.time:
        return a.time
    cls = gpu_class(profile)
    return mc.walltime(mc.job_minutes(job, cls), a.walltime_floor) if cls else profile["DC_TIME_DEFAULT"]


def sbatch_argv(job, profile: dict, name: str, time: str, test_only: bool = False) -> list:
    return ["sbatch", *(["--test-only"] if test_only else []), f"--export=ALL,DC_CLUSTER={name}",
            f"--account={profile['DC_ACCOUNT']}", f"--partition={profile['DC_PARTITION']}",
            *shlex.split(profile["DC_GPU_SPEC"]), f"--time={time}", f"--job-name={job_name(job)}",
            SBATCH_SCRIPT, *mc.chain_args(job)]


def via_argv(job, via: str, time: str, test_only: bool = False) -> list:
    return [via, "submit", *(["--test-only"] if test_only else []), "--script", SBATCH_SCRIPT, "--time", time,
            "--job-name", job_name(job), "--", *mc.chain_args(job)]


def via_command(job, via: str, time: str, test_only: bool = False) -> list:
    """via_argv as executed: a dispatcher without the execute bit (a checkout that lost +x) runs under bash."""
    argv = via_argv(job, via, time, test_only)
    if os.path.isfile(via) and not os.access(via, os.X_OK):
        return ["/bin/bash", *argv]
    return argv


def plan(a) -> list:
    cells = mc.load_suite()["cells"]
    try:
        jobs = mc.jobs_for(mc.select(cells, a.stage))
    except ValueError as e:
        raise UsageError(str(e))
    if a.only:
        unknown = sorted(set(a.only) - {j["job"] for j in jobs})
        if unknown:
            raise UsageError(f"--only: no job(s) {', '.join(unknown)} in stage {a.stage}")
        jobs = [j for j in jobs if j["job"] in a.only]
    if a.first is not None:
        jobs = jobs[:a.first]
    return jobs


# ------------------------------------------------------------------ the compute ledger, under its lock

def lock_path(ledger: str) -> str:
    return os.path.splitext(ledger)[0] + ".lock"


def edit_ledger(path: str, section, fn, owner: str) -> None:
    """Read-modify-write one ledger section with fn(section), then its totals; atomic replace; under the lock.

    The lock is a directory made with mkdir (atomic). A held lock is an error and is never broken: another
    ticket is writing, or a writer died and the orchestrator must look (agent-brief).
    """
    lock = lock_path(path)
    try:
        os.mkdir(lock)
    except FileExistsError:
        try:
            with open(os.path.join(lock, "owner")) as f:
                held = f.read().strip()
        except OSError:
            held = "unknown owner"
        raise UsageError(f"ledger lock {lock} is held ({held}); retry in a few minutes, never break it")
    try:
        with open(os.path.join(lock, "owner"), "w") as f:
            f.write(owner + "\n")
        data = v2._read_json(path)
        sec = ledger_section(data, section)
        fn(sec)
        update_totals(sec)
        v2._write_json(path, data)
    finally:
        # The owner file is missing when writing it was what failed; that error is the one to surface.
        with contextlib.suppress(FileNotFoundError):
            os.remove(os.path.join(lock, "owner"))
        os.rmdir(lock)


def sources_sha256(profile_file: str) -> dict:
    out = {rel: v2._sha256(os.path.join(mc.REPO, rel)) for rel in SOURCES if os.path.exists(os.path.join(mc.REPO, rel))}
    out[os.path.relpath(profile_file, mc.REPO)] = v2._sha256(profile_file)
    return out


def dry_script(jobs, profile: dict, name: str, path: str, a) -> str:
    cls = gpu_class(profile)
    n = gpu_count(profile)
    est = sum(mc.job_minutes(j, cls) for j in jobs) / 60 * n if cls else None
    times = [job_time(j, profile, a) for j in jobs]
    reserved = sum(mc.walltime_hours(t) for t in times) * n
    out = ["#!/bin/bash",
           f"# mechanism-analysis evaluator suite, stage {a.stage}: {sum(len(j['cells']) for j in jobs)} cells in "
           f"{len(jobs)} chained jobs ({sum(len(j['groups']) for j in jobs)} evaluate_circuit.py runs)",
           f"# {mc.load_suite()['stages'][a.stage]['note']}",
           f"# profile {name} from {path}; GPU class {cls or 'unknown (DC_TIME_DEFAULT per job)'}, {n} GPU/job",
           ("# estimate %.2f GPU-h elapsed; " % est if est is not None else "# ")
           + f"reservation {reserved:.2f} GPU-h (--time x GPUs)"]
    for var, value in profile.items():
        if PLACEHOLDER.search(value):
            out.append(f"# WARNING: {var}={value} is a placeholder; --submit refuses it")
    if a.via:      # the dispatcher runs here; it cds into DC_REPO_ROOT on the other cluster itself
        out += [f"# jobs run in {profile['DC_REPO_ROOT']} through {a.via}", "set -euo pipefail",
                f"cd {shlex.quote(os.path.realpath(mc.REPO))}"]
    else:
        out += ["set -euo pipefail", f"cd {shlex.quote(profile['DC_REPO_ROOT'])}", "mkdir -p logs"]
    for job, t in zip(jobs, times):
        est_j = f"est {mc.job_minutes(job, cls):.1f} min, --time {t}" if cls else f"no estimate, --time {t}"
        out.append(f"# {job['job']}: " + "; ".join(
            f"{g['scheme']} ({len(g['cells'])}): " + ", ".join(c["label"] for c in g["cells"])
            for g in job["groups"]) + f" | {est_j}")
        out.append(shlex.join(via_argv(job, a.via, t) if a.via else sbatch_argv(job, profile, name, t)))
    return "\n".join(out) + "\n"


def _is_local(profile: dict) -> bool:
    return os.path.realpath(profile["DC_REPO_ROOT"]) == os.path.realpath(mc.REPO)


def _route(profile: dict, a) -> bool:
    local = _is_local(profile)
    if not local and not a.via:
        raise UsageError(f"DC_REPO_ROOT={profile['DC_REPO_ROOT']} is not this checkout "
                         f"({os.path.realpath(mc.REPO)}); submit to that cluster with --via SCRIPT, its dispatcher "
                         f"under scripts/remote/, which sets the submit environment the job's profile needs")
    return local


def _run(cmd) -> tuple:
    try:
        r = subprocess.run(cmd, cwd=os.path.realpath(mc.REPO), capture_output=True, text=True)
        return r.stdout, r.stderr, r.returncode
    except OSError as e:           # the launcher itself did not start: nothing was submitted
        return "", f"{cmd[0]}: {e}", 127


def test_only(jobs, profile: dict, name: str, a) -> int:
    local = _route(profile, a)
    status = 0
    for job in jobs:
        t = job_time(job, profile, a)
        cmd = sbatch_argv(job, profile, name, t, True) if local else via_command(job, a.via, t, True)
        out, err, code = _run(cmd)
        print(f"{job['job']} --time {t}: exit {code}")
        for text in (out, err):
            if text.strip():
                print("  " + text.strip().replace("\n", "\n  "))
        status = status or code
    return 1 if status else 0


def submit(jobs, profile: dict, name: str, path: str, a) -> int:
    bad = [f"{k}={v}" for k, v in profile.items() if PLACEHOLDER.search(v)]
    if bad:
        raise UsageError(f"profile values are placeholders: {', '.join(bad)}")
    if not a.ledger:
        raise UsageError("--submit needs --ledger PATH (the compute ledger; reservations are written there)")
    local = _route(profile, a)
    repo = os.path.realpath(mc.REPO)
    section = a.ledger_section if a.ledger_section is not None else default_section(v2._read_json(a.ledger), name)
    ticket = a.ledger_ticket
    gpus = gpu_count(profile)
    times = [job_time(j, profile, a) for j in jobs]
    hours = [mc.walltime_hours(t) * gpus for t in times]
    budget_check(ledger_section(v2._read_json(a.ledger), section), ticket, hours)

    import ma_check_cells
    problems = ma_check_cells.check_jobs(jobs, repo)
    print(f"check: {len(jobs)} job(s), {sum(len(p) for p in problems.values())} problem(s)")
    for job, items in problems.items():
        for item in items:
            print(f"  {job}: {item}")
    if any(problems.values()):
        return 1
    if local:
        os.makedirs(os.path.join(repo, "logs"), exist_ok=True)
    sources = sources_sha256(path)
    for job, t, h in zip(jobs, times, hours):
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        owner = f"ma_gen_cells.py ({ticket}) {stamp} pid {os.getpid()}"
        rid = f"{ticket.split('-')[0]}-{job['stage']}-{job['job']}-{stamp}-pid{os.getpid()}"
        res = {"reservation_id": rid, "ticket": ticket,
               "purpose": f"mechanism-analysis stage {job['stage']} job {job['job']}: "
                          + "; ".join(f"{g['scheme']}: " + ", ".join(c["label"] for c in g["cells"])
                                      for g in job["groups"]),
               "job_id": None, "account": profile["DC_ACCOUNT"], "partition": profile["DC_PARTITION"],
               "gpu_spec": profile["DC_GPU_SPEC"], "gpus": gpus, "time_limit": t, "reserved_gpu_hours": h,
               "status": "submitting", "submitted_at": stamp, "ended_at": None, "actual_seconds": None,
               "actual_gpu_hours": None, "output_dir": [g["output_dir"] for g in job["groups"]],
               "source_sha256": sources,
               "notes": f"ma_gen_cells.py --profile {name}" + (f" via {a.via}" if a.via else "")}

        def reserve(sec, res=res):
            budget_check(sec, ticket, [res["reserved_gpu_hours"]])     # re-check on the fresh read
            sec["reservations"].append(res)
        edit_ledger(a.ledger, section, reserve, owner)
        cmd = sbatch_argv(job, profile, name, t) if local else via_command(job, a.via, t)
        out, err, code = _run(cmd)
        m = re.search(r"Submitted batch job (\d+)", out)
        ok = code == 0 and m is not None

        def record(sec, rid=rid, ok=ok, m=m):
            for row in sec["reservations"]:
                if row["reservation_id"] == rid:
                    if ok:
                        row["job_id"], row["status"] = m.group(1), "submitted"
                    else:
                        row["reserved_gpu_hours"], row["status"] = 0.0, "submit-failed"
        edit_ledger(a.ledger, section, record, owner)
        if not ok:
            print(f"submission failed for {job['job']} (reservation zeroed): {out.strip()} {err.strip()}",
                  file=sys.stderr)
            return 1
        row = [stamp, name, job["stage"], job["job"], m.group(1), t,
               ",".join(g["output_dir"] for g in job["groups"])]
        with open(a.jobs_file, "a") as f:
            f.write("\t".join(row) + "\n")
        print("\t".join(row))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    who = p.add_mutually_exclusive_group(required=True)
    who.add_argument("--profile", help="scripts/cluster/<name>.env")
    who.add_argument("--profile-file", help="any profile file (its stem is the DC_CLUSTER name)")
    p.add_argument("--stage", required=True, choices=list(mc.STAGE_DIR))
    p.add_argument("--only", nargs="+", metavar="JOB", help="only these jobs (e.g. a rerun)")
    p.add_argument("--first", type=int, default=None, metavar="N", help="only the first N planned jobs")
    p.add_argument("--account", default=None, help="override the profile's DC_ACCOUNT")
    p.add_argument("--partition", default=None, help="override the profile's DC_PARTITION (and the GPU class)")
    p.add_argument("--time", default=None, help="override --time for every job (HH:MM:SS)")
    p.add_argument("--walltime-floor", type=int, default=mc.WALLTIME_FLOOR_MIN, metavar="MIN",
                   help="minimum --time in minutes for estimated jobs")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry", action="store_true")
    mode.add_argument("--test-only", action="store_true", help="sbatch --test-only every planned job; no ledger")
    mode.add_argument("--submit", action="store_true")
    p.add_argument("--jobs-file", default=JOBS_FILE)
    p.add_argument("--ledger", default=None, help="compute-ledger.json (required by --submit)")
    p.add_argument("--ledger-section", default=None,
                   help="ledger section (default: the profile's name when the ledger has it, else top level)")
    p.add_argument("--ledger-ticket", default=TICKET, help=f"allocation key in the section (default {TICKET})")
    p.add_argument("--via", default=None, metavar="SCRIPT",
                   help="dispatcher for a profile whose DC_REPO_ROOT is another cluster: "
                        "SCRIPT submit [--test-only] --script S --time T --job-name N -- ARGS")
    a = p.parse_args(argv)
    try:
        path = a.profile_file or profile_path(a.profile)
        name = a.profile or os.path.splitext(os.path.basename(path))[0]
        profile = load_profile(path)
        if a.account:
            profile["DC_ACCOUNT"] = a.account
        if a.partition:
            profile["DC_PARTITION"] = a.partition
        if a.walltime_floor < 15:
            raise UsageError("--walltime-floor must be at least 15 minutes")
        jobs = plan(a)
        if a.dry:
            sys.stdout.write(dry_script(jobs, profile, name, path, a))
            return 0
        if a.test_only:
            return test_only(jobs, profile, name, a)
        return submit(jobs, profile, name, path, a)
    except UsageError as e:
        print(f"ma_gen_cells.py: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
