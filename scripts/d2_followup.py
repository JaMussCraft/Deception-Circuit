"""
d2_followup.py -- deception-divergence D2 follow-up: the honest-instructed control (plans/D2-followup-plan.md,
spec.md ruling R15).

The D2 premise (scripts/d2_premise.py, frozen) fitted its classifier on D against H, so it could read the presence of
an instruction. This follow-up adds four conditions on the D2 ids and reads them with D2's own feature code on the
R14 full-sequence path, reusing D2's stored D, I and H features byte for byte:

  HI  the honest mirror of the row's own D clause (data/d2/d2_followup_clauses.json), D's forced wrong answer
  DT  D's clause, the true item as the forced answer
  HT  HI's clause, the true item as the forced answer
  IH  the honest mirror of the row's act-form I clause (far_v2 and sdr_v2 act-form test ids), the forced wrong answer

plus a drift anchor: D2's train D rows recomputed in this job and compared with the stored ones (bar 0.25 logits).

Stages:

  build --dry-run  CPU: the pool rules, the mirror pick with its fallback, the R2a fit test, every row built and
                   token-checked, the per-pair and per-split token-match tables, the row counts and the estimate.
                   Exit status 1 when anything blocks submission (any fallback firing on a read id, among others).
  features         GPU: the stack check, the stored refusal direction's sha256 check, then the anchor, the
                   unablated rows and the ablated HI rows (D2's DirectionalAblation with the stored direction).
  read             CPU: the D2 file hashes, the drift anchor (stops above the bar), C_HI (D against HI), the gate,
                   the act-form readings and the per-task and direction labels, the joint DT and HT statistic, and
                   the descriptive readings.

The D2 premise verdict and finding F8 stand whatever this follow-up returns; nothing under the D2 output directory or
results/d2/ is written. Do not run with `python -O`: the row format checks are assert statements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Sequence

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts import d2_premise as P  # noqa: E402
from scripts import d2_rows as R  # noqa: E402

TASKS = R.TASKS
IH_TASKS = ("far_v2", "sdr_v2")          # the act-form reading: far_v2 primary, sdr_v2 secondary, ser_v2 excluded
PRIMARY_TASK, SECONDARY_TASK = "far_v2", "sdr_v2"
D2_OUT = P.DEFAULT_OUT
DEFAULT_OUT = os.path.join(REPO_ROOT, "outputs", "_analyses", "deception-divergence", "d2_followup")
CLAUSES_PATH = os.path.join(REPO_ROOT, "data", "d2", "d2_followup_clauses.json")
D2_DIRECTION_SHA256 = "3e03edcd4b0458be2ce4a8a73468fcbf7ad33047b9c52bb018c1ff81f0bf7cf0"
PINNED_VERSIONS = {"torch": "2.11.0+cu128", "transformers": "5.13.0"}     # job 50155519's stack
PINNED_GPU = "H100"
DRIFT_TOL = 0.25

NEW_CONDITIONS = ("HI", "DT", "HT", "IH")
BASE_OF = {"D": "D", "I": "I", "H": "H", "HI": "HI", "DT": "D", "HT": "HI", "IH": "IH"}
TRUE_ANSWER = ("DT", "HT")
FRAMES = ("drill", "quiz", "game")
BORDER_REASONS = ("B1", "B2", "B3", "B4")
FORMS = ("act", "predicate", "other")
_ALLOWED_SCREEN = ("predicate_word", "imperative_start", "truth_word")
HONEST_ACT = re.compile(r"\b(correct\w*|accurate\w*|true|truthful\w*)\b", re.IGNORECASE)

RATE_UNABLATED_S = 0.214                  # job 50155519, seconds per row on one H100, full-sequence path
RATE_ABLATED_S = 0.231
PRE_REGISTERED_COUNTS = {"arms": {"anchor": 600, "HI": 1909, "DT": 709, "HT": 709, "IH": 245, "HI_ablated": 1309},
                         "unablated": 4172, "ablated": 1309}
C_CONDITIONS = ("gate_pass", "gap_at_least_15", "interval_above_zero", "spread_at_least_030", "loco_all_above_zero",
                "refusal_control_valid", "refusal_does_not_explain", "ih_interaction_above_zero")
CODE_FILES = ("scripts/d2_followup.py",) + P.CODE_FILES
META_KEYS = ("row_id", "task", "split", "role", "instance_id", "condition", "pressure_id", "d_form",
             "designation_polarity", "i_clause_id", "i_form", "frame", "hi_source", "hi_entry")
STANDING = ("The D2 premise verdict (hand-back 07, readings_final) and finding F8 stand whatever this follow-up "
            "returns; its act-form gap under C_HI is a different reading from review 04's under C_H.")


def _b():
    from dataset import build_inversion_v2 as B
    return B


# ==============================================================================
# THE CLAUSE POOL
# ==============================================================================

def load_pool(path: str = CLAUSES_PATH) -> Dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def hi_form(text: str, task: str) -> str:
    """Plan rule 4: act when an honest act word occurs, else predicate on a designation word, else other."""
    B = _b()
    if HONEST_ACT.search(text):
        return "act"
    if {w.lower() for w in B._WORD.findall(text)} & B.predicate_words(task):
        return "predicate"
    return "other"


def ih_mirror(text: str) -> str:
    """The one-word honest mirror of an act-form I clause ("an incorrect" becomes "a correct")."""
    out = re.sub(r"\ban incorrect\b", "a correct", text)
    out = re.sub(r"\bAn incorrect\b", "A correct", out)
    return re.sub(r"\b(incorrect|wrong)\b", "correct", out)


def frame_of(text: str) -> Optional[str]:
    low = text.lower()
    hits = [f for f in FRAMES if re.search(r"\b" + f + r"\b", low)]
    return hits[0] if len(hits) == 1 else None


def _ntok(tokenizer, text: str) -> int:
    return len(tokenizer.encode(" " + text, add_special_tokens=False))


def _honest_violations(tag: str, text: str, task: str) -> List[str]:
    """Rules 1 and 2: no R12 act word, no mislead word, no item, position or other screen hit."""
    from dataset import clause_screen as cs
    B = _b()
    out = []
    if B.ACT_PATTERN.search(text):
        out.append(f"{tag}: rule 1 act word in {text!r}")
    words = {w.lower() for w in B._WORD.findall(text)}
    out += [f"{tag}: rule 1 mislead word {w}" for w in sorted(words & B.MISLEAD_WORDS)]
    out += [f"{tag}: rule 2 {v}" for v in cs.screen_clause(text, task) if not v.startswith(_ALLOWED_SCREEN)]
    return out


def pool_violations(pool: Dict, tokenizer=None) -> List[str]:
    """Plan section 3.2 rules 1, 2 and 4 on every HI mirror, the IH mirror rule, labels and (with a tokenizer)
    equal standalone token counts; [] is clean. Rule 3 (directs to the true item) is the hand review's."""
    B = _b()
    out = []
    seen = Counter()
    for e in pool["hi"]:
        t, dt, ht = e["task"], e["d_clause"], e["hi_clause"]
        tag = f"HI {t} {e['pressure_id']}"
        seen[("hi", e["pressure_id"])] += 1
        out += _honest_violations(tag, ht, t)
        if B.clause_form(dt, t) != e["d_form"]:
            out.append(f"{tag}: d_form label {e['d_form']} but the R12 rule says {B.clause_form(dt, t)}")
        if hi_form(ht, t) != B.clause_form(dt, t):
            out.append(f"{tag}: rule 4 HI form {hi_form(ht, t)} differs from D form {B.clause_form(dt, t)}")
        if any(r not in BORDER_REASONS for r in e.get("borderline", [])):
            out.append(f"{tag}: unknown borderline reason {e['borderline']}")
        if tokenizer is not None and _ntok(tokenizer, ht) != _ntok(tokenizer, dt):
            out.append(f"{tag}: standalone tokens {_ntok(tokenizer, ht)} differ from D's {_ntok(tokenizer, dt)}")
    for e in pool["ih"]:
        t, it, ih = e["task"], e["i_clause"], e["ih_clause"]
        tag = f"IH {t} {e['instructed_inversion_id']}"
        seen[("ih", it)] += 1
        if t not in IH_TASKS:
            out.append(f"{tag}: task outside {IH_TASKS}")
        out += _honest_violations(tag, ih, t)
        if ih != ih_mirror(it):
            out.append(f"{tag}: not the rule mirror of the I clause")
        if B.clause_form(it, t) != "act" or hi_form(ih, t) != "act":
            out.append(f"{tag}: I clause or mirror is not act-form")
        if frame_of(it) is None or frame_of(ih) != frame_of(it):
            out.append(f"{tag}: frame word missing or changed")
        if tokenizer is not None and _ntok(tokenizer, ih) != _ntok(tokenizer, it):
            out.append(f"{tag}: standalone tokens {_ntok(tokenizer, ih)} differ from I's {_ntok(tokenizer, it)}")
    out += [f"duplicate {kind} entry {key}" for (kind, key), n in seen.items() if n > 1]
    return out


