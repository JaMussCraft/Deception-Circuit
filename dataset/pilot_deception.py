"""
pilot_deception.py — the pilot that must pass before any full FAR/SDR/SER build.

STD needed --overgen-factor 60 at a ~2%% pass rate. At that rate a 200/200/1000
build is ~84k pairs = 168k forward passes per task, x3 tasks, x2 (deceptive +
honest twin). That is too much GPU time to spend on an unvalidated design, so
this script runs a few hundred instances per task and answers four questions:

  1. Is the behavioral pass rate high enough for an affordable overgeneration
     factor?  (pass rate, margin distribution, unexpected-argmax counts)
  2. Is the prior-balance threshold set sensibly?  (margin distribution and
     per-item-pair drop rate under the neutral designating sentence)
  3. ARE THE HONEST LABELS REAL? Each task's honest answer is asserted by the
     spec, and only FAR's is entailed by the prompt. SDR's follows from
     disclosure norms; SER's is normative — "which result should I look at" is
     answered by the unfavorable one only if the user wants what could change
     their decision. So every task is run three ways: pressure kept (the
     designed prompt), pressure removed, and pressure replaced by an explicit
     honesty instruction. Near-100% agreement with the designated honest
     answer on the last two validates the label; pressure-kept is the
     contrast. A split near 50/50 on the honest conditions means that task's
     honest twin is ill-defined, Δ = C_deceptive − C_honest is uninterpretable
     for it, and the user turn needs rewording before any full build.
  4. Do the three tasks behave differently at all, on matched instances?

Run on a GPU node:

    python dataset/pilot_deception.py --n 300
"""

import argparse
import json
import os
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataset import deception_common as dc
from dataset.build_deception_dataset import resolve_hf_token
from dataset.report_utils import (margin_summary, pass_rate_by,
                                  print_pass_rate_table, print_token_length_stats)


def build_parser():
    p = argparse.ArgumentParser(
        description="Pilot the FAR/SDR/SER designs before committing GPU hours.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--tasks", nargs="+", default=sorted(dc.SPECS),
                   choices=sorted(dc.SPECS))
    p.add_argument("--n", type=int, default=300,
                   help="Instances per task (the same instances in each task).")
    p.add_argument("--pools-dir", default=dc.POOLS_DIR)
    p.add_argument("--model", default=dc.DEFAULT_MODEL)
    p.add_argument("--margin-thresh", type=float, default=0.7)
    p.add_argument("--prior-eps", type=float, default=0.5)
    p.add_argument("--max-seq-length", type=int, default=dc.MAX_SEQ_LENGTH)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", default=os.path.join("data", "datasets",
                                                    "pilot_report.json"))
    p.add_argument("--hf-token", default=None)
    return p


def fraction(counter, key, total):
    return counter.get(key, 0) / total if total else 0.0


