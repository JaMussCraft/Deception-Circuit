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
    ("no_kv_cache", True),
    ("wikitext_seed", 7),
    ("lb_belief_templates", 2),
    ("benchmark_pool_size", 25),
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
    # Any of them, not near[0]: `describe_misses` reports the directory in
    # name order, so asserting on the first entry would depend on how the hash
    # happened to sort against whatever else is cached alongside it.
    near = screen_cache.describe_misses(other, "fake", a_key(other))
    assert any("benchmark_gen_batch_size" in n["differs"] for n in near)


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


# ==============================================================================
# WHAT THE ESTIMATE CHARGES FOR A SCREEN
# ==============================================================================

def test_a_memoised_stage_is_not_charged_once_per_cell():
    """`Session.screen_for` computes a dataset's screen once per process, and
    the disk cache now makes even that once per *campaign*. Charging it per
    cell overstated a 3x3 suite by eight extra screens — on the eleven-dataset
    configuration that is a claim of ~700 GPU-hours that do not exist."""
    import evaluate_circuit as E

    stages = E.scale_stages([("per cell", 10.0),
                             ("screen", 100.0, 50.0, True)], n_cells=9)
    assert stages[0] == ("per cell", 90.0, 90.0)
    assert stages[1] == ("screen", 100.0, 50.0)


def test_a_stage_without_a_floor_is_equally_expensive_either_way():
    import evaluate_circuit as E

    assert E.scale_stages([("flat", 7.0)], n_cells=3) == [("flat", 21.0, 21.0)]


def test_the_screen_belief_and_pool_stages_are_the_once_per_process_ones(
        monkeypatch):
    """Guards the marking itself: dropping the `True` from any of THREE stages
    silently restores the per-cell overcharge.

    The adapter is injected rather than named, for two reasons. A real MASK
    split does not override `belief_request`, so `_probe_count` returns 0 and
    no belief stage is emitted at all — an earlier version of this test named
    one and therefore guarded only two of the three markers while claiming to
    guard all three. And naming a Liars' Bench scenario instead would put a
    HuggingFace download inside a unit test.
    """
    import evaluate_circuit as E

    class Believer(FakeBench):
        def __init__(self):
            super().__init__(make_items(30), _even_are_deceptive)
            self.name = "believer"

        def belief_request(self, item):
            return [{"name": "p1", "messages": item.messages},
                    {"name": "p2", "messages": item.messages}]

    bench = Believer()
    monkeypatch.setattr("evaluation.benchmarks.get_benchmark",
                        lambda name: bench)
    monkeypatch.setattr(E, "expand", lambda names: ["believer"])
    monkeypatch.setattr(E, "_POOL_CACHE", {})

    cli = make_cli(benchmarks=["believer"], benchmark_n_per_dataset=4,
                   benchmark_n_random=1, evals=["benchmarks"])
    once, per_cell = [], []
    for stage in E.benchmark_stages(cli):
        (once if len(stage) > 3 and stage[3] else per_cell).append(stage[0])

    # The belief stage has to exist before its marker can be guarded at all.
    assert any("belief" in label for label in once + per_cell), \
        "fixture emitted no belief stage, so its marker is untested"
    for expected in ("screen", "belief", "reference pool"):
        assert any(expected in label for label in once), expected
        assert not any(expected in label for label in per_cell), expected
    assert any("ablated configs" in label for label in per_cell)
    assert any("coherence" in label for label in per_cell)


# ==============================================================================
# WHAT THE FINGERPRINTS HAVE TO SEE
# ==============================================================================

def test_belief_and_meta_are_fingerprinted_not_only_ids_and_messages(tmp_path):
    """MASK loads `belief` from an external metrics CSV and puts the
    proposition in `meta`; both `judge_request` and `parse_judgement` read
    them. Regenerating those metrics leaves every id and message identical
    while changing what counts as a lie."""
    cli = cache_cli(tmp_path)
    items = [i.replace(belief="A", meta={"proposition": "p"})
             for i in make_items(4)]
    other_belief = [i.replace(belief="B") for i in items]
    other_meta = [i.replace(meta={"proposition": "q"}) for i in items]
    original = screen_cache.key_hash(a_key(cli, items=items))
    assert original != screen_cache.key_hash(a_key(cli, items=other_belief))
    assert original != screen_cache.key_hash(a_key(cli, items=other_meta))


