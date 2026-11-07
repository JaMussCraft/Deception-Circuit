"""Ticket 03: ``worklog-append`` (every kind, checkpoint block, import) and ``worklog-set``."""

import json
import os
import re
import shutil
import unittest
from pathlib import Path

from _rs_records import SAT_0805, SUN_0805, RecordsMixin, epoch, templates_dir
from _rs_testlib import FIXTURES, RESET, RSTestCase

from research_session import paths, records, registry, state, worklog

GLUED = (FIXTURES / "lint" / "glued_memory_line29.md").read_text().strip()


def template_head_labels():
    """Row labels of the head table in ``_templates/WORKLOG.md``, parsed at test time."""
    text = Path(templates_dir(), "WORKLOG.md").read_text()
    head = text.split("\n## ", 1)[0]
    return [m.group(1).strip() for m in re.finditer(r"^\| ([^|]+?) \| .* \|$", head, re.M)]


def rendered_head_labels(text):
    head = text.split("\n## Log\n", 1)[0].split("\n## ", 1)[0]
    return [m.group(1).strip() for m in re.finditer(r"^\| ([^|]+?) \| .* \|$", head, re.M)]


class WorklogBase(RecordsMixin, RSTestCase):
    def setUp(self):
        super(WorklogBase, self).setUp()
        self.setup_root(with_templates=False)
        self.set_clock(SAT_0805)
        self.d = self.make_direction("demo")

    def append(self, *extra, **kw):
        code, out, err = self.run_cli("worklog-append", str(self.d), *extra)
        if kw.get("ok", True):
            self.assertEqual(code, 0, out + err)
        return code, out, err

    def text(self):
        return (self.d / "WORKLOG.md").read_text()

    def wl(self):
        return self.read_json_file(self.d / "worklog.json")


