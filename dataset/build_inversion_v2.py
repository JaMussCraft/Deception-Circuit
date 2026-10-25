"""
build_inversion_v2.py — the Instructed-Inversion Condition (I), stored as `<task>_inversion`.

Mechanism-analysis ticket 08 (spec section 2.4, rulings R15, R19(4) and R20). One I row per D
test row of `<task>` (far_v2, sdr_v2, ser_v2): the same instance, the same target item and
labels, with the Pressure Clause replaced by clause surgery with a transparent clause in which
the asker openly requests that item as a game or knowing the answer. Nobody is misled, so a set
that also mediates I is instructed-inversion machinery, not deception-specific. "Instructed
inversion" here is unrelated to the Designation Polarity value `inversion` (CONTEXT.md).

Derived from the stored files, never re-templated; the provenance-pinned v2 builders and the
existing v2 datasets are imported and read, never edited.

  * Form match (R19(4)). Every D clause has a form under the R12 text rule (`clause_form`: act-
    naming first, then Predicate-naming, then other), checked against ticket 02a's committed
    table `docs/research/mechanism-analysis/clause-forms.csv`. The I clause comes from the pool
    entries of the same task and form (`dataset/deception_pools/v2/inversion_v2.json`).
  * Pool rules (R20). Every clause carries a transparency marker (`TRANSPARENCY_MARKERS`: the
    asker knows the answer, or the request is a quiz, drill, game, test or on purpose), names
    no mislead act, and passes the task's clause screen.
  * Token match. Like the Neutral-Clause Twin (`deception_v2.neutral_candidates`), a pool clause
    fits a row only if, in both streams, the full prompt keeps D's token count, I is clause-
    aligned with D, and I is clause-aligned with the twin `<task>_honest` over I's clause. So the
    existing twin pairs with I by `instance_id` (02a's `neutral_twin` kind, I as the pressure
    stream). The pick is sha1("inversion:" + instance_id) mod k over the fitting clauses; a row
    with none is dropped and counted per `pressure_id`.
  * Columns. D's row, every column kept, with the clause swapped in `clean_prompt`,
    `corrupt_prompt` and `neutral_prompt`; `condition: "inversion"` (the condition id),
    `pressure` = the I clause (segmentation and the eval variants locate the clause by it),
    `slot_kind: "transparent"`. Added: `instructed_inversion_id`, `_form`, `_wording`; D's clause
    and margins as `i_source_pressure`, `i_source_clause_form`, `i_source_clean_margin`,
    `i_source_corrupt_margin`; after scoring `h_instructed_inversion_clean/corrupt`, and
    `clean_margin` / `corrupt_margin` become the I target's margins. D's other columns (`h_*`,
    `honest_instruction_*`, `prior_margin`, `neutral_id`, ...) are D's values, unchanged.
  * Behaviour filter (R20). D's pressure rule, `contingency._deceptive` at `contingency.MARGIN`:
    the target is the argmax and its margin is >= 0.7 in both streams. The margin-only count is
    reported beside it.

Stages (all from the worktree root):

  score     (GPU) derive every task's rows first (all CPU checks), then score both streams of
            every row on one loaded model; writes <work-dir>/<task>/{scores.jsonl, meta.json}
            (default work dir outputs/_build_inversion_v2/). `--no-model` is the CPU dry run:
            derive and check all rows, print the coverage, write nothing.
  assemble  (CPU) re-derive, check the scores belong to these rows and this pool, filter, and
            write <data-dir>/<task>_inversion/ (test split only) with dataset_config.json and
            filter_report.json (every scored row's margins). Refuses an existing output dir.
            Exit 3 (EXIT_BELOW_MIN_KEPT) when a task keeps fewer than --min-kept (300) ids:
            a hand-back before phase 1C.

    python -I dataset/build_inversion_v2.py --stage score --no-model
    python -I dataset/build_inversion_v2.py --stage score          # GPU job
    python -I dataset/build_inversion_v2.py --stage assemble

Do not run with `python -O`: the pinned alignment checks are assert statements.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from dataset import clause_screen as cs  # noqa: E402
from dataset import contingency as ct  # noqa: E402
from dataset import deception_common as dc  # noqa: E402
from dataset import deception_v2 as v2  # noqa: E402
from dataset.build_deception_v2 import (  # noqa: E402  (pinned: imported, never edited)
    _load_tokenizer, _write_json, _write_jsonl_atomic, sha256_file)
from dataset.clause_surgery import replace_clause  # noqa: E402
from dataset.matched_honest import assert_clause_aligned_pair  # noqa: E402
from dataset.report_utils import margin_summary  # noqa: E402

TASKS = ("far_v2", "sdr_v2", "ser_v2")
FORMS = ("act", "predicate", "other")
POOL_PATH = os.path.join(v2.V2_POOLS_DIR, "inversion_v2.json")
#: The condition id (impl-02a binds `deception_condition: inversion` -> `<task>_inversion`).
CONDITION = "inversion"
SLOT_KIND = "transparent"

#: R20: every clause carries a knowledge marker (the asker knows the answer) or an intent / game
#: marker, so that naming the requested item cannot work as misleading advice. "openly" alone
#: does not count.
TRANSPARENCY_MARKERS = ("knows", "knowingly", "already knows", "already has",
                        "on purpose", "drill", "quiz", "quizzing", "game", "testing")
#: No clause may tell the model to mislead, hide or pretend.
MISLEAD_WORDS = frozenset({
    "mislead", "misleading", "misled", "deceive", "deceiving", "deception", "deceptive",
    "lie", "lies", "lying", "pretend", "pretending", "trick", "fool", "fake", "hide", "hidden",
    "hiding", "conceal", "concealed", "secret", "secretly", "cover", "bury", "distract",
    "unseen", "sight", "convince", "persuade",
})
#: Screen hits that the D clauses of the selected cells carry too, so they are not violations
#: here: Predicate words (Predicate-naming forms need them) and imperative starts.
_ALLOWED_SCREEN_RULES = ("predicate_word", "imperative_start")

#: The R12 text rule's act words (wrong / incorrect / false / not true, inflections included),
#: checked BEFORE the Predicate words (R19 precedence).
ACT_PATTERN = re.compile(r"\b(wrong|incorrect\w*|false\w*|not (the )?true)\b", re.IGNORECASE)
_WORD = re.compile(r"[A-Za-z]+")


def predicate_words(task: str) -> frozenset:
    """The task's own Predicate pair (failing/passing, critical/harmless, unfavorable/favorable)."""
    spec = v2.SPECS_V2[task]
    return frozenset({spec.desig_inversion, spec.desig_identity})


