"""
build_nopressure_dataset.py — the `<task>_nopressure` dataset (Format Circuit).

The Format Circuit is a mechanism task's `nopressure` condition: the same
instances as the deceptive dataset with the Pressure Clause deleted and honest
labels, so what it recruits is the task format alone (read the designating
sentence, map the predicate, emit one of the two items at the readout).

Derived, never regenerated:

  1. Load the stored deceptive splits `<data-dir>/<task>` (and the honest twin
     `<data-dir>/<task>_honest`, used only as a tagged fallback).
  2. Relabel every deceptive record: swap `target` / `distractor` (they become
     the honest answer and the deceptive one), `condition: "nopressure"`,
     `pressure: ""`, keep `pressure_id` and `instance_id`. Delete the stored
     clause from the stored clean / corrupt / neutral prompts by clause surgery
     (`dataset/clause_surgery.py`) and re-assert alignment. Predicate words stay
     whatever the stored record has (`desig` / `desig_inv`); nothing is
     re-templated through `dc.SPECS`, whose FAR / SDR wording has drifted.
  3. Run `dc.evaluate_behavior` ONCE per split on the full model. Apply the
     behavioral filter's rule (`dc.behavior_passes`: clean argmax == honest
     target at margin AND corrupt argmax == the distractor at margin, i.e. the
     flip) offline at --thresholds in order (default 0.7, 0.5, 0.3) and keep
     the first threshold leaving >= --min-train train, >= --min-train
     validation and >= --min-test test survivors. 0.3 is a hard floor.
  4. Only if even the floor falls short: the honest twin's instances (same
     clause surgery, labels already honest) are filtered the same way and each
     short split is topped up to its minimum, in instance_id order, with
     records tagged `source: "honest_split"`. Every record from the deceptive
     splits carries `source: "deceptive_split"`, so its instance_id pairs it
     with the deceptive dataset; honest-split records pair with nothing.

Saves, next to `<task>` and `<task>_honest`:

    <data-dir>/<task>_nopressure/                       DatasetDict
    <data-dir>/<task>_nopressure/dataset_config.json    condition, margin_thresh, steps
    <data-dir>/<task>_nopressure/filter_report.json     per-threshold counts, mixes

CPU-safe dry run (relabel, surgery and alignment on the real tokenizer; no
forward passes, nothing written):

    python dataset/build_nopressure_dataset.py --task far --no-model

Full build (GPU): scripts/build_nopressure.sbatch
"""

import argparse
import json
import os
import random
import sys
from collections import Counter
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataset import deception_common as dc
from dataset.build_deception_dataset import pass_rate_tables, save_splits
from dataset.clause_surgery import remove_clause
from dataset.report_utils import margin_summary, print_pass_rate_table

SPLITS = ("train", "validation", "test")
DEFAULT_THRESHOLDS = (0.7, 0.5, 0.3)
MARGIN_FLOOR = 0.3
SOURCES = ("deceptive_split", "honest_split")
_SOURCE_CONDITION = {"deceptive_split": "deceptive", "honest_split": "honest"}
_PROMPT_KEYS = ("clean_prompt", "corrupt_prompt", "neutral_prompt")
MIX_FACTORS = ("item_pair", "item_polarity", "designation_polarity",
               "template_variant")


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(
        description="Build <task>_nopressure (the Format Circuit's dataset) from "
                    "the stored deceptive dataset by clause surgery.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--task", choices=["far", "sdr"], required=True,
                   help="SER is deferred until its user turn is reworded.")
    p.add_argument("--data-dir", default=os.path.join("data", "datasets"),
                   help="Holds <task> and <task>_honest; the output goes here "
                        "too unless --output-dir is given.")
    p.add_argument("--output-dir", default=None,
                   help="Default: <data-dir>/<task>_nopressure.")
    p.add_argument("--thresholds", type=float, nargs="+",
                   default=list(DEFAULT_THRESHOLDS),
                   help="Margin thresholds tried in order (strictly descending, "
                        f"none below the {MARGIN_FLOOR} floor).")
    p.add_argument("--min-train", type=int, default=150,
                   help="Minimum train survivors; validation uses it too.")
    p.add_argument("--min-test", type=int, default=500)
    p.add_argument("--model", default=None,
                   help="Default: the source dataset_config.json's model.")
    p.add_argument("--max-seq-length", type=int, default=None,
                   help="Default: the source dataset_config.json's value.")
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--seed", type=int, default=42,
                   help="Only picks the sample pairs printed and reported.")
    p.add_argument("--num-sample-pairs", type=int, default=3)
    p.add_argument("--no-model", action="store_true",
                   help="Dry run (CPU-safe): relabel, clause surgery and "
                        "alignment on the real tokenizer; no forward passes, "
                        "nothing written.")
    p.add_argument("--hf-token", default=None)
    return p


