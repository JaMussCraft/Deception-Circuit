"""
build_std_dataset.py — build the Stipulated-Truth Deception (STD) dataset.

Overgenerates chat-formatted clean/corrupt example pairs, filters them for
deceptive base-model behavior in BOTH streams (argmax == deceptive target with
a logit margin over the distractor >= --margin-thresh), subsamples the
survivors to exact split sizes, and saves:

    <output-dir>/                      HF DatasetDict (train/validation/test)
    <output-dir>/dataset_config.json   build parameters (read at train time)
    <output-dir>/filter_report.json    pass rates + margin distributions

Run on a GPU node (the filter runs Llama-3.1-8B-Instruct). A CPU-safe dry run
that only generates, asserts alignment, prints statistics and 3 sample pairs:

    python dataset/build_std_dataset.py --no-model --statement-source azaria

Full builds:

    python dataset/build_std_dataset.py --statement-source azaria
    python dataset/build_std_dataset.py --statement-source neutral
"""

import argparse
import csv
import json
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date

# Allow running both as `python dataset/build_std_dataset.py` and from dataset/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataset.std_llama import (STIP_PAIRS, DEFAULT_PRESSURES_PATH,
                               DEFAULT_NEUTRAL_FACTS_PATH,
                               generate_std_data, filter_std_by_model_behavior,
                               load_pressure_clauses, load_neutral_facts,
                               print_sample_pair)

DEFAULT_AZARIA_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "liars-bench", "data", "raw", "azaria_mitchell", "facts_true_false.csv")


# ==============================================================================
# CLI
# ==============================================================================

def parse_stip_pairs(spec: str):
    pairs = []
    for part in spec.split(","):
        pos, neg = part.strip().split("/")
        pairs.append((pos.strip(), neg.strip()))
    return pairs


def build_parser():
    p = argparse.ArgumentParser(
        description="Build the Stipulated-Truth Deception (STD) dataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--statement-source", choices=["azaria", "neutral"], default="azaria")
    p.add_argument("--azaria-csv", default=DEFAULT_AZARIA_CSV)
    p.add_argument("--neutral-facts", default=DEFAULT_NEUTRAL_FACTS_PATH)
    p.add_argument("--pressures", default=DEFAULT_PRESSURES_PATH)
    p.add_argument("--stip-pairs", type=parse_stip_pairs,
                   default=STIP_PAIRS, metavar="P/N,P/N,...",
                   help="Comma-separated pos/neg stipulation lexeme pairs "
                        "(default: true/false,correct/incorrect,accurate/inaccurate,"
                        "right/wrong,good/bad).")
    p.add_argument("--train-samples", type=int, default=200)
    p.add_argument("--val-samples", type=int, default=200)
    p.add_argument("--test-samples", type=int, default=1000)
    p.add_argument("--overgen-factor", type=int, default=4,
                   help="Generate this many times the target size per split "
                        "before behavioral filtering.")
    p.add_argument("--max-statement-tokens", type=int, default=12)
    p.add_argument("--max-seq-length", type=int, default=80)
    p.add_argument("--margin-thresh", type=float, default=1.0,
                   help="Minimum logit margin (target - distractor) required in "
                        "both streams; persisted to dataset_config.json.")
    p.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--num-sample-pairs", type=int, default=3,
                   help="Concrete clean/corrupt train pairs printed for inspection.")
    p.add_argument("--output-dir", default=None,
                   help="Default: data/datasets/std_<statement-source>.")
    p.add_argument("--no-model", action="store_true",
                   help="Dry run (CPU-safe): generate, assert alignment, print "
                        "stats and sample pairs; no filtering, nothing saved "
                        "except dataset_config.json.")
    p.add_argument("--hf-token", default=None)
    return p


def resolve_hf_token(args):
    if args.hf_token:
        return args.hf_token
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    for cand in ("../hf_tokken.txt", "hf_tokken.txt"):
        if os.path.exists(cand):
            with open(cand) as f:
                tok = f.read().strip()
            if tok:
                print(f"Loaded HF token from {cand}")
                return tok
    return None