def borderline_pids(pool: Dict) -> set:
    return {e["pressure_id"] for e in pool["hi"] if e.get("borderline")}


# ==============================================================================
# PICKS AND PLANS
# ==============================================================================

def default_fits(tokenizer) -> Callable[[Dict, Dict, str], bool]:
    from dataset import deception_v2 as v2
    B = _b()
    return lambda d, h, text: B._fits(tokenizer, d, h, text, v2.MAX_SEQ_LENGTH)


def pick_hi(task: str, d: Dict, h: Dict, entries: Dict[str, Dict], fits, salt: str) -> Dict:
    """The row's own mirror when it fits (R15: a recorded deviation from the inversion builder's sha1 draw); else the
    salted sha1 draw among the other fitting mirrors of the same task and D form, in pool order."""
    own = entries.get(d["pressure_id"])
    if own is not None and fits(d, h, own["hi_clause"]):
        return {"text": own["hi_clause"], "source": "mirror", "entry": own["pressure_id"]}
    form = _b().clause_form(d["pressure"], task)
    others = [e for e in entries.values() if e is not own and e["task"] == task and e["d_form"] == form
              and fits(d, h, e["hi_clause"])]
    if not others:
        return {"text": None, "source": "none", "entry": None}
    k = int(hashlib.sha1((salt + d["instance_id"]).encode()).hexdigest(), 16) % len(others)
    return {"text": others[k]["hi_clause"], "source": "fallback", "entry": others[k]["pressure_id"]}


def pick_ih(i: Dict, h: Dict, by_clause: Dict[str, Dict], fits) -> Dict:
    e = by_clause.get(i["pressure"])
    if e is not None and fits(i, h, e["ih_clause"]):
        return {"text": e["ih_clause"], "source": "mirror", "entry": e["instructed_inversion_id"]}
    return {"text": None, "source": "none", "entry": None}


def derive(row: Dict, text: str) -> Dict:
    """`row` with its clause replaced by `text` in both scored prompts."""
    from dataset.clause_surgery import replace_clause
    new = dict(row)
    for col in ("clean_prompt", "corrupt_prompt"):
        new[col] = replace_clause(row[col], row["pressure"], text)
    new["pressure"] = text
    return new


def plan_followup(task: str, data_dir: str, pool: Dict, fits, test_cap: int = P.TEST_CAP, max_fit: int = 0) -> Dict:
    """Row specs on D2's ids. Roles: anchor (train D, recomputed), fit (train HI), gate (validation HI), test (HI, DT,
    HT on every test id; IH on the act-form test ids of far_v2 and sdr_v2)."""
    B = _b()
    base = P.plan_task(task, data_dir, test_cap, P.CAL_N, max_fit)
    bundles = base["bundles"]
    entries = {e["pressure_id"]: e for e in pool["hi"] if e["task"] == task}
    by_clause = {e["i_clause"]: e for e in pool["ih"] if e["task"] == task}
    ids = {role: sorted({r["instance_id"] for r in base["rows"] if r["role"] == role}) for role in ("fit", "gate")}
    split_of = {"fit": P.FIT_SPLIT, "gate": P.GATE_SPLIT, "test": P.TEST_SPLIT}
    rows, problems, picks = [], [], Counter()

    def meta(split, iid):
        b = bundles[split][iid]
        d, i = b["D"], b["I"]
        return {"pressure_id": d["pressure_id"], "d_form": B.clause_form(d["pressure"], task),
                "designation_polarity": d["designation_polarity"],
                "i_clause_id": i["instructed_inversion_id"] if i else None,
                "i_form": i["instructed_inversion_form"] if i else None,
                "frame": frame_of(i["pressure"]) if i else None}

    def add(role, split, iid, cond, extra=None):
        r = {"row_id": f"{task}:{split}:{iid}:{cond}", "task": task, "split": split, "role": role,
             "instance_id": iid, "condition": cond, "hi_source": None, "hi_entry": None}
        r.update(meta(split, iid))
        r.update(extra or {})
        rows.append(r)

    for role, id_list in (("fit", ids["fit"]), ("gate", ids["gate"]), ("test", base["test_ids"])):
        split = split_of[role]
        for iid in id_list:
            b = bundles[split][iid]
            pk = pick_hi(task, b["D"], b["H"], entries, fits, pool["fallback_salt"])
            picks[f"{split}:{pk['source']}"] += 1
            if role == "fit":
                add("anchor", split, iid, "D")
            if pk["text"] is None:
                problems.append(f"{task} {split} {iid}: no HI clause fits")
                continue
            b["HI"] = derive(b["D"], pk["text"])
            src = {"hi_source": pk["source"], "hi_entry": pk["entry"]}
            add(role, split, iid, "HI", src)
            if role != "test":
                continue
            add("test", split, iid, "DT")
            add("test", split, iid, "HT", src)
            if task in IH_TASKS and meta(split, iid)["d_form"] == "act":
                ipk = pick_ih(b["I"], b["H"], by_clause, fits)
                picks[f"ih:{ipk['source']}"] += 1
                if ipk["text"] is None:
                    problems.append(f"{task} {split} {iid}: no IH mirror fits I clause {b['I']['pressure']!r}")
                    continue
                b["IH"] = derive(b["I"], ipk["text"])
                add("test", split, iid, "IH")
    return {"task": task, "bundles": bundles, "rows": rows, "test_ids": base["test_ids"], "fit_ids": ids["fit"],
            "gate_ids": ids["gate"], "picks": dict(sorted(picks.items())), "problems": problems}


def build_row(task: str, plan: Dict, row: Dict, user_text: Optional[str] = None) -> Dict:
    """The two-turn row of a spec; the acts-on-it turn names the item the model stated (true for DT and HT)."""
    b = plan["bundles"][row["split"]][row["instance_id"]]
    cond = row["condition"]
    item = R.true_item(b, "clean") if cond in TRUE_ANSWER else R.forced_item(b, "clean")
    text = R.followup_text(task, item, R.noun_of(b["D"])) if user_text is None else user_text
    prompt, clause = R.condition_prompt(b, BASE_OF[cond], "clean")
    return R.two_turn(prompt, item, text, clause=clause)


def rows_for_pass(plan: Dict, pass_name: str, roles: Optional[Sequence[str]] = None) -> List[Dict]:
    if pass_name == "ablated":
        return [r for r in plan["rows"] if r["condition"] == "HI" and r["role"] in ("fit", "test")]
    keep = roles or ("fit", "gate", "test")
    return [r for r in plan["rows"] if r["role"] in keep]


def expected_counts(ids: Dict[str, Sequence[int]]) -> Dict:
    """{task: (n_fit, n_gate, n_test, n_act_test)} -> the arm and pass counts of the design."""
    arms = Counter()
    for task, (n_fit, n_gate, n_test, n_act) in ids.items():
        arms["anchor"] += n_fit
        arms["HI"] += n_fit + n_gate + n_test
        arms["DT"] += n_test
        arms["HT"] += n_test
        arms["IH"] += n_act if task in IH_TASKS else 0
        arms["HI_ablated"] += n_fit + n_test
    un = sum(arms[k] for k in ("anchor", "HI", "DT", "HT", "IH"))
    return {"arms": {k: arms[k] for k in ("anchor", "HI", "DT", "HT", "IH", "HI_ablated")}, "unablated": un,
            "ablated": arms["HI_ablated"]}


