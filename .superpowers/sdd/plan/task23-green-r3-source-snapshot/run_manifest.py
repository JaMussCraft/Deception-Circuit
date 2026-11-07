"""
run_manifest.py — commit-stamped provenance for training runs and evaluation cells.

Every run directory that `run_io.make_run_dir` creates, and every evaluation
cell that `evaluation.suite.run_cell` starts, gets a `run_manifest.json`
(spec §4.6 and §6.1 of docs/research/autoresearch-workflow/spec.md). The name
is not `manifest.json` because that name already means a frozen input
manifest elsewhere in this repository (`evaluate_native_sparse.py`,
`evaluation/generation_checkpoint.py`, the SDR scripts).

Field names reuse the SDR routing pilot's manifest
(`scripts/sdr_routing_pilot.py`): `git_commit`, `dirty_diff_hash`,
`code_sha256`, `software`, `model_revision` and `manifest_hash`, with a
10-second bound on each git call and `git_fingerprint_error` when git cannot
answer. The fields `git_dirty`, `config_sha256`, `dataset_files` and `seed`
are new in spec §4.6.

Rules:

* The writer never overwrites a `run_manifest.json` whose content differs. It
  writes `run_manifest.1.json`, `run_manifest.2.json` and so on instead, and
  prints which file it wrote. Identical content is left alone.
* `DC_RUN_MANIFEST_GIT=0` skips every git call and records
  `git_fingerprint_error: "disabled"`. The test suite sets it in
  `conftest.py`, so tests that reach `make_run_dir` never shell out to git on
  Lustre.
* `git_dirty` is whether `git diff HEAD` (tracked files only) is non-empty;
  untracked files do not count. `dirty_diff_hash` is the sha256 of that diff
  when it is non-empty and null otherwise.
* `direction` is the environment variable `RESEARCH_DIRECTION` when set.
* `manifest_hash` is the sha256 of the canonical JSON (sorted keys, compact
  separators) of the manifest without its `manifest_hash` key, as in the
  pilot. `verify_manifest_hash` recomputes it.
* Nothing here may stop a run: callers wrap `write_run_manifest` and print a
  warning when it raises.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime

SCHEMA = "run-manifest/1"
FILENAME = "run_manifest.json"
GIT_TIMEOUT_SECONDS = 10
GIT_ENV_FLAG = "DC_RUN_MANIFEST_GIT"
DIRECTION_ENV = "RESEARCH_DIRECTION"

#: The repository root: the directory holding this file.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

#: Files hashed into `dataset_files` when a dataset directory is walked.
DATA_SUFFIXES = (".json", ".jsonl", ".csv", ".tsv", ".arrow", ".parquet", ".txt")

#: Packages whose versions go into `software`.
SOFTWARE_PACKAGES = ("torch", "transformers", "nnsight")


# ==============================================================================
# HASHING
# ==============================================================================

def digest(value) -> str:
    """sha256 of bytes, or of the canonical JSON of any other value."""
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_hash(manifest: dict) -> str:
    return digest({k: v for k, v in manifest.items() if k != "manifest_hash"})


def verify_manifest_hash(manifest: dict) -> bool:
    return manifest.get("manifest_hash") == manifest_hash(manifest)


# ==============================================================================
# FINGERPRINTS
# ==============================================================================

def _run_git(args, cwd) -> bytes:
    """One bounded git call. Tests patch `subprocess.check_output`."""
    return subprocess.check_output(["git"] + list(args), cwd=cwd,
                                   timeout=GIT_TIMEOUT_SECONDS,
                                   stderr=subprocess.DEVNULL)


def git_fingerprint(repo_root: str = REPO_ROOT) -> dict:
    """-> git_commit, git_dirty, dirty_diff_hash, and git_fingerprint_error on failure.

    The environment flag is read at call time, so a test that unsets it sees
    the change.
    """
    if os.environ.get(GIT_ENV_FLAG, "1").strip() == "0":
        return {"git_commit": None, "git_dirty": None, "dirty_diff_hash": None,
                "git_fingerprint_error": "disabled"}
    try:
        commit = _run_git(["rev-parse", "HEAD"], repo_root).decode().strip()
        diff = _run_git(["diff", "HEAD", "--no-ext-diff"], repo_root)
    except (OSError, subprocess.SubprocessError) as error:
        return {"git_commit": None, "git_dirty": None, "dirty_diff_hash": None,
                "git_fingerprint_error": "unavailable (%ds bound): %s"
                                         % (GIT_TIMEOUT_SECONDS, type(error).__name__)}
    dirty = bool(diff.strip())
    return {"git_commit": commit, "git_dirty": dirty,
            "dirty_diff_hash": digest(diff) if dirty else None}


def software_versions() -> dict:
    versions = {"python": platform.python_version()}
    for name in SOFTWARE_PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def hf_hub_caches() -> list:
    """Candidate Hugging Face hub cache directories, in the order they are tried.

    The explicit hub variables first, then `TRANSFORMERS_CACHE` (still set on
    Delta, where it points at the cache root), then `$HF_HOME/hub`.
    """
    out = [os.environ.get(name) for name in
           ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE")]
    home = os.environ.get("HF_HOME") or os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "huggingface")
    out.append(os.path.join(home, "hub"))
    return [p for p in out if p]


def model_revision(model, hub_cache=None):
    """Snapshot directory name of `model` in the local hub cache, without loading it.

    `model` is a registry name (`llama-8b-instruct`) or a hub id. The first
    cache holding `models--<org>--<name>/refs/main` answers. Returns None when
    no cache has an entry; this never raises.
    """
    if not model:
        return None
    hf_id = model
    try:
        from models import MODEL_REGISTRY
        hf_id = MODEL_REGISTRY.get(model, (model,))[0]
    except Exception:                                       # noqa: BLE001
        pass
    for root in ([hub_cache] if hub_cache else hf_hub_caches()):
        try:
            ref = os.path.join(root, "models--" + str(hf_id).replace("/", "--"),
                               "refs", "main")
            with open(ref) as f:
                value = f.read().strip()
        except (OSError, ValueError, TypeError):
            continue
        if value:
            return value
    return None


def _relative_key(path: str, root: str = REPO_ROOT) -> str:
    absolute = os.path.abspath(path)
    try:
        rel = os.path.relpath(absolute, root)
    except ValueError:
        return absolute
    return absolute if rel.startswith("..") else rel.replace(os.sep, "/")


def code_hashes(paths, root: str = REPO_ROOT) -> dict:
    out = {}
    for path in paths or ():
        if path and os.path.isfile(path):
            out[_relative_key(path, root)] = file_sha256(path)
    return out


def hash_files(paths) -> dict:
    """{path as given, normalised: sha256} for existing files."""
    out = {}
    for path in paths or ():
        if path and os.path.isfile(path):
            out[os.path.normpath(path).replace(os.sep, "/")] = file_sha256(path)
    return out


def data_files_under(directory: str) -> list:
    """Data files below `directory`, sorted; [] when it does not exist."""
    found = []
    if not directory or not os.path.isdir(directory):
        return found
    for base, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "__pycache__")
        for name in sorted(files):
            if name.endswith(DATA_SUFFIXES) and not name.startswith("."):
                found.append(os.path.join(base, name))
    return found


def dataset_dirs_for_args(args) -> list:
    """The dataset directories a training or evaluation run reads, from its args.

    Deception tasks expose `dataset_dir(args)`; STD reads `std_<variant>`; the
    other tasks read `<data_dir>/<task>`. A joint run lists each subtask.
    """
    data_dir = getattr(args, "data_dir", None)
    task = getattr(args, "task", None)
    if not data_dir or not task:
        return []
    names = list(getattr(args, "joint_tasks", None) or ()) if task == "joint" else [task]
    dirs = []
    for name in names:
        directory = None
        try:
            from tasks import get_task
            instance = get_task(name)
            if hasattr(instance, "dataset_dir"):
                directory = instance.dataset_dir(args)
        except Exception:                                   # noqa: BLE001
            directory = None
        if directory is None:
            if name == "std":
                directory = os.path.join(data_dir, "std_%s" % getattr(args, "std_variant", None))
            else:
                directory = os.path.join(data_dir, name)
        dirs.append(directory)
    return dirs


def dataset_files_for_args(args) -> dict:
    files = []
    for directory in dataset_dirs_for_args(args):
        files.extend(data_files_under(directory))
    return hash_files(files)


def now_chicago() -> str:
    """ISO time with the America/Chicago offset (spec R22), else the local zone."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds")
    except Exception:                                       # noqa: BLE001
        return datetime.now().astimezone().isoformat(timespec="seconds")


