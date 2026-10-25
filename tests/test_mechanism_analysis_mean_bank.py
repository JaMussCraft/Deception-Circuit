"""Ticket 01 of mechanism-analysis: the variant-matched mean bank (R13), CPU only.

Under `--ablation mean` the knockout evaluation reads its no_pressure variant rows with the task bank, which is
collected on the task's test split: under-pressure prompts for every deception task. Mean-ablating a head that
reads the pressure then writes its average under-pressure output into a prompt without pressure (review B4).
`--variant-mean-bank no_pressure` gives those rows a bank of their own, collected over the very rows they ablate
(the Pressure Clause removed from both streams). For the v2 tasks those rows are `<t>_v2_nopressure`'s test split,
row for row; the last test pins that identity on the real datasets.

Seams: the evaluator's argparse (the flag's absence leaves every existing invocation's recorded CLI unchanged),
`Session.mean_bank` (what a `variant:<name>` bank is collected over, and per which task), the knockout
evaluation's variant section (which bank each row group is ablated with, and what is recorded), and the real CLI
end to end on the tiny model.
"""

from __future__ import annotations

import json
import os
import re
import sys
from types import SimpleNamespace

import pytest
import torch
from torch.utils.data import DataLoader

import evaluate_circuit
from evaluation import ablation as abl
from evaluation import knockout as K
from evaluation.ablation import VARIANT_BANK_PREFIX
from evaluation.context import Session
from tests.helpers import build_tiny_pair
from tests.test_end_to_end import TINY, TinyDataset, TinyTask, run_cli, tiny_run  # noqa: F401
from tests.test_evaluation import VariantContext, _Recorder

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NP_BANK = abl.variant_bank_name("no_pressure")


# ---------------------------------------------------------------- the flag

def test_without_the_flag_the_cli_namespace_has_no_new_entry():
    """suite.json and summary.json record vars(cli); an absent flag must leave that record as it was."""
    cli = evaluate_circuit.build_parser().parse_args(["outputs/run_a", "--ablation", "mean"])
    assert not hasattr(cli, "variant_mean_bank")
    cli = evaluate_circuit.build_parser().parse_args(
        ["outputs/run_a", "--ablation", "mean", "--variant-mean-bank", "no_pressure"])
    assert cli.variant_mean_bank == ["no_pressure"]


def test_the_flag_names_only_the_no_pressure_variant():
    with pytest.raises(SystemExit):
        evaluate_circuit.build_parser().parse_args(["x", "--variant-mean-bank", "honest_instruction"])


def test_one_helper_reads_the_flag_and_names_the_bank():
    assert abl.matched_variants(SimpleNamespace()) == ()
    assert abl.matched_variants(SimpleNamespace(variant_mean_bank=["no_pressure"])) == ("no_pressure",)
    assert NP_BANK == VARIANT_BANK_PREFIX + "no_pressure"
    assert abl.is_variant_bank(NP_BANK) and not abl.is_variant_bank("task")


# ---------------------------------------------------------------- Session.mean_bank

class _Task:
    def model_inputs(self, b):
        return {"input_ids": b["input_ids"], "corrupted_input_ids": b["corrupted_input_ids"],
                "attention_mask": b["attention_mask"]}


def _loader(seed, n=6, seq=10, bs=2):
    return DataLoader(TinyDataset(n, seq, TINY["vocab"], seed), batch_size=bs, shuffle=False)


def _session(model, source="corrupt"):
    cli = SimpleNamespace(device="cpu", mean_source=source)
    session = Session(cli, None, {}, None, None, {}, [], [])
    session.node_model = model
    return session


def _ctx(label, test_seed, variant_seed):
    loaders = {"no_pressure": _loader(variant_seed)}
    return SimpleNamespace(task_spec=SimpleNamespace(label=label), task=_Task(), test_loader=_loader(test_seed),
                           variant_loader=lambda v: (loaders.get(v), "" if v in loaders else "no such variant"))


