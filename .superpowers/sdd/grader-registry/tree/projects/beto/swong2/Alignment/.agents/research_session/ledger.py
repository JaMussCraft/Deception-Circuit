"""``ledger add|reconcile|api``: the only commands that record spend (spec 4.4, 5.6; R39).

Each subcommand changes the rows, recomputes ``totals`` from them, writes ``ledger.json`` atomically under the
direction's records lock and re-renders the WORKLOG head. RS never calls ``sbatch`` or ``sacct``; the caller passes
the numbers. ``api_usd_reserve`` has no row field in the schema, so it is kept as an accumulator.
"""

import os
import sys

from research_session import paths, records, registry, state, worklog

ACTIVE = ("PENDING", "RUNNING")
EXIT_API_CAP = 3


class LedgerError(Exception):
    pass


def apply(cfg, d, fn):
    """Run ``fn(ledger) -> message`` under the records lock; re-render the head when the direction has a worklog."""
    d = os.path.abspath(d)
    if os.path.exists(os.path.join(d, "worklog.json")):
        def mutate(ctx):
            if not isinstance(ctx.ledger, dict):
                raise LedgerError("no ledger.json in %s; create it with `research-session init %s --missing-only`"
                                  % (d, os.path.basename(d)))
            registry.carry_legacy(ctx.ledger)
            ctx.messages.append(fn(ctx.ledger))
            ctx.ledger_changed = True
        ctx, warnings = worklog.update_direction(cfg, d, mutate)
        return ctx.ledger, ctx.messages, warnings
    with records.records_lock(cfg, d):
        led = state.load_json(os.path.join(d, "ledger.json"))
        if not isinstance(led, dict):
            raise LedgerError("no ledger.json in %s" % d)
        registry.carry_legacy(led)
        msg = fn(led)
        led["totals"] = registry.ledger_totals(led)
        errors, _ = registry.validate_ledger(led)
        if errors:
            raise LedgerError("ledger.json would be invalid: " + "; ".join(errors[:3]))
        records.write_json(os.path.join(d, "ledger.json"), led)
    return led, [msg], ["no worklog.json in %s; the WORKLOG head was not re-rendered" % d]


def add(args):
    if args.gpus <= 0 or args.minutes <= 0:
        raise LedgerError("--gpus and --minutes must be positive")

    def fn(led):
        caps, res = led["caps"], led["reservations"]
        if [r for r in res if r["job_id"] == args.job_id and r["cluster"] == args.cluster]:
            raise LedgerError("job %s on %s is already in the ledger" % (args.job_id, args.cluster))
        hours = round(args.gpus * args.minutes / 60.0, 4)
        total = round(registry.ledger_totals(led)["reserved_gpu_hours"] + hours, 4)  # includes legacy_totals
        if total > float(caps["reserved_gpu_hours"]) + 1e-9:
            raise LedgerError("refused: %.2f reserved GPU-h would exceed the cap of %s (%s already reserved). A cap "
                              "of 0 means no GPU work is allowed; raising a cap is the user's decision"
                              % (total, worklog._num(caps["reserved_gpu_hours"]), worklog._num(total - hours)))
        active = len([r for r in res if r["status"] in ACTIVE])
        if active + 1 > int(caps["max_concurrent_gpu_jobs"]):
            raise LedgerError("refused: %d pending or running job(s) already; the cap is %d at once"
                              % (active, int(caps["max_concurrent_gpu_jobs"])))
        nums = [int(r["id"][2:]) for r in res if str(r.get("id", "")).startswith("r-") and r["id"][2:].isdigit()]
        rid = "r-%03d" % ((max(nums) + 1) if nums else 1)
        res.append({"id": rid, "job_id": args.job_id, "cluster": args.cluster, "account": args.account,
                    "partition": args.partition, "gpus": args.gpus, "requested_minutes": args.minutes,
                    "reserved_gpu_hours": hours, "actual_seconds": None, "status": "PENDING",
                    "source_commit": args.commit, "manifest_hash": None, "output_dir": args.output_dir})
        return "reserved %s: job %s, %s GPU-h; %s of %s GPU-h reserved" % (
            rid, args.job_id, worklog._num(hours), worklog._num(total), worklog._num(caps["reserved_gpu_hours"]))
    return fn


