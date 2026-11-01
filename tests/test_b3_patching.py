"""B3 ticket T6: patching, nulls, bootstrap and the `scripts/b3_patch.py` entrypoint.

Pure parts (masks, f and its CI, the ported nulls, flip reversal, the sycophancy pass bar, the R5 labels, the compact
proxy readout and the dry run) run on both interpreters. The interchange invariants need a real forward through the
2-layer random Llama under nnsight 0.7.0 and skip elsewhere, as `tests/test_knockout_model.py` does.
"""
from __future__ import annotations

import importlib.util
import json
import math
import random
import re
from pathlib import Path

import numpy as np
import pytest

from spontaneous import patching, stats

ROOT = Path(__file__).resolve().parents[1]
P1C_DIR = Path("/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_launch_mechanism_analysis")


def _load_source(name):
    path = P1C_DIR / f"{name}.py"
    if not path.is_file():
        pytest.skip(f"{path} is not present; the port cannot be compared with its source")
    spec = importlib.util.spec_from_file_location(f"_p1c_source_{name}", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ==============================================================================
# stats: the ports
# ==============================================================================

def _sets():
    from spontaneous.sets import load_sets
    return load_sets()


@pytest.mark.parametrize("seed", [0, 20261025, 20261025 + 1000, 12345])
def test_layer_matched_nulls_equal_the_source_draws_per_seed(seed):
    src = _load_source("p1c_groups")
    sets = _sets()
    for name in ("S_all", "S_far", "S_ser", "S_q", "gupta6"):
        S = sets[name]
        assert stats.layer_matched_nulls(S, n=20, seed=seed) == src.layer_matched_nulls(S, n=20, seed=seed), name


def test_the_null_constants_equal_the_source():
    src = _load_source("p1c_groups")
    assert stats.ALL == src.ALL
    assert stats.POSITIVE_CONTROL == src.POSITIVE_CONTROL
    assert stats.NULL_SEED == src.NULL_SEED and stats.N_NULL == src.N_NULL


def test_null_draws_are_layer_matched_and_fix_the_mlp_part():
    S = _sets()["S_all"]
    want = sorted((k, layer) for k, layer, _ in S)
    mlps = sorted(k for k in S if k[0] == "mlp")
    for draw in stats.layer_matched_nulls(S, n=20, seed=3):
        assert sorted((k, layer) for k, layer, _ in draw) == want
        assert len(set(draw)) == len(draw)
        assert sorted(k for k in draw if k[0] == "mlp") == mlps     # one MLP per layer: fixed


def test_heads_only_nulls_draw_heads_only_with_the_heads_layer_counts():
    S = _sets()["S_all"]
    heads = [k for k in S if k[0] == "head"]
    draws = stats.heads_only_nulls(S, n=20, seed=5)
    assert draws == stats.layer_matched_nulls(heads, n=20, seed=5)
    for draw in draws:
        assert all(k[0] == "head" for k in draw)
        assert sorted(layer for _, layer, _ in draw) == sorted(layer for _, layer, _ in heads)


def test_f_boot_and_instance_boot_equal_the_source():
    src = _load_source("p1c_results")
    rng = np.random.default_rng(7)
    C, K, T = rng.normal(3, 1, 40), rng.normal(1.5, 1, 40), rng.normal(0, 1, 40)
    for seed in (0, 1, 99):
        idx = stats.instance_boot(40, n_boot=500, seed=seed)
        assert np.array_equal(idx, src.instance_boot(40, n_boot=500, seed=seed))
        assert np.array_equal(stats.f_boot(C, K, T, idx), src.f_boot(C, K, T, idx))
        assert stats.ci(stats.f_boot(C, K, T, idx)) == src.ci(src.f_boot(C, K, T, idx))
    assert stats.mediated_fraction(C, K, T) == pytest.approx(src.mediated_fraction(C, K, T), abs=1e-12)


# ==============================================================================
# patching: f, CI, flips, bars, verdicts
# ==============================================================================

def test_f_is_one_when_patched_equals_twin_and_zero_when_it_equals_clean():
    rng = np.random.default_rng(0)
    clean, twin = rng.normal(2, 0.5, 30), rng.normal(-1, 0.5, 30)
    one = patching.f_summary(clean, twin, twin, n_boot=200, seed=0)
    zero = patching.f_summary(clean, clean, twin, n_boot=200, seed=0)
    assert one["f"] == pytest.approx(1.0) and one["ci"][0] == pytest.approx(1.0) and one["ci"][1] == pytest.approx(1.0)
    assert zero["f"] == pytest.approx(0.0) and zero["ci"] == (pytest.approx(0.0), pytest.approx(0.0))


def test_f_is_a_ratio_of_means_with_a_seeded_bootstrap_ci():
    clean = np.array([4.0, 2.0, 3.0, 5.0])
    patched = np.array([2.0, 2.0, 1.0, 3.0])
    twin = np.array([0.0, 1.0, 1.0, 2.0])
    out = patching.f_summary(clean, patched, twin, n_boot=300, seed=4)
    assert out["f"] == pytest.approx((3.5 - 2.0) / (3.5 - 1.0))
    assert out["per_item"] == pytest.approx([0.5, 0.0, 1.0, 2 / 3])
    again = patching.f_summary(clean, patched, twin, n_boot=300, seed=4)
    assert out["ci"] == again["ci"]
    lo, hi = out["ci"]
    assert lo <= out["f"] <= hi
    # the CI is the ported bootstrap on the ported index matrix
    idx = stats.instance_boot(4, n_boot=300, seed=4)
    assert out["ci"] == stats.ci(stats.f_boot(clean, patched, twin, idx))


def test_gap_summary_flags_a_gap_whose_ci_is_clear_of_zero():
    clean = np.array([2.0, 2.5, 3.0, 2.2, 2.8])
    twin = clean - np.array([1.0, 1.2, 0.9, 1.1, 1.0])
    g = patching.gap_summary(clean, twin, n_boot=500, seed=0)
    assert g["gap"] == pytest.approx(1.04)
    assert g["measurable"] is True and g["ci"][0] > 0
    flat = patching.gap_summary(clean, clean + np.array([0.5, -0.5, 0.4, -0.4, 0.0]), n_boot=500, seed=0)
    assert flat["measurable"] is False


def test_flip_table_and_reversal_count_on_a_hand_built_table():
    #             item:   0    1    2    3    4    5
    gold = np.array([0, 1, 2, 3, 0, 1])
    cue = np.array([1, 2, 3, 0, 2, 0])
    uncued = np.array([0, 1, 2, 0, 0, 1])     # item 3 answered wrong without the cue -> not kept
    cued = np.array([1, 2, 2, 0, 2, 1])       # flips: 0, 1, 4 (kept and answered the cue); item 2, 5 stay gold
    table = patching.flip_table(gold, cue, uncued, cued)
    assert table["kept"].tolist() == [True, True, True, False, True, True]
    assert table["flip"].tolist() == [True, True, False, False, True, False]
    patched = np.array([0, 2, 2, 0, 0, 1])    # flips 0 and 4 return to gold, flip 1 stays on the cue
    rev = patching.flip_reversal(table, gold, patched)
    assert rev == {"n_flips": 3, "n_reversed": 2, "share": pytest.approx(2 / 3)}


def test_flip_reversal_with_no_flips_is_none():
    table = {"kept": np.array([True]), "flip": np.array([False])}
    assert patching.flip_reversal(table, np.array([0]), np.array([0]))["share"] is None


def test_sycophancy_pass_bar_at_and_just_below_0_18():
    nulls = [0.05] * 20
    assert patching.syc_pass_bar(0.18, nulls)["pass"] is True
    assert patching.syc_pass_bar(0.18 - 1e-9, nulls)["pass"] is False
    assert patching.syc_pass_bar(9 / 50, nulls)["pass"] is True          # exactly 0.18 as a count ratio
    out = patching.syc_pass_bar(0.40, nulls[:19] + [0.40])                 # a null ties: not beaten
    assert out["pass"] is False and out["beats_all_nulls"] is False and out["meets_bar"] is True
    assert patching.syc_pass_bar(0.40, nulls[:19] + [0.41])["pass"] is False
    assert patching.syc_pass_bar(0.40, [])["pass"] is False                # no nulls run: cannot pass


@pytest.mark.parametrize("f,band", [(0.50, "shared"), (0.75, "shared"), (0.4999, "partial"), (0.25, "partial"),
                                    (0.2499, "divergent"), (-0.3, "divergent")])
def test_r5_bands(f, band):
    v = patching.transfer_verdict(f, [0.1] * 20, gap_measurable=True)
    assert v["band"] == band
    assert v["label"] == band
    assert "F-mech-003" in v["caveat"]


def test_r5_non_specific_label_when_a_null_reaches_0_5():
    v = patching.transfer_verdict(0.8, [0.1] * 19 + [0.5], gap_measurable=True)
    assert v["band"] == "shared" and v["non_specific"] is True and v["label"] == "shared, non-specific"
    v = patching.transfer_verdict(0.8, [0.1] * 19 + [0.4999], gap_measurable=True)
    assert v["non_specific"] is False and v["label"] == "shared"
    v = patching.transfer_verdict(0.3, [0.9] * 20, gap_measurable=True)      # the qualifier is on shared only
    assert v["label"] == "partial" and v["non_specific"] is False


def test_r5_unmeasurable_gap_gives_no_band():
    v = patching.transfer_verdict(0.9, [0.1] * 20, gap_measurable=False)
    assert v["band"] is None and v["label"] == "gap not measurable at the Readout"


def test_r5_cue_following_qualifiers():
    base = dict(gap_measurable=True, gap=2.0)
    v = patching.transfer_verdict(0.6, [0.1] * 20, controls={"delta_c1": 0.9, "delta_c2": -0.1}, **base)
    assert v["cue_following"] == "monitoring-contingent"
    v = patching.transfer_verdict(0.6, [0.1] * 20, controls={"delta_c1": 1.0, "delta_c2": -0.1}, **base)
    assert v["cue_following"] == "cue-following not excluded"           # 1.0 is not < 0.5 * 2.0
    v = patching.transfer_verdict(0.6, [0.1] * 20, controls={"delta_c1": 0.1, "delta_c2": 0.0}, **base)
    assert v["cue_following"] == "cue-following not excluded"
    v = patching.transfer_verdict(0.6, [0.1] * 20, **base)
    assert v["cue_following"] == "not computed"
    v = patching.transfer_verdict(0.6, [0.1] * 20, controls={"f_c3": 0.5}, **base)
    assert v["generic_tier_cue_routing"] is True
    v = patching.transfer_verdict(0.6, [0.1] * 20, controls={"f_c3": 0.49}, **base)
    assert v["generic_tier_cue_routing"] is False
    v = patching.transfer_verdict(0.3, [0.1] * 20, controls={"f_c3": 0.9}, **base)
    assert v["generic_tier_cue_routing"] is None                          # only qualifies a shared verdict


# ==============================================================================
# patching: masks and the compact proxy readout (torch, no model)
# ==============================================================================

def test_post_tag_mask_starts_at_the_tag_token_and_ends_at_the_readout():
    torch = pytest.importorskip("torch")
    free = [[1, 2, 3, 50, 5, 6, 7], [1, 2, 60, 4, 5]]
    paid = [[1, 2, 3, 51, 5, 6, 7], [1, 2, 61, 4, 5]]
    starts = [patching.first_difference(a, b) for a, b in zip(free, paid)]
    assert starts == [3, 2]
    ids, mask, readout = patching.right_pad(free)
    assert readout.tolist() == [6, 4] and ids.shape == (2, 7)
    m = patching.arm_mask("post_tag", starts, readout, ids.shape[1])
    assert m.dtype == torch.bool
    assert m[0].tolist() == [False, False, False, True, True, True, True]
    assert m[1].tolist() == [False, False, True, True, True, False, False]  # never past the Readout (padding)
    r = patching.arm_mask("readout", starts, readout, ids.shape[1])
    assert r[0].nonzero().flatten().tolist() == [6] and r[1].nonzero().flatten().tolist() == [4]


def test_first_difference_refuses_unequal_or_identical_twins():
    with pytest.raises(ValueError):
        patching.first_difference([1, 2, 3], [1, 2])
    with pytest.raises(ValueError):
        patching.first_difference([1, 2, 3], [1, 2, 3])


def _toy_resolved():
    from spontaneous.proxy import ResolvedTokens
    return ResolvedTokens(opener_id=5, r1_ids=frozenset({5, 7, 8}), continuation_paths=((5, 9), (5, 10, 11)),
                          stem_paths=((), (5,), (5, 10)))


def test_compact_proxy_readout_equals_the_full_vocabulary_margins():
    torch = pytest.importorskip("torch")
    from spontaneous import proxy
    res = _toy_resolved()
    compact = patching.CompactProxy.for_af(res)
    rng = np.random.default_rng(1)
    for _ in range(5):
        full = {p: rng.normal(0, 2, 40) for p in res.stem_paths}
        small = {p: compact.reduce(torch.tensor(full[p], dtype=torch.float32)[None])[0] for p in res.stem_paths}
        assert compact.p1(small[()]) == pytest.approx(proxy.p1_margin(full[()], res.r1_ids), abs=1e-5)
        assert compact.p2(small) == pytest.approx(proxy.p2_margin(full, res), abs=1e-5)


def test_c3_bullet_margin_is_log_bullet_minus_log_rest():
    torch = pytest.importorskip("torch")
    compact = patching.CompactProxy.for_bullets([3, 4])
    v = np.log(np.array([0.1, 0.2, 0.3, 0.25, 0.15]))
    small = compact.reduce(torch.tensor(v, dtype=torch.float32)[None])[0]
    assert compact.bullet(small) == pytest.approx(math.log(0.4) - math.log(0.6), abs=1e-6)


# ==============================================================================
# The interchange on the tiny Llama (nnsight 0.7.0 only)
# ==============================================================================

def _nnsight_pinned():
    try:
        import nnsight
    except Exception:                                       # noqa: BLE001
        return False
    return nnsight.__version__ == "0.7.0"


needs_model = pytest.mark.skipif(not _nnsight_pinned(), reason="needs nnsight 0.7.0 (mgnp)")


@pytest.fixture(scope="module")
def tiny():
    import torch
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    from tests.helpers import tiny_config

    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())


