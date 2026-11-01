"""
Tests for `scripts/falsity_probe_capture.py`, the B2 P1 capture entrypoint (instructed-route ticket T6).

CPU only. The datasets are tiny `DatasetDict`s written to `tmp_path` with whitespace prompts, the tokenizer is
`tests.fakes.FakeWordTokenizer` and the model is a fake capturer that returns deterministic tensors from the prompt it
was given. Those tests run on both interpreters. One test drives the real `hooks` / `dla` capture on a tiny Llama under
nnsight 0.7.0 and is skipped elsewhere, as `tests/test_dla_model.py` is. The real-plan tests read the worktree's
datasets and id files and skip when they are absent.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest
import torch

from tests.fakes import FAKE_VOCAB_SIZE, FakeWordTokenizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "falsity_probe_capture.py")
JOBS = os.path.join(ROOT, "docs", "research", "instructed-route", "jobs")


def load_module():
    spec = importlib.util.spec_from_file_location("falsity_probe_capture", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mod():
    return load_module()


# ==============================================================================
# FIXTURE DATA
# ==============================================================================

CONDITION_OF = {"far_v2": "deceptive", "far_v2_honest": "honest",
                "far_v2_nopressure": "nopressure", "far_v2_inversion": "inversion"}

#: Train, validation and test ids are disjoint, as in the real v2 builds.
SPLIT_IDS = {"train": [f"tr{i:02d}" for i in range(6)],
             "validation": [f"va{i:02d}" for i in range(6)],
             "test": [f"te{i:02d}" for i in range(20)]}
SEED0 = SPLIT_IDS["test"][0:4]
SEED1 = SPLIT_IDS["test"][4:8]
#: The I split holds a subset of the test ids, some of them in each sample.
INVERSION_IDS = ["te01", "te05", "te09", "te10", "te11", "te15", "te17", "te19"]
#: HI margins: one row at exactly the bar, one just under, one far under.
HI_MARGIN = {"va01": 0.2999, "va02": 0.3, "va03": -1.0, "te09": 0.1}

CLEAN_WORDS = 8
HI_WORDS = 14
MAX_SEQ = 12          # shorter than the HI prompt, so the HI cell must widen it


def make_record(instance_id, index, name):
    condition = CONDITION_OF[name]
    honest, deceptive = ("alpha", "beta") if index % 2 == 0 else ("beta", "alpha")
    if condition in ("deceptive", "inversion"):
        target, distractor = deceptive, honest
    else:
        target, distractor = honest, deceptive
    clause = {"deceptive": "lie", "honest": "neutral", "nopressure": "",
              "inversion": "drill"}[condition]
    words = ["sys", instance_id, clause or "plain", "say", "which", "result", "is", "failing"]
    assert len(words) == CLEAN_WORDS
    hi_words = ["sys", instance_id, "be", "honest", "and", "accurate", "with", "the", "reviewer",
                "please", "which", "result", "is", "failing"]
    assert len(hi_words) == HI_WORDS
    # As in the real v2 builds: under "inversion" the designated item is the honest one, under "identity" the other.
    polarity = "inversion" if index % 4 < 2 else "identity"
    designated = honest if polarity == "inversion" else deceptive
    return {
        "instance_id": instance_id, "condition": condition, "task": "far_v2",
        "item_1": "alpha", "item_2": "beta", "clean_item_d": designated,
        "designation_polarity": polarity,
        "target": target, "distractor": distractor,
        "pressure_id": f"clause_{index % 3}", "pressure": clause,
        "framing_id": "r8_rule_strong",
        "clean_prompt": " ".join(words),
        "honest_instruction_clean_prompt": " ".join(hi_words),
        "h_honest_instruction_clean": HI_MARGIN.get(instance_id, 2.0),
        "clean_margin": 1.5 if condition in ("deceptive", "inversion") else 3.0,
    }


def write_dataset(root, name, splits):
    from datasets import Dataset, DatasetDict

    path = os.path.join(root, name)
    DatasetDict({split: Dataset.from_list(rows) for split, rows in splits.items()}) \
        .save_to_disk(path)
    with open(os.path.join(path, "dataset_config.json"), "w") as handle:
        json.dump({"task": "far_v2", "condition": CONDITION_OF[name],
                   "max_seq_length": MAX_SEQ}, handle)
    return path


def write_ids(path, ids):
    with open(path, "w") as handle:
        handle.write("".join(f"{one}\n" for one in ids))
    return path


@pytest.fixture
def world(tmp_path):
    """Datasets, id files and a plan exercising every condition and id form."""
    data = tmp_path / "datasets"
    data.mkdir()
    dirs = {}
    for name in ("far_v2", "far_v2_honest", "far_v2_nopressure"):
        dirs[name] = write_dataset(str(data), name, {
            split: [make_record(one, i, name) for i, one in enumerate(ids)]
            for split, ids in SPLIT_IDS.items()})
    index = {one: i for i, one in enumerate(SPLIT_IDS["test"])}
    dirs["far_v2_inversion"] = write_dataset(str(data), "far_v2_inversion", {
        "test": [make_record(one, index[one], "far_v2_inversion") for one in INVERSION_IDS]})
    groups = tmp_path / "groups"
    groups.mkdir()
    seed0 = write_ids(str(groups / "far_seed0_ids.txt"), SEED0)
    seed1 = write_ids(str(groups / "far_seed1_ids.txt"), SEED1)
    chosen = write_ids(str(groups / "chosen_ids.txt"), ["te12", "te03", "te18"])
    flags = {"in_seed0_sample": seed0, "in_seed1_sample": seed1}
    exclude = [seed0, seed1]
    hi_keep = {"field": "h_honest_instruction_clean", "min": 0.3}

    def cell(name, role, condition, dataset, split, **extra):
        prompt = "honest_instruction_clean_prompt" if condition == "HI" else "clean_prompt"
        out = {"name": name, "role": role, "task": "far_v2", "condition": condition,
               "dataset": dirs[dataset], "split": split, "prompt_field": prompt,
               "flag_id_files": flags}
        out.update(extra)
        return out

    plan = {
        "schema": "falsity-probe-capture-plan/1",
        "model": "llama-tiny", "seed": 0, "batch_size": 4,
        "cells": [
            cell("far_fit_D", "fit", "D", "far_v2", "train"),
            cell("far_fit_H", "fit", "H", "far_v2_honest", "train"),
            cell("far_select_HI", "select", "HI", "far_v2", "validation", keep_if=hi_keep),
            cell("far_gate_D", "far_gate", "D", "far_v2", "test", exclude_id_files=exclude),
            cell("far_gate_H", "far_gate", "H", "far_v2_honest", "test",
                 exclude_id_files=exclude),
            cell("far_gate_HI", "far_gate", "HI", "far_v2", "test", exclude_id_files=exclude,
                 keep_if=hi_keep),
            cell("far_gate_F", "far_gate", "F", "far_v2_nopressure", "test",
                 exclude_id_files=exclude),
            cell("far_gate_I", "far_gate", "I", "far_v2_inversion", "test",
                 exclude_id_files=exclude),
            cell("far_chosen_D", "fit", "D", "far_v2", "test", id_file=chosen),
        ],
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=1))
    return {"plan": plan, "plan_path": str(plan_path), "dirs": dirs, "tmp": tmp_path,
            "seed0": seed0, "seed1": seed1, "groups": groups}


def records_by_id(world, dataset, split):
    from datasets import load_from_disk

    return {row["instance_id"]: dict(row)
            for row in load_from_disk(world["dirs"][dataset])[split]}


def no_model(*args, **kwargs):
    raise AssertionError("a dry run must not load a model")


def no_tokenizer(*args, **kwargs):
    raise AssertionError("a dry run without --check-encoding must not load a tokenizer")


def read_rows(out, cell):
    with open(os.path.join(out, f"rows.{cell}.jsonl")) as handle:
        return [json.loads(line) for line in handle]


# ==============================================================================
# A FAKE CAPTURE
# ==============================================================================

class FakeCapturer:
    """Deterministic stand-in for the model capture.

    The residual at every layer boundary is the sum of the row's unpadded input ids plus the layer index, so a row's
    residual names the prompt it came from. The logit of the honest column is +2 and of the deceptive column -1 on
    every row, so the model's target-minus-distractor margin is +3 exactly when the target is the honest item.
    """

    def __init__(self, layers=2, hidden=8, vocab=FAKE_VOCAB_SIZE):
        self.keys = [("embed", 0, 0), ("head", 0, 0), ("mlp", 0, 0)]
        self.layers, self.hidden, self.vocab = layers, hidden, vocab
        self.calls = []

    def __call__(self, input_ids, attention_mask, readout, token_ids):
        self.calls.append({"input_ids": input_ids.clone(),
                           "attention_mask": attention_mask.clone(),
                           "readout": readout.clone(), "token_ids": token_ids.clone()})
        batch = input_ids.shape[0]
        rows = torch.arange(batch)
        signature = (input_ids * attention_mask).sum(-1).float()
        resid = (signature.view(batch, 1, 1)
                 + torch.arange(self.layers + 1).float().view(1, -1, 1)
                 + torch.zeros(batch, 1, self.hidden))
        logits = torch.zeros(batch, self.vocab)
        logits[rows, token_ids[:, 0]] = 2.0
        logits[rows, token_ids[:, 1]] = -1.0
        centred = logits.gather(1, token_ids) - logits.mean(-1, keepdim=True)
        dla = torch.zeros(batch, len(self.keys), token_ids.shape[1])
        dla[:, 0, :] = 0.25 * centred
        dla[:, 2, :] = 0.75 * centred
        return {"resid": resid, "logits": logits, "dla": dla}


@pytest.fixture
def fake_run(mod, world, monkeypatch):
    """A full (not dry) run on the fixture with the fake capturer. -> (out dir, capturer, tokenizer, summary)."""
    tokenizer = FakeWordTokenizer()
    capturer = FakeCapturer()
    monkeypatch.setattr(mod, "load_tokenizer", lambda name: tokenizer)
    monkeypatch.setattr(mod, "load_model", lambda name, device: "the model")
    monkeypatch.setattr(mod, "make_capturer", lambda model: capturer)
    out = str(world["tmp"] / "out")
    summary = mod.run(world["plan_path"], out, argv=["--plan", world["plan_path"]])
    return out, capturer, tokenizer, summary


# ==============================================================================
# DRY RUN: COUNTS, IDS AND THE MANIFEST
# ==============================================================================

EXPECTED_GATE = [one for one in SPLIT_IDS["test"] if one not in SEED0 + SEED1]


def test_dry_run_counts_and_ids_match_the_plan(mod, world, capsys):
    summary = mod.run(world["plan_path"], str(world["tmp"] / "dry"), dry_run=True,
                      argv=["--dry-run"], load_model_fn=no_model,
                      load_tokenizer_fn=no_tokenizer)
    cells = summary["cells"]
    assert cells["far_fit_D"]["ids"] == SPLIT_IDS["train"]
    assert cells["far_fit_H"]["ids"] == SPLIT_IDS["train"]
    assert cells["far_gate_D"]["ids"] == EXPECTED_GATE
    assert cells["far_gate_H"]["ids"] == EXPECTED_GATE
    assert cells["far_gate_F"]["ids"] == EXPECTED_GATE
    # The id file's order is kept.
    assert cells["far_chosen_D"]["ids"] == ["te12", "te03", "te18"]
    assert summary["total_rows"] == sum(len(c["ids"]) for c in cells.values())

    printed = capsys.readouterr().out
    for name, cell in cells.items():
        assert f"{name}" in printed
        assert str(len(cell["ids"])) in printed
    assert f"total {summary['total_rows']}" in printed


def test_the_exclude_form_subtracts_both_id_files(mod, world):
    summary = mod.run(world["plan_path"], str(world["tmp"] / "dry"), dry_run=True,
                      argv=[], load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)
    gate_i = summary["cells"]["far_gate_I"]
    assert gate_i["ids"] == [one for one in INVERSION_IDS if one not in SEED0 + SEED1]
    assert gate_i["report"]["n_split"] == len(INVERSION_IDS)
    assert gate_i["report"]["n_excluded"] == 2          # te01 in seed 0; te05 in seed 1
    assert set(gate_i["report"]["exclude_id_files"]) == {world["seed0"], world["seed1"]}
    assert summary["cells"]["far_gate_D"]["report"]["n_excluded"] == 8


def test_the_hi_filter_keeps_rows_at_the_bar_and_reports_the_kept_share(mod, world):
    summary = mod.run(world["plan_path"], str(world["tmp"] / "dry"), dry_run=True,
                      argv=[], load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)
    select = summary["cells"]["far_select_HI"]
    assert "va02" in select["ids"]                       # exactly 0.3 is kept
    assert "va01" not in select["ids"] and "va03" not in select["ids"]
    assert select["report"]["n_before_filter"] == 6
    assert select["report"]["n_kept_by_filter"] == 4
    assert select["report"]["kept_share"] == pytest.approx(4 / 6)
    gate = summary["cells"]["far_gate_HI"]
    assert gate["ids"] == [one for one in EXPECTED_GATE if one != "te09"]


def test_dry_run_loads_no_model_and_writes_the_manifest_and_the_counts(mod, world):
    out = str(world["tmp"] / "dry")
    mod.run(world["plan_path"], out, dry_run=True, argv=["--plan", "x", "--dry-run"],
            load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)
    with open(os.path.join(out, "run_manifest.json")) as handle:
        manifest = json.load(handle)
    assert manifest["argv"] == ["--plan", "x", "--dry-run"]
    assert manifest["seed"] == 0
    assert manifest["model"] == "llama-tiny"
    assert manifest["git_fingerprint_error"] == "disabled"      # tests/conftest.py
    hashed = " ".join(manifest["dataset_files"])
    assert "far_v2_inversion" in hashed and "far_seed0_ids.txt" in hashed
    assert "plan.json" in hashed
    with open(os.path.join(out, "capture_plan.json")) as handle:
        resolved = json.load(handle)
    assert resolved["cells"]["far_gate_D"]["n_rows"] == len(EXPECTED_GATE)
    assert resolved["dry_run"] is True
    # No capture file is written by a dry run.
    assert not [name for name in os.listdir(out) if name.startswith(("rows.", "resid.", "tokens."))]


def test_dry_run_fails_on_an_id_missing_from_the_split(mod, world):
    plan = dict(world["plan"])
    bad = write_ids(str(world["groups"] / "bad.txt"), ["te12", "nope99"])
    plan["cells"] = [dict(plan["cells"][0], name="far_bad", split="test", id_file=bad)]
    path = world["tmp"] / "bad_plan.json"
    path.write_text(json.dumps(plan))
    with pytest.raises(SystemExit, match="nope99"):
        mod.run(str(path), str(world["tmp"] / "dry"), dry_run=True, argv=[],
                load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)


def test_an_exclude_id_missing_from_the_d_split_fails(mod, world):
    """A mispointed exclude file must not silently subtract nothing. Exclusions are checked against the task's test
    split (the one the samples were drawn from), so an I cell may exclude ids it does not hold."""
    plan = dict(world["plan"])
    bad = write_ids(str(world["groups"] / "bad_exclude.txt"), ["te01", "zz00"])
    plan["cells"] = [dict(plan["cells"][3], exclude_id_files=[bad])]
    path = world["tmp"] / "bad_plan.json"
    path.write_text(json.dumps(plan))
    with pytest.raises(SystemExit, match="zz00"):
        mod.run(str(path), str(world["tmp"] / "dry"), dry_run=True, argv=[],
                load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)


def test_a_cell_whose_dataset_is_not_its_condition_is_refused(mod, world):
    plan = dict(world["plan"])
    plan["cells"] = [dict(plan["cells"][0], condition="H")]      # H read from the D split
    path = world["tmp"] / "bad_plan.json"
    path.write_text(json.dumps(plan))
    with pytest.raises(SystemExit, match="condition"):
        mod.run(str(path), str(world["tmp"] / "dry"), dry_run=True, argv=[],
                load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)


def test_a_record_whose_designation_contradicts_its_condition_is_refused(mod, world):
    """The honest item comes from the condition; a record that disagrees (an H twin with swapped answers) stops the
    run rather than inverting every honest/deceptive column T7 reads."""
    from datasets import Dataset, DatasetDict

    rows = [make_record(one, i, "far_v2_honest") for i, one in enumerate(SPLIT_IDS["train"])]
    rows[3]["target"], rows[3]["distractor"] = rows[3]["distractor"], rows[3]["target"]
    path = os.path.join(str(world["tmp"]), "swapped", "far_v2_honest")
    DatasetDict({"train": Dataset.from_list(rows)}).save_to_disk(path)
    with open(os.path.join(path, "dataset_config.json"), "w") as handle:
        json.dump({"task": "far_v2", "condition": "honest", "max_seq_length": MAX_SEQ}, handle)
    plan = dict(world["plan"])
    plan["cells"] = [dict(plan["cells"][1], dataset=path)]
    plan_path = world["tmp"] / "bad_plan.json"
    plan_path.write_text(json.dumps(plan))
    with pytest.raises(SystemExit, match="tr03"):
        mod.run(str(plan_path), str(world["tmp"] / "dry"), dry_run=True, argv=[],
                load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)


def test_hi_must_read_the_honest_instruction_prompt(mod, world):
    plan = dict(world["plan"])
    plan["cells"] = [dict(plan["cells"][2], prompt_field="clean_prompt")]
    path = world["tmp"] / "bad_plan.json"
    path.write_text(json.dumps(plan))
    with pytest.raises(SystemExit, match="honest_instruction_clean_prompt"):
        mod.run(str(path), str(world["tmp"] / "dry"), dry_run=True, argv=[],
                load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)


def test_max_rows_caps_every_cell(mod, world):
    summary = mod.run(world["plan_path"], str(world["tmp"] / "dry"), dry_run=True, max_rows=2,
                      argv=[], load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)
    for cell in summary["cells"].values():
        assert len(cell["ids"]) <= 2
    assert summary["cells"]["far_gate_D"]["ids"] == EXPECTED_GATE[:2]


def test_the_plan_max_rows_applies_and_the_flag_overrides_it(mod, world):
    plan = dict(world["plan"], max_rows=3)
    path = world["tmp"] / "smoke_plan.json"
    path.write_text(json.dumps(plan))
    summary = mod.run(str(path), str(world["tmp"] / "dry"), dry_run=True, argv=[],
                      load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)
    assert len(summary["cells"]["far_gate_D"]["ids"]) == 3
    summary = mod.run(str(path), str(world["tmp"] / "dry2"), dry_run=True, max_rows=1, argv=[],
                      load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)
    assert len(summary["cells"]["far_gate_D"]["ids"]) == 1


def test_check_encoding_widens_past_max_seq_length_for_the_longer_hi_prompt(mod, world):
    tokenizer = FakeWordTokenizer()
    summary = mod.run(world["plan_path"], str(world["tmp"] / "dry"), dry_run=True,
                      check_encoding=True, argv=[], load_model_fn=no_model,
                      load_tokenizer_fn=lambda name: tokenizer)
    assert summary["cells"]["far_select_HI"]["report"]["max_length"] == HI_WORDS
    assert summary["cells"]["far_fit_D"]["report"]["max_length"] == MAX_SEQ
    assert summary["cells"]["far_select_HI"]["report"]["max_prefix_length"] == HI_WORDS


def test_main_dry_run_prints_counts(mod, world, monkeypatch, capsys):
    monkeypatch.setattr(mod, "load_model", no_model)
    monkeypatch.setattr(mod, "load_tokenizer", no_tokenizer)
    code = mod.main(["--plan", world["plan_path"], "--output-dir", str(world["tmp"] / "dry"),
                     "--dry-run"])
    assert code == 0
    printed = capsys.readouterr().out
    assert "far_gate_I" in printed and "dry run" in printed


# ==============================================================================
# FULL RUN WITH THE FAKE CAPTURE
# ==============================================================================

def test_h_rows_map_the_target_to_the_honest_item(fake_run, world):
    out, _capturer, tokenizer, _summary = fake_run
    honest_records = records_by_id(world, "far_v2_honest", "train")
    for row in read_rows(out, "far_fit_H"):
        record = honest_records[row["instance_id"]]
        assert row["honest_item"] == record["target"]
        assert (row["honest_item"] == record["clean_item_d"]) == \
            (record["designation_polarity"] == "inversion")
        assert row["honest_token"] == row["target_token"] == tokenizer.encode(" " + record["target"])[0]
        assert row["deceptive_token"] == row["distractor_token"]
        assert row["model_margin"] == pytest.approx(3.0)        # target is the honest item
        assert row["model_honest_margin"] == pytest.approx(3.0)
    for row in read_rows(out, "far_fit_D"):
        assert row["honest_token"] == row["distractor_token"]
        assert row["deceptive_token"] == row["target_token"]
        assert row["model_margin"] == pytest.approx(-3.0)
        assert row["model_honest_margin"] == pytest.approx(3.0)
        assert row["dataset_margin_field"] == "clean_margin"
        assert row["dataset_margin"] == row["clean_margin"] == 1.5


def test_hi_rows_target_the_honest_item_and_carry_the_hi_margin(fake_run, world):
    out, _c, _t, _s = fake_run
    records = records_by_id(world, "far_v2", "validation")
    for row in read_rows(out, "far_select_HI"):
        record = records[row["instance_id"]]
        assert row["target_item"] == record["distractor"] == row["honest_item"]
        assert row["distractor_item"] == record["target"]
        assert row["dataset_margin_field"] == "h_honest_instruction_clean"
        assert row["dataset_margin"] == record["h_honest_instruction_clean"]
        assert row["clean_margin"] == record["clean_margin"]
        assert row["model_margin"] == pytest.approx(3.0)


def test_hi_readout_is_prefix_length_minus_one_with_the_right_residual_shape(fake_run, world):
    out, capturer, tokenizer, _s = fake_run
    rows = read_rows(out, "far_select_HI")
    for row in rows:
        assert row["prefix_length"] == HI_WORDS
        assert row["readout"] == HI_WORDS - 1
    hi_calls = [call for call in capturer.calls if call["input_ids"].shape[1] == HI_WORDS]
    assert hi_calls, "the HI cell was encoded at its own widened length"
    for call in hi_calls:
        assert torch.equal(call["readout"], call["attention_mask"].sum(-1) - 1)
    resid = torch.load(os.path.join(out, "resid.far_select_HI.pt"))
    assert resid["resid"].shape == (len(rows), capturer.layers + 1, capturer.hidden)
    assert resid["resid"].dtype == torch.float16
    assert resid["ids"] == [row["instance_id"] for row in rows]
    # Row i of the residual is the prompt of line i of rows.jsonl.
    prompts = records_by_id(world, "far_v2", "validation")
    for i, row in enumerate(rows):
        signature = sum(tokenizer.encode(prompts[row["instance_id"]]["honest_instruction_clean_prompt"]))
        assert float(resid["resid"][i, 0, 0]) == pytest.approx(signature, rel=1e-3)


def test_tokens_file_holds_three_logit_forms_and_per_token_dla(fake_run):
    out, capturer, _t, _s = fake_run
    rows = read_rows(out, "far_gate_I")
    tokens = torch.load(os.path.join(out, "tokens.far_gate_I.pt"))
    n = len(rows)
    assert tokens["ids"] == [row["instance_id"] for row in rows]
    assert tokens["token_order"] == ["honest", "deceptive"]
    assert tokens["token_ids"].shape == (n, 2)
    assert tokens["token_ids"][:, 0].tolist() == [row["honest_token"] for row in rows]
    assert tokens["token_ids"][:, 1].tolist() == [row["deceptive_token"] for row in rows]
    assert tokens["keys"] == [list(key) for key in capturer.keys]
    assert tokens["logits_raw"].shape == (n, 2)
    assert torch.allclose(tokens["logits_raw"][:, 0], torch.full((n,), 2.0))
    assert torch.allclose(tokens["logits_raw"][:, 1], torch.full((n,), -1.0))
    log_z = torch.logsumexp(torch.cat([torch.tensor([2.0, -1.0]),
                                       torch.zeros(FAKE_VOCAB_SIZE - 2)]), 0)
    assert torch.allclose(tokens["logits_logsoftmax"][:, 0], 2.0 - log_z)
    mean = (2.0 - 1.0) / FAKE_VOCAB_SIZE
    assert torch.allclose(tokens["logits_centred"][:, 0], torch.full((n,), 2.0 - mean))
    assert tokens["dla"].shape == (n, len(capturer.keys), 2)
    assert tokens["dla"].dtype == torch.float32
    assert torch.allclose(tokens["dla"].sum(1), tokens["logits_centred"], atol=1e-6)
    for row in rows:
        assert row["condition"] == "I" and row["role"] == "far_gate"
        assert row["honest_token"] == row["distractor_token"]


def test_rows_carry_the_clause_the_sample_flags_and_the_cell(fake_run):
    out, _c, _t, _s = fake_run
    rows = read_rows(out, "far_chosen_D")
    assert [row["instance_id"] for row in rows] == ["te12", "te03", "te18"]
    assert [row["in_seed0_sample"] for row in rows] == [False, True, False]
    assert [row["in_seed1_sample"] for row in rows] == [False, False, False]
    for i, row in enumerate(rows):
        assert row["row"] == i
        assert row["cell"] == "far_chosen_D" and row["task"] == "far_v2"
        assert row["pressure_id"].startswith("clause_") and row["pressure"] == "lie"
        assert row["items"] == ["alpha", "beta"]
        assert len(row["item_token_ids"]) == 2
        assert row["item_token_ids"][row["honest_item_index"]] == row["honest_token"]


def test_the_summary_records_the_margin_check_and_the_dla_sum(fake_run):
    out, _c, _t, summary = fake_run
    with open(os.path.join(out, "capture_summary.json")) as handle:
        written = json.load(handle)
    gate = written["cells"]["far_gate_D"]
    assert gate["n_rows"] == len(EXPECTED_GATE)
    # The fake margin is -3 on every D row against a dataset margin of 1.5.
    assert gate["margin_mean_abs_diff"] == pytest.approx(4.5)
    assert gate["dla_sum_max_abs_error"] == pytest.approx(0.0, abs=1e-6)
    assert gate["resid_nonfinite"] == 0
    assert written["total_rows"] == summary["total_rows"]


def test_a_residual_beyond_fp16_is_counted_not_hidden(mod, world, monkeypatch):
    """bf16 holds values past fp16's 65504; the cast makes them inf. The count is recorded, the cell is kept."""

    class Huge(FakeCapturer):
        def __call__(self, *args):
            out = super().__call__(*args)
            out["resid"][:, -1, 0] = 1e6
            return out

    monkeypatch.setattr(mod, "load_tokenizer", lambda name: FakeWordTokenizer())
    monkeypatch.setattr(mod, "load_model", lambda name, device: "the model")
    monkeypatch.setattr(mod, "make_capturer", lambda model: Huge())
    out = str(world["tmp"] / "huge")
    mod.run(world["plan_path"], out, argv=[])
    with open(os.path.join(out, "capture_summary.json")) as handle:
        gate = json.load(handle)["cells"]["far_gate_D"]
    assert gate["resid_nonfinite"] == len(EXPECTED_GATE)
    assert os.path.isfile(os.path.join(out, "resid.far_gate_D.pt"))


