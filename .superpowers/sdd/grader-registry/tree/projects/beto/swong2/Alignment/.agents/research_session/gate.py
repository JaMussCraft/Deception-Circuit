"""The PreToolUse usage gate (spec 5.2, rulings R5-R7, R30, R32, R36-R37).

``decide`` is a pure function of the hook input, the session record and the usage reading. ``evaluate`` is the thin
I/O around it: kill switch, cwd check, session file, reading and refresh. ``safe_evaluate`` is the fail-closed
wrapper: if anything raises, Agent and ``sbatch`` are denied with "gate error" and everything else is allowed.
``hook_output`` turns a decision into the PreToolUse JSON; ticket 06 only wires stdin and stdout to these.

Order of decisions for one call:

0. Kill switch present, or the realpath of ``cwd`` outside A: allow (the hook is a no-op).
1. Self-ack guard (Bash, Write, Edit) and, for Write and Edit, the glue lint and secret scan (R30, R37).
2. Cap pause: a fresh five-hour or weekly value at or above 80 denies Agent and ``sbatch``.
3. Unknown reading after the refresh: deny Agent and ``sbatch`` unless a human ``--stale-ok`` window is open.
4. Unregistered session (no ``register`` entry; a cwd match does not count): allow.
5. Freeze ``crossed``: deny Agent and ``sbatch``.
6. Freeze ``recorded``: also deny orchestrator SendMessage to anyone but ``main`` unless it starts with ``HOLD``.
7. Allow.
"""

import collections
import os
import re
import time

from research_session import lint as _lint
from research_session import paths, state, usage

MAX_REASON = 400

AGENT_TOOLS = frozenset(["Agent", "Task", "spawn_agent"])
BASH_TOOLS = frozenset(["Bash", "shell", "local_shell", "exec_command"])
WRITE_TOOLS = frozenset(["Write", "Edit", "MultiEdit", "NotebookEdit"])
MESSAGE_TOOLS = frozenset(["SendMessage"])

READ_ONLY_SUBCOMMANDS = ("validate", "status", "usage-check", "lint", "findings-check", "audit-scan")
GUARD_WORDS = ("usage-ack", "set-cadence", "research-session/sessions", "research-session/DISABLED")
SHELL_OPERATORS = (">", "<", ";", "&", "|", "`", "$(", "\n")

_SBATCH_RE = re.compile(r"(?<![A-Za-z0-9_-])sbatch(?![A-Za-z0-9_-])")
_JSON_NAME_RE = re.compile(r"(?:state|worklog)\.json")
_PATH_TOKEN_RE = re.compile(r"[^\s'\"<>|;&()`]*(?:state|worklog)\.json")
_DIRECTION_FILE_RE = re.compile(r"/docs/research/([^/]+)/(?:state|worklog)\.json$")
_READ_ONLY_RE = re.compile(
    r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
    r"(?:\S*/)?(?:research-session|python[0-9.]*\s+(?:-\S+\s+)*\S*research_session/cli\.py)"
    r"\s+(" + "|".join(re.escape(c) for c in READ_ONLY_SUBCOMMANDS) + r")(?:\s|$)")

Decision = collections.namedtuple("Decision", ["allow", "rule", "reason"])


def clip(text, limit=MAX_REASON):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def allow(rule):
    return Decision(True, rule, None)


def deny(rule, reason):
    return Decision(False, rule, clip(reason))


# ---------------------------------------------------------------------------------------------------------------
# Reason texts. Each names the next action and stays under 400 characters (tests check every one).

REASON_SELF_ACK = ("Denied: only a human may acknowledge a checkpoint, change the cadence, or touch the session "
                   "files or the kill switch (R7). Ask the user to run the command with `!` in the prompt, and "
                   "continue other work meanwhile.")


def _short(text, limit):
    text = str(text)
    return text if len(text) <= limit else "..." + text[-(limit - 3):]


def reason_state_file(path):
    return ("Denied: %s is written only by research-session (spec 5.3). Use the RS command that owns it, such as "
            "`research-session worklog-append`, or read it with `research-session status` or `validate`."
            % _short(path, 120))