# ==============================================================================
# BUILD AND WRITE
# ==============================================================================

def build_run_manifest(*, script=None, argv=None, cwd=None, config_path=None,
                       dataset_files=None, model=None, model_revision_value=None,
                       seed=None, grader=None, code_files=None, created=None,
                       repo_root: str = REPO_ROOT, hub_cache=None) -> dict:
    """The §4.6 record. Every field is present on every path.

    script        entry script path; default `sys.argv[0]`. The `script` field
                  is its base name and `code_sha256` hashes it.
    dataset_files a {path: sha256} mapping, or an iterable of paths to hash.
    model_revision_value
                  overrides the hub-cache lookup of `model`.
    grader        `evaluation.grader_hash.grader_fingerprint(...)` or None.
    created       a fixed timestamp, for tests; default now in America/Chicago.
    """
    script = script if script is not None else (sys.argv[0] if sys.argv else "")
    if isinstance(dataset_files, dict):
        datasets = {str(k): v for k, v in dataset_files.items()}
    else:
        datasets = hash_files(dataset_files)
    manifest = {
        "schema": SCHEMA,
        "created": created or now_chicago(),
        "script": os.path.basename(script) if script else None,
        "argv": list(sys.argv if argv is None else argv),
        "cwd": os.path.abspath(cwd or os.getcwd()),
        "code_sha256": code_hashes([script] + list(code_files or ()), repo_root),
        "config_sha256": (file_sha256(config_path)
                          if config_path and os.path.isfile(config_path) else None),
        "dataset_files": datasets,
        "model": model,
        "model_revision": (model_revision_value if model_revision_value is not None
                           else model_revision(model, hub_cache)),
        "seed": seed,
        "software": software_versions(),
        "host": socket.gethostname(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID") or None,
        "direction": os.environ.get(DIRECTION_ENV) or None,
        "grader": grader,
    }
    manifest.update(git_fingerprint(repo_root))
    # Round-trip so the hash is computed over exactly what the file holds.
    manifest = json.loads(json.dumps(manifest, default=str))
    manifest["manifest_hash"] = manifest_hash(manifest)
    return manifest


def render(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def write_run_manifest(output_dir: str, **kwargs) -> str:
    """Write `run_manifest.json` into `output_dir`; -> the path written.

    An existing file with identical content is kept. An existing file with
    different content is never overwritten: the next free
    `run_manifest.<n>.json` is written instead, and the choice is printed.
    """
    manifest = build_run_manifest(**kwargs)
    text = render(manifest)
    os.makedirs(output_dir, exist_ok=True)
    n = 0
    while True:
        name = FILENAME if n == 0 else "run_manifest.%d.json" % n
        path = os.path.join(output_dir, name)
        try:
            with open(path, "x") as f:
                f.write(text)
        except FileExistsError:
            with open(path) as f:
                if f.read() == text:
                    return path
            n += 1
            continue
        if n:
            print("  run_manifest.json already exists with different content; "
                  "wrote %s instead" % path)
        return path