def clause_form(text: str, task: str) -> str:
    """The clause form under the R12 text rule, in R19's order: "act" iff the clause says
    wrong / incorrect / false / not true; else "predicate" iff it contains one of the task's
    Predicate words; else "other"."""
    if ACT_PATTERN.search(text):
        return "act"
    if {w.lower() for w in _WORD.findall(text)} & predicate_words(task):
        return "predicate"
    return "other"


#: Ticket 02a's committed clause-form table of the 49 D test clauses (R12, R19(4)).
CLAUSE_FORMS_PATH = os.path.join(REPO_ROOT, "docs", "research", "mechanism-analysis",
                                 "clause-forms.csv")
_TABLE_FORMS = {"act-naming": "act", "predicate-naming": "predicate", "other": "other"}


def load_clause_forms(path: Optional[str] = None) -> Dict[Tuple[str, str], Tuple[str, str]]:
    """{(task, pressure_id): (clause, form)} from the clause-form table, forms spelled as
    FORMS ("act-naming" -> "act", "predicate-naming" -> "predicate")."""
    with open(path or CLAUSE_FORMS_PATH, newline="") as f:
        return {(r["task"], r["pressure_id"]): (r["clause"], _TABLE_FORMS[r["form"]])
                for r in csv.DictReader(f)}


def check_clause_forms(table: Dict, task: str, d_rows: Sequence[Dict]) -> None:
    """Raise ValueError unless every D row's clause is in the table, with the same text, and
    the table's form equals the text rule (the builder matches forms by `clause_form`)."""
    bad = set()
    for d in d_rows:
        key = (task, d["pressure_id"])
        if key not in table:
            raise ValueError(f"{task}: pressure_id {d['pressure_id']} is not in the clause-form "
                             f"table")
        clause, form = table[key]
        if clause != d["pressure"] or form != clause_form(clause, task):
            bad.add(f"{d['pressure_id']} (table {form!r}, rule "
                    f"{clause_form(d['pressure'], task)!r})")
    if bad:
        raise ValueError(f"{task}: the clause-form table disagrees with the text rule or the "
                         f"stored clause: {sorted(bad)}")