class AppendTest(WorklogBase):
    def test_day_headings_times_and_log_prefix(self):
        self.append("--kind", "entry", "--title", "Session started", "--body", "Goal: one sentence.")
        first = self.text()
        self.assertIn("### Saturday 31 October 2026\n**8:05 am EDT · Session started.** Goal: one sentence.\n",
                      first)
        _, log1 = self.head_and_log(first)
        self.set_clock(epoch(2026, 10, 31, 9, 40))
        self.append("--kind", "handback", "--title", "Plan written", "--body", "The planner handed back.")
        _, log2 = self.head_and_log(self.text())
        self.assertTrue(log2.startswith(log1))
        self.assertEqual(log2[len(log1):], "**9:40 am EDT · Hand-back: Plan written.** The planner handed back.\n")
        self.set_clock(SUN_0805)
        self.append("--kind", "decision", "--title", "User decision", "--body", "Approved.")
        _, log3 = self.head_and_log(self.text())
        self.assertTrue(log3.startswith(log2))
        self.assertEqual(log3[len(log2):], "\n### Sunday 1 November 2026\n**8:05 am EST · User decision.** Approved.\n")
        st = self.read_json_file(self.d / "state.json")
        self.assertEqual(st["last_worklog_entry_at"], paths.iso(SUN_0805))
        self.assertEqual(registry.validate_worklog(self.wl())[0], [])

    def test_head_regeneration_keeps_log_bytes(self):
        self.append("--kind", "entry", "--title", "Session started", "--body", "Goal: one sentence.")
        # A legacy log line that the current renderer would never write stays byte for byte.
        text = self.text()
        odd = "**8:06 am EDT · Odd   spacing kept.**  Two  spaces stay.\n"
        (self.d / "WORKLOG.md").write_text(text + odd)
        self.append("--kind", "switch", "--title", "Switched to the fallback", "--body", "The queue stalled.")
        head, log = self.head_and_log(self.text())
        _, old_log = self.head_and_log(text + odd)
        self.assertTrue(log.startswith(old_log))
        self.assertEqual(rendered_head_labels(self.text()), template_head_labels())

    def test_registers_allocate_numbers(self):
        for i in (1, 2):
            self.append("--kind", "finding", "--plain", "Finding %d holds in 23 of 48 stories." % i,
                        "--setup", "The model was asked to lie; we measured the rate.", "--strength", "reviewed",
                        "--evidence", "reports/05-analysis.md section %d" % i)
            self.append("--kind", "need", "--text", "Approve plan %d?" % i, "--default", "the session waits")
            self.append("--kind", "incident", "--what", "Worker %d stopped on the spend limit." % i,
                        "--effect", "15 minutes lost", "--fix", "resumed from its hand-back")
        wl = self.wl()
        self.assertEqual([f["id"] for f in wl["findings"]], ["F1", "F2"])
        self.assertEqual([n["id"] for n in wl["needs"]], ["N1", "N2"])
        self.assertEqual([p["id"] for p in wl["incidents"]], ["P1", "P2"])
        text = self.text()
        self.assertIn("| F2 | Sat 8:05 am | Finding 2 holds in 23 of 48 stories. |", text)
        self.assertIn("- N2 (Sat 8:05 am): Approve plan 2? Default if no answer: the session waits.", text)
        self.assertIn("| P2 | Sat 8:05 am | Worker 2 stopped on the spend limit. | 15 minutes lost |", text)
        self.assertIn("**8:05 am EDT · Need N2 opened.**", text)
        self.assertIn("**8:05 am EDT · Process incident P2.**", text)
        self.assertIn("**8:05 am EDT · Finding F2 recorded.**", text)
        self.assertIn("| Open needs from you | 2, see below |", text)

    def test_need_resolved(self):
        self.append("--kind", "need", "--text", "Approve the plan?", "--default", "the session waits")
        self.append("--kind", "need", "--text", "Pick a seed?", "--default", "seed 42")
        self.set_clock(epoch(2026, 10, 31, 9, 30))
        self.append("--kind", "need-resolved", "--id", "N1", "--answer", "approved, with \"drop the MLP grid\"")
        text = self.text()
        self.assertIn("- ~~N1 (Sat 8:05 am): Approve the plan?~~ Answered Sat 9:30 am: approved, with "
                      "\"drop the MLP grid\".", text)
        self.assertIn("- N2 (Sat 8:05 am): Pick a seed?", text)
        self.assertIn("**9:30 am EDT · Need N1 answered.**", text)
        self.assertIn("| Open needs from you | 1, see below |", text)
        before = self.text()
        code, out, err = self.append("--kind", "need-resolved", "--id", "N1", "--answer", "again", ok=False)
        self.assertEqual(code, 1)
        self.assertIn("already answered", err)
        code, out, err = self.append("--kind", "need-resolved", "--id", "N9", "--answer", "x", ok=False)
        self.assertEqual(code, 1)
        self.assertIn("unknown", err)
        self.assertEqual(self.text(), before)

    def test_glued_body_refused_before_write(self):
        self.append("--kind", "entry", "--title", "Session started", "--body", "Goal: one sentence.")
        before_md, before_json = self.text(), (self.d / "worklog.json").read_text()
        code, out, err = self.append("--kind", "entry", "--title", "Glued", "--body", GLUED, ok=False)
        self.assertEqual(code, 1)
        self.assertRegex(err, r"WORKLOG\.md:\d+: (join|long-token):")
        self.assertEqual(self.text(), before_md)
        self.assertEqual((self.d / "worklog.json").read_text(), before_json)
        code, out, err = self.append("--kind", "finding", "--plain", GLUED, "--setup", "s", "--strength",
                                     "preliminary", "--evidence", "e", ok=False)
        self.assertEqual(code, 1)
        self.assertEqual(self.wl()["findings"], [])

    def test_preexisting_glued_log_line_does_not_block(self):
        self.append("--kind", "entry", "--title", "Session started", "--body", "Goal: one sentence.")
        (self.d / "WORKLOG.md").write_text(self.text() + GLUED + "\n")
        code, out, err = self.append("--kind", "entry", "--title", "Next", "--body", "A clean entry.")
        self.assertIn("pre-existing", err)

    def test_missing_options_and_records(self):
        code, out, err = self.append("--kind", "finding", "--plain", "x", ok=False)
        self.assertEqual(code, 2)
        os.unlink(str(self.d / "worklog.json"))
        code, out, err = self.append("--kind", "entry", "--title", "x", ok=False)
        self.assertEqual(code, 1)
        self.assertIn("init", err)

    def test_works_without_state_and_ledger(self):
        d = self.make_direction("bare", ledger=False, state_json=False)
        code, out, err = self.run_cli("worklog-append", str(d), "--kind", "entry", "--title", "Hello", "--body",
                                      "First entry.")
        self.assertEqual(code, 0, err)
        text = (d / "WORKLOG.md").read_text()
        self.assertIn("| GPU budget | no ledger.json yet |", text)
        self.assertIn("| Weekly usage, all models | no reading yet; no session has registered |", text)