def blocking(plan: Dict) -> List[str]:
    out = list(plan["problems"])
    n_fb = sum(n for k, n in plan["picks"].items() if k.endswith(":fallback"))
    if n_fb:
        out.append(f"{plan['task']}: the HI fallback fired on {n_fb} read ids (R15: any firing blocks submission)")
    return out


# ==============================================================================
# BUILD STAGE (CPU)
# ==============================================================================

def _count(c: Counter) -> Dict[str, int]:
    return {str(k): v for k, v in sorted(c.items())}


def build_task_report(task: str, plan: Dict, tokenizer, probes: Sequence[Dict]) -> Dict:
    B = _b()
    enc = lambda s: tokenizer.encode(s, add_special_tokens=False)  # noqa: E731
    psuf = P.probe_suffix_ids(tokenizer, probes)
    plen = [len(s) for s in psuf]
    prefix_len, acts_len = [], []
    checks = Counter()
    dt_diff, ht_diff = Counter(), Counter()
    per_split = defaultdict(lambda: {"ids": 0, "d_forms": Counter(), "mirror": 0, "fallback": 0,
                                     "form_mismatch": 0, "full_prompt_hi_minus_d": Counter(),
                                     "clause_hi_minus_d": Counter(), "hi_aligned_with_d": 0})
    pairs = defaultdict(lambda: {"rows": Counter(), "full_prompt_diff": Counter(), "fallback": 0})
    ih_pairs = defaultdict(lambda: {"rows": 0, "full_prompt_diff": Counter()})
    built_d = {}
    for k, row in enumerate(plan["rows"]):
        built = build_row(task, plan, row)
        if k < P.RENDER_CHECK_ROWS:
            P.check_render(tokenizer, built)
        ts = R.token_spans(tokenizer, built)
        pre, suf = P.encode_row(tokenizer, built)
        prefix_len.append(len(pre))
        acts_len.append(len(suf))
        b = plan["bundles"][row["split"]][row["instance_id"]]
        cond, key = row["condition"], (row["split"], row["instance_id"])
        if cond == "D":
            built_d[key] = (built, ts)
        if key not in built_d:
            d_built = build_row(task, plan, dict(row, condition="D"))
            built_d[key] = (d_built, R.token_spans(tokenizer, d_built))
        d_built, d_ts = built_d[key]
        if cond == "HI":
            s = per_split[row["split"]]
            s["ids"] += 1
            s["d_forms"][row["d_form"]] += 1
            s[row["hi_source"]] += 1
            if hi_form(b["HI"]["pressure"], task) != row["d_form"]:
                s["form_mismatch"] += 1
                checks["form_mismatch"] += 1
            full = len(enc(b["HI"]["clean_prompt"])) - len(enc(b["D"]["clean_prompt"]))
            s["full_prompt_hi_minus_d"][full] += 1
            s["clause_hi_minus_d"][_ntok(tokenizer, b["HI"]["pressure"]) - _ntok(tokenizer, b["D"]["pressure"])] += 1
            ok = R.aligned(tokenizer, built, d_built)
            s["hi_aligned_with_d"] += ok
            checks["HI_D_aligned" if ok else "HI_D_not_aligned"] += 1
            p = pairs[row["hi_entry"]]
            p["rows"][row["split"]] += 1
            p["full_prompt_diff"][full] += 1
            p["fallback"] += row["hi_source"] == "fallback"
        elif cond == "IH":
            i_built = build_row(task, plan, dict(row, condition="I"))
            ok = R.aligned(tokenizer, built, i_built)
            checks["IH_I_aligned" if ok else "IH_I_not_aligned"] += 1
            e = ih_pairs[b["I"]["instructed_inversion_id"]]
            e["rows"] += 1
            e["full_prompt_diff"][len(enc(b["IH"]["clean_prompt"])) - len(enc(b["I"]["clean_prompt"]))] += 1
        elif cond == "DT":
            dt_diff[ts["n_tokens"] - d_ts["n_tokens"]] += 1
            if not R.item_is_one_token(tokenizer, R.true_item(b, "clean")):
                checks["true_item_multi_token"] += 1
        elif cond == "HT":
            ht_diff[ts["n_tokens"] - d_ts["n_tokens"]] += 1
            dt_built = build_row(task, plan, dict(row, condition="DT"))
            ok = R.aligned(tokenizer, built, dt_built)
            checks["HT_DT_aligned" if ok else "HT_DT_not_aligned"] += 1
    for name in ("form_mismatch", "true_item_multi_token", "HI_D_aligned", "IH_I_aligned", "HT_DT_aligned"):
        checks.setdefault(name, 0)
    counts = Counter((r["role"], r["condition"]) for r in plan["rows"])
    entries = {e["pressure_id"]: e for e in load_pool_cached()["hi"]}
    pair_table = {}
    for pid, p in sorted(pairs.items()):
        e = entries[pid]
        pair_table[pid] = {"d_form": e["d_form"], "hi_form": hi_form(e["hi_clause"], task),
                           "clause_tokens": [_ntok(tokenizer, e["d_clause"]), _ntok(tokenizer, e["hi_clause"])],
                           "words_changed": e["words_changed"], "borderline": e["borderline"],
                           "rows": dict(p["rows"]), "fallback": p["fallback"],
                           "full_prompt_diff": _count(p["full_prompt_diff"])}
    ih_entries = {e["instructed_inversion_id"]: e for e in load_pool_cached()["ih"]}
    ih_table = {}
    for cid, p in sorted(ih_pairs.items()):
        e = ih_entries[cid]
        ih_table[cid] = {"clause_tokens": [_ntok(tokenizer, e["i_clause"]), _ntok(tokenizer, e["ih_clause"])],
                         "frame": frame_of(e["i_clause"]), "rows": p["rows"],
                         "full_prompt_diff": _count(p["full_prompt_diff"])}
    act_test = sum(1 for r in plan["rows"] if r["role"] == "test" and r["condition"] == "HI" and r["d_form"] == "act")
    width = sum(prefix_len) / len(prefix_len) + max(max(plen), max(acts_len))
    return {
        "task": task,
        "ids": {"fit": len(plan["fit_ids"]), "gate": len(plan["gate_ids"]), "test": len(plan["test_ids"]),
                "test_act_form": act_test},
        "rows": {f"{role}:{cond}": n for (role, cond), n in sorted(counts.items())},
        "rows_unablated_pass": len(rows_for_pass(plan, "unablated", ("anchor", "fit", "gate", "test"))),
        "rows_ablated_pass": len(rows_for_pass(plan, "ablated")),
        "picks": plan["picks"], "problems": plan["problems"],
        "checks": dict(checks, DT_minus_D_tokens=_count(dt_diff), HT_minus_D_tokens=_count(ht_diff)),
        "per_split": {s: dict(v, d_forms=dict(v["d_forms"]),
                              full_prompt_hi_minus_d=_count(v["full_prompt_hi_minus_d"]),
                              clause_hi_minus_d=_count(v["clause_hi_minus_d"]))
                      for s, v in sorted(per_split.items())},
        "pairs": pair_table, "ih_pairs": ih_table,
        "tokens": {"mean_prefix": round(sum(prefix_len) / len(prefix_len), 1),
                   "probe_turn_max": max(plen), "acts_turn_max": max(acts_len),
                   "full_path_tokens_per_row": round((len(probes) + 1) * width, 1)},
        "test_ids_sha256": hashlib.sha256("\n".join(plan["test_ids"]).encode()).hexdigest(),
    }


_POOL_CACHE: Dict[str, Dict] = {}


def load_pool_cached(path: str = CLAUSES_PATH) -> Dict:
    if path not in _POOL_CACHE:
        _POOL_CACHE[path] = load_pool(path)
    return _POOL_CACHE[path]


