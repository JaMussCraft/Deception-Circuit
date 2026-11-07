"""The PreToolUse gate: one test per row of spec 5.2, the extra cases of ticket 02, and the R5 fixtures.

The PreToolUse inputs in ``fixtures/gate/`` follow the documented hook input shape (lane 2 section 1); they are not
live recordings. Ticket 06 records real inputs.
"""

import json
import os
import unittest
from pathlib import Path

from _rs_testlib import FIXTURES, RSTestCase, fake_token

from research_session import gate, lint, oauth_refresh, paths, state, usage

FIXTURE_SID = "5f0c1d2e-7a8b-4c9d-8e1f-2a3b4c5d6e7f"
NEXT_ACTION_WORDS = ("run", "ask", "send", "use", "fix", "retry", "end the turn", "continue", "rewrite")


def reading(five=9, seven=11, fable=17, known=True, error=None, refresh_error=None, age=60):
    r = usage.empty_reading("claude", "/u/swong2/.claude/usage.json")
    if known:
        r.update(known=True, fresh_main=True, fresh_fable=True, five_hour=five, seven_day=seven, fable=fable,
                 h=five, w=max(seven, fable), age_main=age, age_fable=age, fable_gap=fable - seven)
    else:
        r.update(error=error or "stale: timestamp 1800 s old", refresh_attempted=True, refresh="failed",
                 refresh_error=refresh_error, age_main=age, age_fable=age)
    return r


class GateCase(RSTestCase):
    def setUp(self):
        super().setUp()
        self.wt = self.DC / ".claude" / "worktrees" / "demo-wt"
        (self.wt / "docs" / "research" / "demo").mkdir(parents=True)

    def inp(self, tool_name, tool_input=None, agent_id=None, cwd=None):
        h = {"session_id": FIXTURE_SID, "cwd": str(cwd or self.wt), "hook_event_name": "PreToolUse",
             "tool_name": tool_name, "tool_input": tool_input or {}}
        if agent_id:
            h.update(agent_id=agent_id, agent_type="ticket-implementer")
        return h

    def agent(self, **kw):
        return self.inp("Agent", {"description": "x", "prompt": "y", "subagent_type": "ticket-implementer"}, **kw)

    def bash(self, command, **kw):
        return self.inp("Bash", {"command": command}, **kw)

    def msg(self, text, to="impl-03", **kw):
        return self.inp("SendMessage", {"to": to, "message": text, "summary": "s"}, **kw)

    def write(self, path, content="A plain sentence.", tool="Write"):
        if tool == "Write":
            return self.inp("Write", {"file_path": str(path), "content": content})
        return self.inp("Edit", {"file_path": str(path), "old_string": "a", "new_string": content})

    def sess(self, **kw):
        kw.setdefault("sid", FIXTURE_SID)
        kw.setdefault("cwd", str(self.wt))
        return self.make_session(**kw)

    def decide(self, hook, session, r=None, tool="claude"):
        return gate.decide(hook, session, r if r is not None else reading(), self.cfg, tool=tool, now=self.now)

    def assertDenied(self, d, rule=None):
        self.assertFalse(d.allow, d)
        if rule:
            self.assertEqual(d.rule, rule)
        self.assertLessEqual(len(d.reason), gate.MAX_REASON)

    def assertAllowed(self, d):
        self.assertTrue(d.allow, d)


