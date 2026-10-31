"""Tests for migrate_scratch.py (ticket 10). Stdlib only; run on Python 3.9 and 3.12.

Every test builds a fixture tree in a temporary directory: an Alignment root with ``.scratch``, a DC checkout with
``outputs/_studies`` and ``docs/research``, a worktree ``docs/research`` with ``directions.json`` and the feature
directory, a staging root and a backup root. The simulated apply runs the real ``apply_staged.py`` on that staging
root. Only the RS secret scan is read from outside the fixture (the installed package, else the staged one).
"""

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import apply_staged  # noqa: E402
import migrate_scratch  # noqa: E402

RS_CANDIDATES = ["/projects/beto/swong2/Alignment/.agents",
                 "/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/tree/projects/beto/swong2/Alignment/.agents"]
RS_PARENT = next((p for p in RS_CANDIDATES if os.path.isfile(os.path.join(p, "research_session", "lint.py"))), None)

FAKE_TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0" + "K1l2M3n4O5p6Q7r8"  # 36 characters after the prefix; not a real token
OLD = time.time() - 3 * 86400


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_hashes(root):
    """Relative path -> sha256 (files) or 'link:<target>' (symlinks), not following symlinks."""
    out = {}
    root = str(root)
    for cur, dnames, fnames in os.walk(root):
        for n in dnames + fnames:
            p = os.path.join(cur, n)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                out[rel] = "link:" + os.readlink(p)
            elif os.path.isfile(p):
                out[rel] = sha(p)
    return out


def age(root, when=OLD):
    """Set every mtime under ``root`` (and ``root`` itself) to ``when``."""
    for cur, dnames, fnames in os.walk(str(root)):
        for n in dnames + fnames:
            os.utime(os.path.join(cur, n), (when, when), follow_symlinks=False)
    os.utime(str(root), (when, when))


def row(rid, scratch, archive=None):
    return {"id": rid, "title": "T " + rid, "status": "done", "summary": "S.", "claimed_by": None,
            "claimed_at": None, "dir": "docs/research/" + rid, "updated": "2026-10-30",
            "legacy_scratch": [".scratch/" + s for s in scratch], "archive": list(archive or [])}


@unittest.skipIf(RS_PARENT is None, "RS lint module not found")
class Harness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        r = Path(self._tmp.name)
        self.alignment = r / "Alignment"
        self.scratch = self.alignment / ".scratch"
        self.scratch.mkdir(parents=True)
        self.dc = self.alignment / "Deception-Circuit"
        self.studies = self.dc / "outputs" / "_studies"
        self.studies.mkdir(parents=True)
        (self.dc / "docs" / "research" / "autoresearch-workflow").mkdir(parents=True)
        self.docs = r / "W" / "docs" / "research"
        self.feature = self.docs / "autoresearch-workflow"
        (self.feature / "reports").mkdir(parents=True)
        self.staging = r / "S"
        self.backups = r / "backups"
        self.apply_backups = r / "apply-backups"
        rows = [row("alpha-dir", ["alpha"]), row("beta-dir", ["beta"]),
                row("sdr-mechanism", ["sdr-x"]),
                row("selective-deception", ["selective-deception"], ["outputs/_studies/selective-deception/study"]),
                row("autoresearch-workflow", ["autoresearch-workflow"])]
        (self.docs / "directions.json").write_text(json.dumps({"schema": 1, "updated": "2026-10-30",
                                                               "directions": rows}, indent=2, sort_keys=True) + "\n")

    def tearDown(self):
        self._tmp.cleanup()

    # -- fixture helpers

    def make(self, slug, files, link=None):
        base = self.scratch / slug
        for rel, content in files.items():
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content if isinstance(content, bytes) else content.encode())
        if link:
            os.symlink(link[1], str(base / link[0]))
        (base / "empty-dir").mkdir(exist_ok=True)
        age(base)
        return base

    def common(self):
        return ["--alignment", str(self.alignment), "--dc", str(self.dc), "--docs-root", str(self.docs),
                "--feature-dir", str(self.feature), "--staging", str(self.staging), "--backup-root",
                str(self.backups), "--rs-parent", RS_PARENT, "--date", "2026-10-31"]

    def plan(self, *slugs, extra=()):
        argv = ["plan"] + self.common() + ["--include", ",".join(slugs)] + list(extra)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate_scratch.main(argv)
        return code, out.getvalue()

    def verify(self, wave="B"):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate_scratch.main(["verify"] + self.common() + ["--wave", wave])
        return code, out.getvalue()

    def apply(self, wave="B", dry=False):
        argv = ["--staging", str(self.staging), "--wave", wave, "--only", "10", "--backup-root",
                str(self.apply_backups)] + (["--dry-run"] if dry else [])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = apply_staged.main(argv)
        return code, out.getvalue()

    def ops(self, wave="B"):
        p = self.staging / "ops" / ("10-migration-%s.json" % wave.lower())
        return json.loads(p.read_text())["ops"] if p.exists() else None

    def provenance(self, direction, slug):
        return json.loads((self.docs / direction / "scratch-copy" / slug / "provenance.json").read_text())


