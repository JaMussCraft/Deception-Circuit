"""Usage readings, segments, checkpoints and the Fable gap (spec 5.2 and 5.4; lane 4 section 2).

Claude reading: ``w = max(seven_day, Fable model_scoped row)`` and ``h = five_hour`` from ``usage.json``. Freshness
is per field: ``timestamp`` covers ``five_hour`` and ``seven_day``; ``model_scoped_fetched_at`` covers the Fable row.
A missing key reads as 0 only when its freshness stamp is fresh. A reading that is not fully fresh is first
refreshed by RS itself (R8, ``oauth_refresh``); it is unknown only when that refresh also fails.

Codex reading: ``codex-usage --pause-at 80`` JSON, cached for 120 s in the session file. Exit 1 or
``status: unknown`` means unknown. Codex reports no five-hour window, so its cap check uses the weekly reading only.

A reading is a plain dict, so the gate stays a pure function of (hook input, session, reading).
"""

import json
import math
import subprocess

from research_session import oauth_refresh, paths

STALE_SECONDS = 15 * 60
CAP_PERCENT = 80
FABLE_GAP_NOTICE = 5
CODEX_CACHE_SECONDS = 120
CODEX_TIMEOUT = 8
# Reset times from the status-line payload are whole seconds; the usage endpoint gives fractions. Differences up to
# this many seconds are the same window, so a refresh never opens a spurious segment.
RESET_TOLERANCE_SECONDS = 60
FIVE_HOUR_NOTE = "five-hour limit not applicable"