class DecisionTableTests(GateCase):
    # Row 1: self-ack guard, Bash.
    def test_row1_self_ack_guard_bash(self):
        s = self.sess()
        for cmd in ("research-session usage-ack", "/u/swong2/.local/bin/research-session set-cadence 40",
                    "cat /u/swong2/.claude/research-session/sessions/claude-x.json",
                    "touch /u/swong2/.claude/research-session/DISABLED",
                    "rm " + self.cfg.disabled_path,
                    "python3 -c 'print(1)' # usage-ack"):
            self.assertDenied(self.decide(self.bash(cmd), s), "self-ack")

    # Row 1: self-ack guard, Write and Edit.
    def test_row1_self_ack_guard_write_and_edit(self):
        frozen = self.sess(registered=True, freeze=(1, "recorded"))
        for s in (frozen, self.sess(sid="other-session")):
            for tool in ("Write", "Edit"):
                d = self.decide(self.write(Path(self.cfg.state_root) / "sessions" / "x.json", tool=tool), s)
                self.assertDenied(d, "self-ack")
                d = self.decide(self.write(paths.DEFAULT_STATE_ROOT + "/DISABLED", tool=tool), s)
                self.assertDenied(d, "self-ack")
                for name in ("state.json", "worklog.json"):
                    d = self.decide(self.write(self.wt / "docs" / "research" / "demo" / name, "{}", tool=tool), s)
                    self.assertDenied(d, "state-file")
                    d = self.decide(self.write(self.wt / "docs" / "research" / "_templates" / name, "{}", tool), s)
                    self.assertAllowed(d)
                d = self.decide(self.write(self.wt / "docs" / "research" / "demo" / "notes.json", "{}", tool), s)
                self.assertAllowed(d)
                d = self.decide(self.write(self.wt / "outputs" / "run" / "state.json", "{}", tool), s)
                self.assertAllowed(d)

    def test_row1_relative_write_path_resolves_against_cwd(self):
        s = self.sess()
        hook = self.inp("Write", {"file_path": "docs/research/demo/state.json", "content": "{}"})
        self.assertDenied(self.decide(hook, s), "state-file")

    # R37: read-only RS subcommands may name a direction file.
    def test_r37_bash_direction_files(self):
        s = self.sess()
        p = "docs/research/demo/state.json"
        allowed = ["research-session validate " + p,
                   "/u/swong2/.local/bin/research-session status " + p,
                   "/sw/external/python/anaconda3/bin/python3.9 -B /x/research_session/cli.py lint " + p,
                   "research-session findings-check docs/research/demo/worklog.json",
                   "cp docs/research/_templates/state.json /tmp/copy.json",
                   "ls outputs/run/state.json /tmp/state.json"]
        denied = ["research-session validate %s > %s" % (p, p),
                  "research-session validate %s 2>/dev/null" % p,
                  "research-session render " + p,
                  "research-session worklog-append docs/research/demo --kind entry; cat " + p,
                  "cat " + p, "rm docs/research/demo/worklog.json",
                  "echo '{}' > docs/research/demo/state.json",
                  "sed -i s/a/b/ $DIR/state.json"]
        for cmd in allowed:
            self.assertAllowed(self.decide(self.bash(cmd), s))
        for cmd in denied:
            self.assertDenied(self.decide(self.bash(cmd), s), "state-file")
        inside = self.wt / "docs" / "research" / "demo"
        self.assertDenied(self.decide(self.bash("rm state.json", cwd=inside), s), "state-file")
        self.assertAllowed(self.decide(self.bash("research-session validate state.json", cwd=inside), s))

    # Row 2: cap pause on five-hour and on weekly.
    def test_row2_cap_pause_five_hour(self):
        s = self.sess(registered=True)
        r = reading(five=85)
        self.assertDenied(self.decide(self.agent(), s, r), "cap")
        self.assertDenied(self.decide(self.bash("sbatch job.slurm"), s, r), "cap")
        self.assertAllowed(self.decide(self.bash("squeue -u swong2"), s, r))
        self.assertAllowed(self.decide(self.msg("status?"), s, r))
        self.assertIn("five-hour 85%", self.decide(self.agent(), s, r).reason)

    def test_row2_r40_absent_five_hour_is_not_applicable(self):
        s = self.sess(registered=True)
        r = reading(five=None, seven=40, fable=79)
        r["five_hour_missing"] = True
        self.assertAllowed(self.decide(self.agent(), s, r))
        self.assertAllowed(self.decide(self.bash("sbatch job.slurm"), s, r))
        r = reading(five=None, seven=40, fable=80)
        r["five_hour_missing"] = True
        d = self.decide(self.agent(), s, r)
        self.assertDenied(d, "cap")
        self.assertIn("five-hour not applicable", d.reason)

    def test_row2_r40_end_to_end_with_a_fresh_file_without_five_hour(self):
        self.sess(registered=True, w_last=19)
        self.write_usage(seven=15, fable=19, drop=("five_hour",))
        d = gate.evaluate(self.agent(), cfg=self.cfg, now=self.now)
        self.assertAllowed(d)
        self.assertEqual(self.http_calls, [])
        self.assertIsNone(self.session(FIXTURE_SID)["usage"]["last_reading"]["five_hour"])

    def test_row2_cap_pause_weekly(self):
        s = self.sess()
        for r in (reading(seven=80, fable=70), reading(seven=40, fable=81)):
            d = self.decide(self.agent(), s, r)
            self.assertDenied(d, "cap")
            self.assertIn("pause lifts", d.reason)

    # Row 3: unknown reading.
    def test_row3_unknown_reading(self):
        s = self.sess()
        r = reading(known=False, refresh_error="http 500", age=1800)
        d = self.decide(self.agent(), s, r)
        self.assertDenied(d, "unknown")
        for part in ("usage.json", "30 min old", "http 500", "`! research-session usage-ack --stale-ok 30`"):
            self.assertIn(part, d.reason)
        self.assertDenied(self.decide(self.bash("sbatch x.slurm"), s, r), "unknown")
        self.assertAllowed(self.decide(self.bash("ls"), s, r))

    # Row 4: unregistered session.
    def test_row4_unregistered_session_skips_freeze(self):
        s = self.sess(points=100, cadence=16)
        s["usage"]["freeze"] = {"checkpoint": 6, "stage": "recorded"}
        self.assertAllowed(self.decide(self.agent(), s))
        self.assertAllowed(self.decide(self.msg("go on"), s))
        self.assertEqual(self.decide(self.agent(), s).rule, "unregistered")

    # Row 5: freeze crossed.
    def test_row5_freeze_crossed(self):
        s = self.sess(registered=True, freeze=(1, "crossed"), points=16)
        d = self.decide(self.agent(), s)
        self.assertDenied(d, "freeze-crossed")
        self.assertIn("--kind checkpoint --checkpoint 1", d.reason)
        self.assertDenied(self.decide(self.bash("sbatch a.slurm"), s), "freeze-crossed")
        self.assertAllowed(self.decide(self.msg("Please keep going."), s))

    # Row 6: freeze recorded.
    def test_row6_freeze_recorded_normal_message_denied(self):
        s = self.sess(registered=True, freeze=(1, "recorded"), points=16)
        d = self.decide(self.msg("Please start the next ticket."), s)
        self.assertDenied(d, "freeze-message")
        self.assertDenied(self.decide(self.inp("SendMessage", {"to": "x", "message": {"type": "shutdown_request"}}),
                                      s), "freeze-message")
        self.assertDenied(self.decide(self.agent(), s), "freeze-recorded")

    def test_row6_freeze_recorded_hold_message_allowed(self):
        s = self.sess(registered=True, freeze=(1, "recorded"))
        self.assertAllowed(self.decide(self.msg("HOLD: finish your atomic step and write the hand-back."), s))
        self.assertAllowed(self.decide(self.msg("  HOLD now"), s))

    def test_row6_freeze_recorded_message_to_main_allowed(self):
        s = self.sess(registered=True, freeze=(1, "recorded"))
        self.assertAllowed(self.decide(self.msg("Checkpoint 1 is written.", to="main"), s))

    def test_row6_freeze_recorded_subagent_message_allowed(self):
        s = self.sess(registered=True, freeze=(1, "recorded"))
        self.assertAllowed(self.decide(self.msg("Done with step 2.", to="team-lead", agent_id="a1b2c3"), s))

    def test_row6_codex_freeze_denies_spawns_and_sbatch_only(self):
        s = self.sess(tool="codex", registered=True, freeze=(1, "recorded"))
        self.assertAllowed(self.decide(self.msg("continue"), s, tool="codex"))
        self.assertDenied(self.decide(self.inp("spawn_agent", {"message": "x"}), s, tool="codex"), "freeze-recorded")

    # Row 7: allow.
    def test_row7_allow(self):
        s = self.sess(registered=True, points=10)
        for hook in (self.agent(), self.bash("sbatch a.slurm"), self.msg("hi"), self.bash("ls")):
            d = self.decide(hook, s)
            self.assertAllowed(d)
            self.assertIsNone(gate.hook_output(d))

    def test_acked_freeze_allows(self):
        s = self.sess(registered=True, freeze=(1, "recorded"), acked_through=1)
        self.assertAllowed(self.decide(self.agent(), s))


