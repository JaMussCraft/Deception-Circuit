#!/usr/bin/env python3
"""B3 patching entrypoint: the sycophancy control (J3), the transfer test and C3 (J4), and the knockout parity check
(plan B3 sections 2, 3.2 to 3.4, 5 and 6; rulings R4 and R5 in docs/research/instructed-route/spec.md).

    scripts/jobs/run_b3_patch.sh --task syc --out outputs/_studies/b3/syc
    scripts/jobs/run_b3_patch.sh --task af --variant V-B --proxy P2 --sets S_all,S_far,S_ser,S_q,gupta6,heads_only \\
        --null 20 --positions post_tag,readout --out outputs/_studies/b3/transfer
    scripts/jobs/run_b3_patch.sh --task c3 --variant V-B --sets S_all --out outputs/_studies/b3/c3
    scripts/jobs/run_b3_patch.sh --parity-check --out outputs/_studies/b3/parity

Tasks:
  af   free (clean) and paid (twin) alignment-faking prompts of --variant; margin = the primary proxy (--proxy P1 or
       P2, ruling R-B3-a) from --tokens, whose R1 must be calibrated (freeze G2). Writes the spontaneous gap, f per
       set and positions arm with bootstrap CIs, the null f values and maxima, and the R5 transfer verdict on
       S_all at post_tag (qualifiers from --controls when given).
  syc  cued (clean) and uncued (twin) MMLU prompts; margin = logit(cue letter) - logit(gold). Pass 1 fixes kept items
       and flips, pass 2 patches the kept items. Writes f over kept items, flip reversal per arm, and the pass bar
       (gupta6 at the Readout reverses >= 0.18 of flips and beats every null draw).
  c3   the C3 control pair (bullets for free, prose for paid) on XSTest safe prompts; margin = the bullet first-token
       mass. Writes f_C3 (S_all at post_tag), which the af verdict reads through --controls.

Sets: S_all, S_far, S_ser, S_q, gupta6, gupta_writers, L17H24, heads_only (S_all's 32 heads, with a heads-only
null). Each set gets --null layer-matched draws (`spontaneous.stats`), seeded NULL_SEED + 1000 x the set's index in
SET_ORDER, so a set's draws do not depend on the order of --sets.

Outputs in --out: margins.json (per-item margins of every arm), results.json, run_manifest.json.
--dry-run loads no model: it builds the twins with the cached tokenizer, checks them, and prints the forward count
and a walltime estimate. --parity-check runs the FAR deciding set on the first 10 FAR held-out ids through
`spontaneous.patching` and through `component_analysis.knockout`, at knockout's post-clause positions and at the B3
post-tag positions, and prints both f values; agreement within 0.01 is expected.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spontaneous import patching, stats                       # noqa: E402

MODEL = "meta-llama/Llama-3.1-8B-Instruct"
TASKS = ("af", "syc", "c3")
SET_ORDER = ("S_all", "S_far", "S_ser", "S_q", "gupta6", "heads_only", "gupta_writers", "L17H24")
DEFAULT_SETS = {"af": "S_all,S_far,S_ser,S_q,gupta6,heads_only", "syc": "gupta6,gupta_writers,L17H24,S_q,S_all",
                "c3": "S_all"}
DEFAULT_POSITIONS = {"af": "post_tag", "syc": "readout", "c3": "post_tag"}
DEFAULT_ROWS = {"af": ROOT / "data" / "b3" / "af_queries.json", "syc": ROOT / "data" / "b3" / "syc_items.json",
                "c3": ROOT / "data" / "b3" / "xstest_safe.json"}
DEFAULT_BATCH = {"af": 8, "syc": 16, "c3": 8}
TOKENS = ROOT / "spontaneous" / "grader" / "proxy_tokens.json"

#: Parity check (plan section 2): the FAR deciding set on the first 10 FAR held-out ids, neutral-twin interchange.
FAR_HELDOUT = ROOT / "docs" / "research" / "mechanism-analysis" / "phase1" / "groups" / "far_heldout_D_sample.json"
FAR_DATASET = ROOT / "data" / "datasets" / "far_v2"
FAR_TASK = "far_v2"
POST_CLAUSE = "after=pressure_clause,exclude=readout"
FAR_F_D_100 = 0.893
PARITY_TOL = 0.01
PARITY_N = 10

#: Walltime basis (plan section 6): the mechanism-analysis 02a sweep ran about 100 forwards per second on ~250-token
#: prompts on an H100; time per forward is taken as proportional to prompt length, and an A100 at half an H100.
H100_FWD_PER_S_AT_250 = 100.0
A100_OVER_H100 = 0.5
LOAD_S = 476.0


# ==============================================================================
# Sets, nulls and arms
# ==============================================================================

def resolve_sets(names):
    """-> {name: {"members": [...], "null_seed": int, "null_kind": "layer_matched" | "heads_only"}}."""
    from spontaneous.sets import load_sets
    base = load_sets()
    extra = {"heads_only": [k for k in base["S_all"] if k[0] == "head"], "L17H24": [("head", 17, 24)]}
    out = {}
    for name in names:
        if name not in SET_ORDER:
            raise ValueError(f"unknown set {name!r}; expected one of {', '.join(SET_ORDER)}")
        members = base[name] if name in base else extra[name]
        out[name] = {"members": [tuple(k) for k in members],
                     "null_seed": stats.NULL_SEED + 1000 * SET_ORDER.index(name),
                     "null_kind": "heads_only" if name == "heads_only" else "layer_matched"}
    return out


def null_draws(spec, n):
    if n <= 0:
        return []
    fn = stats.heads_only_nulls if spec["null_kind"] == "heads_only" else stats.layer_matched_nulls
    return [[tuple(k) for k in d] for d in fn(spec["members"], n=n, seed=spec["null_seed"])]


def arm_label(name, pos, null=None):
    return f"{name}@{pos}" + ("" if null is None else f"#null{null:02d}")


def build_arms(sets, positions, n_null):
    """-> ({label: (members, pos)}, {set@pos: [null labels]})."""
    arms, nulls = {}, {}
    for name, spec in sets.items():
        draws = null_draws(spec, n_null)
        for pos in positions:
            arms[arm_label(name, pos)] = (spec["members"], pos)
            nulls[arm_label(name, pos)] = []
            for j, d in enumerate(draws):
                arms[arm_label(name, pos, j)] = (d, pos)
                nulls[arm_label(name, pos)].append(arm_label(name, pos, j))
    return arms, nulls


# ==============================================================================
# Estimates
# ==============================================================================

def count_forwards(*, n_rows, n_stems, n_sets, n_null, n_positions):
    """One clean and one twin forward per sequence, plus one per arm (each set and each null draw, per positions
    arm). A P2 row is n_stems sequences."""
    return n_rows * n_stems * (2 + n_positions * n_sets * (1 + n_null))


def seconds_per_forward(tokens, gpu):
    rate = H100_FWD_PER_S_AT_250 * (A100_OVER_H100 if gpu == "a100" else 1.0)
    return tokens / (250.0 * rate)


def walltime_line(n_forwards, tokens):
    parts = []
    for gpu in ("a100", "h100"):
        s = n_forwards * seconds_per_forward(tokens, gpu)
        parts.append(f"{gpu.upper()} {s / 3600:.2f} h compute + {LOAD_S / 60:.0f} min load = "
                     f"{(s + LOAD_S) / 3600:.2f} h")
    return "walltime estimate: " + "; ".join(parts)


# ==============================================================================
# Rows
# ==============================================================================

def load_tokenizer(model):
    from spontaneous.af_prompts import load_cached_tokenizer
    return load_cached_tokenizer(model)


def _row_list(data, split):
    if isinstance(data, list):
        return data
    for key in ([split] if split else []) + ["rows", "items", "test"]:
        if key and key in data:
            return data[key]
    raise ValueError(f"no row list under {split!r}, 'rows', 'items' or 'test'")


def _default_lookup(task):
    data = json.loads(DEFAULT_ROWS[task].read_text())
    lists = [v for v in data.values() if isinstance(v, list)] if isinstance(data, dict) else [data]
    return {r["id"]: r for lst in lists for r in lst if isinstance(r, dict) and "id" in r}


def load_rows(path, task, split=None):
    """Rows of --rows: a committed data file (split for af, `items` otherwise), a list, or ids into the default
    file. A dict without its text (`prompt`, or `question` for syc) is looked up by `id`, `query_id` or `item_id`."""
    data = json.loads(Path(path).read_text())
    rows = _row_list(data, split if task == "af" else None)
    need = "question" if task == "syc" else "prompt"
    lookup = None
    out = []
    for r in rows:
        if isinstance(r, dict) and need in r:
            out.append(r)
            continue
        rid = r if isinstance(r, str) else (r.get("id") or r.get("query_id") or r.get("item_id"))
        if lookup is None:
            lookup = _default_lookup(task)
        if rid not in lookup:
            raise ValueError(f"row {rid!r} is not in {DEFAULT_ROWS[task]}")
        out.append(lookup[rid])
    return out


# ==============================================================================
# Readouts
# ==============================================================================

def af_readout(tokenizer, tokens_path, proxy_name, *, require_r1):
    """-> (CompactProxy, stems, info) for the alignment-faking proxy margin."""
    from spontaneous import proxy
    tokens = proxy.load_proxy_tokens(tokens_path)
    if tokens.r1 is None and require_r1:
        raise SystemExit(f"{tokens_path} has no calibrated R1 (freeze G2 is not recorded); the transfer runs on the "
                         f"frozen primary proxy only")
    res = proxy.resolve_tokens(tokens, tokenizer)
    stems = [tuple(p) for p in res.stem_paths] if proxy_name == "P2" else [()]
    info = {"proxy": proxy_name, "tokens_file": str(tokens_path), "r1_calibrated": tokens.r1 is not None,
            "r1_ids": sorted(res.r1_ids), "opener_id": res.opener_id, "stems": [list(s) for s in stems]}
    return patching.CompactProxy.for_af(res), stems, info


# ==============================================================================
# Results
# ==============================================================================

def _clean(obj):
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        return _clean(obj.item())
    return obj


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(obj), indent=1) + "\n")


def _main_arms(arms):
    return [k for k in arms if "#null" not in k]


def af_results(margins, arms, nulls, *, task, n_boot, seed, controls=None, responsive=None, ids=None):
    import numpy as np
    clean, twin = margins["clean"], margins["twin"]
    out = {"gap": patching.gap_summary(clean, twin, n_boot=n_boot, seed=seed), "f": {}, "f_prob": {}, "nulls": {}}
    for label in arms:
        out["f"][label] = patching.f_summary(clean, margins["arms"][label], twin, n_boot=n_boot, seed=seed)
        out["f_prob"][label] = patching.fraction(patching.sigmoid(clean), patching.sigmoid(margins["arms"][label]),
                                                 patching.sigmoid(twin))
    for label, null_labels in nulls.items():
        fs = [out["f"][n]["f"] for n in null_labels]
        out["nulls"][label] = {"f": fs, "max": max(fs) if fs else None,
                               "mean": float(np.mean(fs)) if fs else None, "n": len(fs)}
    if responsive is not None and ids is not None:
        keep = [i for i, q in enumerate(ids) if q in set(responsive)]
        pick = lambda xs: [xs[i] for i in keep]                     # noqa: E731
        out["responsive"] = {"n": len(keep), "f": {
            label: patching.f_summary(pick(clean), pick(margins["arms"][label]), pick(twin), n_boot=n_boot,
                                      seed=seed) for label in _main_arms(arms)}} if keep else {"n": 0}
    primary = arm_label("S_all", "post_tag")
    if task == "af":
        if primary in out["f"]:
            out["transfer_verdict"] = patching.transfer_verdict(
                out["f"][primary]["f"], out["nulls"][primary]["f"], gap_measurable=out["gap"]["measurable"],
                gap=out["gap"]["gap"], controls=controls)
        else:
            out["transfer_verdict"] = {"label": f"not computed: needs {primary}"}
    if task == "c3":
        out["f_c3"] = out["f"][primary]["f"] if primary in out["f"] else None
    return out


def syc_results(run, arms, nulls, *, n_boot, seed):
    import numpy as np
    n = len(run["ids"])
    kept_rows = run["kept_rows"]
    flip = np.asarray(run["flip"], dtype=bool)
    gold = np.asarray(run["gold"])
    out = {"n_items": n, "n_kept": len(kept_rows), "n_flips": int(flip.sum()), "f": {}, "f_flips": {},
           "reversal": {}, "nulls": {}}
    p2 = run["pass2"]
    flip_in_kept = [i for i, r in enumerate(kept_rows) if flip[r]]
    table = {"kept": np.asarray(run["kept"], dtype=bool), "flip": flip}
    for label in arms:
        if kept_rows:
            out["f"][label] = patching.f_summary(p2["clean"], p2["arms"][label], p2["twin"], n_boot=n_boot, seed=seed)
        if flip_in_kept:
            pick = lambda xs: [xs[i] for i in flip_in_kept]         # noqa: E731
            out["f_flips"][label] = patching.f_summary(pick(p2["clean"]), pick(p2["arms"][label]), pick(p2["twin"]),
                                                       n_boot=n_boot, seed=seed)
        patched = np.full(n, -1)
        patched[kept_rows] = p2["argmax"][label]
        out["reversal"][label] = patching.flip_reversal(table, gold, patched)
    for label, null_labels in nulls.items():
        shares = [out["reversal"][x]["share"] for x in null_labels]
        fs = [out["f"][x]["f"] for x in null_labels if x in out["f"]]
        out["nulls"][label] = {"reversal": shares, "reversal_max": max([s for s in shares if s is not None],
                                                                      default=None),
                               "f": fs, "f_max": max(fs) if fs else None, "n": len(null_labels)}
    named = arm_label("gupta6", "readout")
    if named in out["reversal"] and nulls.get(named):
        out["pass_bar"] = patching.syc_pass_bar(out["reversal"][named]["share"], out["nulls"][named]["reversal"])
    else:
        out["pass_bar"] = {"pass": None, "label": f"not computed: needs {named} with null draws"}
    return out


# ==============================================================================
# The parity check
# ==============================================================================

def parity_inputs(tokenizer):
    """The first 10 FAR held-out ids, their batches (batch size 8, as the mechanism analysis ran) and segmentations."""
    from component_analysis import dataloaders, instances, sampling
    from dataset.deception_common import load_or_generate_deception_data
    ids = json.loads(FAR_HELDOUT.read_text())["instance_ids"][:PARITY_N]
    records = load_or_generate_deception_data(str(FAR_DATASET), "test", 1000)
    rid = sampling.record_ids(records)
    keep = [(r, i) for r, i in zip(records, rid) if i in set(ids)]
    segs, _ = instances.resolve_split_segmentation(FAR_TASK, [r for r, _ in keep], tokenizer,
                                                   ids=[i for _, i in keep])
    batches = dataloaders.causal_batches(str(FAR_DATASET), tokenizer, ids=ids, task=FAR_TASK, batch_size=8)
    return ids, list(batches), {s.record_id: s for s in segs}


def parity_masks(batch, by_id):
    """-> (rows, {"post_clause": mask, "post_tag": mask}) for the twinned rows of a FAR batch."""
    import torch
    from component_analysis import knockout
    pair = batch.neutral_twin
    rows = list(pair.rows)
    sel = torch.tensor(rows, dtype=torch.long)
    ids = [batch.ids[r] for r in rows]
    clean = batch.input_ids[sel]
    readout = batch.readout[sel]
    post = knockout.position_mask(knockout.parse_positions(POST_CLAUSE), ids, by_id, readout, clean.shape[1])
    starts = [patching.first_difference(clean[i].tolist(), pair.input_ids[i].tolist()) for i in range(len(rows))]
    tag = patching.arm_mask("post_tag", starts, readout, clean.shape[1])
    return rows, {"post_clause": post, "post_tag": tag}


def parity_check(args):
    import torch
    from component_analysis import hooks, instances, knockout
    from spontaneous.sets import load_sets
    tokenizer = instances.load_analysis_tokenizer("llama-8b-instruct")
    ids, batches, by_id = parity_inputs(tokenizer)
    s_far = load_sets()["S_far"]
    n_rows = sum(len(b.neutral_twin.rows) for b in batches if b.neutral_twin is not None)
    for b in batches:
        parity_masks(b, by_id)
    # ours: clean, twin, 2 arms; knockout: clean, twin, 1 arm, for each of 2 plans
    n_fwd = len(batches) * (4 + 2 * 3)
    seq = max(b.input_ids.shape[1] for b in batches)
    print(f"parity: FAR deciding set ({len(s_far)} members) on {len(ids)} held-out ids ({n_rows} twinned) in "
          f"{len(batches)} batches; {n_fwd} batched forwards of length {seq}")
    if args.dry_run:
        print(walltime_line(n_fwd, seq))
        return 0
    model = load_model(args)
    t0 = time.time()
    plans = {"post_clause": knockout.KnockoutPlan(counterfactual="neutral_twin", positions=POST_CLAUSE),
             "post_tag": knockout.KnockoutPlan(counterfactual="neutral_twin", positions="all")}
    ko = {name: knockout.knock_out_groups(model, batches, [("S_far", s_far)], plan=plan, segmentations=by_id)
          for name, plan in plans.items()}
    ours = {"clean": [], "twin": [], "post_clause": [], "post_tag": []}
    for b in batches:
        rows, masks = parity_masks(b, by_id)
        sel = torch.tensor(rows, dtype=torch.long)
        target, distractor = b.target_token[sel], b.distractor_token[sel]

        def reduce(logits, t=target, d=distractor):
            return hooks.target_minus_distractor(logits, t.to(logits.device), d.to(logits.device))
        out = patching.interchange_tensors(
            model, b.input_ids[sel], b.attention_mask[sel], b.neutral_twin.input_ids, b.neutral_twin.attention_mask,
            b.readout[sel], {name: (s_far, m) for name, m in masks.items()}, reduce=reduce)
        ours["clean"] += out.clean.tolist()
        ours["twin"] += out.twin.tolist()
        for name in masks:
            ours[name] += out.patched[name].tolist()
    report = {"ids": ids, "n": len(ours["clean"]), "reference_f_D_100_ids": FAR_F_D_100, "tolerance": PARITY_TOL,
              "comparisons": {}, "seconds": time.time() - t0}
    ok = True
    for name in plans:
        e = ko[name]
        f_ko = stats.mediated_fraction(e.clean_logit_difference, e.knocked_logit_difference["S_far"],
                                       e.neutral_twin_logit_difference)
        f_us = stats.mediated_fraction(ours["clean"], ours[name], ours["twin"])
        agree = abs(f_ko - f_us) <= PARITY_TOL
        ok &= agree
        report["comparisons"][name] = {"knockout_positions": plans[name].positions, "f_knockout": f_ko,
                                       "f_patching": f_us, "abs_diff": abs(f_ko - f_us), "agree": agree,
                                       "knockout_ids": e.ids}
        print(f"parity {name}: patching f = {f_us:.4f}, knockout.py f = {f_ko:.4f}, |diff| = {abs(f_ko - f_us):.5f}"
              f" -> {'agree' if agree else 'DISAGREE'} (tolerance {PARITY_TOL}; 100-id f_D {FAR_F_D_100})")
    report["margins"] = ours
    out_dir = Path(args.out)
    _write_json(out_dir / "parity.json", report)
    write_manifest(args, [FAR_HELDOUT, ROOT / "docs" / "research" / "mechanism-analysis" / "phase1" /
                          "p1c_readings.json"])
    return 0 if ok else 1


# ==============================================================================
# Model and manifest
# ==============================================================================

def load_model(args):
    from component_analysis import hooks
    model = hooks.load_analysis_model(args.model, device=args.device)
    print("model:", hooks.describe(model))
    return model


def write_manifest(args, data_files):
    from run_manifest import write_run_manifest
    code = [ROOT / "spontaneous" / f for f in ("patching.py", "stats.py", "proxy.py", "sets.py", "af_prompts.py")]
    code.append(ROOT / "component_analysis" / "hooks.py")
    return write_run_manifest(str(args.out), script=str(Path(__file__).resolve()),
                              dataset_files=[str(p) for p in data_files if Path(p).is_file()], model=args.model,
                              seed=args.seed, grader=None, code_files=[str(p) for p in code])


# ==============================================================================
# Main
# ==============================================================================

def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--task", choices=TASKS)
    p.add_argument("--variant", choices=("V-A", "V-B"), help="alignment-faking scaffold (af, c3)")
    p.add_argument("--proxy", choices=("P1", "P2"), help="the primary proxy of ruling R-B3-a (af)")
    p.add_argument("--sets", help="comma list; default per task: " + "; ".join(f"{k}: {v}"
                                                                             for k, v in DEFAULT_SETS.items()))
    p.add_argument("--null", type=int, default=stats.N_NULL, help="layer-matched null draws per set")
    p.add_argument("--positions", help="comma list of post_tag, readout; default af/c3 post_tag, syc readout")
    p.add_argument("--rows", help="rows file; default the committed data file of the task")
    p.add_argument("--split", default="test", help="af rows split in the data file (default test)")
    p.add_argument("--tokens", default=str(TOKENS), help="the frozen proxy token file (af)")
    p.add_argument("--controls", help="JSON with delta_c1, delta_c2, f_c3 for the af verdict qualifiers")
    p.add_argument("--responsive", help="JSON list of af query ids whose judged gap is >= 0.2 (secondary f)")
    p.add_argument("--out", required=True)
    p.add_argument("--model", default=MODEL)
    p.add_argument("--device", default="cuda")
    p.add_argument("--batch-size", type=int, help="sequences per forward; default af/c3 8, syc 16")
    p.add_argument("--n-boot", type=int, default=stats.N_BOOT)
    p.add_argument("--seed", type=int, default=0, help="bootstrap seed")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--parity-check", action="store_true")
    p.add_argument("--discovery", action="store_true", help="plan 3.5; not built (a later ticket)")
    args = p.parse_args(argv)
    if args.discovery:
        try:
            patching.discovery()
        except NotImplementedError as e:
            p.error(str(e))
    if args.parity_check:
        return args
    if args.task is None:
        p.error("--task is required unless --parity-check")
    if args.task in ("af", "c3") and args.variant is None:
        p.error(f"--task {args.task} needs --variant (the R4 variant ruling)")
    if args.task == "af" and args.proxy is None:
        p.error("--task af needs --proxy P1 or P2 (ruling R-B3-a)")
    args.set_names = [s for s in (args.sets or DEFAULT_SETS[args.task]).split(",") if s]
    bad = [s for s in args.set_names if s not in SET_ORDER]
    if bad:
        p.error(f"unknown set(s) {bad}; expected from {', '.join(SET_ORDER)}")
    args.position_arms = [s for s in (args.positions or DEFAULT_POSITIONS[args.task]).split(",") if s]
    bad = [s for s in args.position_arms if s not in patching.POSITION_ARMS]
    if bad:
        p.error(f"unknown positions {bad}; expected from {patching.POSITION_ARMS}")
    args.rows = args.rows or str(DEFAULT_ROWS[args.task])
    args.batch_size = args.batch_size or DEFAULT_BATCH[args.task]
    return args


def build_pairs(args, tokenizer):
    from spontaneous import af_prompts
    rows = load_rows(args.rows, args.task, args.split)
    if args.task == "syc":
        pairs, dropped = af_prompts.build_syc_pairs(tokenizer, rows)
        return rows, pairs, dropped
    control = "C3" if args.task == "c3" else None
    pairs = [af_prompts.build_af_pair(tokenizer, r["prompt"], args.variant, control) for r in rows]
    return rows, pairs, []


def main(argv=None):
    args = parse_args(argv)
    if args.parity_check:
        return parity_check(args)
    from spontaneous import af_prompts
    tokenizer = load_tokenizer(args.model)
    rows, pairs, dropped = build_pairs(args, tokenizer)
    sets = resolve_sets(args.set_names)
    arms, nulls = build_arms(sets, args.position_arms, args.null)

    if args.task == "af":
        compact, stems, readout_info = af_readout(tokenizer, args.tokens, args.proxy, require_r1=not args.dry_run)
        readout_kind = args.proxy
    elif args.task == "c3":
        ids = patching.bullet_ids(tokenizer)
        compact, stems = patching.CompactProxy.for_bullets(ids), [()]
        readout_info = {"readout": "bullet first-token mass", "openers": list(patching.C3_BULLET_OPENERS),
                        "ids": ids}
        readout_kind = "bullet"
    else:
        letter_ids = af_prompts.letter_token_ids(tokenizer)
        stems = [()]
        readout_info = {"readout": "logit(cue letter) - logit(gold)", "letter_ids": letter_ids}

    lengths = [len(p.cued_ids) if args.task == "syc" else len(p.free_ids) for p in pairs]
    mean_len = (sum(lengths) / len(lengths)) if lengths else 0.0
    stem_extra = (sum(len(s) for s in stems) / len(stems)) if stems else 0.0
    n_fwd = count_forwards(n_rows=len(pairs), n_stems=len(stems), n_sets=len(sets), n_null=args.null,
                           n_positions=len(args.position_arms))
    print(f"task {args.task}: {len(pairs)} twin pairs from {args.rows}"
          + (f" ({len(dropped)} dropped: no equal-length uncued twin)" if args.task == "syc" else "")
          + (f"; variant {args.variant}" if args.variant else ""))
    print(f"  prompt tokens: mean {mean_len:.0f}, max {max(lengths) if lengths else 0}; stems {len(stems)}")
    print("  sets: " + ", ".join(f"{n} ({len(s['members'])}, null seed {s['null_seed']}, {s['null_kind']})"
                                   for n, s in sets.items()))
    print(f"  positions: {', '.join(args.position_arms)}; {args.null} null draws per set; {len(arms)} arms")
    if args.task == "syc":
        pass1 = 2 * len(pairs)
        pass2 = count_forwards(n_rows=len(pairs), n_stems=1, n_sets=len(sets), n_null=args.null,
                               n_positions=len(args.position_arms))
        n_fwd = pass1 + pass2
        print(f"  forwards: pass 1 {pass1}; pass 2 at most {pass2} (every item kept; kept items are unknown before "
              f"the run); total at most {n_fwd}")
    else:
        print(f"  forwards: {n_fwd} sequences ({len(pairs)} rows x {len(stems)} stems x "
              f"(2 + {len(args.position_arms)} x {len(sets)} x (1 + {args.null})))")
    print("  " + walltime_line(n_fwd, mean_len + stem_extra))
    if args.task == "af":
        print(f"  proxy {args.proxy} from {args.tokens}; R1 calibrated: {readout_info['r1_calibrated']}")
    if args.dry_run:
        print("dry run: no model loaded, nothing written")
        return 0

    model = load_model(args)
    out_dir = Path(args.out)
    t0 = time.time()

    def progress(done, total, what=""):
        print(f"  {what} {done}/{total} rows, {time.time() - t0:.0f} s", flush=True)

    if args.task == "syc":
        run = patching.run_syc(model, pairs, letter_ids, arms, batch_size=args.batch_size, progress=progress)
        results = syc_results(run, arms, nulls, n_boot=args.n_boot, seed=args.seed)
        results["dropped"] = dropped
        margins = run
    else:
        run = patching.run_af(model, pairs, arms, compact, readout=readout_kind, stems=stems,
                              batch_size=args.batch_size, progress=progress)
        controls = json.loads(Path(args.controls).read_text()) if args.controls else None
        responsive = json.loads(Path(args.responsive).read_text()) if args.responsive else None
        ids = [r.get("id") for r in rows]
        results = af_results(run, arms, nulls, task=args.task, n_boot=args.n_boot, seed=args.seed,
                             controls=controls, responsive=responsive, ids=ids)
        margins = {"ids": ids, **run}
    meta = {"task": args.task, "variant": args.variant, "readout": readout_info, "positions": args.position_arms,
            "sets": {n: {"members": [list(k) for k in s["members"]], "null_seed": s["null_seed"],
                         "null_kind": s["null_kind"]} for n, s in sets.items()},
            "nulls": {k: v for k, v in nulls.items()}, "null_draws": {k: [list(x) for x in arms[k][0]] for k in arms
                                                                      if "#null" in k},
            "n_null": args.null, "n_boot": args.n_boot, "seed": args.seed, "rows_file": args.rows,
            "n_rows": len(pairs), "seconds": time.time() - t0, "caveat": patching.CAVEAT}
    _write_json(out_dir / "margins.json", {**meta, "margins": margins})
    _write_json(out_dir / "results.json", {**meta, **results})
    data_files = [args.rows, ROOT / "docs" / "research" / "mechanism-analysis" / "phase1" / "p1c_readings.json"]
    if args.task == "af":
        data_files.append(args.tokens)
    path = write_manifest(args, data_files)
    print(f"wrote {out_dir / 'results.json'}, {out_dir / 'margins.json'}, {path}")
    if args.task == "syc":
        print("pass bar:", json.dumps(_clean(results["pass_bar"])))
    elif args.task == "af":
        print("transfer verdict:", results["transfer_verdict"].get("label"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
