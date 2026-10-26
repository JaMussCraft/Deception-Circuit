"""
v1 byte-identity snapshot for ticket 02b (mechanism-analysis spec, R16).

02b adds the Neutral-Clause Twin to attention patterns and path patching. The
twin exists only on the v2 tasks, so a v1 cell — attention patterns under the
three v1 conditions, path patching under both v1 counterfactuals, then the
roles pass — must write exactly the files, columns and numbers it wrote before
the ticket. The snapshot under `tests/fixtures/v1_snapshot_02b/` was taken at
ddd1da4, before any 02b edit, on the tiny model through the real CLI; every
text output of the cell is compared byte for byte after two normalizations
that are not measurements: the pytest tmp directory in recorded paths (and
the instance-set digests that hash it), and the wall-clock fields (`created`,
`wall_seconds`, `seconds_per_forward`).

Regenerate only when a change to v1 output is intended and recorded:

    V1_SNAPSHOT_WRITE=1 python -m pytest tests/test_v1_snapshot_02b.py

nnsight 0.7.0 only (the attention weights and the patched forwards are a 0.7.0
behaviour), so the base login env skips this module.
"""

from __future__ import annotations

import json
import os
import re
import shutil

import pytest

nnsight = pytest.importorskip("nnsight")
if nnsight.__version__ != "0.7.0":
    pytest.skip("the snapshot is a nnsight 0.7.0 behaviour", allow_module_level=True)

import torch                                                       # noqa: E402

import analyze_components                                          # noqa: E402
from component_analysis import attention_patterns as ap            # noqa: E402
from component_analysis import instances as ca_instances           # noqa: E402
from component_analysis import path_patching as pp                 # noqa: E402
from component_analysis import registry                            # noqa: E402
from tests.fakes import FAKE_VOCAB_SIZE                            # noqa: E402
from tests.helpers import tiny_config                              # noqa: E402
from tests.test_analyze_components_end_to_end import written_files  # noqa: E402
from tests.test_analyze_components_segmentation import (           # noqa: E402, F401
    CELL, build_sdr_split, run_cli, sdr_run)

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures",
                       "v1_snapshot_02b")
FILES_LIST = "_files.txt"
WRITE = os.environ.get("V1_SNAPSHOT_WRITE") == "1"
#: Text outputs are compared; PNGs are only listed (matplotlib's bytes are not
#: a promise across library versions).
TEXT = (".json", ".csv", ".md", ".txt")
VOLATILE = re.compile(
    r'"(created|wall_seconds|seconds_per_forward)": ("[^"]*"|[-+0-9.eE]+|null)')
#: An instance-set id digests the dataset *path* with the ids
#: (`head_table.instance_set_id`), so the honest twin's carries the tmp dir.
SET_ID = re.compile(r'"([a-z_]+):[0-9a-f]{10}"')


def tiny_model():
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    config = tiny_config(attn_implementation="sdpa")
    config.vocab_size = FAKE_VOCAB_SIZE
    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(config).eval())


@pytest.fixture
def v1_cell(sdr_run, monkeypatch):
    """(output dir, the tmp root to scrub) after the v1 cell has been run."""
    run_dir, out, _records = sdr_run
    data_dir = json.loads((run_dir / "config.json").read_text())["data_dir"]
    tokenizer = ca_instances.load_analysis_tokenizer("llama-tiny")
    build_sdr_split(os.path.join(data_dir, "sdr_honest"), tokenizer)
    monkeypatch.setattr(registry, "ANALYSES", [ap, pp])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: tiny_model())

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--n-causal", "16",
                   "--device", "cpu", "--path-counterfactual", "both",
                   "--output-dir", str(out)) == 0
    assert analyze_components.main(["roles", os.path.join(str(out), *CELL),
                                    "--roles-allow-missing-views"]) == 0
    return str(out), str(run_dir.parent)


def normalize(text: str, tmp: str) -> str:
    for root in {tmp, os.path.realpath(tmp)}:
        text = text.replace(root, "<TMP>")
    text = VOLATILE.sub(r'"\1": "<volatile>"', text)
    return SET_ID.sub(r'"\1:<digest>"', text)


def snapshot(out: str, tmp: str) -> dict:
    files = written_files(out)
    texts = {}
    for name in files:
        if name.endswith(TEXT):
            with open(os.path.join(out, name)) as handle:
                texts[name] = normalize(handle.read(), tmp)
    texts[FILES_LIST] = "\n".join(files) + "\n"
    return texts


def write_fixture(texts: dict) -> None:
    shutil.rmtree(FIXTURE, ignore_errors=True)
    for name, text in texts.items():
        path = os.path.join(FIXTURE, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as handle:
            handle.write(text)


def read_fixture() -> dict:
    texts = {}
    for name in written_files(FIXTURE):
        with open(os.path.join(FIXTURE, name)) as handle:
            texts[name] = handle.read()
    return texts


def test_a_v1_attention_and_path_patching_cell_is_byte_identical_to_the_snapshot(
        v1_cell):
    out, tmp = v1_cell
    actual = snapshot(out, tmp)
    if WRITE:
        write_fixture(actual)
        pytest.skip(f"snapshot written to {FIXTURE}")
    assert os.path.isdir(FIXTURE), f"no snapshot at {FIXTURE}; see the module docstring"
    expected = read_fixture()

    assert actual[FILES_LIST] == expected[FILES_LIST]
    assert sorted(actual) == sorted(expected)
    differing = [name for name in expected if actual[name] != expected[name]]
    assert differing == [], f"v1 output changed in {differing}"


def test_the_snapshot_holds_the_v1_columns_and_no_neutral_twin_column():
    """The guard guards the right thing: the v1 head table with its v1 column
    set, and nothing of the v2 twin in it."""
    if not os.path.isdir(FIXTURE):
        pytest.skip("no snapshot on disk")
    with open(os.path.join(FIXTURE, *CELL, "head_table.json")) as handle:
        table = json.load(handle)
    columns = table["columns"]
    for name in ("attention_patterns.pressure_top_segment",
                 "attention_patterns.honest_twin_descriptive_top_mass",
                 "path_patching.direct_support",
                 "path_patching.direct_support_honest_instruction_paired_se",
                 "roles.role_proposed"):
        assert name in columns
    assert not [one for one in columns if "neutral_twin" in one]
