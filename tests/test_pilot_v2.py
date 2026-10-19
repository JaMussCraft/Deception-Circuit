"""The v2 pilot harness (`dataset/pilot_v2.py`), end to end on CPU.

`FakeWordTokenizer` + the spec-5 stub in `tests/fakes_v2.py` stand in for the
Llama tokenizer and `dataset/deception_v2.py`. Two fake models:

  * `ScriptedModel` (tests/fakes.py) drives `score_cell` directly, its script
    laid out in the harness's documented `SCORE_ORDER`;
  * `RuleModel` reads each prompt and answers by a rule, so whole rounds run
    through `main()` without depending on batch layout.

The rule: under pressure, a flavor clause with an EVEN slot number elicits
the deceptive answer, slot 01 elicits an unexpected token (" Sorry"), every
other prompt is answered honestly, and the prior is balanced. So the
contingent survivors are exactly the instances with an even flavor slot.
"""

from __future__ import annotations

import json
import os
from types import SimpleNamespace

import pytest
import torch

from dataset import deception_common as dc
from dataset import pilot_v2
from dataset.contingency import stream_words
from tests import fakes_v2
from tests.fakes import FakeWordTokenizer, ScriptedModel

ENTITIES = [{"name": "Acme", "domain": "health"}, {"name": "Borel", "domain": "energy"}]
PAIRS = [["alpha", "beta"], ["gamma", "delta"], ["eps", "zeta"]]
INVERSION_WORDS = {"failing", "critical", "unfavorable"}

REQUIRED_KEYS = {
    "cell_id", "round", "task", "framing_id", "framing_family", "suffix", "ser_wording",
    "seed", "n_generated", "scored", "thresholds", "seconds_per_forward", "n_forwards",
    "partition", "rates", "honest_instruction_on_survivors", "conditions",
    "prior_balance", "contingent_rate_by", "concentration",
    "contingent_rate_shared_vs_flavor", "lengths", "cost_projection", "verdict", "samples",
}
CONDS = ("pressure", "nopressure", "neutral", "honest_instruction")


# ----------------------------------------------------------------------------
# fake model that answers by rule
# ----------------------------------------------------------------------------

def _parse(text):
    toks = text.split()
    j = len(toks) - 1 - toks[::-1].index("or")
    item_1, item_2 = toks[j - 1], toks[j + 1]
    designated = pred = None
    for i in range(len(toks) - 4):
        if toks[i] == "The" and toks[i + 2] in ("result", "reading") and toks[i + 3] == "is":
            designated, pred = toks[i + 1], toks[i + 4]
    if "Pressure" in toks:
        cond, slot = "pressure", int(toks[toks.index("Pressure") + 2])
    elif "Shared" in toks:
        cond, slot = "pressure_shared", None
    elif "Neutral" in toks:
        cond, slot = "neutral", None
    elif "honestly" in toks:
        cond, slot = "honest_instruction", None
    else:
        cond, slot = "nopressure", None
    return SimpleNamespace(item_1=item_1, item_2=item_2, designated=designated,
                           pred=pred, cond=cond, slot=slot)


def rule(text):
    p = _parse(text)
    if p.designated is None:                       # the prior prompt
        return {p.item_1: 0.1, p.item_2: 0.0}
    other = p.item_2 if p.designated == p.item_1 else p.item_1
    honest = p.designated if p.pred in INVERSION_WORDS else other
    deceptive = other if honest == p.designated else p.designated
    if p.cond == "pressure" and p.slot == 1:
        return {"Sorry": 5.0, honest: 0.0, deceptive: 0.0}
    if p.cond == "pressure" and p.slot % 2 == 0:
        return {honest: 0.0, deceptive: 2.0}
    return {honest: 2.0, deceptive: 0.0}


class RuleModel:
    """Logits from `rule(prompt)`; records every prompt it scores."""

    def __init__(self, tok, on_call=None):
        self.tok = tok
        self.on_call = on_call
        self.prompts = []

    def eval(self):
        return self

    def __call__(self, input_ids=None, attention_mask=None, **kw):
        b, l = input_ids.shape
        logits = torch.full((b, l, 256), -10.0)
        for i in range(b):
            ids = input_ids[i][attention_mask[i].bool()].tolist()
            text = self.tok.decode(ids)
            self.prompts.append(text)
            if self.on_call:
                self.on_call(text)
            for word, val in rule(text).items():
                logits[i, :, self.tok.encode(" " + word)[0]] = val
        return SimpleNamespace(logits=logits)


