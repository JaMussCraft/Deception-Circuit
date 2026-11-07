"""``audit-scan``: counts from Claude transcripts and Codex rollouts for the pilot and later audits (ticket 11).

Read-only. It never opens a file for writing, which is why the gate lists it among the read-only subcommands that may
name a direction's ``state.json`` (spec 5.2 step 1).

Inputs are paths. A Claude main transcript ``<session>.jsonl`` also brings in ``<session>/subagents/agent-*.jsonl``
unless ``--no-subagents`` is given; a directory brings in every ``*.jsonl`` under it. Each file is scanned once.

Claude format, as seen in a key-only inspection of real transcripts (hand-back 11):

- Records with a top-level ``agentId`` belong to that subagent; the rest belong to ``main``.
- A compaction is a ``system`` record with ``subtype: compact_boundary`` and ``compactMetadata`` holding ``trigger``,
  ``preTokens`` and ``postTokens``. ``isCompactSummary`` records are counted separately (lane 4 rubric check 1).
- Tool calls are ``tool_use`` blocks in ``assistant`` records; results are ``tool_result`` blocks in ``user`` records.
  ``api-request-blob`` records repeat earlier blocks, so only ``assistant`` and ``user`` records are read, and blocks
  are deduplicated by id.
- A denial is a ``user`` record with a top-level ``toolDenialKind`` or a ``permissionDecision`` whose ``decision`` is
  ``reject``.
- A subagent's ``agent-<id>.meta.json`` gives ``agentType`` and ``model``; no other meta key is read.

Codex format: rollouts hold one ``session_meta`` record, ``compacted`` records (with ``window_number`` and, when
present, ``latest_token_usage_record.usage.input_tokens``, the input size of the last request before compaction) and
``response_item`` function calls; ``spawn_agent`` carries its options as a JSON string in ``arguments``.

Rules:

- **Failing run.** Three or more consecutive tool calls of one agent with the same tool name and the same canonical
  JSON input, each answered by a ``tool_result`` with ``is_error: true``. A different call in between ends the run.
- **Bash repeat.** Five or more Bash calls of one agent with the same command (surrounding whitespace removed) whose
  timestamps fit in a 30-minute window. ``count`` is the largest number in any such window and ``total`` all calls.
- **Agent call without model.** An ``Agent`` or ``Task`` call whose input has no non-empty ``model`` (Claude), or a
  ``spawn_agent`` call whose arguments have none (Codex).

Echoed text (commands, inputs) is whitespace-collapsed, cut to 200 characters and passed through the lint's secret
patterns. Message text, prompts and descriptions are never echoed.
"""

import datetime
import glob
import json
import os
import re
import sys

from research_session import lint as _lint
from research_session import paths

FAILING_RUN_MIN = 3
BASH_REPEAT_MIN = 5
BASH_WINDOW_SECONDS = 30 * 60
ECHO_MAX = 200
AGENT_TOOLS = ("Agent", "Task")
CODEX_TYPES = frozenset(["session_meta", "response_item", "event_msg", "compacted", "turn_context", "world_state",
                         "token_usage_record", "inter_agent_communication_metadata"])
_FRACTION_RE = re.compile(r"\.(\d+)")


# ---------------------------------------------------------------------------------------------------------------
# Small helpers


def parse_time(value):
    """Epoch seconds of an ISO timestamp such as ``2026-10-31T16:00:00.123Z``; None when unparseable.

    Python 3.9's ``fromisoformat`` rejects ``Z`` and fractions that are not 3 or 6 digits, so both are normalised.
    """
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if text.endswith("Z") or text.endswith("z"):
        text = text[:-1] + "+00:00"
    text = _FRACTION_RE.sub(lambda m: "." + (m.group(1) + "000000")[:6], text, count=1)
    try:
        dt = datetime.datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.timestamp()


def show_time(value):
    """The time in America/New_York (R22) when parseable, else the raw value."""
    t = parse_time(value)
    return paths.iso(t) if t is not None else value


def redact(text):
    for kind, pattern in _lint.SECRET_PATTERNS:
        text = pattern.sub("[redacted %s]" % kind, text)
    return text


def echo(text):
    """Collapse whitespace, redact secrets, cut to ``ECHO_MAX`` characters."""
    text = redact(" ".join(str(text).split()))
    return text if len(text) <= ECHO_MAX else text[: ECHO_MAX - 3] + "..."


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError):
        return repr(value)


def iter_records(path, stats):
    """Yield each parsable JSON object of a JSONL file; count unparsable lines in ``stats``."""
    with open(path, "rb") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            stats["records"] += 1
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                stats["unparsable"] += 1
                continue
            if isinstance(rec, dict):
                yield rec
            else:
                stats["unparsable"] += 1


