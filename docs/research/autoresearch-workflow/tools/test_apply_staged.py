"""Tests for apply_staged.py (spec section 7). Stdlib only; run on Python 3.9 and 3.12.

Every test works inside a temporary directory: staging root, targets and backup root. Nothing touches the real
home directory, the Alignment checkout or the staging root used by the feature.
"""

import contextlib
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import apply_staged  # noqa: E402

try:
    import tomllib
except ImportError:  # Python 3.9
    tomllib = None

FAKE_LINT = (
    "import sys\n"
    "bad = 0\n"
    "for p in sys.argv[1:]:\n"
    "    for i, line in enumerate(open(p).read().split('\\n'), 1):\n"
    "        if 'GLUED' in line:\n"
    "            print('%s:%d: join: %s' % (p, i, line[:40]))\n"
    "            bad = 1\n"
    "sys.exit(bad)\n"
)


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


class Harness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.staging = self.root / "S"
        (self.staging / "ops").mkdir(parents=True)
        self.backups = self.root / "backups"
        self.target = self.root / "target"
        self.target.mkdir()
        fake = self.root / "fake_lint.py"
        fake.write_text(FAKE_LINT)
        self.lint_cmd = shlex.quote(sys.executable) + " " + shlex.quote(str(fake))

    def tearDown(self):
        self._tmp.cleanup()

    def t(self, rel):
        return self.target / rel

    def stage(self, dest, content):
        rel = "tree" + str(dest)
        path = self.staging / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return rel

    def ops(self, ticket, ops, slug="test"):
        (self.staging / "ops" / ("%s-%s.json" % (ticket, slug))).write_text(json.dumps({"ticket": ticket, "ops": ops}))

    def run_tool(self, *args, wave="A"):
        argv = ["--staging", str(self.staging), "--backup-root", str(self.backups), "--lint-cmd", self.lint_cmd]
        if wave:
            argv += ["--wave", wave]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = apply_staged.main(argv + list(args))
        return code, out.getvalue()

    def journals(self):
        return sorted(self.backups.glob("*/journal.json")) if self.backups.exists() else []