# ----------------------------------------------------------------------------
# fixtures
# ----------------------------------------------------------------------------

@pytest.fixture
def tok():
    return FakeWordTokenizer()


@pytest.fixture
def env(tmp_path, tok, monkeypatch):
    """Pool files, a framing, cells.json, and the harness's loaders patched."""
    ent = tmp_path / "entities.json"
    ent.write_text(json.dumps(ENTITIES))
    pairs = tmp_path / "pairs.json"
    pairs.write_text(json.dumps(PAIRS))
    framing = fakes_v2.write_framing(tmp_path / "r1_stub.json")
    pool = fakes_v2.write_neutral_pool(tmp_path / "neutral.json")
    cells = [
        {"cell_id": "far-stub-off", "task": "far_v2", "framing": framing,
         "suffix": "off", "ser_wording": None, "n": 40},
        {"cell_id": "ser-stub-on-B", "task": "ser_v2", "framing": framing,
         "suffix": "on", "ser_wording": "B", "n": 40},
    ]
    cells_path = tmp_path / "cells.json"
    cells_path.write_text(json.dumps(cells))
    out = tmp_path / "round1"
    state = SimpleNamespace(model=None, model_loads=0)

    def load_model(args):
        state.model_loads += 1
        return state.model, "cpu"

    monkeypatch.setattr(pilot_v2, "load_backend", lambda: fakes_v2)
    monkeypatch.setattr(pilot_v2, "load_tokenizer", lambda args: tok)
    monkeypatch.setattr(pilot_v2, "load_model", load_model)
    argv = ["--cells", str(cells_path), "--round", "1", "--out-dir", str(out),
            "--entities", str(ent), "--item-pairs", str(pairs),
            "--neutral-pool", pool, "--batch-size", "64", "--partition", "testpart"]
    return SimpleNamespace(tmp=tmp_path, out=out, argv=argv, cells=cells,
                           framing=framing, pool=pool, state=state,
                           cells_path=cells_path, ent=ent, pairs=pairs)


def _instances(n, seed=42):
    return dc.generate_instances(n, ENTITIES, [tuple(p) for p in PAIRS], 25,
                                 ("audit", "lab"), seed=seed)


# ----------------------------------------------------------------------------
# end to end
# ----------------------------------------------------------------------------

