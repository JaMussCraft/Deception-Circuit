"""Ticket 04: HEAD reproduces every stored v2 prompt (spec 8.4).

For each built v2 task under data/datasets/, every prompt of D, H and F is
re-rendered from `provenance.json` (framing verbatim, shared clauses, neutral
pool, make_spec arguments) plus the row's instance fields, with the current
`dataset/deception_v2.py` and `dataset/clause_surgery.py`, and compared byte for
byte. The pool and source sha256s recorded at build time must match the files
on disk: a later edit to a pool or to the scaffold fails this test loudly.
Skips cleanly when the datasets are absent. `check_built_task` is reused on
CPU-built datasets by tests/test_build_v2.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import random

import pytest

from dataset import deception_common as dc

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data", "datasets")
TASKS = ("far_v2", "sdr_v2", "ser_v2")
SPLITS = ("train", "validation", "test")


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def check_hashes(prov):
    """[] when every pool and source file still has its build-time sha256."""
    bad = []
    for name, entry in prov["sha256"]["pools"].items():
        got = _sha(_abs(entry["path"]))
        if got != entry["sha256"]:
            bad.append(f"pool {name} ({entry['path']}): {got} != {entry['sha256']}")
    for path, want in prov["sha256"]["sources"].items():
        got = _sha(_abs(path))
        if got != want:
            bad.append(f"source {path}: {got} != {want}")
    return bad


def _clause_text(prov, task, slot):
    if slot < 20:
        c = prov["framing"]["clauses"][task][slot]
        return c["text"]
    return prov["shared_clauses"][slot - 20]


def render_task(prov, task):
    """A function row -> {condition: {column: expected string}} built only
    from provenance and the row's instance fields."""
    from dataset import deception_v2 as v2
    from dataset.clause_surgery import remove_clause, replace_clause

    ms = prov["make_spec"]
    spec = v2.make_spec(task, ms["suffix"] == "on", ms["ser_wording"],
                        overrides=ms["overrides"] or None)
    neutral = {s["id"]: s["text"] for s in prov["neutral_pool"]["sentences"]}
    hi = prov["scaffold"]["honest_instruction"]

    def render(row):
        clause = _clause_text(prov, task, row["pressure_slot"])
        built = v2.build_prompt_pair(spec, row["template_variant"], row["entity"],
                                     (row["item_1"], row["item_2"]), row["item_polarity"],
                                     row["designation_polarity"], clause)
        ntext = neutral[row["neutral_id"]]
        cols = ("clean_prompt", "corrupt_prompt", "neutral_prompt")
        out = {
            "D": {c: built[c] for c in cols},
            "H": {c: replace_clause(built[c], clause, ntext) for c in cols},
            "F": {c: remove_clause(built[c], clause) for c in cols},
        }
        his = {"honest_instruction_clean_prompt": replace_clause(built["clean_prompt"],
                                                                 clause, hi),
               "honest_instruction_corrupt_prompt": replace_clause(built["corrupt_prompt"],
                                                                   clause, hi)}
        for k in out:
            out[k].update(his)
        out["D"].update(pressure=clause, target=built["target"],
                        distractor=built["distractor"])
        out["H"].update(pressure=ntext, neutral_text=ntext, target=built["distractor"],
                        distractor=built["target"])
        out["F"].update(pressure="", target=built["distractor"], distractor=built["target"])
        return out

    return render


def check_built_task(data_dir, task):
    """Assert byte equality of every stored prompt and label of D, H and F;
    returns the number of rows checked per condition."""
    from datasets import load_from_disk

    base = os.path.join(data_dir, task)
    with open(os.path.join(base, "provenance.json")) as f:
        prov = json.load(f)
    bad = check_hashes(prov)
    assert not bad, "provenance sha256 mismatch:\n" + "\n".join(bad)
    render = render_task(prov, task)
    dsets = {k: load_from_disk(base + sfx) for k, sfx in
             (("D", ""), ("H", "_honest"), ("F", "_nopressure"))}
    n = 0
    for split in SPLITS:
        ids = [dsets[k][split]["instance_id"] for k in dsets]
        assert ids[0] == ids[1] == ids[2], f"{task}/{split}: D/H/F ids differ"
        rows = {k: dsets[k][split] for k in dsets}
        for i in range(len(rows["D"])):
            d = rows["D"][i]
            inst = {f: d[f] for f in dc.INSTANCE_FACTORS}
            assert dc.instance_id(inst) == d["instance_id"]
            want = render(d)
            for k in ("D", "H", "F"):
                row = rows[k][i]
                for col, val in want[k].items():
                    assert row[col] == val, (f"{task}/{split}/{k} {d['instance_id']} "
                                             f"{col} does not re-render")
            n += 1
    return n


def _built(task):
    return os.path.exists(os.path.join(DATA_DIR, task, "provenance.json"))


@pytest.mark.parametrize("task", TASKS)
def test_every_stored_v2_prompt_re_renders_byte_for_byte(task):
    if not _built(task):
        pytest.skip(f"{task} is not built under data/datasets")
    n = check_built_task(DATA_DIR, task)
    assert n > 0


@pytest.mark.parametrize("task", TASKS)
def test_stored_neutral_choice_reproduces_with_the_llama_tokenizer(task):
    """The neutral sentence is re-selected (equal-length candidates, sha1 of
    the instance id) for a seeded sample of rows."""
    if not _built(task):
        pytest.skip(f"{task} is not built under data/datasets")
    transformers = pytest.importorskip("transformers")
    try:
        tok = transformers.AutoTokenizer.from_pretrained(dc.DEFAULT_MODEL)
    except Exception as e:  # offline / not cached / gated
        pytest.skip(f"Llama tokenizer unavailable: {type(e).__name__}: {e}")
    from datasets import load_from_disk

    from dataset import deception_v2 as v2
    with open(os.path.join(DATA_DIR, task, "provenance.json")) as f:
        prov = json.load(f)
    render = render_task(prov, task)
    pool = prov["neutral_pool"]["sentences"]
    rows = load_from_disk(os.path.join(DATA_DIR, task))["test"]
    for i in random.Random(0).sample(range(len(rows)), min(25, len(rows))):
        r = rows[i]
        d = render(r)["D"]
        clause = _clause_text(prov, task, r["pressure_slot"])
        got = v2.select_neutral(tok, [d["clean_prompt"], d["corrupt_prompt"]], clause, pool,
                                r["instance_id"])
        assert got["id"] == r["neutral_id"], r["instance_id"]


def test_a_changed_pool_fails_the_hash_check(tmp_path):
    pool = tmp_path / "pool.json"
    pool.write_text("[1]")
    prov = {"sha256": {"pools": {"neutral_pool": {"path": str(pool),
                                                   "sha256": _sha(str(pool))}},
                       "sources": {}}}
    assert check_hashes(prov) == []
    pool.write_text("[2]")
    assert check_hashes(prov) and "neutral_pool" in check_hashes(prov)[0]