class ExtraCaseTests(GateCase):
    def test_stale_ok_window_allows_spawns(self):
        s = self.sess()
        s["usage"]["stale_ok_until"] = paths.iso(self.now + 600)
        r = reading(known=False, refresh_error="http 500")
        self.assertAllowed(self.decide(self.agent(), s, r))
        self.assertAllowed(self.decide(self.bash("sbatch a.slurm"), s, r))
        s["usage"]["stale_ok_until"] = paths.iso(self.now - 1)
        self.assertDenied(self.decide(self.agent(), s, r), "unknown")

    def test_kill_switch_allows_everything(self):
        paths.ensure_state_root(self.cfg)
        Path(self.cfg.disabled_path).write_text("")
        self.write_usage(five=95)
        d = gate.evaluate(self.agent(), cfg=self.cfg, now=self.now)
        self.assertAllowed(d)
        self.assertEqual(d.rule, "disabled")
        self.assertFalse(os.path.exists(self.cfg.session_file("claude", FIXTURE_SID)))

    def test_cwd_outside_alignment_allows_everything(self):
        self.write_usage(five=95)
        d = gate.evaluate(self.agent(cwd="/tmp"), cfg=self.cfg, now=self.now)
        self.assertAllowed(d)
        self.assertEqual(d.rule, "outside-alignment")

    def test_bash_without_sbatch_allowed_during_freeze(self):
        s = self.sess(registered=True, freeze=(2, "recorded"))
        for cmd in ("squeue -u swong2", "python3 analyze.py", "echo sbatchless", "grep -r 'job' logs"):
            self.assertAllowed(self.decide(self.bash(cmd), s))

    def test_exception_inside_decision_fails_closed_for_spend_only(self):
        def boom(*a, **k):
            raise RuntimeError("decision exploded")
        for hook, allowed in ((self.agent(), False), (self.bash("sbatch a.slurm"), False),
                              (self.bash("ls"), True), (self.msg("hi"), True),
                              (self.write(self.wt / "x.md"), True)):
            d = gate.safe_evaluate(hook, cfg=self.cfg, now=self.now, evaluator=boom)
            self.assertEqual(d.allow, allowed, hook["tool_name"])
            if not allowed:
                self.assertEqual(d.rule, "gate-error")
                self.assertIn("Gate error (RuntimeError)", d.reason)
                self.assertNotIn("decision exploded", d.reason)

    def test_corrupt_session_file_fails_closed_through_safe_evaluate(self):
        self.write_usage()
        paths.ensure_state_root(self.cfg)
        Path(self.cfg.session_file("claude", FIXTURE_SID)).write_text("{not json")
        self.assertDenied(gate.safe_evaluate(self.agent(), cfg=self.cfg, now=self.now), "gate-error")
        self.assertAllowed(gate.safe_evaluate(self.bash("ls"), cfg=self.cfg, now=self.now))

    def test_hook_output_shape(self):
        d = gate.deny("cap", "Usage cap pause: end the turn.")
        self.assertEqual(gate.hook_output(d), {"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": "Usage cap pause: end the turn."}})