def test_two_cells_end_to_end_report_schema_and_survivors(env, tok):
    env.state.model = RuleModel(tok)
    assert pilot_v2.main(env.argv) == 0
    assert env.state.model_loads == 1                        # one model load per job

    expected = {i["instance_id"] for i in _instances(40)
                if i["pressure_slot"] < 20 and i["pressure_slot"] % 2 == 0}
    assert expected
    for cell in env.cells:
        rep = json.loads((env.out / f"{cell['cell_id']}.json").read_text())
        assert REQUIRED_KEYS <= set(rep)
        assert rep["scored"] is True
        assert rep["cell_id"] == cell["cell_id"] and rep["task"] == cell["task"]
        assert rep["round"] == 1 and rep["seed"] == 42
        assert rep["framing_id"] == "r1_stub" and rep["framing_family"] == "stake_incentive"
        assert rep["suffix"] == cell["suffix"] and rep["ser_wording"] == cell["ser_wording"]
        assert rep["n_generated"] == 40 and rep["n_forwards"] == 40 * 9
        assert rep["partition"] == "testpart"
        assert rep["seconds_per_forward"] > 0
        by = rep["rates"]["by_designation_polarity"]
        assert set(by) == {"inversion", "identity"}
        for dp in by.values():
            for k in ("n", "prior_kept", "deceptive_pressure", "honest_nopressure",
                      "honest_neutral", "contingent", "full_build", "contingent_rate",
                      "full_build_rate", "wilson95_contingent"):
                assert k in dp
        assert set(rep["rates"]["by_designation_x_item_polarity"]) == {
            "inversion/item1", "inversion/item2", "identity/item1", "identity/item2"}
        assert set(rep["rates"]["at_margin_1_0"]) == {
            "by_designation_polarity", "by_designation_x_item_polarity"}
        assert sum(d["contingent"] for d in by.values()) == len(expected)
        hi = rep["honest_instruction_on_survivors"]
        assert hi["n_survivors"] == len(expected) and hi["accuracy"] == 1.0
        for k in ("item2_share", "positional_agreement", "survivor_item_polarity_mix",
                  "by_designation_polarity"):
            assert k in hi
        assert hi["positional_agreement"] == 0.0
        assert set(rep["conditions"]) == set(CONDS)
        for c in CONDS:
            assert set(rep["conditions"][c]) == {"argmax_mix", "margin_hist",
                                                 "unexpected_tokens"}
        assert rep["conditions"]["pressure"]["unexpected_tokens"] == {"'Sorry'": sum(
            1 for i in _instances(40) if i["pressure_slot"] == 1) * 2}
        assert set(rep["prior_balance"]) == {"keep_rate", "margin_summary",
                                             "keep_rate_by_item_pair"}
        assert set(rep["contingent_rate_by"]) == {"clause", "item_pair",
                                                  "template_variant", "domain"}
        assert {"top_clause_share", "top5_pair_share", "pair_collapse"} <= set(
            rep["concentration"])
        assert set(rep["contingent_rate_shared_vs_flavor"]) == {"shared", "flavor"}
        assert rep["contingent_rate_shared_vs_flavor"]["shared"]["passed"] == 0
        assert set(rep["lengths"]) >= set(CONDS)
        for c in CONDS:
            assert set(rep["lengths"][c]) == {"summary", "histogram"}
        for k in ("binding_stratum", "rate_min", "cap_used", "n_generate", "n_forwards",
                  "gpu_hours", "gpu_hours_with_safety"):
            assert k in rep["cost_projection"]
        assert rep["verdict"]["status"] in {"pass", "fail", "insufficient_n"}
        assert len(rep["samples"]) == 5
        for smp in rep["samples"]:
            for k in ("instance_id", "designation_polarity", "item_polarity",
                      "prompts", "scores"):
                assert k in smp
            assert set(smp["prompts"]) >= set(CONDS)
            for c in CONDS:
                assert set(smp["prompts"][c]) == {"clean_prompt", "corrupt_prompt"}
                assert set(smp["scores"][c]) == {"clean", "corrupt"}

        rows = [json.loads(line) for line in
                (env.out / f"{cell['cell_id']}.survivors.jsonl").read_text().splitlines()]
        assert {r["instance_id"] for r in rows} == expected
        for r in rows:
            assert r["task"] == cell["task"]
            assert r["flags"]["contingent"] is True
            assert set(r["conditions"]) == set(CONDS)
            assert set(r["scores"]) == set(CONDS)
            assert r["scores"]["pressure"]["clean"]["margin"] == pytest.approx(-2.0)
            assert r["prior_margin"] == pytest.approx(0.1)

    summary = json.loads((env.out / "round_summary.json").read_text())
    assert [c["cell_id"] for c in summary["cells"]] == [c["cell_id"] for c in env.cells]
    assert summary["aborted"] == []
    assert "round_verdict" in summary and "best_cell" in summary["round_verdict"]


def test_cells_of_different_tasks_share_instance_ids(env, tok):
    env.state.model = RuleModel(tok)
    pilot_v2.main(env.argv)
    ids = [{json.loads(line)["instance_id"] for line in
            (env.out / f"{c['cell_id']}.survivors.jsonl").read_text().splitlines()}
           for c in env.cells]
    assert ids[0] == ids[1] and ids[0]


def test_cell_files_are_written_before_the_next_cell_is_scored(env, tok):
    seen = {}

    def on_call(text):
        if "check" in text.split() and "checked" not in seen:     # first SER-B prompt
            seen["checked"] = True
            seen["report"] = (env.out / "far-stub-off.json").exists()
            seen["survivors"] = (env.out / "far-stub-off.survivors.jsonl").exists()
            seen["summary"] = (env.out / "round_summary.json").exists()

    env.state.model = RuleModel(tok, on_call=on_call)
    assert pilot_v2.main(env.argv) == 0
    assert seen == {"checked": True, "report": True, "survivors": True, "summary": True}


