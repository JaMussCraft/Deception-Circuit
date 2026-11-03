"""Tests for scripts/neuron_partition_verdict.py (neuron-partition item-10 verdicts).

A synthetic cell is written in the exact rows.jsonl / summary.json schema of scripts/neuron_set_ablation.py, with
margins chosen so every number is known: D removed 0.6, I removed 0.1, no collateral, nulls well below. Each N1 bar
is then broken alone. The array metrics are checked against W2's own functions (`ladder_ratio`, `share`,
`removed_fraction`), the halves rule against W3's rank halves, and, when a real ablation cell exists, the whole-sample
numbers against its summary.json. CPU only, no network, no git.
"""

import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

np = pytest.importorskip("numpy")

from scripts import neuron_partition_verdict as V  # noqa: E402

DATA = os.path.join(REPO, "outputs", "_analyses", "neuron-partition", "data")
ABLATION = os.path.join(REPO, "outputs", "_analyses", "neuron-partition", "ablation")
N = 20


# ==============================================================================
# THE SYNTHETIC CELL
# ==============================================================================

def _ids(prefix, n=N):
    return [f"{prefix}{i:03d}" for i in range(n)]


def default_params(**over):
    p = {"size": 500, "d_drop": 6.0, "i_drop": 1.5, "h_wrong": 0, "f_wrong": 0, "ioi_wrong": 0,
         "h_m_abl": -7.0, "d_m_abl_rate": None}
    p.update(over)
    return p


def write_cell(directory, sets, *, references=("twin", "mean", "zero"), replay=None, n=N, noise=None):
    """sets: {name: params}. D/H/F ids d000.., I/N ids i000.., IOI ids ioi000.."""
    os.makedirs(directory, exist_ok=True)
    lines = []
    d_ids, i_ids, ioi_ids = _ids("d", n), _ids("i", n), _ids("ioi", 30)

    def per_id(value, k):
        if callable(value):
            return value(k)
        return value

    for ref in references:
        for name, p in sets.items():
            def add(cond, one, m_int, m_abl, twin, ok_abl, streams=("clean", "corrupt")):
                lines.append({
                    "reference": ref, "set": name, "condition": cond, "instance_id": one,
                    "m_intact": {s: m_int for s in streams}, "m_ablated": {s: m_abl for s in streams},
                    "argmax_intact": {s: 7 for s in streams},
                    "argmax_ablated": {s: (7 if ok_abl else 8) for s in streams},
                    "twin_m_intact": ({s: twin for s in streams} if twin is not None else {}),
                    "correct_token": {s: 7 for s in streams}, "opposite_token": {s: 7 for s in streams}})

            for k, one in enumerate(d_ids):
                jitter = 0.0 if noise is None else noise[k]
                add("D", one, 3.0, 3.0 - per_id(p["d_drop"], k) + jitter, -7.0, True)
            for k, one in enumerate(i_ids):
                add("I", one, 6.0, 6.0 - per_id(p["i_drop"], k), -9.0, True)
            for k, one in enumerate(d_ids):
                add("H", one, -7.0, per_id(p["h_m_abl"], k), None, k >= p["h_wrong"])
                if ref != "twin":
                    add("F", one, -6.0, -6.0, None, k >= p["f_wrong"])
            for one in i_ids:
                add("N", one, -9.0, -9.0, None, True)
            if ref != "twin":
                for k, one in enumerate(ioi_ids):
                    add(V.IOI, one, 2.0, 2.0, None, k >= p["ioi_wrong"], streams=("clean",))
    with open(os.path.join(directory, "rows.jsonl"), "w") as handle:
        for line in lines:
            handle.write(json.dumps(line) + "\n")
    summary = {"self_replay_error": replay or {"D": 0.0, "I": 0.0},
               "sets": {name: {"size": p["size"], "per_layer": {}} for name, p in sets.items()}}
    with open(os.path.join(directory, "summary.json"), "w") as handle:
        json.dump(summary, handle)
    return directory


def with_nulls(tested, klass="D_only", k=500, null_drop=lambda i: 0.2 * i):
    """The tested set plus 20 nulls whose D drop is 0, 0.2, ..., 3.8 (removed 0 to 0.38)."""
    sets = {klass: tested}
    for i in range(20):
        sets[f"null_{klass}_{k}_{i}"] = default_params(d_drop=null_drop(i), i_drop=0.0)
    return sets


def halves_map(n=N):
    out = {}
    for prefix in ("d", "i"):
        for k, one in enumerate(_ids(prefix, n)):
            out[one] = "AB"[k % 2]
    return out


