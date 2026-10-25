"""
The real CLI on a real v2 cell, with the tiny model standing in for
Llama-3.1-8B (its vocabulary widened to the Llama tokenizer's so the real v2
prompts run through it on a CPU). One test per phase-1 analysis shape: the
post-clause neutral-twin sweep (S2p), named groups and greedy selection (1C),
a mean sweep (S4), DLA with the neutral twin and the lens crossing summary
(L), and the refusal of a post-clause plan on the nopressure condition (F).

nnsight 0.7.0 only; real tokenizer and datasets, skipped cleanly when absent.
"""

from __future__ import annotations

import json
import os

import pytest

nnsight = pytest.importorskip("nnsight")
if nnsight.__version__ != "0.7.0":
    pytest.skip("these are nnsight 0.7.0 behaviours", allow_module_level=True)

import torch                                                       # noqa: E402

import analyze_components                                          # noqa: E402
from component_analysis import dla, knockout as ko, registry       # noqa: E402
from tests.helpers import tiny_config                              # noqa: E402
from tests.test_component_analysis_v2_cli import (                 # noqa: E402, F401
    cell, read, real_tokenizer, run_cli, v2_run)

POST_CLAUSE = "after=pressure_clause,exclude=readout"
S2P_SUFFIX = "_neutral_twin_paired_after_pressure_clause_excl_readout"
#: DLA reads the whole test split (the descriptive loaders ignore the run's
#: test_samples, as on v1), and every v2 split has 1,000 rows.
WHOLE_SPLIT = 1000


@pytest.fixture
def tiny_llama(monkeypatch, real_tokenizer):
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    config = tiny_config(attn_implementation="sdpa")
    config.vocab_size = len(real_tokenizer)
    torch.manual_seed(0)
    wrapped = NNsight(LlamaForCausalLM(config).eval())
    monkeypatch.setattr(analyze_components, "load_model", lambda cli, resolved: wrapped)
    monkeypatch.setattr(registry, "ANALYSES", [dla, ko])
    return wrapped


def common(run_dir, out, *extra):
    return [str(run_dir), "--num-kv-heads", "2", "--device", "cpu", "--n-causal",
            "8", "--output-dir", str(out), *extra]


def knockout_dir(out):
    return os.path.join(cell(out), "knockout")


def test_the_post_clause_neutral_twin_sweep_records_every_choice(v2_run, tiny_llama):
    run_dir, out = v2_run()
    assert run_cli(*common(run_dir, out, "--analyses", "knockout",
                           "--knockout-completeness-sweep",
                           "--knockout-counterfactual", "neutral_twin",
                           "--knockout-positions", POST_CLAUSE,
                           "--knockout-sweep-exclude", "mlp.0.0")) == 0

    sweep = read(knockout_dir(out), "sweep.json")
    assert sweep["plan"] == {"scheme": "interchange", "counterfactual": "neutral_twin",
                             "positions": POST_CLAUSE, "column_suffix": S2P_SUFFIX}
    assert sweep["target_direction"] == "deceptive"
    assert sweep["excluded_from_ranking"] == ["mlp.0.0"]
    control = [row for row in sweep["components"] if row["label"] == "mlp.0.0"][0]
    assert control["rank"] is None and control["excluded_from_ranking"] is True

    instances = read(knockout_dir(out), sweep["instances_file"])
    assert len(instances["instance_ids"]) == 8
    assert len(instances["counterfactual_logit_difference"]) == 8
    # Under the twin plan the counterfactual run IS the twin's own margin.
    assert instances["neutral_twin_logit_difference"] == \
        instances["counterfactual_logit_difference"]
    assert len(instances["knocked_logit_difference"]) == 10     # 2 x (4 heads + 1 MLP)

    table = read(cell(out), "head_table.json")
    assert f"knockout.logit_diff_drop{S2P_SUFFIX}" in table["columns"]
    assert "knockout.logit_diff_drop" not in table["columns"]
    coverage = table["meta"]["coverage"][f"knockout.logit_diff_drop{S2P_SUFFIX}"]
    assert coverage["n"] == 8
    assert coverage["instance_set"].startswith("causal_sample_neutral_twin_paired:")
    assert coverage["details"]["sample_seed"] == 0


def test_groups_and_greedy_write_their_files_and_per_instance_rows(
        v2_run, tiny_llama, tmp_path):
    run_dir, out = v2_run()
    run_cli(*common(run_dir, out, "--analyses", "knockout",
                    "--knockout-completeness-sweep",
                    "--knockout-counterfactual", "neutral_twin",
                    "--knockout-positions", POST_CLAUSE))
    pool = os.path.join(knockout_dir(out), "sweep.json")
    groups = tmp_path / "groups.json"
    groups.write_text(json.dumps({"pair": [["head", 0, 0], ["mlp", 1, 0]],
                                  "one": [["head", 1, 3]]}))
    second = tmp_path / "second"

    assert run_cli(*common(run_dir, second, "--analyses", "knockout",
                           "--knockout-singles", "off",
                           "--knockout-counterfactual", "neutral_twin",
                           "--knockout-positions", POST_CLAUSE,
                           "--knockout-groups", str(groups),
                           "--knockout-greedy-pool", pool,
                           "--knockout-greedy-pool-size", "4",
                           "--knockout-greedy-k-max", "2")) == 0

    written = os.listdir(knockout_dir(second))
    assert "knockout.json" not in written
    result = read(knockout_dir(second), "groups.json")
    assert [row["name"] for row in result["groups"]] == ["pair", "one"]
    assert result["groups"][0]["members"] == ["head.0.0", "mlp.1.0"]
    assert result["source"]["path"] == str(groups)
    per_instance = read(knockout_dir(second), result["instances_file"])
    assert set(per_instance["knocked_logit_difference"]) == {"pair", "one"}
    assert len(per_instance["counterfactual_logit_difference"]) == 8

    greedy = read(knockout_dir(second), "greedy.json")
    assert [step["k"] for step in greedy["steps"]] == [1, 2]
    assert greedy["cost"]["group_knockouts"] == 4 + 3
    assert greedy["steps"][1]["members"][0] == greedy["steps"][0]["added"]
    assert all(row["label"] != "mlp.0.0" for row in greedy["pool"])