# ==============================================================================
# Statistics helpers
# ==============================================================================

def percentile(values, q):
    vals = sorted(values)
    idx = min(int(round(q / 100 * (len(vals) - 1))), len(vals) - 1)
    return vals[idx]


def print_token_length_stats(name, lengths):
    print(f"\nToken-length statistics — {name} (n={len(lengths)}):")
    print(f"  min={min(lengths)}  mean={statistics.mean(lengths):.1f}  "
          f"median={statistics.median(lengths)}  p90={percentile(lengths, 90)}  "
          f"max={max(lengths)}")


def margin_summary(margins):
    return {
        "n": len(margins),
        "mean": statistics.mean(margins),
        "std": statistics.pstdev(margins) if len(margins) > 1 else 0.0,
        **{f"p{q}": percentile(margins, q) for q in (1, 5, 25, 50, 75, 95, 99)},
    }


def pass_rate_by(records, behaviors, key_fn):
    """Pass-rate per group: {group: {"passed": int, "total": int, "rate": float}}."""
    grouped = defaultdict(lambda: [0, 0])
    for rec, b in zip(records, behaviors):
        g = grouped[key_fn(rec)]
        g[1] += 1
        g[0] += int(b["passed"])
    return {k: {"passed": p, "total": t, "rate": p / t}
            for k, (p, t) in sorted(grouped.items())}


