"""
component_analysis/sampling.py — which instances the causal analyses run on.

Descriptive analyses (attention patterns, DLA, logit lens) run over the whole
test split. Knockout and path patching cannot: they are a forward pass per
Component per instance, so they run over a fixed-seed sample of N instances
whose ids are written out, and a rerun with the same seed patches the same
prompts.

The sample is **stratified** over the metadata factors CONTEXT.md names as the
task's balanced nuisance factors — Designation Polarity, Item Polarity and
Template Variant — but only over those that actually vary in the split. FAR and
SER test sets are entirely identity polarity, and STD carries none of the three
fields at all, so a factor with one level (or no level, which is the same
thing) is recorded as inactive and the draw falls back to a plain seeded sample
of N. A missing level is a property of the dataset, never a failure here.

Allocation is **balanced** (researcher's decision, 2026-09-15): N is spread as
equally as the populations allow, rather than proportionally. A proportional
draw reproduces the split's marginals, which is what you want for describing
the split — but the causal analyses are comparing the levels of a factor
against each other, and on the SDR test split proportional allocation gives the
`inversion / lab` cell one instance where balanced gives it twelve. A contrast
read off one instance is not a contrast. The price is that the sample no longer
represents the split, so a rate read off the sample is not the split's rate.

`target` and `achieved` are therefore two different numbers and `sample.json`
writes both: `target` is the equal share a stratum was aiming at, `achieved`
what it could give, which is smaller on a stratum too small to fill its share
and larger on the strata that absorb that stratum's surplus.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

#: The factors to stratify over, in the order CONTEXT.md introduces them.
DEFAULT_FACTORS = ("designation_polarity", "item_polarity", "template_variant")

DEFAULT_N_CAUSAL = 100
DEFAULT_SEED = 0

#: How N is spread over the strata, recorded in `sample.json` so a reader of a
#: written sample never has to guess which allocation produced it.
ALLOCATION = "balanced"


def record_id(record: dict, index: int) -> str:
    """A stable id for one instance.

    The mechanism tasks carry `instance_id`, the hash of the task-independent
    instance tuple, which is what makes a matched triplet identifiable across
    FAR / SDR / SER. STD records have no id, so their position in the split is
    the id, spelled so it cannot be confused with a hash.
    """
    value = record.get("instance_id")
    return str(value) if value else f"index{index:06d}"


def record_ids(records: Sequence[dict]) -> List[str]:
    """`record_id` over a whole split, so the CLI, the segmentation and the
    sample all key their output the same way."""
    return [record_id(record, i) for i, record in enumerate(records)]


# ==============================================================================
# THE SAMPLE
# ==============================================================================

@dataclass
class Stratum:
    """One cell of the cross product of the active factors.

    `target` is the equal share this cell was allocated and `achieved` is what
    it could give. Under balanced allocation the two differ whenever some cell
    is too small to fill its share: that cell falls short and the cells that
    absorb its surplus exceed theirs.
    """

    key: Dict[str, str]
    available: int
    target: int
    ids: List[str] = field(default_factory=list)
    indices: List[int] = field(default_factory=list)

    @property
    def achieved(self) -> int:
        return len(self.ids)

    def as_json(self) -> dict:
        return {"key": dict(self.key), "available": self.available,
                "target": self.target, "achieved": self.achieved,
                "instance_ids": list(self.ids)}


@dataclass
class Sample:
    """The drawn instances, and how the draw turned out."""

    n_requested: int
    seed: int
    factors: List[str]                       # stratified over these
    inactive_factors: Dict[str, Optional[str]]   # factor -> its only level
    strata: List[Stratum]
    ids: List[str]
    indices: List[int]        # positions in the split AS LOADED (see as_json)
    marginals: Dict[str, Dict[str, int]]

    @property
    def n_drawn(self) -> int:
        return len(self.ids)

    def as_json(self) -> dict:
        return {
            "n_requested": self.n_requested, "n_drawn": self.n_drawn,
            "seed": self.seed, "factors": list(self.factors),
            "inactive_factors": dict(self.inactive_factors),
            "allocation": ALLOCATION,
            "allocation_rule": ("the equal share per stratum, capped by each "
                                "stratum's population, with the surplus "
                                "handed one at a time to the smallest stratum "
                                "that still has room"),
            "strata": [stratum.as_json() for stratum in self.strata],
            "marginals": {factor: dict(counts)
                          for factor, counts in self.marginals.items()},
            "instance_ids": list(self.ids),
            "split_indices": list(self.indices),
            "join_on": ("instance_ids. split_indices are positions in the "
                        "split as the task's loader returns it, BEFORE the "
                        "dataset class filters it — DeceptionDatasetLlama "
                        "drops any record whose target or distractor is not a "
                        "single token — so on a split that is not already "
                        "prefiltered they do not index the dataset the causal "
                        "analyses iterate. The ids always do."),
        }


# ==============================================================================
# DRAWING
# ==============================================================================

def _level(record: dict, factor: str) -> Optional[str]:
    value = record.get(factor)
    return None if value is None else str(value)


def _active_factors(records: Sequence[dict], factors: Sequence[str]):
    """(factors with more than one level, {inactive factor: its only level})."""
    active, inactive = [], {}
    for factor in factors:
        levels = {_level(record, factor) for record in records}
        if len(levels) > 1:
            active.append(factor)
        else:
            inactive[factor] = next(iter(levels)) if levels else None
    return active, inactive


def allocate(sizes: Sequence[int], n: int) -> Tuple[List[int], List[int]]:
    """Balanced allocation of `n` over strata of `sizes`.

    Returns `(targets, counts)`:

    - `targets` is the **equal share** — `n // k` for each of the `k` non-empty
      strata, plus one more for the first `n % k` of them in the order they
      were given, which is the sorted stratum-key order `draw_sample` builds.
      It is what a stratum would get if every stratum had room, and it is
      recorded so `sample.json` says what the draw was aiming at.
    - `counts` is what can actually be drawn: the target capped by the
      stratum's population, with the surplus from any capped stratum handed one
      at a time to the smallest stratum that still has room. That leaves the
      strata which absorb the surplus within one of each other, so the result
      is as balanced as the populations allow. Handing it out in index order
      instead would stack it on a stratum already one ahead from the `n % k`
      extra.

    `sum(counts) == min(n, sum(sizes))`. An empty stratum gets a target of zero
    rather than an equal share it could never fill; it cannot arise from
    `draw_sample`, which builds strata from the records they hold, but
    `allocate` is callable on its own.
    """
    targets = [0] * len(sizes)
    counts = [0] * len(sizes)
    total = sum(sizes)
    n = min(n, total)
    if n == 0:
        return targets, counts

    live = [i for i, size in enumerate(sizes) if size > 0]
    share, extra = divmod(n, len(live))
    for rank, i in enumerate(live):
        targets[i] = share + (1 if rank < extra else 0)
        counts[i] = min(targets[i], sizes[i])

    remaining = n - sum(counts)
    while remaining > 0:
        room = [i for i in live if counts[i] < sizes[i]]
        # A shortfall always leaves room somewhere, so this is an invariant
        # rather than a case to handle: `n` is capped at the total, so if every
        # stratum were full `counts` would already sum to the total, which is
        # at least `n`, and `remaining` would not be positive.
        assert room, "every stratum is full but the draw is still short"
        # Smallest first, ties by index. Index order alone would stack the
        # surplus on a stratum that is already one ahead from the `n % k`
        # extra: 10 over sizes 100, 100, 2 would give 5, 3, 2 rather than
        # 4, 4, 2. Deterministic either way; this one actually levels.
        for i in sorted(room, key=lambda j: (counts[j], j)):
            if remaining == 0:
                break
            counts[i] += 1
            remaining -= 1
    return targets, counts


def draw_sample(records: Sequence[dict], *, n: int = DEFAULT_N_CAUSAL,
                seed: int = DEFAULT_SEED,
                factors: Sequence[str] = DEFAULT_FACTORS,
                ids: Optional[Sequence[str]] = None) -> Sample:
    """N instances, stratified over every factor with more than one level."""
    if n < 0:
        raise ValueError(f"--n-causal must not be negative, got {n}")
    records = list(records)
    ids = list(ids) if ids is not None else record_ids(records)
    if len(ids) != len(records):
        raise ValueError(f"{len(ids)} ids for {len(records)} records")

    active, inactive = _active_factors(records, factors)

    buckets: Dict[Tuple[Tuple[str, Optional[str]], ...], List[Tuple[str, int]]] = {}
    for index, record in enumerate(records):
        key = tuple((factor, _level(record, factor)) for factor in active)
        buckets.setdefault(key, []).append((ids[index], index))

    # Sorting the strata and the members of each stratum is what makes the seed,
    # rather than the dataset's row order, decide the draw.
    keys = sorted(buckets, key=lambda k: tuple(str(v) for _, v in k))
    pools = [sorted(buckets[key]) for key in keys]
    targets, counts = allocate([len(pool) for pool in pools], n)

    rng = random.Random(seed)
    strata: List[Stratum] = []
    for key, pool, target, count in zip(keys, pools, targets, counts):
        drawn = sorted(rng.sample(pool, count)) if count else []
        strata.append(Stratum(
            key={factor: ("" if value is None else value) for factor, value in key},
            available=len(pool), target=target,
            ids=[rid for rid, _ in drawn], indices=[i for _, i in drawn]))

    chosen = sorted((i, rid) for stratum in strata
                    for rid, i in zip(stratum.ids, stratum.indices))
    by_index = {index: rid for index, rid in chosen}

    marginals: Dict[str, Dict[str, int]] = {}
    for factor in factors:
        counts: Dict[str, int] = {}
        for index in by_index:
            level = _level(records[index], factor)
            counts["" if level is None else level] = \
                counts.get("" if level is None else level, 0) + 1
        marginals[factor] = dict(sorted(counts.items()))

    return Sample(n_requested=n, seed=seed, factors=active,
                  inactive_factors=inactive, strata=strata,
                  ids=[rid for _, rid in chosen],
                  indices=[index for index, _ in chosen],
                  marginals=marginals)