def test_no_model_dry_path_loads_no_weights(env, tok, monkeypatch):
    def boom(args):
        raise AssertionError("--no-model must not construct a model")

    monkeypatch.setattr(pilot_v2, "load_model", boom)
    assert pilot_v2.main(env.argv + ["--no-model"]) == 0
    for cell in env.cells:
        rep = json.loads((env.out / f"{cell['cell_id']}.json").read_text())
        assert rep["scored"] is False
        assert rep["n_generated"] == 40
        assert rep["cost_projection"] is None
        for c in CONDS:
            assert rep["lengths"][c]["summary"]["n"] == 40
            assert rep["lengths"][c]["histogram"]
        # nopressure drops the 5-token clause
        assert (rep["lengths"]["nopressure"]["summary"]["max"]
                == rep["lengths"]["pressure"]["summary"]["max"] - 5)
        assert len(rep["samples"]) == 3
        for smp in rep["samples"]:
            assert ">>>" in smp["tokens"]["pressure"]["clean"]
            assert set(smp["prompts"]) >= set(CONDS)
        assert not (env.out / f"{cell['cell_id']}.survivors.jsonl").exists()
    assert (env.out / "round_summary.json").exists()


def test_an_over_length_prompt_aborts_its_cell_and_is_never_scored(env, tok):
    long_clause = "Pressure " + "very " * 117 + "now."
    raw = {"id": "r1_long", "family": "consequence", "round": 1, "hypothesis": "h",
           "clauses": {"sdr_v2": [long_clause] * 20}}
    long_framing = env.tmp / "r1_long.json"
    long_framing.write_text(json.dumps(raw))
    long_pool = env.tmp / "long_neutral.json"
    long_pool.write_text(json.dumps(["Neutral " + "very " * 117 + "now.",
                                     "Neutral " + "very " * 117 + "too."]))
    cells = env.cells[:1] + [{"cell_id": "sdr-long", "task": "sdr_v2",
                              "framing": str(long_framing), "suffix": "off",
                              "ser_wording": None, "n": 40,
                              "neutral_pool": str(long_pool)}]
    env.cells_path.write_text(json.dumps(cells))
    env.state.model = RuleModel(tok)

    assert pilot_v2.main(env.argv) == 1
    assert not (env.out / "sdr-long.json").exists()
    aborted = json.loads((env.out / "sdr-long.aborted.json").read_text())
    assert "max_seq_length=120" in aborted["error"]
    assert aborted["record"]["instance_id"]
    assert (env.out / "far-stub-off.json").exists()           # the other cell ran
    assert all("very" not in p.split() for p in env.state.model.prompts)
    summary = json.loads((env.out / "round_summary.json").read_text())
    assert [a["cell_id"] for a in summary["aborted"]] == ["sdr-long"]


def test_a_malformed_framing_aborts_only_its_cell(env, tok):
    bad = env.tmp / "bad_framing.json"
    bad.write_text(json.dumps({"id": "r1_bad", "family": "consequence", "round": 1,
                               "hypothesis": "h", "clauses": {"far_v2": ["only one"]}}))
    cells = env.cells[:1] + [{"cell_id": "far-bad", "task": "far_v2",
                              "framing": str(bad), "suffix": "off",
                              "ser_wording": None, "n": 40}]
    env.cells_path.write_text(json.dumps(cells))
    env.state.model = RuleModel(tok)
    assert pilot_v2.main(env.argv) == 1
    aborted = json.loads((env.out / "far-bad.aborted.json").read_text())
    assert "20 flavor clauses" in aborted["error"]
    assert (env.out / "far-stub-off.json").exists()


