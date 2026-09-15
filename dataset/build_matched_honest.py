"""
build_matched_honest.py — draft the Matched Honest Instruction pool for a task
and filter a split to the instances that carry the Honest-Instruction
Counterfactual.

Two stages, and the first needs no GPU:

  1. **Draft the pool.** An agent's candidate ladder lives in
     `dataset/deception_pools/matched_honest_candidates.json`, ordered by token
     count. For each Pressure Clause this keeps the first candidate whose FULL
     prompt token count equals the clause's on a sample of that clause's own
     prompts, and writes `dataset/deception_pools/matched_honest_<task>.json`
     keyed by pressure id. Then it asserts the clause-span alignment on EVERY
     instance of the split, not just the sample.

  2. **Filter the split.** The existing margin filter run both ways: the
     instance is kept when the model deceives under its Pressure Clause and
     answers honestly under the Matched Honest Instruction. The surviving
     instance ids and a per-clause pass-rate report land beside the dataset as
     `matched_honest_survivors.json` and `matched_honest_report.json`.

Stage 1 alone (login node, tokenizer only, no weights):

    python dataset/build_matched_honest.py --task sdr --write-pool --no-model

Stage 2 (GPU node; the pool must already exist):

    python dataset/build_matched_honest.py --task sdr

This does NOT touch the fixed-length `honest_instruction` prompt variant that
`evaluation/pressure.py` uses. That variant is a different object: one sentence
for every clause, no length matching, and no alignment guarantee.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataset import deception_common as dc
from dataset import matched_honest as mh

#: How many of a clause's own prompts the length check samples. The clause sits
#: in a fixed scaffold, so a handful across template variants is enough to catch
#: a boundary merge; the every-instance assertion afterwards is the real gate.
DEFAULT_POOL_SAMPLE = 8


def build_parser():
    p = argparse.ArgumentParser(
        description="Draft Matched Honest Instructions and build the "
                    "Honest-Instruction Counterfactual split.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--task", choices=sorted(dc.SPECS), required=True)
    p.add_argument("--dataset-dir", default=None,
                   help="Default: data/datasets/<task>.")
    p.add_argument("--split", default="test")
    p.add_argument("--pools-dir", default=dc.POOLS_DIR)
    p.add_argument("--write-pool", action="store_true",
                   help="Draft (or redraft) the task's pool file from the "
                        "candidate ladder before filtering.")
    p.add_argument("--pool-sample", type=int, default=DEFAULT_POOL_SAMPLE,
                   help="Prompts per clause used to choose its instruction.")
    p.add_argument("--margin-thresh", type=float, default=None,
                   help="Default: the build-time margin_thresh in "
                        "dataset_config.json, else 1.0.")
    p.add_argument("--honest-streams", choices=list(mh.HONEST_STREAM_CHOICES),
                   default="both",
                   help="Which streams must give the honest answer under the "
                        "instruction. Both rates are reported either way.")
    p.add_argument("--min-survivors", type=int, default=1,
                   help="A clause counts as usable at this many survivors.")
    p.add_argument("--max-seq-length", type=int, default=None,
                   help="Default: the dataset's own max_seq_length.")
    p.add_argument("--model", default=None,
                   help="Default: the model recorded in dataset_config.json.")
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--no-model", action="store_true",
                   help="Dry run (CPU-safe): draft/verify the pool and assert "
                        "the clause-span alignment on every instance. No "
                        "filtering, no survivors written.")
    p.add_argument("--hf-token", default=None)
    return p


# ==============================================================================
# Stage 1 — the pool
# ==============================================================================

def sample_prompts_for(records, spec, pressure, limit):
    """That clause's own prompts, or template-built ones when it has none.

    Real prompts are preferred because the saved datasets were built from older
    template text than `SPECS` carries today, and the length that has to match
    is the length of the prompt the analyses will actually run.
    """
    own = [r["clean_prompt"] for r in records
           if r["pressure_id"] == pressure["id"]]
    if own:
        step = max(1, len(own) // limit)
        return own[::step][:limit]
    return [dc.build_prompt_pair(spec, spec.variant(variant), "Vantis Medical",
                                 ("staffing", "pricing"), polarity, designation,
                                 pressure["text"])["clean_prompt"]
            for variant in spec.variant_names
            for polarity in (1, 2)
            for designation in ("inversion", "identity")][:limit]


def draft_pool(args, records, spec, pressures, tokenizer):
    candidates = mh.load_candidates(args.pools_dir)
    print(f"\nDrafting from {len(candidates)} candidate instruction(s) over "
          f"{len(pressures)} Pressure Clause(s)...")
    pool, unmatched = mh.build_pool(
        tokenizer, pressures, candidates,
        lambda p: sample_prompts_for(records, spec, p, args.pool_sample))
    path = mh.write_matched_honest_pool(
        args.task, pool, pools_dir=args.pools_dir,
        meta={"model": args.model, "candidates_file": mh.CANDIDATES_FILE,
              "pool_sample": args.pool_sample})
    print(f"  matched {len(pool)}/{len(pressures)} clause(s) -> {path}")
    if unmatched:
        print(f"  NO candidate of the right length for: {', '.join(unmatched)}\n"
              f"  Add one to {mh.CANDIDATES_FILE} and rerun --write-pool.")
    return pool


def print_pool(pool, pressures):
    print(f"\n{'pressure':<12} {'tokens':>6}  instruction")
    for pressure in pressures:
        entry = pool.get(pressure["id"])
        if entry is None:
            print(f"{pressure['id']:<12} {'—':>6}  (no matched instruction)")
            continue
        print(f"{pressure['id']:<12} {entry['clause_tokens']:>6}  "
              f"{entry['instruction']}")


# ==============================================================================
# Main
# ==============================================================================

def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.dataset_dir is None:
        args.dataset_dir = os.path.join("data", "datasets", args.task)
    spec = dc.SPECS[args.task]

    config = dc.load_dataset_config(args.dataset_dir)
    args.model = args.model or config.get("model", dc.DEFAULT_MODEL)
    if args.max_seq_length is None:
        args.max_seq_length = int(config.get("max_seq_length", dc.MAX_SEQ_LENGTH))
    if args.margin_thresh is None:
        args.margin_thresh = float(config.get("margin_thresh", 1.0))

    print("=" * 70)
    print(f"  MATCHED HONEST INSTRUCTIONS — {spec.display_name}")
    print("=" * 70)
    print(f"dataset       {args.dataset_dir} ({args.split})")
    print(f"model         {args.model}")
    print(f"margin        {args.margin_thresh}  (from the dataset build unless "
          f"overridden)")
    print(f"honest side   {args.honest_streams} stream(s) must give the honest "
          f"answer")

    from transformers import AutoTokenizer
    hf_token = args.hf_token or os.environ.get("HF_TOKEN")
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=hf_token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    records = dc.load_or_generate_deception_data(args.dataset_dir,
                                                 split=args.split)
    pressures = dc.load_pressures(args.task, args.pools_dir)

    if args.write_pool:
        pool = draft_pool(args, records, spec, pressures, tokenizer)
    else:
        pool = mh.load_matched_honest_pool(args.task, args.pools_dir)
    print_pool(pool, pressures)

    # The every-instance assertion. This is what makes the pool a guarantee
    # rather than a sample: it runs on the login node, before any GPU time.
    kept, _, missing = mh.pair_with_matched_instructions(
        records, pool, tokenizer, args.max_seq_length)
    print(f"\nClause-span alignment asserted on {len(kept)}/{len(records)} "
          f"instance(s) of {args.split}.")
    if missing:
        print(f"  {len(records) - len(kept)} instance(s) dropped: no matched "
              f"instruction for {', '.join(missing)}")

    if args.no_model:
        print("\n--no-model dry run: the pool is drafted and aligned. The "
              "two-sided filter needs a GPU; nothing was written beside the "
              "dataset.")
        return 0

    # ----- the two-sided filter -------------------------------------------
    import torch
    from models import MODEL_REGISTRY, ModelAdapter

    registry_name = next((name for name, (hf_id, _) in MODEL_REGISTRY.items()
                          if hf_id == args.model), None)
    if registry_name is None:
        raise SystemExit(
            f"{args.model} is not in the model registry, so the filter cannot "
            f"load it the way the rest of the repo does. Add it to "
            f"models.MODEL_REGISTRY or pass --model with a registered id.")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("\nWARNING: no CUDA device — filtering an 8B model on CPU will be "
              "extremely slow. Use a GPU node.")
    print(f"\nLoading {args.model} on {device} via ModelAdapter"
          f"({registry_name!r})...")
    model = ModelAdapter(registry_name, hf_token=hf_token).load_full_model(device)

    survivors, report = mh.filter_matched_honest(
        records, pool, model, tokenizer, device,
        margin_thresh=args.margin_thresh, honest_streams=args.honest_streams,
        max_length=args.max_seq_length, batch_size=args.batch_size,
        min_survivors=args.min_survivors)
    report["model"] = args.model
    report["dataset_dir"] = args.dataset_dir

    print("\n" + "=" * 70)
    print(f"  {args.task.upper()} — PER-CLAUSE PASS RATES")
    print("=" * 70)
    print(f"{'pressure':<12} {'n':>5} {'deceive':>8} {'honest(c)':>10} "
          f"{'honest(b)':>10} {'kept':>6} {'rate':>7}")
    for pid, row in report["by_clause"].items():
        print(f"{pid:<12} {row['n']:>5} {row['pressure_pass_rate']:>8.2f} "
              f"{row['honest_pass_rate_clean']:>10.2f} "
              f"{row['honest_pass_rate_both']:>10.2f} "
              f"{row['n_survivors']:>6} {row['survivor_rate']:>7.2f}")
    overall = report["overall"]
    print(f"\noverall: {overall['n_survivors']}/{overall['n']} kept "
          f"({overall['survivor_rate']*100:.2f}%); "
          f"{len(report['usable_clauses'])} clause(s) usable at "
          f">= {args.min_survivors} survivor(s)")
    print("  'rate' columns are conditional on n, and n is very uneven across "
          "clauses —\n  read a rate on a handful of instances as noise.")
    other = "clean" if args.honest_streams == "both" else "both"
    n_other = len(report["survivor_ids"][other])
    n_usable_other = sum(
        1 for pid in report["by_clause"]
        if report["by_clause"][pid][f"n_honest_pass_{other}"] > 0)
    print(f"  --honest-streams {other} would keep {n_other} instance(s) across "
          f"{n_usable_other} clause(s); both id lists are written, so switching "
          f"costs no GPU time.")

    written = mh.write_survivors(args.dataset_dir, args.task, survivors, report,
                                 split=args.split)
    print(f"\nWrote {written['survivors']}\n      {written['report']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