# ==============================================================================
# Relabel + clause surgery
# ==============================================================================

def nopressure_record(record, source):
    """One stored record as a `nopressure` record.

    deceptive_split: target / distractor swapped (the stored target is the
    deceptive answer). honest_split: labels kept (the honest twin's target is
    already the honest answer). Either way the stored clause is cut out of the
    stored prompts and `pressure` becomes "".
    """
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}, got {source!r}")
    want = _SOURCE_CONDITION[source]
    if record.get("condition") != want:
        raise ValueError(f"{source} record {record.get('instance_id')} has "
                         f"condition {record.get('condition')!r}, expected "
                         f"{want!r}")
    clause = record["pressure"]
    out = dict(record)
    for key in _PROMPT_KEYS:
        if key in out:
            out[key] = remove_clause(record[key], clause)
    if source == "deceptive_split":
        out["target"], out["distractor"] = record["distractor"], record["target"]
    out.update(condition="nopressure", pressure="", source=source)
    return out


def derive_split(records, source, tokenizer, max_seq_length):
    """nopressure_record over a split, with the pair alignment re-asserted."""
    out = [nopressure_record(r, source) for r in records]
    for r in out:
        dc.assert_aligned_pair(tokenizer, r["clean_prompt"], r["corrupt_prompt"],
                               r["clean_item_d"], r["corrupt_item_d"],
                               max_seq_length)
    return out


# ==============================================================================
# Threshold step-down (offline, on the stored margins)
# ==============================================================================

def _check_thresholds(thresholds):
    thresholds = tuple(float(t) for t in thresholds)
    if not thresholds:
        raise ValueError("need at least one margin threshold")
    if any(b >= a for a, b in zip(thresholds, thresholds[1:])):
        raise ValueError(f"thresholds must be strictly descending: {thresholds}")
    if thresholds[-1] < MARGIN_FLOOR:
        raise ValueError(f"thresholds go below the {MARGIN_FLOOR} floor: "
                         f"{thresholds}")
    return thresholds


def survivor_counts(behaviors_by_split, threshold):
    return {split: sum(dc.behavior_passes(b, threshold) for b in bs)
            for split, bs in behaviors_by_split.items()}


def select_threshold(behaviors_by_split, thresholds, minimums):
    """The first threshold whose survivors meet every split's minimum.

    Returns {margin_thresh, met_minimums, thresholds_tried, per_threshold,
    minimums}: `thresholds_tried` is every step taken, in order, up to and
    including the chosen one; `per_threshold` is every threshold's counts,
    tried or not. When nothing meets the minimums the floor (last threshold) is
    chosen with met_minimums False, which is what triggers the fallback.
    """
    thresholds = _check_thresholds(thresholds)
    per = []
    for t in thresholds:
        surv = survivor_counts(behaviors_by_split, t)
        per.append({"threshold": t, "survivors": surv,
                    "meets_minimums": all(surv.get(s, 0) >= n
                                          for s, n in minimums.items())})
    tried = []
    for step in per:
        tried.append(step)
        if step["meets_minimums"]:
            break
    return {"margin_thresh": tried[-1]["threshold"],
            "met_minimums": tried[-1]["meets_minimums"],
            "thresholds_tried": tried, "per_threshold": per,
            "minimums": dict(minimums)}


