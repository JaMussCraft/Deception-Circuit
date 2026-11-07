"""Registry validators and renders (spec 4.1-4.5, 4.8, 6.4; R15-R17, R23, R29).

Validators return ``(errors, warnings)``, two lists of strings. ``validate <path>`` dispatches on the file name.
``render`` writes ``DIRECTIONS.md`` and ``SESSIONS.md``; ``ledger-rollup`` writes the global ``ledger.json``.
``claim`` and ``release`` edit ``directions.json`` (only the orchestrator runs them, R23).
"""

import glob
import json
import os
import re
import sys

from research_session import paths, records, state

DIRECTION_STATUS = ("proposed", "open", "claimed", "active", "paused", "done", "abandoned")
FINDING_STATUS = ("proposed", "executed", "reviewed", "verified", "replicated", "refuted", "superseded", "paused")
RESERVATION_STATUS = ("PLANNED", "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY")
JOB_STATUS = RESERVATION_STATUS + ("NODE_FAIL", "PREEMPTED", "UNKNOWN")
SESSION_STATE = ("running", "frozen", "paused", "blocked", "closed")
WORKLOG_STATE = ("Running", "Blocked: needs you", "Closed")
STRENGTH = ("preliminary", "reviewed", "final")
MAX_TERMS = 10

TAG_RE = re.compile(r"^(claude|codex)-[0-9a-f]{8}$")
FINDING_ID_RE = re.compile(r"^F-[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{3}$")
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
SHORT_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

DIRECTION_REQUIRED = ("id", "title", "status", "summary", "claimed_by", "claimed_at", "dir", "updated")
DIRECTION_OPTIONAL = ("status_source", "branch", "worktree", "spec", "resume", "worklog", "state", "ledger",
                      "frozen_grader_sha256", "parent_findings", "do_not_touch", "legacy_scratch", "archive")
LEDGER_KEYS = ("schema", "direction", "caps", "totals", "reservations", "api_calls", "converted_from")
CAP_KEYS = ("reserved_gpu_hours", "paid_api_usd", "max_concurrent_gpu_jobs")
TOTAL_KEYS = ("reserved_gpu_hours", "actual_gpu_seconds", "api_usd_known", "api_usd_reserve")
RESERVATION_KEYS = ("id", "job_id", "cluster", "account", "partition", "gpus", "requested_minutes",
                    "reserved_gpu_hours", "actual_seconds", "status", "source_commit", "manifest_hash", "output_dir")
API_KEYS = ("date", "provider", "calls", "usd")
STATE_KEYS = ("schema", "direction", "session_state", "last_worklog_entry_at", "sessions", "jobs")
JOB_KEYS = ("job_id", "cluster", "submitted_at", "waiter", "expected_terminal", "status", "last_progress_at")
WORKLOG_KEYS = ("schema", "title", "state", "right_now", "directions", "terms", "budgets", "transcripts", "needs",
                "findings", "incidents")
NEED_KEYS = ("id", "at", "text", "default", "answer", "answered_at")
FINDING_KEYS = ("id", "at", "plain", "setup", "strength", "evidence")
INCIDENT_KEYS = ("id", "at", "what", "effect", "fix")
HELD_OUT_KEYS = ("id", "task", "path", "sha256", "n", "created", "created_by", "purpose", "scored_runs")
FINDINGS_COLUMNS = ("id", "date", "direction", "claim", "status", "commit", "evidence", "report")


class RegistryError(Exception):
    """A user-facing refusal (exit 1)."""


# ---------------------------------------------------------------------------------------------------------------
# Generic checks


def _keys(obj, where, required, optional=(), errors=None):
    """Missing and unknown keys of a dict record."""
    if not isinstance(obj, dict):
        errors.append("%s: expected an object" % where)
        return False
    for k in required:
        if k not in obj:
            errors.append("%s: missing field %r" % (where, k))
    for k in sorted(obj):
        if k not in required and k not in optional:
            errors.append("%s: unknown key %r" % (where, k))
    return True


def _schema(data, errors, value=1):
    if not isinstance(data, dict):
        errors.append("top level: expected an object")
        return False
    if data.get("schema") != value:
        errors.append("schema: expected %r, found %r" % (value, data.get("schema")))
    return True


def _number(value, where, errors, integer=False, allow_none=False):
    if value is None and allow_none:
        return
    ok = isinstance(value, int) if integer else isinstance(value, (int, float))
    if isinstance(value, bool) or not ok or value < 0:
        errors.append("%s: expected a non-negative %s, found %r" % (where, "integer" if integer else "number", value))


def _str(value, where, errors, allow_none=False, nonempty=True):
    if value is None and allow_none:
        return
    if not isinstance(value, str) or (nonempty and not value.strip()):
        errors.append("%s: expected a non-empty string, found %r" % (where, value))


