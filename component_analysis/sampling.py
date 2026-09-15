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

Allocation is **proportional**: a stratum holding 57% of the split gets 57% of
the sample, by largest remainder, so the sample's marginals reproduce the
split's and a polarity effect read off the sample is not an artefact of the
draw. A stratum with fewer instances than its quota gives the shortfall to the
others, which is why `achieved` is written beside `target` rather than assumed
equal to it.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

#: The factors to stratify over, in the order CONTEXT.md introduces them.
DEFAULT_FACTORS = ("designation_polarity", "item_polarity", "template_variant")

DEFAULT_N_CAUSAL = 100
DEFAULT_SEED = 0


def record_id(record: dict, index: int) -> str:
    """A stable id for one instance.

    The mechanism tasks carry `instance_id`, the hash of the task-independent
    instance tuple, which is what makes a matched triplet identifiable across
    FAR / SDR / SER. STD records have no id, so their position in the split is
    the id, spelled so it cannot be confused with a hash.
    """
    value = record.get("instance_id")
    return str(value) if value else f"index{index:06d}"


# ==============================================================================
# THE SAMPLE
# ==============================================================================

@dataclass
class Stratum:
    """One cell of the cross product of the active factors."""

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
    indices: List[int]
    marginals: Dict[str, Dict[str, int]]

    @property
    def n_drawn(self) -> int:
        return len(self.ids)

    def as_json(self) -> dict:
        return {
            "n_requested": self.n_requested, "n_drawn": self.n_drawn,
            "seed": self.seed, "factors": list(self.factors),
            "inactive_factors": dict(self.inactive_factors),
            "allocation": "proportional (largest remainder)",
            "strata": [stratum.as_json() for stratum in self.strata],
            "marginals": {factor: dict(counts)
                          for factor, counts in self.marginals.items()},
            "instance_ids": list(self.ids),
            "split_indices": list(self.indices),
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


def allocate(sizes: Sequence[int], n: int) -> List[int]:
    """Proportional allocation of `n` over strata of `sizes`, largest remainder.

    Never allocates more to a stratum than it holds; the shortfall goes to the
    strata that still have room, which is what keeps `sum(result) == n`
    whenever the strata hold `n` instances between them.
    """
    total = sum(sizes)
    n = min(n, total)
    if n == 0:
        return [0] * len(sizes)

    quotas = [size * n / total for size in sizes]
    counts = [min(int(math.floor(q)), size) for q, size in zip(quotas, sizes)]
    order = sorted(range(len(sizes)),
                   key=lambda i: (-(quotas[i] - math.floor(quotas[i])), i))

    remaining = n - sum(counts)
    while remaining > 0:
        moved = False
        for i in order:
            if remaining == 0:
                break
            if counts[i] < sizes[i]:
                counts[i] += 1
                remaining -= 1
                moved = True
        if not moved:                   # every stratum is full
            break
    return counts


def draw_sample(records: Sequence[dict], *, n: int = DEFAULT_N_CAUSAL,
                seed: int = DEFAULT_SEED,
                factors: Sequence[str] = DEFAULT_FACTORS,
                ids: Optional[Sequence[str]] = None) -> Sample:
    """N instances, stratified over every factor with more than one level."""
    if n < 0:
        raise ValueError(f"--n-causal must not be negative, got {n}")
    records = list(records)
    ids = list(ids) if ids is not None else [record_id(record, i)
                                             for i, record in enumerate(records)]
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
    targets = allocate([len(pool) for pool in pools], n)

    rng = random.Random(seed)
    strata: List[Stratum] = []
    for key, pool, target in zip(keys, pools, targets):
        drawn = sorted(rng.sample(pool, target)) if target else []
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
