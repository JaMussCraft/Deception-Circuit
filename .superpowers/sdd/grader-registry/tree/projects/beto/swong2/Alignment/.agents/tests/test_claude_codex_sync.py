import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import toml


SOURCE = Path(__file__).resolve().parents[1] / "claude_codex_sync.py"
spec = importlib.util.spec_from_file_location("bridge", SOURCE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.home, self.root = base / "home", base / "project"
        self.codex = self.home / ".codex"
        self.store = self.codex / "claude-bridge"
        self.memory = self.root / ".agents/memory"
        self.old_memory = self.home / ".claude/projects/project/memory"
        values = dict(HOME=self.home, ROOT=self.root, CODEX=self.codex, STORE=self.store,
                      STATE=self.store / "state.json", MEMORY=self.memory,
                      CLAUDE_MEMORY=self.old_memory)
        self.patch = patch.multiple(bridge, **values)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(self.tmp.cleanup)
        self.put(self.root / ".claude/CLAUDE.md", "Project instructions\n")
        self.put(self.home / ".bashrc", "# existing shell settings\n")
        self.put(self.codex / "config.toml", 'model = "keep-my-model"\nmodel_reasoning_effort = "high"\n')
        self.put(self.old_memory / "MEMORY.md", "[Rule](rule.md)\n")
        self.put(self.old_memory / "rule.md", "Original memory\n")
        self.put(self.root / ".claude/agents/researcher.md", '---\nname: researcher\ndescription: Research papers\nmodel: sonnet\n---\nRead sources.\n')
        self.put(self.home / ".claude/skills/local/SKILL.md", '---\nname: local\ndescription: Local workflow\n---\nOriginal instructions.\n')
        self.plugin = self.home / ".claude/plugins/cache/package/1"
        self.put(self.plugin / ".claude-plugin/plugin.json", json.dumps({"skills": ["./skills/deep/nested"]}))
        self.put(self.plugin / "skills/deep/nested/SKILL.md", '---\nname: nested\ndescription: Nested workflow\ndisable-model-invocation: true\n---\nNested instructions.\n')
        self.put(self.plugin / ".mcp.json", json.dumps({"github": {"type": "http", "url": "https://example.invalid/mcp", "headers": {"Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"}}}))
        self.put(self.home / ".claude/plugins/installed_plugins.json", json.dumps({"plugins": {"example@test": [{"scope": "user", "installPath": str(self.plugin), "version": "1"}]}}))
        self.put(self.home / ".claude/settings.json", json.dumps({"enabledPlugins": {"example@test": True}, "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "SECRET-FIXTURE"}}))

    def put(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_live_memory_idempotence_and_credential_boundaries(self):
        w, report = bridge.sync()
        self.assertEqual(len(report["skills"]), 2)
        self.assertEqual(report["agents"], ["researcher"])
        self.assertTrue(self.old_memory.is_symlink())
        (self.memory / "rule.md").write_text("Updated by Codex\n")
        self.assertEqual((self.old_memory / "rule.md").read_text(), "Updated by Codex\n")
        (self.old_memory / "new.md").write_text("Updated by Claude\n")
        self.assertTrue((self.memory / "new.md").exists())
        config = toml.loads((self.codex / "config.toml").read_text())
        self.assertEqual(config["model"], "keep-my-model")
        self.assertEqual(config["mcp_servers"]["github"]["bearer_token_env_var"], "GITHUB_PERSONAL_ACCESS_TOKEN")
        self.assertNotIn("SECRET-FIXTURE", (self.codex / "config.toml").read_text())
        self.assertNotIn("SECRET-FIXTURE", (self.store / "report.json").read_text())
        self.assertNotIn("SECRET-FIXTURE", (self.home / ".bashrc").read_text())
        self.assertIn("false", (self.store / "skills/nested/agents/openai.yaml").read_text())
        w2, _ = bridge.sync(check=True)
        self.assertEqual(w2.changes, [])

    def test_plugin_update_and_disable_remove_only_managed_links(self):
        bridge.sync()
        source = self.plugin / "skills/deep/nested/SKILL.md"
        source.write_text(source.read_text().replace("Nested workflow", "Updated workflow"))
        bridge.sync()
        self.assertIn("Updated workflow", (self.store / "skills/nested/SKILL.md").read_text())
        settings = self.home / ".claude/settings.json"
        data = json.loads(settings.read_text())
        data["enabledPlugins"]["example@test"] = False
        settings.write_text(json.dumps(data))
        self.put(self.home / ".agents/skills/my-own/SKILL.md", "user-managed")
        bridge.sync()
        self.assertFalse((self.home / ".agents/skills/nested").exists())
        self.assertTrue((self.home / ".agents/skills/my-own/SKILL.md").exists())
        self.assertNotIn("github", toml.loads((self.codex / "config.toml").read_text()).get("mcp_servers", {}))

    def test_rollback_keeps_new_memories_and_concurrent_user_edits(self):
        bridge.sync()
        (self.memory / "new.md").write_text("New memory\n")
        shell = self.home / ".bashrc"
        shell.write_text(shell.read_text() + "# new user setting\n")
        settings = self.home / ".claude/settings.json"
        data = json.loads(settings.read_text())
        data["model"] = "new-user-model"
        settings.write_text(json.dumps(data))
        bridge.sync()
        bridge.rollback()
        self.assertFalse(self.old_memory.is_symlink())
        self.assertEqual((self.old_memory / "new.md").read_text(), "New memory\n")
        self.assertIn("# new user setting", shell.read_text())
        self.assertEqual(json.loads(settings.read_text())["model"], "new-user-model")
        self.assertNotIn("hooks", json.loads(settings.read_text()))
        self.assertEqual(toml.loads((self.codex / "config.toml").read_text())["model"], "keep-my-model")
        self.assertFalse((self.root / "AGENTS.md").exists())

    def test_project_disabling_keeps_global_skill_available(self):
        self.put(self.root / ".claude/settings.local.json", json.dumps({"enabledPlugins": {"example@test": False}}))
        bridge.sync()
        self.assertTrue((self.home / ".agents/skills/nested").is_symlink())
        config = toml.loads((self.root / ".codex/config.toml").read_text())
        self.assertFalse(config["skills"]["config"][0]["enabled"])
        self.assertFalse(config["mcp_servers"]["github"]["enabled"])

    def test_nonstandard_upstream_yaml_and_agent_removal(self):
        self.put(self.home / ".claude/skills/local/SKILL.md", '---\nname: local\ndescription: Workflow: with an unquoted colon\n---\nInstructions.\n')
        bridge.sync()
        self.assertIn("unquoted colon", (self.store / "skills/local/SKILL.md").read_text())
        (self.root / ".claude/agents/researcher.md").unlink()
        bridge.sync()
        self.assertFalse((self.root / ".codex/agents/researcher.toml").exists())

    def test_hook_trust_survives_bridge_config_rewrite(self):
        # Codex may write [hooks.state] inside the managed block; sync must relocate it.
        bridge.sync()
        path = self.codex / "config.toml"
        text = path.read_text()
        self.assertIn(bridge.BEGIN, text)
        self.assertIn(bridge.END, text)
        key = str(self.codex / "hooks.json") + ":session_start:0:0"
        poisoned = text.replace(
            bridge.END,
            '[hooks.state."' + key + '"]\ntrusted_hash = "sha256:fixture"\n' + bridge.END,
        )
        path.write_text(poisoned)
        bridge.sync()
        rewritten = path.read_text()
        bridge_block = rewritten[rewritten.index(bridge.BEGIN):rewritten.index(bridge.END) + len(bridge.END)]
        self.assertNotIn("hooks.state", bridge_block)
        self.assertIn('trusted_hash = "sha256:fixture"', rewritten)
        self.assertGreater(rewritten.index(bridge.END), rewritten.index(bridge.BEGIN))
        self.assertGreater(rewritten.index("hooks.state"), rewritten.index(bridge.END))
        self.assertEqual(
            toml.loads(rewritten)["hooks"]["state"][key]["trusted_hash"],
            "sha256:fixture",
        )
        w2, _ = bridge.sync(check=True)
        self.assertEqual(w2.changes, [])

    def test_sync_failure_does_not_block_cli_or_consume_its_flags(self):
        with patch.object(bridge.sys, "argv", ["bridge", "--launch", "codex", "--help"]), \
             patch.object(bridge, "sync", side_effect=RuntimeError("broken plugin metadata")), \
             patch.object(bridge.shutil, "which", return_value="/bin/codex"), \
             patch.object(bridge.os, "execve") as launch:
            bridge.main()
        self.assertEqual(launch.call_args[0][1], ["/bin/codex", "--help"])

    def test_claude_denied_mcp_server_stays_configured_but_off(self):
        settings = self.home / ".claude/settings.json"
        data = json.loads(settings.read_text())
        data["deniedMcpServers"] = [{"serverName": "github"}, {"serverUrl": "https://other.invalid/*"}]
        settings.write_text(json.dumps(data))
        bridge.sync()
        config = toml.loads((self.codex / "config.toml").read_text())
        self.assertIs(config["mcp_servers"]["github"]["enabled"], False)
        self.assertEqual(config["mcp_servers"]["github"]["url"], "https://example.invalid/mcp")
        data["deniedMcpServers"] = []
        settings.write_text(json.dumps(data))
        bridge.sync()
        config = toml.loads((self.codex / "config.toml").read_text())
        self.assertNotIn("enabled", config["mcp_servers"]["github"])


if __name__ == "__main__":
    unittest.main()