def test_a_mean_sweep_records_its_bank_and_writes_mean_columns(v2_run, tiny_llama):
    run_dir, out = v2_run()
    assert run_cli(*common(run_dir, out, "--analyses", "knockout",
                           "--knockout-completeness-sweep",
                           "--knockout-scheme", "mean")) == 0
    sweep = read(knockout_dir(out), "sweep.json")
    # The bank is the cell's whole test split (the descriptive loader does not
    # read --test-samples), as the evaluator's task bank is.
    assert sweep["mean_bank"]["n_instances"] == 1000
    assert sweep["counterfactual_run"]["n_instances"] == 0
    assert "knockout.logit_diff_drop_mean" in read(cell(out), "head_table.json")["columns"]
    # R19(1): a D cell's sweep keeps the twin's own margin under any plan.
    instances = read(knockout_dir(out), sweep["instances_file"])
    twin = instances["neutral_twin_logit_difference"]
    assert len(twin) == 8 and None not in twin


def test_dla_measures_the_neutral_twin_pair_and_the_lens_crossing(v2_run, tiny_llama):
    run_dir, out = v2_run()
    assert run_cli(*common(run_dir, out, "--analyses", "dla",
                           "--dla-conditions", "pressure,neutral_twin")) == 0

    payload = read(os.path.join(cell(out), "dla"), "dla.json")
    assert payload["conditions"]["neutral_twin"]["n_instances"] == WHOLE_SPLIT
    assert payload["conditions"]["neutral_twin"]["direction_sign"] == 1
    table = read(cell(out), "head_table.json")
    for column in ("dla.neutral_twin_paired", "dla.differential_neutral_twin_paired"):
        assert column in table["columns"]
        assert table["meta"]["coverage"][column]["n"] == WHOLE_SPLIT
    lens = read(os.path.join(cell(out), "dla"), "logit_lens.json")
    crossing = lens["crossing"]["conditions"]
    assert set(crossing) == {"pressure", "neutral_twin", "pressure_neutral_twin_paired"}
    one = crossing["neutral_twin"]["instances"][0]
    assert {"instance_id", "pressure_id", "first_layer_below", "final_sign",
            "honest_first", "last_sign_change_layer"} <= set(one)
    for name in (dla.PAIRED_SCATTER_TWIN_JSON_NAME, dla.PAIRED_LENS_TWIN_JSON_NAME,
                 dla.PAIRED_SCATTER_TWIN_PNG_NAME, dla.PAIRED_LENS_TWIN_PNG_NAME):
        assert os.path.exists(os.path.join(cell(out), "dla", name))


def test_dla_on_a_nopressure_cell_reads_the_crossing_in_the_deception_direction(
        v2_run, tiny_llama):
    run_dir, out = v2_run(condition="nopressure")
    assert run_cli(*common(run_dir, out, "--analyses", "dla",
                           "--dla-conditions", "pressure")) == 0
    payload = read(os.path.join(cell(out), "dla"), "dla.json")
    lens = read(os.path.join(cell(out), "dla"), "logit_lens.json")
    # The F rows' Target is the honest item: the stored lens is honest minus
    # deceptive, and the crossing summary turns it round.
    instances = lens["crossing"]["conditions"]["pressure"]["instances"]
    stored_final = lens["conditions"]["pressure"]["levels"]["all"]["mean"][-1]
    assert {one["condition"] for one in instances} == {"nopressure"}
    assert payload["conditions"]["pressure"]["n_instances"] == len(instances) == WHOLE_SPLIT
    turned = sum(one["final_margin"] for one in instances) / len(instances)
    assert turned == pytest.approx(-stored_final, abs=1e-5)
    assert abs(stored_final) > 0


def test_a_post_clause_plan_on_the_nopressure_condition_is_refused_at_dry_run(v2_run):
    run_dir, out = v2_run(condition="nopressure")
    with pytest.raises(ValueError, match="pressure_clause.*absent"):
        run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--analyses",
                "knockout", "--n-causal", "8", "--knockout-positions", POST_CLAUSE,
                "--output-dir", str(out))


def test_a_neutral_twin_plan_on_the_honest_condition_is_refused_at_dry_run(v2_run):
    run_dir, out = v2_run(condition="honest")
    with pytest.raises(ValueError, match="Neutral-Clause Twin itself"):
        run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--analyses",
                "knockout", "--n-causal", "8", "--knockout-counterfactual",
                "neutral_twin", "--output-dir", str(out))