# ==============================================================================
# Assembly
# ==============================================================================

def _with_margins(record, behavior):
    return {**record, "clean_margin": behavior["clean_margin"],
            "corrupt_margin": behavior["corrupt_margin"]}


def _passing(records, behaviors, threshold):
    return [_with_margins(r, b) for r, b in zip(records, behaviors)
            if dc.behavior_passes(b, threshold)]


def assemble(deceptive, deceptive_beh, honest, honest_beh, selection):
    """(final splits, fallback summary). Deceptive-split survivors keep the
    stored order; honest-split records are appended only when the floor failed,
    only to the splits short of their minimum, and only up to it."""
    thresh = selection["margin_thresh"]
    minimums = selection["minimums"]
    final = {s: _passing(deceptive[s], deceptive_beh[s], thresh) for s in SPLITS}
    fallback = {"used": False, "size": 0, "threshold": None, "per_split": {}}
    if selection["met_minimums"]:
        return final, fallback

    fallback["threshold"] = thresh
    for split in SPLITS:
        short = max(minimums.get(split, 0) - len(final[split]), 0)
        pool = sorted(_passing(honest.get(split, []), honest_beh.get(split, []),
                               thresh), key=lambda r: r["instance_id"])
        added = pool[:short]
        final[split].extend(added)
        fallback["per_split"][split] = {
            "short_by": short, "honest_survivors": len(pool),
            "appended": len(added), "still_short_by": short - len(added)}
    fallback["size"] = sum(e["appended"] for e in fallback["per_split"].values())
    fallback["used"] = fallback["size"] > 0
    return final, fallback


# ==============================================================================
# Report
# ==============================================================================

def unexpected_tokens(behaviors):
    """Argmax tokens that were neither answer word, in either stream."""
    c = Counter()
    for b in behaviors:
        pair = (b["target_token"], b["distractor_token"])
        if b["clean_argmax_id"] not in pair:
            c[repr(b["clean_argmax"])] += 1
        if b["corrupt_argmax_id"] not in pair:
            c[repr(b["corrupt_argmax"])] += 1
    return dict(c.most_common())


def _mix(records):
    return {**{f: dict(Counter(str(r[f]) for r in records)) for f in MIX_FACTORS},
            "source": dict(Counter(r["source"] for r in records))}


def build_report(args, deceptive, deceptive_beh, honest, honest_beh, selection,
                 final, fallback):
    thresh = selection["margin_thresh"]
    all_recs = [r for s in SPLITS for r in deceptive[s]]
    all_beh = [b for s in SPLITS for b in deceptive_beh[s]]
    flagged = [{"passed": dc.behavior_passes(b, thresh)} for b in all_beh]

    splits = {}
    for s in SPLITS:
        beh = deceptive_beh[s]
        survived = sum(dc.behavior_passes(b, thresh) for b in beh)
        splits[s] = {
            "input": len(beh), "survived": survived,
            "pass_rate": survived / max(len(beh), 1),
            "kept": len(final[s]),
            "from_honest_split": sum(r["source"] == "honest_split"
                                     for r in final[s]),
            "clean_margin": margin_summary([b["clean_margin"] for b in beh]),
            "corrupt_margin": margin_summary([b["corrupt_margin"] for b in beh]),
            "unexpected_argmax_tokens": unexpected_tokens(beh),
        }
    passed = sum(f["passed"] for f in flagged)
    honest_split_counts = (
        [{"threshold": t,
          "survivors": survivor_counts(honest_beh, t)}
         for t in _check_thresholds(args.thresholds)] if honest_beh else None)

    rng = random.Random(args.seed)
    train = final["train"]
    samples = rng.sample(train, min(args.num_sample_pairs, len(train)))
    keys = ("instance_id", "source", "item_pair", "template_variant",
            "designation_polarity", "item_polarity", "clean_item_d",
            "corrupt_item_d", "target", "distractor", "clean_margin",
            "corrupt_margin", "clean_prompt", "corrupt_prompt")
    return {
        "task": args.task,
        "condition": "nopressure",
        "margin_thresh": thresh,
        "met_minimums": selection["met_minimums"],
        "minimums": selection["minimums"],
        "thresholds_tried": selection["thresholds_tried"],
        "per_threshold": selection["per_threshold"],
        "honest_split_per_threshold": honest_split_counts,
        "splits": splits,
        "overall": {
            "input": len(all_beh), "survived": passed,
            "pass_rate": passed / max(len(all_beh), 1),
            "clean_margin": margin_summary([b["clean_margin"] for b in all_beh]),
            "corrupt_margin": margin_summary(
                [b["corrupt_margin"] for b in all_beh]),
            "unexpected_argmax_tokens": unexpected_tokens(all_beh),
        },
        **pass_rate_tables(all_recs, flagged),
        "fallback": fallback,
        "survivor_mix": {s: _mix(final[s]) for s in SPLITS},
        "sample_pairs": [{k: r[k] for k in keys} for r in samples],
    }