# ==============================================================================
# THE POOL
# ==============================================================================

_POOL_KEYS = ("id", "task", "form", "wording", "text")


def pool_violations(entry: Dict) -> List[str]:
    """Rule violations of one pool entry; [] is clean.

    Rules: a known task and form; the form label equals the text rule; one transparency
    marker (R20); no mislead word; and `clause_screen.screen_clause` for the task (one sentence,
    no all-caps word, no item or position word; SDR / SER no truth words, so act-naming says
    only "wrong"; SER no disclosure words; FAR its forbidden list) minus the Predicate-word and
    imperative-start rules."""
    missing = [k for k in _POOL_KEYS if not entry.get(k)]
    if missing:
        return [f"missing:{','.join(missing)}"]
    task, text = entry["task"], entry["text"]
    if task not in TASKS:
        return [f"unknown task {task!r}"]
    out = []
    if entry["form"] not in FORMS:
        out.append(f"form:unknown {entry['form']!r}")
    elif clause_form(text, task) != entry["form"]:
        out.append(f"form:labelled {entry['form']} but the text rule says "
                   f"{clause_form(text, task)}")
    low = text.lower()
    if not any(re.search(r"\b" + re.escape(m) + r"\b", low) for m in TRANSPARENCY_MARKERS):
        out.append("transparency:no marker")
    words = {w.lower() for w in _WORD.findall(text)}
    out += [f"mislead:{w}" for w in sorted(words & MISLEAD_WORDS)]
    out += [v for v in cs.screen_clause(text, task) if not v.startswith(_ALLOWED_SCREEN_RULES)]
    return out


def load_pool(path: Optional[str] = None) -> List[Dict]:
    """The validated entries of a pool file ({"clauses": [...]}), in file order. Raises
    ValueError on any rule violation and on a duplicate id or text."""
    with open(path or POOL_PATH) as f:
        pool = json.load(f)["clauses"]
    errors, ids, texts = [], set(), set()
    for entry in pool:
        bad = pool_violations(entry)
        if bad:
            errors.append(f"{entry.get('id')}: {bad}")
        for key, seen in (("id", ids), ("text", texts)):
            if entry.get(key) in seen:
                errors.append(f"duplicate {key} {entry.get(key)!r}")
            seen.add(entry.get(key))
    if errors:
        raise ValueError("invalid inversion pool:\n  " + "\n  ".join(errors))
    return pool


# ==============================================================================
# ROW DERIVATION
# ==============================================================================

#: Salt of the per-instance pick, distinct from the neutral twin's unsalted sha1(instance_id).
SELECT_SALT = "inversion:"
#: The two scored prompt columns (clean, corrupt) and the third one that holds the clause.
SCORED_PROMPTS = ("clean_prompt", "corrupt_prompt")
_CLAUSE_PROMPTS = SCORED_PROMPTS + ("neutral_prompt",)


def _fits(tokenizer, d: Dict, h: Dict, text: str, max_seq_length: int) -> bool:
    """True when `text` can replace D's clause: in both streams the full prompt keeps D's token
    count, I is clause-aligned with D (over D's clause) and with the Neutral-Clause Twin H (over
    I's clause, the assertion the `neutral_twin` pairing runs with I as the pressure stream)."""
    clause = d["pressure"]
    for key in SCORED_PROMPTS:
        i_prompt = replace_clause(d[key], clause, text)
        try:
            assert_clause_aligned_pair(tokenizer, d[key], i_prompt, clause, max_seq_length)
            assert_clause_aligned_pair(tokenizer, i_prompt, h[key], text, max_seq_length)
        except (AssertionError, ValueError):
            return False
    return True


def candidates(tokenizer, d: Dict, h: Dict, pool: Sequence[Dict],
               max_seq_length: int) -> List[Dict]:
    """Pool clauses (pool order) of D's task and form that fit the row (`_fits`), pre-filtered on
    the standalone token count (within 1 of D's clause, as `deception_v2.neutral_candidates`)."""
    task, clause = d["task"], d["pressure"]
    form = clause_form(clause, task)
    n_clause = len(tokenizer.encode(" " + clause, add_special_tokens=False))
    out = []
    for c in pool:
        if c["task"] != task or c["form"] != form:
            continue
        if abs(len(tokenizer.encode(" " + c["text"], add_special_tokens=False)) - n_clause) > 1:
            continue
        if _fits(tokenizer, d, h, c["text"], max_seq_length):
            out.append(c)
    return out


