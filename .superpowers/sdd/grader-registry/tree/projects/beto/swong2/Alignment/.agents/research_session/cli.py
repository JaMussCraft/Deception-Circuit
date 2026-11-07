#!/usr/bin/env python3
"""research-session command line (spec section 5.6).

Run as a script (``python3.9 -B .../research_session/cli.py lint FILE...``) or as a module. Later tickets add
subcommands in order (02, 03, 06, 11; ruling R18): each one adds a ``cmd_<name>`` function and registers it in
``build_parser``.

Ticket 02 adds ``register``, ``status``, ``usage-check``, ``usage-ack`` and ``set-cadence``. ``usage-ack`` and
``set-cadence`` are for humans only: the gate denies any model-issued command that names them (R7).

Ticket 03 adds the record commands. Each record module registers its own subcommands through ``add_parsers``:
``registry`` (``validate``, ``render``, ``ledger-rollup``, ``claim``, ``release``), ``worklog`` (``worklog-append``,
``worklog-set``), ``setup`` (``init``), ``ledger`` (``ledger add|reconcile|api``), ``jobs`` (``job add|update|list``)
and ``findings`` (``findings-check``).

Ticket 06 adds ``hook <event> --tool <claude|codex>``, the target of every hook command (spec 5.1). ``main`` passes
it to ``hooks.main`` before argparse runs, so a hook call always exits 0; the ``hook`` parser below exists only for
``--help``.

Ticket 11 adds ``audit-scan <transcript.jsonl>...`` through the ``audit`` module's ``add_parsers``. It is read-only and
prints JSON: compactions with ``preTokens`` per agent, runs of identical failing tool calls, Agent calls without a
model, repeated Bash commands, permission denials and Codex ``compacted`` counts.
"""

import argparse
import os
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_session import lint as _lint  # noqa: E402
from research_session import paths, state, usage  # noqa: E402
from research_session import audit, findings, jobs, ledger, registry, setup, worklog  # noqa: E402

RECORD_MODULES = (registry, worklog, setup, ledger, jobs, findings, audit)

MAX_STALE_OK_MINUTES = 60


def cmd_lint(args):
    """Lint files; print ``path:line: rule: excerpt`` per failing unit; exit 1 on any failure, 2 on a read error."""
    failed = False
    unreadable = False
    for path in args.files:
        try:
            findings = _lint.lint_file(path, glue=not args.secrets_only, secrets=True)
        except (IOError, OSError) as exc:
            sys.stderr.write("%s: cannot read: %s\n" % (path, exc.strerror or exc))
            unreadable = True
            continue
        for f in findings:
            print(_lint.format_finding(path, f))
        if findings:
            failed = True
    if args.summary:
        sys.stderr.write("lint: %d file(s), %s\n" % (len(args.files), "failures" if failed else "clean"))
    if unreadable:
        return 2
    return 1 if failed else 0


# ---------------------------------------------------------------------------------------------------------------
# Ticket 02: session state, readings, acknowledgement


def _cfg():
    return paths.Config.from_env()


def _cwd(args):
    return os.path.realpath(getattr(args, "cwd", None) or os.getcwd())


def _err(message):
    sys.stderr.write("research-session: %s\n" % message)


def _fmt(v):
    return usage._fmt(v)


def _direction_line(cfg, session):
    slug, how = state.resolve_direction(cfg, session)
    if how == "register":
        return "direction: %s (registered %s)" % (slug, session["register"].get("at"))
    if how == "cwd":
        return ("direction: %s by cwd match, attribution only; not registered, so no checkpoints. "
                "Run `research-session register %s` to bind it." % (slug, slug))
    return "direction: none; not registered. Run `research-session register <slug>` to get checkpoints."


def cmd_register(args):
    cfg = _cfg()
    now = time.time()
    try:
        session, warnings, mirrored = state.register(cfg, args.slug, now, selector=args.session, cwd=_cwd(args))
    except state.StateError as exc:
        _err(str(exc))
        return 1
    for w in warnings:
        _err("warning: " + w)
    u = session["usage"]
    print("registered session %s to direction %s" % (session["tag"], args.slug))
    print("session id %s, cwd %s" % (session["session_id"], session.get("cwd")))
    print("points at register %s; checkpoint 1 at +%s points (cadence %s)" % (
        _fmt(u["points_at_register"]), _fmt(u["cadence"]), _fmt(u["cadence"])))
    print("state.json: %s (%s)" % (session["register"]["state_path"], mirrored or "not mirrored"))
    return 0