class ArchiveTests(Harness):
    def alpha(self):
        return self.make("alpha", {"README.md": "# a\n", "reports/r1.md": "report\n", "reviews/deep/x.md": "x\n",
                                   "handbacks/h.md": "h\n", "data.json": '{"k": 1}\n', "bin/blob.pt": b"\x00\x01\xff"},
                         link=("pointer.md", "README.md"))

    def test_archive_move_symlink_and_byte_identity(self):
        src = self.alpha()
        before = tree_hashes(src)
        inode = os.stat(str(src)).st_ino
        code, out = self.plan("alpha")
        self.assertEqual(code, 0, out)
        archive = self.studies / "alpha" / "scratch"
        self.assertEqual(self.ops("B"), [
            {"op": "mkdir", "path": str(self.studies / "alpha"), "wave": "B"},
            {"op": "move", "src": str(src), "dest": str(archive), "wave": "B"},
            {"op": "symlink", "path": str(src), "target": str(archive), "wave": "B"}])
        self.assertTrue(src.is_dir() and not src.is_symlink(), "plan must not move anything")
        code, out = self.apply("B")
        self.assertEqual(code, 0, out)
        self.assertTrue(src.is_symlink())
        self.assertEqual(os.readlink(str(src)), str(archive))
        self.assertEqual(os.stat(str(archive)).st_ino, inode, "the move must be a rename")
        self.assertEqual(tree_hashes(archive), before)
        code, out = self.verify("B")
        self.assertEqual(code, 0, out)
        self.assertIn("alpha: applied", out)

    def test_verify_before_apply_and_after_one_byte_change(self):
        self.alpha()
        self.plan("alpha")
        code, out = self.verify("B")
        self.assertEqual(code, 0, out)
        self.assertIn("not applied yet", out)
        self.apply("B")
        target = self.studies / "alpha" / "scratch" / "data.json"
        with open(str(target), "ab") as fh:
            fh.write(b" ")
        code, out = self.verify("B")
        self.assertEqual(code, 1)
        self.assertIn("changed data.json", out)

    def test_verify_fails_when_a_copy_changes(self):
        self.alpha()
        self.plan("alpha")
        copy = self.docs / "alpha-dir" / "scratch-copy" / "alpha" / "README.md"
        copy.write_text("# b\n")
        code, out = self.verify("B")
        self.assertEqual(code, 1)
        self.assertIn("markdown copy README.md", out)

    def test_destination_exists_is_refused(self):
        self.alpha()
        (self.studies / "alpha" / "scratch").mkdir(parents=True)
        code, out = self.plan("alpha")
        self.assertEqual(code, 1)
        self.assertIn("archive destination already exists", out)
        self.assertIsNone(self.ops("B"))

    def test_twelve_hour_skip(self):
        src = self.alpha()
        now = time.time()
        os.utime(str(src / "reviews" / "deep" / "x.md"), (now - 3600, now - 3600))
        code, out = self.plan("alpha")
        self.assertEqual(code, 0, out)
        self.assertIn("skipped", out)
        self.assertIn("12-hour rule", out)
        self.assertIsNone(self.ops("B"))
        self.assertFalse((self.docs / "alpha-dir" / "scratch-copy").exists())

    def test_report_only_writes_nothing(self):
        self.alpha()
        code, out = self.plan("alpha", extra=["--report-only"])
        self.assertEqual(code, 0, out)
        self.assertIn("report only", out)
        self.assertFalse(self.staging.exists())
        self.assertFalse((self.docs / "alpha-dir").exists())
        reg = json.loads((self.docs / "directions.json").read_text())
        self.assertEqual(reg["directions"][0]["archive"], [])

    def test_registry_gets_archive_path(self):
        self.alpha()
        self.make("beta", {"b.md": "b\n"})
        code, out = self.plan("alpha", "beta")
        self.assertEqual(code, 0, out)
        reg = json.loads((self.docs / "directions.json").read_text())
        by = dict((r["id"], r) for r in reg["directions"])
        self.assertEqual(by["alpha-dir"]["archive"], ["outputs/_studies/alpha/scratch"])
        self.assertEqual(by["beta-dir"]["archive"], ["outputs/_studies/beta/scratch"])
        self.assertEqual(by["alpha-dir"]["updated"], "2026-10-31")
        self.assertEqual(by["sdr-mechanism"]["archive"], [])
        self.assertEqual(len(self.ops("B")), 6)
        code, out = self.plan("alpha", "beta")
        reg2 = json.loads((self.docs / "directions.json").read_text())
        self.assertEqual(reg, reg2, "a second plan must not duplicate archive entries")