def reason_lint(path, findings):
    units = []
    for f in findings:
        units.append("line %d %s: %s" % (f.line, f.rule, f.excerpt))
    head = "Write refused by the text lint (R30) for %s. Fix and retry: " % _short(os.path.basename(path), 60)
    tail = " Rewrite in full sentences with normal spacing; never paste secrets."
    room = MAX_REASON - len(head) - len(tail)
    body = "; ".join(units)
    if len(body) > room:
        body = body[: max(room - 3, 0)].rstrip() + "..."
    return head + body + tail


def reason_cap(reading):
    return ("Usage cap pause: %s (cap %d%%). New agents and sbatch are blocked. Finish the step in flight, update "
            "RESUME and the worklog, send HOLD to running workers, and end the turn; the pause lifts when a fresh "
            "reading is below %d%%." % (usage.format_reading(reading), usage.CAP_PERCENT, usage.CAP_PERCENT))


def reason_unknown(reading):
    src = os.path.basename(reading.get("source") or "usage.json")
    err = reading.get("refresh_error") or reading.get("error") or "no detail"
    if reading.get("tool") == "codex":
        what = "Codex usage is unknown (%s)" % err
    else:
        what = "Usage reading unknown: %s is %s and the refresh failed (%s)" % (
            src, usage.describe_age(usage.usage_file_age(reading)), err)
    return clip(what, 220) + (". New agents and sbatch are blocked; other work may continue. Ask the user to run "
                              "`! research-session usage-ack --stale-ok 30`, or retry later.")


def reason_freeze(session, recorded):
    u = session["usage"]
    n = u["freeze"]["checkpoint"]
    pts = u.get("session_points", 0) - u.get("points_at_register", 0)
    if recorded:
        return ("Checkpoint %d is recorded and waits for the user (+%s points since register). New agents and "
                "sbatch are held. Send HOLD to running workers and end the turn; the user replies `continue` or "
                "runs `! research-session usage-ack`." % (n, usage._fmt(pts)))
    return ("Checkpoint %d crossed (+%s points since register). New agents and sbatch are held. Finish the step in "
            "flight, run `research-session worklog-append <dir> --kind checkpoint --checkpoint %d`, send HOLD to "
            "running workers, and end the turn." % (n, usage._fmt(pts), n))


def reason_message(session):
    n = session["usage"]["freeze"]["checkpoint"]
    return ("Checkpoint %d is recorded and waits for the user. Only messages that start with HOLD, or messages to "
            "main, may go out now. Send HOLD to workers or end the turn; the user replies `continue` or runs "
            "`! research-session usage-ack`." % n)


def reason_gate_error(exc):
    return ("Gate error (%s): new agents and sbatch are blocked until the gate works. Continue other work and ask "
            "the user to check `research-session status` or create the DISABLED kill switch."
            % _short(type(exc).__name__, 60))


# ---------------------------------------------------------------------------------------------------------------
# Classification


def tool_kind(tool_name):
    if tool_name in AGENT_TOOLS:
        return "agent"
    if tool_name in BASH_TOOLS:
        return "bash"
    if tool_name in WRITE_TOOLS:
        return "write"
    if tool_name in MESSAGE_TOOLS:
        return "message"
    return "other"


def bash_command(tool_input):
    cmd = (tool_input or {}).get("command", "")
    if isinstance(cmd, list):
        cmd = " ".join(str(c) for c in cmd)
    return cmd if isinstance(cmd, str) else ""


def is_spend(kind, tool_input):
    """Agent spawns and Bash commands containing ``sbatch`` are new spend."""
    if kind == "agent":
        return True
    return kind == "bash" and bool(_SBATCH_RE.search(bash_command(tool_input)))


# ---------------------------------------------------------------------------------------------------------------
# Step 1: self-ack guard and the write lint


