"""
CPU scaffold report for the v2 aligned scaffold (mechanism-datasets ticket 02).

Checks, with the real Llama-3.1 tokenizer, everything spec section 4 asks of the
v2 Scaffold before any GPU hour is spent, and writes
``reports/02-scaffold-report.json`` and ``reports/02-scaffold-report.md``:

* predicate-word and item-word tokenization (every item pair failing the
  single-token gate is listed and dropped from v2 use);
* per-task user-turn token counts;
* the clause pools: every flavor clause passes the mechanical screen (and, when
  ``--clause-screen`` is given, the LLM screen), per framing the per-task median
  flavor-clause length is within 1 token across tasks and all flavor clauses sit
  in one band no wider than 6 tokens;
* neutral-pool coverage: every clause of every framing (shared ones included)
  has >= 2 equal-length neutral candidates under every task, variant, suffix
  level and SER wording, measured on a sample of that clause's prompts;
* a 1,000-instance sample realized under every task x framing x suffix x SER
  wording cell (``deception_v2.realize`` asserts alignment and <= 120 tokens in
  every condition), with length summaries and histograms per cell x variant x
  condition;
* the D-prompt (pressure condition) length constraints: <= 120 everywhere, one
  common band no wider than 12 tokens per suffix level, cross-task median gap
  <= 6 tokens (spec 14.C1);
* the SER wording flags, and 3 rendered sample pairs per task with token
  boundaries and the corruption slot marked.

Exits non-zero when any check fails (the report is still written).

    python -m dataset.check_v2_scaffold            # defaults: all r1 framings
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
from collections import defaultdict
from typing import Dict, List

from dataset import clause_screen as cs
from dataset import deception_common as dc
from dataset import deception_v2 as v2
from dataset.report_utils import histogram, length_summary

DEFAULT_REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports"

MAX_LEN = 120
D_BAND = 12
MEDIAN_GAP = 6
CLAUSE_MEDIAN_SPREAD = 1
CLAUSE_BAND = 6
MIN_NEUTRAL = 2

#: (task, ser_wording) pairs: every task, SER once per wording.
TASK_WORDINGS = [("far_v2", None), ("sdr_v2", None), ("ser_v2", "A"),
                 ("ser_v2", "B")]


def tw_name(task, wording):
    return task if wording is None else f"{task}_{wording}"


class Checks:
    def __init__(self):
        self.results = []

    def add(self, name, ok, detail=""):
        self.results.append({"check": name, "ok": bool(ok), "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    @property
    def ok(self):
        return all(r["ok"] for r in self.results)


def n_tokens(tok, text):
    return len(tok.encode(text, add_special_tokens=False))


# ==============================================================================
# SECTIONS
# ==============================================================================

def tokenization_section(tok, checks):
    words = {}
    for t, pieces in v2.SPECS_V2.items():
        for w in (pieces.desig_inversion, pieces.desig_identity):
            words[w] = tok.encode(" " + w, add_special_tokens=False)
    pred_ok = all(len(ids) == 1 for ids in words.values())
    checks.add("predicate words single-token with leading space", pred_ok,
               ", ".join(f"{w}={ids}" for w, ids in words.items()))
    pairs = dc.load_item_pairs(v2.ITEM_PAIRS_PATH)
    item_tok, dropped = {}, []
    for a, b in pairs:
        ids = {w: tok.encode(" " + w, add_special_tokens=False) for w in (a, b)}
        item_tok.update(ids)
        if any(len(i) != 1 for i in ids.values()):
            dropped.append([a, b])
    kept = [p for p in pairs if list(p) not in dropped]
    gate_ok = bool(kept) and all(len(item_tok[w]) == 1 for p in kept for w in p)
    checks.add("item pairs used by v2 are all single-token (failing pairs dropped)",
               gate_ok, f"{len(kept)}/{len(pairs)} kept, dropped {dropped}")
    return {"predicate_words": words, "item_words": item_tok,
            "item_pairs_total": len(pairs), "item_pairs_dropped": dropped}, dropped


def user_turn_section(tok):
    """Tokens after the system turn's <|eot_id|> (user header, question,
    assistant header, stem), and the bare question, per task and variant."""
    out = {}
    for task, wording in TASK_WORDINGS:
        spec = v2.make_spec(task, False, wording)
        for vname in v2.VARIANT_NAMES:
            prompt = v2.build_prompt(spec, vname, "Vantis Medical", "budget",
                                     "timeline", "budget", spec.desig_inversion,
                                     spec.desig_identity, "Clause.")
            head = prompt.split("<|eot_id|>")[0] + "<|eot_id|>"
            v = spec.variant(vname)
            out[f"{tw_name(task, wording)}/{vname}"] = {
                "question_tokens": n_tokens(tok, v.user.format(item_1="budget",
                                                               item_2="timeline")),
                "stem_tokens": n_tokens(tok, v.stem),
                "after_system_turn_tokens": n_tokens(tok, prompt) - n_tokens(tok, head),
            }
    return out


def clause_section(tok, framings, clause_screen, checks):
    out = {}
    for fr in framings:
        per_task, all_flavor = {}, []
        mech_fail = []
        for task in v2.TASKS_V2:
            flavor = [c for c in fr.clauses[task] if not c["shared"]]
            lens = [n_tokens(tok, " " + c["text"]) for c in flavor]
            all_flavor += lens
            per_task[task] = {"median": statistics.median(lens), "min": min(lens),
                              "max": max(lens), "histogram": histogram(lens)}
            for c in fr.clauses[task]:
                v = cs.screen_clause(c["text"], None if c["shared"] else task)
                if v:
                    mech_fail.append((c["id"], v))
        meds = [d["median"] for d in per_task.values()]
        spread = max(meds) - min(meds)
        band = max(all_flavor) - min(all_flavor)
        checks.add(f"{fr.id}: mechanical screen clean (75 clauses)", not mech_fail,
                   str(mech_fail[:5]))
        checks.add(f"{fr.id}: per-task flavor median within {CLAUSE_MEDIAN_SPREAD}",
                   spread <= CLAUSE_MEDIAN_SPREAD, f"medians {meds}")
        checks.add(f"{fr.id}: flavor clauses in one band <= {CLAUSE_BAND}",
                   band <= CLAUSE_BAND, f"{min(all_flavor)}-{max(all_flavor)}")
        referents = {}
        for task in v2.TASKS_V2:
            texts = [c["text"] for c in fr.clauses[task] if not c["shared"]]
            referents[task] = {"shares": cs.referent_shares(texts),
                               "violations": cs.referent_violations(texts)}
        bad = {t: r["violations"] for t, r in referents.items() if r["violations"]}
        checks.add(f"{fr.id}: no referent marker in more than "
                   f"{cs.MAX_REFERENT_SHARE:.0%} of a task's flavor clauses",
                   not bad, str(bad or {t: r["shares"] for t, r in referents.items()}))
        out[fr.id] = {"family": fr.family, "per_task": per_task,
                      "referents": referents,
                      "median_spread": spread,
                      "band": [min(all_flavor), max(all_flavor)],
                      "mechanical_failures": mech_fail}
    shared = [c for c in framings[0].clauses["far_v2"] if c["shared"]]
    out["shared"] = {c["id"]: n_tokens(tok, " " + c["text"]) for c in shared}
    if clause_screen:
        with open(clause_screen) as f:
            screen = json.load(f)
        by_id = {r["id"]: r for r in screen["clauses"]}
        missing, rejected = [], []
        for fr in framings:
            for task in v2.TASKS_V2:
                for c in fr.clauses[task]:
                    r = by_id.get(c["id"])
                    if r is None or r["text"] != c["text"]:
                        missing.append(c["id"])
                    elif not r["accepted"]:
                        rejected.append(c["id"])
        missing = sorted(set(missing))
        checks.add("LLM clause screen covers every clause with current text",
                   not missing, str(missing[:8]))
        checks.add("LLM clause screen accepts every clause", not rejected,
                   str(rejected[:8]))
        out["llm_screen"] = {"path": clause_screen,
                             "summary": screen.get("summary"),
                             "missing": missing, "rejected": rejected}
    return out


def neutral_coverage_section(tok, framings, pool, item_pairs, checks):
    """min #equal-length candidates per clause over task x wording x suffix x
    variant, on a sample of that clause's prompts (shortest and longest entity,
    both item polarities, both designation polarities, both streams)."""
    ents = dc.load_entities()
    by_len = sorted(ents, key=lambda e: n_tokens(tok, e["name"] + "'s"))
    sample_ents = [by_len[0]["name"], by_len[-1]["name"]]
    pair = tuple(item_pairs[0])
    worst, rows = None, []
    for fr in framings:
        for task, wording in TASK_WORDINGS:
            for suffix in (False, True):
                spec = v2.make_spec(task, suffix, wording)
                for vname in v2.VARIANT_NAMES:
                    for c in fr.clauses[task]:
                        prompts = []
                        for e in sample_ents:
                            for pol in (1, 2):
                                for des in ("inversion", "identity"):
                                    b = v2.build_prompt_pair(spec, vname, e, pair,
                                                             pol, des, c["text"])
                                    prompts += [b["clean_prompt"], b["corrupt_prompt"]]
                        k = len(v2.neutral_candidates(tok, prompts, c["text"], pool))
                        row = {"framing": fr.id, "task": tw_name(task, wording),
                               "suffix": spec.suffix_policy, "variant": vname,
                               "clause": c["id"], "n_candidates": k}
                        rows.append(row)
                        if worst is None or k < worst["n_candidates"]:
                            worst = row
    short = [r for r in rows if r["n_candidates"] < MIN_NEUTRAL]
    checks.add(f"every clause has >= {MIN_NEUTRAL} equal-length neutral candidates",
               not short, f"min {worst['n_candidates']} at {worst}; "
                          f"{len(short)} short combos")
    counts = defaultdict(list)
    for r in rows:
        counts[r["clause"]].append(r["n_candidates"])
    return {"sample_entities": sample_ents, "sample_pair": list(pair),
            "n_combos": len(rows), "min": worst,
            "short": short[:50],
            "min_candidates_per_clause": {k: min(v) for k, v in counts.items()}}


def sample_section(tok, framings, pool, instances, checks):
    lengths = {}         # cell -> variant -> condition -> [lengths]
    d_lengths = defaultdict(list)     # (suffix, task_wording) -> D lengths
    d_by_framing = defaultdict(list)  # (framing, suffix, task_wording)
    errors = []
    for fr in framings:
        for task, wording in TASK_WORDINGS:
            for suffix in (False, True):
                spec = v2.make_spec(task, suffix, wording)
                cell = f"{tw_name(task, wording)}/{fr.id}/suffix_{spec.suffix_policy}"
                per = defaultdict(lambda: defaultdict(list))
                for inst in instances:
                    try:
                        rec = v2.realize(tok, spec, fr, inst, pool, MAX_LEN)
                    except (AssertionError, ValueError) as e:
                        errors.append({"cell": cell, "instance_id": inst["instance_id"],
                                       "error": str(e)[:300]})
                        continue
                    for cond, ps in rec["conditions"].items():
                        n = n_tokens(tok, ps["clean_prompt"])
                        per[inst["template_variant"]][cond].append(n)
                        if cond == "pressure":
                            d_lengths[(spec.suffix_policy, tw_name(task, wording))].append(n)
                            d_by_framing[(fr.id, spec.suffix_policy,
                                          tw_name(task, wording))].append(n)
                    per[inst["template_variant"]]["prior_balance"].append(
                        n_tokens(tok, rec["neutral_prompt"]))
                lengths[cell] = {
                    vname: {cond: {"summary": length_summary(L), "histogram": histogram(L)}
                            for cond, L in conds.items()}
                    for vname, conds in per.items()}
    checks.add("every realized record of every condition aligned and <= 120 tokens",
               not errors, f"{len(errors)} errors; first {errors[:2]}")

    bands, gaps = {}, {}
    combos = {"far+sdr+serA": ["far_v2", "sdr_v2", "ser_v2_A"],
              "far+sdr+serB": ["far_v2", "sdr_v2", "ser_v2_B"],
              "all": ["far_v2", "sdr_v2", "ser_v2_A", "ser_v2_B"]}
    for suffix in ("off", "on"):
        for name, tws in combos.items():
            L = [x for tw in tws for x in d_lengths[(suffix, tw)]]
            meds = {tw: statistics.median(d_lengths[(suffix, tw)]) for tw in tws}
            band = max(L) - min(L)
            gap = max(meds.values()) - min(meds.values())
            bands[f"suffix_{suffix}/{name}"] = {"min": min(L), "max": max(L),
                                                "width": band}
            gaps[f"suffix_{suffix}/{name}"] = {"medians": meds, "gap": gap}
            checks.add(f"D-prompt common band <= {D_BAND} (suffix {suffix}, {name})",
                       band <= D_BAND, f"{min(L)}-{max(L)} = {band}")
            checks.add(f"cross-task D-prompt median gap <= {MEDIAN_GAP} "
                       f"(suffix {suffix}, {name})", gap <= MEDIAN_GAP,
                       f"medians {meds}")
    d_max = max(max(L) for L in d_lengths.values())
    checks.add("D prompts <= 120 tokens", d_max <= MAX_LEN, f"max {d_max}")
    d_hist = {f"suffix_{s}/{tw}": histogram(L) for (s, tw), L in d_lengths.items()}
    per_framing = {f"{f}/suffix_{s}/{tw}": length_summary(L)
                   for (f, s, tw), L in d_by_framing.items()}
    return {"n_instances": len(instances), "lengths": lengths,
            "d_prompt_bands": bands, "d_prompt_median_gaps": gaps,
            "d_prompt_histograms": d_hist, "d_prompt_per_framing": per_framing,
            "errors": errors[:50]}


def render_samples(tok, framings, pool, instances):
    out = []
    fr = framings[0]
    # One audit/inversion, one lab/identity, one audit/identity instance, so the
    # samples cover both variants and both designation polarities.
    wanted = [("audit", "inversion"), ("lab", "identity"), ("audit", "identity")]
    picks = [next(i for i in instances if (i["template_variant"],
                                           i["designation_polarity"]) == w)
             for w in wanted]
    for task, wording in (("far_v2", None), ("sdr_v2", None), ("ser_v2", "B")):
        for k, inst in enumerate(picks):
            spec = v2.make_spec(task, bool(k % 2), wording)
            rec = v2.realize(tok, spec, fr, inst, pool, MAX_LEN)
            ids_c, ids_x, d = dc.assert_aligned_pair(
                tok, rec["clean_prompt"], rec["corrupt_prompt"],
                rec["clean_item_d"], rec["corrupt_item_d"], MAX_LEN)
            out.append({
                "task": tw_name(task, wording), "framing": fr.id,
                "suffix": rec["suffix"], "variant": rec["template_variant"],
                "designation_polarity": rec["designation_polarity"],
                "item_polarity": rec["item_polarity"],
                "pressure_id": rec["pressure_id"], "neutral_id": rec["neutral_id"],
                "target": rec["target"], "distractor": rec["distractor"],
                "corruption_position": d, "n_tokens": len(ids_c),
                "clean_tokens": dc.format_token_boundaries(tok, ids_c, mark_pos=d),
                "corrupt_tokens": dc.format_token_boundaries(tok, ids_x, mark_pos=d),
                "conditions_clean": {c: p["clean_prompt"]
                                     for c, p in rec["conditions"].items()},
                "neutral_prompt": rec["neutral_prompt"],
            })
    return out


# ==============================================================================
# MARKDOWN
# ==============================================================================

def to_markdown(report) -> str:
    L = ["# Ticket 02 scaffold report (v2 aligned scaffold, CPU, Llama-3.1 tokenizer)",
         "", f"Generated by `dataset/check_v2_scaffold.py`; verdict: "
             f"**{'all checks pass' if report['ok'] else 'CHECKS FAILED'}**.", "",
         "## Checks", "", "| check | ok | detail |", "|---|---|---|"]
    for c in report["checks"]:
        L.append(f"| {c['check']} | {'yes' if c['ok'] else 'NO'} | "
                 f"{str(c['detail']).replace('|', '/')[:160]} |")
    L += ["", "## User turns (tokens)", "",
          "| task/variant | question | stem | after system turn |", "|---|---|---|---|"]
    for k, v in report["user_turns"].items():
        L.append(f"| {k} | {v['question_tokens']} | {v['stem_tokens']} | "
                 f"{v['after_system_turn_tokens']} |")
    L += ["", "## SER wordings", ""]
    for w in report["ser_wordings"]:
        L.append(f"- Wording {w['wording']} (`{w['question']}` / `{w['stem']}`): "
                 f"**{w['status']}**{' — ' + ', '.join(w['hits']) if w['hits'] else ''}")
    L += ["", "## Clause lengths (standalone tokens, leading space)", "",
          "| framing | far_v2 median | sdr_v2 median | ser_v2 median | band |",
          "|---|---|---|---|---|"]
    for fid, d in report["clauses"].items():
        if fid in ("shared", "llm_screen"):
            continue
        pt = d["per_task"]
        L.append(f"| {fid} | {pt['far_v2']['median']} | {pt['sdr_v2']['median']} | "
                 f"{pt['ser_v2']['median']} | {d['band'][0]}-{d['band'][1]} |")
    L.append(f"\nShared clauses: {report['clauses']['shared']}")
    L += ["", "## D-prompt length bands (pressure condition, all framings pooled)", "",
          "| suffix / tasks | min | max | width | medians |", "|---|---|---|---|---|"]
    for k, b in report["sample"]["d_prompt_bands"].items():
        meds = report["sample"]["d_prompt_median_gaps"][k]["medians"]
        L.append(f"| {k} | {b['min']} | {b['max']} | {b['width']} | {meds} |")
    L += ["", "## D-prompt histograms", ""]
    for k, h in sorted(report["sample"]["d_prompt_histograms"].items()):
        L.append(f"- {k}: " + ", ".join(f"{n}:{c}" for n, c in h.items()))
    L += ["", "## Prompt lengths per cell x variant x condition (median [min-max])", ""]
    for cell, per in report["sample"]["lengths"].items():
        parts = []
        for vname, conds in sorted(per.items()):
            for cond, d in conds.items():
                s = d["summary"]
                parts.append(f"{vname}/{cond} {s['median']} [{s['min']}-{s['max']}]")
        L.append(f"- {cell}: " + "; ".join(parts))
    nc = report["neutral_coverage"]
    L += ["", "## Neutral pool coverage", "",
          f"{nc['n_combos']} (framing, task, suffix, variant, clause) combinations; "
          f"minimum candidates {nc['min']['n_candidates']} at {nc['min']}.", "",
          "## Sample pairs (corruption slot marked >>> <<<)", ""]
    for s in report["samples"]:
        L += [f"### {s['task']} / {s['framing']} / suffix {s['suffix']} / {s['variant']} "
              f"/ {s['designation_polarity']} / item_polarity {s['item_polarity']}", "",
              f"target `{s['target']}`, distractor `{s['distractor']}`, "
              f"{s['n_tokens']} tokens, corruption at {s['corruption_position']}, "
              f"clause {s['pressure_id']}, neutral {s['neutral_id']}", "",
              "```", "CLEAN   " + s["clean_tokens"], "CORRUPT " + s["corrupt_tokens"],
              "```", ""]
        for cond, p in s["conditions_clean"].items():
            L.append(f"- {cond}: `{p.split('<|eot_id|>')[0].split(chr(10))[-1]}`")
        L.append("")
    return "\n".join(L) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--framings", nargs="*", default=None,
                   help="framing files (default: every r1_*.json in the v2 pool)")
    p.add_argument("--neutral-pool", default=v2.NEUTRAL_POOL_PATH)
    p.add_argument("--clause-screen", default=None,
                   help="02-clause-screen.json; when given, every clause must be "
                        "accepted with its current text")
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--model", default=dc.DEFAULT_MODEL)
    p.add_argument("--out-dir", default=DEFAULT_REPORTS)
    args = p.parse_args(argv)

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.model)
    paths = args.framings or sorted(glob.glob(os.path.join(v2.FRAMINGS_DIR, "r1_*.json")))
    framings = [v2.load_framing(path) for path in paths]
    pool = v2.load_neutral_pool(args.neutral_pool)
    checks = Checks()

    tok_section, dropped = tokenization_section(tok, checks)
    item_pairs = v2.load_item_pairs_v2(drop=dropped)
    instances = v2.generate_instances_v2(args.n, seed=args.seed, item_pairs=item_pairs)
    flags = [v2.ser_wording_flags(w) for w in v2.SER_WORDINGS]
    suffix_bad = {}
    for cand in v2.SUFFIX_CANDIDATES:
        for t, pieces in v2.SPECS_V2.items():
            text = cand.format(inv_word=pieces.desig_inversion, noun="result")
            v = [x for x in cs.screen_clause(text, None)
                 if x != f"predicate_word:{pieces.desig_inversion}"]
            if v:
                suffix_bad[text] = v
    checks.add("suffix candidates pass the generic clause rules (no item, "
               "position, caps or imperative; inversion predicate by design)",
               not suffix_bad, str(suffix_bad))
    checks.add("SER wording B clean, wording A judge_decided",
               flags[0]["status"] == "judge_decided" and flags[1]["status"] == "clean",
               str([(f["wording"], f["status"], f["hits"]) for f in flags]))

    report = {
        "framings": [{"id": f.id, "family": f.family, "path": f.path} for f in framings],
        "neutral_pool": {"path": args.neutral_pool, "n": len(pool)},
        "seed": args.seed, "max_seq_length": MAX_LEN,
        "suffix_candidates": list(v2.SUFFIX_CANDIDATES), "suffix": v2.SUFFIX,
        "tokenization": tok_section,
        "user_turns": user_turn_section(tok),
        "ser_wordings": flags,
        "clauses": clause_section(tok, framings, args.clause_screen, checks),
        "neutral_coverage": neutral_coverage_section(tok, framings, pool,
                                                     item_pairs, checks),
        "sample": sample_section(tok, framings, pool, instances, checks),
        "samples": render_samples(tok, framings, pool, instances),
    }
    report["checks"] = checks.results
    report["ok"] = checks.ok
    os.makedirs(args.out_dir, exist_ok=True)
    jpath = os.path.join(args.out_dir, "02-scaffold-report.json")
    with open(jpath, "w") as f:
        json.dump(report, f, indent=1, default=str)
    mpath = os.path.join(args.out_dir, "02-scaffold-report.md")
    with open(mpath, "w") as f:
        f.write(to_markdown(report))
    print(f"wrote {jpath}\nwrote {mpath}\nverdict: {'PASS' if report['ok'] else 'FAIL'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
