"""
scripts/neuron_attribution.py — rank every MLP hidden neuron by attribution patching (neuron-partition N1).

One model load, one or more condition pairs, each written to its own directory:

    outputs/_analyses/neuron-partition/attribution/<task>_<pair>_<splits>_<commit>[_limit<N>][_rev]/
        scores.pt          {name: float32 [32, 14336]}  (see component_analysis/neuron_attribution.py)
        rows.json          ids, m_clean, m_twin, stored reference margins, counts, baseline summary, timing
        run_manifest.json  run_manifest.py's record (full commit, dataset_files with sha256, argv) plus notes

Pairs: `dh` is D (the task's pressure prompt) against its Neutral-Clause Twin H; `in` is the user-turn inversion I
against its user-neutral twin N, read in place from the specificity-ladder A1 control cell (an unmerged Codex pool).

    python scripts/neuron_attribution.py --task far_v2 --pair dh in --split train,validation --dry-run
    python scripts/neuron_attribution.py --task far_v2 --pair dh --split validation --limit 64 --batch-size 4

`--dry-run` loads the tokenizer and the paired rows (CPU, no model) and prints the plan, the row counts and a runtime
estimate. Ranking uses the train and validation splits only (item 10 of START.md).
"""

from __future__ import annotations

import argparse
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from component_analysis import neuron_attribution as na  # noqa: E402

DEFAULT_MODEL = "llama-8b-instruct"
DEFAULT_OUTPUT_ROOT = os.path.join(REPO, "outputs", "_analyses", "neuron-partition", "attribution")
RANKING_SPLITS = ("train", "validation")
#: Assumed until the pilot measures it (an H200/A40 guess for batch 4, one backward per row); the dry run says so.
ASSUMED_SECONDS_PER_ROW = 0.5
ASSUMED_LOAD_SECONDS = 240.0


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--task", default="far_v2", choices=("far_v2", "ser_v2"))
    p.add_argument("--pair", nargs="+", default=["dh"], choices=na.PAIRS)
    p.add_argument("--split", default="train,validation",
                   help="Comma-separated splits; only train and validation are allowed for ranking.")
    p.add_argument("--limit", type=int, default=None, help="Score only the first N paired rows (over the splits in "
                                                           "order).")
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--reverse", action="store_true", help="Also differentiate the twin run (H as clean, D as twin): "
                                                          "one more backward per batch.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--device", default=None)
    p.add_argument("--data-dir", default=os.path.join(REPO, "data", "datasets"))
    p.add_argument("--inversion-dir", default=None, help="User-turn I pool; default the A1 control cell's "
                                                         "<task>_user_inversion.")
    p.add_argument("--neutral-dir", default=None, help="User-neutral twin pool; default <task>_user_neutral there.")
    p.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    p.add_argument("--commit", default=None, help="Short commit for the directory name; default read from .git.")
    p.add_argument("--note", action="append", default=[], help="Free-text note for run_manifest.json (repeatable).")
    p.add_argument("--dry-run", action="store_true")
    return p


# ==============================================================================
# COMMIT (read from the .git files; no git process)
# ==============================================================================

def head_commit(repo_root: str = REPO):
    """The 40-hex HEAD commit, read from `.git` (worktree pointer, HEAD, loose ref or packed-refs); None if unknown."""
    try:
        git = os.path.join(repo_root, ".git")
        if os.path.isfile(git):
            with open(git) as handle:
                line = handle.read().strip()
            gitdir = line.split(":", 1)[1].strip() if line.startswith("gitdir:") else None
            if gitdir is None:
                return None
        else:
            gitdir = git
        with open(os.path.join(gitdir, "HEAD")) as handle:
            head = handle.read().strip()
        if not head.startswith("ref:"):
            return head if len(head) == 40 else None
        ref = head.split(":", 1)[1].strip()
        common = gitdir
        commondir = os.path.join(gitdir, "commondir")
        if os.path.exists(commondir):
            with open(commondir) as handle:
                common = os.path.normpath(os.path.join(gitdir, handle.read().strip()))
        for base in (gitdir, common):
            loose = os.path.join(base, ref)
            if os.path.isfile(loose):
                with open(loose) as handle:
                    return handle.read().strip()
        packed = os.path.join(common, "packed-refs")
        if os.path.isfile(packed):
            with open(packed) as handle:
                for line in handle:
                    parts = line.strip().split(" ")
                    if len(parts) == 2 and parts[1] == ref:
                        return parts[0]
    except (OSError, IndexError):
        return None
    return None