class R28Tests(Harness):
    def test_refused_without_override(self):
        self.make("sdr-x", {"spec.md": "s\n"})
        code, out = self.plan("sdr-x")
        self.assertEqual(code, 1)
        self.assertIn("refused", out)
        self.assertIn("R28", out)
        self.assertFalse((self.staging / "ops").exists())
        self.assertFalse((self.docs / "sdr-mechanism").exists())

    def test_mixed_include_refuses_only_the_protected_one(self):
        self.make("sdr-x", {"spec.md": "s\n"})
        self.make("beta", {"b.md": "b\n"})
        code, out = self.plan("beta", "sdr-x")
        self.assertEqual(code, 1)
        ops = self.ops("B")
        self.assertEqual(len(ops), 3)
        self.assertFalse(any("sdr-x" in json.dumps(op) for op in ops))
        self.assertIsNone(self.ops("D"))

    def test_override_writes_wave_d_ops_only(self):
        src = self.make("sdr-x", {"spec.md": "s\n", "issues/01.md": "i\n"})
        code, out = self.plan("sdr-x", extra=["--confirmed-live-session-finished"])
        self.assertEqual(code, 0, out)
        self.assertIsNone(self.ops("B"))
        ops = self.ops("D")
        self.assertEqual([op["wave"] for op in ops], ["D", "D", "D"])
        code, out = self.apply("B")
        self.assertIn("0 op(s) selected", out)
        self.assertTrue(src.is_dir() and not src.is_symlink())
        code, out = self.apply("D")
        self.assertEqual(code, 0, out)
        self.assertTrue(src.is_symlink())
        code, out = self.verify("D")
        self.assertEqual(code, 0, out)

    def test_already_archived_gets_copy_only(self):
        study = self.studies / "selective-deception" / "study"
        (study / "reports").mkdir(parents=True)
        (study / "README.md").write_text("r\n")
        (study / "reports" / "x.md").write_text("x\n")
        (study / "rows.json").write_text("[]\n")
        age(study)
        os.symlink(str(study), str(self.scratch / "selective-deception"))
        code, out = self.plan("selective-deception")
        self.assertEqual(code, 1)
        code, out = self.plan("selective-deception", extra=["--confirmed-live-session-finished"])
        self.assertEqual(code, 0, out)
        self.assertIsNone(self.ops("D"))
        prov = self.provenance("selective-deception", "selective-deception")
        self.assertEqual(sorted(c["path"] for c in prov["copies"]), ["README.md", "reports/x.md"])
        self.assertEqual(prov["archive"], "outputs/_studies/selective-deception/study")
        self.assertEqual(prov["archive_only"], {"files": 1, "bytes": 3})
        code, out = self.verify("D")
        self.assertEqual(code, 0, out)


