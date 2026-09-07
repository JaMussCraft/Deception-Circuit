"""
evaluation/benchmarks — the datasets EVAL 5 knocks the circuit out on.

A "dataset" here is one table in the report: one MASK split, one Liars' Bench
scenario, or sandbagging. They are named `mask:<split>`, `lb:<scenario>` and
`sandbagging`, and the group names `mask` and `lb` expand to all of their
members so `--benchmarks mask` is a whole benchmark and `--benchmarks
sandbagging` is a smoke test that needs no API key.

Adapters are imported lazily. Constructing the registry must not require
pandas, huggingface_hub or a populated cache, because `--dry-run` and the
key-check that guards a GPU job both run before any of that is available.
"""

MASK_SPLITS = ("continuations", "disinformation", "doubling_down_known_facts",
               "known_facts", "provided_facts", "statistics")

LB_SCENARIOS = ("instructed-deception", "harm-pressure-choice",
                "harm-pressure-knowledge-report", "convincing-game")

MASK_DATASETS = tuple("mask:%s" % split for split in MASK_SPLITS)
LB_DATASETS = tuple("lb:%s" % scenario for scenario in LB_SCENARIOS)

# Report order: local grader first, then the two judged benchmarks. A run whose
# key check fails should fail before anything expensive, but a run that gets
# through should produce its free numbers first.
ALL_DATASETS = ("sandbagging",) + MASK_DATASETS + LB_DATASETS

GROUPS = {"sandbagging": ("sandbagging",),
          "mask": MASK_DATASETS,
          "lb": LB_DATASETS,
          "liars-bench": LB_DATASETS,
          "all": ALL_DATASETS}

DEFAULT_BENCHMARKS = ALL_DATASETS


def list_benchmarks():
    return list(ALL_DATASETS)


def list_choices():
    """Everything `--benchmarks` accepts: the datasets plus the group names."""
    return list(ALL_DATASETS) + [name for name in GROUPS
                                 if name not in ALL_DATASETS]


def expand(names):
    """Group names to dataset names, order preserved, duplicates dropped."""
    out = []
    for name in names:
        for dataset in GROUPS.get(name, (name,)):
            if dataset not in out:
                out.append(dataset)
    unknown = [name for name in out if name not in ALL_DATASETS]
    if unknown:
        raise ValueError("unknown benchmark(s): %s\n  known: %s"
                         % (", ".join(unknown), ", ".join(list_choices())))
    return out


def get_benchmark(name):
    if name == "sandbagging":
        from .sandbagging import Sandbagging
        return Sandbagging()
    if name.startswith("mask:"):
        from .mask_bench import MaskSplit
        split = name[len("mask:"):]
        if split not in MASK_SPLITS:
            raise ValueError("unknown MASK split %r (have: %s)"
                             % (split, ", ".join(MASK_SPLITS)))
        return MaskSplit(split)
    if name.startswith("lb:"):
        from .liars_bench import get_scenario
        return get_scenario(name[len("lb:"):])
    raise ValueError("unknown benchmark %r (have: %s)"
                     % (name, ", ".join(list_choices())))


def required_keys(names):
    """-> {env var: [dataset, ...]} for the selected datasets.

    EVAL 5 calls this *before* loading the model. Judging is inline and
    fail-fast, so the alternative is discovering a missing key after an hour of
    generation, with nothing labelled and nothing to resume from.
    """
    needed = {}
    for name in expand(names):
        key = get_benchmark(name).requires_key
        if key:
            needed.setdefault(key, []).append(name)
    return needed
