#!/usr/bin/env python3
"""
gen_cells.py -- sbatch lines for the v2 coarse evaluation suite on any cluster profile (ticket 06).

    python outputs/_launch_mechanism_v2/evals/gen_cells.py --profile {delta,bridges2} \\
        --stage {control,1,2} [--include-conditional] [--no-pack] [--only JOB ...] [--first N] \\
        [--time HH:MM:SS | --walltime-floor MIN] \\
        --dry | --submit --ledger PATH [--ledger-section NAME] [--via SCRIPT] [--drift-ok] [--user-go]

Cells come from suite_v2.json (build_suite.py). A cluster profile is `scripts/cluster/<name>.env`
(ticket 07), or any file given with --profile-file. It is sourced in a clean bash and must export
DC_ACCOUNT, DC_PARTITION, DC_GPU_SPEC, DC_ACTIVATE, DC_HF_HOME, DC_HF_OFFLINE, DC_REPO_ROOT and
DC_TIME_DEFAULT. Every sbatch line is built from those variables only:

    sbatch --export=ALL,DC_CLUSTER=<profile> --account=$DC_ACCOUNT --partition=$DC_PARTITION $DC_GPU_SPEC
           --time=<T> --job-name=mv2-<stage>-<job> scripts/evaluate_circuit.sbatch <evaluate_circuit.py args>

run from $DC_REPO_ROOT, with every path in the arguments relative to it. DC_CLUSTER makes the wrapper
source the same profile inside the job (DC_ACTIVATE, DC_HF_HOME, DC_HF_OFFLINE act there). <T> is the
suite cost model's estimate for the profile's GPU class (read from DC_GPU_SPEC and DC_PARTITION) x 1.5,
rounded up to 15 min, at least --walltime-floor minutes (default 60); DC_TIME_DEFAULT when the class is
unknown; --time overrides both.

--dry prints a bash script (cd, mkdir -p logs, one sbatch per job) and the GPU-hour estimate; nothing
runs. --submit runs on the canonical checkout (where the compute ledger lives):

  * it refuses stage 1 without --drift-ok (the orchestrator accepted the drift control), stage 2 without
    --user-go (the user has seen stage 1), and any profile value that is still a placeholder (__NAME__)
  * it enforces the ticket's allocation in the ledger section (--ledger-section, default: the section
    named after the profile when the ledger has one, else the top level): reserved GPU-h of this ticket's
    reservations (reconciled + in flight) + the new reservations must stay within
    allocations_gpu_hours[<ticket>] and within reserved_gpu_hour_cap when the section has one. Nothing is
    submitted when it does not fit; the message says how many leading jobs would (--first N)
  * it runs the login-node checker (check_cells.py) on this checkout; any problem aborts
  * per job it writes the reservation to the ledger (read-modify-write, atomic replace), submits, then
    records the job id there and in eval_jobs.txt (submitted_at, profile, stage, job, job_id, time,
    output_dir); a failed sbatch zeroes its reservation
  * it submits with sbatch when DC_REPO_ROOT is this checkout, else through --via SCRIPT, called as
    `SCRIPT submit --time T --job-name N -- <evaluate_circuit.py args>` (scripts/remote/b2.sh for a remote
    profile; it must print `Submitted batch job <id>`)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import mv2_cells as mc  # noqa: E402

PROFILE_VARS = ("DC_ACCOUNT", "DC_PARTITION", "DC_GPU_SPEC", "DC_ACTIVATE", "DC_HF_HOME", "DC_HF_OFFLINE",
                "DC_REPO_ROOT", "DC_TIME_DEFAULT")
SBATCH_SCRIPT = "scripts/evaluate_circuit.sbatch"
JOBS_FILE = os.path.join(HERE, "eval_jobs.txt")
#: Files whose sha256 each reservation records (repo-relative), plus the profile file.
SOURCES = ("outputs/_launch_mechanism_v2/evals/gen_cells.py", "outputs/_launch_mechanism_v2/evals/mv2_cells.py",
           "outputs/_launch_mechanism_v2/evals/suite_v2.json", "evaluate_circuit.py", SBATCH_SCRIPT)
PLACEHOLDER = re.compile(r"__[A-Z0-9_]+__")
#: GPU class names as they appear in a GPU spec or partition name (lower case), checked in this order.
GPU_TOKENS = (("h200", "H200"), ("h100", "H100"), ("a100", "A100"), ("l40s", "L40S"), ("a40", "A40"))


class UsageError(Exception):
    pass


def profile_path(name: str, repo: str = mc.REPO) -> str:
    return os.path.join(repo, "scripts", "cluster", f"{name}.env")


def load_profile(path: str) -> dict:
    """The DC_* variables a profile exports, sourced in a clean bash.

    Only PATH and HOME reach the shell: every value, including any cross-cluster root mapping, comes
    from the profile file itself, never from the caller's environment.
    """
    if not os.path.isfile(path):
        raise UsageError(f"cluster profile {path} not found. Profiles are scripts/cluster/<name>.env and come "
                         f"from ticket 07; pass --profile-file for any other file.")
    script = ('set -e; source "$1"; for v in ' + " ".join(PROFILE_VARS) +
              '; do if [ -n "${!v+x}" ]; then printf "%s=%s\\0" "$v" "${!v}"; fi; done')
    env = {"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/")}
    r = subprocess.run(["/bin/bash", "--noprofile", "--norc", "-c", script, "profile", path],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise UsageError(f"sourcing {path} failed: {r.stderr.strip()}")
    values = dict(item.split("=", 1) for item in r.stdout.split("\0") if item)
    missing = [v for v in PROFILE_VARS if v not in values]
    if missing:
        raise UsageError(f"{path} does not export {', '.join(missing)}")
    return values


def gpu_class(profile: dict):
    """The slowest GPU class named by DC_GPU_SPEC / DC_PARTITION, or None."""
    text = f"{profile['DC_GPU_SPEC']} {profile['DC_PARTITION']}".lower()
    found = [cls for token, cls in GPU_TOKENS if token in text]
    return min(found, key=lambda c: mc.SPEEDUP[c]) if found else None


#: The GPU count of a spec: --gpus=N, --gpus=type:N, --gpus-per-node=..., --gres=gpu[:type]:N.
GPU_COUNT = re.compile(r"--(?:gpus(?:-per-node)?=(?:[A-Za-z0-9_.-]+:)?|gres=gpu:(?:[A-Za-z0-9_.-]+:)?)(\d+)\b")


def gpu_count(profile: dict) -> int:
    m = GPU_COUNT.search(profile["DC_GPU_SPEC"])
    return int(m.group(1)) if m else 1


def job_time(job, profile: dict, a) -> str:
    if a.time:
        return a.time
    cls = gpu_class(profile)
    return mc.walltime(mc.job_minutes(job, cls), a.walltime_floor) if cls else profile["DC_TIME_DEFAULT"]


def sbatch_argv(job, profile: dict, name: str, time: str) -> list:
    return ["sbatch", f"--export=ALL,DC_CLUSTER={name}", f"--account={profile['DC_ACCOUNT']}",
            f"--partition={profile['DC_PARTITION']}", *shlex.split(profile["DC_GPU_SPEC"]),
            f"--time={time}", f"--job-name=mv2-{job['stage']}-{job['job']}", SBATCH_SCRIPT, *mc.job_args(job)]


def plan(a) -> list:
    cells = mc.load_suite()["cells"]
    try:
        jobs = mc.jobs_for(mc.select(cells, a.stage, a.include_conditional), pack=not a.no_pack)
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


def via_argv(job, via: str, time: str) -> list:
    return [via, "submit", "--time", time, "--job-name", f"mv2-{job['stage']}-{job['job']}", "--",
            *mc.job_args(job)]


# ------------------------------------------------------------------ the compute ledger

def _read_json(path):
    with open(path) as f:
        return json.load(f)


def _write_json(path, data):
    tmp = f"{path}.tmp-{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def ledger_section(ledger: dict, name):
    """The section holding `reservations` and `allocations_gpu_hours` (the top level when name is None)."""
    if name is None:
        return ledger
    sec = ledger.get(name)
    if not isinstance(sec, dict) or "reservations" not in sec:
        raise UsageError(f"ledger has no section {name!r} with reservations")
    return sec


def default_section(ledger: dict, profile_name: str):
    sec = ledger.get(profile_name)
    return profile_name if isinstance(sec, dict) and "reservations" in sec else None


def committed_hours(sec: dict, ticket=None) -> float:
    """Reserved GPU-h (reconciled rows already lowered to actual, in-flight rows at their --time)."""
    return sum(float(r.get("reserved_gpu_hours") or 0) for r in sec.get("reservations", [])
               if ticket is None or r.get("ticket") == ticket)


def budget_check(sec: dict, ticket: str, new_hours: list) -> None:
    """Refuse unless reconciled + in flight + new stays within the ticket allocation (and any cap)."""
    alloc = (sec.get("allocations_gpu_hours") or {}).get(ticket)
    if alloc is None:
        raise UsageError(f"ledger section has no allocation for {ticket}")
    mine, everyone = committed_hours(sec, ticket), committed_hours(sec)
    cap = sec.get("reserved_gpu_hour_cap")
    fit, total = 0, 0.0
    for h in new_hours:
        if mine + total + h > alloc + 1e-9 or (cap is not None and everyone + total + h > cap + 1e-9):
            break
        fit, total = fit + 1, total + h
    if fit < len(new_hours):
        raise UsageError(
            f"budget: {ticket} has {mine:.2f} GPU-h reserved (reconciled + in flight) of {alloc:.2f}"
            + (f", section total {everyone:.2f} of cap {cap:.2f}" if cap is not None else "")
            + f"; these {len(new_hours)} job(s) need {sum(new_hours):.2f}. Only the first {fit} fit "
              f"(--first {fit}); or reconcile finished jobs first.")


#: Reservation states that count as in flight in the totals.
IN_FLIGHT = ("submitting", "submitted", "pending", "running")


def update_totals(sec: dict) -> None:
    """Recompute those totals keys of the section that exist, from its reservations."""
    tot = sec.get("totals")
    if not isinstance(tot, dict):
        return
    rows = sec.get("reservations", [])
    inflight = sum(float(r.get("reserved_gpu_hours") or 0) for r in rows if r.get("status") in IN_FLIGHT)
    committed = committed_hours(sec)
    for key, value in (("reserved_gpu_hours_in_flight", inflight),
                       ("reconciled_gpu_hours", committed - inflight), ("committed_gpu_hours", committed)):
        if key in tot:
            tot[key] = round(value, 4)
    if "remaining_gpu_hours" in tot and sec.get("reserved_gpu_hour_cap") is not None:
        tot["remaining_gpu_hours"] = round(sec["reserved_gpu_hour_cap"] - committed, 4)
    if "committed_su" in tot and sec.get("su_rate_per_h100_gpu_hour") is not None:
        tot["committed_su"] = round(committed * sec["su_rate_per_h100_gpu_hour"], 4)
    if isinstance(tot.get("by_ticket_committed"), dict):
        for t in tot["by_ticket_committed"]:
            tot["by_ticket_committed"][t] = round(committed_hours(sec, t), 4)


def edit_ledger(path: str, section, fn) -> None:
    """Read-modify-write one ledger section with fn(section), then its totals; atomic replace."""
    data = _read_json(path)
    sec = ledger_section(data, section)
    fn(sec)
    update_totals(sec)
    _write_json(path, data)


def sources_sha256(profile_file: str) -> dict:
    out = {rel: _sha256(os.path.join(mc.REPO, rel)) for rel in SOURCES if os.path.exists(os.path.join(mc.REPO, rel))}
    out[os.path.relpath(profile_file, mc.REPO)] = _sha256(profile_file)
    return out


def dry_script(jobs, profile: dict, name: str, path: str, a) -> str:
    cls = gpu_class(profile)
    n = gpu_count(profile)
    est = sum(mc.job_minutes(j, cls) for j in jobs) / 60 * n if cls else None
    times = [job_time(j, profile, a) for j in jobs]
    reserved = sum(mc.walltime_hours(t) for t in times) * n
    out = ["#!/bin/bash",
           f"# mechanism-v2 coarse evals, stage {a.stage}: {sum(len(j['cells']) for j in jobs)} cells in "
           f"{len(jobs)} jobs ({'unpacked' if a.no_pack else 'packed'})"
           + (", conditional cells included" if a.include_conditional else ""),
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
        labels = ", ".join(c["label"] + (" [conditional]" if c["conditional"] else "") for c in job["cells"])
        est_j = f"est {mc.job_minutes(job, cls):.1f} min" if cls else "no estimate"
        out.append(f"# {job['job']}: {labels} | {est_j}")
        out.append(shlex.join(via_argv(job, a.via, t) if a.via else sbatch_argv(job, profile, name, t)))
    return "\n".join(out) + "\n"


def submit(jobs, profile: dict, name: str, path: str, a) -> int:
    if a.stage == "1" and not a.drift_ok:
        raise UsageError("stage 1 needs --drift-ok: the orchestrator must accept the drift control first")
    if a.stage == "2" and not a.user_go:
        raise UsageError("stage 2 needs --user-go: the user must have seen the stage-1 results")
    bad = [f"{k}={v}" for k, v in profile.items() if PLACEHOLDER.search(v)]
    if bad:
        raise UsageError(f"profile values are placeholders: {', '.join(bad)}")
    if not a.ledger:
        raise UsageError("--submit needs --ledger PATH (the compute ledger; reservations are written there)")
    repo = os.path.realpath(mc.REPO)
    local = os.path.realpath(profile["DC_REPO_ROOT"]) == repo
    if not local and not a.via:
        raise UsageError(f"DC_REPO_ROOT={profile['DC_REPO_ROOT']} is not this checkout ({repo}); submit to "
                         f"that cluster with --via SCRIPT, its dispatcher under scripts/remote/, which sets "
                         f"the submit environment the job's profile needs (DC_CLUSTER, the allocation)")
    section = a.ledger_section if a.ledger_section is not None else default_section(_read_json(a.ledger), name)
    ticket = mc.load_suite()["ticket"]
    gpus = gpu_count(profile)
    times = [job_time(j, profile, a) for j in jobs]
    hours = [mc.walltime_hours(t) * gpus for t in times]
    budget_check(ledger_section(_read_json(a.ledger), section), ticket, hours)

    import check_cells
    problems = check_cells.check_jobs(jobs, repo)
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
        rid = f"06-{job['stage']}-{job['job']}-{stamp}"
        res = {"reservation_id": rid, "ticket": ticket,
               "purpose": f"ticket 06 stage {job['stage']} job {job['job']}: "
                          + ", ".join(c["label"] for c in job["cells"]),
               "job_id": None, "account": profile["DC_ACCOUNT"], "partition": profile["DC_PARTITION"],
               "gpus": gpus, "time_limit": t, "reserved_gpu_hours": h, "status": "submitting",
               "submitted_at": stamp, "ended_at": None, "actual_seconds": None, "actual_gpu_hours": None,
               "output_dir": job["output_dir"], "source_sha256": sources,
               "notes": f"gen_cells.py --profile {name}" + (f" via {a.via}" if a.via else "")}

        def reserve(sec, res=res):
            budget_check(sec, ticket, [res["reserved_gpu_hours"]])     # re-check on the fresh read
            sec["reservations"].append(res)
        edit_ledger(a.ledger, section, reserve)
        cmd = sbatch_argv(job, profile, name, t) if local else via_argv(job, a.via, t)
        r = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
        m = re.search(r"Submitted batch job (\d+)", r.stdout)
        ok = r.returncode == 0 and m is not None

        def record(sec, rid=rid, ok=ok, m=m):
            for row in sec["reservations"]:
                if row["reservation_id"] == rid:
                    if ok:
                        row["job_id"], row["status"] = m.group(1), "submitted"
                    else:
                        row["reserved_gpu_hours"], row["status"] = 0.0, "submit-failed"
        edit_ledger(a.ledger, section, record)
        if not ok:
            print(f"sbatch failed for {job['job']}: {r.stdout.strip()} {r.stderr.strip()}", file=sys.stderr)
            return 1
        row = [stamp, name, job["stage"], job["job"], m.group(1), t, job["output_dir"]]
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
    p.add_argument("--include-conditional", action="store_true", help="stage 2: add the D-H cross-task cells")
    p.add_argument("--no-pack", action="store_true", help="one cell per job (default: packed jobs)")
    p.add_argument("--only", nargs="+", metavar="JOB", help="only these jobs (e.g. a rerun)")
    p.add_argument("--first", type=int, default=None, metavar="N", help="only the first N planned jobs")
    p.add_argument("--time", default=None, help="override --time for every job (HH:MM:SS)")
    p.add_argument("--walltime-floor", type=int, default=mc.WALLTIME_FLOOR_MIN, metavar="MIN",
                   help="minimum --time in minutes for estimated jobs (tighten once times are measured)")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry", action="store_true")
    mode.add_argument("--submit", action="store_true")
    p.add_argument("--drift-ok", action="store_true", help="required for --submit --stage 1")
    p.add_argument("--user-go", action="store_true", help="required for --submit --stage 2")
    p.add_argument("--jobs-file", default=JOBS_FILE)
    p.add_argument("--ledger", default=None, help="compute-ledger.json (required by --submit)")
    p.add_argument("--ledger-section", default=None,
                   help="ledger section (default: the profile's name when the ledger has it, else top level)")
    p.add_argument("--via", default=None, metavar="SCRIPT",
                   help="dispatcher for a profile whose DC_REPO_ROOT is another cluster: "
                        "SCRIPT submit --time T --job-name N -- ARGS")
    a = p.parse_args(argv)
    try:
        path = a.profile_file or profile_path(a.profile)
        name = a.profile or os.path.splitext(os.path.basename(path))[0]
        profile = load_profile(path)
        jobs = plan(a)
        if a.dry:
            sys.stdout.write(dry_script(jobs, profile, name, path, a))
            return 0
        if a.walltime_floor < 15:
            raise UsageError("--walltime-floor must be at least 15 minutes")
        return submit(jobs, profile, name, path, a)
    except UsageError as e:
        print(f"gen_cells.py: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
