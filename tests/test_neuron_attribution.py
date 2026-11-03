"""Tests for component_analysis/neuron_attribution.py and scripts/neuron_attribution.py (neuron-partition N1 scorer).

Model tests run a tiny random Llama (2 layers, 64 hidden, 128 MLP neurons) whose vocabulary is the real Llama-3
tokenizer's, so the real far_v2 rows and answer token ids are used unchanged; they skip without the cached tokenizer.
The key correctness test compares attribution patching with a finite-difference activation patch of one neuron, in
float64, at layer 0 (where a cut autograd graph would show) and layer 1. CPU only, no network, no git.
"""

import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

np = pytest.importorskip("numpy")
torch = pytest.importorskip("torch")

from component_analysis import neuron_attribution as na  # noqa: E402
from scripts import neuron_attribution as cli  # noqa: E402

DATA = os.path.join(REPO, "data", "datasets")
HAVE_FAR = all(os.path.exists(os.path.join(DATA, n, "dataset_dict.json")) for n in ("far_v2", "far_v2_honest"))
POOL_I = os.path.join(na.CODEX_POOL_ROOT, "far_v2_user_inversion")
POOL_N = os.path.join(na.CODEX_POOL_ROOT, "far_v2_user_neutral")
HAVE_POOL = all(os.path.exists(os.path.join(p, "dataset_dict.json")) for p in (POOL_I, POOL_N))


@pytest.fixture(scope="module")
def tok():
    pytest.importorskip("transformers")
    try:
        tokenizer, _ = cli.load_tokenizer(cli.DEFAULT_MODEL)
        return tokenizer
    except Exception as e:  # offline / not cached / gated
        pytest.skip(f"Llama tokenizer unavailable: {type(e).__name__}: {e}")


def _tiny(tok, dtype):
    from transformers import LlamaConfig, LlamaForCausalLM
    eot = tok.convert_tokens_to_ids("<|eot_id|>")
    cfg = LlamaConfig(hidden_size=64, num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
                      intermediate_size=128, vocab_size=len(tok), max_position_embeddings=1024,
                      bos_token_id=128000, eos_token_id=eot, pad_token_id=eot)
    torch.manual_seed(0)
    model = LlamaForCausalLM(cfg).to(dtype).eval()
    for p in model.parameters():
        p.requires_grad = False
    return model


@pytest.fixture(scope="module")
def tiny(tok):
    return _tiny(tok, torch.float32)


@pytest.fixture(scope="module")
def tiny64(tok):
    return _tiny(tok, torch.float64)


def _random_rows(n, length, *, seed, vocab=1000, span=(3, 7), pad_tail=0):
    """Rows of random token ids: the twin differs from the clean prompt only inside `span`."""
    g = torch.Generator().manual_seed(seed)
    rows = []
    for i in range(n):
        real = length - (pad_tail if i % 2 else 0)
        ids = torch.randint(10, vocab, (length,), generator=g)
        twin = ids.clone()
        twin[span[0]:span[1]] = torch.randint(10, vocab, (span[1] - span[0],), generator=g)
        mask = torch.zeros(length, dtype=torch.long)
        mask[:real] = 1
        ids[real:] = 0
        twin[real:] = 0
        rows.append(na.PairedRow(id=f"r{i}", split="validation", input_ids=ids, twin_input_ids=twin,
                                 attention_mask=mask, readout=real - 1, span=span,
                                 target=int(torch.randint(10, vocab, (1,), generator=g)),
                                 distractor=int(torch.randint(10, vocab, (1,), generator=g))))
    return rows


def _metric(model, batch):
    return na.run_metric(model, batch.input_ids, batch.attention_mask, batch.readout, batch.target, batch.distractor)


# ==============================================================================
# HOOKS
# ==============================================================================