def _pct(value):
    """A usage percentage as a number, or None when malformed. Booleans and non-finite values are malformed."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _field(obj, *keys):
    for k in keys:
        obj = obj.get(k) if isinstance(obj, dict) else None
    return obj


def _fable_row(rows):
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, dict) and str(row.get("display_name", "")).strip().lower() == "fable":
            return row
    return None


def empty_reading(tool, source):
    return {
        "tool": tool, "source": source, "known": False,
        "five_hour": None, "seven_day": None, "fable": None, "w": None, "h": None, "resets_at": None,
        "fresh_main": False, "fresh_fable": False, "age_main": None, "age_fable": None,
        "fable_gap": None, "error": None, "five_hour_missing": False, "notes": [],
        "refresh_attempted": False, "refresh": None, "refresh_error": None, "cached": False,
    }


def parse_claude_usage(data, now, source="usage.json", stale=STALE_SECONDS):
    """Turn a loaded ``usage.json`` into a reading dict (no I/O)."""
    r = empty_reading("claude", source)
    if not isinstance(data, dict):
        r["error"] = "usage file is not a JSON object"
        return r
    rl = data.get("rate_limits") if isinstance(data.get("rate_limits"), dict) else {}
    ts = _pct(data.get("timestamp"))
    msf = _pct(rl.get("model_scoped_fetched_at"))
    if ts is not None:
        r["age_main"] = int(now - ts)
        r["fresh_main"] = (now - ts) <= stale
    if msf is not None:
        r["age_fable"] = int(now - msf)
        r["fresh_fable"] = (now - msf) <= stale
    malformed = []
    if r["fresh_main"]:
        for key in ("five_hour", "seven_day"):
            raw = _field(rl, key, "used_percentage")
            if raw is None and key == "five_hour":
                # R40 (revised): the five-hour limit was removed from the account on 2026-10-31. A missing key
                # means "not applicable": not 0, and not a reason to refresh. A present key is still capped.
                r["five_hour_missing"] = True
                r["notes"].append(FIVE_HOUR_NOTE)
                continue
            val = 0 if raw is None else _pct(raw)
            if val is None:
                malformed.append(key)
            r[key] = val
        r["resets_at"] = _pct(_field(rl, "seven_day", "resets_at"))
    if r["fresh_fable"]:
        row = _fable_row(rl.get("model_scoped"))
        raw = row.get("used_percentage") if row else None
        val = 0 if raw is None else _pct(raw)
        if val is None:
            malformed.append("Fable")
        r["fable"] = val
        if r["resets_at"] is None and row:
            r["resets_at"] = _pct(row.get("resets_at"))
    r["h"] = r["five_hour"]
    r["known"] = r["fresh_main"] and r["fresh_fable"] and not malformed
    if r["known"]:
        r["w"] = max(r["seven_day"], r["fable"])
    if r["seven_day"] is not None and r["fable"] is not None:
        r["fable_gap"] = r["fable"] - r["seven_day"]
    if malformed:
        r["error"] = "malformed value for %s" % ", ".join(malformed)
    elif not r["known"]:
        stale_parts = []
        if not r["fresh_main"]:
            stale_parts.append("timestamp %s" % ("missing" if r["age_main"] is None else "%d s old" % r["age_main"]))
        if not r["fresh_fable"]:
            stale_parts.append("model_scoped_fetched_at %s" % (
                "missing" if r["age_fable"] is None else "%d s old" % r["age_fable"]))
        r["error"] = "stale: " + "; ".join(stale_parts)
    return r


def _load_usage(path):
    try:
        with open(path, "r") as fh:
            return json.load(fh), None
    except (IOError, OSError):
        return None, "usage file missing or unreadable"
    except ValueError:
        return None, "usage file is not valid JSON"


def read_claude(cfg, now, refresh=True):
    """Read ``usage.json``; refresh through the OAuth endpoint when not fully fresh (R8).

    A fresh file without ``five_hour`` is fully fresh: the five-hour limit is not applicable (R40) and no refresh
    runs for it.
    """
    data, err = _load_usage(cfg.usage_file)
    r = parse_claude_usage(data, now, source=cfg.usage_file) if err is None else empty_reading("claude", cfg.usage_file)
    if err is not None:
        r["error"] = err
    if r["known"] or not refresh:
        return r
    result = oauth_refresh.refresh(cfg, now)
    data, err2 = _load_usage(cfg.usage_file)
    r2 = parse_claude_usage(data, now, source=cfg.usage_file) if err2 is None else r
    r2["refresh_attempted"] = True
    r2["refresh"] = result.how
    r2["refresh_error"] = result.error
    if not r2["known"] and result.error and not r2.get("error"):
        r2["error"] = result.error
    if err2 is not None and not r2.get("error"):
        r2["error"] = err2
    return r2


def run_codex_usage(binary, timeout=CODEX_TIMEOUT):
    """Run ``codex-usage --pause-at 80``; return ``(exit_code, parsed_json_or_None)``."""
    try:
        p = subprocess.run([binary, "--pause-at", str(CAP_PERCENT), "--timeout", str(timeout)],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout + 4,
                           universal_newlines=True)
    except (OSError, subprocess.SubprocessError):
        return 1, None
    try:
        data = json.loads(p.stdout)
    except ValueError:
        data = None
    return p.returncode, data if isinstance(data, dict) else None


def read_codex(cfg, now, cache=None, runner=None):
    """Return ``(reading, cache_entry)``. A cache entry younger than 120 s is reused without running the binary."""
    r = empty_reading("codex", cfg.codex_usage)
    if isinstance(cache, dict) and isinstance(cache.get("at"), (int, float)) and 0 <= now - cache["at"] < CODEX_CACHE_SECONDS:
        entry = cache
        r["cached"] = True
    else:
        code, data = (runner or run_codex_usage)(cfg.codex_usage)
        entry = {"at": now, "exit": code, "data": data}
    code, data = entry.get("exit"), entry.get("data")
    weekly = data.get("weekly") if isinstance(data, dict) else None
    used = _pct(weekly.get("used_percent")) if isinstance(weekly, dict) else None
    if code not in (0, 2) or not isinstance(data, dict) or data.get("status") == "unknown" or used is None:
        r["error"] = "codex-usage exit %s%s" % (code, (": " + str(data.get("error"))[:120]) if isinstance(data, dict) and data.get("error") else "")
        return r, entry
    r.update(known=True, fresh_main=True, fresh_fable=True, seven_day=used, w=used, h=None,
             resets_at=_pct(weekly.get("resets_at")), age_main=int(now - entry["at"]))
    return r, entry


def read(cfg, tool, now, session=None, refresh=True):
    """Reading for ``tool``; for Codex the session's cache entry is updated in place."""
    if tool == "codex":
        cache = (session or {}).get("codex_cache")
        reading, entry = read_codex(cfg, now, cache)
        if session is not None:
            session["codex_cache"] = entry
        return reading
    return read_claude(cfg, now, refresh=refresh)


