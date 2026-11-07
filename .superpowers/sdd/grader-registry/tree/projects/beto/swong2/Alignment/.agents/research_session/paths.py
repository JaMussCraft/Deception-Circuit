"""Paths, configuration and small shared helpers for research-session (spec sections 4.5, 5.1 and 5.2).

Every path RS touches comes from a ``Config``. The defaults are the real locations on this machine. Tests and
humans can override each one with an environment variable, so a test never reads the real ``~/.claude``:

=================================  ==============================================================
Environment variable               Default
=================================  ==============================================================
``RESEARCH_SESSION_ROOT``          ``/u/swong2/.claude/research-session`` (state root, mode 0700)
``RESEARCH_SESSION_ALIGNMENT_ROOT`` ``/projects/beto/swong2/Alignment``
``RESEARCH_SESSION_DC_ROOT``       ``<Alignment>/Deception-Circuit`` (DC main checkout)
``RESEARCH_SESSION_DIRECTIONS``    ``<DC>/docs/research/directions.json``
``RESEARCH_SESSION_USAGE_FILE``    ``/u/swong2/.claude/usage.json``
``RESEARCH_SESSION_OAUTH_CACHE``   ``/u/swong2/.claude/.usage_oauth_cache.json``
``RESEARCH_SESSION_OAUTH_LOCK``    ``/u/swong2/.claude/.usage_oauth_cache.lock``
``RESEARCH_SESSION_CREDENTIALS``   ``/u/swong2/.claude/.credentials.json`` (read only by the token reader)
``RESEARCH_SESSION_CODEX_USAGE``   ``/u/swong2/.local/bin/codex-usage``
=================================  ==============================================================
"""

import datetime
import os

DEFAULT_STATE_ROOT = "/u/swong2/.claude/research-session"
DEFAULT_ALIGNMENT_ROOT = "/projects/beto/swong2/Alignment"
DEFAULT_CLAUDE_DIR = "/u/swong2/.claude"
DEFAULT_CODEX_USAGE = "/u/swong2/.local/bin/codex-usage"
OAUTH_URL = "https://api.anthropic.com/api/oauth/usage"

# The literal kill-switch path of the hook guard (spec 5.1). The self-ack guard denies commands naming it.
DEFAULT_DISABLED = DEFAULT_STATE_ROOT + "/DISABLED"

TIMEZONE = "America/New_York"  # the user's zone (R22); offsets and labels are always computed from it


class Config(object):
    """All paths RS uses. Build with ``Config.from_env()`` or pass explicit paths (tests)."""

    def __init__(self, state_root=DEFAULT_STATE_ROOT, alignment_root=DEFAULT_ALIGNMENT_ROOT, dc_root=None,
                 directions_file=None, usage_file=None, oauth_cache=None, oauth_lock=None, credentials=None,
                 codex_usage=DEFAULT_CODEX_USAGE, oauth_url=OAUTH_URL):
        self.state_root = os.path.abspath(state_root)
        self.alignment_root = os.path.abspath(alignment_root)
        self.dc_root = os.path.abspath(dc_root or os.path.join(self.alignment_root, "Deception-Circuit"))
        self.directions_file = os.path.abspath(
            directions_file or os.path.join(self.dc_root, "docs", "research", "directions.json"))
        self.usage_file = os.path.abspath(usage_file or os.path.join(DEFAULT_CLAUDE_DIR, "usage.json"))
        self.oauth_cache = os.path.abspath(oauth_cache or os.path.join(DEFAULT_CLAUDE_DIR, ".usage_oauth_cache.json"))
        self.oauth_lock = os.path.abspath(oauth_lock or os.path.join(DEFAULT_CLAUDE_DIR, ".usage_oauth_cache.lock"))
        self.credentials = os.path.abspath(credentials or os.path.join(DEFAULT_CLAUDE_DIR, ".credentials.json"))
        self.codex_usage = codex_usage
        self.oauth_url = oauth_url

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        return cls(
            state_root=env.get("RESEARCH_SESSION_ROOT") or DEFAULT_STATE_ROOT,
            alignment_root=env.get("RESEARCH_SESSION_ALIGNMENT_ROOT") or DEFAULT_ALIGNMENT_ROOT,
            dc_root=env.get("RESEARCH_SESSION_DC_ROOT") or None,
            directions_file=env.get("RESEARCH_SESSION_DIRECTIONS") or None,
            usage_file=env.get("RESEARCH_SESSION_USAGE_FILE") or None,
            oauth_cache=env.get("RESEARCH_SESSION_OAUTH_CACHE") or None,
            oauth_lock=env.get("RESEARCH_SESSION_OAUTH_LOCK") or None,
            credentials=env.get("RESEARCH_SESSION_CREDENTIALS") or None,
            codex_usage=env.get("RESEARCH_SESSION_CODEX_USAGE") or DEFAULT_CODEX_USAGE,
        )

    @property
    def sessions_dir(self):
        return os.path.join(self.state_root, "sessions")

    @property
    def locks_dir(self):
        return os.path.join(self.state_root, "locks")

    @property
    def disabled_path(self):
        return os.path.join(self.state_root, "DISABLED")

    def disabled(self):
        """True when the kill switch exists (spec 5.1)."""
        return os.path.lexists(self.disabled_path)

    def session_file(self, tool, session_id):
        return os.path.join(self.sessions_dir, "%s-%s.json" % (tool, session_id))


def ensure_dir(path, mode=0o700):
    """Create ``path`` (and parents) with ``mode`` when missing. An existing directory keeps its mode.

    Safe when two processes race to create the same directory: only the creator sets the mode.
    """
    if os.path.isdir(path):
        return path
    parent = os.path.dirname(path)
    if parent and parent != path and not os.path.isdir(parent):
        ensure_dir(parent, mode)
    try:
        os.mkdir(path, mode)
    except FileExistsError:
        return path
    os.chmod(path, mode)
    return path


def ensure_state_root(cfg):
    ensure_dir(cfg.state_root)
    ensure_dir(cfg.sessions_dir)
    ensure_dir(cfg.locks_dir)
    return cfg.state_root


def is_within(path, root):
    """True when the realpath of ``path`` equals or lies under the realpath of ``root``."""
    if not path:
        return False
    p = os.path.realpath(path)
    r = os.path.realpath(root)
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


def cwd_inside_alignment(cwd, cfg):
    """The hook script no-ops when the realpath of ``cwd`` is outside A (spec 5.1)."""
    return is_within(cwd, cfg.alignment_root)


def session_tag(tool, session_id):
    """``<tool>-<first 8 characters of the session id>`` (R29)."""
    return "%s-%s" % (tool, (session_id or "")[:8])


def _zone():
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+
        return ZoneInfo(TIMEZONE)
    except Exception:  # pragma: no cover - tzdata missing
        return None


def iso(t):
    """ISO time in ``TIMEZONE`` (America/New_York) with an offset computed by zoneinfo, never typed (R22)."""
    zone = _zone()
    if zone is None:  # pragma: no cover
        return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec="seconds")
    return datetime.datetime.fromtimestamp(t, zone).isoformat(timespec="seconds")


def parse_iso(value):
    """Epoch seconds of an ISO string written by ``iso``; None when unparseable."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None