class CheckpointTest(WorklogBase):
    def test_checkpoint_block_and_freeze_recorded(self):
        sid = "b2cb53cd99999999"
        s = self.make_session(sid=sid, cwd=str(self.DC), registered=True, slug="demo", points=16,
                              freeze=(1, "crossed"), w_last=33)
        self.assertEqual(s["register"]["state_path"], records.state_json_path(str(self.d)))
        s["checkpoints"] = [{"n": 1, "at": paths.iso(SAT_0805), "session_points": 16, "all_models": 27, "fable": 33,
                             "acked_at": None, "acked_by": None}]
        s["usage"]["last_reading"] = {"five_hour": None, "seven_day": 27, "fable": 33, "read_at": paths.iso(SAT_0805),
                                      "fresh": True}
        s["compactions"] = 1
        state.write_json_atomic(self.cfg.session_file("claude", sid), s)
        state.mirror(self.cfg, s)
        self.append("--kind", "incident", "--what", "A worker lost its place.", "--effect", "ten minutes lost",
                    "--fix", "resumed")
        self.set_clock(epoch(2026, 10, 31, 18, 30))
        self.append("--kind", "checkpoint", "--checkpoint", "1", "--session", sid,
                    "--body", "Two findings landed (F1, F2).", "--plan", "Finish the analysis and review it.")
        text = self.text()
        block = text[text.index("**6:30 pm EDT · CHECKPOINT 1"):]
        self.assertIn("CHECKPOINT 1 (+16 session points; all models 27%, Fable 33%; resets "
                      + records.reset_when(RESET) + ").**", block)
        self.assertIn("- Since the last checkpoint: Two findings landed (F1, F2).", block)
        self.assertIn("- Spend: GPU 0.0 of 20 GPU-h actual (0.0 reserved); OpenRouter $0.00 of $10.00 cap; "
                      "compactions 1.", block)
        self.assertIn("- Process health: P1.", block)
        self.assertIn("- Fable gap: Fable is 6 points above all models: delegate reading, analysis and review to Opus"
                      " agents.", block)
        self.assertIn("- Plan to the next checkpoint: Finish the analysis and review it.", block)
        self.assertIn("- Frozen until you reply \"continue\": new agents, new Slurm jobs and messages to workers other"
                      " than HOLD. Still running and not cancelled: nothing recorded.", block)
        self.assertIn("| Weekly usage, all models | account reads 27%; +16 points this session |", text)
        self.assertIn("| Weekly usage, Fable | account reads 33%; 6 points above all models, so reading, analysis and"
                      " review go to Opus agents |", text)
        self.assertIn("| State | At checkpoint 1, frozen until you reply \"continue\" |", text)
        self.assertEqual(self.session(sid)["usage"]["freeze"]["stage"], "recorded")
        st = self.read_json_file(self.d / "state.json")
        self.assertEqual(st["sessions"]["claude-b2cb53cd"]["usage"]["freeze"]["stage"], "recorded")
        self.assertEqual(st["last_worklog_entry_at"], paths.iso(epoch(2026, 10, 31, 18, 30)))

    def test_checkpoint_refuses_unknown_number(self):
        sid = "b2cb53cd99999999"
        self.make_session(sid=sid, cwd=str(self.DC), registered=True, slug="demo")
        code, out, err = self.append("--kind", "checkpoint", "--checkpoint", "3", "--session", sid, "--body", "b",
                                     "--plan", "p", ok=False)
        self.assertEqual(code, 1)
        self.assertIn("checkpoint 3", err)


