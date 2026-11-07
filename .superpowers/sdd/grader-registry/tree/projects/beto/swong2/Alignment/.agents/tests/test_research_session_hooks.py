"""Tests for the hook entry points (ticket 06, spec 5.1, H-a to H-j).

Each test feeds a recorded-shape input from ``fixtures/hooks/`` to ``hooks.run`` and asserts the exact stdout JSON
and the exit code. Claude inputs follow https://code.claude.com/docs/en/hooks; Codex inputs follow the generated
schemas linked from https://learn.chatgpt.com/docs/hooks. ``{A}`` is the temporary Alignment root, ``{STATE}`` the
temporary state root and ``{TOKEN}`` a synthetic token built at run time.
"""

import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _rs_testlib import RSTestCase, fake_token  # noqa: E402
from research_session import gate, hooks, paths, state  # noqa: E402

HOOK_FIX = Path(__file__).resolve().parent / "fixtures" / "hooks"
CLI = Path(__file__).resolve().parents[1] / "research_session" / "cli.py"
CSID = "c1a2b3c4-5d6e-4f70-8a9b-0c1d2e3f4a5b"
XSID = "019a3b4c-5d6e-7f80-9a1b-2c3d4e5f6a7b"
GLUED = ("Lead8unchanged CPUgeometrypreliminaryPASS heads24to27restoreblocked clause5influence "
         "queryside3sensitive factual2keyside sensitive.")
CLEAN = ("The gate denied one spawn at the cap, and the session waited for the reset. Nothing else changed in "
         "this step.")
READING = "Usage: five-hour not applicable, seven-day 15%, Fable 22%, weekly max 22%."
FABLE = "Fable is 7 points above all-models: delegate reading, analysis and review to Opus agents."
UNREGISTERED = ("Direction: none; not registered. This session gets only the cap and stale gates, no checkpoints. "
                "To get checkpoints, run `research-session register <slug>`.")
LINT_REASON = ("Write refused by the text lint (R30) for %s. Fix and retry: line 1 join: 5 letter-digit joins; "
               "Lead8unchanged CPUgeometrypreliminaryPASS heads24to27restoreblocked clause5influence queryside3se... "
               "Rewrite in full sentences with normal spacing; never paste secrets.")
FREEZE_HOLDS = ("Freeze holds; answer questions only. Checkpoint 1 waits for the user's `continue` or "
                "`! research-session usage-ack`; start no new work.")


def ctx(event, text):
    return {"hookSpecificOutput": {"additionalContext": text, "hookEventName": event}}


def deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


class HookCase(RSTestCase):
    def setUp(self):
        super(HookCase, self).setUp()
        self.demo = self.DC / "docs" / "research" / "demo"
        self.demo.mkdir(parents=True)
        self.write_usage(seven=15, fable=22, drop=("five_hour",))

    def raw(self, name, cwd=None):
        text = (HOOK_FIX / (name + ".json")).read_text()
        text = text.replace("{A}", str(self.A)).replace("{STATE}", self.cfg.state_root)
        text = text.replace("{TOKEN}", fake_token())
        if cwd is not None:
            data = json.loads(text)
            data["cwd"] = cwd
            text = json.dumps(data)
        return text

    def data(self, name):
        return json.loads(self.raw(name))

    def run_hook(self, event, tool, name=None, raw=None, **overrides):
        if raw is None:
            data = self.data(name)
            data.update(overrides)
            raw = json.dumps(data)
        code, out = hooks.run(event, tool, raw, cfg=self.cfg, now=self.now)
        self.assertEqual(code, 0)
        return out

    def run_json(self, event, tool, name=None, **overrides):
        out = self.run_hook(event, tool, name, **overrides)
        self.assertTrue(out.endswith("\n"), out)
        return json.loads(out)

    def register(self, tool="claude", sid=CSID, freeze=None, points=0, acked_through=0):
        return self.make_session(sid=sid, tool=tool, cwd=str(self.DC), registered=True, slug="demo",
                                 freeze=freeze, points=points, acked_through=acked_through, w_last=22)


# ---------------------------------------------------------------------------------------------------------------
# H-a: SessionStart startup|resume