# ==============================================================================
# PLAN
# ==============================================================================

def splits_of(text: str):
    splits = [s.strip() for s in text.split(",") if s.strip()]
    bad = [s for s in splits if s not in RANKING_SPLITS]
    if bad:
        raise SystemExit(f"--split {text!r}: ranking uses only {', '.join(RANKING_SPLITS)} (item 10 of START.md); "
                         f"not {', '.join(bad)}")
    return splits


def pool_dirs(args, pair):
    if pair == "dh":
        clean = os.path.join(args.data_dir, args.task)
        return {"clean": clean, "twin": os.path.join(args.data_dir, f"{args.task}_honest")}
    return {"clean": args.inversion_dir or os.path.join(na.CODEX_POOL_ROOT, f"{args.task}_user_inversion"),
            "twin": args.neutral_dir or os.path.join(na.CODEX_POOL_ROOT, f"{args.task}_user_neutral")}


def output_dir(args, pair, splits, commit):
    name = f"{args.task}_{pair}_{'+'.join(splits)}_{(commit or 'nocommit')[:7]}"
    if args.limit is not None:
        name += f"_limit{args.limit}"
    if args.reverse:
        name += "_rev"
    return os.path.join(args.output_root, name)


def load_rows(args, pair, splits, tokenizer):
    dirs = pool_dirs(args, pair)
    rows, reports = [], []
    for split in splits:
        if pair == "dh":
            got, report = na.dh_pairs(dirs["clean"], tokenizer, split=split)
        else:
            got, report = na.in_pairs(dirs["clean"], dirs["twin"], tokenizer, split=split)
        rows.extend(got)
        reports.append(report.as_dict())
    if args.limit is not None:
        rows = rows[:args.limit]
    return rows, reports, dirs


def pool_record(dirs, pair):
    """{role: {path, files: {path: sha256}, note}} for rows.json."""
    import run_manifest as rm
    out = {}
    for role, directory in dirs.items():
        entry = {"path": os.path.abspath(directory),
                 "files": rm.hash_files(rm.data_files_under(directory))}
        if pair == "in":
            entry["note"] = na.UNMERGED_NOTE
        out[role] = entry
    return out