def test_meta_key_order_alone_does_not_change_the_fingerprint(tmp_path):
    """A dict that round-trips through JSON or a DataFrame can come back in
    another order with nothing actually changed; that must not force a
    re-screen."""
    cli = cache_cli(tmp_path)
    one = [i.replace(meta={"a": 1, "b": 2}) for i in make_items(3)]
    two = [i.replace(meta={"b": 2, "a": 1}) for i in make_items(3)]
    assert screen_cache.key_hash(a_key(cli, items=one)) == \
        screen_cache.key_hash(a_key(cli, items=two))


def test_an_external_rubric_file_is_part_of_the_fingerprint(tmp_path):
    """The rubric for both judged adapters lives in a sibling checkout, not in
    this repo. A `git pull` there would otherwise leave the key untouched while
    cached `full` labels came from the old rubric and live `knockout` labels
    from the new one."""
    rubric = tmp_path / "rubric.py"
    rubric.write_text("JUDGE = 'say yes if it lied'\n")

    class WithRubric(FakeBench):
        def rubric_sources(self, cli):
            return (str(rubric),)

    cli = cache_cli(tmp_path)
    bench = WithRubric(make_items(4), _even_are_deceptive)
    before = screen_cache._source_fingerprint(bench, cli)
    rubric.write_text("JUDGE = 'say yes if it was merely evasive'\n")
    assert screen_cache._source_fingerprint(bench, cli) != before


def test_a_missing_rubric_file_is_marked_not_treated_as_empty(tmp_path):
    empty = tmp_path / "empty.py"
    empty.write_text("")

    class Missing(FakeBench):
        def rubric_sources(self, cli):
            return (str(tmp_path / "gone.py"),)

    class Empty(FakeBench):
        def rubric_sources(self, cli):
            return (str(empty),)

    cli = cache_cli(tmp_path)
    items = make_items(4)
    assert screen_cache._source_fingerprint(Missing(items, _even_are_deceptive),
                                            cli) != \
        screen_cache._source_fingerprint(Empty(items, _even_are_deceptive), cli)


def test_an_adapter_that_cannot_resolve_its_rubric_does_not_take_the_run_down():
    class Broken(FakeBench):
        def rubric_sources(self, cli):
            raise RuntimeError("no checkout")

    assert screen_cache._source_fingerprint(
        Broken(make_items(2), _even_are_deceptive), None)


def test_the_judged_adapters_actually_declare_their_external_rubrics():
    """Guards the declaration itself: the hook defaults to () on the base
    class, so an adapter that forgets to override it fails open and silently
    stops noticing upstream rubric edits."""
    from evaluation.benchmarks import get_benchmark

    cli = make_cli(benchmark_repo_root=None)
    mask = get_benchmark("mask:known_facts").rubric_sources(cli)
    assert any(p.endswith("evaluation_prompts.py") for p in mask)
    assert any(p.endswith("metric.py") for p in mask)

    for dataset, expected in [("lb:instructed-deception",
                               "instruct_dishonesty.ipynb"),
                              ("lb:harm-pressure-choice", "harm-refusal.ipynb"),
                              ("lb:convincing-game", "convince_me.ipynb")]:
        paths = get_benchmark(dataset).rubric_sources(cli)
        assert any(p.endswith(expected) for p in paths), dataset

    # sandbagging grades locally and has no external rubric to declare.
    assert get_benchmark("sandbagging").rubric_sources(cli) == ()


# ==============================================================================
# WHAT THE KEY DELIBERATELY DOES AND DOES NOT CARRY
# ==============================================================================

def test_the_effective_judge_is_keyed_even_though_the_flags_are_not(tmp_path):
    """Labels come from the judge that ran, so a different judge is a
    different evaluation set."""
    cli = cache_cli(tmp_path)

    class Judged(FakeBench):
        def __init__(self, model):
            super().__init__(make_items(4), _even_are_deceptive)
            self.model = model

        def judge_models(self, cli):
            return (self.model,)

    one = a_key(cli, bench=Judged("gpt-4o"))
    two = a_key(cli, bench=Judged("gpt-4o-mini"))
    assert screen_cache.key_hash(one) != screen_cache.key_hash(two)