class SessionStartTests(HookCase):
    def test_unregistered_prints_register_line_and_gates(self):
        out = self.run_json("session-start", "claude", "claude_session_start_startup")
        self.assertEqual(out, ctx("SessionStart", "research-session: session claude-c1a2b3c4. %s %s %s"
                                  % (UNREGISTERED, READING, FABLE)))
        s = self.session(CSID)
        self.assertEqual(s["orchestrator_model"], "claude-fable-5-1")
        self.assertEqual(s["usage"]["segments"][0]["baseline"], 22)
        self.assertLessEqual(len(out["hookSpecificOutput"]["additionalContext"]), 600)

    def test_cwd_match_names_the_slug(self):
        self.write_directions([{"id": "demo", "title": "Demo", "status": "claimed", "summary": "x",
                                "claimed_by": "claude-c1a2b3c4", "claimed_at": None, "dir": "docs/research/demo",
                                "worktree": ".", "updated": "2026-10-31"}])
        text = self.run_json("session-start", "claude", "claude_session_start_startup")[
            "hookSpecificOutput"]["additionalContext"]
        self.assertIn("Direction: demo by cwd match, attribution only; not registered.", text)
        self.assertIn("only the cap and stale gates", text)
        self.assertIn("`research-session register demo`", text)

    def test_registered_prints_freeze_state_instead(self):
        self.register(freeze=(1, "crossed"))
        out = self.run_json("session-start", "claude", "claude_session_start_resume")
        expected = ("research-session: session claude-c1a2b3c4. Direction: demo, registered; <dir> is %s. Freeze: "
                    "checkpoint 1 crossed (+0 points since register); new agents and sbatch are held. Record it with "
                    "`research-session worklog-append <dir> --kind checkpoint --checkpoint 1`, send HOLD to workers "
                    "and end the turn. %s %s" % (self.demo, READING, FABLE))
        self.assertEqual(out, ctx("SessionStart", hooks.clip(expected, 600)))
        self.assertNotIn("register <slug>", expected)

    def test_registered_without_freeze(self):
        self.register()
        text = self.run_json("session-start", "claude", "claude_session_start_resume")[
            "hookSpecificOutput"]["additionalContext"]
        self.assertIn("Freeze: none. Next checkpoint 1 at +16 points since register (now +0).", text)

    def test_codex_startup_never_runs_codex_usage(self):
        calls = self.fake_codex_usage(0, {"status": "ok", "weekly": {"used_percent": 10}})
        out = self.run_json("session-start", "codex", "codex_session_start_startup")
        self.assertEqual(out, ctx("SessionStart", "research-session: session codex-019a3b4c. %s Usage: unknown (no "
                                  "recent Codex reading); the gate refreshes it before the next spawn." % UNREGISTERED))
        self.assertEqual(self.codex_calls(), 0)
        self.assertIsNotNone(calls)

    def test_clear_source_is_a_no_op(self):
        self.assertEqual(self.run_hook("session-start", "claude", "claude_session_start_clear"), "")
        self.assertIsNone(self.session(CSID))

    def test_startup_never_fetches_a_stale_reading(self):
        self.write_usage(seven=15, fable=22, age=3600, drop=("five_hour",))
        text = self.run_json("session-start", "claude", "claude_session_start_startup")[
            "hookSpecificOutput"]["additionalContext"]
        self.assertIn("Usage: unknown (stale:", text)
        self.assertEqual(self.token_calls, [])
        self.assertEqual(self.http_calls, [])


# ---------------------------------------------------------------------------------------------------------------
# H-b and H-c: compaction count and summary


