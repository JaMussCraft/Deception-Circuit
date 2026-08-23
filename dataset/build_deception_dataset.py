"""
build_deception_dataset.py — build one deception-mechanism dataset (FAR/SDR/SER).

Overgenerates chat-formatted clean/corrupt pairs from the shared content pools,
runs the filtering pipeline from `deception_tasks_shared.md`, and saves:

    <output-dir>/                        HF DatasetDict (train/validation/test)
    <output-dir>/dataset_config.json     build parameters (read at train time)
    <output-dir>/filter_report.json      pass rates, margins, histograms
    <output-dir>_honest/                 the honest twin, marginal-matched

Pipeline (steps 3-5 need a GPU node; 1-2 are CPU-only):

  1. generate + assert alignment          (--no-model stops here)
  2. tokenizer gate on the item pool
  3. prior-balance filter                 (--no-prior-filter to skip)
  4. behavioral filter (deceptive in both streams)
  5. honest-twin harvest from the failures + marginal resampling

The instance list is task-independent and seeded, so building all three tasks
with the same --seed and pools yields matched triplets: the same instances,
under the three predicates, with the same corruption site. Survivors are
subsampled in `instance_id` order rather than at random so the three tasks'
final splits overlap as much as their filters allow; the size of the three-way
intersection is reported whenever the sibling datasets already exist.

CPU-safe dry run:

    python dataset/build_deception_dataset.py --task far --no-model

Full builds (GPU):

    python dataset/build_deception_dataset.py --task far
    python dataset/build_deception_dataset.py --task sdr
    python dataset/build_deception_dataset.py --task ser
"""

import argparse
import json
import os
import random
import sys
from collections import Counter
from datetime import date

# Allow running both as `python dataset/build_deception_dataset.py` and from dataset/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataset import deception_common as dc
from dataset.report_utils import (histogram, length_summary, margin_summary,
                                  pass_rate_by, plot_margin_distributions,
                                  print_pass_rate_table,
                                  print_token_length_stats)


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(
        description="Build a deception-mechanism dataset (FAR / SDR / SER).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--task", choices=sorted(dc.SPECS), required=True)
    p.add_argument("--pools-dir", default=dc.POOLS_DIR,
                   help="Directory holding item_pairs.json, entities.json and "
                        "pressure_*.json.")
    p.add_argument("--train-samples", type=int, default=200)
    p.add_argument("--val-samples", type=int, default=200)
    p.add_argument("--test-samples", type=int, default=1000)
    p.add_argument("--overgen-factor", type=int, default=60,
                   help="Generate this many times the target size per split "
                        "before filtering. STD needed 60 at a ~2%% pass rate; "
                        "set it from the pilot's measured pass rate.")
    p.add_argument("--max-seq-length", type=int, default=dc.MAX_SEQ_LENGTH)
    p.add_argument("--margin-thresh", type=float, default=0.7,
                   help="Minimum logit margin required in both streams; "
                        "persisted to dataset_config.json.")
    p.add_argument("--prior-eps", type=float, default=0.5,
                   help="Prior-balance filter: keep examples whose neutral-prompt "
                        "|logit(item_1) - logit(item_2)| is below this.")
    p.add_argument("--no-prior-filter", action="store_true",
                   help="Skip the prior-balance filter (it costs one extra "
                        "forward pass per example).")
    p.add_argument("--match-length-distribution", action="store_true",
                   help="Restrict the flavor pressure clauses to a common "
                        "cross-task prompt-length band. The 5 shared clauses are "
                        "always kept.")
    p.add_argument("--no-honest-twin", action="store_true",
                   help="Skip the honest-twin harvest and its dataset.")
    p.add_argument("--model", default=dc.DEFAULT_MODEL)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--seed", type=int, default=42,
                   help="Must match across the three tasks for matched triplets.")
    p.add_argument("--num-sample-pairs", type=int, default=3,
                   help="Concrete clean/corrupt train pairs printed for inspection.")
    p.add_argument("--output-dir", default=None,
                   help="Default: data/datasets/<task>.")
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
# Pools
# ==============================================================================

