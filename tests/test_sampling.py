"""
Library-seam tests for `component_analysis/sampling.py`.

Descriptive analyses run over the whole test split; causal ones run over a
fixed-seed sample whose ids are written out. The properties that matter to the
caller are: the sample has the size asked for, it is stratified over every
metadata factor that has more than one level, a task with only one level of
every factor still gets its N, and the same seed gives the same instances.
"""

from __future__ import annotations

import pytest

from component_analysis import sampling


# ==============================================================================
# FIXTURES
# ==============================================================================

def balanced_records(per_cell=50):
    """A 2 x 2 x 2 design over the three metadata factors, evenly filled."""
    records = []
    for designation in ("identity", "inversion"):
        for item_polarity in (1, 2):
            for variant in ("audit", "lab"):
                for i in range(per_cell):
                    records.append({
                        "instance_id": f"{designation[:3]}{item_polarity}"
                                       f"{variant[:3]}{i:04d}",
                        "designation_polarity": designation,
                        "item_polarity": item_polarity,
                        "template_variant": variant,
                    })
    return records


def skewed_records():
    """SDR-shaped skew: 569/431 designation, 782/218 template variant."""
    records = []
    for i in range(1000):
        records.append({
            "instance_id": f"skew{i:04d}",
            "designation_polarity": "identity" if i < 569 else "inversion",
            "item_polarity": 1 if i % 1000 < 509 else 2,
            "template_variant": "audit" if i % 1000 < 782 else "lab",
        })
    return records


def identity_only_records(n=300):
    """FAR / SER shape: one level of every factor."""
    return [{"instance_id": f"far{i:04d}",
             "designation_polarity": "identity",
             "item_polarity": 1,
             "template_variant": "audit"} for i in range(n)]


# ==============================================================================
# TESTS
# ==============================================================================

def test_a_balanced_fixture_is_sampled_evenly_over_every_stratum():
    sample = sampling.draw_sample(balanced_records(), n=100, seed=7)

    assert sample.n_drawn == 100
    assert sample.factors == list(sampling.DEFAULT_FACTORS)
    assert len(sample.strata) == 8
    assert {stratum.achieved for stratum in sample.strata} == {12, 13}
    assert sum(stratum.achieved for stratum in sample.strata) == 100
    assert len(set(sample.ids)) == 100


def test_achieved_counts_track_the_populations_marginals():
    """Proportional allocation: the sample's polarity balance is the split's."""
    sample = sampling.draw_sample(skewed_records(), n=100, seed=0)

    assert sample.marginals["designation_polarity"] == {"identity": 57,
                                                        "inversion": 43}
    assert sample.marginals["template_variant"] == {"audit": 78, "lab": 22}
    assert sum(sample.marginals["item_polarity"].values()) == 100


def test_an_identity_only_task_still_returns_n_instances():
    """FAR and SER test sets have one level of every factor; the sample must
    not fail on the missing ones."""
    sample = sampling.draw_sample(identity_only_records(), n=100, seed=3)

    assert sample.n_drawn == 100
    assert sample.factors == []
    assert sorted(sample.inactive_factors) == sorted(sampling.DEFAULT_FACTORS)
    assert len(sample.strata) == 1
    assert sample.strata[0].achieved == 100


def test_a_factor_the_records_do_not_carry_counts_as_one_level():
    """STD records have none of the three factors, so it takes the same path."""
    records = [{"statement": f"s{i}"} for i in range(50)]
    sample = sampling.draw_sample(records, n=20, seed=1)

    assert sample.n_drawn == 20
    assert sample.factors == []
    assert sample.inactive_factors["designation_polarity"] is None
    assert sample.ids == sorted(sample.ids)
    assert all(rid.startswith("index") for rid in sample.ids)


def test_the_same_seed_reproduces_the_same_instances():
    records = skewed_records()
    first = sampling.draw_sample(records, n=60, seed=11)
    again = sampling.draw_sample(records, n=60, seed=11)
    other = sampling.draw_sample(records, n=60, seed=12)

    assert first.ids == again.ids
    assert first.indices == again.indices
    assert first.ids != other.ids


def test_record_order_does_not_change_the_sample():
    """The seed, not the dataset's row order, decides which instances are drawn."""
    records = skewed_records()
    shuffled = list(reversed(records))

    assert sorted(sampling.draw_sample(records, n=40, seed=5).ids) == \
        sorted(sampling.draw_sample(shuffled, n=40, seed=5).ids)


def test_asking_for_more_than_the_split_holds_returns_the_whole_split():
    records = identity_only_records(30)
    sample = sampling.draw_sample(records, n=100, seed=0)

    assert sample.n_requested == 100
    assert sample.n_drawn == 30
    assert sorted(sample.ids) == sorted(r["instance_id"] for r in records)


def test_a_stratum_smaller_than_its_quota_gives_its_share_to_the_others():
    records = balanced_records(per_cell=50)
    records = [r for r in records
               if not (r["designation_polarity"] == "inversion"
                       and r["item_polarity"] == 2
                       and r["template_variant"] == "lab")][:351]
    records += [dict(r, instance_id=f"rare{i}")
                for i, r in enumerate(balanced_records(per_cell=2)[-2:])]

    sample = sampling.draw_sample(records, n=100, seed=2)
    assert sample.n_drawn == 100
    for stratum in sample.strata:
        assert stratum.achieved <= stratum.available


def test_the_sample_json_records_ids_and_achieved_counts(tmp_path):
    sample = sampling.draw_sample(skewed_records(), n=50, seed=4)
    payload = sample.as_json()

    assert payload["n_requested"] == 50 and payload["n_drawn"] == 50
    assert payload["seed"] == 4
    assert payload["instance_ids"] == sample.ids
    assert sum(s["achieved"] for s in payload["strata"]) == 50
    for stratum in payload["strata"]:
        assert set(stratum["key"]) == set(sampling.DEFAULT_FACTORS)
        assert all(isinstance(v, str) for v in stratum["key"].values())