def _tiny_twins(seq=10, batch=3, tag=3):
    import torch
    torch.manual_seed(2)
    free = torch.randint(0, 101, (batch, seq))
    paid = free.clone()
    paid[:, tag] = (free[:, tag] + 7) % 101
    rows_free = [free[0].tolist(), free[1].tolist(), free[2, :seq - 2].tolist()]   # one shorter row: right padding
    rows_paid = [paid[0].tolist(), paid[1].tolist(), paid[2, :seq - 2].tolist()]
    return rows_free, rows_paid


def _all_components():
    from tests.helpers import TINY
    return ([("head", layer, h) for layer in range(TINY["layers"]) for h in range(TINY["heads"])]
            + [("mlp", layer, 0) for layer in range(TINY["layers"])])


@needs_model
def test_the_empty_set_gives_the_clean_run_bit_identically(tiny):
    import torch
    free, paid = _tiny_twins()
    out = patching.twin_interchange(tiny, free, paid, {"empty@post_tag": ([], "post_tag")})
    assert torch.equal(out.patched["empty@post_tag"], out.clean)
    assert not torch.equal(out.clean, out.twin)


@needs_model
@pytest.mark.parametrize("arm", ["post_tag", "readout"])
def test_all_heads_and_mlps_give_the_twin_margin(tiny, arm):
    free, paid = _tiny_twins()
    out = patching.twin_interchange(tiny, free, paid, {"all": (_all_components(), arm)})
    m = lambda x: (x[:, 5] - x[:, 8]).cpu().numpy()                 # noqa: E731
    assert np.allclose(m(out.patched["all"]), m(out.twin), atol=1e-3)
    assert np.abs(m(out.clean) - m(out.twin)).max() > 1e-3          # the twin is not the clean run