class WriteLintTests(GateCase):
    def test_glued_worklog_paragraph_is_denied(self):
        glued = (FIXTURES / "lint" / "glued_resume_excerpt.md").read_text()
        d = self.decide(self.write(self.wt / "docs" / "research" / "demo" / "WORKLOG.md", glued), self.sess())
        self.assertDenied(d, "lint")
        self.assertIn("line ", d.reason)
        self.assertIn("Rewrite in full sentences", d.reason)

    def test_glued_edit_new_string_is_denied(self):
        line = (FIXTURES / "lint" / "glued_memory_line29.md").read_text()
        d = self.decide(self.write(self.wt / "docs" / "research" / "demo" / "README.md", line, tool="Edit"),
                        self.sess())
        self.assertDenied(d, "lint")

    def test_planted_fake_token_is_denied_without_echo(self):
        token = fake_token()
        for target in (self.A / ".agents" / "helper.py", self.wt / "docs" / "research" / "demo" / "WORKLOG.md"):
            d = self.decide(self.write(target, "key = '%s'\n" % token), self.sess())
            self.assertDenied(d, "lint")
            self.assertIn("secret", d.reason)
            self.assertNotIn(token, d.reason)
            self.assertNotIn("PLANTED", d.reason)

    def test_clean_write_is_allowed(self):
        text = "Swapping five shared heads flips the model from hiding to disclosing in 23 of 48 stories.\n"
        self.assertAllowed(self.decide(self.write(self.wt / "docs" / "research" / "demo" / "WORKLOG.md", text),
                                       self.sess()))

    def test_out_of_scope_markdown_gets_only_the_secret_scan(self):
        glued = (FIXTURES / "lint" / "glued_resume_excerpt.md").read_text()
        target = self.A / "project_context" / "notes.md"
        self.assertTrue(lint.lint_glue(glued))
        self.assertAllowed(self.decide(self.write(target, glued), self.sess()))
        self.assertDenied(self.decide(self.write(target, glued + "\n" + fake_token()), self.sess()), "lint")

    def test_write_outside_alignment_is_not_scanned(self):
        d = self.decide(self.write("/tmp/elsewhere.md", fake_token()), self.sess())
        self.assertAllowed(d)


