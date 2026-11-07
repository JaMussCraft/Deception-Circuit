"""Hook entry points for Claude Code and Codex (spec 5.1, ticket 06).

Every hook command is the literal shell guard of spec 5.1, which ends in
``cli.py hook <event> --tool <claude|codex>``. ``cli.main`` hands those arguments to ``main`` here before it builds
its own parser, so no argparse error can ever exit 2 (exit 2 from PreToolUse would block the tool call).

Events (the CLI ``<event>`` argument) and the hooks of spec 5.1 they serve:

=====================  ==========================================================================================
``session-start``      H-a for source ``startup`` or ``resume``; H-b for source ``compact``. Other sources no-op.
``post-compact``       H-c (Claude only): save ``compact_summary``; never counts, never blocks.
``pre-tool-use``       H-d: the usage gate of ``gate.py``; for Codex ``apply_patch`` the patch is split per file and
                       each file runs the Write guard (state files, glue lint, secret scan).
``post-tool-use``      H-e for Agent spawns (reading and checkpoint context); H-f for Write, Edit and Codex
                       ``apply_patch`` (advice only: lint problems elsewhere in the file).
``user-prompt-submit`` H-g: human acknowledgement by "continue"; the freeze notice otherwise.
``subagent-start``     H-h: record the start time; inject the hand-back convention in registered sessions.
``subagent-stop``      H-i: save the last message; block once when no hand-back file changed, or when the newest
                       changed hand-back has no terminal ``Status:`` (missing, placeholder, or not terminal).
``stop``               H-j: remind about a crossed, unrecorded checkpoint; never blocks.
=====================  ==========================================================================================

Rules shared by every hook:

- Kill switch present, or the realpath of ``cwd`` outside the Alignment root: exit 0 and no output. The one
  exception is Codex ``subagent-stop`` and ``stop``, which always print a JSON object (``{}`` when silent), because
  the Codex docs call plain text invalid for those events.
- Any exception exits 0. PreToolUse keeps the gate's own fail-closed rule (``gate.safe_evaluate``): a gate error
  denies Agent and ``sbatch`` and allows everything else. Errors are appended to ``<state root>/hook-errors.log``.
- Only registered sessions get checkpoint text, hand-back injection and the SubagentStop block (R5). Any session
  inside A gets its counters, its compaction count and the saved subagent messages.
"""

import json
import os
import re
import sys
import time
import traceback

from research_session import gate, paths, state, usage
from research_session import lint as _lint

TOOLS = ("claude", "codex")
EVENTS = ("session-start", "post-compact", "pre-tool-use", "post-tool-use", "user-prompt-submit", "subagent-start",
          "subagent-stop", "stop")
JSON_ALWAYS = {("codex", "subagent-stop"), ("codex", "stop")}

MAX_START = 600       # H-a: at most 600 characters (spec 5.1)
MAX_CONTEXT = 600     # every other injected text
MAX_COMPACT = 1000    # H-b names the direction directory and two lint results
MAX_REASON = gate.MAX_REASON
MAX_LINT_UNITS = 3    # lint findings named in H-b and H-f text
MAX_LINT_BYTES = 2 * 1024 * 1024
ERROR_LOG_MAX = 256 * 1024

SKIP_AGENT_TYPES = frozenset(["Explore", "Plan", "claude-code-guide", "statusline-setup"])
ENVELOPES = ("<teammate-message", "<agent-message", "<cross-session-message", "<task-notification")
ACK_RE = re.compile(r"continue\b", re.IGNORECASE)
WRITE_POST_TOOLS = frozenset(["Write", "Edit", "MultiEdit", "apply_patch"])
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


# ---------------------------------------------------------------------------------------------------------------
# Small helpers


