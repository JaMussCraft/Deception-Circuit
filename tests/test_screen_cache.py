"""tests/test_screen_cache.py — the on-disk screen cache.

The cache exists to stop every sbatch job repaying ~79% of EVAL 5's cost. That
makes its failure mode *silence*: a key that is too loose reuses a screen the
current configuration would not have produced, and nothing anywhere says so —
the run just reports someone else's evaluation set as its own.

So most of what is tested here is the key, one field at a time.
"""

import json
import os

import pytest
import torch

import evaluation.benchmark_eval as B
from evaluation import screen_cache
from evaluation.benchmarks import base

from tests.test_benchmark_eval import (FakeBench, _even_are_deceptive,
                                       make_cli, make_ctx, make_items)


def cache_cli(tmp_path, **overrides):
    overrides.setdefault("benchmark_screen_cache", str(tmp_path / "screens"))
    overrides.setdefault("no_benchmark_screen_cache", False)
    return make_cli(**overrides)


def a_key(cli, bench=None, items=None, device="TEST-GPU"):
    bench = bench or FakeBench(make_items(6), _even_are_deceptive)
    items = make_items(6) if items is None else items
    return screen_cache.build_key(cli, "fake", bench, items, "llama-tiny",
                                  device=device)


# ==============================================================================
# THE KEY
# ==============================================================================

@pytest.mark.parametrize("flag,value", [
    ("benchmark_n_per_dataset", 99),
    ("benchmark_new_tokens", 77),
    ("benchmark_belief_tokens", 11),
    ("benchmark_ref_pool", "pooled"),
    ("benchmark_screen_seed", 12345),
    ("benchmark_screen_budget", 400),
    ("benchmark_gen_batch_size", 32),
    ("benchmark_repo_root", "/somewhere/else"),
    ("no_kv_cache", True),
    ("wikitext_seed", 7),
    ("mask_judge_model", "gpt-4o-mini"),
    ("mask_numeric_judge_model", "gpt-4o"),
    ("lb_judge_model", "claude-x"),
    ("lb_harm_judge_model", "claude-y"),
])
def test_every_keyed_flag_changes_the_hash(tmp_path, flag, value):
    """One parametrisation per keyed flag.

    A mutant that drops any single field from `KEYED_FLAGS` dies exactly here,
    which is the point: the list is the whole correctness argument for the
    cache, and a reviewer cannot check it by reading `run_screen`.
    """
    base_cli = cache_cli(tmp_path)
    assert getattr(base_cli, flag) != value, (
        "%s's fixture default already equals the mutated value, so this "
        "parametrisation would pass no matter what the key contained" % flag)
    other = cache_cli(tmp_path, **{flag: value})
    assert screen_cache.key_hash(a_key(base_cli)) != \
        screen_cache.key_hash(a_key(other))


def test_the_device_is_part_of_the_key(tmp_path):
    """`full` reuses the screen's own tokens, so mixing devices would put the
    GPU inside the delta EVAL 5 measures."""
    cli = cache_cli(tmp_path)
    assert screen_cache.key_hash(a_key(cli, device="NVIDIA A40")) != \
        screen_cache.key_hash(a_key(cli, device="NVIDIA H200"))


def test_the_model_is_part_of_the_key(tmp_path):
    cli = cache_cli(tmp_path)
    bench = FakeBench(make_items(6), _even_are_deceptive)
    one = screen_cache.build_key(cli, "fake", bench, make_items(6), "llama-8b",
                                 device="G")
    two = screen_cache.build_key(cli, "fake", bench, make_items(6), "gemma-9b",
                                 device="G")
    assert screen_cache.key_hash(one) != screen_cache.key_hash(two)


def test_the_dataset_is_part_of_the_key(tmp_path):
    cli = cache_cli(tmp_path)
    bench = FakeBench(make_items(6), _even_are_deceptive)
    one = screen_cache.build_key(cli, "mask:known_facts", bench, make_items(6),
                                 "m", device="G")
    two = screen_cache.build_key(cli, "mask:statistics", bench, make_items(6),
                                 "m", device="G")
    assert screen_cache.key_hash(one) != screen_cache.key_hash(two)


def test_changed_prompt_text_changes_the_key_even_with_the_same_ids(tmp_path):
    """Ids alone would miss an edited prompt template: same rows, same hash,
    and the cached screen would be prompts the adapter no longer produces."""
    cli = cache_cli(tmp_path)
    items = make_items(6)
    edited = [i.replace(messages=[{"role": "user", "content": "rewritten"}])
              for i in items]
    assert [i.item_id for i in items] == [i.item_id for i in edited]
    assert screen_cache.key_hash(a_key(cli, items=items)) != \
        screen_cache.key_hash(a_key(cli, items=edited))


def test_a_changed_condition_changes_the_key(tmp_path):
    cli = cache_cli(tmp_path)
    items = make_items(6, condition=base.HONEST)
    flipped = [i.replace(condition=base.DECEPTIVE) for i in items]
    assert screen_cache.key_hash(a_key(cli, items=items)) != \
        screen_cache.key_hash(a_key(cli, items=flipped))