def _unique(ids, where, errors):
    seen = set()
    for i in ids:
        if i in seen:
            errors.append("%s: duplicate id %r" % (where, i))
        seen.add(i)


# ---------------------------------------------------------------------------------------------------------------
# directions.json (spec 4.2)


def validate_directions(data):
    errors, warnings = [], []
    if not _schema(data, errors):
        return errors, warnings
    _keys(data, "directions.json", ("schema", "updated", "directions"), (), errors)
    rows = data.get("directions")
    if not isinstance(rows, list):
        errors.append("directions: expected a list")
        return errors, warnings
    for i, row in enumerate(rows):
        where = "directions[%d]" % i
        if not _keys(row, where, DIRECTION_REQUIRED, DIRECTION_OPTIONAL, errors):
            continue
        where = "direction %s" % row.get("id", i)
        if not isinstance(row.get("id"), str) or not SLUG_RE.match(row.get("id") or ""):
            errors.append("%s: id must be a lower-case slug" % where)
        if row.get("status") not in DIRECTION_STATUS:
            errors.append("%s: status %r is not one of %s" % (where, row.get("status"), ", ".join(DIRECTION_STATUS)))
        by = row.get("claimed_by")
        if by is not None and not (isinstance(by, str) and TAG_RE.match(by)):
            errors.append("%s: claimed_by %r is not <claude|codex>-<8 hex> (R29)" % (where, by))
        if row.get("status") in ("claimed", "active") and by is None:
            errors.append("%s: status %s needs claimed_by" % (where, row.get("status")))
        if by is not None and not row.get("claimed_at"):
            errors.append("%s: claimed_by set without claimed_at" % where)
        for k in ("parent_findings", "do_not_touch", "legacy_scratch", "archive"):
            if k in row and not (isinstance(row[k], list) and all(isinstance(x, str) for x in row[k])):
                errors.append("%s: %s must be a list of strings" % (where, k))
        g = row.get("frozen_grader_sha256")
        if g is not None and not (isinstance(g, str) and re.match(r"^[0-9a-f]{64}$", g)):
            errors.append("%s: frozen_grader_sha256 must be 64 hex characters or null" % where)
    _unique([r.get("id") for r in rows if isinstance(r, dict)], "directions", errors)
    return errors, warnings


# ---------------------------------------------------------------------------------------------------------------
# ledger.json (spec 4.4)


LEGACY_KEYS = ("reserved_gpu_hours", "actual_gpu_seconds", "api_usd_known")


def _row_sums(data):
    res = data.get("reservations") or []
    calls = data.get("api_calls") or []
    return {"reserved_gpu_hours": round(sum(float(r.get("reserved_gpu_hours") or 0) for r in res), 4),
            "actual_gpu_seconds": int(sum(int(r.get("actual_seconds") or 0) * int(r.get("gpus") or 0) for r in res)),
            "api_usd_known": round(sum(float(c.get("usd") or 0) for c in calls), 4)}


def ledger_totals(data):
    """Totals: the row sums plus ``legacy_totals`` (spend recorded before RS, with no rows).

    ``api_usd_reserve`` is an accumulator with no row field, so it is carried as stored.
    """
    sums = _row_sums(data)
    legacy = data.get("legacy_totals") or {}
    reserve = float(((data.get("totals") or {}).get("api_usd_reserve")) or 0.0)
    return {"reserved_gpu_hours": round(sums["reserved_gpu_hours"] + float(legacy.get("reserved_gpu_hours") or 0), 4),
            "actual_gpu_seconds": int(sums["actual_gpu_seconds"] + int(legacy.get("actual_gpu_seconds") or 0)),
            "api_usd_known": round(sums["api_usd_known"] + float(legacy.get("api_usd_known") or 0), 4),
            "api_usd_reserve": round(reserve, 4)}


def carry_legacy(data):
    """Before RS recomputes totals, keep spend that has no rows (a converted legacy ledger).

    When ``legacy_totals`` is absent and a stored total exceeds its row sum, the surplus becomes ``legacy_totals``,
    so the next recomputation keeps it. Returns True when the field was added. Called by every RS ledger write.
    """
    if "legacy_totals" in data or not isinstance(data.get("totals"), dict):
        return False
    sums = _row_sums(data)
    surplus = {}
    for k in LEGACY_KEYS:
        diff = float(data["totals"].get(k) or 0) - float(sums[k])
        surplus[k] = (int(round(diff)) if k == "actual_gpu_seconds" else round(diff, 4)) if diff > 1e-9 else (
            0 if k == "actual_gpu_seconds" else 0.0)
    if not any(surplus.values()):
        return False
    data["legacy_totals"] = surplus
    return True


