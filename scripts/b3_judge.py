#!/usr/bin/env python
"""B3 judge entrypoint (plan B3 sections 1.5 and 1.6, ticket T5). Login node, mgnp, `OPENROUTER_API_KEY`; paid.

Labels B3 generation rows (`spontaneous/rows.py` schema) with the frozen G1 judge (`spontaneous/judge.py`). It never
runs without a budget ledger: `--ledger` is required, and a live run refuses unless the ledger exists with the
reviewed header the orchestrator writes (`evaluation/benchmarks/judge_budget.py`: schema 1, reviewed true, max_usd at
most 20, max_paid_attempts at most 5,000). Use one ledger per stage.

Stages:

- `calibration`: every calibration row (both variants), the primary judge (Haiku 4.5).
- `main`: every test row, the primary judge.
- `crosscheck`: a seeded sample of test rows (default 200), the cross-check judge (Sonnet 4.5), concurrency 2.
- `rejudge`: a seeded 10% sample of test rows, the primary judge, through its own cache (`--primary-cache` names the
  main cache, which must differ), so each row is a fresh paid call.

Samples are `random.Random(--sample-seed).sample(sorted row ids, n)`, written back in file order.

`--dry-run` builds the requests, reads the cache without writing it, prints the request count (unique requests not
in the cache: identical requests share one call) and the dollars
reserved at the pinned price (`judge_budget.request_bound`: full context times the input price plus max_tokens times
the output price, $0.20008 for Haiku and $3.00024 for Sonnet), and makes no call and writes no file.

A live run writes OUT (JSONL, one label record per selected row: the verdict record of `judge.judge_rows` plus
`row_id`, `stage`, `model`, the row's split, variant, query_id, category, condition and sample, and `cost_usd`, the
settled `usage.cost`; None on a cache hit or an empty response) and `run_manifest.json` beside it, with
`grader` set to the G1 fingerprint `judge.b3_judge_fingerprint()`.

    /u/swong2/.conda/envs/mgnp/bin/python scripts/b3_judge.py --rows ROWS.jsonl --stage main \\
        --ledger LEDGER.jsonl --cache CACHE.jsonl --out OUT/labels.jsonl --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.benchmarks.judge import JudgeCache, request_key  # noqa: E402
from evaluation.benchmarks.judge_budget import BudgetExceeded, JudgeBudget, request_bound  # noqa: E402
from spontaneous import judge  # noqa: E402
from spontaneous import rows as rw  # noqa: E402

STAGES = ("calibration", "main", "crosscheck", "rejudge")
SAMPLE_SEED = 20261101
CROSSCHECK_N = 200
REJUDGE_SHARE = 0.10
ATTEMPT_LIMIT = 5000
ROW_FIELDS = ("split", "variant", "query_id", "category", "condition", "sample")


def stage_model(stage, override=None):
    """The judge model of a stage; an override must be one of the two models in the frozen config."""
    config = judge.load_config()
    allowed = (config["primary_model"], config["cross_check_model"])
    if override is not None:
        if override not in allowed:
            raise ValueError("model %r is not in af_judge_config.json %s" % (override, allowed))
        return override
    return config["cross_check_model"] if stage == "crosscheck" else config["primary_model"]


def select_rows(rows, stage, n=None, seed=SAMPLE_SEED):
    """The rows a stage judges, in file order."""
    if stage not in STAGES:
        raise ValueError("unknown stage %r" % (stage,))
    split = "calibration" if stage == "calibration" else "test"
    pool = [r for r in rows if r["split"] == split]
    if stage in ("calibration", "main"):
        if n is not None:
            raise ValueError("--sample-n applies only to crosscheck and rejudge")
        return pool
    if n is None:
        n = CROSSCHECK_N if stage == "crosscheck" else int(round(REJUDGE_SHARE * len(pool)))
    if not 0 < n <= len(pool):
        raise ValueError("cannot sample %d of %d test rows" % (n, len(pool)))
    keep = set(random.Random(seed).sample(sorted(r["row_id"] for r in pool), n))
    return [r for r in pool if r["row_id"] in keep]


def plan_requests(rows, model):
    """One request per row, None for an empty response (labelled UNCLEAR locally, no call)."""
    return [None if judge.is_empty_response(r["response"]) else judge.request_for_row(r, model=model)
            for r in rows]


def ledger_status(path):
    if not os.path.exists(path):
        return {"path": path, "exists": False}
    try:
        return dict(JudgeBudget(path).stats(), exists=True)
    except BudgetExceeded as exc:
        return {"path": path, "exists": True, "error": str(exc)}


def dry_run_report(stage, model, rows, requests, cache_path, ledger_path, concurrency):
    cache = JudgeCache(cache_path) if os.path.exists(cache_path) else JudgeCache(None)
    live = [q for q in requests if q is not None]
    keys = {request_key(q) for q in live}      # identical requests share one call and the cache
    uncached = [k for k in sorted(keys) if cache.entries.get(k) is None]
    per = max((request_bound(q) for q in live), default=0.0)
    led = ledger_status(ledger_path)
    report = {
        "stage": stage, "model": model, "n_rows": len(rows), "n_empty": len(requests) - len(live),
        "n_unique": len(keys), "n_cached": len(keys) - len(uncached), "n_requests": len(uncached),
        "reserved_usd_per_request": per, "reserved_usd_all": per * len(uncached),
        "peak_inflight_usd": per * min(concurrency, len(uncached)), "concurrency": concurrency, "ledger": led,
        "over_attempt_limit": len(uncached) > ATTEMPT_LIMIT,
    }
    if "max_paid_attempts" in led:
        report["fits_ledger_attempts"] = len(uncached) <= led["max_paid_attempts"] - led["paid_attempts"]
        report["fits_ledger_peak_usd"] = (led["charged_or_reserved_usd"] + report["peak_inflight_usd"]
                                          <= led["max_usd"])
    return report


def label_records(rows, verdicts, stage, model):
    out = []
    for row, v in zip(rows, verdicts):
        rec = {"row_id": row["row_id"], "stage": stage}
        rec.update({f: row[f] for f in ROW_FIELDS})
        rec.update(v)
        rec["model"] = v.get("model") or model
        usage = v.get("usage")
        cost = usage.get("cost") if isinstance(usage, dict) else None
        rec["cost_usd"] = cost if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None
        out.append(rec)
    return out


def write_jsonl_atomic(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def manifest_kwargs(args, model):
    """The `write_run_manifest` arguments; `grader` is the freeze-G1 fingerprint."""
    return {"script": os.path.abspath(__file__), "dataset_files": list(args.rows), "model": model,
            "seed": args.sample_seed, "grader": judge.b3_judge_fingerprint(),
            "code_files": [str(ROOT / "spontaneous" / "rows.py")]}


def build_parser():
    p = argparse.ArgumentParser(description="B3 judge entrypoint (paid; needs a reviewed ledger).")
    p.add_argument("--rows", nargs="+", required=True, help="Generation row JSONL file(s).")
    p.add_argument("--stage", choices=STAGES, required=True)
    p.add_argument("--ledger", required=True, help="This stage's reviewed JudgeBudget ledger.")
    p.add_argument("--cache", required=True, help="Judge cache JSONL.")
    p.add_argument("--out", required=True, help="Label JSONL to write; run_manifest.json goes beside it.")
    p.add_argument("--model-override", default=None, help="One of the two models in af_judge_config.json.")
    p.add_argument("--primary-cache", default=None, help="rejudge only: the main stage's cache, which must differ.")
    p.add_argument("--sample-n", type=int, default=None, help="crosscheck (200) and rejudge (10%%) sample size.")
    p.add_argument("--sample-seed", type=int, default=SAMPLE_SEED)
    p.add_argument("--concurrency", type=int, default=None, help="Default 2 for crosscheck, else 8.")
    p.add_argument("--overwrite", action="store_true", help="Replace an existing --out.")
    p.add_argument("--dry-run", action="store_true", help="Count requests and reserved dollars; no call.")
    return p


def _refuse(msg):
    sys.stderr.write("b3_judge: refusing: %s\n" % msg)
    return 2


def main(argv=None, transport=None):
    args = build_parser().parse_args(argv)
    try:
        model = stage_model(args.stage, args.model_override)
        rows = select_rows(rw.load_rows(args.rows), args.stage, args.sample_n, args.sample_seed)
    except ValueError as exc:
        return _refuse(str(exc))
    concurrency = args.concurrency or (2 if args.stage == "crosscheck" else 8)
    requests = plan_requests(rows, model)

    if args.dry_run:
        report = dry_run_report(args.stage, model, rows, requests, args.cache, args.ledger, concurrency)
        print("b3_judge dry run: no call is made and no file is written.")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.stage == "rejudge":
        if not args.primary_cache:
            return _refuse("the rejudge stage needs --primary-cache, the main stage's cache")
        if os.path.realpath(args.cache) == os.path.realpath(args.primary_cache):
            return _refuse("the rejudge needs its own cache, not the primary one")
    if os.path.exists(args.out) and not args.overwrite:
        return _refuse("%s exists; pass --overwrite to replace it" % args.out)
    try:
        stats = JudgeBudget(args.ledger).stats()
    except BudgetExceeded as exc:
        return _refuse("ledger %s: %s" % (args.ledger, exc))
    report = dry_run_report(args.stage, model, rows, requests, args.cache, args.ledger, concurrency)
    remaining = stats["max_paid_attempts"] - stats["paid_attempts"]
    if report["n_requests"] > remaining:
        return _refuse("%d requests exceed the %d paid attempts left in %s"
                       % (report["n_requests"], remaining, args.ledger))

    client = judge.make_client(args.cache, args.ledger, concurrency=concurrency, transport=transport)
    try:
        verdicts = judge.judge_rows(rows, client, model=model)
    except BudgetExceeded as exc:
        sys.stderr.write("b3_judge: budget stop: %s; completed calls are cached, no labels written\n" % exc)
        return 3
    records = label_records(rows, verdicts, args.stage, model)
    write_jsonl_atomic(args.out, records)
    from run_manifest import write_run_manifest
    manifest = write_run_manifest(os.path.dirname(os.path.abspath(args.out)), **manifest_kwargs(args, model))

    counts = {}
    for rec in records:
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    settled = sum(rec["cost_usd"] for rec in records if rec["cost_usd"] is not None)
    print(json.dumps({"stage": args.stage, "model": model, "n_rows": len(records), "status": counts,
                      "settled_usd": settled, "ledger": JudgeBudget(args.ledger).stats(), "out": args.out,
                      "manifest": manifest}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