def reconcile(args):
    if args.status not in registry.RESERVATION_STATUS:
        raise LedgerError("unknown status %r; use one of %s" % (args.status, ", ".join(registry.RESERVATION_STATUS)))
    if args.actual_seconds < 0:
        raise LedgerError("--actual-seconds cannot be negative")

    def fn(led):
        rows = [r for r in led["reservations"] if r["job_id"] == args.job_id]
        if not rows:
            raise LedgerError("unknown job id %s in this ledger" % args.job_id)
        for r in rows:
            r["actual_seconds"] = int(args.actual_seconds)
            r["status"] = args.status
        return "job %s reconciled: %s after %d s" % (args.job_id, args.status, int(args.actual_seconds))
    return fn


def api(args):
    if args.usd < 0 or (args.calls or 0) < 0:
        raise LedgerError("--usd and --calls cannot be negative")

    def fn(led):
        day = records.today()
        rows = [c for c in led["api_calls"] if c["date"] == day and c["provider"] == args.provider]
        if rows:
            row = rows[0]
        else:
            row = {"date": day, "provider": args.provider, "calls": 0, "usd": 0.0}
            led["api_calls"].append(row)
        row["calls"] = int(row["calls"]) + int(args.calls or 0)
        if args.reserve:
            led["totals"]["api_usd_reserve"] = round(float(led["totals"].get("api_usd_reserve") or 0) + args.usd, 4)
        else:
            row["usd"] = round(float(row["usd"]) + args.usd, 4)
        return "recorded %s %s on %s (%s)" % (worklog._money(args.usd), "reserve" if args.reserve else "spend",
                                             args.provider, day)
    return fn


def cmd_ledger(args):
    cfg = paths.Config.from_env()
    try:
        fn = {"add": add, "reconcile": reconcile, "api": api}[args.action](args)
        led, messages, warnings = apply(cfg, args.dir, fn)
    except (LedgerError, worklog.WorklogError, worklog.UsageError) as exc:
        sys.stderr.write("research-session: %s\n" % exc)
        return 1
    for w in warnings:
        sys.stderr.write("research-session: warning: %s\n" % w)
    for m in messages:
        print(m)
    if args.action == "api":
        tot, cap = led["totals"], float(led["caps"]["paid_api_usd"])
        spent = float(tot["api_usd_known"]) + float(tot["api_usd_reserve"])
        if spent > cap + 1e-9:
            sys.stderr.write("research-session: CAP WARNING: paid API spend %s (known plus reserve) is past the cap "
                             "of %s. The spend is recorded. Stop paid work and open a need for the user.\n"
                             % (worklog._money(spent), worklog._money(cap)))
            return EXIT_API_CAP
    return 0


def add_parsers(sub):
    p = sub.add_parser("ledger", help="record GPU reservations and API spend; the only spend writers (R39)")
    lsub = p.add_subparsers(dest="action")
    a = lsub.add_parser("add", help="add a PENDING reservation; refuses past the caps")
    a.add_argument("dir")
    for name in ("--cluster", "--account", "--partition", "--job-id"):
        a.add_argument(name, required=True)
    a.add_argument("--gpus", type=int, required=True)
    a.add_argument("--minutes", type=float, required=True, help="requested wall time in minutes")
    a.add_argument("--commit", help="short SHA of the code the job runs")
    a.add_argument("--output-dir")
    a.set_defaults(func=cmd_ledger)
    r = lsub.add_parser("reconcile", help="set a job's actual seconds and final status")
    r.add_argument("dir")
    r.add_argument("job_id")
    r.add_argument("--actual-seconds", type=float, required=True)
    r.add_argument("--status", required=True)
    r.set_defaults(func=cmd_ledger)
    c = lsub.add_parser("api", help="record paid API spend for today; exits 3 past the cap")
    c.add_argument("dir")
    c.add_argument("--usd", type=float, required=True)
    c.add_argument("--provider", default="openrouter")
    c.add_argument("--calls", type=int, default=0)
    c.add_argument("--reserve", action="store_true", help="record a reserve instead of known spend")
    c.set_defaults(func=cmd_ledger)