def is_direction_file(path):
    """``docs/research/<slug>/state.json`` or ``worklog.json``; ``_templates`` is exempt (R37)."""
    m = _DIRECTION_FILE_RE.search(path.replace(os.sep, "/"))
    return bool(m) and m.group(1) != "_templates"


def _abs(path, cwd):
    path = os.path.expanduser(path)
    return os.path.normpath(path if os.path.isabs(path) else os.path.join(cwd or "/", path))


def _under_state_root(path, cfg):
    return any(paths.is_within(path, root) or os.path.normpath(path).startswith(root.rstrip("/") + "/")
               for root in (cfg.state_root, paths.DEFAULT_STATE_ROOT))


def bash_names_direction_file(command, cwd):
    for tok in _PATH_TOKEN_RE.findall(command):
        if "_templates/" in tok:
            continue
        if any(c in tok for c in ("$", "*", "?", "[")):
            return True  # cannot resolve; treat as a direction file
        if is_direction_file(_abs(tok, cwd)):
            return True
    return False


def read_only_rs_command(command):
    if any(op in command for op in SHELL_OPERATORS):
        return False
    return bool(_READ_ONLY_RE.match(command))


def guard_bash(command, cwd, cfg):
    if any(w in command for w in GUARD_WORDS) or cfg.disabled_path in command \
            or paths.DEFAULT_DISABLED in command:
        return deny("self-ack", REASON_SELF_ACK)
    if os.path.join(cfg.state_root, "sessions") in command:
        return deny("self-ack", REASON_SELF_ACK)
    if _JSON_NAME_RE.search(command) and bash_names_direction_file(command, cwd):
        if not read_only_rs_command(command):
            return deny("state-file", reason_state_file("a direction state.json or worklog.json"))
    return None


def write_target(tool_input):
    ti = tool_input or {}
    return ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""


def write_text(tool_name, tool_input):
    ti = tool_input or {}
    if tool_name == "Write":
        return ti.get("content")
    if tool_name == "Edit":
        return ti.get("new_string")
    if tool_name == "MultiEdit":
        edits = ti.get("edits") or []
        return "\n\n".join(e.get("new_string", "") for e in edits if isinstance(e, dict))
    if tool_name == "NotebookEdit":
        return ti.get("new_source")
    return ti.get("content") or ti.get("new_string")


def guard_write(tool_name, tool_input, cwd, cfg):
    target = write_target(tool_input)
    if not target:
        return None
    path = _abs(target, cwd)
    if _under_state_root(path, cfg):
        return deny("self-ack", REASON_SELF_ACK)
    if is_direction_file(path):
        return deny("state-file", reason_state_file(target))
    text = write_text(tool_name, tool_input)
    if not isinstance(text, str) or not text:
        return None
    if _lint.glue_in_scope(path, cfg.alignment_root):
        findings = _lint.lint_text(text, glue=True, secrets=True)
    elif _lint.secret_in_scope(path, cfg.alignment_root):
        findings = _lint.lint_text(text, glue=False, secrets=True)
    else:
        findings = []
    if findings:
        return deny("lint", reason_lint(path, findings))
    return None


# ---------------------------------------------------------------------------------------------------------------
# The pure decision


def cap_reached(reading):
    """Any fresh five-hour or weekly value at or above the cap (fresh fields count even if another is stale)."""
    values = [reading.get(k) for k in ("h", "w", "five_hour", "seven_day", "fable")]
    return any(v is not None and v >= usage.CAP_PERCENT for v in values)