def _hand_mean(model, loader):
    """Masked mean of every site's corrupted-stream reference over the loader's rows, by hand."""
    rec, masks = _Recorder(), []
    with torch.no_grad(), abl.ablation_hook(model, rec):
        for b in loader:
            masks.append(b["attention_mask"])
            model(input_ids=b["input_ids"], corrupted_input_ids=b["corrupted_input_ids"],
                  attention_mask=b["attention_mask"], use_cache=False)
    total = float(sum(m.sum() for m in masks))
    out = {}
    for site, layers in rec.seen.items():
        for layer, tensors in layers.items():
            acc = sum((t.float() * m.reshape(*m.shape, *([1] * (t.dim() - 2))).float()).sum(dim=(0, 1))
                      for t, m in zip(tensors, masks))
            out.setdefault(site, {})[layer] = acc / total
    return out


def test_a_variant_bank_is_the_mean_over_that_variants_rows():
    _, model = build_tiny_pair()
    session = _session(model)
    ctx = _ctx("far_v2", test_seed=3, variant_seed=11)
    bank = session.mean_bank(ctx, NP_BANK)
    expected = _hand_mean(model, ctx.variant_loader("no_pressure")[0])
    task_bank = session.mean_bank(ctx, "task")
    assert set(bank) == set(expected)
    for site in expected:
        for layer in expected[site]:
            assert torch.allclose(bank[site][layer], expected[site][layer], atol=1e-6), (site, layer)
    # ... and not the task bank, which comes from the with-pressure test rows
    assert any(not torch.allclose(bank[s][l], task_bank[s][l]) for s in bank for l in bank[s])


def test_a_variant_bank_is_kept_per_task_and_records_what_it_was_collected_on():
    _, model = build_tiny_pair()
    session = _session(model)
    far, sdr = _ctx("far_v2", 3, 11), _ctx("sdr_v2", 4, 12)
    a = session.mean_bank(far, NP_BANK)
    b = session.mean_bank(sdr, NP_BANK)
    assert session.mean_bank(far, NP_BANK) is a          # collected once per task
    assert any(not torch.allclose(a[s][l], b[s][l]) for s in a for l in a[s])
    meta = session.mean_bank_meta(far, NP_BANK)
    assert meta == {"bank": NP_BANK, "task": "far_v2", "rows": "no_pressure", "n_rows": 6,
                    "source": "corrupt", "n_tokens": meta["n_tokens"]}
    assert meta["n_tokens"] == float(sum(int(x["attention_mask"].sum()) for x in far.variant_loader(
        "no_pressure")[0]))


def test_a_variant_bank_without_the_variant_rows_is_an_error():
    _, model = build_tiny_pair()
    with pytest.raises(ValueError, match="honest_instruction"):
        _session(model).mean_bank(_ctx("far_v2", 3, 11), abl.variant_bank_name("honest_instruction"))


# ---------------------------------------------------------------- the knockout variant section

class _SpyContext(VariantContext):
    """VariantContext recording which bank each hook was asked for."""

    def __init__(self, model, flag, variants_available=K.VARIANTS):
        super().__init__(model, variants_available)
        self.asked = []
        self.cli.ablation = "mean"
        if flag is not None:
            self.cli.variant_mean_bank = flag

    def hook_for(self, bank_name="task"):
        self.asked.append(bank_name)
        return None

    def mean_bank_meta(self, name):
        return {"bank": name, "rows": name[len(VARIANT_BANK_PREFIX):]}


SECTION_KEYS = {"variant", "description", "label_convention", "rows", "per_example", "flip_summary",
                "flip_audit_reason", "headline"}


def test_without_the_flag_every_variant_row_group_uses_the_task_bank_and_nothing_new_is_recorded():
    _, pruned = build_tiny_pair()
    ctx = _SpyContext(pruned, None)
    sections = K.KnockoutEvaluation()._variant_sections(ctx)
    assert ctx.asked == ["task", "task"]
    assert set(sections) == {"variants"}
    for section in sections["variants"].values():
        assert set(section) == SECTION_KEYS