def build_config(args, src_config, selection, final, model, max_seq_length,
                 src_dir, honest_dir):
    return {
        **src_config,
        "task": args.task,
        "condition": "nopressure",
        "model": model,
        "max_seq_length": max_seq_length,
        "margin_thresh": selection["margin_thresh"],
        "met_minimums": selection["met_minimums"],
        "thresholds": list(_check_thresholds(args.thresholds)),
        "thresholds_tried": selection["thresholds_tried"],
        "min_train": args.min_train,
        "min_validation": args.min_train,
        "min_test": args.min_test,
        "source_counts": {s: {src: sum(r["source"] == src for r in final[s])
                              for src in SOURCES} for s in SPLITS},
        "source_datasets": {"deceptive_split": src_dir,
                            "honest_split": honest_dir},
        "derivation": ("stored prompts with the stored Pressure Clause deleted "
                       "by clause surgery (dataset/clause_surgery.py); "
                       "deceptive-split labels swapped to honest; pressure_id "
                       "kept for provenance"),
        "prior_margin_note": ("prior_margin is carried over from the source "
                              "build (measured on the with-pressure neutral "
                              "prompt); clean_margin / corrupt_margin are this "
                              "build's, under the honest labels"),
        "filtered": True,
        "created": date.today().isoformat(),
    }


# ==============================================================================
# Run
# ==============================================================================

def _load_splits(path):
    return {s: dc.load_or_generate_deception_data(path, s) for s in SPLITS}