def test_a_rerun_skips_completed_cells(mod, world, fake_run, monkeypatch):
    out, capturer, _t, _s = fake_run
    calls = len(capturer.calls)
    mod.run(world["plan_path"], out, argv=[])
    assert len(capturer.calls) == calls


# ==============================================================================
# THE REAL CAPTURE ON A TINY LLAMA (nnsight 0.7.0 only)
# ==============================================================================

def test_the_real_capture_adds_up_on_a_tiny_llama(mod, world, monkeypatch):
    nnsight = pytest.importorskip("nnsight")
    if nnsight.__version__ != "0.7.0":
        pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned 0.7.0")
    from nnsight import NNsight
    from transformers import LlamaConfig, LlamaForCausalLM

    from component_analysis import hooks
    from tests.helpers import TINY

    torch.manual_seed(0)
    config = LlamaConfig(hidden_size=TINY["hidden"], num_hidden_layers=TINY["layers"],
                         num_attention_heads=TINY["heads"],
                         num_key_value_heads=TINY["kv_heads"],
                         intermediate_size=TINY["intermediate"],
                         vocab_size=FAKE_VOCAB_SIZE,
                         max_position_embeddings=TINY["max_pos"],
                         attn_implementation="sdpa")
    model = NNsight(LlamaForCausalLM(config).eval())
    tokenizer = FakeWordTokenizer()
    monkeypatch.setattr(mod, "load_tokenizer", lambda name: tokenizer)
    monkeypatch.setattr(mod, "load_model", lambda name, device: model)
    out = str(world["tmp"] / "real")
    mod.run(world["plan_path"], out, argv=[], device="cpu")

    shape = hooks.geometry(model)
    rows = read_rows(out, "far_select_HI")
    resid = torch.load(os.path.join(out, "resid.far_select_HI.pt"))["resid"]
    assert resid.shape == (len(rows), shape["num_layers"] + 1, shape["hidden_size"])
    tokens = torch.load(os.path.join(out, "tokens.far_select_HI.pt"))
    assert len(tokens["keys"]) == 1 + shape["num_layers"] * (shape["num_heads"] + 1)
    # Every head, every MLP and the embedding add up to the centred logit of each token.
    assert torch.allclose(tokens["dla"].sum(1), tokens["logits_centred"], atol=1e-4)
    for i, row in enumerate(rows):
        honest, deceptive = tokens["logits_raw"][i].tolist()
        assert row["model_honest_margin"] == pytest.approx(honest - deceptive, abs=1e-5)
        assert row["model_margin"] == pytest.approx(honest - deceptive, abs=1e-5)   # HI target is honest
    # The HI residual's last row is what the real model's final norm reads at the Readout.
    record = records_by_id(world, "far_v2", "validation")[rows[0]["instance_id"]]
    ids = torch.tensor([tokenizer.encode(record["honest_instruction_clean_prompt"])])
    with torch.no_grad():
        hidden = model._model(ids, output_hidden_states=True).hidden_states
    assert torch.allclose(resid[0, 0].float(), hidden[0][0, -1].half().float(), atol=1e-2)


