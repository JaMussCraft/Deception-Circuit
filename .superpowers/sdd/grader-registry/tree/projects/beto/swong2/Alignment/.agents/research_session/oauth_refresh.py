"""Refresh a stale ``usage.json`` from the OAuth usage endpoint (rulings R8 and R27).

This replicates the status line's refresh (``~/.claude/statusline.sh``, ``refresh_oauth_cache`` and the
``model_scoped`` mapping) in Python, with the same files:

- cache ``~/.claude/.usage_oauth_cache.json`` as ``{"fetched_at": <epoch>, "body": {...}}`` (or ``"error"``);
- lock directory ``~/.claude/.usage_oauth_cache.lock``, swept when older than 60 s;
- retry floor: no fetch while the cache file's mtime is younger than 300 s (a failed fetch touches it).

The token is read inside this process by ``read_token``, the one function that opens the credentials file. It is
passed only to ``http_get`` in a request header. It never reaches output, logs, exception text, ``argv`` or a child
process. Error strings are built from fixed text, HTTP status codes and exception class names only.

RS never calls ``statusline.sh`` (R8): a status-line call with an empty payload would drop ``five_hour``.
"""

import datetime
import json
import os
import re
import socket
import tempfile
import time
import urllib.error
import urllib.request

RETRY_FLOOR_SECONDS = 300
LOCK_STALE_SECONDS = 60
TIMEOUT_SECONDS = 8
STALE_BODY_SECONDS = 15 * 60


class FetchError(Exception):
    """A fetch failure whose message is safe to show (no token, no response text)."""


class RefreshResult(object):
    def __init__(self, ok, how, error=None, fetched_at=None):
        self.ok = ok
        self.how = how  # "fetched", "cache", "skipped" or "failed"
        self.error = error
        self.fetched_at = fetched_at

    def __repr__(self):
        return "RefreshResult(ok=%r, how=%r, error=%r)" % (self.ok, self.how, self.error)


def read_token(path):
    """The credentials reader: ``(access_token, expires_at_epoch_or_None)``. Tests replace this function."""
    with open(path, "r") as fh:
        data = json.load(fh)
    oauth = (data or {}).get("claudeAiOauth") or {}
    token = oauth.get("accessToken") or ""
    exp = oauth.get("expiresAt")
    expires = exp / 1000.0 if isinstance(exp, (int, float)) and not isinstance(exp, bool) else None
    return token, expires


def http_get(url, token, timeout):
    """GET the usage endpoint with ``urllib``; return the JSON body dict or raise ``FetchError``."""
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "anthropic-beta": "oauth-2025-04-20",
        "Content-Type": "application/json",
        "User-Agent": "research-session",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        raise FetchError("http %d" % exc.code) from None
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            raise FetchError("timeout after %d s" % timeout) from None
        raise FetchError("network error (%s)" % type(exc.reason).__name__) from None
    except socket.timeout:
        raise FetchError("timeout after %d s" % timeout) from None
    except Exception as exc:
        raise FetchError("fetch failed (%s)" % type(exc).__name__) from None
    if status != 200:
        raise FetchError("http %s" % status)
    try:
        body = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise FetchError("response is not JSON") from None
    if not isinstance(body, dict):
        raise FetchError("response is not a JSON object")
    return body


# ---------------------------------------------------------------------------------------------------------------
# Mapping the endpoint body into usage.json (statusline.sh, python branch)

_FRACTION_RE = re.compile(r"\.[0-9]+")


