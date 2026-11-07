"""
sources.py — locating the benchmark data on disk.

Two kinds of source, two rules.

**Sibling repos** (`mask/`, `liars-bench/`) are checked out next to
`Deception-Circuit`, so `--benchmark-repo-root` defaults to this repo's parent
directory. It is a flag rather than a constant because the layout is a
convention, not a guarantee, and a wrong guess should be fixable without
editing code.

**HuggingFace datasets** (`cais/wmdp`, `cais/mmlu`, `Cadenza-Labs/liars-bench`)
are resolved through `snapshot_download(..., local_files_only=True)` rather
than `datasets.load_dataset`. Three reasons, all learned the hard way: it never
touches the network, so it works on a login node and inside a job with no
egress; it picks one snapshot deterministically when the cache holds several
revisions of the same repo (liars-bench currently has three); and it hands back
a plain directory of parquet files, which pandas reads without dragging in the
`datasets` library's own version-sensitive behaviour.
"""

import glob
import os


def repo_root(cli, default=None):
    """The directory holding the sibling benchmark repos."""
    value = getattr(cli, "benchmark_repo_root", None)
    if value:
        return os.path.abspath(value)
    if default:
        return os.path.abspath(default)
    # .../Deception-Circuit/evaluation/benchmarks/sources.py -> .../Alignment
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(os.path.dirname(here)))


def repo_path(cli, *parts):
    return os.path.join(repo_root(cli), *parts)


def require_dir(path, what, hint=None):
    if not os.path.isdir(path):
        message = "%s not found at %s" % (what, path)
        if hint:
            message += "\n  " + hint
        raise FileNotFoundError(message)
    return path


def require_file(path, what, hint=None):
    if not os.path.isfile(path):
        message = "%s not found at %s" % (what, path)
        if hint:
            message += "\n  " + hint
        raise FileNotFoundError(message)
    return path


def hf_snapshot(repo_id):
    """The local snapshot directory for a cached HF dataset. Never downloads.

    `local_files_only=True` turns a cache miss into a clear exception naming
    the repo, instead of a job that silently stalls on a network call it cannot
    make.
    """
    from huggingface_hub import snapshot_download
    try:
        return snapshot_download(repo_id=repo_id, repo_type="dataset",
                                 local_files_only=True)
    except Exception as exc:                     # noqa: BLE001 — re-raised
        raise FileNotFoundError(
            "dataset %r is not in the local HuggingFace cache (%s).\n"
            "  Fetch it once with network access, or point HF_HOME at a cache "
            "that has it." % (repo_id, exc))


def read_parquet(directory, pattern="*.parquet"):
    """Every parquet file under `directory` matching `pattern`, concatenated."""
    import pandas as pd
    paths = sorted(glob.glob(os.path.join(directory, pattern)))
    if not paths:
        raise FileNotFoundError("no parquet matching %s under %s"
                                % (pattern, directory))
    frames = [pd.read_parquet(path) for path in paths]
    return pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]


def hf_config(repo_id, config, split="test"):
    """One config/split of a cached HF dataset, as a DataFrame."""
    snapshot = hf_snapshot(repo_id)
    directory = os.path.join(snapshot, config)
    if not os.path.isdir(directory):
        available = sorted(name for name in os.listdir(snapshot)
                           if os.path.isdir(os.path.join(snapshot, name)))
        raise FileNotFoundError(
            "config %r not in %s (have: %s)"
            % (config, repo_id, ", ".join(available) or "none"))
    return read_parquet(directory, "%s-*.parquet" % split)


def import_module_from(path, module_name):
    """Import a module by file path.

    Used to pull MASK's judge prompts out of `mask/mask/prompts/` rather than
    copying 259 lines of template text into this repo. A copy would be one
    upstream edit away from silently judging with a stale rubric, and the
    plan's word is "verbatim".
    """
    import importlib.util
    require_file(path, "module %s" % module_name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