def cmd_status(args):
    cfg = _cfg()
    now = time.time()
    try:
        session = state.find_session(cfg, args.session, _cwd(args))
    except state.StateError as exc:
        _err(str(exc))
        return 1
    u = session["usage"]
    print("session %s (%s), cwd %s" % (session["tag"], session["session_id"], session.get("cwd")))
    print(_direction_line(cfg, session))
    last = u.get("last_reading") or {}
    if last:
        five = "not applicable" if last.get("five_hour") is None and last.get("fresh") else \
            "%s%%" % _fmt(last.get("five_hour"))
        print("last reading: five-hour %s, seven-day %s%%, Fable %s%% at %s (%s)" % (
            five, _fmt(last.get("seven_day")), _fmt(last.get("fable")),
            last.get("read_at"), "fresh" if last.get("fresh") else "unknown or stale"))
    else:
        print("last reading: none yet")
    since = u.get("session_points", 0) - u.get("points_at_register", 0)
    print("session points %s (%s since register); cadence %s; next checkpoint %s at +%s" % (
        _fmt(u.get("session_points")), _fmt(since), _fmt(u.get("cadence")), u.get("next_checkpoint"),
        _fmt(u.get("next_checkpoint", 1) * (u.get("cadence") or 0))))
    freeze = u.get("freeze")
    if freeze and freeze.get("checkpoint", 0) > u.get("acked_through", 0):
        print("freeze: checkpoint %s, stage %s since %s; waits for a human `continue` or "
              "`! research-session usage-ack`" % (freeze["checkpoint"], freeze.get("stage"), freeze.get("crossed_at")))
    else:
        print("freeze: none; acked through checkpoint %s" % u.get("acked_through", 0))
    if usage.stale_ok_active(session, now):
        print("stale-ok window open until %s" % u.get("stale_ok_until"))
    print("compactions: %s" % session.get("compactions", 0))
    return 0


