"""Local session files, the direction state.json mirror, and direction resolution (spec 4.5, R5, R29).

The local session file ``<state root>/sessions/<tool>-<session_id>.json`` is authoritative for gate decisions. Every
RS write to it is mirrored into the registered direction's ``state.json`` under ``sessions.<tool>-<short id>``.

Writers lock a persistent sidecar file with ``fcntl.flock`` and replace the data file atomically, so two hook
processes never lose each other's updates. The lock is never taken on the data file itself, because an atomic
replace gives the data file a new inode.
"""

import contextlib
import copy
import fcntl
import hashlib
import json
import os
import tempfile

from research_session import paths

SCHEMA = 1
DEFAULT_CADENCE = {"claude": 16, "codex": 25}
METRIC = {"claude": "max(seven_day, Fable)", "codex": "codex weekly"}

# Fields of a session record that are mirrored into a direction's state.json (spec 4.5).
MIRROR_KEYS = ("tool", "session_id", "cwd", "started_at", "orchestrator_model", "compactions", "compaction_log",
               "usage", "checkpoints", "agents")


class StateError(Exception):
    """A user-facing error from a state operation (no session found, bad argument)."""


# ---------------------------------------------------------------------------------------------------------------
# JSON files


def dumps(data):
    """RS JSON style: indent 2, sorted keys, trailing newline (spec 4)."""
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def load_json(path, default=None):
    """Load a JSON file. A missing file gives ``default``; an invalid file raises ValueError."""
    try:
        with open(path, "r") as fh:
            text = fh.read()
    except (IOError, OSError) as exc:
        if getattr(exc, "errno", None) == 2:
            return default
        raise
    return json.loads(text)


def write_json_atomic(path, data, mode=0o600, text=None):
    """Write ``data`` to ``path`` by a temporary file in the same directory and ``os.replace``.

    An existing file keeps its mode; a new file gets ``mode``.
    """
    directory = os.path.dirname(path) or "."
    payload = dumps(data) if text is None else text
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(payload)
        try:
            os.chmod(tmp, os.stat(path).st_mode & 0o7777)
        except OSError:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@contextlib.contextmanager
def file_lock(lock_path):
    """Exclusive ``fcntl.flock`` on a persistent sidecar lock file."""
    paths.ensure_dir(os.path.dirname(lock_path))
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


# ---------------------------------------------------------------------------------------------------------------
# Session records


def new_usage(tool):
    return {
        "metric": METRIC.get(tool, METRIC["claude"]),
        "cadence": DEFAULT_CADENCE.get(tool, DEFAULT_CADENCE["claude"]),
        "segments": [],
        "session_points": 0,
        "registered_at": None,
        "points_at_register": 0,
        "next_checkpoint": 1,
        "acked_through": 0,
        "stale_ok_until": None,
        "freeze": None,
        "last_reading": None,
    }


def new_session(tool, session_id, cwd, now):
    return {
        "schema": SCHEMA,
        "tool": tool,
        "session_id": session_id,
        "tag": paths.session_tag(tool, session_id),
        "cwd": os.path.realpath(cwd) if cwd else None,
        "started_at": paths.iso(now),
        "updated_at": paths.iso(now),
        "updated_epoch": now,
        "orchestrator_model": None,
        "register": None,
        "compactions": 0,
        "compaction_log": [],
        "usage": new_usage(tool),
        "checkpoints": [],
        "agents": {},
        "codex_cache": None,
    }


def load_session(cfg, tool, session_id):
    return load_json(cfg.session_file(tool, session_id))


def update_session(cfg, tool, session_id, fn, now, cwd=None, create=True):
    """Lock, load (or create), apply ``fn(session)``, write atomically, and mirror.

    Returns ``(session, result, mirror_result)``. ``fn`` mutates the session in place and may return a value. The
    mirror runs inside the session lock, so an older snapshot never overwrites a newer one in ``state.json``.
    Returns ``(None, None, None)`` when the session file does not exist and ``create`` is false.
    """
    paths.ensure_state_root(cfg)
    path = cfg.session_file(tool, session_id)
    with file_lock(path + ".lock"):
        session = load_json(path)
        if session is None:
            if not create:
                return None, None, None
            session = new_session(tool, session_id, cwd, now)
        result = fn(session)
        session["updated_at"] = paths.iso(now)
        session["updated_epoch"] = now
        write_json_atomic(path, session)
        mirrored = mirror(cfg, session)
    return session, result, mirrored


