"""
pilot_v2.py — the reusable pilot harness for the v2 mechanism datasets.

A round is a list of Pilot Cells, each (task, framing, suffix policy[, SER
wording]) over ~1,000 instances. One shared instance list per (round, seed) is
realized under every cell's spec through `dataset/deception_v2.py` (spec
section 5), so cells of different tasks share instance ids. Every prompt of
every condition is asserted aligned and within `--max-seq-length` before any
scoring; a violation aborts that cell (never truncates), is recorded, and the
job exits nonzero after the other cells. Then ONE model load scores, per cell,
the prior (`neutral_prompt`) and the four conditions x two streams with
`dc.score_prompts`, in `SCORE_ORDER`, and `dataset/contingency.py` applies the
pre-registered acceptance rule (spec section 6).

After each cell, before the next is scored:
    <out-dir>/<cell_id>.json              the cell report (ticket 01 schema)
    <out-dir>/<cell_id>.survivors.jsonl   every contingent survivor: record,
                                          all condition prompts, scores, flags
    <out-dir>/round_summary.json          rewritten with the cells so far
An aborted cell writes <out-dir>/<cell_id>.aborted.json instead.

Usage (from the worktree root):

    # CPU dry path on the login node: realize, assert, length report; no weights
    python dataset/pilot_v2.py --cells cells.json --round 1 \
        --out-dir /abs/out --no-model
    # GPU (see scripts/pilot_v2.sbatch)
    python dataset/pilot_v2.py --cells cells.json --round 1 --out-dir /abs/out
    # summary table of a finished round
    python dataset/pilot_v2.py --summarize /abs/out --markdown /abs/pilot-round-1.md

cells.json: a list of {cell_id, task, framing (path to a framing JSON), suffix
("on"/"off"), ser_wording ("A"/"B" for ser_v2, else null), n}; an optional
per-cell `neutral_pool` path overrides `--neutral-pool`.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import random
import sys
import time
import traceback
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from dataset import contingency as ct  # noqa: E402
from dataset import deception_common as dc  # noqa: E402
from dataset.report_utils import histogram, length_summary  # noqa: E402

V2_TASKS = ("far_v2", "sdr_v2", "ser_v2")
VARIANTS = ("audit", "lab")
N_CLAUSE_SLOTS = 25                  # 20 flavor + 5 shared (spec 13.3)
MAX_SEQ_LENGTH = 120                 # training max_seq_length (spec section 4)
DEFAULT_NEUTRAL_POOL = os.path.join(dc.POOLS_DIR, "v2", "neutral_candidates.json")
DEFAULT_ITEM_PAIRS = os.path.join(dc.POOLS_DIR, "item_pairs.json")
DEFAULT_ENTITIES = os.path.join(dc.POOLS_DIR, "entities.json")
N_SAMPLES_SCORED = 5
N_SAMPLES_DRY = 3
SUMMARY_NAME = "round_summary.json"

# The order in which score_cell runs its nine prompt sets (one dc.score_prompts
# call each). (condition, stream); "prior" reads `neutral_prompt` with the
# word pair (item_1, item_2), exactly as dc.evaluate_prior_balance does.
SCORE_ORDER: Tuple[Tuple[str, Optional[str]], ...] = (("prior", None),) + tuple(
    (c, s) for c in ct.CONDITIONS for s in ct.STREAMS)


class CellAborted(Exception):
    def __init__(self, cell_id, error, record):
        super().__init__(f"{cell_id}: {error}")
        self.cell_id = cell_id
        self.error = error
        self.record = record


# ==============================================================================
# LOADERS (patched in tests)
# ==============================================================================

def load_backend():
    """The v2 scaffold module (ticket 02). Imported lazily so a half-landed
    module cannot break this harness's import or its tests."""
    return importlib.import_module("dataset.deception_v2")


def load_tokenizer(args):
    from transformers import AutoTokenizer

    from dataset.build_deception_dataset import resolve_hf_token
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=resolve_hf_token(args))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    return tokenizer