class ReasonTests(GateCase):
    def test_every_reason_is_short_and_names_the_next_action(self):
        s = self.sess(registered=True, freeze=(3, "recorded"), points=48)
        many = [lint.Finding(i, "long-token", "x" * 100) for i in range(1, 60)]

        class AVeryLongExceptionClassNameThatKeepsGoingAndGoingAndGoingForeverAndEver(Exception):
            pass
        reasons = [
            gate.REASON_SELF_ACK,
            gate.reason_state_file("/very/long/" + "segment/" * 80 + "state.json"),
            gate.reason_lint("/x/" + "y" * 300 + ".md", many),
            gate.reason_cap(reading(five=99, seven=99, fable=99)),
            gate.reason_unknown(reading(known=False, refresh_error="e" * 500, age=10 ** 7)),
            gate.reason_unknown(dict(usage.empty_reading("codex", "/bin/codex-usage"), error="x" * 500)),
            gate.reason_freeze(s, recorded=False),
            gate.reason_freeze(s, recorded=True),
            gate.reason_message(s),
            gate.reason_gate_error(AVeryLongExceptionClassNameThatKeepsGoingAndGoingAndGoingForeverAndEver()),
        ]
        for text in reasons:
            clipped = gate.deny("x", text).reason
            self.assertLessEqual(len(clipped), gate.MAX_REASON, text)
            self.assertTrue(any(w in clipped.lower() for w in NEXT_ACTION_WORDS), clipped)
            self.assertFalse(clipped.endswith("..."), clipped)


