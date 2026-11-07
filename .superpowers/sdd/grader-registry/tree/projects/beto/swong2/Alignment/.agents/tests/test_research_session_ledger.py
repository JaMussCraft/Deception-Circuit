"""Ticket 03: ``ledger add|reconcile|api`` and ``job add|update|list``."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

from _rs_records import SAT_0805, RecordsMixin
from _rs_testlib import RSTestCase

from research_session import registry

CLI = str(Path(__file__).resolve().parents[1] / "research_session" / "cli.py")


class LedgerTest(RecordsMixin, RSTestCase):
    def setUp(self):
        super(LedgerTest, self).setUp()
        self.setup_root(with_templates=False)
        self.set_clock(SAT_0805)
        self.d = self.make_direction("demo")
        self.run_cli("worklog-append", str(self.d), "--kind", "entry", "--title", "Session started", "--body",
                     "Goal: test the ledger.")

    def ledger(self):
        return self.read_json_file(self.d / "ledger.json")

    def add(self, job, gpus=1, minutes=60, cluster="delta"):
        return self.run_cli("ledger", "add", str(self.d), "--cluster", cluster, "--account", "bimc-delta-gpu",
                            "--partition", "gpuA40x4", "--gpus", str(gpus), "--minutes", str(minutes), "--job-id", job,
                            "--commit", "abc1234")

    def head_row(self, label):
        for line in (self.d / "WORKLOG.md").read_text().splitlines():
            if line.startswith("| %s | " % label):
                return line
        raise AssertionError(label)

    def test_add_computes_hours_totals_and_rows(self):
        before = self.head_row("GPU budget")
        code, out, err = self.add("101", gpus=2, minutes=90)
        self.assertEqual(code, 0, err)
        led = self.ledger()
        r = led["reservations"][0]
        self.assertEqual((r["id"], r["status"], r["reserved_gpu_hours"]), ("r-001", "PENDING", 3.0))
        self.assertEqual(led["totals"]["reserved_gpu_hours"], 3.0)
        self.assertNotEqual(self.head_row("GPU budget"), before)
        self.assertIn("(3.0 reserved)", self.head_row("GPU budget"))
        self.assertIn("clusters: Delta", self.head_row("GPU budget"))
        self.assertEqual(registry.validate_ledger(led), ([], []))

    def test_add_refuses_past_caps(self):
        code, out, err = self.add("101", gpus=4, minutes=301)  # 20.07 GPU-h > 20
        self.assertEqual(code, 1)
        self.assertIn("exceed the cap", err)
        self.assertEqual(self.ledger()["reservations"], [])
        self.assertEqual(self.add("1")[0], 0)
        self.assertEqual(self.add("2")[0], 0)
        code, out, err = self.add("3")
        self.assertEqual(code, 1)
        self.assertIn("at once", err)
        self.run_cli("ledger", "reconcile", str(self.d), "1", "--actual-seconds", "3000", "--status", "COMPLETED")
        self.assertEqual(self.add("3")[0], 0)

    def test_cap_zero_allows_no_gpu_work(self):
        self.run_cli("worklog-set", str(self.d), "gpu-cap", "0")
        code, out, err = self.add("9", gpus=1, minutes=1)
        self.assertEqual(code, 1)
        self.run_cli("worklog-set", str(self.d), "gpu-cap", "5")
        self.run_cli("worklog-set", str(self.d), "max-gpu-jobs", "0")
        code, out, err = self.add("9", gpus=1, minutes=1)
        self.assertEqual(code, 1)
        self.assertIn("at once", err)

    def test_reconcile(self):
        self.add("101", gpus=2, minutes=60)
        code, out, err = self.run_cli("ledger", "reconcile", str(self.d), "101", "--actual-seconds", "1800",
                                      "--status", "COMPLETED")
        self.assertEqual(code, 0, err)
        led = self.ledger()
        self.assertEqual((led["reservations"][0]["actual_seconds"], led["reservations"][0]["status"]),
                         (1800, "COMPLETED"))
        self.assertEqual(led["totals"]["actual_gpu_seconds"], 3600)
        self.assertIn("1.0 of 20 GPU-h actual", self.head_row("GPU budget"))
        self.assertEqual(self.run_cli("ledger", "reconcile", str(self.d), "999", "--actual-seconds", "1",
                                      "--status", "COMPLETED")[0], 1)
        self.assertEqual(self.run_cli("ledger", "reconcile", str(self.d), "101", "--actual-seconds", "1",
                                      "--status", "DONE")[0], 1)

    def test_api_known_reserve_and_cap(self):
        code, out, err = self.run_cli("ledger", "api", str(self.d), "--usd", "1.25", "--calls", "10")
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("ledger", "api", str(self.d), "--usd", "0.5", "--calls", "2")
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("ledger", "api", str(self.d), "--usd", "0.4", "--reserve")
        self.assertEqual(code, 0, err)
        led = self.ledger()
        self.assertEqual(led["api_calls"], [{"date": "2026-10-31", "provider": "openrouter", "calls": 12,
                                             "usd": 1.75}])
        self.assertEqual((led["totals"]["api_usd_known"], led["totals"]["api_usd_reserve"]), (1.75, 0.4))
        self.assertEqual(self.head_row("OpenRouter credit"),
                         "| OpenRouter credit | $1.75 of $10.00 cap, plus $0.40 reserved |")
        code, out, err = self.run_cli("ledger", "api", str(self.d), "--usd", "9")
        self.assertEqual(code, 3)
        self.assertIn("CAP WARNING", err)
        self.assertEqual(self.ledger()["totals"]["api_usd_known"], 10.75)
        self.assertIn("$10.75 of $10.00 cap", self.head_row("OpenRouter credit"))

    def test_totals_without_rows_survive_writes_and_rollup(self):
        legacy = {"reserved_gpu_hours": 39.5333, "actual_gpu_seconds": 9409, "api_usd_known": 0.0,
                  "api_usd_reserve": 0.0}
        d = self.make_direction("sdr-mechanism", ledger={
            "caps": {"reserved_gpu_hours": 100.0, "paid_api_usd": 0.0, "max_concurrent_gpu_jobs": 2},
            "totals": dict(legacy)})
        self.run_cli("worklog-append", str(d), "--kind", "entry", "--title", "Resumed", "--body", "Paused work resumes.")
        self.assertEqual(self.read_json_file(d / "ledger.json")["totals"], legacy)
        code, out, err = self.run_cli("worklog-set", str(d), "max-gpu-jobs", "3")
        self.assertEqual(code, 0, err)
        led = self.read_json_file(d / "ledger.json")
        self.assertEqual(led["totals"], legacy)
        self.assertEqual(led["legacy_totals"], {"reserved_gpu_hours": 39.5333, "actual_gpu_seconds": 9409,
                                                "api_usd_known": 0.0})
        code, out, err = self.run_cli("ledger", "add", str(d), "--cluster", "delta", "--account", "a", "--partition",
                                      "p", "--gpus", "1", "--minutes", "60", "--job-id", "5")
        self.assertEqual(code, 0, err)
        self.run_cli("ledger", "reconcile", str(d), "5", "--actual-seconds", "1800", "--status", "COMPLETED")
        led = self.read_json_file(d / "ledger.json")
        self.assertAlmostEqual(led["totals"]["reserved_gpu_hours"], 40.5333)
        self.assertEqual(led["totals"]["actual_gpu_seconds"], 9409 + 1800)
        self.assertEqual(registry.validate_ledger(led), ([], []))
        self.assertIn("(40.5 reserved)", (d / "WORKLOG.md").read_text())
        # The reserved cap counts the carried history: 40.53 + 60 > 100.
        code, out, err = self.run_cli("ledger", "add", str(d), "--cluster", "delta", "--account", "a", "--partition",
                                      "p", "--gpus", "1", "--minutes", "3600", "--job-id", "6")
        self.assertEqual(code, 1)
        self.assertIn("exceed the cap", err)
        code, out, err = self.run_cli("ledger-rollup", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        roll = self.read_json_file(self.root / "ledger.json")["directions"]["sdr-mechanism"]
        self.assertAlmostEqual(roll["reserved_gpu_hours"], 40.5333)
        self.assertEqual(roll["actual_gpu_seconds"], 11209)

    def test_rows_free_ledger_without_worklog_keeps_totals(self):
        d = self.make_direction("paused-legacy", ledger={"totals": {
            "reserved_gpu_hours": 2.5, "actual_gpu_seconds": 900, "api_usd_known": 1.5, "api_usd_reserve": 0.0}})
        os.unlink(str(d / "worklog.json"))
        code, out, err = self.run_cli("ledger", "api", str(d), "--usd", "0.25", "--calls", "1")
        self.assertEqual(code, 0, err)
        led = self.read_json_file(d / "ledger.json")
        self.assertEqual((led["totals"]["reserved_gpu_hours"], led["totals"]["actual_gpu_seconds"],
                          led["totals"]["api_usd_known"]), (2.5, 900, 1.75))

    def test_ledger_without_worklog_writes_ledger_only(self):
        d = self.make_direction("paused-one")
        os.unlink(str(d / "worklog.json"))
        code, out, err = self.run_cli("ledger", "api", str(d), "--usd", "1")
        self.assertEqual(code, 0, err)
        self.assertIn("not re-rendered", err)
        self.assertFalse((d / "WORKLOG.md").exists())

    def test_two_concurrent_adds_lose_nothing(self):
        self.run_cli("worklog-set", str(self.d), "gpu-cap", "1000")
        self.run_cli("worklog-set", str(self.d), "max-gpu-jobs", "100")
        driver = Path(self.tmp) / "driver.py"
        driver.write_text(
            "import sys\n"
            "sys.argv = [sys.argv[0]] + sys.argv[1:]\n"
            "sys.path.insert(0, %r)\n"
            "from research_session import cli\n"
            "d, tag = sys.argv[1], sys.argv[2]\n"
            "for i in range(10):\n"
            "    code = cli.main(['ledger', 'add', d, '--cluster', 'delta', '--account', 'a', '--partition', 'p',\n"
            "                     '--gpus', '1', '--minutes', '6', '--job-id', '%%s-%%d' %% (tag, i)])\n"
            "    assert code == 0, code\n" % str(Path(CLI).parents[1]))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        procs = [subprocess.Popen([sys.executable, "-B", str(driver), str(self.d), tag], env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE) for tag in ("a", "b")]
        for p in procs:
            out, err = p.communicate(timeout=120)
            self.assertEqual(p.returncode, 0, err.decode())
        led = self.ledger()
        self.assertEqual(len(led["reservations"]), 20)
        self.assertEqual(len(set(r["id"] for r in led["reservations"])), 20)
        self.assertAlmostEqual(led["totals"]["reserved_gpu_hours"], 2.0)


class JobTest(RecordsMixin, RSTestCase):
    def setUp(self):
        super(JobTest, self).setUp()
        self.setup_root(with_templates=False)
        self.set_clock(SAT_0805)
        self.d = self.make_direction("demo")

    def test_add_update_list_round_trip(self):
        code, out, err = self.run_cli("job", "add", str(self.d), "--job-id", "123", "--cluster", "delta")
        self.assertEqual(code, 0, err)
        self.assertIn("timeout 60m sh -c 'until sacct -j 123 -X -n -o State | grep -qE", out)
        code, out, err = self.run_cli("job", "add", str(self.d), "--job-id", "77", "--cluster", "bridges2",
                                      "--timeout-min", "30")
        self.assertIn("timeout 30m sh -c 'until ssh -o BatchMode=yes bridges2 sacct -j 77", out)
        self.assertEqual(self.run_cli("job", "add", str(self.d), "--job-id", "5", "--cluster", "delta",
                                      "--timeout-min", "90")[0], 1)
        self.assertEqual(self.run_cli("job", "add", str(self.d), "--job-id", "123", "--cluster", "delta")[0], 1)
        st = self.read_json_file(self.d / "state.json")
        self.assertEqual([j["job_id"] for j in st["jobs"]], ["123", "77"])
        self.assertEqual(st["jobs"][0]["status"], "PENDING")
        self.assertEqual(registry.validate_state(st), ([], []))
        code, out, err = self.run_cli("job", "update", str(self.d), "123", "--status", "RUNNING")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read_json_file(self.d / "state.json")["jobs"][0]["status"], "RUNNING")
        self.run_cli("job", "update", str(self.d), "77", "--status", "COMPLETED")
        code, out, err = self.run_cli("job", "list", str(self.d))
        self.assertIn("job 123 on delta: RUNNING", out)
        self.assertIn("waiter: timeout 60m", out)
        self.assertNotIn("job 77", out)
        code, out, err = self.run_cli("job", "list", str(self.d), "--all")
        self.assertIn("job 77 on bridges2: COMPLETED", out)
        self.assertEqual(self.run_cli("job", "update", str(self.d), "999", "--status", "RUNNING")[0], 1)


if __name__ == "__main__":
    unittest.main()
