"""``job add|update|list``: the Slurm job list in a direction's ``state.json`` (spec 4.5, 5.6; R39).

RS never calls ``sbatch`` or ``sacct``. ``job add`` stores the job with its waiter command, a ``sacct`` polling loop
bounded by ``timeout`` at 60 minutes or less. ``job add`` does not write the ledger; ``ledger add`` does (R39).
"""

import os
import sys

from research_session import paths, records, registry, state

EXPECTED_TERMINAL = ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL"]
MAX_WAIT_MINUTES = 60
SSH_CLUSTERS = {"bridges2": "bridges2", "bridges-2": "bridges2"}


def waiter(job_id, cluster, minutes=MAX_WAIT_MINUTES):
    """The waiter command for a job, run in the background by the orchestrator."""
    sacct = "sacct -j %s -X -n -o State" % job_id
    host = SSH_CLUSTERS.get(str(cluster).lower())
    if host:
        sacct = "ssh -o BatchMode=yes %s %s" % (host, sacct)
    return "timeout %dm sh -c 'until %s | grep -qE \"%s\"; do sleep 300; done'" % (
        minutes, sacct, "|".join(EXPECTED_TERMINAL))


def _edit_state(cfg, d, fn):
    d = os.path.abspath(d)
    if not os.path.isdir(d):
        raise ValueError("no direction directory at %s" % d)
    sp = records.state_json_path(d)
    with records.state_lock(cfg, sp):
        st = state.load_json(sp)
        if st is None:
            st = {"schema": 1, "direction": os.path.basename(d), "session_state": "running",
                  "last_worklog_entry_at": None, "sessions": {}, "jobs": []}
        result = fn(st)
        errors, _ = registry.validate_state(st)
        if errors:
            raise ValueError("state.json would be invalid: " + "; ".join(errors[:3]))
        records.write_json(sp, st)
    return result


def cmd_job(args):
    cfg = paths.Config.from_env()
    t = records.now()
    try:
        if args.action == "add":
            if not (0 < args.timeout_min <= MAX_WAIT_MINUTES):
                raise ValueError("--timeout-min is 1 to %d minutes" % MAX_WAIT_MINUTES)

            def add(st):
                if [j for j in st["jobs"] if j["job_id"] == args.job_id and j["cluster"] == args.cluster]:
                    raise ValueError("job %s on %s is already recorded" % (args.job_id, args.cluster))
                job = {"job_id": args.job_id, "cluster": args.cluster, "submitted_at": paths.iso(t),
                       "waiter": waiter(args.job_id, args.cluster, args.timeout_min),
                       "expected_terminal": list(EXPECTED_TERMINAL), "status": args.status,
                       "last_progress_at": paths.iso(t)}
                st["jobs"].append(job)
                return job
            job = _edit_state(cfg, args.dir, add)
            print("recorded job %s on %s (%s). Waiter, run in the background:" % (job["job_id"], job["cluster"],
                                                                                 job["status"]))
            print(job["waiter"])
            return 0
        if args.action == "update":
            def update(st):
                rows = [j for j in st["jobs"] if j["job_id"] == args.job_id and
                        (args.cluster is None or j["cluster"] == args.cluster)]
                if not rows:
                    raise ValueError("unknown job %s" % args.job_id)
                for j in rows:
                    j["status"] = args.status
                    j["last_progress_at"] = paths.iso(t)
                return rows[0]
            job = _edit_state(cfg, args.dir, update)
            print("job %s on %s is now %s" % (job["job_id"], job["cluster"], job["status"]))
            return 0
        st = state.load_json(records.state_json_path(args.dir)) or {"jobs": []}
        jobs = [j for j in st.get("jobs") or [] if args.all or j.get("status") not in EXPECTED_TERMINAL]
        if not jobs:
            print("no %sjobs recorded" % ("" if args.all else "open "))
        for j in jobs:
            print("job %s on %s: %s since %s" % (j["job_id"], j["cluster"], j["status"], j.get("last_progress_at")))
            print("  waiter: %s" % j["waiter"])
        return 0
    except ValueError as exc:
        sys.stderr.write("research-session: refused: %s\n" % exc)
        return 1


def add_parsers(sub):
    p = sub.add_parser("job", help="record Slurm jobs and their waiter commands in state.json (add, update, list)")
    p.add_argument("action", choices=("add", "update", "list"))
    p.add_argument("dir", help="direction directory")
    p.add_argument("job_id", nargs="?", help="job id (update)")
    p.add_argument("--job-id", dest="job_id_opt", help="job id (add)")
    p.add_argument("--cluster", help="cluster name, e.g. delta or bridges2")
    p.add_argument("--status", choices=registry.JOB_STATUS, help="job state (default PENDING for add)")
    p.add_argument("--timeout-min", type=int, default=MAX_WAIT_MINUTES, help="waiter timeout, at most 60 minutes")
    p.add_argument("--all", action="store_true", help="list terminal jobs too")
    p.set_defaults(func=_dispatch)


def _dispatch(args):
    if args.action == "add":
        args.job_id = args.job_id_opt or args.job_id
        if not args.job_id or not args.cluster:
            sys.stderr.write("research-session: job add needs --job-id and --cluster\n")
            return 2
        args.status = args.status or "PENDING"
    elif args.action == "update":
        args.job_id = args.job_id or args.job_id_opt
        if not args.job_id or not args.status:
            sys.stderr.write("research-session: job update needs a job id and --status\n")
            return 2
    return cmd_job(args)
