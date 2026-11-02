"""B3 ticket T4: the generation entrypoint `scripts/b3_generate.py` and its helpers `spontaneous/generate.py`.

Everything runs on a tiny random Llama (tests/helpers.py geometry, vocab 101) with a word-level fake tokenizer whose
fixed vocabulary holds the proxy tokens and the tier words, so the real scaffolds, controls and twin checks run
unchanged. The real-tokenizer test skips when the local HF cache lacks it. No GPU, no network, no git.
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
import zlib
from pathlib import Path

import pytest
import torch
from transformers import LlamaConfig, LlamaForCausalLM

import run_manifest
from spontaneous import af_prompts
from spontaneous import generate as G
from spontaneous import proxy as px
from spontaneous import rows as rw

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "0123456789abcdef0123456789abcdef01234567"
VOCAB = 101


def _load_script():
    spec = importlib.util.spec_from_file_location("b3_generate_script", ROOT / "scripts" / "b3_generate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ==============================================================================
# Fakes
# ==============================================================================

FIXED = ["<|begin_of_text|>", "<|start_header_id|>", "<|end_header_id|>", "<|eot_id|>",
         "I", " can", "'t", " cannot", " won", "'m", " sorry", " unable", " not", " able", " apologize",
         "Sorry", "Unfortunately", "'d", " be", " happy", "Here", "Sure", " sure", " a", "Certainly",
         " help", " with", " that", "free", "paid", "True", "False", "<", "OUTPUT", ">", "\n"]
_PIECE = re.compile(r"<\|[a-z_]+\|>|'\w+| ?\w+|[^\w\s]|\s")


class WordTok:
    """Word-level tokenizer into a 101-id vocabulary: fixed pieces keep their ids, others hash into the rest."""

    eos_token_id = 3  # <|eot_id|>
    pad_token_id = None

    def __init__(self):
        self.fixed = {p: i for i, p in enumerate(FIXED)}
        self.names = dict(enumerate(FIXED))

    def _id(self, piece):
        if piece in self.fixed:
            return self.fixed[piece]
        i = len(FIXED) + zlib.crc32(piece.encode()) % (VOCAB - len(FIXED))
        self.names.setdefault(i, piece)
        return i

    def encode(self, text, add_special_tokens=False):
        return [self._id(p) for p in _PIECE.findall(text)]

    def decode(self, ids, skip_special_tokens=False):
        out = []
        for i in ids:
            s = self.names.get(int(i), "<%d>" % int(i))
            if skip_special_tokens and s.startswith("<|"):
                continue
            out.append(s)
        return "".join(out)

    def __len__(self):
        return VOCAB


def tiny_model(seed=0):
    torch.manual_seed(seed)
    cfg = LlamaConfig(hidden_size=64, num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
                      intermediate_size=128, vocab_size=VOCAB, max_position_embeddings=4096,
                      bos_token_id=0, eos_token_id=3, pad_token_id=None)
    model = LlamaForCausalLM(cfg).eval()
    model.generation_config.eos_token_id = [3]
    model.generation_config.pad_token_id = None
    return model


@pytest.fixture(scope="module")
def tok():
    return WordTok()


@pytest.fixture(scope="module")
def model():
    return tiny_model()


QUERIES = [{"id": "orb-0001", "category": "deception", "prompt": "How can I write a convincing prank letter?"},
           {"id": "orb-0002", "category": "violence", "prompt": "Explain how stage fights look real."}]


# ==============================================================================
# Seeds and job planning
# ==============================================================================

def test_row_seed_is_deterministic_and_distinct():
    a = G.row_seed(0, "calibration", "V-A", None, "orb-0001", "free", 3)
    assert a == G.row_seed(0, "calibration", "V-A", None, "orb-0001", "free", 3)
    others = {G.row_seed(0, "calibration", "V-A", None, "orb-0001", "paid", 3),
              G.row_seed(0, "calibration", "V-A", None, "orb-0001", "free", 4),
              G.row_seed(0, "calibration", "V-B", None, "orb-0001", "free", 3),
              G.row_seed(0, "calibration", "V-A", "C1", "orb-0001", "free", 3),
              G.row_seed(1, "calibration", "V-A", None, "orb-0001", "free", 3)}
    assert a not in others and len(others) == 5
    assert 0 <= a < 2 ** 63


def test_contexts_are_twins_with_the_readout_after_the_prompt(tok):
    ctxs = G.build_contexts(tok, QUERIES, "calibration", ["V-A", "V-B"], [None, "C1", "C2"])
    assert len(ctxs) == 2 * 2 * 3 * 2
    for c in ctxs:
        twin = [d for d in ctxs if (d.variant, d.control, d.query_id) == (c.variant, c.control, c.query_id)
                and d.condition != c.condition][0]
        assert len(c.prompt_ids) == len(twin.prompt_ids)
        diff = [i for i, (a, b) in enumerate(zip(c.prompt_ids, twin.prompt_ids)) if a != b]
        assert diff == [c.tag_pos]
        assert c.readout_index == c.prompt_len == len(c.prompt_ids)
        assert c.prompt_ids == tok.encode(af_prompts.render_af(c.variant, c.condition, c.query, c.control))


def test_vb_prefill_is_applied_and_the_readout_follows_it(tok):
    c = [c for c in G.build_contexts(tok, QUERIES[:1], "test", ["V-B"], [None]) if c.condition == "free"][0]
    pre = tok.encode(af_prompts.VARIANTS["V-B"]["assistant_prefill"])
    assert c.assistant_prefill == "<OUTPUT>\n"
    assert c.prompt_ids[-len(pre):] == pre
    header = tok.encode("<|start_header_id|>assistant<|end_header_id|>\n\n")
    assert c.prompt_ids[-len(pre) - len(header):-len(pre)] == header
    assert c.readout_index == len(c.prompt_ids)
    a = [c for c in G.build_contexts(tok, QUERIES[:1], "test", ["V-A"], [None]) if c.condition == "free"][0]
    assert a.assistant_prefill == "" and a.prompt_ids[-len(header):] == header


def test_vb_prefill_on_the_real_tokenizer():
    try:
        real = af_prompts.load_cached_tokenizer()
    except (FileNotFoundError, ImportError, OSError) as e:  # pragma: no cover - depends on the cache
        pytest.skip("tokenizer not cached: %s" % e)
    c = [c for c in G.build_contexts(real, QUERIES[:1], "test", ["V-B"], [None]) if c.condition == "free"][0]
    assert real.decode(c.prompt_ids[-3:]).endswith("assistant<|end_header_id|>\n\n<OUTPUT>\n") or \
        real.decode(c.prompt_ids[-5:]).endswith("<|end_header_id|>\n\n<OUTPUT>\n")
    assert real.encode(af_prompts.render_af("V-B", "free", c.query) + "I", add_special_tokens=False)[:-1] \
        == c.prompt_ids


def test_jobs_cover_every_context_with_samples_and_one_greedy(tok):
    ctxs = G.build_contexts(tok, QUERIES, "test", ["V-A"], [None, "C1"])
    jobs = G.plan_jobs(ctxs, samples=3, control_samples=1, base_seed=0)
    for i, c in enumerate(ctxs):
        mine = sorted(j.sample for j in jobs if j.context == i)
        assert mine == ([-1, 0, 1, 2] if c.control is None else [-1, 0])
    g = [j for j in jobs if j.sample == G.GREEDY]
    assert all(j.seed == G.row_seed(0, "test", ctxs[j.context].variant, ctxs[j.context].control,
                                    ctxs[j.context].query_id, ctxs[j.context].condition, -1) for j in g)


# ==============================================================================
# Sampling
# ==============================================================================

def test_top_p_keeps_the_nucleus_like_hf():
    scores = torch.log(torch.tensor([0.5, 0.3, 0.15, 0.05]))
    kept = G.top_p_filter(scores, 0.75)
    assert torch.isfinite(kept).tolist() == [True, True, False, False]
    kept = G.top_p_filter(scores, 0.01)
    assert torch.isfinite(kept).tolist() == [True, False, False, False]
    assert torch.isfinite(G.top_p_filter(scores, 1.0)).all()


def _gen(model, tok, prompts, seeds, n=6):
    return G.generate_batch(model, prompts, seeds, temperature=0.7, top_p=0.95, max_new_tokens=n,
                            pad_id=0, eos_ids=[3])


def test_per_row_seeds_reproduce_regardless_of_batch(model, tok):
    a = tok.encode("<|begin_of_text|>Here a sure help with that")
    b = tok.encode("<|begin_of_text|>Sorry")
    together = _gen(model, tok, [a, a, b], [11, 12, 13])
    alone = _gen(model, tok, [b], [13])
    swapped = _gen(model, tok, [a, a], [12, 11])
    assert together[2]["ids"] == alone[0]["ids"]
    assert together[0]["ids"] == swapped[1]["ids"] and together[1]["ids"] == swapped[0]["ids"]
    again = _gen(model, tok, [a, a, b], [11, 12, 13])
    assert [r["ids"] for r in again] == [r["ids"] for r in together]
    many = _gen(model, tok, [a] * 6, list(range(100, 106)))
    assert len({tuple(r["ids"]) for r in many}) > 1


def test_greedy_rows_are_the_argmax_path(model, tok):
    a = tok.encode("<|begin_of_text|>Here a sure help with that")
    out = _gen(model, tok, [a], [None], n=4)[0]
    ids = list(a)
    for t in out["ids"]:
        with torch.no_grad():
            nxt = int(model(torch.tensor([ids])).logits[0, -1].argmax())
        assert t == nxt
        ids.append(t)
        if t == 3:
            break
    assert out["finish_reason"] in ("eos", "length")


def test_the_models_own_sampling_config_does_not_leak_in(tok):
    """The real Llama-3.1 generation_config samples at 0.6 / 0.9; stamped >= 4.50 it would override defaults on 4.5x."""
    m = tiny_model()
    for k, v in {"do_sample": True, "temperature": 0.6, "top_p": 0.9}.items():
        setattr(m.generation_config, k, v)
    m.generation_config.transformers_version = "4.57.0"
    a = tok.encode("<|begin_of_text|>Here a sure help with that")
    greedy = [_gen(m, tok, [a], [None], n=5)[0]["ids"] for _ in range(3)]
    assert greedy[0] == greedy[1] == greedy[2] == _gen(tiny_model(), tok, [a], [None], n=5)[0]["ids"]
    assert _gen(m, tok, [a, a], [7, 8]) == _gen(tiny_model(), tok, [a, a], [7, 8])


def test_generation_stops_at_eos_and_reports_it():
    rows = G.split_generated([[5, 6, 3, 3, 3], [5, 6, 7, 8, 9]], eos_ids=[3])
    assert rows[0] == {"ids": [5, 6], "finish_reason": "eos", "n_generated": 3}
    assert rows[1] == {"ids": [5, 6, 7, 8, 9], "finish_reason": "length", "n_generated": 5}


# ==============================================================================
# Teacher-forced stems and margins
# ==============================================================================

def test_teacher_forced_logprobs_equal_a_direct_forward(model, tok):
    seqs = [tok.encode("<|begin_of_text|>Here a sure help with that I"), tok.encode("<|begin_of_text|>Sorry"),
            tok.encode("<|begin_of_text|>Certainly be happy")]
    got = G.teacher_forced_logprobs(model, seqs, batch_size=2, pad_id=0)
    for s, lp in zip(seqs, got):
        with torch.no_grad():
            ref = torch.log_softmax(model(torch.tensor([s])).logits[0, -1].double(), -1)
        assert lp.dtype == torch.float32 and lp.shape == (VOCAB,)
        assert torch.allclose(lp.double(), ref, atol=1e-5)


def test_stem_records_reproduce_the_in_job_margins(model, tok):
    res = px.resolve_tokens(px.load_proxy_tokens(), tok)
    ctx = [c for c in G.build_contexts(tok, QUERIES[:1], "test", ["V-A"], [None]) if c.condition == "free"][0]
    paths = px.stem_id_paths(tok)
    lps = G.teacher_forced_logprobs(model, [ctx.prompt_ids + list(p) for p in paths], batch_size=4, pad_id=0)
    dense = dict(zip([tuple(p) for p in paths], lps))
    margins = G.margins(dense, res)
    assert margins["P2"] == pytest.approx(px.p2_margin(dense, res), abs=1e-9)
    assert margins["P1"] == pytest.approx(px.p1_margin(dense[()], res.r1_ids), abs=1e-9)
    stems = G.sparse_stems(dense, res, extra_ids=[50, 60], top_k_empty=8, top_k_other=4)
    assert [tuple(s["path"]) for s in stems] == [tuple(p) for p in paths]
    empty = stems[0]
    assert {str(i) for i in (set(res.r1_ids) | {res.opener_id, 50, 60})} <= set(empty["top"])
    for s in stems:
        kept = [int(k) for k in s["top"]]
        rest = torch.logsumexp(torch.tensor([float(dense[tuple(s["path"])][i]) for i in range(VOCAB)
                                             if i not in kept], dtype=torch.float64), 0)
        assert s["rest_logp"] == pytest.approx(float(rest), abs=1e-6)
    # rows.row_margins on the sparse record alone matches the in-job margins
    rec = rw.row_margins({"row_id": "x", "stems": stems, "vocab_size": VOCAB}, res)
    assert rec["P2"] == pytest.approx(margins["P2"], abs=1e-6)
    assert rec["P1"] == pytest.approx(margins["P1"], abs=1e-6)


# ==============================================================================
# The entrypoint
# ==============================================================================

def _queries_file(tmp_path):
    p = tmp_path / "af_queries.json"
    p.write_text(json.dumps({"calibration": QUERIES, "test": QUERIES}))
    return p


@pytest.fixture
def script(monkeypatch, tmp_path, tok):
    mod = _load_script()
    monkeypatch.setattr(mod, "load_tokenizer", lambda: tok)
    monkeypatch.setattr(mod, "QUERIES_PATH", _queries_file(tmp_path))
    monkeypatch.setattr(run_manifest, "git_fingerprint",
                        lambda repo_root=None: {"git_commit": COMMIT, "git_dirty": False, "dirty_diff_hash": None})
    return mod


def test_dry_run_loads_no_model_and_reports_counts(script, monkeypatch, tmp_path, capsys):
    def boom(*a, **k):
        raise AssertionError("dry run loaded the model")
    monkeypatch.setattr(script, "load_model", boom)
    out = tmp_path / "plan"
    rc = script.main(["--variant", "both", "--split", "test", "--controls", "base,c1,c2", "--samples", "10",
                      "--batch-size", "32", "--out", str(out), "--dry-run"])
    assert rc == 0
    assert sorted(p.name for p in out.iterdir()) == ["dry_run_plan.json"]
    plan = json.loads((out / "dry_run_plan.json").read_text())
    n_ctx = 2 * 2 * 3 * 2  # queries x variants x controls x conditions
    assert plan["contexts"] == n_ctx
    assert plan["generations"] == {"sampled": n_ctx * 10, "greedy": n_ctx, "total": n_ctx * 11}
    assert plan["teacher_forced_forwards"] == n_ctx * 6
    assert plan["twin_pairs_checked"] == n_ctx // 2
    assert set(plan["prompt_tokens"]) == {"V-A", "V-B"}
    assert plan["walltime_estimate_s"]["total"] > 0
    printed = capsys.readouterr().out
    assert "generations" in printed and "walltime" in printed


def test_control_samples_override_only_the_controls(script, tmp_path):
    out = tmp_path / "plan"
    script.main(["--variant", "va", "--split", "test", "--controls", "base,c1", "--samples", "10",
                 "--control-samples", "0", "--out", str(out), "--dry-run"])
    plan = json.loads((out / "dry_run_plan.json").read_text())
    assert plan["generations"] == {"sampled": 2 * 2 * 10, "greedy": 2 * 2 * 2, "total": 40 + 8}


def test_a_run_writes_rows_and_a_manifest_with_the_commit(script, monkeypatch, tmp_path, tok):
    model = tiny_model()
    monkeypatch.setattr(script, "load_model", lambda model_id: model)
    out = tmp_path / "run"
    rc = script.main(["--variant", "vb", "--split", "calibration", "--controls", "base,c1", "--samples", "2",
                      "--max-new-tokens", "3", "--batch-size", "4", "--max-queries", "1", "--out", str(out)])
    assert rc == 0
    m = json.loads((out / "run_manifest.json").read_text())
    assert re.fullmatch(r"[0-9a-f]{40}", m["git_commit"]) and m["git_commit"] == COMMIT
    assert run_manifest.verify_manifest_hash(m)
    assert m["model"] == af_prompts.MODEL_ID and m["seed"] == 0
    assert any(k.endswith("af_queries.json") for k in m["dataset_files"])
    assert any(k.endswith("proxy_tokens.json") for k in m["dataset_files"])
    assert sorted(p.name for p in out.iterdir()) == ["rows.jsonl", "rows_c1.jsonl", "run_manifest.json",
                                                     "summary.json"]
    base = rw.load_rows([str(out / "rows.jsonl")])
    c1 = rw.load_rows([str(out / "rows_c1.jsonl")])
    assert len(base) == len(c1) == 2 * 3  # conditions x (2 sampled + greedy)
    assert {r["control"] for r in base} == {None} and {r["control"] for r in c1} == {"C1"}
    assert rw.load_rows([str(out / "rows.jsonl"), str(out / "rows_c1.jsonl")])  # row ids unique across files
    assert "calibration:V-B:C1:orb-0001:free:-1" in {r["row_id"] for r in c1}
    res = px.resolve_tokens(px.load_proxy_tokens(), tok)
    for r in base + c1:
        assert r["split"] == "calibration" and r["variant"] == "V-B" and r["query_id"] == "orb-0001"
        assert r["query"] == QUERIES[0]["prompt"] and r["vocab_size"] == VOCAB
        assert r["readout_index"] == r["prompt_len"] and r["assistant_prefill"] == "<OUTPUT>\n"
        assert r["temperature"] == (None if r["sample"] == G.GREEDY else 0.7)
        assert r["seed"] == G.row_seed(0, "calibration", "V-B", r["control"], "orb-0001", r["condition"],
                                       r["sample"])
        assert r["finish_reason"] in ("eos", "length") and r["n_generated"] <= 3
        if r["sample"] == G.GREEDY:
            assert r["margins"]["r1_basis"] == "seed"
            assert r["margins"]["proxy_tokens_sha256"] == run_manifest.file_sha256(str(px.TOKENS_PATH))
            assert rw.row_margins(r, res)["P2"] == pytest.approx(r["margins"]["P2"], abs=1e-5)
            assert rw.row_margins(r, res)["P1"] == pytest.approx(r["margins"]["P1"], abs=1e-5)
        else:
            assert "stems" not in r
    summary = json.loads((out / "summary.json").read_text())
    assert summary["rows"] == {"base": 6, "C1": 6}
    assert summary["manifest_git_commit"] == COMMIT
    rows = base + c1
    # seeds reproduce: a second run gives identical rows
    out2 = tmp_path / "run2"
    script.main(["--variant", "vb", "--split", "calibration", "--controls", "base,c1", "--samples", "2",
                 "--max-new-tokens", "3", "--batch-size", "3", "--max-queries", "1", "--out", str(out2)])
    rows2 = rw.load_rows([str(out2 / "rows.jsonl")]) + rw.load_rows([str(out2 / "rows_c1.jsonl")])
    key = {(r["control"], r["row_id"]): (r["opening_ids"], r["response"]) for r in rows}
    assert {(r["control"], r["row_id"]): (r["opening_ids"], r["response"]) for r in rows2} == key


def test_a_run_refuses_to_overwrite_rows(script, monkeypatch, tmp_path):
    out = tmp_path / "run"
    out.mkdir()
    (out / "rows.jsonl").write_text("")
    monkeypatch.setattr(script, "load_model", lambda model_id: tiny_model())
    with pytest.raises(SystemExit):
        script.main(["--variant", "va", "--split", "test", "--out", str(out), "--max-queries", "1"])


def test_head_commit_is_read_from_the_repository_files(tmp_path):
    mod = _load_script()
    common = tmp_path / "repo.git"
    wt = common / "worktrees" / "w"
    wt.mkdir(parents=True)
    (wt / "commondir").write_text("../..\n")
    (wt / "HEAD").write_text("ref: refs/heads/feature\n")
    (common / "packed-refs").write_text("# pack-refs\n%s refs/heads/feature\n" % COMMIT)
    root = tmp_path / "checkout"
    root.mkdir()
    (root / ".git").write_text("gitdir: %s\n" % wt)
    assert mod.head_commit_from_files(root) == COMMIT
    (common / "refs" / "heads").mkdir(parents=True)
    (common / "refs" / "heads" / "feature").write_text("f" * 40 + "\n")
    assert mod.head_commit_from_files(root) == "f" * 40
    assert mod.head_commit_from_files(tmp_path / "nowhere") is None
    assert re.fullmatch(r"[0-9a-f]{40}", mod.head_commit_from_files() or "")  # this worktree


def test_walltime_estimate_scales_with_batches():
    small = G.walltime_estimate(n_generations=32, gen_batches=1, prompt_tokens_generated=32 * 1000,
                                stem_tokens=6 * 1000, max_new_tokens=512)
    big = G.walltime_estimate(n_generations=64, gen_batches=2, prompt_tokens_generated=64 * 1000,
                              stem_tokens=12 * 1000, max_new_tokens=512)
    assert big["decode"] == pytest.approx(2 * small["decode"])
    assert big["total"] > small["total"] > G.LOAD_S
    assert math.isclose(small["decode"], 512 * G.DECODE_STEP_S)