def test_with_the_flag_the_no_pressure_rows_run_under_both_banks_and_say_so():
    """R19(2)/R21: the task-bank result stays where it always was; the variant-matched result is added."""
    _, pruned = build_tiny_pair()
    ctx = _SpyContext(pruned, ["no_pressure"])
    sections = K.KnockoutEvaluation()._variant_sections(ctx)
    assert ctx.asked == ["task", "task", VARIANT_BANK_PREFIX + "no_pressure"]
    honest = sections["variants"]["honest_instruction"]
    task_np = sections["variants"]["no_pressure"]
    (matched_np,) = sections["variants_matched_bank"].values()
    assert honest["mean_bank"] == {"bank": "task"} and task_np["mean_bank"] == {"bank": "task"}
    assert matched_np["mean_bank"] == {"bank": VARIANT_BANK_PREFIX + "no_pressure", "rows": "no_pressure"}
    assert set(matched_np) == SECTION_KEYS | {"mean_bank"}
    # nothing varies but the bank, and the spy installs no hook, so the two no_pressure runs agree
    assert matched_np["rows"] == task_np["rows"]


def test_with_the_flag_a_skipped_variant_gets_no_second_run_and_names_no_bank():
    _, pruned = build_tiny_pair()
    ctx = _SpyContext(pruned, ["no_pressure"], variants_available=("honest_instruction",))
    sections = K.KnockoutEvaluation()._variant_sections(ctx)
    assert ctx.asked == ["task"]                      # no bank is collected for rows that do not exist
    assert "skipped" in sections["variants"]["no_pressure"]
    assert sections["variants_matched_bank"] == {}
    assert K.section_banks({"variants": sections["variants"], "wikitext": None,
                                 "variants_matched_bank": {}}) == {
        "task": "task", "variants": {"honest_instruction": "task"}, "variants_matched_bank": {}}


# ---------------------------------------------------------------- the real CLI on the tiny model

class VariantTinyTask(TinyTask):
    """TinyTask whose two prompt variants exist (distinct rows), so the variant sections run."""

    def build_variant_dataloader(self, variant, tokenizer, args, state):
        seed = {"no_pressure": 11, "honest_instruction": 12}[variant]
        return DataLoader(TinyDataset(args.test_samples, args.max_seq_length, TINY["vocab"], seed),
                          batch_size=args.batch_size, shuffle=False)


ARGS = ("--evals", "knockout", "--n-random", "2", "--wikitext-blocks", "2", "--wikitext-block-size", "16",
        "--wikitext-batch-size", "2", "--gen-examples", "0")


def _knockout(run_dir, scheme):
    with open(os.path.join(str(run_dir), "evaluations", scheme, "knockout.json")) as f:
        return json.load(f)


@pytest.fixture
def variant_run(tiny_run, monkeypatch):
    import tasks
    monkeypatch.setitem(tasks._TASKS, "tinystd", VariantTinyTask)
    return tiny_run


def test_cli_mean_with_the_flag_adds_the_matched_no_pressure_run_and_keeps_the_task_bank_run(variant_run,
                                                                                              monkeypatch):
    assert run_cli(monkeypatch, variant_run, "--ablation", "mean", *ARGS) == 0
    plain = _knockout(variant_run, "mean")
    assert "mean_banks" not in plain and "variants_matched_bank" not in plain
    assert all("mean_bank" not in s for s in plain["variants"].values())
    assert run_cli(monkeypatch, variant_run, "--ablation", "mean", "--variant-mean-bank", "no_pressure",
                   *ARGS) == 0
    matched = _knockout(variant_run, "mean")
    assert matched["task"] == plain["task"]
    assert matched["wikitext"] == plain["wikitext"]
    # both variants under the task bank: exactly the run without the flag, plus the bank it names
    for variant in K.VARIANTS:
        section = dict(matched["variants"][variant])
        assert section.pop("mean_bank") == {"bank": "task"}
        assert section == plain["variants"][variant]
    # the no_pressure rows again, under their own bank
    (only,) = matched["variants_matched_bank"]
    np_task, np_own = plain["variants"]["no_pressure"], matched["variants_matched_bank"]["no_pressure"]
    assert only == "no_pressure"
    assert np_own["rows"]["full"] == np_task["rows"]["full"]      # all gates open: no bank is read
    assert np_own["rows"]["knockout"] != np_task["rows"]["knockout"]
    bank = np_own["mean_bank"]
    assert (bank["bank"], bank["rows"], bank["task"], bank["n_rows"]) == (
        VARIANT_BANK_PREFIX + "no_pressure", "no_pressure", "tinystd", 24)
    assert matched["mean_banks"] == {
        "task": "task", "wikitext": "wikitext",
        "variants": {"honest_instruction": "task", "no_pressure": "task"},
        "variants_matched_bank": {"no_pressure": VARIANT_BANK_PREFIX + "no_pressure"}}


