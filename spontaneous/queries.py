"""B3 query sets (plan sections 1.1 and 2): OR-Bench-Hard-1K, XSTest safe prompts and MMLU items.

The selection functions are pure: they take source rows and a seed and never look at model behaviour. `download`
fetches the raw files at pinned hub revisions into a fresh directory and records their sha256; `build` turns those
files into the committed JSON under `data/b3/`. Downloaded files are untrusted data: they are only parsed (CSV and
parquet), never executed.

    /u/swong2/.conda/envs/mgnp/bin/python -m spontaneous.queries download data/b3/_downloads
    /u/swong2/.conda/envs/mgnp/bin/python -m spontaneous.queries build data/b3/_downloads data/b3

Python's `random.Random` is used for every draw, so the selection is identical on both interpreters.
"""
import argparse
import csv
import hashlib
import json
import os
import random
from pathlib import Path

EXCLUDED_CATEGORIES = ("sexual", "self-harm")
LETTERS = "ABCD"

SOURCES = {
    "or_bench": {"repo": "bench-llm/or-bench", "revision": "e36d8b80e81837c8a8f264bbb2a49f1b32c7e272",
                 "file": "or-bench-hard-1k.csv"},
    "xstest": {"repo": "natolambert/xstest-v2-copy", "revision": "b71afe2a6d10e5a6254ea8bcb006c48b095a15d5",
               "file": "data/prompts-00000-of-00001.parquet"},
    "mmlu": {"repo": "cais/mmlu", "revision": "c30699e8356da336a370243923dbaf21066bb9fe",
             "file": "all/test-00000-of-00001.parquet", "config": "all"},
}


# ------------------------------------------------------------------------------------------------ selection


def select_af_queries(rows, seed=0, n_per_category=15, n_calibration=20, exclude=EXCLUDED_CATEGORIES):
    """Stratified draw from OR-Bench rows ({"prompt", "category"}), split into calibration and test.

    Equal allocation: `n_per_category` prompts from each kept category (sorted by name), drawn with
    `rng.sample` over that category's source indices. The calibration split takes the first
    `n_calibration // k` drawn prompts of every category plus one more from `n_calibration % k` categories chosen
    by the same generator; the rest is the test split. Disjoint by construction.
    """
    rng = random.Random(seed)
    cats = sorted({r["category"] for r in rows} - set(exclude))
    drawn = {}
    for c in cats:
        idx = [i for i, r in enumerate(rows) if r["category"] == c]
        if len(idx) < n_per_category:
            raise ValueError(f"category {c!r} has {len(idx)} rows, fewer than {n_per_category}")
        drawn[c] = rng.sample(idx, n_per_category)
    base, extra = divmod(n_calibration, len(cats))
    plus = set(rng.sample(cats, extra))

    def item(i):
        return {"id": f"orb-{i:04d}", "source_index": i, "category": rows[i]["category"],
                "prompt": rows[i]["prompt"]}

    cal, test = [], []
    for c in cats:
        k = base + (1 if c in plus else 0)
        cal += [item(i) for i in drawn[c][:k]]
        test += [item(i) for i in drawn[c][k:]]
    return {"calibration": cal, "test": test}


def select_xstest_safe(rows, seed=0, per_type=10):
    """`per_type` prompts from each safe XSTest type (every type not starting with `contrast_`)."""
    rng = random.Random(seed)
    types = sorted({r["type"] for r in rows if not r["type"].startswith("contrast_")})
    out = []
    for t in types:
        idx = [i for i, r in enumerate(rows) if r["type"] == t]
        for i in rng.sample(idx, per_type):
            out.append({"id": rows[i]["id"], "source_index": i, "type": t, "prompt": rows[i]["prompt"]})
    return out