def list_sessions(cfg):
    """Every readable session record, most recently updated first."""
    out = []
    try:
        names = os.listdir(cfg.sessions_dir)
    except OSError:
        return out
    for name in names:
        if not name.endswith(".json"):
            continue
        try:
            data = load_json(os.path.join(cfg.sessions_dir, name))
        except (ValueError, IOError, OSError):
            continue
        if isinstance(data, dict) and data.get("session_id"):
            out.append(data)
    out.sort(key=lambda s: (s.get("updated_epoch") or 0, s.get("started_at") or ""), reverse=True)
    return out


def find_session(cfg, selector=None, cwd=None):
    """Pick a session by ``--session`` selector (full id, tag, or id prefix), else the most recent whose cwd matches.

    Raises StateError when nothing matches or a selector is ambiguous.
    """
    sessions = list_sessions(cfg)
    if selector:
        exact = [s for s in sessions if selector in (s.get("session_id"), s.get("tag"))]
        if exact:
            return exact[0]
        pref = [s for s in sessions if (s.get("session_id") or "").startswith(selector)
                or ("%s-%s" % (s.get("tool"), s.get("session_id") or "")).startswith(selector)]
        if len(pref) == 1:
            return pref[0]
        if len(pref) > 1:
            raise StateError("session selector %r matches %d sessions; give more characters" % (selector, len(pref)))
        raise StateError("no session matches %r under %s" % (selector, cfg.sessions_dir))
    here = os.path.realpath(cwd or os.getcwd())
    for s in sessions:
        if s.get("cwd") and os.path.realpath(s["cwd"]) == here:
            return s
    raise StateError("no session has cwd %s; pass --session ID" % here)


# ---------------------------------------------------------------------------------------------------------------
# Directions


def load_directions(cfg):
    """Rows of ``directions.json``, or None when the file is missing or unreadable."""
    try:
        data = load_json(cfg.directions_file)
    except (ValueError, IOError, OSError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("directions"), list):
        return None
    return [r for r in data["directions"] if isinstance(r, dict) and r.get("id")]


def _row_worktree(cfg, row):
    wt = row.get("worktree")
    if not isinstance(wt, str) or not wt:
        return None
    return wt if os.path.isabs(wt) else os.path.join(cfg.dc_root, wt)


def cwd_direction(cfg, cwd):
    """Attribution only (R5): the direction whose ``worktree`` contains ``cwd``, most specific first."""
    rows = load_directions(cfg) or []
    best = None
    for row in rows:
        wt = _row_worktree(cfg, row)
        if wt and paths.is_within(cwd, wt):
            if best is None or len(os.path.realpath(wt)) > len(os.path.realpath(_row_worktree(cfg, best))):
                best = row
    return best["id"] if best else None


def resolve_direction(cfg, session, cwd=None):
    """Return ``(slug, how)``: how is ``register``, ``cwd`` (attribution only) or None (R5)."""
    reg = session.get("register") if session else None
    if reg and reg.get("slug"):
        return reg["slug"], "register"
    slug = cwd_direction(cfg, cwd or (session or {}).get("cwd"))
    if slug:
        return slug, "cwd"
    return None, None


def is_registered(session):
    """Only an explicit ``register`` counts; a cwd match never does (R5, spec 5.2 step 4)."""
    reg = (session or {}).get("register")
    return bool(reg and reg.get("slug"))


