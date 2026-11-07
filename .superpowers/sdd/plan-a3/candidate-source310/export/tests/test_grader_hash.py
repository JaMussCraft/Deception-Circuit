"""evaluation/grader_hash.py: one stable hash over the benchmark grader code (spec §6.3)."""

from __future__ import annotations

import hashlib
import os
import shutil

from evaluation import grader_hash as G


def copy_grader_tree(dest):
    """A temporary copy of exactly the files the hash covers, plus a bystander."""
    files = G.grader_files()
    for rel in files:
        target = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(os.path.join(G.REPO_ROOT, rel), target)
    bystander = os.path.join(dest, "evaluation", "suite.py")
    with open(bystander, "w") as f:
        f.write("# not grader code\n")
    return sorted(files)


def test_the_listed_files_are_the_benchmark_modules_and_benchmark_eval():
    files = G.grader_files()
    assert "evaluation/benchmark_eval.py" in files
    for name in ("base", "judge", "judge_budget", "liars_bench", "mask_bench",
                 "notebook", "sandbagging", "sources", "__init__"):
        assert "evaluation/benchmarks/%s.py" % name in files
    assert all(rel.startswith("evaluation/") and rel.endswith(".py") for rel in files)
    assert list(files) == sorted(files)


def test_the_hash_is_the_documented_canonical_form():
    files = G.grader_files()
    lines = "".join("%s\t%s\n" % (rel, files[rel]) for rel in sorted(files))
    assert G.grader_sha256() == hashlib.sha256(lines.encode()).hexdigest()
    for rel, sha in files.items():
        with open(os.path.join(G.REPO_ROOT, rel), "rb") as f:
            assert sha == hashlib.sha256(f.read()).hexdigest()


def test_the_hash_is_stable_across_calls_and_copies(tmp_path):
    copy_grader_tree(str(tmp_path))
    assert G.grader_sha256() == G.grader_sha256()
    assert G.grader_sha256(str(tmp_path)) == G.grader_sha256()


def test_the_hash_changes_when_any_listed_file_changes(tmp_path):
    rels = copy_grader_tree(str(tmp_path))
    root = str(tmp_path)
    original = G.grader_sha256(root)
    seen = {original}
    for rel in rels:
        path = os.path.join(root, rel)
        with open(path, "rb") as f:
            before = f.read()
        with open(path, "ab") as f:
            f.write(b"\n# edited\n")
        changed = G.grader_sha256(root)
        assert changed != original, rel
        assert changed not in seen, rel
        seen.add(changed)
        with open(path, "wb") as f:
            f.write(before)
        assert G.grader_sha256(root) == original


def test_unlisted_files_do_not_change_the_hash(tmp_path):
    copy_grader_tree(str(tmp_path))
    root = str(tmp_path)
    original = G.grader_sha256(root)
    with open(os.path.join(root, "evaluation", "suite.py"), "a") as f:
        f.write("x = 1\n")
    os.makedirs(os.path.join(root, "evaluation", "benchmarks", "__pycache__"))
    with open(os.path.join(root, "evaluation", "benchmarks", "__pycache__", "base.pyc"), "wb") as f:
        f.write(b"\0")
    assert G.grader_sha256(root) == original


def test_adding_or_removing_a_benchmark_module_changes_the_hash(tmp_path):
    copy_grader_tree(str(tmp_path))
    root = str(tmp_path)
    original = G.grader_sha256(root)
    extra = os.path.join(root, "evaluation", "benchmarks", "new_bench.py")
    with open(extra, "w") as f:
        f.write("")
    assert G.grader_sha256(root) != original
    os.remove(extra)
    assert G.grader_sha256(root) == original


def test_fingerprint_and_cli(capsys):
    fp = G.grader_fingerprint(["sandbagging"])
    assert fp["grader_sha256"] == G.grader_sha256()
    assert fp["files"] == G.grader_files()
    assert fp["judge_spec"] == {"sandbagging": None}
    assert G.grader_fingerprint()["judge_spec"] == {}
    assert G.main([]) == 0
    assert capsys.readouterr().out.strip() == G.grader_sha256()


def test_cli_refuses_a_root_without_grader_files(tmp_path):
    assert G.main(["--root", str(tmp_path)]) == 1
