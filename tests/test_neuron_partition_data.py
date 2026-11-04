"""scripts/neuron_partition_data.py: the fresh test sample, the split halves and the matched nulls.

CPU only and model-free. The draw and null tests run on synthetic records; the tests of the
written sample read `outputs/_analyses/neuron-partition/data/` and skip when it is absent.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from scripts import neuron_partition_data as npd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "outputs" / "_analyses" / "neuron-partition" / "data"


def _records(n, prefix="id"):
    rows = []
    for i in range(n):
        rows.append({"instance_id": f"{prefix}{i:04d}",
                     "designation_polarity": ("identity", "inversion")[i % 2],
                     "item_polarity": 1 + (i // 2) % 2,
                     "template_variant": ("audit", "lab")[(i // 4) % 2],
                     "pressure_id": f"p{i % 5}",
                     "pressure": "Answer the reviewer's question with the wrong result."})
    return rows


# ------------------------------------------------------------------------------ the draw

def test_draw_excludes_every_excluded_id_and_pairs_by_id():
    rows = _records(200)
    all_ids = [r["instance_id"] for r in rows]
    excluded = all_ids[::3]                      # 67 ids
    no_twin = {"id0001", "id0005"}               # present in D, absent from H
    h_ids = [i for i in all_ids if i not in no_twin]
    draw = npd.draw_condition(rows, twin_id_sets=[h_ids, all_ids], exclude_ids=excluded,
                              n=100, seed=2)
    ids = draw["ids"]
    assert len(ids) == 100 == len(set(ids))
    assert not set(ids) & set(excluded)
    assert not set(ids) & no_twin
    assert set(ids) <= set(h_ids)
    assert draw["counts"]["dropped_no_twin"] == 2
    assert draw["counts"]["eligible"] == 200 - 2 - len(set(excluded) - no_twin)


def test_draw_is_deterministic_for_seed_2_and_moves_with_the_seed():
    rows = _records(300)
    kw = dict(twin_id_sets=[[r["instance_id"] for r in rows]], exclude_ids=["id0000"], n=120)
    a = npd.draw_condition(rows, seed=2, **kw)["ids"]
    b = npd.draw_condition(list(reversed(rows)), seed=2, **kw)["ids"]
    c = npd.draw_condition(rows, seed=3, **kw)["ids"]
    assert a == npd.draw_condition(rows, seed=2, **kw)["ids"]
    assert sorted(a) == sorted(b)                # row order does not decide which ids
    assert sorted(a) != sorted(c)


def test_draw_takes_all_survivors_when_fewer_than_n():
    rows = _records(50)
    draw = npd.draw_condition(rows, twin_id_sets=[[r["instance_id"] for r in rows]],
                              exclude_ids=[r["instance_id"] for r in rows[:10]], n=300, seed=2)
    assert draw["counts"]["drawn"] == 40


def test_form_filter_by_id_reads_the_d_row():
    d_rows = _records(4)
    d_rows[1]["pressure"] = "Show the reviewer whichever result is passing."   # predicate form
    pool = [dict(r, pressure="The facility employs around sixty people.") for r in d_rows]
    keep = npd.act_naming_by_id(d_rows)
    assert [keep(r) for r in pool] == [True, False, True, True]
    with pytest.raises(ValueError):
        keep({"instance_id": "missing"})


# ------------------------------------------------------------------------------ --exclude-ids

def test_load_exclude_file_reads_per_condition_dicts_and_flat_lists(tmp_path):
    per = tmp_path / "per.json"
    per.write_text(json.dumps({"seed": 2, "ids": {"D": ["a", "b"], "H": ["a", "b"], "I": ["c"]}}))
    flat_ids = tmp_path / "flat_ids.json"
    flat_ids.write_text(json.dumps({"ids": ["x", "y", "x"]}))
    flat = tmp_path / "flat.json"
    flat.write_text(json.dumps(["p", "q"]))
    a = npd.load_exclude_file(str(per))
    assert a["ids"] == ["a", "b", "c"] and a["per_condition_in_file"] == {"D": 2, "H": 2, "I": 1}
    assert a["sha256"] == npd.sha256_file(str(per))
    assert npd.load_exclude_file(str(flat_ids))["ids"] == ["x", "y"]
    assert npd.load_exclude_file(str(flat))["ids"] == ["p", "q"]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"ids": {"D": "a"}}))
    with pytest.raises(ValueError):
        npd.load_exclude_file(str(bad))


def _fake_sample_env(monkeypatch, tmp_path, n_d=240, n_i=200):
    """Synthetic D/H/F and I/N splits behind `cmd_sample`, with the real-file readers stubbed."""
    d = {split: _records(n_d, prefix=f"{split[:2]}") for split in ("train", "validation", "test")}
    pool = {split: [dict(r) for r in rows[:n_i]] for split, rows in d.items()}
    by_cond = {"far_v2": d, "far_v2_honest": d, "far_v2_nopressure": d,
               "far_v2_user_inversion": pool, "far_v2_user_neutral": pool}
    monkeypatch.setattr(npd, "load_split_records",
                        lambda path, split: [dict(r) for r in by_cond[os.path.basename(path)][split]])
    monkeypatch.setattr(npd, "hash_tree", lambda root: {})
    real_sha = npd.sha256_file
    monkeypatch.setattr(npd, "sha256_file",
                        lambda path: real_sha(path) if os.path.isfile(path) else "absent")
    fixed = {"a1_assessment": {"path": "design.json", "sha256": "x",
                               "ids": [f"te{i:04d}" for i in range(0, 20)]}}
    monkeypatch.setattr(npd, "exclusion_sources", lambda task_key="far_v2": {
        k: dict(v) for k, v in fixed.items()})
    out = tmp_path / "data"
    out.mkdir()
    (out / "pools_manifest.json").write_text(json.dumps({"pools": {
        "far_v2_user_inversion": {"files": {}, "source": "s"},
        "far_v2_user_neutral": {"files": {}, "source": "s"}}}))
    return out, fixed["a1_assessment"]["ids"]


def test_sample_exclude_ids_removes_a_prior_sample_from_every_pool(monkeypatch, tmp_path, capsys):
    out, fixed = _fake_sample_env(monkeypatch, tmp_path)
    assert npd.main(["sample", "--n", "60", "--seed", "2", "--out-dir", str(out),
                     "--no-rank-ids"]) == 0
    prior_path = out / "far_test_sample_seed2.json"
    prior = json.loads(prior_path.read_text())
    assert not (out / "far_rank_ids.json").exists()             # --no-rank-ids writes none
    capsys.readouterr()
    assert npd.main(["sample", "--n", "60", "--seed", "3", "--out-dir", str(out), "--no-rank-ids",
                     "--exclude-ids", str(prior_path)]) == 0
    fresh = json.loads((out / "far_test_sample_seed3.json").read_text())
    barred = set(fixed) | {i for v in prior["ids"].values() for i in v}
    for cond in ("D", "H", "F", "I", "N"):
        assert len(fresh["ids"][cond]) == 60
        assert not set(fresh["ids"][cond]) & barred, cond
    ex = fresh["excluded"]["exclude_ids_0"]
    assert ex["sha256"] == npd.sha256_file(str(prior_path))
    assert ex["path"].endswith("far_test_sample_seed2.json")
    assert ex["per_condition_in_file"] == {c: 60 for c in ("D", "H", "F", "I", "N")}
    # the draw is balanced as before: the 8 strata of the 3 factors within one of each other
    for label in ("D", "I"):
        counts = [len(s["instance_ids"]) for s in fresh["samples"][label]["strata"]]
        assert len(counts) == 8 and max(counts) - min(counts) <= 1
    # every pool shrank by exactly the prior sample's ids it held, from every condition of
    # the prior file (a prior I id is barred from the fresh D pool too)
    prior_union = set(prior["ids"]["D"]) | set(prior["ids"]["I"])
    assert len(prior_union) > 60
    assert fresh["counts"]["D"]["eligible"] == prior["counts"]["D"]["eligible"] - len(prior_union)
    i_pool = {f"te{i:04d}" for i in range(200)}
    assert fresh["counts"]["I"]["eligible"] == prior["counts"]["I"]["eligible"] - len(
        prior_union & i_pool)


def test_sample_count_only_counts_without_drawing(monkeypatch, tmp_path, capsys):
    out, fixed = _fake_sample_env(monkeypatch, tmp_path)
    flat = tmp_path / "more.json"
    flat.write_text(json.dumps([f"te{i:04d}" for i in range(20, 60)]))
    capsys.readouterr()
    assert npd.main(["sample", "--count-only", "--out-dir", str(out),
                     "--exclude-ids", str(flat)]) == 0
    got = json.loads(capsys.readouterr().out)
    assert got["D"]["eligible"] == 240 - 60 and got["D"]["max_n_balanced_draw"] == 180
    assert got["I"]["eligible"] == 200 - 60
    assert got["D"]["n_strata"] == 8
    assert got["D"]["max_n_equal_share"] == 8 * min(got["D"]["strata"].values())
    assert not list(out.glob("far_test_sample_seed*.json"))     # nothing drawn or written


# ------------------------------------------------------------------------------ split halves

def test_split_halves_balanced_per_cluster_and_overall():
    rows = _records(203)
    ids = [r["instance_id"] for r in rows]
    clusters = [r["pressure_id"] for r in rows]
    halves = npd.split_halves(ids, clusters, seed=2)
    assert set(halves) == set(ids) and set(halves.values()) == {"A", "B"}
    total = Counter(halves.values())
    assert abs(total["A"] - total["B"]) <= 1
    for cluster in set(clusters):
        c = Counter(halves[i] for i, k in zip(ids, clusters) if k == cluster)
        assert abs(c["A"] - c["B"]) <= 1
    assert npd.split_halves(list(reversed(ids)), list(reversed(clusters)), seed=2) == halves
    assert npd.split_halves(ids, clusters, seed=5) != halves


def test_split_halves_refuses_duplicates():
    with pytest.raises(ValueError):
        npd.split_halves(["a", "a"], ["x", "x"])


# ------------------------------------------------------------------------------ matched nulls

TESTED = {3: [0, 5, 14335], 17: list(range(100, 140)), 31: [7]}


def test_nulls_preserve_size_and_per_layer_counts_and_avoid_tested_neurons():
    nulls = npd.matched_nulls(TESTED, k=20, seed=2)
    assert len(nulls) == 20
    for null in nulls:
        assert {l: len(v) for l, v in null.items()} == {l: len(v) for l, v in TESTED.items()}
        for layer, idx in null.items():
            assert len(set(idx)) == len(idx)
            assert not set(idx) & set(TESTED[layer])
            assert all(0 <= i < npd.INTERMEDIATE for i in idx)
    assert len({json.dumps(n, sort_keys=True) for n in nulls}) == 20


def test_nulls_are_seeded_per_draw():
    a = npd.matched_nulls(TESTED, k=5, seed=2)
    assert a == npd.matched_nulls(TESTED, k=5, seed=2)
    assert npd.matched_null(TESTED, seed=2, index=3) == a[3]   # draw k stands alone
    assert a != npd.matched_nulls(TESTED, k=5, seed=7)


def test_null_refuses_a_layer_with_no_room():
    full = {0: list(range(npd.INTERMEDIATE // 2 + 1))}
    with pytest.raises(ValueError):
        npd.matched_null(full, seed=2, index=0)


@pytest.mark.parametrize("bad", [
    [], [["head", 3, 1]], [["mlp_hidden", 32, 0]], [["mlp_hidden", 0, 14336]],
    [["mlp_hidden", 1, 2], ["mlp_hidden", 1, 2]], [["mlp_hidden", 1]],
])
def test_parse_neuron_set_refuses_malformed_sets(bad):
    with pytest.raises(ValueError):
        npd.parse_neuron_set(bad)


def test_nulls_cli_writes_a_flat_groups_file_and_a_provenance_sidecar(tmp_path):
    src = tmp_path / "set.json"
    src.write_text(json.dumps({"d_only": npd.to_members(TESTED)}))
    out = tmp_path / "groups.json"
    assert npd.main(["nulls", str(src), "--out", str(out), "-k", "20"]) == 0
    groups = json.loads(out.read_text())
    assert list(groups) == ["d_only"] + [f"null_{i}" for i in range(20)]
    tested = set(map(tuple, groups["d_only"]))
    for name, members in groups.items():
        assert isinstance(members, list) and members
        assert all(len(m) == 3 and m[0] == "mlp_hidden" for m in members)
        assert Counter(m[1] for m in members) == Counter(m[1] for m in groups["d_only"])
        if name != "d_only":
            assert not set(map(tuple, members)) & tested
    prov = json.loads((tmp_path / "groups.provenance.json").read_text())
    assert prov["seed"] == 2 and prov["k"] == 20 and prov["size"] == 44
    assert prov["source"]["sha256"] == npd.sha256_file(str(src))
    assert prov["output"]["sha256"] == npd.sha256_file(str(out))


def test_nulls_cli_needs_set_when_several(tmp_path):
    src = tmp_path / "sets.json"
    src.write_text(json.dumps({"a": npd.to_members(TESTED), "b": [["mlp_hidden", 0, 1]]}))
    with pytest.raises(SystemExit):
        npd.main(["nulls", str(src), "--out", str(tmp_path / "o.json")])
    assert npd.main(["nulls", str(src), "--set", "b", "--out", str(tmp_path / "o.json"), "-k", "3"]) == 0
    assert list(json.loads((tmp_path / "o.json").read_text())) == ["b", "null_0", "null_1", "null_2"]


# ------------------------------------------------------------------------------ the written sample

def _load(name):
    path = DATA / name
    if not path.exists():
        pytest.skip(f"{path} not built (run scripts/neuron_partition_data.py sample)")
    return json.loads(path.read_text())


def test_written_sample_meets_the_id_contract():
    s = _load("far_test_sample_seed2.json")
    ids = s["ids"]
    assert s["seed"] == 2 and s["task"] == "far"
    assert all(len(ids[c]) >= 300 for c in ("D", "H", "F")) and len(ids["I"]) > 0
    assert ids["H"] == ids["D"] and ids["F"] == ids["D"] and ids["N"] == ids["I"]
    for label, ex in s["excluded"].items():
        if label == "union":
            continue
        assert not set(ex["ids"]) & set(ids["D"]), label
        assert not set(ex["ids"]) & set(ids["I"]), label
    assert s["excluded"]["a1_assessment"]["n"] == 100
    assert s["excluded"]["mech_heldout_D"]["n"] == 100 and s["excluded"]["mech_heldout_I"]["n"] == 100


def test_written_rank_ids_are_train_and_validation_and_halves_balance():
    r = _load("far_rank_ids.json")
    s = _load("far_test_sample_seed2.json")
    rank = set(r["ids"]["D"]["train"]) | set(r["ids"]["D"]["validation"])
    assert not rank & set(s["ids"]["D"]) and not rank & set(s["ids"]["I"])
    a, b = set(r["halves"]["A"]), set(r["halves"]["B"])
    assert a | b == rank and not a & b and abs(len(a) - len(b)) <= 1
    for counts in r["halves"]["per_stratum"].values():
        assert abs(counts.get("A", 0) - counts.get("B", 0)) <= 1
    i_rank = set(r["ids"]["I"]["train"]) | set(r["ids"]["I"]["validation"])
    assert set(r["halves"]["I_A"]) | set(r["halves"]["I_B"]) == i_rank
    assert set(r["halves"]["I_A"]) <= a and set(r["halves"]["I_B"]) <= b


# ------------------------------------------------------------------------------ the fetch glob

def test_b2_fetch_brings_back_neuron_partition(tmp_path):
    import re

    b2 = ROOT / "scripts" / "remote" / "b2.sh"
    match = re.search(r"^FETCH_ANALYSIS_GLOBS=\((.*)\)\s*$", b2.read_text(), flags=re.M)
    assert "neuron-partition*" in re.findall(r'"([^"]+)"', match.group(1))
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("no bash")
    env = dict(os.environ, DC_DELTA_REPO_ROOT=str(tmp_path))
    done = subprocess.run([bash, str(b2), "fetch", "--dry"], cwd=str(ROOT), env=env,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    (line,) = [one for one in done.stdout.splitlines() if "outputs/_analyses/" in one]
    assert "--include=/neuron-partition*/***" in line