def load_tokenizer(model_name):
    """The model's tokenizer with pad = eos (ModelAdapter's rule), from the cached snapshot path when there is one
    (transformers 4.57 asks the hub for every hub id even offline, but not for a local directory)."""
    from transformers import AutoTokenizer

    from models import MODEL_REGISTRY
    hf_id = MODEL_REGISTRY.get(model_name, (model_name,))[0]
    path = None
    try:
        from huggingface_hub import try_to_load_from_cache
        found = try_to_load_from_cache(hf_id, "tokenizer_config.json")
        if isinstance(found, str) and os.path.exists(os.path.join(os.path.dirname(found), "tokenizer.json")):
            path = os.path.dirname(found)
    except Exception:                                            # noqa: BLE001 - fall back to the hub id
        path = None
    tok = AutoTokenizer.from_pretrained(path or hf_id)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
        tok.pad_token_id = tok.eos_token_id
    tok.padding_side = "right"
    return tok, hf_id


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    argv_list = list(sys.argv if argv is None else ["scripts/neuron_attribution.py"] + list(argv))
    splits = splits_of(args.split)
    commit = args.commit or head_commit()
    tokenizer, hf_id = load_tokenizer(args.model)

    plans = []
    for pair in args.pair:
        rows, reports, dirs = load_rows(args, pair, splits, tokenizer)
        out = output_dir(args, pair, splits, commit)
        plans.append((pair, rows, reports, dirs, out))
        n_clause = sum(r.span is not None for r in rows)
        print(f"[{pair}] {len(rows)} paired row(s) from {', '.join(splits)}; clause on {n_clause}; "
              f"clean {dirs['clean']}; twin {dirs['twin']}")
        for report in reports:
            print(f"  {report['split']}: {report['n_rows']} of {report['n_split']} paired; "
                  f"{len(report['without_twin'])} without twin; {len(report['dropped_by_tokenization'])} dropped by "
                  f"tokenization; {len(report['clause_fallback'])} clause fallback")
        print(f"  -> {out}")
    total = sum(len(p[1]) for p in plans)
    factor = 1.5 if args.reverse else 1.0
    estimate = ASSUMED_LOAD_SECONDS + total * ASSUMED_SECONDS_PER_ROW * factor
    print(f"plan: {total} row(s), batch {args.batch_size}, reverse {args.reverse}; estimate "
          f"{estimate / 60:.1f} min at an ASSUMED {ASSUMED_SECONDS_PER_ROW} s/row and {ASSUMED_LOAD_SECONDS:.0f} s "
          f"load (replace with the pilot's measured seconds per row)")
    if args.dry_run:
        print("dry run: no model loaded")
        return 0

    import torch
    from models import ModelAdapter

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    loading = time.perf_counter()
    model = ModelAdapter(args.model).load_full_model(device)
    load_seconds = time.perf_counter() - loading
    print(f"model loaded in {load_seconds:.1f} s on {device}", flush=True)

    status = 0
    for pair, rows, reports, dirs, out in plans:
        if not rows:
            print(f"[{pair}] no rows; skipped")
            status = 1
            continue

        def progress(done, total_batches, _pair=pair):
            if done == 1 or done % 10 == 0 or done == total_batches:
                print(f"[{_pair}] batch {done}/{total_batches}", flush=True)

        scores, record = na.score_rows(model, rows, batch_size=args.batch_size, reverse=args.reverse,
                                       progress=progress)
        pools = pool_record(dirs, pair)
        paths = na.write_outputs(out, scores, record, reports=reports, pools=pools,
                                 extra={"task": args.task, "pair": pair, "splits": splits, "model": hf_id,
                                        "model_load_seconds": load_seconds,
                                        "device": torch.cuda.get_device_name(0) if device == "cuda" else device})
        dataset_files = {}
        for entry in pools.values():
            dataset_files.update(entry["files"])
        notes = list(args.note)
        if pair == "in":
            notes.append(f"{na.UNMERGED_NOTE}: I = {dirs['clean']}, N = {dirs['twin']} (specificity-ladder A1 "
                         f"control cell, read in place)")
        manifest = na.write_manifest(
            out, notes=notes, script=os.path.join(REPO, "scripts", "neuron_attribution.py"), argv=argv_list,
            dataset_files=dataset_files, model=hf_id, seed=None,
            code_files=[os.path.join(REPO, "component_analysis", "neuron_attribution.py")])
        base = na.baseline_summary(record)
        print(f"[{pair}] {record['n_rows']} rows in {record['scoring_seconds']:.1f} s: measured "
              f"{record['seconds_per_row']:.3f} seconds per row (batch {args.batch_size})")
        for stream, stats in base.items():
            ref = stats.get("vs_stored_margin")
            print(f"[{pair}] {stream}: mean {stats['mean']:.3f}, frac > 0 {stats['frac_gt_0']:.3f}, "
                  f"frac > 0.7 {stats['frac_gt_0.7']:.3f}" +
                  (f"; vs stored margin: pearson {ref['pearson']}, mean |diff| {ref['mean_abs_diff']:.3f}, "
                   f"max |diff| {ref['max_abs_diff']:.3f}, sign agreement {ref['sign_agreement']:.3f}"
                   if ref else ""))
        print(f"[{pair}] wrote {paths['scores']}, {paths['rows']}, {manifest}")
        print(f"[{pair}] score keys: {sorted(scores)}")
    return status


if __name__ == "__main__":
    sys.exit(main())