def estimate(reports: Sequence[Dict]) -> Dict:
    """Measured D2 rates (the estimate of record) and the D2 plan's model constant (the upper reference)."""
    un = sum(r["rows_unablated_pass"] for r in reports)
    ab = sum(r["rows_ablated_pass"] for r in reports)
    meas = un * RATE_UNABLATED_S + ab * RATE_ABLATED_S + P.EST_LOAD_S
    model = P.EST_LOAD_S + sum((r["rows_unablated_pass"] + r["rows_ablated_pass"]) *
                               (r["tokens"]["full_path_tokens_per_row"] / P.EST_TOKENS_PER_S +
                                P.EST_FORWARD_OVERHEAD_S) for r in reports)
    return {"rows": {"unablated": un, "ablated": ab},
            "measured": {"seconds": round(meas), "gpu_hours": round(meas / 3600.0, 2),
                         "rates_s_per_row": {"unablated": RATE_UNABLATED_S, "ablated": RATE_ABLATED_S},
                         "load_s": P.EST_LOAD_S},
            "model_constant": {"seconds": round(model), "gpu_hours": round(model / 3600.0, 2),
                               "tokens_per_s": P.EST_TOKENS_PER_S, "forward_overhead_s": P.EST_FORWARD_OVERHEAD_S},
            "reservation": "00:45:00"}


def _pre_registered(args) -> bool:
    return args.max_test_ids == P.TEST_CAP and args.max_fit_ids == 0 and list(args.tasks) == list(TASKS)


def run_build(args, tokenizer, fits=None) -> int:
    if not args.dry_run:
        raise SystemExit("build is CPU-only and writes reports only; pass --dry-run")
    pool = load_pool(args.clauses)
    _POOL_CACHE[CLAUSES_PATH] = pool
    viol = pool_violations(pool, tokenizer)
    fits = fits or default_fits(tokenizer)
    probes = P.load_inputs(args.inputs)["probes"]
    reports, blocked = {}, [f"pool: {v}" for v in viol]
    for task in args.tasks:
        t0 = time.time()
        plan = plan_followup(task, args.data_dir, pool, fits, args.max_test_ids, args.max_fit_ids)
        rep = build_task_report(task, plan, tokenizer, probes)
        rep["seconds_cpu"] = round(time.time() - t0, 1)
        reports[task] = rep
        blocked += blocking(plan)
        c = rep["checks"]
        for name, bad in (("form_mismatch", c["form_mismatch"]), ("true_item_multi_token", c["true_item_multi_token"]),
                          ("HI_D_not_aligned", c.get("HI_D_not_aligned", 0)),
                          ("IH_I_not_aligned", c.get("IH_I_not_aligned", 0)),
                          ("HT_DT_not_aligned", c.get("HT_DT_not_aligned", 0))):
            if bad:
                blocked.append(f"{task}: {bad} rows with {name}")
        for name in ("DT_minus_D_tokens", "HT_minus_D_tokens"):
            if set(c[name]) - {"0"}:
                blocked.append(f"{task}: {name} not zero on every row: {c[name]}")
        print(json.dumps({"task": task, "ids": rep["ids"], "rows": rep["rows"], "picks": rep["picks"],
                          "checks": rep["checks"], "seconds_cpu": rep["seconds_cpu"]}, indent=1), flush=True)
    pre = _pre_registered(args)
    got = expected_counts({t: (r["ids"]["fit"], r["ids"]["gate"], r["ids"]["test"], r["ids"]["test_act_form"])
                           for t, r in reports.items()})
    if pre and got != PRE_REGISTERED_COUNTS:
        blocked.append(f"row counts {got} differ from the pre-registered {PRE_REGISTERED_COUNTS}")
    d2_dir = os.path.join(args.d2_root, "refusal_direction.pt")
    summary = {"created": datetime.now().isoformat(timespec="seconds"), "tasks": reports,
               "pre_registered": pre, "counts": got, "pre_registered_counts": PRE_REGISTERED_COUNTS,
               "counts_match": got == PRE_REGISTERED_COUNTS,
               "pool": {"path": os.path.relpath(args.clauses, REPO_ROOT), "sha256": P.sha256_file(args.clauses),
                        "hi": len(pool["hi"]), "ih": len(pool["ih"]),
                        "borderline": sorted(borderline_pids(pool))},
               "pool_violations": viol,
               "mirror_pick": {"rule": "own mirror; salted sha1 draw (salt " + pool["fallback_salt"] + ") among other "
                               "fitting mirrors of the same task and D form as the fallback; a recorded deviation "
                               "from the inversion builder's draw",
                               "fallback_firings": {t: sum(n for k, n in r["picks"].items() if k.endswith(":fallback"))
                                                    for t, r in reports.items()}},
               "estimate": estimate(list(reports.values())),
               "refusal_direction": {"path": os.path.relpath(d2_dir, REPO_ROOT),
                                     "expected_sha256": D2_DIRECTION_SHA256,
                                     "local_sha256": P.sha256_file(d2_dir) if os.path.exists(d2_dir) else None},
               "inputs_sha256": P.sha256_file(args.inputs), "code_sha256": code_hashes(),
               "blocked": blocked, "submission_blocked": bool(blocked)}
    P.write_json(args.report or os.path.join(args.out_root, "build_report.json"), summary)
    print(json.dumps({k: summary[k] for k in ("counts", "counts_match", "estimate", "mirror_pick", "blocked")},
                     indent=1), flush=True)
    return 1 if blocked else 0


# ==============================================================================
# FEATURES STAGE (GPU)
# ==============================================================================

def code_hashes() -> Dict[str, str]:
    return {p: P.sha256_file(os.path.join(REPO_ROOT, p)) for p in CODE_FILES}


def check_stack(versions: Dict, gpu: Optional[str]) -> List[str]:
    """Differences from job 50155519's stack (R15): torch, transformers and an H100."""
    out = [f"{k} {versions.get(k)} is not the pinned {v}" for k, v in PINNED_VERSIONS.items() if versions.get(k) != v]
    if not gpu or PINNED_GPU not in gpu:
        out.append(f"GPU {gpu!r} is not an {PINNED_GPU}")
    return out


def d2_feature_hashes(d2_root: str, tasks: Sequence[str]) -> Dict:
    out = {}
    for t in tasks:
        for p in P.PASSES:
            path = os.path.join(P.task_dir(d2_root, t), f"features_{p}.jsonl")
            out[f"{t}/features_{p}.jsonl"] = P.sha256_file(path) if os.path.exists(path) else None
    return out


def manifest(stage: str, args, commit: str, extra: Optional[Dict] = None) -> Dict:
    m = {"stage": stage, "commit": commit, "created": datetime.now().isoformat(timespec="seconds"),
         "model": args.model, "dtype": "bfloat16", "tasks": list(args.tasks), "argv": list(sys.argv),
         "versions": P._versions(), "code_sha256": code_hashes(), "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
         "host": os.uname().nodename, "path_of_record": "full",
         "samples": {"max_test_ids": args.max_test_ids, "max_fit_ids": args.max_fit_ids,
                     "pre_registered": _pre_registered(args)},
         "clauses": {"path": os.path.relpath(args.clauses, REPO_ROOT), "sha256": P.sha256_file(args.clauses)},
         "inputs": {"path": os.path.relpath(args.inputs, REPO_ROOT), "sha256": P.sha256_file(args.inputs)},
         "d2_root": os.path.relpath(args.d2_root, REPO_ROOT),
         "d2_feature_sha256": d2_feature_hashes(args.d2_root, args.tasks)}
    m.update(extra or {})
    return m


def feature_rows(model, tokenizer, task: str, plan: Dict, rows: Sequence[Dict], probes, yes_ids, no_ids, device,
                 pass_name: str, ablation=None, pad_id: int = 0, label: str = "") -> List[Dict]:
    """D2's row features (`d2_premise.row_features`) on the full-sequence path of record (R14)."""
    psuf = P.probe_suffix_ids(tokenizer, probes)
    out = []
    t0 = time.time()
    with (ablation if ablation is not None else P.null_context()):
        for k, row in enumerate(rows):
            rec = P.row_features(model, tokenizer, build_row(task, plan, row), psuf, yes_ids, no_ids, device,
                                 use_cache=False, pad_id=pad_id)
            rec.update({key: row.get(key) for key in META_KEYS})
            rec["pass"] = pass_name
            out.append(rec)
            if (k + 1) % 200 == 0:
                print(f"  {task} {label}: {k + 1}/{len(rows)} rows, {time.time() - t0:.0f} s", flush=True)
    return out


