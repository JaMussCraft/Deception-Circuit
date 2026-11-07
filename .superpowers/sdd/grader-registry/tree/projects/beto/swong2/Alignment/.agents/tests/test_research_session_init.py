"""Ticket 03: ``init`` (R39) and the head layout of a freshly created direction."""

import json
import os
import re
import unittest
from pathlib import Path

from _rs_records import SAT_0805, RecordsMixin
from _rs_testlib import RESET, RSTestCase
from test_research_session_worklog import rendered_head_labels, template_head_labels

from research_session import paths, registry, setup

FILES = sorted(setup.FILES)


def snapshot(root):
    out = {}
    for d, _, files in os.walk(str(root)):
        for f in files:
            p = os.path.join(d, f)
            out[os.path.relpath(p, str(root))] = Path(p).read_bytes()
    return out


class InitTest(RecordsMixin, RSTestCase):
    def setUp(self):
        super(InitTest, self).setUp()
        self.setup_root()
        self.set_clock(SAT_0805)
        self.write_json_file(self.root / "directions.json", {"schema": 1, "updated": "2026-10-30", "directions": []})

    def init(self, *argv):
        return self.run_cli("init", *argv, "--root", str(self.root))

    def test_fresh_slug_creates_seven_valid_files(self):
        before = snapshot(self.root)
        code, out, err = self.init("pilot-hooks", "--gpu-cap", "8", "--max-gpu-jobs", "1", "--api-cap", "5")
        self.assertEqual(code, 0, out + err)
        d = self.root / "pilot-hooks"
        self.assertEqual(sorted(os.listdir(str(d))), FILES)
        for name in ("state.json", "worklog.json", "ledger.json"):
            self.assertEqual(registry.validate_path(str(d / name)), ([], []), name)
        wl = self.read_json_file(d / "worklog.json")
        self.assertEqual(wl["directions"], [])
        self.assertEqual(wl["title"], "pilot-hooks")
        led = self.read_json_file(d / "ledger.json")
        self.assertEqual(led["caps"], {"reserved_gpu_hours": 8.0, "max_concurrent_gpu_jobs": 1, "paid_api_usd": 5.0})
        self.assertEqual(led["direction"], "pilot-hooks")
        st = self.read_json_file(d / "state.json")
        self.assertEqual((st["direction"], st["last_worklog_entry_at"]), ("pilot-hooks", paths.iso(SAT_0805)))
        text = (d / "WORKLOG.md").read_text()
        self.assertNotIn("Plain name", text + json.dumps(wl))
        self.assertNotIn("<", text.split("## Log")[0].replace("<!--", "").replace("<br>", ""))
        self.assertIn("**8:05 am EDT · Direction created.**", text)
        self.assertIn("# Resume: pilot-hooks", (d / "RESUME.md").read_text())
        self.assertEqual((d / "START.md").read_bytes(), (self.root / "_templates" / "START.md").read_bytes())
        rows = self.read_json_file(self.root / "directions.json")["directions"]
        self.assertEqual([(r["id"], r["status"], r["claimed_by"]) for r in rows], [("pilot-hooks", "proposed", None)])
        self.assertEqual(rows[0]["state"], "docs/research/pilot-hooks/state.json")
        self.assertEqual(registry.validate_path(str(self.root / "directions.json")), ([], []))
        after = snapshot(self.root)
        changed = sorted(k for k in after if before.get(k) != after[k])
        self.assertTrue(all(k.startswith("pilot-hooks/") or k == "directions.json" for k in changed), changed)
        from research_session import lint
        for name in ("WORKLOG.md", "README.md"):
            self.assertEqual(lint.lint_text((d / name).read_text()), [], name)

    def test_from_start_copies_bytes_and_title(self):
        start = Path(self.tmp) / "my-start.md"
        start.write_bytes(b"Preamble line.\n# Does the clause reader generalize?\n\nBody text, kept   byte for byte.\n")
        code, out, err = self.init("clause-reader", "--from-start", str(start))
        self.assertEqual(code, 0, err)
        d = self.root / "clause-reader"
        self.assertEqual((d / "START.md").read_bytes(), start.read_bytes())
        self.assertEqual(self.read_json_file(d / "worklog.json")["title"], "Does the clause reader generalize?")
        self.assertIn("# Worklog: Does the clause reader generalize?", (d / "WORKLOG.md").read_text())
        self.assertIn("# Does the clause reader generalize?", (d / "README.md").read_text())

    def test_second_init_refuses_and_missing_only(self):
        self.assertEqual(self.init("demo")[0], 0)
        code, out, err = self.init("demo")
        self.assertEqual(code, 1)
        for name in FILES:
            self.assertIn(name, err)
        d = self.root / "demo"
        os.unlink(str(d / "RESUME.md"))
        os.unlink(str(d / "ledger.json"))
        keep = {n: (d / n).read_bytes() for n in os.listdir(str(d))}
        code, out, err = self.init("demo", "--missing-only")
        self.assertEqual(code, 0, err)
        self.assertIn("created RESUME.md, ledger.json", out)
        for n, b in keep.items():
            self.assertEqual((d / n).read_bytes(), b, n)
        self.assertEqual(len(self.read_json_file(self.root / "directions.json")["directions"]), 1)

    def test_init_head_layout_matches_template(self):
        self.assertEqual(self.init("demo")[0], 0)
        d = self.root / "demo"
        st = self.read_json_file(d / "state.json")
        st["sessions"]["claude-b2cb53cd"] = {
            "tool": "claude", "session_id": "b2cb53cd", "started_at": paths.iso(SAT_0805), "compactions": 1,
            "usage": {"cadence": 16, "points_at_register": 2, "session_points": 18, "next_checkpoint": 2,
                      "acked_through": 1, "segments": [{"resets_at": RESET, "baseline": 9, "last": 27}],
                      "freeze": None,
                      "last_reading": {"five_hour": None, "seven_day": 27, "fable": 33, "read_at": paths.iso(SAT_0805),
                                       "fresh": True}},
            "checkpoints": [{"n": 1, "at": paths.iso(SAT_0805), "session_points": 18, "all_models": 27, "fable": 33,
                             "acked_at": paths.iso(SAT_0805), "acked_by": "prompt"}]}
        self.write_json_file(d / "state.json", st)
        self.run_cli("worklog-append", str(d), "--kind", "entry", "--title", "Registered", "--body", "Checkpoints apply.")
        text = (d / "WORKLOG.md").read_text()
        labels = template_head_labels()
        self.assertEqual(len(labels), 11)
        self.assertEqual(rendered_head_labels(text), labels)
        self.assertIn("| Weekly usage, all models | account reads 27%; +16 points this session |", text)
        self.assertIn("| Weekly usage, Fable | account reads 33%; 6 points above all models, so reading, analysis and "
                      "review go to Opus agents |", text)
        self.assertIn("| Review checkpoints | 1 of 1 acknowledged; next at +32 session points; cadence 16 points; cap "
                      "pause at 80% |", text)
        sections = re.findall(r"^## (.+)$", text, re.M)
        template_sections = re.findall(r"^## (.+)$", (self.root / "_templates" / "WORKLOG.md").read_text(), re.M)
        self.assertEqual(sections, template_sections)
        self.assertEqual(self.read_json_file(d / "state.json")["sessions"]["claude-b2cb53cd"]["compactions"], 1)


if __name__ == "__main__":
    unittest.main()
