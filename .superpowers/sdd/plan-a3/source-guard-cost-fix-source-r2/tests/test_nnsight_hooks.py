"""
The nnsight facts the component analyses are built on, on the tiny model.

Everything here describes nnsight 0.7.0, which is the version ADR-0001 pins and
which lives in the `mgnp` environment. The module skips wholesale anywhere
else, and "anywhere else" is not hypothetical: the login-node base env carries
an nnsight 0.5.12 for the parent Alignment repo, so gating on "nnsight
imports" would run 0.7.0 assertions against 0.5.12 and report the wrong
version as a broken hook. The gate is the version itself.

The assertions are the same ones `scripts/smoke_nnsight.py` makes by hand —
they live here as well so that an nnsight or transformers upgrade that moves a
module boundary fails the suite rather than a GPU job three tickets later.

Tests are deliberately at the same seam the hook module will use: module
boundaries on the unmodified `LlamaForCausalLM`, never the prunable wrapper
(ADR-0001).
"""

from __future__ import annotations

import pytest

nnsight = pytest.importorskip("nnsight")
PINNED = "0.7.0"
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}; these are 0.7.0 behaviours.",
                allow_module_level=True)

from types import SimpleNamespace                         # noqa: E402

import torch                                              # noqa: E402

from scripts import smoke_nnsight                         # noqa: E402
from tests.helpers import TINY, tiny_config               # noqa: E402

SEQ = smoke_nnsight.SEQ


@pytest.fixture(scope="module")
def input_ids():
    torch.manual_seed(1)
    return torch.randint(0, TINY["vocab"], (2, SEQ))


def test_nnsight_is_the_pinned_version_over_the_repos_transformers():
    smoke_nnsight.check_versions()


def test_tracing_reproduces_a_plain_forward(input_ids):
    smoke_nnsight.check_trace_matches_a_plain_forward(
        smoke_nnsight.build_tiny(), input_ids)


def test_every_sender_and_receiver_boundary_is_reachable(input_ids):
    smoke_nnsight.check_module_boundaries(smoke_nnsight.build_tiny(), input_ids)


def test_attention_weights_arrive_only_under_eager_attention(input_ids):
    smoke_nnsight.check_attention_weights_need_eager(input_ids)


def test_envoy_accesses_must_be_written_in_execution_order(input_ids):
    """Out-of-order access silently drops a module from the trace.

    This is the failure mode later tickets are most likely to hit, and its
    error message names the module that *was* asked for rather than the one
    that came too early, so it is pinned here as behaviour.
    """
    from nnsight import NNsight

    traced = NNsight(smoke_nnsight.build_tiny())
    with pytest.raises(Exception, match="was not provided"):
        with traced.trace(input_ids):
            traced.model.layers[0].self_attn.o_proj.input.save()
            traced.model.layers[0].self_attn.q_proj.output.save()


# ==============================================================================
# load_analysis_model
# ==============================================================================

def fake_hf_loaders(monkeypatch) -> dict:
    """Record what the HuggingFace loaders receive, and load nothing real.

    nnsight reaches `AutoConfig`, `AutoTokenizer` and `AutoModelForCausalLM`
    through the transformers classes themselves, so replacing their
    `from_pretrained` runs `LanguageModel.__init__` end to end without a repo,
    a network or weights. The tiny random Llama stands in for the real model so
    that nnsight's own wrapping is exercised rather than skipped.

    Returns {"config" | "tokenizer" | "model": the kwargs that loader saw}.
    """
    import transformers

    seen = {}

    def load_config(repo_id, **kwargs):
        seen["config"] = kwargs
        return tiny_config()

    def load_tokenizer(repo_id, **kwargs):
        kwargs.pop("config", None)
        seen["tokenizer"] = kwargs
        return SimpleNamespace(pad_token="<pad>", eos_token="<eos>")

    def load_model(repo_id, **kwargs):
        seen["model"] = kwargs
        return smoke_nnsight.build_tiny()

    monkeypatch.setattr(transformers.AutoConfig, "from_pretrained", load_config)
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained",
                        load_tokenizer)
    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained",
                        load_model)
    return seen


def test_the_hf_token_reaches_the_tokenizer_and_not_only_the_weights(monkeypatch):
    """A gated repo needs the token twice, and nnsight keeps the two apart.

    `LanguageModel._load` forwards `**kwargs` to the config and to the model,
    but loads the tokenizer from a separate `tokenizer_kwargs` that defaults to
    empty. A token passed only in `**kwargs` therefore loads the weights of a
    gated repo and then fails on the tokenizer with a 401 that names the
    tokenizer rather than the token.
    """
    from component_analysis.hooks import load_analysis_model

    seen = fake_hf_loaders(monkeypatch)

    load_analysis_model("some-org/some-gated-llama", device="cpu",
                        hf_token="hf_a_test_token")

    assert seen["tokenizer"].get("token") == "hf_a_test_token"
    assert seen["model"].get("token") == "hf_a_test_token"


def test_no_hf_token_means_no_token_kwarg_anywhere(monkeypatch):
    """An ungated repo, or a cached login, must not be handed a null token."""
    from component_analysis.hooks import load_analysis_model

    seen = fake_hf_loaders(monkeypatch)

    load_analysis_model("some-org/some-open-llama", device="cpu")

    assert "token" not in seen["tokenizer"]
    assert "token" not in seen["model"]