def anchor_drift(anchor: Sequence[Dict], d2_unablated: Sequence[Dict]) -> Dict:
    stored = {r["instance_id"]: r for r in d2_unablated if r["role"] == "fit" and r["condition"] == "D"}
    diffs, missing, identical = [], 0, 0
    for r in anchor:
        s = stored.get(r["instance_id"])
        if s is None:
            missing += 1
            continue
        d = max(abs(a - b) for a, b in zip(r["features"], s["features"]))
        diffs.append(d)
        identical += r["features"] == s["features"]
    mx = max(diffs) if diffs else None
    return {"rows": len(diffs), "missing": missing, "bit_identical_rows": identical, "max_abs_diff": mx,
            "mean_max_abs_diff": (sum(diffs) / len(diffs)) if diffs else None, "tolerance": DRIFT_TOL,
            "exceeds": bool(missing or mx is None or mx > DRIFT_TOL)}


def run_features(args, tokenizer, model_loader=None, fits=None) -> int:
    import torch
    injected = model_loader is not None
    commit = os.environ.get("DD_COMMIT", "test") if injected else P._commit_from_env()
    # the stored refusal direction, verified before anything else (R15)
    dpath = os.path.join(args.d2_root, "refusal_direction.pt")
    if not os.path.exists(dpath):
        raise SystemExit(f"{dpath} is missing; the follow-up reuses D2's stored direction")
    got = P.sha256_file(dpath)
    if got != D2_DIRECTION_SHA256:
        raise SystemExit(f"refusal direction sha256 {got} is not D2's {D2_DIRECTION_SHA256}")
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    stack = check_stack(P._versions(), gpu)
    if stack and not injected and not args.allow_stack_mismatch:
        raise SystemExit("stack differs from job 50155519 (R15): " + "; ".join(stack))
    pool = load_pool(args.clauses)
    _POOL_CACHE[CLAUSES_PATH] = pool
    viol = pool_violations(pool)
    if viol:
        raise SystemExit("pool violations: " + "; ".join(viol))
    fits = fits or default_fits(tokenizer)
    t_plan = time.time()
    plans = {t: plan_followup(t, args.data_dir, pool, fits, args.max_test_ids, args.max_fit_ids) for t in args.tasks}
    blocked = [b for t in args.tasks for b in blocking(plans[t])]
    if blocked:
        raise SystemExit("submission blocked: " + "; ".join(blocked))
    plan_s = time.time() - t_plan
    probes = P.load_inputs(args.inputs)["probes"]
    yes = P.word_ids(tokenizer, P.YES_WORDS, ("Yes",))
    no = P.word_ids(tokenizer, P.NO_WORDS, ("No",))
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    saved = torch.load(dpath, map_location="cpu")
    vec = saved.get("direction")
    if vec is None or not saved.get("valid"):
        raise SystemExit("the stored refusal direction is absent or invalid")
    t_load = time.time()
    model, device = (model_loader or P._load_model)(args)
    timings = {"plan_s": round(plan_s, 1), "load_s": round(time.time() - t_load, 1), "gpu": gpu}
    common = {"refusal_direction_sha256": got, "stack_check": stack, "gpu": gpu, "yes_ids": yes, "no_ids": no}

    def write(task, name, recs, secs, extra=None):
        path = os.path.join(P.task_dir(args.out_root, task), f"features_{name}.jsonl")
        P.write_jsonl(path, recs)
        P.write_json(os.path.join(P.task_dir(args.out_root, task), f"features_{name}.manifest.json"),
                     manifest(f"features_{name}", args, commit,
                              dict(common, rows=len(recs), seconds=round(secs, 1), sha256=P.sha256_file(path),
                                   picks=plans[task]["picks"],
                                   test_ids_sha256=hashlib.sha256("\n".join(plans[task]["test_ids"]).encode()
                                                                  ).hexdigest(), **(extra or {}))))
        timings[f"{task}_{name}_s"] = round(secs, 1)
        print(f"{task} {name}: {len(recs)} rows in {secs:.0f} s", flush=True)

    def done(task, name):
        p = os.path.join(P.task_dir(args.out_root, task), f"features_{name}.jsonl")
        if os.path.exists(p) and not args.overwrite:
            print(f"{p} exists; skipping (pass --overwrite to redo)")
            return True
        return False

    # 1. the drift anchor first, so the log shows it before anything else is spent
    drift = {}
    for task in args.tasks:
        if done(task, "anchor"):
            continue
        t0 = time.time()
        recs = feature_rows(model, tokenizer, task, plans[task], rows_for_pass(plans[task], "unablated", ("anchor",)),
                            probes, yes, no, device, "unablated", pad_id=pad, label="anchor")
        d2u = os.path.join(P.task_dir(args.d2_root, task), "features_unablated.jsonl")
        drift[task] = anchor_drift(recs, P.read_jsonl(d2u)) if os.path.exists(d2u) else {"exceeds": True,
                                                                                          "missing_d2_file": d2u}
        write(task, "anchor", recs, time.time() - t0, {"drift": drift[task]})
        print(f"{task} drift anchor: {drift[task]}", flush=True)
    if drift:
        P.write_json(os.path.join(args.out_root, "drift_anchor.json"), summarise_drift(drift))
    # 2. the unablated rows, 3. the ablated HI rows
    for task in args.tasks:
        if done(task, "unablated"):
            continue
        t0 = time.time()
        recs = feature_rows(model, tokenizer, task, plans[task], rows_for_pass(plans[task], "unablated"), probes, yes,
                            no, device, "unablated", pad_id=pad, label="unablated")
        write(task, "unablated", recs, time.time() - t0)
    for task in args.tasks:
        if done(task, "ablated"):
            continue
        t0 = time.time()
        recs = feature_rows(model, tokenizer, task, plans[task], rows_for_pass(plans[task], "ablated"), probes, yes,
                            no, device, "ablated", ablation=P.DirectionalAblation(model, vec), pad_id=pad,
                            label="ablated")
        write(task, "ablated", recs, time.time() - t0)
    P.write_json(os.path.join(args.out_root, f"gpu_timings_{int(time.time())}.json"), timings)
    return 0


def summarise_drift(per_task: Dict[str, Dict]) -> Dict:
    vals = [d.get("max_abs_diff") for d in per_task.values()]
    mx = max(v for v in vals if v is not None) if any(v is not None for v in vals) else None
    return {"tasks": per_task, "max_abs_diff": mx, "tolerance": DRIFT_TOL,
            "exceeds": any(d.get("exceeds") for d in per_task.values())}


# ==============================================================================
# READ STAGE (CPU)
# ==============================================================================

def _index(recs: Optional[Iterable[Dict]]) -> Dict:
    out = defaultdict(dict)
    for r in recs or ():
        out[(r["role"], r["condition"])][r["instance_id"]] = r
    return out


def fit_clf(pos: Sequence[Dict], neg: Sequence[Dict]) -> Dict:
    """D2's classifier (R10): standardised features, L2 logistic regression, C = 1, threshold 0.5."""
    import numpy as np
    X = P._matrix(list(pos) + list(neg))
    y = np.asarray([1] * len(pos) + [0] * len(neg))
    mu, sd = X.mean(axis=0), np.where(X.std(axis=0) > 0, X.std(axis=0), 1.0)
    return {"mu": mu, "sd": sd, "beta": P.fit_logreg((X - mu) / sd, y)}


def clf_scores(clf: Dict, rows: Sequence[Dict]):
    """(probability, logit) arrays."""
    import numpy as np
    if not rows:
        return np.zeros(0), np.zeros(0)
    Z = (P._matrix(rows) - clf["mu"]) / clf["sd"]
    return P.predict_proba(clf["beta"], Z), Z @ clf["beta"][:-1] + clf["beta"][-1]


def _rate(lab: Dict[str, int], ids: Sequence[str]) -> Optional[float]:
    return (sum(lab[i] for i in ids) / len(ids)) if ids else None


def _gap_block(lab: Dict[str, Dict[str, int]], ids: Sequence[str], clusters: Dict[str, str]) -> Dict:
    diffs = [lab["D"][i] - lab["I"][i] for i in ids]
    return {"n": len(ids), "gap": (sum(diffs) / len(diffs)) if ids else None,
            "ci95": P.cluster_bootstrap(diffs, [clusters[i] for i in ids]) if ids else None}