def validate_ledger(data):
    errors, warnings = [], []
    if not _schema(data, errors):
        return errors, warnings
    if "generated" in data:
        return validate_global_ledger(data)
    _keys(data, "ledger.json", LEDGER_KEYS, ("legacy_totals",), errors)
    _str(data.get("direction"), "direction", errors)
    if "legacy_totals" in data and _keys(data["legacy_totals"], "legacy_totals", LEGACY_KEYS, (), errors):
        for k in LEGACY_KEYS:
            _number(data["legacy_totals"].get(k), "legacy_totals." + k, errors, integer=(k == "actual_gpu_seconds"))
    if _keys(data.get("caps"), "caps", CAP_KEYS, (), errors):
        for k in CAP_KEYS:
            _number(data["caps"].get(k), "caps." + k, errors, integer=(k == "max_concurrent_gpu_jobs"))
    if _keys(data.get("totals"), "totals", TOTAL_KEYS, (), errors):
        for k in TOTAL_KEYS:
            _number(data["totals"].get(k), "totals." + k, errors)
    res = data.get("reservations")
    if not isinstance(res, list):
        errors.append("reservations: expected a list")
        res = []
    for i, r in enumerate(res):
        where = "reservations[%d]" % i
        if not _keys(r, where, RESERVATION_KEYS, (), errors):
            continue
        if r.get("status") not in RESERVATION_STATUS:
            errors.append("%s: status %r is not one of %s" % (where, r.get("status"), ", ".join(RESERVATION_STATUS)))
        _number(r.get("gpus"), where + ".gpus", errors, integer=True)
        _number(r.get("requested_minutes"), where + ".requested_minutes", errors)
        _number(r.get("reserved_gpu_hours"), where + ".reserved_gpu_hours", errors)
        _number(r.get("actual_seconds"), where + ".actual_seconds", errors, allow_none=True)
        for k in ("job_id", "cluster", "id"):
            _str(r.get(k), "%s.%s" % (where, k), errors)
    _unique([r.get("id") for r in res if isinstance(r, dict)], "reservations", errors)
    calls = data.get("api_calls")
    if not isinstance(calls, list):
        errors.append("api_calls: expected a list")
        calls = []
    for i, c in enumerate(calls):
        where = "api_calls[%d]" % i
        if not _keys(c, where, API_KEYS, (), errors):
            continue
        if not (isinstance(c.get("date"), str) and DATE_RE.match(c["date"])):
            errors.append("%s: date must be YYYY-MM-DD" % where)
        _number(c.get("calls"), where + ".calls", errors, integer=True)
        _number(c.get("usd"), where + ".usd", errors)
    if not errors and isinstance(data.get("totals"), dict):
        expect = ledger_totals(data)
        for k in LEGACY_KEYS:
            stored = float(data["totals"].get(k) or 0)
            if abs(stored - float(expect[k])) <= 1e-6:
                continue
            if stored > expect[k] and "legacy_totals" not in data:
                warnings.append("totals.%s is %r but the rows give %r; the next RS ledger write keeps the "
                                "difference as legacy_totals" % (k, data["totals"].get(k), expect[k]))
            else:
                warnings.append("totals.%s is %r but the rows and legacy_totals give %r; the next RS ledger write "
                                "recomputes it" % (k, data["totals"].get(k), expect[k]))
    return errors, warnings


def validate_global_ledger(data):
    errors, warnings = [], []
    _keys(data, "global ledger.json", ("schema", "generated", "directions", "totals"), (), errors)
    if isinstance(data.get("directions"), dict):
        for slug, tot in sorted(data["directions"].items()):
            if _keys(tot, "directions.%s" % slug, TOTAL_KEYS, (), errors):
                for k in TOTAL_KEYS:
                    _number(tot.get(k), "directions.%s.%s" % (slug, k), errors)
    else:
        errors.append("directions: expected an object")
    if _keys(data.get("totals"), "totals", TOTAL_KEYS, (), errors):
        for k in TOTAL_KEYS:
            _number(data["totals"].get(k), "totals." + k, errors)
    return errors, warnings


# ---------------------------------------------------------------------------------------------------------------
# state.json (spec 4.5)