def test_capture_is_the_post_swiglu_down_proj_input(tiny):
    batch = na.collate(_random_rows(3, 12, seed=1))
    mlp_inputs = {}
    handles = [layer.mlp.register_forward_pre_hook(lambda m, a, i=i: mlp_inputs.__setitem__(i, a[0]))
               for i, layer in enumerate(tiny.model.layers)]
    try:
        with torch.no_grad(), na.NeuronCapture(tiny, grad=False) as cap:
            tiny.model(input_ids=batch.input_ids, attention_mask=batch.attention_mask, use_cache=False)
    finally:
        for h in handles:
            h.remove()
    assert na.geometry(tiny) == (2, 128)
    assert len(cap.acts) == 2
    for i, act in enumerate(cap.acts):
        assert tuple(act.shape) == (3, 12, 128)
        mlp = tiny.model.layers[i].mlp
        x = mlp_inputs[i]
        torch.testing.assert_close(act, mlp.act_fn(mlp.gate_proj(x)) * mlp.up_proj(x))
    assert tuple(cap.final.shape) == (3, 12, 64)


def test_readout_metric_matches_the_full_logits(tiny):
    batch = na.collate(_random_rows(3, 12, seed=2, pad_tail=4))
    m = _metric(tiny, batch)
    with torch.no_grad():
        logits = tiny(input_ids=batch.input_ids, attention_mask=batch.attention_mask, use_cache=False).logits.float()
    rows = torch.arange(3)
    ref = logits[rows, batch.readout, batch.target] - logits[rows, batch.readout, batch.distractor]
    torch.testing.assert_close(m, ref, rtol=1e-4, atol=1e-4)


def test_collate_trims_shared_padding_without_changing_the_metric(tiny):
    rows = _random_rows(2, 16, seed=3, pad_tail=5)
    for r in rows:   # extra right padding every row shares
        r.input_ids = torch.cat([r.input_ids, torch.zeros(6, dtype=torch.long)])
        r.twin_input_ids = torch.cat([r.twin_input_ids, torch.zeros(6, dtype=torch.long)])
        r.attention_mask = torch.cat([r.attention_mask, torch.zeros(6, dtype=torch.long)])
    batch = na.collate(rows)
    assert batch.input_ids.shape[1] == 16
    together = _metric(tiny, batch)
    alone = torch.cat([_metric(tiny, na.collate([r])) for r in rows])
    torch.testing.assert_close(together, alone, rtol=1e-4, atol=1e-4)


# ==============================================================================
# ATTRIBUTION PATCHING AGAINST A FINITE-DIFFERENCE PATCH
# ==============================================================================

def _row_scores(model, row, reverse=False):
    acc = na.Accumulator(*na.geometry(model), torch.device("cpu"), reverse=reverse)
    m_clean, m_twin = na.score_batch(model, na.collate([row]), acc)
    return acc.finalize(), m_clean, m_twin


def _activations(model, ids, mask):
    with torch.no_grad(), na.NeuronCapture(model, grad=False) as cap:
        model.model(input_ids=ids, attention_mask=mask, use_cache=False)
    return [a.clone() for a in cap.acts]


def _fd_gradient(model, batch, *, layer, index, position, eps=1e-3):
    """dm/da for one neuron at one position by a central difference of a unit shift.

    Central, with a step of 1e-3: Llama's RMSNorm casts to float32 inside even a float64 model, so a forward
    difference with a tiny step measures float32 rounding, not the derivative (1e-3 agrees with the analytic
    gradient to about 1e-5 relative on this model; 1e-1 is already off by 3e-3 from curvature).
    """
    def moved(step):
        with na.shift_neuron(model, layer=layer, index=index, position=[position], delta=[step]):
            return _metric(model, batch).item()
    return (moved(eps) - moved(-eps)) / (2 * eps)


