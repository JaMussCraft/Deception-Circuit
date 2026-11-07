"""Shared helpers for the research records (ticket 03): the clock, time formats, locks and atomic text writes.

Times are always computed in America/New_York (R22). The zone label comes from ``zoneinfo``; it is never typed.
The clock reads ``RESEARCH_SESSION_NOW`` (epoch seconds) when that variable is set, so tests can fix the time.
"""

import contextlib
import datetime
import hashlib
import os
import tempfile
import time

from research_session import paths, state

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December")


def now():
    """Epoch seconds; ``RESEARCH_SESSION_NOW`` overrides the real clock (tests)."""
    fixed = os.environ.get("RESEARCH_SESSION_NOW")
    if fixed:
        return float(fixed)
    return time.time()


def zone():
    from zoneinfo import ZoneInfo
    return ZoneInfo(paths.TIMEZONE)


def local(t):
    """A timezone-aware datetime in America/New_York for epoch seconds ``t``."""
    return datetime.datetime.fromtimestamp(t, zone())


def from_iso(value):
    """A local datetime from an ISO string, or None."""
    t = paths.parse_iso(value)
    return None if t is None else local(t)


def clock_text(dt, with_zone=True):
    """``8:05 am EDT``: 12-hour time, lower-case am and pm, computed zone label."""
    hour = dt.hour % 12 or 12
    text = "%d:%02d %s" % (hour, dt.minute, "am" if dt.hour < 12 else "pm")
    return text + (" " + dt.tzname() if with_zone else "")


def day_heading(dt):
    """``### Saturday 31 October 2026``."""
    return "### %s %d %s %d" % (WEEKDAYS[dt.weekday()], dt.day, MONTHS[dt.month - 1], dt.year)


def short_when(dt):
    """``Sat 9:20 am``, the register and needs form."""
    return "%s %s" % (WEEKDAYS[dt.weekday()][:3], clock_text(dt, with_zone=False))


def long_when(dt):
    """``Sat 31 Oct 2026, 9:05 am EDT``, the head form."""
    return "%s %d %s %d, %s" % (WEEKDAYS[dt.weekday()][:3], dt.day, MONTHS[dt.month - 1][:3], dt.year,
                                clock_text(dt))


def reset_when(epoch):
    """``Wed 4 Nov 7:00 am EST`` for a reset time."""
    dt = local(epoch)
    return "%s %d %s %s" % (WEEKDAYS[dt.weekday()][:3], dt.day, MONTHS[dt.month - 1][:3], clock_text(dt))


def today(t=None):
    """ISO date in America/New_York."""
    return local(now() if t is None else t).date().isoformat()


def iso(t):
    return paths.iso(t)


# ---------------------------------------------------------------------------------------------------------------
# Locks and writes


def _lock_file(cfg, key):
    return os.path.join(cfg.locks_dir, hashlib.sha1(key.encode("utf-8")).hexdigest() + ".lock")


def state_json_path(direction_dir):
    """The direction ``state.json`` path, built from the realpath of the directory.

    ``state.mirror`` locks on the path ``register`` stored, which ``state.repo_root_for`` builds from the realpath of
    the session's cwd, so the two lock keys agree for a direction under a real ``docs/research`` directory.
    """
    return os.path.join(os.path.realpath(direction_dir), "state.json")


@contextlib.contextmanager
def state_lock(cfg, state_path):
    """The same lock ``state.mirror`` takes for this ``state.json`` path."""
    paths.ensure_state_root(cfg)
    with state.file_lock(_lock_file(cfg, state_path)):
        yield


@contextlib.contextmanager
def records_lock(cfg, direction_dir):
    """One lock per direction for worklog, ledger and job writes, so concurrent RS commands never lose a record."""
    paths.ensure_state_root(cfg)
    with state.file_lock(_lock_file(cfg, "records:" + os.path.realpath(direction_dir))):
        yield


def write_text_atomic(path, text, mode=0o664):
    """Replace ``path`` by a temporary file in the same directory; an existing file keeps its mode."""
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
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


def write_json(path, data):
    """RS JSON style (indent 2, sorted keys, trailing newline), written atomically."""
    write_text_atomic(path, state.dumps(data))


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def sentence(text):
    """``text`` with a final full stop added when it ends without one."""
    text = (text or "").strip()
    core = text.rstrip("\"')]")
    if not text or (core and core[-1] in ".!?:"):
        return text
    return text + "."