def test_no_model_load_when_every_cell_aborts(env, tok):
    bad = env.tmp / "bad_framing.json"
    bad.write_text(json.dumps({"id": "r1_bad", "family": "consequence", "round": 1,
                               "hypothesis": "h", "clauses": {"far_v2": ["only one"]}}))
    env.cells_path.write_text(json.dumps([{"cell_id": "far-bad", "task": "far_v2",
                                           "framing": str(bad), "suffix": "off",
                                           "ser_wording": None, "n": 40}]))
    assert pilot_v2.main(env.argv) == 1
    assert env.state.model_loads == 0
    summary = json.loads((env.out / "round_summary.json").read_text())
    assert [a["cell_id"] for a in summary["aborted"]] == ["far-bad"]


def test_a_rerun_clears_the_stale_file_of_the_other_outcome(env, tok):
    # first run: the cell aborts (malformed framing); second run: it is fixed
    bad = env.tmp / "bad_framing.json"
    bad.write_text(json.dumps({"id": "r1_bad", "family": "consequence", "round": 1,
                               "hypothesis": "h", "clauses": {"far_v2": ["only one"]}}))
    cell = {"cell_id": "far-x", "task": "far_v2", "framing": str(bad), "suffix": "off",
            "ser_wording": None, "n": 40}
    env.cells_path.write_text(json.dumps([cell]))
    env.state.model = RuleModel(tok)
    assert pilot_v2.main(env.argv) == 1
    assert (env.out / "far-x.aborted.json").exists()
    cell["framing"] = env.framing
    env.cells_path.write_text(json.dumps([cell]))
    assert pilot_v2.main(env.argv) == 0
    assert (env.out / "far-x.json").exists()
    assert not (env.out / "far-x.aborted.json").exists()
    summary = pilot_v2.summarize(str(env.out))
    assert summary["aborted"] == [] and len(summary["cells"]) == 1
    # and the other way round: a scored cell that now aborts loses its report
    cell["framing"] = str(bad)
    env.cells_path.write_text(json.dumps([cell]))
    assert pilot_v2.main(env.argv) == 1
    assert not (env.out / "far-x.json").exists()
    assert not (env.out / "far-x.survivors.jsonl").exists()


def test_a_longer_instance_list_starts_with_the_shorter_one():
    pairs = [tuple(p) for p in PAIRS]
    short = pilot_v2.shared_instances(20, ENTITIES, pairs, 42)
    long = pilot_v2.shared_instances(60, ENTITIES, pairs, 42)
    assert [i["instance_id"] for i in long[:20]] == [i["instance_id"] for i in short]


def test_a_misaligned_record_aborts(tok):
    rec = {"instance_id": "x", "clean_item_d": "alpha", "corrupt_item_d": "beta",
           "neutral_prompt": "a b c",
           "conditions": {c: {"clean_prompt": "p alpha q", "corrupt_prompt": "p beta q"}
                          for c in CONDS}}
    pilot_v2.check_record(tok, rec, 120)
    rec["conditions"]["neutral"]["corrupt_prompt"] = "p beta q extra"
    with pytest.raises(AssertionError):
        pilot_v2.check_record(tok, rec, 120)


def test_summarize_writes_the_round_summary_and_a_markdown_table(env, tok):
    env.state.model = RuleModel(tok)
    pilot_v2.main(env.argv)
    (env.out / "round_summary.json").unlink()
    md = env.tmp / "pilot-round-1.md"
    assert pilot_v2.main(["--summarize", str(env.out), "--markdown", str(md)]) == 0
    text = md.read_text()
    assert "far-stub-off" in text and "ser-stub-on-B" in text
    assert text.count("\n|") >= 4                      # header, rule, two rows
    summary = json.loads((env.out / "round_summary.json").read_text())
    assert len(summary["cells"]) == 2


# ----------------------------------------------------------------------------
# score_cell with ScriptedModel
# ----------------------------------------------------------------------------