@pytest.mark.parametrize("layer", [0, 1])
def test_atp_at_the_readout_equals_a_finite_difference_patch(tiny64, layer):
    """AtP = (a_clean - a_twin) * dm/da, against the same product with dm/da from a finite-difference patch of the
    one neuron. Layer 0 is where a cut autograd graph would show (its gradient runs through layer 1)."""
    row = _random_rows(1, 14, seed=4)[0]
    batch = na.collate([row])
    scores, _, _ = _row_scores(tiny64, row)
    a_c = _activations(tiny64, batch.input_ids, batch.attention_mask)[layer][0, row.readout]
    a_t = _activations(tiny64, batch.twin_input_ids, batch.attention_mask)[layer][0, row.readout]
    checked = 0
    for index in range(0, 128, 9):
        fd = (a_c[index] - a_t[index]).item() * _fd_gradient(tiny64, batch, layer=layer, index=index,
                                                             position=row.readout)
        atp = scores["atp_readout_mean"][layer, index].item()
        assert atp == pytest.approx(fd, rel=1e-4, abs=1e-8), (layer, index)
        assert scores["atp_readout_absmean"][layer, index].item() == pytest.approx(abs(atp), rel=1e-9, abs=1e-12)
        checked += abs(fd) > 1e-6
    assert checked >= 5   # the comparison was not between zeros


def test_atp_over_the_clause_equals_the_summed_finite_differences(tiny64):
    row = _random_rows(1, 14, seed=5, span=(4, 8))[0]
    batch = na.collate([row])
    scores, _, _ = _row_scores(tiny64, row)
    layer, index = 0, 17
    a_c = _activations(tiny64, batch.input_ids, batch.attention_mask)[layer][0]
    a_t = _activations(tiny64, batch.twin_input_ids, batch.attention_mask)[layer][0]
    total = sum((a_c[pos, index] - a_t[pos, index]).item()
                * _fd_gradient(tiny64, batch, layer=layer, index=index, position=pos) for pos in range(4, 8))
    assert abs(total) > 1e-6
    assert scores["atp_clause_mean"][layer, index].item() == pytest.approx(total, rel=1e-4, abs=1e-8)


def test_a_one_neuron_patch_moves_m_by_about_the_atp_estimate(tiny64):
    """The full activation patch (clean value replaced by the twin value) against AtP: equal to first order, so
    the two agree closely on this small, smooth model (not a tolerance claim for the 8B model)."""
    row = _random_rows(1, 14, seed=4)[0]
    batch = na.collate([row])
    scores, _, _ = _row_scores(tiny64, row)
    a_c = _activations(tiny64, batch.input_ids, batch.attention_mask)[1][0, row.readout]
    a_t = _activations(tiny64, batch.twin_input_ids, batch.attention_mask)[1][0, row.readout]
    base = _metric(tiny64, batch).item()
    index = int(scores["atp_readout_absmean"][1].argmax())
    with na.shift_neuron(tiny64, layer=1, index=index, position=[row.readout],
                         delta=[(a_t[index] - a_c[index]).item()]):
        patched = _metric(tiny64, batch).item()
    assert scores["atp_readout_mean"][1, index].item() == pytest.approx(base - patched, rel=0.05)


def test_reverse_atp_uses_the_twin_gradient(tiny64):
    row = _random_rows(1, 12, seed=6)[0]
    swapped = na.PairedRow(id=row.id, split=row.split, input_ids=row.twin_input_ids, twin_input_ids=row.input_ids,
                           attention_mask=row.attention_mask, readout=row.readout, span=row.span, target=row.target,
                           distractor=row.distractor)
    forward, _, _ = _row_scores(tiny64, row, reverse=True)
    backward, _, _ = _row_scores(tiny64, swapped)
    torch.testing.assert_close(forward["rev_atp_readout_mean"], backward["atp_readout_mean"])
    torch.testing.assert_close(forward["rev_atp_clause_mean"], backward["atp_clause_mean"])


def test_rows_in_one_batch_are_scored_independently(tiny64):
    rows = _random_rows(3, 12, seed=7, pad_tail=3)
    together, record = na.score_rows(tiny64, rows, batch_size=3)
    acc_sum = {k: torch.zeros_like(v) for k, v in together.items()}
    for r in rows:
        alone, _, _ = _row_scores(tiny64, r)
        for k in ("atp_readout_mean", "atp_clause_mean", "contrast_readout_mean"):
            acc_sum[k] += alone[k] / 3
    for k in ("atp_readout_mean", "atp_clause_mean", "contrast_readout_mean"):
        torch.testing.assert_close(together[k], acc_sum[k], rtol=1e-5, atol=1e-6)
    assert record["n_rows"] == 3 and len(record["m_clean"]) == 3 and len(record["m_twin"]) == 3