@needs_model
def test_twin_interchange_writes_the_twin_value_only_from_the_tag(tiny):
    """A patch from a position after the tag differs from a patch at all positions only through the tag position,
    so writing every position from the tag equals writing every position (positions before it are identical)."""
    import torch
    from component_analysis import hooks
    free, paid = _tiny_twins()
    keys = [("head", 1, 2), ("mlp", 0, 0)]
    out = patching.twin_interchange(tiny, free, paid, {"s": (keys, "post_tag")})
    ids, mask, readout = patching.right_pad(free)
    tids, tmask, _ = patching.right_pad(paid)
    cap = hooks.capture_forward(tiny, tids, tmask, components=keys, positions=readout)
    ref = hooks.capture_forward(tiny, ids, mask, components=[], positions=readout,
                                replacements={k: cap.outputs[k] for k in keys})
    expect = hooks.readout_logits(tiny, ref.residual[:, -1, :])
    assert torch.allclose(out.patched["s"], expect, atol=1e-5)


@needs_model
def test_twin_interchange_reduces_each_run(tiny):
    free, paid = _tiny_twins()
    out = patching.twin_interchange(tiny, free, paid, {"s": ([("head", 0, 1)], "readout")},
                                    reduce=lambda logits: logits[:, :4])
    assert tuple(out.clean.shape) == (3, 4) and tuple(out.patched["s"].shape) == (3, 4)