def ratio_bootstrap(lab: Dict[str, Dict[str, int]], ids: Sequence[str], clusters: Dict[str, str],
                    n_boot: int = P.N_BOOT, seed: int = P.BOOT_SEED) -> Dict:
    """Clustered percentile interval of p_DT - p_HT, p_X = (rate_X - rate_HI) / (rate_D - rate_HI)."""
    import numpy as np
    labels = sorted({clusters[i] for i in ids})
    if not labels:
        return {"ci95": None, "n_undefined": None}
    idx = {lab_: k for k, lab_ in enumerate(labels)}
    cnt = np.zeros(len(labels))
    sums = {c: np.zeros(len(labels)) for c in ("D", "HI", "DT", "HT")}
    for i in ids:
        k = idx[clusters[i]]
        cnt[k] += 1
        for c in sums:
            sums[c][k] += lab[c][i]
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, len(labels), size=(n_boot, len(labels)))
    n = cnt[picks].sum(axis=1)
    r = {c: sums[c][picks].sum(axis=1) / n for c in sums}
    spread = r["D"] - r["HI"]
    ok = np.abs(spread) > 1e-12
    stat = ((r["DT"][ok] - r["HI"][ok]) - (r["HT"][ok] - r["HI"][ok])) / spread[ok]
    if not len(stat):
        return {"ci95": None, "n_undefined": int((~ok).sum())}
    return {"ci95": [float(np.percentile(stat, 2.5)), float(np.percentile(stat, 97.5))],
            "n_undefined": int((~ok).sum())}


def _level(p: Optional[float]) -> Optional[str]:
    if p is None:
        return None
    return "high" if p >= P.R2_HIGH - 1e-12 else "low" if p <= P.R2_LOW + 1e-12 else "middle"


def joint_cell(p_dt: Optional[float], p_ht: Optional[float]) -> str:
    a, b = _level(p_dt), _level(p_ht)
    if a is None or b is None:
        return "undefined"
    return {("high", "low"): "instruction content", ("low", "high"): "compliance",
            ("low", "low"): "conjunction (has lied) or truth shift",
            ("high", "high"): "HI-specific or truth shift"}.get((a, b), "no label")


def task_label(task: str, gate_pass: bool, conditions: Dict[str, bool]) -> str:
    """Per task (R15): (a) the D-against-HI gate fails; (c) the gate passes and every act-form condition holds (far_v2
    and sdr_v2 only); (b) otherwise."""
    if not gate_pass:
        return "a"
    if task in IH_TASKS and conditions and all(conditions.get(k) for k in C_CONDITIONS):
        return "c"
    return "b"


def direction_label(labels: Dict[str, str]) -> Dict:
    """(c) when far_v2 is (c); a (c) on sdr_v2 alone is suggestive and does not re-admit U1; (a) when every task is
    (a); (b) otherwise."""
    far, sdr = labels.get(PRIMARY_TASK), labels.get(SECONDARY_TASK)
    if far == "c":
        out = {"label": "c", "suggestive": False, "u1_readmission_possible": True,
               "note": "far_v2 meets (c); re-admitting U1 still needs a new ruling, which must weigh the I frame words"}
    elif sdr == "c":
        out = {"label": "c", "suggestive": True, "u1_readmission_possible": False,
               "note": "sdr_v2 alone meets (c) (35 ids, 7 clusters): reported as suggestive; U1 is not re-admitted"}
    elif labels and all(v == "a" for v in labels.values()):
        out = {"label": "a", "suggestive": False, "u1_readmission_possible": False,
               "note": "the D-against-HI gate fails on every task: the D2 separation was instruction presence"}
    else:
        out = {"label": "b", "suggestive": False, "u1_readmission_possible": False,
               "note": "D and I share what C_HI reads (instructed falsity or instruction content)"}
    out["standing"] = STANDING
    return out