class CompactionTests(HookCase):
    def test_compact_counts_exactly_once_per_call(self):
        out = self.run_json("session-start", "claude", "claude_session_start_compact")
        self.assertEqual(out, ctx("SessionStart", (
            "research-session: compaction #1 recorded for session claude-c1a2b3c4. No direction is registered, so "
            "there is no RESUME or WORKLOG to name. Re-read your notes and the latest hand-backs before acting; do "
            "not restart finished work.")))
        self.assertEqual(self.session(CSID)["compactions"], 1)
        self.run_hook("session-start", "claude", "claude_session_start_compact")
        s = self.session(CSID)
        self.assertEqual(s["compactions"], 2)
        self.assertEqual([e["n"] for e in s["compaction_log"]], [1, 2])

    def test_post_compact_never_counts_and_never_prints(self):
        self.assertEqual(self.run_hook("post-compact", "claude", "claude_post_compact_auto"), "")
        s = self.session(CSID)
        self.assertEqual(s["compactions"], 0)
        saved = Path(hooks.fallback_dir(self.cfg, "claude", CSID)) / "compaction-1.md"
        self.assertIn("ticket 06 hooks", saved.read_text())
        self.assertEqual(oct(saved.stat().st_mode & 0o777), oct(0o600))

    def _order(self, first, second):
        for event in (first, second):
            name = "claude_session_start_compact" if event == "session-start" else "claude_post_compact_auto"
            self.run_hook(event, "claude", name)
        return self.session(CSID)

    def test_both_orders_give_the_same_count_and_trigger(self):
        s1 = self._order("post-compact", "session-start")
        self.assertEqual(s1["compactions"], 1)
        self.assertEqual(s1["compaction_log"][0]["trigger"], "auto")
        os.remove(self.cfg.session_file("claude", CSID))
        for p in Path(hooks.fallback_dir(self.cfg, "claude", CSID)).iterdir():
            p.unlink()
        s2 = self._order("session-start", "post-compact")
        self.assertEqual(s2["compactions"], 1)
        self.assertEqual(s2["compaction_log"][0]["trigger"], "auto")
        self.assertTrue((Path(hooks.fallback_dir(self.cfg, "claude", CSID)) / "compaction-1.md").exists())

    def test_registered_compaction_names_resume_worklog_and_lint(self):
        self.register()
        (self.demo / "RESUME.md").write_text("# Resume\n\n" + GLUED + "\n")
        (self.demo / "WORKLOG.md").write_text("# Worklog\n\n" + CLEAN + "\n")
        text = self.run_json("session-start", "claude", "claude_session_start_compact")[
            "hookSpecificOutput"]["additionalContext"]
        self.assertIn("Write a 'Resumed after compaction #1' worklog entry; do not restart finished work.", text)
        self.assertIn("`research-session worklog-append <dir> --kind compaction`, where <dir> is %s." % self.demo, text)
        self.assertIn("<dir>/RESUME.md (lint: 1 failing unit, line 3 join:", text)
        self.assertIn("<dir>/WORKLOG.md (lint clean)", text)
        self.assertLessEqual(len(text), hooks.MAX_COMPACT)

    def test_registered_summary_saved_in_direction_and_redacted(self):
        self.register()
        self.run_hook("post-compact", "claude", "claude_post_compact_auto",
                      compact_summary="Summary with a key %s inside." % fake_token())
        text = (self.demo / "handbacks" / "compaction-1.md").read_text()
        self.assertNotIn(fake_token(), text)
        self.assertIn("[redacted anthropic-key]", text)

    def test_summary_files_are_never_overwritten(self):
        self.register()
        (self.demo / "handbacks").mkdir()
        (self.demo / "handbacks" / "compaction-1.md").write_text("older\n")
        self.run_hook("post-compact", "claude", "claude_post_compact_auto")
        self.assertEqual((self.demo / "handbacks" / "compaction-1.md").read_text(), "older\n")
        self.assertTrue((self.demo / "handbacks" / "compaction-1.2.md").exists())

    def test_subagent_and_codex_post_compact_are_ignored(self):
        self.assertEqual(self.run_hook("post-compact", "claude", "claude_post_compact_auto", agent_id="a1"), "")
        self.assertIsNone(self.session(CSID))
        self.assertEqual(self.run_hook("post-compact", "codex", "codex_session_start_compact",
                                       hook_event_name="PostCompact", trigger="auto"), "")

    def test_codex_compact_counts(self):
        out = self.run_json("session-start", "codex", "codex_session_start_compact")
        self.assertIn("compaction #1 recorded for session codex-019a3b4c", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.session(XSID, "codex")["compactions"], 1)


# ---------------------------------------------------------------------------------------------------------------
# H-d: PreToolUse