def decide(hook_input, session, reading, cfg, tool="claude", now=None):
    """Steps 1-7 of spec 5.2 for one PreToolUse call. ``reading`` may be None for Write and Edit."""
    now = time.time() if now is None else now
    tool_name = hook_input.get("tool_name") or ""
    tool_input = hook_input.get("tool_input") or {}
    cwd = hook_input.get("cwd") or ""
    kind = tool_kind(tool_name)

    # Step 1: files are protected in every session, registered or not, frozen or not.
    if kind == "bash":
        d = guard_bash(bash_command(tool_input), cwd, cfg)
        if d:
            return d
    if kind == "write":
        d = guard_write(tool_name, tool_input, cwd, cfg)
        return d or allow("write")
    if kind not in ("agent", "bash", "message"):
        return allow("other")

    spend = is_spend(kind, tool_input)
    reading = reading or usage.empty_reading(tool, "")

    # Step 2: cap pause.
    if spend and cap_reached(reading):
        return deny("cap", reason_cap(reading))
    # Step 3: unknown reading.
    if spend and not reading.get("known") and not usage.stale_ok_active(session, now):
        return deny("unknown", reason_unknown(reading))
    # Step 4: unregistered sessions get only the cap and stale gates (R5).
    if not state.is_registered(session):
        return allow("unregistered")
    u = session["usage"]
    freeze = u.get("freeze")
    pending = bool(freeze) and freeze.get("checkpoint", 0) > u.get("acked_through", 0)
    if pending:
        recorded = freeze.get("stage") == "recorded"
        # Steps 5 and 6.
        if spend:
            return deny("freeze-recorded" if recorded else "freeze-crossed", reason_freeze(session, recorded))
        if kind == "message" and recorded and tool != "codex" and not hook_input.get("agent_id"):
            to = tool_input.get("to")
            msg = tool_input.get("message")
            if to != "main" and not (isinstance(msg, str) and msg.lstrip().startswith("HOLD")):
                return deny("freeze-message", reason_message(session))
    return allow("allow")


# ---------------------------------------------------------------------------------------------------------------
# Thin I/O and the fail-closed wrapper


def evaluate(hook_input, tool="claude", cfg=None, now=None, reader=None):
    """Kill switch, cwd check, session file and reading around ``decide``.

    ``reader(cfg, tool, now, session)`` returns a reading; the default refreshes a stale Claude reading (R8) and
    uses the 120 s Codex cache. Readings are taken outside the session lock, so a slow refresh never blocks another
    hook call of the same session.
    """
    cfg = cfg or paths.Config.from_env()
    now = time.time() if now is None else now
    if cfg.disabled():
        return allow("disabled")
    cwd = hook_input.get("cwd") or ""
    if not paths.cwd_inside_alignment(cwd, cfg):
        return allow("outside-alignment")
    session_id = hook_input.get("session_id")
    if not session_id:
        raise ValueError("hook input has no session_id")
    kind = tool_kind(hook_input.get("tool_name") or "")
    if kind not in ("agent", "bash", "message"):
        return decide(hook_input, None, None, cfg, tool, now)
    if kind == "bash":
        d = guard_bash(bash_command(hook_input.get("tool_input")), cwd, cfg)
        if d:
            return d
    current = state.load_session(cfg, tool, session_id)
    read = reader or (lambda c, t, n, s: usage.read(c, t, n, s))
    probe = dict(current) if isinstance(current, dict) else {}
    reading = read(cfg, tool, now, probe)
    codex_cache = probe.get("codex_cache")

    def apply(session):
        if tool == "codex" and codex_cache is not None:
            session["codex_cache"] = codex_cache
        usage.apply_reading(session, reading, now)

    session, _, _ = state.update_session(cfg, tool, session_id, apply, now, cwd=cwd)
    return decide(hook_input, session, reading, cfg, tool, now)


def safe_evaluate(hook_input, tool="claude", cfg=None, now=None, reader=None, evaluator=None):
    """Fail closed for new spend, open for the rest (spec 5.2)."""
    try:
        return (evaluator or evaluate)(hook_input, tool=tool, cfg=cfg, now=now, reader=reader)
    except Exception as exc:
        try:
            kind = tool_kind((hook_input or {}).get("tool_name") or "")
            spend = is_spend(kind, (hook_input or {}).get("tool_input"))
        except Exception:
            spend = True
        if spend:
            return deny("gate-error", reason_gate_error(exc))
        return allow("gate-error-open")


def hook_output(decision):
    """PreToolUse JSON for a denial; None (no output, exit 0) for an allow."""
    if decision.allow:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": decision.reason}}
