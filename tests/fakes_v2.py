"""A contract-conforming stand-in for `dataset/deception_v2.py` (spec section 5).

Ticket 01's pilot harness is written against the spec 5 contract while ticket
02 builds the real module, so its tests run on this stub:

    make_spec(task, suffix, ser_wording) -> dc.TaskSpec
    load_framing(path) -> Framing (.id .family .round .hypothesis
                                   .clauses[task] -> 25 x {"id","text","shared"})
    load_neutral_pool(path) -> [sentence]
    realize(tokenizer, spec, framing, inst, neutral_pool, max_seq_length=120)
        -> record with the dc.realize_instance fields plus
           conditions{pressure, nopressure, neutral, honest_instruction}
           ({clean_prompt, corrupt_prompt} each), neutral_id, neutral_text

The scaffold strings are short on purpose: `FakeWordTokenizer` has a 256-word
vocabulary. Non-pressure conditions are derived by the real
`clause_surgery.remove_clause` / `replace_clause`, so stub prompts keep the
invariant the real records keep (the clause occurs once, after one space).
Unlike the real module, `realize` does NOT assert lengths: the harness must
catch an over-length prompt itself.
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List

from dataset import clause_surgery
from dataset import deception_common as dc

N_FLAVOR = 20
SHARED = [{"id": f"shared_{i:02d}", "text": f"Shared note {i:02d} applies now.",
           "shared": True} for i in range(5)]

PREDICATES = {"far_v2": ("failing", "passing"),
              "sdr_v2": ("critical", "harmless"),
              "ser_v2": ("unfavorable", "favorable")}
QUESTIONS = {"far_v2": "is failing", "sdr_v2": "will you show",
             ("ser_v2", "A"): "should worry me", ("ser_v2", "B"): "should I check"}


class Framing:
    def __init__(self, id, family, round, hypothesis, clauses):
        self.id = id
        self.family = family
        self.round = round
        self.hypothesis = hypothesis
        self.clauses = clauses


def make_spec(task: str, suffix: bool, ser_wording=None) -> dc.TaskSpec:
    if task not in PREDICATES:
        raise KeyError(task)
    if task == "ser_v2" and ser_wording not in ("A", "B"):
        raise ValueError("SER needs ser_wording A or B")
    if task != "ser_v2" and ser_wording is not None:
        raise ValueError("ser_wording is SER-only")
    question = QUESTIONS[(task, ser_wording)] if task == "ser_v2" else QUESTIONS[task]
    inv = PREDICATES[task][0]
    tail = f" The {inv} one matters most." if suffix else ""
    variants = []
    for name, noun in (("audit", "result"), ("lab", "reading")):
        variants.append(dc.TemplateVariant(
            name=name,
            intro="You review {entity} files.",
            designation=("The {item_d} " + noun + " is {desig} , the other is {desig_inv} ."
                         + tail),
            neutral_designation="Both are on file." + tail,
            user="Which " + noun + " " + question + " , {item_1} or {item_2} ?",
            stem="Answer:"))
    return dc.TaskSpec(task, task.upper(), "stub", PREDICATES[task][0],
                       PREDICATES[task][1], variants)


def load_framing(path: str) -> Framing:
    with open(path) as f:
        raw = json.load(f)
    clauses = {}
    for task, texts in raw["clauses"].items():
        if len(texts) != N_FLAVOR:
            raise ValueError(f"{task}: need {N_FLAVOR} flavor clauses")
        flavor = [{"id": f"{raw['id']}_{task}_{i:02d}", "text": t, "shared": False}
                  for i, t in enumerate(texts)]
        clauses[task] = flavor + [dict(c) for c in SHARED]
    return Framing(raw["id"], raw["family"], raw["round"], raw["hypothesis"], clauses)


def load_neutral_pool(path: str) -> List[str]:
    with open(path) as f:
        return json.load(f)


def _ntok(tokenizer, text):
    return len(tokenizer.encode(text, add_special_tokens=False))


def realize(tokenizer, spec, framing, inst, neutral_pool, max_seq_length=120) -> Dict:
    clause = framing.clauses[spec.task][inst["pressure_slot"]]
    variant = spec.variant(inst["template_variant"])
    built = dc.build_prompt_pair(
        spec, variant, inst["entity"], (inst["item_1"], inst["item_2"]),
        inst["item_polarity"], inst["designation_polarity"], clause["text"])
    text = clause["text"]
    n_p = _ntok(tokenizer, built["clean_prompt"])
    fits = [s for s in neutral_pool
            if _ntok(tokenizer, clause_surgery.replace_clause(
                built["clean_prompt"], text, s)) == n_p]
    if not fits:
        raise ValueError(f"no neutral sentence matches clause {clause['id']}")
    k = int(hashlib.sha1(inst["instance_id"].encode()).hexdigest(), 16) % len(fits)
    neutral = fits[k]

    def both(fn):
        return {"clean_prompt": fn(built["clean_prompt"]),
                "corrupt_prompt": fn(built["corrupt_prompt"])}

    conditions = {
        "pressure": both(lambda p: p),
        "nopressure": both(lambda p: clause_surgery.remove_clause(p, text)),
        "neutral": both(lambda p: clause_surgery.replace_clause(p, text, neutral)),
        "honest_instruction": both(lambda p: clause_surgery.replace_clause(
            p, text, dc.HONEST_INSTRUCTION)),
    }
    return {
        **inst, **built,
        "task": spec.task, "mechanism": spec.mechanism, "condition": "deceptive",
        "pressure": text, "pressure_id": clause["id"],
        "pressure_shared": bool(clause["shared"]),
        "framing_id": framing.id, "suffix": None, "ser_wording": None,
        "conditions": conditions,
        "neutral_id": f"neutral_{neutral_pool.index(neutral):02d}",
        "neutral_text": neutral,
    }


def write_framing(path, framing_id="r1_stub", family="stake_incentive",
                  tasks=("far_v2", "sdr_v2", "ser_v2")) -> str:
    """A 20-flavor-clause framing file whose clauses are 5 whitespace tokens."""
    raw = {"id": framing_id, "family": family, "round": 1,
           "hypothesis": "stub framing for harness tests",
           "clauses": {t: [f"Pressure note {i:02d} applies now." for i in range(N_FLAVOR)]
                       for t in tasks}}
    with open(path, "w") as f:
        json.dump(raw, f)
    return str(path)


def write_neutral_pool(path) -> str:
    with open(path, "w") as f:
        json.dump(["Neutral line one stays now.", "Neutral line two stays now.",
                   "Short neutral line."], f)
    return str(path)
