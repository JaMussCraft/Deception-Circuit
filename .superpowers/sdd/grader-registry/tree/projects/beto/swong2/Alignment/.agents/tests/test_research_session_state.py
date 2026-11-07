"""Session files, locking, the state.json mirror, direction resolution, register, usage-ack and set-cadence."""

import json
import os
import stat
import subprocess
import sys
import unittest
from pathlib import Path

from _rs_testlib import PKG_PARENT, RSTestCase

from research_session import paths, state

WRITER = r"""
import sys
sys.path.insert(0, sys.argv[1])
from research_session import paths, state
cfg = paths.Config(state_root=sys.argv[2], alignment_root=sys.argv[3])
def bump(s):
    s["compactions"] = s.get("compactions", 0) + 1
    s["agents"]["writer-" + sys.argv[4]] = s["compactions"]
for i in range(int(sys.argv[5])):
    state.update_session(cfg, "claude", "concurrent-session", bump, 1.0e9 + i, cwd=sys.argv[3])
"""


class LockingTests(RSTestCase):
    def test_two_concurrent_writers_lose_no_update(self):
        script = Path(self.tmp) / "writer.py"
        script.write_text(WRITER)
        n = 60
        procs = [subprocess.Popen([sys.executable, "-B", str(script), str(PKG_PARENT), self.cfg.state_root,
                                   str(self.A), name, str(n)]) for name in ("one", "two")]
        for p in procs:
            self.assertEqual(p.wait(timeout=120), 0)
        s = state.load_session(self.cfg, "claude", "concurrent-session")
        self.assertEqual(s["compactions"], 2 * n)
        self.assertEqual(set(s["agents"]), {"writer-one", "writer-two"})
        leftovers = [f for f in os.listdir(self.cfg.sessions_dir) if f.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_state_root_is_created_private(self):
        paths.ensure_state_root(self.cfg)
        for d in (self.cfg.state_root, self.cfg.sessions_dir):
            self.assertEqual(stat.S_IMODE(os.stat(d).st_mode), 0o700)

    def test_times_use_the_new_york_zone_with_computed_offsets(self):
        import datetime
        from zoneinfo import ZoneInfo
        self.assertEqual(paths.TIMEZONE, "America/New_York")
        zone = ZoneInfo(paths.TIMEZONE)
        # One instant on each side of the 1 November 2026 daylight-saving change.
        summer = datetime.datetime(2026, 10, 31, 16, 0, tzinfo=datetime.timezone.utc).timestamp()
        winter = datetime.datetime(2026, 11, 2, 16, 0, tzinfo=datetime.timezone.utc).timestamp()
        for t in (summer, winter):
            self.assertEqual(paths.iso(t), datetime.datetime.fromtimestamp(t, zone).isoformat(timespec="seconds"))
            self.assertAlmostEqual(paths.parse_iso(paths.iso(t)), t)
        self.assertNotEqual(paths.iso(summer)[-6:], paths.iso(winter)[-6:])

    def test_json_style_is_sorted_indented_with_newline(self):
        s = self.make_session()
        text = Path(self.cfg.session_file("claude", s["session_id"])).read_text()
        self.assertTrue(text.endswith("}\n"))
        self.assertEqual(text, state.dumps(json.loads(text)))


class MirrorAndResolutionTests(RSTestCase):
    def worktree(self, name="demo-wt"):
        wt = self.DC / ".claude" / "worktrees" / name
        (wt / "docs" / "research" / "demo").mkdir(parents=True)
        return wt

    def test_mirror_into_direction_state_json(self):
        wt = self.worktree()
        self.make_session(cwd=str(wt), points=5)
        code, out, err = self.run_cli("register", "demo", "--cwd", str(wt))
        self.assertEqual(code, 0, err)
        target = wt / "docs" / "research" / "demo" / "state.json"
        data = json.loads(target.read_text())
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["direction"], "demo")
        rec = data["sessions"]["claude-01234567"]
        self.assertEqual(rec["usage"]["points_at_register"], 5)
        self.assertEqual(rec["session_id"], "0123456789abcdef")
        self.assertNotIn("codex_cache", rec)

        def bump(s):
            s["compactions"] += 1
        state.update_session(self.cfg, "claude", "0123456789abcdef", bump, self.now + 5)
        self.assertEqual(json.loads(target.read_text())["sessions"]["claude-01234567"]["compactions"], 1)

        def touch_read_at(s):
            s["usage"]["last_reading"] = {"read_at": paths.iso(self.now + 99)}
        state.update_session(self.cfg, "claude", "0123456789abcdef", touch_read_at, self.now + 6)
        before = target.read_text()

        def touch_again(s):
            s["usage"]["last_reading"]["read_at"] = paths.iso(self.now + 200)
        _, _, result = state.update_session(self.cfg, "claude", "0123456789abcdef", touch_again, self.now + 7)
        self.assertEqual(result, "unchanged")
        self.assertEqual(target.read_text(), before)

    def test_mirror_keeps_other_sessions_and_fields(self):
        wt = self.worktree()
        target = wt / "docs" / "research" / "demo" / "state.json"
        target.write_text(json.dumps({"schema": 1, "direction": "demo", "session_state": "paused",
                                      "sessions": {"codex-aaaaaaaa": {"tool": "codex"}}, "jobs": [{"job_id": "1"}]}))
        self.make_session(cwd=str(wt))
        self.assertEqual(self.run_cli("register", "demo", "--cwd", str(wt))[0], 0)
        data = json.loads(target.read_text())
        self.assertEqual(set(data["sessions"]), {"codex-aaaaaaaa", "claude-01234567"})
        self.assertEqual(data["jobs"], [{"job_id": "1"}])
        self.assertEqual(data["session_state"], "paused")

    def test_resolution_by_register(self):
        s = self.make_session(registered=True, slug="demo")
        self.assertEqual(state.resolve_direction(self.cfg, s), ("demo", "register"))
        self.assertTrue(state.is_registered(s))

    def test_resolution_by_cwd_match_is_attribution_only(self):
        wt = self.worktree()
        self.write_directions([{"id": "demo", "worktree": str(wt)},
                               {"id": "other", "worktree": str(self.DC / ".claude" / "worktrees")}])
        s = self.make_session(cwd=str(wt / "docs"))
        self.assertEqual(state.resolve_direction(self.cfg, s), ("demo", "cwd"))
        self.assertFalse(state.is_registered(s))

    def test_resolution_unregistered(self):
        self.write_directions([{"id": "demo", "worktree": str(self.DC / "elsewhere")}])
        s = self.make_session()
        self.assertEqual(state.resolve_direction(self.cfg, s), (None, None))
        self.assertFalse(state.is_registered(s))

    def test_state_path_follows_the_checkout_of_the_cwd(self):
        wt = self.worktree()
        self.assertEqual(state.direction_state_path(self.cfg, "demo", str(wt / "docs")),
                         str(wt / "docs" / "research" / "demo" / "state.json"))
        self.assertEqual(state.direction_state_path(self.cfg, "demo", str(self.A)),
                         str(self.DC / "docs" / "research" / "demo" / "state.json"))