# ==============================================================================
# THE COMMITTED PLANS
# ==============================================================================

def test_the_committed_plans_are_what_the_generator_writes(mod):
    for smoke, name in ((False, "B2-p1-plan.json"), (True, "B2-p1-smoke.json")):
        path = os.path.join(JOBS, name)
        with open(path) as handle:
            assert handle.read() == mod.render_plan(mod.build_p1_plan(smoke=smoke)), name


def test_the_p1_plan_follows_the_split_table(mod):
    plan = mod.build_p1_plan()
    cells = {cell["name"]: cell for cell in plan["cells"]}
    by_role = {}
    for cell in plan["cells"]:
        by_role.setdefault(cell["role"], []).append(cell)
    assert sorted((c["task"], c["condition"]) for c in by_role["fit"]) == \
        [("far_v2", "D"), ("far_v2", "H")]
    assert sorted(c["condition"] for c in by_role["select"]) == ["D", "H", "HI"]
    assert sorted(c["condition"] for c in by_role["far_gate"]) == ["D", "F", "H", "HI", "I"]
    assert sorted(c["condition"] for c in by_role["ser_test"]) == ["D", "F", "H", "HI", "I"]
    assert sorted(c["condition"] for c in by_role["sdr"]) == ["D", "H", "I_reported"]
    # Fitting and selection never read a SER, SDR or FAR-test row.
    for cell in by_role["fit"] + by_role["select"]:
        assert cell["task"] == "far_v2" and os.path.basename(cell["dataset"]).startswith("far_v2")
        assert cell["split"] == ("train" if cell["role"] == "fit" else "validation")
        assert not cell.get("exclude_id_files") and not cell.get("id_file")
    for role, task in (("far_gate", "far"), ("ser_test", "ser"), ("sdr", "sdr")):
        for cell in by_role[role]:
            assert cell["split"] == "test"
            if cell["condition"] == "I_reported":
                assert cell["id_file"].endswith("sdr_wish_ids.txt")
                continue
            assert [os.path.basename(p) for p in cell["exclude_id_files"]] == \
                [f"{task}_seed0_ids.txt", f"{task}_seed1_ids.txt"]
    for cell in plan["cells"]:
        if cell["condition"] == "HI":
            assert cell["keep_if"] == {"field": "h_honest_instruction_clean", "min": 0.3}
            assert cell["prompt_field"] == "honest_instruction_clean_prompt"
        else:
            assert "keep_if" not in cell and cell["prompt_field"] == "clean_prompt"
        assert not os.path.isabs(cell["dataset"])
    assert cells["sdr_test_I_reported"]["dataset"].endswith("sdr_v2_inversion_reported")
    assert mod.build_p1_plan(smoke=True) == dict(plan, max_rows=64)