def gate_item_pairs(tokenizer, pairs):
    """Drop any pair whose members are not single tokens with a leading space."""
    kept, dropped = [], []
    for pair in pairs:
        lengths = [len(tokenizer.encode(" " + w, add_special_tokens=False))
                   for w in pair]
        if all(n == 1 for n in lengths):
            kept.append(pair)
        else:
            dropped.append((pair, lengths))
    if dropped:
        print(f"\nTokenizer gate dropped {len(dropped)} item pair(s):")
        for pair, lengths in dropped:
            print(f"  {pair[0]}/{pair[1]}  token counts {lengths}")
    else:
        print("\nTokenizer gate: all item pairs are single-token. No drops.")
    return kept, [{"pair": f"{p[0]}/{p[1]}", "token_counts": n} for p, n in dropped]


def report_pools(tokenizer, task, entities, pairs, pressures):
    """Token-length statistics for every pool, as was done for STD."""
    n = lambda s: len(tokenizer.encode(s, add_special_tokens=False))
    print_token_length_stats("entities", [n(" " + e["name"]) for e in entities])
    print_token_length_stats("item words",
                             [n(" " + w) for pair in pairs for w in pair])
    flavor = [p for p in pressures if not p["shared"]]
    shared = [p for p in pressures if p["shared"]]
    print_token_length_stats(f"pressure clauses — {task} flavor",
                             [n(" " + p["text"]) for p in flavor])
    print_token_length_stats("pressure clauses — shared (mechanism-neutral)",
                             [n(" " + p["text"]) for p in shared])
    return {
        "entities": length_summary([n(" " + e["name"]) for e in entities]),
        "item_words": length_summary([n(" " + w) for pair in pairs for w in pair]),
        "pressure_flavor": length_summary([n(" " + p["text"]) for p in flavor]),
        "pressure_shared": length_summary([n(" " + p["text"]) for p in shared]),
    }


def allowed_length_matched_slots(tokenizer, task, pressures, pools_dir):
    """(pressure slots to keep for this task, task-independent inflation factor).

    The pool itself is never shortened: slot k has to keep meaning slot k in all
    three tasks or the instance ids stop lining up and the matched triplets are
    lost. Instances using a disallowed slot are dropped after generation
    instead, which costs sample count rather than comparability — each task then
    drops a *different* set of slots, so the three-way intersection narrows to
    the slots that were in-band everywhere.

    The inflation factor that compensates for those drops is computed from the
    WORST task, not from this one. It has to be task-independent: the generated
    count is what advances the shared `seen` set, so a per-task count would
    leave the three tasks with different `seen` sets after the first split and
    the later splits would stop being matched at all.

    The pools as shipped already sit within ~1 token of each other, so this is a
    tightening option rather than part of the default build.
    """
    selected = dc.select_length_matched_pressures(tokenizer, pools_dir=pools_dir)
    n_shared = sum(p["shared"] for p in pressures)
    keep = set(selected[task])
    slots = {p["slot"] for p in pressures if p["shared"] or p["id"] in keep}
    worst = min(len(ids) + n_shared for ids in selected.values())
    inflate = 1.1 * len(pressures) / worst   # 1.1 is headroom; slots are only
    print(f"\n--match-length-distribution: keeping {len(slots)}/{len(pressures)} "
          f"pressure slots for {task} ({len(keep)} flavor + {n_shared} shared). "
          f"Instances on other slots are discarded after generation so slot ids "
          f"stay comparable; generating {inflate:.2f}x to compensate (set by the "
          f"narrowest task, {worst} slots, so all three generate the same count).")
    return slots, inflate


# ==============================================================================
# Reporting
# ==============================================================================

def prompt_lengths(tokenizer, records):
    return [len(tokenizer.encode(r["clean_prompt"], add_special_tokens=False))
            for r in records]