class RegisterCliTests(RSTestCase):
    def test_register_binds_most_recent_session_with_matching_cwd(self):
        self.write_directions([{"id": "demo"}])
        (self.DC / "docs" / "research" / "demo").mkdir()
        old = self.make_session(sid="aaaaaaaa1111")
        new = self.make_session(sid="bbbbbbbb2222")
        other = self.make_session(sid="cccccccc3333", cwd=str(self.A))
        for sid, t in (("aaaaaaaa1111", 10), ("bbbbbbbb2222", 20), ("cccccccc3333", 30)):
            state.update_session(self.cfg, "claude", sid, lambda s: None, self.now + t)
        code, out, err = self.run_cli("register", "demo", "--cwd", str(self.DC))
        self.assertEqual(code, 0, err)
        self.assertIn("registered session claude-bbbbbbbb to direction demo", out)
        self.assertTrue(state.is_registered(self.session("bbbbbbbb2222")))
        self.assertFalse(state.is_registered(self.session("aaaaaaaa1111")))
        self.assertFalse(state.is_registered(self.session("cccccccc3333")))
        self.assertEqual(err, "")
        del old, new, other

    def test_register_with_session_binds_that_session(self):
        self.write_directions([{"id": "demo"}])
        self.make_session(sid="aaaaaaaa1111")
        self.make_session(sid="bbbbbbbb2222")
        code, out, err = self.run_cli("register", "demo", "--session", "aaaaaaaa1111", "--cwd", str(self.A))
        self.assertEqual(code, 0, err)
        self.assertIn("registered session claude-aaaaaaaa to direction demo", out)
        self.assertTrue(state.is_registered(self.session("aaaaaaaa1111")))
        self.assertFalse(state.is_registered(self.session("bbbbbbbb2222")))

    def test_register_stores_points_at_register(self):
        self.make_session(points=40, cadence=16)
        code, out, _ = self.run_cli("register", "demo", "--cwd", str(self.DC))
        self.assertEqual(code, 0)
        u = self.session()["usage"]
        self.assertEqual(u["points_at_register"], 40)
        self.assertEqual(u["next_checkpoint"], 1)
        self.assertIsNone(u["freeze"])
        self.assertIn("points at register 40", out)

    def test_register_without_directions_json_warns_but_registers(self):
        self.make_session()
        code, out, err = self.run_cli("register", "demo", "--cwd", str(self.DC))
        self.assertEqual(code, 0)
        self.assertIn("directions.json not found", err)
        self.assertIn("mirror skipped", err)
        self.assertTrue(state.is_registered(self.session()))

    def test_register_with_no_matching_session_fails(self):
        code, out, err = self.run_cli("register", "demo", "--cwd", str(self.DC))
        self.assertEqual(code, 1)
        self.assertIn("no session has cwd", err)