def verdict_of(tmp_path, sets, **kw):
    cell = V.Cell(write_cell(str(tmp_path / "cell"), sets, **kw))
    subsets = V.keep_maps(None, halves_map())
    return V.analyse([cell], subsets, n_boot=200, seed=2), cell


# ==============================================================================
# THE NUMBERS
# ==============================================================================

def test_designed_numbers_and_a_full_pass(tmp_path):
    results, _ = verdict_of(tmp_path, with_nulls(default_params()))
    for ref in ("twin", "mean", "zero"):
        entry = results[ref]["D_only"]["500"]
        own = entry["subsets"]["whole"]["own"]
        assert own["D_removed_margin"] == pytest.approx(0.6)
        assert own["I_removed_margin"] == pytest.approx(0.1)
        assert own["D_removed_rate"] == pytest.approx(1.0)      # 3 -> -3 crosses the 0.7 margin
        assert own["I_removed_rate"] == pytest.approx(0.0)      # 6 -> 4.5 stays above it
        assert entry["subsets"]["whole"]["null"]["D_removed_margin"]["p95"] == pytest.approx(
            np.percentile([0.02 * i for i in range(20)], 95))
        for subset in V.SUBSETS:
            assert entry["subsets"][subset]["n1_bars"]["all"], (ref, subset)
    collateral = results["twin"]["D_only"]["500"]["subsets"]["whole"]["collateral_from_mean"]
    assert collateral == {"H_shift_points": 0.0, "F_shift_points": 0.0, "IOI_shift_points": 0.0}
    n1 = V.n1_summary(results)
    assert n1["deciding_references"] == ["twin", "mean"]
    assert n1["by_k"]["500"]["pass"] and n1["n1_pass_any_k"]


@pytest.mark.parametrize("change, bar", [
    ({"size": 2500}, "size_le_2000"),
    ({"d_drop": 4.0}, "D_removed_ge_0.50"),
    ({"i_drop": 6.0}, "I_removed_lt_0.25"),
    ({"h_wrong": 2}, "H_shift_lt_5"),           # 2 of 20 ids wrong: -10 points
    ({"f_wrong": 2}, "F_shift_lt_5"),
    ({"ioi_wrong": 3}, "IOI_shift_lt_5"),       # 3 of 30: -10 points
])
def test_each_n1_bar_fails_alone(tmp_path, change, bar):
    results, _ = verdict_of(tmp_path, with_nulls(default_params(**change)))
    bars = results["mean"]["D_only"]["500"]["subsets"]["whole"]["n1_bars"]
    failed = [name for name, b in bars.items() if name != "all" and not b["passed"]]
    assert failed == [bar]
    assert not V.n1_summary(results)["by_k"]["500"]["pass"]


def test_the_null_bar_fails_alone(tmp_path):
    results, _ = verdict_of(tmp_path, with_nulls(default_params(), null_drop=lambda i: 7.0))
    bars = results["twin"]["D_only"]["500"]["subsets"]["whole"]["n1_bars"]
    assert [n for n, b in bars.items() if n != "all" and not b["passed"]] == ["beats_null_p95"]


def test_a_tiny_gap_is_uninterpretable_never_a_pass(tmp_path):
    sets = with_nulls(default_params())
    results, _ = verdict_of(tmp_path, sets, replay={"D": 2.0, "I": 0.0})   # epsilon 20 > G = 10
    own = results["mean"]["D_only"]["500"]["subsets"]["whole"]["own"]
    assert own["D_removed_margin"] is None
    assert "epsilon" in own["detail"]["D"]["reason"]
    bar = results["mean"]["D_only"]["500"]["subsets"]["whole"]["n1_bars"]["D_removed_ge_0.50"]
    assert bar["passed"] is False and bar["value"] is None


def test_a_half_that_fails_makes_a_lead_not_a_pass(tmp_path):
    # D drop 6 on half A ids (even k) and 2 on half B: whole 0.4 fails, half A 0.6 passes.
    tested = default_params(d_drop=lambda k: 6.0 if k % 2 == 0 else 2.0)
    results, _ = verdict_of(tmp_path, with_nulls(tested))
    subsets = results["twin"]["D_only"]["500"]["subsets"]
    assert subsets["half1"]["n1_bars"]["all"] and not subsets["whole"]["n1_bars"]["all"]
    summary = V.n1_summary(results)["by_k"]["500"]
    assert not summary["pass"] and summary["lead"]


@pytest.mark.parametrize("h_wrong, d_drop, expected", [
    (6, 0.0, "bypass"),                      # H -30 points, D rate unchanged
    (6, 6.0, "suppression or shared"),       # H -30 points, D rate -100 points
    (2, 0.0, "undetermined at this size"),   # H only -10
])
def test_n2_verdicts(tmp_path, h_wrong, d_drop, expected):
    sets = with_nulls(default_params(h_wrong=h_wrong, d_drop=d_drop), klass="H_only")
    results, _ = verdict_of(tmp_path, sets)
    n2 = results["mean"]["H_only"]["500"]["subsets"]["whole"]["n2"]
    assert n2["verdict"] == expected


