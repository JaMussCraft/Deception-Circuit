"""Ticket 03: ``findings-check`` (spec 6.3, 6.5; R2, R16, R17)."""

import json
import unittest
from pathlib import Path

from _rs_records import RecordsMixin
from _rs_testlib import RSTestCase

HEAD = ("| id | date | direction | claim | status | commit | evidence | report |\n"
        "|----|------|-----------|-------|--------|--------|----------|--------|\n")
COMMIT = "0123456789abcdef0123456789abcdef01234567"
FROZEN = "a" * 64


class FindingsCheckTest(RecordsMixin, RSTestCase):
    def setUp(self):
        super(FindingsCheckTest, self).setUp()
        self.setup_root(with_templates=False)
        self.write_json_file(self.root / "directions.json", {"schema": 1, "updated": "2026-10-31", "directions": [{
            "id": "sdr", "title": "SDR", "status": "open", "summary": "s", "claimed_by": None, "claimed_at": None,
            "dir": "docs/research/sdr", "updated": "2026-10-31", "frozen_grader_sha256": FROZEN}]})

    def manifest(self, run, seed, commit=COMMIT, grader=None, name="run_manifest.json"):
        p = self.DC / "outputs" / run / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"schema": "run-manifest/1", "git_commit": commit, "seed": seed,
                                 "grader": {"grader_sha256": grader} if grader else None}))
        return "outputs/%s/%s" % (run, name)

    def row(self, fid, status, evidence, commit="0123456"):
        return "| %s | 2026-10-31 | sdr | A claim. | %s | %s | %s | docs/research/sdr/r.md |\n" % (
            fid, status, commit, evidence)

    def check(self, rows, *extra):
        (self.root / "FINDINGS.md").write_text(HEAD + "".join(rows))
        return self.run_cli("findings-check", "--root", str(self.root), *extra)

    def test_replicated_needs_two_distinct_seeds(self):
        a = self.manifest("r1", 1)
        code, out, err = self.check([self.row("F-sdr-001", "replicated", a)])
        self.assertEqual(code, 1)
        self.assertIn("distinct seeds", out)
        b = self.manifest("r2", 1)
        code, out, err = self.check([self.row("F-sdr-001", "replicated", a + "<br>" + b)])
        self.assertEqual(code, 1)
        c = self.manifest("r3", 2)
        code, out, err = self.check([self.row("F-sdr-001", "replicated", a + "<br>" + c)])
        self.assertEqual(code, 0, out)

    def test_verified_needs_a_commit_naming_provenance_file(self):
        a = self.manifest("r1", 1, commit="abc")
        code, out, err = self.check([self.row("F-sdr-001", "verified", a)])
        self.assertEqual(code, 1)
        self.assertIn("40-hex", out)
        code, out, err = self.check([self.row("F-sdr-001", "verified", "outputs/missing/run_manifest.json")])
        self.assertEqual(code, 1)
        self.assertIn("missing", out)
        legacy = self.manifest("old", 1, name="manifest.json")
        code, out, err = self.check([self.row("F-sdr-001", "verified", legacy)])
        self.assertEqual(code, 0, out)
        self.assertIn("legacy manifest.json", out)

    def test_grader_hash_mismatch_fails(self):
        good = self.manifest("g1", 1, grader=FROZEN)
        code, out, err = self.check([self.row("F-sdr-001", "verified", good)])
        self.assertEqual(code, 0, out)
        bad = self.manifest("g2", 1, grader="b" * 64)
        code, out, err = self.check([self.row("F-sdr-001", "verified", bad)])
        self.assertEqual(code, 1)
        self.assertIn("frozen grader", out)

    def test_paper_gate(self):
        a, c = self.manifest("r1", 1), self.manifest("r3", 2)
        rows = [self.row("F-sdr-001", "replicated", a + "<br>" + c), self.row("F-sdr-002", "reviewed", "x.md",
                                                                             commit="pre-manifest")]
        paper = Path(self.tmp) / "draft.md"
        paper.write_text("We show F-sdr-001 holds.\n")
        code, out, err = self.check(rows, "--paper", str(paper))
        self.assertEqual(code, 0, out)
        paper.write_text("We show F-sdr-001 and F-sdr-002.\n")
        code, out, err = self.check(rows, "--paper", str(paper))
        self.assertEqual(code, 1)
        self.assertIn("F-sdr-002, whose status is reviewed", out)


if __name__ == "__main__":
    unittest.main()
