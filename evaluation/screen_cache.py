"""screen_cache.py — persist EVAL 5's screening pass across sbatch jobs.

`run_screen` is the expensive part of EVAL 5 and none of it depends on which
circuit is loaded: it runs under `all_gates_open` with `hook=None`, and stores
the full model's own tokens. At `--benchmark-n-per-dataset 100` the screen,
the belief probes and the reference pool are ~79% of the ceiling (~81h of
~103h across all eleven datasets); the ablated configs and coherence are the
remaining ~21.6h, and only those genuinely have to be repaid per circuit.

`Session.screen_for` already memoises the screen so a 3x3 suite computes it
once. That memo dies with the process, so every sbatch job re-screened from
scratch. This module moves it to disk, keyed so that a hit is only ever a
screen that would have been recomputed identically.

    The device is part of the key, deliberately.

`full` reuses the screen's own tokens rather than regenerating them, so a
screen made on one GPU and ablated configs generated on another would put
"which GPU" inside the very delta EVAL 5 measures — Hopper `full` against
Ampere `knockout`. Batch re-bucketing can already flip an argmax on a near-tie
and Hopper/Ampere bf16 kernels differ by more than that. Keying on the device
name means switching GPU type is a miss and the screen is repaid, which is the
honest outcome: the two sets of numbers were never comparable.

Layout, one directory per dataset:

    <cache_dir>/<dataset>/<hash>.pt      the Screen
    <cache_dir>/<dataset>/<hash>.json    the full key, plainly readable

The sidecar exists so `--dry-run` — which runs on a login node with no GPU and
therefore cannot compute a key containing the device — can still scan what is
cached, report it, and say which fields the nearest cache differs in.

A cache must never be able to fail an evaluation. Every save and load failure
degrades to a warning and a miss; the alternative is a save bug at hour three
killing a job whose results were about to be written.
"""

import hashlib
import json
import os
import time

import torch


# Bumped whenever the pickled `Screen` shape or `BenchmarkItem` changes in a
# way that makes an older file wrong rather than merely stale. An unreadable
# file is a miss, so a missed bump costs a re-screen, not a wrong answer.
CACHE_VERSION = 1

# Every CLI flag the screen's contents depend on. Kept as an explicit list
# rather than "everything on cli" so that adding an unrelated flag does not
# invalidate every cache on disk — and so a reviewer can check the list against
# `run_screen` by reading, which is the only way anyone will ever check it.
#
# `benchmark_gen_batch_size` is here because batching changes the argmax
# reduction order, so a screen generated at batch 8 is not the screen that
# batch 32 would have produced. `wikitext_seed` is here because it seeds
# `assign_partners`, which fixes the reference each item is paired against.
KEYED_FLAGS = (
    "benchmark_n_per_dataset",
    "benchmark_new_tokens",
    "benchmark_belief_tokens",
    "benchmark_ref_pool",
    "benchmark_screen_seed",
    "benchmark_screen_budget",
    "benchmark_gen_batch_size",
    "benchmark_repo_root",
    "no_kv_cache",
    "wikitext_seed",
    # The screen's labels come from these, so a different judge is a different
    # evaluation set even with every generation identical.
    "mask_judge_model",
    "mask_numeric_judge_model",
    "lb_judge_model",
    "lb_harm_judge_model",
    # Read inside `belief_request` DURING the screen, not at load time: it
    # changes how many probes each item gets, so it changes which items
    # survive the "probes must agree" rule and therefore the evaluation set.
    # `candidate_fingerprint` cannot see it -- probes are not a property of a
    # loaded item.
    "lb_belief_templates",
    # Caps what `load()` returns, so it is already covered transitively by
    # `candidate_fingerprint`. Named anyway: the fingerprint degrades to the
    # constant "unloadable" when the pool cannot be read, and a field that
    # almost never changes costs no misses while a silent reuse costs a whole
    # evaluation.
    "benchmark_pool_size",
)