# ==============================================================================
# ACTIVATION CONTRAST AGAINST NUMPY
# ==============================================================================

def test_activation_contrast_matches_numpy(tiny):
    rows = _random_rows(5, 13, seed=8, span=(2, 6))
    rows[3].span = None                     # the Readout-only fallback row
    scores, record = na.score_rows(tiny, rows, batch_size=2)
    assert record["n_clause_rows"] == 4 and record["clause_fallback_ids"] == ["validation/r3"]
    diffs_ro, twins_ro, diffs_cl, twins_cl = [], [], [], []
    for r in rows:
        batch = na.collate([r])
        c = np.stack([a[0].numpy() for a in _activations(tiny, batch.input_ids, batch.attention_mask)])
        t = np.stack([a[0].numpy() for a in _activations(tiny, batch.twin_input_ids, batch.attention_mask)])
        diffs_ro.append(c[:, r.readout] - t[:, r.readout])
        twins_ro.append(t[:, r.readout])
        if r.span is not None:
            s = slice(*r.span)
            diffs_cl.append((c[:, s] - t[:, s]).sum(1))
            twins_cl.append(t[:, s].sum(1))
    d_ro, t_ro = np.stack(diffs_ro), np.stack(twins_ro)
    d_cl, t_cl = np.stack(diffs_cl), np.stack(twins_cl)
    np.testing.assert_allclose(scores["contrast_readout_mean"].numpy(), d_ro.mean(0), rtol=1e-4, atol=1e-6)
    np.testing.assert_allclose(scores["contrast_readout_std"].numpy(), d_ro.mean(0) / (t_ro.std(0) + 1e-6),
                               rtol=1e-3, atol=1e-4)
    np.testing.assert_allclose(scores["contrast_clause_mean"].numpy(), d_cl.mean(0), rtol=1e-4, atol=1e-6)
    np.testing.assert_allclose(scores["contrast_clause_std"].numpy(), d_cl.mean(0) / (t_cl.std(0) + 1e-6),
                               rtol=1e-3, atol=1e-4)


# ==============================================================================
# OUTPUT FILES
# ==============================================================================

EXPECTED_KEYS = {"atp_readout_mean", "atp_readout_absmean", "atp_clause_mean", "atp_clause_absmean",
                 "contrast_readout_mean", "contrast_readout_std", "contrast_clause_mean", "contrast_clause_std"}


def test_outputs_have_the_expected_keys_and_shapes(tiny, tmp_path):
    import run_manifest as rm
    rows = _random_rows(4, 12, seed=9, pad_tail=2)
    scores, record = na.score_rows(tiny, rows, batch_size=4)
    out = str(tmp_path / "cell")
    paths = na.write_outputs(out, scores, record, reports=[{"split": "validation"}], pools={"clean": {}})
    manifest_path = na.write_manifest(out, notes=["unmerged Codex pool: test"], script=cli.__file__,
                                      argv=["x"], dataset_files={"a": "b"}, model="tiny", seed=None)
    saved = torch.load(paths["scores"])
    assert set(saved) == EXPECTED_KEYS
    for v in saved.values():
        assert v.dtype == torch.float32 and tuple(v.shape) == (2, 128)
        assert torch.isfinite(v).all()
    with open(paths["rows"]) as handle:
        rows_json = json.load(handle)
    for key in ("ids", "m_clean", "m_twin", "n_rows", "baseline", "seconds_per_row", "pools", "loader_reports"):
        assert key in rows_json
    assert rows_json["n_rows"] == 4 and len(rows_json["ids"]) == 4
    with open(manifest_path) as handle:
        manifest = json.load(handle)
    assert manifest["notes"] == ["unmerged Codex pool: test"]
    assert manifest["dataset_files"] == {"a": "b"}
    assert rm.verify_manifest_hash(manifest)
    again = na.write_manifest(out, notes=["different"], script=cli.__file__, argv=["x"], dataset_files={},
                              model="tiny", seed=None)
    assert os.path.basename(again) == "run_manifest.1.json"   # never overwrites