def validate_state(data):
    errors, warnings = [], []
    if not _schema(data, errors):
        return errors, warnings
    _keys(data, "state.json", STATE_KEYS, (), errors)
    _str(data.get("direction"), "direction", errors)
    if data.get("session_state") not in SESSION_STATE:
        errors.append("session_state %r is not one of %s" % (data.get("session_state"), ", ".join(SESSION_STATE)))
    last = data.get("last_worklog_entry_at")
    if last is not None and paths.parse_iso(last) is None:
        errors.append("last_worklog_entry_at %r is not an ISO time" % last)
    sessions = data.get("sessions")
    if not isinstance(sessions, dict):
        errors.append("sessions: expected an object")
        sessions = {}
    for tag, rec in sorted(sessions.items()):
        if not TAG_RE.match(tag):
            errors.append("session key %r is not <claude|codex>-<8 hex> (R29)" % tag)
        _keys(rec, "sessions.%s" % tag, (), state.MIRROR_KEYS, errors)
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        errors.append("jobs: expected a list")
        jobs = []
    for i, j in enumerate(jobs):
        where = "jobs[%d]" % i
        if not _keys(j, where, JOB_KEYS, (), errors):
            continue
        if j.get("status") not in JOB_STATUS:
            errors.append("%s: status %r is not one of %s" % (where, j.get("status"), ", ".join(JOB_STATUS)))
        _str(j.get("job_id"), where + ".job_id", errors)
    _unique([(j.get("cluster"), j.get("job_id")) for j in jobs if isinstance(j, dict)], "jobs", errors)
    return errors, warnings


# ---------------------------------------------------------------------------------------------------------------
# worklog.json (spec 4.8)


def _register(items, where, keys, prefix, errors):
    if not isinstance(items, list):
        errors.append("%s: expected a list" % where)
        return []
    for i, item in enumerate(items):
        w = "%s[%d]" % (where, i)
        if not _keys(item, w, keys, (), errors):
            continue
        if not (isinstance(item.get("id"), str) and re.match(r"^%s[0-9]+$" % prefix, item["id"])):
            errors.append("%s: id %r must be %s<number>" % (w, item.get("id"), prefix))
        _str(item.get("at"), w + ".at", errors)
    ids = [x.get("id") for x in items if isinstance(x, dict)]
    _unique(ids, where, errors)
    return items


def validate_worklog(data):
    errors, warnings = [], []
    if not _schema(data, errors):
        return errors, warnings
    _keys(data, "worklog.json", WORKLOG_KEYS, (), errors)
    for k in ("title", "right_now", "transcripts"):
        _str(data.get(k), k, errors)
    if data.get("state") not in WORKLOG_STATE:
        errors.append("state %r is not one of %s" % (data.get("state"), ", ".join(WORKLOG_STATE)))
    errors.extend(check_directions_list(data.get("directions")))
    errors.extend(check_terms_list(data.get("terms")))
    if _keys(data.get("budgets"), "budgets", ("gpu", "openrouter"), (), errors):
        for k in ("gpu", "openrouter"):
            _str(data["budgets"].get(k), "budgets." + k, errors, nonempty=False)
    for n in _register(data.get("needs"), "needs", NEED_KEYS, "N", errors):
        if isinstance(n, dict):
            _str(n.get("text"), "need %s text" % n.get("id"), errors)
            _str(n.get("default"), "need %s default" % n.get("id"), errors, allow_none=True)
            if (n.get("answer") is None) != (n.get("answered_at") is None):
                errors.append("need %s: answer and answered_at must be set together" % n.get("id"))
    for f in _register(data.get("findings"), "findings", FINDING_KEYS, "F", errors):
        if isinstance(f, dict):
            if f.get("strength") not in STRENGTH:
                errors.append("finding %s: strength %r is not one of %s" % (f.get("id"), f.get("strength"),
                                                                            ", ".join(STRENGTH)))
            for k in ("plain", "setup", "evidence"):
                _str(f.get(k), "finding %s %s" % (f.get("id"), k), errors)
    for p in _register(data.get("incidents"), "incidents", INCIDENT_KEYS, "P", errors):
        if isinstance(p, dict):
            for k in ("what", "effect", "fix"):
                _str(p.get(k), "incident %s %s" % (p.get("id"), k), errors)
    return errors, warnings


def check_directions_list(value):
    errors = []
    if not isinstance(value, list):
        return ["directions: expected a list of {\"name\", \"state\"} objects"]
    for i, d in enumerate(value):
        if _keys(d, "directions[%d]" % i, ("name", "state"), (), errors):
            _str(d.get("name"), "directions[%d].name" % i, errors)
            _str(d.get("state"), "directions[%d].state" % i, errors)
    return errors


def check_terms_list(value):
    errors = []
    if not isinstance(value, list):
        return ["terms: expected a list of {\"term\", \"meaning\"} objects"]
    if len(value) > MAX_TERMS:
        errors.append("terms: at most %d terms; more means the entries are too low-level" % MAX_TERMS)
    for i, t in enumerate(value):
        if _keys(t, "terms[%d]" % i, ("term", "meaning"), (), errors):
            _str(t.get("term"), "terms[%d].term" % i, errors)
            _str(t.get("meaning"), "terms[%d].meaning" % i, errors)
    return errors