#: The counts of the real plan, from the datasets and id files on 2026-11-01.
REAL_COUNTS = {
    "far_fit_D": 200, "far_fit_H": 200,
    "far_select_D": 200, "far_select_H": 200, "far_select_HI": 200,
    "far_gate_D": 800, "far_gate_H": 800, "far_gate_HI": 800, "far_gate_F": 800, "far_gate_I": 177,
    "ser_test_D": 800, "ser_test_H": 800, "ser_test_HI": 783, "ser_test_F": 800, "ser_test_I": 194,
    "sdr_test_D": 800, "sdr_test_H": 800, "sdr_test_I_reported": 618,
}


def test_the_real_plan_dry_run_reports_the_planned_counts(mod, tmp_path):
    path = os.path.join(JOBS, "B2-p1-plan.json")
    if not os.path.isdir(os.path.join(ROOT, "data", "datasets", "far_v2")):
        pytest.skip("the v2 datasets are not in this checkout")
    summary = mod.run(path, str(tmp_path / "dry"), dry_run=True, argv=[],
                      load_model_fn=no_model, load_tokenizer_fn=no_tokenizer)
    assert {name: len(cell["ids"]) for name, cell in summary["cells"].items()} == REAL_COUNTS
    assert summary["total_rows"] == sum(REAL_COUNTS.values())