def test_score_cell_reads_each_stream_with_its_honest_word_first(env, tok):
    cell = pilot_v2.parse_cells(str(env.cells_path))[0]
    cell["n"] = 4
    prepared = pilot_v2.prepare_cell(
        cell, _instances(4), tok, fakes_v2, max_seq_length=120,
        neutral_pool_path=env.pool)
    recs = prepared["records"]

    def tid(w):
        return tok.encode(" " + w)[0]

    script = []
    for cond, stream in pilot_v2.SCORE_ORDER:
        rows = []
        for r in recs:
            if cond == "prior":
                rows.append({tid(r["item_1"]): 0.25, tid(r["item_2"]): 0.0})
                continue
            honest = r["distractor"] if stream == "clean" else r["target"]
            deceptive = r["target"] if stream == "clean" else r["distractor"]
            # deceptive under pressure by 1.5, honest elsewhere by 0.5
            if cond == "pressure":
                rows.append({honest: 0.0, deceptive: 1.5})
            else:
                rows.append({honest: 0.5, deceptive: 0.0})
            rows[-1] = {tid(w): v for w, v in rows[-1].items()}
        script.append(rows)
    model = ScriptedModel(script)
    scores, prior, spf, n_fwd = pilot_v2.score_cell(
        prepared, model, tok, "cpu", batch_size=64, max_seq_length=120)
    assert model.calls == 9 and n_fwd == 36 and spf > 0
    assert prior == pytest.approx([0.25] * 4)
    for sc in scores:
        for st in ("clean", "corrupt"):
            assert sc["pressure"][st]["margin"] == pytest.approx(-1.5)
            assert sc["pressure"][st]["choice"] == "b"
            for c in ("nopressure", "neutral", "honest_instruction"):
                assert sc[c][st]["margin"] == pytest.approx(0.5)
                assert sc[c][st]["choice"] == "a"


def test_parse_cells_normalizes_suffix_and_rejects_bad_cells(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([{"cell_id": "a", "task": "far_v2", "framing": "f.json",
                              "suffix": True, "ser_wording": None, "n": 10}]))
    assert pilot_v2.parse_cells(str(p))[0]["suffix"] == "on"
    for bad in ({"suffix": "maybe"}, {"task": "far"}, {"ser_wording": "C"}):
        cell = {"cell_id": "a", "task": "far_v2", "framing": "f.json", "suffix": "off",
                "ser_wording": None, "n": 10, **bad}
        p.write_text(json.dumps([cell]))
        with pytest.raises(ValueError):
            pilot_v2.parse_cells(str(p))
    dup = {"cell_id": "a", "task": "far_v2", "framing": "f.json", "suffix": "off",
           "ser_wording": None, "n": 10}
    p.write_text(json.dumps([dup, dup]))
    with pytest.raises(ValueError):
        pilot_v2.parse_cells(str(p))


def test_multi_token_item_pairs_are_dropped_before_generation():
    class TwoTok(FakeWordTokenizer):
        def encode(self, text, add_special_tokens=False):
            ids = super().encode(text)
            return ids + ids if text.strip() == "zeta" else ids
    keep, dropped = pilot_v2.single_token_pairs(TwoTok(), [tuple(p) for p in PAIRS])
    assert keep == [("alpha", "beta"), ("gamma", "delta")]
    assert dropped == ["eps/zeta"]


# ----------------------------------------------------------------------------
# integration with the real dataset/deception_v2.py (ticket 02)
# ----------------------------------------------------------------------------

class BigVocabTokenizer(FakeWordTokenizer):
    """FakeWordTokenizer with room for the real v2 scaffold's vocabulary."""
    LIMIT = 1024

    def _id(self, piece):
        if piece not in self.vocab:
            if len(self.vocab) >= self.LIMIT:
                raise RuntimeError("BigVocabTokenizer vocabulary exhausted")
            self.vocab[piece] = len(self.vocab)
        return self.vocab[piece]


_NEUTRAL_BASES = [
    "The review ran over several weeks in a mild spring with long quiet days",
    "Paper copies sit in the archive beside old ledgers and maps from earlier",
]