def run(args, tokenizer, score_fn):
    """Load, derive, score (score_fn(records) -> evaluate_behavior records, or
    None for the dry run), select, assemble and write. Returns
    (final, config, report), or None on the dry run."""
    src_dir = os.path.join(args.data_dir, args.task)
    honest_dir = src_dir.rstrip("/") + "_honest"
    out_dir = args.output_dir or os.path.join(args.data_dir,
                                              f"{args.task}_nopressure")
    src_config = dc.load_dataset_config(src_dir)
    model = args.model or src_config.get("model", dc.DEFAULT_MODEL)
    max_seq = (args.max_seq_length or src_config.get("max_seq_length")
               or dc.MAX_SEQ_LENGTH)
    thresholds = _check_thresholds(args.thresholds)
    minimums = {"train": args.min_train, "validation": args.min_train,
                "test": args.min_test}

    deceptive = {s: derive_split(r, "deceptive_split", tokenizer, max_seq)
                 for s, r in _load_splits(src_dir).items()}
    have_honest = os.path.exists(os.path.join(honest_dir, "dataset_dict.json"))
    honest = ({s: derive_split(r, "honest_split", tokenizer, max_seq)
               for s, r in _load_splits(honest_dir).items()}
              if have_honest else {})
    if not have_honest:
        print(f"WARNING: {honest_dir} not found; no honest-split fallback.")
    print(f"\nClause surgery + alignment OK: "
          f"deceptive {({s: len(v) for s, v in deceptive.items()})}, "
          f"honest {({s: len(v) for s, v in honest.items()})}")
    print(f"Thresholds {thresholds}, minimums {minimums}, model {model}, "
          f"max_seq_length {max_seq}")

    if score_fn is None:
        rng = random.Random(args.seed)
        for i, rec in enumerate(rng.sample(
                deceptive["train"], min(args.num_sample_pairs,
                                        len(deceptive["train"]))), 1):
            dc.print_sample_pair(tokenizer, rec, i, max_seq_length=max_seq)
        print(f"\n--no-model dry run: no forward passes; would write {out_dir}")
        return None

    deceptive_beh = {s: score_fn(deceptive[s]) for s in SPLITS}
    honest_beh = {s: score_fn(honest[s]) for s in honest}
    selection = select_threshold(deceptive_beh, thresholds, minimums)
    final, fallback = assemble(deceptive, deceptive_beh, honest, honest_beh,
                               selection)
    report = build_report(args, deceptive, deceptive_beh, honest, honest_beh,
                          selection, final, fallback)
    config = build_config(args, src_config, selection, final, model, max_seq,
                          src_dir, honest_dir if have_honest else None)

    print_summary(report, config)
    os.makedirs(out_dir, exist_ok=True)
    save_splits(final, out_dir)
    with open(os.path.join(out_dir, "dataset_config.json"), "w") as f:
        json.dump(config, f, indent=2)
    with open(os.path.join(out_dir, "filter_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved dataset_config.json and filter_report.json to {out_dir}")
    return final, config, report


def print_summary(report, config):
    print("\n" + "=" * 70)
    print(f"  {report['task'].upper()} NOPRESSURE FILTER REPORT")
    print("=" * 70)
    for step in report["per_threshold"]:
        print(f"  threshold {step['threshold']:.2f}: survivors "
              f"{step['survivors']}  meets minimums: {step['meets_minimums']}")
    print(f"Chosen margin_thresh {config['margin_thresh']} "
          f"(met minimums: {config['met_minimums']}); "
          f"source counts {config['source_counts']}")
    print(f"Fallback: {report['fallback']}")
    for key, label in (("pass_rate_by_item_pair", "item pair"),
                       ("pass_rate_by_item_polarity", "item polarity"),
                       ("pass_rate_by_designation_polarity",
                        "designation polarity"),
                       ("pass_rate_by_template_variant", "template variant")):
        print_pass_rate_table(label, report[key], max_rows=50)
    print(f"\nUnexpected argmax tokens: "
          f"{report['overall']['unexpected_argmax_tokens']}")


def main(argv=None):
    args = build_parser().parse_args(argv)
    src_config = dc.load_dataset_config(os.path.join(args.data_dir, args.task))
    model_name = args.model or src_config.get("model", dc.DEFAULT_MODEL)

    # Same loading as dataset/build_deception_dataset.py, which built the
    # source datasets.
    from transformers import AutoTokenizer

    from dataset.build_deception_dataset import resolve_hf_token
    hf_token = resolve_hf_token(args)
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    if args.no_model:
        return run(args, tokenizer, None)

    import torch
    from transformers import LlamaForCausalLM
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: no CUDA device; scoring an 8B model on CPU is very slow.")
    print(f"Loading {model_name} on {device}...")
    model = LlamaForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, token=hf_token).to(device).eval()
    max_seq = (args.max_seq_length or src_config.get("max_seq_length")
               or dc.MAX_SEQ_LENGTH)

    def score(records):
        return dc.evaluate_behavior(records, model, tokenizer, device,
                                    max_length=max_seq,
                                    batch_size=args.batch_size)
    return run(args, tokenizer, score)


if __name__ == "__main__":
    main()