def read_task(task: str, d2_un: Sequence[Dict], d2_ab: Optional[Sequence[Dict]], fu_un: Sequence[Dict],
              fu_ab: Optional[Sequence[Dict]], borderline_pids: Iterable[str] = ()) -> Dict:
    import numpy as np
    U, A, FU, FA = _index(d2_un), _index(d2_ab), _index(fu_un), _index(fu_ab)
    meta = {}
    for (role, cond), rows in FU.items():
        if cond == "HI":
            for i, r in rows.items():
                meta[(role, i)] = r
    fit_ids = sorted(set(U[("fit", "D")]) & set(FU[("fit", "HI")]))
    gate_ids = sorted(set(U[("gate", "D")]) & set(FU[("gate", "HI")]))
    clf = fit_clf([U[("fit", "D")][i] for i in fit_ids], [FU[("fit", "HI")][i] for i in fit_ids])

    def scores(src, role, cond, ids, c=clf):
        p, z = clf_scores(c, [src[(role, cond)][i] for i in ids])
        return dict(zip(ids, p.tolist())), dict(zip(ids, z.tolist()))

    gD, _ = scores(U, "gate", "D", gate_ids)
    gH, _ = scores(FU, "gate", "HI", gate_ids)
    gate_auroc = P.auroc([gD[i] for i in gate_ids], [gH[i] for i in gate_ids]) if gate_ids else None
    gate_pass = gate_auroc is not None and gate_auroc >= P.GATE_AUROC
    gate_act = [i for i in gate_ids if meta[("gate", i)]["d_form"] == "act"]
    gate_act_auroc = P.auroc([gD[i] for i in gate_act], [gH[i] for i in gate_act]) if gate_act else None

    test_ids = sorted(set(U[("test", "D")]) & set(U[("test", "I")]) & set(U[("test", "H")]) &
                      set(FU[("test", "HI")]) & set(FU[("test", "DT")]) & set(FU[("test", "HT")]))
    tmeta = {i: meta[("test", i)] for i in test_ids}
    prob, logit = {}, {}
    for c, src in (("D", U), ("I", U), ("H", U), ("HI", FU), ("DT", FU), ("HT", FU)):
        prob[c], logit[c] = scores(src, "test", c, test_ids)
    ih_ids = sorted(set(FU[("test", "IH")]) & set(test_ids))
    prob["IH"], logit["IH"] = scores(FU, "test", "IH", ih_ids)
    lab = {c: {i: int(p >= 0.5) for i, p in prob[c].items()} for c in prob}
    dcl = {i: tmeta[i]["pressure_id"] for i in test_ids}
    icl = {i: tmeta[i]["i_clause_id"] for i in test_ids}
    rates_all = {c: _rate(lab[c], test_ids) for c in ("D", "I", "H", "HI", "DT", "HT")}

    res = {"task": task, "classifier": {
        "role": "primary", "n_fit": len(fit_ids), "n_gate": len(gate_ids), "gate_auroc": gate_auroc,
        "gate_pass": gate_pass, "train_auroc": P.auroc(*[clf_scores(clf, [s[("fit", c)][i] for i in fit_ids])[0]
                                                        for s, c in ((U, "D"), (FU, "HI"))]),
        "beta": [float(b) for b in clf["beta"]]}}

    # ---- primary: the act-form reading (far_v2 primary, sdr_v2 secondary, ser_v2 excluded) ----
    act_ids = [i for i in test_ids if tmeta[i]["d_form"] == "act"]
    if task not in IH_TASKS:
        prim = {"role": "excluded", "status": f"excluded: {len(act_ids)} act-form test ids", "n": len(act_ids),
                "conditions": {}}
    else:
        act_ids = [i for i in act_ids if i in prob["IH"]]
        g = _gap_block(lab, act_ids, dcl)
        rates_act = {c: _rate(lab[c], act_ids) for c in ("D", "I", "H", "HI", "DT", "HT", "IH")}
        spread = (rates_act["D"] - rates_act["HI"]) if act_ids else None
        p_i = ((rates_act["I"] - rates_act["HI"]) / spread) if spread else None
        loco = {}
        for cl in sorted({dcl[i] for i in act_ids}):
            keep = [i for i in act_ids if dcl[i] != cl]
            loco[cl] = (sum(lab["D"][i] - lab["I"][i] for i in keep) / len(keep)) if keep else None
        loco_ok = bool(loco) and all(v is not None and v > 0 for v in loco.values())
        # refusal control (R12 as in D2, R15 scope): ablated C_HI on the same ids and statistic
        refusal = {"status": "absent"}
        if d2_ab is not None and fu_ab is not None:
            afit = sorted(set(A[("fit", "D")]) & set(FA[("fit", "HI")]))
            if afit:
                aclf = fit_clf([A[("fit", "D")][i] for i in afit], [FA[("fit", "HI")][i] for i in afit])
                aids = [i for i in act_ids if i in A[("test", "D")] and i in A[("test", "I")]
                        and i in FA[("test", "HI")]]
                ap = {c: scores(src, "test", c, aids, aclf)[0] for c, src in (("D", A), ("I", A), ("HI", FA))}
                alab = {c: {i: int(v >= 0.5) for i, v in ap[c].items()} for c in ap}
                agap = (sum(alab["D"][i] - alab["I"][i] for i in aids) / len(aids)) if aids else None
                aall = [i for i in test_ids if i in A[("test", "D")] and i in FA[("test", "HI")]]
                apall = {c: scores(src, "test", c, aall, aclf)[0] for c, src in (("D", A), ("HI", FA))}
                refusal = {"status": "read", "n_fit": len(afit), "n": len(aids), "gap": agap,
                           "rates": {c: _rate(alab[c], aids) for c in alab},
                           "ablated_auroc_D_vs_HI": P.auroc([ap["D"][i] for i in aids], [ap["HI"][i] for i in aids])
                           if aids else None,
                           "ablated_auroc_D_vs_HI_all_test_ids": P.auroc([apall["D"][i] for i in aall],
                                                                          [apall["HI"][i] for i in aall])
                           if aall else None,
                           "explains": P.explains(g["gap"], agap)}
        # frame control: the IH interaction on the C_HI logit
        inter = [(logit["D"][i] - logit["I"][i]) - (logit["HI"][i] - logit["IH"][i]) for i in act_ids]
        shift_di = [logit["D"][i] - logit["I"][i] for i in act_ids]
        shift_hih = [logit["HI"][i] - logit["IH"][i] for i in act_ids]
        mean = lambda xs: (sum(xs) / len(xs)) if xs else None  # noqa: E731
        inter_ci = P.cluster_bootstrap(inter, [dcl[i] for i in act_ids]) if act_ids else None
        ih = {"n": len(act_ids), "interaction": mean(inter), "ci95": inter_ci, "shift_D_minus_I": mean(shift_di),
              "shift_HI_minus_IH": mean(shift_hih),
              "frame_share": (mean(shift_hih) / mean(shift_di)) if act_ids and mean(shift_di) else None}
        av = refusal.get("ablated_auroc_D_vs_HI")
        conds = {"gate_pass": gate_pass,
                 "gap_at_least_15": g["gap"] is not None and g["gap"] >= P.RULE_POINTS - 1e-12,
                 "interval_above_zero": bool(g["ci95"]) and g["ci95"][0] > 0,
                 "spread_at_least_030": spread is not None and spread >= P.R2_SPREAD - 1e-12,
                 "loco_all_above_zero": loco_ok,
                 "refusal_control_valid": av is not None and av >= P.GATE_AUROC,
                 "refusal_does_not_explain": refusal.get("explains") is False,
                 "ih_interaction_above_zero": bool(inter_ci) and inter_ci[0] > 0}
        prim = {"role": "primary" if task == PRIMARY_TASK else "secondary", "status": "read", "n": len(act_ids),
                "n_clusters": len({dcl[i] for i in act_ids}), "gap": g["gap"], "ci95": g["ci95"],
                "ci95_by_i_clause": P.cluster_bootstrap([lab["D"][i] - lab["I"][i] for i in act_ids],
                                                        [icl[i] for i in act_ids]) if act_ids else None,
                "n_i_clauses": len({icl[i] for i in act_ids}), "rates": rates_act, "spread_D_minus_HI": spread,
                "p_I": p_i, "loco": loco, "loco_min": min((v for v in loco.values() if v is not None), default=None),
                "refusal": refusal, "ih_interaction": ih, "conditions": conds,
                "frame_split": {f: dict(_gap_block(lab, [i for i in act_ids if tmeta[i]["frame"] == f], dcl),
                                        role="descriptive") for f in FRAMES}}
    res["primary"] = prim
    res["label"] = task_label(task, gate_pass, prim.get("conditions", {}))

    # ---- joint DT and HT statistic (all test ids) ----
    spread_all = (rates_all["D"] - rates_all["HI"]) if test_ids else None
    defined = bool(gate_pass and spread_all is not None and spread_all >= P.R2_SPREAD - 1e-12)
    pos = {c: ((rates_all[c] - rates_all["HI"]) / spread_all) if spread_all else None for c in ("I", "H", "DT", "HT")}
    joint = {"role": "primary", "defined": defined, "spread_D_minus_HI": spread_all, "rates": rates_all,
             "p": pos, "statistic": (pos["DT"] - pos["HT"]) if defined else None,
             "ci95": ratio_bootstrap(lab, test_ids, dcl)["ci95"] if defined else None,
             "cell": joint_cell(pos["DT"], pos["HT"]) if defined else "undefined"}
    res["joint"] = joint

    # ---- descriptive readings ----
    by_form = {f: _gap_block(lab, [i for i in test_ids if tmeta[i]["d_form"] == f], dcl) for f in FORMS}
    d2clf = P.classifier_arm(list(d2_un))
    score_h = d2clf.pop("_score_fn")
    frozen = {}
    for c, src, ids in (("D", U, test_ids), ("I", U, test_ids), ("H", U, test_ids), ("HI", FU, test_ids),
                        ("DT", FU, test_ids), ("HT", FU, test_ids), ("IH", FU, ih_ids)):
        s = score_h([src[("test", c)][i] for i in ids])
        frozen[c] = float((s >= 0.5).mean()) if len(ids) else None
    desc = {"role": "descriptive", "gap_all_ids": _gap_block(lab, test_ids, dcl), "gap_by_form": by_form,
            "rate_H_under_C_HI": rates_all["H"], "gate_auroc_act_form_validation": gate_act_auroc,
            "n_gate_act_form": len(gate_act), "rates_under_frozen_C_H": frozen}
    bl = set(borderline_pids)
    if task in ("sdr_v2", "ser_v2") and bl:
        keep = lambda role, ids: [i for i in ids if meta[(role, i)]["pressure_id"] not in bl]  # noqa: E731
        sfit, sgate, stest = keep("fit", fit_ids), keep("gate", gate_ids), keep("test", test_ids)
        if sfit:
            sclf = fit_clf([U[("fit", "D")][i] for i in sfit], [FU[("fit", "HI")][i] for i in sfit])
            sg = {c: scores(src, "gate", c, sgate, sclf)[0] for c, src in (("D", U), ("HI", FU))}
            st = {c: scores(src, "test", c, stest, sclf)[0] for c, src in (("D", U), ("I", U), ("HI", FU))}
            slab = {c: {i: int(v >= 0.5) for i, v in st[c].items()} for c in st}
            desc["sensitivity_without_borderline"] = {
                "excluded_pressure_ids": sorted(bl & {meta[(r, i)]["pressure_id"] for (r, i) in meta}),
                "n_fit": len(sfit), "n_gate": len(sgate), "n_test": len(stest),
                "gate_auroc": P.auroc([sg["D"][i] for i in sgate], [sg["HI"][i] for i in sgate]) if sgate else None,
                "gap_all_ids": _gap_block(slab, stest, dcl),
                "gap_by_form": {f: _gap_block(slab, [i for i in stest if tmeta[i]["d_form"] == f], dcl)
                                for f in FORMS}}
    res["descriptive"] = desc
    res["n_test_ids"] = len(test_ids)
    json.dumps(res, allow_nan=False)
    return res


