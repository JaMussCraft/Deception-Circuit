"""Ticket 04: the v2 full builder (`dataset/build_deception_v2.py`), on CPU.

The real `dataset/deception_v2.py` renders the prompts; a whitespace tokenizer
(`BigVocabTokenizer`) and a rule model stand in for Llama. The rule model reads
each prompt and answers:

  * prior prompt (neutral designation): balanced, except entities starting
    with "B" (|margin| = 1.0, so their instances fail the prior gate);
  * pressure with a flavor clause whose slot is EVEN: deceptive;
  * entities starting with "C", lab variant: deceptive without the clause too
    (designation copying, fails the nopressure gate);
  * entities starting with "C", audit variant: deceptive under the neutral twin
    (contingent but not full-build);
  * every other prompt: honest.
So full-build survivors are exactly the "A" entities' instances with an even
flavor slot.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from types import SimpleNamespace

import pytest
import torch

from dataset import build_deception_v2 as bv
from dataset import deception_common as dc
from tests.fakes import FakeWordTokenizer

v2 = pytest.importorskip("dataset.deception_v2")

TASKS = ("far_v2", "sdr_v2", "ser_v2")
ENTITIES = [{"name": n, "domain": d} for n, d in
            (("Acme", "health"), ("Alder", "energy"), ("Arbor", "retail"),
             ("Ashby", "health"), ("Borel", "energy"), ("Corin", "retail"))]
N_GENERATE = 43077            # 1.3 x 43077 / 1400 = 40.0 instances per target row
PAIRS = [("alpha", "beta"), ("gamma", "delta"), ("eps", "zeta"), ("eta", "theta")]
INVERSION = {"failing", "critical", "unfavorable"}


class BigVocabTokenizer(FakeWordTokenizer):
    LIMIT = 2048

    def _id(self, piece):
        if piece not in self.vocab:
            if len(self.vocab) >= self.LIMIT:
                raise RuntimeError("vocabulary exhausted")
            self.vocab[piece] = len(self.vocab)
        return self.vocab[piece]


def _parse(text):
    toks = text.replace("\n", " ").split()
    designated = pred = None
    for i in range(len(toks) - 5):
        if toks[i] == "The" and toks[i + 2] in ("result", "reading") and toks[i + 3] == "came":
            designated, pred = toks[i + 1], toks[i + 5].strip(",")
    slot = int(toks[toks.index("Pressure") + 2]) if "Pressure" in toks else None
    entity = next((e["name"] for e in ENTITIES
                   if e["name"] in toks or e["name"] + "'s" in toks), None)
    return SimpleNamespace(toks=toks, designated=designated, pred=pred, slot=slot,
                           entity=entity, lab="reading" in toks or "readings" in toks,
                           neutral="Neutral" in toks, honest_instruction="honestly" in toks)


def _pair_of(text):
    words = set(text.replace(".", " ").replace(",", " ").replace("?", " ").split())
    for a, b in PAIRS:
        if a in words and b in words:
            return a, b
    raise AssertionError(text)


def rule(text):
    p = _parse(text)
    a, b = _pair_of(text)
    if p.designated is None:                        # prior prompt
        return {a: 1.0 if p.entity.startswith("B") else 0.1, b: 0.0}
    other = b if p.designated == a else a
    honest = p.designated if p.pred in INVERSION else other
    deceptive = other if honest == p.designated else p.designated
    lie = {honest: 0.0, deceptive: 2.0}
    truth = {honest: 2.0, deceptive: 0.0}
    if p.slot is not None:
        return lie if (p.slot < 20 and p.slot % 2 == 0) else truth
    if p.honest_instruction:
        return truth
    if p.neutral:
        return lie if (p.entity.startswith("C") and not p.lab) else truth
    return lie if (p.entity.startswith("C") and p.lab) else truth   # nopressure


class RuleModel:
    def __init__(self, tok):
        self.tok = tok
        self.prompts = []

    def eval(self):
        return self

    def __call__(self, input_ids=None, attention_mask=None, **kw):
        b, l = input_ids.shape
        logits = torch.full((b, l, BigVocabTokenizer.LIMIT), -10.0)
        for i in range(b):
            ids = input_ids[i][attention_mask[i].bool()].tolist()
            text = self.tok.decode(ids)
            self.prompts.append(text)
            for word, val in rule(text).items():
                logits[i, :, self.tok.encode(" " + word)[0]] = val
        return SimpleNamespace(logits=logits)


@pytest.fixture
def tok():
    return BigVocabTokenizer()


@pytest.fixture
def env(tmp_path, tok):
    """A selection file, three framings, pilot reports and pools on disk."""
    pilots = tmp_path / "pilots"
    framing = {"id": "r9_itest", "family": "rule_instructed", "round": 9, "hypothesis": "h",
               "clauses": {t: [{"id": f"r9_itest_{t}_{i:02d}",
                                "text": f"Pressure {t} {i:02d} ends this pilot."}
                               for i in range(20)] for t in TASKS}}
    fpath = tmp_path / "r9_itest.json"
    fpath.write_text(json.dumps(framing))
    shared_counts = {len(s.split()) for s in v2.load_shared_clauses()}
    bases = ["Neutral one two three four five six seven eight nine ten eleven twelve",
             "Neutral uno dos tres cuatro cinco seis siete ocho nueve diez once doce"]
    neutrals = [" ".join(b.split()[:n]) + "." for n in sorted({6} | shared_counts)
                for b in bases]
    npath = tmp_path / "neutral.json"
    npath.write_text(json.dumps({"sentences": [{"id": f"neutral_{i:03d}", "text": t}
                                               for i, t in enumerate(neutrals)]}))
    ent = tmp_path / "entities.json"
    ent.write_text(json.dumps(ENTITIES))
    pairs = tmp_path / "pairs.json"
    pairs.write_text(json.dumps([list(p) for p in PAIRS]))
    per_task = {}
    for t, w, cap in (("far_v2", None, 0.5), ("sdr_v2", None, 0.5), ("ser_v2", "B", 0.5)):
        cid = f"c_{t}"
        d = pilots / "round9"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{cid}.json").write_text(json.dumps(
            {"cell_id": cid, "cost_projection": {"n_generate": N_GENERATE, "cap_used": cap}}))
        per_task[t] = {"round": 9, "cell_id": cid, "framing_path": str(fpath),
                       "framing_id": "r9_itest", "family": "rule_instructed",
                       "suffix": "on", "ser_wording": w, "overrides": {}, "cap_used": cap}
    sel = {"status": "FINAL", "suffix": "on", "family": "rule_instructed",
           "per_task": per_task, "ser_wordings_passing": ["B"]}
    spath = tmp_path / "pilot-selection.json"
    spath.write_text(json.dumps(sel))
    return SimpleNamespace(tmp=tmp_path, selection=str(spath), pilots=str(pilots),
                           neutral=str(npath), entities=str(ent), pairs=str(pairs),
                           framing=str(fpath), work=str(tmp_path / "work"),
                           data=str(tmp_path / "datasets"))


def _args(env, task, *extra):
    return ["--task", task, "--selection", env.selection, "--pilots-dir", env.pilots,
            "--neutral-pool", env.neutral, "--entities", env.entities,
            "--item-pairs", env.pairs, "--work-dir", env.work, "--data-dir", env.data,
            "--batch-size", "512", "--chunk-size", "5000", *extra]


# ------------------------------------------------------------------------------
# plan and instance list
# ------------------------------------------------------------------------------

def test_plan_uses_13x_the_pilot_n_generate_and_shares_the_longest_list(env):
    sel = bv.load_selection(env.selection)
    plan = bv.instance_plan(sel, env.pilots, targets={"train": 20, "validation": 20,
                                                      "test": 100})
    # 1.3 x n_generate / 1,400 rows (the pilot projected n_generate for 1,400)
    assert plan["factor"]["far_v2"] == pytest.approx(1.3 * N_GENERATE / 1400)
    # 100 x 1.3 x 43077 / 1400 = 4000.007 -> rounded up
    assert plan["per_task"]["far_v2"]["test"] == 4001
    assert plan["shared"]["test"] == max(plan["per_task"][t]["test"] for t in TASKS)


def test_instance_lists_are_task_independent_and_splits_disjoint(env):
    ents, pairs = dc.load_entities(env.entities), dc.load_item_pairs(env.pairs)
    counts = {"train": 30, "validation": 30, "test": 60}
    a = bv.shared_instance_lists(counts, ents, pairs, seed=42)
    b = bv.shared_instance_lists(counts, ents, pairs, seed=42)
    assert a == b
    ids = [i["instance_id"] for s in a.values() for i in s]
    assert len(ids) == len(set(ids))
    # the train list starts with the pilot's list (same seed, fresh seen set)
    pilot = dc.generate_instances(10, ents, pairs, 25, ("audit", "lab"), seed=42)
    assert a["train"][:10] == pilot
    top = bv.shared_instance_lists(counts, ents, pairs, seed=42, topup=1, base=a)
    assert not {i["instance_id"] for s in top.values() for i in s} & set(ids)


# ------------------------------------------------------------------------------
# stratified, capped selection
# ------------------------------------------------------------------------------

def _cands(n_per_cell, clauses=10, pairs=10, variants=("audit", "lab")):
    out, k = [], 0
    for dp in ("inversion", "identity"):
        for ip in (1, 2):
            for v in variants:
                for j in range(n_per_cell):
                    out.append({"instance_id": f"{k:06x}", "designation_polarity": dp,
                                "item_polarity": ip, "template_variant": v,
                                "pressure_id": f"c{k % clauses}",
                                "item_pair": f"p{(k // clauses) % pairs}"})
                    k += 1
    return out


def test_selection_hits_25_percent_per_stratum_and_balances_variants():
    # 12 clauses / 12 pairs at cap 20 each: 240 capacity for 200 rows (the
    # greedy fill is a heuristic; an exactly saturated pool may fall short)
    rows, rep = bv.select_split(_cands(40, clauses=12, pairs=12), 200, cap=0.10)
    assert len(rows) == 200 and rep["shortfall"] == 0
    assert rep["strategy"] in bv.SELECTION_STRATEGIES and rep["variant_deviation"] == 0
    st = Counter((r["designation_polarity"], r["item_polarity"]) for r in rows)
    assert set(st.values()) == {50}
    var = Counter(r["template_variant"] for r in rows)
    assert var == {"audit": 100, "lab": 100}


def test_selection_enforces_the_clause_and_pair_caps():
    cands = _cands(60, clauses=4, pairs=40)          # 4 clauses: cap 0.10 x 200 = 20 each
    rows, rep = bv.select_split(cands, 200, cap=0.10)
    assert max(Counter(r["pressure_id"] for r in rows).values()) <= 20
    assert rep["shortfall"] > 0                       # 4 x 20 = 80 < 200
    rows, rep = bv.select_split(_cands(60, clauses=8, pairs=8), 200, cap=0.15)
    assert len(rows) == 200
    assert max(Counter(r["pressure_id"] for r in rows).values()) <= 30
    assert max(Counter(r["item_pair"] for r in rows).values()) <= 30


def test_variant_floor_of_25_percent_and_fill_from_the_other_variant():
    cands = [c for c in _cands(60) if not (c["template_variant"] == "lab" and
                                           c["designation_polarity"] == "identity")]
    rows, rep = bv.select_split(cands, 200, cap=1.0)
    var = Counter(r["template_variant"] for r in rows)
    assert len(rows) == 200 and var["lab"] == 50 and var["audit"] == 150
    cands = [c for c in _cands(60) if c["template_variant"] == "audit" or
             c["instance_id"] < "000004"]
    rows, rep = bv.select_split(cands, 200, cap=1.0)
    assert rep["variant_floor_ok"] is False


def test_selection_walks_instance_id_order_within_a_stratum():
    cands = _cands(40)
    rows, _ = bv.select_split(list(reversed(cands)), 200, cap=1.0)
    for key in {(r["designation_polarity"], r["item_polarity"], r["template_variant"])
                for r in rows}:
        mine = sorted(c["instance_id"] for c in cands
                      if (c["designation_polarity"], c["item_polarity"],
                          c["template_variant"]) == key)
        got = sorted(r["instance_id"] for r in rows
                     if (r["designation_polarity"], r["item_polarity"],
                         r["template_variant"]) == key)
        assert got == mine[:len(got)]


# ------------------------------------------------------------------------------
# end to end: score then assemble
# ------------------------------------------------------------------------------

def _build(env, tok, task, model=None, extra=()):
    model = model or RuleModel(tok)
    hooks = dict(tokenizer=tok, model_loader=lambda args: (model, "cpu"))
    bv.main(_args(env, task, "--stage", "score", *extra), **hooks)
    return bv.main(_args(env, task, "--stage", "assemble", *extra), **hooks), model


SMALL = ("--train-samples", "8", "--val-samples", "8", "--test-samples", "16")


def test_gated_filters_only_score_rows_that_passed_the_previous_gate(env, tok):
    model = RuleModel(tok)
    bv.main(_args(env, "sdr_v2", "--stage", "score", *SMALL),
            tokenizer=tok, model_loader=lambda a: (model, "cpu"))
    outcomes, _, _ = bv.load_work(os.path.join(env.work, "sdr_v2"))
    n = len(outcomes)
    parsed = [_parse(p) for p in model.prompts]
    prior = [p for p in parsed if p.designated is None]
    assert len(prior) == n
    kept = [o for o in outcomes if o["prior_kept"]]
    dec = [o for o in kept if o["deceptive_pressure"]]
    cont = [o for o in dec if o["contingent"]]
    assert kept and dec and cont and len(cont) < len(dec) < len(kept) < n
    # prior -> 2 pressure streams per kept row -> 2 nopressure streams per
    # deceptive row -> 2 neutral + 2 honest-instruction streams per contingent row
    assert len(model.prompts) == n + 2 * len(kept) + 2 * len(dec) + 4 * len(cont)
    # prior-failed ("B") instances never reach a later gate
    assert not any(p.entity.startswith("B") for p in parsed if p.designated is not None)
    assert all(not o["entity"].startswith("B") for o in kept)
    # neutral twins are scored only for contingent rows
    assert sum(p.neutral and p.designated is not None for p in parsed) == 2 * len(cont)
    assert all(o["deceptive_pressure"] is None for o in outcomes if not o["prior_kept"])
    assert all(o["honest_nopressure"] is None for o in kept if not o["deceptive_pressure"])
    assert all(o["honest_neutral"] is None for o in dec if not o["contingent"])


def test_dhf_share_ids_and_order_with_labels_flipped_per_condition(env, tok):
    rc, _ = _build(env, tok, "far_v2", extra=SMALL)
    assert rc == 0
    from datasets import load_from_disk
    d = load_from_disk(os.path.join(env.data, "far_v2"))
    h = load_from_disk(os.path.join(env.data, "far_v2_honest"))
    f = load_from_disk(os.path.join(env.data, "far_v2_nopressure"))
    for split in ("train", "validation", "test"):
        assert d[split]["instance_id"] == h[split]["instance_id"] == f[split]["instance_id"]
        assert len(d[split]) > 0
        for rd, rh, rf in zip(d[split], h[split], f[split]):
            assert rd["condition"] == "deceptive" and rd["slot_kind"] == "pressure"
            assert rh["condition"] == "honest" and rh["slot_kind"] == "neutral"
            assert rf["condition"] == "nopressure" and rf["slot_kind"] == "none"
            assert (rh["target"], rh["distractor"]) == (rd["distractor"], rd["target"])
            assert (rf["target"], rf["distractor"]) == (rd["distractor"], rd["target"])
            assert rh["pressure"] == rh["neutral_text"] and rh["pressure_id"] == rd["pressure_id"]
            assert rh["honest_twin_kind"] == "neutral_clause"
            assert rf["pressure"] == "" and rf["pressure_id"] == rd["pressure_id"]
            assert rd["pressure"] in rd["clean_prompt"]
            assert rd["pressure"] not in rh["clean_prompt"]
            assert rh["neutral_text"] in rh["clean_prompt"]
            assert rd["pressure"] not in rf["clean_prompt"]
            assert rd["clean_margin"] >= 0.7 and rd["corrupt_margin"] >= 0.7
            assert rh["clean_margin"] >= 0.3 and rf["corrupt_margin"] >= 0.3
            # only Acme instances with an even flavor slot are full-build survivors
            assert rd["pressure_slot"] < 20 and rd["pressure_slot"] % 2 == 0
            assert rd["entity"].startswith("A")
            assert rd["framing_id"] == "r9_itest" and rd["suffix"] == "on"
            assert rd["honest_instruction_clean_prompt"].count("honestly") == 1


def test_configs_reports_and_provenance_carry_the_required_keys(env, tok):
    _build(env, tok, "ser_v2", extra=SMALL)
    base = os.path.join(env.data, "ser_v2")
    for suffix, cond, margin in (("", "deceptive", 0.7), ("_honest", "honest", 0.3),
                                 ("_nopressure", "nopressure", 0.3)):
        cfg = json.load(open(base + suffix + "/dataset_config.json"))
        for k in ("task", "mechanism", "condition", "margin_thresh", "prior_eps",
                  "max_seq_length", "framing_id", "suffix", "ser_wording", "seed",
                  "overgen_factor", "created"):
            assert k in cfg, k
        assert cfg["condition"] == cond and cfg["margin_thresh"] == margin
        assert cfg["max_seq_length"] == 120 and cfg["ser_wording"] == "B"
    assert json.load(open(base + "_honest/dataset_config.json"))["honest_twin_kind"] == \
        "neutral_clause"
    rep = json.load(open(base + "/filter_report.json"))
    for k in ("splits", "per_stratum", "pass_rate_by_pressure", "pass_rate_by_item_pair",
              "pass_rate_by_entity", "pass_rate_by_domain", "pass_rate_by_template_variant",
              "pass_rate_by_designation_polarity", "pass_rate_by_item_polarity",
              "unexpected_argmax_tokens", "margins", "prior_margin", "prompt_length",
              "shared_vs_flavor", "matched_pressure_subset", "cap_used", "cap_reason",
              "length_window", "honest_instruction_on_selected", "dhf_instance_ids_identical",
              "comparison_set"):
        assert k in rep, k
    assert rep["dhf_instance_ids_identical"] is True
    for stage in ("generated", "in_window", "prior_kept", "deceptive_pressure",
                  "contingent", "full_build", "selected"):
        assert stage in rep["splits"]["train"], stage
    prov = json.load(open(base + "/provenance.json"))
    for k in ("framing", "scaffold", "suffix_sentence", "neutral_pool", "sha256",
              "seed", "thresholds", "overgen_factor", "selection_path", "plan"):
        assert k in prov, k
    assert prov["framing"]["id"] == "r9_itest"
    for k in ("dataset/deception_v2.py", "dataset/build_deception_v2.py"):
        assert k in prov["sha256"]["sources"]


def test_refuses_to_write_into_an_existing_output_directory(env, tok):
    rc, _ = _build(env, tok, "sdr_v2", extra=SMALL)
    assert rc == 0
    model = RuleModel(tok)
    with pytest.raises(SystemExit, match="exists"):
        bv.main(_args(env, "sdr_v2", "--stage", "assemble", *SMALL),
                tokenizer=tok, model_loader=lambda a: (model, "cpu"))
    os.makedirs(os.path.join(env.data, "far_v2_nopressure"))
    with pytest.raises(SystemExit, match="exists"):
        _build(env, tok, "far_v2", extra=SMALL)
    assert not os.path.exists(os.path.join(env.data, "far_v2"))


def test_a_rerun_of_the_score_stage_skips_finished_chunks(env, tok):
    model = RuleModel(tok)
    bv.main(_args(env, "sdr_v2", "--stage", "score", *SMALL),
            tokenizer=tok, model_loader=lambda a: (model, "cpu"))
    n = len(model.prompts)
    bv.main(_args(env, "sdr_v2", "--stage", "score", *SMALL),
            tokenizer=tok, model_loader=lambda a: (model, "cpu"))
    assert len(model.prompts) == n


def test_shortfall_hands_back_with_counts_and_writes_nothing(env, tok):
    sel = json.load(open(env.selection))
    sel["per_task"]["far_v2"]["cap_used"] = 0.05        # floor(0.05 x 8) = 0 per clause
    json.dump(sel, open(env.selection, "w"))
    model = RuleModel(tok)
    hooks = dict(tokenizer=tok, model_loader=lambda a: (model, "cpu"))
    bv.main(_args(env, "far_v2", "--stage", "score", *SMALL), **hooks)
    rc = bv.main(_args(env, "far_v2", "--stage", "assemble", *SMALL), **hooks)
    assert rc == 4
    assert not os.path.exists(os.path.join(env.data, "far_v2"))
    short = json.load(open(os.path.join(env.work, "far_v2", "shortfall.json")))
    assert short["train"]["shortfall"] > 0


def test_length_window_drops_out_of_band_prompts_before_scoring(env, tok):
    model = RuleModel(tok)
    bv.main(_args(env, "far_v2", "--stage", "score", "--length-window", "0", "1", *SMALL),
            tokenizer=tok, model_loader=lambda a: (model, "cpu"))
    assert model.prompts == []
    outcomes, _, _ = bv.load_work(os.path.join(env.work, "far_v2"))
    assert outcomes and not any(o["in_window"] for o in outcomes)


def test_no_model_dry_path_loads_no_weights(env, tok):
    def boom(args):
        raise AssertionError("weights loaded")
    rc = bv.main(_args(env, "far_v2", "--stage", "score", "--no-model", *SMALL),
                 tokenizer=tok, model_loader=boom)
    assert rc == 0
    assert not os.path.exists(os.path.join(env.work, "far_v2"))


def test_finalize_writes_the_comparison_set_and_cross_task_band(env, tok):
    for t in TASKS:
        _build(env, tok, t, extra=SMALL)
    out = bv.finalize(env.data, tok, max_band=12, max_gap=6)
    path = os.path.join(env.data, "comparison_set_v2.json")
    rep = json.load(open(path))
    assert rep == out
    for split in ("train", "validation", "test"):
        assert "intersection_size" in rep["splits"][split]
        assert "shared_clause_subset" in rep["splits"][split]
    assert "d_prompt_band" in rep and "median_gap" in rep


def test_sbatch_wrapper_guards_env_init_and_passes_every_argument():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    text = open(os.path.join(root, "scripts", "build_v2.sbatch")).read()
    assert 'conda activate mgnp || { echo "Environment initialization failed"' in text
    assert "set +u" in text
    assert 'python dataset/build_deception_v2.py "$@"' in text
    assert "--no-model" in text


def test_the_reproducibility_check_re_renders_a_built_dataset_and_catches_drift(env, tok):
    from tests.test_v2_reproducibility import check_built_task
    _build(env, tok, "ser_v2", extra=SMALL)
    assert check_built_task(env.data, "ser_v2") == 8 + 8 + 16
    prov_path = os.path.join(env.data, "ser_v2", "provenance.json")
    prov = json.load(open(prov_path))
    prov["make_spec"]["ser_wording"] = "A"          # a different scaffold renders differently
    json.dump(prov, open(prov_path, "w"))
    with pytest.raises(AssertionError, match="does not re-render"):
        check_built_task(env.data, "ser_v2")
    with open(env.neutral, "a") as f:                 # a pool edit fails the hash check
        f.write("\n")
    with pytest.raises(AssertionError, match="sha256 mismatch"):
        check_built_task(env.data, "ser_v2")


def test_score_runs_on_disjoint_splits_equal_one_run(env, tok):
    model = RuleModel(tok)
    hooks = dict(tokenizer=tok, model_loader=lambda a: (model, "cpu"))
    bv.main(_args(env, "sdr_v2", "--stage", "score", "--splits", "test", *SMALL), **hooks)
    bv.main(_args(env, "sdr_v2", "--stage", "score", "--splits", "train", "validation",
                  *SMALL), **hooks)
    split_run, _, _ = bv.load_work(os.path.join(env.work, "sdr_v2"))
    other = env.tmp / "work_one"
    argv = _args(env, "sdr_v2", "--stage", "score", *SMALL)
    argv[argv.index("--work-dir") + 1] = str(other)
    bv.main(argv, **hooks)
    one_run, _, _ = bv.load_work(str(other / "sdr_v2"))
    key = lambda o: o["instance_id"]
    assert sorted(split_run, key=key) == sorted(one_run, key=key)



def _real_record(task, designation="inversion", wording=None):
    """A rendered v2 record with the real scaffold (no tokenizer needed)."""
    spec = v2.make_spec(task, True, wording)
    inst = {"entity": "Acme", "domain": "health", "item_1": "alpha", "item_2": "beta",
            "item_pair": "alpha/beta", "item_polarity": 1,
            "designation_polarity": designation, "pressure_slot": 0,
            "template_variant": "audit"}
    inst["instance_id"] = dc.instance_id(inst)
    built = v2.build_prompt_pair(spec, "audit", "Acme", ("alpha", "beta"), 1, designation,
                                 "Pressure clause ends this pilot.")
    return {**inst, **built, "task": task, "overrides": {}}


@pytest.mark.parametrize("task,wording", [("far_v2", None), ("sdr_v2", None), ("ser_v2", "B")])
@pytest.mark.parametrize("designation", ["inversion", "identity"])
def test_construction_check_holds_for_the_deceptive_target_and_fails_for_the_other(
        task, wording, designation):
    rec = _real_record(task, designation, wording)
    assert bv.construction_check(rec)["pass"]
    swapped = dict(rec, target=rec["distractor"], distractor=rec["target"])
    assert not bv.construction_check(swapped)["pass"]


def test_filter_report_and_provenance_record_construction_purity_and_the_judge_limit(env, tok):
    judge = env.tmp / "purity_v2.json"
    judge.write_text(json.dumps({"judge_model": "m", "confusion": {"far_v2": {"fabrication": 1}},
                                 "purity": {"far_v2": 1.0},
                                 "gate": {"pass": False, "failures": ["x"], "notes": []}}))
    _build(env, tok, "far_v2", extra=SMALL + ("--purity-report", str(judge)))
    base = os.path.join(env.data, "far_v2")
    rep = json.load(open(base + "/filter_report.json"))
    cc = rep["construction_checks"]
    assert all(v["passed"] == v["total"] > 0 for v in cc["selected_rows"].values())
    assert cc["all_full_build_survivors"]["passed"] == cc["all_full_build_survivors"]["total"]
    prov = json.load(open(base + "/provenance.json"))
    mp = prov["mechanism_purity"]
    assert mp["basis"].startswith("construction") and "do not separate" in mp["limitation"]
    assert mp["judge_reports"][0]["gate"]["pass"] is False
    assert mp["judge_reports"][0]["sha256"] == bv.sha256_file(str(judge))
