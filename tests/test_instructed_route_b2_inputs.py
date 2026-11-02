"""
B2 ticket T3 (instructed-route): the id and group files P2 and P3 read.

`scripts/instructed_route_b2_inputs.py` writes, under
`docs/research/instructed-route/groups/`, the 618 SDR wish ids, the seed-0
(selection) and seed-1 (held-out) id lists per task, a seed-2 draw per task with
seeds 0 and 1 excluded, and the two `--knockout-groups` files. These tests pin
the group contents, the null draws' determinism, and that the seed-2 draw uses
the procedure that reproduces the tracked seed-1 held-out ids.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

from component_analysis import knockout, sampling

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "instructed_route_b2_inputs.py")
DATA = os.path.join(REPO, "data", "datasets")
GROUPS = os.path.join(REPO, "docs", "research", "instructed-route", "groups")
HELDOUT = os.path.join(REPO, "docs", "research", "mechanism-analysis",
                       "phase1", "groups")
TASKS = ("far", "sdr", "ser")
QUARTET = [24, 25, 26, 27]


def _load_script():
    spec = importlib.util.spec_from_file_location("instructed_route_b2_inputs",
                                                  SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


b2 = _load_script()


def _need(path):
    if not os.path.exists(path):
        pytest.skip(f"{path} is not present here")
    return path


def _lines(path):
    with open(path) as handle:
        return [line.strip() for line in handle if line.strip()]


# ------------------------------------------------------------------------------
# P2 groups
# ------------------------------------------------------------------------------

def test_quartet_is_exactly_the_four_l17_heads_24_to_27():
    groups = b2.p2_groups()
    assert groups["quartet"] == [["head", 17, h] for h in QUARTET]
    assert groups["L17H24"] == [["head", 17, 24]]


def test_p2_group_names_and_order():
    names = list(b2.p2_groups())
    assert names == (["quartet", "L17H24"]
                     + [f"kvg_{g}" for g in range(8) if g != 6]
                     + [f"null_d{i:02d}" for i in range(20)])


def test_kv_groups_are_seven_disjoint_runs_of_four_with_exact_unions():
    groups = b2.p2_groups()
    kv = {name: members for name, members in groups.items()
          if name.startswith("kvg_")}
    assert sorted(kv) == sorted(f"kvg_{g}" for g in (0, 1, 2, 3, 4, 5, 7))
    seen = set()
    for name, members in kv.items():
        g = int(name.split("_")[1])
        assert members == [["head", 17, h] for h in range(4 * g, 4 * g + 4)]
        heads = {h for _kind, _layer, h in members}
        assert not heads & seen
        seen |= heads
    assert seen == set(range(32)) - set(QUARTET)
    # With the quartet (KV group 6) the KV groups tile layer 17 exactly.
    assert seen | {h for _k, _l, h in groups["quartet"]} == set(range(32))


def test_nulls_are_twenty_distinct_l17_quartets_outside_24_to_27():
    groups = b2.p2_groups()
    nulls = [groups[f"null_d{i:02d}"] for i in range(20)]
    assert len(nulls) == 20
    as_sets = []
    for members in nulls:
        assert len(members) == 4
        assert all(kind == "head" and layer == 17 for kind, layer, _h in members)
        heads = [h for _k, _l, h in members]
        assert len(set(heads)) == 4
        assert all(0 <= h < 32 and h not in QUARTET for h in heads)
        assert heads == sorted(heads)
        as_sets.append(frozenset(heads))
    assert len(set(as_sets)) == 20
    # No null coincides with the quartet or one of the KV groups by accident.
    kv_sets = {frozenset(range(4 * g, 4 * g + 4)) for g in range(8)}
    assert not set(as_sets) & kv_sets


def test_nulls_are_identical_across_calls_and_follow_the_declared_seeds():
    first, second = b2.p2_groups(), b2.p2_groups()
    assert json.dumps(first) == json.dumps(second)
    for i in range(20):
        expected = b2.null_quartet(20261101 + i)
        assert first[f"null_d{i:02d}"] == [["head", 17, h] for h in expected]


def test_p2_groups_file_loads_through_knockout_load_groups(tmp_path):
    path = tmp_path / "p2_groups.json"
    path.write_text(json.dumps(b2.p2_groups()))
    loaded = knockout.load_groups(str(path))
    knockout.check_groups(loaded, {"num_layers": 32, "num_heads": 32})
    assert len(loaded) == 2 + 7 + 20


# ------------------------------------------------------------------------------
# P3 groups
# ------------------------------------------------------------------------------

def test_p3_groups_are_six_one_member_mlp_groups(tmp_path):
    groups = b2.p3_groups()
    assert groups == {f"mlp.{layer}": [["mlp", layer, 0]]
                      for layer in (11, 13, 16, 30, 31, 0)}
    assert list(groups) == ["mlp.11", "mlp.13", "mlp.16", "mlp.30", "mlp.31",
                            "mlp.0"]
    path = tmp_path / "p3_groups.json"
    path.write_text(json.dumps(groups))
    loaded = knockout.load_groups(str(path))
    knockout.check_groups(loaded, {"num_layers": 32, "num_heads": 32})
    assert len(loaded) == 6


# ------------------------------------------------------------------------------
# Ids
# ------------------------------------------------------------------------------

def test_wish_ids_are_the_618_unique_ids_of_the_dataset():
    path = _need(os.path.join(DATA, "sdr_v2_inversion_reported"))
    ids = b2.wish_ids(DATA)
    assert len(ids) == 618
    assert len(set(ids)) == 618
    from datasets import load_from_disk
    rows = load_from_disk(path)["test"]
    assert ids == [str(one) for one in rows["instance_id"]]


def test_seed_one_redraw_reproduces_the_tracked_held_out_ids():
    for task in TASKS:
        tracked = sampling.read_id_file(
            _need(os.path.join(HELDOUT, f"{task}_heldout_D_sample.json")))
        records = b2.test_records(DATA, task)
        selection = b2.draw_ids(records, seed=0)
        held_out = b2.draw_ids(records, seed=1, exclude=selection)
        assert held_out == tracked, task


def test_seed_zero_redraw_reproduces_the_selection_sample_where_present():
    for task in TASKS:
        path = os.path.join(b2.DEFAULT_SAMPLE_ROOT, f"{task}_v2", "sample.json")
        if not os.path.exists(path):
            pytest.skip(f"{path} is local and untracked; absent here")
        records = b2.test_records(DATA, task)
        assert b2.draw_ids(records, seed=0) == sampling.read_id_file(path), task


def test_seed_two_is_disjoint_from_seeds_zero_and_one_and_deterministic():
    for task in TASKS:
        records = b2.test_records(DATA, task)
        seed0 = b2.draw_ids(records, seed=0)
        seed1 = b2.draw_ids(records, seed=1, exclude=seed0)
        seed2 = b2.draw_ids(records, seed=2, exclude=seed0 + seed1)
        assert len(seed2) == 100 and len(set(seed2)) == 100
        assert not set(seed2) & set(seed0)
        assert not set(seed2) & set(seed1)
        assert seed2 == b2.draw_ids(records, seed=2, exclude=seed0 + seed1)


# ------------------------------------------------------------------------------
# The writer
# ------------------------------------------------------------------------------

def _run_main(out_dir, sample_root=None):
    argv = ["--out-dir", str(out_dir), "--data-dir", DATA,
            "--heldout-dir", HELDOUT]
    if sample_root is not None:
        argv += ["--sample-root", str(sample_root)]
    return b2.main(argv)


def _fake_sample_root(tmp_path):
    """Seed-0 sample.json files redrawn on CPU, so the writer test runs where
    the untracked originals are absent."""
    root = tmp_path / "sample_root"
    for task in TASKS:
        records = b2.test_records(DATA, task)
        (root / f"{task}_v2").mkdir(parents=True)
        (root / f"{task}_v2" / "sample.json").write_text(
            json.dumps({"instance_ids": b2.draw_ids(records, seed=0)}))
    return root


def test_main_writes_every_file_and_a_rerun_is_unchanged(tmp_path):
    _need(os.path.join(DATA, "sdr_v2_inversion_reported"))
    out = tmp_path / "groups"
    root = _fake_sample_root(tmp_path)
    assert _run_main(out, root) == 0
    expected = {"sdr_wish_ids.txt", "p2_groups.json", "p3_groups.json",
                "b2_inputs_meta.json"}
    for task in TASKS:
        expected |= {f"{task}_seed{s}_ids.txt" for s in (0, 1, 2)}
    assert set(os.listdir(out)) == expected
    assert _lines(out / "sdr_wish_ids.txt") == b2.wish_ids(DATA)
    for task in TASKS:
        s0, s1, s2 = (_lines(out / f"{task}_seed{s}_ids.txt") for s in (0, 1, 2))
        assert s1 == sampling.read_id_file(
            os.path.join(HELDOUT, f"{task}_heldout_D_sample.json"))
        assert len(s0) == len(s1) == len(s2) == 100
        assert not (set(s0) | set(s1)) & set(s2)
    assert json.loads((out / "p2_groups.json").read_text()) == b2.p2_groups()
    assert json.loads((out / "p3_groups.json").read_text()) == b2.p3_groups()
    before = {name: (out / name).read_bytes() for name in expected}
    assert _run_main(out, root) == 0
    assert {name: (out / name).read_bytes() for name in expected} == before


def test_main_keeps_an_equal_wish_file_and_refuses_a_different_one(tmp_path):
    _need(os.path.join(DATA, "sdr_v2_inversion_reported"))
    root = _fake_sample_root(tmp_path)
    ids = b2.wish_ids(DATA)

    same = tmp_path / "same"
    same.mkdir()
    # Another ticket's copy, same ids in another order: verified, not rewritten.
    (same / "sdr_wish_ids.txt").write_text("\n".join(reversed(ids)) + "\n")
    assert _run_main(same, root) == 0
    assert _lines(same / "sdr_wish_ids.txt") == list(reversed(ids))

    differ = tmp_path / "differ"
    differ.mkdir()
    (differ / "sdr_wish_ids.txt").write_text("\n".join(ids[:-1]) + "\n")
    with pytest.raises(SystemExit):
        _run_main(differ, root)
    assert _lines(differ / "sdr_wish_ids.txt") == ids[:-1]


def test_main_refuses_when_the_seed_one_redraw_does_not_match(tmp_path):
    _need(os.path.join(DATA, "sdr_v2_inversion_reported"))
    root = _fake_sample_root(tmp_path)
    bad_heldout = tmp_path / "heldout"
    bad_heldout.mkdir()
    for task in TASKS:
        ids = sampling.read_id_file(
            os.path.join(HELDOUT, f"{task}_heldout_D_sample.json"))
        (bad_heldout / f"{task}_heldout_D_sample.json").write_text(
            json.dumps({"instance_ids": ids[1:] + ["not-an-id"]}))
    with pytest.raises(SystemExit):
        b2.main(["--out-dir", str(tmp_path / "out"), "--data-dir", DATA,
                 "--heldout-dir", str(bad_heldout),
                 "--sample-root", str(root)])


def test_tracked_files_match_a_fresh_build():
    """The committed files under groups/ are what the script writes now."""
    _need(os.path.join(GROUPS, "p2_groups.json"))
    with open(os.path.join(GROUPS, "p2_groups.json")) as handle:
        assert json.load(handle) == b2.p2_groups()
    with open(os.path.join(GROUPS, "p3_groups.json")) as handle:
        assert json.load(handle) == b2.p3_groups()
    assert sorted(_lines(os.path.join(GROUPS, "sdr_wish_ids.txt"))) == \
        sorted(b2.wish_ids(DATA))
    for task in TASKS:
        records = b2.test_records(DATA, task)
        s0 = _lines(os.path.join(GROUPS, f"{task}_seed0_ids.txt"))
        s1 = _lines(os.path.join(GROUPS, f"{task}_seed1_ids.txt"))
        s2 = _lines(os.path.join(GROUPS, f"{task}_seed2_ids.txt"))
        assert s0 == b2.draw_ids(records, seed=0)
        assert s1 == sampling.read_id_file(
            os.path.join(HELDOUT, f"{task}_heldout_D_sample.json"))
        assert s2 == b2.draw_ids(records, seed=2, exclude=s0 + s1)
