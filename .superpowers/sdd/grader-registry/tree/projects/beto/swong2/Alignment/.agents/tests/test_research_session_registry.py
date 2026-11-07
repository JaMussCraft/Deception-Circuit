"""Ticket 03: registry validators, ``validate``, ``render``, ``claim``, ``release`` and ``ledger-rollup``."""

import copy
import json
import os
import unittest
from pathlib import Path

from _rs_records import SAT_0805, SUN_0805, RecordsMixin
from _rs_testlib import RSTestCase

from research_session import registry

DIRECTION_EXAMPLE = {
    "schema": 1, "updated": "2026-10-31", "directions": [{
        "id": "sdr-mechanism", "title": "How shared SDR heads compose into deceptive reporting",
        "status": "paused", "status_source": "docs/research/sdr-mechanism/README.md", "summary": "One sentence.",
        "claimed_by": None, "claimed_at": None, "branch": None, "worktree": None,
        "dir": "docs/research/sdr-mechanism", "spec": None, "resume": None, "worklog": None, "state": None,
        "ledger": "docs/research/sdr-mechanism/ledger.json", "frozen_grader_sha256": None,
        "parent_findings": ["F-sdr-001"], "do_not_touch": ["outputs/_analyses/sdr-*"],
        "legacy_scratch": [".scratch/sdr-cue-probe"], "archive": ["outputs/_studies/sdr-cue-probe/scratch"],
        "updated": "2026-10-31"}]}

LEDGER_EXAMPLE = {
    "schema": 1, "direction": "selective-deception",
    "caps": {"reserved_gpu_hours": 40.0, "paid_api_usd": 20.0, "max_concurrent_gpu_jobs": 2},
    "totals": {"reserved_gpu_hours": 38.35, "actual_gpu_seconds": 45167, "api_usd_known": 4.18,
               "api_usd_reserve": 0.66},
    "reservations": [{"id": "r-001", "job_id": "123", "cluster": "delta", "account": "bimc-delta-gpu",
                      "partition": "gpuA40x4", "gpus": 1, "requested_minutes": 15, "reserved_gpu_hours": 0.25,
                      "actual_seconds": None, "status": "RUNNING", "source_commit": "abc1234",
                      "manifest_hash": None, "output_dir": "outputs/..."}],
    "api_calls": [{"date": "2026-10-31", "provider": "openrouter", "calls": 0, "usd": 0.0}],
    "converted_from": None}

STATE_EXAMPLE = {
    "schema": 1, "direction": "pilot-hooks", "session_state": "running",
    "last_worklog_entry_at": "2026-11-02T10:05:00-06:00",
    "sessions": {"claude-01a2b3c4": {
        "tool": "claude", "session_id": "...", "cwd": "/abs/worktree", "started_at": "...",
        "orchestrator_model": "claude-fable-5-1", "compactions": 2,
        "compaction_log": [{"n": 1, "at": "...", "trigger": "auto"}],
        "usage": {"metric": "max(seven_day, Fable)", "cadence": 16,
                  "segments": [{"resets_at": 1793797200, "baseline": 11, "last": 27}]},
        "checkpoints": [{"n": 1, "at": "...", "session_points": 16, "all_models": 27, "fable": 33,
                         "acked_at": None, "acked_by": None}],
        "agents": {"a1b2": {"agent_type": "ticket-implementer", "started_at": "...", "stop_blocks": 0}}}},
    "jobs": [{"job_id": "123", "cluster": "delta", "submitted_at": "...",
              "waiter": "until sacct ...; do sleep 300; done",
              "expected_terminal": ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL"],
              "status": "PENDING", "last_progress_at": "..."}]}

WORKLOG_EXAMPLE = {
    "schema": 1, "title": "Plain session title", "state": "Running", "right_now": "Three lines at most.",
    "directions": [{"name": "Plain name", "state": "active"}], "terms": [{"term": "U5", "meaning": "..."}],
    "budgets": {"gpu": "6.5 of 20 GPU-h actual", "openrouter": "$1.84 of $10"}, "transcripts": "Claude session ...",
    "needs": [{"id": "N1", "at": "...", "text": "...", "default": "If no answer: ...", "answer": None,
               "answered_at": None}],
    "findings": [{"id": "F1", "at": "...", "plain": "...", "setup": "...", "strength": "reviewed",
                  "evidence": "..."}],
    "incidents": [{"id": "P1", "at": "...", "what": "...", "effect": "...", "fix": "..."}]}