class MarkdownTests(Harness):
    def test_selection_at_any_depth(self):
        self.make("alpha", {"a.md": "a\n", "reports/b.md": "b\n", "reviews/c.md": "c\n", "handbacks/d.md": "d\n",
                            "x/y/z/e.md": "e\n", "f.json": "{}\n", "g.txt": "g\n", "h.MD.bak": "h\n"})
        code, out = self.plan("alpha")
        self.assertEqual(code, 0, out)
        prov = self.provenance("alpha-dir", "alpha")
        self.assertEqual(sorted(c["path"] for c in prov["copies"]),
                         ["a.md", "handbacks/d.md", "reports/b.md", "reviews/c.md", "x/y/z/e.md"])
        for c in prov["copies"]:
            self.assertEqual(c["archive_path"], "outputs/_studies/alpha/scratch/" + c["path"])
            self.assertEqual(sha(self.docs / "alpha-dir" / "scratch-copy" / "alpha" / c["path"]), c["sha256"])
        self.assertEqual(prov["archive_only"], {"files": 3, "bytes": 7})
        self.assertFalse((self.docs / "alpha-dir" / "scratch-copy" / "alpha" / "f.json").exists())

    def test_dot_directories_are_skipped(self):
        # Ticket 12: a pytest cache README was copied from component-analysis; tool caches are not research notes.
        self.make("alpha", {"a.md": "a\n", ".pytest_cache/README.md": "cache\n", "x/.hidden/b.md": "b\n",
                            ".notes.md": "n\n"})
        code, out = self.plan("alpha")
        self.assertEqual(code, 0, out)
        prov = self.provenance("alpha-dir", "alpha")
        self.assertEqual(sorted(c["path"] for c in prov["copies"]), [".notes.md", "a.md"])
        self.assertFalse((self.docs / "alpha-dir" / "scratch-copy" / "alpha" / ".pytest_cache").exists())
        self.assertEqual(prov["archive_only"], {"files": 2, "bytes": 8})

    def test_both_size_caps_with_exclusions_reported(self):
        files = {"big.md": "x" * (migrate_scratch.FILE_CAP + 1)}
        chunk = 190 * 1024
        for i in range(9):  # 9 x 190 KB = 1710 KB > 1536 KB: the last ones hit the directory cap
            files["notes/n%d.md" % i] = chr(ord("a") + i) * chunk
        files["small.md"] = "s\n"
        self.make("alpha", files)
        code, out = self.plan("alpha")
        self.assertEqual(code, 0, out)
        prov = self.provenance("alpha-dir", "alpha")
        reasons = dict((e["path"], e["reason"]) for e in prov["excluded_by_caps"])
        self.assertEqual(reasons["big.md"], "file-cap")
        dir_capped = sorted(p for p, r in reasons.items() if r == "dir-cap")
        self.assertEqual(dir_capped, ["notes/n8.md"])
        copied = sum(c["bytes"] for c in prov["copies"])
        self.assertLessEqual(copied, migrate_scratch.DIR_CAP)
        self.assertIn("small.md", [c["path"] for c in prov["copies"]])
        self.assertIn("excluded (file-cap): big.md", out)
        self.assertIn("excluded (dir-cap): notes/n8.md", out)
        for e in prov["excluded_by_caps"]:
            self.assertFalse((self.docs / "alpha-dir" / "scratch-copy" / "alpha" / e["path"]).exists())
            self.assertGreater(e["bytes"], 0)
        self.assertEqual(prov["archive_only"]["files"], 2)

    def test_planted_token_blocks_that_copy(self):
        self.make("alpha", {"clean.md": "fine\n", "reports/leak.md": "line one\nremote " + FAKE_TOKEN + "\n"})
        code, out = self.plan("alpha")
        self.assertEqual(code, 0, out)
        self.assertNotIn(FAKE_TOKEN, out)
        self.assertIn("secret scan blocked: reports/leak.md (github-token; lines 2)", out)
        copy_dir = self.docs / "alpha-dir" / "scratch-copy" / "alpha"
        self.assertFalse((copy_dir / "reports" / "leak.md").exists())
        self.assertTrue((copy_dir / "clean.md").exists())
        prov_text = (copy_dir / "provenance.json").read_text()
        self.assertNotIn(FAKE_TOKEN, prov_text)
        prov = json.loads(prov_text)
        self.assertEqual(prov["blocked_by_secret_scan"][0]["path"], "reports/leak.md")
        self.assertEqual(prov["blocked_by_secret_scan"][0]["patterns"], ["github-token"])
        records = (self.staging / "records" / "10-migration-b.json").read_text()
        self.assertNotIn(FAKE_TOKEN, records)

    def test_missing_scanner_fails_closed(self):
        self.make("alpha", {"a.md": "a\n"})
        argv = ["plan"] + self.common() + ["--include", "alpha"]
        argv[argv.index("--rs-parent") + 1] = str(self.alignment / "nowhere")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = migrate_scratch.main(argv)
        self.assertEqual(code, 2)
        self.assertIn("secret scan unavailable", err.getvalue())
        self.assertFalse(self.staging.exists())