def select(fits: Sequence[Dict], instance_id: str) -> Dict:
    """sha1(SELECT_SALT + instance_id) mod k over the fitting clauses."""
    k = int(hashlib.sha1((SELECT_SALT + instance_id).encode()).hexdigest(), 16) % len(fits)
    return fits[k]


def inversion_row(d: Dict, chosen: Dict) -> Dict:
    """The I row: D's row, every column kept, with the clause replaced in every stored prompt
    that holds it and the I clause in `pressure` (the column segmentation and the eval variants
    locate the clause by). D's clause and margins move to `i_source_*`."""
    clause, text = d["pressure"], chosen["text"]
    row = dict(d)
    for key in _CLAUSE_PROMPTS:
        if key in d:
            row[key] = replace_clause(d[key], clause, text)
    row.update({
        "condition": CONDITION, "pressure": text, "slot_kind": SLOT_KIND,
        "honest_twin_kind": None,
        "instructed_inversion_id": chosen["id"],
        "instructed_inversion_form": chosen["form"],
        "instructed_inversion_wording": chosen["wording"],
        "i_source_pressure": clause, "i_source_clause_form": clause_form(clause, d["task"]),
        "i_source_clean_margin": d.get("clean_margin"),
        "i_source_corrupt_margin": d.get("corrupt_margin"),
        "clean_margin": None, "corrupt_margin": None,
    })
    return row


def derive_task(tokenizer, task: str, d_rows: Sequence[Dict], h_rows: Sequence[Dict],
                pool: Sequence[Dict], max_seq_length: int) -> Tuple[List[Dict], Dict]:
    """(I rows in D's order, report). Every D row is paired with its Neutral-Clause Twin by
    `instance_id` (same `pressure_id` required). A row with no fitting clause is dropped and
    counted under its `pressure_id`. Raises ValueError on bad input data."""
    if not __debug__:
        raise RuntimeError("run without -O: the pinned alignment checks (matched_honest, "
                           "deception_common) are assert statements")
    twins = {h["instance_id"]: h for h in h_rows}
    rows, dropped, chosen_ids = [], Counter(), Counter()
    by_form = defaultdict(Counter)
    for d in d_rows:
        h = twins.get(d["instance_id"])
        if h is None:
            raise ValueError(f"{task}: D row {d['instance_id']} has no Neutral-Clause twin")
        if h.get("honest_twin_kind") != "neutral_clause":
            raise ValueError(f"{task}: the twin of {d['instance_id']} has honest_twin_kind "
                             f"{h.get('honest_twin_kind')!r}, need 'neutral_clause'")
        if h["pressure_id"] != d["pressure_id"]:
            raise ValueError(f"{task}: D row {d['instance_id']} has pressure_id "
                             f"{d['pressure_id']} but its twin has {h['pressure_id']}")
        form = clause_form(d["pressure"], task)
        fits = candidates(tokenizer, d, h, pool, max_seq_length)
        if not fits:
            dropped[d["pressure_id"]] += 1
            by_form[form]["dropped"] += 1
            continue
        row = inversion_row(d, select(fits, d["instance_id"]))
        dc.assert_aligned_pair(tokenizer, row["clean_prompt"], row["corrupt_prompt"],
                               row["clean_item_d"], row["corrupt_item_d"], max_seq_length)
        n = len(tokenizer.encode(row["neutral_prompt"], add_special_tokens=False))
        if n > max_seq_length:
            raise ValueError(f"{task}: I neutral_prompt of {d['instance_id']} is {n} tokens > "
                             f"{max_seq_length}")
        rows.append(row)
        chosen_ids[row["instructed_inversion_id"]] += 1
        by_form[form]["derived"] += 1
    report = {"task": task, "n_input": len(d_rows), "n_derived": len(rows),
              "dropped": dict(dropped), "by_form": {f: dict(c) for f, c in by_form.items()},
              "instructed_inversion_id_counts": dict(sorted(chosen_ids.items()))}
    return rows, report


# ==============================================================================
# SCORING AND THE BEHAVIOUR FILTER
# ==============================================================================