# ---------------------------------------------------------------------------------------------------------------
# Segments and checkpoints


def update_segments(u, w, resets_at):
    """Lane 4 section 2: close the open segment on a reset change or a drop below ``last``; sum the increments."""
    segs = u.setdefault("segments", [])
    cur = segs[-1] if segs else None
    if cur is None:
        segs.append({"resets_at": resets_at, "baseline": w, "last": w})
    else:
        changed = (resets_at is not None and cur.get("resets_at") is not None
                   and abs(resets_at - cur["resets_at"]) > RESET_TOLERANCE_SECONDS)
        if changed or w < cur.get("last", 0):
            segs.append({"resets_at": resets_at, "baseline": w, "last": w})
        else:
            cur["last"] = w
            if cur.get("resets_at") is None:
                cur["resets_at"] = resets_at
    total = sum(s["last"] - s["baseline"] for s in segs)
    u["session_points"] = int(total) if float(total).is_integer() else round(total, 2)
    return u["session_points"]


def checkpoints_crossed(u):
    """Highest checkpoint N with ``session_points - points_at_register >= N * cadence``."""
    cadence = u.get("cadence") or 0
    if cadence <= 0:
        return 0
    return int((u.get("session_points", 0) - u.get("points_at_register", 0)) // cadence)


def advance_checkpoints(session, reading, now):
    """Record newly crossed checkpoints and set the freeze (registered sessions only). Returns new numbers."""
    from research_session import state  # local import: state does not import usage

    if not state.is_registered(session):
        return []
    u = session["usage"]
    crossed = checkpoints_crossed(u)
    new = []
    while u.get("next_checkpoint", 1) <= crossed:
        n = u.get("next_checkpoint", 1)
        session.setdefault("checkpoints", []).append({
            "n": n, "at": paths.iso(now), "session_points": u.get("session_points"),
            "all_models": reading.get("seven_day"), "fable": reading.get("fable"),
            "acked_at": None, "acked_by": None})
        u["next_checkpoint"] = n + 1
        new.append(n)
    if new and new[-1] > u.get("acked_through", 0):
        u["freeze"] = {"checkpoint": new[-1], "stage": "crossed", "crossed_at": paths.iso(now), "recorded_at": None}
    return new


def apply_reading(session, reading, now):
    """Store the reading; when known, update segments and (registered only) checkpoints. Returns new checkpoints."""
    u = session["usage"]
    u["last_reading"] = {"five_hour": reading.get("five_hour"), "seven_day": reading.get("seven_day"),
                         "fable": reading.get("fable"), "read_at": paths.iso(now), "fresh": bool(reading.get("known"))}
    if not reading.get("known"):
        return []
    update_segments(u, reading["w"], reading.get("resets_at"))
    return advance_checkpoints(session, reading, now)


def fable_notice(reading):
    """The D8 advisory text when the Fable row exceeds all-models by more than 5 points, else None."""
    gap = reading.get("fable_gap")
    if gap is None or gap <= FABLE_GAP_NOTICE:
        return None
    return ("Fable is %s points above all-models: delegate reading, analysis and review to Opus agents."
            % _fmt(gap))


def _fmt(v):
    if v is None:
        return "unknown"
    return str(int(v)) if float(v).is_integer() else "%.1f" % v


def format_reading(reading):
    """One line for humans and hook context."""
    if reading.get("tool") == "codex":
        return "Codex weekly %s%%" % _fmt(reading.get("w"))
    five = "five-hour not applicable" if reading.get("five_hour_missing") else \
        "five-hour %s%%" % _fmt(reading.get("five_hour"))
    return "%s, seven-day %s%%, Fable %s%%, weekly max %s%%" % (
        five, _fmt(reading.get("seven_day")), _fmt(reading.get("fable")), _fmt(reading.get("w")))


def stale_ok_active(session, now):
    until = paths.parse_iso(((session or {}).get("usage") or {}).get("stale_ok_until"))
    return until is not None and now < until


def describe_age(seconds):
    if seconds is None:
        return "of unknown age"
    if seconds < 120:
        return "%d s old" % seconds
    return "%d min old" % (seconds // 60)


def usage_file_age(reading):
    ages = [a for a in (reading.get("age_main"), reading.get("age_fable")) if a is not None]
    return max(ages) if ages else None