def test_two_adapters_do_not_share_a_source_fingerprint():
    """A rubric change relabels the same generations, and no data hash sees it,
    so the adapter's source stands in for its parse and judge rules."""
    from evaluation.benchmarks import get_benchmark

    one = screen_cache._source_fingerprint(get_benchmark("sandbagging"))
    two = screen_cache._source_fingerprint(get_benchmark("mask:known_facts"))
    assert one != two


# ==============================================================================
# ROUND TRIP
# ==============================================================================

def test_a_saved_screen_comes_back_field_for_field(tmp_path):
    """Round-tripped through the real `run_screen`, not a hand-built Screen:
    a stub would not notice a field that pickles badly."""
    cli = cache_cli(tmp_path, benchmark_n_per_dataset=3)
    ctx = make_ctx(cli)
    bench = FakeBench(make_items(20), _even_are_deceptive)
    from evaluation.benchmarks.judge import JudgeClient
    screen = B.run_screen(ctx, bench, JudgeClient(cache_path=None,
                                                  verbose=False), "fake")

    key = a_key(cli)
    assert screen_cache.save(cli, "fake", key, screen)["saved"] is True
    back, provenance = screen_cache.load(cli, "fake", key)

    assert provenance["hit"] is True
    assert [i.item_id for i in back.items] == [i.item_id for i in screen.items]
    assert back.prompts == screen.prompts
    assert back.pairing == screen.pairing
    assert back.partner_index == screen.partner_index
    assert back.stats == screen.stats
    assert torch.equal(back.full_ids, screen.full_ids)
    assert torch.equal(back.clean_ids, screen.clean_ids)
    assert torch.equal(back.clean_mask, screen.clean_mask)
    assert back.pool_refs == screen.pool_refs
    assert [r["label"] for r in back.full_rows] == \
        [r["label"] for r in screen.full_rows]


def test_saving_leaves_no_temporary_file_behind(tmp_path):
    cli = cache_cli(tmp_path)
    key = a_key(cli)
    screen_cache.save(cli, "fake", key, B.Screen("fake"))
    directory = screen_cache.cache_dir_for(cli, "fake")
    assert not [n for n in os.listdir(directory) if ".tmp" in n]


def test_the_sidecar_records_the_key_and_the_hardware(tmp_path):
    cli = cache_cli(tmp_path)
    key = a_key(cli)
    screen_cache.save(cli, "fake", key, B.Screen("fake"))
    _, sidecar = screen_cache.paths_for(cli, "fake", key)
    with open(sidecar) as handle:
        side = json.load(handle)
    assert side["benchmark_gen_batch_size"] == cli.benchmark_gen_batch_size
    assert "torch" in side["_stamp"] and "device" in side["_stamp"]
    assert side["_created_at"]


# ==============================================================================
# MISSES, AND FAILING SAFE
# ==============================================================================

def test_a_screen_from_another_device_is_a_miss(tmp_path):
    cli = cache_cli(tmp_path)
    screen_cache.save(cli, "fake", a_key(cli, device="NVIDIA A40"),
                      B.Screen("fake"))
    back, provenance = screen_cache.load(cli, "fake",
                                         a_key(cli, device="NVIDIA H200"))
    assert back is None and provenance["hit"] is False


def test_a_dry_run_key_with_no_device_can_never_hit(tmp_path):
    """A login node has no GPU, so it cannot verify a hit and must not claim
    one — an estimate that assumes a hit that does not happen is exactly how a
    job gets killed at the walltime."""
    cli = cache_cli(tmp_path)
    screen_cache.save(cli, "fake", a_key(cli, device="NVIDIA A40"),
                      B.Screen("fake"))
    back, _ = screen_cache.load(cli, "fake", a_key(cli, device=None))
    assert back is None


def test_a_dry_run_can_still_see_what_is_cached_and_on_what(tmp_path):
    cli = cache_cli(tmp_path)
    screen_cache.save(cli, "fake", a_key(cli, device="NVIDIA A40"),
                      B.Screen("fake"))
    devices = screen_cache.cached_on_devices(cli, "fake",
                                             a_key(cli, device=None))
    assert devices == ["NVIDIA A40"]


def test_a_configuration_change_is_not_reported_as_merely_a_device_change(
        tmp_path):
    cli = cache_cli(tmp_path)
    screen_cache.save(cli, "fake", a_key(cli, device="NVIDIA A40"),
                      B.Screen("fake"))
    other = cache_cli(tmp_path, benchmark_gen_batch_size=32)
    assert screen_cache.cached_on_devices(other, "fake",
                                          a_key(other, device=None)) == []
    near = screen_cache.describe_misses(other, "fake", a_key(other))
    assert "benchmark_gen_batch_size" in near[0]["differs"]