def _source_fingerprint(bench, cli=None) -> str:
    """Hash the adapter's own source, `base.py`, and its external rubric files.

    The candidate fingerprint below catches changed *data*. It cannot catch a
    changed *rubric* — an edited `judge_request` prompt or `parse_judgement`
    rule relabels the same generations, and the screen is a set of labels. No
    data hash sees that, so source stands in for it.

    The adapter module alone is not enough, because for both adapters that
    have a judge the rubric does not live in this repo. MASK imports its judge
    prompts from `mask/prompts/evaluation_prompts.py` and its numeric rules
    from `mask/metric.py`; Liars' Bench lifts its rubrics out of the notebooks
    in `liars-bench/src/`, deliberately, so that a copy here cannot go stale.
    A `git pull` in either checkout changes how a response is judged while
    nothing in this repo moves — and the cached `full` rows would then carry
    the old rubric's labels while every ablated configuration is judged under
    the new one. `Benchmark.rubric_sources` names those files; their raw bytes
    are hashed here under the same whole-file policy as the modules.

    Blunt on purpose: a comment-only edit to `mask_bench.py` invalidates MASK's
    caches. That costs a re-screen. The alternative — trying to hash "only the
    parts that matter" — is a guess about which parts matter, and being wrong
    silently reuses labels the current rubric would not produce.
    """
    import inspect

    from evaluation.benchmarks import base

    digest = hashlib.sha256()
    for module in (base, inspect.getmodule(type(bench))):
        try:
            digest.update(inspect.getsource(module).encode("utf-8"))
        except (OSError, TypeError):                        # noqa: PERF203
            # Frozen or synthesised module: contribute its identity instead of
            # silently contributing nothing.
            digest.update(repr(getattr(module, "__name__", module)).encode())
    for path in sorted(_rubric_paths(bench, cli)):
        digest.update(path.encode("utf-8"))
        try:
            with open(path, "rb") as handle:
                digest.update(handle.read())
        except OSError:
            # A checkout that is not there cannot have its rubric hashed. The
            # adapter will fail loudly when it tries to read the same file, so
            # marking it here rather than pretending the file was empty --
            # which would collide with a genuinely empty file.
            digest.update(b"<missing>")
    return digest.hexdigest()[:16]


def _rubric_paths(bench, cli):
    hook = getattr(bench, "rubric_sources", None)
    if hook is None:
        return ()
    try:
        return tuple(hook(cli))
    except Exception:                                       # noqa: BLE001
        # A cache key must not be the thing that takes a run down; an adapter
        # that cannot resolve its own rubric paths will say so when it reads
        # them.
        return ()


def candidate_fingerprint(bench, items) -> str:
    """Hash every field of every candidate that can change how it is judged.

    Ids alone would miss a changed prompt template — same rows, different text,
    same hash, and the cached screen would be prompts the adapter no longer
    produces.

    `belief` and `meta` matter for the same reason and are less obvious: MASK
    loads `belief` from an external metrics CSV and puts the proposition, the
    doubling-down turns and the system prompt in `meta`, and both
    `judge_request` and `parse_judgement` read them. Regenerating those metrics
    leaves every id and every message identical while changing what counts as
    a lie, so hashing only the first three fields would reuse labels computed
    against the old propositions.
    """
    if items is None:
        return "unloadable"
    digest = hashlib.sha256()
    digest.update(("%d\n" % len(items)).encode("utf-8"))
    for item in items:
        digest.update(repr(getattr(item, "item_id", None)).encode("utf-8"))
        digest.update(repr(getattr(item, "condition", None)).encode("utf-8"))
        digest.update(repr(getattr(item, "messages", None)).encode("utf-8"))
        digest.update(repr(getattr(item, "belief", None)).encode("utf-8"))
        meta = getattr(item, "meta", None)
        # Sorted: a dict that round-trips through JSON or a DataFrame can come
        # back with its keys in another order without anything having changed.
        digest.update(repr(sorted(meta.items()) if isinstance(meta, dict)
                           else meta).encode("utf-8"))
    return digest.hexdigest()[:16]


def device_stamp() -> dict:
    """What generated a screen. `device` is in the key; the rest is provenance."""
    import transformers

    name = "cpu"
    if torch.cuda.is_available():
        try:
            name = torch.cuda.get_device_name(0)
        except Exception:                                   # noqa: BLE001
            name = "cuda-unknown"
    return {"device": name, "torch": torch.__version__,
            "transformers": transformers.__version__}


def build_key(cli, dataset, bench, items, model, device=None) -> dict:
    """The full cache key, as a dict so a miss can be explained field by field.

    `model` comes from `session.base_args.model` — the run's model, not a CLI
    flag. `device` is passed in rather than read here so `--dry-run` can build
    the key on a login node with no GPU and leave it None, which never matches
    a real screen: a dry run must not be able to claim a hit it cannot verify.
    """
    key = {"version": CACHE_VERSION, "dataset": dataset,
           "model": model,
           "device": device,
           "candidates": candidate_fingerprint(bench, items),
           "adapter_source": _source_fingerprint(bench, cli)}
    for flag in KEYED_FLAGS:
        key[flag] = getattr(cli, flag, None)
    return key


def key_hash(key) -> str:
    payload = json.dumps(key, sort_keys=True, default=repr)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def cache_dir_for(cli, dataset) -> str:
    root = getattr(cli, "benchmark_screen_cache", None) or DEFAULT_CACHE_DIR
    return os.path.join(root, dataset.replace(":", "__").replace("/", "__"))


