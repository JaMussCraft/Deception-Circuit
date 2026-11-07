"""
evaluation/rejudge.py — repair an EVAL 5 suite whose judge API failed mid-run.

EVAL 5 generates every configuration's text on the GPU and then judges it. When
the judge API fails (an account out of credits returns HTTP 402 on every call),
`benchmark_eval._judge_all` records the row as `unparsed` with
`raw == "judge-failed"` and the error in `judge_error`, and the run carries on.
The generations are stored verbatim in `benchmarks.json`, so the expensive part
survives: what is missing is only the verdicts, and those can be bought later
without a GPU.

This module does that, and nothing else:

1. finds every label row a failed judge call produced;
2. rebuilds the request the evaluator made for it, through the benchmark's own
   adapter (`judge_request`), and refuses the dataset unless the rebuilt
   prompt is byte-identical to the `judge_prompt` stored with the row and the
   model matches the dataset's recorded judge — so a rubric that moved in a
   sibling checkout cannot be mixed into old labels;
3. re-runs those rows through `benchmark_eval._judge_all` with a
   `JudgeClient` built the way the evaluator builds it (same cache file at the
   suite root, same concurrency, same retry policy), so label construction,
   parsing and caching are the evaluator's own code;
4. recomputes every field derived from labels, with the evaluator's functions:
   per-config `counts` / `rates` (`tally_labels`), the dataset `null`
   (`BenchmarkEvaluation._null`) and `examples` (`BenchmarkEvaluation._examples`),
   the cell `headline` (`headline_of`), and the suite's `matrix.json` /
   `matrix.csv` (`suite.write_matrix`).

Coherence, screens, beliefs and generations do not depend on the response
judge and are never touched. The original run's `judge` block (its cache
stats) is left as it was; this tool's own stats go in a `rejudge` block.

Every write is atomic, and the first write to a file keeps a one-time copy of
it beside it (`*.pre_rejudge`).
"""

import argparse
import copy
import glob
import json
import os
import shutil
import sys
import time

from evaluation import benchmark_eval as B
from evaluation.benchmarks import base, get_benchmark
from evaluation.benchmarks.base import BenchmarkItem
from evaluation.benchmarks.judge import KEY_ENV, JudgeClient, request_key

#: What `_judge_all` writes in `raw` when the judge never answered.
FAILED_RAW = "judge-failed"

BACKUP_SUFFIX = ".pre_rejudge"

# Exit codes, in increasing order of severity; the run returns the worst seen.
EXIT_OK = 0            # nothing left failing (dry: plan is clean)
EXIT_STILL_FAILING = 1  # some labels still failing (capped, or the judge failed)
EXIT_REFUSED = 2       # a dataset was refused: prompt/model drift, or a
                       # recomputation that does not reproduce stored fields
EXIT_ABORTED = 3       # a suite was skipped before writing anything to it:
                       # its preflight call failed or a key is missing (the
                       # other suites in the invocation still run)


def is_failed(row) -> bool:
    """A label produced by a judge call that never answered."""
    return row.get("raw") == FAILED_RAW or row.get("judge_error") is not None


# ==============================================================================
# LOCATING THINGS
# ==============================================================================

def suite_cli(suite_dir):
    """The evaluator's resolved CLI, from `suite.json`. The adapters' `bind`
    reads the repo root and the judge-model overrides from it."""
    path = os.path.join(suite_dir, "suite.json")
    with open(path) as handle:
        record = json.load(handle)
    if "cli" not in record:
        raise ValueError("%s has no `cli` block" % path)
    return argparse.Namespace(**record["cli"])


def cell_files(suite_dir):
    return sorted(glob.glob(os.path.join(suite_dir, "cells", "*", "*", "*",
                                         "benchmarks.json")))


def cache_file(suite_dir):
    """Where `benchmark_eval.judge_cache_path` puts a suite's cache."""
    return os.path.join(suite_dir, "judge_cache.jsonl")