def pass_rate_tables(records, behaviors):
    return {
        "pass_rate_by_item_pair": pass_rate_by(records, behaviors,
                                               lambda r: r["item_pair"]),
        "pass_rate_by_pressure": pass_rate_by(records, behaviors,
                                              lambda r: r["pressure_id"]),
        "pass_rate_by_entity": pass_rate_by(records, behaviors,
                                            lambda r: r["entity"]),
        "pass_rate_by_domain": pass_rate_by(records, behaviors,
                                            lambda r: r["domain"]),
        "pass_rate_by_designation_polarity": pass_rate_by(
            records, behaviors, lambda r: r["designation_polarity"]),
        "pass_rate_by_item_polarity": pass_rate_by(
            records, behaviors, lambda r: str(r["item_polarity"])),
        "pass_rate_by_template_variant": pass_rate_by(
            records, behaviors, lambda r: r["template_variant"]),
    }


def report_three_way_intersection(args, final_splits):
    """Instance ids shared with the sibling tasks' built datasets, if present.

    Reported PER SPLIT as well as overall. A union-over-splits count would stay
    healthy even if an instance landed in far/train but sdr/test, which is
    exactly the failure the matched-triplet design has to rule out — the paired
    comparison is only valid within a split.
    """
    from datasets import load_from_disk

    per_task = {args.task: {split: [r["instance_id"] for r in recs]
                            for split, recs in final_splits.items()}}
    for other in sorted(dc.SPECS):
        if other == args.task:
            continue
        path = os.path.join(os.path.dirname(args.output_dir), other)
        if not os.path.exists(os.path.join(path, "dataset_dict.json")):
            print(f"  {other}: not built yet — three-way intersection pending.")
            continue
        dd = load_from_disk(path)
        per_task[other] = {split: list(dd[split]["instance_id"]) for split in dd}

    report = {"tasks_available": sorted(per_task),
              "complete": len(per_task) == len(dc.SPECS), "splits": {}}
    print(f"\nComparison set across {sorted(per_task)}:")
    for split in final_splits:
        by_task = {t: [{"instance_id": i} for i in ids.get(split, [])]
                   for t, ids in per_task.items()}
        common, sizes = dc.three_way_intersection(by_task)
        report["splits"][split] = {"per_task_sizes": sizes,
                                   "intersection_size": len(common)}
        print(f"  {split:<11} per-task {sizes} -> {len(common)} shared")

    all_by_task = {t: [{"instance_id": i} for ids in splits.values() for i in ids]
                   for t, splits in per_task.items()}
    common_any, sizes_any = dc.three_way_intersection(all_by_task)
    within = sum(s["intersection_size"] for s in report["splits"].values())
    report["ignoring_splits"] = {"per_task_sizes": sizes_any,
                                 "intersection_size": len(common_any)}
    print(f"  ignoring splits: {len(common_any)} shared "
          f"({within} of them in the SAME split — only those are usable "
          f"for a paired comparison)")
    return report


# ==============================================================================
# Main
# ==============================================================================