# ---------------------------------------------------------------------------------------------------------------
# FINDINGS.md (spec 4.1, R16, R17)


def split_row(line):
    """Cells of a Markdown table row, splitting on unescaped pipes."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells = re.split(r"(?<!\\)\|", s)
    return [c.strip().replace("\\|", "|") for c in cells]


def parse_findings(text):
    """``(rows, errors)``; each row is a dict of the eight columns plus ``line``."""
    rows, errors = [], []
    lines = text.splitlines()
    header = None
    for no, line in enumerate(lines, 1):
        if not line.strip().startswith("|"):
            continue
        cells = split_row(line)
        if header is None:
            header = no
            if tuple(c.lower() for c in cells) != FINDINGS_COLUMNS:
                errors.append("line %d: table header must be | %s |" % (no, " | ".join(FINDINGS_COLUMNS)))
                return rows, errors
            continue
        if all(re.match(r"^:?-+:?$", c) for c in cells if c):
            continue
        if len(cells) != len(FINDINGS_COLUMNS):
            errors.append("line %d: expected %d columns, found %d" % (no, len(FINDINGS_COLUMNS), len(cells)))
            continue
        row = dict(zip(FINDINGS_COLUMNS, cells))
        row["line"] = no
        rows.append(row)
    if header is None:
        errors.append("no findings table found")
    return rows, errors


def evidence_paths(cell):
    return [p.strip().strip("`") for p in re.split(r"<br\s*/?>", cell or "") if p.strip()]


def is_provenance_path(p):
    return os.path.basename(p) in ("run_manifest.json", "manifest.json") or re.match(
        r"^run_manifest\.[0-9]+\.json$", os.path.basename(p)) is not None


def validate_findings_text(text):
    rows, errors = parse_findings(text)
    warnings = []
    for r in rows:
        where = "line %d (%s)" % (r["line"], r["id"])
        if not FINDING_ID_RE.match(r["id"]):
            errors.append("%s: id must be F-<direction-short>-NNN" % where)
        if not DATE_RE.match(r["date"]):
            errors.append("%s: date must be YYYY-MM-DD" % where)
        if r["status"] not in FINDING_STATUS:
            errors.append("%s: status %r is not one of %s" % (where, r["status"], ", ".join(FINDING_STATUS)))
        if not (r["commit"] == "pre-manifest" or SHORT_SHA_RE.match(r["commit"])):
            errors.append("%s: commit must be a short SHA or pre-manifest" % where)
        if not r["claim"]:
            errors.append("%s: empty claim" % where)
        if r["status"] in ("verified", "replicated"):
            if r["commit"] == "pre-manifest":
                errors.append("%s: a pre-manifest row is at most reviewed (R16)" % where)
            if not any(is_provenance_path(p) for p in evidence_paths(r["evidence"])):
                errors.append("%s: %s needs a provenance file (run_manifest.json) in evidence" % (where, r["status"]))
        if r["status"] == "superseded" and not re.search(r"\(superseded by F-[a-z0-9-]+-[0-9]{3}\)\s*$", r["claim"]):
            errors.append("%s: a superseded claim must end with (superseded by F-x-NNN)" % where)
    _unique([r["id"] for r in rows], "FINDINGS", errors)
    return errors, warnings


# ---------------------------------------------------------------------------------------------------------------
# held_out.json (spec 6.4)


def validate_held_out(data):
    errors, warnings = [], []
    if not _schema(data, errors):
        return errors, warnings
    _keys(data, "held_out.json", ("schema", "sets"), (), errors)
    sets = data.get("sets")
    if not isinstance(sets, list):
        errors.append("sets: expected a list")
        return errors, warnings
    for i, s in enumerate(sets):
        where = "sets[%d]" % i
        if not _keys(s, where, HELD_OUT_KEYS, (), errors):
            continue
        if not (isinstance(s.get("sha256"), str) and re.match(r"^[0-9a-f]{64}$", s["sha256"])):
            errors.append("%s: sha256 must be 64 hex characters" % where)
        _number(s.get("n"), where + ".n", errors, integer=True)
        if not isinstance(s.get("scored_runs"), list):
            errors.append("%s: scored_runs must be a list" % where)
    _unique([s.get("id") for s in sets if isinstance(s, dict)], "sets", errors)
    return errors, warnings


# ---------------------------------------------------------------------------------------------------------------
# validate <path>


JSON_VALIDATORS = {"directions.json": validate_directions, "ledger.json": validate_ledger,
                   "state.json": validate_state, "worklog.json": validate_worklog,
                   "held_out.json": validate_held_out}


def validate_path(path):
    """``(errors, warnings)`` for one file; raises KeyError for a file name RS does not know."""
    name = os.path.basename(path)
    if name == "FINDINGS.md":
        return validate_findings_text(records.read_text(path))
    fn = JSON_VALIDATORS[name]
    try:
        data = json.loads(records.read_text(path))
    except ValueError as exc:
        return ["invalid JSON: %s" % exc], []
    return fn(data)


def cmd_validate(args):
    code = 0
    for path in args.paths:
        try:
            errors, warnings = validate_path(path)
        except KeyError:
            sys.stderr.write("%s: no validator for this file name (known: FINDINGS.md, %s)\n"
                             % (path, ", ".join(sorted(JSON_VALIDATORS))))
            code = max(code, 2)
            continue
        except (IOError, OSError) as exc:
            sys.stderr.write("%s: cannot read: %s\n" % (path, exc))
            code = max(code, 2)
            continue
        for e in errors:
            print("%s: error: %s" % (path, e))
        for w in warnings:
            print("%s: warning: %s" % (path, w))
        if errors:
            code = max(code, 1)
        else:
            print("%s: valid%s" % (path, " with %d warning(s)" % len(warnings) if warnings else ""))
    return code


# ---------------------------------------------------------------------------------------------------------------
# Paths under a research root


def default_root(cfg=None):
    cfg = cfg or paths.Config.from_env()
    return os.path.join(cfg.dc_root, "docs", "research")


def repo_root(root):
    """The checkout that holds ``<root>``: two levels up from ``docs/research``."""
    return os.path.dirname(os.path.dirname(os.path.abspath(root)))


def load_directions_file(root):
    path = os.path.join(root, "directions.json")
    data = state.load_json(path)
    if data is None:
        raise RegistryError("no directions.json at %s" % path)
    errors, _ = validate_directions(data)
    if errors:
        raise RegistryError("directions.json is invalid: " + "; ".join(errors[:5]))
    return path, data


def _cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ")


# ---------------------------------------------------------------------------------------------------------------
# render (spec 4.3)


STAMP_PREFIX = "Generated by `research-session render` at "


def render_directions(data):
    lines = ["# Directions", "",
             "Generated by `research-session render` from `directions.json` (registry updated %s). Never edit this"
             " file by hand." % data.get("updated"), "",
             "| Direction | Title | Status | Claimed by | Summary | Directory |",
             "|---|---|---|---|---|---|"]
    for r in data["directions"]:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            _cell(r["id"]), _cell(r["title"]), r["status"], _cell(r.get("claimed_by") or "nobody"),
            _cell(r.get("summary")), _cell(r.get("dir"))))
    return "\n".join(lines) + "\n"


def _session_row(root, row):
    rr = repo_root(root)
    rel_state = row.get("state") or os.path.join(row.get("dir") or os.path.join("docs", "research", row["id"]),
                                                 "state.json")
    st_path = rel_state if os.path.isabs(rel_state) else os.path.join(rr, rel_state)
    st = None
    try:
        st = state.load_json(st_path)
    except (ValueError, IOError, OSError):
        st = None
    if isinstance(st, dict):
        sstate = st.get("session_state") or "unknown"
        dt = records.from_iso(st.get("last_worklog_entry_at"))
        last = records.long_when(dt) if dt else "none yet"
    else:
        sstate, last = "no state yet", "none yet"
    worklog = row.get("worklog") or os.path.join(row.get("dir") or "", "WORKLOG.md")
    return "| %s | %s | %s | %s | %s | %s |" % (
        row["claimed_by"], _cell(row["id"]), _cell(sstate), last, _cell(worklog),
        "<br>".join(_cell(x) for x in row.get("do_not_touch") or []) or "nothing listed")


def render_sessions(root, data, t):
    claimed = sorted([r for r in data["directions"] if r.get("claimed_by")], key=lambda r: (r["claimed_by"], r["id"]))
    lines = ["# Sessions", "",
             STAMP_PREFIX + "%s from `directions.json` and each direction's `state.json`. Never edit this file by"
             " hand." % records.long_when(records.local(t)), "",
             "| Session | Directions claimed | State | Last worklog entry | Worklog | Do not touch |",
             "|---|---|---|---|---|---|"]
    lines.extend(_session_row(root, r) for r in claimed)
    if not claimed:
        lines.append("| none | no direction is claimed | | | | |")
    return "\n".join(lines) + "\n"


def _drop_stamp(text, prefix):
    return "\n".join(l for l in text.splitlines() if not l.startswith(prefix))


def write_if_changed(path, text, stamp_prefix=None):
    """Write unless the file already holds ``text``, ignoring a stamp line. Returns True when written."""
    try:
        old = records.read_text(path)
    except (IOError, OSError):
        old = None
    if old is not None:
        if old == text:
            return False
        if stamp_prefix and _drop_stamp(old, stamp_prefix) == _drop_stamp(text, stamp_prefix):
            return False
    records.write_text_atomic(path, text)
    return True


def cmd_render(args):
    root = args.root or default_root()
    try:
        _, data = load_directions_file(root)
    except RegistryError as exc:
        sys.stderr.write("research-session: %s\n" % exc)
        return 1
    t = records.now()
    out = []
    for name, text, stamp in (("DIRECTIONS.md", render_directions(data), None),
                              ("SESSIONS.md", render_sessions(root, data, t), STAMP_PREFIX)):
        path = os.path.join(root, name)
        out.append("%s %s" % (path, "written" if write_if_changed(path, text, stamp) else "unchanged"))
    print("\n".join(out))
    return 0


# ---------------------------------------------------------------------------------------------------------------
# ledger-rollup (spec 4.4)


def rollup(root, t):
    dirs = {}
    for path in sorted(glob.glob(os.path.join(root, "*", "ledger.json"))):
        if os.path.basename(os.path.dirname(path)).startswith(("_", ".")):
            continue  # _templates and hidden directories are not directions
        data = state.load_json(path)
        errors, _ = validate_ledger(data)
        if errors:
            raise RegistryError("%s is invalid: %s" % (path, "; ".join(errors[:3])))
        # Stored totals: RS recomputes them on every ledger write, and a converted legacy ledger has only them.
        dirs[data["direction"]] = {k: data["totals"][k] for k in TOTAL_KEYS}
    totals = {k: 0 for k in TOTAL_KEYS}
    for tot in dirs.values():
        for k in TOTAL_KEYS:
            totals[k] += tot[k]
    for k in ("reserved_gpu_hours", "api_usd_known", "api_usd_reserve"):
        totals[k] = round(float(totals[k]), 4)
    return {"schema": 1, "generated": records.iso(t), "directions": dirs, "totals": totals}


def cmd_ledger_rollup(args):
    root = args.root or default_root()
    try:
        data = rollup(root, records.now())
    except RegistryError as exc:
        sys.stderr.write("research-session: %s\n" % exc)
        return 1
    path = os.path.join(root, "ledger.json")
    old = state.load_json(path) if os.path.exists(path) else None
    if isinstance(old, dict) and {k: v for k, v in old.items() if k != "generated"} == \
            {k: v for k, v in data.items() if k != "generated"}:
        print("%s unchanged (%d directions)" % (path, len(data["directions"])))
        return 0
    records.write_json(path, data)
    print("%s written (%d directions; %.2f GPU-h reserved; $%.2f known API spend)" % (
        path, len(data["directions"]), data["totals"]["reserved_gpu_hours"], data["totals"]["api_usd_known"]))
    return 0


# ---------------------------------------------------------------------------------------------------------------
# claim and release (R23)


def _caller_tag(args):
    if args.as_tag:
        if not TAG_RE.match(args.as_tag):
            raise ValueError("--as %r is not <claude|codex>-<8 hex> (R29)" % args.as_tag)
        return args.as_tag
    cfg = paths.Config.from_env()
    s = state.find_session(cfg, args.session, os.path.realpath(args.cwd or os.getcwd()))
    return s.get("tag") or paths.session_tag(s["tool"], s["session_id"])


def _edit_directions(root, slug, fn):
    cfg = paths.Config.from_env()
    path = os.path.join(root, "directions.json")
    with records.state_lock(cfg, os.path.realpath(path)):
        path, data = load_directions_file(root)
        rows = [r for r in data["directions"] if r["id"] == slug]
        if not rows:
            raise RegistryError("unknown direction %r in %s" % (slug, path))
        message = fn(rows[0])
        rows[0]["updated"] = records.today()
        data["updated"] = records.today()
        errors, _ = validate_directions(data)
        if errors:
            raise RegistryError("refused; the result would be invalid: " + "; ".join(errors[:3]))
        records.write_json(path, data)
    return message


def cmd_claim(args):
    try:
        tag = _caller_tag(args)
    except ValueError as exc:
        sys.stderr.write("research-session: %s\n" % exc)
        return 2
    except state.StateError as exc:
        sys.stderr.write("research-session: %s; pass --as <tool>-<8 hex>\n" % exc)
        return 2

    def claim(row):
        if row["status"] in ("claimed", "active") and row.get("claimed_by") not in (None, tag):
            raise RegistryError("direction %s is %s by %s since %s" % (row["id"], row["status"], row["claimed_by"],
                                                                        row.get("claimed_at")))
        if row["status"] in ("done", "abandoned"):
            raise RegistryError("direction %s is %s; reopening it is the user's decision" % (row["id"], row["status"]))
        if row.get("claimed_by") == tag:
            return "already claimed by %s" % tag
        row["status"] = "claimed"
        row["claimed_by"] = tag
        row["claimed_at"] = records.iso(records.now())
        if args.branch:
            row["branch"] = args.branch
        if args.worktree:
            row["worktree"] = args.worktree
        return "claimed by %s" % tag

    root = args.root or default_root()
    try:
        msg = _edit_directions(root, args.slug, claim)
    except RegistryError as exc:
        sys.stderr.write("research-session: refused: %s\n" % exc)
        return 1
    print("%s: %s. Commit directions.json on DC main before branching (R23)." % (args.slug, msg))
    return 0


def cmd_freeze_grader(args):
    try:
        if not isinstance(args.sha256, str) or re.fullmatch(r"[0-9a-f]{64}", args.sha256) is None:
            raise ValueError("SHA256 must be exactly 64 lowercase hexadecimal characters")
        if not args.session or not args.session.strip():
            raise ValueError("--session must be a non-empty session selector")
        session = state.find_session(paths.Config.from_env(), args.session)
        tag = session.get("tag") or paths.session_tag(session["tool"], session["session_id"])
    except (ValueError, state.StateError) as exc:
        sys.stderr.write("research-session: %s\n" % exc)
        return 2

    def freeze(row):
        if row["status"] not in ("claimed", "active") or row.get("claimed_by") != tag:
            raise RegistryError("direction %s must be claimed or active and owned by %s" % (row["id"], tag))
        existing = row.get("frozen_grader_sha256")
        if existing is not None and existing != args.sha256:
            raise RegistryError("direction %s already has a different frozen grader hash" % row["id"])
        row["frozen_grader_sha256"] = args.sha256
        return "grader frozen at %s" % args.sha256

    try:
        msg = _edit_directions(args.root or default_root(), args.slug, freeze)
    except RegistryError as exc:
        sys.stderr.write("research-session: refused: %s\n" % exc)
        return 1
    print("%s: %s." % (args.slug, msg))
    return 0


def cmd_release(args):
    try:
        tag = _caller_tag(args)
    except ValueError as exc:
        sys.stderr.write("research-session: %s\n" % exc)
        return 2
    except state.StateError as exc:
        sys.stderr.write("research-session: %s; pass --as <tool>-<8 hex>\n" % exc)
        return 2

    def release(row):
        if row.get("claimed_by") not in (None, tag):
            raise RegistryError("direction %s is claimed by %s, not %s" % (row["id"], row["claimed_by"], tag))
        row["status"] = args.status
        row["claimed_by"] = None
        row["claimed_at"] = None
        return "released with status %s" % args.status

    root = args.root or default_root()
    try:
        msg = _edit_directions(root, args.slug, release)
    except RegistryError as exc:
        sys.stderr.write("research-session: refused: %s\n" % exc)
        return 1
    print("%s: %s." % (args.slug, msg))
    return 0


# ---------------------------------------------------------------------------------------------------------------
# argparse


def _root_arg(p):
    p.add_argument("--root", help="research root holding directions.json (default: DC/docs/research)")


def add_parsers(sub):
    p = sub.add_parser("validate", help="validate RS files by name: directions, ledger, state, worklog, FINDINGS, "
                                        "held_out (read-only)")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("render", help="render DIRECTIONS.md and SESSIONS.md from directions.json (spec 4.3)")
    _root_arg(p)
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("ledger-rollup", help="write the global ledger.json from every direction ledger (spec 4.4)")
    _root_arg(p)
    p.set_defaults(func=cmd_ledger_rollup)

    p = sub.add_parser("freeze-grader", help="freeze the initial grader hash for a session-owned direction")
    p.add_argument("slug")
    p.add_argument("sha256", metavar="SHA256")
    p.add_argument("--session", required=True, help="session id, tag or unique prefix")
    _root_arg(p)
    p.set_defaults(func=cmd_freeze_grader)

    for name, fn, helptext in (("claim", cmd_claim, "claim a direction for this session (R23, orchestrator only)"),
                               ("release", cmd_release, "release a claimed direction with a final status")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("slug")
        if name == "release":
            p.add_argument("--status", required=True, choices=("open", "paused", "done", "abandoned"))
        else:
            p.add_argument("--branch")
            p.add_argument("--worktree")
        p.add_argument("--as", dest="as_tag", metavar="TAG", help="session tag <tool>-<8 hex> (default: this session)")
        p.add_argument("--session", help="session id, tag or prefix (default: most recent session with this cwd)")
        p.add_argument("--cwd", help=argparse_suppress())
        _root_arg(p)
        p.set_defaults(func=fn)


def argparse_suppress():
    import argparse
    return argparse.SUPPRESS
