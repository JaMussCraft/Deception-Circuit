"""
Held-out sampling (spec R11(b), R19(3)): the causal sample can exclude a file of
ids (the selection sample's) and can be restricted to a file of ids (D's
held-out ids that survived I's filter). Without either option the draw is
byte-identical to the one the package made before the options existed: the
golden file was written by the unmodified `draw_sample` on 2026-10-25.
"""

from __future__ import annotations

import json
import os
from collections import Counter

import pytest

from component_analysis import sampling

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "datasets")
GOLDEN = os.path.join(REPO, "tests", "fixtures", "component_analysis_v2",
                      "sample_snapshot.json")


def split(task):
    path = os.path.join(DATA, task)
    if not os.path.isdir(path):
        pytest.skip(f"{task} is not built under data/datasets")
    from datasets import load_from_disk
    return [dict(row) for row in load_from_disk(path)["test"]]


@pytest.fixture(scope="module")
def golden():
    with open(GOLDEN) as handle:
        return json.load(handle)


@pytest.mark.parametrize("task", ["far_v2", "sdr_v2", "ser_v2", "sdr"])
@pytest.mark.parametrize("seed", [0, 1])
def test_without_an_id_option_the_draw_is_the_one_made_before_the_options(
        golden, task, seed):
    sample = sampling.draw_sample(split(task), n=100, seed=seed)
    assert sample.as_json() == golden[f"{task}/seed{seed}"]


def test_seed_one_with_the_seed_zero_ids_excluded_is_disjoint_and_balanced():
    rows = split("sdr_v2")
    selection = sampling.draw_sample(rows, n=100, seed=0)

    held_out = sampling.draw_sample(rows, n=100, seed=1,
                                    exclude_ids=selection.ids)

    assert held_out.n_drawn == 100
    assert not set(held_out.ids) & set(selection.ids)
    # 8 strata of 125 each, so balanced allocation gives 12 or 13 per stratum.
    assert len(held_out.strata) == 8
    assert sorted({stratum.achieved for stratum in held_out.strata}) == [12, 13]
    excluded = held_out.as_json()["id_exclusion"]
    assert excluded["n_ids"] == 100 and excluded["n_removed_from_split"] == 100


def test_an_inclusion_list_no_larger_than_n_is_drawn_exactly():
    rows = split("sdr_v2")
    ids = sampling.record_ids(rows)
    wanted = ids[5:45] + ["not_an_id_1", "not_an_id_2"]

    sample = sampling.draw_sample(rows, n=100, seed=1, include_ids=wanted)

    assert sorted(sample.ids) == sorted(ids[5:45])
    included = sample.as_json()["id_inclusion"]
    assert included["n_ids"] == 42
    assert included["not_in_split"] == ["not_an_id_1", "not_an_id_2"]
    assert included["n_kept_in_split"] == 40


def record(rid, d, i, t):
    return {"instance_id": rid, "designation_polarity": d, "item_polarity": i,
            "template_variant": t}


def test_inclusion_and_exclusion_compose_and_exclusion_wins():
    rows = [record(f"r{n}", "identity" if n % 2 else "inversion", n % 3 % 2,
                   "audit") for n in range(30)]
    sample = sampling.draw_sample(rows, n=50, seed=3,
                                  include_ids=[f"r{n}" for n in range(10)],
                                  exclude_ids=["r0", "r1"])
    assert sorted(sample.ids, key=lambda s: int(s[1:])) == \
        [f"r{n}" for n in range(2, 10)]


def test_a_draw_from_a_restricted_pool_is_still_stratified():
    rows = [record(f"r{n}", "identity" if n < 50 else "inversion", 0, "audit")
            for n in range(100)]
    sample = sampling.draw_sample(rows, n=10, seed=0,
                                  exclude_ids=[f"r{n}" for n in range(40)])
    counts = Counter(rows[int(rid[1:])]["designation_polarity"]
                     for rid in sample.ids)
    assert counts == {"identity": 5, "inversion": 5}


@pytest.mark.parametrize("form", ["sample", "list", "lines"])
def test_an_id_file_may_be_a_sample_json_a_json_list_or_lines(tmp_path, form):
    ids = ["a1", "b2", "c3"]
    path = tmp_path / "ids"
    if form == "sample":
        path.write_text(json.dumps({"instance_ids": ids, "seed": 0}))
    elif form == "list":
        path.write_text(json.dumps(ids))
    else:
        path.write_text("a1\nb2\n\nc3\n")
    assert sampling.read_id_file(str(path)) == ids


def test_an_empty_id_file_is_refused(tmp_path):
    path = tmp_path / "ids.txt"
    path.write_text("\n")
    with pytest.raises(ValueError, match="no instance ids"):
        sampling.read_id_file(str(path))