def cell_rel(suite_dir, path):
    """`cells/<label>/<task>/<ablation>` for a cell's benchmarks.json."""
    return os.path.relpath(os.path.dirname(path), suite_dir).replace(os.sep, "/")


class BenchCache(object):
    """One bound adapter per dataset name, for the whole process."""

    def __init__(self, cli):
        self.cli = cli
        self._benches = {}

    def get(self, dataset):
        if dataset not in self._benches:
            bench = get_benchmark(dataset)
            if hasattr(bench, "bind"):
                bench.bind(self.cli)
            self._benches[dataset] = bench
        return self._benches[dataset]


# ==============================================================================
# PLANNING
# ==============================================================================

class Pending(object):
    """One failed label row and the request that will re-judge it."""

    __slots__ = ("dataset", "config", "index", "request", "key")

    def __init__(self, dataset, config, index, request, key):
        self.dataset = dataset
        self.config = config
        self.index = index
        self.request = request
        self.key = key


def items_of(entry):
    return [BenchmarkItem(**item) for item in entry["items"]]


def plan_dataset(dataset, entry, benches):
    """-> (pending, problems) for one dataset entry.

    `problems` non-empty means the dataset is refused as a whole: re-judging
    some of its rows under a rubric that is not the one its other rows were
    judged under would make the configurations incomparable.
    """
    configs = entry.get("configs") or {}
    failed = [(config, index)
              for config, cell in configs.items()
              for index, row in enumerate(cell.get("labels") or [])
              if is_failed(row)]
    if not failed:
        return [], []
    problems = []
    try:
        bench = benches.get(dataset)
        items = items_of(entry)
    except Exception as error:                      # noqa: BLE001 — reported
        return [], ["cannot rebuild adapter/items: %s: %s"
                    % (type(error).__name__, error)]
    spec = entry.get("judge") or {}
    pending = []
    for config, index in failed:
        cell = configs[config]
        row = cell["labels"][index]
        generations = cell.get("generations") or []
        if index >= len(generations) or index >= len(items):
            problems.append("%s[%d]: no stored generation/item" % (config, index))
            continue
        request = bench.judge_request(items[index], generations[index])
        if request is None:
            problems.append("%s[%d]: adapter makes no judge request for this "
                            "row, but it is marked judge-failed" % (config, index))
            continue
        if request.prompt_text != row.get("judge_prompt"):
            problems.append("%s[%d]: rebuilt judge prompt differs from the "
                            "stored one (rubric or adapter drift)"
                            % (config, index))
            continue
        if spec.get("model") and request.model != spec["model"]:
            problems.append("%s[%d]: rebuilt judge model %r is not the "
                            "dataset's recorded judge %r"
                            % (config, index, request.model, spec["model"]))
            continue
        pending.append(Pending(dataset, config, index, request,
                               request_key(request)))
    return pending, problems


# ==============================================================================
# RECOMPUTING DERIVED FIELDS
# ==============================================================================

class _ScreenStub(object):
    """What `BenchmarkEvaluation._examples` reads off a `Screen`."""

    def __init__(self, entry):
        self.items = items_of(entry)
        self.prompts = list(entry.get("prompts") or [])


def recompute_dataset(entry):
    """Rewrite every label-derived field of one dataset entry in place."""
    for cell in entry["configs"].values():
        cell["counts"], cell["rates"] = B.tally_labels(cell["labels"])
    evaluation = B.BenchmarkEvaluation()
    entry["null"] = evaluation._null(entry)
    entry["examples"] = evaluation._examples(entry, _ScreenStub(entry))


def recompute_payload(payload, datasets):
    for dataset in datasets:
        recompute_dataset(payload["datasets"][dataset])
    payload["headline"] = B.headline_of(payload["datasets"])


DERIVED_DATASET_FIELDS = ("null", "examples")
DERIVED_CONFIG_FIELDS = ("counts", "rates")


