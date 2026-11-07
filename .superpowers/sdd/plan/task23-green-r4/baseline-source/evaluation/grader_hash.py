"""
evaluation/grader_hash.py — one hash for the benchmark grader code (spec §6.3).

`grader_sha256` covers every `evaluation/benchmarks/*.py` file and
`evaluation/benchmark_eval.py`. The canonical form is one line per file,
sorted by relative path:

    <relative posix path>\\t<sha256 of the file>\\n

and the hash is the sha256 of those lines concatenated as UTF-8. It can be
reproduced in a shell with `sha256sum` and `printf`, without Python.

A direction records its frozen value in its `spec.md` and in
`directions.json` (`frozen_grader_sha256`) before its first benchmark run;
`research-session findings-check` errors on evidence whose provenance names a
different value. Evaluation cells that run benchmarks store
`grader_fingerprint(...)` in their `run_manifest.json`.

Usage:

    python evaluation/grader_hash.py            # prints grader_sha256
    python evaluation/grader_hash.py --json     # also the files and judge specs
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

#: The repository root (the parent of evaluation/).
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Grader files, as globs relative to the repository root.
GRADER_GLOBS = ("evaluation/benchmarks/*.py", "evaluation/benchmark_eval.py")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def grader_files(root: str = REPO_ROOT) -> dict:
    """{relative posix path: sha256} for every grader file under `root`."""
    out = {}
    for pattern in GRADER_GLOBS:
        for path in glob.glob(os.path.join(root, pattern)):
            if os.path.isfile(path):
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                out[rel] = _sha256(path)
    return dict(sorted(out.items()))


def grader_sha256(root: str = REPO_ROOT, files=None) -> str:
    """sha256 over the sorted (relative path, sha256) pairs; see the module doc."""
    files = grader_files(root) if files is None else files
    lines = "".join("%s\t%s\n" % (rel, sha) for rel, sha in sorted(files.items()))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def judge_specs(benchmarks) -> dict:
    """{dataset: judge spec} for the selected benchmarks; None for local graders."""
    if not benchmarks:
        return {}
    from evaluation.benchmarks import expand, get_benchmark
    return {name: get_benchmark(name).judge_spec() for name in expand(benchmarks)}


def grader_fingerprint(benchmarks=None, root: str = REPO_ROOT) -> dict:
    """The `grader` block of run_manifest.json (spec §4.6)."""
    files = grader_files(root)
    return {"grader_sha256": grader_sha256(root, files), "files": files,
            "judge_spec": judge_specs(benchmarks)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=REPO_ROOT,
                        help="Repository root to hash (default: this checkout).")
    parser.add_argument("--json", action="store_true",
                        help="Print the hash and the per-file hashes as JSON.")
    args = parser.parse_args(argv)
    files = grader_files(args.root)
    if not files:
        print("no grader files under %s" % args.root, file=sys.stderr)
        return 1
    value = grader_sha256(args.root, files)
    if args.json:
        print(json.dumps({"grader_sha256": value, "files": files}, indent=2))
    else:
        print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