class UnregisteredFixtureTests(GateCase):
    """R5 and spec 5.2 step 4, through ``evaluate`` with recorded-shape inputs and a session without ``register``."""

    def fixture(self, name):
        text = (FIXTURES / "gate" / name).read_text().replace("{A}", str(self.A))
        return json.loads(text)

    def forty_points(self):
        # Segment baseline 10, last 50: 40 session points, cadence 16, no register entry.
        return self.sess(points=40, cadence=16, w_last=50)

    def run_all(self):
        return {name: gate.evaluate(self.fixture(name), cfg=self.cfg, now=self.now)
                for name in ("pretooluse_agent.json", "pretooluse_bash_sbatch.json",
                             "pretooluse_sendmessage_orchestrator.json")}

    def test_a_forty_points_fresh_under_cap_all_allowed_no_freeze(self):
        self.forty_points()
        self.write_usage(five=20, seven=45, fable=50)
        for name, d in self.run_all().items():
            self.assertAllowed(d)
            self.assertEqual(d.rule, "unregistered", name)
        s = self.session(FIXTURE_SID)
        self.assertIsNone(s["register"])
        self.assertEqual(s["usage"]["session_points"], 40)
        self.assertIsNone(s["usage"]["freeze"])
        self.assertEqual(s["checkpoints"], [])

    def test_b_at_w_81_cap_pause_denies_spawns(self):
        self.forty_points()
        self.write_usage(five=20, seven=60, fable=81)
        out = self.run_all()
        self.assertDenied(out["pretooluse_agent.json"], "cap")
        self.assertDenied(out["pretooluse_bash_sbatch.json"], "cap")
        self.assertAllowed(out["pretooluse_sendmessage_orchestrator.json"])
        self.assertIsNone(self.session(FIXTURE_SID)["usage"]["freeze"])

    def test_c_stale_reading_and_failed_refresh_denies_agent_as_unknown(self):
        self.forty_points()
        self.write_usage(age=3600)
        self.token_reader = lambda path: (fake_token(), self.now + 3600)

        def http(url, token, timeout):
            raise oauth_refresh.FetchError("http 502")
        self.http = http
        d = gate.evaluate(self.fixture("pretooluse_agent.json"), cfg=self.cfg, now=self.now)
        self.assertDenied(d, "unknown")
        self.assertIn("http 502", d.reason)
        self.assertEqual(len(self.http_calls), 1)

    def test_d_cwd_matching_a_direction_worktree_is_still_unregistered(self):
        self.write_directions([{"id": "demo", "worktree": str(self.wt), "status": "active"}])
        self.forty_points()
        self.write_usage(five=20, seven=45, fable=70)  # 60 points, past checkpoints 1-3 if it were registered
        for d in self.run_all().values():
            self.assertAllowed(d)
            self.assertEqual(d.rule, "unregistered")
        s = self.session(FIXTURE_SID)
        self.assertEqual(state.resolve_direction(self.cfg, s), ("demo", "cwd"))
        self.assertIsNone(s["usage"]["freeze"])
        self.assertEqual(s["checkpoints"], [])

    def test_e_register_at_forty_crosses_checkpoint_one_only_at_56(self):
        self.forty_points()
        self.write_usage(five=20, seven=45, fable=50)
        code, out, err = self.run_cli("register", "demo", "--session", FIXTURE_SID)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.session(FIXTURE_SID)["usage"]["points_at_register"], 40)
        self.assertAllowed(gate.evaluate(self.fixture("pretooluse_agent.json"), cfg=self.cfg, now=self.now))
        self.write_usage(five=20, seven=45, fable=65)  # 55 points
        self.assertAllowed(gate.evaluate(self.fixture("pretooluse_agent.json"), cfg=self.cfg, now=self.now))
        self.assertIsNone(self.session(FIXTURE_SID)["usage"]["freeze"])
        self.write_usage(five=20, seven=45, fable=66)  # 56 points
        d = gate.evaluate(self.fixture("pretooluse_agent.json"), cfg=self.cfg, now=self.now)
        self.assertDenied(d, "freeze-crossed")
        s = self.session(FIXTURE_SID)
        self.assertEqual(s["usage"]["freeze"]["checkpoint"], 1)
        self.assertEqual([c["n"] for c in s["checkpoints"]], [1])
        self.assertEqual(s["checkpoints"][0]["fable"], 66)
        mirrored = json.loads((self.wt / "docs" / "research" / "demo" / "state.json").read_text())
        self.assertEqual(mirrored["sessions"]["claude-5f0c1d2e"]["usage"]["freeze"]["stage"], "crossed")
        self.assertAllowed(gate.evaluate(self.fixture("pretooluse_sendmessage_orchestrator.json"),
                                         cfg=self.cfg, now=self.now))

    def test_file_guards_still_apply_in_unregistered_sessions(self):
        self.forty_points()
        self.write_usage()
        state_json = self.wt / "docs" / "research" / "demo" / "state.json"
        d = gate.evaluate(self.write(state_json, "{}"), cfg=self.cfg, now=self.now)
        self.assertDenied(d, "state-file")
        d = gate.evaluate(self.bash("research-session usage-ack"), cfg=self.cfg, now=self.now)
        self.assertDenied(d, "self-ack")
        glued = (FIXTURES / "lint" / "glued_resume_excerpt.md").read_text()
        d = gate.evaluate(self.write(self.wt / "docs" / "research" / "demo" / "WORKLOG.md", glued),
                          cfg=self.cfg, now=self.now)
        self.assertDenied(d, "lint")


if __name__ == "__main__":
    unittest.main()