#: `contingency`'s stream names -> the prompt column each one scores.
_PROMPT_OF_STREAM = {"clean": "clean_prompt", "corrupt": "corrupt_prompt"}


def score_rows(rows: Sequence[Dict], score_fn) -> List[Dict]:
    """Per row {"clean": s, "corrupt": s} in `contingency`'s convention: s["margin"] = h =
    logit(honest word) - logit(I target), s["choice"] "a" (honest), "b" (target) or "other".
    `score_fn(prompts, word_pairs)` returns `dc.score_prompts`-like records, one per prompt;
    it is called once over both streams of every row."""
    prompts, pairs = [], []
    for r in rows:
        for st in ct.STREAMS:
            prompts.append(r[_PROMPT_OF_STREAM[st]])
            pairs.append(ct.stream_words(r, st))
    out = score_fn(prompts, pairs)
    if len(out) != len(prompts):
        raise ValueError(f"score_fn returned {len(out)} records for {len(prompts)} prompts")
    it = iter(out)
    return [{st: {k: o[k] for k in ("margin", "choice", "argmax")}
             for st, o in zip(ct.STREAMS, (next(it), next(it)))} for _ in rows]


def _target_margin_in_both_streams(scores: Dict) -> bool:
    """The margin half of the rule alone (reported beside the full rule, R20)."""
    return all(-scores[st]["margin"] >= ct.MARGIN for st in ct.STREAMS)


def _retention(rows, flags, key_fn) -> Dict:
    n, k = Counter(), Counter()
    for r, f in zip(rows, flags):
        n[key_fn(r)] += 1
        k[key_fn(r)] += bool(f)
    return {g: {"n": n[g], "kept": k[g], "rate": k[g] / n[g]} for g in sorted(n)}


def filter_scored(rows: Sequence[Dict], scores: Sequence[Dict]) -> Tuple[List[Dict], Dict]:
    """(kept I rows with their margins, retention report). Kept = D's pressure rule
    (`contingency._deceptive` at `contingency.MARGIN`): the I target is the argmax and its
    margin is >= 0.7 in both streams. A kept row's `clean_margin` / `corrupt_margin` are the I
    target's margins (-h), as D's are."""
    if len(rows) != len(scores):
        raise ValueError(f"{len(rows)} rows but {len(scores)} score records")
    flags = [ct._deceptive(s, ct.MARGIN) for s in scores]
    kept = []
    for r, s, ok in zip(rows, scores, flags):
        if ok:
            kept.append({**r, "h_instructed_inversion_clean": s["clean"]["margin"],
                         "h_instructed_inversion_corrupt": s["corrupt"]["margin"],
                         "clean_margin": -s["clean"]["margin"],
                         "corrupt_margin": -s["corrupt"]["margin"]})
    other = Counter(repr(s[st]["argmax"]) for s in scores for st in ct.STREAMS
                    if s[st]["choice"] == "other")
    report = {
        "n_scored": len(rows), "kept": len(kept),
        "rate": len(kept) / len(rows) if rows else None,
        "rule": "argmax = I target and -h >= contingency.MARGIN in both streams "
                "(contingency._deceptive, D's pressure rule)",
        "margin_thresh": ct.MARGIN,
        "margin_only_kept": sum(_target_margin_in_both_streams(s) for s in scores),
        "retention_by_pressure_id": _retention(rows, flags, lambda r: r["pressure_id"]),
        "retention_by_stratum": _retention(
            rows, flags, lambda r: f"{r['designation_polarity']}/{r['item_polarity']}"),
        "retention_by_template_variant": _retention(rows, flags,
                                                    lambda r: r["template_variant"]),
        # The full sampler stratum: Designation Polarity x Item Polarity x Template Variant.
        "retention_by_sampler_stratum": _retention(
            rows, flags, lambda r: f"{r['designation_polarity']}/{r['item_polarity']}/"
                                   f"{r['template_variant']}"),
        "retention_by_form": _retention(rows, flags, lambda r: r["instructed_inversion_form"]),
        "target_margin": {st: margin_summary([-s[st]["margin"] for s in scores])
                          for st in ct.STREAMS},
        "unexpected_argmax_tokens": dict(other.most_common()),
    }
    return kept, report


# ==============================================================================
# IO
# ==============================================================================