def select_mmlu(rows, n=800, seed=0):
    """`n` MMLU items drawn without replacement, each with a seeded wrong cue letter."""
    rng = random.Random(seed)
    idx = sorted(rng.sample(range(len(rows)), n))
    out = []
    for i in idx:
        r = rows[i]
        gold = LETTERS[int(r["answer"])]
        cue = rng.choice([L for L in LETTERS if L != gold])
        out.append({"id": f"mmlu-{i:05d}", "source_index": i, "subject": r["subject"], "question": r["question"],
                    "choices": [str(c) for c in r["choices"]], "answer": int(r["answer"]),
                    "answer_letter": gold, "cue_letter": cue})
    return out


# ------------------------------------------------------------------------------------------------ io


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _local(dest, key):
    s = SOURCES[key]
    return Path(dest) / s["repo"].replace("/", "__") / s["file"]


def download(dest):
    """Fetch the three source files at their pinned revisions into `dest` (login node; the hub is reachable)."""
    from huggingface_hub import hf_hub_download
    os.makedirs(dest, exist_ok=True)
    manifest = {}
    for key, s in SOURCES.items():
        path = hf_hub_download(s["repo"], s["file"], repo_type="dataset", revision=s["revision"],
                               local_dir=str(Path(dest) / s["repo"].replace("/", "__")))
        manifest[key] = dict(s, sha256=sha256_file(path), bytes=os.path.getsize(path))
    (Path(dest) / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def _source(dest, key):
    s = SOURCES[key]
    path = _local(dest, key)
    return dict(s, sha256=sha256_file(path),
                url=f"https://huggingface.co/datasets/{s['repo']}/blob/{s['revision']}/{s['file']}")


def read_or_bench(dest):
    with open(_local(dest, "or_bench"), newline="", encoding="utf-8") as f:
        return [{"prompt": r["prompt"], "category": r["category"]} for r in csv.DictReader(f)]


def _read_parquet(path):
    import pandas as pd
    return pd.read_parquet(path).to_dict("records")


def build(dest, out, seed=0):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    split = select_af_queries(read_or_bench(dest), seed=seed)
    af = {"source": _source(dest, "or_bench"), "seed": seed,
          "selection": ("OR-Bench-Hard-1K without sexual and self-harm; 15 per remaining category (8), "
                        "random.Random(seed).sample per category in sorted category order; calibration takes the "
                        "first 2 of each category plus a third from 4 categories drawn by the same generator"),
          "calibration": split["calibration"], "test": split["test"]}
    (out / "af_queries.json").write_text(json.dumps(af, indent=1, ensure_ascii=False) + "\n")

    xs = select_xstest_safe(_read_parquet(_local(dest, "xstest")), seed=seed)
    xsj = {"source": dict(_source(dest, "xstest"), canonical="Paul/XSTest (xstest_prompts.csv); this copy holds "
                          "the same 450 prompts with their type labels"),
           "seed": seed, "selection": "10 per safe type (types not starting with contrast_), 10 types",
           "items": xs}
    (out / "xstest_safe.json").write_text(json.dumps(xsj, indent=1, ensure_ascii=False) + "\n")

    mm = select_mmlu(_read_parquet(_local(dest, "mmlu")), n=800, seed=seed)
    mmj = {"source": _source(dest, "mmlu"), "seed": seed,
           "selection": ("800 test rows by random.Random(seed).sample over row indices, sorted; cue_letter drawn "
                         "uniformly from the three wrong letters by the same generator in that order"),
           "items": mm}
    (out / "syc_items.json").write_text(json.dumps(mmj, indent=1, ensure_ascii=False) + "\n")
    return {"af": len(af["calibration"]) + len(af["test"]), "xstest": len(xs), "mmlu": len(mm)}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download")
    d.add_argument("dest")
    b = sub.add_parser("build")
    b.add_argument("dest")
    b.add_argument("out")
    b.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    if a.cmd == "download":
        print(json.dumps(download(a.dest), indent=1))
    else:
        print(json.dumps(build(a.dest, a.out, seed=a.seed)))


if __name__ == "__main__":
    main()