def load_model(args):
    """(model, device). Same loading as dataset/build_deception_dataset.py."""
    import torch
    from transformers import LlamaForCausalLM

    from dataset.build_deception_dataset import resolve_hf_token
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: no CUDA device; scoring an 8B model on CPU is very slow.")
    print(f"Loading {args.model} on {device}...")
    model = LlamaForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16,
        token=resolve_hf_token(args)).to(device).eval()
    return model, device


# ==============================================================================
# CELLS AND INSTANCES
# ==============================================================================

def _resolve(path: str) -> str:
    if os.path.isabs(path) or os.path.exists(path):
        return path
    alt = os.path.join(REPO_ROOT, path)
    return alt if os.path.exists(alt) else path


def parse_cells(path: str) -> List[Dict]:
    """Read and validate cells.json; suffix normalized to "on"/"off"."""
    with open(path) as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = raw["cells"]
    cells, seen = [], set()
    for c in raw:
        missing = {"cell_id", "task", "framing", "suffix", "n"} - set(c)
        if missing:
            raise ValueError(f"cell {c.get('cell_id')!r} lacks {sorted(missing)}")
        if c["cell_id"] in seen:
            raise ValueError(f"duplicate cell_id {c['cell_id']!r}")
        seen.add(c["cell_id"])
        if c["task"] not in V2_TASKS:
            raise ValueError(f"cell {c['cell_id']!r}: task must be one of {V2_TASKS}")
        suffix = {True: "on", False: "off", "on": "on", "off": "off"}.get(c["suffix"])
        if suffix is None:
            raise ValueError(f"cell {c['cell_id']!r}: suffix must be on/off")
        wording = c.get("ser_wording")
        overrides = c.get("overrides") or {}
        if not isinstance(overrides, dict):
            raise ValueError(f"cell {c['cell_id']!r}: overrides must be an object")
        if c["task"] == "ser_v2" and wording not in ("A", "B") and not (
                "question" in overrides and isinstance(wording, str) and wording):
            raise ValueError(f"cell {c['cell_id']!r}: ser_v2 needs ser_wording A or B "
                             f"(or a new label with a question/stem override)")
        if c["task"] != "ser_v2" and wording is not None:
            raise ValueError(f"cell {c['cell_id']!r}: ser_wording is SER-only")
        if int(c["n"]) < 1:
            raise ValueError(f"cell {c['cell_id']!r}: n must be positive")
        cells.append({"cell_id": c["cell_id"], "task": c["task"],
                      "framing": _resolve(c["framing"]), "suffix": suffix,
                      "ser_wording": wording, "n": int(c["n"]),
                      "overrides": dict(overrides),
                      "neutral_pool": _resolve(c["neutral_pool"])
                      if c.get("neutral_pool") else None})
    return cells