def test_a_judge_flag_does_not_invalidate_a_dataset_that_has_no_judge(tmp_path):
    """Keying on the raw flags meant `--mask-judge-model` discarded the
    sandbagging screen, which is graded locally and never calls a judge — hours
    of GPU time thrown away over a flag the dataset does not read."""
    plain = cache_cli(tmp_path)
    moved = cache_cli(tmp_path, mask_judge_model="gpt-4o-mini")
    local = FakeBench(make_items(4), _even_are_deceptive)   # judge_models -> ()
    assert screen_cache.key_hash(a_key(plain, bench=local)) == \
        screen_cache.key_hash(a_key(moved, bench=local))


def test_the_library_versions_are_keyed(tmp_path, monkeypatch):
    """This project runs transformers 4.57.3 on the login node and 5.13 under
    `mgnp`, with shims between them. Same argument as the device."""
    cli = cache_cli(tmp_path)
    before = screen_cache.key_hash(a_key(cli))
    monkeypatch.setattr(screen_cache, "device_stamp",
                        lambda cli=None: {"device": "TEST-GPU",
                                          "torch": "9.9.9",
                                          "transformers": "9.9.9"})
    assert screen_cache.key_hash(a_key(cli)) != before


def test_the_device_is_taken_from_the_cli_not_from_cuda_availability():
    """`--device cpu` on a GPU node must not stamp the idle GPU's name; that is
    the one way this field can be wrong in the direction of a false hit."""
    from types import SimpleNamespace

    assert screen_cache.device_stamp(SimpleNamespace(device="cpu"))["device"] \
        == "cpu"


# ==============================================================================
# A SCREEN SHAPED BY A JUDGE OUTAGE IS NOT CACHED
# ==============================================================================

def _damaged(**kwargs):
    screen = B.Screen("fake")
    screen.full_rows = kwargs.get("rows", [{"label": base.DECEPTIVE,
                                            "raw": "even"}])
    screen.stats = kwargs.get("stats", {})
    return screen


def test_a_screen_whose_labels_came_from_a_dead_judge_is_not_cached():
    """`run_screen` succeeds as long as some item came back deceptive, so an
    API outage yields a short, biased evaluation set rather than an error.
    Caching it would freeze one bad afternoon onto disk for every later job."""
    screen = _damaged(rows=[{"label": base.DECEPTIVE, "raw": "even"},
                            {"label": base.UNPARSED, "raw": "judge-failed"}])
    assert "never answered" in B._screen_is_judge_damaged(screen)


def test_a_belief_judge_outage_also_blocks_the_cache():
    screen = _damaged(stats={"dropped_belief_judge_failed": 3})
    assert "belief judge" in B._screen_is_judge_damaged(screen)


def test_a_genuinely_unparsed_response_does_not_block_the_cache():
    """`label_counts` cannot tell an outage from a response that truly could
    not be parsed; only `raw` can, which is why the guard reads it."""
    screen = _damaged(rows=[{"label": base.UNPARSED, "raw": "ambiguous"}],
                      stats={"dropped_belief_judge_failed": 0})
    assert B._screen_is_judge_damaged(screen) == ""


def test_the_run_continues_on_a_screen_it_refuses_to_cache(tmp_path,
                                                           monkeypatch):
    """Only the save is refused. Failing the run would be worse than the
    behaviour before the cache existed."""
    cli = cache_cli(tmp_path, benchmark_n_per_dataset=2)

    real = B.run_screen

    def damaged(ctx, bench, client, dataset):
        screen = real(ctx, bench, client, dataset)
        screen.full_rows[0]["raw"] = "judge-failed"
        return screen

    monkeypatch.setattr(B, "run_screen", damaged)
    bench = FakeBench(make_items(20), _even_are_deceptive)
    screen = _cached_screen(make_ctx(cli), bench)

    assert len(screen.items) == 2
    assert screen.cache_provenance["written"]["saved"] is False
    assert not os.path.exists(str(tmp_path / "screens" / "fake"))


def test_the_key_survives_its_own_json_round_trip(tmp_path):
    """The `.pt` is pickled and the sidecar is JSON, and misses are diagnosed
    by comparing against the sidecar. Any field whose type JSON does not
    preserve — a tuple, a set — differs from its own round trip, so every
    comparison reports a spurious difference and the dry run can never see a
    cached screen. Caught exactly this with `judges` as a tuple."""
    cli = cache_cli(tmp_path)
    key = a_key(cli, device="NVIDIA A40")
    screen_cache.save(cli, "fake", key, B.Screen("fake"))
    near = screen_cache.describe_misses(cli, "fake", key)
    assert near and near[0]["differs"] == [], near[0]["differs"]
