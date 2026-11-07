"""Helpers for the ticket 03 record tests: fixed clocks, fixture research roots and the real templates.

The templates are read from the first directory that exists in this list, and copied into the test's temporary
research root. Nothing is ever written next to the real templates.

1. ``RESEARCH_SESSION_TEMPLATES`` when set;
2. ``Deception-Circuit/docs/research/_templates`` in the main checkout (present after the DC merge);
3. the autoresearch-workflow worktree's ``docs/research/_templates`` (present before the merge).

If none exists the tests fail with the list of paths tried; they never skip silently.
"""

import datetime
import json
import os
import shutil
from pathlib import Path

from _rs_testlib import RSTestCase  # noqa: F401  (re-exported for the test modules)

TEMPLATE_CANDIDATES = (
    "/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/_templates",
    "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates",
)


def templates_dir():
    tried = []
    env = os.environ.get("RESEARCH_SESSION_TEMPLATES")
    for cand in ([env] if env else []) + list(TEMPLATE_CANDIDATES):
        tried.append(cand)
        if os.path.isfile(os.path.join(cand, "WORKLOG.md")):
            return cand
    raise AssertionError("no _templates directory found; tried: " + ", ".join(tried))


def epoch(year, month, day, hour, minute, zone="America/New_York"):
    """Epoch seconds of a wall-clock time in America/New_York."""
    from zoneinfo import ZoneInfo
    return datetime.datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(zone)).timestamp()


SAT_0805 = epoch(2026, 10, 31, 8, 5)   # EDT
SUN_0805 = epoch(2026, 11, 1, 8, 5)    # EST, after the 2 am change


class RecordsMixin(object):
    """Mixed into ``RSTestCase``: a research root under the test's DC root with the real templates copied in."""

    def setup_root(self, with_templates=True):
        self.root = self.DC / "docs" / "research"
        self.root.mkdir(parents=True, exist_ok=True)
        if with_templates:
            shutil.copytree(templates_dir(), str(self.root / "_templates"))
        return self.root

    def set_clock(self, t):
        os.environ["RESEARCH_SESSION_NOW"] = repr(float(t))
        self.addCleanup(os.environ.pop, "RESEARCH_SESSION_NOW", None)

    def write_json_file(self, path, data):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

    def read_json_file(self, path):
        return json.loads(Path(path).read_text())

    def make_direction(self, slug="demo", worklog=None, ledger=None, state_json=None):
        """A direction directory with ``worklog.json``, ``ledger.json`` and ``state.json`` (fixtures, not RS)."""
        d = self.root / slug
        d.mkdir(parents=True, exist_ok=True)
        wl = {"schema": 1, "title": "Demo session", "state": "Running", "right_now": "Nothing is running yet.",
              "directions": [{"name": "Demo direction", "state": "active"}], "terms": [],
              "budgets": {"gpu": "", "openrouter": ""}, "transcripts": "Claude session demo",
              "needs": [], "findings": [], "incidents": []}
        wl.update(worklog or {})
        self.write_json_file(d / "worklog.json", wl)
        led = {"schema": 1, "direction": slug,
               "caps": {"reserved_gpu_hours": 20.0, "paid_api_usd": 10.0, "max_concurrent_gpu_jobs": 2},
               "totals": {"reserved_gpu_hours": 0.0, "actual_gpu_seconds": 0, "api_usd_known": 0.0,
                          "api_usd_reserve": 0.0},
               "reservations": [], "api_calls": [], "converted_from": None}
        if ledger is not False:
            led.update(ledger or {})
            self.write_json_file(d / "ledger.json", led)
        st = {"schema": 1, "direction": slug, "session_state": "running", "last_worklog_entry_at": None,
              "sessions": {}, "jobs": []}
        if state_json is not False:
            st.update(state_json or {})
            self.write_json_file(d / "state.json", st)
        return d

    def head_and_log(self, text):
        i = text.index("\n## Log\n")
        return text[:i + 1], text[i + len("\n## Log\n"):]