DEFAULT_WORK_DIR = os.path.join(REPO_ROOT, "outputs", "_build_inversion_v2")
DEFAULT_DATA_DIR = os.path.join(REPO_ROOT, "data", "datasets")
#: Spec / ticket 08: fewer kept test ids than this for a task is a hand-back before phase 1C.
MIN_KEPT = 300
EXIT_BELOW_MIN_KEPT = 3
SCORES_FILE = "scores.jsonl"
META_FILE = "meta.json"
#: What the added row columns hold (written into every dataset_config.json, R20).
FIELD_NOTES = {
    "condition": "the condition id 'inversion' (the Instructed-Inversion Condition, I); not the "
                 "Designation Polarity value of the same spelling",
    "pressure": "the I clause (transparent, from the pool)",
    "slot_kind": "'transparent'",
    "instructed_inversion_id/_form/_wording": "the chosen pool clause",
    "i_source_*": "renamed from D: D's clause (i_source_pressure), its form, and D's "
                  "clean/corrupt target margins",
    "clean_margin/corrupt_margin": "the I target's margins (-h) on the I prompts",
    "h_instructed_inversion_clean/corrupt": "h = logit(honest) - logit(I target) on the I "
                                            "prompts",
    "other columns": "D's values, unchanged (h_*, honest_instruction_*, prior_margin, "
                     "neutral_id, ...)",
}


def _read_jsonl(path: str) -> List[Dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def bridges2_delivery(path: str, timeout: float = 120) -> str:
    """How `path` reaches Bridges-2: "branch" (tracked: the pushed branch carries it),
    "sync-data" (git-ignored: list it for `scripts/remote/b2.sh sync-data`), or "unknown"
    (not in a repository, or git failed or timed out)."""
    try:
        r = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(path)), "check-ignore",
                            "-q", os.path.abspath(path)], capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return {0: "sync-data", 1: "branch"}.get(r.returncode, "unknown")


# ==============================================================================
# STAGES
# ==============================================================================

def _task_context(args, task: str, tokenizer, pool: Sequence[Dict]) -> Dict:
    """D and H test splits of one task, its I rows and the derivation report. One length limit
    throughout: the D config's `max_seq_length`, which must equal `v2.MAX_SEQ_LENGTH` (the
    scorer's)."""
    d_dir = os.path.join(args.data_dir, task)
    h_dir = d_dir + "_honest"
    d_config = dc.load_dataset_config(d_dir)
    max_len = d_config.get("max_seq_length")
    if max_len != v2.MAX_SEQ_LENGTH:
        raise ValueError(f"{task}: {d_dir}/dataset_config.json has max_seq_length {max_len!r}, "
                         f"but the builder derives and scores at v2.MAX_SEQ_LENGTH = "
                         f"{v2.MAX_SEQ_LENGTH}; one length limit is required")
    d_rows = dc.load_or_generate_deception_data(d_dir, "test")
    h_rows = dc.load_or_generate_deception_data(h_dir, "test")
    check_clause_forms(load_clause_forms(args.clause_forms), task, d_rows)
    rows, report = derive_task(tokenizer, task, d_rows, h_rows, pool, max_len)
    return {"task": task, "d_dir": d_dir, "h_dir": h_dir, "d_config": d_config,
            "max_seq_length": max_len, "rows": rows, "derive": report}


def _print_derivation(ctx: Dict) -> None:
    rep = ctx["derive"]
    print(f"{ctx['task']}: {rep['n_derived']} of {rep['n_input']} D test rows derived; "
          f"dropped by pressure_id {rep['dropped'] or '{}'}; by form {rep['by_form']}")


