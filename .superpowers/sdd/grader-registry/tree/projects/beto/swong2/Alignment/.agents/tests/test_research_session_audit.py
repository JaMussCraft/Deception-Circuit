"""Ticket 11: ``audit-scan`` over synthetic Claude and Codex transcripts.

The record shapes copy the key sets seen in a key-only inspection of real transcripts (hand-back 11): main-session
records have no ``agentId``, subagent records do; ``api-request-blob`` records repeat earlier tool blocks; denials
carry a top-level ``toolDenialKind`` and a ``permissionDecision`` with ``decision: reject``; Codex rollouts hold
``compacted`` records and ``spawn_agent`` function calls whose ``arguments`` is a JSON string.
"""

import json
import os
import unittest
from pathlib import Path

from _rs_testlib import RSTestCase, fake_token

SID = "0123abcd-1111-2222-3333-444455556666"
TAG = "claude-0123abcd"


def ts(minute, second=0, ms=0):
    """A transcript timestamp ``minute`` minutes after 16:00 UTC (minutes may exceed 59)."""
    hour, minute = divmod(minute, 60)
    return ("2026-10-31T%02d:%02d:%02d.%03dZ" % (16 + hour, minute, second, ms))


class Transcript(object):
    """Builds Claude transcript records with the observed key sets."""

    def __init__(self, agent=None, sid=SID):
        self.agent = agent
        self.sid = sid
        self.records = []
        self.n = 0

    def _base(self, kind, when):
        self.n += 1
        r = {"type": kind, "sessionId": self.sid, "timestamp": when, "uuid": "u-%s-%d" % (self.agent, self.n),
             "parentUuid": None, "isSidechain": self.agent is not None, "cwd": "/abs", "gitBranch": "b",
             "entrypoint": "cli", "userType": "external", "version": "2.1.316", "sessionKind": "main",
             "slug": "s"}
        if self.agent:
            r["agentId"] = self.agent
        return r

    def call(self, tid, name, inp, when):
        r = self._base("assistant", when)
        r.update({"requestId": "req", "message": {"role": "assistant", "model": "claude-opus-5-5", "content": [
            {"type": "thinking", "thinking": "hidden"},
            {"type": "tool_use", "id": tid, "name": name, "input": inp}]}})
        self.records.append(r)
        return self

    def result(self, tid, is_error, when, denial=None, decision=None):
        r = self._base("user", when)
        r.update({"promptId": "p", "sourceToolAssistantUUID": "a", "toolUseResult": "Error: x" if is_error else {},
                  "message": {"role": "user", "content": [
                      {"type": "tool_result", "tool_use_id": tid, "content": "output text", "is_error": is_error}]}})
        r["permissionDecision"] = {"decision": decision or ("reject" if denial else "accept"), "source": "config",
                                   "reasonType": "rule"}
        if denial:
            r["toolDenialKind"] = denial
        self.records.append(r)
        return self

    def ok(self, tid, name, inp, when):
        return self.call(tid, name, inp, when).result(tid, False, when)

    def fail(self, tid, name, inp, when):
        return self.call(tid, name, inp, when).result(tid, True, when)

    def boundary(self, when, pre, post=27000, trigger="auto"):
        r = self._base("system", when)
        r.update({"subtype": "compact_boundary", "content": "Conversation compacted", "level": "info",
                  "logicalParentUuid": None, "compactMetadata": {
                      "trigger": trigger, "preTokens": pre, "postTokens": post, "durationMs": 1000,
                      "cumulativeDroppedTokens": pre - post, "preservedMessages": {"uuids": []},
                      "preservedSegment": {"headUuid": "h", "tailUuid": "t", "anchorUuid": "a"}}})
        self.records.append(r)
        return self

    def summary(self, when):
        r = self._base("user", when)
        r.update({"isCompactSummary": True, "isVisibleInTranscriptOnly": True,
                  "message": {"role": "user", "content": "This session is being continued."}})
        self.records.append(r)
        return self

    def blob(self, blocks):
        self.records.append({"type": "api-request-blob", "hash": "h%d" % len(self.records), "sessionId": self.sid,
                             "message": {"content": blocks}})
        return self

    def other(self, kind):
        self.records.append({"type": kind, "sessionId": self.sid})
        return self

    def write(self, path, garbage=0):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(r) for r in self.records] + ["{not json"] * garbage
        path.write_text("\n".join(lines) + "\n")
        return path