def test_cli_mean_with_the_flag_and_no_wikitext_names_no_wikitext_bank(variant_run, monkeypatch):
    assert run_cli(monkeypatch, variant_run, "--ablation", "mean", "--variant-mean-bank", "no_pressure",
                   "--skip-wikitext", *ARGS) == 0
    assert "wikitext" not in _knockout(variant_run, "mean")["mean_banks"]


# ---------------------------------------------------------------- without the flag: byte-identical to the base

#: knockout.json of real evaluate_circuit.py cells on the tiny model, written by the branch base (c24b5d9, before
#: ticket 01) per environment, with the run-time `seconds` field masked. A run without --variant-mean-bank must
#: reproduce them byte for byte. CPU float math differs by about one ulp across the two envs, hence one set each,
#: and in the job env also across hosts: the snapshots hold on the CPU model in cpu.txt and the test skips on
#: another one.
V1_SNAPSHOTS = os.path.join(REPO, "tests", "fixtures", "mechanism_analysis_v1_knockout")
SECONDS = re.compile(rb'"seconds": [-+0-9.eE]+')
SNAP_ARGS = ("--evals", "knockout", "--n-random", "3", "--wikitext-blocks", "4", "--wikitext-block-size", "16",
             "--wikitext-batch-size", "2", "--gen-examples", "0")


def _env_key():
    return "py%d%d-torch%s" % (sys.version_info[0], sys.version_info[1], torch.__version__.split("+")[0])


def mask_seconds(raw: bytes) -> bytes:
    return SECONDS.sub(b'"seconds": 0', raw)


def _cpu_model() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return "unknown"


@pytest.mark.parametrize("scheme", ["interchange", "zero", "mean"])
def test_without_the_flag_knockout_json_is_byte_identical_to_the_branch_base(variant_run, monkeypatch, scheme):
    fixture = os.path.join(V1_SNAPSHOTS, _env_key(), f"{scheme}.json")
    if not os.path.isfile(fixture):
        pytest.skip(f"no branch-base snapshot for {_env_key()}")
    with open(os.path.join(V1_SNAPSHOTS, "cpu.txt")) as f:
        recorded = f.read().strip()
    if _cpu_model() != recorded:
        pytest.skip(f"branch-base snapshots were taken on {recorded}, this host is {_cpu_model()}")
    torch.manual_seed(0)
    assert run_cli(monkeypatch, variant_run, "--ablation", scheme, *SNAP_ARGS) == 0
    with open(os.path.join(str(variant_run), "evaluations", scheme, "knockout.json"), "rb") as f:
        got = mask_seconds(f.read())
    with open(fixture, "rb") as f:
        want = f.read()
    assert got == want


@pytest.mark.parametrize("scheme", ["zero", "interchange"])
def test_cli_refuses_the_flag_without_mean_ablation(variant_run, monkeypatch, scheme):
    with pytest.raises(ValueError, match="--variant-mean-bank"):
        run_cli(monkeypatch, variant_run, "--ablation", scheme, "--variant-mean-bank", "no_pressure", *ARGS)


# ---------------------------------------------------------------- the premise on the real v2 datasets

DATA = os.path.join(REPO, "data", "datasets")


@pytest.mark.parametrize("task", ["far", "sdr", "ser"])
def test_no_pressure_rows_of_d_are_the_nopressure_test_split(task):
    """R13 asks for a bank on `<t>_v2_nopressure`'s test split. The variant bank is collected over the
    no_pressure rows of D's test split instead; this holds them equal, both streams, row for row."""
    d_dir, np_dir = os.path.join(DATA, f"{task}_v2"), os.path.join(DATA, f"{task}_v2_nopressure")
    if not (os.path.isdir(d_dir) and os.path.isdir(np_dir)):
        pytest.skip(f"{task}_v2 datasets not present")
    from datasets import load_from_disk

    from dataset.clause_surgery import remove_clause
    d, n = load_from_disk(d_dir)["test"], load_from_disk(np_dir)["test"]
    assert d["instance_id"] == n["instance_id"]
    for stream in ("clean_prompt", "corrupt_prompt"):
        assert [remove_clause(p, c) for p, c in zip(d[stream], d["pressure"])] == n[stream], stream