class AutoresearchTests(Harness):
    def seed_feature(self):
        (self.feature / "reports" / "lane1.md").write_text("lane one\n")
        (self.feature / "reports" / "proposal-full.md").write_text("proposal\n")

    def test_all_matched_backup_stash_and_link(self):
        self.seed_feature()
        src = self.make("autoresearch-workflow", {"lane1.md": "lane one\n", "proposal-full.md": "proposal\n"})
        now = time.time()
        os.utime(str(src / "lane1.md"), (now, now))  # fresh: autoresearch-workflow is exempt from the 12-hour rule
        before = tree_hashes(src)
        code, out = self.plan("autoresearch-workflow")
        self.assertEqual(code, 0, out)
        self.assertIn("2 file(s) with a sha256 twin in F, 0 without", out)
        ops = self.ops("B")
        self.assertEqual([op["op"] for op in ops], ["write", "write", "mkdir", "move", "symlink"])
        link_target = str(self.dc / "docs" / "research" / "autoresearch-workflow")
        self.assertEqual(ops[-1], {"op": "symlink", "path": str(src), "target": link_target, "wave": "B"})
        self.assertFalse((self.feature.parent / "autoresearch-workflow" / "scratch-copy").exists())
        code, out = self.apply("B")
        self.assertEqual(code, 0, out)
        self.assertEqual(os.readlink(str(src)), link_target)
        backup = self.backups / migrate_scratch.AR_BACKUP_NAME
        self.assertEqual(sha(backup / "lane1.md"), before["lane1.md"])
        self.assertEqual(sha(backup / "proposal-full.md"), before["proposal-full.md"])
        stash = self.studies / "autoresearch-workflow" / migrate_scratch.AR_STASH_NAME
        self.assertEqual(tree_hashes(stash), before)
        code, out = self.verify("B")
        self.assertEqual(code, 0, out)

    def test_unmatched_file_is_listed_and_kept(self):
        self.seed_feature()
        src = self.make("autoresearch-workflow", {"lane1.md": "lane one\n", "orphan.md": "only here\n"})
        code, out = self.plan("autoresearch-workflow")
        self.assertEqual(code, 1)
        self.assertIn("blocked", out)
        self.assertIn("kept, no twin: orphan.md", out)
        self.assertIsNone(self.ops("B"))
        self.assertTrue((src / "orphan.md").exists())
        self.assertTrue((src / "lane1.md").exists())


if __name__ == "__main__":
    unittest.main()