def _same(a, b):
    # By serialisation: NaN != NaN, and `null.z` is NaN when every random
    # circuit ties the knockout.
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(
        b, sort_keys=True, default=str)


def consistency_problems(payload):
    """Recompute every derived field from the stored labels and list what does
    not reproduce. Run before any change: if the stored numbers cannot be
    rebuilt from the stored labels, rebuilding them after a re-judge would
    change more than the re-judged rows."""
    problems = []
    trial = copy.deepcopy(payload)
    names = [name for name, entry in trial["datasets"].items()
             if "configs" in entry]
    recompute_payload(trial, names)
    for name in names:
        old, new = payload["datasets"][name], trial["datasets"][name]
        for config in old["configs"]:
            for field in DERIVED_CONFIG_FIELDS:
                if not _same(old["configs"][config].get(field),
                             new["configs"][config][field]):
                    problems.append("%s/%s.%s" % (name, config, field))
        for field in DERIVED_DATASET_FIELDS:
            if not _same(old.get(field), new[field]):
                problems.append("%s.%s" % (name, field))
    if not _same(payload.get("headline"), trial["headline"]):
        problems.append("headline")
    return problems


# ==============================================================================
# WRITING
# ==============================================================================

def write_json_atomic(path, payload):
    """`suite.write_json`'s format, written to a sibling temp file and moved
    into place, keeping a one-time backup of what was there."""
    backup = path + BACKUP_SUFFIX
    if os.path.exists(path) and not os.path.exists(backup):
        shutil.copy2(path, backup)
    tmp = path + ".rejudge.tmp"
    with open(tmp, "w") as handle:
        json.dump(payload, handle, indent=2, default=str)
        handle.flush()
        os.fsync(handle.fileno())
    if os.path.exists(path):
        shutil.copymode(path, tmp)
    os.replace(tmp, path)
    return path


def sync_matrix(suite_dir, headlines, dry):
    """Bring `matrix.json` / `matrix.csv` in line with the cells' headlines.

    Driven by comparison rather than by "did this run change a cell", so a run
    interrupted between a cell write and this step is repaired by the next one.
    -> list of cell paths whose matrix headline was (or would be) updated.
    """
    from evaluation import suite as suite_mod

    path = os.path.join(suite_dir, "matrix.json")
    if not os.path.exists(path):
        return []
    with open(path) as handle:
        matrix = json.load(handle)
    cells = matrix.get("cells") or []
    changed = []
    for cell in cells:
        out_dir = str(cell.get("out_dir") or "").replace(os.sep, "/")
        for rel, headline in headlines.items():
            if out_dir == rel or out_dir.endswith("/" + rel):
                current = (cell.get("headlines") or {}).get("benchmarks")
                if not _same(current, headline):
                    cell.setdefault("headlines", {})["benchmarks"] = headline
                    changed.append(rel)
    if changed and not dry:
        for name in ("matrix.json", "matrix.csv"):
            target = os.path.join(suite_dir, name)
            if os.path.exists(target) and not os.path.exists(target + BACKUP_SUFFIX):
                shutil.copy2(target, target + BACKUP_SUFFIX)
        suite_mod.write_matrix(suite_dir, cells)
    return changed


# ==============================================================================
# THE RUN
# ==============================================================================

class Budget(object):
    """`--max-calls`: a cap on judge requests that are not cache hits.

    Counted per request sent, not per retry attempt; the client's own retry
    policy (up to six attempts on transient errors) is the evaluator's.
    """

    def __init__(self, limit):
        self.limit = limit
        self.used = 0

    def take(self):
        if self.limit is not None and self.used >= self.limit:
            return False
        self.used += 1
        return True


def default_client_factory(cache_path, concurrency):
    return JudgeClient(cache_path=cache_path, concurrency=concurrency)


def _say(out, text=""):
    out.write(text + "\n")
    out.flush()


