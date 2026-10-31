"""Tests for the staged hook settings of ticket 06 (stdlib only; base python3.9 and mgnp).

They check that every staged hook command is the literal shell guard of spec 5.1, that the two wave H json_merge ops
keep the bridge hook and are idempotent, that a missing CLI or the kill switch gives exit 0 with no output, and that
the smoke script passes against the staged cli.py. Nothing outside temporary directories is written.
"""

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.dirname(HERE)
STAGED = os.path.join(F, "staged")
sys.path.insert(0, HERE)

import apply_staged  # noqa: E402
import hook_smoke  # noqa: E402

S = "/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging"
OPS = os.path.join(S, "ops", "06-hooks.json")
STAGED_CLI = S + "/tree" + hook_smoke.CLI
BRIDGE = "/projects/beto/swong2/Alignment/.agents/claude_codex_sync.py --hook"
PRE_H_A_SETTINGS = {"enabledPlugins": {"andrej-karpathy-skills@karpathy-skills": False}}
PRE_H_CODEX_HOOKS = {"hooks": {"SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": [{
    "type": "command", "timeout": 30,
    "command": "/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/.agents/claude_codex_sync.py --hook"}]}]}}
EVENTS = {"session-start", "post-compact", "pre-tool-use", "post-tool-use", "user-prompt-submit", "subagent-start",
          "subagent-stop", "stop"}


def load(name):
    with open(os.path.join(STAGED, name)) as fh:
        return json.load(fh)


def commands(data):
    for event_key, groups in data["hooks"].items():
        for g in groups:
            for h in g["hooks"]:
                yield event_key, g.get("matcher"), h


def guard(event, tool):
    return ("sh -c 'test -f %s && ! test -e %s && exec %s -B %s hook %s --tool %s || exit 0'"
            % (hook_smoke.CLI, hook_smoke.DISABLED, hook_smoke.PY, hook_smoke.CLI, event, tool))


class StagedSettingsTest(unittest.TestCase):
    def test_dc_settings_parse_and_match_the_claude_fragment(self):
        self.assertEqual(load("dc-claude-settings.json"), load("claude-hooks-fragment.json"))

    def test_every_command_is_the_literal_guard(self):
        for name, tool in (("dc-claude-settings.json", "claude"), ("codex-hooks-fragment.json", "codex")):
            n = 0
            for event_key, matcher, h in commands(load(name)):
                cmd = h["command"]
                self.assertNotIn("$", cmd)
                m = hook_smoke.GUARD_RE.match(cmd)
                self.assertIsNotNone(m, cmd)
                self.assertEqual(m.group("tool"), tool)
                self.assertIn(m.group("event"), EVENTS)
                self.assertEqual(cmd, guard(m.group("event"), tool))
                self.assertEqual(h["type"], "command")
                self.assertEqual(h["timeout"], 20 if m.group("event") == "pre-tool-use" else 10)
                n += 1
            self.assertGreater(n, 0)

    def test_claude_events_and_matchers(self):
        got = sorted((k, m, hook_smoke.GUARD_RE.match(h["command"]).group("event"))
                     for k, m, h in commands(load("dc-claude-settings.json")))
        self.assertEqual(got, sorted([
            ("SessionStart", "startup|resume", "session-start"), ("SessionStart", "compact", "session-start"),
            ("PostCompact", "manual|auto", "post-compact"),
            ("PreToolUse", "Agent|Bash|SendMessage|Write|Edit", "pre-tool-use"),
            ("PostToolUse", "Agent", "post-tool-use"), ("PostToolUse", "Write|Edit", "post-tool-use"),
            ("UserPromptSubmit", None, "user-prompt-submit"), ("SubagentStart", None, "subagent-start"),
            ("SubagentStop", None, "subagent-stop"), ("Stop", None, "stop")]))

    def test_codex_events_and_no_message_matcher(self):
        data = load("codex-hooks-fragment.json")
        self.assertEqual(sorted(data["hooks"]), ["PostToolUse", "PreToolUse", "SessionStart", "SubagentStart",
                                                 "SubagentStop", "UserPromptSubmit"])
        for _, matcher, _ in commands(data):
            self.assertNotIn("send_message", matcher or "")
            self.assertNotIn("SendMessage", matcher or "")


