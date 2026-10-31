#!/usr/bin/env python3
"""Hook smoke test for wave H (ticket 06). Stdlib only; runs on base python3.9 and on mgnp.

It reads the research-session hook commands from the installed settings files, checks that each one is the literal
shell guard of spec 5.1, and runs each one through ``/bin/sh -c`` the way Claude Code and Codex do:

1. With every RS path pointed at a temporary directory (state root, usage.json, OAuth cache and lock, credentials,
   codex-usage, directions.json), it feeds one input per event and asserts the exact stdout and exit 0. The usage
   fixture is fresh and at 85% weekly, so the PreToolUse input ``hook_smoke.json`` (a crafted Agent call) must be
   denied by the cap. No real session file, no real usage.json and no credentials are touched.
2. It rewrites the CLI path of each command to a missing file under the temporary directory, and then the kill-switch
   path to a file that exists there, and asserts exit 0 with no output both times.
3. With ``--live`` it also runs the installed PreToolUse command once in the real environment with
   ``hook_smoke.json`` and accepts exit 0 with no output or valid JSON. That run uses the real usage.json and may
   refresh it through the OAuth endpoint, exactly as a real hook call would. Its session file is removed afterwards.

Usage, after wave A is applied and before wave H:

    python3.9 -B hook_smoke.py --settings F/staged/claude-hooks-fragment.json F/staged/codex-hooks-fragment.json

and after wave H, with the installed files (the default):

    python3.9 -B hook_smoke.py [--live]

``--cli PATH`` runs the test copies against another cli.py (for example the staged one) instead of the installed one.
Exit status 0 means every check passed; 1 means at least one failed.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

A = "/projects/beto/swong2/Alignment"
CLI = A + "/.agents/research_session/cli.py"
DISABLED = "/u/swong2/.claude/research-session/DISABLED"
PY = "/sw/external/python/anaconda3/bin/python3.9"
HERE = os.path.dirname(os.path.abspath(__file__))
SMOKE_INPUT = os.path.join(HERE, "hook_smoke.json")
DEFAULT_SETTINGS = [A + "/.claude/settings.json",
                    A + "/Deception-Circuit/.claude/worktrees/autoresearch-workflow/.claude/settings.json",
                    A + "/Deception-Circuit/.claude/settings.json",
                    "/u/swong2/.codex/hooks.json"]
GUARD_RE = re.compile(
    r"^sh -c 'test -f " + re.escape(CLI) + r" && ! test -e " + re.escape(DISABLED) + r" && exec "
    + re.escape(PY) + r" -B " + re.escape(CLI) + r" hook (?P<event>[a-z-]+) --tool (?P<tool>claude|codex) \|\| exit 0'$")
RESET = 1793797200

CAP_CLAUDE = ("Usage cap pause: five-hour not applicable, seven-day 85%, Fable 20%, weekly max 85% (cap 80%). New "
              "agents and sbatch are blocked. Finish the step in flight, update RESUME and the worklog, send HOLD to "
              "running workers, and end the turn; the pause lifts when a fresh reading is below 80%.")
CAP_CODEX = ("Usage cap pause: Codex weekly 85% (cap 80%). New agents and sbatch are blocked. Finish the step in "
             "flight, update RESUME and the worklog, send HOLD to running workers, and end the turn; the pause lifts "
             "when a fresh reading is below 80%.")
CLAUDE_READING = "Usage: five-hour not applicable, seven-day 85%, Fable 20%, weekly max 85%."
UNREG = ("Direction: none; not registered. This session gets only the cap and stale gates, no checkpoints. To get "
         "checkpoints, run `research-session register <slug>`.")


def ctx(event, text):
    return json.dumps({"hookSpecificOutput": {"additionalContext": text, "hookEventName": event}},
                      sort_keys=True) + "\n"


def deny(reason):
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                              "permissionDecisionReason": reason}}, sort_keys=True) + "\n"


def base_input(tool, sid, event):
    d = {"session_id": sid, "transcript_path": None, "cwd": A, "permission_mode": "default",
         "hook_event_name": event, "model": "smoke"}
    if tool == "codex":
        d["turn_id"] = "turn-smoke"
    return d


def cases(tool):
    """Ordered (event, input, expected stdout) for one tool. The order matters: the spawn precedes its PostToolUse."""
    with open(SMOKE_INPUT) as fh:
        smoke = json.load(fh)
    sid = smoke["session_id"]
    tag = "%s-%s" % (tool, sid[:8])
    spawn = dict(smoke)
    if tool == "codex":
        spawn["tool_name"] = "spawn_agent"
    out = []

    def add(event, hook_event, expected, **fields):
        d = base_input(tool, sid, hook_event)
        d.update(fields)
        out.append((event, d, expected))

    start_usage = CLAUDE_READING if tool == "claude" else \
        "Usage: unknown (no recent Codex reading); the gate refreshes it before the next spawn."
    add("session-start", "SessionStart", ctx("SessionStart", "research-session: session %s. %s %s"
                                              % (tag, UNREG, start_usage)), source="startup")
    out.append(("pre-tool-use", spawn, deny(CAP_CLAUDE if tool == "claude" else CAP_CODEX)))
    after = CLAUDE_READING if tool == "claude" else "Usage: Codex weekly 85%."
    add("post-tool-use", "PostToolUse", ctx("PostToolUse", "research-session after spawn: %s Not registered, so no "
                                             "checkpoints." % after),
        tool_name=spawn["tool_name"], tool_input=spawn["tool_input"], tool_response="ok", tool_use_id="t1")
    add("session-start", "SessionStart", ctx("SessionStart", (
        "research-session: compaction #1 recorded for session %s. No direction is registered, so there is no RESUME "
        "or WORKLOG to name. Re-read your notes and the latest hand-backs before acting; do not restart finished "
        "work." % tag)), source="compact")
    if tool == "claude":
        add("post-compact", "PostCompact", "", trigger="auto", compact_summary="Smoke-test summary.")
    add("user-prompt-submit", "UserPromptSubmit", "", prompt="continue")
    add("subagent-start", "SubagentStart", "", agent_id="smoke-agent", agent_type="general-purpose")
    add("subagent-stop", "SubagentStop", "{}\n" if tool == "codex" else "", agent_id="smoke-agent",
        agent_type="general-purpose", agent_transcript_path=None, stop_hook_active=False,
        last_assistant_message="Smoke-test agent finished.")
    add("stop", "Stop", "{}\n" if tool == "codex" else "", stop_hook_active=False, last_assistant_message="Done.",
        background_tasks=[], session_crons=[])
    return out


def collect(settings_files):
    """``[(file, event_key, matcher, command)]`` for every RS hook command, plus problems found."""
    found, problems = [], []
    for path in settings_files:
        if not os.path.exists(path):
            continue
        try:
            with open(path) as fh:
                data = json.load(fh)
        except ValueError as exc:
            problems.append("%s: not valid JSON (%s)" % (path, exc))
            continue
        for event_key, groups in sorted(((data or {}).get("hooks") or {}).items()):
            for g in groups or []:
                for h in g.get("hooks") or []:
                    cmd = h.get("command") or ""
                    if "research_session/cli.py hook" not in cmd:
                        continue
                    if "$" in cmd or not GUARD_RE.match(cmd):
                        problems.append("%s %s: command is not the literal guard of spec 5.1: %s" % (path, event_key, cmd))
                        continue
                    found.append((path, event_key, g.get("matcher"), cmd))
    return found, problems


def make_env(tmp, weekly=85, fable=20):
    now = int(time.time())
    usage_file = os.path.join(tmp, "usage.json")
    with open(usage_file, "w") as fh:
        json.dump({"timestamp": now, "rate_limits": {
            "seven_day": {"used_percentage": weekly, "resets_at": RESET},
            "model_scoped": [{"display_name": "Fable", "used_percentage": fable, "resets_at": RESET}],
            "model_scoped_fetched_at": now}}, fh)
    fake = os.path.join(tmp, "codex-usage")
    with open(fake, "w") as fh:
        fh.write("#!/bin/sh\necho '{\"status\": \"ok\", \"weekly\": {\"used_percent\": %d, \"resets_at\": %d}}'\n"
                 % (weekly, RESET))
    os.chmod(fake, 0o700)
    env = dict(os.environ)
    env.update({
        "RESEARCH_SESSION_ROOT": os.path.join(tmp, "state"),
        "RESEARCH_SESSION_USAGE_FILE": usage_file,
        "RESEARCH_SESSION_OAUTH_CACHE": os.path.join(tmp, "oauth-cache.json"),
        "RESEARCH_SESSION_OAUTH_LOCK": os.path.join(tmp, "oauth-cache.lock"),
        "RESEARCH_SESSION_CREDENTIALS": os.path.join(tmp, "no-credentials.json"),
        "RESEARCH_SESSION_CODEX_USAGE": fake,
        "RESEARCH_SESSION_DIRECTIONS": os.path.join(tmp, "no-directions.json"),
    })
    for key in ("RESEARCH_SESSION_ALIGNMENT_ROOT", "RESEARCH_SESSION_DC_ROOT", "RESEARCH_SESSION_NOW"):
        env.pop(key, None)
    return env


def run(command, stdin_text, env, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(["/bin/sh", "-c", command], input=stdin_text, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True, env=env, timeout=timeout, cwd=A)
    except subprocess.TimeoutExpired:
        return None, "", "timed out after %s s" % timeout, time.time() - t0
    return p.returncode, p.stdout, p.stderr, time.time() - t0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--settings", nargs="+", default=DEFAULT_SETTINGS, help="settings or hooks.json files to read")
    ap.add_argument("--cli", help="run the test copies against this cli.py instead of the installed one")
    ap.add_argument("--live", action="store_true", help="also run PreToolUse once in the real environment")
    ap.add_argument("--timeout", type=float, default=30.0, help="seconds per call (default 30)")
    args = ap.parse_args(argv)

    found, problems = collect(args.settings)
    failures = list(problems)
    for p in problems:
        print("FAIL " + p)
    if not found:
        print("FAIL no research-session hook command found in: " + ", ".join(args.settings))
        return 1
    by_tool_event = {}
    for path, event_key, matcher, cmd in found:
        m = GUARD_RE.match(cmd)
        by_tool_event.setdefault((m.group("tool"), m.group("event")), cmd)
        print("found %-16s %-26s %s (%s)" % (event_key, matcher or "(no matcher)", m.group("event") + " --tool " +
                                             m.group("tool"), path))

    tmp = tempfile.mkdtemp(prefix="hook-smoke-")
    try:
        env = make_env(tmp)

        def test_copy(cmd, cli=None, disabled=None):
            out = cmd
            if cli or args.cli:
                out = out.replace(CLI, cli or args.cli)
            if disabled:
                out = out.replace(DISABLED, disabled)
            return out

        slowest = 0.0
        for tool in ("claude", "codex"):
            for event, data, expected in cases(tool):
                cmd = by_tool_event.get((tool, event))
                if not cmd:
                    continue
                code, out, err, dt = run(test_copy(cmd), json.dumps(data), env, args.timeout)
                slowest = max(slowest, dt)
                label = "%s --tool %s (%s)" % (event, tool, data.get("source") or data.get("tool_name") or
                                               data["hook_event_name"])
                if code == 0 and out == expected:
                    print("PASS %-58s %.2f s" % (label, dt))
                else:
                    failures.append(label)
                    print("FAIL %-58s exit %s\n  expected: %r\n  got:      %r\n  stderr:   %r"
                          % (label, code, expected, out, err[-500:]))
        missing = os.path.join(tmp, "missing", "cli.py")
        switch = os.path.join(tmp, "DISABLED")
        with open(switch, "w") as fh:
            fh.write("")
        with open(SMOKE_INPUT) as fh:
            smoke_text = fh.read()
        for (tool, event), cmd in sorted(by_tool_event.items()):
            for what, copy in (("missing CLI", test_copy(cmd, cli=missing)),
                               ("kill switch", test_copy(cmd, disabled=switch))):
                code, out, err, dt = run(copy, smoke_text, env, args.timeout)
                label = "%s --tool %s, %s" % (event, tool, what)
                if code == 0 and out == "" and err == "":
                    print("PASS %-58s %.2f s" % (label, dt))
                else:
                    failures.append(label)
                    print("FAIL %-58s exit %s stdout %r stderr %r" % (label, code, out, err[-300:]))
        if args.live:
            cmd = by_tool_event.get(("claude", "pre-tool-use"))
            data = json.loads(smoke_text)
            data["session_id"] = "5m0ke0live-%d" % os.getpid()
            live_env = {k: v for k, v in os.environ.items() if not k.startswith("RESEARCH_SESSION_")}
            code, out, err, dt = run(test_copy(cmd), json.dumps(data), live_env, args.timeout)
            ok = code == 0
            if out:
                try:
                    parsed = json.loads(out)
                    ok = ok and parsed["hookSpecificOutput"]["permissionDecision"] in ("deny", "allow")
                except (ValueError, KeyError, TypeError):
                    ok = False
            label = "live pre-tool-use --tool claude (real usage.json)"
            print("%s %-58s exit %s, %.2f s, output %s" % ("PASS" if ok else "FAIL", label, code, dt,
                                                         out.strip() or "(none: allowed)"))
            if not ok:
                failures.append(label)
            for suffix in ("", ".lock"):
                p = "/u/swong2/.claude/research-session/sessions/claude-%s.json%s" % (data["session_id"], suffix)
                if os.path.exists(p):
                    os.remove(p)
        print("slowest isolated call: %.2f s (Claude timeout 10 s, 20 s for PreToolUse)" % slowest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        print("hook smoke: %d failure(s)" % len(failures))
        return 1
    print("hook smoke: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