class AckAndCadenceTests(RSTestCase):
    def frozen(self, sid, cwd=None, stage="crossed"):
        s = self.make_session(sid=sid, cwd=cwd, registered=True, freeze=(1, stage))
        s["checkpoints"] = [{"n": 1, "at": paths.iso(self.now), "session_points": 16, "all_models": 20,
                             "fable": 26, "acked_at": None, "acked_by": None}]
        state.write_json_atomic(self.cfg.session_file("claude", sid), s)
        return s

    def test_usage_ack_acks_most_recent_session_with_cwd_and_prints_it(self):
        self.frozen("aaaaaaaa1111")
        self.frozen("bbbbbbbb2222")
        state.update_session(self.cfg, "claude", "bbbbbbbb2222", lambda s: None, self.now + 50)
        code, out, err = self.run_cli("usage-ack", "--cwd", str(self.DC))
        self.assertEqual(code, 0, err)
        self.assertIn("acknowledged checkpoint 1 for session claude-bbbbbbbb", out)
        s = self.session("bbbbbbbb2222")
        self.assertEqual(s["usage"]["acked_through"], 1)
        self.assertIsNone(s["usage"]["freeze"])
        self.assertEqual(s["checkpoints"][0]["acked_by"], "usage-ack")
        self.assertIsNotNone(s["checkpoints"][0]["acked_at"])
        self.assertIsNotNone(self.session("aaaaaaaa1111")["usage"]["freeze"])

    def test_usage_ack_with_session(self):
        self.frozen("aaaaaaaa1111", stage="recorded")
        code, out, _ = self.run_cli("usage-ack", "--session", "claude-aaaaaaaa", "--cwd", "/")
        self.assertEqual(code, 0)
        self.assertIn("claude-aaaaaaaa", out)
        self.assertEqual(self.session("aaaaaaaa1111")["usage"]["acked_through"], 1)

    def test_usage_ack_with_nothing_pending(self):
        self.make_session()
        code, out, _ = self.run_cli("usage-ack", "--cwd", str(self.DC))
        self.assertEqual(code, 0)
        self.assertIn("nothing acknowledged", out)

    def test_stale_ok_above_60_is_refused(self):
        self.make_session()
        code, out, err = self.run_cli("usage-ack", "--stale-ok", "61", "--cwd", str(self.DC))
        self.assertEqual(code, 2)
        self.assertIn("refused", err)
        self.assertIsNone(self.session()["usage"]["stale_ok_until"])

    def test_stale_ok_opens_a_window_recorded_as_usage_ack(self):
        self.make_session()
        code, out, _ = self.run_cli("usage-ack", "--stale-ok", "30", "--cwd", str(self.DC))
        self.assertEqual(code, 0)
        u = self.session()["usage"]
        until = paths.parse_iso(u["stale_ok_until"])
        self.assertAlmostEqual(until - self.now, 1800, delta=120)
        self.assertEqual(u["stale_ok_by"], "usage-ack")
        self.assertIn("acked_by usage-ack", out)

    def test_set_cadence(self):
        self.make_session()
        code, out, _ = self.run_cli("set-cadence", "20", "--cwd", str(self.DC))
        self.assertEqual(code, 0)
        self.assertEqual(self.session()["usage"]["cadence"], 20)
        self.assertEqual(self.run_cli("set-cadence", "0", "--cwd", str(self.DC))[0], 2)

    def test_status_is_read_only_and_names_the_direction(self):
        self.frozen("aaaaaaaa1111")
        path = self.cfg.session_file("claude", "aaaaaaaa1111")
        before = Path(path).read_text()
        code, out, _ = self.run_cli("status", "--cwd", str(self.DC))
        self.assertEqual(code, 0)
        self.assertIn("direction: demo (registered", out)
        self.assertIn("freeze: checkpoint 1, stage crossed", out)
        self.assertEqual(Path(path).read_text(), before)

    def test_mark_checkpoint_recorded(self):
        s = self.frozen("aaaaaaaa1111")
        self.assertTrue(state.mark_checkpoint_recorded(s, 1, self.now))
        self.assertEqual(s["usage"]["freeze"]["stage"], "recorded")
        self.assertFalse(state.mark_checkpoint_recorded(s, 2, self.now))


if __name__ == "__main__":
    unittest.main()