def to_epoch(value):
    """Epoch seconds (int) of a number or an ISO string; the fraction is dropped as the status line does."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str) or not value.strip():
        return None
    x = _FRACTION_RE.sub("", value.strip())
    if x.endswith("Z"):
        x = x[:-1] + "+00:00"
    try:
        dt = datetime.datetime.fromisoformat(x)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return int(dt.timestamp())


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def map_body(body):
    """Return ``(five_hour, seven_day, model_scoped)`` from an endpoint body; each part may be None."""
    limits = body.get("limits") if isinstance(body.get("limits"), list) else []
    by_kind = {}
    for row in limits:
        if isinstance(row, dict) and row.get("kind") not in by_kind:
            by_kind[row.get("kind")] = row

    def window(key, kind):
        w = body.get(key)
        if isinstance(w, dict) and _num(w.get("utilization")) is not None:
            return {"used_percentage": w["utilization"], "resets_at": to_epoch(w.get("resets_at"))}
        row = by_kind.get(kind)
        if row and _num(row.get("percent")) is not None:
            return {"used_percentage": row["percent"], "resets_at": to_epoch(row.get("resets_at"))}
        return None

    model_scoped = None
    if isinstance(body.get("limits"), list):
        model_scoped = []
        for row in limits:
            if not isinstance(row, dict) or row.get("kind") != "weekly_scoped":
                continue
            name = ((row.get("scope") or {}).get("model") or {}).get("display_name") if isinstance(
                row.get("scope"), dict) else None
            if not isinstance(name, str):
                continue
            model_scoped.append({"display_name": name, "used_percentage": row.get("percent"),
                                 "resets_at": to_epoch(row.get("resets_at"))})
    return window("five_hour", "session"), window("seven_day", "weekly_all"), model_scoped


def _atomic_write(path, text, mode=0o600):
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + ".", suffix=".rs-tmp", dir=directory)
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def merge_into_usage(usage_path, body, fetched_at):
    """Merge the endpoint rows into ``usage.json`` by atomic replace, keeping every existing key.

    ``five_hour`` and ``seven_day`` update their sub-keys and set ``timestamp``; the weekly-scoped rows replace
    ``model_scoped`` and set ``model_scoped_fetched_at``. A part is written only when the fetch is not older than the
    stamp already in the file, so a newer status-line write is never regressed. One exception: a window that is
    absent from the file is filled from the fetch even when the fetch is older, without moving ``timestamp``. The
    file is not rewritten when nothing changes.
    """
    try:
        with open(usage_path, "r") as fh:
            original = fh.read()
        data = json.loads(original)
        if not isinstance(data, dict):
            data = {}
    except (IOError, OSError, ValueError):
        original = None
        data = {}
    before = json.dumps(data, sort_keys=True)
    rl = data.get("rate_limits")
    rl = dict(rl) if isinstance(rl, dict) else {}
    five, seven, model_scoped = map_body(body)
    ts_old = _num(data.get("timestamp"))
    newer = ts_old is None or fetched_at >= ts_old
    for key, part in (("five_hour", five), ("seven_day", seven)):
        if part is None:
            continue
        absent = not isinstance(rl.get(key), dict) or rl[key].get("used_percentage") is None
        if newer or absent:
            entry = dict(rl.get(key)) if isinstance(rl.get(key), dict) else {}
            entry.update(part)
            rl[key] = entry
    if (five or seven) and newer:
        data["timestamp"] = fetched_at
    msf_old = _num(rl.get("model_scoped_fetched_at"))
    if model_scoped is not None and (msf_old is None or fetched_at >= msf_old):
        rl["model_scoped"] = model_scoped
        rl["model_scoped_fetched_at"] = fetched_at
    data["rate_limits"] = rl
    if original is not None and json.dumps(data, sort_keys=True) == before:
        return
    _atomic_write(usage_path, json.dumps(data, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------------------------------------------
# Cache and lock


def _load_cache(path):
    try:
        with open(path, "r") as fh:
            data = json.load(fh)
    except (IOError, OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _safe_error_text(value):
    """Cache ``error`` strings come from the status line or from us; keep them short and printable."""
    text = re.sub(r"[^A-Za-z0-9 ._()-]", "", str(value))[:60]
    return text or "unknown error"


def acquire_lock(lock_path, now):
    """mkdir lock as in the status line. A lock older than 60 s is swept. Returns True when acquired."""
    try:
        os.mkdir(lock_path, 0o700)
        return True
    except FileExistsError:
        pass
    except OSError:
        return False
    try:
        age = now - os.stat(lock_path).st_mtime
    except OSError:
        age = LOCK_STALE_SECONDS
    if age < LOCK_STALE_SECONDS:
        return False
    try:
        os.rmdir(lock_path)
    except OSError:
        pass
    try:
        os.mkdir(lock_path, 0o700)
        return True
    except OSError:
        return False


def release_lock(lock_path):
    try:
        os.rmdir(lock_path)
    except OSError:
        pass


def _record_failure(cache_path, now, message):
    """Like the status line: keep a good body and bump its mtime (retry timer); otherwise record the error."""
    cache = _load_cache(cache_path)
    if cache is not None and isinstance(cache.get("body"), dict):
        try:
            os.utime(cache_path, (now, now))
        except OSError:
            pass
    else:
        try:
            _atomic_write(cache_path, json.dumps({"fetched_at": int(now), "error": message}, separators=(",", ":")) + "\n")
        except OSError:
            pass
    return RefreshResult(False, "failed", message)


def refresh(cfg, now=None):
    """Refresh ``cfg.usage_file`` from the cache or the endpoint. Never raises; returns a ``RefreshResult``."""
    now = time.time() if now is None else now
    try:
        return _refresh(cfg, now)
    except Exception as exc:  # never let a refresh problem escape with details
        return RefreshResult(False, "failed", "refresh error (%s)" % type(exc).__name__)


def _refresh(cfg, now):
    cache_path = cfg.oauth_cache
    try:
        mtime = os.stat(cache_path).st_mtime
    except OSError:
        mtime = None
    if mtime is not None and now - mtime < RETRY_FLOOR_SECONDS:
        cache = _load_cache(cache_path)
        fetched = _num((cache or {}).get("fetched_at"))
        wait = int(RETRY_FLOOR_SECONDS - (now - mtime))
        if cache is not None and isinstance(cache.get("body"), dict) and fetched is not None \
                and now - fetched <= STALE_BODY_SECONDS:
            merge_into_usage(cfg.usage_file, cache["body"], int(fetched))
            return RefreshResult(True, "cache", None, int(fetched))
        if cache is not None and cache.get("error"):
            why = "last fetch failed (%s)" % _safe_error_text(cache["error"])
        elif cache is not None and isinstance(cache.get("body"), dict):
            why = "last fetch failed; cached body is %d s old" % int(now - (fetched or 0))
        else:
            why = "cache unreadable"
        return RefreshResult(False, "skipped", "retry floor: %s; next fetch in %d s" % (why, max(wait, 1)))
    if not acquire_lock(cfg.oauth_lock, now):
        return RefreshResult(False, "skipped", "another process holds the usage-fetch lock (under 60 s old)")
    try:
        try:
            token, expires = read_token(cfg.credentials)
        except Exception as exc:
            return _record_failure(cache_path, now, "credentials unreadable (%s)" % type(exc).__name__)
        if not token:
            return _record_failure(cache_path, now, "no token")
        if expires is not None and expires <= now:
            return _record_failure(cache_path, now, "token expired")
        try:
            body = http_get(cfg.oauth_url, token, TIMEOUT_SECONDS)
        except FetchError as exc:
            return _record_failure(cache_path, now, str(exc.args[0]) if exc.args else "fetch failed")
        except socket.timeout:
            return _record_failure(cache_path, now, "timeout after %d s" % TIMEOUT_SECONDS)
        except Exception as exc:
            return _record_failure(cache_path, now, "fetch failed (%s)" % type(exc).__name__)
        finally:
            token = None
        if not isinstance(body, dict):
            return _record_failure(cache_path, now, "response is not a JSON object")
        fetched_at = int(now)
        _atomic_write(cache_path, json.dumps({"fetched_at": fetched_at, "body": body}, separators=(",", ":")) + "\n")
        merge_into_usage(cfg.usage_file, body, fetched_at)
        return RefreshResult(True, "fetched", None, fetched_at)
    finally:
        release_lock(cfg.oauth_lock)