class WriteTests(Harness):
    def test_write_with_backup_and_journal(self):
        dest = self.t("note.md")
        dest.write_text("old\n")
        self.ops("01", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "new\n"),
                         "expect_sha256": sha("old\n"), "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertEqual(dest.read_text(), "new\n")
        [journal] = self.journals()
        entries = json.loads(journal.read_text())["entries"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(Path(entries[0]["backup"]).read_text(), "old\n")
        self.assertEqual(entries[0]["sha256_before"], sha("old\n"))
        self.assertEqual(entries[0]["sha256_after"], sha("new\n"))
        self.assertTrue(entries[0]["backup"].endswith(str(dest)))

    def test_idempotent_rerun_with_expect_sha256(self):
        dest = self.t("note.md")
        dest.write_text("old\n")
        self.ops("01", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "new\n"),
                         "expect_sha256": sha("old\n"), "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertIn("SKIP", out)
        self.assertNotIn("CONFLICT", out)
        self.assertEqual(len(self.journals()), 1)

    def test_expect_sha256_conflict_leaves_file_alone(self):
        dest = self.t("note.md")
        dest.write_text("changed by codex\n")
        self.ops("01", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "new\n"),
                         "expect_sha256": sha("old\n"), "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT", out)
        self.assertEqual(dest.read_text(), "changed by codex\n")

    def test_new_file_creates_parents_and_rollback_removes_them(self):
        dest = self.t("a/b/new.py")
        self.ops("01", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "x = 1\n"), "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        self.assertEqual(dest.read_text(), "x = 1\n")
        [journal] = self.journals()
        code, out = self.run_tool("--rollback", str(journal), wave=None)
        self.assertEqual(code, 0, out)
        self.assertFalse(self.t("a").exists())

    def test_src_outside_staging_is_refused(self):
        dest = self.t("x.md")
        self.ops("01", [{"op": "write", "dest": str(dest), "src": "../../etc/passwd", "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        self.assertFalse(dest.exists())


class JsonMergeTests(Harness):
    def settings(self, data):
        dest = self.t("settings.json")
        dest.write_text(json.dumps(data, indent=2) + "\n")
        return dest

    def test_deep_merge_adds_keys_and_extends_lists(self):
        dest = self.settings({"a": {"x": 1}, "auto": {"environment": ["one", "two"]}, "keep": True})
        frag = {"a": {"y": 2}, "auto": {"environment": ["two", "three"]}, "new": 365}
        self.ops("01", [{"op": "json_merge", "dest": str(dest), "fragment": frag, "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        self.assertEqual(json.loads(dest.read_text()), {
            "a": {"x": 1, "y": 2}, "auto": {"environment": ["one", "two", "three"]}, "keep": True, "new": 365})
        code, out = self.run_tool()
        self.assertIn("SKIP", out)

    def test_list_merge_never_removes_or_duplicates(self):
        dest = self.settings({"l": [{"k": 1}, "s", 3]})
        frag = {"l": [{"k": 1}, 3]}
        self.ops("01", [{"op": "json_merge", "dest": str(dest), "fragment": frag, "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 0)
        self.assertIn("SKIP", out)
        self.assertEqual(json.loads(dest.read_text()), {"l": [{"k": 1}, "s", 3]})

    def hook(self, matcher, command, timeout=10):
        return {"matcher": matcher, "hooks": [{"type": "command", "command": command, "timeout": timeout}]}

    def test_hook_groups_dedupe_by_matcher_and_command(self):
        dest = self.settings({"hooks": {"SessionStart": [self.hook("startup|resume", "run-a", 10)]}})
        frag = {"hooks": {"SessionStart": [
            self.hook("startup|resume", "run-a", 30),  # same matcher and command, other timeout: present
            self.hook("compact", "run-a"),              # same command, other matcher: appended
            self.hook("startup|resume", "run-b"),       # new command: appended
        ]}}
        self.ops("06", [{"op": "json_merge", "dest": str(dest), "fragment": frag, "wave": "H"}])
        code, out = self.run_tool(wave="H")
        self.assertEqual(code, 0, out)
        groups = json.loads(dest.read_text())["hooks"]["SessionStart"]
        self.assertEqual([(g["matcher"], g["hooks"][0]["command"], g["hooks"][0]["timeout"]) for g in groups], [
            ("startup|resume", "run-a", 10), ("compact", "run-a", 10), ("startup|resume", "run-b", 10)])

    def test_hook_fragment_outside_wave_h_is_refused(self):
        dest = self.settings({})
        self.ops("06", [{"op": "json_merge", "dest": str(dest), "fragment": {"hooks": {"Stop": []}}, "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", out)
        self.assertEqual(json.loads(dest.read_text()), {})

    def test_type_mismatch_is_a_conflict(self):
        dest = self.settings({"a": [1]})
        self.ops("01", [{"op": "json_merge", "dest": str(dest), "fragment": {"a": {"b": 1}}, "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT", out)

    def test_output_never_prints_env_values(self):
        dest = self.settings({"env": {"EXISTING_TOKEN": "existing-secret-value"}, "x": "visible-old"})
        frag = {"env": {"NEW_KEY": "fragment-secret-value"}, "x": "visible-new", "y": "other-value"}
        self.ops("01", [{"op": "json_merge", "dest": str(dest), "fragment": frag, "wave": "A"}])
        for args in (("--dry-run",), ()):
            code, out = self.run_tool(*args)
            self.assertEqual(code, 0, out)
            self.assertIn("env.NEW_KEY", out)
            for value in ("existing-secret-value", "fragment-secret-value", "visible-new", "other-value"):
                self.assertNotIn(value, out)
        self.assertEqual(json.loads(dest.read_text())["env"],
                         {"EXISTING_TOKEN": "existing-secret-value", "NEW_KEY": "fragment-secret-value"})

    def test_non_ascii_is_kept_verbatim(self):
        dest = self.t("settings.json")
        dest.write_bytes('{\n  "a": "dash — here"\n}\n'.encode("utf-8"))
        self.ops("01", [{"op": "json_merge", "dest": str(dest), "fragment": {"b": 1}, "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        self.assertIn("dash — here".encode("utf-8"), dest.read_bytes())


CODEX_TOML = ('# comment\nmodel = "gpt-6-astra"\napproval_policy = "on-request"\n[tui]\nx = true\n\n'
              '[projects."/p"]\ntrust_level = "trusted"\n\n# BEGIN Claude-Codex bridge\n[mcp_servers.a]\nurl = "u"\n'
              '# END Claude-Codex bridge\n')


class TextBlockTests(Harness):
    def codex(self):
        d = self.t(".codex")
        d.mkdir()
        dest = d / "config.toml"
        dest.write_text(CODEX_TOML)
        return dest

    def op(self, dest, text='[agents]\ndefault_subagent_model = "gpt-6.1-sol"\n'):
        return {"op": "text_block", "dest": str(dest), "marker": "autoresearch-workflow-agents", "text": text,
                "position": "before_first_table", "wave": "C"}

    def test_codex_config_needs_allow_flag(self):
        dest = self.codex()
        self.ops("01", [self.op(dest)])
        code, out = self.run_tool(wave="C")
        self.assertEqual(code, 1)
        self.assertIn("--allow codex-config", out)
        self.assertEqual(dest.read_text(), CODEX_TOML)

    def test_block_goes_before_first_table_and_is_idempotent(self):
        dest = self.codex()
        self.ops("01", [self.op(dest)])
        code, out = self.run_tool("--allow", "codex-config", wave="C")
        self.assertEqual(code, 0, out)
        text = dest.read_text()
        self.assertLess(text.index("# BEGIN autoresearch-workflow-agents"), text.index("[tui]"))
        self.assertLess(text.index('approval_policy'), text.index("# BEGIN autoresearch-workflow-agents"))
        bridge = CODEX_TOML[CODEX_TOML.index("# BEGIN Claude-Codex"):]
        self.assertTrue(text.endswith(bridge))
        self.assertIn("SKIP", self.run_tool("--allow", "codex-config", wave="C")[1])
        if tomllib is not None:
            data = tomllib.loads(text)
            self.assertEqual(data["agents"], {"default_subagent_model": "gpt-6.1-sol"})
            self.assertEqual(data["model"], "gpt-6-astra")
            self.assertTrue(data["tui"]["x"])

    def test_existing_block_is_replaced(self):
        dest = self.codex()
        self.ops("01", [self.op(dest)])
        self.run_tool("--allow", "codex-config", wave="C")
        self.ops("01", [self.op(dest, '[agents]\ndefault_subagent_model = "other"\n')])
        self.assertEqual(self.run_tool("--allow", "codex-config", wave="C")[0], 0)
        text = dest.read_text()
        self.assertEqual(text.count("# BEGIN autoresearch-workflow-agents"), 1)
        self.assertIn('"other"', text)
        self.assertNotIn("gpt-6.1-sol", text)

    def test_no_table_appends_at_end(self):
        dest = self.t("plain.toml")
        dest.write_text('a = 1\n')
        op = self.op(dest)
        op["wave"] = "A"
        self.ops("01", [op])
        self.assertEqual(self.run_tool()[0], 0)
        self.assertTrue(dest.read_text().startswith('a = 1\n'))
        self.assertTrue(dest.read_text().endswith("# END autoresearch-workflow-agents\n"))


MEMORY = "# Memory Index\n\n- [A](a.md) — first line.\n- [B](b.md) — GLUED old line stays.\n- [C](c.md) — third line.\n"


class TextOpTests(Harness):
    def memory(self, text=MEMORY):
        dest = self.t("MEMORY.md")
        dest.write_text(text)
        return dest

    def test_replace_text_zero_one_and_two_matches(self):
        dest = self.memory(MEMORY + "- [D](d.md) — dup.\n- [D](d.md) — dup.\n")
        self.ops("01", [
            {"op": "replace_text", "dest": str(dest), "old_text": "missing text", "new_text": "- [X](x.md) — new.",
             "wave": "A"},
            {"op": "replace_text", "dest": str(dest), "old_text": "first line.", "new_text": "first, fixed.",
             "wave": "A"},
            {"op": "replace_text", "dest": str(dest), "old_text": "- [D](d.md) — dup.", "new_text": "y", "wave": "A"},
        ])
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        text = dest.read_text()
        self.assertIn("first, fixed.", text)
        self.assertEqual(text.count("- [D](d.md) — dup."), 2)
        self.assertNotIn("[X](x.md)", text)
        self.assertEqual(out.count("CONFLICT"), 2)

    def test_replace_text_is_idempotent_when_new_text_contains_old_text(self):
        dest = self.memory()
        self.ops("01", [{"op": "replace_text", "dest": str(dest), "old_text": "third line.",
                         "new_text": "third line. More.", "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        code, out = self.run_tool()
        self.assertEqual(code, 0)
        self.assertIn("SKIP", out)
        self.assertEqual(dest.read_text().count("More."), 1)

    def test_replace_text_applies_when_new_text_is_part_of_old_text(self):
        dest = self.memory()
        self.ops("01", [{"op": "replace_text", "dest": str(dest), "old_text": "- [C](c.md) — third line.",
                         "new_text": "- [C](c.md) — third", "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertIn("APPLY", out)
        self.assertNotIn("third line.", dest.read_text())
        self.assertIn("SKIP", self.run_tool()[1])

    def test_append_text_skips_text_already_present(self):
        dest = self.memory()
        self.ops("01", [{"op": "append_text", "dest": str(dest), "text": "- [E](e.md) — new.\n", "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        self.assertIn("SKIP", self.run_tool()[1])
        self.assertEqual(dest.read_text(), MEMORY + "- [E](e.md) — new.\n")

    def test_append_adds_missing_final_newline(self):
        dest = self.memory("line")
        self.ops("01", [{"op": "append_text", "dest": str(dest), "text": "next\n", "wave": "A"}])
        self.run_tool()
        self.assertEqual(dest.read_text(), "line\nnext\n")

    def test_lint_true_refuses_glued_write(self):
        dest = self.t("note.md")
        dest.write_text("old\n")
        self.ops("01", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "GLUED text\n"), "lint": True,
                         "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", out)
        self.assertEqual(dest.read_text(), "old\n")

    def test_lint_text_ops_ignore_failures_already_in_the_file(self):
        dest = self.memory()
        self.ops("01", [
            {"op": "replace_text", "dest": str(dest), "old_text": "first line.", "new_text": "first, fixed.",
             "lint": True, "wave": "A"},
            {"op": "append_text", "dest": str(dest), "text": "- [F](f.md) — clean.\n", "lint": True, "wave": "A"},
        ])
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertIn("first, fixed.", dest.read_text())

    def test_lint_text_ops_refuse_new_glue(self):
        dest = self.memory()
        self.ops("01", [
            {"op": "replace_text", "dest": str(dest), "old_text": "third line.", "new_text": "GLUED now.",
             "lint": True, "wave": "A"},
            {"op": "append_text", "dest": str(dest), "text": "- GLUED again\n", "lint": True, "wave": "A"},
        ])
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        self.assertEqual(out.count("REFUSED"), 2)
        self.assertEqual(dest.read_text(), MEMORY)


class FilesystemOpTests(Harness):
    def test_move_symlink_mkdir_and_rollback(self):
        src = self.t("old")
        src.mkdir()
        (src / "f.txt").write_text("f\n")
        moved = self.t("archive/old")
        self.t("archive").mkdir()
        link = self.t("link")
        newdir = self.t("made/deep")
        self.ops("10", [
            {"op": "move", "src": str(src), "dest": str(moved), "wave": "B"},
            {"op": "symlink", "path": str(link), "target": str(moved), "wave": "B"},
            {"op": "mkdir", "path": str(newdir), "wave": "B"},
        ])
        code, out = self.run_tool(wave="B")
        self.assertEqual(code, 0, out)
        self.assertEqual((moved / "f.txt").read_text(), "f\n")
        self.assertFalse(src.exists())
        self.assertEqual(os.readlink(str(link)), str(moved))
        self.assertTrue(newdir.is_dir())
        self.assertEqual(out.count("SKIP"), 0)
        self.assertEqual(self.run_tool(wave="B")[1].count("SKIP"), 3)
        [journal] = self.journals()
        code, out = self.run_tool("--rollback", str(journal), wave=None)
        self.assertEqual(code, 0, out)
        self.assertEqual((src / "f.txt").read_text(), "f\n")
        self.assertFalse(os.path.lexists(str(link)))
        self.assertFalse(self.t("made").exists())

    def test_symlink_over_existing_path_is_a_conflict(self):
        path = self.t("busy")
        path.mkdir()
        self.ops("10", [{"op": "symlink", "path": str(path), "target": str(self.t("x")), "wave": "B"}])
        code, out = self.run_tool(wave="B")
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT", out)


class ModeTests(Harness):
    def setup_two_tickets(self):
        a = self.t("a.md")
        b = self.t("b.md")
        c = self.t("c.md")
        for p in (a, b, c):
            p.write_text("old\n")
        self.ops("01", [{"op": "write", "dest": str(a), "src": self.stage(a, "new a\n"), "wave": "A"},
                        {"op": "write", "dest": str(c), "src": self.stage(c, "new c\n"), "wave": "D"}])
        self.ops("02", [{"op": "write", "dest": str(b), "src": self.stage(b, "new b\n"), "wave": "A"}])
        return a, b, c

    def test_dry_run_writes_nothing(self):
        a, b, c = self.setup_two_tickets()
        code, out = self.run_tool("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("WOULD APPLY", out)
        self.assertEqual([p.read_text() for p in (a, b, c)], ["old\n"] * 3)
        self.assertFalse(self.backups.exists())

    def test_wave_and_only_filters(self):
        a, b, c = self.setup_two_tickets()
        self.assertEqual(self.run_tool("--only", "02")[0], 0)
        self.assertEqual([p.read_text() for p in (a, b, c)], ["old\n", "new b\n", "old\n"])
        self.assertEqual(self.run_tool()[0], 0)
        self.assertEqual([p.read_text() for p in (a, b, c)], ["new a\n", "new b\n", "old\n"])
        self.assertEqual(self.run_tool("--only", "01", wave="D")[0], 0)
        self.assertEqual(c.read_text(), "new c\n")

    def test_wave_is_required(self):
        self.setup_two_tickets()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                self.run_tool(wave=None)

    def test_rollback_restores_and_refuses_after_later_edit(self):
        a, b, _ = self.setup_two_tickets()
        self.run_tool()
        [journal] = self.journals()
        b.write_text("edited after apply\n")
        code, out = self.run_tool("--rollback", str(journal), wave=None)
        self.assertEqual(code, 1)
        self.assertEqual(a.read_text(), "old\n")
        self.assertEqual(b.read_text(), "edited after apply\n")
        self.assertIn("CONFLICT", out)

    def test_protected_paths_are_refused_in_waves_a_and_b(self):
        mem = self.t("MEMORY.md")
        mem.write_text("- [SDR mechanism review](sdr-mechanism-review.md) — glued\n")
        note = self.t("selective-deception-execution.md")
        note.write_text("old\n")
        scratch = self.t(".scratch/sdr-clause-choice")
        scratch.mkdir(parents=True)

        def ops(wave):
            return [
                {"op": "replace_text", "dest": str(mem), "old_text": "- [SDR mechanism review]"
                 "(sdr-mechanism-review.md) — glued", "new_text": "- clean", "wave": wave},
                {"op": "write", "dest": str(note), "src": self.stage(note, "new\n"), "wave": wave},
                {"op": "move", "src": str(scratch), "dest": str(self.t("moved")), "wave": wave},
            ]

        self.ops("12", ops("A"))
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        self.assertEqual(out.count("REFUSED"), 3)
        self.assertEqual(note.read_text(), "old\n")
        self.ops("12", ops("D"))
        self.assertEqual(self.run_tool(wave="D")[0], 0)
        self.assertEqual(note.read_text(), "new\n")
        self.assertEqual(mem.read_text(), "- clean\n")


class DryRunChainTests(Harness):
    """Ticket 12: a dry run carries planned state forward, so chained mkdir, move and symlink ops plan cleanly."""

    def chain(self):
        src = self.t(".scratch/demo")
        (src / "reports").mkdir(parents=True)
        (src / "reports" / "a.md").write_text("a\n")
        study = self.t("outputs/_studies/demo")
        self.t("outputs/_studies").mkdir(parents=True)
        self.ops("10", [
            {"op": "mkdir", "path": str(study), "wave": "B"},
            {"op": "move", "src": str(src), "dest": str(study / "scratch"), "wave": "B"},
            {"op": "symlink", "path": str(src), "target": str(study / "scratch"), "wave": "B"},
        ])
        return src, study

    def test_chained_mkdir_move_symlink_dry_runs_clean(self):
        src, study = self.chain()
        code, out = self.run_tool("--dry-run", wave="B")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.count("WOULD APPLY"), 3, out)
        self.assertNotIn("ERROR", out)
        self.assertNotIn("CONFLICT", out)
        self.assertTrue(src.is_dir() and not src.is_symlink())
        self.assertFalse(study.exists())
        self.assertFalse(self.backups.exists())

    def test_real_run_is_unchanged_by_the_overlay(self):
        src, study = self.chain()
        self.assertEqual(self.run_tool(wave="B")[0], 0)
        self.assertEqual(os.readlink(str(src)), str(study / "scratch"))
        self.assertEqual((src / "reports" / "a.md").read_text(), "a\n")
        code, out = self.run_tool("--dry-run", wave="B")
        self.assertEqual((code, out.count("SKIP")), (0, 3), out)

    def test_rerun_skips_a_move_whose_source_became_a_link_elsewhere(self):
        # Ticket 10's autoresearch-workflow pattern: move the stale copy aside, then link the old path to the
        # canonical feature directory, not to the moved copy.
        src = self.t(".scratch/feature")
        src.mkdir(parents=True)
        (src / "old.md").write_text("old\n")
        canonical = self.t("docs/feature")
        canonical.mkdir(parents=True)
        stash = self.t("outputs/feature/stale")
        self.ops("10", [
            {"op": "mkdir", "path": str(stash.parent), "wave": "B"},
            {"op": "move", "src": str(src), "dest": str(stash), "wave": "B"},
            {"op": "symlink", "path": str(src), "target": str(canonical), "wave": "B"},
        ])
        self.assertEqual(self.run_tool(wave="B")[0], 0)
        self.assertEqual(os.readlink(str(src)), str(canonical))
        code, out = self.run_tool(wave="B")
        self.assertEqual((code, out.count("SKIP")), (0, 3), out)

    def test_planned_write_fills_its_path_and_moves_chain(self):
        new = self.t("made/new.md")
        a = self.t("a")
        a.mkdir()
        self.ops("12", [
            {"op": "write", "dest": str(new), "src": self.stage(new, "x\n"), "wave": "D"},
            {"op": "symlink", "path": str(new), "target": str(a), "wave": "D"},
            {"op": "move", "src": str(a), "dest": str(self.t("b")), "wave": "D"},
            {"op": "move", "src": str(self.t("b")), "dest": str(self.t("c")), "wave": "D"},
            {"op": "move", "src": str(a), "dest": str(self.t("d")), "wave": "D"},
        ])
        code, out = self.run_tool("--dry-run", wave="D")
        lines = out.splitlines()[1:]
        self.assertIn("WOULD APPLY", lines[0])
        self.assertIn("CONFLICT: link path exists", lines[1])
        self.assertIn("WOULD APPLY", lines[2])
        self.assertIn("WOULD APPLY", lines[3])
        self.assertIn("ERROR: move source missing", lines[4])
        self.assertEqual(code, 1)
        self.assertFalse(new.exists())


class CrossDeviceMoveTests(Harness):
    """Ticket 12: op_move falls back to copy, sha256 verify and unlink when os.rename fails with EXDEV."""

    EXDEV = OSError(errno.EXDEV, "Invalid cross-device link")

    def tree(self):
        src = self.t("from/pc")
        (src / "deep").mkdir(parents=True)
        (src / "deep" / "f.md").write_text("f\n")
        (src / "top.md").write_text("top\n")
        (src / "empty").mkdir()
        os.symlink("top.md", str(src / "link.md"))
        self.t("to").mkdir()
        return src, self.t("to/pc")

    def test_directory_move_across_devices(self):
        src, dest = self.tree()
        before = apply_staged.tree_manifest(str(src))
        self.ops("12", [{"op": "move", "src": str(src), "dest": str(dest), "wave": "D"}])
        with mock.patch.object(apply_staged.os, "rename", side_effect=self.EXDEV):
            code, out = self.run_tool(wave="D")
        self.assertEqual(code, 0, out)
        self.assertIn("copied across file systems", out)
        self.assertFalse(os.path.lexists(str(src)))
        self.assertEqual(apply_staged.tree_manifest(str(dest)), before)
        self.assertEqual(os.readlink(str(dest / "link.md")), "top.md")
        [journal] = self.journals()
        self.assertEqual(json.loads(journal.read_text())["entries"][0]["method"], "copy")
        with mock.patch.object(apply_staged.os, "rename", side_effect=self.EXDEV):
            code, out = self.run_tool("--rollback", str(journal), wave=None)
        self.assertEqual(code, 0, out)
        self.assertEqual(apply_staged.tree_manifest(str(src)), before)
        self.assertFalse(os.path.lexists(str(dest)))

    def test_file_move_across_devices(self):
        src = self.t("one.md")
        src.write_text("one\n")
        self.ops("12", [{"op": "move", "src": str(src), "dest": str(self.t("two.md")), "wave": "D"}])
        with mock.patch.object(apply_staged.os, "rename", side_effect=self.EXDEV):
            self.assertEqual(self.run_tool(wave="D")[0], 0)
        self.assertEqual(self.t("two.md").read_text(), "one\n")
        self.assertFalse(src.exists())

    def test_failed_verification_keeps_the_source(self):
        src, dest = self.tree()
        self.ops("12", [{"op": "move", "src": str(src), "dest": str(dest), "wave": "D"}])
        real = apply_staged.tree_manifest
        calls = []

        def corrupt(path):
            calls.append(path)
            result = real(path)
            if len(calls) == 2:
                result["top.md"] = ("file", "0" * 64)
            return result

        with mock.patch.object(apply_staged.os, "rename", side_effect=self.EXDEV):
            with mock.patch.object(apply_staged, "tree_manifest", side_effect=corrupt):
                code, out = self.run_tool(wave="D")
        self.assertEqual(code, 1)
        self.assertIn("ERROR: cross-device copy did not verify", out)
        self.assertEqual((src / "top.md").read_text(), "top\n")
        self.assertFalse(os.path.lexists(str(dest)))

    def test_other_rename_errors_are_not_copied(self):
        src, dest = self.tree()
        self.ops("12", [{"op": "move", "src": str(src), "dest": str(dest), "wave": "D"}])
        with mock.patch.object(apply_staged.os, "rename", side_effect=OSError(errno.EACCES, "Permission denied")):
            code, out = self.run_tool(wave="D")
        self.assertEqual(code, 1)
        self.assertIn("ERROR", out)
        self.assertTrue(src.is_dir())
        self.assertFalse(os.path.lexists(str(dest)))


class ExpectAbsentTests(Harness):
    """Spec 7: ``expect_sha256: "absent"`` means the destination must not exist yet."""

    def test_absent_creates_then_skips(self):
        dest = self.t("memory/new-note.md")
        self.ops("12", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "note\n"),
                         "expect_sha256": "absent", "wave": "A"}])
        code, out = self.run_tool("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("WOULD APPLY: +1 -0 lines, new file", out)
        self.assertEqual(self.run_tool()[0], 0)
        self.assertEqual(dest.read_text(), "note\n")
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertIn("SKIP", out)

    def test_absent_conflicts_when_the_file_exists(self):
        dest = self.t("note.md")
        dest.write_text("written by someone else\n")
        self.ops("12", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "note\n"),
                         "expect_sha256": "absent", "wave": "A"}])
        code, out = self.run_tool()
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT: expect_sha256 is absent but the destination exists", out)
        self.assertEqual(dest.read_text(), "written by someone else\n")


class AppliedEarlierTests(Harness):
    """Ticket 12: a write this op installed in an earlier run, since changed by later ops, re-runs as SKIP."""

    def test_guarded_write_changed_later_is_skipped(self):
        dest = self.t("CLAUDE.md")
        dest.write_text("old\n")
        self.ops("09", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "new\n"),
                         "expect_sha256": sha("old\n"), "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        dest.write_text("new\nplus a block from a later op\n")
        code, out = self.run_tool("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("SKIP: applied in run ", out)
        self.assertIn("changed since by later ops or edits", out)
        self.assertEqual(self.run_tool()[0], 0)
        self.assertEqual(dest.read_text(), "new\nplus a block from a later op\n")

    def test_unguarded_write_is_not_reverted(self):
        dest = self.t("research-session.md")
        self.ops("08", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "doc\n"), "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        dest.write_text("doc\nwith a later text op\n")
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertIn("SKIP: applied in run ", out)
        self.assertEqual(dest.read_text(), "doc\nwith a later text op\n")

    def test_rolled_back_write_applies_again(self):
        dest = self.t("note.md")
        dest.write_text("old\n")
        self.ops("01", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "new\n"),
                         "expect_sha256": sha("old\n"), "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        [journal] = self.journals()
        self.assertEqual(self.run_tool("--rollback", str(journal), wave=None)[0], 0)
        self.assertEqual(dest.read_text(), "old\n")
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertIn("APPLY", out)
        self.assertEqual(dest.read_text(), "new\n")

    def test_changed_staged_source_is_not_skipped(self):
        dest = self.t("hooks.py")
        self.ops("06", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "v1\n"), "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        self.stage(dest, "v2\n")
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertNotIn("SKIP", out)
        self.assertEqual(dest.read_text(), "v2\n")

    def test_another_op_with_the_same_dest_does_not_count(self):
        dest = self.t("note.md")
        dest.write_text("old\n")
        self.ops("01", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "new\n"),
                         "expect_sha256": sha("old\n"), "wave": "A"}])
        self.assertEqual(self.run_tool()[0], 0)
        dest.write_text("changed by codex\n")
        self.ops("02", [{"op": "write", "dest": str(dest), "src": self.stage(dest, "new\n"),
                         "expect_sha256": sha("old\n"), "wave": "A"}], slug="other")
        code, out = self.run_tool("--only", "02")
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT", out)


class LintCommandTests(unittest.TestCase):
    def test_default_prefers_staged_cli_then_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            staged = Path(tmp) / "S" / apply_staged.STAGED_CLI_REL
            installed = Path(tmp) / "installed" / "cli.py"
            self.assertIsNone(apply_staged.default_lint_cmd(str(Path(tmp) / "S"), str(installed), "/py"))
            installed.parent.mkdir(parents=True)
            installed.write_text("")
            self.assertEqual(apply_staged.default_lint_cmd(str(Path(tmp) / "S"), str(installed), "/py"),
                             ["/py", "-B", str(installed), "lint"])
            staged.parent.mkdir(parents=True)
            staged.write_text("")
            self.assertEqual(apply_staged.default_lint_cmd(str(Path(tmp) / "S"), str(installed), "/py"),
                             ["/py", "-B", str(staged), "lint"])

    def test_staged_cli_path_matches_the_rs_install_path(self):
        self.assertEqual("/" + apply_staged.STAGED_CLI_REL[len("tree/"):], apply_staged.INSTALLED_CLI)


if __name__ == "__main__":
    unittest.main()