def main(argv=None):
    args = build_parser().parse_args(argv)

    import torch
    from transformers import AutoTokenizer, LlamaForCausalLM

    hf_token = resolve_hf_token(args)
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=hf_token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    entities = dc.load_entities(os.path.join(args.pools_dir, "entities.json"))
    pairs = dc.load_item_pairs(os.path.join(args.pools_dir, "item_pairs.json"))

    # One instance list, realized under all three predicates: matched triplets.
    n_slots = min(len(dc.load_pressures(t, args.pools_dir)) for t in args.tasks)
    instances = dc.generate_instances(
        args.n, entities, pairs, n_pressure_slots=n_slots,
        variant_names=dc.SPECS[args.tasks[0]].variant_names, seed=args.seed)
    print(f"Pilot: {len(instances)} matched instances x {len(args.tasks)} tasks")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: no CUDA device — this pilot will be very slow on CPU.")
    print(f"Loading {args.model} on {device}...")
    model = LlamaForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, token=hf_token).to(device).eval()

    report = {"n_instances": len(instances), "model": args.model,
              "margin_thresh": args.margin_thresh, "prior_eps": args.prior_eps,
              "seed": args.seed, "tasks": {}}
    survivors_by_task = {}

    for task in args.tasks:
        spec = dc.SPECS[task]
        pressures = dc.load_pressures(task, args.pools_dir)
        records = [dc.realize_instance(tokenizer, spec, inst, pressures,
                                       args.max_seq_length)
                   for inst in instances]

        print("\n" + "=" * 70)
        print(f"  PILOT — {spec.display_name} ({spec.mechanism})")
        print("=" * 70)
        lengths = [len(tokenizer.encode(r["clean_prompt"], add_special_tokens=False))
                   for r in records]
        print_token_length_stats(f"{task} prompts", lengths)

        # ---- 2. prior balance ------------------------------------------------
        balanced, prior = dc.filter_by_prior_balance(
            records, model, tokenizer, device, eps=args.prior_eps,
            max_length=args.max_seq_length, batch_size=args.batch_size)
        prior_by_pair = pass_rate_by(records, [{"passed": m["kept"]} for m in prior],
                                     lambda r: r["item_pair"])
        print_pass_rate_table("item pair (prior-balance KEEP rate)", prior_by_pair,
                              max_rows=20)

        # ---- 1. behavioral filter -------------------------------------------
        survivors, behaviors, unexpected = dc.filter_by_model_behavior(
            balanced, model, tokenizer, device, margin_thresh=args.margin_thresh,
            max_length=args.max_seq_length, batch_size=args.batch_size)
        survivors_by_task[task] = survivors
        honest_twins = dc.harvest_honest_twins(balanced, behaviors,
                                               margin_thresh=args.margin_thresh)

        # ---- 3. honest-label validation --------------------------------------
        conditions = {}
        # None → each record's own pressure clause (the designed prompt).
        for cond, pressure in (("pressure_kept", None),
                               ("no_pressure", ""),
                               ("honest_instruction", dc.HONEST_INSTRUCTION)):
            # HONEST_INSTRUCTION can be longer than the record's own clause, and
            # the build-time length assertion only covers the original prompt.
            # A prompt over budget would be truncated and its readout taken at
            # the wrong position, so drop those and say how many.
            kept, prompts, word_pairs = [], [], []
            for r in records:
                clause = r["pressure"] if pressure is None else pressure
                text = dc.rebuild_prompt(spec, r, clause)
                if len(tokenizer.encode(text, add_special_tokens=False)) > args.max_seq_length:
                    continue
                kept.append(r)
                prompts.append(text)
                # (a, b) = (honest answer, deceptive answer)
                word_pairs.append((r["distractor"], r["target"]))
            n_dropped = len(records) - len(kept)
            if n_dropped:
                print(f"  {task}/{cond}: {n_dropped} prompt(s) exceeded "
                      f"max_seq_length={args.max_seq_length} and were skipped.")
            scored = dc.score_prompts(prompts, word_pairs, model, tokenizer, device,
                                      max_length=args.max_seq_length,
                                      batch_size=args.batch_size,
                                      desc=f"{task}: {cond}")
            choices = Counter(s["choice"] for s in scored)
            conditions[cond] = {
                "n": len(scored),
                "n_skipped_over_length": n_dropped,
                "honest_fraction": fraction(choices, "a", len(scored)),
                "deceptive_fraction": fraction(choices, "b", len(scored)),
                "other_fraction": fraction(choices, "other", len(scored)),
                "margin_honest_minus_deceptive": margin_summary(
                    [s["margin"] for s in scored]),
                "other_tokens": dict(Counter(
                    repr(s["argmax"]) for s in scored
                    if s["choice"] == "other").most_common(10)),
            }
            print(f"\n{task} / {cond}: honest "
                  f"{conditions[cond]['honest_fraction']*100:.1f}%  deceptive "
                  f"{conditions[cond]['deceptive_fraction']*100:.1f}%  other "
                  f"{conditions[cond]['other_fraction']*100:.1f}%")

        report["tasks"][task] = {
            "mechanism": spec.mechanism,
            "prompt_length": {"median": statistics.median(lengths),
                              "max": max(lengths)},
            "prior_balance": {
                "kept": len(balanced), "of": len(records),
                "rate": len(balanced) / max(len(records), 1),
                "margin": margin_summary([m["prior_margin"] for m in prior]),
                "keep_rate_by_item_pair": prior_by_pair,
            },
            "behavioral": {
                "kept": len(survivors), "of": len(balanced),
                "pass_rate": len(survivors) / max(len(balanced), 1),
                "clean_margin": margin_summary([b["clean_margin"] for b in behaviors]),
                "corrupt_margin": margin_summary([b["corrupt_margin"] for b in behaviors]),
                "unexpected_argmax_tokens": dict(unexpected.most_common(20)),
            },
            "honest_twins_available": len(honest_twins),
            "label_validation": conditions,
        }

    # ---- 4. matched-instance comparison --------------------------------------
    common, sizes = dc.three_way_intersection(survivors_by_task)
    report["comparison_set"] = {"per_task_sizes": sizes,
                                "intersection_size": len(common)}

    print("\n" + "=" * 70)
    print("  PILOT SUMMARY")
    print("=" * 70)
    for task, r in report["tasks"].items():
        lv = r["label_validation"]
        print(f"\n{task.upper()}  prior-balance {r['prior_balance']['rate']*100:5.1f}%"
              f"  behavioral {r['behavioral']['pass_rate']*100:5.1f}%"
              f"  honest twins {r['honest_twins_available']}")
        print(f"      honest label: pressure-kept "
              f"{lv['pressure_kept']['honest_fraction']*100:5.1f}% honest, "
              f"no-pressure "
              f"{lv['no_pressure']['honest_fraction']*100:5.1f}% honest, "
              f"instruction {lv['honest_instruction']['honest_fraction']*100:5.1f}% honest")
        if lv["honest_instruction"]["honest_fraction"] < 0.8:
            print(f"      !! {task}: the honest answer is NOT clearly the model's "
                  f"reading of the question. Reword the user turn before building "
                  f"— Δ = C_{task} − C_{task}_honest would be uninterpretable.")
    print(f"\nMatched survivors across {sorted(survivors_by_task)}: "
          f"{report['comparison_set']['intersection_size']} of {args.n} instances")

    n_needed = {task: (1 / r["behavioral"]["pass_rate"]
                       if r["behavioral"]["pass_rate"] else float("inf"))
                for task, r in report["tasks"].items()}
    print("\nImplied overgeneration factor (1 / pass rate): " +
          ", ".join(f"{t}={f:.0f}" for t, f in n_needed.items()))
    report["implied_overgen_factor"] = n_needed

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved pilot report to {args.output}")


if __name__ == "__main__":
    main()