def test_reverse_adds_its_keys(tiny):
    scores, _ = na.score_rows(tiny, _random_rows(2, 10, seed=10), batch_size=2, reverse=True)
    assert set(scores) == EXPECTED_KEYS | {"rev_atp_readout_mean", "rev_atp_readout_absmean",
                                           "rev_atp_clause_mean", "rev_atp_clause_absmean"}


def test_baseline_summary():
    record = {"m_clean": [1.0, 2.0, -1.0], "m_twin": [-3.0, -2.0, 0.5], "ref_m_clean": [1.1, 2.0, -0.9],
              "ref_m_twin": [None, None, None]}
    out = na.baseline_summary(record)
    assert out["m_clean"]["frac_gt_0"] == pytest.approx(2 / 3)
    assert out["m_clean"]["frac_gt_0.7"] == pytest.approx(2 / 3)
    assert out["m_clean"]["vs_stored_margin"]["sign_agreement"] == 1.0
    assert "vs_stored_margin" not in out["m_twin"]


# ==============================================================================
# THE REAL PAIRS AND THE CLI
# ==============================================================================

@pytest.mark.skipif(not HAVE_FAR, reason="far_v2 datasets not built")
def test_dh_pairs_on_far_v2(tok):
    rows, report = na.dh_pairs(os.path.join(DATA, "far_v2"), tok, split="validation")
    assert report.n_rows == len(rows) > 0
    for r in rows[:20]:
        assert r.readout == int(r.attention_mask.sum()) - 1
        start, end = r.span
        assert 0 < start < end <= r.readout
        differing = torch.nonzero(r.input_ids != r.twin_input_ids).flatten().tolist()
        assert differing and all(start <= p < end for p in differing)
        assert r.ref_m_clean is not None and r.ref_m_twin is not None


@pytest.mark.skipif(not HAVE_POOL, reason="specificity-ladder user-turn pools not present")
def test_in_pairs_on_the_user_turn_pools(tok):
    rows, report = na.in_pairs(POOL_I, POOL_N, tok, split="validation")
    assert report.n_split == 177 and report.n_rows == len(rows) > 0
    assert not report.without_twin
    for r in rows[:20]:
        assert r.span is not None and r.readout == int(r.attention_mask.sum()) - 1
        differing = torch.nonzero(r.input_ids != r.twin_input_ids).flatten().tolist()
        assert differing and all(r.span[0] <= p < r.span[1] for p in differing)
        assert r.ref_m_clean is not None and r.ref_m_twin is not None


def test_splits_outside_ranking_are_refused():
    assert cli.splits_of("train,validation") == ["train", "validation"]
    with pytest.raises(SystemExit):
        cli.splits_of("validation,test")


def test_head_commit_reads_the_git_files():
    commit = cli.head_commit()
    if commit is None:
        pytest.skip("no readable .git here")
    assert len(commit) == 40 and all(c in "0123456789abcdef" for c in commit)


@pytest.mark.skipif(not (HAVE_FAR and HAVE_POOL), reason="datasets not present")
def test_cli_end_to_end_on_the_tiny_model(tok, tiny, tmp_path, monkeypatch, capsys):
    import models
    monkeypatch.setattr(models.ModelAdapter, "load_full_model", lambda self, device: tiny)
    code = cli.main(["--pair", "dh", "in", "--split", "validation", "--limit", "3", "--batch-size", "2",
                     "--device", "cpu", "--output-root", str(tmp_path), "--commit", "abcdef0123"])
    assert code == 0
    for pair in ("dh", "in"):
        cell = tmp_path / f"far_v2_{pair}_validation_abcdef0_limit3"
        saved = torch.load(str(cell / "scores.pt"))
        assert set(saved) == EXPECTED_KEYS
        assert all(tuple(v.shape) == (2, 128) for v in saved.values())
        rows_json = json.loads((cell / "rows.json").read_text())
        assert rows_json["n_rows"] == 3 and rows_json["pair"] == pair
        manifest = json.loads((cell / "run_manifest.json").read_text())
        assert manifest["dataset_files"]
        if pair == "in":
            assert any(na.UNMERGED_NOTE in note for note in manifest["notes"])
            assert rows_json["pools"]["clean"]["note"] == na.UNMERGED_NOTE
    assert "seconds per row" in capsys.readouterr().out