def run(suite_dirs, dry=False, max_calls=None, client_factory=None,
        out=None) -> int:
    """Re-judge every failed label in `suite_dirs`. -> exit code."""
    out = out or sys.stdout
    client_factory = client_factory or default_client_factory
    budget = Budget(max_calls)
    worst = EXIT_OK
    grand = {"rows": 0, "cache_hits": 0, "calls": 0}

    for suite_dir in suite_dirs:
        cli = suite_cli(suite_dir)
        benches = BenchCache(cli)
        cache_path = cache_file(suite_dir)
        client = client_factory(cache_path,
                                getattr(cli, "judge_concurrency", 8) or 8)
        _say(out, "=" * 78)
        _say(out, "suite %s" % suite_dir)
        _say(out, "  judge cache %s (%d entries), concurrency %d"
             % (cache_path, len(client.cache.entries), client.concurrency))

        # ---- plan every cell before touching anything ----------------------
        plans = []
        seen = set()             # uncached keys already counted in this suite
        models = {}
        for path in cell_files(suite_dir):
            with open(path) as handle:
                payload = json.load(handle)
            rel = cell_rel(suite_dir, path)
            inconsistent = consistency_problems(payload)
            per_dataset, refused = {}, {}
            for dataset, entry in payload["datasets"].items():
                if "configs" not in entry:
                    continue
                pending, problems = plan_dataset(dataset, entry, benches)
                if problems:
                    refused[dataset] = problems
                elif pending:
                    per_dataset[dataset] = pending
            plans.append((path, rel, payload, per_dataset, refused,
                          inconsistent))

            _say(out, "\n  cell %s" % rel)
            if inconsistent:
                worst = max(worst, EXIT_REFUSED)
                _say(out, "    !! stored derived fields do not reproduce from "
                          "stored labels: %s" % ", ".join(inconsistent[:8]))
            for dataset, problems in refused.items():
                worst = max(worst, EXIT_REFUSED)
                _say(out, "    !! %s REFUSED (%d problems), first: %s"
                     % (dataset, len(problems), problems[0]))
            if not per_dataset:
                _say(out, "    nothing to re-judge")
            for dataset, pending in per_dataset.items():
                by_config = {}
                for p in pending:
                    models.setdefault(p.request.model, 0)
                    models[p.request.model] += 1
                    row = by_config.setdefault(p.config, [0, 0, 0])
                    row[0] += 1
                    if p.key in client.cache.entries:
                        row[1] += 1
                    elif p.key not in seen:
                        seen.add(p.key)
                        row[2] += 1
                total = [sum(v[i] for v in by_config.values()) for i in range(3)]
                for i, key in enumerate(("rows", "cache_hits", "calls")):
                    grand[key] += total[i]
                _say(out, "    %-34s rows %4d  cache hits %4d  calls %4d"
                     % (dataset, total[0], total[1], total[2]))
                _say(out, "      " + ", ".join(
                    "%s %d/%d/%d" % (config, v[0], v[1], v[2])
                    for config, v in by_config.items()))

        _say(out, "\n  judge models: %s" % (", ".join(
            "%s (%d rows)" % kv for kv in sorted(models.items())) or "none"))
        if dry:
            matrix = sync_matrix(suite_dir, {
                rel: payload.get("headline") for _, rel, payload, _, _, _
                in plans}, dry=True)
            if matrix:
                _say(out, "  matrix.json out of date for: %s" % ", ".join(matrix))
            continue

        # ---- live ----------------------------------------------------------
        uncached = [p for _, _, _, per_dataset, _, inconsistent in plans
                    if not inconsistent
                    for pending in per_dataset.values() for p in pending
                    if p.key not in client.cache.entries]
        providers = sorted({p.request.provider for p in uncached})
        missing = [KEY_ENV[pv] for pv in providers
                   if not os.environ.get(KEY_ENV[pv])]
        if missing:
            _say(out, "  !! suite %s skipped before any call or write: %s not "
                      "set" % (suite_dir, ", ".join(missing)))
            worst = max(worst, EXIT_ABORTED)
            continue
        if uncached and budget.take():
            # One call alone before the fan-out. An account out of credits
            # fails every request identically and instantly; finding that out
            # from one call is free, from six thousand it is a log flood.
            first = uncached[0]
            result = client.run([first.request])[0]
            if result is None or not result.ok:
                _say(out, "  !! preflight judge call failed: %s"
                     % (result.error if result is not None else "no result"))
                _say(out, "     suite %s skipped; nothing was written to it."
                     % suite_dir)
                worst = max(worst, EXIT_ABORTED)
                continue
            _say(out, "  preflight judge call ok (%s)" % first.request.model)

        headlines = {}
        for path, rel, payload, per_dataset, refused, inconsistent in plans:
            headlines[rel] = payload.get("headline")
            if inconsistent or not per_dataset:
                continue
            stats = {"attempted": 0, "fixed": 0, "still_failing": 0,
                     "capped": 0, "per_dataset": {}}
            for dataset, pending in per_dataset.items():
                entry = payload["datasets"][dataset]
                bench = benches.get(dataset)
                items = items_of(entry)
                ds = {"attempted": 0, "fixed": 0, "still_failing": 0,
                      "capped": 0}
                by_config = {}
                for p in pending:
                    by_config.setdefault(p.config, []).append(p)
                for config, group in by_config.items():
                    cell = entry["configs"][config]
                    chosen = []
                    for p in group:
                        if p.key in client.cache.entries or budget.take():
                            chosen.append(p)
                        else:
                            ds["capped"] += 1
                    if not chosen:
                        continue
                    rows = B._judge_all(
                        client, bench, [items[p.index] for p in chosen],
                        [cell["generations"][p.index] for p in chosen])
                    for p, row in zip(chosen, rows):
                        cell["labels"][p.index] = row
                        ds["attempted"] += 1
                        if is_failed(row):
                            ds["still_failing"] += 1
                        else:
                            ds["fixed"] += 1
                stats["per_dataset"][dataset] = ds
                for key in ("attempted", "fixed", "still_failing", "capped"):
                    stats[key] += ds[key]
            if not stats["attempted"]:
                _say(out, "  %s: nothing re-judged (cap reached)" % rel)
                worst = max(worst, EXIT_STILL_FAILING)
                continue
            recompute_payload(payload, list(stats["per_dataset"]))
            remaining = sum(1 for entry in payload["datasets"].values()
                            for cell in (entry.get("configs") or {}).values()
                            for row in cell["labels"] if is_failed(row))
            block = payload.setdefault("rejudge", {"runs": []})
            block["runs"].append(dict(
                stats, when=time.strftime("%Y-%m-%dT%H:%M:%S"),
                judge_cache=cache_path,
                judge=client.stats(),
                refused_datasets=sorted(refused)))
            block["still_failing"] = remaining
            block["backup"] = os.path.basename(path) + BACKUP_SUFFIX
            write_json_atomic(path, payload)
            headlines[rel] = payload["headline"]
            _say(out, "  %s: re-judged %d, fixed %d, still failing %d, capped "
                      "%d; file now has %d failing" % (
                          rel, stats["attempted"], stats["fixed"],
                          stats["still_failing"], stats["capped"], remaining))
            if remaining:
                worst = max(worst, EXIT_STILL_FAILING)
        updated = sync_matrix(suite_dir, headlines, dry=False)
        if updated:
            _say(out, "  matrix.json/csv updated for: %s" % ", ".join(updated))

    _say(out, "\n" + "=" * 78)
    _say(out, "total: %d rows to re-judge, %d cache hits, %d new judge calls%s"
         % (grand["rows"], grand["cache_hits"], grand["calls"],
            " (dry run: no call made, nothing written)" if dry else ""))
    if not dry:
        _say(out, "judge calls made this run (excluding retries): %d"
             % budget.used)
    return worst