def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.output_dir is None:
        args.output_dir = os.path.join("data", "datasets", args.task)
    spec = dc.SPECS[args.task]
    rng = random.Random(args.seed)

    from transformers import AutoTokenizer
    hf_token = resolve_hf_token(args)
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=hf_token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    print("=" * 70)
    print(f"  BUILDING {spec.display_name} — mechanism: {spec.mechanism}")
    print("=" * 70)
    print(f"Predicate: designated item is '{spec.desig_inversion}' (inversion) or "
          f"'{spec.desig_identity}' (identity)")

    # ----- Pools --------------------------------------------------------------
    entities = dc.load_entities(os.path.join(args.pools_dir, "entities.json"))
    pairs = dc.load_item_pairs(os.path.join(args.pools_dir, "item_pairs.json"))
    pressures = dc.load_pressures(args.task, args.pools_dir)

    pairs, dropped_pairs = gate_item_pairs(tokenizer, pairs)
    allowed_slots, inflate = None, 1.0
    if args.match_length_distribution:
        allowed_slots, inflate = allowed_length_matched_slots(
            tokenizer, args.task, pressures, args.pools_dir)
    pool_stats = report_pools(tokenizer, args.task, entities, pairs, pressures)
    print(f"\nPools: {len(entities)} entities, {len(pairs)} item pairs, "
          f"{len(pressures)} pressure clauses, {len(spec.variant_names)} template "
          f"variants -> {len(entities) * len(pairs) * len(pressures) * 4 * len(spec.variant_names):,} "
          f"unique instances available")

    # ----- Overgenerate per split (shared instance space) ---------------------
    targets = {"train": args.train_samples, "validation": args.val_samples,
               "test": args.test_samples}
    seen = set()
    raw_splits = {}
    for offset, (split, n_target) in enumerate(targets.items()):
        n_gen = n_target * args.overgen_factor
        # Generate over the full slot space (so instance ids stay comparable
        # across tasks), inflating to absorb the slots length matching drops.
        # `inflate` is task-independent — see allowed_length_matched_slots.
        records = dc.generate_task_data(
            tokenizer, spec, int(n_gen * inflate), entities, pairs, pressures,
            max_seq_length=args.max_seq_length, seed=args.seed + offset, seen=seen)
        if allowed_slots is not None:
            records = [r for r in records if r["pressure_slot"] in allowed_slots]
        raw_splits[split] = records[:n_gen]
        print(f"Generated {len(raw_splits[split])} aligned pairs for {split} "
              f"(target {n_target} after filtering)")

    all_raw = [r for split in raw_splits for r in raw_splits[split]]
    lengths = prompt_lengths(tokenizer, all_raw)
    length_stats, length_hist = length_summary(lengths), histogram(lengths)
    print_token_length_stats("full chat-formatted prompts (all generated examples)",
                             lengths)

    os.makedirs(args.output_dir, exist_ok=True)
    dataset_config = {
        "task": args.task,
        "mechanism": spec.mechanism,
        "condition": "deceptive",
        "model": args.model,
        "margin_thresh": args.margin_thresh,
        "prior_eps": None if args.no_prior_filter else args.prior_eps,
        "max_seq_length": args.max_seq_length,
        "designation_words": [spec.desig_inversion, spec.desig_identity],
        "template_variants": list(spec.variant_names),
        "n_entities": len(entities),
        "n_item_pairs": len(pairs),
        "n_pressures": len(pressures),
        "match_length_distribution": args.match_length_distribution,
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
        print("\n--no-model dry run: skipping filtering and save_to_disk.")
        for i, rec in enumerate(rng.sample(raw_splits["train"],
                                           min(args.num_sample_pairs,
                                               len(raw_splits["train"]))), 1):
            dc.print_sample_pair(tokenizer, rec, i,
                                 max_seq_length=args.max_seq_length)
        return

    # ----- Load the base model ------------------------------------------------
    import torch
    from transformers import LlamaForCausalLM

    if not torch.cuda.is_available():
        print("\nWARNING: no CUDA device — filtering an 8B model on CPU will be "
              "extremely slow. Consider a GPU node.")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\nLoading {args.model} on {device} for filtering...")
    model = LlamaForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, token=hf_token).to(device).eval()

    report = {"task": args.task, "mechanism": spec.mechanism,
              "margin_thresh": args.margin_thresh,
              "prior_eps": None if args.no_prior_filter else args.prior_eps,
              "pool_token_lengths": pool_stats,
              "dropped_item_pairs": dropped_pairs,
              "prompt_length": {"summary": length_stats, "histogram": length_hist},
              "splits": {}}

    final_splits, honest_splits = {}, {}
    all_records, all_behaviors = [], []
    split_behaviors = {}
    total_unexpected = Counter()
    honest_reports = {}

    for split, raw in raw_splits.items():
        print(f"\n===== Filtering split: {split} =====")

        # --- step 3: prior balance -------------------------------------------
        prior_summary = None
        if args.no_prior_filter:
            balanced = raw
        else:
            balanced, prior_margins = dc.filter_by_prior_balance(
                raw, model, tokenizer, device, eps=args.prior_eps,
                max_length=args.max_seq_length, batch_size=args.batch_size)
            for rec, m in zip(raw, prior_margins):
                rec["prior_margin"] = m["prior_margin"]
            prior_summary = {
                "kept": len(balanced),
                "of": len(raw),
                "rate": len(balanced) / max(len(raw), 1),
                "margin": margin_summary([m["prior_margin"] for m in prior_margins]),
                "drop_rate_by_item_pair": {
                    k: 1 - v["rate"] for k, v in pass_rate_by(
                        raw, [{"passed": m["kept"]} for m in prior_margins],
                        lambda r: r["item_pair"]).items()},
            }

        # --- step 4: behavioral filter ---------------------------------------
        survivors, behaviors, unexpected = dc.filter_by_model_behavior(
            balanced, model, tokenizer, device, margin_thresh=args.margin_thresh,
            max_length=args.max_seq_length, batch_size=args.batch_size)
        total_unexpected.update(unexpected)
        all_records.extend(balanced)
        all_behaviors.extend(behaviors)
        split_behaviors[split] = behaviors

        for rec, b in zip(balanced, behaviors):
            rec["clean_margin"] = b["clean_margin"]
            rec["corrupt_margin"] = b["corrupt_margin"]

        n_target = targets[split]
        final_splits[split] = take_split(survivors, n_target, split)

        # --- step 5: honest twins --------------------------------------------
        if not args.no_honest_twin:
            harvested = dc.harvest_honest_twins(balanced, behaviors,
                                                margin_thresh=args.margin_thresh)
            # The failures vastly outnumber the survivors, and the marginal
            # matcher is O(pool x selected); cap the pool at 5x the target.
            honest_pool = take_split(harvested, 5 * n_target, f"{split} (honest)",
                                     warn=False)
            matched, hrep = dc.resample_to_match_marginals(
                honest_pool, final_splits[split], seed=args.seed)
            hrep["n_harvested"] = len(harvested)
            honest_splits[split] = matched
            honest_reports[split] = hrep
            print(f"  Honest twin: {len(harvested)} harvested "
                  f"({len(honest_pool)} after capping), "
                  f"{len(matched)} kept after marginal matching")

        report["splits"][split] = {
            "generated": len(raw),
            "prior_balance": prior_summary,
            "behavioral_input": len(balanced),
            "survived": len(survivors),
            "pass_rate": len(survivors) / max(len(balanced), 1),
            "kept": len(final_splits[split]),
            "honest_kept": len(honest_splits.get(split, [])),
            "clean_margin": margin_summary([b["clean_margin"] for b in behaviors]),
            "corrupt_margin": margin_summary([b["corrupt_margin"] for b in behaviors]),
        }

    # ----- Report -------------------------------------------------------------
    # max(..., 1): a filter can legitimately empty a split, and crashing here
    # would throw away every GPU hour spent above without writing the report
    # that says why.
    overall_pass = (sum(int(b["passed"]) for b in all_behaviors) /
                    max(len(all_behaviors), 1))
    report["overall"] = {
        "generated": len(all_behaviors),
        "pass_rate": overall_pass,
        "clean_margin": margin_summary([b["clean_margin"] for b in all_behaviors]),
        "corrupt_margin": margin_summary([b["corrupt_margin"] for b in all_behaviors]),
        "unexpected_argmax_tokens": dict(total_unexpected.most_common()),
    }
    report.update(pass_rate_tables(all_records, all_behaviors))
    if honest_reports:
        report["honest_marginal_match"] = honest_reports
    report["comparison_set"] = report_three_way_intersection(args, final_splits)

    print("\n" + "=" * 70)
    print(f"  {args.task.upper()} FILTER REPORT")
    print("=" * 70)
    print(f"\nOverall pass rate: {overall_pass*100:.2f}% "
          f"({sum(int(b['passed']) for b in all_behaviors)}/{len(all_behaviors)})")
    for split, s in report["splits"].items():
        print(f"  {split:<11} {s['pass_rate']*100:6.2f}%  "
              f"({s['survived']}/{s['behavioral_input']}, kept {s['kept']}, "
              f"honest {s['honest_kept']})")
    print_pass_rate_table("item pair", report["pass_rate_by_item_pair"], max_rows=20)
    print_pass_rate_table("pressure clause", report["pass_rate_by_pressure"],
                          max_rows=20)
    print_pass_rate_table("designation polarity",
                          report["pass_rate_by_designation_polarity"])
    print_pass_rate_table("item polarity", report["pass_rate_by_item_polarity"])
    print_pass_rate_table("template variant",
                          report["pass_rate_by_template_variant"])
    print_pass_rate_table("domain", report["pass_rate_by_domain"])
    print_pass_rate_table("entity", report["pass_rate_by_entity"], max_rows=10)
    for stream in ("clean_margin", "corrupt_margin"):
        s = report["overall"][stream]
        if not s["n"]:
            print(f"\n{stream} distribution: (no examples reached the filter)")
            continue
        print(f"\n{stream} distribution (all filtered-in examples): "
              f"mean={s['mean']:.2f} std={s['std']:.2f} | " +
              " ".join(f"p{q}={s[f'p{q}']:.2f}" for q in (1, 5, 25, 50, 75, 95, 99)))
    print("\nUnexpected argmax tokens (neither target nor distractor), by count:")
    if total_unexpected:
        for tok_repr, cnt in total_unexpected.most_common(20):
            print(f"  {cnt:>5}  {tok_repr}")
    else:
        print("  (none)")

    report_path = os.path.join(args.output_dir, "filter_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved filter report to {report_path}")

    try:
        plot_margin_distributions(
            split_behaviors, args.margin_thresh,
            os.path.join(args.output_dir, "margin_distributions.pdf"),
            task_label=args.task.upper())
        plot_margin_distributions(
            split_behaviors, args.margin_thresh,
            os.path.join(args.output_dir, "margin_distributions_filtered.pdf"),
            only_passed=True, task_label=args.task.upper())
    except ImportError as e:
        print(f"Skipping margin distribution plots (matplotlib unavailable: {e})")

    # ----- Sample pairs for manual inspection ---------------------------------
    print("\n" + "=" * 70)
    print(f"  {args.num_sample_pairs} RANDOM TRAIN PAIRS FOR MANUAL INSPECTION")
    print("=" * 70)
    for i, rec in enumerate(rng.sample(final_splits["train"],
                                       min(args.num_sample_pairs,
                                           len(final_splits["train"]))), 1):
        dc.print_sample_pair(tokenizer, rec, i, max_seq_length=args.max_seq_length)

    # ----- Save ---------------------------------------------------------------
    save_splits(final_splits, args.output_dir)
    if honest_splits:
        honest_dir = args.output_dir.rstrip("/") + "_honest"
        os.makedirs(honest_dir, exist_ok=True)
        with open(os.path.join(honest_dir, "dataset_config.json"), "w") as f:
            json.dump({**dataset_config, "condition": "honest"}, f, indent=2)
        save_splits(honest_splits, honest_dir)


def take_split(records, n_target, label, warn=True):
    """Deterministic subsample in instance_id order.

    Sorting by the (hashed) instance id is a fixed pseudo-random order that is
    the SAME in all three tasks, so taking a prefix maximises the three-way
    intersection instead of shrinking it the way independent random sampling
    would.
    """
    ordered = sorted(records, key=lambda r: r["instance_id"])
    if len(ordered) < n_target:
        if warn:
            print(f"WARNING: only {len(ordered)} survivors for {label} "
                  f"(target {n_target}) — keeping all. Raise --overgen-factor or "
                  f"lower --margin-thresh and rebuild.")
        return ordered
    return ordered[:n_target]


def save_splits(splits, output_dir):
    from datasets import Dataset, DatasetDict
    dd = DatasetDict({split: Dataset.from_list(records)
                      for split, records in splits.items()})
    dd.save_to_disk(output_dir)
    print(f"\nSaved DatasetDict to {output_dir} "
          f"({ {k: len(v) for k, v in splits.items()} })")


if __name__ == "__main__":
    main()