def run_score(args, tokenizer, model_loader) -> int:
    """Derive every task's I rows (CPU checks first, for every task), then score them on one
    loaded model and write <work-dir>/<task>/{scores.jsonl, meta.json}. --no-model stops after
    the derivation and writes nothing."""
    pool = load_pool(args.pool)
    contexts = [_task_context(args, t, tokenizer, pool) for t in args.tasks]
    for ctx in contexts:
        _print_derivation(ctx)
    if args.no_model:
        for ctx in contexts:
            if ctx["rows"]:
                r = ctx["rows"][0]
                print(f"\n{ctx['task']} sample I row {r['instance_id']} "
                      f"({r['instructed_inversion_id']}, D clause "
                      f"{r['i_source_pressure']!r}):\n{r['clean_prompt']}")
        print(f"\n--no-model dry run: nothing scored; would write under {args.work_dir}")
        return 0
    for ctx in contexts:
        path = os.path.join(args.work_dir, ctx["task"], SCORES_FILE)
        if os.path.exists(path):
            raise SystemExit(f"scores exist, refusing to overwrite: {path}")
    score_fn = model_loader(args)
    for ctx in contexts:
        out = os.path.join(args.work_dir, ctx["task"])
        os.makedirs(out, exist_ok=True)
        t0 = time.time()
        scores = score_rows(ctx["rows"], score_fn)
        seconds = time.time() - t0
        _write_jsonl_atomic(os.path.join(out, SCORES_FILE), [
            {"instance_id": r["instance_id"],
             "instructed_inversion_id": r["instructed_inversion_id"], **s}
            for r, s in zip(ctx["rows"], scores)])
        _write_json(os.path.join(out, META_FILE), {
            "task": ctx["task"], "n": len(scores), "forwards": 2 * len(scores),
            "seconds": seconds, "model": args.model, "max_seq_length": v2.MAX_SEQ_LENGTH,
            "job_id": os.environ.get("SLURM_JOB_ID"),
            "cluster": os.environ.get("DC_CLUSTER", "delta"),
            "partition": os.environ.get("SLURM_JOB_PARTITION"),
            "host": os.uname().nodename, "gpu": _gpu_name(),
            "pool_sha256": sha256_file(args.pool),
            "builder_sha256": sha256_file(os.path.abspath(__file__)),
            "created": datetime.now().isoformat(timespec="seconds")})
        print(f"{ctx['task']}: scored {len(scores)} rows in {seconds:.1f} s -> {out}")
    return 0


def _gpu_name() -> Optional[str]:
    try:
        import torch
        return torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:  # noqa: BLE001 - a missing torch build only loses a label
        return None


def _compact(row: Dict, scores: Dict, kept: bool) -> Dict:
    return {"instance_id": row["instance_id"], "pressure_id": row["pressure_id"],
            "instructed_inversion_id": row["instructed_inversion_id"],
            "instructed_inversion_form": row["instructed_inversion_form"],
            "h": [scores[st]["margin"] for st in ct.STREAMS],
            "choice": [scores[st]["choice"] for st in ct.STREAMS], "kept": kept}