FINDINGS_HEAD = ("| id | date | direction | claim | status | commit | evidence | report |\n"
                 "|----|------|-----------|-------|--------|--------|----------|--------|\n")
FINDINGS_ROW = ("| F-sdr-007 | 2026-10-26 | sdr-mechanism | One sentence claim. | verified | 695b126 | "
                "outputs/_analyses/x/run_manifest.json | docs/research/sdr-mechanism/reports/y.md |\n")

HELD_OUT_EXAMPLE = {"schema": 1, "sets": [{"id": "sdr-v2-test", "task": "sdr", "path": "data/x.json",
                                           "sha256": "0" * 64, "n": 200, "created": "2026-10-31",
                                           "created_by": "claude-b2cb53cd", "purpose": "paper", "scored_runs": []}]}


def _row(**kw):
    r = copy.deepcopy(DIRECTION_EXAMPLE["directions"][0])
    r.update(kw)
    return r


class ZoneTest(unittest.TestCase):
    def test_zoneinfo_new_york_loads(self):
        import zoneinfo
        z = zoneinfo.ZoneInfo("America/New_York")
        from research_session import records
        self.assertEqual(records.clock_text(records.local(SAT_0805)), "8:05 am EDT")
        self.assertEqual(records.clock_text(records.local(SUN_0805)), "8:05 am EST")
        self.assertEqual(str(z), "America/New_York")