# ==============================================================================
# The entrypoint
# ==============================================================================

def _script():
    spec = importlib.util.spec_from_file_location("b3_patch_script", str(ROOT / "scripts" / "b3_patch.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _WordTok:
    """Word tokenizer: "(" and apostrophe suffixes are their own tokens, everything else splits on whitespace. A tier
    twin differs at one token, "I'm not able" opens with "I", and an option letter follows the prefill's "(" as one
    token, so the real proxy, twin and letter checks run on it."""

    PATTERN = re.compile(r"\(|'\w+|[^\s(']+")

    def __init__(self):
        self.vocab = {}

    def encode(self, text, add_special_tokens=False):
        return [self.vocab.setdefault(w, len(self.vocab) + 1) for w in self.PATTERN.findall(text)]


@pytest.fixture
def no_model(monkeypatch):
    from component_analysis import hooks

    def boom(*a, **k):
        raise AssertionError("--dry-run loaded a model")
    monkeypatch.setattr(hooks, "load_analysis_model", boom)


@pytest.mark.parametrize("argv", [
    ["--task", "af", "--variant", "V-B", "--proxy", "P2", "--positions", "post_tag,readout"],
    ["--task", "af", "--variant", "V-A", "--proxy", "P1"],
    ["--task", "syc"],
    ["--task", "c3", "--variant", "V-A"],
])
def test_dry_run_loads_no_model_and_prints_counts(argv, no_model, monkeypatch, capsys, tmp_path):
    mod = _script()
    monkeypatch.setattr(mod, "load_tokenizer", lambda model: _WordTok())
    assert mod.main(argv + ["--dry-run", "--out", str(tmp_path / "o")]) == 0
    out = capsys.readouterr().out
    assert "forwards" in out and "walltime" in out
    assert not (tmp_path / "o" / "results.json").exists()


def test_dry_run_forward_count_for_af_p2():
    mod = _script()
    n = mod.count_forwards(n_rows=100, n_stems=6, n_sets=6, n_null=20, n_positions=2)
    assert n == 100 * 6 * (2 + 2 * 6 * 21)


def test_af_needs_a_proxy_and_a_variant(no_model, monkeypatch, tmp_path):
    mod = _script()
    monkeypatch.setattr(mod, "load_tokenizer", lambda model: _WordTok())
    with pytest.raises(SystemExit):
        mod.main(["--task", "af", "--variant", "V-A", "--dry-run", "--out", str(tmp_path)])
    with pytest.raises(SystemExit):
        mod.main(["--task", "af", "--proxy", "P1", "--dry-run", "--out", str(tmp_path)])


def test_unknown_set_is_refused(no_model, monkeypatch, tmp_path):
    mod = _script()
    with pytest.raises(SystemExit):
        mod.main(["--task", "syc", "--sets", "S_nope", "--dry-run", "--out", str(tmp_path)])


def test_set_resolution_and_null_seeds_are_stable():
    mod = _script()
    sets = mod.resolve_sets(["S_all", "heads_only", "gupta6", "L17H24"])
    assert len(sets["S_all"]["members"]) == 35
    assert all(k[0] == "head" for k in sets["heads_only"]["members"]) and len(sets["heads_only"]["members"]) == 32
    assert sets["heads_only"]["null_kind"] == "heads_only"
    assert sets["L17H24"]["members"] == [("head", 17, 24)]
    again = mod.resolve_sets(["L17H24", "gupta6", "heads_only", "S_all"])
    for name in sets:
        assert sets[name]["null_seed"] == again[name]["null_seed"]
        assert mod.null_draws(sets[name], 20) == mod.null_draws(again[name], 20)


def test_discovery_is_a_stub():
    with pytest.raises(NotImplementedError, match="3.5"):
        patching.discovery()


def test_dry_run_with_the_cached_tokenizer_for_v_b_p2(no_model, capsys, tmp_path):
    from spontaneous import af_prompts
    try:
        af_prompts.load_cached_tokenizer()
    except Exception as e:                                  # noqa: BLE001
        pytest.skip(f"Llama-3.1 tokenizer not cached: {e}")
    mod = _script()
    assert mod.main(["--task", "af", "--variant", "V-B", "--proxy", "P2", "--dry-run", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "100 twin pairs" in out and "stems 6" in out


# ------------------------------------------------------------------ end to end on the tiny Llama

TINY_SETS = {"S_all": [("head", 1, 2), ("mlp", 0, 0)], "gupta6": [("head", 0, 1), ("head", 1, 3)]}


@pytest.fixture
def tiny_script(monkeypatch, tmp_path):
    """The script with the tiny Llama (vocabulary widened for the word tokenizer) and sets the tiny model has."""
    import torch
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    from tests.helpers import tiny_config

    config = tiny_config(attn_implementation="sdpa")
    config.vocab_size = 4096
    torch.manual_seed(0)
    model = NNsight(LlamaForCausalLM(config).eval())
    mod = _script()
    tok = _WordTok()
    monkeypatch.setattr(mod, "load_tokenizer", lambda name: tok)
    monkeypatch.setattr(mod, "load_model", lambda args: model)

    def sets(names):
        return {n: {"members": TINY_SETS[n], "null_seed": 1 + i, "null_kind": "layer_matched"}
                for i, n in enumerate(names)}

    def draws(spec, n):
        rng = random.Random(spec["null_seed"])
        return [[("head", layer, rng.randrange(4)) for _k, layer, _i in spec["members"]] for _ in range(n)]
    monkeypatch.setattr(mod, "resolve_sets", sets)
    monkeypatch.setattr(mod, "null_draws", draws)
    return mod


@needs_model
def test_af_run_end_to_end_writes_margins_results_and_a_manifest(tiny_script, tmp_path, monkeypatch):
    import run_manifest
    from spontaneous import proxy
    # conftest disables the commit fingerprint; a fake bounded call shows the script records the 40-hex commit
    monkeypatch.delenv(run_manifest.GIT_ENV_FLAG, raising=False)
    monkeypatch.setattr(run_manifest, "_run_git",
                        lambda args, cwd: b"0123456789abcdef0123456789abcdef01234567\n" if args[0] == "rev-parse"
                        else b"")
    tokens = proxy.load_proxy_tokens().with_r1(["Sorry", "Unfortunately"])
    tpath = tmp_path / "tokens.json"
    proxy.write_proxy_tokens(tokens, tpath)
    rows = json.loads((ROOT / "data" / "b3" / "af_queries.json").read_text())["test"][:3]
    rpath = tmp_path / "rows.json"
    rpath.write_text(json.dumps([r["id"] for r in rows]))
    out = tmp_path / "af"
    assert tiny_script.main(["--task", "af", "--variant", "V-A", "--proxy", "P2", "--sets", "S_all", "--null", "2",
                             "--positions", "post_tag,readout", "--rows", str(rpath), "--tokens", str(tpath),
                             "--n-boot", "50", "--device", "cpu", "--out", str(out)]) == 0
    res = json.loads((out / "results.json").read_text())
    mar = json.loads((out / "margins.json").read_text())
    assert mar["margins"]["ids"] == [r["id"] for r in rows]
    assert set(mar["margins"]["arms"]) == {"S_all@post_tag", "S_all@post_tag#null00", "S_all@post_tag#null01",
                                           "S_all@readout", "S_all@readout#null00", "S_all@readout#null01"}
    assert len(mar["margins"]["clean"]) == 3
    assert res["nulls"]["S_all@post_tag"]["n"] == 2
    assert "label" in res["transfer_verdict"] and "F-mech-003" in res["transfer_verdict"]["caveat"]
    man = json.loads((out / "run_manifest.json").read_text())
    assert re.fullmatch(r"[0-9a-f]{40}", man["git_commit"] or "")
    assert man["script"] == "b3_patch.py" and str(rpath) in man["dataset_files"]


@needs_model
def test_af_margins_match_a_direct_p2_readout(tiny_script, tmp_path):
    """The clean margin of a row equals P2 read from six direct forwards of the free prompt plus each stem."""
    import torch
    from component_analysis import hooks
    from spontaneous import af_prompts, proxy
    tok = tiny_script.load_tokenizer(None)
    model = tiny_script.load_model(None)
    tokens = proxy.load_proxy_tokens().with_r1(["Sorry"])
    res = proxy.resolve_tokens(tokens, tok)
    q = json.loads((ROOT / "data" / "b3" / "af_queries.json").read_text())["test"][0]["prompt"]
    pair = af_prompts.build_af_pair(tok, q, "V-A")
    compact = patching.CompactProxy.for_af(res)
    run = patching.run_af(model, [pair], {}, compact, readout="P2", stems=res.stem_paths)
    direct = {}
    for s in res.stem_paths:
        ids = torch.tensor([list(pair.free_ids) + list(s)])
        cap = hooks.capture_forward(model, ids, torch.ones_like(ids), components=[])
        direct[s] = hooks.readout_logits(model, cap.residual[:, -1, :])[0]
    assert run["clean"][0] == pytest.approx(proxy.p2_margin(direct, res), abs=1e-4)


@needs_model
def test_syc_run_end_to_end_reports_the_pass_bar(tiny_script, tmp_path):
    items = json.loads((ROOT / "data" / "b3" / "syc_items.json").read_text())["items"][:6]
    rpath = tmp_path / "rows.json"
    rpath.write_text(json.dumps({"items": items}))
    out = tmp_path / "syc"
    assert tiny_script.main(["--task", "syc", "--sets", "gupta6,S_all", "--null", "3", "--rows", str(rpath),
                             "--n-boot", "50", "--device", "cpu", "--out", str(out)]) == 0
    res = json.loads((out / "results.json").read_text())
    assert res["n_items"] == 6
    assert set(res["reversal"]) >= {"gupta6@readout", "S_all@readout"}
    assert "pass" in res["pass_bar"]
    if res["n_kept"]:
        assert res["pass_bar"]["n_null"] == 3