class PreToolUseTests(HookCase):
    def test_glued_worklog_write_denied_with_units(self):
        out = self.run_json("pre-tool-use", "claude", "claude_pretooluse_write_worklog_glued")
        self.assertEqual(out, deny(LINT_REASON % "WORKLOG.md"))

    def test_planted_token_edit_denied_without_echo(self):
        out = self.run_hook("pre-tool-use", "claude", "claude_pretooluse_edit_token")
        self.assertEqual(json.loads(out), deny(
            "Write refused by the text lint (R30) for notes.txt. Fix and retry: line 1 secret: anthropic-key match "
            "redacted Rewrite in full sentences with normal spacing; never paste secrets."))
        self.assertNotIn(fake_token(), out)

    def test_clean_write_allowed(self):
        self.assertEqual(self.run_hook("pre-tool-use", "claude", "claude_pretooluse_write_clean"), "")

    def test_state_and_worklog_json_denied_templates_allowed(self):
        for name, fname in (("claude_pretooluse_write_state_json", "state.json"),
                            ("claude_pretooluse_edit_worklog_json", "worklog.json")):
            out = self.run_json("pre-tool-use", "claude", name)
            reason = out["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertTrue(reason.startswith("Denied: "), reason)
            self.assertIn(fname + " is written only by research-session (spec 5.3).", reason)
        self.assertEqual(self.run_hook("pre-tool-use", "claude", "claude_pretooluse_write_templates_state"), "")

    def test_session_state_root_denied(self):
        out = self.run_json("pre-tool-use", "claude", "claude_pretooluse_write_session_root")
        self.assertEqual(out, deny(gate.REASON_SELF_ACK))

    def test_agent_allowed_unregistered_and_denied_when_frozen(self):
        self.assertEqual(self.run_hook("pre-tool-use", "claude", "claude_pretooluse_agent"), "")
        self.register(freeze=(1, "crossed"))
        out = self.run_json("pre-tool-use", "claude", "claude_pretooluse_agent")
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertTrue(out["hookSpecificOutput"]["permissionDecisionReason"].startswith("Checkpoint 1 crossed"))

    def test_recorded_freeze_denies_orchestrator_message(self):
        self.register(freeze=(1, "recorded"))
        out = self.run_json("pre-tool-use", "claude", "claude_pretooluse_sendmessage")
        self.assertEqual(out, deny(gate.reason_message(self.session(CSID))))

    def test_gate_error_denies_spawn_allows_write(self):
        with mock.patch.object(gate, "evaluate", side_effect=RuntimeError("boom")):
            out = self.run_json("pre-tool-use", "claude", "claude_pretooluse_agent")
            self.assertEqual(out, deny(gate.reason_gate_error(RuntimeError("boom"))))
            self.assertEqual(self.run_hook("pre-tool-use", "claude", "claude_pretooluse_write_clean"), "")

    def test_codex_spawn_denied_at_cap(self):
        self.fake_codex_usage(0, {"status": "ok", "weekly": {"used_percent": 85, "resets_at": 1793797200}})
        out = self.run_json("pre-tool-use", "codex", "codex_pretooluse_spawn_agent")
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertTrue(out["hookSpecificOutput"]["permissionDecisionReason"].startswith(
            "Usage cap pause: Codex weekly 85% (cap 80%)."))

    def test_codex_bash_sbatch_allowed_below_cap(self):
        self.fake_codex_usage(0, {"status": "ok", "weekly": {"used_percent": 20, "resets_at": 1793797200}})
        self.assertEqual(self.run_hook("pre-tool-use", "codex", "codex_pretooluse_bash_sbatch"), "")

    def test_codex_apply_patch(self):
        self.assertEqual(self.run_json("pre-tool-use", "codex", "codex_pretooluse_apply_patch_glued"),
                         deny(LINT_REASON % "README.md"))
        self.assertEqual(self.run_hook("pre-tool-use", "codex", "codex_pretooluse_apply_patch_clean"), "")
        out = self.run_json("pre-tool-use", "codex", "codex_pretooluse_apply_patch_state")
        self.assertEqual(out, deny(gate.reason_state_file("docs/research/demo/state.json")))
        tok = self.run_hook("pre-tool-use", "codex", "codex_pretooluse_apply_patch_token")
        self.assertIn("line 1 secret: anthropic-key match redacted", tok)
        self.assertNotIn(fake_token(), tok)

    def test_parse_patch(self):
        patch = ("*** Begin Patch\n*** Add File: a.md\n+one\n+two\n*** Update File: b.md\n*** Move to: c.md\n@@\n"
                 " ctx\n-old\n+new\n@@ def f\n+again\n*** Delete File: d.json\n*** End Patch\n")
        self.assertEqual(hooks.parse_patch(patch), [
            ("add", "a.md", None, "one\ntwo\n"),
            ("update", "b.md", "c.md", "new\n\nagain\n"),
            ("delete", "d.json", None, "")])

    def test_codex_patch_deleting_a_state_file_is_denied(self):
        raw = self.data("codex_pretooluse_apply_patch_state")
        raw["tool_input"]["command"] = "*** Begin Patch\n*** Delete File: docs/research/demo/worklog.json\n*** End Patch\n"
        out = json.loads(hooks.run("pre-tool-use", "codex", json.dumps(raw), cfg=self.cfg, now=self.now)[1])
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")


# ---------------------------------------------------------------------------------------------------------------
# H-e and H-f: PostToolUse


class PostToolUseTests(HookCase):
    def test_agent_context_uses_the_gate_reading(self):
        self.run_hook("pre-tool-use", "claude", "claude_pretooluse_agent")
        out = self.run_json("post-tool-use", "claude", "claude_posttooluse_agent")
        self.assertEqual(out, ctx("PostToolUse", "research-session after spawn: %s Not registered, so no "
                                  "checkpoints. %s" % (READING, FABLE)))

    def test_agent_context_registered(self):
        self.register()
        self.run_hook("pre-tool-use", "claude", "claude_pretooluse_agent")
        text = self.run_json("post-tool-use", "claude", "claude_posttooluse_agent")[
            "hookSpecificOutput"]["additionalContext"]
        self.assertIn("Session points +0 since register. Freeze: none. Next checkpoint 1 at +16 points", text)

    def test_agent_context_never_reads_usage(self):
        self.run_hook("pre-tool-use", "claude", "claude_pretooluse_agent")
        os.remove(self.cfg.usage_file)
        out = self.run_json("post-tool-use", "claude", "claude_posttooluse_agent")
        self.assertIn(READING, out["hookSpecificOutput"]["additionalContext"])

    def test_codex_agent_context(self):
        self.fake_codex_usage(0, {"status": "ok", "weekly": {"used_percent": 30, "resets_at": 1793797200}})
        self.run_hook("pre-tool-use", "codex", "codex_pretooluse_spawn_agent")
        out = self.run_json("post-tool-use", "codex", "codex_posttooluse_spawn_agent")
        self.assertEqual(out, ctx("PostToolUse", "research-session after spawn: Usage: Codex weekly 30%. Not "
                                  "registered, so no checkpoints."))

    def test_clean_edit_reports_problem_elsewhere_advice_only(self):
        (self.demo / "README.md").write_text("# Demo\n\n%s\n\n%s\n" % (CLEAN, GLUED))
        out = self.run_json("post-tool-use", "claude", "claude_posttooluse_edit")
        self.assertNotIn("decision", out)
        text = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        excerpt = " ".join(GLUED.split())[:97] + "..."
        self.assertEqual(out, ctx("PostToolUse", hooks.clip(
            "Lint advice (the write already happened and is not undone): problems outside the text you just wrote "
            "in README.md: line 5 join: 5 letter-digit joins; %s. Fix them with a follow-up edit, or through the RS "
            "command that owns the file." % excerpt)))
        self.assertNotIn("line 3", text)

    def test_edit_whose_own_text_is_the_only_problem_is_silent(self):
        (self.demo / "README.md").write_text("# Demo\n\n%s\n" % CLEAN)
        self.assertEqual(self.run_hook("post-tool-use", "claude", "claude_posttooluse_edit"), "")

    def test_write_is_silent(self):
        (self.demo / "README.md").write_text("# Demo\n\n%s\n" % GLUED)
        self.assertEqual(self.run_hook("post-tool-use", "claude", "claude_posttooluse_write"), "")

    def test_codex_apply_patch_advice(self):
        (self.demo / "README.md").write_text("# Demo\n\n%s\n\n%s\n" % (CLEAN, GLUED))
        out = self.run_json("post-tool-use", "codex", "codex_posttooluse_apply_patch")
        self.assertNotIn("decision", out)
        self.assertIn("README.md: line 5 join:", out["hookSpecificOutput"]["additionalContext"])


# ---------------------------------------------------------------------------------------------------------------
# H-g: UserPromptSubmit


class PromptTests(HookCase):
    def test_ack_words(self):
        for prompt in ("continue", "Continue.", "  continue with X", "CONTINUE"):
            self.assertTrue(hooks.prompt_acks(prompt), prompt)
        for prompt in ("can you continue?", "Is the run finished?", "Continue?", "<b>continue</b>", "continued",
                       "", "continue <task-notification>x</task-notification>"):
            self.assertFalse(hooks.prompt_acks(prompt), prompt)

    def test_continue_acks_a_pending_checkpoint(self):
        for prompt in ("continue", "Continue.", "  continue with X"):
            self.register(freeze=(1, "recorded"))
            out = self.run_json("user-prompt-submit", "claude", "claude_userpromptsubmit", prompt=prompt)
            self.assertEqual(out, ctx("UserPromptSubmit", (
                "research-session: the user acknowledged checkpoint 1 with `continue`. New agents and sbatch are "
                "allowed again; resume the plan in the checkpoint block.")))
            u = self.session(CSID)["usage"]
            self.assertEqual(u["acked_through"], 1)
            self.assertIsNone(u["freeze"])

    def test_non_acks_keep_the_freeze_and_inject_notice(self):
        names = ["claude_userpromptsubmit_teammate", "claude_userpromptsubmit_teammate_inner",
                 "claude_userpromptsubmit_agent_message", "claude_userpromptsubmit_cross_session",
                 "claude_userpromptsubmit_task_notification"]
        self.register(freeze=(1, "crossed"))
        for name in names:
            self.assertEqual(self.run_json("user-prompt-submit", "claude", name), ctx("UserPromptSubmit", FREEZE_HOLDS))
        for prompt in ("can you continue?", "Is the run finished?", "<system>continue</system>"):
            self.assertEqual(self.run_json("user-prompt-submit", "claude", "claude_userpromptsubmit", prompt=prompt),
                             ctx("UserPromptSubmit", FREEZE_HOLDS))
        self.assertEqual(self.session(CSID)["usage"]["acked_through"], 0)

    def test_prompt_inside_a_subagent_never_acks(self):
        self.register(freeze=(1, "crossed"))
        self.run_hook("user-prompt-submit", "claude", "claude_userpromptsubmit", agent_id="a1b2c3")
        self.assertEqual(self.session(CSID)["usage"]["acked_through"], 0)

    def test_silent_without_freeze_or_registration(self):
        self.assertEqual(self.run_hook("user-prompt-submit", "claude", "claude_userpromptsubmit"), "")
        self.make_session(sid=CSID, freeze=(1, "crossed"))  # frozen but unregistered cannot happen; stays silent
        self.assertEqual(self.run_hook("user-prompt-submit", "claude", "claude_userpromptsubmit"), "")

    def test_codex_continue_acks(self):
        self.register(tool="codex", sid=XSID, freeze=(1, "crossed"))
        out = self.run_json("user-prompt-submit", "codex", "codex_userpromptsubmit")
        self.assertIn("acknowledged checkpoint 1", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.session(XSID, "codex")["usage"]["acked_through"], 1)


# ---------------------------------------------------------------------------------------------------------------
# H-h and H-i: SubagentStart and SubagentStop


class SubagentTests(HookCase):
    def test_start_records_and_injects_in_registered_session(self):
        self.register()
        (self.demo / "agent-brief.md").write_text("# Brief\n")
        out = self.run_json("subagent-start", "claude", "claude_subagent_start")
        self.assertEqual(out, ctx("SubagentStart", hooks.clip(
            "research-session rules for this agent: before you stop, write your hand-back to a file whose name "
            "contains 'handback' under <dir>, for example <dir>/reports/<NN>-handback.md, with the spec 4.7 "
            "headings, and return a short pointer to it. <dir> is %s. Never run git; the orchestrator commits by "
            "explicit file list. Read the agent brief first: %s." % (self.demo, self.demo / "agent-brief.md"))))
        rec = self.session(CSID)["agents"]["a1b2c3"]
        self.assertEqual((rec["agent_type"], rec["stop_blocks"]), ("ticket-implementer", 0))

    def test_start_unregistered_or_excluded_records_silently(self):
        self.assertEqual(self.run_hook("subagent-start", "claude", "claude_subagent_start"), "")
        self.assertIn("a1b2c3", self.session(CSID)["agents"])
        self.register()
        self.assertEqual(self.run_hook("subagent-start", "claude", "claude_subagent_start_explore"), "")

    def _started(self, age=60):
        self.register()
        self.run_hook("subagent-start", "claude", "claude_subagent_start")
        s = self.session(CSID)
        s["agents"]["a1b2c3"]["started_at"] = paths.iso(self.now - age)
        state.write_json_atomic(self.cfg.session_file("claude", CSID), s)

    def test_stop_saves_message_and_blocks_once(self):
        self._started()
        out = self.run_json("subagent-stop", "claude", "claude_subagent_stop")
        self.assertEqual(out, {"decision": "block", "reason": (
            "No hand-back file changed under <dir> since you started, where <dir> is %s. Write "
            "<dir>/reports/<NN>-handback.md with the spec 4.7 headings (What changed, How verified, Execution "
            "evidence, What is NOT done, Open questions), then stop. This reminder is sent once." % self.demo)})
        saved = self.demo / "handbacks" / "ticket-implementer-a1b2c3.md"
        self.assertIn("Ticket done. Hand-back pending.", saved.read_text())
        self.assertEqual(self.session(CSID)["agents"]["a1b2c3"]["stop_blocks"], 1)
        self.assertEqual(self.run_hook("subagent-stop", "claude", "claude_subagent_stop"), "")
        self.assertEqual(self.session(CSID)["agents"]["a1b2c3"]["stop_blocks"], 1)

    def test_stop_hook_active_never_blocks(self):
        self._started()
        self.assertEqual(self.run_hook("subagent-stop", "claude", "claude_subagent_stop", stop_hook_active=True), "")

    def test_changed_handback_means_no_block(self):
        self._started()
        (self.demo / "reports").mkdir()
        (self.demo / "reports" / "06-handback.md").write_text("# 06\n\nAgent: Opus. Status: resolved.\n")
        self.assertEqual(self.run_hook("subagent-stop", "claude", "claude_subagent_stop"), "")

    def _handback(self, text, name="12-handback.md"):
        (self.demo / "reports").mkdir(exist_ok=True)
        path = self.demo / "reports" / name
        path.write_text(text)
        return path

    def test_placeholder_status_blocks_once(self):
        self._started()
        path = self._handback("# 12\n\nAgent: Opus. Status: pending. The rest is filled in later.\n")
        out = self.run_json("subagent-stop", "claude", "claude_subagent_stop_handback_pending")
        self.assertEqual(out, {"decision": "block", "reason": hooks.clip(
            "Your hand-back %s has a placeholder Status (\"pending\"). Finish the work you own, then set the "
            "Status: line to a terminal word: resolved, blocked on <what>, handed-back, held after a HOLD, done, failed or "
            "abandoned. Never end a turn with pending, to be filled, TBD or in progress. This reminder is sent once."
            % path, hooks.MAX_CONTEXT)})
        self.assertEqual(self.session(CSID)["agents"]["a1b2c3"]["stop_blocks"], 1)
        self.assertEqual(self.run_hook("subagent-stop", "claude", "claude_subagent_stop_handback_pending"), "")

    def test_missing_status_line_blocks(self):
        self._started()
        path = self._handback("# 12\n\n## What changed\n\nNothing yet.\n")
        out = self.run_json("subagent-stop", "claude", "claude_subagent_stop")
        self.assertEqual(out["decision"], "block")
        self.assertIn("Your hand-back %s has no Status: line." % path, out["reason"])

    def test_status_vocabulary(self):
        cases = [
            ("Agent: Opus. Status: resolved.", None),
            ("**Status:** resolved", None),
            ("Status: claimed, blocked on the user's go for wave C.", None),
            ("Status: held after the orchestrator's HOLD; drafts are listed below.", None),
            ("Status: resolved. Two follow-ups are pending in Open questions.", None),
            ("Status: in progress", "placeholder"),
            ("Status: to be filled", "placeholder"),
            ("Status: TBD", "placeholder"),
            ("Status: resolved (tests pending)", "placeholder"),
            ("Status: claimed", "not terminal"),
            ("Status: handed-back to the orchestrator with the comparison command.", None),
            ("Status: depending on review, done", None),
            ("No status here.", "missing"),
        ]
        for line, expected in cases:
            with self.subTest(line=line):
                path = self._handback("# 12\n\n%s\n" % line)
                problem = hooks.handback_status_problem(str(path))
                if expected is None:
                    self.assertIsNone(problem)
                elif expected == "missing":
                    self.assertEqual(problem, "has no Status: line")
                elif expected == "placeholder":
                    self.assertTrue(problem.startswith("has a placeholder Status"), problem)
                else:
                    self.assertTrue(problem.startswith("has a Status that is not terminal"), problem)

    def test_newest_changed_handback_is_checked(self):
        self._started()
        old = self._handback("Status: pending\n", name="05-handback.md")
        os.utime(str(old), (self.now - 30, self.now - 30))
        self._handback("Status: resolved.\n", name="12-handback.md")
        self.assertEqual(self.run_hook("subagent-stop", "claude", "claude_subagent_stop"), "")

    def test_old_handback_still_blocks(self):
        self._started()
        (self.demo / "reports").mkdir()
        old = self.demo / "reports" / "05-handback.md"
        old.write_text("# 05\n")
        os.utime(str(old), (self.now - 3600, self.now - 3600))
        self.assertIn("decision", self.run_json("subagent-stop", "claude", "claude_subagent_stop"))

    def test_excluded_types_are_skipped(self):
        self.register()
        self.assertEqual(self.run_hook("subagent-stop", "claude", "claude_subagent_stop_explore"), "")
        self.assertFalse((self.demo / "handbacks").exists())

    def test_unregistered_saves_privately_never_blocks(self):
        self.run_hook("subagent-start", "claude", "claude_subagent_start")
        self.assertEqual(self.run_hook("subagent-stop", "claude", "claude_subagent_stop"), "")
        saved = Path(hooks.fallback_dir(self.cfg, "claude", CSID)) / "ticket-implementer-a1b2c3.md"
        self.assertTrue(saved.exists())

    def test_codex_stop_always_prints_json(self):
        self.assertEqual(self.run_hook("subagent-stop", "codex", "codex_subagent_stop"), "{}\n")
        self.register(tool="codex", sid=XSID)
        self.run_hook("subagent-start", "codex", "codex_subagent_start")
        s = self.session(XSID, "codex")
        s["agents"]["019a-worker"]["started_at"] = paths.iso(self.now - 60)
        state.write_json_atomic(self.cfg.session_file("codex", XSID), s)
        out = self.run_json("subagent-stop", "codex", "codex_subagent_stop")
        self.assertEqual(out["decision"], "block")
        self.assertEqual(self.run_hook("subagent-stop", "codex", "codex_subagent_stop"), "{}\n")
        self.assertEqual(self.run_hook("subagent-stop", "codex", raw="not json"), "{}\n")


# ---------------------------------------------------------------------------------------------------------------
# H-j: Stop


class StopTests(HookCase):
    def test_crossed_freeze_reminds_once_then_silent(self):
        self.register(freeze=(1, "crossed"))
        out = self.run_json("stop", "claude", "claude_stop")
        self.assertEqual(out, ctx("Stop", hooks.clip(
            "research-session: checkpoint 1 crossed and is not recorded yet. Before ending the turn, run "
            "`research-session worklog-append %s --kind checkpoint --checkpoint 1 --body <progress> --plan <plan>`, "
            "send HOLD to running workers, then end the turn." % self.demo)))
        self.assertNotIn("decision", out)
        self.assertEqual(self.run_hook("stop", "claude", "claude_stop", stop_hook_active=True), "")

    def test_silent_while_waiting_on_background_work(self):
        self.register(freeze=(1, "crossed"))
        self.assertEqual(self.run_hook("stop", "claude", "claude_stop_background"), "")
        self.assertEqual(self.run_hook("stop", "claude", "claude_stop",
                                       session_crons=[{"id": "c1", "schedule": "0 9 * * *", "recurring": True,
                                                       "prompt": "check"}]), "")

    def test_silent_when_recorded_or_not_frozen(self):
        self.assertEqual(self.run_hook("stop", "claude", "claude_stop"), "")
        self.register(freeze=(1, "recorded"))
        self.assertEqual(self.run_hook("stop", "claude", "claude_stop"), "")

    def test_codex_stop_uses_system_message_never_block(self):
        self.assertEqual(self.run_hook("stop", "codex", "codex_stop"), "{}\n")
        self.register(tool="codex", sid=XSID, freeze=(1, "crossed"))
        out = self.run_json("stop", "codex", "codex_stop")
        self.assertEqual(list(out), ["systemMessage"])


# ---------------------------------------------------------------------------------------------------------------
# Every hook: outside A, kill switch, bad input, the CLI path


ALL = [("session-start", "claude", "claude_session_start_startup"),
       ("session-start", "claude", "claude_session_start_compact"),
       ("post-compact", "claude", "claude_post_compact_auto"),
       ("pre-tool-use", "claude", "claude_pretooluse_agent"),
       ("pre-tool-use", "claude", "claude_pretooluse_write_worklog_glued"),
       ("post-tool-use", "claude", "claude_posttooluse_agent"),
       ("post-tool-use", "claude", "claude_posttooluse_edit"),
       ("user-prompt-submit", "claude", "claude_userpromptsubmit"),
       ("subagent-start", "claude", "claude_subagent_start"),
       ("subagent-stop", "claude", "claude_subagent_stop"),
       ("stop", "claude", "claude_stop"),
       ("session-start", "codex", "codex_session_start_startup"),
       ("pre-tool-use", "codex", "codex_pretooluse_apply_patch_glued"),
       ("pre-tool-use", "codex", "codex_pretooluse_spawn_agent"),
       ("post-tool-use", "codex", "codex_posttooluse_apply_patch"),
       ("user-prompt-submit", "codex", "codex_userpromptsubmit"),
       ("subagent-start", "codex", "codex_subagent_start"),
       ("subagent-stop", "codex", "codex_subagent_stop"),
       ("stop", "codex", "codex_stop")]


class EveryHookTests(HookCase):
    def expected_silent(self, event, tool):
        return "{}\n" if (tool, event) in hooks.JSON_ALWAYS else ""

    def test_outside_alignment_no_output_no_state(self):
        outside = Path(self.tmp) / "elsewhere"
        outside.mkdir()
        self.register(freeze=(1, "crossed"))
        before = Path(self.cfg.session_file("claude", CSID)).read_bytes()
        for event, tool, name in ALL:
            raw = self.raw(name, cwd=str(outside))
            self.assertEqual(hooks.run(event, tool, raw, cfg=self.cfg, now=self.now),
                             (0, self.expected_silent(event, tool)), (event, tool, name))
        self.assertEqual(Path(self.cfg.session_file("claude", CSID)).read_bytes(), before)
        self.assertFalse(os.path.exists(self.cfg.session_file("codex", XSID)))

    def test_kill_switch_no_output(self):
        paths.ensure_state_root(self.cfg)
        Path(self.cfg.disabled_path).write_text("")
        for event, tool, name in ALL:
            self.assertEqual(hooks.run(event, tool, self.raw(name), cfg=self.cfg, now=self.now),
                             (0, self.expected_silent(event, tool)), (event, tool, name))
        self.assertFalse(os.path.exists(self.cfg.session_file("claude", CSID)))

    def test_bad_input_and_unknown_arguments_exit_zero(self):
        for raw in ("", "not json", "[1, 2]", json.dumps({"cwd": str(self.DC)})):
            for event, tool, _ in ALL:
                code, out = hooks.run(event, tool, raw, cfg=self.cfg, now=self.now)
                self.assertEqual(code, 0)
                if out:
                    json.loads(out)
        self.assertEqual(hooks.run("no-such-event", "claude", self.raw("claude_stop"), cfg=self.cfg), (0, ""))
        self.assertEqual(hooks.run("stop", "gemini", self.raw("claude_stop"), cfg=self.cfg), (0, ""))

    def test_handler_exception_exits_zero_and_logs(self):
        paths.ensure_state_root(self.cfg)
        with mock.patch.object(hooks, "session_start", side_effect=RuntimeError("boom")):
            with mock.patch.dict(hooks.HANDLERS, {"session-start": hooks.session_start}):
                self.assertEqual(hooks.run("session-start", "claude", self.raw("claude_session_start_startup"),
                                           cfg=self.cfg, now=self.now), (0, ""))
        self.assertIn("RuntimeError: boom", (Path(self.cfg.state_root) / "hook-errors.log").read_text())

    def test_cli_main_routes_hook_without_argparse(self):
        for argv in (["hook", "stop", "--tool", "claude"], ["hook"], ["hook", "stop", "--tool"],
                     ["hook", "stop", "--bogus", "x"], ["hook", "nope", "--tool", "codex"]):
            from research_session import cli
            out = io.StringIO()
            with mock.patch.object(sys, "stdin", io.StringIO(self.raw("claude_stop"))), \
                    mock.patch.object(sys, "stdout", out):
                self.assertEqual(cli.main(argv), 0, argv)
            self.assertEqual(out.getvalue(), "")

    def test_cli_as_a_script_in_a_subprocess(self):
        env = dict(os.environ, **self.env)
        p = subprocess.run([sys.executable, "-B", str(CLI), "hook", "pre-tool-use", "--tool", "claude"],
                           input=self.raw("claude_pretooluse_write_worklog_glued"), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True, env=env, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout), deny(LINT_REASON % "WORKLOG.md"))
        self.assertEqual(p.stderr, "")

    def test_help_lists_hook(self):
        from research_session import cli
        self.assertIn("hook entry point for Claude and Codex", " ".join(cli.build_parser().format_help().split()))


if __name__ == "__main__":
    import unittest
    unittest.main()