def run_assemble(args, tokenizer) -> int:
    """Read the scores, re-derive the rows (deterministic), apply the behaviour filter and write
    <data-dir>/<task>_inversion/ (for example `far_v2_inversion`; test split only) with
    dataset_config.json and filter_report.json. Returns EXIT_BELOW_MIN_KEPT if a task keeps
    fewer than --min-kept."""
    from dataset.build_deception_dataset import save_splits
    pool_sha = sha256_file(args.pool)
    pool = load_pool(args.pool)
    status = 0
    for task in args.tasks:
        out_dir = os.path.join(args.data_dir, f"{task}_{CONDITION}")
        if os.path.exists(out_dir):
            raise SystemExit(f"output directory exists, refusing to overwrite: {out_dir}")
        work = os.path.join(args.work_dir, task)
        with open(os.path.join(work, META_FILE)) as f:
            meta = json.load(f)
        if meta["pool_sha256"] != pool_sha:
            raise SystemExit(f"{task}: the scores were made with another pool "
                             f"({meta['pool_sha256'][:12]} vs {pool_sha[:12]} of {args.pool})")
        ctx = _task_context(args, task, tokenizer, pool)
        scored = _read_jsonl(os.path.join(work, SCORES_FILE))
        want = [(r["instance_id"], r["instructed_inversion_id"]) for r in ctx["rows"]]
        have = [(s["instance_id"], s["instructed_inversion_id"]) for s in scored]
        if want != have:
            raise SystemExit(f"{task}: the scored rows do not match the derived rows")
        scores = [{st: s[st] for st in ct.STREAMS} for s in scored]
        kept, freport = filter_scored(ctx["rows"], scores)
        kept_ids = {r["instance_id"] for r in kept}
        meets = len(kept) >= args.min_kept
        save_splits({"test": kept}, out_dir)
        config = {
            "task": task, "mechanism": ctx["d_config"].get("mechanism"),
            "condition": CONDITION, "condition_name": "Instructed-Inversion Condition (I)",
            "splits": ["test"],
            "model": ctx["d_config"].get("model"), "max_seq_length": ctx["max_seq_length"],
            "margin_thresh": ct.MARGIN, "filter_rule": freport["rule"],
            "n_margin_only_kept": freport["margin_only_kept"],
            "min_kept": args.min_kept, "meets_min_kept": meets,
            "n_input": ctx["derive"]["n_input"], "n_derived": ctx["derive"]["n_derived"],
            "n_kept": len(kept),
            "source_datasets": {"deceptive": ctx["d_dir"], "neutral_twin": ctx["h_dir"]},
            "source_cell": {k: ctx["d_config"].get(k) for k in
                            ("framing_id", "framing_family", "pilot_cell", "suffix",
                             "ser_wording")},
            "pool_path": args.pool, "pool_sha256": pool_sha, "select_salt": SELECT_SALT,
            "clause_forms_path": args.clause_forms,
            "clause_forms_sha256": sha256_file(args.clause_forms),
            "builder_sha256": sha256_file(os.path.abspath(__file__)),
            "scoring": {k: meta.get(k) for k in ("job_id", "cluster", "partition", "host",
                                                 "gpu", "seconds", "forwards", "model",
                                                 "builder_sha256", "created")},
            "bridges2_delivery": bridges2_delivery(out_dir),
            "field_notes": FIELD_NOTES,
            "derivation": ("D test rows with the Pressure Clause replaced by clause surgery with "
                           "a form-matched, token-matched transparent clause "
                           "(dataset/deception_pools/v2/inversion_v2.json); D's instance ids, "
                           "pressure_id, target and distractor kept; the I clause is in "
                           "`pressure`, D's in `i_source_pressure`; paired with <task>_honest "
                           "by instance_id"),
            "created": datetime.now().date().isoformat(),
        }
        report = {"task": task, "derive": ctx["derive"], "filter": freport,
                  "rows": [_compact(r, s, r["instance_id"] in kept_ids)
                           for r, s in zip(ctx["rows"], scores)]}
        _write_json(os.path.join(out_dir, "dataset_config.json"), config)
        _write_json(os.path.join(out_dir, "filter_report.json"), report)
        print(f"{task}: kept {len(kept)} of {len(ctx['rows'])} derived rows "
              f"({ctx['derive']['n_input']} D test rows; margin-only rule "
              f"{freport['margin_only_kept']}) -> {out_dir}")
        if not meets:
            print(f"HAND-BACK: {task} keeps {len(kept)} < {args.min_kept} test ids")
            status = EXIT_BELOW_MIN_KEPT
    return status


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(
        description="Build <task>_inversion, the Instructed-Inversion Condition (I): D test rows "
                    "with a transparent, form- and token-matched clause in place of the "
                    "Pressure Clause.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--stage", choices=("score", "assemble"), required=True)
    p.add_argument("--tasks", nargs="+", choices=TASKS, default=list(TASKS))
    p.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    p.add_argument("--work-dir", default=DEFAULT_WORK_DIR)
    p.add_argument("--pool", default=POOL_PATH)
    p.add_argument("--clause-forms", default=CLAUSE_FORMS_PATH,
                   help="ticket 02a's clause-form table; every D test clause must be in it and "
                        "agree with the text rule")
    p.add_argument("--min-kept", type=int, default=MIN_KEPT)
    p.add_argument("--model", default=dc.DEFAULT_MODEL)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--hf-token", default=None)
    p.add_argument("--no-model", action="store_true",
                   help="score stage dry run (CPU): derive and check every row, write nothing")
    return p


def _default_model_loader(tokenizer):
    def load(args):
        from dataset.pilot_v2 import load_model
        model, device = load_model(args)

        def score_fn(prompts, pairs):
            return dc.score_prompts(prompts, pairs, model, tokenizer, device,
                                    max_length=v2.MAX_SEQ_LENGTH,
                                    batch_size=args.batch_size, desc="scoring inversion")
        return score_fn
    return load


def main(argv=None, tokenizer=None, model_loader=None) -> int:
    args = build_parser().parse_args(argv)
    tokenizer = tokenizer if tokenizer is not None else _load_tokenizer(args)
    if args.stage == "score":
        return run_score(args, tokenizer, model_loader or _default_model_loader(tokenizer))
    return run_assemble(args, tokenizer)


if __name__ == "__main__":
    sys.exit(main())