DEFAULT_CACHE_DIR = os.path.join("outputs", "_screens")


def paths_for(cli, dataset, key):
    directory = cache_dir_for(cli, dataset)
    stem = os.path.join(directory, key_hash(key))
    return stem + ".pt", stem + ".json"


def describe_misses(cli, dataset, key, limit=3):
    """Why did this key miss? Compare it to the sidecars already on disk.

    Without this a miss is indistinguishable from an empty cache, and the
    difference between "you changed --benchmark-gen-batch-size" and "nothing is
    cached" is the difference between a five-second fix and a re-screen.
    """
    directory = cache_dir_for(cli, dataset)
    try:
        names = sorted(n for n in os.listdir(directory) if n.endswith(".json"))
    except OSError:
        return []
    reports = []
    for name in names[:limit]:
        try:
            with open(os.path.join(directory, name)) as handle:
                other = json.load(handle)
        except (OSError, ValueError):
            continue
        stamp = other.pop("_stamp", {})
        created = other.pop("_created_at", None)
        # Underscore-prefixed fields are provenance the sidecar carries for a
        # human reader; they are not part of the key and must not show up as
        # differences, or every comparison would differ in `_created_at` and
        # "differs only in the device" could never be true.
        differs = sorted(field for field in set(key) | set(other)
                         if key.get(field) != other.get(field))
        reports.append({"file": name, "differs": differs, "stamp": stamp,
                        "key": other, "created_at": created})
    return reports


def cached_on_devices(cli, dataset, key):
    """Devices that already hold a screen matching `key` in every other field.

    `--dry-run` runs on a login node with no GPU, so it cannot build a key that
    includes the device and cannot honestly claim a hit. What it *can* say is
    "this screen is already cached, and here is the hardware it was made on" —
    which is exactly the information needed to decide whether the job about to
    be submitted will pay for the screen or skip it.
    """
    devices = []
    for near in describe_misses(cli, dataset, key, limit=64):
        if near["differs"] == ["device"]:
            # The key's own `device` field, not the stamp's. They agree in a
            # real run, but the key field is the one a hit has to match, so
            # reporting the stamp would be reporting a different thing than
            # the one being decided.
            devices.append(near["key"].get("device", "?"))
    return devices


def load(cli, dataset, key):
    """-> (screen, provenance) on a hit, (None, provenance) on a miss.

    Any failure is a miss. A cache that can raise is a cache that can fail an
    eight-hour job at minute one for no scientific reason.
    """
    if key.get("device") is None:
        return None, {"hit": False, "reason": "no device in key"}
    path, sidecar = paths_for(cli, dataset, key)
    if not os.path.exists(path):
        return None, {"hit": False, "reason": "not cached", "path": path,
                      "near": describe_misses(cli, dataset, key)}
    try:
        blob = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as error:                              # noqa: BLE001
        return None, {"hit": False, "reason": "unreadable: %s" % error,
                      "path": path}
    if not isinstance(blob, dict) or blob.get("key") != key:
        # A hash collision, or a file written by a version whose key fields
        # differed. Recompute rather than trust the filename.
        return None, {"hit": False, "reason": "key mismatch", "path": path}
    provenance = {"hit": True, "path": path,
                  "created_at": blob.get("created_at")}
    provenance.update(blob.get("stamp", {}))
    del sidecar
    return blob.get("screen"), provenance


def save(cli, dataset, key, screen) -> dict:
    """Write the screen and its sidecar. Never raises.

    Written to a temporary name and renamed, so a job killed mid-write leaves
    no half-file for the next job to read — and so two jobs screening the same
    dataset concurrently cannot interleave into one corrupt file.
    """
    path, sidecar = paths_for(cli, dataset, key)
    stamp = device_stamp()
    created = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = "%s.tmp.%d" % (path, os.getpid())
        torch.save({"key": key, "screen": screen, "stamp": stamp,
                    "created_at": created}, tmp)
        os.replace(tmp, path)
        side = dict(key)
        side["_stamp"] = stamp
        side["_created_at"] = created
        tmp_side = "%s.tmp.%d" % (sidecar, os.getpid())
        with open(tmp_side, "w") as handle:
            json.dump(side, handle, indent=2, sort_keys=True, default=repr)
        os.replace(tmp_side, sidecar)
    except Exception as error:                              # noqa: BLE001
        for leftover in (locals().get("tmp"), locals().get("tmp_side")):
            if leftover and os.path.exists(leftover):
                try:
                    os.remove(leftover)
                except OSError:
                    pass
        print("  WARNING: could not cache %s's screen: %s" % (dataset, error))
        return {"saved": False, "error": str(error)}
    result = {"saved": True, "path": path, "created_at": created}
    result.update(stamp)
    return result