def clip(text, limit=MAX_CONTEXT):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def context_output(event_name, text):
    return {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": text}}


def safe_name(text, default="unknown"):
    name = SAFE_NAME_RE.sub("-", str(text or "")).strip("-.")
    return name[:80] or default


def redact(text):
    """Replace every secret-pattern match of the lint with a marker, so a saved file never holds a token."""
    for kind, pattern in _lint.SECRET_PATTERNS:
        text = pattern.sub("[redacted %s]" % kind, text)
    return text


def active(cfg, data):
    """False when the kill switch exists or the realpath of ``cwd`` is outside A (spec 5.1)."""
    if cfg.disabled():
        return False
    return paths.cwd_inside_alignment(data.get("cwd") or "", cfg)


def direction_dir(session):
    """The registered direction's directory (the parent of the mirrored state.json), when it exists."""
    reg = (session or {}).get("register") or {}
    sp = reg.get("state_path")
    if not reg.get("slug") or not sp:
        return None
    d = os.path.dirname(sp)
    return d if os.path.isdir(d) else None


def fallback_dir(cfg, tool, session_id):
    """Private home for saved text of sessions without a direction: ``<state root>/handbacks/<tool>-<id>``."""
    return os.path.join(cfg.state_root, "handbacks", "%s-%s" % (tool, safe_name(session_id)))


def write_text_new(directory, base, text, private):
    """Write ``text`` to ``directory/base`` without overwriting: ``x.md``, then ``x.2.md``, ``x.3.md`` and so on.

    ``private`` files (under the state root) get modes 0700 and 0600; files in a direction get 0770 and 0660.
    """
    mode = 0o600 if private else 0o660
    paths.ensure_dir(directory, 0o700 if private else 0o770)
    stem, ext = os.path.splitext(base)
    n = 1
    while True:
        name = base if n == 1 else "%s.%d%s" % (stem, n, ext)
        path = os.path.join(directory, name)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        except FileExistsError:
            n += 1
            continue
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        return path


def pending_freeze(session):
    u = (session or {}).get("usage") or {}
    f = u.get("freeze")
    if f and f.get("checkpoint", 0) > u.get("acked_through", 0):
        return f
    return None


def lint_findings(path, text, alignment_root):
    """Glue lint and secret scan for files in the glue scope; secret scan alone elsewhere under A."""
    if _lint.glue_in_scope(path, alignment_root):
        return _lint.lint_text(text, glue=True, secrets=True)
    if _lint.secret_in_scope(path, alignment_root):
        return _lint.lint_text(text, glue=False, secrets=True)
    return []


def describe_findings(findings, limit=MAX_LINT_UNITS):
    parts = ["line %d %s: %s" % (f.line, f.rule, f.excerpt) for f in findings[:limit]]
    more = len(findings) - limit
    if more > 0:
        parts.append("%d more" % more)
    return "; ".join(parts)


def lint_status(path, alignment_root):
    if not os.path.isfile(path):
        return "missing"
    try:
        findings = _lint.lint_file(path, glue=True, secrets=True)
    except (IOError, OSError):
        return "unreadable"
    if not findings:
        return "lint clean"
    return "lint: %d failing unit%s, %s" % (len(findings), "" if len(findings) == 1 else "s",
                                           describe_findings(findings, 1))


def points_since_register(u):
    return (u.get("session_points") or 0) - (u.get("points_at_register") or 0)


def checkpoint_line(session):
    """Freeze state, or the next checkpoint, of a registered session."""
    u = session["usage"]
    f = pending_freeze(session)
    since = usage._fmt(points_since_register(u))
    if f:
        if f.get("stage") == "recorded":
            return ("Freeze: checkpoint %d is recorded and waits for the user; new agents and sbatch are held until "
                    "the user replies `continue` or runs `! research-session usage-ack`." % f["checkpoint"])
        return ("Freeze: checkpoint %d crossed (+%s points since register); new agents and sbatch are held. Record it "
                "with `research-session worklog-append <dir> --kind checkpoint --checkpoint %d`, send HOLD to workers "
                "and end the turn." % (f["checkpoint"], since, f["checkpoint"]))
    n = u.get("next_checkpoint", 1)
    return "Freeze: none. Next checkpoint %d at +%s points since register (now +%s)." % (
        n, usage._fmt(n * (u.get("cadence") or 0)), since)


def reading_line(reading):
    if reading.get("known"):
        return "Usage: %s." % usage.format_reading(reading)
    why = reading.get("error") or "no reading yet"
    return "Usage: unknown (%s); the gate refreshes it before the next spawn." % clip(why, 120)


def last_reading_view(session, tool):
    """A reading dict built from the session's ``last_reading``, written by the preceding gate call (no I/O)."""
    last = ((session or {}).get("usage") or {}).get("last_reading") or {}
    r = usage.empty_reading(tool, "session file")
    if not last:
        r["error"] = "no reading recorded in this session yet"
        return r
    five, seven, fable = last.get("five_hour"), last.get("seven_day"), last.get("fable")
    r.update(five_hour=five, seven_day=seven, fable=fable, known=bool(last.get("fresh")))
    if tool == "codex":
        r["w"] = seven
    else:
        r["five_hour_missing"] = five is None and bool(last.get("fresh"))
        if seven is not None and fable is not None:
            r["w"] = max(seven, fable)
            r["fable_gap"] = fable - seven
    if not r["known"]:
        r["error"] = "the last reading was stale or unknown"
    return r


def quiet_reading(cfg, tool, now, session):
    """A reading for SessionStart that never fetches: Claude reads usage.json only; Codex uses a fresh cache only."""
    if tool == "codex":
        cache = (session or {}).get("codex_cache")
        if isinstance(cache, dict) and isinstance(cache.get("at"), (int, float)) and \
                0 <= now - cache["at"] < usage.CODEX_CACHE_SECONDS:
            reading, _ = usage.read_codex(cfg, now, cache)
            return reading
        r = usage.empty_reading("codex", cfg.codex_usage)
        r["error"] = "no recent Codex reading"
        return r
    return usage.read_claude(cfg, now, refresh=False)


# ---------------------------------------------------------------------------------------------------------------
# H-a and H-b: SessionStart


def session_start(ctx):
    source = ctx.data.get("source")
    if source == "compact":
        return compaction(ctx)
    if source not in ("startup", "resume"):
        return None
    cfg, now, tool, data = ctx.cfg, ctx.now, ctx.tool, ctx.data
    current = state.load_session(cfg, tool, ctx.session_id) or {}
    reading = quiet_reading(cfg, tool, now, current)

    def apply(s):
        if data.get("model") and (source == "startup" or not s.get("orchestrator_model")):
            s["orchestrator_model"] = data["model"]
        usage.apply_reading(s, reading, now)

    session, _, _ = state.update_session(cfg, tool, ctx.session_id, apply, now, cwd=ctx.cwd)
    slug, how = state.resolve_direction(cfg, session)
    parts = ["research-session: session %s." % session["tag"]]
    if how == "register":
        d = direction_dir(session)
        parts.append("Direction: %s, registered%s." % (slug, "; <dir> is %s" % d if d else ""))
        parts.append(checkpoint_line(session))
    else:
        if how == "cwd":
            parts.append("Direction: %s by cwd match, attribution only; not registered." % slug)
        else:
            parts.append("Direction: none; not registered.")
        parts.append("This session gets only the cap and stale gates, no checkpoints. To get checkpoints, run "
                     "`research-session register %s`." % (slug or "<slug>"))
    parts.append(reading_line(reading))
    notice = usage.fable_notice(reading)
    if notice:
        parts.append(notice)
    return context_output("SessionStart", clip(" ".join(parts), MAX_START))


def compaction(ctx):
    """H-b: the only place that counts compactions."""
    cfg, now, tool = ctx.cfg, ctx.now, ctx.tool

    def apply(s):
        s["compactions"] = int(s.get("compactions") or 0) + 1
        n = s["compactions"]
        trigger = None
        for rec in s.get("compaction_summaries") or []:
            if rec.get("n") == n:
                trigger = rec.get("trigger")
        s.setdefault("compaction_log", []).append({"n": n, "at": paths.iso(now), "trigger": trigger})
        return n

    session, n, _ = state.update_session(cfg, tool, ctx.session_id, apply, now, cwd=ctx.cwd)
    d = direction_dir(session)
    parts = ["research-session: compaction #%d recorded for session %s." % (n, session["tag"])]
    if d:
        parts.append("Write a 'Resumed after compaction #%d' worklog entry; do not restart finished work. Use "
                     "`research-session worklog-append <dir> --kind compaction`, where <dir> is %s." % (n, d))
        parts.append("Re-read <dir>/RESUME.md (%s) and <dir>/WORKLOG.md (%s) before acting." % (
            lint_status(os.path.join(d, "RESUME.md"), cfg.alignment_root),
            lint_status(os.path.join(d, "WORKLOG.md"), cfg.alignment_root)))
    else:
        parts.append("No direction is registered, so there is no RESUME or WORKLOG to name. Re-read your notes and "
                     "the latest hand-backs before acting; do not restart finished work.")
    f = pending_freeze(session)
    if f:
        parts.append(checkpoint_line(session))
    return context_output("SessionStart", clip(" ".join(parts), MAX_COMPACT))


# ---------------------------------------------------------------------------------------------------------------
# H-c: PostCompact (Claude)


def post_compact(ctx):
    if ctx.tool != "claude" or ctx.data.get("agent_id"):
        return None  # Codex PostCompact has no summary; subagent compactions are not the session's count
    cfg, now, tool, data = ctx.cfg, ctx.now, ctx.tool, ctx.data
    summary = data.get("compact_summary")
    trigger = data.get("trigger") if data.get("trigger") in ("manual", "auto") else None

    def apply(s):
        lst = s.setdefault("compaction_summaries", [])
        n = len(lst) + 1
        lst.append({"n": n, "at": paths.iso(now), "trigger": trigger, "path": None})
        for rec in s.get("compaction_log") or []:
            if rec.get("n") == n and not rec.get("trigger"):
                rec["trigger"] = trigger
        return n

    session, n, _ = state.update_session(cfg, tool, ctx.session_id, apply, now, cwd=ctx.cwd)
    if not isinstance(summary, str) or not summary.strip():
        return None
    d = direction_dir(session)
    target = os.path.join(d, "handbacks") if d else fallback_dir(cfg, tool, ctx.session_id)
    text = "# Compaction %d summary (%s, %s)\n\n%s\n" % (n, trigger or "unknown trigger", paths.iso(now),
                                                        redact(summary).rstrip())
    path = write_text_new(target, "compaction-%d.md" % n, text, private=not d)

    def note(s):
        for rec in s.get("compaction_summaries") or []:
            if rec.get("n") == n:
                rec["path"] = path

    state.update_session(cfg, tool, ctx.session_id, note, now, cwd=ctx.cwd)
    return None


# ---------------------------------------------------------------------------------------------------------------
# H-d: PreToolUse


def parse_patch(text):
    """Split a Codex ``apply_patch`` body into ``[(action, path, move_to, added_text)]``.

    Grammar: ``*** Begin Patch``, then hunks ``*** Add File: p`` (``+`` lines), ``*** Delete File: p`` and
    ``*** Update File: p`` (optional ``*** Move to: q``, ``@@`` context markers, ``+``, ``-`` and space lines),
    then ``*** End Patch`` (codex-rs/apply-patch/src/parser.rs). Added text keeps one blank line between hunks, so
    the lint never joins two hunks into one unit.
    """
    files = []
    cur = None
    for line in (text or "").splitlines():
        if line.startswith("*** Add File: "):
            cur = ["add", line[len("*** Add File: "):].strip(), None, []]
            files.append(cur)
        elif line.startswith("*** Update File: "):
            cur = ["update", line[len("*** Update File: "):].strip(), None, []]
            files.append(cur)
        elif line.startswith("*** Delete File: "):
            files.append(["delete", line[len("*** Delete File: "):].strip(), None, []])
            cur = None
        elif line.startswith("*** Move to: ") and cur is not None:
            cur[2] = line[len("*** Move to: "):].strip()
        elif line.startswith("*** "):
            continue  # Begin Patch, End Patch, End of File, Environment ID
        elif cur is not None and line.startswith("@@"):
            if cur[3] and cur[3][-1] != "":
                cur[3].append("")
        elif cur is not None and line.startswith("+"):
            cur[3].append(line[1:])
        elif cur is not None and line[:1] in ("-", " ") and cur[3] and cur[3][-1] != "":
            cur[3].append("")  # a removed or context line ends the run of added lines
    return [(a, p, m, "\n".join(lines).strip("\n") + ("\n" if lines else "")) for a, p, m, lines in files]


def patch_text(tool_input):
    ti = tool_input or {}
    for key in ("command", "patch", "input"):
        v = ti.get(key)
        if isinstance(v, list):
            v = "\n".join(str(x) for x in v)
        if isinstance(v, str) and "*** Begin Patch" in v:
            return v
    return ""


def guard_patch(data, tool, cfg):
    """Run the Write guard of ``gate.py`` on every file of a Codex ``apply_patch`` call; the first denial wins."""
    if not active(cfg, data):
        return gate.allow("inactive")
    cwd = data.get("cwd") or ""
    for action, path, move_to, added in parse_patch(patch_text(data.get("tool_input"))):
        for target in [p for p in (path, move_to) if p]:
            content = added if action != "delete" else ""
            d = gate.guard_write("Write", {"file_path": target, "content": content}, cwd, cfg)
            if d:
                return d
    return gate.allow("patch")


def pre_tool_use(ctx):
    data = ctx.data
    if data.get("tool_name") == "apply_patch":
        try:
            d = guard_patch(data, ctx.tool, ctx.cfg)
        except Exception as exc:  # a write is not new spend: fail open, as the gate does
            log_error(ctx.cfg, "pre-tool-use apply_patch", exc)
            d = gate.allow("patch-error-open")
    else:
        d = gate.safe_evaluate(data, tool=ctx.tool, cfg=ctx.cfg, now=ctx.now)
    return gate.hook_output(d)


# ---------------------------------------------------------------------------------------------------------------
# H-e and H-f: PostToolUse


def post_agent(ctx):
    session = state.load_session(ctx.cfg, ctx.tool, ctx.session_id)
    if not session:
        return None
    reading = last_reading_view(session, ctx.tool)
    parts = ["research-session after spawn: %s" % reading_line(reading)]
    if state.is_registered(session):
        u = session["usage"]
        parts.append("Session points +%s since register." % usage._fmt(points_since_register(u)))
        parts.append(checkpoint_line(session))
    else:
        parts.append("Not registered, so no checkpoints.")
    notice = usage.fable_notice(reading)
    if notice:
        parts.append(notice)
    return context_output("PostToolUse", clip(" ".join(parts), MAX_CONTEXT))


def _covered_lines(text, snippets):
    """Line ranges (1-based, inclusive) that the just-written snippets occupy in ``text``."""
    ranges = []
    for snip in snippets:
        snip = (snip or "").strip("\n")
        if not snip:
            continue
        start = 0
        while True:
            i = text.find(snip, start)
            if i < 0:
                break
            first = text.count("\n", 0, i) + 1
            ranges.append((first, first + snip.count("\n")))
            start = i + max(len(snip), 1)
    return ranges


def advise_file(path, snippets, cfg):
    """Lint findings in ``path`` outside the just-written snippets, or an empty list."""
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > MAX_LINT_BYTES:
            return []
        text = _lint.read_text(path)
    except (IOError, OSError):
        return []
    findings = lint_findings(path, text, cfg.alignment_root)
    ranges = _covered_lines(text, snippets)
    return [f for f in findings if not any(a <= f.line <= b for a, b in ranges)]


def post_write(ctx):
    data, cfg = ctx.data, ctx.cfg
    tool_name = data.get("tool_name")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or ""
    targets = []
    if tool_name == "apply_patch":
        for action, path, move_to, added in parse_patch(patch_text(ti)):
            if action == "update":
                targets.append((gate._abs(move_to or path, cwd), [b for b in added.split("\n\n")]))
    elif tool_name in ("Edit", "MultiEdit"):
        target = gate.write_target(ti)
        if target:
            snippets = [e.get("new_string", "") for e in (ti.get("edits") or []) if isinstance(e, dict)] \
                if tool_name == "MultiEdit" else [ti.get("new_string") or ""]
            targets.append((gate._abs(target, cwd), snippets))
    # A Write replaces the whole file, and H-d linted that whole text before the write: nothing to add.
    notes = []
    for path, snippets in targets:
        if not paths.is_within(path, cfg.alignment_root):
            continue
        findings = advise_file(path, snippets, cfg)
        if findings:
            notes.append("%s: %s" % (os.path.basename(path), describe_findings(findings)))
    if not notes:
        return None
    text = ("Lint advice (the write already happened and is not undone): problems outside the text you just wrote "
            "in %s. Fix them with a follow-up edit, or through the RS command that owns the file." % "; ".join(notes))
    return context_output("PostToolUse", clip(text, MAX_CONTEXT))


def post_tool_use(ctx):
    name = ctx.data.get("tool_name") or ""
    if name in gate.AGENT_TOOLS:
        return post_agent(ctx)
    if name in WRITE_POST_TOOLS:
        return post_write(ctx)
    return None


# ---------------------------------------------------------------------------------------------------------------
# H-g: UserPromptSubmit


def prompt_acks(prompt):
    """A human "continue" (R36): starts with the word after whitespace, no envelope, no leading ``<``, not a question."""
    if not isinstance(prompt, str):
        return False
    text = prompt.strip()
    if not text or text.startswith("<"):
        return False
    if any(env in prompt for env in ENVELOPES):
        return False
    if text.endswith("?"):
        return False
    return bool(ACK_RE.match(text))


def user_prompt_submit(ctx):
    cfg, now, tool, data = ctx.cfg, ctx.now, ctx.tool, ctx.data
    current = state.load_session(cfg, tool, ctx.session_id)
    if not state.is_registered(current) or not pending_freeze(current):
        return None
    if not data.get("agent_id") and prompt_acks(data.get("prompt")):
        session, n, _ = state.update_session(cfg, tool, ctx.session_id, lambda s: state.ack(s, now, "prompt"),
                                             now, create=False)
        if n:
            return context_output("UserPromptSubmit", (
                "research-session: the user acknowledged checkpoint %d with `continue`. New agents and sbatch are "
                "allowed again; resume the plan in the checkpoint block." % n))
        return None
    f = pending_freeze(current)
    return context_output("UserPromptSubmit", (
        "Freeze holds; answer questions only. Checkpoint %d waits for the user's `continue` or "
        "`! research-session usage-ack`; start no new work." % f["checkpoint"]))


# ---------------------------------------------------------------------------------------------------------------
# H-h and H-i: SubagentStart and SubagentStop


def subagent_start(ctx):
    cfg, now, tool, data = ctx.cfg, ctx.now, ctx.tool, ctx.data
    agent_id = data.get("agent_id")
    if not agent_id:
        return None
    agent_type = data.get("agent_type") or "unknown"

    def apply(s):
        s.setdefault("agents", {})[agent_id] = {"agent_type": agent_type, "started_at": paths.iso(now),
                                                 "stop_blocks": 0}

    session, _, _ = state.update_session(cfg, tool, ctx.session_id, apply, now, cwd=ctx.cwd)
    d = direction_dir(session)
    if not state.is_registered(session) or not d or agent_type in SKIP_AGENT_TYPES:
        return None
    parts = ["research-session rules for this agent: before you stop, write your hand-back to a file whose name "
             "contains 'handback' under <dir>, for example <dir>/reports/<NN>-handback.md, with the spec 4.7 "
             "headings, and return a short pointer to it. <dir> is %s." % d,
             "Never run git; the orchestrator commits by explicit file list."]
    brief = os.path.join(d, "agent-brief.md")
    if os.path.isfile(brief):
        parts.append("Read the agent brief first: %s." % brief)
    return context_output("SubagentStart", clip(" ".join(parts), MAX_CONTEXT))


def changed_handbacks(d, since, exclude=()):
    """Files named ``*handback*.md`` anywhere under ``d`` with an mtime at or after ``since``, newest first."""
    skip = set(os.path.realpath(p) for p in exclude)
    found = []
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        for name in files:
            if "handback" in name and name.endswith(".md"):
                p = os.path.join(root, name)
                if os.path.realpath(p) in skip:
                    continue
                try:
                    mtime = os.path.getmtime(p)
                except OSError:
                    continue
                if mtime >= since:
                    found.append((mtime, p))
    return [p for _, p in sorted(found, reverse=True)]


def handback_changed(d, since, exclude=()):
    """True when a file named ``*handback*.md`` anywhere under ``d`` has an mtime at or after ``since``."""
    return bool(changed_handbacks(d, since, exclude))


# Hand-back Status vocabulary (ticket 12, H-i). The template line is "Status: <resolved / claimed, blocked on ...>".
# A Status passes when its first sentence names a terminal word and no placeholder. "claimed" alone is not terminal.
HANDBACK_TERMINAL = ("resolved", "blocked", "handed-back", "held", "done", "failed", "abandoned")
HANDBACK_PLACEHOLDERS = ("pending", "to be filled", "tbd", "in progress")
_STATUS_RE = re.compile(r"\bStatus:\**[ \t]*(.*)$", re.IGNORECASE | re.MULTILINE)
_TERMINAL_RE = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(w) for w in HANDBACK_TERMINAL), re.IGNORECASE)
_PLACEHOLDER_RE = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(w) for w in HANDBACK_PLACEHOLDERS), re.IGNORECASE)