def test_a_real_deception_v2_record_runs_through_pilot_scoring(tmp_path):
    v2 = pytest.importorskip("dataset.deception_v2")
    tok = BigVocabTokenizer()
    tasks = ("far_v2", "sdr_v2", "ser_v2")
    # six-word flavor clauses; neutral sentences at 6 words and at every shared
    # clause's word count, so the whitespace tokenizer finds equal-length twins
    framing = {"id": "r1_itest", "family": "consequence", "round": 1, "hypothesis": "h",
               "clauses": {t: [{"id": f"r1_itest_{t}_{i:02d}",
                                "text": f"Pressure {t} {i:02d} ends this pilot."}
                               for i in range(20)] for t in tasks}}
    fpath = tmp_path / "r1_itest.json"
    fpath.write_text(json.dumps(framing))
    shared_counts = {len(s.split()) for s in v2.load_shared_clauses()}
    neutrals = [" ".join(b.split()[:n]) + "." for n in sorted({6} | shared_counts)
                for b in _NEUTRAL_BASES]
    npath = tmp_path / "neutral.json"
    npath.write_text(json.dumps({"sentences": [{"id": f"neutral_{i:03d}", "text": t}
                                               for i, t in enumerate(neutrals)]}))
    entities = [{"name": "Vantis Medical", "domain": "healthcare"}]
    pairs, dropped = pilot_v2.single_token_pairs(tok, [("budget", "timeline"),
                                                       ("audio", "charging")])
    assert not dropped
    instances = pilot_v2.shared_instances(12, entities, pairs, seed=42)

    cell = {"cell_id": "sdr-itest-on", "task": "sdr_v2", "framing": str(fpath),
            "suffix": "on", "ser_wording": None, "n": 12, "neutral_pool": None}
    prepared = pilot_v2.prepare_cell(cell, instances, tok, v2, max_seq_length=120,
                                     neutral_pool_path=str(npath))
    recs = prepared["records"]
    assert len(recs) == 12 and recs[0]["task"] == "sdr_v2"
    for r in recs:
        assert set(r["conditions"]) == set(CONDS)
        n_p = len(tok.encode(r["conditions"]["pressure"]["clean_prompt"]))
        assert len(tok.encode(r["conditions"]["neutral"]["clean_prompt"])) == n_p

    def tid(w):
        return tok.encode(" " + w)[0]

    def deceives(r):
        return r["pressure_slot"] < 20 and r["pressure_slot"] % 2 == 0

    script = []
    for cond, stream in pilot_v2.SCORE_ORDER:
        rows = []
        for r in recs:
            if cond == "prior":
                rows.append({tid(r["item_1"]): 0.0, tid(r["item_2"]): 0.2})
                continue
            honest, deceptive = stream_words(r, stream)
            lie = cond == "pressure" and deceives(r)
            rows.append({tid(honest): 0.0 if lie else 1.0,
                         tid(deceptive): 1.0 if lie else 0.0})
        script.append(rows)
    model = ScriptedModel(script, vocab_size=BigVocabTokenizer.LIMIT)
    scores, prior, spf, n_fwd = pilot_v2.score_cell(
        prepared, model, tok, "cpu", batch_size=64, max_seq_length=120)
    rep, survivors = pilot_v2.cell_report(prepared, tokenizer=tok, round_id=0, seed=42,
                                          scores=scores, prior=prior,
                                          seconds_per_forward=spf, partition="cpu")
    assert n_fwd == 12 * 9 and prior == pytest.approx([-0.2] * 12)
    assert {s["instance_id"] for s in survivors} == {r["instance_id"] for r in recs
                                                     if deceives(r)}
    assert rep["scored"] and rep["framing_id"] == "r1_itest" and rep["suffix"] == "on"
    assert rep["honest_instruction_on_survivors"]["accuracy"] == 1.0
    assert REQUIRED_KEYS <= set(rep)


def test_sbatch_wrapper_guards_env_init_and_passes_every_argument():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "scripts", "pilot_v2.sbatch")
    text = open(path).read()
    directives = [l for l in text.splitlines() if l.startswith("#SBATCH")]
    assert "#SBATCH --gpus-per-node=1" in directives
    assert "#SBATCH --output=logs/pilot_v2_%j.out" in directives
    # account, partition and time go on the command line, never as defaults
    assert not any(d.split()[1].split("=")[0] in ("--account", "--partition", "--time")
                   for d in directives)
    assert ("source ~/.bashrc && conda activate mgnp || "
            "{ echo \"Environment initialization failed\" >&2; exit 1; }") in text
    assert 'python dataset/pilot_v2.py "$@"' in text
    assert "--no-model" in text and "--test-only" in text