class WorklogSetTest(WorklogBase):
    def set(self, field, value, ok=True):
        code, out, err = self.run_cli("worklog-set", str(self.d), field, value)
        if ok:
            self.assertEqual(code, 0, out + err)
        return code, out, err

    def test_text_fields_round_trip(self):
        for field, key, value, row in (
                ("title", "title", "Testing the worklog", "# Worklog: Testing the worklog"),
                ("state", "state", "Blocked: needs you", "| State | Blocked: needs you |"),
                ("right-now", "right_now", "Two jobs run; the next finishes at noon.",
                 "**Right now.** Two jobs run; the next finishes at noon."),
                ("transcripts", "transcripts", "Claude session b2cb53cd", "| Transcripts (for audits) | Claude session"
                                                                          " b2cb53cd |")):
            self.set(field, value)
            self.assertEqual(self.wl()[key], value)
            self.assertIn(row, self.text())
        code, out, err = self.set("state", "Sleeping", ok=False)
        self.assertEqual(code, 2)

    def test_list_fields(self):
        self.set("directions", json.dumps([{"name": "Hooks", "state": "active"}, {"name": "Docs", "state": "done"}]))
        self.assertIn("| Directions | 1. Hooks: active · 2. Docs: done |", self.text())
        self.set("terms", json.dumps([{"term": "U5", "meaning": "the fifth clause set"}]))
        self.assertIn("**Terms.** *U5*: the fifth clause set.", self.text())
        for field, bad in (("directions", "[{\"name\": \"x\"}]"), ("directions", "{not json"),
                           ("directions", "[{\"name\": \"x\", \"state\": \"y\", \"extra\": 1}]"),
                           ("terms", "[{\"term\": \"x\", \"meaning\": \"y\", \"colour\": 1}]"), ("terms", "[1, 2")):
            before = self.text()
            code, out, err = self.set(field, bad, ok=False)
            self.assertEqual(code, 2, (field, bad))
            self.assertEqual(self.text(), before)

    def test_caps_change_ledger_and_rows(self):
        self.set("gpu-cap", "12.5")
        self.set("max-gpu-jobs", "3")
        self.set("api-cap", "7")
        caps = self.read_json_file(self.d / "ledger.json")["caps"]
        self.assertEqual(caps, {"reserved_gpu_hours": 12.5, "max_concurrent_gpu_jobs": 3, "paid_api_usd": 7.0})
        text = self.text()
        self.assertIn("| GPU budget | 0.0 of 12.5 GPU-h actual (0.0 reserved); at most 3 jobs at once; clusters: none"
                      " yet |", text)
        self.assertIn("| OpenRouter credit | $0.00 of $7.00 cap |", text)
        self.assertEqual(self.wl()["budgets"]["openrouter"], "$0.00 of $7.00 cap")
        code, out, err = self.set("gpu-cap", "-1", ok=False)
        self.assertEqual(code, 2)

    def test_glued_right_now_refused_before_write(self):
        self.set("right-now", "Clean text first.")
        before_md, before_json = self.text(), (self.d / "worklog.json").read_text()
        code, out, err = self.set("right-now", GLUED, ok=False)
        self.assertEqual(code, 1)
        self.assertIn("join", err + out)
        self.assertEqual(self.text(), before_md)
        self.assertEqual((self.d / "worklog.json").read_text(), before_json)

    def test_freeze_and_cap_override_state_row(self):
        self.set("state", "Running")
        st = self.read_json_file(self.d / "state.json")
        st["sessions"]["claude-b2cb53cd"] = {
            "tool": "claude", "session_id": "b2cb53cd", "started_at": paths.iso(SAT_0805),
            "usage": {"cadence": 16, "points_at_register": 0, "session_points": 20, "next_checkpoint": 2,
                      "acked_through": 0, "segments": [{"resets_at": RESET, "baseline": 10, "last": 30}],
                      "freeze": {"checkpoint": 1, "stage": "crossed", "crossed_at": paths.iso(SAT_0805),
                                 "recorded_at": None},
                      "last_reading": {"five_hour": None, "seven_day": 30, "fable": 31, "read_at": paths.iso(SAT_0805),
                                       "fresh": True}},
            "checkpoints": [{"n": 1, "at": paths.iso(SAT_0805), "session_points": 16, "all_models": 27, "fable": 28,
                             "acked_at": None, "acked_by": None}], "compactions": 2}
        self.write_json_file(self.d / "state.json", st)
        self.set("title", "Same title")
        text = self.text()
        self.assertIn("| State | At checkpoint 1, frozen until you reply \"continue\" |", text)
        self.assertIn("| Review checkpoints | 0 of 1 acknowledged; next at +32 session points; cadence 16 points; cap"
                      " pause at 80% |", text)
        self.assertIn("| Orchestrator auto-compactions | 2, counted by the compaction hook |", text)
        self.assertIn("within 5 points of all models", text)
        st["sessions"]["claude-b2cb53cd"]["usage"]["last_reading"]["fable"] = 81
        self.write_json_file(self.d / "state.json", st)
        self.set("title", "Same title")
        self.assertIn("| State | Paused for usage cap until " + records.reset_when(RESET)
                      + "; at checkpoint 1, frozen until you reply \"continue\" |", self.text())