def test_n2_needs_the_null_to_leave_h_alone(tmp_path):
    sets = {"H_only": default_params(h_wrong=6, d_drop=0.0)}
    for i in range(20):
        sets[f"null_H_only_500_{i}"] = default_params(h_wrong=6, d_drop=0.0)
    results, _ = verdict_of(tmp_path, sets)
    n2 = results["mean"]["H_only"]["500"]["subsets"]["whole"]["n2"]
    assert n2["null_H_shift_p95_abs"] == pytest.approx(30.0)
    assert n2["verdict"] == "undetermined at this size"


def test_k_comes_from_the_null_names_and_a_suffix(tmp_path):
    sets = with_nulls(default_params(), klass="DI_shared", k=1000)
    sets["D_only_2000"] = default_params()
    cell = V.Cell(write_cell(str(tmp_path / "cell"), sets))
    tested = V.tested_sets(cell)
    assert tested["DI_shared"]["k"] == 1000 and len(tested["DI_shared"]["nulls"]) == 20
    assert tested["D_only_2000"] == {"class": "D_only", "k": 2000, "nulls": []}


# ==============================================================================
# AGREEMENT WITH W2'S FUNCTIONS
# ==============================================================================

def test_the_array_metrics_equal_w2s_functions(tmp_path):
    from scripts import neuron_set_ablation as A
    rng = np.random.default_rng(0)
    noise = rng.normal(0, 2.0, N)
    tested = default_params(d_drop=lambda k: float(rng.uniform(0, 8)), h_m_abl=lambda k: float(rng.normal(-1, 3)))
    sets = {"D_only": tested}
    cell = V.Cell(write_cell(str(tmp_path / "cell"), sets, noise=noise))
    with open(tmp_path / "cell" / "rows.jsonl") as handle:
        lines = [json.loads(t) for t in handle]

    def dicts(ref, cond, field):
        out = {}
        for line in lines:
            if line["reference"] == ref and line["condition"] == cond and line["set"] == "D_only":
                for s, v in line[field].items():
                    out.setdefault(s, {})[line["instance_id"]] = v
        return out

    for ref in ("twin", "mean"):
        mine = V.effect(cell, ref, "D_only", "D", None)
        m_int, m_abl, m_tw = dicts(ref, "D", "m_intact"), dicts(ref, "D", "m_ablated"), dicts(ref, "D", "twin_m_intact")
        ids = sorted(m_int["clean"])
        theirs = A.ladder_ratio(m_int, m_abl, m_tw, ids, 1e-6)
        assert mine["margin"] == pytest.approx(theirs["fraction_removed"])
        assert mine["G"] == pytest.approx(theirs["G"])
        rate = lambda d: A.share(d, ids, lambda v: v >= 0.7)                     # noqa: E731
        if ref == "twin":
            e_int, e_abl = rate(m_int) - rate(m_tw), rate(m_abl) - rate(m_tw)
        else:
            h_int, h_abl = dicts(ref, "H", "m_intact"), dicts(ref, "H", "m_ablated")
            e_int, e_abl = rate(m_int) - rate(h_int), rate(m_abl) - rate(h_abl)
        expected = A.removed_fraction(e_int, e_abl)
        assert (mine["rate"] is None and expected is None) or mine["rate"] == pytest.approx(expected)


def test_bootstrap_is_seeded_and_brackets_the_estimate(tmp_path):
    rng = np.random.default_rng(1)
    noise = rng.normal(0, 1.5, N)
    results, cell = verdict_of(tmp_path, with_nulls(default_params()), noise=noise)
    point = results["twin"]["D_only"]["500"]["subsets"]["whole"]["own"]["D_removed_margin"]
    a = V.bootstrap(cell, "twin", "D_only", "D", None, n=300, seed=2)
    b = V.bootstrap(cell, "twin", "D_only", "D", None, n=300, seed=2)
    assert a == b
    assert a["margin"]["lo"] <= point <= a["margin"]["hi"]
    assert a["margin"]["hi"] - a["margin"]["lo"] > 0


# ==============================================================================
# HALVES AND THE CLI
# ==============================================================================