def repo_root_for(cfg, cwd):
    """The nearest ancestor of ``cwd`` inside A that has ``docs/research``; DC main when there is none."""
    d = os.path.realpath(cwd) if cwd else None
    stop = os.path.realpath(cfg.alignment_root)
    while d and paths.is_within(d, stop):
        if os.path.isdir(os.path.join(d, "docs", "research")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return cfg.dc_root


def direction_state_path(cfg, slug, cwd):
    """Where a registered session mirrors its record: ``<repo>/docs/research/<slug>/state.json``.

    ``<repo>`` is the checkout that contains the session's cwd (a worktree or DC main); a ``state`` field in the
    direction's registry row overrides the repo-relative part.
    """
    root = repo_root_for(cfg, cwd)
    rel = None
    for row in load_directions(cfg) or []:
        if row.get("id") == slug and isinstance(row.get("state"), str) and row["state"]:
            rel = row["state"]
    if not rel:
        rel = os.path.join("docs", "research", slug, "state.json")
    return rel if os.path.isabs(rel) else os.path.join(root, rel)


def mirror_record(session):
    rec = {k: copy.deepcopy(session.get(k)) for k in MIRROR_KEYS}
    return rec


def _strip_read_at(rec):
    rec = copy.deepcopy(rec)
    last = ((rec or {}).get("usage") or {}).get("last_reading")
    if isinstance(last, dict):
        last.pop("read_at", None)
    return rec


def mirror(cfg, session):
    """Mirror a registered session's record into its direction ``state.json``.

    Returns ``written``, ``unchanged``, ``skipped: <why>`` or None for an unregistered session. A change that only
    moves ``last_reading.read_at`` is not written, so a tracked file does not churn on every tool call.
    """
    reg = session.get("register")
    if not reg or not reg.get("state_path"):
        return None
    path = reg["state_path"]
    if not os.path.isdir(os.path.dirname(path)):
        return "skipped: direction directory %s does not exist" % os.path.dirname(path)
    tag = session.get("tag") or paths.session_tag(session.get("tool"), session.get("session_id"))
    lock = os.path.join(cfg.locks_dir, hashlib.sha1(path.encode("utf-8")).hexdigest() + ".lock")
    with file_lock(lock):
        st = load_json(path)
        if not isinstance(st, dict):
            st = {"schema": SCHEMA, "direction": reg["slug"], "session_state": "running",
                  "last_worklog_entry_at": None, "sessions": {}, "jobs": []}
        sessions = st.setdefault("sessions", {})
        rec = mirror_record(session)
        old = sessions.get(tag)
        if old is not None and _strip_read_at(old) == _strip_read_at(rec):
            return "unchanged"
        sessions[tag] = rec
        write_json_atomic(path, st, mode=0o660)
    return "written"


# ---------------------------------------------------------------------------------------------------------------
# Register, acknowledge, cadence, checkpoint recording


def register(cfg, slug, now, selector=None, cwd=None):
    """Bind a session to ``slug`` (spec 5.6). Returns ``(session, warnings, mirror_result)``.

    ``points_at_register`` stores the current session total, so registering late never freezes at once (R5).
    """
    if not slug or "/" in slug or slug.startswith("."):
        raise StateError("invalid direction slug %r" % slug)
    target = find_session(cfg, selector, cwd)
    warnings = []
    rows = load_directions(cfg)
    if rows is None:
        warnings.append("directions.json not found at %s; registered without a registry check" % cfg.directions_file)
    elif slug not in [r.get("id") for r in rows]:
        warnings.append("direction %r is not in %s" % (slug, cfg.directions_file))
    state_path = direction_state_path(cfg, slug, target.get("cwd"))

    def bind(s):
        u = s["usage"]
        s["register"] = {"slug": slug, "at": paths.iso(now), "state_path": state_path}
        u["registered_at"] = paths.iso(now)
        u["points_at_register"] = u.get("session_points", 0)
        u["next_checkpoint"] = 1
        u["acked_through"] = 0
        u["freeze"] = None

    session, _, result = update_session(cfg, target["tool"], target["session_id"], bind, now, create=False)
    if session is None:
        raise StateError("session file for %s disappeared" % target.get("tag"))
    if result and result.startswith("skipped"):
        warnings.append("state.json mirror " + result)
    return session, warnings, result


def ack(session, now, by):
    """Acknowledge the pending checkpoint (spec 5.2). Returns the acked number, or None when nothing is pending."""
    u = session["usage"]
    freeze = u.get("freeze")
    if not freeze or freeze.get("checkpoint", 0) <= u.get("acked_through", 0):
        return None
    n = freeze["checkpoint"]
    u["acked_through"] = n
    for cp in session.get("checkpoints", []):
        if cp.get("n", 0) <= n and not cp.get("acked_at"):
            cp["acked_at"] = paths.iso(now)
            cp["acked_by"] = by
    u["freeze"] = None
    return n


def mark_checkpoint_recorded(session, n, now):
    """Move a ``crossed`` freeze to ``recorded`` (called by ``worklog-append --checkpoint N``, ticket 03)."""
    freeze = session["usage"].get("freeze")
    if not freeze or freeze.get("checkpoint") != n:
        return False
    freeze["stage"] = "recorded"
    freeze["recorded_at"] = paths.iso(now)
    return True