def test_a_corrupt_cache_file_is_a_miss_not_a_crash(tmp_path):
    cli = cache_cli(tmp_path)
    key = a_key(cli)
    path, _ = screen_cache.paths_for(cli, "fake", key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(b"not a torch file")
    back, provenance = screen_cache.load(cli, "fake", key)
    assert back is None
    assert "unreadable" in provenance["reason"]


def test_a_file_whose_stored_key_disagrees_is_a_miss(tmp_path):
    """Trust the stored key, never the filename: a hash collision or a version
    whose key fields differed must not be read as a hit."""
    cli = cache_cli(tmp_path)
    key = a_key(cli)
    path, _ = screen_cache.paths_for(cli, "fake", key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save({"key": dict(key, benchmark_new_tokens=-1),
                "screen": B.Screen("fake")}, path)
    back, provenance = screen_cache.load(cli, "fake", key)
    assert back is None and provenance["reason"] == "key mismatch"


def test_a_save_that_fails_warns_and_does_not_raise(tmp_path, capsys):
    """A cache is an optimisation. A save bug at hour three must not kill a job
    whose results were about to be written."""
    cli = cache_cli(tmp_path)
    key = a_key(cli)

    class Unpicklable:
        def __reduce__(self):
            raise RuntimeError("nope")

    screen = B.Screen("fake")
    screen.items = [Unpicklable()]
    result = screen_cache.save(cli, "fake", key, screen)
    assert result["saved"] is False and "nope" in result["error"]
    assert "WARNING" in capsys.readouterr().out
    directory = screen_cache.cache_dir_for(cli, "fake")
    assert not [n for n in os.listdir(directory) if ".tmp" in n]


# ==============================================================================
# THE WIRING: cached_screen
# ==============================================================================

class _Spy:
    """Counts real screening passes."""

    def __init__(self, monkeypatch):
        self.calls = 0
        real = B.run_screen

        def counted(ctx, bench, client, dataset):
            self.calls += 1
            return real(ctx, bench, client, dataset)

        monkeypatch.setattr(B, "run_screen", counted)


def _cached_screen(ctx, bench, dataset="fake"):
    from evaluation.benchmarks.judge import JudgeClient
    return B.cached_screen(ctx, bench, JudgeClient(cache_path=None,
                                                   verbose=False), dataset)


def test_a_second_run_reuses_the_screen_instead_of_regenerating_it(
        tmp_path, monkeypatch):
    spy = _Spy(monkeypatch)
    cli = cache_cli(tmp_path, benchmark_n_per_dataset=3)
    bench = FakeBench(make_items(20), _even_are_deceptive)

    first = _cached_screen(make_ctx(cli), bench)
    assert spy.calls == 1
    assert first.cache_provenance["written"]["saved"] is True

    # A *fresh* ctx, so the Session memo cannot be what serves this.
    second = _cached_screen(make_ctx(cli), bench)
    assert spy.calls == 1, "the second run screened again"
    assert second.cache_provenance["hit"] is True
    assert [i.item_id for i in second.items] == [i.item_id for i in first.items]
    assert torch.equal(second.full_ids, first.full_ids)


def test_refresh_screens_again_and_overwrites(tmp_path, monkeypatch):
    spy = _Spy(monkeypatch)
    cli = cache_cli(tmp_path, benchmark_n_per_dataset=3)
    bench = FakeBench(make_items(20), _even_are_deceptive)
    _cached_screen(make_ctx(cli), bench)

    refresh = cache_cli(tmp_path, benchmark_n_per_dataset=3,
                        benchmark_refresh_screen=True)
    screen = _cached_screen(make_ctx(refresh), bench)
    assert spy.calls == 2
    assert screen.cache_provenance["hit"] is False
    assert screen.cache_provenance["written"]["saved"] is True


def test_the_cache_can_be_turned_off_entirely(tmp_path, monkeypatch):
    spy = _Spy(monkeypatch)
    cli = cache_cli(tmp_path, benchmark_n_per_dataset=3,
                    no_benchmark_screen_cache=True)
    bench = FakeBench(make_items(20), _even_are_deceptive)
    _cached_screen(make_ctx(cli), bench)
    _cached_screen(make_ctx(cli), bench)
    assert spy.calls == 2
    assert not os.path.exists(str(tmp_path / "screens"))


def test_a_changed_target_does_not_reuse_the_smaller_screen(tmp_path,
                                                            monkeypatch):
    """The failure this whole file exists to prevent: silently evaluating on
    someone else's evaluation set."""
    spy = _Spy(monkeypatch)
    bench = FakeBench(make_items(20), _even_are_deceptive)
    small = _cached_screen(make_ctx(cache_cli(tmp_path,
                                              benchmark_n_per_dataset=2)),
                           bench)
    large = _cached_screen(make_ctx(cache_cli(tmp_path,
                                              benchmark_n_per_dataset=4)),
                           bench)
    assert spy.calls == 2
    assert len(small.items) == 2 and len(large.items) == 4