def single_token_pairs(tokenizer, pairs) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Item pairs whose two words are each one token with a leading space."""
    keep, dropped = [], []
    for a, b in pairs:
        ok = all(len(tokenizer.encode(" " + w, add_special_tokens=False)) == 1
                 for w in (a, b))
        (keep.append((a, b)) if ok else dropped.append(f"{a}/{b}"))
    return keep, dropped


def shared_instances(n: int, entities, pairs, seed: int) -> List[Dict]:
    """The round's instance list. A longer list starts with the shorter one
    (dc.generate_instances draws in a fixed sequence), so a cell of n
    instances uses the first n."""
    return dc.generate_instances(n, entities, pairs, N_CLAUSE_SLOTS, VARIANTS,
                                 seed=seed)


# ==============================================================================
# REALIZE AND ASSERT
# ==============================================================================

def check_record(tokenizer, record: Dict, max_seq_length: int) -> None:
    """Every condition aligned (dc.assert_aligned_pair) and within budget; the
    prior prompt within budget. Raises AssertionError."""
    for c in ct.CONDITIONS:
        pair = record["conditions"][c]
        try:
            dc.assert_aligned_pair(tokenizer, pair["clean_prompt"], pair["corrupt_prompt"],
                                   record["clean_item_d"], record["corrupt_item_d"],
                                   max_seq_length)
        except AssertionError as e:
            raise AssertionError(f"condition {c}: {e}") from None
    n_prior = len(tokenizer.encode(record["neutral_prompt"], add_special_tokens=False))
    assert n_prior <= max_seq_length, (
        f"neutral_prompt is {n_prior} tokens > max_seq_length={max_seq_length}")


def prepare_cell(cell: Dict, instances: Sequence[Dict], tokenizer, backend, *,
                 max_seq_length: int, neutral_pool_path: str) -> Dict:
    """Realize the cell's first n instances and assert every prompt. Any
    failure (a spec, framing or pool that does not load, a misaligned or
    over-length prompt) aborts this cell only."""
    try:
        ov = cell.get("overrides") or {}
        # Overrides (round 3) only reach backends that take them.
        spec = (backend.make_spec(cell["task"], cell["suffix"] == "on",
                                  cell["ser_wording"], overrides=ov) if ov else
                backend.make_spec(cell["task"], cell["suffix"] == "on",
                                  cell["ser_wording"]))
        framing = backend.load_framing(cell["framing"])
        pool = backend.load_neutral_pool(cell.get("neutral_pool") or neutral_pool_path)
    except Exception as e:  # any load failure aborts this cell only
        print(f"\nABORT cell {cell['cell_id']}: {e}", flush=True)
        raise CellAborted(cell["cell_id"], f"{type(e).__name__}: {e}", None) from e
    records = []
    for inst in instances[:cell["n"]]:
        rec = None
        try:
            rec = backend.realize(tokenizer, spec, framing, inst, pool,
                                  max_seq_length=max_seq_length)
            check_record(tokenizer, rec, max_seq_length)
        except Exception as e:  # misaligned, over length, or realize failed
            shown = rec if rec is not None else inst
            print(f"\nABORT cell {cell['cell_id']}: {e}\nrecord: "
                  f"{json.dumps(shown, indent=1, default=str)}", flush=True)
            raise CellAborted(cell["cell_id"], f"{type(e).__name__}: {e}", shown) from e
        records.append(rec)
    return {"cell": cell, "spec": spec, "framing": framing, "records": records}


# ==============================================================================
# SCORING
# ==============================================================================

def _prompts_for(records, cond, stream):
    if cond == "prior":
        return ([r["neutral_prompt"] for r in records],
                [(r["item_1"], r["item_2"]) for r in records])
    return ([r["conditions"][cond][f"{stream}_prompt"] for r in records],
            [ct.stream_words(r, stream) for r in records])


def score_cell(prepared: Dict, model, tokenizer, device, *, batch_size: int,
               max_seq_length: int):
    """(scores per record, prior margins, seconds per forward, forwards)."""
    records = prepared["records"]
    scores = [{c: {} for c in ct.CONDITIONS} for _ in records]
    prior: List[float] = []
    n_forwards = 0
    t0 = time.perf_counter()
    for cond, stream in SCORE_ORDER:
        prompts, pairs = _prompts_for(records, cond, stream)
        out = dc.score_prompts(prompts, pairs, model, tokenizer, device,
                               max_length=max_seq_length, batch_size=batch_size,
                               desc=f"{prepared['cell']['cell_id']}: {cond}"
                                    + (f"/{stream}" if stream else ""))
        n_forwards += len(prompts)
        for i, o in enumerate(out):
            if cond == "prior":
                prior.append(o["margin"])
            else:
                scores[i][cond][stream] = {
                    "margin": o["margin"], "choice": o["choice"], "argmax": o["argmax"],
                    "logit_a": o["logit_a"], "logit_b": o["logit_b"]}
    elapsed = time.perf_counter() - t0
    return scores, prior, (elapsed / n_forwards if n_forwards else None), n_forwards


# ==============================================================================
# REPORT
# ==============================================================================

def _lengths(tokenizer, records) -> Dict:
    out = {}
    for c in ct.CONDITIONS:
        lens = [len(tokenizer.encode(r["conditions"][c]["clean_prompt"],
                                     add_special_tokens=False)) for r in records]
        out[c] = {"summary": length_summary(lens),
                  "histogram": {str(k): v for k, v in histogram(lens).items()}}
    lens = [len(tokenizer.encode(r["neutral_prompt"], add_special_tokens=False))
            for r in records]
    out["prior"] = {"summary": length_summary(lens),
                    "histogram": {str(k): v for k, v in histogram(lens).items()}}
    return out


def _samples(tokenizer, records, k, seed, cell_id, scores=None, prior=None,
             flags=None) -> List[Dict]:
    rng = random.Random(f"{seed}:{cell_id}")
    idx = sorted(rng.sample(range(len(records)), min(k, len(records))))
    out = []
    for i in idx:
        r = records[i]
        tokens = {}
        for c in ct.CONDITIONS:
            pair = r["conditions"][c]
            ids_c, ids_x, d = dc.assert_aligned_pair(
                tokenizer, pair["clean_prompt"], pair["corrupt_prompt"],
                r["clean_item_d"], r["corrupt_item_d"], 10 ** 6)
            tokens[c] = {"clean": dc.format_token_boundaries(tokenizer, ids_c, d),
                         "corrupt": dc.format_token_boundaries(tokenizer, ids_x, d)}
        smp = {"instance_id": r["instance_id"],
               "designation_polarity": r["designation_polarity"],
               "item_polarity": r["item_polarity"],
               "template_variant": r["template_variant"],
               "item_pair": r["item_pair"], "pressure_id": r["pressure_id"],
               "neutral_id": r.get("neutral_id"),
               "target": r["target"], "distractor": r["distractor"],
               "prompts": {**{c: dict(r["conditions"][c]) for c in ct.CONDITIONS},
                           "prior": r["neutral_prompt"]},
               "tokens": tokens}
        if scores is not None:
            smp["scores"] = scores[i]
            smp["prior_margin"] = prior[i]
            smp["flags"] = flags[i]
        out.append(smp)
    return out


def cell_report(prepared: Dict, *, tokenizer, round_id, seed: int,
                scores=None, prior=None, seconds_per_forward=None,
                partition=None) -> Tuple[Dict, List[Dict]]:
    """(report, survivor rows). Unscored (dry path) when scores is None."""
    cell, framing, records = prepared["cell"], prepared["framing"], prepared["records"]
    meta = {"cell_id": cell["cell_id"], "round": round_id, "task": cell["task"],
            "framing_id": framing.id, "framing_family": framing.family,
            "framing_round": framing.round, "framing_hypothesis": framing.hypothesis,
            "framing_path": cell["framing"], "suffix": cell["suffix"],
            "ser_wording": cell["ser_wording"], "seed": seed,
            "overrides": dict(cell.get("overrides") or {}),
            "n_generated": len(records), "scored": scores is not None}
    if scores is None:
        report = {**meta, "thresholds": dict(ct.THRESHOLDS), "seconds_per_forward": None,
                  "n_forwards": 0, "partition": partition, "cost_projection": None,
                  "verdict": {"status": "not_scored", "reasons": ["--no-model dry run"]},
                  "lengths": _lengths(tokenizer, records),
                  "samples": _samples(tokenizer, records, N_SAMPLES_DRY, seed,
                                      cell["cell_id"])}
        return report, []
    metrics = ct.cell_metrics(records, scores, prior,
                              seconds_per_forward=seconds_per_forward,
                              partition=partition)
    flags = ct.classify_all(scores, prior)
    report = {**meta, **metrics, "lengths": _lengths(tokenizer, records),
              "samples": _samples(tokenizer, records, N_SAMPLES_SCORED, seed,
                                  cell["cell_id"], scores, prior, flags)}
    survivors = [{**r, "scores": sc, "prior_margin": pm, "flags": f}
                 for r, sc, pm, f in zip(records, scores, prior, flags)
                 if f["contingent"]]
    return report, survivors


def _write_json(path: str, obj) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(tmp, path)


def _clear_cell_files(out_dir: str, cell_id: str) -> None:
    """Remove a cell's files from an earlier run in the same out-dir, so a
    re-run cell never leaves a stale report, survivors file or abort record
    for --summarize to pick up."""
    for suffix in (".json", ".survivors.jsonl", ".aborted.json"):
        path = os.path.join(out_dir, cell_id + suffix)
        if os.path.exists(path):
            os.remove(path)


def _write_jsonl(path: str, rows) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    os.replace(tmp, path)


def _cell_row(rep: Dict) -> Dict:
    row = {k: rep.get(k) for k in ("cell_id", "task", "framing_id", "framing_family",
                                    "suffix", "ser_wording", "n_generated", "scored")}
    row["status"] = rep["verdict"]["status"]
    row["reasons"] = rep["verdict"]["reasons"]
    if rep.get("scored"):
        by = rep["rates"]["by_designation_polarity"]
        row.update({
            "inversion_contingent_rate": by["inversion"]["contingent_rate"],
            "identity_contingent_rate": by["identity"]["contingent_rate"],
            "n_survivors": rep["honest_instruction_on_survivors"]["n_survivors"],
            "hi_accuracy": rep["honest_instruction_on_survivors"]["accuracy"],
            "hi_item2_share": rep["honest_instruction_on_survivors"]["item2_share"],
            "gpu_hours_with_safety": rep["cost_projection"]["gpu_hours_with_safety"],
            "cap_used": rep["cost_projection"]["cap_used"],
            "top5_pair_share": rep["concentration"]["top5_pair_share"],
            "seconds_per_forward": rep["seconds_per_forward"],
            "partition": rep["partition"],
        })
    return row


def round_summary(reports: Sequence[Dict], aborted: Sequence[Dict], *, round_id=None,
                  seed=None, extra: Optional[Dict] = None) -> Dict:
    return {"round": round_id, "seed": seed, **(extra or {}),
            "cells": [_cell_row(r) for r in reports],
            "aborted": list(aborted),
            "round_verdict": ct.round_verdict(reports)}


# ==============================================================================
# ROUND
# ==============================================================================

def run_round(cells: Sequence[Dict], *, tokenizer, backend, out_dir: str, round_id,
              seed: int, entities, pairs, neutral_pool: str, model_loader=None,
              batch_size: int = 32, max_seq_length: int = MAX_SEQ_LENGTH,
              partition: Optional[str] = None) -> Dict:
    """Prepare every cell, then (unless model_loader is None) load the model
    once and score the cells one by one, writing each cell's files before the
    next. Returns the round summary."""
    os.makedirs(out_dir, exist_ok=True)
    pairs, dropped = single_token_pairs(tokenizer, pairs)
    if dropped:
        print(f"Dropped {len(dropped)} item pair(s) failing the single-token gate: "
              f"{dropped}")
    instances = shared_instances(max(c["n"] for c in cells), entities, pairs, seed)
    extra = {"n_instances": len(instances), "item_pairs_dropped": dropped,
             "n_item_pairs": len(pairs), "partition": partition}

    prepared, aborted = [], []
    for cell in cells:
        try:
            prepared.append(prepare_cell(cell, instances, tokenizer, backend,
                                         max_seq_length=max_seq_length,
                                         neutral_pool_path=neutral_pool))
            print(f"Prepared {cell['cell_id']}: {cell['n']} instances, all prompts "
                  f"aligned and <= {max_seq_length} tokens")
        except CellAborted as e:
            info = {"cell_id": e.cell_id, "error": e.error, "record": e.record}
            _clear_cell_files(out_dir, e.cell_id)
            _write_json(os.path.join(out_dir, f"{e.cell_id}.aborted.json"), info)
            aborted.append({"cell_id": e.cell_id, "error": e.error})

    reports: List[Dict] = []

    def flush():
        _write_json(os.path.join(out_dir, SUMMARY_NAME),
                    round_summary(reports, aborted, round_id=round_id, seed=seed,
                                  extra=extra))

    if model_loader is None or not prepared:
        for p in prepared:
            rep, _ = cell_report(p, tokenizer=tokenizer, round_id=round_id, seed=seed,
                                 partition=partition)
            _clear_cell_files(out_dir, p["cell"]["cell_id"])
            _write_json(os.path.join(out_dir, f"{p['cell']['cell_id']}.json"), rep)
            reports.append(rep)
            flush()
        flush()
        return round_summary(reports, aborted, round_id=round_id, seed=seed, extra=extra)

    model, device = model_loader()
    for p in prepared:
        cid = p["cell"]["cell_id"]
        scores, prior, spf, _ = score_cell(p, model, tokenizer, device,
                                           batch_size=batch_size,
                                           max_seq_length=max_seq_length)
        rep, survivors = cell_report(p, tokenizer=tokenizer, round_id=round_id,
                                     seed=seed, scores=scores, prior=prior,
                                     seconds_per_forward=spf, partition=partition)
        _clear_cell_files(out_dir, cid)
        _write_json(os.path.join(out_dir, f"{cid}.json"), rep)
        _write_jsonl(os.path.join(out_dir, f"{cid}.survivors.jsonl"), survivors)
        reports.append(rep)
        flush()
        print(f"{cid}: {rep['verdict']['status']} {rep['verdict']['reasons']} "
              f"({len(survivors)} contingent survivors, {spf:.4f} s/forward)", flush=True)
    flush()
    return round_summary(reports, aborted, round_id=round_id, seed=seed, extra=extra)


# ==============================================================================
# SUMMARIZE
# ==============================================================================

def _f(x, pct=False) -> str:
    if x is None:
        return "-"
    if isinstance(x, float) and math.isinf(x):
        return "inf"
    return f"{100 * x:.1f}%" if pct else f"{x:.3g}"


def markdown_table(summary: Dict) -> str:
    lines = [f"# Pilot round {summary.get('round')}", "",
             "| cell | task | family | suffix | SER | n | inversion | identity | "
             "survivors | HI acc | HI item_2 | GPU-h | cap | status | reasons |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in summary["cells"]:
        lines.append("| " + " | ".join([
            c["cell_id"], c["task"], str(c.get("framing_family")), c["suffix"],
            str(c.get("ser_wording") or "-"), str(c.get("n_generated")),
            _f(c.get("inversion_contingent_rate"), True),
            _f(c.get("identity_contingent_rate"), True),
            str(c.get("n_survivors", "-")), _f(c.get("hi_accuracy")),
            _f(c.get("hi_item2_share")), _f(c.get("gpu_hours_with_safety")),
            _f(c.get("cap_used")), c["status"],
            "; ".join(c.get("reasons") or []) or "-"]) + " |")
    for a in summary.get("aborted", []):
        lines.append(f"| {a['cell_id']} | | | | | | | | | | | | | aborted | "
                     f"{a['error']} |")
    rv = summary["round_verdict"]
    lines += ["", f"All tasks pass under one suffix policy within budget: "
                  f"**{rv['all_tasks_pass']}**"]
    sel = rv.get("selection")
    if sel:
        lines.append(f"Selection: suffix {sel['suffix']}, cells {sel['cells']}, "
                     f"family confound {sel['family_confound']}, three-task "
                     f"{_f(sel['three_task_gpu_hours'])} GPU-h")
    lines.append(f"Best passing cell per task: {rv['best_cell']}")
    if rv.get("pair_collapse_cells"):
        lines.append(f"Pair-driven collapse (top-5 pairs > 50% of survivors): "
                     f"{rv['pair_collapse_cells']}")
    return "\n".join(lines) + "\n"


def summarize(out_dir: str, markdown_path: Optional[str] = None) -> Dict:
    reports, aborted = [], []
    for name in sorted(os.listdir(out_dir)):
        path = os.path.join(out_dir, name)
        if name == SUMMARY_NAME or not name.endswith(".json"):
            continue
        with open(path) as f:
            obj = json.load(f)
        if name.endswith(".aborted.json"):
            aborted.append({"cell_id": obj["cell_id"], "error": obj["error"]})
        elif "cell_id" in obj and "verdict" in obj:
            reports.append(obj)
    rounds = {r.get("round") for r in reports}
    seeds = {r.get("seed") for r in reports}
    summary = round_summary(reports, aborted,
                            round_id=rounds.pop() if len(rounds) == 1 else sorted(rounds, key=str),
                            seed=seeds.pop() if len(seeds) == 1 else sorted(seeds, key=str))
    _write_json(os.path.join(out_dir, SUMMARY_NAME), summary)
    if markdown_path:
        os.makedirs(os.path.dirname(os.path.abspath(markdown_path)), exist_ok=True)
        with open(markdown_path, "w") as f:
            f.write(markdown_table(summary))
        print(f"Wrote {markdown_path}")
    return summary


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(
        description="Pilot the v2 FAR/SDR/SER cells (spec section 7).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--cells", help="cells.json (list of pilot cells)")
    p.add_argument("--round", default=None, help="round id recorded in the reports")
    p.add_argument("--out-dir", help="absolute output directory for the round")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--model", default=dc.DEFAULT_MODEL)
    p.add_argument("--max-seq-length", type=int, default=MAX_SEQ_LENGTH)
    p.add_argument("--no-model", action="store_true",
                   help="CPU dry path: realize, assert, length report; no weights")
    p.add_argument("--neutral-pool", default=DEFAULT_NEUTRAL_POOL)
    p.add_argument("--item-pairs", default=DEFAULT_ITEM_PAIRS)
    p.add_argument("--entities", default=DEFAULT_ENTITIES)
    p.add_argument("--partition", default=None,
                   help="recorded with seconds/forward (default $SLURM_JOB_PARTITION)")
    p.add_argument("--hf-token", default=None)
    p.add_argument("--summarize", metavar="OUT_DIR", default=None,
                   help="summarize a finished round directory instead of running")
    p.add_argument("--markdown", default=None, help="markdown table path (--summarize)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.summarize:
        summarize(args.summarize, args.markdown)
        return 0
    if not (args.cells and args.out_dir):
        raise SystemExit("--cells and --out-dir are required unless --summarize is given")
    if not os.path.isabs(args.out_dir):
        raise SystemExit(f"--out-dir must be absolute, got {args.out_dir!r}")
    round_id = args.round
    if isinstance(round_id, str) and round_id.isdigit():
        round_id = int(round_id)
    partition = args.partition or os.environ.get("SLURM_JOB_PARTITION") or (
        "cpu-dry-run" if args.no_model else "unknown")

    cells = parse_cells(args.cells)
    tokenizer = load_tokenizer(args)
    backend = load_backend()
    entities = dc.load_entities(args.entities)
    pairs = dc.load_item_pairs(args.item_pairs)
    loader = None if args.no_model else (lambda: load_model(args))
    try:
        summary = run_round(cells, tokenizer=tokenizer, backend=backend,
                            out_dir=args.out_dir, round_id=round_id, seed=args.seed,
                            entities=entities, pairs=pairs,
                            neutral_pool=args.neutral_pool, model_loader=loader,
                            batch_size=args.batch_size,
                            max_seq_length=args.max_seq_length, partition=partition)
    except Exception:
        traceback.print_exc()
        return 2
    if summary["aborted"]:
        print(f"ABORTED cells: {[a['cell_id'] for a in summary['aborted']]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
