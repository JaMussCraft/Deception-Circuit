"""D4(a): `--attention-instances causal_sample` points the pressure and neutral-twin attention conditions at the
cell's causal sample (`--n-causal`, `--include-ids`) instead of the whole test split; the default is unchanged."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

from component_analysis import attention_patterns as ap      # noqa: E402
from component_analysis import head_table as ht              # noqa: E402


def test_the_default_is_the_whole_split_and_the_choice_is_validated():
    import argparse

    parser = argparse.ArgumentParser()
    ap.add_arguments(parser.add_argument_group("attention"))
    assert parser.parse_args([]).attention_instances == ap.INSTANCES_SPLIT
    assert parser.parse_args(["--attention-instances", "causal_sample"]).attention_instances == ap.INSTANCES_SAMPLE
    with pytest.raises(SystemExit):
        parser.parse_args(["--attention-instances", "sample"])


class _Ctx:
    def __init__(self, instances):
        self.cli = SimpleNamespace(attention_instances=instances)
        self.calls = []

    def causal_batches(self):
        self.calls.append("causal")
        return SimpleNamespace(report={"n_with_neutral_twin": 3})

    def descriptive_batches(self):
        self.calls.append("descriptive")
        return "descriptive"

    def neutral_twin_batches(self):
        self.calls.append("neutral_twin")
        return SimpleNamespace(report={"n_with_neutral_twin": 1000})


def test_the_loaders_follow_the_flag():
    split = _Ctx(None)
    assert ap.instances_of(split) == ap.INSTANCES_SPLIT
    assert ap.pressure_batches(split) == "descriptive"
    batches, reason = ap.neutral_twin_batches(split)
    assert reason is None and batches.report["n_with_neutral_twin"] == 1000
    assert split.calls == ["descriptive", "neutral_twin"]

    sample = _Ctx("causal_sample")
    ap.pressure_batches(sample)
    batches, reason = ap.neutral_twin_batches(sample)
    assert reason is None and batches.report["n_with_neutral_twin"] == 3
    assert sample.calls == ["causal", "causal"]


def test_coverage_labels_name_the_causal_sample_only_off_the_default():
    assert ap._instance_set(ap.PRESSURE) == ht.TEST_SPLIT
    assert ap._instance_set(ap.NEUTRAL_TWIN) == ht.PAIRED_NEUTRAL_TWIN
    assert ap._instance_set(ap.PRESSURE, ap.INSTANCES_SAMPLE) == ht.CAUSAL_SAMPLE
    for name in (ap.NEUTRAL_TWIN, ap.PRESSURE_NEUTRAL_TWIN_PAIRED):
        assert ap._instance_set(name, ap.INSTANCES_SAMPLE) == ht.CAUSAL_SAMPLE_NEUTRAL_TWIN
    assert ap._instance_set(ap.HONEST_INSTRUCTION, ap.INSTANCES_SAMPLE) == ht.PAIRED_HONEST_INSTRUCTION


# ==============================================================================
# The CLI on a real v2 cell, tiny model (nnsight 0.7.0), as test_attention_patterns_neutral_twin.py
# ==============================================================================

def _nnsight_pinned():
    try:
        import nnsight
    except Exception:                                       # noqa: BLE001
        return False
    return nnsight.__version__ == "0.7.0"


needs_model = pytest.mark.skipif(not _nnsight_pinned(), reason="attention weights are a nnsight 0.7.0 behaviour")

import analyze_components                                          # noqa: E402
from component_analysis import registry                            # noqa: E402
from tests.helpers import tiny_config                              # noqa: E402
from tests.test_component_analysis_v2_cli import (                 # noqa: E402, F401
    cell, read, real_tokenizer, run_cli, v2_run)

N_CAUSAL = 8


@pytest.fixture
def tiny_llama(monkeypatch, real_tokenizer):
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    config = tiny_config(attn_implementation="sdpa")
    config.vocab_size = len(real_tokenizer)
    torch.manual_seed(0)
    wrapped = NNsight(LlamaForCausalLM(config).eval())
    monkeypatch.setattr(analyze_components, "load_model", lambda cli, resolved: wrapped)
    monkeypatch.setattr(registry, "ANALYSES", [ap])
    return wrapped


def _common(run_dir, out, *extra):
    return [str(run_dir), "--num-kv-heads", "2", "--device", "cpu", "--n-causal",
            str(N_CAUSAL), "--output-dir", str(out), *extra]


@needs_model
def test_causal_sample_profiles_pressure_and_both_twin_sides_on_the_sample_ids(v2_run, tiny_llama):
    run_dir, out = v2_run()
    assert run_cli(*_common(run_dir, out, "--attention-conditions", "pressure,neutral_twin",
                            "--attention-instances", "causal_sample")) == 0
    payload = read(os.path.join(cell(out), ap.SUBDIR), ap.PATTERNS_FILE)
    assert payload["instances"] == ap.INSTANCES_SAMPLE
    sample = read(cell(out), "sample.json")
    sample_ids = [str(one) for one in sample["instance_ids"]]
    assert len(sample_ids) == N_CAUSAL
    conditions = {one["name"]: one for one in payload["conditions"]}
    assert set(conditions) == {ap.PRESSURE, ap.PRESSURE_NEUTRAL_TWIN_PAIRED, ap.NEUTRAL_TWIN}
    for name in conditions:
        assert conditions[name]["n_loaded"] == N_CAUSAL
        assert sorted(conditions[name]["instance_ids"]) == sorted(sample_ids)
    left, right = conditions[ap.PRESSURE_NEUTRAL_TWIN_PAIRED], conditions[ap.NEUTRAL_TWIN]
    assert left["instance_ids"] == right["instance_ids"]
    assert right["alignment"]["n_pairs"] == N_CAUSAL
    assert right["alignment"]["n_differing_outside_the_clause"] == 0
    assert right["b2"]["n"] == N_CAUSAL
    table = read(cell(out), "head_table.json")
    entry = ht.coverage_of(table["meta"], "attention_patterns.clause_mass_drop_neutral_twin_paired")
    assert entry["n"] == N_CAUSAL and entry["instance_set"].startswith(ht.CAUSAL_SAMPLE_NEUTRAL_TWIN)
    entry = ht.coverage_of(table["meta"], "attention_patterns.pressure_top_mass")
    assert entry["n"] == N_CAUSAL and entry["instance_set"].startswith(ht.CAUSAL_SAMPLE)


@needs_model
def test_the_default_still_reads_the_whole_split_and_writes_no_instances_key(v2_run, tiny_llama):
    run_dir, out = v2_run()
    assert run_cli(*_common(run_dir, out, "--attention-conditions", "neutral_twin")) == 0
    payload = read(os.path.join(cell(out), ap.SUBDIR), ap.PATTERNS_FILE)
    assert "instances" not in payload
    twin = {one["name"]: one for one in payload["conditions"]}[ap.NEUTRAL_TWIN]
    assert twin["n_loaded"] == 1000
