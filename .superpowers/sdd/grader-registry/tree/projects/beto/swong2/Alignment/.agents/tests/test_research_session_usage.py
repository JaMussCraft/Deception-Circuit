"""Usage readings, segments, the Codex reader and the R8 refresh (ticket 02).

No test opens a real credentials file or reaches the network: the reader and the endpoint are mocked.
"""

import datetime
import json
import os
import socket
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from _rs_testlib import RESET, RSTestCase, fake_token

from research_session import gate, oauth_refresh, state, usage

# The real fetch function, captured before RSTestCase replaces it with a guard in each test.
ORIGINAL_HTTP_GET = oauth_refresh.http_get
WEEKLY_RESET_FROM_BODY = int(datetime.datetime(2026, 11, 4, 12, tzinfo=datetime.timezone.utc).timestamp())


class ClaudeReadingTests(RSTestCase):
    def test_fresh_reading(self):
        self.write_usage(five=9, seven=11, fable=17, age=60)
        r = usage.read_claude(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual((r["h"], r["seven_day"], r["fable"], r["w"]), (9, 11, 17, 17))
        self.assertEqual(r["fable_gap"], 6)
        self.assertEqual(r["resets_at"], RESET)
        self.assertFalse(r["refresh_attempted"])

    def test_stale_timestamp_with_fresh_model_scoped_makes_five_hour_unknown(self):
        self.write_usage(age=20 * 60, fable_age=60)
        r = usage.read_claude(self.cfg, self.now, refresh=False)
        self.assertFalse(r["known"])
        self.assertIsNone(r["h"])
        self.assertIsNone(r["five_hour"])
        self.assertEqual(r["fable"], 17)
        self.assertTrue(r["fresh_fable"])
        self.assertFalse(r["fresh_main"])
        self.assertIn("timestamp", r["error"])

    def test_missing_weekly_key_in_fresh_file_reads_zero(self):
        self.write_usage(seven=None, fable=23)
        data = self.read_usage_file()
        del data["rate_limits"]["seven_day"]["used_percentage"]
        Path(self.cfg.usage_file).write_text(json.dumps(data))
        r = usage.read_claude(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual(r["seven_day"], 0)
        self.assertEqual(r["w"], 23)
        self.assertEqual(r["notes"], [])
        self.assertEqual(self.token_calls, [])

    def test_r40_missing_five_hour_in_fresh_file_is_not_applicable(self):
        self.write_usage(seven=15, fable=19, drop=("five_hour",))
        r = usage.read_claude(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertIsNone(r["h"])
        self.assertIsNone(r["five_hour"])
        self.assertEqual(r["w"], 19)
        self.assertEqual(r["notes"], ["five-hour limit not applicable"])
        self.assertFalse(r["refresh_attempted"])
        self.assertEqual(self.token_calls, [])
        self.assertEqual(self.http_calls, [])
        self.assertTrue(usage.format_reading(r).startswith("five-hour not applicable, seven-day 15%"))

    def test_missing_fable_row_reads_zero(self):
        data = self.write_usage(seven=23)
        data["rate_limits"]["model_scoped"] = [{"display_name": "Opus", "used_percentage": 50, "resets_at": RESET}]
        Path(self.cfg.usage_file).write_text(json.dumps(data))
        r = usage.read_claude(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual(r["fable"], 0)
        self.assertEqual(r["w"], 23)

    def test_missing_key_in_stale_file_is_unknown_not_zero(self):
        self.write_usage(age=3600, drop=("five_hour",))
        r = usage.read_claude(self.cfg, self.now, refresh=False)
        self.assertFalse(r["known"])
        self.assertIsNone(r["h"])

    def test_malformed_value_is_unknown(self):
        data = self.write_usage()
        data["rate_limits"]["seven_day"]["used_percentage"] = "11"
        Path(self.cfg.usage_file).write_text(json.dumps(data))
        r = usage.read_claude(self.cfg, self.now, refresh=False)
        self.assertFalse(r["known"])
        self.assertIn("malformed", r["error"])


class SegmentTests(unittest.TestCase):
    def u(self):
        return state.new_usage("claude")

    def test_resets_at_rollover_opens_a_segment(self):
        u = self.u()
        usage.update_segments(u, 20, RESET)
        usage.update_segments(u, 30, RESET)
        usage.update_segments(u, 4, RESET + 7 * 86400)
        self.assertEqual(len(u["segments"]), 2)
        self.assertEqual(u["session_points"], 10)
        usage.update_segments(u, 12, RESET + 7 * 86400)
        self.assertEqual(u["session_points"], 18)

    def test_drop_below_last_without_reset_change_opens_a_segment(self):
        u = self.u()
        usage.update_segments(u, 20, RESET)
        usage.update_segments(u, 27, RESET)
        usage.update_segments(u, 15, RESET)
        self.assertEqual(len(u["segments"]), 2)
        self.assertEqual(u["segments"][-1], {"resets_at": RESET, "baseline": 15, "last": 15})
        self.assertEqual(u["session_points"], 7)

    def test_points_sum_across_two_segments(self):
        u = self.u()
        for w, r in ((11, RESET), (27, RESET), (2, RESET + 604800), (9, RESET + 604800)):
            usage.update_segments(u, w, r)
        self.assertEqual(u["session_points"], (27 - 11) + (9 - 2))

    def test_sub_minute_reset_jitter_is_the_same_window(self):
        u = self.u()
        usage.update_segments(u, 20, RESET)
        usage.update_segments(u, 22, RESET + 1)
        self.assertEqual(len(u["segments"]), 1)
        self.assertEqual(u["session_points"], 2)


class CodexReaderTests(RSTestCase):
    def weekly(self, used):
        return {"status": "ok", "weekly": {"used_percent": used, "remaining_percent": 100 - used,
                                           "resets_at": RESET}, "should_pause": used >= 80}

    def test_exit_0_below_cap(self):
        self.fake_codex_usage(0, self.weekly(31))
        r, entry = usage.read_codex(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual(r["w"], 31)
        self.assertIsNone(r["h"])
        self.assertEqual(entry["exit"], 0)

    def test_exit_2_cap_reached_is_known(self):
        self.fake_codex_usage(2, dict(self.weekly(83), status="pause"))
        r, _ = usage.read_codex(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual(r["w"], 83)
        self.assertTrue(gate.cap_reached(r))

    def test_exit_1_unknown(self):
        self.fake_codex_usage(1, {"status": "unknown", "weekly": None, "error": "Requested usage bucket is unavailable."})
        r, _ = usage.read_codex(self.cfg, self.now)
        self.assertFalse(r["known"])
        self.assertIn("exit 1", r["error"])

    def test_cache_hit_within_120_s(self):
        self.fake_codex_usage(0, self.weekly(31))
        session = {"codex_cache": None}
        r1 = usage.read(self.cfg, "codex", self.now, session)
        r2 = usage.read(self.cfg, "codex", self.now + 119, session)
        self.assertEqual(self.codex_calls(), 1)
        self.assertTrue(r2["cached"])
        self.assertEqual(r1["w"], r2["w"])
        usage.read(self.cfg, "codex", self.now + 121, session)
        self.assertEqual(self.codex_calls(), 2)


class RefreshTests(RSTestCase):
    def setUp(self):
        super().setUp()
        self.token_reader = lambda path: (fake_token(), self.now + 3600)
        self.http = lambda url, token, timeout: self.body(five=30, seven=40, fable=45)

    def test_stale_usage_is_refreshed_and_becomes_fresh(self):
        self.write_usage(age=3600)
        r = usage.read_claude(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual((r["h"], r["seven_day"], r["fable"], r["w"]), (30, 40, 45, 45))
        self.assertEqual(r["refresh"], "fetched")
        self.assertEqual(self.http_calls, [(self.cfg.oauth_url, 8)])
        data = self.read_usage_file()
        self.assertEqual(data["timestamp"], int(self.now))
        self.assertEqual(data["rate_limits"]["model_scoped_fetched_at"], int(self.now))
        self.assertEqual(data["rate_limits"]["seven_day"]["resets_at"], WEEKLY_RESET_FROM_BODY)
        cache = json.loads(Path(self.cfg.oauth_cache).read_text())
        self.assertEqual(cache["fetched_at"], int(self.now))
        self.assertFalse(os.path.exists(self.cfg.oauth_lock))

    def test_every_preexisting_key_survives(self):
        data = self.write_usage(age=3600, extra={"note": "kept", "other": {"x": 1}})
        data["rate_limits"]["seven_day"]["window_label"] = "kept-too"
        data["rate_limits"]["seven_day_opus"] = {"used_percentage": 3}
        Path(self.cfg.usage_file).write_text(json.dumps(data))
        usage.read_claude(self.cfg, self.now)
        after = self.read_usage_file()
        self.assertEqual(after["note"], "kept")
        self.assertEqual(after["other"], {"x": 1})
        self.assertEqual(after["rate_limits"]["seven_day"]["window_label"], "kept-too")
        self.assertEqual(after["rate_limits"]["seven_day_opus"], {"used_percentage": 3})

        def keys(d, prefix=""):
            out = set()
            for k, v in d.items():
                out.add(prefix + k)
                if isinstance(v, dict):
                    out |= keys(v, prefix + k + ".")
            return out
        self.assertLessEqual(keys(data), keys(after))

    def test_lock_held_by_another_process_within_60_s_skips_fetch(self):
        self.write_usage(age=3600)
        os.mkdir(self.cfg.oauth_lock)
        os.utime(self.cfg.oauth_lock, (self.now - 30, self.now - 30))
        r = usage.read_claude(self.cfg, self.now)
        self.assertFalse(r["known"])
        self.assertEqual(self.http_calls, [])
        self.assertIn("lock", r["refresh_error"])
        self.assertTrue(os.path.isdir(self.cfg.oauth_lock))

    def test_lock_older_than_60_s_is_swept(self):
        self.write_usage(age=3600)
        os.mkdir(self.cfg.oauth_lock)
        os.utime(self.cfg.oauth_lock, (self.now - 61, self.now - 61))
        r = usage.read_claude(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual(len(self.http_calls), 1)
        self.assertFalse(os.path.exists(self.cfg.oauth_lock))

    def test_cache_younger_than_300_s_is_reused_without_fetch(self):
        self.write_usage(age=3600)
        self.write_cache(fetched_age=200)
        r = usage.read_claude(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual(r["refresh"], "cache")
        self.assertEqual(self.http_calls, [])
        self.assertEqual(self.token_calls, [])
        self.assertEqual(self.read_usage_file()["timestamp"], int(self.now - 200))

    def test_retry_floor_after_a_failed_fetch_leaves_reading_unknown(self):
        self.write_usage(age=3600)
        self.write_cache(error="http 500", fetched_age=100)
        r = usage.read_claude(self.cfg, self.now)
        self.assertFalse(r["known"])
        self.assertEqual(self.http_calls, [])
        self.assertIn("retry floor", r["refresh_error"])
        self.assertIn("http 500", r["refresh_error"])

    def check_failure_denies_spawn(self, expect):
        self.write_usage(age=3600)
        r = usage.read_claude(self.cfg, self.now)
        self.assertFalse(r["known"])
        self.assertIn(expect, r["refresh_error"])
        session = state.new_session("claude", "abc", str(self.DC), self.now)
        d = gate.decide({"tool_name": "Agent", "tool_input": {}, "cwd": str(self.DC)}, session, r, self.cfg)
        self.assertFalse(d.allow)
        self.assertIn(expect, d.reason)
        self.assertIn("--stale-ok 30", d.reason)
        return d

    def test_endpoint_error_leaves_reading_unknown_and_gate_denies(self):
        def http(url, token, timeout):
            raise oauth_refresh.FetchError("http 503")
        self.http = http
        self.check_failure_denies_spawn("http 503")
        self.assertIn("http 503", json.loads(Path(self.cfg.oauth_cache).read_text())["error"])

    def test_timeout_leaves_reading_unknown_and_gate_denies(self):
        def http(url, token, timeout):
            raise socket.timeout("timed out")
        self.http = http
        self.check_failure_denies_spawn("timeout after 8 s")

    def test_default_http_get_uses_8_s_timeout_and_maps_timeout(self):
        seen = {}

        def urlopen(req, timeout=None):
            seen["timeout"] = timeout
            seen["auth_in_url"] = fake_token() in req.full_url
            raise urllib.error.URLError(socket.timeout("timed out"))
        with mock.patch("urllib.request.urlopen", urlopen):
            with self.assertRaises(oauth_refresh.FetchError) as ctx:
                ORIGINAL_HTTP_GET(self.cfg.oauth_url, fake_token(), oauth_refresh.TIMEOUT_SECONDS)
        self.assertEqual(seen["timeout"], 8)
        self.assertFalse(seen["auth_in_url"])
        self.assertEqual(str(ctx.exception), "timeout after 8 s")
        self.assertIsNone(ctx.exception.__cause__)
        self.assertTrue(ctx.exception.__suppress_context__)

    def test_absent_window_is_filled_from_an_older_cache_without_moving_timestamp(self):
        # Fresh timestamp without five_hour, stale Fable row: the refresh reuses a cache fetched 100 s ago.
        self.write_usage(seven=15, fable=19, fable_age=3600, drop=("five_hour",))
        self.write_cache(self.body(five=37, seven=40, fable=45), fetched_age=100)
        r = usage.read_claude(self.cfg, self.now)
        self.assertEqual(self.http_calls, [])
        self.assertEqual(r["refresh"], "cache")
        self.assertTrue(r["known"])
        self.assertEqual(r["h"], 37)
        self.assertEqual(r["seven_day"], 15)
        self.assertEqual(r["fable"], 45)
        data = self.read_usage_file()
        self.assertEqual(data["timestamp"], int(self.now))
        self.assertEqual(data["rate_limits"]["five_hour"]["used_percentage"], 37)
        self.assertEqual(data["rate_limits"]["seven_day"]["used_percentage"], 15)
        self.assertEqual(data["rate_limits"]["model_scoped_fetched_at"], int(self.now - 100))

    def test_merge_does_not_rewrite_an_unchanged_file(self):
        self.write_usage(age=3600)
        oauth_refresh.merge_into_usage(self.cfg.usage_file, self.body(), int(self.now))
        os.utime(self.cfg.usage_file, (self.now - 500, self.now - 500))
        before = os.stat(self.cfg.usage_file)
        oauth_refresh.merge_into_usage(self.cfg.usage_file, self.body(), int(self.now))
        after = os.stat(self.cfg.usage_file)
        self.assertEqual((before.st_ino, before.st_mtime), (after.st_ino, after.st_mtime))

    def test_r40_stale_refresh_whose_body_lacks_five_hour_is_not_applicable(self):
        body = self.body(seven=40, fable=45)
        del body["five_hour"]
        body["limits"] = [row for row in body["limits"] if row["kind"] != "session"]
        self.http = lambda url, token, timeout: body
        self.write_usage(age=3600, drop=("five_hour",))
        r = usage.read_claude(self.cfg, self.now)
        self.assertTrue(r["known"])
        self.assertEqual(len(self.http_calls), 1)
        self.assertIsNone(r["h"])
        self.assertEqual(r["w"], 45)
        self.assertEqual(r["notes"], ["five-hour limit not applicable"])
        self.assertNotIn("five_hour", self.read_usage_file()["rate_limits"])

    def test_expired_token_is_not_sent(self):
        self.token_reader = lambda path: (fake_token(), self.now - 1)
        self.write_usage(age=3600)
        r = usage.read_claude(self.cfg, self.now)
        self.assertFalse(r["known"])
        self.assertEqual(self.http_calls, [])
        self.assertIn("token expired", r["refresh_error"])

    def test_planted_token_never_appears_in_output_or_files(self):
        token = fake_token()
        self.assertIn("PLANTED", token)

        def leaky(url, tok, timeout):
            raise RuntimeError("upstream said: bad bearer " + tok)
        for http in (leaky, lambda url, tok, timeout: self.body()):
            for path in (self.cfg.oauth_cache,):
                if os.path.exists(path):
                    os.unlink(path)
            self.http = http
            self.write_usage(age=3600)
            code, out, err = self.run_cli("usage-check")
            for text in (out, err, Path(self.cfg.usage_file).read_text(), Path(self.cfg.oauth_cache).read_text()):
                self.assertNotIn(token, text)
                self.assertNotIn("PLANTED", text)
        self.assertEqual(len(self.http_calls), 2)


class UsageCheckCliTests(RSTestCase):
    def test_usage_check_prints_reading_freshness_refresh_and_gap(self):
        self.token_reader = lambda path: (fake_token(), self.now + 3600)
        self.http = lambda url, token, timeout: self.body(five=30, seven=40, fable=47)
        self.write_usage(age=3600)
        code, out, err = self.run_cli("usage-check")
        self.assertEqual(code, 0, err)
        self.assertIn("five-hour 30%, seven-day 40%, Fable 47%, weekly max 47%", out)
        self.assertIn("freshness: five-hour and seven-day fresh", out)
        self.assertIn("refresh: fetched from the usage endpoint", out)
        self.assertIn("fable gap: 7 points. Fable is 7 points above all-models", out)

    def test_usage_check_fresh_file_needs_no_refresh(self):
        self.write_usage(seven=11, fable=14)
        code, out, _ = self.run_cli("usage-check")
        self.assertEqual(code, 0)
        self.assertIn("refresh: not needed", out)
        self.assertIn("fable gap: 3 points\n", out)

    def test_usage_check_prints_the_r40_note(self):
        self.write_usage(seven=15, fable=19, drop=("five_hour",))
        code, out, _ = self.run_cli("usage-check")
        self.assertEqual(code, 0)
        self.assertIn("reading (claude): five-hour not applicable, seven-day 15%, Fable 19%", out)
        self.assertIn("refresh: not needed", out)
        self.assertIn("note: five-hour limit not applicable", out)
        self.assertEqual(self.http_calls, [])

    def test_usage_check_unknown_exits_1(self):
        self.write_usage(age=3600)
        self.write_cache(error="no token", fetched_age=10)
        code, out, _ = self.run_cli("usage-check")
        self.assertEqual(code, 1)
        self.assertIn("reading (claude): unknown", out)
        self.assertIn("refresh: skipped; retry floor", out)


if __name__ == "__main__":
    unittest.main()