class OpsTest(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(OPS):
            self.skipTest("staging op file not present")
        with open(OPS) as fh:
            self.ops = json.load(fh)["ops"]

    def test_waves_and_order(self):
        waves = [op["wave"] for op in self.ops]
        self.assertEqual(waves, sorted(waves, key=lambda w: 0 if w == "A" else 1))
        for op in self.ops:
            if op["op"] == "json_merge" or op.get("dest", "").endswith(".json"):
                self.assertNotIn("lint", op)
            if op["wave"] == "A":
                self.assertFalse(apply_staged.installs_hooks(op, S), op["dest"])
            else:
                self.assertEqual(op["wave"], "H")

    def test_fragments_equal_the_staged_files(self):
        merges = {op["dest"]: op["fragment"] for op in self.ops if op["op"] == "json_merge"}
        self.assertEqual(merges["/projects/beto/swong2/Alignment/.claude/settings.json"],
                         load("claude-hooks-fragment.json"))
        self.assertEqual(merges["/u/swong2/.codex/hooks.json"], load("codex-hooks-fragment.json"))
        dc = [op for op in self.ops if op["op"] == "write" and op["dest"].endswith("/.claude/settings.json")][0]
        with open(os.path.join(S, dc["src"])) as fh, open(os.path.join(STAGED, "dc-claude-settings.json")) as gh:
            self.assertEqual(fh.read(), gh.read())

    def test_live_files_still_hold_the_bridge_hook(self):
        with open("/u/swong2/.codex/hooks.json") as fh:
            live = json.load(fh)
        self.assertTrue(any(BRIDGE in h.get("command", "") for g in live["hooks"]["SessionStart"]
                            for h in g["hooks"]))

    def test_merges_keep_the_bridge_hook_and_are_idempotent(self):
        # The two files as they were before wave H (2026-10-31), so this test stays valid after installation.
        sources = {"a-settings": (PRE_H_A_SETTINGS, load("claude-hooks-fragment.json")),
                   "codex-hooks": (PRE_H_CODEX_HOOKS, load("codex-hooks-fragment.json"))}
        for dest, (before, fragment) in sources.items():
            base = copy.deepcopy(before)
            original = copy.deepcopy(base)
            changes = []
            apply_staged.deep_merge(base, fragment, [], changes)
            self.assertTrue(changes)
            json.loads(json.dumps(base))
            for key, value in original.items():
                if key != "hooks":
                    self.assertEqual(base[key], value)
            for event, groups in (original.get("hooks") or {}).items():
                for g in groups:
                    self.assertIn(g, base["hooks"][event])
            if "codex" in dest:
                bridge = [g for g in base["hooks"]["SessionStart"] if BRIDGE in g["hooks"][0]["command"]]
                self.assertEqual(bridge, [g for g in original["hooks"]["SessionStart"]
                                          if BRIDGE in g["hooks"][0]["command"]])
            again = []
            apply_staged.deep_merge(base, fragment, [], again)
            self.assertEqual(again, [])


class GuardBehaviourTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hook-guard-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def unique_commands(self):
        out = set()
        for name in ("dc-claude-settings.json", "codex-hooks-fragment.json"):
            for _, _, h in commands(load(name)):
                out.add(h["command"])
        return sorted(out)

    def run_sh(self, cmd):
        with open(hook_smoke.SMOKE_INPUT) as fh:
            text = fh.read()
        return subprocess.run(["/bin/sh", "-c", cmd], input=text, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=60)

    def test_missing_cli_exits_zero_silently(self):
        missing = os.path.join(self.tmp, "missing", "cli.py")
        for cmd in self.unique_commands():
            p = self.run_sh(cmd.replace(hook_smoke.CLI, missing))
            self.assertEqual((p.returncode, p.stdout, p.stderr), (0, "", ""), cmd)

    def test_kill_switch_exits_zero_silently(self):
        switch = os.path.join(self.tmp, "DISABLED")
        open(switch, "w").close()
        for cmd in self.unique_commands():
            p = self.run_sh(cmd.replace(hook_smoke.CLI, STAGED_CLI).replace(hook_smoke.DISABLED, switch))
            self.assertEqual((p.returncode, p.stdout, p.stderr), (0, "", ""), cmd)

    def test_smoke_script_passes_on_the_staged_cli(self):
        if not os.path.exists(STAGED_CLI):
            self.skipTest("staged cli.py not present")
        p = subprocess.run([sys.executable, "-B", os.path.join(HERE, "hook_smoke.py"), "--settings",
                            os.path.join(STAGED, "claude-hooks-fragment.json"),
                            os.path.join(STAGED, "codex-hooks-fragment.json"), "--cli", STAGED_CLI],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=600)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("hook smoke: all checks passed", p.stdout)


if __name__ == "__main__":
    unittest.main()