@pytest.mark.skipif(not os.path.exists(os.path.join(DATA, "far_rank_ids.json")), reason="W3's rank ids absent")
def test_the_halves_rule_reproduces_w3s_rank_halves():
    """R10 asks for the rank-half rule on the test sample; recovering it here proves it is the same rule."""
    datasets = pytest.importorskip("datasets")
    from scripts.neuron_partition_data import split_halves
    with open(os.path.join(DATA, "far_rank_ids.json")) as handle:
        halves = json.load(handle)["halves"]
    ids = halves["A"] + halves["B"]
    d = datasets.load_from_disk(V.DEFAULT_D_DIR)
    cluster = {}
    for split in ("train", "validation"):
        for record in d[split]:
            cluster[record["instance_id"]] = record["pressure_id"]
    got = split_halves(ids, [cluster[one] for one in ids], seed=2)
    assert sorted(i for i, h in got.items() if h == "A") == sorted(halves["A"])


@pytest.mark.skipif(not os.path.exists(V.DEFAULT_SAMPLE), reason="seed-2 test sample absent")
def test_sample_halves_use_the_rule_and_balance():
    pytest.importorskip("datasets")
    with open(V.DEFAULT_SAMPLE) as handle:
        sample = json.load(handle)
    halves, info = V.sample_halves(sample, d_dir=V.DEFAULT_D_DIR, i_dir=V.DEFAULT_I_DIR)
    assert info["method"].startswith("split_halves")
    assert set(halves) == set(sample["ids"]["D"]) | set(sample["ids"]["I"])
    counts = [sum(1 for h in halves.values() if h == x) for x in "AB"]
    assert abs(counts[0] - counts[1]) <= 1
    for cond in ("D", "I"):
        a, b = info["counts"][cond]["A"], info["counts"][cond]["B"]
        assert a + b == 300 and abs(a - b) <= 30


def test_cli_writes_verdict_files(tmp_path):
    write_cell(str(tmp_path / "cell"), with_nulls(default_params()))
    halves = tmp_path / "halves.json"
    halves.write_text(json.dumps(halves_map()))
    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps({"ids": {"D": _ids("d"), "I": _ids("i")}}))
    out = tmp_path / "out"
    assert V.main(["--cell", str(tmp_path / "cell"), "--sample", str(sample), "--halves-json", str(halves),
                   "--bootstrap", "100", "--output-dir", str(out)]) == 0
    verdict = json.loads((out / "verdict.json").read_text())
    assert set(verdict["results"]) == {"twin", "mean", "zero"}
    assert verdict["n1"]["by_k"]["500"]["pass"]
    assert verdict["choices"]["halves"]["method"].startswith("precomputed")
    entry = verdict["results"]["twin"]["D_only"]["500"]
    assert set(entry["subsets"]) == set(V.SUBSETS)
    assert entry["bootstrap"]["D"]["margin"]["lo"] is not None
    text = (out / "verdict.md").read_text()
    assert "## Reference: twin" in text and "## N1 (D_only)" in text and "| 500 |" in text


# ==============================================================================
# A REAL ABLATION CELL (when one exists)
# ==============================================================================

def _real_cells():
    if not os.path.isdir(ABLATION):
        return []
    out = []
    for base, _dirs, files in os.walk(ABLATION):
        if "rows.jsonl" in files and "summary.json" in files:
            out.append(base)
    return sorted(out)


REAL = _real_cells()
ROW_KEYS = {"reference", "set", "condition", "instance_id", "m_intact", "m_ablated", "argmax_intact",
            "argmax_ablated", "twin_m_intact", "correct_token", "opposite_token"}


@pytest.mark.skipif(not REAL, reason="no real ablation cell yet")
@pytest.mark.parametrize("directory", REAL)
def test_real_cell_whole_sample_equals_its_summary(directory):
    with open(os.path.join(directory, "rows.jsonl")) as handle:
        first = json.loads(handle.readline())
    assert ROW_KEYS <= set(first)
    cell = V.Cell(directory)
    checked = 0
    for name, block in cell.summary["sets"].items():
        for ref, by_ref in block["references"].items():
            for cond, eff in by_ref.get("effects", {}).items():
                mine = V.effect(cell, ref, name, cond, None)
                theirs = eff["ladder_margin_ratio"]
                if theirs["fraction_removed"] is None:
                    assert mine["margin"] is None
                else:
                    assert mine["margin"] == pytest.approx(theirs["fraction_removed"], abs=1e-9)
                if eff["rate"].get("fraction_removed") is None:
                    assert mine["rate"] is None
                else:
                    assert mine["rate"] == pytest.approx(eff["rate"]["fraction_removed"], abs=1e-9)
                checked += 1
            for cond, col in by_ref.get("collateral", {}).items():
                if col is None:
                    continue
                mine = V.accuracy_shift(cell, ref, name, cond, None)
                assert mine == pytest.approx(col["accuracy_argmax_shift_points"], abs=1e-9)
                checked += 1
    assert checked
