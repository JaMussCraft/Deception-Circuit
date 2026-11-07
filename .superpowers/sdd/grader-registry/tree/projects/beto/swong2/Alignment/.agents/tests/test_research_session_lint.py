"""Tests for research_session.lint and the ``lint`` subcommand (spec section 5.5).

The tests read only their own fixtures. Synthetic secrets are assembled at run time, so this file never contains a
string that the secret scan would flag.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

AGENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENTS))

from research_session import lint  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "lint"
CLI = AGENTS / "research_session" / "cli.py"


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def words(n, word="alpha"):
    return " ".join([word] * n)


class UnitSplitTests(unittest.TestCase):
    def test_headings_list_items_and_table_rows_are_separate_units(self):
        text = "# Title\nfirst line\nsecond line\n- item one\n  continued\n- item two\n| a | b |\n|---|---|\n| c | d |\n"
        units = lint.split_units(text)
        self.assertEqual([u[0] for u in units], [1, 2, 4, 6, 7, 9])
        self.assertEqual(units[1][1], "first line\nsecond line")
        self.assertEqual(units[2][1], "- item one\n  continued")

    def test_code_comments_frontmatter_and_separators_are_skipped(self):
        text = ("---\nname: x\ndescription: gluedgluedgluedglued1234\n---\n\nprose here\n\n```\nbody2body3 code4code\n"
                "```\n<!-- hidden\nhidden2hidden -->\nafter comment\n|---|:---:|\n")
        units = lint.split_units(text)
        self.assertEqual(units, [(6, "prose here"), (13, "after comment")])

    def test_inline_comment_is_removed(self):
        self.assertEqual(lint.split_units("keep <!-- drop1drop --> this\n"), [(1, "keep   this")])


class TokenTests(unittest.TestCase):
    def test_inline_code_links_and_urls_are_removed(self):
        toks = lint.tokens("See `code1code2code3` and [the note](memory/note1note.md) at https://example.com/a1b2c3d4.")
        self.assertEqual(toks, ["See", "and", "the", "note", "at"])

    def test_tokens_with_path_or_assignment_characters_are_dropped_and_punctuation_stripped(self):
        toks = lint.tokens("a/b c\\d e@f g=h (word), “quoted” —")
        self.assertEqual(toks, ["word", "quoted"])


class LongTokenRuleTests(unittest.TestCase):
    LONG = "abcdefghijklmnopqrst"  # 20 characters

    def test_fails_above_fifteen_percent_in_a_unit_of_eight_or_more(self):
        unit = words(6) + " " + self.LONG + " " + self.LONG  # 2 of 8 = 25%
        self.assertEqual([r for r, _ in lint.check_unit(unit)], ["long-token"])

    def test_exactly_fifteen_percent_passes(self):
        unit = words(17) + " " + " ".join([self.LONG] * 3)  # 3 of 20 = 15%
        self.assertEqual(lint.check_unit(unit), [])

    def test_units_under_eight_tokens_are_exempt(self):
        self.assertEqual(lint.check_unit(" ".join([self.LONG] * 7)), [])

    def test_nineteen_characters_is_not_long(self):
        self.assertEqual(lint.check_unit(words(4) + " " + " ".join([self.LONG[:19]] * 4)), [])


class JoinRuleTests(unittest.TestCase):
    def test_three_joins_pass_and_four_fail(self):
        three = "we saw run12 and 3heads with total7 today"
        four = three + " plus 9layers"
        self.assertEqual(lint.check_unit(three), [])
        self.assertEqual([r for r, _ in lint.check_unit(four)], ["join"])

    def test_two_letter_prefixes_do_not_count(self):
        self.assertEqual(lint.check_unit("at1 on2 L17H24 L24H27 v2 D1 A100 H200 8B"), [])

    def test_allowlist_tokens_are_not_counted(self):
        unit = "sha256 sha1 eval5 bfloat16 float32 uint8 utf8 base64 python3 python3.9 gpuA100x4 gpuH200x8"
        self.assertEqual(lint.join_tokens(lint.tokens(unit)), [])
        self.assertEqual(lint.check_unit(unit), [])

    def test_ticket01_allowlist_additions(self):
        self.assertTrue(lint.is_allowlisted("lane1-public-patterns.md"))
        self.assertTrue(lint.is_allowlisted("cc-plugin-you-should-know"))
        self.assertTrue(lint.is_allowlisted("claude-md-management"))
        # Glue stays counted: a kebab token needs two purely alphabetic parts.
        self.assertFalse(lint.is_allowlisted("locally2026-10-31"))
        self.assertFalse(lint.is_allowlisted("completed1109s"))


class GluedSampleTests(unittest.TestCase):
    def test_memory_line_27_fails(self):
        self.assertTrue(lint.lint_glue(fixture("glued_memory_line27.md")))

    def test_memory_line_29_fails(self):
        self.assertTrue(lint.lint_glue(fixture("glued_memory_line29.md")))

    def test_resume_excerpt_fails_in_at_least_half_its_units(self):
        text = fixture("glued_resume_excerpt.md")
        units = lint.split_units(text)
        failing = [u for u in units if lint.check_unit(u[1])]
        self.assertGreaterEqual(len(units), 4)
        self.assertGreaterEqual(2 * len(failing), len(units))


class CleanSampleTests(unittest.TestCase):
    def test_clean_fixtures_pass(self):
        names = sorted(p.name for p in FIXTURES.glob("clean_*.md"))
        self.assertGreaterEqual(len(names), 5)
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(lint.lint_text(fixture(name)), [])


class LintTextTests(unittest.TestCase):
    """The PreToolUse hook lints Write content and Edit new_string before the write (R30)."""

    def test_lint_text_on_a_string(self):
        glued = fixture("glued_memory_line29.md")
        findings = lint.lint_text("# Heading\n\nA clean sentence about the plan.\n\n" + glued)
        self.assertEqual([(f.line, f.rule) for f in findings], [(5, "join")])
        self.assertEqual(lint.lint_text("A clean sentence about the plan.\n"), [])

    def test_lint_text_can_skip_glue(self):
        self.assertEqual(lint.lint_text(fixture("glued_memory_line29.md"), glue=False), [])


def synthetic_secrets():
    """One synthetic token per pattern of spec 5.5, built so that this source file contains none of them."""
    a36 = "A1b2" * 9
    return {
        "github-token": "gh" + "p_" + a36,
        "github-oauth": "gh" + "o_" + a36,
        "github-user": "gh" + "u_" + a36,
        "github-server": "gh" + "s_" + a36,
        "github-refresh": "gh" + "r_" + a36,
        "github-pat": "github" + "_pat_" + "11ABCDEFG0" + "x" * 30,
        "anthropic-key": "sk" + "-ant-" + "api03-" + "Z9" * 20,
        "openrouter-key": "sk" + "-or-v1-" + "0f" * 32,
        "sk-key": "sk" + "-" + "Q7" * 24,
        "aws-access-key": "AK" + "IA" + "ABCDEFGH23456789",
        "huggingface-token": "hf" + "_" + "Hx" * 17,
        "slack-token": "xo" + "xb-" + "1234567890-abcdefghij",
        "private-key": "-----BEGIN " + "RSA PRIVATE" + " KEY-----",
        "openssh-key": "-----BEGIN " + "OPENSSH PRIVATE" + " KEY-----",
    }


class SecretScanTests(unittest.TestCase):
    def test_every_pattern_is_flagged_and_never_echoed(self):
        for kind, secret in synthetic_secrets().items():
            with self.subTest(kind=kind):
                text = "intro line\nvalue: " + secret + " trailing\n"
                findings = lint.scan_secrets(text)
                self.assertEqual(len(findings), 1, findings)
                self.assertEqual((findings[0].line, findings[0].rule), (2, "secret"))
                self.assertNotIn(secret, findings[0].excerpt)
                self.assertNotIn(secret[4:20], lint.format_finding("x.md", findings[0]))

    def test_secret_in_code_block_is_flagged(self):
        secret = synthetic_secrets()["github-token"]
        self.assertEqual(len(lint.lint_text("```\n" + secret + "\n```\n")), 1)

    def test_prefix_names_in_documentation_are_not_flagged(self):
        doc = ("Fail on `ghp_` or gh[osur]_ plus 36 alphanumerics, github_pat_, sk-ant-, sk-or-v1-, sk- plus 32, "
               "AKIA plus 16, hf_ plus 30, xoxb- and private-key headers. The task-runner and risk-based checks.\n")
        self.assertEqual(lint.scan_secrets(doc), [])

    def test_clean_fixtures_have_no_secrets(self):
        for path in FIXTURES.glob("clean_*.md"):
            self.assertEqual(lint.scan_secrets(path.read_text(encoding="utf-8")), [], path.name)


class ScopeTests(unittest.TestCase):
    def test_glue_scope(self):
        self.assertTrue(lint.glue_in_scope("/x/Deception-Circuit/docs/research/sdr/WORKLOG.md"))
        self.assertTrue(lint.glue_in_scope("/r/.agents/memory/MEMORY.md", alignment_root="/r"))
        self.assertFalse(lint.glue_in_scope("/x/Deception-Circuit/docs/research/sdr/reports/01-handback.md"))
        self.assertFalse(lint.glue_in_scope("/r/.agents/memory/notes.json", alignment_root="/r"))

    def test_secret_scope(self):
        self.assertTrue(lint.secret_in_scope("/r/a/b.md", alignment_root="/r"))
        self.assertFalse(lint.secret_in_scope("/rr/a.md", alignment_root="/r"))


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, "-B", str(CLI), "lint"] + list(args), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, universal_newlines=True, env=env)

    def test_clean_file_exits_zero_and_prints_nothing(self):
        result = self.run_cli(str(FIXTURES / "clean_lane4_section0.md"))
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_glued_file_exits_one_with_path_line_rule_excerpt(self):
        path = str(FIXTURES / "glued_memory_line29.md")
        result = self.run_cli(path)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.startswith(path + ":1: join: "), result.stdout)

    def test_secret_output_is_redacted(self):
        secret = synthetic_secrets()["anthropic-key"]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "note.md")
            with open(path, "w") as fh:
                fh.write("A clean line.\nkey " + secret + "\n")
            result = self.run_cli("--secrets-only", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn(":2: secret: anthropic-key match redacted", result.stdout)
        self.assertNotIn(secret[7:], result.stdout + result.stderr)

    def test_missing_file_exits_two(self):
        self.assertEqual(self.run_cli("/nonexistent/research-session/lint.md").returncode, 2)


if __name__ == "__main__":
    unittest.main()