def codex_rollout(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))
    return path


def cx(kind, payload, when):
    return {"timestamp": when, "type": kind, "ordinal": 1, "metadata": {}, "payload": payload}


class AuditScanTest(RSTestCase):
    def setUp(self):
        super(AuditScanTest, self).setUp()
        self.proj = Path(self.tmp) / "projects" / "-abs"

    def scan(self, *argv):
        code, out, err = self.run_cli("audit-scan", *[str(a) for a in argv])
        self.assertIn(code, (0, 2), err)
        return code, json.loads(out), err

    def agent(self, report, name, tool="claude"):
        for a in report["agents"]:
            if a["agent"] == name and a["tool"] == tool:
                return a
        self.fail("no agent %r in %r" % (name, [a["agent"] for a in report["agents"]]))

    def main_with_subagent(self):
        main = Transcript().ok("t1", "Bash", {"command": "ls"}, ts(0)).boundary(ts(5), 368681, 27778).summary(ts(5))
        main.call("t2", "Agent", {"description": "d", "prompt": "p", "subagent_type": "ticket-implementer",
                                  "name": "impl-01", "model": "opus"}, ts(6))
        mpath = main.write(self.proj / (SID + ".jsonl"))
        sub = Transcript(agent="aimpl-01-c457").boundary(ts(9), 612000).boundary(ts(20), 598000, trigger="manual")
        spath = sub.write(self.proj / SID / "subagents" / "agent-aimpl-01-c457.jsonl")
        (self.proj / SID / "subagents" / "agent-aimpl-01-c457.meta.json").write_text(json.dumps(
            {"agentType": "impl-01", "model": "opus", "description": "secret prompt text", "name": "impl-01"}))
        return mpath, spath

    # -- compactions

    def test_compactions_with_pretokens_per_agent_including_subagents(self):
        mpath, spath = self.main_with_subagent()
        code, rep, err = self.scan(mpath)
        self.assertEqual(code, 0)
        main = self.agent(rep, "main")
        self.assertEqual(main["session_id"], SID)
        self.assertEqual([(c["trigger"], c["preTokens"], c["postTokens"]) for c in main["compactions"]],
                         [("auto", 368681, 27778)])
        self.assertEqual(main["compact_summaries"], 1)
        self.assertTrue(main["compactions"][0]["at"].startswith("2026-10-31T12:05:00"))  # 16:05 UTC is 12:05 EDT
        sub = self.agent(rep, "aimpl-01-c457")
        self.assertEqual([c["preTokens"] for c in sub["compactions"]], [612000, 598000])
        self.assertEqual(sub["first_compaction_preTokens"], 612000)
        self.assertEqual(sub["agent_type"], "impl-01")
        self.assertEqual(sub["meta_model"], "opus")
        self.assertNotIn("secret prompt text", json.dumps(rep))
        self.assertEqual(rep["totals"]["compactions"], 3)
        self.assertEqual(rep["totals"]["main_compactions"], 1)
        self.assertEqual(len(rep["files"]), 2)

    def test_no_subagents_flag_and_directory_argument_without_duplicates(self):
        mpath, spath = self.main_with_subagent()
        code, rep, err = self.scan(mpath, "--no-subagents")
        self.assertEqual([a["agent"] for a in rep["agents"]], ["main"])
        code, rep, err = self.scan(mpath, self.proj, spath)
        self.assertEqual(sorted(f["path"] for f in rep["files"]), sorted([str(mpath), str(spath)]))
        self.assertEqual(rep["totals"]["compactions"], 3)

    def test_subagent_file_alone(self):
        mpath, spath = self.main_with_subagent()
        code, rep, err = self.scan(spath)
        self.assertEqual([a["agent"] for a in rep["agents"]], ["aimpl-01-c457"])
        self.assertEqual(self.agent(rep, "aimpl-01-c457")["meta_model"], "opus")

    # -- duplicates in api-request-blob records

    def test_api_request_blob_blocks_are_not_counted(self):
        t = Transcript().fail("t1", "Bash", {"command": "false"}, ts(0))
        t.blob([{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "false"}},
                {"type": "tool_result", "tool_use_id": "t1", "content": "x", "is_error": True},
                {"type": "tool_use", "id": "t9", "name": "Agent", "input": {"prompt": "p"}}])
        t.other("attachment").other("api-request").other("worktree-state")
        code, rep, err = self.scan(t.write(self.proj / "a.jsonl"))
        main = self.agent(rep, "main")
        self.assertEqual(main["tool_calls"], 1)
        self.assertEqual(main["tool_errors"], 1)
        self.assertEqual(main["agent_calls_without_model"], [])

    # -- runs of identical failing calls

    def test_runs_of_three_or_more_identical_failing_calls(self):
        t = Transcript()
        for i in range(4):  # a run of 4
            t.fail("a%d" % i, "Bash", {"command": "make test", "description": "d"}, ts(i))
        t.ok("b0", "Bash", {"command": "echo"}, ts(5))
        for i in range(2):  # 2 identical, then a different failure: no run
            t.fail("c%d" % i, "Read", {"file_path": "/x"}, ts(6 + i))
        t.fail("c9", "Read", {"file_path": "/y"}, ts(8))
        for i, ok in enumerate((False, False, True, False)):  # broken by a success: no run
            (t.ok if ok else t.fail)("d%d" % i, "Edit", {"file_path": "/z", "old_string": "a", "new_string": "b"},
                                     ts(10 + i))
        for i in range(3):  # 3 failures with the same input in a different key order: one run
            inp = {"file_path": "/w", "content": "q"} if i % 2 else {"content": "q", "file_path": "/w"}
            t.fail("e%d" % i, "Write", inp, ts(20 + i))
        code, rep, err = self.scan(t.write(self.proj / "a.jsonl"))
        runs = self.agent(rep, "main")["failing_runs"]
        self.assertEqual([(r["tool"], r["count"]) for r in runs], [("Bash", 4), ("Write", 3)])
        self.assertEqual(runs[0]["input"], "make test")
        self.assertTrue(runs[0]["first_at"] < runs[0]["last_at"])
        self.assertEqual(self.agent(rep, "main")["tool_errors"], 13)
        self.assertEqual(rep["totals"]["failing_runs"], 2)

    # -- Agent calls without a model

    def test_agent_calls_without_model(self):
        t = Transcript()
        t.call("g1", "Agent", {"prompt": "p", "subagent_type": "Explore", "description": "d", "model": "opus"}, ts(0))
        t.call("g2", "Agent", {"prompt": "p", "subagent_type": "general-purpose", "description": "d"}, ts(1))
        t.call("g3", "Task", {"prompt": "p", "subagent_type": "Plan", "description": "d"}, ts(2))
        t.call("g4", "Agent", {"prompt": "p", "name": "w1", "model": ""}, ts(3))
        t.call("g5", "Agent", {"prompt": "p", "subagent_type": "fork"}, ts(4))
        code, rep, err = self.scan(t.write(self.proj / "a.jsonl"))
        missing = self.agent(rep, "main")["agent_calls_without_model"]
        self.assertEqual([m["tool_use_id"] for m in missing], ["g2", "g3", "g4", "g5"])
        self.assertEqual(missing[0]["subagent_type"], "general-purpose")
        self.assertEqual(missing[2]["name"], "w1")
        self.assertEqual(self.agent(rep, "main")["agent_calls"], 5)
        self.assertEqual(rep["totals"]["agent_calls_without_model"], 4)

    # -- Bash repeated five or more times within 30 minutes

    def test_bash_repeats_within_thirty_minutes(self):
        t = Transcript()
        for i, m in enumerate((0, 7, 14, 21, 29)):  # five within 29 minutes
            t.ok("p%d" % i, "Bash", {"command": "squeue -u me"}, ts(m))
        for i, m in enumerate((0, 10, 20, 31, 41)):  # never five within 30 minutes
            t.ok("q%d" % i, "Bash", {"command": "sacct -j 1"}, ts(m))
        for i, m in enumerate((0, 40, 41, 42, 43, 44)):  # six in total, five in the best window
            t.ok("r%d" % i, "Bash", {"command": "  tail -n 5 log  "}, ts(m))
        for i, m in enumerate((0, 1, 2, 3, 4)):  # five Read calls are not Bash
            t.ok("s%d" % i, "Read", {"file_path": "/x"}, ts(m))
        code, rep, err = self.scan(t.write(self.proj / "a.jsonl"))
        reps = {r["command"]: r for r in self.agent(rep, "main")["bash_repeats"]}
        self.assertEqual(sorted(reps), ["squeue -u me", "tail -n 5 log"])
        self.assertEqual((reps["squeue -u me"]["count"], reps["squeue -u me"]["total"]), (5, 5))
        self.assertEqual((reps["tail -n 5 log"]["count"], reps["tail -n 5 log"]["total"]), (5, 6))
        self.assertEqual(rep["rules"]["bash_window_minutes"], 30)

    def test_repeated_command_text_is_redacted(self):
        token = fake_token()
        t = Transcript()
        for i in range(5):
            t.ok("p%d" % i, "Bash", {"command": "curl -H 'x: %s' https://h" % token}, ts(i))
        for i in range(3):
            t.fail("f%d" % i, "Bash", {"command": "echo %s" % token}, ts(10 + i))
        code, rep, err = self.scan(t.write(self.proj / "a.jsonl"))
        text = json.dumps(rep)
        self.assertNotIn(token, text)
        self.assertIn("[redacted", text)

    # -- permission denials

    def test_permission_denials(self):
        t = Transcript()
        t.call("d1", "Bash", {"command": "rm -rf x"}, ts(0)).result("d1", True, ts(0), denial="automode-blocked")
        t.call("d2", "Agent", {"prompt": "p"}, ts(1)).result("d2", True, ts(1), decision="reject")
        t.call("d3", "Bash", {"command": "ls"}, ts(2)).result("d3", False, ts(2), decision="accept")
        code, rep, err = self.scan(t.write(self.proj / "a.jsonl"))
        denials = self.agent(rep, "main")["denials"]
        self.assertEqual([(d["tool_use_id"], d["tool"], d["kind"]) for d in denials],
                         [("d1", "Bash", "automode-blocked"), ("d2", "Agent", "reject:config")])
        self.assertEqual(rep["totals"]["denials"], 2)

    # -- Codex rollouts

    def test_codex_compacted_counts_and_spawns_without_model(self):
        sid = "01a17906-30b0-7902-90e7-9d4df093685a"
        usage = {"usage": {"input_tokens": 176995, "output_tokens": 68}, "thread_token_usage": {"input_tokens": 7}}
        recs = [
            cx("session_meta", {"id": sid, "session_id": sid, "parent_thread_id": None, "cwd": "/abs",
                                "cli_version": "0.166.0"}, "2026-10-26T15:23:31.001Z"),
            cx("turn_context", {"model": "gpt-6.1-sol", "cwd": "/abs"}, "2026-10-26T15:23:32.001Z"),
            cx("response_item", {"type": "function_call", "name": "spawn_agent", "call_id": "c1", "arguments":
                                 json.dumps({"agent_type": "worker", "message": "m", "model": "gpt-6.1-sol",
                                             "task_name": "t", "fork_turns": 0})}, "2026-10-26T15:30:00.000Z"),
            cx("response_item", {"type": "function_call", "name": "spawn_agent", "call_id": "c2", "arguments":
                                 json.dumps({"agent_type": "worker", "message": "m", "task_name": "t"})},
               "2026-10-26T15:31:00.000Z"),
            cx("response_item", {"type": "function_call", "name": "exec", "call_id": "c3", "arguments": "{}"},
               "2026-10-26T15:31:30.000Z"),
            cx("compacted", {"window_number": 1, "latest_token_usage_record": usage, "message": "summary"},
               "2026-10-26T16:00:00.000Z"),
            cx("compacted", {"window_number": 2, "latest_token_usage_record": {}, "message": "summary"},
               "2026-10-26T17:00:00.000Z"),
            cx("event_msg", {"type": "token_count", "info": {}}, "2026-10-26T17:00:01.000Z"),
        ]
        path = codex_rollout(Path(self.tmp) / "codex" / "2026" / "10" / "26" / ("rollout-x-%s.jsonl" % sid), recs)
        code, rep, err = self.scan(path)
        self.assertEqual(code, 0)
        self.assertEqual(rep["files"][0]["format"], "codex")
        a = self.agent(rep, "main", tool="codex")
        self.assertEqual(a["session_id"], sid)
        self.assertEqual(a["compacted"], 2)
        self.assertEqual([(c["window_number"], c["last_input_tokens"]) for c in a["compactions"]],
                         [(1, 176995), (2, None)])
        self.assertEqual(a["spawn_calls"], 2)
        self.assertEqual([s["call_id"] for s in a["agent_calls_without_model"]], ["c2"])
        self.assertEqual(rep["totals"]["codex_compacted"], 2)
        self.assertEqual(rep["totals"]["agent_calls_without_model"], 1)

    def test_codex_subagent_rollout_is_labelled_by_thread(self):
        recs = [cx("session_meta", {"id": "child-thread", "session_id": "parent-sess",
                                    "parent_thread_id": "parent-thread"}, "2026-10-26T15:23:31.001Z"),
                cx("compacted", {"window_number": 1}, "2026-10-26T16:00:00.000Z")]
        path = codex_rollout(Path(self.tmp) / "rollout-y.jsonl", recs)
        code, rep, err = self.scan(path)
        a = rep["agents"][0]
        self.assertEqual((a["agent"], a["parent_thread_id"], a["compacted"]), ("child-thread", "parent-thread", 1))
        self.assertEqual(rep["totals"]["main_compactions"], 0)

    # -- comparison with state.json

    def test_state_comparison(self):
        mpath, spath = self.main_with_subagent()
        st = Path(self.tmp) / "state.json"
        st.write_text(json.dumps({"schema": 1, "direction": "pilot-hooks", "sessions": {
            TAG: {"tool": "claude", "session_id": SID, "compactions": 1},
            "claude-99999999": {"tool": "claude", "session_id": "99999999-x", "compactions": 2}}}))
        before = st.stat().st_mtime
        code, rep, err = self.scan(mpath, "--state", st)
        cmp = rep["state"][str(st)]
        self.assertEqual(cmp[TAG], {"state": 1, "transcript": 1, "match": True})
        self.assertEqual(cmp["claude-99999999"], {"state": 2, "transcript": None, "match": None})
        self.assertEqual(st.stat().st_mtime, before)
        st.write_text(json.dumps({"schema": 1, "sessions": {TAG: {"tool": "claude", "session_id": SID,
                                                                   "compactions": 3}}}))
        code, rep, err = self.scan(mpath, "--state", st)
        self.assertEqual(rep["state"][str(st)][TAG]["match"], False)

    # -- robustness

    def test_unparsable_lines_and_timestamps(self):
        t = Transcript().ok("t1", "Bash", {"command": "ls"}, "2026-10-31T16:00:00Z")
        t.ok("t2", "Bash", {"command": "ls"}, "2026-10-31T16:00:00.12345Z")
        t.ok("t3", "Bash", {"command": "ls"}, "not a time")
        code, rep, err = self.scan(t.write(self.proj / "a.jsonl", garbage=2))
        self.assertEqual(rep["files"][0]["unparsable"], 2)
        self.assertEqual(self.agent(rep, "main")["tool_calls"], 3)

    def test_parse_time_accepts_z_and_any_fraction(self):
        from research_session import audit
        a = audit.parse_time("2026-10-31T16:00:00Z")
        self.assertAlmostEqual(audit.parse_time("2026-10-31T16:00:00.12345Z") - a, 0.12345, places=5)
        self.assertAlmostEqual(audit.parse_time("2026-10-31T16:00:00.1Z") - a, 0.1, places=5)
        self.assertEqual(audit.parse_time("2026-10-31T12:00:00-04:00"), a)
        self.assertIsNone(audit.parse_time("not a time"))
        self.assertIsNone(audit.parse_time(None))

    def test_missing_path_exits_two_and_reports(self):
        code, rep, err = self.scan(Path(self.tmp) / "nope.jsonl")
        self.assertEqual(code, 2)
        self.assertEqual(len(rep["errors"]), 1)

    def test_scan_is_read_only(self):
        mpath, spath = self.main_with_subagent()
        def listing():
            out = []
            for d, _, files in os.walk(self.tmp):
                for f in files:
                    p = os.path.join(d, f)
                    out.append((p, os.stat(p).st_mtime))
            return sorted(out)
        before = listing()
        self.scan(mpath)
        self.assertEqual(listing(), before)

    def test_help_lists_audit_scan(self):
        code, out, err = self.run_cli_help()
        self.assertIn("audit-scan", out)

    def run_cli_help(self):
        import contextlib
        import io
        from research_session import cli
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                cli.main(["--help"])
            except SystemExit as exc:
                return exc.code, buf.getvalue(), ""
        return 0, buf.getvalue(), ""


if __name__ == "__main__":
    unittest.main()