class ValidatorTest(unittest.TestCase):
    def assertOK(self, errors):
        self.assertEqual(errors, [], errors)

    def assertFails(self, errors, fragment):
        self.assertTrue(any(fragment in e for e in errors), "%r not in %r" % (fragment, errors))

    def test_spec_examples_pass(self):
        self.assertOK(registry.validate_directions(DIRECTION_EXAMPLE)[0])
        self.assertOK(registry.validate_ledger(LEDGER_EXAMPLE)[0])
        self.assertOK(registry.validate_state(STATE_EXAMPLE)[0])
        self.assertOK(registry.validate_worklog(WORKLOG_EXAMPLE)[0])
        self.assertOK(registry.validate_findings_text(FINDINGS_HEAD + FINDINGS_ROW)[0])
        self.assertOK(registry.validate_held_out(HELD_OUT_EXAMPLE)[0])

    def test_spec_ledger_example_totals_mismatch_is_a_warning(self):
        errors, warnings = registry.validate_ledger(LEDGER_EXAMPLE)
        self.assertOK(errors)
        self.assertTrue(any("totals" in w for w in warnings))

    def test_directions_bad_cases(self):
        def check(row, fragment):
            data = dict(DIRECTION_EXAMPLE, directions=[row])
            self.assertFails(registry.validate_directions(data)[0], fragment)
        check(_row(status="finished"), "status")
        bad = _row()
        del bad["title"]
        check(bad, "missing")
        check(_row(colour="blue"), "unknown key")
        check(_row(status="claimed", claimed_by="claude-b2cb53c", claimed_at="2026-10-31T09:00:00-04:00"),
              "claimed_by")
        check(_row(status="claimed", claimed_by="claude_b2cb53cd", claimed_at="2026-10-31T09:00:00-04:00"),
              "claimed_by")
        check(_row(status="claimed", claimed_by="gemini-b2cb53cd", claimed_at="2026-10-31T09:00:00-04:00"),
              "claimed_by")
        check(_row(status="active", claimed_by=None), "claimed_by")
        data = dict(DIRECTION_EXAMPLE, directions=[_row(), _row()])
        self.assertFails(registry.validate_directions(data)[0], "duplicate")
        self.assertFails(registry.validate_directions(dict(DIRECTION_EXAMPLE, extra=1))[0], "unknown key")
        self.assertOK(registry.validate_directions(dict(DIRECTION_EXAMPLE, directions=[_row(
            status="claimed", claimed_by="claude-b2cb53cd", claimed_at="2026-10-31T09:00:00-04:00")]))[0])

    def test_ledger_bad_cases(self):
        bad = copy.deepcopy(LEDGER_EXAMPLE)
        bad["reservations"][0]["status"] = "DONE"
        self.assertFails(registry.validate_ledger(bad)[0], "status")
        bad = copy.deepcopy(LEDGER_EXAMPLE)
        del bad["caps"]["paid_api_usd"]
        self.assertFails(registry.validate_ledger(bad)[0], "missing")
        bad = copy.deepcopy(LEDGER_EXAMPLE)
        bad["reservations"][0]["note"] = "x"
        self.assertFails(registry.validate_ledger(bad)[0], "unknown key")
        bad = copy.deepcopy(LEDGER_EXAMPLE)
        bad["schema"] = 2
        self.assertFails(registry.validate_ledger(bad)[0], "schema")

    def test_state_bad_cases(self):
        bad = copy.deepcopy(STATE_EXAMPLE)
        bad["session_state"] = "sleeping"
        self.assertFails(registry.validate_state(bad)[0], "session_state")
        bad = copy.deepcopy(STATE_EXAMPLE)
        bad["sessions"]["claude-xyz"] = bad["sessions"].pop("claude-01a2b3c4")
        self.assertFails(registry.validate_state(bad)[0], "session key")
        bad = copy.deepcopy(STATE_EXAMPLE)
        bad["jobs"][0]["colour"] = 1
        self.assertFails(registry.validate_state(bad)[0], "unknown key")
        bad = copy.deepcopy(STATE_EXAMPLE)
        del bad["jobs"]
        self.assertFails(registry.validate_state(bad)[0], "missing")

    def test_worklog_bad_cases(self):
        bad = copy.deepcopy(WORKLOG_EXAMPLE)
        bad["findings"].append(dict(bad["findings"][0]))
        self.assertFails(registry.validate_worklog(bad)[0], "duplicate")
        bad = copy.deepcopy(WORKLOG_EXAMPLE)
        bad["findings"][0]["strength"] = "strong"
        self.assertFails(registry.validate_worklog(bad)[0], "strength")
        bad = copy.deepcopy(WORKLOG_EXAMPLE)
        bad["mood"] = "fine"
        self.assertFails(registry.validate_worklog(bad)[0], "unknown key")
        bad = copy.deepcopy(WORKLOG_EXAMPLE)
        bad["state"] = "Sleeping"
        self.assertFails(registry.validate_worklog(bad)[0], "state")
        bad = copy.deepcopy(WORKLOG_EXAMPLE)
        bad["terms"] = [{"term": "T%d" % i, "meaning": "m"} for i in range(11)]
        self.assertFails(registry.validate_worklog(bad)[0], "terms")
        bad = copy.deepcopy(WORKLOG_EXAMPLE)
        bad["needs"][0]["id"] = "Q1"
        self.assertFails(registry.validate_worklog(bad)[0], "id")

    def test_findings_bad_cases(self):
        def check(row, fragment):
            self.assertFails(registry.validate_findings_text(FINDINGS_HEAD + row)[0], fragment)
        check(FINDINGS_ROW.replace("verified", "great"), "status")
        check(FINDINGS_ROW + FINDINGS_ROW, "duplicate")
        check(FINDINGS_ROW.replace("695b126", "pre-manifest"), "pre-manifest")
        check(FINDINGS_ROW.replace("outputs/_analyses/x/run_manifest.json", "outputs/_analyses/x/table.csv"),
              "provenance")
        check(FINDINGS_ROW.replace("F-sdr-007", "F7"), "id")
        check(FINDINGS_ROW.replace("| docs/research/sdr-mechanism/reports/y.md |", "|"), "columns")
        self.assertFails(registry.validate_findings_text(
            FINDINGS_HEAD.replace("| report |", "| report | extra |") + FINDINGS_ROW)[0], "header")
        ok = FINDINGS_ROW.replace("verified", "reviewed").replace("695b126", "pre-manifest")
        self.assertEqual(registry.validate_findings_text(FINDINGS_HEAD + ok)[0], [])
        sup = FINDINGS_ROW.replace("verified", "superseded")
        check(sup, "superseded by")

    def test_held_out_bad_case(self):
        bad = copy.deepcopy(HELD_OUT_EXAMPLE)
        del bad["sets"][0]["sha256"]
        self.assertFails(registry.validate_held_out(bad)[0], "missing")


