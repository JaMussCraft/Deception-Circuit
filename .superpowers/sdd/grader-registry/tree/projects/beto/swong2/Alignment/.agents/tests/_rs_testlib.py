"""Shared helpers for the research-session tests (ticket 02).

Every path lives in a temporary directory. The real ``~/.claude`` is never read: the credentials path points at a
missing file, and ``oauth_refresh.read_token`` and ``oauth_refresh.http_get`` are replaced by functions that fail
the test unless a test installs its own mock.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

PKG_PARENT = Path(__file__).resolve().parents[1]
if str(PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(PKG_PARENT))

from research_session import oauth_refresh, paths, state  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
RESET = 1793797200  # a weekly reset time, as in spec 4.5


def fake_token():
    """A synthetic token, assembled at run time so the source holds no token-shaped literal."""
    return "sk-" + "ant-" + "oat01-" + "PLANTED" + "x" * 24 + "TOKENFAKE"


class RSTestCase(unittest.TestCase):
    """Temporary state root, Alignment root, DC root, usage file, cache, lock and codex-usage path."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rs-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        t = Path(self.tmp)
        self.A = t / "Alignment"
        self.DC = self.A / "Deception-Circuit"
        (self.DC / "docs" / "research").mkdir(parents=True)
        (t / "claude").mkdir()
        (t / "bin").mkdir()
        self.cfg = paths.Config(
            state_root=str(t / "state"), alignment_root=str(self.A), dc_root=str(self.DC),
            usage_file=str(t / "claude" / "usage.json"),
            oauth_cache=str(t / "claude" / ".usage_oauth_cache.json"),
            oauth_lock=str(t / "claude" / ".usage_oauth_cache.lock"),
            credentials=str(t / "claude" / "no-credentials-here.json"),
            codex_usage=str(t / "bin" / "codex-usage"),
            oauth_url="https://usage.invalid/api/oauth/usage")
        self.env = {
            "RESEARCH_SESSION_ROOT": self.cfg.state_root,
            "RESEARCH_SESSION_ALIGNMENT_ROOT": self.cfg.alignment_root,
            "RESEARCH_SESSION_DC_ROOT": self.cfg.dc_root,
            "RESEARCH_SESSION_USAGE_FILE": self.cfg.usage_file,
            "RESEARCH_SESSION_OAUTH_CACHE": self.cfg.oauth_cache,
            "RESEARCH_SESSION_OAUTH_LOCK": self.cfg.oauth_lock,
            "RESEARCH_SESSION_CREDENTIALS": self.cfg.credentials,
            "RESEARCH_SESSION_CODEX_USAGE": self.cfg.codex_usage,
        }
        env_patch = mock.patch.dict(os.environ, self.env)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.token_calls = []
        self.http_calls = []
        self.token_reader = None
        self.http = None

        def guarded_reader(path):
            self.token_calls.append(path)
            if self.token_reader is None:
                raise AssertionError("credentials reader called without a mock")
            return self.token_reader(path)

        def guarded_http(url, token, timeout):
            self.http_calls.append((url, timeout))
            if self.http is None:
                raise AssertionError("usage endpoint called without a mock")
            return self.http(url, token, timeout)

        for name, fn in (("read_token", guarded_reader), ("http_get", guarded_http)):
            p = mock.patch.object(oauth_refresh, name, fn)
            p.start()
            self.addCleanup(p.stop)
        self.now = time.time()

    # -- usage.json and the OAuth cache

    def write_usage(self, five=9, seven=11, fable=17, age=0, fable_age=None, resets=RESET, drop=(), extra=None):
        fable_age = age if fable_age is None else fable_age
        rl = {"five_hour": {"used_percentage": five, "resets_at": resets - 6 * 86400},
              "seven_day": {"used_percentage": seven, "resets_at": resets},
              "model_scoped": [{"display_name": "Fable", "used_percentage": fable, "resets_at": resets}],
              "model_scoped_fetched_at": int(self.now - fable_age)}
        for key in drop:
            rl.pop(key, None)
        data = {"rate_limits": rl, "timestamp": int(self.now - age)}
        if extra:
            data.update(extra)
        Path(self.cfg.usage_file).write_text(json.dumps(data))
        return data

    def read_usage_file(self):
        return json.loads(Path(self.cfg.usage_file).read_text())

    def body(self, five=30, seven=40, fable=45):
        return {
            "five_hour": {"utilization": five, "resets_at": "2026-11-01T02:00:00.317000+00:00"},
            "seven_day": {"utilization": seven, "resets_at": "2026-11-04T12:00:00.317000+00:00"},
            "limits": [
                {"kind": "session", "percent": five, "resets_at": "2026-11-01T02:00:00.317000+00:00", "scope": None},
                {"kind": "weekly_all", "percent": seven, "resets_at": "2026-11-04T12:00:00.317000+00:00",
                 "scope": None},
                {"kind": "weekly_scoped", "percent": fable, "resets_at": "2026-11-04T12:00:00.317000+00:00",
                 "scope": {"model": {"id": None, "display_name": "Fable"}, "surface": None}},
            ],
        }

    def write_cache(self, body=None, fetched_age=0, mtime_age=None, error=None):
        data = {"fetched_at": int(self.now - fetched_age)}
        if error:
            data["error"] = error
        else:
            data["body"] = body if body is not None else self.body()
        Path(self.cfg.oauth_cache).write_text(json.dumps(data))
        m = self.now - (fetched_age if mtime_age is None else mtime_age)
        os.utime(self.cfg.oauth_cache, (m, m))

    # -- sessions

    def make_session(self, sid="0123456789abcdef", tool="claude", cwd=None, points=0, cadence=None,
                     registered=False, slug="demo", freeze=None, acked_through=0, w_last=None):
        cwd = cwd or str(self.DC)
        os.makedirs(cwd, exist_ok=True)
        s = state.new_session(tool, sid, cwd, self.now)
        u = s["usage"]
        if cadence:
            u["cadence"] = cadence
        last = 10 + points if w_last is None else w_last
        u["segments"] = [{"resets_at": RESET, "baseline": last - points, "last": last}]
        u["session_points"] = points
        u["acked_through"] = acked_through
        if registered:
            s["register"] = {"slug": slug, "at": paths.iso(self.now),
                             "state_path": state.direction_state_path(self.cfg, slug, cwd)}
            u["points_at_register"] = 0
        if freeze:
            u["freeze"] = {"checkpoint": freeze[0], "stage": freeze[1], "crossed_at": paths.iso(self.now),
                           "recorded_at": paths.iso(self.now) if freeze[1] == "recorded" else None}
            u["next_checkpoint"] = freeze[0] + 1
        paths.ensure_state_root(self.cfg)
        state.write_json_atomic(self.cfg.session_file(tool, sid), s)
        return s

    def session(self, sid="0123456789abcdef", tool="claude"):
        return state.load_session(self.cfg, tool, sid)

    def write_directions(self, rows):
        Path(self.cfg.directions_file).write_text(json.dumps({"schema": 1, "updated": "2026-10-31",
                                                              "directions": rows}))

    # -- CLI in process

    def run_cli(self, *argv):
        from research_session import cli
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    # -- a fake codex-usage executable

    def fake_codex_usage(self, exit_code, payload):
        counter = Path(self.tmp) / "codex-calls"
        script = ("#!" + sys.executable + "\n"
                  "import json, sys\n"
                  "p = " + repr(str(counter)) + "\n"
                  "open(p, 'a').write('x')\n"
                  "print(json.dumps(" + repr(payload) + "))\n"
                  "sys.exit(" + str(int(exit_code)) + ")\n")
        Path(self.cfg.codex_usage).write_text(script)
        os.chmod(self.cfg.codex_usage, 0o700)
        return counter

    def codex_calls(self):
        counter = Path(self.tmp) / "codex-calls"
        return len(counter.read_text()) if counter.exists() else 0