def print_pass_rate_table(title, rates, max_rows=None):
    print(f"\nPass rate by {title}:")
    rows = sorted(rates.items(), key=lambda kv: kv[1]["rate"])
    if max_rows is not None and len(rows) > max_rows:
        shown = rows[:max_rows // 2] + rows[-(max_rows - max_rows // 2):]
        print(f"  (showing {max_rows} lowest/highest of {len(rows)} groups; "
              f"full table in filter_report.json)")
    else:
        shown = rows
    for k, v in shown:
        print(f"  {v['rate']*100:6.1f}%  ({v['passed']:>4}/{v['total']:<4})  {k}")


# ==============================================================================
# Data loading
# ==============================================================================

def load_azaria_statements(csv_path):
    """Return [(statement, label)] with label 1 (true) / 0 (false)."""
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    return [(r["statement"].strip(), int(r["label"])) for r in rows]


# ==============================================================================
# Main
# ==============================================================================

def main():
    args = build_parser().parse_args()
    if args.output_dir is None:
        args.output_dir = os.path.join("data", "datasets", f"std_{args.statement_source}")
    rng = random.Random(args.seed)

    from transformers import AutoTokenizer
    hf_token = resolve_hf_token(args)
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=hf_token)

    def n_tokens(text):
        return len(tokenizer.encode(text, add_special_tokens=False))

    # ----- Load statements and pressure clauses; report length statistics ----
    pressures = load_pressure_clauses(args.pressures)
    # Clauses follow a space in the system prompt, so measure with leading space.
    print_token_length_stats(f"pressure clauses ({args.pressures})",
                             [n_tokens(" " + c) for c in pressures])

    if args.statement_source == "azaria":
        all_statements = load_azaria_statements(args.azaria_csv)
        print_token_length_stats(
            f"UNFILTERED Azaria-Mitchell statements ({args.azaria_csv})",
            [n_tokens(s) for s, _ in all_statements])
    else:
        all_statements = [(s, -1) for s in load_neutral_facts(args.neutral_facts)]
        print_token_length_stats(
            f"neutral statements ({args.neutral_facts})",
            [n_tokens(s) for s, _ in all_statements])

    statements = [(s, l) for s, l in all_statements
                  if n_tokens(s) <= args.max_statement_tokens and '"' not in s]
    labels = Counter(l for _, l in statements)
    print(f"\nStatements kept after <= {args.max_statement_tokens}-token filter: "
          f"{len(statements)}/{len(all_statements)} (labels: {dict(labels)})")

    # ----- Overgenerate per split (shared statement pool, unique configs) ----
    targets = {"train": args.train_samples, "validation": args.val_samples,
               "test": args.test_samples}
    seen = set()
    raw_splits = {}
    for offset, (split, n_target) in enumerate(targets.items()):
        n_gen = n_target * args.overgen_factor
        raw_splits[split] = generate_std_data(
            tokenizer, n_gen, statements, pressures,
            stip_pairs=args.stip_pairs, max_seq_length=args.max_seq_length,
            seed=args.seed + offset, seen=seen)
        print(f"Generated {len(raw_splits[split])} aligned pairs for {split} "
              f"(target {n_target} after filtering)")

    print_token_length_stats(
        "full chat-formatted prompts (all generated examples)",
        [len(tokenizer.encode(r["clean_prompt"], add_special_tokens=False))
         for split in raw_splits for r in raw_splits[split]])

    os.makedirs(args.output_dir, exist_ok=True)
    dataset_config = {
        "task": "std",
        "statement_source": args.statement_source,
        "model": args.model,
        "margin_thresh": args.margin_thresh,
        "max_seq_length": args.max_seq_length,
        "max_statement_tokens": args.max_statement_tokens,
        "stip_pairs": [list(p) for p in args.stip_pairs],
        "overgen_factor": args.overgen_factor,
        "seed": args.seed,
        "train_samples": args.train_samples,
        "val_samples": args.val_samples,
        "test_samples": args.test_samples,
        "filtered": not args.no_model,
        "created": date.today().isoformat(),
    }
    config_path = os.path.join(args.output_dir, "dataset_config.json")
    with open(config_path, "w") as f:
        json.dump(dataset_config, f, indent=2)
    print(f"\nSaved build parameters to {config_path}")

    if args.no_model:
        print("\n--no-model dry run: skipping behavioral filtering and save_to_disk.")
        show = rng.sample(raw_splits["train"],
                          min(args.num_sample_pairs, len(raw_splits["train"])))
        for i, rec in enumerate(show, 1):
            print_sample_pair(tokenizer, rec, i, max_seq_length=args.max_seq_length)
        return

    # ----- Behavioral filtering with the full model --------------------------
    import torch
    from transformers import LlamaForCausalLM

    if not torch.cuda.is_available():
        print("\nWARNING: no CUDA device — filtering an 8B model on CPU will be "
              "extremely slow. Consider a GPU node.")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\nLoading {args.model} on {device} for behavioral filtering...")
    model = LlamaForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, token=hf_token).to(device).eval()

    final_splits = {}
    report = {"margin_thresh": args.margin_thresh, "splits": {}}
    all_records, all_behaviors = [], []
    total_unexpected = Counter()

    for split, raw in raw_splits.items():
        print(f"\n===== Filtering split: {split} =====")
        survivors, behaviors, unexpected = filter_std_by_model_behavior(
            raw, model, tokenizer, device, margin_thresh=args.margin_thresh,
            max_length=args.max_seq_length, batch_size=args.batch_size)
        total_unexpected.update(unexpected)
        all_records.extend(raw)
        all_behaviors.extend(behaviors)

        # Attach margins to the surviving records before saving.
        margins = {id(rec): b for rec, b in zip(raw, behaviors)}
        for rec in survivors:
            rec["clean_margin"] = margins[id(rec)]["clean_margin"]
            rec["corrupt_margin"] = margins[id(rec)]["corrupt_margin"]

        n_target = targets[split]
        if len(survivors) < n_target:
            print(f"WARNING: only {len(survivors)} survivors for {split} "
                  f"(target {n_target}) — keeping all. Raise --overgen-factor "
                  f"or lower --margin-thresh and rebuild.")
            final_splits[split] = survivors
        else:
            idx = sorted(rng.sample(range(len(survivors)), n_target))
            final_splits[split] = [survivors[i] for i in idx]

        report["splits"][split] = {
            "generated": len(raw),
            "survived": len(survivors),
            "pass_rate": len(survivors) / len(raw),
            "kept": len(final_splits[split]),
            "clean_margin": margin_summary([b["clean_margin"] for b in behaviors]),
            "corrupt_margin": margin_summary([b["corrupt_margin"] for b in behaviors]),
        }

    # ----- Report -------------------------------------------------------------
    overall_pass = sum(int(b["passed"]) for b in all_behaviors) / len(all_behaviors)
    report["overall"] = {
        "generated": len(all_behaviors),
        "pass_rate": overall_pass,
        "clean_margin": margin_summary([b["clean_margin"] for b in all_behaviors]),
        "corrupt_margin": margin_summary([b["corrupt_margin"] for b in all_behaviors]),
        "unexpected_argmax_tokens": dict(total_unexpected.most_common()),
    }
    report["pass_rate_by_stip_pair"] = pass_rate_by(
        all_records, all_behaviors, lambda r: f"{r['stip_pos']}/{r['stip_neg']}")
    report["pass_rate_by_pressure"] = pass_rate_by(
        all_records, all_behaviors, lambda r: r["pressure"])
    report["pass_rate_by_statement"] = pass_rate_by(
        all_records, all_behaviors, lambda r: r["statement"])
    report["pass_rate_by_polarity"] = pass_rate_by(
        all_records, all_behaviors, lambda r: r["polarity"])

    print("\n" + "=" * 70)
    print("  BEHAVIORAL FILTER REPORT")
    print("=" * 70)
    print(f"\nOverall pass rate: {overall_pass*100:.1f}% "
          f"({sum(int(b['passed']) for b in all_behaviors)}/{len(all_behaviors)})")
    for split, s in report["splits"].items():
        print(f"  {split:<11} {s['pass_rate']*100:6.1f}%  "
              f"({s['survived']}/{s['generated']}, kept {s['kept']})")
    print_pass_rate_table("stipulation lexeme pair", report["pass_rate_by_stip_pair"])
    print_pass_rate_table("polarity (lexeme the clean prompt stipulates)",
                          report["pass_rate_by_polarity"])
    print_pass_rate_table("pressure clause", report["pass_rate_by_pressure"])
    print_pass_rate_table("statement", report["pass_rate_by_statement"], max_rows=20)
    for stream in ("clean_margin", "corrupt_margin"):
        s = report["overall"][stream]
        print(f"\n{stream} distribution (all generated examples): "
              f"mean={s['mean']:.2f} std={s['std']:.2f} | " +
              " ".join(f"p{q}={s[f'p{q}']:.2f}" for q in (1, 5, 25, 50, 75, 95, 99)))
    print(f"\nUnexpected argmax tokens (neither target nor distractor), by count:")
    if total_unexpected:
        for tok_repr, cnt in total_unexpected.most_common():
            print(f"  {cnt:>5}  {tok_repr}")
    else:
        print("  (none)")

    report_path = os.path.join(args.output_dir, "filter_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved filter report to {report_path}")

    # ----- Sample pairs for manual inspection ---------------------------------
    print("\n" + "=" * 70)
    print(f"  {args.num_sample_pairs} RANDOM TRAIN PAIRS FOR MANUAL INSPECTION")
    print("=" * 70)
    show = rng.sample(final_splits["train"],
                      min(args.num_sample_pairs, len(final_splits["train"])))
    for i, rec in enumerate(show, 1):
        print_sample_pair(tokenizer, rec, i, max_seq_length=args.max_seq_length)

    # ----- Save ---------------------------------------------------------------
    from datasets import Dataset, DatasetDict
    dd = DatasetDict({split: Dataset.from_list(records)
                      for split, records in final_splits.items()})
    dd.save_to_disk(args.output_dir)
    print(f"\nSaved DatasetDict to {args.output_dir} "
          f"({ {k: len(v) for k, v in final_splits.items()} })")


if __name__ == "__main__":
    main()