class RegistryCliTest(RecordsMixin, RSTestCase):
    def setUp(self):
        super(RegistryCliTest, self).setUp()
        self.setup_root(with_templates=False)
        self.set_clock(SAT_0805)

    def directions(self, rows):
        self.write_json_file(self.root / "directions.json", {"schema": 1, "updated": "2026-10-31",
                                                            "directions": rows})

    def test_validate_dispatch(self):
        self.directions([_row()])
        self.write_json_file(self.root / "held_out.json", HELD_OUT_EXAMPLE)
        (self.root / "FINDINGS.md").write_text(FINDINGS_HEAD + FINDINGS_ROW)
        code, out, err = self.run_cli("validate", str(self.root / "directions.json"), str(self.root / "held_out.json"),
                                      str(self.root / "FINDINGS.md"))
        self.assertEqual(code, 0, out + err)
        self.directions([_row(status="nope")])
        code, out, err = self.run_cli("validate", str(self.root / "directions.json"))
        self.assertEqual(code, 1)
        self.assertIn("status", out)
        other = self.root / "notes.json"
        other.write_text("{}")
        code, out, err = self.run_cli("validate", str(other))
        self.assertEqual(code, 2)

    def test_validate_templates(self):
        from _rs_records import templates_dir
        tdir = templates_dir()
        code, out, err = self.run_cli("validate", os.path.join(tdir, "state.json"), os.path.join(tdir, "ledger.json"),
                                      os.path.join(tdir, "worklog.json"))
        self.assertEqual(code, 0, out + err)

    def _claimed(self, slug, tag, state_rel=None):
        return _row(id=slug, title="Title of " + slug, status="claimed", claimed_by=tag,
                    claimed_at="2026-10-31T09:00:00-04:00", dir="docs/research/" + slug, state=state_rel,
                    worklog="docs/research/%s/WORKLOG.md" % slug, do_not_touch=["outputs/_analyses/%s-*" % slug])

    def test_render_byte_stable_and_no_state_yet(self):
        self.directions([_row(), self._claimed("autoresearch-workflow", "claude-b2cb53cd"),
                         self._claimed("demo", "codex-0a1b2c3d")])
        self.make_direction("demo", state_json={"session_state": "running",
                                                "last_worklog_entry_at": "2026-10-31T08:00:00-04:00"})
        code, out, err = self.run_cli("render", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        sessions = (self.root / "SESSIONS.md").read_bytes()
        directions = (self.root / "DIRECTIONS.md").read_bytes()
        text = sessions.decode()
        self.assertIn("no state yet", text)
        self.assertIn("claude-b2cb53cd", text)
        self.assertIn("Sat 31 Oct 2026, 8:00 am EDT", text)
        self.assertNotIn("sdr-mechanism", text)
        self.assertIn("sdr-mechanism", directions.decode())
        m1 = os.stat(self.root / "SESSIONS.md").st_mtime_ns
        self.set_clock(SAT_0805 + 3600)
        code, out, err = self.run_cli("render", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertEqual((self.root / "SESSIONS.md").read_bytes(), sessions)
        self.assertEqual((self.root / "DIRECTIONS.md").read_bytes(), directions)
        self.assertEqual(os.stat(self.root / "SESSIONS.md").st_mtime_ns, m1)
        from research_session import lint
        self.assertEqual(lint.lint_text(text), [])

    def test_claim_and_release(self):
        self.directions([_row(id="free", status="open"), self._claimed("taken", "codex-0a1b2c3d")])
        code, out, err = self.run_cli("claim", "free", "--as", "claude-b2cb53cd", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        rows = {r["id"]: r for r in self.read_json_file(self.root / "directions.json")["directions"]}
        self.assertEqual(rows["free"]["status"], "claimed")
        self.assertEqual(rows["free"]["claimed_by"], "claude-b2cb53cd")
        self.assertTrue(rows["free"]["claimed_at"].endswith("-04:00"))
        code, out, err = self.run_cli("claim", "taken", "--as", "claude-b2cb53cd", "--root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("codex-0a1b2c3d", err)
        code, out, err = self.run_cli("claim", "missing", "--as", "claude-b2cb53cd", "--root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("unknown", err)
        code, out, err = self.run_cli("claim", "free", "--as", "claude-xyz", "--root", str(self.root))
        self.assertEqual(code, 2)
        code, out, err = self.run_cli("release", "taken", "--status", "paused", "--as", "claude-b2cb53cd",
                                      "--root", str(self.root))
        self.assertEqual(code, 1)
        code, out, err = self.run_cli("release", "free", "--status", "done", "--as", "claude-b2cb53cd",
                                      "--root", str(self.root))
        self.assertEqual(code, 0, err)
        rows = {r["id"]: r for r in self.read_json_file(self.root / "directions.json")["directions"]}
        self.assertEqual(rows["free"]["status"], "done")
        self.assertIsNone(rows["free"]["claimed_by"])
        self.assertEqual(registry.validate_directions(self.read_json_file(self.root / "directions.json"))[0], [])

    def freeze_fixture(self, status="claimed", owner="codex-0a1b2c3d", frozen=None):
        session = self.make_session(sid="0a1b2c3d-owner", tool="codex", cwd=str(self.DC))
        row = self._claimed("demo", owner)
        row.update(status=status, frozen_grader_sha256=frozen)
        if owner is None:
            row["claimed_at"] = None
        self.directions([row, _row()])
        self.make_direction("demo")
        self.write_usage()
        return session

    def freeze(self, digest="a" * 64, selector="codex-0a1b2c3d", slug="demo"):
        return self.run_cli("freeze-grader", slug, digest, "--session", selector, "--root", str(self.root))

    def assert_freeze_refused(self, code=1, **kwargs):
        path = self.root / "directions.json"
        before = path.read_bytes()
        result, out, err = self.freeze(**kwargs)
        self.assertEqual(result, code, out + err)
        self.assertTrue(err)
        self.assertEqual(path.read_bytes(), before)
        return err

    def test_freeze_grader_owned_initial_and_idempotent(self):
        for status in ("claimed", "active"):
            with self.subTest(status=status):
                self.freeze_fixture(status=status)
                # Another same-cwd session must not override the explicit owner selector.
                self.make_session(sid="ffffffff-newer", tool="codex", cwd=str(self.DC))
                other_paths = [p for p in Path(self.tmp).rglob("*")
                               if p.is_file() and p.name != "directions.json"]
                before = {p: p.read_bytes() for p in other_paths}
                rows_before = self.read_json_file(self.root / "directions.json")["directions"]
                for selector in ("0a1b2c3d-owner", "codex-0a1b2c3d", "0a1b2c3d-o"):
                    code, out, err = self.freeze(selector=selector)
                    self.assertEqual(code, 0, err)
                rows_after = self.read_json_file(self.root / "directions.json")["directions"]
                expected = copy.deepcopy(rows_before)
                expected[0]["frozen_grader_sha256"] = "a" * 64
                expected[0]["updated"] = rows_after[0]["updated"]
                self.assertEqual(rows_after, expected)
                self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_freeze_grader_strict_hashes(self):
        self.freeze_fixture()
        for digest in ("", "a" * 63, "a" * 65, "A" * 64, "g" * 64,
                       "a" * 64 + "\n", " " + "a" * 64, "a" * 63 + " "):
            with self.subTest(digest=digest):
                self.assert_freeze_refused(code=2, digest=digest)

    def test_freeze_grader_selector_required_no_override(self):
        self.freeze_fixture()
        for extra in ([], ["--as", "codex-0a1b2c3d"],
                      ["--session", "codex-0a1b2c3d", "--as", "codex-0a1b2c3d"]):
            before = (self.root / "directions.json").read_bytes()
            with self.assertRaises(SystemExit) as raised:
                self.run_cli("freeze-grader", "demo", "a" * 64, "--root", str(self.root), *extra)
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual((self.root / "directions.json").read_bytes(), before)
        for selector in ("", " ", "\t", "missing"):
            self.assert_freeze_refused(code=2, selector=selector)
        self.make_session(sid="0a1b2c3d-another", tool="codex")
        self.assertIn("matches", self.assert_freeze_refused(code=2, selector="0a1b2c3d"))

    def test_freeze_grader_status_owner_conflict_unknown_and_invalid(self):
        for status, owner in (("open", None), ("proposed", None), ("paused", None),
                              ("done", None), ("abandoned", None), ("claimed", "claude-12345678"),
                              ("active", "claude-12345678"), ("paused", "codex-0a1b2c3d")):
            with self.subTest(status=status, owner=owner):
                self.freeze_fixture(status=status, owner=owner)
                self.assert_freeze_refused()
        self.freeze_fixture(frozen="b" * 64)
        self.assert_freeze_refused()
        self.assertIn("unknown", self.assert_freeze_refused(slug="missing"))
        data = self.read_json_file(self.root / "directions.json")
        data["directions"][0]["surprise"] = True
        self.write_json_file(self.root / "directions.json", data)
        self.assert_freeze_refused()

    def test_freeze_grader_uses_locked_edit_and_preserves_new_fields(self):
        from unittest import mock
        self.freeze_fixture()
        edit = registry._edit_directions

        def intervening_edit(root, slug, fn):
            # Simulate a separate completed writer before our lock/load.
            data = self.read_json_file(self.root / "directions.json")
            data["directions"][0]["summary"] = "Another writer updated this."
            data["directions"][1]["summary"] = "Another row changed."
            self.write_json_file(self.root / "directions.json", data)
            return edit(root, slug, fn)

        with mock.patch.object(registry, "_edit_directions", side_effect=intervening_edit) as helper:
            code, out, err = self.freeze()
        self.assertEqual(code, 0, err)
        helper.assert_called_once()
        rows = self.read_json_file(self.root / "directions.json")["directions"]
        self.assertEqual(rows[0]["frozen_grader_sha256"], "a" * 64)
        self.assertEqual(rows[0]["summary"], "Another writer updated this.")
        self.assertEqual(rows[1]["summary"], "Another row changed.")

    def test_claim_uses_the_session_tag(self):
        self.directions([_row(id="free", status="open")])
        self.make_session(sid="b2cb53cd-1111-2222", cwd=str(self.DC))
        code, out, err = self.run_cli("claim", "free", "--root", str(self.root), "--cwd", str(self.DC))
        self.assertEqual(code, 0, err)
        rows = self.read_json_file(self.root / "directions.json")["directions"]
        self.assertEqual(rows[0]["claimed_by"], "claude-b2cb53cd")

    def test_ledger_rollup(self):
        self.make_direction("a", ledger={"totals": {"reserved_gpu_hours": 1.5, "actual_gpu_seconds": 100,
                                                    "api_usd_known": 0.5, "api_usd_reserve": 0.0}})
        self.make_direction("b", ledger={"totals": {"reserved_gpu_hours": 2.0, "actual_gpu_seconds": 50,
                                                    "api_usd_known": 1.0, "api_usd_reserve": 0.25}})
        code, out, err = self.run_cli("ledger-rollup", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        data = self.read_json_file(self.root / "ledger.json")
        self.assertEqual(sorted(data["directions"]), ["a", "b"])
        self.assertAlmostEqual(data["totals"]["reserved_gpu_hours"], 3.5)
        self.assertEqual(data["totals"]["actual_gpu_seconds"], 150)
        self.assertAlmostEqual(data["totals"]["api_usd_reserve"], 0.25)
        before = (self.root / "ledger.json").read_bytes()
        self.set_clock(SAT_0805 + 600)
        self.run_cli("ledger-rollup", "--root", str(self.root))
        self.assertEqual((self.root / "ledger.json").read_bytes(), before)
        code, out, err = self.run_cli("validate", str(self.root / "ledger.json"))
        self.assertEqual(code, 0, out + err)

    def test_ledger_rollup_skips_templates_and_hidden_directories(self):
        import shutil
        from _rs_records import templates_dir
        shutil.copytree(templates_dir(), str(self.root / "_templates"))
        self.make_direction("a")
        hidden = self.make_direction("a-copy")
        os.rename(str(hidden), str(self.root / ".a-copy"))
        code, out, err = self.run_cli("ledger-rollup", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        data = self.read_json_file(self.root / "ledger.json")
        self.assertEqual(sorted(data["directions"]), ["a"])
        self.assertNotIn("example-direction", json.dumps(data))

    def test_legacy_totals_field(self):
        led = copy.deepcopy(LEDGER_EXAMPLE)
        led["reservations"] = []
        led["totals"] = {"reserved_gpu_hours": 39.5333, "actual_gpu_seconds": 9409, "api_usd_known": 0.0,
                         "api_usd_reserve": 0.0}
        errors, warnings = registry.validate_ledger(led)
        self.assertEqual(errors, [])
        self.assertTrue(any("legacy_totals" in w for w in warnings), warnings)
        led["legacy_totals"] = {"reserved_gpu_hours": 39.5333, "actual_gpu_seconds": 9409, "api_usd_known": 0.0}
        self.assertEqual(registry.validate_ledger(led), ([], []))
        led["legacy_totals"]["note"] = "x"
        self.assertTrue(any("unknown key" in e for e in registry.validate_ledger(led)[0]))


if __name__ == "__main__":
    unittest.main()