def detect_format(path):
    """``claude`` or ``codex`` from the first parsable record; ``claude`` when unclear."""
    try:
        with open(path, "rb") as fh:
            for n, raw in enumerate(fh):
                if n > 50:
                    break
                try:
                    rec = json.loads(raw.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if isinstance(rec, dict):
                    if "payload" in rec and rec.get("type") in CODEX_TYPES and "sessionId" not in rec:
                        return "codex"
                    return "claude"
    except (IOError, OSError):
        raise
    return "claude"


def read_meta(path):
    """``(agentType, model)`` from a subagent's ``.meta.json`` next to its transcript, else ``(None, None)``."""
    if not path.endswith(".jsonl"):
        return None, None
    meta = path[: -len(".jsonl")] + ".meta.json"
    try:
        with open(meta, "rb") as fh:
            data = json.loads(fh.read().decode("utf-8", "replace"))
    except (IOError, OSError, ValueError):
        return None, None
    if not isinstance(data, dict):
        return None, None
    keep = lambda v: v if isinstance(v, str) and len(v) <= 80 else None  # noqa: E731
    return keep(data.get("agentType")), keep(data.get("model"))


# ---------------------------------------------------------------------------------------------------------------
# Claude


def _new_claude_agent(path, agent):
    return {"tool": "claude", "file": path, "agent": agent, "session_id": None, "agent_type": None,
            "meta_model": None, "_calls": [], "_seen_calls": set(), "_results": {}, "_denials": [],
            "_denied_ids": set(), "compactions": [], "compact_summaries": 0}


def _content_blocks(rec):
    msg = rec.get("message")
    if isinstance(msg, dict) and isinstance(msg.get("content"), list):
        return [b for b in msg["content"] if isinstance(b, dict)]
    return []


def scan_claude(path, stats):
    agents = {}
    for rec in iter_records(path, stats):
        name = rec.get("agentId") if isinstance(rec.get("agentId"), str) and rec.get("agentId") else "main"
        a = agents.get(name)
        if a is None:
            a = agents[name] = _new_claude_agent(path, name)
        sid = rec.get("sessionId") or rec.get("session_id")
        if a["session_id"] is None and isinstance(sid, str):
            a["session_id"] = sid
        kind = rec.get("type")
        when = rec.get("timestamp")
        if rec.get("subtype") == "compact_boundary":
            md = rec.get("compactMetadata") if isinstance(rec.get("compactMetadata"), dict) else {}
            a["compactions"].append({"at": show_time(when), "trigger": md.get("trigger"),
                                     "preTokens": md.get("preTokens"), "postTokens": md.get("postTokens")})
        if rec.get("isCompactSummary"):
            a["compact_summaries"] += 1
        if kind == "assistant":
            for b in _content_blocks(rec):
                if b.get("type") == "tool_use" and b.get("id") not in a["_seen_calls"]:
                    a["_seen_calls"].add(b.get("id"))
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    a["_calls"].append({"id": b.get("id"), "name": b.get("name"), "input": inp, "when": when})
        elif kind == "user":
            results = [b for b in _content_blocks(rec) if b.get("type") == "tool_result"]
            for b in results:
                tid = b.get("tool_use_id")
                if tid not in a["_results"]:
                    a["_results"][tid] = bool(b.get("is_error"))
            pd = rec.get("permissionDecision")
            rejected = isinstance(pd, dict) and pd.get("decision") == "reject"
            if "toolDenialKind" in rec or rejected:
                if isinstance(rec.get("toolDenialKind"), str) and rec.get("toolDenialKind"):
                    why = rec["toolDenialKind"]
                else:
                    why = "reject:%s" % (pd.get("source") if isinstance(pd, dict) else "unknown")
                for tid in [b.get("tool_use_id") for b in results] or [None]:
                    key = tid if tid is not None else rec.get("uuid")
                    if key in a["_denied_ids"]:
                        continue
                    a["_denied_ids"].add(key)
                    a["_denials"].append({"at": show_time(when), "kind": echo(why), "tool_use_id": tid})
    out = []
    for name in sorted(agents, key=lambda n: (n != "main", n)):
        out.append(_finish_claude(agents[name]))
    return out


def _signature(call):
    return call["name"], canonical(call["input"])


def _input_echo(call):
    inp = call["input"]
    if call["name"] == "Bash" and isinstance(inp.get("command"), str):
        return echo(inp["command"])
    return echo(canonical(inp))


def failing_runs(calls, results):
    runs = []
    current = []

    def close():
        if len(current) >= FAILING_RUN_MIN:
            first, last = current[0], current[-1]
            runs.append({"tool": first["name"], "input": _input_echo(first), "count": len(current),
                         "first_at": show_time(first["when"]), "last_at": show_time(last["when"]),
                         "tool_use_ids": [c["id"] for c in current]})

    for call in calls:
        failed = results.get(call["id"]) is True
        if failed and current and _signature(current[-1]) == _signature(call):
            current.append(call)
            continue
        close()
        current = [call] if failed else []
    close()
    return runs


def bash_repeats(calls):
    groups = {}
    for call in calls:
        if call["name"] != "Bash":
            continue
        cmd = call["input"].get("command")
        if not isinstance(cmd, str) or not cmd.strip():
            continue
        groups.setdefault(cmd.strip(), []).append(call)
    out = []
    for cmd, group in groups.items():
        timed = sorted((parse_time(c["when"]), c["when"]) for c in group if parse_time(c["when"]) is not None)
        best, best_span = 0, None
        i = 0
        for j in range(len(timed)):
            while timed[j][0] - timed[i][0] > BASH_WINDOW_SECONDS:
                i += 1
            if j - i + 1 > best:
                best, best_span = j - i + 1, (timed[i][1], timed[j][1])
        if best >= BASH_REPEAT_MIN:
            out.append({"command": echo(cmd), "count": best, "total": len(group),
                        "first_at": show_time(best_span[0]), "last_at": show_time(best_span[1])})
    out.sort(key=lambda r: (-r["count"], r["command"]))
    return out


def _finish_claude(a):
    calls, results = a["_calls"], a["_results"]
    names = dict((c["id"], c["name"]) for c in calls)
    without_model = []
    for c in calls:
        if c["name"] in AGENT_TOOLS:
            model = c["input"].get("model")
            if not (isinstance(model, str) and model.strip()):
                without_model.append({"at": show_time(c["when"]), "tool_use_id": c["id"], "tool": c["name"],
                                      "subagent_type": echo(c["input"].get("subagent_type") or "") or None,
                                      "name": echo(c["input"].get("name") or "") or None})
    for d in a["_denials"]:
        d["tool"] = names.get(d["tool_use_id"])
    compactions = a["compactions"]
    return {
        "tool": "claude", "file": a["file"], "agent": a["agent"], "session_id": a["session_id"],
        "agent_type": a["agent_type"], "meta_model": a["meta_model"],
        "compactions": compactions, "compaction_count": len(compactions),
        "first_compaction_preTokens": compactions[0]["preTokens"] if compactions else None,
        "compact_summaries": a["compact_summaries"],
        "tool_calls": len(calls), "tool_errors": sum(1 for v in results.values() if v),
        "failing_runs": failing_runs(calls, results),
        "agent_calls": sum(1 for c in calls if c["name"] in AGENT_TOOLS),
        "agent_calls_without_model": without_model,
        "bash_repeats": bash_repeats(calls),
        "denials": a["_denials"],
    }


# ---------------------------------------------------------------------------------------------------------------
# Codex


def scan_codex(path, stats):
    a = {"tool": "codex", "file": path, "agent": "main", "session_id": None, "thread_id": None,
         "parent_thread_id": None, "compactions": [], "spawn_calls": 0, "agent_calls_without_model": []}
    meta_seen = False
    for rec in iter_records(path, stats):
        kind = rec.get("type")
        p = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
        when = rec.get("timestamp")
        if kind == "session_meta" and not meta_seen:
            meta_seen = True
            a["thread_id"] = p.get("id") if isinstance(p.get("id"), str) else None
            sid = p.get("session_id") or p.get("id")
            a["session_id"] = sid if isinstance(sid, str) else None
            parent = p.get("parent_thread_id")
            if isinstance(parent, str) and parent:
                a["parent_thread_id"] = parent
                a["agent"] = a["thread_id"] or "subagent"
        elif kind == "compacted":
            usage = (p.get("latest_token_usage_record") or {}) if isinstance(p.get("latest_token_usage_record"),
                                                                             dict) else {}
            last = usage.get("usage") if isinstance(usage.get("usage"), dict) else {}
            a["compactions"].append({"at": show_time(when), "window_number": p.get("window_number"),
                                     "last_input_tokens": last.get("input_tokens")})
        elif kind == "response_item" and p.get("type") == "function_call" and p.get("name") == "spawn_agent":
            a["spawn_calls"] += 1
            args = p.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except ValueError:
                    args = {}
            args = args if isinstance(args, dict) else {}
            model = args.get("model")
            if not (isinstance(model, str) and model.strip()):
                a["agent_calls_without_model"].append({
                    "at": show_time(when), "call_id": p.get("call_id"), "tool": "spawn_agent",
                    "agent_type": echo(args.get("agent_type") or "") or None})
    a["compacted"] = len(a["compactions"])
    a["compaction_count"] = a["compacted"]
    return [a]


# ---------------------------------------------------------------------------------------------------------------
# Paths, totals, state comparison


def expand(paths_in, subagents=True):
    """``(files, errors)``: transcript files in argument order, each real path once."""
    files, errors, seen = [], [], set()

    def add(p):
        rp = os.path.realpath(p)
        if rp not in seen:
            seen.add(rp)
            files.append(p)

    for p in paths_in:
        if os.path.isdir(p):
            for d, _, names in sorted(os.walk(p)):
                for n in sorted(names):
                    if n.endswith(".jsonl"):
                        add(os.path.join(d, n))
        elif os.path.isfile(p):
            add(p)
            if subagents and p.endswith(".jsonl"):
                for sub in sorted(glob.glob(os.path.join(p[: -len(".jsonl")], "subagents", "agent-*.jsonl"))):
                    add(sub)
        else:
            errors.append({"path": p, "error": "not a file or directory"})
    return files, errors


def totals(agents):
    t = {"agents": len(agents), "compactions": 0, "main_compactions": 0, "codex_compacted": 0,
         "compact_summaries": 0, "tool_calls": 0, "tool_errors": 0, "failing_runs": 0, "agent_calls_without_model": 0,
         "bash_repeats": 0, "denials": 0}
    for a in agents:
        t["compactions"] += a["compaction_count"]
        if a["agent"] == "main":
            t["main_compactions"] += a["compaction_count"]
        t["agent_calls_without_model"] += len(a["agent_calls_without_model"])
        if a["tool"] == "codex":
            t["codex_compacted"] += a["compacted"]
            continue
        t["compact_summaries"] += a["compact_summaries"]
        t["tool_calls"] += a["tool_calls"]
        t["tool_errors"] += a["tool_errors"]
        t["failing_runs"] += len(a["failing_runs"])
        t["bash_repeats"] += len(a["bash_repeats"])
        t["denials"] += len(a["denials"])
    return t


def compare_state(state_path, agents):
    """Compare each session's ``compactions`` in a direction ``state.json`` with its main transcript's count."""
    with open(state_path, "rb") as fh:
        data = json.loads(fh.read().decode("utf-8"))
    out = {}
    for tag, rec in sorted(((data or {}).get("sessions") or {}).items()):
        rec = rec if isinstance(rec, dict) else {}
        tool, sid = rec.get("tool"), rec.get("session_id")
        found = None
        for a in agents:
            if a["tool"] == tool and a["agent"] == "main" and sid and a["session_id"] == sid:
                found = (found or 0) + a["compaction_count"]
        n = rec.get("compactions")
        out[tag] = {"state": n, "transcript": found, "match": None if found is None else found == n}
    return out


def scan(paths_in, subagents=True, states=()):
    files, errors = expand(paths_in, subagents)
    file_rows, agents = [], []
    for path in files:
        stats = {"records": 0, "unparsable": 0}
        try:
            fmt = detect_format(path)
            found = scan_codex(path, stats) if fmt == "codex" else scan_claude(path, stats)
        except (IOError, OSError) as exc:
            errors.append({"path": path, "error": exc.strerror or str(exc)})
            continue
        if fmt == "claude":
            agent_type, model = read_meta(path)
            for a in found:
                if a["agent"] != "main":
                    a["agent_type"], a["meta_model"] = agent_type, model
        file_rows.append({"path": path, "format": fmt, "records": stats["records"],
                          "unparsable": stats["unparsable"]})
        agents.extend(found)
    report = {"schema": 1, "kind": "audit-scan",
              "rules": {"failing_run_min": FAILING_RUN_MIN, "bash_repeat_min": BASH_REPEAT_MIN,
                        "bash_window_minutes": BASH_WINDOW_SECONDS // 60, "echo_max_chars": ECHO_MAX},
              "files": file_rows, "agents": agents, "totals": totals(agents), "errors": errors}
    if states:
        report["state"] = {}
        for sp in states:
            try:
                report["state"][sp] = compare_state(sp, agents)
            except (IOError, OSError, ValueError) as exc:
                errors.append({"path": sp, "error": "state.json unreadable: %s" % (getattr(exc, "strerror", None)
                                                                                   or exc)})
    return report


def cmd_audit_scan(args):
    report = scan(args.paths, subagents=not args.no_subagents, states=args.state or ())
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
    return 2 if report["errors"] else 0


def add_parsers(sub):
    p = sub.add_parser("audit-scan", help="count compactions, failing runs, model omissions, polling and denials in "
                                          "transcripts (read-only; JSON on stdout)")
    p.add_argument("paths", nargs="+", metavar="transcript.jsonl",
                   help="Claude transcripts, Codex rollouts or directories of them")
    p.add_argument("--no-subagents", action="store_true",
                   help="do not add <session>/subagents/agent-*.jsonl for a main transcript")
    p.add_argument("--state", action="append", metavar="STATE_JSON",
                   help="compare each session's compactions in this state.json with the transcript (repeatable)")
    p.set_defaults(func=cmd_audit_scan)