def cmd_usage_check(args):
    cfg = _cfg()
    now = time.time()
    if args.tool == "codex":
        reading, _ = usage.read_codex(cfg, now)
    else:
        reading = usage.read_claude(cfg, now, refresh=not args.no_refresh)
    print("reading (%s): %s" % (reading["tool"], usage.format_reading(reading) if reading["known"] else "unknown"))
    if reading["tool"] == "claude":
        print("freshness: five-hour and seven-day %s (%s); Fable %s (%s); limit %d min" % (
            "fresh" if reading["fresh_main"] else "stale", usage.describe_age(reading["age_main"]),
            "fresh" if reading["fresh_fable"] else "stale", usage.describe_age(reading["age_fable"]),
            usage.STALE_SECONDS // 60))
        if reading["refresh_attempted"]:
            status = {"fetched": "fetched from the usage endpoint", "cache": "merged from the cache",
                      "skipped": "skipped", "failed": "failed"}.get(reading["refresh"], reading["refresh"])
            print("refresh: %s%s" % (status, "; " + reading["refresh_error"] if reading["refresh_error"] else ""))
        else:
            print("refresh: not needed" if reading["known"] else "refresh: not attempted (--no-refresh)")
        gap = reading.get("fable_gap")
        notice = usage.fable_notice(reading)
        print("fable gap: %s points%s" % (_fmt(gap), (". " + notice) if notice else ""))
    else:
        print("source: %s%s" % (reading["source"], " (cached)" if reading.get("cached") else ""))
    for note in reading.get("notes") or []:
        print("note: %s" % note)
    if not reading["known"] and reading.get("error"):
        print("unknown because: %s" % reading["error"])
    return 0 if reading["known"] else 1


def cmd_usage_ack(args):
    cfg = _cfg()
    now = time.time()
    if args.stale_ok is not None and not (0 < args.stale_ok <= MAX_STALE_OK_MINUTES):
        _err("refused: --stale-ok takes 1 to %d minutes (R8)" % MAX_STALE_OK_MINUTES)
        return 2
    try:
        target = state.find_session(cfg, args.session, _cwd(args))
    except state.StateError as exc:
        _err(str(exc))
        return 1

    def apply(session):
        u = session["usage"]
        if args.stale_ok is not None:
            u["stale_ok_until"] = paths.iso(now + args.stale_ok * 60)
            u["stale_ok_by"] = "usage-ack"
            return ("stale", u["stale_ok_until"])
        return ("ack", state.ack(session, now, "usage-ack"))

    session, (what, value), _ = state.update_session(cfg, target["tool"], target["session_id"], apply, now,
                                                     create=False)
    slug, how = state.resolve_direction(cfg, session)
    where = "session %s (cwd %s, direction %s)" % (session["tag"], session.get("cwd"), slug or "none")
    if what == "stale":
        print("stale-ok window open until %s for %s; acked_by usage-ack" % (value, where))
    elif value is None:
        print("no pending checkpoint for %s; nothing acknowledged" % where)
    else:
        print("acknowledged checkpoint %s for %s; acked_by usage-ack" % (value, where))
    return 0


def cmd_set_cadence(args):
    cfg = _cfg()
    now = time.time()
    if args.points <= 0:
        _err("cadence must be a positive number of points")
        return 2
    try:
        target = state.find_session(cfg, args.session, _cwd(args))
    except state.StateError as exc:
        _err(str(exc))
        return 1

    def apply(session):
        session["usage"]["cadence"] = args.points

    session, _, _ = state.update_session(cfg, target["tool"], target["session_id"], apply, now, create=False)
    u = session["usage"]
    print("cadence for session %s set to %s points; next checkpoint %s at +%s points since register" % (
        session["tag"], _fmt(args.points), u.get("next_checkpoint"), _fmt(u.get("next_checkpoint", 1) * args.points)))
    return 0


def _add_session_args(p):
    p.add_argument("--session", help="session id, tag or id prefix (default: most recent session with this cwd)")
    p.add_argument("--cwd", help=argparse.SUPPRESS)


def build_parser():
    parser = argparse.ArgumentParser(prog="research-session", description="Research-session state and lint tools.")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("lint", help="glue lint and secret scan of Markdown files (spec 5.5)")
    p.add_argument("files", nargs="+", help="files to lint")
    p.add_argument("--secrets-only", action="store_true", help="run only the secret scan")
    p.add_argument("--summary", action="store_true", help="print a one-line summary on stderr")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("register", help="bind a session to a direction; enables checkpoints (R5)")
    p.add_argument("slug", help="direction id, as in directions.json")
    _add_session_args(p)
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("status", help="show the session, direction, reading, points and freeze (read-only)")
    _add_session_args(p)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("usage-check", help="print the usage reading, its freshness, the refresh and the Fable gap")
    p.add_argument("--tool", choices=("claude", "codex"), default="claude")
    p.add_argument("--no-refresh", action="store_true", help="do not refresh a stale reading")
    p.set_defaults(func=cmd_usage_check)

    p = sub.add_parser("usage-ack", help="human only: acknowledge the pending checkpoint, or open a stale-ok window")
    _add_session_args(p)
    p.add_argument("--stale-ok", type=int, metavar="MIN",
                   help="allow spawns for MIN minutes (at most 60) while the reading is unknown")
    p.set_defaults(func=cmd_usage_ack)

    p = sub.add_parser("set-cadence", help="human only: set the checkpoint cadence in points")
    p.add_argument("points", type=int)
    _add_session_args(p)
    p.set_defaults(func=cmd_set_cadence)

    for module in RECORD_MODULES:
        module.add_parsers(sub)

    p = sub.add_parser("hook", help="hook entry point for Claude and Codex: hook <event> --tool <claude|codex> "
                                    "(reads the hook JSON on stdin; always exits 0)")
    p.add_argument("event", help="session-start, post-compact, pre-tool-use, post-tool-use, user-prompt-submit, "
                                 "subagent-start, subagent-stop or stop")
    p.add_argument("--tool", default="claude", help="claude or codex")
    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "hook":
        # Ticket 06: hook calls bypass argparse, so a bad argument can never exit 2 (which blocks in PreToolUse).
        from research_session import hooks
        return hooks.main(argv[1:])
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
