"""
scripts/falsity_probe_capture.py: the B2 P1 capture (instructed-route ticket T6).

For every cell of a capture plan this runs one forward per row and writes the Readout residual at every layer
boundary, the two items' final logits, and each Component's direct attribution to each item's logit. Ticket T7
(`scripts/falsity_probe.py`, CPU only) fits and scores the falsity probe from these files.

    python scripts/falsity_probe_capture.py --plan PLAN.json --output-dir DIR [--dry-run] [--max-rows N]
        [--check-encoding] [--batch-size N] [--device cuda]
    python scripts/falsity_probe_capture.py --write-plans docs/research/instructed-route/jobs

`--dry-run` loads no model and no tokenizer. It resolves every cell's ids, applies the exclusions and the HI filter,
prints the per-cell row counts, and writes `capture_plan.json` and `run_manifest.json`. A missing id fails it.
`--check-encoding` (dry run only) also loads the tokenizer and encodes every row, so a multi-token answer or a
Readout that is not `prefix_length - 1` fails on the login node. `--write-plans DIR` writes the real plan
`B2-p1-plan.json` and the smoke plan `B2-p1-smoke.json` (`build_p1_plan`); a test asserts the committed files equal
the generator's output byte for byte.

PLAN (JSON)
-----------
Top level: `schema` ("falsity-probe-capture-plan/1"), `model` (a `models.MODEL_REGISTRY` alias or a HuggingFace id),
`seed` (recorded in the manifest; the capture has no randomness), `batch_size`, optional `max_rows` (the CLI flag
overrides it) and `cells`, a list of objects with:

- `name`: the cell name, used in every file name. Unique.
- `role`: what T7 may use the rows for: `fit`, `select`, `far_gate`, `ser_test` or `sdr`.
- `task`: the v2 task, `far_v2`, `ser_v2` or `sdr_v2`.
- `condition`: `D`, `H`, `HI`, `F`, `I` or `I_reported` (table below). Checked against the dataset's
  `dataset_config.json` and against every record's `condition` field, so a cell cannot read the wrong split.
- `dataset`: the dataset directory. A relative path is resolved against the repository root (this file's parent's
  parent), so a plan works from any checkout.
- `split`: `train`, `validation` or `test`.
- `prompt_field`: `clean_prompt`, or `honest_instruction_clean_prompt` for HI (enforced).
- `id_file` (optional): one id per line. Only these ids, in this order; an id missing from the split fails the run.
- `exclude_id_files` (optional): ids removed from the cell. Every listed id must be in the task's D test split
  (`<dirname(dataset)>/<task>`, `test`), which is where the seed-0 and seed-1 samples were drawn, so a mispointed
  file fails instead of subtracting nothing. An I cell may exclude ids it does not hold.
- `keep_if` (optional): `{"field": F, "min": m}` keeps a row when `record[F] >= m` (HI: `h_honest_instruction_clean`
  at 0.3, the twin's bar). The kept share is reported in `capture_plan.json`.
- `flag_id_files` (optional): `{flag name: id file}`. Each row gets a boolean `flag name` field (the real plan sets
  `in_seed0_sample` and `in_seed1_sample` from the task's seed files).

The order of a cell's rows is the id file's order, or else the split's order; `--max-rows N` keeps the first N after
exclusion and filtering.

CONDITIONS AND ORIENTATION
--------------------------
| condition | dataset (v2)            | record condition     | prompt                           | honest item | cell target  |
| D         | `<task>`                | deceptive            | clean_prompt                     | distractor  | record's     |
| H         | `<task>_honest`         | honest               | clean_prompt                     | target      | record's     |
| HI        | `<task>` (D's records)  | deceptive            | honest_instruction_clean_prompt  | distractor  | honest item  |
| F         | `<task>_nopressure`     | nopressure           | clean_prompt                     | target      | record's     |
| I         | `<task>_inversion`      | inversion            | clean_prompt                     | distractor  | record's     |
| I_reported| `<task>_inversion_reported` | inversion_reported | clean_prompt                   | distractor  | record's     |

Every row's honest item is checked against the record: it is the clean stream's designated item (`clean_item_d`)
when `designation_polarity` is "inversion" and the other item when it is "identity". The HI cell's target is the
honest item, because the honest instruction asks for it; its distractor is D's target.

OUTPUT FILES (in `--output-dir`)
--------------------------------
Line i of `rows.<cell>.jsonl` describes row i of every tensor in `resid.<cell>.pt` and `tokens.<cell>.pt`, and
both `.pt` files carry the same `ids` list so the join can be checked.

`rows.<cell>.jsonl`, one JSON object per row:
    row (int, 0-based), cell, role, task, condition, split, prompt_field, instance_id,
    pressure_id, pressure (the clause text; "" for F), framing_id, instructed_inversion_id (I rows, else null),
    items ([item_1, item_2]), item_token_ids ([id of " "+item_1, id of " "+item_2]), honest_item_index (0 or 1),
    honest_item, deceptive_item, honest_token, deceptive_token,
    target_item, distractor_item, target_token, distractor_token (the cell's target, see the table),
    prefix_length, readout (= prefix_length - 1, the Readout position),
    model_margin: fp32 logit(target) - logit(distractor) at the Readout, through the fp32 final norm;
    model_honest_margin: fp32 logit(honest) - logit(deceptive), the same convention on every cell;
    dataset_margin: the dataset's margin in the cell's target convention, `clean_margin` for every condition but HI
      and `h_honest_instruction_clean` for HI (both are target minus distractor of their own prompt);
    dataset_margin_field: which field that was;
    clean_margin: the record's `clean_margin` as stored (for HI rows, D's margin on the D prompt), or null;
    keep_if_value: the `keep_if` field's value, or null;
    one boolean per `flag_id_files` entry (in_seed0_sample, in_seed1_sample in the real plan).

`resid.<cell>.pt`, a dict:
    ids: list of instance ids; readout: LongTensor [n];
    resid: float16 [n, num_layers + 1, hidden] ([n, 33, 4096] on Llama-3.1-8B), `hooks.Capture.residual` at the
      Readout: row 0 is the embedding output and row l + 1 the residual after decoder layer l.

`tokens.<cell>.pt`, a dict:
    ids, token_order (["honest", "deceptive"]), token_ids: LongTensor [n, 2] (column 0 the honest item's token,
      column 1 the deceptive item's);
    logits_raw: float32 [n, 2], the fp32 Readout logits at those ids (`hooks.readout_logits` of the last residual);
    logits_logsoftmax: float32 [n, 2], log-softmax over the whole vocabulary, gathered;
    logits_centred: float32 [n, 2], raw minus the mean logit over the vocabulary;
    keys: [[kind, layer, index], ...], every sender in `hooks.all_component_keys` order (the embedding, then per
      layer each head and the MLP block; 1 + 32 * 33 = 1057 on the 8B model);
    dla: float32 [n, len(keys), 2], `dla.component_token_logits(..., centre=True)`: each key's direct contribution to
      each token's logit at the fixed final-norm scale, centred on the mean unembedding row. Summed over keys it
      equals logits_centred (the check is recorded as dla_sum_max_abs_error);
    dla_centre: True.

`done.<cell>.json`: written last for a cell, with its ids and checks. A rerun into the same directory skips a cell
whose marker names the same ids and fails if they differ.

`capture_plan.json`: the resolved plan: per cell the spec, the ids, the row count and the resolution report
(n_split, n_excluded, n_before_filter, n_kept_by_filter, kept_share, and with encoding max_length and
max_prefix_length). Written by dry and real runs.

`capture_summary.json` (real runs): per cell n_rows, margin_mean_abs_diff (mean |model_margin - dataset_margin|;
the plan's execution evidence asks for at most 0.05 on the D cells), dla_sum_max_abs_error, resid_nonfinite (the
number of residual elements that are inf or nan after the float16 cast; a bfloat16 value past 65504 overflows, and
the cell is kept so T7 decides), and total_rows.

`run_manifest.json`: `run_manifest.write_run_manifest` with the argv, the plan's seed and model, and the sha256 of
the plan, every id file and every data file of every dataset directory read. It is written before any model load.

Encoding: each prompt goes through `component_analysis.dataloaders._encode`, the function the clean prompt goes
through in every analysis, with `add_special_tokens=False` and right padding to the cell's length,
`max(dataset max_seq_length, longest prefix in the cell)`, so the longer HI prompt is never truncated. The Readout
is `prefix_length - 1` and is asserted to be the last unpadded position. Answer tokens are
`deception_common.encode_answer_token` (leading space) and must be single tokens.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Sequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PLAN_SCHEMA = "falsity-probe-capture-plan/1"
OUTPUT_SCHEMA = "falsity-probe-capture/1"
TOKEN_ORDER = ["honest", "deceptive"]
ROLES = ("fit", "select", "far_gate", "ser_test", "sdr")
CODE_FILES = ("component_analysis/hooks.py", "component_analysis/dla.py",
              "component_analysis/dataloaders.py", "dataset/deception_common.py")

HI_PROMPT = "honest_instruction_clean_prompt"
HI_MARGIN = "h_honest_instruction_clean"
HI_BAR = 0.3

#: condition -> (record condition, the record answer that is the honest item, prompt field, dataset margin field,
#: whether the cell's target is the honest item rather than the record's target).
CONDITIONS = {
    "D": ("deceptive", "distractor", "clean_prompt", "clean_margin", False),
    "H": ("honest", "target", "clean_prompt", "clean_margin", False),
    "HI": ("deceptive", "distractor", HI_PROMPT, HI_MARGIN, True),
    "F": ("nopressure", "target", "clean_prompt", "clean_margin", False),
    "I": ("inversion", "distractor", "clean_prompt", "clean_margin", False),
    "I_reported": ("inversion_reported", "distractor", "clean_prompt", "clean_margin", False),
}


#: Whether the clean stream's designated item (`clean_item_d`) is the honest answer, by `designation_polarity`.
#: Checked on every v2 split on 2026-11-01 (D, H, F, I and I-reported of all three tasks): under "inversion" the
#: designated item is the honest one, under "identity" it is the other item.
POLARITY_HONEST_IS_DESIGNATED = {"inversion": True, "identity": False}


def fail(message: str):
    raise SystemExit(f"falsity_probe_capture: {message}")


def resolve_path(path: Optional[str]) -> Optional[str]:
    if path is None:
        return None
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def read_ids(path: str) -> List[str]:
    if not os.path.isfile(path):
        fail(f"id file {path} does not exist")
    with open(path) as handle:
        ids = [line.strip() for line in handle if line.strip()]
    if len(set(ids)) != len(ids):
        fail(f"id file {path} lists an id more than once")
    return ids


# ==============================================================================
# LOADERS (module-level so tests can replace them)
# ==============================================================================

def load_model(name: str, device: str):
    from component_analysis import hooks

    return hooks.load_analysis_model(name, device=device,
                                     hf_token=os.environ.get("HF_TOKEN") or None)


def load_tokenizer(name: str):
    from component_analysis import instances

    return instances.load_analysis_tokenizer(name)


class ModelCapturer:
    """One traced forward per batch through `hooks.capture_forward`, read three ways.

    Returns `resid` ([b, L + 1, hidden], the model's dtype), `logits` (fp32 [b, vocab] through
    `hooks.readout_logits`) and `dla` (fp32 [b, len(keys), n_tokens] from `dla.component_token_logits`).
    """

    def __init__(self, model):
        from component_analysis import hooks

        self.model = model
        self.keys = [tuple(key) for key in hooks.all_component_keys(model)]

    def __call__(self, input_ids, attention_mask, readout, token_ids):
        from component_analysis import dla, hooks

        device, _dtype = hooks.device_and_dtype(self.model)
        capture = hooks.capture_forward(self.model, input_ids.to(device), attention_mask.to(device),
                                        components=self.keys, positions=readout.to(device))
        logits = hooks.readout_logits(self.model, capture.residual[:, -1, :])
        per_token = dla.component_token_logits(self.model, capture, self.keys, token_ids.to(device),
                                               centre=True)
        return {"resid": capture.residual, "logits": logits, "dla": per_token}


def make_capturer(model):
    return ModelCapturer(model)


# ==============================================================================
# THE PLAN
# ==============================================================================

def load_plan(path: str) -> dict:
    with open(path) as handle:
        plan = json.load(handle)
    if plan.get("schema") != PLAN_SCHEMA:
        fail(f"{path}: schema {plan.get('schema')!r} is not {PLAN_SCHEMA!r}")
    names = [cell.get("name") for cell in plan.get("cells", [])]
    if not names or len(set(names)) != len(names) or not all(names):
        fail(f"{path}: every cell needs a unique name")
    for cell in plan["cells"]:
        if cell.get("role") not in ROLES:
            fail(f"cell {cell['name']}: role {cell.get('role')!r} is not one of {ROLES}")
        condition = cell.get("condition")
        if condition not in CONDITIONS:
            fail(f"cell {cell['name']}: condition {condition!r} is not one of {sorted(CONDITIONS)}")
        expected_field = CONDITIONS[condition][2]
        if cell.get("prompt_field") != expected_field:
            fail(f"cell {cell['name']}: condition {condition} reads {expected_field}, "
                 f"not {cell.get('prompt_field')!r}")
    return plan


class Splits:
    """Each (dataset, split) loaded once."""

    def __init__(self):
        self._records: Dict[tuple, list] = {}
        self._configs: Dict[str, dict] = {}

    def config(self, directory: str) -> dict:
        from dataset import deception_common as dc

        if directory not in self._configs:
            self._configs[directory] = dc.load_dataset_config(directory)
        return self._configs[directory]

    def records(self, directory: str, split: str) -> list:
        from dataset import deception_common as dc

        key = (directory, split)
        if key not in self._records:
            if not os.path.isdir(directory):
                fail(f"dataset directory {directory} does not exist")
            self._records[key] = dc.load_or_generate_deception_data(directory, split=split)
        return self._records[key]


def resolve_cell(cell: dict, splits: Splits, *, max_rows: Optional[int]) -> dict:
    """-> {"name", "cell", "ids", "records", "flags", "report"} without a tokenizer."""
    from component_analysis import sampling

    name, condition = cell["name"], cell["condition"]
    record_condition, honest_answer, _field, _margin, _swap = CONDITIONS[condition]
    directory = resolve_path(cell["dataset"])
    config = splits.config(directory)
    if config.get("condition") != record_condition:
        fail(f"cell {name}: condition {condition} needs a {record_condition!r} dataset, but "
             f"{directory} says condition {config.get('condition')!r}")
    if cell.get("task") and config.get("task") != cell["task"]:
        fail(f"cell {name}: task {cell['task']!r} but {directory} is task {config.get('task')!r}")

    records = splits.records(directory, cell["split"])
    split_ids = sampling.record_ids(records)
    by_id = dict(zip(split_ids, records))
    report = {"dataset": directory, "split": cell["split"], "n_split": len(records)}

    if cell.get("id_file"):
        path = resolve_path(cell["id_file"])
        wanted = read_ids(path)
        missing = [one for one in wanted if one not in by_id]
        if missing:
            fail(f"cell {name}: {len(missing)} id(s) of {path} are not in {directory} "
                 f"{cell['split']}: {', '.join(missing[:10])}")
        report["id_file"] = path
    else:
        wanted = list(split_ids)

    excluded = set()
    if cell.get("exclude_id_files"):
        reference = os.path.join(os.path.dirname(directory), config["task"])
        reference_ids = set(sampling.record_ids(splits.records(reference, "test")))
        files = [resolve_path(path) for path in cell["exclude_id_files"]]
        for path in files:
            ids = read_ids(path)
            stray = [one for one in ids if one not in reference_ids]
            if stray:
                fail(f"cell {name}: {len(stray)} exclude id(s) of {path} are not in {reference} test: "
                     f"{', '.join(stray[:10])}")
            excluded.update(ids)
        report["exclude_id_files"] = files
    before = len(wanted)
    wanted = [one for one in wanted if one not in excluded]
    report["n_excluded"] = before - len(wanted)

    keep_if = cell.get("keep_if")
    report["n_before_filter"] = len(wanted)
    if keep_if:
        field, bar = keep_if["field"], float(keep_if["min"])
        wanted = [one for one in wanted
                  if by_id[one].get(field) is not None and float(by_id[one][field]) >= bar]
        report["keep_if"] = keep_if
    report["n_kept_by_filter"] = len(wanted)
    report["kept_share"] = (len(wanted) / report["n_before_filter"]
                            if report["n_before_filter"] else None)

    if max_rows is not None:
        wanted = wanted[:max_rows]
    report["n_rows"] = len(wanted)

    flags = {}
    for flag, path in sorted((cell.get("flag_id_files") or {}).items()):
        flags[flag] = set(read_ids(resolve_path(path)))

    chosen = [by_id[one] for one in wanted]
    for one, record in zip(wanted, chosen):
        if record.get("condition") != record_condition:
            fail(f"cell {name}: instance {one} has condition {record.get('condition')!r}, "
                 f"not {record_condition!r}")
        honest = record[honest_answer]
        designated = record.get("clean_item_d")
        polarity = record.get("designation_polarity")
        if designated is not None:
            if polarity not in POLARITY_HONEST_IS_DESIGNATED:
                fail(f"cell {name}: instance {one}: designation_polarity {polarity!r} is not one of "
                     f"{sorted(POLARITY_HONEST_IS_DESIGNATED)}, so the honest item cannot be checked")
            if (designated == honest) != POLARITY_HONEST_IS_DESIGNATED[polarity]:
                fail(f"cell {name}: instance {one}: the honest item by condition is {honest!r}, but under "
                     f"designation_polarity {polarity!r} the clean stream designates {designated!r}")
    return {"name": name, "cell": cell, "ids": wanted, "records": chosen, "flags": flags,
            "report": report, "max_seq_length": config.get("max_seq_length")}


def encode_cell(resolved: dict, tokenizer) -> List[dict]:
    """Per row: input ids, mask, Readout and every token id. Fails on a multi-token answer or a bad Readout."""
    from component_analysis.dataloaders import _encode
    from dataset import deception_common as dc

    cell = resolved["cell"]
    _rc, honest_answer, field, _margin, swap = CONDITIONS[cell["condition"]]
    name = resolved["name"]

    def one_token(word, one):
        ids = dc.encode_answer_token(tokenizer, word)
        if len(ids) != 1:
            fail(f"cell {name}: instance {one}: answer {word!r} is {len(ids)} tokens, not one")
        return ids[0]

    prefix = [len(tokenizer.encode(record[field], add_special_tokens=False))
              for record in resolved["records"]]
    floor = int(resolved.get("max_seq_length") or dc.MAX_SEQ_LENGTH)
    max_length = max([floor] + prefix)
    resolved["report"]["max_length"] = max_length
    resolved["report"]["max_prefix_length"] = max(prefix) if prefix else None

    out = []
    for one, record, length in zip(resolved["ids"], resolved["records"], prefix):
        input_ids, attention_mask = _encode(tokenizer, record[field], max_length)
        readout = length - 1
        if readout != int(attention_mask.sum()) - 1:
            fail(f"cell {name}: instance {one}: the Readout is prefix_length - 1 = {readout} but the last "
                 f"unpadded position is {int(attention_mask.sum()) - 1}; the tokenizer must pad on the right")
        honest = record[honest_answer]
        deceptive = record["target"] if honest_answer == "distractor" else record["distractor"]
        target, distractor = (honest, deceptive) if swap else (record["target"], record["distractor"])
        items = [record["item_1"], record["item_2"]]
        if honest not in items or deceptive not in items:
            fail(f"cell {name}: instance {one}: answers {honest!r}/{deceptive!r} are not its items {items}")
        out.append({
            "input_ids": input_ids, "attention_mask": attention_mask, "readout": readout,
            "prefix_length": length, "items": items,
            "item_token_ids": [one_token(item, one) for item in items],
            "honest_item": honest, "deceptive_item": deceptive,
            "honest_token": one_token(honest, one), "deceptive_token": one_token(deceptive, one),
            "target_item": target, "distractor_item": distractor,
            "target_token": one_token(target, one), "distractor_token": one_token(distractor, one),
        })
    return out


# ==============================================================================
# THE CAPTURE
# ==============================================================================

def _save(obj, path: str, torch_save: bool):
    import torch

    tmp = path + ".tmp"
    if torch_save:
        torch.save(obj, tmp)
    else:
        with open(tmp, "w") as handle:
            handle.write(obj)
    os.replace(tmp, path)


def row_metadata(resolved: dict, index: int, encoded: dict) -> dict:
    cell, record, one = resolved["cell"], resolved["records"][index], resolved["ids"][index]
    margin_field = CONDITIONS[cell["condition"]][3]
    keep_if = cell.get("keep_if")
    row = {
        "row": index, "cell": resolved["name"], "role": cell["role"], "task": cell.get("task"),
        "condition": cell["condition"], "split": cell["split"], "prompt_field": cell["prompt_field"],
        "instance_id": one, "pressure_id": record.get("pressure_id"),
        "pressure": record.get("pressure"), "framing_id": record.get("framing_id"),
        "instructed_inversion_id": record.get("instructed_inversion_id"),
        "items": encoded["items"], "item_token_ids": encoded["item_token_ids"],
        "honest_item_index": encoded["items"].index(encoded["honest_item"]),
    }
    for key in ("honest_item", "deceptive_item", "honest_token", "deceptive_token", "target_item",
                "distractor_item", "target_token", "distractor_token", "prefix_length", "readout"):
        row[key] = encoded[key]
    row["dataset_margin"] = record.get(margin_field)
    row["dataset_margin_field"] = margin_field
    row["clean_margin"] = record.get("clean_margin")
    row["keep_if_value"] = record.get(keep_if["field"]) if keep_if else None
    for flag, ids in resolved["flags"].items():
        row[flag] = one in ids
    return row


def capture_cell(resolved: dict, encoded: List[dict], capturer, out_dir: str, *, batch_size: int) -> dict:
    import torch

    name, n = resolved["name"], len(encoded)
    resid, raw, logsm, centred, per_token, margins, honest_margins = [], [], [], [], [], [], []
    with torch.no_grad():
        for start in range(0, n, batch_size):
            chunk = encoded[start:start + batch_size]
            input_ids = torch.stack([item["input_ids"] for item in chunk])
            mask = torch.stack([item["attention_mask"] for item in chunk])
            readout = torch.tensor([item["readout"] for item in chunk], dtype=torch.long)
            token_ids = torch.tensor([[item["honest_token"], item["deceptive_token"]] for item in chunk],
                                     dtype=torch.long)
            target = torch.tensor([item["target_token"] for item in chunk], dtype=torch.long)
            distractor = torch.tensor([item["distractor_token"] for item in chunk], dtype=torch.long)
            out = capturer(input_ids, mask, readout, token_ids)
            logits = out["logits"].detach().float().cpu()
            rows = torch.arange(len(chunk))
            raw.append(logits.gather(1, token_ids))
            logsm.append(torch.log_softmax(logits, dim=-1).gather(1, token_ids))
            centred.append(logits.gather(1, token_ids) - logits.mean(-1, keepdim=True))
            margins.append(logits[rows, target] - logits[rows, distractor])
            honest_margins.append(raw[-1][:, 0] - raw[-1][:, 1])
            resid.append(out["resid"].detach().to(torch.float16).cpu())
            per_token.append(out["dla"].detach().float().cpu())
    cat = (lambda parts, empty: torch.cat(parts) if parts else empty)
    raw_t = cat(raw, torch.zeros(0, 2))
    centred_t = cat(centred, torch.zeros(0, 2))
    dla_t = cat(per_token, torch.zeros(0, len(capturer.keys), 2))
    margin_t = cat(margins, torch.zeros(0))
    honest_t = cat(honest_margins, torch.zeros(0))

    rows_out, diffs = [], []
    for index, item in enumerate(encoded):
        row = row_metadata(resolved, index, item)
        row["model_margin"] = float(margin_t[index])
        row["model_honest_margin"] = float(honest_t[index])
        if row["dataset_margin"] is not None:
            diffs.append(abs(row["model_margin"] - float(row["dataset_margin"])))
        rows_out.append(row)

    ids = list(resolved["ids"])
    readout_t = torch.tensor([item["readout"] for item in encoded], dtype=torch.long)
    resid_t = cat(resid, torch.zeros(0, dtype=torch.float16))
    _save({"ids": ids, "readout": readout_t, "resid": resid_t},
          os.path.join(out_dir, f"resid.{name}.pt"), True)
    _save({"ids": ids, "token_order": list(TOKEN_ORDER),
           "token_ids": torch.tensor([[item["honest_token"], item["deceptive_token"]] for item in encoded],
                                     dtype=torch.long).reshape(-1, 2),
           "logits_raw": raw_t, "logits_logsoftmax": cat(logsm, torch.zeros(0, 2)),
           "logits_centred": centred_t, "keys": [list(key) for key in capturer.keys],
           "dla": dla_t, "dla_centre": True},
          os.path.join(out_dir, f"tokens.{name}.pt"), True)
    _save("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows_out),
          os.path.join(out_dir, f"rows.{name}.jsonl"), False)

    nonfinite = int((~torch.isfinite(resid_t)).sum()) if n else 0
    if nonfinite:
        print(f"    !! {name}: {nonfinite} residual element(s) are not finite in float16 (a bfloat16 value past "
              f"65504 becomes inf on the cast); recorded as resid_nonfinite")
    stats = {
        "n_rows": n, "ids": ids,
        "margin_mean_abs_diff": (sum(diffs) / len(diffs)) if diffs else None,
        "dla_sum_max_abs_error": (float((dla_t.sum(1) - centred_t).abs().max()) if n else None),
        "resid_nonfinite": nonfinite,
    }
    _save(json.dumps(stats, indent=1) + "\n", os.path.join(out_dir, f"done.{name}.json"), False)
    return stats


def _done(out_dir: str, name: str, ids: List[str]) -> Optional[dict]:
    path = os.path.join(out_dir, f"done.{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path) as handle:
        stats = json.load(handle)
    if stats.get("ids") != ids:
        fail(f"cell {name}: {path} was written for other ids; use a fresh --output-dir")
    return stats


def write_manifest(out_dir: str, plan_path: str, plan: dict, resolved: List[dict], argv) -> Optional[str]:
    """run_manifest.json for the capture. Provenance never stops a run: a failure is printed."""
    try:
        import run_manifest

        files = [plan_path]
        directories = set()
        for cell in resolved:
            report = cell["report"]
            directories.add(report["dataset"])
            if report.get("exclude_id_files"):
                directories.add(os.path.join(os.path.dirname(report["dataset"]),
                                             cell["cell"].get("task") or ""))
                files.extend(report["exclude_id_files"])
            if report.get("id_file"):
                files.append(report["id_file"])
            files.extend(resolve_path(path) for path in (cell["cell"].get("flag_id_files") or {}).values())
        for directory in sorted(directories):
            files.extend(run_manifest.data_files_under(directory))
        unique = sorted(set(files))
        return run_manifest.write_run_manifest(
            out_dir, script=os.path.abspath(__file__), argv=list(argv), seed=plan.get("seed"),
            model=plan.get("model"), config_path=plan_path, dataset_files=run_manifest.hash_files(unique),
            code_files=[os.path.join(ROOT, path) for path in CODE_FILES])
    except Exception as error:                  # noqa: BLE001 -- provenance never stops a run
        print(f"  !! run_manifest.json not written: {type(error).__name__}: {error}")
        return None


def print_counts(resolved: List[dict], total: int, *, dry_run: bool) -> None:
    print(f"falsity-probe capture ({'dry run' if dry_run else 'run'}): {len(resolved)} cells")
    print(f"  {'cell':<22} {'role':<9} {'cond':<10} {'split':<10} {'rows':>6}  kept share")
    for cell in resolved:
        report = cell["report"]
        share = report.get("kept_share")
        share_text = (f"{report['n_kept_by_filter']}/{report['n_before_filter']} = {share:.3f}"
                      if cell["cell"].get("keep_if") and share is not None else "")
        print(f"  {cell['name']:<22} {cell['cell']['role']:<9} {cell['cell']['condition']:<10} "
              f"{cell['cell']['split']:<10} {len(cell['ids']):>6}  {share_text}")
    print(f"  total {total}")


def run(plan_path: str, out_dir: str, *, dry_run: bool = False, max_rows: Optional[int] = None,
        check_encoding: bool = False, batch_size: Optional[int] = None, device: str = "cuda",
        argv: Optional[Sequence[str]] = None, load_model_fn=None, load_tokenizer_fn=None) -> dict:
    """Resolve, then (unless a dry run) capture every cell. -> {"cells": {name: {...}}, "total_rows": n}."""
    load_model_fn = load_model_fn or globals()["load_model"]
    load_tokenizer_fn = load_tokenizer_fn or globals()["load_tokenizer"]
    argv = list(sys.argv[1:] if argv is None else argv)
    plan_path = os.path.abspath(plan_path)
    plan = load_plan(plan_path)
    if max_rows is None:
        max_rows = plan.get("max_rows")
    batch_size = int(batch_size or plan.get("batch_size") or 8)

    splits = Splits()
    resolved = [resolve_cell(cell, splits, max_rows=max_rows) for cell in plan["cells"]]
    total = sum(len(cell["ids"]) for cell in resolved)
    os.makedirs(out_dir, exist_ok=True)

    tokenizer, encoded = None, {}
    if not dry_run or check_encoding:
        tokenizer = load_tokenizer_fn(plan["model"])
        for cell in resolved:
            encoded[cell["name"]] = encode_cell(cell, tokenizer)

    summary = {"schema": OUTPUT_SCHEMA, "plan": plan_path, "dry_run": dry_run, "max_rows": max_rows,
               "batch_size": batch_size, "total_rows": total,
               "cells": {cell["name"]: {"spec": cell["cell"], "n_rows": len(cell["ids"]),
                                        "ids": cell["ids"], "report": cell["report"]}
                         for cell in resolved}}
    _save(json.dumps(summary, indent=1) + "\n", os.path.join(out_dir, "capture_plan.json"), False)
    print_counts(resolved, total, dry_run=dry_run)
    write_manifest(out_dir, plan_path, plan, resolved, argv)
    if dry_run:
        return summary

    import torch

    torch.manual_seed(int(plan.get("seed") or 0))
    pending = [cell for cell in resolved if _done(out_dir, cell["name"], cell["ids"]) is None]
    stats = {cell["name"]: _done(out_dir, cell["name"], cell["ids"]) for cell in resolved
             if cell not in pending}
    if pending:
        capturer = make_capturer(load_model_fn(plan["model"], device))
        for cell in pending:
            print(f"  capturing {cell['name']}: {len(cell['ids'])} rows")
            stats[cell["name"]] = capture_cell(cell, encoded[cell["name"]], capturer, out_dir,
                                               batch_size=batch_size)
            done = stats[cell["name"]]
            print(f"    margin mean |model - dataset| {done['margin_mean_abs_diff']}, "
                  f"dla sum max error {done['dla_sum_max_abs_error']}")
    written = {"schema": OUTPUT_SCHEMA, "plan": plan_path, "total_rows": total,
               "cells": {name: {key: value for key, value in one.items() if key != "ids"}
                         for name, one in stats.items()}}
    _save(json.dumps(written, indent=1, sort_keys=True) + "\n",
          os.path.join(out_dir, "capture_summary.json"), False)
    summary["captured"] = written["cells"]
    return summary


# ==============================================================================
# THE B2 P1 PLAN (plan section 1, the split table)
# ==============================================================================

DATA = "data/datasets"
GROUPS = "docs/research/instructed-route/groups"
SUFFIX = {"D": "", "HI": "", "H": "_honest", "F": "_nopressure", "I": "_inversion",
          "I_reported": "_inversion_reported"}


def build_p1_plan(smoke: bool = False) -> dict:
    """The capture plan for B2 P1 (plan section 1). `smoke` adds `max_rows: 64` and nothing else."""

    def cell(task, label, role, condition, split, **extra):
        out = {"name": f"{task}_{label}_{condition}", "role": role, "task": f"{task}_v2",
               "condition": condition, "dataset": f"{DATA}/{task}_v2{SUFFIX[condition]}",
               "split": split, "prompt_field": CONDITIONS[condition][2]}
        if condition == "HI":
            out["keep_if"] = {"field": HI_MARGIN, "min": HI_BAR}
        out.update(extra)
        out["flag_id_files"] = {"in_seed0_sample": f"{GROUPS}/{task}_seed0_ids.txt",
                                "in_seed1_sample": f"{GROUPS}/{task}_seed1_ids.txt"}
        return out

    def held_out(task):
        return {"exclude_id_files": [f"{GROUPS}/{task}_seed0_ids.txt", f"{GROUPS}/{task}_seed1_ids.txt"]}

    cells = [cell("far", "fit", "fit", c, "train") for c in ("D", "H")]
    cells += [cell("far", "select", "select", c, "validation") for c in ("D", "H", "HI")]
    cells += [cell("far", "gate", "far_gate", c, "test", **held_out("far")) for c in ("D", "H", "HI", "F", "I")]
    cells += [cell("ser", "test", "ser_test", c, "test", **held_out("ser")) for c in ("D", "H", "HI", "F", "I")]
    cells += [cell("sdr", "test", "sdr", c, "test", **held_out("sdr")) for c in ("D", "H")]
    cells.append(cell("sdr", "test", "sdr", "I_reported", "test", id_file=f"{GROUPS}/sdr_wish_ids.txt"))
    plan = {
        "schema": PLAN_SCHEMA,
        "description": ("instructed-route B2 P1 capture, plans/B2-plan.md section 1 (split table); "
                        "written by scripts/falsity_probe_capture.py --write-plans"),
        "model": "llama-8b-instruct",
        "seed": 0,
        "batch_size": 8,
        "cells": cells,
    }
    if smoke:
        plan["max_rows"] = 64
    return plan


def render_plan(plan: dict) -> str:
    return json.dumps(plan, indent=1) + "\n"


def write_plans(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)
    for smoke, name in ((False, "B2-p1-plan.json"), (True, "B2-p1-smoke.json")):
        path = os.path.join(directory, name)
        with open(path, "w") as handle:
            handle.write(render_plan(build_p1_plan(smoke=smoke)))
        print(f"wrote {path}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    parser.add_argument("--plan")
    parser.add_argument("--output-dir")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--check-encoding", action="store_true",
                        help="with --dry-run: load the tokenizer and encode every row")
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--write-plans", metavar="DIR")
    args = parser.parse_args(argv)
    if args.write_plans:
        write_plans(args.write_plans)
        return 0
    if not args.plan or not args.output_dir:
        parser.error("--plan and --output-dir are required")
    run(args.plan, args.output_dir, dry_run=args.dry_run, max_rows=args.max_rows,
        check_encoding=args.check_encoding, batch_size=args.batch_size, device=args.device, argv=argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
