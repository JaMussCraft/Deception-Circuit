"""D4(b): the `after_cue` positions arm of `spontaneous/patching.py` (positions strictly after the cue window through
the Readout) and its exposure in `scripts/b3_patch.py`. The pure parts run on both interpreters; the interchange
check needs the 2-layer random Llama under nnsight 0.7.0, as `tests/test_b3_patching.py` does."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from spontaneous import patching

ROOT = Path(__file__).resolve().parents[1]

# A synthetic sycophancy-style pair: identical prefix, a three-token cue window (positions 3 to 5) where the twins
# differ at the first and last token but agree in the middle, then an identical suffix through the Readout.
CUED = [[1, 2, 3, 40, 9, 42, 7, 8, 10], [1, 2, 50, 4, 52, 6, 7]]
UNCUED = [[1, 2, 3, 41, 9, 43, 7, 8, 10], [1, 2, 51, 4, 53, 6, 7]]


def test_after_cue_is_appended_and_the_existing_arms_keep_their_names():
    assert patching.POSITION_ARMS[:2] == ("post_tag", "readout")
    assert "after_cue" in patching.POSITION_ARMS


def test_last_difference_is_one_past_the_last_differing_token():
    assert [patching.last_difference(a, b) for a, b in zip(CUED, UNCUED)] == [6, 5]
    with pytest.raises(ValueError):
        patching.last_difference([1, 2], [1, 2, 3])
    with pytest.raises(ValueError):
        patching.last_difference([1, 2, 3], [1, 2, 3])


def test_after_cue_mask_covers_exactly_the_positions_after_the_window_through_the_readout():
    torch = pytest.importorskip("torch")
    starts = [patching.first_difference(a, b) for a, b in zip(CUED, UNCUED)]
    ends = [patching.last_difference(a, b) for a, b in zip(CUED, UNCUED)]
    ids, _mask, readout = patching.right_pad(CUED)
    assert starts == [3, 2] and readout.tolist() == [8, 6]
    after = patching.arm_mask("after_cue", starts, readout, ids.shape[1], ends=ends)
    assert after.dtype == torch.bool
    assert after[0].nonzero().flatten().tolist() == [6, 7, 8]
    assert after[1].nonzero().flatten().tolist() == [5, 6]          # never past the Readout (padding)
    post = patching.arm_mask("post_tag", starts, readout, ids.shape[1])
    # post_tag is the cue window plus after_cue, and the two never overlap
    window = post & ~after
    assert window[0].nonzero().flatten().tolist() == [3, 4, 5]
    assert window[1].nonzero().flatten().tolist() == [2, 3, 4]
    assert not bool((after & ~post).any())
    # every after_cue position is token-identical in the twins; every cue-window edge differs
    for row, (a, b) in enumerate(zip(CUED, UNCUED)):
        assert all(a[i] == b[i] for i in after[row].nonzero().flatten().tolist())
        assert a[starts[row]] != b[starts[row]] and a[ends[row] - 1] != b[ends[row] - 1]


def test_existing_arms_ignore_ends_and_are_unchanged():
    pytest.importorskip("torch")
    starts = [3, 2]
    _ids, _m, readout = patching.right_pad(CUED)
    for arm in ("post_tag", "readout"):
        a = patching.arm_mask(arm, starts, readout, 9)
        b = patching.arm_mask(arm, starts, readout, 9, ends=[6, 5])
        assert bool((a == b).all())


def test_after_cue_refuses_missing_ends_an_empty_tail_and_a_window_that_does_not_open():
    pytest.importorskip("torch")
    _ids, _m, readout = patching.right_pad(CUED)
    with pytest.raises(ValueError, match="needs the cue window ends"):
        patching.arm_mask("after_cue", [3, 2], readout, 9)
    with pytest.raises(ValueError, match="no position after the cue window"):
        patching.arm_mask("after_cue", [3, 2], readout, 9, ends=[9, 5])
    with pytest.raises(ValueError, match="at or before it starts"):
        patching.arm_mask("after_cue", [3, 2], readout, 9, ends=[3, 5])


def test_the_real_sycophancy_pairs_carry_a_cue_window_that_ends_before_the_readout():
    """`SycPair.cue_end` is what run_syc passes; on the committed items with a word tokenizer it closes the window."""
    from spontaneous import af_prompts

    class WordTok:
        def __init__(self):
            self.vocab = {}

        def encode(self, text, add_special_tokens=False):
            return [self.vocab.setdefault(w, len(self.vocab) + 1) for w in text.replace("(", " ( ").split()]

    items = json.loads((ROOT / "data" / "b3" / "syc_items.json").read_text())["items"][:20]
    pairs, _dropped = af_prompts.build_syc_pairs(WordTok(), items)
    assert pairs
    for p in pairs:
        assert p.cue_start < p.cue_end < len(p.cued_ids)
        assert p.cue_end == patching.last_difference(p.cued_ids, p.uncued_ids)


# ------------------------------------------------------------------------------ the entrypoint


def _script():
    spec = importlib.util.spec_from_file_location("b3_patch_script_d4", str(ROOT / "scripts" / "b3_patch.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_b3_patch_accepts_after_cue_and_still_refuses_an_unknown_arm(tmp_path):
    mod = _script()
    args = mod.parse_args(["--task", "syc", "--positions", "after_cue", "--out", str(tmp_path)])
    assert args.position_arms == ["after_cue"]
    with pytest.raises(SystemExit):
        mod.parse_args(["--task", "syc", "--positions", "after_tag", "--out", str(tmp_path)])
    assert mod.DEFAULT_POSITIONS == {"af": "post_tag", "syc": "readout", "c3": "post_tag"}


# ------------------------------------------------------------------------------ the interchange (nnsight 0.7.0)


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


@needs_model
def test_twin_interchange_after_cue_writes_the_twin_value_only_after_the_window(tiny):
    import torch
    from component_analysis import hooks

    keys = [("head", 1, 2), ("mlp", 0, 0)]
    out = patching.twin_interchange(tiny, CUED, UNCUED, {"s": (keys, "after_cue")})
    ids, mask, readout = patching.right_pad(CUED)
    tids, tmask, _ = patching.right_pad(UNCUED)
    starts = [patching.first_difference(a, b) for a, b in zip(CUED, UNCUED)]
    ends = [patching.last_difference(a, b) for a, b in zip(CUED, UNCUED)]
    where = patching.arm_mask("after_cue", starts, readout, ids.shape[1], ends=ends)
    cap = hooks.capture_forward(tiny, tids, tmask, components=keys, positions=readout)
    ref = hooks.capture_forward(tiny, ids, mask, components=[], positions=readout,
                                replacements={k: hooks.Replacement(cap.outputs[k], positions=where) for k in keys})
    expect = hooks.readout_logits(tiny, ref.residual[:, -1, :])
    assert torch.allclose(out.patched["s"], expect, atol=1e-5)
    # explicit ends equal the default
    again = patching.twin_interchange(tiny, CUED, UNCUED, {"s": (keys, "after_cue")}, ends=ends)
    assert torch.allclose(again.patched["s"], out.patched["s"])
    # and the arm differs from post_tag, which also writes the cue window
    post = patching.twin_interchange(tiny, CUED, UNCUED, {"s": (keys, "post_tag")})
    assert not torch.allclose(post.patched["s"], out.patched["s"])


# The B3 entrypoint with the tiny Llama and the tiny sets (the fixture of tests/test_b3_patching.py).
from tests.test_b3_patching import tiny_script  # noqa: E402, F401


@needs_model
def test_syc_run_end_to_end_with_after_cue_writes_the_arm_and_its_nulls(tiny_script, tmp_path):
    """main -> build_pairs -> run_syc (ends = cue_end) -> syc_results, on six committed items."""
    items = json.loads((ROOT / "data" / "b3" / "syc_items.json").read_text())["items"][:6]
    rpath = tmp_path / "rows.json"
    rpath.write_text(json.dumps({"items": items}))
    out = tmp_path / "syc"
    assert tiny_script.main(["--task", "syc", "--sets", "S_all", "--null", "2", "--positions", "after_cue,readout",
                             "--rows", str(rpath), "--n-boot", "50", "--device", "cpu", "--out", str(out)]) == 0
    res = json.loads((out / "results.json").read_text())
    assert res["positions"] == ["after_cue", "readout"]
    assert res["n_items"] == 6
    assert {"S_all@after_cue", "S_all@readout"} <= set(res["reversal"])
    assert len(res["nulls"]["S_all@after_cue"]["reversal"]) == 2
    if res["n_kept"]:
        assert "S_all@after_cue" in res["f"]