class ImportTest(RecordsMixin, RSTestCase):
    LEGACY = FIXTURES / "worklog" / "legacy_feature_WORKLOG.md"

    def setUp(self):
        super(ImportTest, self).setUp()
        self.setup_root(with_templates=False)
        self.set_clock(epoch(2026, 10, 31, 15, 0))
        self.d = self.root / "autoresearch-workflow"
        self.d.mkdir()
        shutil.copy(str(self.LEGACY), str(self.d / "WORKLOG.md"))

    def test_import_legacy_head(self):
        old = (self.d / "WORKLOG.md").read_text()
        code, out, err = self.run_cli("worklog-append", str(self.d), "--import")
        self.assertEqual(code, 0, out + err)
        new = (self.d / "WORKLOG.md").read_text()
        _, old_log = self.head_and_log(old)
        _, new_log = self.head_and_log(new)
        self.assertEqual(new_log.encode(), old_log.encode())
        wl = self.read_json_file(self.d / "worklog.json")
        self.assertEqual(registry.validate_worklog(wl)[0], [])
        self.assertEqual([f["id"] for f in wl["findings"]], ["F1", "F2", "F3"])
        self.assertEqual([p["id"] for p in wl["incidents"]], ["P1", "P2"])
        self.assertEqual([n["id"] for n in wl["needs"]], ["N0"])
        self.assertIsNotNone(wl["needs"][0]["answer"])
        self.assertEqual(wl["title"], "setting up the autoresearch workflow")
        self.assertEqual(rendered_head_labels(new), template_head_labels())
        old_head = old.split("\n## Log\n")[0]
        new_head = new.split("\n## Log\n")[0]
        for line in old_head.splitlines():
            if re.match(r"^(- |\| [FP][0-9]+ )", line):
                self.assertIn(line, new_head.splitlines())
        self.assertIn("--- old head", out)
        self.assertIn("Weekly usage (this session)", out)
        code, out, err = self.run_cli("worklog-append", str(self.d), "--kind", "entry", "--title", "After import",
                                      "--body", "The tool now owns this worklog.")
        self.assertEqual(code, 0, err)
        self.assertTrue(self.head_and_log((self.d / "WORKLOG.md").read_text())[1].startswith(old_log))

    def test_import_refuses_when_worklog_json_exists(self):
        (self.d / "worklog.json").write_text("{}")
        code, out, err = self.run_cli("worklog-append", str(self.d), "--import")
        self.assertEqual(code, 1)
        self.assertIn("already", err)

    def test_import_refuses_a_lost_row(self):
        text = (self.d / "WORKLOG.md").read_text().replace("| F2 | Sat 9:25 am |", "| F2 Sat 9:25 am |")
        (self.d / "WORKLOG.md").write_text(text)
        code, out, err = self.run_cli("worklog-append", str(self.d), "--import")
        self.assertEqual(code, 1)
        self.assertIn("F2", err)
        self.assertFalse((self.d / "worklog.json").exists())

    def test_import_of_a_rendered_worklog_is_stable(self):
        self.run_cli("worklog-append", str(self.d), "--import")
        first = (self.d / "WORKLOG.md").read_text()
        os.unlink(str(self.d / "worklog.json"))
        code, out, err = self.run_cli("worklog-append", str(self.d), "--import")
        self.assertEqual(code, 0, out + err)
        self.assertEqual((self.d / "WORKLOG.md").read_text(), first)


if __name__ == "__main__":
    unittest.main()