def handback_status_problem(path):
    """None when the first ``Status:`` value of the hand-back at ``path`` is terminal, else a short description."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read(MAX_LINT_BYTES)
    except (IOError, OSError):
        return "could not be read"
    m = _STATUS_RE.search(text)
    if not m:
        return "has no Status: line"
    value = m.group(1).strip().strip("*").strip()
    first = re.split(r"\.(?:\s|$)", value, 1)[0].strip()
    placeholder = _PLACEHOLDER_RE.search(first)
    if placeholder:
        return "has a placeholder Status (\"%s\")" % placeholder.group(0)
    if not _TERMINAL_RE.search(first):
        return "has a Status that is not terminal (\"%s\")" % first[:60]
    return None


def subagent_stop(ctx):
    cfg, now, tool, data = ctx.cfg, ctx.now, ctx.tool, ctx.data
    agent_id = data.get("agent_id")
    agent_type = data.get("agent_type") or "unknown"
    if not agent_id or agent_type in SKIP_AGENT_TYPES:
        return None
    session = state.load_session(cfg, tool, ctx.session_id)
    d = direction_dir(session)
    saved = None
    message = data.get("last_assistant_message")
    if isinstance(message, str) and message.strip():
        target = os.path.join(d, "handbacks") if d else fallback_dir(cfg, tool, ctx.session_id)
        name = "%s-%s.md" % (safe_name(agent_type), safe_name(agent_id))
        text = "# Last message of %s %s (%s)\n\n%s\n" % (agent_type, agent_id, paths.iso(now), redact(message).rstrip())
        saved = write_text_new(target, name, text, private=not d)
    if not d or not state.is_registered(session) or data.get("stop_hook_active"):
        return None
    rec = (session.get("agents") or {}).get(agent_id)
    if not rec or int(rec.get("stop_blocks") or 0) >= 1:
        return None
    since = paths.parse_iso(rec.get("started_at"))
    if since is None:
        return None
    changed = changed_handbacks(d, since - 1, exclude=[saved] if saved else ())
    problem = handback_status_problem(changed[0]) if changed else None
    if changed and problem is None:
        return None

    def bump(s):
        r = (s.get("agents") or {}).get(agent_id)
        if not r or int(r.get("stop_blocks") or 0) >= 1:
            return False
        r["stop_blocks"] = int(r.get("stop_blocks") or 0) + 1
        return True

    _, bumped, _ = state.update_session(cfg, tool, ctx.session_id, bump, now, create=False)
    if not bumped:
        return None
    if changed:
        reason = ("Your hand-back %s %s. Finish the work you own, then set the Status: line to a terminal word: "
                  "resolved, blocked on <what>, handed-back, held after a HOLD, done, failed or abandoned. Never end a turn with "
                  "pending, to be filled, TBD or in progress. This reminder is sent once." % (changed[0], problem))
    else:
        reason = ("No hand-back file changed under <dir> since you started, where <dir> is %s. Write "
                  "<dir>/reports/<NN>-handback.md with the spec 4.7 headings (What changed, How verified, Execution "
                  "evidence, What is NOT done, Open questions), then stop. This reminder is sent once." % d)
    return {"decision": "block", "reason": clip(reason, MAX_CONTEXT)}


# ---------------------------------------------------------------------------------------------------------------
# H-j: Stop


def stop(ctx):
    data = ctx.data
    if data.get("stop_hook_active") or data.get("background_tasks") or data.get("session_crons"):
        return None
    session = state.load_session(ctx.cfg, ctx.tool, ctx.session_id)
    if not state.is_registered(session):
        return None
    f = pending_freeze(session)
    if not f or f.get("stage") != "crossed":
        return None
    d = direction_dir(session) or "<dir>"
    text = ("research-session: checkpoint %d crossed and is not recorded yet. Before ending the turn, run "
            "`research-session worklog-append %s --kind checkpoint --checkpoint %d --body <progress> --plan <plan>`, "
            "send HOLD to running workers, then end the turn." % (f["checkpoint"], d, f["checkpoint"]))
    text = clip(text, MAX_CONTEXT)
    if ctx.tool == "codex":
        return {"systemMessage": text}  # the Codex Stop schema has no additionalContext; never block
    return context_output("Stop", text)


# ---------------------------------------------------------------------------------------------------------------
# Dispatch


class Context(object):
    def __init__(self, event, tool, data, cfg, now):
        self.event = event
        self.tool = tool
        self.data = data
        self.cfg = cfg
        self.now = now
        self.cwd = data.get("cwd") or ""
        self.session_id = data.get("session_id")


HANDLERS = {
    "session-start": session_start,
    "post-compact": post_compact,
    "pre-tool-use": pre_tool_use,
    "post-tool-use": post_tool_use,
    "user-prompt-submit": user_prompt_submit,
    "subagent-start": subagent_start,
    "subagent-stop": subagent_stop,
    "stop": stop,
}


def log_error(cfg, where, exc):
    """Append one line and the traceback to ``<state root>/hook-errors.log``; never raises."""
    try:
        if not os.path.isdir(cfg.state_root):
            return
        path = os.path.join(cfg.state_root, "hook-errors.log")
        if os.path.exists(path) and os.path.getsize(path) > ERROR_LOG_MAX:
            os.replace(path, path + ".1")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a") as fh:
            fh.write("%s %s: %s: %s\n%s\n" % (paths.iso(time.time()), where, type(exc).__name__, exc,
                                              traceback.format_exc()))
    except Exception:
        pass


def parse_args(argv):
    """``<event> --tool <claude|codex>``, parsed by hand so a bad argument never exits 2."""
    argv = list(argv or [])
    event = argv[0] if argv else ""
    tool = "claude"
    for i, a in enumerate(argv[1:], 1):
        if a == "--tool" and i + 1 < len(argv):
            tool = argv[i + 1]
        elif a.startswith("--tool="):
            tool = a.split("=", 1)[1]
    return event, tool


def run(event, tool, raw, cfg=None, now=None):
    """Run one hook. Returns ``(exit_code, stdout_text)``; the exit code is always 0."""
    cfg = cfg or paths.Config.from_env()
    now = time.time() if now is None else now
    always_json = (tool, event) in JSON_ALWAYS
    silent = "{}\n" if always_json else ""
    if event not in HANDLERS or tool not in TOOLS:
        return 0, silent
    try:
        data = json.loads(raw) if raw and raw.strip() else {}
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    try:
        if not active(cfg, data):
            return 0, silent
        if event != "pre-tool-use" and not data.get("session_id"):
            return 0, silent
        result = HANDLERS[event](Context(event, tool, data, cfg, now))
    except Exception as exc:
        log_error(cfg, "%s --tool %s" % (event, tool), exc)
        if event == "pre-tool-use":
            d = gate.safe_evaluate(data, tool=tool, cfg=cfg, now=now,
                                   evaluator=lambda *a, **k: (_ for _ in ()).throw(exc))
            out = gate.hook_output(d)
            return 0, (json.dumps(out, sort_keys=True) + "\n") if out else ""
        return 0, silent
    if result is None:
        return 0, silent
    return 0, json.dumps(result, sort_keys=True) + "\n"


def main(argv=None, stdin=None, stdout=None):
    """Entry point for ``cli.py hook``. Never raises, never exits non-zero."""
    stdout = stdout or sys.stdout
    event, tool = "", ""
    try:
        event, tool = parse_args(argv)
        raw = (stdin or sys.stdin).read()
        code, out = run(event, tool, raw)
    except Exception:
        code, out = 0, "{}\n" if (tool, event) in JSON_ALWAYS else ""
    if out:
        stdout.write(out)
        stdout.flush()
    return code