def _fmt(x, nd=3):
    if x is None:
        return "n/a"
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(_fmt(v, nd) for v in x) + "]"
    if isinstance(x, bool):
        return "yes" if x else "no"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def readings_md(out: Dict) -> str:
    lines = ["# D2 follow-up readings", "", f"Generated {out['created']} by scripts/d2_followup.py read "
             f"(pre-registered sample: {_fmt(out['pre_registered'])}).", "", STANDING, "",
             f"Drift anchor: maximum absolute feature difference {_fmt(out['drift_anchor']['max_abs_diff'], 4)} "
             f"against the bar {DRIFT_TOL} logits.", "",
             f"Direction label: ({out['direction']['label']}). {out['direction']['note']}.", "",
             "## Act-form reading under C_HI", "",
             "| task | role | gate AUROC | label | n | clusters | rate D | rate I | rate HI | gap | interval | "
             "spread | p_I | LOCO min | ablated gap | ablated AUROC | IH interaction | interval |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t, r in out["tasks"].items():
        pr = r["primary"]
        if pr.get("status") != "read":
            lines.append(f"| {t} | {pr['role']} | {_fmt(r['classifier']['gate_auroc'])} | ({r['label']}) | {pr['n']} "
                         "| | | | | | | | | | | | | |")
            continue
        rf, ih = pr["refusal"], pr["ih_interaction"]
        lines.append(f"| {t} | {pr['role']} | {_fmt(r['classifier']['gate_auroc'])} | ({r['label']}) | {pr['n']} | "
                     f"{pr['n_clusters']} | {_fmt(pr['rates']['D'])} | {_fmt(pr['rates']['I'])} | "
                     f"{_fmt(pr['rates']['HI'])} | {_fmt(pr['gap'])} | {_fmt(pr['ci95'])} | "
                     f"{_fmt(pr['spread_D_minus_HI'])} | {_fmt(pr['p_I'])} | {_fmt(pr['loco_min'])} | "
                     f"{_fmt(rf.get('gap'))} | {_fmt(rf.get('ablated_auroc_D_vs_HI'))} | {_fmt(ih['interaction'])} | "
                     f"{_fmt(ih['ci95'])} |")
    lines += ["", "## Joint DT and HT reading (all test ids)", "",
              "| task | spread | p_I | p_H | p_DT | p_HT | p_DT minus p_HT | interval | cell |",
              "|---|---|---|---|---|---|---|---|---|"]
    for t, r in out["tasks"].items():
        j = r["joint"]
        lines.append(f"| {t} | {_fmt(j['spread_D_minus_HI'])} | {_fmt(j['p']['I'])} | {_fmt(j['p']['H'])} | "
                     f"{_fmt(j['p']['DT'])} | {_fmt(j['p']['HT'])} | {_fmt(j['statistic'])} | {_fmt(j['ci95'])} | "
                     f"{j['cell']} |")
    lines += ["", "## Descriptive", "", "| task | gap all ids | interval | act | predicate | other | rate H "
              "under C_HI | frozen C_H rates HI, DT, HT, IH |", "|---|---|---|---|---|---|---|---|"]
    for t, r in out["tasks"].items():
        d = r["descriptive"]
        fz = d["rates_under_frozen_C_H"]
        lines.append(f"| {t} | {_fmt(d['gap_all_ids']['gap'])} | {_fmt(d['gap_all_ids']['ci95'])} | "
                     f"{_fmt(d['gap_by_form']['act']['gap'])} | {_fmt(d['gap_by_form']['predicate']['gap'])} | "
                     f"{_fmt(d['gap_by_form']['other']['gap'])} | {_fmt(d['rate_H_under_C_HI'])} | "
                     f"{_fmt([fz['HI'], fz['DT'], fz['HT'], fz['IH']])} |")
    return "\n".join(lines) + "\n"


def verify_d2_files(d2_root: str, tasks: Sequence[str]) -> Dict:
    out = {}
    for t in tasks:
        for p in P.PASSES:
            path = os.path.join(P.task_dir(d2_root, t), f"features_{p}.jsonl")
            man = os.path.join(P.task_dir(d2_root, t), f"features_{p}.manifest.json")
            if not os.path.exists(path) or not os.path.exists(man):
                raise SystemExit(f"D2 file or manifest missing: {path}")
            want = json.load(open(man, encoding="utf-8"))["sha256"]
            got = P.sha256_file(path)
            if got != want:
                raise SystemExit(f"D2 file {path} sha256 {got} differs from its manifest's {want}")
            out[f"{t}/features_{p}.jsonl"] = got
    return out


def run_read(args) -> int:
    d2_hashes = verify_d2_files(args.d2_root, args.tasks)
    per = {}
    for t in args.tasks:
        d2u = P.read_jsonl(os.path.join(P.task_dir(args.d2_root, t), "features_unablated.jsonl"))
        per[t] = anchor_drift(P.read_jsonl(os.path.join(P.task_dir(args.out_root, t), "features_anchor.jsonl")), d2u)
    drift = summarise_drift(per)
    P.write_json(os.path.join(args.out_root, "drift_anchor.json"), drift)
    if drift["exceeds"]:
        raise SystemExit(f"drift anchor: maximum absolute difference {drift['max_abs_diff']} exceeds {DRIFT_TOL} "
                         "logits (or rows are missing); the read stops for a ruling (R15)")
    pool = load_pool(args.clauses)
    bl = borderline_pids(pool)
    tasks = {}
    for t in args.tasks:
        td, fd = P.task_dir(args.d2_root, t), P.task_dir(args.out_root, t)
        tasks[t] = read_task(t, P.read_jsonl(os.path.join(td, "features_unablated.jsonl")),
                             P.read_jsonl(os.path.join(td, "features_ablated.jsonl")),
                             P.read_jsonl(os.path.join(fd, "features_unablated.jsonl")),
                             P.read_jsonl(os.path.join(fd, "features_ablated.jsonl")), bl)
    out = {"created": datetime.now().isoformat(timespec="seconds"), "pre_registered": _pre_registered(args),
           "tasks": tasks, "labels": {t: r["label"] for t, r in tasks.items()},
           "direction": direction_label({t: r["label"] for t, r in tasks.items()}),
           "drift_anchor": drift, "d2_feature_sha256": d2_hashes,
           "clauses_sha256": P.sha256_file(args.clauses), "code_sha256": code_hashes(),
           "constants": {"gate_auroc": P.GATE_AUROC, "rule_points": P.RULE_POINTS, "explain_share": P.EXPLAIN_SHARE,
                         "r2_spread": P.R2_SPREAD, "r2_low": P.R2_LOW, "r2_high": P.R2_HIGH, "n_boot": P.N_BOOT,
                         "boot_seed": P.BOOT_SEED, "c": P.C_REG, "drift_tol": DRIFT_TOL}}
    P.write_json(os.path.join(args.out_root, "readings.json"), out)
    with open(os.path.join(args.out_root, "readings.md"), "w", encoding="utf-8") as f:
        f.write(readings_md(out))
    print(json.dumps({"labels": out["labels"], "direction": out["direction"]["label"],
                      "drift": drift["max_abs_diff"]}, indent=1), flush=True)
    return 0


# ==============================================================================
# CLI
# ==============================================================================

STAGES = ("build", "features", "read")


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    p.add_argument("stages", nargs="+", choices=STAGES)
    p.add_argument("--tasks", nargs="+", default=list(TASKS), choices=TASKS)
    p.add_argument("--out-root", default=DEFAULT_OUT)
    p.add_argument("--d2-root", default=D2_OUT, help="D2's output directory (stored features and direction).")
    p.add_argument("--data-dir", default=P.DEFAULT_DATA_DIR)
    p.add_argument("--inputs", default=P.INPUTS_PATH)
    p.add_argument("--clauses", default=CLAUSES_PATH)
    p.add_argument("--model", default=P.DEFAULT_MODEL)
    p.add_argument("--max-test-ids", type=int, default=P.TEST_CAP)
    p.add_argument("--max-fit-ids", type=int, default=0, help="Smoke runs only; 0 (pre-registered) uses all 200.")
    p.add_argument("--report", default=None, help="build: where to write the report (default <out-root>).")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--allow-stack-mismatch", action="store_true",
                   help="Not pre-registered: run on a stack other than job 50155519's (recorded in the manifests).")
    return p


def main(argv=None, tokenizer=None, model_loader=None, fits=None) -> int:
    args = build_parser().parse_args(argv)
    stages = list(dict.fromkeys(args.stages))
    if "features" in stages and args.dry_run:
        raise SystemExit("features has no dry run; use `build --dry-run`")
    rc = 0
    if "build" in stages:
        rc = run_build(args, tokenizer if tokenizer is not None else P._load_tokenizer(args), fits)
        if rc:
            return rc
    if "features" in stages:
        run_features(args, tokenizer if tokenizer is not None else P._load_tokenizer(args), model_loader, fits)
    if "read" in stages:
        rc = run_read(args)
    return rc


if __name__ == "__main__":
    sys.exit(main())