@pytest.mark.skipif(not (HAVE_FAR and HAVE_POOL), reason="datasets not present")
def test_cli_dry_run_loads_no_model(tok, tmp_path, monkeypatch, capsys):
    import models

    def boom(self, device):
        raise AssertionError("the dry run loaded a model")
    monkeypatch.setattr(models.ModelAdapter, "load_full_model", boom)
    assert cli.main(["--pair", "dh", "in", "--dry-run", "--output-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "dry run: no model loaded" in out and "[dh]" in out and "[in]" in out


# ==============================================================================
# POOL CHECKS AND THE R2 ORIENTATION
# ==============================================================================

@pytest.mark.skipif(not HAVE_POOL, reason="specificity-ladder user-turn pools not present")
def test_the_pool_arrows_match_the_reader_brief():
    for directory in (POOL_I, POOL_N):
        checked = na.verify_pool_arrows(directory, ("train", "validation", "test"))
        assert all(entry["ok"] is True for entry in checked.values())


def test_a_pool_copy_with_a_wrong_arrow_is_refused(tmp_path):
    split = tmp_path / "far_v2_user_inversion" / "train"
    split.mkdir(parents=True)
    (split / "data-00000-of-00001.arrow").write_bytes(b"not the pool")
    with pytest.raises(ValueError, match="sha256"):
        na.verify_pool_arrows(str(tmp_path / "far_v2_user_inversion"), ("train",))
    unknown = tmp_path / "other_pool" / "train"
    unknown.mkdir(parents=True)
    (unknown / "data-00000-of-00001.arrow").write_bytes(b"x")
    assert na.verify_pool_arrows(str(tmp_path / "other_pool"), ("train",))["train"]["ok"] is None


@pytest.mark.skipif(not (HAVE_FAR and HAVE_POOL), reason="datasets not present")
@pytest.mark.parametrize("split", ["train", "validation"])
def test_i_and_n_are_scored_with_d_labels(tok, split):
    """Ruling R2: m = logit(opposite) - logit(honest) in D's orientation on every stream. D's Target is the
    deceptive (opposite) answer, and the I/N rows are scored with the I row's labels, which must equal D's."""
    d_rows, _ = na.dh_pairs(os.path.join(DATA, "far_v2"), tok, split=split)
    d_labels = {r.id: (r.target, r.distractor) for r in d_rows}
    i_rows, _ = na.in_pairs(POOL_I, POOL_N, tok, split=split)
    assert len(i_rows) == 177
    assert all(d_labels[r.id] == (r.target, r.distractor) for r in i_rows)


@pytest.mark.skipif(not (HAVE_FAR and HAVE_POOL), reason="datasets not present")
def test_cli_pool_dir_reads_the_pools_from_there(tok, tmp_path, monkeypatch, capsys):
    import shutil
    pools = tmp_path / "pools"
    for directory in (POOL_I, POOL_N):
        shutil.copytree(directory, str(pools / os.path.basename(directory)))
    assert cli.main(["--pair", "in", "--split", "validation", "--dry-run", "--pool-dir", str(pools),
                     "--output-root", str(tmp_path / "out")]) == 0
    assert str(pools / "far_v2_user_inversion") in capsys.readouterr().out


# ==============================================================================
# THE --ids FILTER (split halves for N3)
# ==============================================================================

RANK_IDS = os.path.join(REPO, "outputs", "_analyses", "neuron-partition", "data", "far_rank_ids.json")
HAVE_RANK_IDS = os.path.exists(RANK_IDS)


def test_load_id_list_reads_a_dotted_key_and_refuses_bad_ones(tmp_path):
    path = tmp_path / "ids.json"
    path.write_text(json.dumps({"halves": {"A": ["a", "b"], "n": 3, "dup": ["a", "a"]}, "flat": ["x"]}))
    assert cli.load_id_list(str(path), "halves.A") == ["a", "b"]
    assert cli.load_id_list(str(path), "flat") == ["x"]
    for bad in ("halves.C", "halves.n", "halves.dup", "halves.A.x"):
        with pytest.raises(SystemExit):
            cli.load_id_list(str(path), bad)


def test_filter_rows_keeps_listed_ids_in_row_order():
    rows = _random_rows(4, 8, seed=11)
    kept, report = cli.filter_rows(rows, ["r3", "r1", "zz"])
    assert [r.id for r in kept] == ["r1", "r3"]
    assert report == {"n_wanted": 3, "n_matched": 2, "n_wanted_not_in_pool": 1}


@pytest.mark.skipif(not (HAVE_FAR and HAVE_POOL and HAVE_RANK_IDS), reason="datasets or W3's id file not present")
def test_the_halves_split_both_pairs_by_the_same_ids(tok):
    """halves.A and halves.B are D ids over train+validation; the same lists, matched by id on the I/N pool, give
    exactly W3's I_A and I_B."""
    with open(RANK_IDS) as handle:
        halves = json.load(handle)["halves"]
    parser = cli.build_parser()
    for half, i_key in (("A", "I_A"), ("B", "I_B")):
        args = parser.parse_args(["--pair", "dh", "in", "--ids", RANK_IDS, "--ids-key", f"halves.{half}"])
        dh, dh_reports, _ = cli.load_rows(args, "dh", ["train", "validation"], tok)
        inv, in_reports, _ = cli.load_rows(args, "in", ["train", "validation"], tok)
        assert len(dh) == len(halves[half]) == 200
        assert {r.id for r in dh} == set(halves[half])
        assert {r.id for r in inv} == set(halves[i_key])
        assert dh_reports[-1]["id_filter"]["n_wanted_not_in_pool"] == 0
        assert in_reports[-1]["id_filter"]["n_matched"] == len(halves[i_key])
    assert not set(halves["A"]) & set(halves["B"])


@pytest.mark.skipif(not (HAVE_FAR and HAVE_POOL), reason="datasets not present")
def test_cli_ids_and_tag_end_to_end_on_the_tiny_model(tok, tiny, tmp_path, monkeypatch):
    import models
    monkeypatch.setattr(models.ModelAdapter, "load_full_model", lambda self, device: tiny)
    d_rows, _ = na.dh_pairs(os.path.join(DATA, "far_v2"), tok, split="validation")
    i_rows, _ = na.in_pairs(POOL_I, POOL_N, tok, split="validation")
    i_ids = {x.id for x in i_rows}
    shared = [r.id for r in d_rows if r.id in i_ids][:2]
    extra = d_rows[-1].id
    ids = tmp_path / "ids.json"
    ids.write_text(json.dumps({"halves": {"A": shared + [extra]}}))
    code = cli.main(["--pair", "dh", "in", "--split", "validation", "--batch-size", "2", "--device", "cpu",
                     "--ids", str(ids), "--ids-key", "halves.A", "--tag", "half1",
                     "--output-root", str(tmp_path / "out"), "--commit", "abcdef0123"])
    assert code == 0
    for pair in ("dh", "in"):
        cell = tmp_path / "out" / f"far_v2_{pair}_validation_half1_abcdef0"
        rows_json = json.loads((cell / "rows.json").read_text())
        expected = 3 if pair == "dh" else 2 + (extra in i_ids)
        assert rows_json["n_rows"] == expected
        assert {i.split("/", 1)[1] for i in rows_json["ids"]} <= set(shared + [extra])
        assert rows_json["loader_reports"][-1]["id_filter"]["key"] == "halves.A"
        manifest = json.loads((cell / "run_manifest.json").read_text())
        assert any(k.endswith("ids.json") for k in manifest["dataset_files"])
